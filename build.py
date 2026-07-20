#!/usr/bin/env python3
"""Standard-library static build and content validation for Party.LAN."""
from __future__ import annotations
import csv, hashlib, html, json, os, re, shutil, sys
from pathlib import Path

# BUILD PIPELINE OVERVIEW
# -----------------------
# 1. Read editable business content from content/ (JSON, CSV and images).
# 2. Validate required fields, fixed business facts, routes and asset paths.
# 3. Recreate dist/ from static/ and the approved content images.
# 4. Render the homepage and the packages, contact and legal pages as HTML.
#
# This file intentionally uses only the Python standard library. Render runs it
# during deployment, so changing the functions below changes the generated site.
# The older templates/index.html file is not used by this build.

# BEGINNER'S MENTAL MODEL: HOW THE WEBSITE FITS TOGETHER
# -----------------------------------------------------
# A visitor's browser receives three things:
# - HTML: the page structure and words (headings, sections, links and forms).
# - CSS: how that structure looks at different screen sizes and in each theme.
# - JavaScript: what happens after a click, swipe, form submission or scroll.
#
# Visitors do NOT run this Python file. Python runs once when the site is built.
# Think of build.py as a small factory: it takes the editable content and source
# assets, checks them, assembles the HTML, and places the finished website in
# dist/. Render then serves the files in dist/ directly to visitors.
#
# FOLDER MAP
# content/   = editable words, prices, FAQs, legal text and original photographs
# static/    = source CSS, browser JavaScript and fallback artwork
# build.py   = validation rules and the HTML assembly process
# dist/      = generated website that Render publishes; never edit it directly
# templates/ = an old prototype kept for reference; the current build ignores it
#
# CONTENT FILE TYPES
# JSON stores nested named values and lists, such as homepage sections or legal
# blocks. CSV stores table-like rows, such as one FAQ or gallery item per line.
# Neither format supports safe comments, so explanations for their expected
# fields live in this validator and the existing content/CONTENT_GUIDE.md file.
#
# PYTHON READING GUIDE
# name=value       stores a value under a name.
# def name(...):   starts a reusable function.
# return value     sends a completed value back to the caller.
# if / elif / else chooses which instructions run.
# for item in list repeats instructions for every item.
# [...]            is a list; {...} is a dictionary of named values.
# obj.get('name')  safely looks up a dictionary value that might be missing.
# f'...{value}...' inserts a value into text; these are called f-strings.
# A semicolon in this compact file separates statements that could have been
# written on separate lines. Read each semicolon as a visual line break.

# Absolute project paths used by every read, validation and output operation.
ROOT=Path(__file__).parent.resolve(); CONTENT=ROOT/'content'; STATIC=ROOT/'static'; DIST=ROOT/'dist'; IMAGES=CONTENT/'images'

# Change the stylesheet URL whenever its content changes so browsers cannot keep
# serving an older caption layout after a deployment.
STYLESHEET_VERSION=hashlib.sha256((STATIC/'css'/'styles.css').read_bytes()).hexdigest()[:12]

# Shared validation state and the small set of values accepted from content.
# ERRORS starts empty and gathers readable messages throughout validation.
# BOOL translates the words used in CSV files into Python True/False values.
# IMG_EXT lists the image file endings the build knows how to publish safely.
ERRORS=[]; BOOL={'true':True,'false':False}; IMG_EXT={'.jpg','.jpeg','.png','.webp','.avif'}

# A build cannot succeed unless every content source in this list exists.
REQUIRED_FILES=['homepage.json','packages.json','addons.csv','testimonials.csv','testimonials.example.csv','gallery.csv','gallery.example.csv','faq.csv','packages_faq.csv','legal/terms.json','legal/privacy.json']

# Gallery records keep their author-facing fields, but the build normalises the
# category/platform values and adds separate composite/internal identifiers.
GALLERY_FIELDS=('id','category','Platform','image','Header','Subtext','visible','display_order')
GALLERY_CATEGORIES=('experience','equipment')
GALLERY_PLATFORMS=('PC','Mobile','All')
GALLERY_MOBILE_QUERY='(max-width: 920px)'  # Keep aligned with the gallery CSS media query.

# SEO: These keys are the complete set of public, indexable routes. Keep this
# tuple aligned with meta.pages in content/homepage.json and write_seo_files().
# Demo/test URLs deliberately do not belong here.
SEO_PAGE_KEYS=('home','packages','contact','terms','privacy')

# These commercial package facts are deliberately fixed in code. Validation
# prevents an accidental content edit from changing the advertised offer.
PACKAGE_FACTS={'onyx':{'name':'ONYX','label':'Premium Experience','price':'£150','duration':'2 hours','capacity':'Up to 6 players','included':['PlayStation and Nintendo gaming','Racing simulator','VR hardware','Displays','Party host/operator','Free digital invitation']},'jade':{'name':'JADE','label':'Big Party','price':'£150','duration':'2 hours','capacity':'Up to 10 players','included':['Multiplayer gaming across multiple stations','Displays','Party host/operator','Free digital invitation']}}

# Legal JSON is rendered as a sequence of these supported content components.
LEGAL_BLOCK_TYPES={'paragraph','list','definitions','fields','table'}

# ================================================================
# Validation helpers
# ================================================================

# Collect errors instead of stopping at the first one, so an editor sees every
# content problem in a single build attempt.
def err(f,k,r): ERRORS.append(f'{f} {k}: {r}')

# All content-originated text passes through this helper before entering HTML.
# Escaping changes characters such as < and > into safe HTML text, preventing a
# content entry from accidentally becoming a real HTML tag or attribute.
def esc(v): return html.escape(str(v), quote=True)

# Return trimmed text or record which required field is missing.
def req_text(file,obj,key,ctx):
    v=obj.get(key) if isinstance(obj,dict) else None
    if not isinstance(v,str) or not v.strip(): err(file,ctx+'.'+key,'required text is empty'); return ''
    return v.strip()

# CSV booleans are strings; only explicit true/false values are accepted.
def req_bool(file,row,key,ctx):
    v=(row.get(key,'') or '').strip().lower()
    if v not in BOOL: err(file,ctx,f'{key} must be true or false'); return False
    return BOOL[v]

# Convert display_order to a unique positive number used for stable sorting.
def req_order(file,row,ctx,orders):
    raw=(row.get('display_order','') or '').strip()
    try: order=int(raw); assert order>0
    except Exception: err(file,ctx,'display_order must be a positive integer'); return 999999
    if order in orders: err(file,ctx,f'duplicate display_order {order}')
    orders.add(order); return order

# Restrict content images to the local image pipeline and supported formats.
def image_ok(file,ctx,value):
    if not value: err(file,ctx,'referenced image is required'); return
    prefixes=('/content/images/','/assets/images/')
    prefix=next((candidate for candidate in prefixes if value.startswith(candidate)),None)
    if prefix is None: err(file,ctx,'unsupported image path; expected /content/images/...'); return
    if Path(value).suffix.lower() not in IMG_EXT: err(file,ctx,'unsupported image extension'); return
    if not (IMAGES/value.removeprefix(prefix)).is_file(): err(file,ctx,'referenced image does not exist')

# Read a content JSON file and convert file/parser failures into build errors.
def read_json(rel):
    p=CONTENT/rel
    try: return json.loads(p.read_text(encoding='utf-8'))
    except FileNotFoundError: err(str(Path('content')/rel),'$','missing required file'); return {}
    except json.JSONDecodeError as e: err(str(Path('content')/rel),f'line {e.lineno}',f'malformed JSON: {e.msg}'); return {}

# Read CSV rows as dictionaries keyed by their header names. For example, a CSV
# heading named "question" becomes row['question'] inside the build.
def read_csv(rel):
    try:
        with (CONTENT/rel).open(newline='',encoding='utf-8') as fh: return list(csv.DictReader(fh))
    except FileNotFoundError: err('content/'+rel,'$','missing required file'); return []
    except csv.Error as e: err('content/'+rel,'$','malformed CSV: '+str(e)); return []

# Read gallery CSV separately because detailed conflict errors need the original
# line number and header shape. Parsing, normalisation and validation deliberately
# remain independent so each stage can be tested without rendering HTML.
def read_gallery_source(rel):
    file='content/'+rel; path=CONTENT/rel
    try:
        with path.open(newline='',encoding='utf-8') as fh:
            reader=csv.DictReader(fh); fieldnames=reader.fieldnames or []; rows=[]
            try:
                for row in reader: rows.append((reader.line_num,row))
            except csv.Error as e:
                err(file,f'line {reader.line_num} gallery "<unknown>"',f'malformed CSV: {e}. Fix: correct the quoting or column separators on this line')
            return fieldnames,rows
    except FileNotFoundError:
        err(file,'line 1 gallery "<file>"','missing required file. Fix: create the CSV with the documented gallery header')
        return [],[]

def gallery_record_key(row):
    """Deterministic internal identity; raw CSV IDs are never used alone."""
    return '|'.join((row.get('category',''),row.get('Platform',''),row.get('id',''),str(row.get('display_order',''))))

def gallery_equivalent_key(row):
    """Identity used to preserve a slide while changing responsive platform."""
    return '|'.join((row.get('category',''),row.get('id',''),str(row.get('display_order',''))))

def gallery_dom_id(record_key):
    slug=re.sub(r'[^a-z0-9]+','-',record_key.lower()).strip('-')[:58] or 'gallery-slide'
    digest=hashlib.sha1(record_key.encode('utf-8')).hexdigest()[:8]
    return f'gallery-slide-{slug}-{digest}'

