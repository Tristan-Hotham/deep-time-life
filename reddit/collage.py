"""r/dataisbeautiful collage for deep-time-life: 2400 x 3200 px, light background. Six snapshots of the world with fossil
finds by group, a full legend, and a strip of each group's share of all genera through time. Numbers from
data/results.json and the page data; all labels sit on the paper, outside the maps."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "code"))
from figlib import *
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
PAN = {a: p for a, p in SITE["pangaea"]}
ORDER = R["group_order"]
FH = 19.2
fig = plt.figure(figsize=(12, FH), dpi=200, facecolor=BG)
Y = lambda inch: 1 - inch / FH          # inches from the top to figure fraction
fig.text(.045, Y(.35), "Life on the moving map", fontproperties=DISP, fontsize=54, color=FG, va="top")
fig.text(.045, Y(1.3), f"{R['records']['n']:,} fossil finds of {R['records']['n_groups']} animal groups from the Paleobiology Database, each put back\n"
         "where it lived on the drifting continents (PALEOMAP plate model). Six moments from 540 million years.",
         fontproperties=SERP, fontsize=15.5, color=FG, va="top", linespacing=1.3)

AG = [(500, "Cambrian"), (300, "Carboniferous"), (200, "Earliest Jurassic"), (150, "Late Jurassic"), (66, "End of the Cretaceous"), (0, "Last 5 million years")]
present = set()
for i, (a, nm) in enumerate(AG):
    col, row = i % 2, i // 2
    top_in = 2.3 + row * 3.95
    ax = fig.add_axes([.012 + col * .494, Y(top_in + .9 + 2.84), .482, 2.84 / FH])
    world(ax, a, lw=.3); dots(ax, a, scale=1.1, ew=.3)
    fr = frame(a); present |= {GK[c[0]] for c in fr["cells"]}
    top = sorted(range(len(GK)), key=lambda j: -fr["byg"][j])[:3]
    head = "Today" if a == 0 else f"{a} million years ago"
    x = .045 + col * .494
    fig.text(x, Y(top_in), head, fontproperties=DISP6, fontsize=17, color=FG, va="top")
    land = f"largest land mass {PAN[a]:.0f}% of all land" + (": Pangaea" if PAN[a] >= 85 else "")
    fig.text(x, Y(top_in + .36), f"{nm}. Most finds: {', '.join(G[GK[j]]['short'].lower() for j in top)}\n{land}", fontsize=9.5, color=MUT, va="top", linespacing=1.4)

# legend, full names, in order of first appearance
keys = [k for k in ORDER if k in present]
h = [Line2D([], [], marker="o", ls="", ms=9, mfc=G[k]["c"], mec="white", mew=.6, label=G[k]["name"]) for k in keys]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(.035, Y(14.15), .94, .001), ncol=3, frameon=False, fontsize=9.6, handletextpad=.25,
           columnspacing=.8, labelspacing=.55, mode="expand", prop={"family": MONO, "size": 9.6})

# timeline strip: share of all genera per 5 million years
ax = fig.add_axes([.045, Y(17.75), .91, .6 / FH]); ax.set_facecolor(BG)
BW, NB = SITE["binw"], SITE["bins"]
mid = np.arange(NB) * BW + BW / 2
tot = np.array([sum(SITE["gen"][k][b] for k in GK) for b in range(NB)], float)
ok = tot >= 5
bottom = np.zeros(NB)
for k in ORDER:
    v = np.where(ok, np.array(SITE["gen"][k], float) / np.maximum(tot, 1), 0)
    ax.fill_between(mid, bottom, bottom + v, step="mid", color=G[k]["c"], lw=0)
    bottom += v
for i, (_, n, a) in enumerate(EXTINCTIONS):
    ax.axvline(a, color=FG, lw=1.1, ls=(0, (2, 2)))
    ax.plot([a, a], [-.42, -.5 - .3 * (i % 2)], color=HOT, lw=.8, clip_on=False)
    ax.text(a, -.52 - .3 * (i % 2), f"{n.replace('End-', 'end-')} {a}", ha="center", va="top", fontsize=8.3, color=HOT)
ax.set_xlim(540, 0); ax.set_ylim(0, 1); ax.axis("off")
period_band(ax, -.32, .26, fs=8)
for name, hi, lo, _ in ERAS:
    L = R["leaders"][name]
    xx, ha = ((min(hi, 540) + lo) / 2, "center") if name != "Cenozoic" else (0, "right")
    ax.text(xx, 1.08, f"{name}: {G[L['k']]['short'].lower()} {L['pct']:.0f}%", ha=ha, va="bottom", fontsize=10, color=FG)
fig.text(.045, Y(16.38), "Which groups dominated the record: each group's share of all genera found in each 5 million years.\nAbove: the leading group in each era. Dashed: the five mass extinctions. Gap: no collection midpoints fall in 225 to 230 Ma.",
         fontsize=10, color=FG, va="top", linespacing=1.4)

fig.text(.045, Y(19.12), f"Source: The Paleobiology Database (paleobiodb.org, CC BY 4.0), data accessed 2026; palaeo-positions and coastlines from PALEOMAP (C. R. Scotese) via the\n"
         f"GPlates Web Service (EarthByte). Dots: 1 degree squares of finds within 5 million years of each moment. Counts follow where rock is exposed and\n"
         f"who has looked ({R['sampling']['na_eu_pct']:.0f}% of finds are from North America and Europe), not abundance.  "
         "Chart: Tristan Hotham  ·  maps.tristanhotham.com/deep-time-life", family=MONO, fontsize=8.3, color=MUT, linespacing=1.5, va="bottom")
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "life_on_the_moving_map.png")
fig.savefig(out, facecolor=BG, dpi=200)
print("ok", out)
