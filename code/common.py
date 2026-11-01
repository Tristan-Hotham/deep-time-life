"""Shared paths, groups, time scale and helpers for the deep-time-life study ("Life on the moving map").

Raw inputs (read in place, never copied into the repo):
  OCC    /home/claude/newdata/raw7/paleo/pbdb_occurrences_scotese.tsv
         The Paleobiology Database (paleobiodb.org, data API 1.2, CC BY 4.0), data accessed 2026. Fossil occurrences of
         23 animal groups, one query per group:
           https://paleobiodb.org/data1.2/occs/list.json?base_name=<grp>&show=coords,paleoloc,class&vocab=pbdb&pgm=scotese&pgs=mid
         Columns: grp, occurrence_no, collection_no, accepted_name, accepted_rank, phylum, class, order, family, genus,
         max_ma, min_ma, lng, lat (present day), paleolng, paleolat (PALEOMAP model of C. R. Scotese, rotated by the
         PBDB to each collection's midpoint age), geoplate. 'Theropoda^Aves' means non-bird theropods and
         'Synapsida^Mammalia' non-mammal synapsids. 'Dinosauria' overlaps the three dinosaur subgroups and Aves, and
         'Mammalia' overlaps Cetacea, Proboscidea and Hominidae: every occurrence is kept once, in its most specific group.
  COAST  /home/claude/newdata/raw7/paleo/paleomap_coastlines_gws.json
         {age_Ma: GeoJSON FeatureCollection}: PALEOMAP coastlines (C. R. Scotese, PALEOMAP Project) reconstructed with the
         GPlates Web Service (gws.gplates.org, EarthByte group, University of Sydney; model=PALEOMAP), every 10 Ma from
         0 to 540 Ma plus 5, 23, 34, 56, 66, 94, 145, 201, 252, 372 and 445 Ma.
         Query: https://gws.gplates.org/reconstruct/coastlines/?time=<age>&model=PALEOMAP
  NE     Natural Earth 1:10m admin 0 countries and admin 1 states and provinces (public domain), for the present-day place
         of each fossil: /home/claude/newdata/raw/geo/
Intermediates are written to WORK (outside the repo)."""
import json, gzip, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.environ.get("PALEO_RAW", "/home/claude/newdata/raw7/paleo")
OCC = os.path.join(RAW, "pbdb_occurrences_scotese.tsv")
COAST = os.path.join(RAW, "paleomap_coastlines_gws.json")
GEO = os.environ.get("PALEO_GEO", "/home/claude/newdata/raw/geo")
NE0 = os.path.join(GEO, "ne_10m_admin_0_countries.geojson")
NE1 = os.path.join(GEO, "ne_10m_admin_1_states_provinces.geojson")
FONTS = os.environ.get("FONT_DIR", "/home/claude/ref/fonts")
DATA = os.path.join(ROOT, "data")
FRAMES = os.path.join(DATA, "frames")
COASTD = os.path.join(DATA, "coast")
WORK = os.environ.get("PALEO_WORK", "/dev/shm/deep-time-life")
for d in (DATA, FRAMES, COASTD, WORK):
    os.makedirs(d, exist_ok=True)

SLUG = "deep-time-life"
TITLE = "Life on the moving map"
PAGE_URL = "https://maps.tristanhotham.com/deep-time-life/"
REPO = "https://github.com/Tristan-Hotham/deep-time-life"
PAPER_NAME = "Hotham_Life_on_the_Moving_Map"
ACCESSED = "2026"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
PBDB_CITE = "The Paleobiology Database (paleobiodb.org), data accessed 2026"

