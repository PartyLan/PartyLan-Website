#!/usr/bin/env python3
"""Standard-library static build and content validation for Party.LAN."""
from __future__ import annotations
import csv, html, json, os, shutil, sys
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

# Absolute project paths used by every read, validation and output operation.
ROOT=Path(__file__).parent.resolve(); CONTENT=ROOT/'content'; STATIC=ROOT/'static'; DIST=ROOT/'dist'; IMAGES=CONTENT/'images'

# Shared validation state and the small set of values accepted from content.
ERRORS=[]; BOOL={'true':True,'false':False}; IMG_EXT={'.jpg','.jpeg','.png','.webp','.avif'}

# A build cannot succeed unless every content source in this list exists.
REQUIRED_FILES=['homepage.json','packages.json','addons.csv','testimonials.csv','testimonials.example.csv','gallery.csv','faq.csv','packages_faq.csv','legal/terms.json','legal/privacy.json']

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
    if not value.startswith('/assets/images/'): err(file,ctx,'unsupported asset path; expected /assets/images/...'); return
    if Path(value).suffix.lower() not in IMG_EXT: err(file,ctx,'unsupported image extension'); return
    if not (IMAGES/value.removeprefix('/assets/images/')).is_file(): err(file,ctx,'referenced image does not exist')

# Read a content JSON file and convert file/parser failures into build errors.
def read_json(rel):
    p=CONTENT/rel
    try: return json.loads(p.read_text(encoding='utf-8'))
    except FileNotFoundError: err(str(Path('content')/rel),'$','missing required file'); return {}
    except json.JSONDecodeError as e: err(str(Path('content')/rel),f'line {e.lineno}',f'malformed JSON: {e.msg}'); return {}

# Read CSV rows as dictionaries keyed by their header names.
def read_csv(rel):
    try:
        with (CONTENT/rel).open(newline='',encoding='utf-8') as fh: return list(csv.DictReader(fh))
    except FileNotFoundError: err('content/'+rel,'$','missing required file'); return []
    except csv.Error as e: err('content/'+rel,'$','malformed CSV: '+str(e)); return []

# Validate homepage structure, navigation contracts, image references and the
# content fragments reused by the packages page.
def validate_home(h):
    f='content/homepage.json'
    for k in ['meta','navigation','navigation_groups','header','hero','reassurance','testimonials_section','how_it_works','gallery_section','faq_section','final_cta','footer','packages_page','addons_section']:
        if k not in h: err(f,k,'required top-level key is missing')
    req_text(f,h.get('hero',{}),'title','hero'); req_text(f,h.get('hero',{}),'description','hero')
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

# Apply common CSV rules plus type-specific checks for add-ons, gallery images,
# testimonials and FAQs. Invisible rows validate but are not rendered.
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
        if kind=='gallery':
            if r.get('category') not in {'experience','equipment'}: err(file,ctx,'invalid gallery category; expected experience or equipment')
            if visible: image_ok(file,ctx+'.image',r.get('image',''))
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
def copy_assets():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(); shutil.copytree(STATIC,DIST,dirs_exist_ok=True)
    dest=DIST/'assets'/'images'; dest.mkdir(parents=True,exist_ok=True)
    for p in IMAGES.rglob('*'):
        if p.is_file() and p.suffix.lower() in IMG_EXT:
            d=dest/p.relative_to(IMAGES); d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,d)
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