def normalise_gallery_rows(source_rows):
    """Trim editable values and canonicalise recognised category/platform data."""
    category_names={value.lower():value for value in GALLERY_CATEGORIES}
    platform_names={value.lower():value for value in GALLERY_PLATFORMS}
    normalised=[]
    for line,raw in source_rows:
        row={field:((raw.get(field) or '').strip() if raw.get(field) is not None else '') for field in GALLERY_FIELDS}
        row['_source_row']=line
        row['_missing_cells']=[field for field in GALLERY_FIELDS if raw.get(field) is None]
        row['_extra_cells']=[str(value) for value in (raw.get(None) or [])]
        category_key=row['category'].lower(); platform_key=row['Platform'].lower()
        row['category']=category_names.get(category_key,row['category'])
        row['Platform']=platform_names.get(platform_key,row['Platform'])
        visible_key=row['visible'].lower(); row['_visible_valid']=visible_key in BOOL
        row['visible']=BOOL.get(visible_key,False)
        raw_order=row['display_order']; row['_order_valid']=bool(re.fullmatch(r'[1-9][0-9]*',raw_order))
        row['display_order']=int(raw_order) if row['_order_valid'] else None
        row['_record_key']=gallery_record_key(row)
        row['_equivalent_key']=gallery_equivalent_key(row)
        row['_dom_id']=gallery_dom_id(row['_record_key'])
        normalised.append(row)
    return normalised

def gallery_validation_error(file,row,explanation,fix,*,platform=None,conflict=None,earlier=None):
    category=row.get('category') or '<missing>'
    detail=[]
    if platform: detail.append(f'platform {platform}')
    if conflict: detail.append(conflict)
    if earlier: detail.append(f'earlier line {earlier["_source_row"]} (platform {earlier.get("Platform") or "<missing>"})')
    detail.append(explanation); detail.append('Fix: '+fix)
    err(file,f'line {row.get("_source_row",1)} gallery "{category}"','; '.join(detail))

def validate_gallery_rows(rel):
    """Validate gallery scope independently by category and responsive platform."""
    file='content/'+rel; fieldnames,source_rows=read_gallery_source(rel)
    missing=[field for field in GALLERY_FIELDS if field not in fieldnames]
    unexpected=[field for field in fieldnames if field not in GALLERY_FIELDS]
    file_row={'_source_row':1,'category':'<file>'}
    if missing:
        gallery_validation_error(file,file_row,'missing required column(s): '+', '.join(missing),'use exactly this header: '+','.join(GALLERY_FIELDS))
    if unexpected:
        gallery_validation_error(file,file_row,'unsupported column(s): '+', '.join(unexpected),'remove or rename these columns to match the documented schema')
    if missing: return []  # One schema error is clearer than one missing-field error per row.

    rows=normalise_gallery_rows(source_rows); exact_seen={}; accepted=[]
    for row in rows:
        platform=row.get('Platform') or '<missing>'
        if row['_missing_cells'] or row['_extra_cells']:
            problem=[]
            if row['_missing_cells']: problem.append('missing cell(s): '+', '.join(row['_missing_cells']))
            if row['_extra_cells']: problem.append('unexpected trailing cell(s): '+', '.join(row['_extra_cells']))
            gallery_validation_error(file,row,'malformed row ('+'; '.join(problem)+')','add or remove CSV cells so the row matches the header',platform=platform)
            continue
        if not row['id']:
            gallery_validation_error(file,row,'ID is missing','add a stable author-facing ID',platform=platform)
        if row['category'] not in GALLERY_CATEGORIES:
            gallery_validation_error(file,row,'unsupported or blank gallery category','use Experience or Equipment',platform=platform)
        if row['Platform'] not in GALLERY_PLATFORMS:
            gallery_validation_error(file,row,'unsupported or missing Platform value','use PC, Mobile or All (capitalisation is optional)')
        if not row['image']:
            gallery_validation_error(file,row,'image path is missing','add an existing image path under /content/images/',platform=platform)
        elif not row['image'].startswith('/content/images/'):
            gallery_validation_error(file,row,f'image path "{row["image"]}" is outside the required gallery content location','move the image under content/images and use /content/images/...',platform=platform)
        elif Path(row['image']).suffix.lower() not in IMG_EXT:
            gallery_validation_error(file,row,'image has an unsupported extension','use a JPG, JPEG, PNG, WebP or AVIF image under /content/images/',platform=platform)
        elif not (IMAGES/row['image'].removeprefix('/content/images/')).is_file():
            gallery_validation_error(file,row,f'image path "{row["image"]}" does not exist','add the file under content/images or correct the path',platform=platform)
        if not row['_visible_valid']:
            gallery_validation_error(file,row,'visible must be true or false','set visible to true or false',platform=platform)
        if not row['_order_valid']:
            gallery_validation_error(file,row,'display_order is missing or invalid','use a positive whole number such as 1, without decimals or trailing text',platform=platform)

        signature=tuple(row.get(field) for field in GALLERY_FIELDS)
        if signature in exact_seen:
            gallery_validation_error(file,row,'exact duplicate row', 'remove the duplicate or change the intended record',platform=platform,earlier=exact_seen[signature])
            row['_exact_duplicate']=True
            continue
        exact_seen[signature]=row; row['_exact_duplicate']=False; accepted.append(row)

    # Same-platform uniqueness and All-vs-specific overlap are category-scoped.
    id_seen={}; order_seen={}; prior_by_category={category:[] for category in GALLERY_CATEGORIES}
    for row in accepted:
        category=row.get('category'); platform=row.get('Platform'); rid=row.get('id'); order=row.get('display_order')
        if category not in GALLERY_CATEGORIES or platform not in GALLERY_PLATFORMS: continue
        if rid:
            key=(category,platform,rid)
            if key in id_seen:
                gallery_validation_error(file,row,'duplicate ID within the same gallery and platform','change one ID or move the intended variant to the other specific platform',platform=platform,conflict=f'conflicting ID "{rid}"',earlier=id_seen[key])
            else: id_seen[key]=row
        if order is not None:
            key=(category,platform,order)
            if key in order_seen:
                gallery_validation_error(file,row,'duplicate display_order within the same gallery and platform','give each row in this gallery/platform a unique positive display_order',platform=platform,conflict=f'conflicting order {order}',earlier=order_seen[key])
            else: order_seen[key]=row
        for earlier in prior_by_category[category]:
            if 'All' not in {platform,earlier['Platform']} or platform==earlier['Platform']: continue
            matches=[]
            if rid and rid==earlier.get('id'): matches.append(f'ID "{rid}"')
            if order is not None and order==earlier.get('display_order'): matches.append(f'order {order}')
            if matches:
                gallery_validation_error(file,row,'All overlaps a PC or Mobile row by '+(' and '.join(matches)),'change the All ID/order, or replace All with separate PC and Mobile rows',platform=platform,conflict='conflicting '+(' and '.join(matches)),earlier=earlier)
        prior_by_category[category].append(row)

    # Both tabs are intentionally always enabled, so both need effective content.
    visible=[row for row in accepted if row.get('visible')]
    for category in GALLERY_CATEGORIES:
        for mode in ('PC','Mobile'):
            if not any(row.get('category')==category and row.get('Platform') in {mode,'All'} for row in visible):
                category_row={'_source_row':1,'category':category}
                gallery_validation_error(file,category_row,f'category has no effective {mode} content',f'add at least one visible {mode} or All row for {category}',platform=mode)
    return sorted(visible,key=lambda row:(GALLERY_CATEGORIES.index(row['category']) if row['category'] in GALLERY_CATEGORIES else 99,row['display_order'] or 999999,row['_source_row']))

