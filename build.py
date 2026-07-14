#!/usr/bin/env python3
"""Small standard-library static build for the Party.LAN homepage."""
from __future__ import annotations
import csv, html, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
DIST = ROOT / "dist"
TEMPLATE = ROOT / "templates" / "index.html"
WARNINGS, ERRORS = [], []

CSV_BOOL = {"true": True, "false": False}
URL_RE = re.compile(r"^(#|/|https://|http://)")


def err(file, key, reason): ERRORS.append(f"{file}: {key}: {reason}")
def warn(file, key, reason): WARNINGS.append(f"{file}: {key}: {reason}")
def esc(value): return html.escape(str(value), quote=True)
def attr(value): return esc(value)

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        err(path.name, "$", f"invalid JSON ({exc})"); return {} if path.name == "site.json" else []

def req_string(file, obj, key, ctx, max_len=None, warning_only=True):
    value = obj.get(key) if isinstance(obj, dict) else None
    if not isinstance(value, str) or not value.strip():
        err(file, f"{ctx}.{key}", "required non-empty string is missing"); return ""
    value = value.strip()
    if max_len and len(value) > max_len:
        (warn if warning_only else err)(file, f"{ctx}.{key}", f"length {len(value)} exceeds suggested {max_len} characters")
    return value

def req_link(file, obj, key, ctx):
    value = req_string(file, obj, key, ctx)
    if value and not URL_RE.match(value): err(file, f"{ctx}.{key}", "link must be an anchor, root-relative path or http(s) URL")
    return value

def asset_exists(url):
    if not url.startswith("/assets/"): return True
    return (STATIC / url.lstrip("/")).exists()

def validate_site(site):
    for key in ["meta","navigation","header","hero","reassurance","packages_section","how_it_works","gallery_section","space","testimonials_section","final_cta","footer"]:
        if key not in site: err("site.json", key, "required top-level key is missing")
    meta = site.get("meta", {})
    req_string("site.json", meta, "title", "meta")
    req_string("site.json", meta, "description", "meta", 170)
    req_link("site.json", meta, "canonical_url", "meta")
    if not asset_exists(meta.get("og_image", "")): err("site.json", "meta.og_image", "referenced asset does not exist")
    labels = set()
    for i, item in enumerate(site.get("navigation", [])):
        label = req_string("site.json", item, "label", f"navigation[{i}]", 24)
        req_link("site.json", item, "href", f"navigation[{i}]")
        if label in labels: err("site.json", f"navigation[{i}]", "duplicate navigation label")
        labels.add(label)
    hero = site.get("hero", {})
    req_string("site.json", hero, "eyebrow", "hero")
    req_string("site.json", hero, "title", "hero", 70)
    req_string("site.json", hero, "description", "hero", 180)
    for cta_key in ["primaryCta", "secondaryCta"]:
        cta = hero.get(cta_key, {})
        req_string("site.json", cta, "label", f"hero.{cta_key}", 24)
        req_link("site.json", cta, "href", f"hero.{cta_key}")
    media = hero.get("media", {})
    for theme in ["light", "dark"]:
        value = req_string("site.json", media, theme, "hero.media")
        if value and not asset_exists(value): err("site.json", f"hero.media.{theme}", "theme image path does not exist")
    req_string("site.json", media, "alt", "hero.media")
    for sec in ["packages_section", "gallery_section", "space"]:
        req_string("site.json", site.get(sec, {}), "heading", sec, 55)
    req_string("site.json", site.get("final_cta", {}), "heading", "final_cta", 55)
    req_string("site.json", site.get("final_cta", {}).get("button", {}), "label", "final_cta.button", 24)

def validate_packages(packages):
    ids = set()
    for i, pkg in enumerate(packages):
        ctx = f"packages[{i}]"
        pid = req_string("packages.json", pkg, "id", ctx)
        if pid in ids: err("packages.json", ctx, "duplicate package id")
        ids.add(pid)
        for key in ["name","subtitle","price","duration","capacity"]: req_string("packages.json", pkg, key, ctx, 55 if key in ["name","subtitle"] else None)
        if not pkg.get("price"): err("packages.json", f"{ctx}.price", "missing package price")
        if not pkg.get("capacity"): err("packages.json", f"{ctx}.capacity", "missing package capacity")
        feats = pkg.get("features")
        if not isinstance(feats, list) or not feats: err("packages.json", f"{ctx}.features", "must contain feature strings")
        else:
            for j, feat in enumerate(feats):
                if not isinstance(feat, str) or not feat.strip(): err("packages.json", f"{ctx}.features[{j}]", "empty feature")
                elif len(feat) > 180: warn("packages.json", f"{ctx}.features[{j}]", "feature is longer than suggested 180 characters")
        req_string("packages.json", pkg.get("action", {}), "label", f"{ctx}.action", 24)
        req_link("packages.json", pkg.get("action", {}), "href", f"{ctx}.action")

