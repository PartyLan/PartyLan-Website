#!/usr/bin/env python3
"""Standard-library static build and content validation for Party.LAN."""
from __future__ import annotations
import csv, html, json, re, shutil, sys
from pathlib import Path

ROOT=Path(__file__).parent.resolve(); CONTENT=ROOT/'content'; STATIC=ROOT/'static'; DIST=ROOT/'dist'; IMAGES=CONTENT/'images'
ERRORS=[]; WARNINGS=[]; BOOL={'true':True,'false':False}; IMG_EXT={'.jpg','.jpeg','.png','.webp','.avif'}
REQUIRED_FILES=['homepage.json','packages.json','addons.csv','testimonials.csv','testimonials.example.csv','gallery.csv','faq.csv','legal/terms.json','legal/privacy.json']
PACKAGE_FACTS={'onyx':{'name':'ONYX','label':'Premium Experience','price':'£150','duration':'2 hours','capacity':'Up to 6 players','included':['PlayStation and Nintendo gaming','Racing simulator','VR hardware','Displays','Party host/operator','Free digital invitation']},'jade':{'name':'JADE','label':'Big Party','price':'£150','duration':'2 hours','capacity':'Up to 10 players','included':['Multiplayer gaming across multiple stations','Displays','Party host/operator','Free digital invitation']}}
LEGAL_SECTIONS={'terms':['introduction','booking','payment','cancellation','venue_access','room_and_power_requirements','supervision','equipment_care','damage','travel','contact'],'privacy':['introduction','information_collected','purpose_of_processing','service_providers','retention','customer_rights','contact']}

def err(f,k,r): ERRORS.append(f'{f} {k}: {r}')
def esc(v): return html.escape(str(v), quote=True)
def attr(v): return esc(v)
def req_text(file,obj,key,ctx):
    v=obj.get(key) if isinstance(obj,dict) else None
    if not isinstance(v,str) or not v.strip(): err(file,ctx+'.'+key,'required text is empty'); return ''
    return v.strip()
def req_bool(file,row,key,ctx):
    v=(row.get(key,'') or '').strip().lower()
    if v not in BOOL: err(file,ctx,f'{key} must be true or false'); return False
    return BOOL[v]
def req_order(file,row,ctx,orders):
    raw=(row.get('display_order','') or '').strip()
    try: order=int(raw); assert order>0
    except Exception: err(file,ctx,'display_order must be a positive integer'); return 999999
    if order in orders: err(file,ctx,f'duplicate display_order {order}')
    orders.add(order); return order
def image_ok(file,ctx,value):
    if not value: err(file,ctx,'referenced image is required'); return
    if not value.startswith('/assets/images/'): err(file,ctx,'unsupported asset path; expected /assets/images/...'); return
    if Path(value).suffix.lower() not in IMG_EXT: err(file,ctx,'unsupported image extension'); return
    if not (IMAGES/value.removeprefix('/assets/images/')).is_file(): err(file,ctx,'referenced image does not exist')
def read_json(rel):
    p=CONTENT/rel
    try: return json.loads(p.read_text(encoding='utf-8'))
    except FileNotFoundError: err(str(Path('content')/rel),'$','missing required file'); return {}
    except json.JSONDecodeError as e: err(str(Path('content')/rel),f'line {e.lineno}',f'malformed JSON: {e.msg}'); return {}
def read_csv(rel):
    p=CONTENT/rel
    try:
        with p.open(newline='',encoding='utf-8') as fh: return list(csv.DictReader(fh))
    except FileNotFoundError: err(str(Path('content')/rel),'$','missing required file'); return []
    except csv.Error as e: err(str(Path('content')/rel),'$','malformed CSV: '+str(e)); return []

def validate_home(h):
    f='content/homepage.json'
    for k in ['meta','navigation','header','hero','reassurance','packages_section','addons_section','testimonials_section','how_it_works','gallery_section','room_planning','faq_section','final_cta','footer']:
        if k not in h: err(f,k,'required top-level key is missing')
    req_text(f,h.get('hero',{}),'title','hero'); req_text(f,h.get('hero',{}),'description','hero')
    for key in ['light','dark']: image_ok(f,'hero.media.'+key,h.get('hero',{}).get('media',{}).get(key,''))
    for key in ['logo_light','logo_dark']: image_ok(f,'header.'+key,h.get('header',{}).get(key,''))