# Validate homepage structure, navigation contracts, image references and the
# content fragments reused by the packages page. "Validate" means check and
# report mistakes; this function does not create or alter the page.
def validate_home(h):
    f='content/homepage.json'
    for k in ['meta','navigation','navigation_groups','header','hero','reassurance','testimonials_section','how_it_works','gallery_section','faq_section','final_cta','footer','packages_page','addons_section']:
        if k not in h: err(f,k,'required top-level key is missing')
    req_text(f,h.get('hero',{}),'title','hero'); req_text(f,h.get('hero',{}),'description','hero')
    # SEO: Validate the single editable metadata block before it is used for
    # canonical URLs, social previews, structured data and the XML sitemap.
    meta=h.get('meta',{})
    for key in ['site_name','canonical_url','og_image','og_image_alt','logo','contact_email','locale']:
        req_text(f,meta,key,'meta')
    if not meta.get('canonical_url','').startswith('https://'):
        err(f,'meta.canonical_url','must be the public HTTPS site URL')
    image_ok(f,'meta.og_image',meta.get('og_image',''))
    image_ok(f,'meta.logo',meta.get('logo',''))
    pages=meta.get('pages',{})
    if set(pages) != set(SEO_PAGE_KEYS):
        err(f,'meta.pages',f'expected exactly {list(SEO_PAGE_KEYS)}')
    seen_paths=set()
    for page_key in SEO_PAGE_KEYS:
        page=pages.get(page_key,{})
        for key in ['path','title','description']:
            req_text(f,page,key,f'meta.pages.{page_key}')
        path=page.get('path','')
        if not path.startswith('/') or ('?' in path or '#' in path):
            err(f,f'meta.pages.{page_key}.path','must be a clean root-relative URL path')
        if path in seen_paths: err(f,f'meta.pages.{page_key}.path','duplicates another SEO page path')
        seen_paths.add(path)
    if h.get('hero',{}).get('primary_cta',{}).get('href')!='/packages/': err(f,'hero.primary_cta.href','expected /packages/')
    for key in ['light','dark']: image_ok(f,'hero.media.'+key,h.get('hero',{}).get('media',{}).get(key,''))
    for key in ['logo_light','logo_dark']: image_ok(f,'header.'+key,h.get('header',{}).get(key,''))
    labels=[n.get('label') for n in h.get('navigation',[])]
    if labels!=['Home','Packages','FAQ']: err(f,'navigation','expected Home, Packages and FAQ only')
    hrefs={n.get('label'):n.get('href') for n in h.get('navigation',[])}
    for label,expected in {'Home':'/','Packages':'/packages/','FAQ':'/#faq'}.items():
        if hrefs.get(label)!=expected: err(f,'navigation.'+label,f'expected {expected}')
    if h.get('header',{}).get('availability_cta',{}).get('href')!='/contact/?intent=booking': err(f,'header.availability_cta.href','expected /contact/?intent=booking')
    expected_groups=[['How it works','Shared Moments','FAQ'],['Packages','Make your own'],['Contact','Terms of Service','Privacy Policy']]
    expected_hrefs={'How it works':'/#how-it-works','Shared Moments':'/#gallery','FAQ':'/#faq','Packages':'/packages/','Make your own':'/packages/#make-your-own','Contact':'/contact/?intent=question','Terms of Service':'/terms/','Privacy Policy':'/privacy/'}
    groups=h.get('navigation_groups',[])
    if len(groups)!=3: err(f,'navigation_groups','expected exactly 3 dropdown groups')
    seen=[]
    for gi,g in enumerate(groups):
        got=[x.get('label') for x in g.get('links',[])]
        if gi < 3 and got!=expected_groups[gi]: err(f,f'navigation_groups[{gi}].links',f'expected {expected_groups[gi]}')
        for link in g.get('links',[]):
            label=link.get('label'); href=link.get('href'); seen.append(label)
            if expected_hrefs.get(label)!=href: err(f,f'navigation_groups.{label}',f'expected href {expected_hrefs.get(label)}')
    if len(seen)!=len(set(seen)): err(f,'navigation_groups','duplicate navigation labels')
    if h.get('addons_section',{}).get('accordion_label')!='Make it your own': err(f,'addons_section.accordion_label','expected Make it your own')
    sec=h.get('hero',{}).get('secondary_cta',{})
    if sec.get('label')!='See the experience': err(f,'hero.secondary_cta.label','expected See the experience')
    if sec.get('href')!='#gallery': err(f,'hero.secondary_cta.href','expected #gallery')
    step_ids=set(); allowed_pos={'center','top','bottom','left','right'}
    for i,step in enumerate(h.get('how_it_works',{}).get('steps',[])):
        ctx=f'how_it_works.steps[{i}]'; sid=req_text(f,step,'id',ctx)
        if sid in step_ids: err(f,ctx,'duplicate step ID')
        step_ids.add(sid); req_text(f,step,'title',ctx); req_text(f,step,'description',ctx)
        image=step.get('image','').strip()
        if image:
            image_ok(f,ctx+'.image',image)
            req_text(f,step,'image_alt',ctx)
        pos=step.get('image_position','center')
        if pos not in allowed_pos: err(f,ctx+'.image_position','expected one of center, top, bottom, left or right')
    pp=h.get('packages_page',{})
    for key in ['meta_title','hero','intro','guidance','shared_enquiry','cta']:
        if key not in pp: err(f,'packages_page.'+key,'required Packages-page content is missing')
    req_text(f,pp.get('hero',{}),'heading','packages_page.hero'); req_text(f,pp.get('hero',{}),'description','packages_page.hero')
    se=pp.get('shared_enquiry',{})
    for key in ['heading','description','button_label','href']: req_text(f,se,key,'packages_page.shared_enquiry')
    if se.get('button_label')!='Ask about packages': err(f,'packages_page.shared_enquiry.button_label','expected Ask about packages')
    if se.get('href')!='/contact/?intent=question': err(f,'packages_page.shared_enquiry.href','expected /contact/?intent=question')

    ph=pp.get('hero',{})
    image_ok(f,'packages_page.hero.fallback_image',ph.get('fallback_image',''))
    image_ok(f,'packages_page.hero.fallback_image_dark',ph.get('fallback_image_dark',ph.get('fallback_image','')))
    if ph.get('image','').strip(): image_ok(f,'packages_page.hero.image',ph.get('image',''))
    for i,item in enumerate(h.get('reassurance',[])):
        icon=item.get('icon','').strip()
        if icon: image_ok(f,f'reassurance[{i}].icon',icon)
    gallery_tabs=h.get('gallery_section',{}).get('tabs',{})
    for category in GALLERY_CATEGORIES:
        tab=gallery_tabs.get(category,{})
        if not isinstance(tab,dict):
            err(f,f'gallery_section.tabs.{category}','must contain label and subtitle text')
            continue
        req_text(f,tab,'label',f'gallery_section.tabs.{category}')
        req_text(f,tab,'subtitle',f'gallery_section.tabs.{category}')

# Validate package records against PACKAGE_FACTS and return visible packages in
# their requested display order. The private _order key is build-only metadata.
def validate_packages(data):
    rows=data.get('packages',data if isinstance(data,list) else []); out=[]; ids=set(); orders=set(); f='content/packages.json'
    if not isinstance(rows,list): err(f,'packages','must be a list'); return []
    for p in rows:
        ctx=f'package "{p.get("id","")}"'; pid=req_text(f,p,'id',ctx)
        if pid in ids: err(f,ctx,'duplicate ID')
        ids.add(pid)
        if pid not in PACKAGE_FACTS: err(f,ctx,'invalid package ID')
        else:
            facts=PACKAGE_FACTS[pid]
            for key in ['name','label','price','duration','capacity']:
                if p.get(key)!=facts[key]: err(f,ctx,f'{key} must remain {facts[key]}')
            if p.get('included')!=facts['included']: err(f,ctx,'package business-detail inconsistencies in included list')
        for key in ['summary','addon_intro','enquiry_note','enquiry_button','details_button']: req_text(f,p,key,ctx)
        if not isinstance(p.get('visible'),bool): err(f,ctx,'visible must be JSON true or false')
        try: order=int(p.get('display_order')); assert order>0
        except Exception: err(f,ctx,'display_order must be a positive integer'); order=999999
        if order in orders: err(f,ctx,'duplicate display_order')
        orders.add(order); p['_order']=order
        exp=p.get('expanded',{})
        for key in ['overview','suited_to','age_guidance','room_guidance']: req_text(f,exp,key,ctx+'.expanded')
        if p.get('visible'): out.append(p)
    if ids != {'onyx','jade'}: err(f,'packages','both ONYX and JADE must exist')
    return sorted(out,key=lambda r:r['_order'])

# Apply common CSV rules plus type-specific checks for add-ons, testimonials and
# FAQs. Gallery records use their own category/platform-aware validator above.
# This shared function avoids repeating the same ID,
# visibility and display-order checks for every CSV. Invisible rows are checked
# for correctness but deliberately omitted from the finished website.
def validate_rows(rel, required, kind, pkg_ids=None):
    rows=read_csv(rel); out=[]; ids=set(); orders=set(); file='content/'+rel
    for n,r in enumerate(rows,start=2):
        ctx=f'row {n}'; rid=(r.get('id') or '').strip()
        if not rid: err(file,ctx,'missing id'); continue
        if rid in ids: err(file,ctx,'duplicate ID')
        ids.add(rid); visible=req_bool(file,r,'visible',ctx); r['_order']=req_order(file,r,ctx,orders)
        for key in required:
            if visible and not (r.get(key) or '').strip(): err(file,ctx,f'{key} is required')
        if kind=='addon' and r.get('available_for') not in {'onyx','jade','both'}: err(file,ctx,f'unknown available_for value "{r.get("available_for")}"; expected onyx, jade or both')
        if kind=='testimonial' and visible:
            if r.get('package') and r.get('package') not in pkg_ids: err(file,ctx,'invalid testimonial package reference')
            image_ok(file,ctx+'.image',r.get('image',''))
        if kind=='faq':
            label=(r.get('link_label') or '').strip(); href=(r.get('link_href') or '').strip()
            if bool(label) != bool(href): err(file,ctx,'link_label and link_href must both be present or both be empty')
            if href and href not in {'/terms/','/privacy/','/#booking','/packages/','/#faq'}: err(file,ctx,'unsupported local FAQ link route')
        if visible: out.append(r)
    return sorted(out,key=lambda r:r['_order'])

