"""Blog post and meta (release/blog), README.md and LICENSE, Zenodo files and metadata (release/zenodo), and the Reddit
post (reddit/post.md). Numbers are filled from data/results.json; 10.5281/zenodo.23856870, https://doi.org/10.5281/zenodo.23856870 and https://blog.tristanhotham.com/2026/10/31/deep-time-life/ are left for
the publisher. Zenodo copies of files that also live elsewhere in the repo are hard links."""
import re, zipfile, json as _json
import importlib.util
from common import *

R = jload(f"{DATA}/results.json")
REL = os.path.join(ROOT, "release")
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py")); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
B.checks(R)
# facts stated in words in the blog and its alt text
ex = {e["k"]: e for e in R["extinctions"]}
assert round(ex["eor"]["by_group"]["tri"]["lost_pct"]) == 62
assert all(64.5 <= ex["lde"]["by_group"][k]["lost_pct"] <= 70.5 for k in ("amm", "tri", "pla"))
assert round(ex["epe"]["by_group"]["syn"]["lost_pct"]) == 87 and round(ex["epe"]["by_group"]["amm"]["lost_pct"]) == 84 and round(ex["etr"]["by_group"]["amm"]["lost_pct"]) == 74
bc = {c["name"]: c["pct"] for c in R["sampling"]["by_continent"]}
assert (round(bc["North America"]), round(bc["Europe"]), round(bc["Asia"]), bc["Africa"], bc["South America"], round(bc["Oceania"])) == (36, 30, 16, 8.5, 6.5, 3) and bc["Antarctica"] < 1
assert round(R["sampling"]["na_eu_land_pct"]) == 32 and 74 <= R["dino"]["peak_na_pct"] <= 76 and R["dino"]["peak_genera"] > 300
assert all(10 <= d["multi_pct"] <= 16 for d in R["dino"]["intervals"][:4]) and all(4.5 <= d["multi_pct"] <= 5.5 for d in R["dino"]["intervals"][4:])
assert 21 <= R["pangaea"]["at"]["100"] <= 25 and 5 <= R["facts"]["trex_mt_dlat"] <= 9

# ------------------------------------------------------------------ blog
post = fill(open(os.path.join(ROOT, "code", "blog_template.html"), encoding="utf-8").read(), R)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, used
for img in used:
    assert os.path.exists(f"{REL}/blog/{img}"), img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
for ln in post.splitlines():
    if "{{IMG|" in ln:
        assert ln.startswith("{{IMG|") and ln.endswith("}}"), ln[:60]
check_text(re.sub(r"<!--.*?-->", "", post, flags=re.S), "blog")
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]+\}\}", " ", re.sub(r"<!--.*?-->", "", post, flags=re.S)).split())
meta = {"title": "Life on the moving map: 540 million years of animals on the drifting continents",
        "slug": SLUG,
        "excerpt": f"I put {R['records']['n']:,} fossil finds, from trilobites to dinosaurs to hominids, back where they lived on the drifting continents. Watch Pangaea form and break apart, see who ruled when, and why {R['sampling']['na_eu_pct']:.0f}% of the finds come from North America and Europe.",
        "seo_description": "An interactive map of the Earth through 540 million years: drifting continents, Pangaea, and fossil animals from trilobites to dinosaurs where they lived.",
        "tags": ["deep time", "fossils", "palaeontology", "Pangaea", "dinosaurs", "plate tectonics", "mass extinctions", "maps", "data visualisation"],
        "header_alt": "Title card reading 'Life on the moving map' in black and red on cream paper, with the line: 409,895 fossil finds of 24 animal groups, from trilobites to hominids, put back where they lived on the drifting continents, 540 million years to today. Beside it a world map 200 million years ago showing the supercontinent Pangaea in sand on pale blue sea, dotted with coloured fossil finds."}
assert len(meta["seo_description"]) < 160 and str(f"{R['records']['n']:,}") in meta["header_alt"] and str(R["records"]["n_groups"]) in meta["header_alt"]
jsave(meta, f"{REL}/blog/meta.json", indent=2)

