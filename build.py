#!/usr/bin/env python3
"""Small standard-library static build for the Party.LAN homepage."""
from __future__ import annotations
import csv, html, json, re, shutil, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
CONTENT = ROOT / "content"
STATIC = ROOT / "static"
DIST = ROOT / "dist"
TEMPLATE = ROOT / "templates" / "index.html"
WARNINGS, ERRORS = [], []

CSV_BOOL = {"true": True, "false": False}
URL_RE = re.compile(r"^(#|/|https://|http://)")
IMAGE_RE = re.compile(r"^(/assets/|https://)")
PLACEHOLDER_RE = re.compile(r"{{[^{}]+}}")
PRODUCTION_HOST = "https://partylan.co.uk"
EXAMPLE_DOMAIN = "example" + ".com"


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
    if url.startswith("https://"):
        return True
    if not url.startswith("/assets/"):
        return True
    return (STATIC / url.lstrip("/")).exists()

def valid_image_source(url):
    return bool(IMAGE_RE.match(url or ""))

def validate_site(site):
    for key in ["meta","navigation","header","hero","reassurance","packages_section","how_it_works","gallery_section","space","faq_section","testimonials_section","final_cta","footer"]:
        if key not in site: err("site.json", key, "required top-level key is missing")
    meta = site.get("meta", {})
    req_string("site.json", meta, "title", "meta")
    req_string("site.json", meta, "description", "meta", 170)
    canonical = req_link("site.json", meta, "canonical_url", "meta")
    if canonical and canonical.rstrip("/") != PRODUCTION_HOST:
        err("site.json", "meta.canonical_url", f"must be {PRODUCTION_HOST}/ for production previews")
    if EXAMPLE_DOMAIN in json.dumps(meta):
        err("site.json", "meta", "sample domain must not remain in production metadata")
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
        if value and not valid_image_source(value): err("site.json", f"hero.media.{theme}", "image must be a local /assets/ path or absolute https:// URL")
        elif value and not asset_exists(value): err("site.json", f"hero.media.{theme}", "theme image path does not exist")
    req_string("site.json", media, "alt", "hero.media")
    for sec in ["packages_section", "gallery_section", "space"]:
        req_string("site.json", site.get(sec, {}), "heading", sec, 55)
    faq = site.get("faq_section", {})
    req_string("site.json", faq, "eyebrow", "faq_section")
    req_string("site.json", faq, "heading", "faq_section", 70)
    req_string("site.json", faq, "description", "faq_section", 140)
    faq_items = faq.get("items")
    faq_ids = set()
    if not isinstance(faq_items, list) or not faq_items:
        err("site.json", "faq_section.items", "must contain FAQ items")
    else:
        for i, item in enumerate(faq_items):
            ctx = f"faq_section.items[{i}]"
            faq_id = req_string("site.json", item, "id", ctx)
            if faq_id in faq_ids:
                err("site.json", ctx, "duplicate FAQ id")
            faq_ids.add(faq_id)
            req_string("site.json", item, "question", ctx, 120)
            req_string("site.json", item, "answer", ctx, 320)
    testimonials = site.get("testimonials_section", {})
    req_string("site.json", testimonials, "eyebrow", "testimonials_section")
    req_string("site.json", testimonials, "heading", "testimonials_section", 70)
    req_string("site.json", testimonials, "description", "testimonials_section", 160)
    req_string("site.json", site.get("final_cta", {}), "heading", "final_cta", 55)
    req_string("site.json", site.get("final_cta", {}).get("button", {}), "label", "final_cta.button", 32)

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
            elif not valid_image_source(value): err("gallery.csv", ctx, f"{key} must be a local /assets/ path or absolute https:// URL")
            elif not asset_exists(value): err("gallery.csv", ctx, f"{key} asset does not exist")
        href = row.get("href", "").strip()
        if href and not URL_RE.match(href): err("gallery.csv", ctx, "href is not a practical valid link")
        out.append(row)
    return sorted(out, key=lambda r: r["order_int"])