# Validate the block-based terms/privacy schema before any legal HTML is built.
def validate_legal(rel):
    d=read_json(Path('legal')/(rel+'.json')); file=f'content/legal/{rel}.json'
    req_text(file,d,'title','page')
    for optional_key in ['last_updated','draft_warning','summary']:
        if optional_key in d: req_text(file,d,optional_key,'page')
    sections=d.get('sections')
    if not isinstance(sections,list) or not sections:
        err(file,'sections','must be a non-empty list')
        return d
    section_ids=set()
    for section_index,section in enumerate(sections):
        ctx=f'sections[{section_index}]'
        if not isinstance(section,dict):
            err(file,ctx,'must be an object')
            continue
        section_id=req_text(file,section,'id',ctx)
        req_text(file,section,'title',ctx)
        if section_id in section_ids: err(file,ctx+'.id',f'duplicate section ID "{section_id}"')
        section_ids.add(section_id)
        blocks=section.get('blocks')
        if not isinstance(blocks,list) or not blocks:
            err(file,ctx+'.blocks','must be a non-empty list')
            continue
        for block_index,block in enumerate(blocks):
            block_ctx=f'{ctx}.blocks[{block_index}]'
            if not isinstance(block,dict):
                err(file,block_ctx,'must be an object')
                continue
            block_type=block.get('type')
            if block_type not in LEGAL_BLOCK_TYPES:
                err(file,block_ctx+'.type',f'expected one of {sorted(LEGAL_BLOCK_TYPES)}')
                continue
            if block_type=='paragraph':
                req_text(file,block,'text',block_ctx)
            elif block_type=='list':
                if block.get('style') not in {'bulleted','numbered'}: err(file,block_ctx+'.style','must be bulleted or numbered')
                items=block.get('items')
                if not isinstance(items,list) or not items: err(file,block_ctx+'.items','must be a non-empty list')
                else:
                    for item_index,item in enumerate(items):
                        if not isinstance(item,str) or not item.strip(): err(file,f'{block_ctx}.items[{item_index}]','must be non-empty text')
            elif block_type=='definitions':
                items=block.get('items')
                if not isinstance(items,list) or not items: err(file,block_ctx+'.items','must be a non-empty list')
                else:
                    for item_index,item in enumerate(items):
                        item_ctx=f'{block_ctx}.items[{item_index}]'
                        req_text(file,item,'term',item_ctx); req_text(file,item,'text',item_ctx)
                        href=item.get('href') if isinstance(item,dict) else None
                        if href is not None:
                            req_text(file,item,'href',item_ctx)
                            if not href.startswith(('https://','mailto:')): err(file,item_ctx+'.href','must begin with https:// or mailto:')
            elif block_type=='fields':
                items=block.get('items')
                if not isinstance(items,list) or not items: err(file,block_ctx+'.items','must be a non-empty list')
                else:
                    for item_index,item in enumerate(items):
                        if not isinstance(item,str) or not item.strip(): err(file,f'{block_ctx}.items[{item_index}]','must be non-empty text')
            elif block_type=='table':
                req_text(file,block,'label',block_ctx)
                columns=block.get('columns'); rows=block.get('rows')
                if not isinstance(columns,list) or not columns: err(file,block_ctx+'.columns','must be a non-empty list')
                else:
                    column_keys=set()
                    for column_index,column in enumerate(columns):
                        column_ctx=f'{block_ctx}.columns[{column_index}]'
                        key=req_text(file,column,'key',column_ctx); req_text(file,column,'label',column_ctx)
                        if key in column_keys: err(file,column_ctx+'.key',f'duplicate column key "{key}"')
                        column_keys.add(key)
                    if not isinstance(rows,list) or not rows: err(file,block_ctx+'.rows','must be a non-empty list')
                    else:
                        for row_index,row in enumerate(rows):
                            row_ctx=f'{block_ctx}.rows[{row_index}]'
                            if not isinstance(row,dict): err(file,row_ctx,'must be an object'); continue
                            for key in column_keys: req_text(file,row,key,row_ctx)
    return d
# ================================================================
# Build output helpers
# ================================================================

# Recreate dist/ from scratch, copy browser code/assets, then copy only approved
# content image formats. Never hand-edit dist/: the next build deletes it.
# shutil.rmtree removes the previous generated folder; copytree then copies the
# complete static/ source tree before original content images are added.
def copy_assets():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(); shutil.copytree(STATIC,DIST,dirs_exist_ok=True)
    destinations=(DIST/'content'/'images',DIST/'assets'/'images')
    for p in IMAGES.rglob('*'):
        if p.is_file() and p.suffix.lower() in IMG_EXT:
            for dest in destinations:
                d=dest/p.relative_to(IMAGES); d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,d)

# SEO: Generate crawler discovery files from the same canonical route records
# used by page metadata. This prevents robots.txt, sitemap.xml and HTML links
# from drifting apart when a route changes. The demo page is intentionally
# excluded because it contains example content and is marked noindex.
def write_seo_files(home):
    pages=home['meta']['pages']
    urls=''.join(f'  <url><loc>{esc(seo_absolute_url(home,pages[key]["path"]))}</loc></url>\n' for key in SEO_PAGE_KEYS)
    sitemap='<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+urls+'</urlset>\n'
    robots='''# SEO: Search crawlers may access the public site.\nUser-agent: *\nAllow: /\n\n# SEO: Canonical URL discovery.\nSitemap: {sitemap}\n'''.format(sitemap=seo_absolute_url(home,'/sitemap.xml'))
    (DIST/'sitemap.xml').write_text(sitemap,encoding='utf-8')
    (DIST/'robots.txt').write_text(robots,encoding='utf-8')
# ================================================================
# Shared page chrome
# ================================================================

# Hash links need a route prefix when rendered outside the homepage.
def rel_href(href,prefix): return (prefix+href if href.startswith('#') else href)

# Build the grouped links shown inside the complete navigation menu.
def mega_nav(home):
    cols=[]
    for i,g in enumerate(home.get('navigation_groups',[]),1):
        links=''.join(f'<li><a href="{esc(l["href"])}">{esc(l["label"])}</a></li>' for l in g.get('links',[]))
        cols.append(f'<div class="site-menu__group"><p class="site-menu__heading">{esc(g.get("heading","Group "+str(i)))}</p><ul>{links}</ul></div>')
    return ''.join(cols)

# Retained helper from the earlier compact navigation. The current header uses
# mega_nav(); keep this here only while older markup may still reference it.
def nav(home,prefix=''):
    items=list(home['navigation'])
    links=''.join(f'<a class="{"is-active" if (prefix=="" and i["label"]=="Home") or (prefix and i["label"]=="Packages" and prefix=="/packages") else ""}" href="{rel_href(i["href"],prefix)}">{esc(i["label"])}</a>' for i in items)
    return links

# Render the footer shared by every public page.
def footer(home,prefix=''):
    links=''.join(f'<a href="{rel_href(l["href"],prefix)}">{esc(l["label"])}</a>' for l in home['footer']['links'])
    return f'<footer class="site-footer"><p>{esc(home["footer"]["tagline"])}</p><nav aria-label="Footer navigation">{links}</nav></footer>'

# Render the sticky header, theme logos, theme switch and menu controls.
def header(home,prefix=''):
    c=home['header']['availability_cta']
    return f"""<header class="site-header"><nav class="nav-shell" aria-label="Main navigation"><a class="brand" href="/"><span class="brand__mark"><img class="brand__logo brand__logo--light" src="{home['header']['logo_light']}" alt="Party.LAN" width="168" height="58"><img class="brand__logo brand__logo--dark" src="{home['header']['logo_dark']}" alt="" aria-hidden="true" width="168" height="58"></span></a><a class="button button--key button--small header-cta" href="{rel_href(c['href'],prefix)}">{esc(c['label'])}</a><button class="button button--secondary button--icon theme-toggle" type="button" aria-pressed="false" aria-label="Light mode active. Switch to dark mode" title="Light mode active. Switch to dark mode"><span class="theme-toggle__icon" aria-hidden="true">☀</span></button><div class="menu-anchor"><button class="button button--secondary button--icon menu-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open navigation menu"><span class="menu-toggle__bars" aria-hidden="true"><span></span><span></span><span></span></span></button><div class="site-menu" id="site-menu" aria-label="Complete navigation"><div class="site-menu__panel">{mega_nav(home)}</div></div></div></nav></header>"""

# ================================================================
# SEO: metadata, canonical URLs and structured data
# ================================================================
# Edit the public wording and identity values in content/homepage.json under
# "meta". Keep implementation changes inside this clearly labelled section so
# all search/share behaviour remains easy to audit in one place.

# Convert a site-relative path into one absolute HTTPS URL. Search metadata must
# not publish relative image, logo or canonical references.
def seo_absolute_url(home,path):
    return home['meta']['canonical_url'].rstrip('/')+'/'+path.lstrip('/')

# Return the approved metadata record for one public route.
def seo_page(home,page_key): return home['meta']['pages'][page_key]

# Safely place JSON-LD inside HTML. The replacements stop content text from
# accidentally closing the script element while preserving valid JSON.
def seo_json_ld(data):
    payload=json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    return f'<script type="application/ld+json">{payload}</script>'

# Describe the Party.LAN identity without inventing an address, phone number,
# reviews, opening hours or service area that has not been approved in content.
# Organization is intentionally used instead of LocalBusiness until a public
# business address or confirmed service-area profile is available.
def seo_organization(home):
    m=home['meta']; base=seo_absolute_url(home,'/')
    return {
        '@type':'Organization','@id':base+'#organization','name':m['site_name'],
        'url':base,'description':seo_page(home,'home')['description'],
        'logo':{'@type':'ImageObject','url':seo_absolute_url(home,m['logo'])},
        'image':seo_absolute_url(home,m['og_image']),'email':m['contact_email'],
        'contactPoint':{'@type':'ContactPoint','contactType':'customer service','email':m['contact_email'],'availableLanguage':'English'},
    }

# Build the common Organization, WebSite and page entities. Page-specific
# entities are appended by the homepage and packages helpers below.
def seo_graph(home,page_key,page_type='WebPage',extra=None):
    m=home['meta']; page=seo_page(home,page_key); base=seo_absolute_url(home,'/'); url=seo_absolute_url(home,page['path'])
    graph=[
        seo_organization(home),
        {'@type':'WebSite','@id':base+'#website','url':base,'name':m['site_name'],'inLanguage':'en-GB','publisher':{'@id':base+'#organization'}},
        {'@type':page_type,'@id':url+'#webpage','url':url,'name':page['title'],'description':page['description'],'inLanguage':'en-GB','isPartOf':{'@id':base+'#website'},'about':{'@id':base+'#organization'},'primaryImageOfPage':{'@type':'ImageObject','url':seo_absolute_url(home,m['og_image'])}},
    ]
    graph.extend(extra or [])
    return {'@context':'https://schema.org','@graph':graph}

# FAQ answers already visible in the homepage accordion become machine-readable
# Question/Answer entities. Never place hidden or unapproved claims here.
def seo_home_graph(home,faq_rows):
    url=seo_absolute_url(home,seo_page(home,'home')['path'])
    questions=[{'@type':'Question','name':r['question'],'acceptedAnswer':{'@type':'Answer','text':r['answer']}} for r in faq_rows]
    faq_entity={'@type':'FAQPage','@id':url+'#faq','url':url+'#faq','isPartOf':{'@id':url+'#webpage'},'mainEntity':questions}
    return seo_graph(home,'home','WebPage',[faq_entity])