def read_csv(path):
    with path.open(newline="", encoding="utf-8") as fh: return list(csv.DictReader(fh))

def validate_gallery(rows):
    out, ids = [], set()
    for n, row in enumerate(rows, start=2):
        rid = row.get("id", "").strip(); ctx = f"row {n} ({rid or 'no id'})"
        if not rid: err("gallery.csv", ctx, "missing id"); continue
        if rid in ids: err("gallery.csv", ctx, "duplicate id")
        ids.add(rid)
        raw_visible = row.get("visible", "").strip().lower()
        if raw_visible not in CSV_BOOL: err("gallery.csv", ctx, "visible must be true or false"); continue
        try: order = int(row.get("display_order", ""))
        except ValueError: err("gallery.csv", ctx, "display_order must be an integer"); continue
        row["visible_bool"] = CSV_BOOL[raw_visible]; row["order_int"] = order
        if not row["visible_bool"]: continue
        if not row.get("alt", "").strip(): err("gallery.csv", ctx, "missing image alternative text")
        if len(row.get("caption", "")) > 120: warn("gallery.csv", ctx, "caption exceeds suggested 120 characters")
        for key in ["image_light", "image_dark"]:
            value = row.get(key, "").strip()
            if not value: err("gallery.csv", ctx, f"missing {key}")
            elif not asset_exists(value): err("gallery.csv", ctx, f"{key} asset does not exist")
        href = row.get("href", "").strip()
        if href and not URL_RE.match(href): err("gallery.csv", ctx, "href is not a practical valid link")
        out.append(row)
    return sorted(out, key=lambda r: r["order_int"])

def validate_testimonials(rows):
    out, ids = [], set()
    for n, row in enumerate(rows, start=2):
        rid = row.get("id", "").strip(); ctx = f"row {n} ({rid or 'no id'})"
        if not rid: continue
        if rid in ids: err("testimonials.csv", ctx, "duplicate id")
        ids.add(rid)
        raw_visible = row.get("visible", "").strip().lower()
        if raw_visible not in CSV_BOOL: err("testimonials.csv", ctx, "visible must be true or false"); continue
        try: row["order_int"] = int(row.get("display_order", ""))
        except ValueError: err("testimonials.csv", ctx, "display_order must be an integer"); continue
        if CSV_BOOL[raw_visible]: out.append(row)
    return sorted(out, key=lambda r: r["order_int"])

def render_list(items): return "\n".join(f"<li>{esc(i)}</li>" for i in items)
def render_nav(items): return "\n".join(f'<a href="{attr(i["href"])}">{esc(i["label"])}</a>' for i in items)

def render_packages(packages):
    cards=[]
    for p in packages:
        features = render_list(p["features"][:5])
        cards.append(f'''<article class="package-card reveal"><div><p class="package-subtitle">{esc(p["subtitle"])}</p><h3>{esc(p["name"])}</h3><p class="package-price">{esc(p["price"])} <span>{esc(p["duration"])}</span></p><p class="package-capacity">{esc(p["capacity"])}</p></div><ul class="feature-list">{features}</ul><a class="button button--ghost" href="{attr(p["action"]["href"])}">{esc(p["action"]["label"])}</a></article>''')
    return "\n".join(cards)

def render_gallery(rows):
    if not rows: return ""
    items=[]
    for r in rows:
        img=f'<img class="theme-image" src="{attr(r["image_light"])}" data-light-src="{attr(r["image_light"])}" data-dark-src="{attr(r["image_dark"])}" alt="{attr(r["alt"])}" loading="lazy" width="720" height="520">'
        body=f'{img}<figcaption>{esc(r.get("caption", ""))}</figcaption>' if r.get("caption") else img
        if r.get("href", "").strip(): body=f'<a href="{attr(r["href"].strip())}">{body}</a>'
        items.append(f'<figure class="gallery-card reveal">{body}</figure>')
    return "\n".join(items)