def validate_testimonials(rows):
    out, ids, orders = [], set(), set()
    for n, row in enumerate(rows, start=2):
        rid = row.get("id", "").strip(); ctx = f"row {n} ({rid or 'no id'})"
        if not rid: continue
        if rid in ids: err("testimonials.csv", ctx, "duplicate id")
        ids.add(rid)
        raw_visible = row.get("visible", "").strip().lower()
        if raw_visible not in CSV_BOOL: err("testimonials.csv", ctx, "visible must be true or false"); continue
        visible = CSV_BOOL[raw_visible]
        if not visible: continue
        for key in ["quote", "name", "location", "alt"]:
            req_string("testimonials.csv", row, key, ctx, 260 if key == "quote" else 120)
        try:
            age = int(row.get("age", ""))
            if age <= 0 or age > 120: err("testimonials.csv", ctx, "age must be a sensible positive integer")
        except ValueError:
            err("testimonials.csv", ctx, "age must be an integer")
        try:
            order = int(row.get("display_order", ""))
            if order <= 0: err("testimonials.csv", ctx, "display_order must be a positive integer")
            if order in orders: err("testimonials.csv", ctx, "duplicate display_order")
            orders.add(order); row["order_int"] = order
        except ValueError:
            err("testimonials.csv", ctx, "display_order must be an integer")
        for key in ["image_light", "image_dark"]:
            value = row.get(key, "").strip()
            if not value: err("testimonials.csv", ctx, f"missing {key}")
            elif not valid_image_source(value): err("testimonials.csv", ctx, f"{key} must be a local /assets/ path or absolute https:// URL")
            elif value.startswith("http://"): err("testimonials.csv", ctx, f"{key} must use https:// for external images")
            elif not asset_exists(value): err("testimonials.csv", ctx, f"{key} asset does not exist")
        out.append(row)
    return sorted(out, key=lambda r: r["order_int"])


class RenderedDocumentParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.assets = []
        self.package_features = {}
        self._current_package = None
        self._in_feature = False
        self._feature_parts = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag in {"img", "script"} and attrs.get("src"):
            self.assets.append(attrs["src"])
        if tag == "link" and attrs.get("href"):
            self.assets.append(attrs["href"])
        if tag == "article" and "package-card" in attrs.get("class", ""):
            self._current_package = ""
        if self._current_package is not None and tag == "li":
            self._in_feature = True
            self._feature_parts = []

    def handle_endtag(self, tag):
        if tag == "li" and self._in_feature and self._current_package is not None:
            feature = "".join(self._feature_parts).strip()
            if feature:
                self.package_features.setdefault(self._current_package, []).append(feature)
            self._in_feature = False
        if tag == "article" and self._current_package is not None:
            self._current_package = None

    def handle_data(self, data):
        if self._current_package is not None and not self._current_package and data.strip() in {"ONYX", "JADE"}:
            self._current_package = data.strip()
            self.package_features.setdefault(self._current_package, [])
        if self._in_feature:
            self._feature_parts.append(data)


def validate_rendered(html_out, site, packages):
    if EXAMPLE_DOMAIN in html_out:
        err("dist/index.html", "metadata", "sample domain must not appear in generated public files")
    placeholders = sorted(set(PLACEHOLDER_RE.findall(html_out)))
    if placeholders:
        err("dist/index.html", "template", "unresolved template placeholders remain: " + ", ".join(placeholders))
    parser = RenderedDocumentParser()
    parser.feed(html_out)
    for item in site.get("navigation", []):
        href = item.get("href", "")
        if href.startswith("#") and href[1:] not in parser.ids:
            err("dist/index.html", f"navigation {item.get('label', href)}", f"anchor {href} does not exist in rendered document")
        elif href.startswith("/") and href not in {"/", "/index.html"}:
            err("dist/index.html", f"navigation {item.get('label', href)}", f"links to unavailable page {href}")
    for pkg in packages:
        rendered = parser.package_features.get(pkg.get("name"), [])
        missing = [feat for feat in pkg.get("features", []) if feat not in rendered]
        if missing:
            err("dist/index.html", f"package {pkg.get('name')}", "omitted configured features: " + "; ".join(missing))
    for asset in parser.assets:
        if asset.startswith("/") and not (DIST / asset.lstrip("/")).exists():
            err("dist/index.html", asset, "referenced local asset is missing")

def render_list(items): return "\n".join(f"<li>{esc(i)}</li>" for i in items)
def render_nav(items):
    links = []
    for i in items:
        class_attr = ' class="site-menu__availability"' if i.get("href") == "#booking" else ""
        links.append(f'<a{class_attr} href="{attr(i["href"])}">{esc(i["label"])}</a>')
    return "\n".join(links)

def render_footer_links(items):
    valid = [i for i in items if i.get("href", "").startswith("#") and i.get("href") != "#top"]
    return "\n".join(f'<a href="{attr(i["href"])}">{esc(i["label"])}</a>' for i in valid)

def render_packages(packages):
    cards=[]
    for p in packages:
        features = render_list(p["features"])
        cards.append(f'''<article class="package-card package-card--{attr(p["id"])} reveal"><div class="package-card__head"><p class="package-subtitle">{esc(p["subtitle"])}</p><h3>{esc(p["name"])}</h3><div class="package-meta"><p class="package-price">{esc(p["price"])}</p><p>{esc(p["duration"])}</p><p>{esc(p["capacity"])}</p></div></div><ul class="feature-list">{features}</ul><a class="button button--ghost" href="{attr(p["action"]["href"])}">{esc(p["action"]["label"])}</a></article>''')
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

