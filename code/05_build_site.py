"""Build index.html from code/page_template.html and code/page_app.js. Every number in the text is a {{path|format}}
token filled from data/results.json; 10.5281/zenodo.23856870, https://doi.org/10.5281/zenodo.23856870 and https://blog.tristanhotham.com/2026/10/31/deep-time-life/ are left for the publisher. Facts stated in
words are checked here. The full-screen map snippet (code/fullscreen_snippet.html, from the reference studies) is
pasted before </body>."""
import re
from common import *

R = jload(f"{DATA}/results.json")
SITE = jload(f"{DATA}/site.json")


def checks(R):
    """Facts stated in words on the page, in the paper, blog and collage."""
    g = R["groups"]
    assert R["drift"]["uk_420"] < -15 and abs(R["drift"]["uk_300"]) < 1 and 30 < R["drift"]["uk_190"] < 45
    assert 174.7 <= R["pangaea"]["peak_age"] <= 201.4                       # Early Jurassic
    assert R["pangaea"]["first_over_85"] == 270 and R["pangaea"]["last_over_85"] == 180
    assert R["pangaea"]["at"]["150"] < R["pangaea"]["at"]["170"] < R["pangaea"]["peak_pct"] and R["pangaea"]["at"]["100"] < 30
    assert R["leaders"]["Paleozoic"]["k"] == "tri" and R["leaders"]["Mesozoic"]["k"] == "ins" and R["leaders"]["Cenozoic"]["k"] == "mam"
    assert sorted(g, key=lambda k: -g[k]["genera"])[:2] == ["ins", "mam"]
    assert R["dino"]["multi_pangaea"]["pct"] > 2 * R["dino"]["multi_cretaceous"]["pct"]
    assert R["facts"]["tyr_north_pct"] == 100 and R["facts"]["cer_north_pct"] == 100 and R["facts"]["abe_south_india_pct"] > 75
    assert R["dino"]["polar75_places"]["Alaska"] + R["dino"]["polar75_places"]["Victoria"] > R["dino"]["polar75_coll"] / 2
    assert 230 <= max(g[k]["first"] for k in DINO) <= 250 and max(g[k]["first"] for k in DINO) - R["pangaea"]["last_over_85"] >= 50
    assert R["facts"]["hom_afr_asia_pct"] > 80 and R["facts"]["hom_abs_lat_tropics_pct"] > 50
    assert 20 <= R["facts"]["ins_top50_coll_pct"] < 30                      # 'a quarter'
    ex = {e["k"]: e for e in R["extinctions"]}
    assert ex["epe"]["lost_pct"] == max(e["lost_pct"] for e in R["extinctions"]) and ex["epe"]["lost_pct"] > R["ext_bg_p90"]
    assert all(ex["ecr"]["by_group"][k]["lost_pct"] == 100 for k in ("the", "sau", "orn", "ple", "mos"))
    assert ex["ecr"]["by_group"]["ins"]["lost_pct"] < 5 and ex["etr"]["lost_pct"] < R["ext_bg_median"]
    assert g["tri"]["youngest"] < 262 and 515 <= g["tri"]["first"] <= 525   # 'the last trilobites vanish'; 'around 520 Ma'
    assert R["sampling"]["top_countries"][0]["name"] == "United States of America"
    assert R["dino"]["peak_na_pct"] > 50
    lab = SITE["labels"]["0"]; assert -20 < lab[0] < 52 and -35 < lab[1] < 37   # today's largest block is centred in Africa
    return True


def build():
    checks(R)
    tpl = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()
    html = fill(tpl, R)
    left = set(re.findall(r"\{\{([^}]+)\}\}", html))
    assert left <= {"DOI", "DOI_URL", "BLOG_URL"}, left
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
    app = open(os.path.join(ROOT, "code", "page_app.js"), encoding="utf-8").read()
    html = html.replace("/*APPJS*/", app).replace("/*RESULTS*/", J(R)).replace("/*SITE*/", J(SITE))
    html = html.replace("/*FULLSCREEN*/", open(os.path.join(ROOT, "code", "fullscreen_snippet.html"), encoding="utf-8").read())
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", html, flags=re.S)
    vis = re.sub(r"<[^>]+>", " ", vis)
    check_text(vis, "index visible")
    for scr in re.findall(r"<script>(.*?)</script>", html, flags=re.S):
        for bad in ("—", "–", "DSIT", "DCMS"):
            assert bad not in scr, bad
    # visible strings inside the script: no double hyphen inside quotes
    for m in re.findall(r'"([^"\n]{4,})"', app):
        assert "--" not in m or m.startswith("--") or "var(--" in m, m
    open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(html)
    print("index.html", len(html.encode()) // 1024, "KB")


if __name__ == "__main__":
    build()