# Package records become accurate Service/Offer entities. This is descriptive
# schema only; it does not claim availability, ratings or stock information.
def seo_packages_graph(home,pkgs):
    page=seo_page(home,'packages'); url=seo_absolute_url(home,page['path']); base=seo_absolute_url(home,'/')
    services=[]; item_refs=[]
    for position,pkg in enumerate(pkgs,1):
        service_id=f'{url}#service-{pkg["id"]}'
        services.append({'@type':'Service','@id':service_id,'name':f'{pkg["name"]} — {pkg["label"]}','description':pkg['summary'],'provider':{'@id':base+'#organization'},'offers':{'@type':'Offer','url':f'{url}#package-panel-{pkg["id"]}','price':pkg['price'].lstrip('£'),'priceCurrency':'GBP','description':f'{pkg["duration"]}; {pkg["capacity"]}'}})
        item_refs.append({'@type':'ListItem','position':position,'item':{'@id':service_id}})
    item_list={'@type':'ItemList','@id':url+'#packages','name':'Party.LAN gaming party packages','itemListElement':item_refs}
    return seo_graph(home,'packages','CollectionPage',[item_list,*services])

# Render complete page-specific search and social metadata. The demo route uses
# index=False, keeping example testimonials out of search results and sitemaps.
def head(home,page_key='home',structured_data=None,index=True,canonical_path=None):
    m=home['meta']; page=seo_page(home,page_key); path=canonical_path or page['path']; canonical=seo_absolute_url(home,path); image=seo_absolute_url(home,m['og_image'])
    robots='index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1' if index else 'noindex,follow'
    schema='' if structured_data is False else seo_json_ld(structured_data or seo_graph(home,page_key))
    return f'''<!doctype html><html lang="en-GB"><head>
<!-- SEO: Core indexation and canonical metadata. Edit values in content/homepage.json > meta. -->
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(page['title'])}</title><meta name="description" content="{esc(page['description'])}"><meta name="robots" content="{robots}"><link rel="canonical" href="{esc(canonical)}"><link rel="alternate" hreflang="en-GB" href="{esc(canonical)}"><link rel="alternate" hreflang="x-default" href="{esc(canonical)}">
<!-- SEO: Open Graph and X/Twitter link-preview metadata. -->
<meta property="og:type" content="website"><meta property="og:site_name" content="{esc(m['site_name'])}"><meta property="og:locale" content="{esc(m['locale'])}"><meta property="og:title" content="{esc(page['title'])}"><meta property="og:description" content="{esc(page['description'])}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{esc(image)}"><meta property="og:image:width" content="1576"><meta property="og:image:height" content="941"><meta property="og:image:alt" content="{esc(m['og_image_alt'])}"><meta name="twitter:card" content="summary_large_image"><meta name="twitter:title" content="{esc(page['title'])}"><meta name="twitter:description" content="{esc(page['description'])}"><meta name="twitter:image" content="{esc(image)}"><meta name="twitter:image:alt" content="{esc(m['og_image_alt'])}">
<!-- SEO: Schema.org JSON-LD describing the business and this page. -->
{schema}<meta name="theme-color" content="{m['theme_color_light']}"><link rel="icon" href="/content/images/Logo_fav_icon.png?v=3" type="image/png" sizes="160x159"><link rel="apple-touch-icon" href="/content/images/Logo_fav_icon.png?v=3"><script>(function(){{try{{var s=localStorage.getItem('partyLanTheme');document.documentElement.dataset.theme=s||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}}catch(e){{document.documentElement.dataset.theme='light';}}}}());</script><link rel="stylesheet" href="/css/styles.css?v={STYLESHEET_VERSION}"></head>'''

# ================================================================
# Contact form rendering
# ================================================================

# Render the reusable enquiry form. "Render" here means return a long HTML text
# string. It looks dense because the complete form is kept in one f-string, but
# the browser reads it as the normal nested <form>, <label> and <input> elements.
# The same form is inserted on the contact page and inside the packages panel.
# Without a Web3Forms key, submission is disabled and direct email remains.
def contact_form(form_id='contact-form', default_intent='question', default_package='unsure', inline=False, access_key='', allow_event_disclosure=False):
    event_hidden=' hidden' if default_intent=='question' and not inline else ''
    online='true' if access_key else 'false'
    submit_disabled='' if access_key else ' disabled'
    disclosure_html='<div class="field field--full contact-disclosure"><button class="button button--rollout quiet-button" type="button" data-event-toggle aria-expanded="false" data-label-closed="Add event details" data-label-open="Hide event details"><span class="rollout-control__label" data-rollout-label>Add event details</span><span class="rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></button></div>' if allow_event_disclosure else ''
    return f"""<div class=\"contact-form-shell\" data-contact-component data-default-intent=\"{esc(default_intent)}\" data-default-package=\"{esc(default_package)}\" data-online-enabled=\"{online}\"><div class=\"contact-status\" data-contact-status role=\"status\" aria-live=\"polite\" tabindex=\"-1\"></div><form class=\"contact-form\" id=\"{esc(form_id)}\" data-contact-form action=\"https://api.web3forms.com/submit\" method=\"POST\"><input type=\"hidden\" name=\"access_key\" value=\"{access_key}\"><input type=\"hidden\" name=\"subject\" value=\"New Party.LAN question\"><input type=\"hidden\" name=\"from_name\" value=\"Party.LAN Website\"><input type=\"checkbox\" name=\"botcheck\" tabindex=\"-1\" aria-hidden=\"true\" autocomplete=\"off\" class=\"form-honeypot\"><div class=\"contact-form__grid\"><div class=\"field field--full\"><label for=\"{esc(form_id)}-intent\">Enquiry type</label><select id=\"{esc(form_id)}-intent\" name=\"intent\" required aria-describedby=\"{esc(form_id)}-intent-error\"><optgroup label=\"Party enquiries\"><option value=\"booking\">Booking enquiry</option><option value=\"party_question\">General party question</option></optgroup><optgroup label=\"Other enquiries\"><option value=\"collaboration\">Work with Party.LAN</option><option value=\"venue_partnership\">Venue or business partnership</option><option value=\"media\">Press or media enquiry</option><option value=\"other\">Other enquiry</option></optgroup></select><p class=\"field-error\" id=\"{esc(form_id)}-intent-error\" data-error-for=\"intent\"></p></div><div class=\"field\"><label for=\"{esc(form_id)}-name\">Name</label><input id=\"{esc(form_id)}-name\" name=\"name\" autocomplete=\"name\" required minlength=\"2\" maxlength=\"80\" aria-describedby=\"{esc(form_id)}-name-error\"><p class=\"field-error\" id=\"{esc(form_id)}-name-error\" data-error-for=\"name\"></p></div><div class=\"field\"><label for=\"{esc(form_id)}-email\">Email</label><input id=\"{esc(form_id)}-email\" name=\"email\" type=\"email\" autocomplete=\"email\" required maxlength=\"120\" aria-describedby=\"{esc(form_id)}-email-error\"><p class=\"field-error\" id=\"{esc(form_id)}-email-error\" data-error-for=\"email\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-date\">Preferred date</label><input id=\"{esc(form_id)}-date\" name=\"preferred_date\" type=\"date\" aria-describedby=\"{esc(form_id)}-date-error\"><p class=\"field-error\" id=\"{esc(form_id)}-date-error\" data-error-for=\"preferred_date\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-alt-date\">Alternative date</label><input id=\"{esc(form_id)}-alt-date\" name=\"alternative_date\" type=\"date\" aria-describedby=\"{esc(form_id)}-alt-date-error\"><p class=\"field-error\" id=\"{esc(form_id)}-alt-date-error\" data-error-for=\"alternative_date\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-location\">Town or postcode</label><input id=\"{esc(form_id)}-location\" name=\"location\" autocomplete=\"postal-code\" maxlength=\"100\" aria-describedby=\"{esc(form_id)}-location-error\"><p class=\"field-error\" id=\"{esc(form_id)}-location-error\" data-error-for=\"location\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-players\">Number of players</label><input id=\"{esc(form_id)}-players\" name=\"players\" type=\"number\" min=\"1\" max=\"40\" inputmode=\"numeric\" aria-describedby=\"{esc(form_id)}-players-error\"><p class=\"field-error\" id=\"{esc(form_id)}-players-error\" data-error-for=\"players\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-package\">Package</label><select id=\"{esc(form_id)}-package\" name=\"package\" aria-describedby=\"{esc(form_id)}-package-error\"><option value=\"unsure\">Not sure yet</option><option value=\"onyx\">ONYX</option><option value=\"jade\">JADE</option></select><p class=\"field-error\" id=\"{esc(form_id)}-package-error\" data-error-for=\"package\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-phone\">Phone</label><input id=\"{esc(form_id)}-phone\" name=\"phone\" type=\"tel\" autocomplete=\"tel\" maxlength=\"30\" aria-describedby=\"{esc(form_id)}-phone-error\"><p class=\"field-error\" id=\"{esc(form_id)}-phone-error\" data-error-for=\"phone\"></p></div><div class=\"field field--full\"><label for=\"{esc(form_id)}-message\">Message</label><textarea id=\"{esc(form_id)}-message\" name=\"message\" rows=\"5\" maxlength=\"2000\" aria-describedby=\"{esc(form_id)}-message-help {esc(form_id)}-message-error\"></textarea><p class=\"field-help\" id=\"{esc(form_id)}-message-help\">For booking enquiries, a preferred date or venue detail can provide enough context.</p><p class=\"field-error\" id=\"{esc(form_id)}-message-error\" data-error-for=\"message\"></p></div>{disclosure_html}<div class=\"field field--full privacy-check\"><label class=\"privacy-check__label\"><input name=\"privacy\" type=\"checkbox\" required aria-describedby=\"{esc(form_id)}-privacy-error\"><span class=\"privacy-check__copy\">I have read the <a href="/privacy/">Privacy Policy</a> and understand that Party.LAN will use these details to respond to my enquiry.</span></label><p class=\"field-error\" id=\"{esc(form_id)}-privacy-error\" data-error-for=\"privacy\"></p></div><div class=\"contact-form__actions\"><button class=\"button button--key contact-submit\" type=\"submit\" data-submit-label=\"Send enquiry\"{submit_disabled}>Send enquiry</button><a class=\"button button--secondary direct-email\" href=\"mailto:hello@partylan.co.uk\"><span>Email Party.LAN directly</span><small>hello@partylan.co.uk</small></a></div></div></form><div class=\"contact-success\" data-contact-success hidden tabindex=\"-1\"><h3>Thanks — your enquiry has been sent.</h3><p>We’ll get back to you as soon as possible.</p><button class=\"button button--secondary\" type=\"button\" data-send-another>Send another enquiry</button></div></div>"""

