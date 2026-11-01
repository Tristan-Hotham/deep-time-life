# Life on the moving map

An interactive map of the Earth through 540 million years: the continents drifting, Pangaea gathering and breaking apart, and 409,895 fossil occurrences of 24 animal groups, from trilobites to dinosaurs, whales and hominids, plotted where they lived. Fossils from the Paleobiology Database, with palaeo-positions and continental outlines from the PALEOMAP plate model (C. R. Scotese) via the GPlates Web Service.

Interactive page: https://maps.tristanhotham.com/deep-time-life/
Paper: {https://doi.org/10.5281/zenodo.23856870}
Blog post: {https://blog.tristanhotham.com/2026/10/31/deep-time-life/}

## Headline results

- The share of all land joined in the largest single land mass was above 85% from 270 to 180 million years ago, peaking at 90.2% at 180 million years ago (Pangaea). It fell to 23.1% by 100 million years ago; today it is 54.4% (Africa with Eurasia).
- By share of distinct genera in these groups, trilobites lead the Paleozoic (56.8%), insects the Mesozoic (41.7%) and mammals the Cenozoic (39.3%).
- 11.3% of dinosaur genera from the Late Triassic and Early Jurassic (Pangaea) are found on more than one present-day continent, against 5.1% of Cretaceous genera.
- Genera last seen in the 10 million years before each extinction: end-Permian 74.4%, end-Cretaceous 56.7% (every non-bird dinosaur, plesiosaur and mosasaur genus), end-Triassic 33.2%, against a median of 36.8% at other times.
- Sampling: 65.6% of occurrences come from North America and Europe, which hold 32.2% of the land; the United States alone 27.7%. Counts are records, not abundance.

## Groups

| Group | Occurrences | Genera | Oldest to youngest (Ma, midpoints, ignoring the extreme 0.2%) |
|---|---|---|---|
| Trilobites | 53,823 | 2,674 | 518 to 266 |
| Sea scorpions | 595 | 70 | 455 to 280 |
| Armoured fish | 1,004 | 272 | 429 to 353 |
| Ammonites | 85,962 | 2,790 | 399 to 69 |
| Sharks and rays | 24,821 | 632 | 338 to 0 |
| Temnospondyls | 1,738 | 280 | 333 to 120 |
| Insects | 50,489 | 12,832 | 318 to 0 |
| Early synapsids | 3,137 | 564 | 309 to 117 |
| Ichthyosaurs | 669 | 87 | 250 to 97 |
| Other dinosaurs | 1,596 | 44 | 248 to 69 |
| Theropods | 8,035 | 693 | 242 to 69 |
| Crocodile relatives | 5,397 | 401 | 232 to 0 |
| Sauropods | 3,842 | 380 | 232 to 69 |
| Ornithischians | 6,758 | 471 | 232 to 69 |
| Pterosaurs | 1,105 | 202 | 232 to 69 |
| Turtles | 10,839 | 572 | 216 to 0 |
| Plesiosaurs | 1,138 | 130 | 207 to 69 |
| Frogs and salamanders | 4,229 | 239 | 192 to 0 |
| Mammals | 116,607 | 5,648 | 149 to 0 |
| Birds | 16,205 | 1,421 | 124 to 0 |
| Mosasaurs | 832 | 44 | 97 to 67 |
| Elephants | 4,322 | 61 | 50 to 0 |
| Whales | 6,138 | 440 | 45 to 0 |
| Hominids | 614 | 21 | 18 to 0 |

## Files

| File | What it is |
|---|---|
| `index.html` | The interactive page (built by `code/05_build_site.py`): canvas map in the Equal Earth projection with d3-geo, time slider and play, layers panel, full-screen button, genus search, charts. |
| `header.png` | Social card, 1200 x 630. |
| `data/coast/<age>.json` | PALEOMAP outlines merged into land masses and simplified, one GeoJSON file per age (66 ages, under 100 KB each). |
| `data/frames/<age>.json` | Fossils of each map frame, binned by group into 1 degree cells of palaeo-latitude and longitude: counts, palaeo and present positions, place, ages, taxon ids (3,312 KB in all). |
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

- Occurrences of 23 named taxa from the PBDB data service (`occs/list.json?base_name=<taxon>&show=coords,paleoloc,class&pgm=scotese&pgs=mid`), 480,977 rows. Overlapping queries resolved by keeping each occurrence in its most specific group; three query problems corrected (an insect homonym of Proboscidea; Lissamphibia inside Temnospondyli, split off; bird orders under non-avian theropods, moved to birds).
- Ages: midpoint of each collection's range; ranges over 25 million years left out. Palaeo-positions: PALEOMAP at the collection's midpoint (present position for collections under 1 million years old without one).
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

Hotham, T. (2026) Life on the moving map: 540 million years of animal fossils on the drifting continents, from the Paleobiology Database and the PALEOMAP plate model. Zenodo. {https://doi.org/10.5281/zenodo.23856870}

Dr Tristan Hotham, Independent researcher. ORCID 0000-0003-4931-9349.

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