def render_steps(steps):
    return "\n".join(f'<article class="step-card reveal"><span>{i}</span><h3>{esc(s["title"])}</h3><p>{esc(s["description"])}</p></article>' for i,s in enumerate(steps,1))

def render_reassurance(items): return "\n".join(f'<li>{esc(i["text"])}</li>' for i in items)

def main():
    site, packages = read_json(CONTENT/"site.json"), read_json(CONTENT/"packages.json")
    validate_site(site); validate_packages(packages)
    gallery = validate_gallery(read_csv(CONTENT/"gallery.csv"))
    testimonials = validate_testimonials(read_csv(CONTENT/"testimonials.csv"))
    if ERRORS:
        print("Build failed with validation errors:", file=sys.stderr)
        print("\n".join(f"- {e}" for e in ERRORS), file=sys.stderr); sys.exit(1)
    template = TEMPLATE.read_text(encoding="utf-8")
    h=site["hero"]
    replacements = {
        "{{meta_title}}": esc(site["meta"]["title"]), "{{meta_description}}": esc(site["meta"]["description"]),
        "{{canonical_url}}": attr(site["meta"]["canonical_url"]), "{{og_image}}": attr(site["meta"]["og_image"]),
        "{{theme_color_light}}": attr(site["meta"].get("theme_color_light", "#f6efe4")), "{{nav_links}}": render_nav(site["navigation"]),
        "{{availability_label}}": esc(site["header"]["availabilityCta"]["label"]), "{{availability_href}}": attr(site["header"]["availabilityCta"]["href"]),
        "{{hero_eyebrow}}": esc(h["eyebrow"]), "{{hero_title}}": esc(h["title"]), "{{hero_description}}": esc(h["description"]),
        "{{hero_primary_label}}": esc(h["primaryCta"]["label"]), "{{hero_primary_href}}": attr(h["primaryCta"]["href"]),
        "{{hero_secondary_label}}": esc(h["secondaryCta"]["label"]), "{{hero_secondary_href}}": attr(h["secondaryCta"]["href"]),
        "{{hero_light}}": attr(h["media"]["light"]), "{{hero_dark}}": attr(h["media"]["dark"]), "{{hero_alt}}": attr(h["media"]["alt"]),
        "{{reassurance_items}}": render_reassurance(site["reassurance"]), "{{packages_heading}}": esc(site["packages_section"]["heading"]),
        "{{packages_eyebrow}}": esc(site["packages_section"]["eyebrow"]), "{{packages_description}}": esc(site["packages_section"]["description"]), "{{package_cards}}": render_packages(packages),
        "{{how_eyebrow}}": esc(site["how_it_works"]["eyebrow"]), "{{how_heading}}": esc(site["how_it_works"]["heading"]), "{{steps}}": render_steps(site["how_it_works"]["steps"]),
        "{{gallery_eyebrow}}": esc(site["gallery_section"]["eyebrow"]), "{{gallery_heading}}": esc(site["gallery_section"]["heading"]), "{{gallery_description}}": esc(site["gallery_section"]["description"]), "{{gallery_items}}": render_gallery(gallery),
        "{{space_eyebrow}}": esc(site["space"]["eyebrow"]), "{{space_heading}}": esc(site["space"]["heading"]), "{{space_description}}": esc(site["space"]["description"]),
        "{{testimonials_section}}": "" if not testimonials else "<section class=\"section\"><h2>Testimonials</h2></section>",
        "{{final_heading}}": esc(site["final_cta"]["heading"]), "{{final_description}}": esc(site["final_cta"]["description"]), "{{final_button_label}}": esc(site["final_cta"]["button"]["label"]), "{{final_button_href}}": attr(site["final_cta"]["button"]["href"]),
        "{{footer_tagline}}": esc(site["footer"]["tagline"]), "{{footer_note}}": esc(site["footer"]["note"])
    }
    html_out = template
    for k,v in replacements.items(): html_out = html_out.replace(k,v)
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(STATIC, DIST, dirs_exist_ok=True)
    (DIST/"index.html").write_text(html_out, encoding="utf-8")
    print(f"Built dist/index.html with {len(packages)} packages, {len(gallery)} gallery items and {len(testimonials)} testimonials.")
    for w in WARNINGS: print(f"Warning: {w}")

if __name__ == "__main__": main()
