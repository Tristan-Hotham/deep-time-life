"""Read the PBDB occurrences, keep each occurrence once in its most specific group, add ages, fill palaeo-positions for
the youngest collections, and find the present-day country and province of every collection (Natural Earth).

Writes WORK/occ.pkl (one row per kept occurrence) and WORK/occ_stats.json (counts used in results.json)."""
import pandas as pd, numpy as np, geopandas as gpd
from common import *

d = pd.read_csv(OCC, sep="\t", low_memory=False)
st = {"rows_raw": len(d), "by_query": d.grp.value_counts().to_dict()}
d["g"] = d.grp.map(PBDB2K)
assert d.g.notna().all()
# Fix the query results where the PBDB name reaches beyond the animals meant:
#  'Proboscidea' also matches an insect name (kept only in class Mammalia; the insects are also in the Insecta query);
#  'Temnospondyli' includes the living amphibians (Lissamphibia), split off as their own group by order;
#  'Theropoda^Aves' still holds Mesozoic and some living birds (bird orders, Ichthyornithes), moved to birds.
bad_pro = (d.g == "pro") & (d["class"] != "Mammalia")
st["pro_not_mammal"] = int(bad_pro.sum())
d = d[~bad_pro].copy()
liss = (d.g == "tem") & (d.order.isin(LISS_ORDERS) | (d.family == "Albanerpetontidae") | d.accepted_name.isin(["Lissamphibia", "Batrachia"]))
st["tem_to_lis"] = int(liss.sum())
d.loc[liss, "g"] = "lis"
birdish = (d.g == "the") & (d.order.fillna("").str.endswith("formes") | (d.order == "Ichthyornithes"))
st["the_to_ave"] = int(birdish.sum())
d.loc[birdish, "g"] = "ave"
d["pri"] = d.g.map({k: i for i, k in enumerate(PRIORITY)})
d = d.sort_values(["occurrence_no", "pri"]).drop_duplicates("occurrence_no", keep="first").drop(columns=["pri", "grp"])
st["occ_unique"] = len(d)
st["dupes_removed"] = st["rows_raw"] - st["pro_not_mammal"] - len(d)

d["mid"] = (d.max_ma + d.min_ma) / 2
d["rng"] = d.max_ma - d.min_ma
# non-bird dinosaurs whose midpoint falls after the end-Cretaceous extinction: reworked bones or loosely dated beds
late = d.g.isin(DINO) & (d.mid < 66.0)
st["dino_after_66_dropped"] = int(late.sum())
d = d[~late].copy()
st["occ_unique_kept"] = len(d)
# genus: first word of PBDB's genus field (subgenera are written 'Genus (Subgenus)')
d["gen"] = d.genus.fillna("").astype(str).str.split(" ").str[0].replace({"": None, "nan": None})

# Palaeo-positions. PALEOMAP positions are missing for 'not computable' collections; for collections younger than
# 1 million years the present position is used (plates move at most a few tens of km in that time).
miss = d.paleolat.isna()
young = miss & (d.mid <= 1.0)
d.loc[young, "paleolng"] = d.loc[young, "lng"]
d.loc[young, "paleolat"] = d.loc[young, "lat"]
d["filled"] = young
st["paleo_missing"] = int(miss.sum())
st["paleo_filled_young"] = int(young.sum())
d = d[d.paleolat.notna()].copy()
st["occ_with_paleo"] = len(d)
st["occ_dropped_no_paleo"] = st["occ_unique_kept"] - len(d)
d["ok_age"] = d.rng <= MAX_RANGE
st["occ_ok_age"] = int(d.ok_age.sum())
st["occ_wide_age"] = int((~d.ok_age).sum())

# Present-day place of each collection
col = d.groupby("collection_no").agg(lng=("lng", "first"), lat=("lat", "first")).reset_index()
pts = gpd.GeoDataFrame(col, geometry=gpd.points_from_xy(col.lng, col.lat), crs=4326)
a1 = gpd.read_file(NE1)[["name", "admin", "adm0_a3", "geometry"]]
a0 = gpd.read_file(NE0)[["NAME", "ADM0_A3", "CONTINENT", "geometry"]].rename(columns={"NAME": "country", "ADM0_A3": "iso", "CONTINENT": "continent"})
j0 = gpd.sjoin(pts, a0, how="left", predicate="within").drop_duplicates("collection_no")
lost = j0.country.isna()
# offshore or on a coastline the 1:10m outline misses: nearest country within about 1 degree
near = gpd.sjoin_nearest(pts[lost.values].to_crs(3857), a0.to_crs(3857), how="left", max_distance=120000).drop_duplicates("collection_no")
j0 = j0.set_index("collection_no")
near = near.set_index("collection_no")
for c in ("country", "iso", "continent"):
    j0.loc[near.index, c] = near[c]
j1 = gpd.sjoin(pts, a1, how="left", predicate="within").drop_duplicates("collection_no").set_index("collection_no")
col = col.set_index("collection_no")
col["country"] = j0.country
col["iso"] = j0.iso
col["continent"] = j0.continent
col["province"] = j1["name"]
st["coll_no_country"] = int(col.country.isna().sum())
col["country"] = col.country.fillna("At sea")
col["continent"] = col.continent.fillna("Ocean")
col.loc[col.continent == "Seven seas (open ocean)", "continent"] = "Ocean"
col.loc[col.iso.isin(["RUS"]), "continent"] = np.where(col.loc[col.iso.isin(["RUS"]), "lng"] < 60, "Europe", "Asia")
d = d.join(col[["country", "iso", "continent", "province"]], on="collection_no")
st["collections"] = int(d.collection_no.nunique())
d.to_pickle(f"{WORK}/occ.pkl")
jsave(st, f"{WORK}/occ_stats.json", indent=1)
print(json.dumps(st, indent=1))
print(d.g.value_counts())
print(d.continent.value_counts())