# ------------------------------------------------------------------ README and LICENSE
gt = "\n".join(f"| {R['groups'][k]['short']} | {R['groups'][k]['n']:,} | {R['groups'][k]['genera']:,} | {R['groups'][k]['first']:.0f} to {R['groups'][k]['last']:.0f} |" for k in R["group_order"])
readme = f"""# Life on the moving map

An interactive map of the Earth through 540 million years: the continents drifting, Pangaea gathering and breaking apart, and {R['records']['n']:,} fossil occurrences of {R['records']['n_groups']} animal groups, from trilobites to dinosaurs, whales and hominids, plotted where they lived. Fossils from the Paleobiology Database, with palaeo-positions and continental outlines from the PALEOMAP plate model (C. R. Scotese) via the GPlates Web Service.

Interactive page: {PAGE_URL}
Paper: {{https://doi.org/10.5281/zenodo.23856870}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/deep-time-life/}}

## Headline results

- The share of all land joined in the largest single land mass was above 85% from {R['pangaea']['first_over_85']} to {R['pangaea']['last_over_85']} million years ago, peaking at {R['pangaea']['peak_pct']}% at {R['pangaea']['peak_age']} million years ago (Pangaea). It fell to {R['pangaea']['at']['100']}% by 100 million years ago; today it is {R['pangaea']['today_pct']}% (Africa with Eurasia).
- By share of distinct genera in these groups, trilobites lead the Paleozoic ({R['leaders']['Paleozoic']['pct']}%), insects the Mesozoic ({R['leaders']['Mesozoic']['pct']}%) and mammals the Cenozoic ({R['leaders']['Cenozoic']['pct']}%).
- {R['dino']['multi_pangaea']['pct']}% of dinosaur genera from the Late Triassic and Early Jurassic (Pangaea) are found on more than one present-day continent, against {R['dino']['multi_cretaceous']['pct']}% of Cretaceous genera.
- Genera last seen in the 10 million years before each extinction: end-Permian {ex['epe']['lost_pct']}%, end-Cretaceous {ex['ecr']['lost_pct']}% (every non-bird dinosaur, plesiosaur and mosasaur genus), end-Triassic {ex['etr']['lost_pct']}%, against a median of {R['ext_bg_median']}% at other times.
- Sampling: {R['sampling']['na_eu_pct']}% of occurrences come from North America and Europe, which hold {R['sampling']['na_eu_land_pct']}% of the land; the United States alone {R['sampling']['usa_pct']}%. Counts are records, not abundance.

## Groups

| Group | Occurrences | Genera | Oldest to youngest (Ma, midpoints, ignoring the extreme 0.2%) |
|---|---|---|---|
{gt}

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`): canvas map in the Equal Earth projection with d3-geo, time slider and play, layers panel, full-screen button, genus search, charts. |
| `header.png` | Social card, 1200 x 630. |
| `data/coast/<age>.json` | PALEOMAP outlines merged into land masses and simplified, one GeoJSON file per age ({R['frames']['n']} ages, under 100 KB each). |
| `data/frames/<age>.json` | Fossils of each map frame, binned by group into 1 degree cells of palaeo-latitude and longitude: counts, palaeo and present positions, place, ages, taxon ids ({R['frames']['kb_total']:,} KB in all). |
| `data/names.json`, `data/places.json` | Lookup tables for the frames: taxon names (with group, occurrences and age span) and present-day places. |
| `data/collections.csv.gz` | One row per collection and group: occurrences, age range and midpoint, present and palaeo coordinates, country, province, genera. |
| `data/genera.csv` | Every genus: group, occurrences, collections, continents, oldest and youngest midpoint age. |
| `data/groups_through_time.csv` | Genera and occurrences per group per 5 million years. |
| `data/latitude_bands.csv` | Palaeo-latitude of collections per group per 10 million years (10th, 50th, 90th percentiles). |
| `data/pangaea_index.csv` | Land area, largest land mass and its share at each outline age. |
| `data/extinctions.csv` | The last-appearance measure at the five mass extinctions. |
| `data/results.json` | Every number used in the page, paper, blog and collage. `data/site.json`: chart data for the page. |
| `code/` | Scripts, run in order (below), with page, paper and blog templates. |
| `release/` | Paper PDF and LaTeX source with figures, blog post and figures, Zenodo files. |
| `reddit/` | Collage (`collage.py`, PNG) and post text. |

## Method in brief

- Occurrences of {R['records']['n_queries']} named taxa from the PBDB data service (`occs/list.json?base_name=<taxon>&show=coords,paleoloc,class&pgm=scotese&pgs=mid`), {R['records']['rows_raw']:,} rows. Overlapping queries resolved by keeping each occurrence in its most specific group; three query problems corrected (an insect homonym of Proboscidea; Lissamphibia inside Temnospondyli, split off; bird orders under non-avian theropods, moved to birds).
- Ages: midpoint of each collection's range; ranges over {R['records']['max_range']:.0f} million years left out. Palaeo-positions: PALEOMAP at the collection's midpoint (present position for collections under 1 million years old without one).
- Map frames: midpoints within 5 million years of each outline age (the 10 million years before, at the five extinctions), binned into 1 degree cells per group.
- Pangaea index: outlines merged, gaps under about 0.3 degrees closed, joined across the 180th meridian, areas on a cylindrical equal-area projection.
- Diversity: distinct genera per 5 million years, no sampling correction. Extinctions: genera with at least 2 collections whose youngest midpoint falls in the 10 million years before the boundary, as a share of those standing.
- Caveats: counts follow rock exposure and collecting effort; outlines are present-day coastlines and blocks moved by the plate model, not ancient shorelines; one plate model; midpoint ages blur timing; one 5 million year bin (225 to 230 Ma) has no midpoints.

## How to rerun

Needs Python 3 with pandas, geopandas, shapely 2, pyproj, matplotlib and fontTools; xelatex and pdftotext; node with playwright and d3 7.9.0 (for QA). Raw inputs are read in place (paths in `code/common.py`): `pbdb_occurrences_scotese.tsv`, `paleomap_coastlines_gws.json`, Natural Earth 1:10m countries and provinces. Intermediates go to `/dev/shm/deep-time-life` (set `PALEO_WORK` to change).

```
python3 code/01_occurrences.py   # groups, ages, palaeo-positions, present-day places
python3 code/02_coastlines.py    # web outlines and the Pangaea index
python3 code/03_frames.py        # map frames, names and places
python3 code/04_results.py       # results.json, site.json and the data tables
python3 code/05_build_site.py    # index.html
python3 code/06_figures.py       # header, paper and blog figures
python3 code/07_paper.py         # paper PDF (set DOI=... to print the DOI)
python3 reddit/collage.py        # collage
python3 code/08_release.py       # blog post, README, LICENSE, Zenodo files, Reddit post
node code/11_qa.js               # screenshots and console check
```

## Sources and licences

- The Paleobiology Database (paleobiodb.org), data accessed 2026, data service 1.2 (Peters and McClennen 2016). CC BY 4.0. Cite as "The Paleobiology Database (paleobiodb.org), data accessed 2026".
- PALEOMAP plate model and coastlines: C. R. Scotese, PALEOMAP Project (Scotese 2016; Scotese and Wright 2018), reconstructed with the GPlates Web Service (gws.gplates.org), EarthByte group, University of Sydney (Müller et al. 2018). I could not consult PALEOMAP's own reuse terms from the build environment, so they are not stated here: the simplified outlines in `data/coast/` are shared with full credit, and anyone reusing them should check the PALEOMAP Project's terms.
- Natural Earth countries and states and provinces (public domain).
- Geological time scale after the ICS International Chronostratigraphic Chart, rounded.
- This repository: code MIT; text, figures and derived data CC BY 4.0 (see LICENSE).

## Citation

Hotham, T. (2026) Life on the moving map: 540 million years of animal fossils on the drifting continents, from the Paleobiology Database and the PALEOMAP plate model. Zenodo. {{https://doi.org/10.5281/zenodo.23856870}}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

{AI}
"""
check_text("\n".join(l for l in readme.splitlines() if not re.fullmatch(r"[|\- ]+", l)), "README")
open(os.path.join(ROOT, "README.md"), "w", encoding="utf-8").write(readme)
LIC = """MIT License

Copyright (c) 2026 Tristan Hotham

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.


This licence covers the code in code/, reddit/collage.py and the page scripts.
The text of the page, the paper, the figures and the derived data in data/ are
released under CC BY 4.0 (https://creativecommons.org/licenses/by/4.0/).
The fossil data are derived from The Paleobiology Database (paleobiodb.org),
data accessed 2026, CC BY 4.0, which must be credited when reused. The
continental outlines in data/coast/ are simplified from PALEOMAP coastlines
(C. R. Scotese, PALEOMAP Project) reconstructed with the GPlates Web Service
(EarthByte, University of Sydney); credit them when reused and check the
PALEOMAP Project's terms, which could not be verified when this was built.
Natural Earth is public domain.
"""
open(os.path.join(ROOT, "LICENSE"), "w", encoding="utf-8").write(LIC)