# ---------------------------------------------------------------------------------------------------------------
# Animal groups. key, PBDB base name (column grp), short label, full legend name, colour.
# Order here is the order of first appearance in the data (checked in 01_occurrences.py), used in every legend.
# Colours: groups that live at the same time get clearly different hues; a few groups that never overlap share a
# family of hues (whales and ichthyosaurs, hominids and theropods are 34 to 60 million years apart at the closest).
GROUPS = [
    ("tri", "Trilobita", "Trilobites", "Trilobites (Trilobita)", "#B5523B"),
    ("eur", "Eurypterida", "Sea scorpions", "Sea scorpions (Eurypterida)", "#E39BB0"),
    ("pla", "Placodermi", "Armoured fish", "Armoured fish (placoderms)", "#56677A"),
    ("amm", "Ammonoidea", "Ammonites", "Ammonites and kin (Ammonoidea)", "#A8841C"),
    ("ela", "Elasmobranchii", "Sharks and rays", "Sharks and rays (Elasmobranchii)", "#1F6FB4"),
    ("ins", "Insecta", "Insects", "Insects (Insecta)", "#7C8C2A"),
    ("tem", "Temnospondyli", "Temnospondyls", "Temnospondyls (early amphibians)", "#3BA24A"),
    ("syn", "Synapsida^Mammalia", "Early synapsids", "Early synapsids (mammal forerunners)", "#9B7BC4"),
    ("lis", "Temnospondyli", "Frogs and salamanders", "Frogs and salamanders (Lissamphibia)", "#5CC98B"),
    ("tes", "Testudinata", "Turtles", "Turtles and kin (Testudinata)", "#A9C23F"),
    ("ich", "Ichthyosauromorpha", "Ichthyosaurs", "Ichthyosaurs (Ichthyosauromorpha)", "#22B5C9"),
    ("cro", "Crocodylomorpha", "Crocodile relatives", "Crocodiles and relatives (Crocodylomorpha)", "#1E6B53"),
    ("ple", "Plesiosauria", "Plesiosaurs", "Plesiosaurs (Plesiosauria)", "#123F73"),
    ("ptr", "Pterosauria", "Pterosaurs", "Pterosaurs (Pterosauria)", "#F08BC0"),
    ("the", "Theropoda^Aves", "Theropods", "Theropods, not birds (Theropoda)", "#D7262B"),
    ("sau", "Sauropodomorpha", "Sauropods", "Sauropods and relatives (Sauropodomorpha)", "#8E1F55"),
    ("orn", "Ornithischia", "Ornithischians", "Ornithischians (Ornithischia)", "#EF7D27"),
    ("din", "Dinosauria", "Other dinosaurs", "Dinosaurs not identified further", "#C9A3A0"),
    ("mam", "Mammalia", "Mammals", "Mammals, other (Mammalia)", "#3E3A40"),
    ("ave", "Aves", "Birds", "Birds (Aves)", "#F2BE00"),
    ("mos", "Mosasauridae", "Mosasaurs", "Mosasaurs (Mosasauridae)", "#6B3FA0"),
    ("pro", "Proboscidea", "Elephants", "Elephants and relatives (Proboscidea)", "#8A6F5C"),
    ("cet", "Cetacea", "Whales", "Whales and dolphins (Cetacea)", "#1AA39A"),
    ("hom", "Hominidae", "Hominids", "Hominids (great apes and humans)", "#E8452C"),
]
GK = [g[0] for g in GROUPS]
G = {g[0]: dict(pbdb=g[1], short=g[2], name=g[3], c=g[4]) for g in GROUPS}
PBDB2K = {g[1]: g[0] for g in GROUPS if g[0] != "lis"}
# Lissamphibia (frogs, salamanders, caecilians) come back from the PBDB inside Temnospondyli; they are split off by order.
LISS_ORDERS = {"Anura", "Urodela", "Caudata", "Proteida", "Salientia", "Gymnophiona", "Allocaudata"}
# Most specific first: an occurrence in several query results is kept in the first group listed here.
PRIORITY = ["cet", "pro", "hom", "mam", "ave", "the", "sau", "orn", "din", "lis"] + [k for k in GK if k not in
            ("cet", "pro", "hom", "mam", "ave", "the", "sau", "orn", "din", "lis")]