def validate_packages(data):
    rows=data.get('packages',data if isinstance(data,list) else []) ; out=[]; ids=set(); orders=set(); f='content/packages.json'
    if not isinstance(rows,list): err(f,'packages','must be a list'); return []
    for i,p in enumerate(rows):
        ctx=f'package "{p.get("id",i)}"'; pid=req_text(f,p,'id',ctx)
        if pid in ids: err(f,ctx,'duplicate ID')
        ids.add(pid)
        if pid not in PACKAGE_FACTS: err(f,ctx,'invalid package ID')
        if pid in PACKAGE_FACTS:
            facts=PACKAGE_FACTS[pid]
            for key in ['name','label','price','duration','capacity']:
                if p.get(key)!=facts[key]: err(f,ctx,f'{key} must remain {facts[key]}')
            if p.get('included')!=facts['included']: err(f,ctx,'package business-detail inconsistencies in included list')
        for key in ['summary','addon_intro','enquiry_note','enquiry_button']: req_text(f,p,key,ctx)
        if not isinstance(p.get('visible'),bool): err(f,ctx,'visible must be JSON true or false')
        try: order=int(p.get('display_order')); assert order>0
        except Exception: err(f,ctx,'display_order must be a positive integer'); order=999999
        if order in orders: err(f,ctx,'duplicate display_order')
        orders.add(order); p['_order']=order
        exp=p.get('expanded',{})
        for key in ['overview','suited_to','age_guidance','room_guidance']: req_text(f,exp,key,ctx+'.expanded')
        if p.get('visible'): out.append(p)
    return sorted(out,key=lambda r:r['_order'])

def validate_rows(rel, required, kind, pkg_ids=None):
    rows=read_csv(rel); out=[]; ids=set(); orders=set(); file='content/'+rel
    for n,r in enumerate(rows,start=2):
        ctx=f'row {n}'; rid=(r.get('id') or '').strip()
        if not rid: err(file,ctx,'missing id'); continue
        if rid in ids: err(file,ctx,'duplicate ID')
        ids.add(rid); visible=req_bool(file,r,'visible',ctx); order=req_order(file,r,ctx,orders); r['_order']=order; r['_visible']=visible
        for key in required:
            if visible and not (r.get(key) or '').strip(): err(file,ctx,f'{key} is required')
        if kind=='addon' and r.get('available_for') not in {'onyx','jade','both'}: err(file,ctx,f'unknown available_for value "{r.get("available_for")}"; expected onyx, jade or both')
        if kind=='gallery':
            if r.get('category') not in {'experience','equipment'}: err(file,ctx,'invalid gallery category; expected experience or equipment')
            if visible: image_ok(file,ctx+'.image',r.get('image',''))
        if kind=='testimonial' and visible:
            if r.get('package') and r.get('package') not in pkg_ids: err(file,ctx,'invalid testimonial package reference')
            image_ok(file,ctx+'.image',r.get('image',''))
        if visible: out.append(r)
    return sorted(out,key=lambda r:r['_order'])

def validate_legal(rel, key):
    d=read_json(Path('legal')/(rel+'.json')); file=f'content/legal/{rel}.json'
    req_text(file,d,'title','page'); req_text(file,d,'draft_warning','page')
    sections=d.get('sections',{})
    for s in LEGAL_SECTIONS[key]: req_text(file,sections,s,'sections')
    return d

def copy_assets():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(); shutil.copytree(STATIC,DIST,dirs_exist_ok=True)
    dest=DIST/'assets'/'images'; dest.mkdir(parents=True,exist_ok=True)
    for p in IMAGES.rglob('*'):
        if p.is_file() and p.suffix.lower() in IMG_EXT:
            d=dest/p.relative_to(IMAGES); d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,d)

