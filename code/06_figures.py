"""Static figures: header.png (1200 x 630), paper figures (release/paper/f_*.png) and blog figures (release/blog/b_*.png,
the same drawings, hard-linked). All numbers from data/results.json and data/site.json."""
import shutil
from matplotlib.patches import Rectangle, Patch
from matplotlib.lines import Line2D
from figlib import *

R = jload(f"{DATA}/results.json"); SITE = jload(f"{DATA}/site.json")
PAP = os.path.join(ROOT, "release", "paper"); BLOG = os.path.join(ROOT, "release", "blog")
for d in (PAP, BLOG):
    os.makedirs(d, exist_ok=True)
ORDER = R["group_order"]
BW, NB = SITE["binw"], SITE["bins"]
PAN = {a: p for a, p in SITE["pangaea"]}
per = lambda a: next(p[0] for p in PERIODS if p[3] <= a <= p[2]) if a > 0 else "Today"


def out(fig, name, dpi=200):
    save(fig, f"{PAP}/f_{name}.png", dpi)
    dst = f"{BLOG}/b_{name}.png"
    if os.path.exists(dst):
        os.remove(dst)
    os.link(f"{PAP}/f_{name}.png", dst)


def legend_groups(fig, keys, y, x0=.05, ncol=4, fs=10.5, full=True, w=.9):
    h = [Line2D([], [], marker="o", ls="", ms=8, mfc=GC[k], mec="white", mew=.6, label=G[k]["name"] if full else G[k]["short"]) for k in keys]
    fig.legend(handles=h, loc="upper left", bbox_to_anchor=(x0, y, w, .01), ncol=ncol, frameon=False, fontsize=fs, handletextpad=.3,
               columnspacing=1.2, labelspacing=.5, mode="expand")


# ------------------------------------------------------------------ header (social card)
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=BG)
fig.text(.045, .86, "Life on the", fontproperties=DISP, fontsize=50, color=FG, va="top")
fig.text(.045, .72, "moving map", fontproperties=DISP, fontsize=50, color=HOT, va="top")
fig.text(.045, .53, f"{R['records']['n']:,} fossil finds of {R['records']['n_groups']} animal\ngroups, from trilobites to hominids,\nput back where they lived on the\ndrifting continents, 540 million\nyears to today.",
         fontproperties=SERP, fontsize=17, color=FG, va="top", linespacing=1.45)
fig.text(.045, .07, "maps.tristanhotham.com/deep-time-life", family=MONO, fontsize=12, color=MUT)
ax = fig.add_axes([.40, .08, .59, .84]); world(ax, 200, grat=True); dots(ax, 200, scale=.9)
ax.text(0, -8.0e6, "200 million years ago: Pangaea", ha="center", fontsize=12, color=FG, family=MONO)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100, facecolor=BG); plt.close(fig)