# Render document metadata and apply the chosen theme before CSS loads, avoiding
# a light-theme flash for visitors who have selected dark mode.
def head(home,title=None,desc=None):
    m=home['meta']; return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title or m['title'])}</title><meta name="description" content="{esc(desc or m['description'])}"><link rel="canonical" href="{esc(m['canonical_url'])}"><meta property="og:image" content="{esc(m['og_image'])}"><meta name="theme-color" content="{m['theme_color_light']}"><script>(function(){{try{{var s=localStorage.getItem('partyLanTheme');document.documentElement.dataset.theme=s||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}}catch(e){{document.documentElement.dataset.theme='light';}}}}());</script><link rel="stylesheet" href="/css/styles.css"></head>'''

# ================================================================
# Contact form rendering
# ================================================================

# Render the reusable enquiry form. Without a Web3Forms key, submission is
# disabled and the direct email route remains available.
def contact_form(form_id='contact-form', default_intent='question', default_package='unsure', inline=False, access_key='', allow_event_disclosure=False):
    event_hidden=' hidden' if default_intent=='question' and not inline else ''
    online='true' if access_key else 'false'
    submit_disabled='' if access_key else ' disabled'
    disclosure_html='<div class="field field--full contact-disclosure"><button class="button button--rollout quiet-button" type="button" data-event-toggle aria-expanded="false" data-label-closed="Add event details" data-label-open="Hide event details"><span class="rollout-control__label" data-rollout-label>Add event details</span><span class="rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></button></div>' if allow_event_disclosure else ''
    return f"""<div class=\"contact-form-shell\" data-contact-component data-default-intent=\"{esc(default_intent)}\" data-default-package=\"{esc(default_package)}\" data-online-enabled=\"{online}\"><div class=\"contact-status\" data-contact-status role=\"status\" aria-live=\"polite\" tabindex=\"-1\"></div><form class=\"contact-form\" id=\"{esc(form_id)}\" data-contact-form action=\"https://api.web3forms.com/submit\" method=\"POST\"><input type=\"hidden\" name=\"access_key\" value=\"{access_key}\"><input type=\"hidden\" name=\"subject\" value=\"New Party.LAN question\"><input type=\"hidden\" name=\"from_name\" value=\"Party.LAN Website\"><input type=\"checkbox\" name=\"botcheck\" tabindex=\"-1\" aria-hidden=\"true\" autocomplete=\"off\" class=\"form-honeypot\"><div class=\"contact-form__grid\"><div class=\"field field--full\"><label for=\"{esc(form_id)}-intent\">Enquiry type</label><select id=\"{esc(form_id)}-intent\" name=\"intent\" required aria-describedby=\"{esc(form_id)}-intent-error\"><optgroup label=\"Party enquiries\"><option value=\"booking\">Booking enquiry</option><option value=\"party_question\">General party question</option></optgroup><optgroup label=\"Other enquiries\"><option value=\"collaboration\">Work with Party.LAN</option><option value=\"venue_partnership\">Venue or business partnership</option><option value=\"media\">Press or media enquiry</option><option value=\"other\">Other enquiry</option></optgroup></select><p class=\"field-error\" id=\"{esc(form_id)}-intent-error\" data-error-for=\"intent\"></p></div><div class=\"field\"><label for=\"{esc(form_id)}-name\">Name</label><input id=\"{esc(form_id)}-name\" name=\"name\" autocomplete=\"name\" required minlength=\"2\" maxlength=\"80\" aria-describedby=\"{esc(form_id)}-name-error\"><p class=\"field-error\" id=\"{esc(form_id)}-name-error\" data-error-for=\"name\"></p></div><div class=\"field\"><label for=\"{esc(form_id)}-email\">Email</label><input id=\"{esc(form_id)}-email\" name=\"email\" type=\"email\" autocomplete=\"email\" required maxlength=\"120\" aria-describedby=\"{esc(form_id)}-email-error\"><p class=\"field-error\" id=\"{esc(form_id)}-email-error\" data-error-for=\"email\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-date\">Preferred date</label><input id=\"{esc(form_id)}-date\" name=\"preferred_date\" type=\"date\" aria-describedby=\"{esc(form_id)}-date-error\"><p class=\"field-error\" id=\"{esc(form_id)}-date-error\" data-error-for=\"preferred_date\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-alt-date\">Alternative date</label><input id=\"{esc(form_id)}-alt-date\" name=\"alternative_date\" type=\"date\" aria-describedby=\"{esc(form_id)}-alt-date-error\"><p class=\"field-error\" id=\"{esc(form_id)}-alt-date-error\" data-error-for=\"alternative_date\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-location\">Town or postcode</label><input id=\"{esc(form_id)}-location\" name=\"location\" autocomplete=\"postal-code\" maxlength=\"100\" aria-describedby=\"{esc(form_id)}-location-error\"><p class=\"field-error\" id=\"{esc(form_id)}-location-error\" data-error-for=\"location\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-players\">Number of players</label><input id=\"{esc(form_id)}-players\" name=\"players\" type=\"number\" min=\"1\" max=\"40\" inputmode=\"numeric\" aria-describedby=\"{esc(form_id)}-players-error\"><p class=\"field-error\" id=\"{esc(form_id)}-players-error\" data-error-for=\"players\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-package\">Package</label><select id=\"{esc(form_id)}-package\" name=\"package\" aria-describedby=\"{esc(form_id)}-package-error\"><option value=\"unsure\">Not sure yet</option><option value=\"onyx\">ONYX</option><option value=\"jade\">JADE</option></select><p class=\"field-error\" id=\"{esc(form_id)}-package-error\" data-error-for=\"package\"></p></div><div class=\"field field--event\"{event_hidden}><label for=\"{esc(form_id)}-phone\">Phone</label><input id=\"{esc(form_id)}-phone\" name=\"phone\" type=\"tel\" autocomplete=\"tel\" maxlength=\"30\" aria-describedby=\"{esc(form_id)}-phone-error\"><p class=\"field-error\" id=\"{esc(form_id)}-phone-error\" data-error-for=\"phone\"></p></div><div class=\"field field--full\"><label for=\"{esc(form_id)}-message\">Message</label><textarea id=\"{esc(form_id)}-message\" name=\"message\" rows=\"5\" maxlength=\"2000\" aria-describedby=\"{esc(form_id)}-message-help {esc(form_id)}-message-error\"></textarea><p class=\"field-help\" id=\"{esc(form_id)}-message-help\">For booking enquiries, a preferred date or venue detail can provide enough context.</p><p class=\"field-error\" id=\"{esc(form_id)}-message-error\" data-error-for=\"message\"></p></div>{disclosure_html}<div class=\"field field--full privacy-check\"><label class=\"privacy-check__label\"><input name=\"privacy\" type=\"checkbox\" required aria-describedby=\"{esc(form_id)}-privacy-error\"><span class=\"privacy-check__copy\">I have read the <a href="/privacy/">Privacy Policy</a> and understand that Party.LAN will use these details to respond to my enquiry.</span></label><p class=\"field-error\" id=\"{esc(form_id)}-privacy-error\" data-error-for=\"privacy\"></p></div><div class=\"contact-form__actions\"><button class=\"button button--key contact-submit\" type=\"submit\" data-submit-label=\"Send enquiry\"{submit_disabled}>Send enquiry</button><a class=\"button button--secondary direct-email\" href=\"mailto:hello@partylan.co.uk\"><span>Email Party.LAN directly</span><small>hello@partylan.co.uk</small></a></div></div></form><div class=\"contact-success\" data-contact-success hidden tabindex=\"-1\"><h3>Thanks — your enquiry has been sent.</h3><p>We’ll get back to you as soon as possible.</p><button class=\"button button--secondary\" type=\"button\" data-send-another>Send another enquiry</button></div></div>"""

# Convert testimonial CSV rows into accessible slides and dot controls.
def testimonial_section(home, rows):
    if not rows: return ''
    slides=''.join(f'<article class="testimonial-slide {"is-active" if i==0 else ""}" aria-hidden="{"false" if i==0 else "true"}"><img src="{r["image"]}" alt="{esc(r["alt"])}"><div class="testimonial-slide__content"><blockquote><p>“{esc(r["quote"])}”</p></blockquote><p><b>{esc(r["name"])}</b>{", age "+esc(r["age"]) if r.get("age") else ""}</p><p>{esc(r.get("location",""))} {esc(r.get("package",""))}</p></div></article>' for i,r in enumerate(rows))
    dots=''.join(f'<button class="testimonial-dot" type="button" aria-label="Show testimonial {i+1} of {len(rows)}"><span></span></button>' for i,_ in enumerate(rows))
    s=home['testimonials_section']; return f'<section class="section testimonials" id="testimonials" aria-labelledby="testimonials-title"><div class="section-heading reveal"><p class="eyebrow">{esc(s["eyebrow"])}</p><h2 id="testimonials-title">{esc(s["heading"])}</h2><p>{esc(s["description"])}</p></div><div class="testimonial-stage" role="region" aria-roledescription="carousel"><div class="testimonial-track">{slides}</div><button class="showcase-toggle testimonial-toggle" type="button" aria-pressed="false" aria-label="Pause testimonials"><span aria-hidden="true">Ⅱ</span></button><div class="testimonial-dots">{dots}</div></div></section>'
# Split gallery rows by category and render them into the shared slider shell.
def showcase(home,gallery):
    # Gallery images are a small, fixed set. Load them up front so a click can
    # cross-fade to decoded pixels instead of briefly showing an empty frame.
    slides=''.join(f'<figure class="showcase-slide {"is-active" if i==0 else ""}" data-category="{r["category"]}" data-caption="{esc(r["caption"])}"><div class="showcase-slide__pan"><div class="showcase-slide__breathe"><img src="{r["image"]}" alt="{esc(r["alt"])}" loading="eager" decoding="async"></div></div><figcaption>{esc(r["caption"])}</figcaption></figure>' for i,r in enumerate(gallery))
    g=home['gallery_section']; return f'<section class="section showcase-section" id="gallery" aria-labelledby="gallery-title"><div class="section-intro section-heading reveal"><p class="eyebrow">{esc(g["eyebrow"])}</p><h2 id="gallery-title">{esc(g["heading"])}</h2><p>{esc(g["description"])}</p></div><div class="gallery-tabs" role="tablist"><button role="tab" aria-selected="true" data-gallery-tab="experience">{esc(g["tabs"]["experience"])}</button><button role="tab" aria-selected="false" data-gallery-tab="equipment">{esc(g["tabs"]["equipment"])}</button></div><div class="showcase" role="region" aria-label="Party.LAN image showcase"><div class="showcase-track">{slides}</div><button class="showcase-toggle" type="button" aria-pressed="false" aria-label="Pause gallery"><span aria-hidden="true">Ⅱ</span></button><div class="showcase-feedback" aria-hidden="true"></div><div class="showcase-indicators" aria-label="Choose gallery image"></div></div></section>'
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
def home_page(home,gallery,faq_rows,testimonials,web3forms_access_key):
    h=home['hero']; reass=render_reassurance(home['reassurance']); cta=home['final_cta']
    return head(home)+'<body id="top"><div class="site-background" aria-hidden="true"><div class="site-background__top"></div><div class="site-background__middle"></div><div class="site-background__bottom"></div></div><a class="skip-link" href="#main">Skip to content</a>'+header(home,'')+f'''<main id="main" class="site-shell"><section class="hero hero--home" aria-labelledby="hero-title"><div class="hero__picture" role="img" aria-label="{esc(h['media']['alt'])}"><div class="hero__media-pan"><div class="hero__media-breathe"><img class="hero__image hero__image--light" src="{h['media']['light']}" alt=""><img class="hero__image hero__image--dark" src="{h['media']['dark']}" alt=""></div></div></div><div class="hero__inner"><div class="hero__content reveal"><p class="eyebrow">{esc(h['eyebrow'])}</p><h1 id="hero-title">{esc(h['title'])}</h1><p>{esc(h['description'])}</p><div class="button-row"><a class="button button--key" href="{h['primary_cta']['href']}">{esc(h['primary_cta']['label'])}</a><a class="button button--secondary" href="{h['secondary_cta']['href']}">{esc(h['secondary_cta']['label'])}</a></div></div></div></section><section class="reassurance"><ul>{reass}</ul></section><section class="section how-section" id="how-it-works"><div class="section-intro section-heading reveal"><p class="eyebrow">{esc(home['how_it_works']['eyebrow'])}</p><h2>{esc(home['how_it_works']['heading'])}</h2><p>{esc(home['how_it_works'].get('description','Choose your hosted experience, share the venue details and let us handle setup, hosting and pack-down.'))}</p></div><div class="steps-grid">{steps(home)}</div></section>{testimonial_section(home,testimonials)}{showcase(home,gallery)}{faq(home,faq_rows)}<section class="section final-cta" id="booking"><div><h2>{esc(cta['heading'])}</h2><p>{esc(cta['description'])}</p><a class="button button--key" href="{esc(cta['button'].get('href','/contact/?intent=booking'))}">{esc(cta['button']['label'])}</a></div></section></main>'''+footer(home,'')+'<script src="/js/main.js" defer></script></body></html>'
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
    return head(home,pp['meta_title'],pp['hero']['description'])+f"""<body id="top"><div class="site-background" aria-hidden="true"><div class="site-background__top"></div><div class="site-background__middle"></div><div class="site-background__bottom"></div></div><a class="skip-link" href="#main">Skip to content</a>{header(home,'/packages')}<main id="main" class="site-shell"><section class="packages-hero" aria-labelledby="packages-title"><div class="packages-hero__media" role="img" aria-label="{esc(ph['alt'])}"><img class="hero__image hero__image--light" src="{light}" alt=""><img class="hero__image hero__image--dark" src="{dark}" alt=""></div><div class="packages-hero__content"><p class="eyebrow">{esc(ph['eyebrow'])}</p><h1 id="packages-title">{esc(ph['heading'])}</h1><p>{esc(ph['description'])}</p></div></section><section class="packages-overlap" aria-label="Party.LAN packages"><div class="package-tabs" role="tablist" aria-label="Choose package">{tabs}</div><div class="package-grid package-grid--overlap">{package_cards(pkgs)}</div><section class="addons-panel addons-panel--packages" id="make-your-own"><button class="button button--rollout addons-toggle" type="button" aria-expanded="true" aria-controls="addons-content" data-label-closed="Browse add-ons" data-label-open="Hide add-ons"><span class="addons-toggle__copy"><span class="eyebrow">Add-ons</span><strong>{esc(addon_label)}</strong><small>{esc(home['addons_section']['description'])}</small></span><span class="addons-toggle__control"><span class="addons-toggle__label rollout-control__label" data-rollout-label>Browse add-ons</span><span class="addons-toggle__icon rollout-control__icon" data-rollout-icon aria-hidden="true">⌄</span></span></button><div class="addons-content" id="addons-content" role="region"><div class="addons-content__inner">{add}</div></div></section>{final}</section></main>{footer(home,'/')}<script src="/js/main.js" defer></script></body></html>"""

# Assemble the standalone contact page around the shared form component.
def contact_page(home, web3forms_access_key):
    return head(home,'Contact Party.LAN','Start a booking enquiry or ask Party.LAN a question.')+f"""<body id=\"top\"><div class=\"site-background\" aria-hidden=\"true\"><div class=\"site-background__top\"></div><div class=\"site-background__middle\"></div><div class=\"site-background__bottom\"></div></div><a class=\"skip-link\" href=\"#main\">Skip to content</a>{header(home,'/')}<main id=\"main\" class=\"site-shell contact-page\"><section class=\"section contact-section\" aria-labelledby=\"contact-title\"><div class=\"section-heading reveal\"><p class=\"eyebrow\">CONTACT</p><h1 id=\"contact-title\">How can we help?</h1><p>Start a booking enquiry or ask us anything before deciding.</p></div>{contact_form('contact-page-form', access_key=web3forms_access_key, allow_event_disclosure=False)}</section></main>{footer(home,'/')}<script src=\"/js/main.js\" defer></script></body></html>"""

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
    return head(home,d['title'])+f'<body id="top"><div class="site-background" aria-hidden="true"><div class="site-background__top"></div><div class="site-background__middle"></div><div class="site-background__bottom"></div></div><a class="skip-link" href="#main">Skip to content</a>{header(home,"/")}<main id="main" class="site-shell legal-page"><section class="section legal-section" aria-labelledby="legal-page-title"><div class="legal-page__top"><a class="button button--secondary legal-page__back" href="/">← Homepage</a><header class="section-heading legal-page__heading"><h1 id="legal-page-title">{esc(d["title"])}</h1>{updated}{notice}{summary}</header></div><div class="legal-accordion" data-legal-accordion>{accordion}</div></section></main>{footer(home,"/")}<script src="/js/main.js" defer></script></body></html>'
# ================================================================
# Build orchestration
# ================================================================

# Validate everything before touching dist/. Only a fully valid content set may
# replace the currently generated site.
def main():
    for rel in REQUIRED_FILES:
        if not (CONTENT/rel).exists(): err('content/'+rel,'$','missing required file')
    home=read_json(Path('homepage.json')); validate_home(home)
    pkgs=validate_packages(read_json(Path('packages.json'))); pkg_ids={p['id'] for p in pkgs}
    addons=validate_rows('addons.csv',['title','description','available_for','price_note'],'addon')
    gallery=validate_rows('gallery.csv',['category','image','alt','caption'],'gallery')
    faq_rows=validate_rows('faq.csv',['question','answer'],'faq')
    package_faq_rows=validate_rows('packages_faq.csv',['question','answer'],'packages_faq')
    live=validate_rows('testimonials.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    demo=validate_rows('testimonials.example.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    terms=validate_legal('terms'); privacy=validate_legal('privacy')
    web3forms_access_key=esc(os.environ.get('WEB3FORMS_ACCESS_KEY','').strip())
    if ERRORS:
        print('Build failed with content validation errors:',file=sys.stderr); print('\n'.join('- '+e for e in ERRORS),file=sys.stderr); sys.exit(1)
    copy_assets()
    (DIST/'index.html').write_text(home_page(home,gallery,faq_rows,live,web3forms_access_key),encoding='utf-8')
    (DIST/'demo-testimonials.html').write_text(home_page(home,gallery,faq_rows,demo,web3forms_access_key),encoding='utf-8')
    (DIST/'packages').mkdir(); (DIST/'packages'/'index.html').write_text(package_page(home,pkgs,addons,package_faq_rows,web3forms_access_key),encoding='utf-8')
    (DIST/'terms').mkdir(); (DIST/'terms'/'index.html').write_text(legal_page(home,terms,'terms'),encoding='utf-8')
    (DIST/'privacy').mkdir(); (DIST/'privacy'/'index.html').write_text(legal_page(home,privacy,'privacy'),encoding='utf-8')
    (DIST/'contact').mkdir(); (DIST/'contact'/'index.html').write_text(contact_page(home,web3forms_access_key),encoding='utf-8')
    print(f'Built dist with homepage, packages page, {len(addons)} add-ons, {len(gallery)} gallery items, {len(live)} live testimonials, {len(faq_rows)} landing FAQs and {len(package_faq_rows)} package FAQs.')

# Importing build.py is safe for tools/tests; generation runs only as a script.
if __name__=='__main__': main()
