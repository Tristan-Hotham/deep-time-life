"""Every number used in the page, paper, blog and collage (data/results.json), the chart data for the page
(data/site.json) and the reusable tables in data/ (groups_through_time.csv, genera.csv, collections.csv,
pangaea_index.csv, latitude_bands.csv, extinctions.csv)."""
import pandas as pd, numpy as np
from collections import Counter
from common import *

d = pd.read_pickle(f"{WORK}/occ.pkl")
ST = jload(f"{WORK}/occ_stats.json")
C = jload(f"{WORK}/coast_stats.json")
FS = jload(f"{WORK}/frames_summary.json")
AGES = C["ages"]
t = d[d.ok_age].copy()             # time analyses: ages known to within 25 million years
NB = int(540 / BIN)
t["bin"] = np.minimum((t.mid // BIN).astype(int), NB - 1)
R = {"meta": {"accessed": ACCESSED, "page": PAGE_URL, "repo": REPO, "slug": SLUG}}
pct = lambda a, b: round(100 * a / b, 1) if b else 0.0

# ---------------------------------------------------------------- records
R["records"] = {"rows_raw": ST["rows_raw"], "occ_unique": ST["occ_unique"], "dupes": ST["dupes_removed"],
                "pro_not_mammal": ST["pro_not_mammal"], "tem_to_lis": ST["tem_to_lis"], "the_to_ave": ST["the_to_ave"],
                "dino_late": ST["dino_after_66_dropped"], "paleo_missing": ST["paleo_missing"], "paleo_filled": ST["paleo_filled_young"],
                "dropped_no_paleo": ST["occ_dropped_no_paleo"], "with_paleo": ST["occ_with_paleo"], "wide_age": ST["occ_wide_age"],
                "n": len(t), "collections": int(t.collection_no.nunique()), "genera": int(t.gen.nunique()),
                "with_genus_pct": pct(t.gen.notna().sum(), len(t)), "countries": int(t[t.country != "At sea"].country.nunique()),
                "n_groups": len(GK), "n_queries": len(ST["by_query"]), "max_range": MAX_RANGE}
assert R["records"]["n"] == ST["occ_ok_age"]

# ---------------------------------------------------------------- sampling: where the fossils come from (present day)
cont = t.continent.value_counts()
R["sampling"] = {"by_continent": [{"name": k, "n": int(v), "pct": pct(v, len(t))} for k, v in cont.items()],
                 "na_eu_pct": pct(cont.get("North America", 0) + cont.get("Europe", 0), len(t)),
                 "africa_pct": pct(cont.get("Africa", 0), len(t)), "sam_pct": pct(cont.get("South America", 0), len(t)),
                 "top_countries": [{"name": k, "n": int(v), "pct": pct(v, len(t))} for k, v in t.country.value_counts().head(10).items()]}
R["sampling"]["usa_pct"] = R["sampling"]["top_countries"][0]["pct"]
assert R["sampling"]["top_countries"][0]["name"] == "United States of America"
# share from North America and Europe by era
era_s = {}
for name, hi, lo, _ in ERAS:
    s = t[(t.mid < hi) & (t.mid >= lo)]
    era_s[name] = pct(s.continent.isin(["North America", "Europe"]).sum(), len(s))
R["sampling"]["na_eu_by_era"] = era_s
# land area today of the two continents, for comparison (Natural Earth continents, from the 1:10m countries)
import geopandas as gpd
a0 = gpd.read_file(NE0)[["CONTINENT", "geometry"]].to_crs("+proj=cea +datum=WGS84")
ca = a0.assign(a=a0.area).groupby("CONTINENT").a.sum()
R["sampling"]["na_eu_land_pct"] = pct(ca.get("North America", 0) + ca.get("Europe", 0), ca.drop(labels=["Seven seas (open ocean)"], errors="ignore").sum())

# ---------------------------------------------------------------- groups
gen_rng = t[t.gen.notna()].groupby("gen").agg(fad=("mid", "max"), lad=("mid", "min"), g=("g", lambda s: s.mode().iat[0]),
                                              n=("occurrence_no", "size"), ncoll=("collection_no", "nunique"), ncont=("continent", "nunique"))
groups = []
for k in GK:
    s = t[t.g == k]
    q = s.mid.quantile([0.002, 0.998]) if len(s) else pd.Series([0, 0], index=[0.002, 0.998])
    byb = s.groupby("bin").gen.nunique()
    peak = int(byb.idxmax()) if len(byb) else 0
    top_c = s.country.value_counts()
    groups.append({"k": k, "short": G[k]["short"], "name": G[k]["name"], "c": G[k]["c"], "n": int(len(s)),
                   "coll": int(s.collection_no.nunique()), "genera": int(s.gen.nunique()),
                   "oldest": round(float(s.mid.max()), 1), "youngest": round(float(s.mid.min()), 1),
                   "first": round(float(q.iloc[1]), 1), "last": round(float(q.iloc[0]), 1),
                   "peak_bin": [peak * BIN, peak * BIN + BIN], "peak_genera": int(byb.max()) if len(byb) else 0,
                   "top_country": top_c.index[0] if len(top_c) else "", "top_country_pct": pct(top_c.iloc[0], len(s)) if len(top_c) else 0,
                   "na_eu_pct": pct(s.continent.isin(["North America", "Europe"]).sum(), len(s))})
R["groups"] = {x["k"]: x for x in groups}
order = sorted(GK, key=lambda k: -R["groups"][k]["first"])
R["group_order"] = order
R["largest_group"] = max(GK, key=lambda k: R["groups"][k]["n"])
R["smallest_group"] = min(GK, key=lambda k: R["groups"][k]["n"])

# ---------------------------------------------------------------- through time: genera and occurrences per 5 Myr bin
gen_bin = t[t.gen.notna()].groupby(["g", "bin"]).gen.nunique().unstack(fill_value=0).reindex(index=GK, columns=range(NB), fill_value=0)
occ_bin = t.groupby(["g", "bin"]).size().unstack(fill_value=0).reindex(index=GK, columns=range(NB), fill_value=0)
coll_bin = t.groupby("bin").collection_no.nunique().reindex(range(NB), fill_value=0)
rows = []
for k in GK:
    for b in range(NB):
        if gen_bin.at[k, b] or occ_bin.at[k, b]:
            rows.append({"group": G[k]["short"], "group_key": k, "bin_young_ma": b * BIN, "bin_old_ma": b * BIN + BIN,
                         "genera": int(gen_bin.at[k, b]), "occurrences": int(occ_bin.at[k, b])})
pd.DataFrame(rows).to_csv(f"{DATA}/groups_through_time.csv", index=False)
tot_gen = gen_bin.sum(axis=0)
R["empty_bins"] = [int(b * BIN) for b in range(int(500 / BIN)) if occ_bin[b].sum() == 0]
assert R["empty_bins"] == [225], R["empty_bins"]
lead = {}
for b in range(NB):
    col = gen_bin[b]
    if col.sum() >= 20:
        lead[b] = col.idxmax()
# leading group per era (by genera share, summed over bins)
R["leaders"] = {}
for name, hi, lo, _ in ERAS:
    bs = [b for b in range(NB) if lo <= b * BIN < hi]
    s = gen_bin[bs].sum(axis=1)
    R["leaders"][name] = {"k": s.idxmax(), "pct": pct(s.max(), s.sum())}
# runs of leadership through time
runs = []
for b in sorted(lead, reverse=True):
    k = lead[b]
    if runs and runs[-1]["k"] == k and runs[-1]["young"] == b * BIN + BIN:
        runs[-1]["young"] = b * BIN
    else:
        runs.append({"k": k, "old": b * BIN + BIN, "young": b * BIN})
R["lead_runs"] = runs

# ---------------------------------------------------------------- Pangaea index (largest joined land mass)
pi = [{"age": a, **{k: C["stats"][str(a)][k] for k in ("largest_pct", "land_mkm2", "largest_mkm2", "n_blocks_1mkm2")}} for a in AGES]
pd.DataFrame(pi).to_csv(f"{DATA}/pangaea_index.csv", index=False)
peak = max(pi, key=lambda r: (r["largest_pct"], r["age"]))
R["pangaea"] = {"peak_pct": peak["largest_pct"], "peak_age": peak["age"], "today_pct": C["stats"]["0"]["largest_pct"],
                "at": {str(a): C["stats"][str(a)]["largest_pct"] for a in (0, 66, 100, 150, 170, 180, 200, 250, 270, 280, 300, 335, 340, 400, 500)
                       if str(a) in C["stats"]},
                "first_over_85": max(a for a in AGES if C["stats"][str(a)]["largest_pct"] >= 85),
                "last_over_85": min(a for a in AGES if C["stats"][str(a)]["largest_pct"] >= 85),
                "years_over_85": None}
over = [a for a in AGES if C["stats"][str(a)]["largest_pct"] >= 85]
R["pangaea"]["years_over_85"] = R["pangaea"]["first_over_85"] - R["pangaea"]["last_over_85"]
assert all(C["stats"][str(a)]["largest_pct"] >= 85 for a in AGES if R["pangaea"]["last_over_85"] <= a <= R["pangaea"]["first_over_85"])
R["pangaea"]["land_mkm2_today"] = C["stats"]["0"]["land_mkm2"]

# ---------------------------------------------------------------- dinosaurs
DINT = [("Late Triassic", 237.0, 201.4), ("Early Jurassic", 201.4, 174.7), ("Middle Jurassic", 174.7, 161.5),
        ("Late Jurassic", 161.5, 143.1), ("Early Cretaceous", 143.1, 100.5), ("Late Cretaceous", 100.5, 66.0)]
dn = t[t.g.isin(DINO)]
R["dino"] = {"n": int(len(dn)), "genera": int(dn.gen.nunique()), "coll": int(dn.collection_no.nunique()),
             "by_sub": {k: {"n": int((dn.g == k).sum()), "genera": int(dn[dn.g == k].gen.nunique())} for k in DINO},
             "oldest": round(float(dn.mid.max()), 1), "na_eu_pct": pct(dn.continent.isin(["North America", "Europe"]).sum(), len(dn)),
             "top_country": dn.country.value_counts().index[0], "top_country_pct": pct(dn.country.value_counts().iloc[0], len(dn))}
dg = dn[dn.gen.notna()].groupby("gen").agg(fad=("mid", "max"), lad=("mid", "min"))
iv = []
for name, hi, lo in DINT:
    s = dn[(dn.mid < hi) & (dn.mid >= lo) & dn.gen.notna()]
    gc = s.groupby("gen").continent.nunique()
    conts = s.continent.value_counts()
    mid_age = (hi + lo) / 2
    near = min(AGES, key=lambda a: abs(a - mid_age))
    # median distance between all pairs of collections, in degrees of palaeo position, is not used: sampling decides it
    iv.append({"name": name, "old": hi, "young": lo, "genera": int(len(gc)), "multi": int((gc >= 2).sum()),
               "multi_pct": pct((gc >= 2).sum(), len(gc)), "n": int(len(s)), "n_cont": int((conts >= 10).sum()),
               "pangaea_pct": C["stats"][str(near)]["largest_pct"], "pangaea_age": near,
               "na_eu_pct": pct(s.continent.isin(["North America", "Europe"]).sum(), len(s))})
R["dino"]["intervals"] = iv
for key, hi, lo in (("pangaea", 237.0, 174.7), ("cretaceous", 143.1, 66.0)):
    s = dn[(dn.mid < hi) & (dn.mid >= lo) & dn.gen.notna()]
    gc = s.groupby("gen").continent.nunique()
    R["dino"][f"multi_{key}"] = {"genera": int(len(gc)), "multi": int((gc >= 2).sum()), "pct": pct((gc >= 2).sum(), len(gc)),
                                  "one_in": round(len(gc) / max(1, (gc >= 2).sum()))}
# shared genera between continents, Pangaea time (Late Triassic and Early Jurassic) against the Late Cretaceous
dsub = {k: (G[k]["short"]) for k in DINO}
# dinosaur genera per 5 Myr bin per subgroup (and birds)
DB = list(range(int(66 / BIN) - 1, int(240 / BIN)))
R["dino"]["peak_bin"] = None
db = {k: [int(gen_bin.at[k, b]) for b in DB] for k in DINO + ["ave"]}
tot = [sum(db[k][i] for k in DINO) for i in range(len(DB))]
pk = int(np.argmax(tot))
R["dino"]["peak_bin"] = [DB[pk] * BIN, DB[pk] * BIN + BIN]
R["dino"]["peak_genera"] = tot[pk]
pb = dn[(dn.mid >= DB[pk] * BIN) & (dn.mid < DB[pk] * BIN + BIN)]
R["dino"]["peak_na_pct"] = pct((pb.continent == "North America").sum(), len(pb))
last = dn.groupby("g").mid.min()
R["dino"]["maastrichtian_genera"] = int(dn[(dn.mid < 72.1) & (dn.mid >= 66)].gen.nunique())
R["dino"]["maastrichtian_coll"] = int(dn[(dn.mid < 72.1) & (dn.mid >= 66)].collection_no.nunique())
mh = dn[(dn.mid < 72.1) & (dn.mid >= 66)]
R["dino"]["maastrichtian_na_pct"] = pct((mh.continent == "North America").sum(), len(mh))

# ---------------------------------------------------------------- latitude
latrows, LAT = [], {}
LB = 10.0
for k in GK:
    s = t[t.g == k].drop_duplicates(["collection_no"])
    s = s.assign(lb=(s.mid // LB).astype(int))
    series = []
    for b, x in s.groupby("lb"):
        if len(x) < 5:
            continue
        q = x.paleolat.quantile([.1, .5, .9]).round(1).tolist()
        ab = x.paleolat.abs()
        series.append([b * LB + LB / 2, q[0], q[1], q[2], int(len(x))])
        latrows.append({"group": G[k]["short"], "group_key": k, "bin_young_ma": b * LB, "bin_old_ma": b * LB + LB, "collections": int(len(x)),
                        "palaeolat_p10": q[0], "palaeolat_median": q[1], "palaeolat_p90": q[2], "abs_palaeolat_median": round(float(ab.median()), 1)})
    LAT[k] = sorted(series, key=lambda r: -r[0])
pd.DataFrame(latrows).to_csv(f"{DATA}/latitude_bands.csv", index=False)
la = pd.DataFrame(latrows)
# polar dinosaurs: collections above 60 degrees palaeo-latitude
dc = dn.drop_duplicates("collection_no")
R["dino"]["polar_coll"] = int((dc.paleolat.abs() >= 60).sum())
R["dino"]["polar_max"] = round(float(dc.paleolat.abs().max()), 1)
pm = dc.loc[dc.paleolat.abs().idxmax()]
R["dino"]["polar_place"] = f"{pm.province}, {pm.country}" if isinstance(pm.province, str) else pm.country
R["dino"]["polar_place_age"] = round(float(pm.mid), 1)
pc = dc[dc.paleolat.abs() >= 75]
R["dino"]["polar75_coll"] = int(len(pc))
R["dino"]["polar75_places"] = {k: int(v) for k, v in pc.province.fillna(pc.country).value_counts().head(8).items()}
# median palaeo-latitude of trilobite and ammonite and mammal collections, absolute
R["lat"] = {k: round(float(t[t.g == k].drop_duplicates("collection_no").paleolat.abs().median()), 1) for k in GK}
R["lat_today_vs"] = {"mam_0_10": round(float(la[(la.group_key == "mam") & (la.bin_young_ma == 0)].abs_palaeolat_median.iloc[0]), 1)}
# palaeo-latitude drift: present-day latitude minus palaeo-latitude, median absolute, for collections older than 200 Ma
old = t[t.mid > 200].drop_duplicates("collection_no")
R["drift"] = {"median_abs_dlat_old200": round(float((old.lat - old.paleolat).abs().median()), 1)}
uk = t[(t.country == "United Kingdom")].drop_duplicates("collection_no")
for lo, hi in ((420, 440), (300, 320), (190, 210), (60, 70)):
    s = uk[(uk.mid >= lo) & (uk.mid < hi)]
    R["drift"][f"uk_{lo}"] = round(float(s.paleolat.median()), 1) if len(s) else None
R["drift"]["uk_today"] = round(float(uk.lat.median()), 1)
R["drift"]["uk_420_abs"] = abs(R["drift"]["uk_420"])
assert R["drift"]["uk_420"] < -15 and R["drift"]["uk_190"] > 30
v = R["drift"]["uk_300"]
R["drift"]["uk_300_age"] = "300 to 320"
R["drift"]["uk_300_txt"] = "within a degree of it" if abs(v) < 1 else f"{abs(v):.0f} degrees {'north' if v > 0 else 'south'}"
R["drift"]["uk_n"] = int(len(uk))

# ---------------------------------------------------------------- extinctions: genera last seen in the 10 Myr before
# Genera known from at least two collections (one-off finds would count as 'last seen' wherever they happen to be found).
gr = gen_rng[gen_rng.ncoll >= 2]
R["ext_min_coll"] = 2
ext = []
for key, name, A in EXTINCTIONS:
    stand = gr[(gr.fad > A) & (gr.lad < A + 10)]
    vict = stand[stand.lad >= A]
    per = {}
    for k in GK:
        sk = stand[stand.g == k]
        if len(sk) >= 10:
            per[k] = {"standing": int(len(sk)), "lost_pct": pct((sk.lad >= A).sum(), len(sk))}
    ext.append({"k": key, "name": name, "age": A, "standing": int(len(stand)), "lost": int(len(vict)), "lost_pct": pct(len(vict), len(stand)), "by_group": per})
# background: the same measure at every other 10 Myr step from 440 to 20 Ma
bg = []
for A in range(20, 541, 10):
    if any(abs(A - e[2]) < 10 for e in EXTINCTIONS):
        continue
    stand = gr[(gr.fad > A) & (gr.lad < A + 10)]
    if len(stand) >= 50:
        bg.append(pct((stand.lad >= A).sum(), len(stand)))
R["extinctions"] = ext
R["ext_bg_median"] = round(float(np.median(bg)), 1)
R["ext_bg_p90"] = round(float(np.percentile(bg, 90)), 1)
R["ext_bg_n"] = len(bg)
pd.DataFrame([{k: v for k, v in e.items() if k != "by_group"} for e in ext]).to_csv(f"{DATA}/extinctions.csv", index=False)
# signature losses: last records of groups
R["last"] = {k: R["groups"][k]["last"] for k in ("tri", "eur", "pla", "amm", "ich", "ple", "mos", "ptr", "the", "sau", "orn", "tem", "syn")}

# ---------------------------------------------------------------- facts stated in words
hm = t[t.g == "hom"]
R["facts"] = {"hom_afr_asia_pct": pct(hm.continent.isin(["Africa", "Asia"]).sum(), len(hm)),
              "hom_abs_lat_tropics_pct": pct((hm.paleolat.abs() <= 23.44).sum(), len(hm))}
ins = t[t.g == "ins"]; ic = ins.collection_no.value_counts()
R["facts"]["ins_top50_coll_pct"] = pct(ic.head(50).sum(), len(ins))
R["facts"]["ins_coll"] = int(len(ic))
for fam, key in (("Tyrannosauridae", "tyr"), ("Ceratopsidae", "cer"), ("Abelisauridae", "abe"), ("Titanosauria", "tit")):
    s_ = t[(t.family == fam) | (t.accepted_name == fam)] if fam != "Titanosauria" else t[t.g == "sau"][t[t.g == "sau"].mid < 100]
    north = s_.continent.isin(["North America", "Asia", "Europe"]).sum()
    R["facts"][f"{key}_north_pct"] = pct(north, len(s_)); R["facts"][f"{key}_n"] = int(len(s_))
ab = t[t.family == "Abelisauridae"]
R["facts"]["abe_south_india_pct"] = pct((~ab.continent.isin(["North America", "Asia", "Europe"]) | (ab.country == "India")).sum(), len(ab))
tm = d[(d.gen == "Tyrannosaurus") & (d.province == "Montana")].drop_duplicates("collection_no")
R["facts"]["trex_mt_n"] = int(len(tm)); R["facts"]["trex_mt_dlat"] = round(float((tm.paleolat - tm.lat).median()), 1)
pa = dc[(dc.paleolat.abs() >= 75) & (dc.province == "Alaska")]
R["facts"]["alaska_polar_min_lat"] = round(float(pa.lat.min()), 1)

# ---------------------------------------------------------------- frames
R["frames"] = {"n": len(AGES), "first": AGES[-1], "last": AGES[0], "max_n": max(FS[str(a)]["n"] for a in AGES),
               "cells_total": sum(FS[str(a)]["cells"] for a in AGES)}
R["frames"]["kb_total"] = round(sum(FS[str(a)]["kb"] for a in AGES))

# ---------------------------------------------------------------- genera and collections tables
gtab = gen_rng.reset_index().rename(columns={"gen": "genus", "fad": "oldest_mid_ma", "lad": "youngest_mid_ma", "n": "occurrences", "ncont": "continents"})
gtab["group"] = gtab.g.map(lambda k: G[k]["short"]); gtab = gtab.drop(columns=["g"]).sort_values(["group", "genus"])
gtab.to_csv(f"{DATA}/genera.csv", index=False, float_format="%.2f")
cl = d.groupby(["collection_no", "g"]).agg(occurrences=("occurrence_no", "size"), max_ma=("max_ma", "first"), min_ma=("min_ma", "first"),
                                           lng=("lng", "first"), lat=("lat", "first"), paleolng=("paleolng", "first"), paleolat=("paleolat", "first"),
                                           country=("country", "first"), province=("province", "first"), genera=("gen", lambda s: "|".join(sorted(set(s.dropna()))[:30]))).reset_index()
cl["group"] = cl.g.map(lambda k: G[k]["short"]); cl = cl.drop(columns=["g"])
cl["mid_ma"] = ((cl.max_ma + cl.min_ma) / 2).round(2)
cl.to_csv(f"{DATA}/collections.csv.gz", index=False, compression="gzip")
R["records"]["collections_rows"] = len(cl)

# ---------------------------------------------------------------- page data
SITE = {"groups": [[k, G[k]["short"], G[k]["name"], G[k]["c"]] for k in GK], "order": order,
        "bins": NB, "binw": BIN, "gen": {k: gen_bin.loc[k].tolist() for k in GK}, "occ": {k: occ_bin.loc[k].tolist() for k in GK},
        "coll": coll_bin.tolist(), "eras": ERAS, "periods": PERIODS, "ext": EXTINCTIONS, "ages": AGES,
        "pangaea": [[a, C["stats"][str(a)]["largest_pct"]] for a in AGES],
        "labels": {str(a): C["stats"][str(a)]["label"] for a in AGES},
        "frames": {str(a): {"win": FS[str(a)]["win"], "n": FS[str(a)]["n"]} for a in AGES},
        "dino_bins": [b * BIN for b in DB], "dino": db, "lat": LAT, "dint": iv,
        "na_eu_bin": []}
nab = t.assign(ne=t.continent.isin(["North America", "Europe"])).groupby("bin").ne.mean().reindex(range(NB))
SITE["na_eu_bin"] = [None if np.isnan(v) else round(100 * v, 1) for v in nab]
jsave(SITE, f"{DATA}/site.json")
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps({k: R[k] for k in ("records", "sampling", "pangaea", "leaders", "lead_runs", "dino", "extinctions", "ext_bg_median", "lat", "drift", "last")}, indent=0, ensure_ascii=False)[:9000])
print(os.path.getsize(f"{DATA}/site.json") // 1024, "KB site")