DINO = ["the", "sau", "orn", "din"]          # non-bird dinosaurs
MARINE_REPTILES = ["ich", "ple", "mos"]

# ---------------------------------------------------------------------------------------------------------------
# Geological time scale: base ages in Ma after the ICS International Chronostratigraphic Chart (v2023/09 and later),
# rounded; colours are the chart's standard colours.
ERAS = [("Paleozoic", 538.8, 251.9, "#99C08D"), ("Mesozoic", 251.9, 66.0, "#67C5CA"), ("Cenozoic", 66.0, 0.0, "#F2F91D")]
PERIODS = [("Cambrian", "Cm", 538.8, 486.9, "#7FA056"), ("Ordovician", "O", 486.9, 443.1, "#009270"),
           ("Silurian", "S", 443.1, 419.6, "#B3E1B6"), ("Devonian", "D", 419.6, 358.9, "#CB8C37"),
           ("Carboniferous", "C", 358.9, 298.9, "#67A599"), ("Permian", "P", 298.9, 251.9, "#F04028"),
           ("Triassic", "Tr", 251.9, 201.4, "#812B92"), ("Jurassic", "J", 201.4, 143.1, "#34B2C9"),
           ("Cretaceous", "K", 143.1, 66.0, "#7FC64E"), ("Paleogene", "Pg", 66.0, 23.0, "#FD9A52"),
           ("Neogene", "N", 23.0, 2.6, "#FFE619"), ("Quaternary", "Q", 2.6, 0.0, "#F9F97F")]
# The five mass extinctions (ages as given in the brief, rounded, Ma).
EXTINCTIONS = [("eor", "End-Ordovician", 445), ("lde", "Late Devonian", 372), ("epe", "End-Permian", 252),
               ("etr", "End-Triassic", 201), ("ecr", "End-Cretaceous", 66)]

# Map frames: one per coastline age. Fossils shown with a frame: midpoint age within +-5 million years of the frame,
# except at the five extinction ages, where a frame shows the 10 million years before the extinction.
HALF = 5.0
MAX_RANGE = 25.0       # collections whose age is known only to within more than 25 million years are left out of time analyses
BIN = 5.0              # chart bins, million years
CELL = 1.0             # map cells, degrees of palaeo-latitude and longitude


def period_of(ma):
    for p in PERIODS:
        if p[3] <= ma <= p[2]:
            return p[0]
    return None


def jload(path):
    op = gzip.open if path.endswith(".gz") else open
    with op(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def dash(v):
    """Remove em and en dashes and double hyphens from names taken from the sources (house style)."""
    if isinstance(v, str):
        v = re.sub(r"(\d)\s*[–—]\s*(\d)", r"\1 to \2", v)
        v = v.replace(" — ", ", ").replace("—", ", ").replace(" – ", ", ").replace("–", "-")
        while "--" in v:
            v = v.replace("--", "-")
        return v
    if isinstance(v, list):
        return [dash(x) for x in v]
    if isinstance(v, dict):
        return {k: dash(x) for k, x in v.items()}
    return v


def jsave(obj, path, indent=None):
    if os.path.abspath(path).startswith(DATA):
        obj = dash(obj)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=indent, separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f0": return f"{float(v):.0f}"
    raise ValueError(f)


PLACEHOLDERS = ("IMG", "DOI", "DOI_URL", "BLOG_URL")


def fill(text, R):
    def rep(m):
        if m.group(1) in PLACEHOLDERS or m.group(1).startswith("IMG"):
            return m.group(0)
        return fmt(get(R, m.group(1)), m.group(3))
    return re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", rep, text)


def check_text(text, where):
    for bad in ("—", "–", "--", "DSIT", "DCMS", "civil serv", "Civil Serv"):
        assert bad not in text, (where, bad, text[max(0, text.find(bad) - 80):text.find(bad) + 80])