# Render whichever parts of the optional Header/Subtext pair contain text.
# Empty values do not create empty semantic elements or an unnecessary overlay.
def media_caption(header, subtext, tag='div', class_name=''):
    header=(header or '').strip(); subtext=(subtext or '').strip()
    parts=[]
    if header: parts.append(f'<h3 class="media-caption__header">{esc(header)}</h3>')
    if subtext: parts.append(f'<p class="media-caption__subtext">{esc(subtext)}</p>')
    if not parts: return ''
    classes='media-caption'+((' '+class_name) if class_name else '')
    return f'<{tag} class="{classes}">{"".join(parts)}</{tag}>'

# Convert testimonial CSV rows into accessible slides and dot controls.
def testimonial_section(home, rows):
    if not rows: return ''
    def text(r):
        if 'Header' in r or 'Subtext' in r:
            return (r.get('Header') or '').strip(),(r.get('Subtext') or '').strip()
        header='“'+(r.get('quote') or '').strip()+'”'
        person=(r.get('name') or '').strip()+(', age '+r['age'].strip() if (r.get('age') or '').strip() else '')
        context=' · '.join(v for v in [(r.get('location') or '').strip(),(r.get('package') or '').strip()] if v)
        return header,' · '.join(v for v in [person,context] if v)
    slides=''.join(f'<article class="testimonial-slide {"is-active" if i==0 else ""}" aria-hidden="{"false" if i==0 else "true"}"><img src="{r["image"]}" alt="{esc(r["alt"])}">{media_caption(*text(r),class_name="testimonial-slide__content")}</article>' for i,r in enumerate(rows))
    dots=''.join(f'<button class="testimonial-dot" type="button" aria-label="Show testimonial {i+1} of {len(rows)}"><span></span></button>' for i,_ in enumerate(rows))
    s=home['testimonials_section']; return f'<section class="section testimonials" id="testimonials" aria-labelledby="testimonials-title"><div class="section-heading reveal"><p class="eyebrow">{esc(s["eyebrow"])}</p><h2 id="testimonials-title">{esc(s["heading"])}</h2><p>{esc(s["description"])}</p></div><div class="testimonial-stage" role="region" aria-roledescription="carousel"><div class="testimonial-track">{slides}</div><button class="showcase-toggle testimonial-toggle" type="button" aria-pressed="false" aria-label="Pause testimonials"><span aria-hidden="true">Ⅱ</span></button><div class="testimonial-dots">{dots}</div></div></section>'
def gallery_tab_icon(category):
    if category=='experience':
        return '<svg viewBox="0 0 24 24" focusable="false"><circle cx="12" cy="7" r="3"/><circle cx="5.5" cy="9" r="2.3"/><circle cx="18.5" cy="9" r="2.3"/><path d="M7 19v-2.2A5 5 0 0 1 12 12a5 5 0 0 1 5 4.8V19M2 18v-1.4A3.6 3.6 0 0 1 5.6 13h1.1M22 18v-1.4a3.6 3.6 0 0 0-3.6-3.6h-1.1"/></svg>'
    return '<svg viewBox="0 0 24 24" focusable="false"><rect x="3" y="4" width="18" height="13" rx="1.5"/><path d="M9 21h6M12 17v4"/></svg>'

# Render one accessible tab system and a single responsive slider controller.
# Slide records stay as inert JSON until the selected category/platform is known,
# preventing the browser from downloading unused desktop or mobile variants.
def showcase(home,gallery):
    records=[{'authorId':r['id'],'category':r['category'],'platform':r['Platform'],'image':r['image'],'header':r.get('Header',''),'subtext':r.get('Subtext',''),'order':r['display_order'],'recordKey':r['_record_key'],'equivalentKey':r['_equivalent_key'],'domId':r['_dom_id']} for r in gallery]
    payload=json.dumps(records,ensure_ascii=False,separators=(',',':')).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e')
    g=home['gallery_section']
    def tab(category,selected):
        content=g['tabs'][category]
        return f'<button class="gallery-tab" type="button" role="tab" id="gallery-tab-{category}" aria-controls="gallery-panel-{category}" aria-selected="{str(selected).lower()}" tabindex="{0 if selected else -1}" data-gallery-tab="{category}"><span class="gallery-tab__icon" aria-hidden="true">{gallery_tab_icon(category)}</span><span class="gallery-tab__copy"><span class="gallery-tab__title">{esc(content["label"])}</span><span class="gallery-tab__subtitle">{esc(content["subtitle"])}</span></span></button>'
    switch='<span class="gallery-tabs__switch" aria-hidden="true"><svg viewBox="0 0 24 24" focusable="false"><path d="M7 8h11m0 0-3-3m3 3-3 3M17 16H6m0 0 3 3m-3-3 3-3"/></svg></span>'
    panels=''.join(f'<div class="showcase-panel" id="gallery-panel-{category}" role="tabpanel" aria-labelledby="gallery-tab-{category}" data-gallery-panel="{category}"{" hidden" if category!="experience" else ""}><div class="showcase-track" data-gallery-track="{category}"></div></div>' for category in GALLERY_CATEGORIES)
    return f'<section class="section showcase-section" id="gallery" aria-labelledby="gallery-title"><div class="section-intro section-heading reveal"><p class="eyebrow">{esc(g["eyebrow"])}</p><h2 id="gallery-title">{esc(g["heading"])}</h2><p>{esc(g["description"])}</p></div><div class="gallery-tabs" role="tablist" aria-label="Choose gallery view">{tab("experience",True)}{switch}{tab("equipment",False)}</div><div class="showcase" role="region" aria-label="Party.LAN image showcase" data-gallery-mobile-query="{esc(GALLERY_MOBILE_QUERY)}">{panels}<button class="showcase-toggle" type="button" aria-pressed="false" aria-label="Pause gallery"><span aria-hidden="true">Ⅱ</span></button><div class="showcase-feedback" aria-hidden="true"></div><div class="showcase-indicators" aria-label="Choose gallery image"></div></div><script class="gallery-data" type="application/json">{payload}</script></section>'
# Render numbered "How it works" cards, with a placeholder when no image exists.
def steps(home):
    out=[]
    for i,s in enumerate(home['how_it_works']['steps'],1):
        pos=esc(s.get('image_position','center'))
        if s.get('image','').strip():
            media=f'<img src="{esc(s["image"])}" alt="{esc(s.get("image_alt",""))}" loading="lazy" style="object-position:{pos}">'
        else:
            media=f'<div class="step-card__placeholder" aria-hidden="true"><span>{i}</span></div>'
        out.append(f'<article class="step-card reveal"><div class="step-card__media">{media}</div><div class="step-card__body"><span class="step-card__number">{i}</span><h3>{esc(s["title"])}</h3><p>{esc(s["description"])}</p></div></article>')
    return ''.join(out)
# Render the landing FAQ accordion and optional related-page buttons.
def faq(home, rows):
    parts=[]
    for r in rows:
        link=''
        if (r.get('link_label') or '').strip():
            link=f'<p class="faq-item__link"><a class="button button--small faq-item__button-link" href="{esc(r["link_href"])}">{esc(r["link_label"])}</a></p>'
        parts.append(f'<div class="faq-item"><h3><button aria-expanded="false" aria-controls="faq-{r["id"]}" id="faq-btn-{r["id"]}"><span class="faq-item__question rollout-control__label">{esc(r["question"])}</span><span class="rollout-control__icon-shell" aria-hidden="true"><span class="rollout-control__icon" data-rollout-icon>⌄</span></span></button></h3><div class="faq-item__answer" id="faq-{r["id"]}" role="region" aria-labelledby="faq-btn-{r["id"]}"><div class="faq-item__answer-inner"><p>{esc(r["answer"])}</p>{link}</div></div></div>')
    items=''.join(parts)
    f=home['faq_section']
    return f'<section class="section faq-section" id="faq"><div class="section-intro faq-section__heading reveal"><p class="eyebrow">{esc(f["eyebrow"])}</p><h2>{esc(f["heading"])}</h2><p>{esc(f["description"])}</p></div><div><div class="faq-list">{items}</div></div></section>'
# Render the reassurance strip, falling back to a decorative star icon.
def render_reassurance(items):
    out=[]
    for i in items:
        if i.get('icon','').strip():
            icon=f'<img src="{esc(i["icon"])}" alt="">'
        else:
            icon='✦'
        out.append(f'<li><span class="reassurance__icon" aria-hidden="true">{icon}</span><span>{esc(i["text"])}</span></li>')
    return ''.join(out)
# ================================================================
# Landing-page rendering
# ================================================================