def render_nav(items): return ''.join(f'<a class="{"site-menu__availability" if i["href"]=="#booking" else ""}" href="{attr(i["href"])}">{esc(i["label"])}</a>' for i in items)
def render_footer(home, prefix=''):
    links=''.join(f'<a href="{prefix+attr(l["href"]) if l["href"].startswith("#") else attr(l["href"])}">{esc(l["label"])}</a>' for l in home['footer']['links'])
    return f'<footer class="site-footer"><p>{esc(home["footer"]["tagline"])}</p><nav aria-label="Footer navigation">{links}</nav></footer>'
def header(home,prefix=''):
    c=home['header']['availability_cta']; return f'''<header class="site-header"><nav class="nav-shell" aria-label="Main navigation"><a class="brand" href="{prefix or '#top'}"><span class="brand__mark"><img class="brand__logo brand__logo--light" src="{home['header']['logo_light']}" alt="Party.LAN" width="168" height="58"><img class="brand__logo brand__logo--dark" src="{home['header']['logo_dark']}" alt="" aria-hidden="true" width="168" height="58"></span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-menu">Menu</button><div class="site-menu" id="site-menu">{render_nav(home['navigation'])}</div><button class="theme-toggle" type="button" aria-pressed="false"><span aria-hidden="true">◐</span><span class="theme-toggle__label">Theme</span></button><a class="button button--small header-cta" href="{prefix+c['href']}">{esc(c['label'])}</a></nav></header>'''
