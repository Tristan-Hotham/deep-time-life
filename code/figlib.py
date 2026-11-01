"""Shared drawing helpers for the static figures, the header and the collage: fonts (static instances cut from the
variable Fraunces font, written to WORK), colours, the PALEOMAP outlines in the Equal Earth projection, and dots."""
import os, sys
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MPoly
from matplotlib.collections import PatchCollection
from pyproj import Transformer
from shapely.geometry import shape, Polygon, MultiPolygon
from shapely import segmentize
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import *

FD = os.path.join(WORK, "fonts"); os.makedirs(FD, exist_ok=True)
if not os.path.exists(f"{FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, n in ((900, "Black"), (600, "Semibold")):
        instancer.instantiateVariableFont(TTFont(os.path.join(FONTS, "FrauncesVar.ttf")), {"wght": w, "opsz": 144 if w == 900 else 36, "SOFT": 0, "WONK": 0}).save(f"{FD}/Fraunces-{n}.ttf")
DISP = fm.FontProperties(fname=f"{FD}/Fraunces-Black.ttf")
DISP6 = fm.FontProperties(fname=f"{FD}/Fraunces-Semibold.ttf")
SERP = fm.FontProperties(fname=os.path.join(FONTS, "SourceSerif4-Regular.ttf"))
SERB = fm.FontProperties(fname=os.path.join(FONTS, "SourceSerif4-Semibold.ttf"))
SERI = fm.FontProperties(fname=os.path.join(FONTS, "SourceSerif4-It.ttf"))
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(os.path.join(FONTS, f))
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#6A6570", "axes.labelcolor": "#1F1D22",
                     "xtick.color": "#6A6570", "ytick.color": "#6A6570"})
BG, FG, MUT, RULE, CARD = "#F7F4EE", "#1F1D22", "#6A6570", "#E0D9CC", "#FFFDF8"
HOT, COOL, GOLD = "#B0352B", "#2D6A8E", "#C98A12"
SEA, SEAEDGE, LAND, LANDEDGE, GRAT = "#DCE7EB", "#B9CBD3", "#E6D8BC", "#BFA982", "#C9D8DE"
GC = {k: G[k]["c"] for k in GK}
tr = Transformer.from_crs("+proj=longlat +datum=WGS84", "+proj=eqearth +datum=WGS84", always_xy=True)
EXT_WORLD = (-17.25e6, 17.25e6, -8.45e6, 8.45e6)
_FINE = None


def fine():
    global _FINE
    if _FINE is None:
        _FINE = jload(f"{WORK}/coast_fine.json")
    return _FINE


def proj_xy(lon, lat):
    return tr.transform(np.clip(np.asarray(lon, float), -179.999, 179.999), np.clip(np.asarray(lat, float), -89.999, 89.999))


def rings_of(geom):
    g = shape(geom)
    for p in (g.geoms if isinstance(g, MultiPolygon) else [g]):
        p = segmentize(p, 1.0)
        yield np.array(p.exterior.coords), [np.array(h.coords) for h in p.interiors]


def sphere_outline(n=361):
    lat = np.linspace(-90, 90, n)
    xs, ys = proj_xy(np.r_[np.full(n, 180), np.full(n, -180)], np.r_[lat, lat[::-1]])
    return np.column_stack([xs, ys])


def world(ax, age, sea=SEA, land=LAND, edge=LANDEDGE, lw=.35, grat=True, outline=True):
    ax.add_patch(MPoly(sphere_outline(), closed=True, fc=sea, ec="none", zorder=0))
    if grat:
        for lat in (-60, -30, 0, 30, 60):
            x, y = proj_xy(np.linspace(-180, 180, 181), np.full(181, lat))
            ax.plot(x, y, color=GRAT, lw=.5 if lat else .8, zorder=1, ls=(0, (3, 3)) if lat in (-30, 30) else "-")
        for lon in range(-150, 181, 30):
            x, y = proj_xy(np.full(181, lon), np.linspace(-90, 90, 181))
            ax.plot(x, y, color=GRAT, lw=.4, zorder=1)
    patches = []
    for ext, holes in rings_of(fine()[str(age)]):
        x, y = proj_xy(ext[:, 0], ext[:, 1])
        patches.append(MPoly(np.column_stack([x, y]), closed=True))
    ax.add_collection(PatchCollection(patches, fc=land, ec=edge, lw=lw, zorder=2))
    if outline:
        o = sphere_outline(); ax.plot(o[:, 0], o[:, 1], color=SEAEDGE, lw=.8, zorder=3)
    ax.set_xlim(EXT_WORLD[0], EXT_WORLD[1]); ax.set_ylim(EXT_WORLD[2], EXT_WORLD[3]); ax.set_aspect("equal"); ax.axis("off")


def frame(age):
    return jload(f"{DATA}/frames/{age}.json")


def dots(ax, age, groups=None, scale=1.0, alpha=.9, edge="white", ew=.35, today=False, zorder=5):
    fr = frame(age)
    cells = [c for c in fr["cells"] if groups is None or GK[c[0]] in groups]
    if not cells:
        return 0
    lon = [c[5] if today else c[1] for c in cells]; lat = [c[6] if today else c[2] for c in cells]
    x, y = proj_xy(lon, lat)
    s = [scale * (1.6 + 1.25 * np.log10(1 + c[3])) ** 2 for c in cells]
    col = [GC[GK[c[0]]] for c in cells]
    ax.scatter(x, y, s=s, c=col, alpha=alpha, lw=ew, edgecolors=edge, zorder=zorder)
    return len(cells)


def style(ax, grid=True, axis="y"):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUT)
    ax.tick_params(colors=FG, labelsize=10)
    if grid:
        ax.grid(axis=axis, color=RULE, lw=.8); ax.set_axisbelow(True)


def period_band(ax, y0, h, x0=540, x1=0, fs=8, labels=True):
    for name, ab, old, young, c in PERIODS:
        lo, hi = max(min(old, x0), x1), max(min(young, x0), x1)
        if lo <= hi:
            continue
        ax.add_patch(matplotlib.patches.Rectangle((lo, y0), hi - lo, h, fc=c, ec="white", lw=.6, clip_on=False, zorder=4))
        if labels:
            wd = lo - hi
            nm = name if wd > len(name) * (x0 - x1) / 95 else ab if wd > (x0 - x1) / 60 else ""
            ax.text((lo + hi) / 2, y0 + h / 2, nm, ha="center", va="center", fontsize=fs, color="#fff" if name in ("Triassic", "Ordovician", "Permian") else "#222",
                    clip_on=False, zorder=5)


def save(fig, path, dpi=200):
    fig.savefig(path, dpi=dpi, facecolor=fig.get_facecolor())
    plt.close(fig)