# ------------------------------------------------------------------ Zenodo
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
os.link(f"{REL}/paper/{PAPER_NAME}.pdf", f"{Z}/{PAPER_NAME}.pdf")
zp = f"{Z}/{SLUG}_code_and_data.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for top in ("code", "data"):
        for dp, dn, fns in os.walk(os.path.join(ROOT, top)):
            dn[:] = [x for x in dn if x != "__pycache__"]
            for fn in sorted(fns):
                if fn.endswith(".pyc"):
                    continue
                full = os.path.join(dp, fn); z.write(full, f"{SLUG}/{os.path.relpath(full, ROOT)}")
    for fn in ("README.md", "LICENSE", "index.html"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
tex = open(f"{REL}/paper/{PAPER_NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n\\textbf\{Keywords", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\emph{", "").replace("}", "").replace("\\&", "&")
zmeta = {"title": "Life on the Moving Map: 540 Million Years of Animal Fossils on the Drifting Continents, from the Paleobiology Database and the PALEOMAP Plate Model",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE_URL}\">{PAGE_URL}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/deep-time-life/}}.</p>"
                        "<p>Text, figures and derived data: CC BY 4.0; code: MIT. Fossil data: The Paleobiology Database (paleobiodb.org), data accessed 2026, CC BY 4.0. "
                        "Continental outlines and palaeo-coordinates: PALEOMAP (C. R. Scotese, PALEOMAP Project) via the GPlates Web Service (EarthByte group, University of Sydney); "
                        "PALEOMAP's own reuse terms could not be verified and are credited in full. Present-day places: Natural Earth (public domain).</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["palaeogeography", "fossil record", "Paleobiology Database", "PALEOMAP", "Pangaea", "plate tectonics", "dinosaurs", "mass extinctions", "sampling bias", "data visualisation"],
         "license": "cc-by-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE_URL, "relation": "isSupplementedBy", "resource_type": "other"},
                                 {"identifier": "https://paleobiodb.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://gws.gplates.org/", "relation": "isDerivedFrom", "resource_type": "dataset"},
                                 {"identifier": "https://www.naturalearthdata.com/", "relation": "isDerivedFrom", "resource_type": "dataset"}]}