# Assemble the complete homepage from the validated content components above.
# The additions join shared head/header/footer HTML with page-specific sections.
# Every visible content value is read from the validated dictionaries/CSV rows.
def home_page(home,gallery,faq_rows,testimonials,web3forms_access_key,demo=False):
    h=home['hero']; reass=render_reassurance(home['reassurance']); cta=home['final_cta']
    page_head=head(home,'home',False if demo else seo_home_graph(home,faq_rows),index=not demo,canonical_path='/demo-testimonials.html' if demo else None)
    return page_head+'<body id="top"><div class="site-background" aria-hidden="true"><div class="site-background__top"></div><div class="site-background__middle"></div><div class="site-background__bottom"></div></div><a class="skip-link" href="#main">Skip to content</a>'+header(home,'')+f'''<main id="main" class="site-shell"><section class="hero hero--home" aria-labelledby="hero-title"><div class="hero__picture" role="img" aria-label="{esc(h['media']['alt'])}"><div class="hero__media-pan"><div class="hero__media-breathe"><img class="hero__image hero__image--light" src="{h['media']['light']}" alt="" width="1576" height="941" fetchpriority="high"><img class="hero__image hero__image--dark" src="{h['media']['dark']}" alt="" width="1576" height="941" fetchpriority="high"></div></div></div><div class="hero__inner"><div class="hero__content reveal"><p class="eyebrow">{esc(h['eyebrow'])}</p><h1 id="hero-title">{esc(h['title'])}</h1><p>{esc(h['description'])}</p><div class="button-row"><a class="button button--key" href="{h['primary_cta']['href']}">{esc(h['primary_cta']['label'])}</a><a class="button button--secondary" href="{h['secondary_cta']['href']}">{esc(h['secondary_cta']['label'])}</a></div></div></div></section><section class="reassurance"><ul>{reass}</ul></section><section class="section how-section" id="how-it-works"><div class="section-intro section-heading reveal"><p class="eyebrow">{esc(home['how_it_works']['eyebrow'])}</p><h2>{esc(home['how_it_works']['heading'])}</h2><p>{esc(home['how_it_works'].get('description','Choose your hosted experience, share the venue details and let us handle setup, hosting and pack-down.'))}</p></div><div class="steps-grid">{steps(home)}</div></section>{testimonial_section(home,testimonials)}{showcase(home,gallery)}{faq(home,faq_rows)}<section class="section final-cta" id="booking"><div><h2>{esc(cta['heading'])}</h2><p>{esc(cta['description'])}</p><a class="button button--key" href="{esc(cta['button'].get('href','/contact/?intent=booking'))}">{esc(cta['button']['label'])}</a></div></section></main>'''+footer(home,'')+'<script src="/js/main.js" defer></script></body></html>'
# Render ONYX and JADE summaries and their expandable detail regions.
def package_cards(pkgs):
    out=[]
    for p in pkgs:
        feats=''.join(f'<li>{esc(x)}</li>' for x in p['included'])
        detail_id=f'package-details-{p["id"]}'
        add_notes=''.join(f'<li>{esc(x)}</li>' for x in p.get('expanded',{}).get('additional_notes',[]))
        notes_html=f'<ul class="package-notes">{add_notes}</ul>' if add_notes else ''
        out.append(f"""<article class="package-card package-card--{p['id']} reveal" id="package-panel-{p['id']}" role="tabpanel" aria-labelledby="package-tab-{p['id']}" data-package-panel="{p['id']}"><div class="package-card__summary"><p class="package-subtitle">{esc(p['label'])}</p><h2>{esc(p['name'])}</h2><div class="package-facts"><strong>{esc(p['price'])}</strong><span>{esc(p['duration'])}</span><span>{esc(p['capacity'])}</span></div><p class="package-summary">{esc(p['summary'])}</p></div><button class="package-expand button button--rollout" type="button" aria-expanded="false" aria-controls="{detail_id}" data-label-closed="{esc(p['details_button'])}" data-label-open="Hide package details"><span class="rollout-control__label" data-rollout-label>{esc(p['details_button'])}</span><span class="rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></button><div class="package-details" id="{detail_id}" role="region"><div class="package-details__inner"><p>{esc(p['expanded']['overview'])}</p><h3>Included</h3><ul class="feature-list">{feats}</ul><dl><dt>Suited to</dt><dd>{esc(p['expanded']['suited_to'])}</dd><dt>Age/group guidance</dt><dd>{esc(p['expanded']['age_guidance'])}</dd><dt>Room guidance</dt><dd>{esc(p['expanded']['room_guidance'])}</dd></dl>{notes_html}<p>{esc(p['enquiry_note'])}</p></div></div></article>""")
    return ''.join(out)
# Render at most five FAQs inside the packages decision panel.
def compact_package_faq(rows):
    picked=[]
    for r in rows:
        if len(picked)>=5: break
        picked.append(r)
    return ''.join(f'<div class="package-faq-item"><h3><button type="button" aria-expanded="false" aria-controls="package-faq-{esc(r["id"])}" id="package-faq-btn-{esc(r["id"])}"><span class="rollout-control__label">{esc(r["question"])}</span><span class="rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></button></h3><div class="package-faq-answer" id="package-faq-{esc(r["id"])}" role="region" aria-labelledby="package-faq-btn-{esc(r["id"])}"><div><p>{esc(r["answer"])}</p></div></div></div>' for r in picked)
# ================================================================
# Packages-page rendering
# ================================================================

# Assemble the packages page, add-on groups and three-mode decision panel.
# HTML data-* attributes such as data-decision-mode do not change appearance by
# themselves; they give main.js reliable labels for finding interactive parts.
# aria-* attributes describe the same controls to assistive technology.
def package_page(home, pkgs, addons, package_faq_rows, web3forms_access_key):
    pp=home['packages_page']; ph=pp['hero']
    light=ph.get('image') or ph.get('fallback_image'); dark=ph.get('image') or ph.get('fallback_image_dark', light)
    both=[a for a in addons if a['available_for']=='both']; specific=[a for a in addons if a['available_for']!='both']
    # Format one add-on group; grouping itself is performed immediately above.
    def rows(items):
        return ''.join(f'<li class="addon-row addon-row--{esc(a["available_for"])}"><span class="addon-marker" aria-hidden="true"></span><div class="addon-copy"><h3>{esc(a["title"])}</h3><p>{esc(a["description"])}</p></div><div class="addon-meta"><span class="addon-badge">{esc("Both" if a["available_for"]=="both" else a["available_for"].upper())}</span><strong>{esc(a["price_note"])}</strong></div></li>' for a in items)
    add=f'<section class="addon-group"><h3>Available with both packages</h3><ul class="addon-list-structured">{rows(both)}</ul></section><section class="addon-group"><h3>Package-specific options</h3><ul class="addon-list-structured">{rows(specific)}</ul></section>'
    addon_label=home['addons_section'].get('accordion_label',home['addons_section']['heading'])
    tabs=''.join(f'<button id="package-tab-{p["id"]}" role="tab" type="button" aria-selected="{str(i==0).lower()}" aria-controls="package-panel-{p["id"]}" data-package-tab="{p["id"]}" class="package-tab package-tab--{p["id"]}"><span>{esc(p["name"])}</span><small>{esc(p["capacity"].replace(" players",""))}</small></button>' for i,p in enumerate(pkgs))
    fd=pp.get('final_decision',{})
    support_faq=compact_package_faq(package_faq_rows)
    final=f'''<section class="packages-decision" aria-labelledby="packages-decision-title" data-active-mode="none">
      <div class="packages-decision__header">
        <p class="eyebrow">{esc(fd.get("eyebrow","Next step"))}</p>
        <h2 id="packages-decision-title">{esc(fd.get("heading","Ready to plan your party?"))}</h2>
        <p>{esc(fd.get("description","Reserve now when you know what you need, or ask us anything before deciding."))}</p>
      </div>
      <div class="packages-decision__actions">
        <button class="button button--key packages-decision__control" type="button" aria-expanded="false" aria-controls="packages-decision-expansion" data-decision-mode="booking"><span class="packages-decision__label">Reserve now</span></button>
        <button class="button button--secondary packages-decision__control" type="button" aria-expanded="false" aria-controls="packages-decision-expansion" data-decision-mode="question"><span class="packages-decision__label">Ask a question</span></button>
        <button class="button button--rollout packages-decision__control" type="button" aria-expanded="false" aria-controls="packages-decision-expansion" data-decision-mode="questions"><span class="packages-decision__label rollout-control__label">Common questions</span><span class="packages-decision__icon rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></button>
      </div>
      <div class="packages-decision__expansion" id="packages-decision-expansion" data-decision-expansion role="region" aria-labelledby="packages-decision-title" hidden>
        <div class="packages-decision__expansion-inner">
          <div class="packages-decision__divider" aria-hidden="true"></div>
          <div class="packages-decision__content" data-decision-content>
            <div data-decision-copy="booking" hidden><h3>Reserve your date</h3><p>Tell us when and where the party is taking place, and we’ll help confirm the right package and hosted setup.</p></div>
            <div data-decision-copy="question" hidden><h3>{esc(fd.get("ask_heading","Ask us before deciding"))}</h3><p>{esc(fd.get("ask_description","Tell us about package choice, venue space, player numbers, add-ons, accessibility or setup and we can help you plan the right fit."))}</p><ul><li>Package choice</li><li>Venue or available space</li><li>Player numbers</li><li>Add-ons</li><li>Accessibility or setup</li><li>Another question</li></ul></div>
            <div data-decision-copy="questions" hidden><h3>Common package questions</h3><div class="package-faq-list">{support_faq}</div></div>
          </div>
          <div class="packages-inline-contact" id="packages-contact" data-decision-contact hidden>{contact_form('packages-contact-form', default_intent='question', default_package='unsure', inline=True, access_key=web3forms_access_key, allow_event_disclosure=True)}</div>
        </div>
      </div>
    </section>'''
    return head(home,'packages',seo_packages_graph(home,pkgs))+f"""<body id="top"><div class="site-background" aria-hidden="true"><div class="site-background__top"></div><div class="site-background__middle"></div><div class="site-background__bottom"></div></div><a class="skip-link" href="#main">Skip to content</a>{header(home,'/packages')}<main id="main" class="site-shell"><section class="packages-hero" aria-labelledby="packages-title"><div class="packages-hero__media" role="img" aria-label="{esc(ph['alt'])}"><img class="hero__image hero__image--light" src="{light}" alt="" width="1576" height="941" fetchpriority="high"><img class="hero__image hero__image--dark" src="{dark}" alt="" width="1576" height="941" fetchpriority="high"></div><div class="packages-hero__content"><p class="eyebrow">{esc(ph['eyebrow'])}</p><h1 id="packages-title">{esc(ph['heading'])}</h1><p>{esc(ph['description'])}</p></div></section><section class="packages-overlap" aria-label="Party.LAN packages"><div class="package-tabs" role="tablist" aria-label="Choose package">{tabs}</div><div class="package-grid package-grid--overlap">{package_cards(pkgs)}</div><section class="addons-panel addons-panel--packages" id="make-your-own"><button class="button button--rollout addons-toggle" type="button" aria-expanded="true" aria-controls="addons-content" data-label-closed="Browse add-ons" data-label-open="Hide add-ons"><span class="addons-toggle__copy"><span class="eyebrow">Add-ons</span><strong>{esc(addon_label)}</strong><small>{esc(home['addons_section']['description'])}</small></span><span class="addons-toggle__control"><span class="addons-toggle__label rollout-control__label" data-rollout-label>Browse add-ons</span><span class="addons-toggle__icon rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></span></button><div class="addons-content" id="addons-content" role="region"><div class="addons-content__inner">{add}</div></div></section>{final}</section></main>{footer(home,'/')}<script src="/js/main.js" defer></script></body></html>"""

