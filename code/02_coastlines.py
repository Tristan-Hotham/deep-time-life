"""Coastlines: merge the PALEOMAP blocks of each age into land masses, simplify them for the web (data/coast/<age>.json,
well under 150 KB each) and keep a finer copy for the static figures (WORK/coast_fine.json). Measures how much of the
land is joined in one block at each age (the 'Pangaea index'), on the sphere, joining blocks across the 180th meridian.

The PALEOMAP coastline polygons are present-day coastlines and continental blocks carried back in time by the plate
model, not ancient shorelines: shallow seas that flooded continents (for example the Cretaceous Western Interior
Seaway) are not shown. Writes WORK/coast_stats.json."""
import numpy as np
from shapely.geometry import shape, Polygon, MultiPolygon, box, mapping
from shapely.ops import unary_union
from shapely import set_precision
from shapely.geometry.polygon import orient
from pyproj import Transformer
from shapely.ops import transform as stransform
from common import *

J = jload(COAST)
AGES = sorted((int(float(k)) for k in J), key=int)
cea = Transformer.from_crs("+proj=longlat +datum=WGS84", "+proj=cea +datum=WGS84", always_xy=True)
EARTH = 4 * np.pi * 6371.0088 ** 2


def polys(fc):
    out = []
    for f in fc["features"]:
        g = f["geometry"]
        cs = [g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"]
        for c in cs:
            if len(c[0]) < 4:
                continue
            p = Polygon(c[0], [h for h in c[1:] if len(h) >= 4])
            if not p.is_valid:
                p = p.buffer(0)
            if not p.is_empty:
                out.append(p)
    return out


def parts(g):
    return list(g.geoms) if isinstance(g, MultiPolygon) else ([g] if isinstance(g, Polygon) and not g.is_empty else [])


def area_km2(g):
    return stransform(lambda x, y: cea.transform(x, y), g).area / 1e6


WORLD = box(-180, -90, 180, 90)
stats, fine = {}, {}
for age in AGES:
    P = polys(J[str(age)])
    land = unary_union(P).intersection(WORLD)
    # blocks of one continent are separated by hairline gaps: close gaps narrower than about 0.3 degrees
    joined = land.buffer(0.15, join_style="mitre").buffer(-0.15, join_style="mitre").intersection(WORLD)
    comps = sorted(parts(joined), key=lambda p: -p.area)
    # join components across the 180th meridian
    par = list(range(len(comps)))

    def find(i):
        while par[i] != i:
            par[i] = par[par[i]]; i = par[i]
        return i
    east = [c.intersection(box(179.7, -90, 180, 90)) for c in comps]
    west = [c.intersection(box(-180, -90, -179.7, 90)) for c in comps]
    for i, e in enumerate(east):
        if e.is_empty:
            continue
        ey = (e.bounds[1], e.bounds[3])
        for k, w in enumerate(west):
            if w.is_empty:
                continue
            # overlap in latitude along the seam
            seam_e = e.intersection(box(179.7, -90, 180, 90)); seam_w = w
            for pe in parts(seam_e):
                for pw in parts(seam_w):
                    lo, hi = max(pe.bounds[1], pw.bounds[1]), min(pe.bounds[3], pw.bounds[3])
                    if hi - lo > 0.2:
                        par[find(i)] = find(k)
    areas = [area_km2(c) for c in comps]
    tot = sum(areas)
    grp = {}
    for i, a in enumerate(areas):
        grp.setdefault(find(i), []).append(i)
    blocks = sorted(((sum(areas[i] for i in v), v) for v in grp.values()), key=lambda t: -t[0])
    big = blocks[0]
    # where the largest block is centred (for labels): its largest piece's representative point
    rp = comps[max(big[1], key=lambda i: areas[i])].representative_point()
    stats[age] = {"land_mkm2": round(tot / 1e6, 2), "land_pct_earth": round(100 * tot / EARTH, 1),
                  "largest_mkm2": round(big[0] / 1e6, 2), "largest_pct": round(100 * big[0] / tot, 1),
                  "second_pct": round(100 * blocks[1][0] / tot, 1) if len(blocks) > 1 else 0,
                  "n_blocks_1mkm2": sum(1 for b in blocks if b[0] >= 1e6), "label": [round(rp.x, 1), round(rp.y, 1)]}

    # web version: simplify, drop specks, round to 0.1 degree, clockwise outer rings (d3-geo convention)
    def web(tol, minarea, prec):
        out = []
        for p in parts(land):
            if p.area < minarea:
                continue
            s = p.simplify(tol, preserve_topology=True)
            s = set_precision(s, prec)
            for q in parts(s.buffer(0)) if not s.is_valid else parts(s):
                if q.area < minarea or q.is_empty:
                    continue
                q = orient(q, sign=-1.0)
                out.append(q)
        return out
    w = web(0.22, 0.35, 0.1)
    geo = {"type": "Feature", "properties": {"age": age},
           "geometry": mapping(MultiPolygon(w))}
    jsave(geo, f"{COASTD}/{age}.json")
    sz = os.path.getsize(f"{COASTD}/{age}.json")
    assert sz < 150_000, (age, sz)
    f2 = web(0.06, 0.02, 0.01)
    fine[age] = mapping(MultiPolygon(f2))
    stats[age]["web_kb"] = round(sz / 1024, 1)
    print(age, stats[age], len(w), "polys")
jsave(fine, f"{WORK}/coast_fine.json")
jsave({"ages": AGES, "stats": stats}, f"{WORK}/coast_stats.json", indent=1)
