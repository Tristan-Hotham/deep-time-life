"""Build the paper: fill code/paper_template.tex from data/results.json, add the group table, compile with xelatex.
The DOI is not known until the Zenodo record exists: set the environment variable DOI (e.g. 10.5281/zenodo.123) and
rerun to print it on the title page and in the data statement."""
import re, subprocess, shutil
from common import *
import importlib.util

R = jload(f"{DATA}/results.json")
spec = importlib.util.spec_from_file_location("b", os.path.join(ROOT, "code", "05_build_site.py")); B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
B.checks(R)
assert max(R["lat"], key=R["lat"].get) == "syn" and min(R["lat"], key=R["lat"].get) == "hom"
assert all(56 <= R_ <= 71 for a, R_ in jload(f"{DATA}/site.json")["pangaea"] if a >= 280)
OUT = os.path.join(ROOT, "release", "paper"); NAME = PAPER_NAME
tex = lambda s: str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#").replace("^", "\\^{}")


def f(v, k):
    if k == "int": return f"{int(round(float(v))):,}"
    if k == "pc": return f"{round(float(v))}\\%"
    if k == "f1": return f"{float(v):.1f}"
    return tex(str(v))


rows = ""
for k in R["group_order"]:
    g = R["groups"][k]
    rows += f"{tex(g['short'])} & {tex(G[k]['pbdb'].replace('^', ' not '))} & {g['n']:,} & {g['coll']:,} & {g['genera']:,} & {g['first']:.0f} & {g['last']:.0f}\\\\\n"
TG = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{The {{records.n_groups|int}} groups: occurrences, collections and genera in the analysis set, and the oldest and youngest midpoint ages in million years (ignoring the oldest and youngest 0.2\\% of occurrences). `not' marks a query excluding a subgroup.}\\label{tab:groups}\\setlength{\\tabcolsep}{4pt}"
      "\\begin{tabular}{llrrrrr}\\toprule Group & PBDB query & Occurrences & Collections & Genera & Oldest & Youngest\\\\\\midrule\n" + rows +
      f"\\midrule All & & {R['records']['n']:,} & {R['records']['collections']:,} & {R['records']['genera']:,} & & \\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
t = open(os.path.join(ROOT, "code", "paper_template.tex"), encoding="utf-8").read().replace("{{TABLE_GROUPS}}", TG)
for k in ("page", "repo"):
    t = t.replace("\\url{{{meta.%s}}}" % k, "\\url{%s}" % R["meta"][k])
t = re.sub(r"\{\{([^}|]+)(\|(\w+))?\}\}", lambda m: f(get(R, m.group(1)), m.group(3) or "raw"), t)
doi = os.environ.get("DOI", "").strip()
t = t.replace("%%DOILINE%%", f"DOI: \\href{{https://doi.org/{doi}}}{{https://doi.org/{doi}}}" if doi else "Working paper")
t = t.replace("%%ARCHIVE%%", f", archived with this paper at \\url{{https://doi.org/{doi}}}" if doi else ", archived with this paper on Zenodo")
body = re.sub(r"^%.*$", "", t, flags=re.M)
assert "{{" not in t and "--" not in body and "\u2014" not in t and "\u2013" not in t
os.makedirs(OUT, exist_ok=True)
open(os.path.join(OUT, NAME + ".tex"), "w", encoding="utf-8").write(t)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", NAME + ".tex"], cwd=OUT, capture_output=True, text=True)
log = open(os.path.join(OUT, NAME + ".log"), encoding="utf-8", errors="ignore").read()
print([l for l in log.splitlines() if "Missing character" in l or "undefined" in l.lower() or "Overfull" in l][:12])
for ext in (".aux", ".log", ".out"):
    q = os.path.join(OUT, NAME + ext)
    if os.path.exists(q): os.remove(q)
txt = subprocess.run(["pdftotext", os.path.join(OUT, NAME + ".pdf"), "-"], capture_output=True, text=True).stdout
pages = subprocess.run(["pdfinfo", os.path.join(OUT, NAME + ".pdf")], capture_output=True, text=True).stdout
print("paper", r.returncode, len(txt.split()), "words;", [l for l in pages.splitlines() if l.startswith("Pages")], "dashes:", txt.count("\u2014") + txt.count("\u2013") + txt.count("--"))