jsave(zmeta, f"{Z}/metadata.json", indent=2)
s = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
check_text(s, "zenodo/meta")

# ------------------------------------------------------------------ Reddit post
pm = f"""## Title

[OC] Life on the moving map: {R['records']['n']:,} fossils, from trilobites to T. rex to us, put back where they lived on the drifting continents. At its peak {R['pangaea']['peak_age']} million years ago, {R['pangaea']['peak_pct']:.0f}% of all land was one supercontinent

## Body

I took {R['records']['n']:,} fossil occurrences of {R['records']['n_groups']} animal groups from the Paleobiology Database, each with its ancient position from the PALEOMAP plate model, and drew them on the continents of their time. Six moments here: trilobites ring the scattered continents 500 million years ago; Pangaea holds {R['pangaea']['at']['200']:.0f}% of all land at 200; by 66 the Atlantic is open. The strip shows which groups dominate the genera through time: trilobites {R['leaders']['Paleozoic']['pct']:.0f}% of Paleozoic genera, insects {R['leaders']['Mesozoic']['pct']:.0f}% of Mesozoic, mammals {R['leaders']['Cenozoic']['pct']:.0f}% of Cenozoic. Dinosaur genera on Pangaea turn up on more than one of today's continents about twice as often as Cretaceous ones ({R['dino']['multi_pangaea']['pct']:.0f}% vs {R['dino']['multi_cretaceous']['pct']:.0f}%). Big caveat: this maps where rock is exposed and who looked. {R['sampling']['na_eu_pct']:.0f}% of the finds come from North America and Europe. Interactive version with a time slider, a play button and a 'where is this today?' switch: {PAGE_URL}

## Source comment

Source: The Paleobiology Database (paleobiodb.org), data accessed 2026, CC BY 4.0, via the data service with PALEOMAP palaeo-coordinates; PALEOMAP coastlines (C. R. Scotese, PALEOMAP Project) reconstructed with the GPlates Web Service (EarthByte, University of Sydney); Natural Earth (public domain).

Tools: Python (pandas, geopandas, shapely, pyproj, matplotlib); d3-geo and canvas for the interactive map.

Interactive version: {PAGE_URL}
Paper: {{https://doi.org/10.5281/zenodo.23856870}}
Blog post: {{https://blog.tristanhotham.com/2026/10/31/deep-time-life/}}
"""
check_text(pm, "reddit")
open(os.path.join(ROOT, "reddit", "post.md"), "w", encoding="utf-8").write(pm)
print("blog words", words, "| figures", used, "| zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