# ------------------------------------------------------------------ 1. small multiples
AG6 = [500, 300, 200, 150, 66, 0]
fig = plt.figure(figsize=(12, 12.4), facecolor=BG)
present = set()
for i, a in enumerate(AG6):
    y0 = .705 - (i // 2) * .265
    ax = fig.add_axes([.01 + (i % 2) * .495, y0, .48, .232])
    world(ax, a); dots(ax, a, scale=.55)
    fr = frame(a); present |= {GK[c[0]] for c in fr["cells"]}
    t = "Today" if a == 0 else f"{a} million years ago"
    fig.text(.03 + (i % 2) * .495, y0 + .252, t, fontproperties=DISP6, fontsize=15, color=FG, va="bottom")
    fig.text(.03 + (i % 2) * .495, y0 + .236, f"{per(a) if a else 'Quaternary'}, largest land mass {PAN[a]:.0f}% of land", fontsize=9.5, color=MUT, va="bottom")
legend_groups(fig, [k for k in ORDER if k in present], .165, ncol=3, fs=9.5)
out(fig, "multiples")

# ------------------------------------------------------------------ 2. Pangaea index
P = sorted(SITE["pangaea"], key=lambda r: -r[0])
fig, ax = plt.subplots(figsize=(10, 4.4), facecolor=BG); ax.set_facecolor(BG)
ax.axvspan(R["pangaea"]["first_over_85"], R["pangaea"]["last_over_85"], color=GOLD, alpha=.14, lw=0)
ax.text((R["pangaea"]["first_over_85"] + R["pangaea"]["last_over_85"]) / 2, 97, "Pangaea", ha="center", va="top", fontsize=11, color=FG)
ax.fill_between([p[0] for p in P], [p[1] for p in P], color=COOL, alpha=.13, lw=0)
ax.plot([p[0] for p in P], [p[1] for p in P], color=COOL, lw=2.2)
for _, n, a in EXTINCTIONS:
    ax.axvline(a, color=HOT, lw=1, ls=(0, (3, 3)), alpha=.8)
ax.plot([R["pangaea"]["peak_age"]], [R["pangaea"]["peak_pct"]], "o", color=COOL); ax.text(R["pangaea"]["peak_age"] - 5, R["pangaea"]["peak_pct"] + 2.5, f"{R['pangaea']['peak_pct']}% at {R['pangaea']['peak_age']} Ma", fontsize=10, color=FG)
ax.plot([0], [R["pangaea"]["today_pct"]], "o", color=COOL); ax.text(8, R["pangaea"]["today_pct"] + 5, f"today {R['pangaea']['today_pct']}%", fontsize=10, ha="right", color=FG)
ax.set_xlim(540, 0); ax.set_ylim(0, 100); style(ax); ax.set_ylabel("share of all land in the largest land mass, %")
period_band(ax, -14, 7, fs=8); ax.set_xlabel("million years ago", labelpad=22)
fig.tight_layout(); out(fig, "pangaea")

# ------------------------------------------------------------------ 3. swim lanes
fig = plt.figure(figsize=(10, 8.4), facecolor=BG); ax = fig.add_axes([.2, .1, .78, .87]); ax.set_facecolor(BG)
mid = np.arange(NB) * BW + BW / 2
for j, k in enumerate(ORDER):
    s = np.array(SITE["gen"][k], float); y0 = len(ORDER) - 1 - j
    ax.fill_between(mid, y0, y0 + .9 * s / max(1, s.max()), color=GC[k], lw=0, step="mid")
    ax.axhline(y0, color=RULE, lw=.6)
    ax.text(545, y0 + .3, G[k]["short"], ha="right", va="center", fontsize=9.5, color=FG)
for _, n, a in EXTINCTIONS:
    ax.axvline(a, color=HOT, lw=1, ls=(0, (3, 3)))
ax.set_xlim(540, 0); ax.set_ylim(-1.2, len(ORDER)); ax.set_yticks([]); style(ax, grid=False); ax.spines["left"].set_visible(False)
period_band(ax, -1.15, .8, fs=8); ax.set_xlabel("million years ago")
out(fig, "lanes")

# ------------------------------------------------------------------ 4. dinosaur genera
A = np.array(SITE["dino_bins"]) + BW / 2; keys = ["the", "sau", "orn", "din"]
fig, ax = plt.subplots(figsize=(10, 4.6), facecolor=BG); ax.set_facecolor(BG)
ax.stackplot(A, *[SITE["dino"][k] for k in keys], colors=[GC[k] for k in keys], labels=[G[k]["short"] for k in keys], alpha=.92, step=None)
ax.plot(A, SITE["dino"]["ave"], color=GC["ave"], lw=2.4, ls=(0, (5, 3)), label="Birds")
for _, n, a in EXTINCTIONS:
    if a <= 240:
        ax.axvline(a, color=HOT, lw=1, ls=(0, (3, 3)))
ax.set_xlim(240, 60); style(ax); ax.set_ylabel("genera per 5 million years")
ymax = ax.get_ylim()[1]; period_band(ax, -ymax * .14, ymax * .07, x0=240, x1=60, fs=8); ax.set_ylim(0, ymax)
ax.legend(loc="upper left", frameon=False, fontsize=10); ax.set_xlabel("million years ago", labelpad=22)
fig.tight_layout(); out(fig, "dinos")

# ------------------------------------------------------------------ 5. dinosaurs on Pangaea and after
fig = plt.figure(figsize=(12, 7.2), facecolor=BG)
for i, (a, nm) in enumerate(((210, "Late Triassic"), (150, "Late Jurassic"), (70, "Late Cretaceous"))):
    ax = fig.add_axes([.005 + i * .333, .52, .325, .44]); world(ax, a); dots(ax, a, groups=DINO, scale=.9)
    ax.set_title(f"{a} million years ago, {nm}", fontsize=11, color=FG, pad=2)
ax = fig.add_axes([.07, .1, .6, .34]); ax.set_facecolor(BG)
D = R["dino"]["intervals"]; xs = np.arange(len(D))
ax.bar(xs, [d["multi_pct"] for d in D], color=GC["sau"], alpha=.85, width=.62)
for x, d in zip(xs, D):
    ax.text(x, d["multi_pct"] + .5, f"{d['multi_pct']}%", ha="center", fontsize=9.5)
ax.set_xticks(xs, [d["name"].replace(" ", "\n") for d in D], fontsize=9); style(ax); ax.set_ylabel("genera on 2+ continents, %"); ax.set_ylim(0, 20)
a2 = ax.twinx(); a2.plot(xs, [d["pangaea_pct"] for d in D], color=GOLD, lw=2.2, marker="o"); a2.set_ylim(0, 100); a2.set_ylabel("largest land mass, % of land", color=GOLD)
for s in ("top",): a2.spines[s].set_visible(False)
a2.tick_params(colors=GOLD, labelsize=9)
h = [Line2D([], [], marker="o", ls="", ms=8, mfc=GC[k], mec="white", label=G[k]["short"]) for k in DINO]
fig.legend(handles=h, loc="upper left", bbox_to_anchor=(.76, .42), frameon=False, fontsize=10.5)
out(fig, "cosmo")

# ------------------------------------------------------------------ 6. two addresses: then and today, 300 Ma
fig = plt.figure(figsize=(12, 3.9), facecolor=BG)
for i, (today, t) in enumerate(((False, "Where they lived, 300 million years ago"), (True, "Where the same fossils are found today"))):
    ax = fig.add_axes([.005 + i * .5, .04, .49, .84]); world(ax, 0 if today else 300); dots(ax, 300, scale=1.5, today=today)
    ax.set_title(t, fontsize=12, color=FG, pad=3)
out(fig, "twoaddresses")

# ------------------------------------------------------------------ 7. latitude
LG = ["tri", "amm", "ins", "the", "orn", "mam"]
fig, axs = plt.subplots(2, 3, figsize=(12, 6.4), facecolor=BG, sharey=True)
for ax, k in zip(axs.flat, LG):
    ax.set_facecolor(BG); D = sorted(SITE["lat"][k], key=lambda r: -r[0])
    ax.axhspan(-23.44, 23.44, color=GOLD, alpha=.09, lw=0); ax.axhline(0, color=MUT, lw=.8)
    segs, cur = [], []
    for d in D:
        if cur and abs(cur[-1][0] - d[0]) > 10.5:
            segs.append(cur); cur = []
        cur.append(d)
    if cur: segs.append(cur)
    for s in segs:
        s = np.array(s)
        ax.fill_between(s[:, 0], s[:, 1], s[:, 3], color=GC[k], alpha=.25, lw=0); ax.plot(s[:, 0], s[:, 2], color=GC[k], lw=2)
    ax.set_xlim(540, 0); ax.set_ylim(-90, 90); ax.set_yticks([-60, -30, 0, 30, 60]); style(ax)
    ax.set_title(f"{G[k]['short']}, median {R['lat'][k]:.0f} degrees", fontsize=10.5, color=FG, loc="left")
for ax in axs[:, 0]:
    ax.set_ylabel("palaeo-latitude")
for ax in axs[1]:
    ax.set_xlabel("million years ago")
fig.tight_layout(); out(fig, "latitude")

# ------------------------------------------------------------------ 8. extinctions
fig, axs = plt.subplots(2, 3, figsize=(13, 7.6), facecolor=BG)
axs = axs.flat; axs[5].axis("off")
for ax, e in zip(axs, R["extinctions"]):
    ax.set_facecolor(BG); rows = sorted(e["by_group"].items(), key=lambda r: r[1]["lost_pct"])[-7:]
    ax.barh(range(len(rows)), [r[1]["lost_pct"] for r in rows], color=[GC[r[0]] for r in rows], height=.62)
    ax.set_yticks(range(len(rows)), [f"{G[r[0]]['short']} ({r[1]['standing']})" for r in rows], fontsize=8.5)
    ax.axvline(R["ext_bg_median"], color=MUT, ls=(0, (3, 3)), lw=1)
    ax.set_title(f"{e['name']}, {e['age']} Ma\n{e['lost_pct']:.0f}% of {e['standing']} genera last seen", fontsize=10, color=FG, loc="left")
    ax.set_xlim(0, 100); style(ax, axis="x")
axs[3].set_xlabel("% last seen before the extinction"); fig.text(.99, .02, f"dashed: median at other 10 million year steps ({R['ext_bg_median']:.0f}%)", ha="right", fontsize=9, color=MUT)
fig.tight_layout(rect=(0, .04, 1, 1)); out(fig, "extinctions")

# ------------------------------------------------------------------ 9. sampling
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 4.2), facecolor=BG, gridspec_kw={"width_ratios": [1, 1.4]})
C = [c for c in R["sampling"]["by_continent"] if c["name"] != "Ocean"][::-1]
a1.set_facecolor(BG); a1.barh([c["name"] for c in C], [c["pct"] for c in C], color=[HOT if c["name"] in ("North America", "Europe") else MUT for c in C])
for i, c in enumerate(C):
    a1.text(c["pct"] + .6, i, f"{c['pct']}%", va="center", fontsize=9.5)
style(a1, axis="x"); a1.set_xlabel("share of occurrences, %"); a1.set_title("Where the finds are today", loc="left", fontsize=11)
a2.set_facecolor(BG)
v = np.array([np.nan if x is None else x for x in SITE["na_eu_bin"]], float); n = np.array(SITE["coll"]); v[n < 20] = np.nan
a2.plot(mid, v, color=HOT, lw=1.8); a2.axhline(R["sampling"]["na_eu_land_pct"], color=MUT, ls=(0, (4, 3)))
a2.text(5, R["sampling"]["na_eu_land_pct"] - 7, "their share of the land", ha="right", fontsize=9, color=MUT)
a2.set_xlim(540, 0); a2.set_ylim(0, 100); style(a2); a2.set_title("North America and Europe, share of finds per 5 million years", loc="left", fontsize=11)
period_band(a2, -14, 7, fs=7); a2.set_xlabel("million years ago", labelpad=20)
fig.tight_layout(); out(fig, "sampling")
print("figures", sorted(os.listdir(PAP)))