# Assemble the standalone contact page around the shared form component.
def contact_page(home, web3forms_access_key):
    return head(home,'contact',seo_graph(home,'contact','ContactPage'))+f"""<body id=\"top\"><div class=\"site-background\" aria-hidden=\"true\"><div class=\"site-background__top\"></div><div class=\"site-background__middle\"></div><div class=\"site-background__bottom\"></div></div><a class=\"skip-link\" href=\"#main\">Skip to content</a>{header(home,'/')}<main id=\"main\" class=\"site-shell contact-page\"><section class=\"section contact-section\" aria-labelledby=\"contact-title\"><div class=\"section-heading reveal\"><p class=\"eyebrow\">CONTACT</p><h1 id=\"contact-title\">How can we help?</h1><p>Start a booking enquiry or ask us anything before deciding.</p></div>{contact_form('contact-page-form', access_key=web3forms_access_key, allow_event_disclosure=False)}</section></main>{footer(home,'/')}<script src=\"/js/main.js\" defer></script></body></html>"""

# ================================================================
# Legal-page rendering
# ================================================================

# Convert each validated legal block type to its semantic HTML equivalent.
def legal_blocks(blocks):
    rendered=[]
    for block in blocks:
        block_type=block['type']
        if block_type=='paragraph':
            rendered.append(f'<p>{esc(block["text"])}</p>')
        elif block_type=='list':
            tag='ol' if block['style']=='numbered' else 'ul'
            items=''.join(f'<li>{esc(item)}</li>' for item in block['items'])
            rendered.append(f'<{tag} class="legal-content__list legal-content__list--{esc(block["style"])}">{items}</{tag}>')
        elif block_type=='definitions':
            # Only definition rows with an href become links.
            def definition_value(item):
                value=esc(item['text'])
                return f'<a href="{esc(item["href"])}">{value}</a>' if item.get('href') else value
            items=''.join(f'<div><dt>{esc(item["term"])}</dt><span class="legal-definitions__separator" aria-hidden="true">–</span><dd>{definition_value(item)}</dd></div>' for item in block['items'])
            rendered.append(f'<dl class="legal-definitions">{items}</dl>')
        elif block_type=='fields':
            items=''.join(f'<div><dt>{esc(item)}</dt><dd aria-hidden="true"></dd></div>' for item in block['items'])
            rendered.append(f'<dl class="legal-fields">{items}</dl>')
        elif block_type=='table':
            columns=block['columns']
            heading=''.join(f'<th scope="col">{esc(column["label"])}</th>' for column in columns)
            rows=''.join('<tr>'+''.join(f'<td>{esc(row[column["key"]])}</td>' for column in columns)+'</tr>' for row in block['rows'])
            rendered.append(f'<div class="legal-table-scroll" role="region" aria-label="{esc(block["label"])}" tabindex="0"><table class="legal-table"><thead><tr>{heading}</tr></thead><tbody>{rows}</tbody></table></div>')
    return ''.join(rendered)
# Render one legal document as an accessible single-open accordion.
def legal_page(home,d,slug):
    items=[]
    for section in d['sections']:
        safe_id=''.join(ch if ch.isalnum() else '-' for ch in section['id'].lower()).strip('-')
        section_id=f'legal-{slug}-{safe_id}'
        button_id=f'legal-button-{slug}-{safe_id}'
        content=legal_blocks(section['blocks'])
        items.append(f'<div class="legal-accordion__item"><h2><button type="button" aria-expanded="false" aria-controls="{section_id}" id="{button_id}"><span class="legal-accordion__label">{esc(section["title"])}</span><span class="rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></button></h2><div class="legal-accordion__answer" id="{section_id}" role="region" aria-labelledby="{button_id}"><div class="legal-accordion__answer-inner"><div class="legal-content">{content}</div></div></div></div>')
    accordion=''.join(items)
    updated=f'<p class="legal-page__updated">Last updated: {esc(d["last_updated"])}</p>' if d.get('last_updated') else ''
    notice=f'<p class="legal-page__notice">{esc(d["draft_warning"])}</p>' if d.get('draft_warning') else ''
    summary=f'<p class="legal-page__summary">{esc(d["summary"])}</p>' if d.get('summary') else ''
    return head(home,slug,seo_graph(home,slug))+f'<body id="top"><div class="site-background" aria-hidden="true"><div class="site-background__top"></div><div class="site-background__middle"></div><div class="site-background__bottom"></div></div><a class="skip-link" href="#main">Skip to content</a>{header(home,"/")}<main id="main" class="site-shell legal-page"><section class="section legal-section" aria-labelledby="legal-page-title"><div class="legal-page__top"><a class="button button--secondary legal-page__back" href="/">← Homepage</a><header class="section-heading legal-page__heading"><h1 id="legal-page-title">{esc(d["title"])}</h1>{updated}{notice}{summary}</header></div><div class="legal-accordion" data-legal-accordion>{accordion}</div></section></main>{footer(home,"/")}<script src="/js/main.js" defer></script></body></html>'
# ================================================================
# Build orchestration
# ================================================================

# Validate everything before touching dist/. Only a fully valid content set may
# replace the currently generated site. This two-phase order is important: a
# typo in one content file cannot leave dist/ half rebuilt or partly missing.
def main():
    # PHASE 1 — confirm every required source file exists.
    for rel in REQUIRED_FILES:
        if not (CONTENT/rel).exists(): err('content/'+rel,'$','missing required file')
    # PHASE 2 — read and validate all JSON/CSV content in memory.
    home=read_json(Path('homepage.json')); validate_home(home)
    pkgs=validate_packages(read_json(Path('packages.json'))); pkg_ids={p['id'] for p in pkgs}
    addons=validate_rows('addons.csv',['title','description','available_for','price_note'],'addon')
    gallery=validate_gallery_rows('gallery.csv')
    validate_gallery_rows('gallery.example.csv')
    faq_rows=validate_rows('faq.csv',['question','answer'],'faq')
    package_faq_rows=validate_rows('packages_faq.csv',['question','answer'],'packages_faq')
    live=validate_rows('testimonials.csv',['image','alt'],'testimonial',pkg_ids)
    demo=validate_rows('testimonials.example.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    terms=validate_legal('terms'); privacy=validate_legal('privacy')
    # Render supplies this secret through the environment. It is escaped before
    # being inserted into the hidden form field and is never stored in content/.
    web3forms_access_key=esc(os.environ.get('WEB3FORMS_ACCESS_KEY','').strip())
    # Stop here if any earlier check called err(). The old dist/ is still intact.
    if ERRORS:
        print('Build failed with content validation errors:',file=sys.stderr); print('\n'.join('- '+e for e in ERRORS),file=sys.stderr); sys.exit(1)
    # PHASE 3 — validation passed, so it is safe to recreate generated assets.
    copy_assets()
    # PHASE 4 — write one index.html inside each public route folder. Static web
    # hosts treat /packages/index.html as the page visitors see at /packages/.
    (DIST/'index.html').write_text(home_page(home,gallery,faq_rows,live,web3forms_access_key),encoding='utf-8')
    (DIST/'demo-testimonials.html').write_text(home_page(home,gallery,faq_rows,demo,web3forms_access_key,demo=True),encoding='utf-8')
    (DIST/'packages').mkdir(); (DIST/'packages'/'index.html').write_text(package_page(home,pkgs,addons,package_faq_rows,web3forms_access_key),encoding='utf-8')
    (DIST/'terms').mkdir(); (DIST/'terms'/'index.html').write_text(legal_page(home,terms,'terms'),encoding='utf-8')
    (DIST/'privacy').mkdir(); (DIST/'privacy'/'index.html').write_text(legal_page(home,privacy,'privacy'),encoding='utf-8')
    (DIST/'contact').mkdir(); (DIST/'contact'/'index.html').write_text(contact_page(home,web3forms_access_key),encoding='utf-8')
    # SEO: Generate robots.txt and sitemap.xml only after every canonical page
    # has been written successfully.
    write_seo_files(home)
    # This summary is for the developer/build log; visitors never see it.
    print(f'Built dist with homepage, packages page, {len(addons)} add-ons, {len(gallery)} gallery items, {len(live)} live testimonials, {len(faq_rows)} landing FAQs and {len(package_faq_rows)} package FAQs.')

# Importing build.py is safe for tools/tests; generation runs only as a script.
if __name__=='__main__': main()