def render_faq_items(items):
    out = []
    for item in items:
        out.append(f'''<details class="faq-item" id="faq-{attr(item["id"])}"><summary>{esc(item["question"])}</summary><div class="faq-item__answer"><p>{esc(item["answer"])}</p></div></details>''')
    return "\n".join(out)

def render_testimonials_section(section, rows):
    if not rows:
        return ""
    dots = ""
    if len(rows) > 1:
        dots = '<div class="testimonial-dots" role="tablist" aria-label="Choose testimonial">' + "\n".join(
            f'<button class="testimonial-dot{" is-active" if i == 1 else ""}" type="button" aria-label="Show testimonial {i} of {len(rows)}" aria-current="{"true" if i == 1 else "false"}" data-testimonial-dot="{i - 1}"><span></span></button>'
            for i, _ in enumerate(rows, 1)
        ) + "</div>"
    slides = []
    for i, row in enumerate(rows):
        active = " is-active" if i == 0 else ""
        slides.append(f'''<article class="testimonial-slide{active}" data-testimonial-slide="{i}">
  <img class="testimonial-slide__image theme-image" src="{attr(row["image_light"])}" data-light-src="{attr(row["image_light"])}" data-dark-src="{attr(row["image_dark"])}" alt="{attr(row["alt"])}" loading="lazy" width="1440" height="540">
  <div class="testimonial-slide__overlay" aria-hidden="true"></div>
  <div class="testimonial-slide__content">
    <blockquote class="testimonial-quote"><p>“{esc(row["quote"])}”</p></blockquote>
    <p class="testimonial-person">{esc(row["name"])}, age {esc(row["age"])}</p>
    <p class="testimonial-location">{esc(row["location"])}</p>
  </div>
</article>''')
    return f'''<section class="section testimonials" id="testimonials" aria-labelledby="testimonials-title">
  <div class="section-heading reveal">
    <p class="eyebrow">{esc(section["eyebrow"])}</p>
    <h2 id="testimonials-title">{esc(section["heading"])}</h2>
    <p>{esc(section["description"])}</p>
  </div>
  <div class="testimonial-stage reveal" aria-label="Customer testimonials">
    {"".join(slides)}
    {dots}
  </div>
</section>'''

def render_reassurance(items):
    icons = {
        "delivered": "M4 13h10V5H4v8Zm10 0h3l3-3v3h2M7 17a2 2 0 1 0 0-4 2 2 0 0 0 0 4Zm11 0a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z",
        "hosted": "M12 4a4 4 0 0 0-4 4v3a4 4 0 0 0 8 0V8a4 4 0 0 0-4-4Zm-7 16a7 7 0 0 1 14 0",
        "selected": "M5 12l4 4L19 6M6 5h7M6 19h12"
    }
    out=[]
    for i in items:
        path=icons.get(i.get("id", ""), icons["selected"])
        svg=f'<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="{path}"/></svg>'
        out.append(f'<li>{svg}<span>{esc(i["text"])}</span></li>')
    return "\n".join(out)

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
        "{{canonical_url}}": attr(site["meta"]["canonical_url"]), "{{og_image}}": attr(PRODUCTION_HOST + site["meta"]["og_image"]),
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
        "{{testimonials_section}}": render_testimonials_section(site["testimonials_section"], testimonials),
        "{{faq_eyebrow}}": esc(site["faq_section"]["eyebrow"]), "{{faq_heading}}": esc(site["faq_section"]["heading"]), "{{faq_description}}": esc(site["faq_section"]["description"]), "{{faq_items}}": render_faq_items(site["faq_section"]["items"]),
        "{{final_heading}}": esc(site["final_cta"]["heading"]), "{{final_description}}": esc(site["final_cta"]["description"]), "{{final_button_label}}": esc(site["final_cta"]["button"]["label"]),
        "{{footer_tagline}}": esc(site["footer"]["tagline"]), "{{footer_links}}": render_footer_links(site["navigation"])
    }
    html_out = template
    for k,v in replacements.items(): html_out = html_out.replace(k,v)
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir()
    shutil.copytree(STATIC, DIST, dirs_exist_ok=True)
    validate_rendered(html_out, site, packages)
    if ERRORS:
        print("Build failed with rendered-output validation errors:", file=sys.stderr)
        print("\n".join(f"- {e}" for e in ERRORS), file=sys.stderr); sys.exit(1)
    (DIST/"index.html").write_text(html_out, encoding="utf-8")
    print(f"Built dist/index.html with {len(packages)} packages, {len(gallery)} gallery items and {len(testimonials)} testimonials.")
    for w in WARNINGS: print(f"Warning: {w}")

if __name__ == "__main__": main()
