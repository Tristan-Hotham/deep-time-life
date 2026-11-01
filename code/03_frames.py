"""Map frames: for each coastline age, the fossils of that time binned by collection into 1 degree cells of palaeo-
latitude and longitude, per group. One small JSON file per frame (data/frames/<age>.json), loaded by the page as the
slider moves, plus two lookup tables shared by all frames: data/names.json (taxon names) and data/places.json
(present-day places).

Frame windows: midpoint age within 5 million years either side of the frame age, except at the five extinction ages,
where the frame shows the 10 million years before the extinction (so the 66 Ma frame shows the last dinosaurs, not
the first mammals after them)."""
import pandas as pd, numpy as np
from collections import Counter
from common import *

d = pd.read_pickle(f"{WORK}/occ.pkl")
d = d[d.ok_age].copy()
C = jload(f"{WORK}/coast_stats.json")
AGES = C["ages"]
EXT = {e[2] for e in EXTINCTIONS}
gi = {k: i for i, k in enumerate(GK)}
d["gi"] = d.g.map(gi)
d["name"] = d.gen.where(d.gen.notna(), d.accepted_name)
d["is_gen"] = d.gen.notna()
d["place"] = np.where(d.province.notna(), d.province.fillna("") + ", " + d.country, d.country)

# names table: every name used, with its group (most common), occurrences and age span (midpoints)
nm = d.groupby("name").agg(n=("occurrence_no", "size"), old=("mid", "max"), young=("mid", "min"), is_gen=("is_gen", "first"),
                          g=("gi", lambda s: s.mode().iat[0])).reset_index().sort_values("n", ascending=False).reset_index(drop=True)
NID = {n: i for i, n in enumerate(nm.name)}
d["nid"] = d.name.map(NID)
pl = d.place.value_counts()
PID = {p: i for i, p in enumerate(pl.index)}
d["pid"] = d.place.map(PID)
jsave([[r.name, int(r.g), int(r.n), round(float(r.old), 1), round(float(r.young), 1), int(bool(r.is_gen))] for r in nm.itertuples()], f"{DATA}/names.json")
jsave(list(pl.index), f"{DATA}/places.json")


def window(a):
    return (a, a + 10.0) if a in EXT else (max(0.0, a - HALF), a + HALF)


summary = {}
tot_kb = 0
for a in AGES:
    lo, hi = window(a)
    f = d[(d.mid >= lo) & (d.mid < hi)].copy()
    f["cx"] = np.floor(f.paleolng / CELL).astype(int)
    f["cy"] = np.floor(f.paleolat / CELL).astype(int)
    cells = []
    for (g, cx, cy), s in f.groupby(["gi", "cx", "cy"]):
        cl = s.drop_duplicates("collection_no")
        names = Counter(s.nid)
        cells.append([int(g), round(float(cl.paleolng.mean()), 1), round(float(cl.paleolat.mean()), 1), int(len(s)), int(len(cl)),
                      round(float(cl.lng.mean()), 1), round(float(cl.lat.mean()), 1), int(cl.pid.mode().iat[0]),
                      round(float(s.mid.min()), 1), round(float(s.mid.max()), 1), [n for n, _ in names.most_common(40)]])
    cells.sort(key=lambda c: -c[3])   # big cells drawn first, small on top
    byg = f.groupby("gi").size()
    out = {"age": a, "win": [lo, hi], "n": int(len(f)), "nc": int(f.collection_no.nunique()),
           "byg": [int(byg.get(i, 0)) for i in range(len(GK))], "cells": cells}
    jsave(out, f"{FRAMES}/{a}.json")
    kb = os.path.getsize(f"{FRAMES}/{a}.json") / 1024
    tot_kb += kb
    summary[a] = {"win": [lo, hi], "n": int(len(f)), "nc": int(f.collection_no.nunique()), "cells": len(cells),
                  "byg": {GK[i]: int(v) for i, v in byg.items()}, "kb": round(kb, 1)}
    print(a, lo, hi, len(f), len(cells), round(kb), "KB")
jsave(summary, f"{WORK}/frames_summary.json", indent=1)
print("names", len(nm), os.path.getsize(f"{DATA}/names.json") // 1024, "KB; places", len(pl), os.path.getsize(f"{DATA}/places.json") // 1024, "KB; frames", round(tot_kb), "KB")