def head(home,title=None,desc=None):
    m=home['meta']; return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title or m['title'])}</title><meta name="description" content="{esc(desc or m['description'])}"><link rel="canonical" href="{attr(m['canonical_url'])}"><meta property="og:image" content="{attr(m['og_image'])}"><meta name="theme-color" content="{m['theme_color_light']}"><script>(function(){{try{{var s=localStorage.getItem('partyLanTheme');document.documentElement.dataset.theme=s||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}}catch(e){{document.documentElement.dataset.theme='light';}}}}());</script><link rel="stylesheet" href="/css/styles.css"></head>'''

def render_packages(pkgs, addons):
    cards=[]
    for p in pkgs:
        ads=[a for a in addons if a['available_for'] in (p['id'],'both')]
        lis=''.join(f'<li>{esc(x)}</li>' for x in p['included'])
        details=''.join(f'<li><b>{esc(a["title"])}</b><span>{esc(a["description"])} {esc(a["price_note"])}</span></li>' for a in ads)
        notes=''.join(f'<li>{esc(n)}</li>' for n in p['expanded'].get('additional_notes',[]))
        cards.append(f'''<article class="package-card package-card--{p['id']} reveal"><div><p class="package-subtitle">{esc(p['label'])}</p><h3>{esc(p['name'])}</h3><div class="package-meta"><p class="package-price">{esc(p['price'])}</p><p>{esc(p['duration'])}</p><p>{esc(p['capacity'])}</p></div><p>{esc(p['summary'])}</p></div><ul class="feature-list">{lis}</ul><p class="addon-callout">Optional add-ons available</p><button class="package-expand" type="button" aria-expanded="false">See full package & add-ons <span aria-hidden="true">⌄</span></button><div class="package-details"><p>{esc(p['expanded']['overview'])}</p><dl><dt>Suited to</dt><dd>{esc(p['expanded']['suited_to'])}</dd><dt>Age/group guidance</dt><dd>{esc(p['expanded']['age_guidance'])}</dd><dt>Room guidance</dt><dd>{esc(p['expanded']['room_guidance'])}</dd></dl><h4>Included details</h4><ul>{''.join(f'<li>{esc(x)}</li>' for x in p['expanded']['included_details'])}</ul><h4>Add-ons</h4><p>{esc(p['addon_intro'])}</p><ul class="addon-list">{details}</ul><ul>{notes}</ul><p>{esc(p['enquiry_note'])}</p><a class="button" href="#booking">{esc(p['enquiry_button'])}</a></div><a class="button button--ghost" href="#booking">{esc(p['enquiry_button'])}</a></article>''')
    return ''.join(cards)

def page(home, pkgs, addons, gallery, faq, testimonials):
    h=home['hero']; reass=''.join(f'<li><span>{esc(i["text"])}</span></li>' for i in home['reassurance'])
    steps=''.join(f'<article class="step-card reveal"><span>{i}</span><h3>{esc(s["title"])}</h3><p>{esc(s["description"])}</p></article>' for i,s in enumerate(home['how_it_works']['steps'],1))
    gal=''.join(f'<figure class="gallery-card" data-category="{r["category"]}"><img src="{r["image"]}" alt="{esc(r["alt"])}" loading="lazy"><figcaption>{esc(r["caption"])}</figcaption></figure>' for r in gallery)
    faqs=''.join(f'<div class="faq-item"><h3><button aria-expanded="false" aria-controls="faq-{r["id"]}" id="faq-btn-{r["id"]}">{esc(r["question"])}<span aria-hidden="true">+</span></button></h3><div class="faq-item__answer" id="faq-{r["id"]}" role="region" aria-labelledby="faq-btn-{r["id"]}"><p>{esc(r["answer"])}</p></div></div>' for r in faq)
    test=''
    if testimonials:
        slides=''.join(f'<article class="testimonial-slide {"is-active" if i==0 else ""}"><img src="{r["image"]}" alt="{esc(r["alt"])}"><div class="testimonial-slide__content"><p class="demo-badge">{esc(home["testimonials_section"]["demo_label"])}</p><blockquote><p>“{esc(r["quote"])}”</p></blockquote><p><b>{esc(r["name"])}</b>{", age "+esc(r["age"]) if r.get("age") else ""}</p><p>{esc(r.get("location",""))} {esc(r.get("package",""))}</p></div></article>' for i,r in enumerate(testimonials))
        dots=''.join(f'<button class="testimonial-dot" type="button" aria-label="Show testimonial {i+1} of {len(testimonials)}"><span></span></button>' for i,_ in enumerate(testimonials))
        test=f'<section class="section testimonials" id="testimonials" aria-labelledby="testimonials-title"><div class="section-heading reveal"><p class="eyebrow">{esc(home["testimonials_section"]["eyebrow"])}</p><h2 id="testimonials-title">{esc(home["testimonials_section"]["heading"])}</h2><p>{esc(home["testimonials_section"]["description"])}</p></div><div class="testimonial-stage" role="region" aria-roledescription="carousel"><div class="testimonial-track">{slides}</div><button class="testimonial-prev" type="button">Previous</button><button class="testimonial-next" type="button">Next</button><div class="testimonial-dots">{dots}</div></div></section>'
    return head(home)+'<body id="top"><a class="skip-link" href="#main">Skip to content</a>'+header(home)+f'''<main id="main"><section class="hero" aria-labelledby="hero-title"><div class="hero__picture" role="img" aria-label="{esc(h['media']['alt'])}"><div class="hero__media-motion"><img class="hero__image hero__image--light" src="{h['media']['light']}" alt=""><img class="hero__image hero__image--dark" src="{h['media']['dark']}" alt=""></div></div><div class="hero__inner"><div class="hero__content reveal"><p class="eyebrow">{esc(h['eyebrow'])}</p><h1 id="hero-title">{esc(h['title'])}</h1><p>{esc(h['description'])}</p><div class="button-row"><a class="button" href="{h['primary_cta']['href']}">{esc(h['primary_cta']['label'])}</a><a class="button button--ghost" href="{h['secondary_cta']['href']}">{esc(h['secondary_cta']['label'])}</a></div></div></div></section><section class="reassurance"><ul>{reass}</ul></section><section class="section" id="packages"><div class="section-heading reveal"><p class="eyebrow">{esc(home['packages_section']['eyebrow'])}</p><h2>{esc(home['packages_section']['heading'])}</h2><p>{esc(home['packages_section']['description'])}</p></div><div class="package-grid">{render_packages(pkgs,addons)}</div><aside class="addons-panel reveal"><h3>{esc(home['addons_section']['heading'])}</h3><p>{esc(home['addons_section']['description'])}</p></aside></section>{test}<section class="section" id="how-it-works"><div class="section-heading section-heading--center reveal"><p class="eyebrow">{esc(home['how_it_works']['eyebrow'])}</p><h2>{esc(home['how_it_works']['heading'])}</h2></div><div class="steps-grid">{steps}</div></section><section class="section gallery-section" id="gallery"><div class="section-heading reveal"><p class="eyebrow">{esc(home['gallery_section']['eyebrow'])}</p><h2>{esc(home['gallery_section']['heading'])}</h2><p>{esc(home['gallery_section']['description'])}</p></div><div class="gallery-tabs" role="tablist"><button role="tab" aria-selected="true" data-gallery-tab="experience">{esc(home['gallery_section']['tabs']['experience'])}</button><button role="tab" aria-selected="false" data-gallery-tab="equipment">{esc(home['gallery_section']['tabs']['equipment'])}</button></div><div class="gallery-rail">{gal}</div><button class="gallery-prev" type="button">Previous</button><button class="gallery-next" type="button">Next</button></section><section class="section room-planning"><div class="room-planning__text reveal"><p class="eyebrow">{esc(home['room_planning']['eyebrow'])}</p><h2>{esc(home['room_planning']['heading'])}</h2><p>{esc(home['room_planning']['description'])}</p><a href="{home['room_planning']['link_href']}">{esc(home['room_planning']['link_label'])}</a></div><div class="room-planning__sketch" aria-hidden="true"><span></span><span></span><span></span><span></span></div></section><section class="section faq-section" id="faq"><div class="faq-section__heading reveal"><p class="eyebrow">{esc(home['faq_section']['eyebrow'])}</p><h2>{esc(home['faq_section']['heading'])}</h2><p>{esc(home['faq_section']['description'])}</p></div><div class="faq-list">{faqs}</div></section><section class="section final-cta" id="booking"><div><h2>{esc(home['final_cta']['heading'])}</h2><p>{esc(home['final_cta']['description'])}</p><button class="button button--disabled" disabled>{esc(home['final_cta']['button']['label'])}</button></div></section></main><a class="mobile-booking" href="#booking">Check availability</a>'''+render_footer(home)+'<script src="/js/main.js" defer></script></body></html>'

def legal_page(home,d):
    sections=''.join(f'<section><h2>{esc(k.replace("_"," ").title())}</h2><p>{esc(v)}</p></section>' for k,v in d['sections'].items())
    return head(home,d['title'])+f'<body id="top"><a class="skip-link" href="#main">Skip to content</a>{header(home,"/")}<main id="main" class="legal-page"><p><a href="/">← Homepage</a></p><h1>{esc(d["title"])}</h1><p class="draft-warning">{esc(d["draft_warning"])}</p>{sections}</main>{render_footer(home,"/")}<script src="/js/main.js" defer></script></body></html>'

def main():
    for rel in REQUIRED_FILES:
        if not (CONTENT/rel).exists(): err('content/'+rel,'$','missing required file')
    home=read_json(Path('homepage.json')); validate_home(home)
    pkgs=validate_packages(read_json(Path('packages.json'))); pkg_ids={p['id'] for p in pkgs}
    addons=validate_rows('addons.csv',['title','description','available_for','price_note'],'addon')
    gallery=validate_rows('gallery.csv',['category','image','alt','caption'],'gallery')
    faq=validate_rows('faq.csv',['question','answer'],'faq')
    live=validate_rows('testimonials.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    demo=validate_rows('testimonials.example.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    terms=validate_legal('terms','terms'); privacy=validate_legal('privacy','privacy')
    if ERRORS:
        print('Build failed with content validation errors:',file=sys.stderr); print('\n'.join('- '+e for e in ERRORS),file=sys.stderr); sys.exit(1)
    copy_assets()
    html_out=page(home,pkgs,addons,gallery,faq,live)
    demo_out=page(home,pkgs,addons,gallery,faq,demo)
    (DIST/'index.html').write_text(html_out,encoding='utf-8')
    (DIST/'demo-testimonials.html').write_text(demo_out,encoding='utf-8')
    (DIST/'terms').mkdir(); (DIST/'terms'/'index.html').write_text(legal_page(home,terms),encoding='utf-8')
    (DIST/'privacy').mkdir(); (DIST/'privacy'/'index.html').write_text(legal_page(home,privacy),encoding='utf-8')
    print(f'Built dist with {len(pkgs)} packages, {len(addons)} add-ons, {len(gallery)} gallery items, {len(live)} live testimonials and {len(faq)} FAQs.')
if __name__=='__main__': main()
