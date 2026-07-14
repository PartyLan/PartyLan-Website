#!/usr/bin/env python3
"""Standard-library static build and content validation for Party.LAN."""
from __future__ import annotations
import csv, html, json, shutil, sys
from pathlib import Path
ROOT=Path(__file__).parent.resolve(); CONTENT=ROOT/'content'; STATIC=ROOT/'static'; DIST=ROOT/'dist'; IMAGES=CONTENT/'images'
ERRORS=[]; BOOL={'true':True,'false':False}; IMG_EXT={'.jpg','.jpeg','.png','.webp','.avif'}
REQUIRED_FILES=['homepage.json','packages.json','addons.csv','testimonials.csv','testimonials.example.csv','gallery.csv','faq.csv','legal/terms.json','legal/privacy.json']
PACKAGE_FACTS={'onyx':{'name':'ONYX','label':'Premium Experience','price':'£150','duration':'2 hours','capacity':'Up to 6 players','included':['PlayStation and Nintendo gaming','Racing simulator','VR hardware','Displays','Party host/operator','Free digital invitation']},'jade':{'name':'JADE','label':'Big Party','price':'£150','duration':'2 hours','capacity':'Up to 10 players','included':['Multiplayer gaming across multiple stations','Displays','Party host/operator','Free digital invitation']}}
LEGAL_SECTIONS={'terms':['introduction','booking','payment','cancellation','venue_access','room_and_power_requirements','supervision','equipment_care','damage','travel','contact'],'privacy':['introduction','information_collected','purpose_of_processing','service_providers','retention','customer_rights','contact']}
def err(f,k,r): ERRORS.append(f'{f} {k}: {r}')
def esc(v): return html.escape(str(v), quote=True)
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
    try:
        with (CONTENT/rel).open(newline='',encoding='utf-8') as fh: return list(csv.DictReader(fh))
    except FileNotFoundError: err('content/'+rel,'$','missing required file'); return []
    except csv.Error as e: err('content/'+rel,'$','malformed CSV: '+str(e)); return []
def validate_home(h):
    f='content/homepage.json'
    for k in ['meta','navigation','header','hero','reassurance','testimonials_section','how_it_works','gallery_section','faq_section','final_cta','footer','packages_page','addons_section']:
        if k not in h: err(f,k,'required top-level key is missing')
    req_text(f,h.get('hero',{}),'title','hero'); req_text(f,h.get('hero',{}),'description','hero')
    if h.get('hero',{}).get('primary_cta',{}).get('href')!='/packages/': err(f,'hero.primary_cta.href','expected /packages/')
    for key in ['light','dark']: image_ok(f,'hero.media.'+key,h.get('hero',{}).get('media',{}).get(key,''))
    for key in ['logo_light','logo_dark']: image_ok(f,'header.'+key,h.get('header',{}).get(key,''))
    labels=[n.get('label') for n in h.get('navigation',[])]
    if labels!=['Packages','FAQ','Check availability']: err(f,'navigation','expected Packages, FAQ and Check availability only')
    pp=h.get('packages_page',{})
    for key in ['meta_title','hero','intro','guidance','cta']:
        if key not in pp: err(f,'packages_page.'+key,'required Packages-page content is missing')
    req_text(f,pp.get('hero',{}),'heading','packages_page.hero'); req_text(f,pp.get('hero',{}),'description','packages_page.hero')
    for key in ['light','dark']: image_ok(f,'packages_page.hero.media.'+key,pp.get('hero',{}).get('media',{}).get(key,''))
    terms=h.get('faq_section',{}).get('terms_link',{})
    if terms.get('href')!='/terms/': err(f,'faq_section.terms_link.href','expected /terms/')
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
        if visible: out.append(r)
    return sorted(out,key=lambda r:r['_order'])
def validate_legal(rel, key):
    d=read_json(Path('legal')/(rel+'.json')); file=f'content/legal/{rel}.json'
    req_text(file,d,'title','page'); req_text(file,d,'draft_warning','page')
    for s in LEGAL_SECTIONS[key]: req_text(file,d.get('sections',{}),s,'sections')
    return d
def copy_assets():
    if DIST.exists(): shutil.rmtree(DIST)
    DIST.mkdir(); shutil.copytree(STATIC,DIST,dirs_exist_ok=True)
    dest=DIST/'assets'/'images'; dest.mkdir(parents=True,exist_ok=True)
    for p in IMAGES.rglob('*'):
        if p.is_file() and p.suffix.lower() in IMG_EXT:
            d=dest/p.relative_to(IMAGES); d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,d)
def rel_href(href,prefix): return (prefix+href if href.startswith('#') else href)
def nav(home,prefix=''):
    links=''.join(f'<a class="{"site-menu__availability" if i["label"]=="Check availability" else ""}" href="{rel_href(i["href"],prefix)}">{esc(i["label"])}</a>' for i in home['navigation'])
    return links
def footer(home,prefix=''):
    links=''.join(f'<a href="{rel_href(l["href"],prefix)}">{esc(l["label"])}</a>' for l in home['footer']['links'])
    return f'<footer class="site-footer"><p>{esc(home["footer"]["tagline"])}</p><nav aria-label="Footer navigation">{links}</nav></footer>'
def header(home,prefix=''):
    c=home['header']['availability_cta']
    return f'''<header class="site-header"><nav class="nav-shell" aria-label="Main navigation"><a class="brand" href="/"><span class="brand__mark"><img class="brand__logo brand__logo--light" src="{home['header']['logo_light']}" alt="Party.LAN" width="168" height="58"><img class="brand__logo brand__logo--dark" src="{home['header']['logo_dark']}" alt="" aria-hidden="true" width="168" height="58"></span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-menu">Menu</button><div class="site-menu" id="site-menu">{nav(home,prefix)}</div><button class="theme-toggle" type="button" aria-pressed="false"><span aria-hidden="true">◐</span><span class="theme-toggle__label">Theme</span></button><a class="button button--small header-cta" href="{rel_href(c['href'],prefix)}">{esc(c['label'])}</a></nav></header>'''
def head(home,title=None,desc=None):
    m=home['meta']; return f'''<!doctype html><html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title or m['title'])}</title><meta name="description" content="{esc(desc or m['description'])}"><link rel="canonical" href="{esc(m['canonical_url'])}"><meta property="og:image" content="{esc(m['og_image'])}"><meta name="theme-color" content="{m['theme_color_light']}"><script>(function(){{try{{var s=localStorage.getItem('partyLanTheme');document.documentElement.dataset.theme=s||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}}catch(e){{document.documentElement.dataset.theme='light';}}}}());</script><link rel="stylesheet" href="/css/styles.css"></head>'''
def testimonial_section(home, rows):
    if not rows: return ''
    slides=''.join(f'<article class="testimonial-slide {"is-active" if i==0 else ""}" aria-hidden="{"false" if i==0 else "true"}"><img src="{r["image"]}" alt="{esc(r["alt"])}"><div class="testimonial-slide__content"><blockquote><p>“{esc(r["quote"])}”</p></blockquote><p><b>{esc(r["name"])}</b>{", age "+esc(r["age"]) if r.get("age") else ""}</p><p>{esc(r.get("location",""))} {esc(r.get("package",""))}</p></div></article>' for i,r in enumerate(rows))
    dots=''.join(f'<button class="testimonial-dot" type="button" aria-label="Show testimonial {i+1} of {len(rows)}"><span></span></button>' for i,_ in enumerate(rows))
    s=home['testimonials_section']; return f'<section class="section testimonials" id="testimonials" aria-labelledby="testimonials-title"><div class="section-heading reveal"><p class="eyebrow">{esc(s["eyebrow"])}</p><h2 id="testimonials-title">{esc(s["heading"])}</h2><p>{esc(s["description"])}</p></div><div class="testimonial-stage" role="region" aria-roledescription="carousel"><div class="testimonial-track">{slides}</div><div class="testimonial-dots">{dots}</div></div></section>'
def showcase(home,gallery):
    slides=''.join(f'<figure class="showcase-slide {"is-active" if i==0 else ""}" data-category="{r["category"]}" data-caption="{esc(r["caption"])}"><img src="{r["image"]}" alt="{esc(r["alt"])}" loading="lazy"><figcaption>{esc(r["caption"])}</figcaption></figure>' for i,r in enumerate(gallery))
    g=home['gallery_section']; return f'<section class="section showcase-section" id="gallery" aria-labelledby="gallery-title"><div class="section-heading reveal"><p class="eyebrow">{esc(g["eyebrow"])}</p><h2 id="gallery-title">{esc(g["heading"])}</h2><p>{esc(g["description"])}</p></div><div class="gallery-tabs" role="tablist"><button role="tab" aria-selected="true" data-gallery-tab="experience">{esc(g["tabs"]["experience"])}</button><button role="tab" aria-selected="false" data-gallery-tab="equipment">{esc(g["tabs"]["equipment"])}</button></div><div class="showcase" role="region" aria-label="Party.LAN image showcase"><div class="showcase-track">{slides}</div><div class="showcase-indicators" aria-label="Choose gallery image"></div></div></section>'
def steps(home):
    return ''.join(f'<article class="step-card reveal"><span>{i}</span><h3>{esc(s["title"])}</h3><p>{esc(s["description"])}</p></article>' for i,s in enumerate(home['how_it_works']['steps'],1))
def faq(home, rows):
    items=''.join(f'<div class="faq-item"><h3><button aria-expanded="false" aria-controls="faq-{r["id"]}" id="faq-btn-{r["id"]}">{esc(r["question"])}<span aria-hidden="true">+</span></button></h3><div class="faq-item__answer" id="faq-{r["id"]}" role="region" aria-labelledby="faq-btn-{r["id"]}"><p>{esc(r["answer"])}</p></div></div>' for r in rows)
    f=home['faq_section']; tl=f['terms_link']
    return f'<section class="section faq-section" id="faq"><div class="faq-section__heading reveal"><p class="eyebrow">{esc(f["eyebrow"])}</p><h2>{esc(f["heading"])}</h2><p>{esc(f["description"])}</p></div><div><div class="faq-list">{items}</div><p class="faq-terms"><a href="{tl["href"]}">{esc(tl["text"])}</a></p></div></section>'
def home_page(home,gallery,faq_rows,testimonials):
    h=home['hero']; reass=''.join(f'<li><span>{esc(i["text"])}</span></li>' for i in home['reassurance']); cta=home['final_cta']
    return head(home)+'<body id="top"><a class="skip-link" href="#main">Skip to content</a>'+header(home,'')+f'''<main id="main"><section class="hero hero--home" aria-labelledby="hero-title"><div class="hero__picture" role="img" aria-label="{esc(h['media']['alt'])}"><div class="hero__media-motion"><img class="hero__image hero__image--light" src="{h['media']['light']}" alt=""><img class="hero__image hero__image--dark" src="{h['media']['dark']}" alt=""></div></div><div class="hero__inner"><div class="hero__content reveal"><p class="eyebrow">{esc(h['eyebrow'])}</p><h1 id="hero-title">{esc(h['title'])}</h1><p>{esc(h['description'])}</p><div class="button-row"><a class="button" href="{h['primary_cta']['href']}">{esc(h['primary_cta']['label'])}</a><a class="button button--ghost" href="{h['secondary_cta']['href']}">{esc(h['secondary_cta']['label'])}</a></div></div></div></section><section class="reassurance"><ul>{reass}</ul></section><section class="section how-section" id="how-it-works"><div class="section-heading section-heading--center reveal"><p class="eyebrow">{esc(home['how_it_works']['eyebrow'])}</p><h2>{esc(home['how_it_works']['heading'])}</h2></div><div class="steps-grid">{steps(home)}</div></section>{testimonial_section(home,testimonials)}{showcase(home,gallery)}{faq(home,faq_rows)}<section class="section final-cta" id="booking"><div><h2>{esc(cta['heading'])}</h2><p>{esc(cta['description'])}</p><a class="button" href="/packages/">{esc(cta['button']['label'])}</a></div></section></main><a class="mobile-booking" href="#booking">Check availability</a>'''+footer(home,'')+'<script src="/js/main.js" defer></script></body></html>'
def package_cards(pkgs):
    out=[]
    for p in pkgs:
        feats=''.join(f'<li>{esc(x)}</li>' for x in p['included'])
        out.append(f'''<article class="package-card package-card--{p['id']} reveal" id="package-{p['id']}"><div class="package-card__top"><p class="package-subtitle">{esc(p['label'])}</p><h2>{esc(p['name'])}</h2><p>{esc(p['summary'])}</p></div><div class="package-facts"><strong>{esc(p['price'])}</strong><span>{esc(p['duration'])}</span><span>{esc(p['capacity'])}</span></div><ul class="feature-list">{feats}</ul><button class="package-expand" type="button" aria-expanded="false">{esc(p['details_button'])}<span aria-hidden="true">⌄</span></button><div class="package-details"><p>{esc(p['expanded']['overview'])}</p><dl><dt>Suited to</dt><dd>{esc(p['expanded']['suited_to'])}</dd><dt>Age/group guidance</dt><dd>{esc(p['expanded']['age_guidance'])}</dd><dt>Room guidance</dt><dd>{esc(p['expanded']['room_guidance'])}</dd></dl><p>{esc(p['enquiry_note'])}</p></div><a class="button" href="/#booking">{esc(p['enquiry_button'])}</a></article>''')
    return ''.join(out)
def package_page(home, pkgs, addons):
    pp=home['packages_page']; ph=pp['hero']
    add=''.join(f'<article class="addon-tile"><p class="addon-kicker">{esc(a["available_for"])}</p><h3>{esc(a["title"])}</h3><p>{esc(a["description"])}</p><strong>{esc(a["price_note"])}</strong></article>' for a in addons)
    return head(home,pp['meta_title'],pp['hero']['description'])+f'''<body id="top"><a class="skip-link" href="#main">Skip to content</a>{header(home,'/')}<main id="main"><section class="packages-hero" aria-labelledby="packages-title"><div class="packages-hero__media" role="img" aria-label="{esc(ph['media']['alt'])}"><img class="hero__image hero__image--light" src="{ph['media']['light']}" alt=""><img class="hero__image hero__image--dark" src="{ph['media']['dark']}" alt=""></div><div class="packages-hero__content"><p class="eyebrow">{esc(ph['eyebrow'])}</p><h1 id="packages-title">{esc(ph['heading'])}</h1><p>{esc(ph['description'])}</p></div></section><section class="packages-overlap" aria-label="Party.LAN packages"><div class="package-grid package-grid--overlap">{package_cards(pkgs)}</div><section class="addons-panel addons-panel--packages"><h2>{esc(home['addons_section']['heading'])}</h2><p>{esc(home['addons_section']['description'])}</p><div class="addon-grid">{add}</div></section></section><section class="section package-guidance"><p class="eyebrow">{esc(pp['guidance']['eyebrow'])}</p><h2>{esc(pp['guidance']['heading'])}</h2><p>{esc(pp['guidance']['description'])}</p></section><section class="section final-cta" id="booking"><div><h2>{esc(pp['cta']['heading'])}</h2><p>{esc(pp['cta']['description'])}</p><a class="button" href="/#booking">{esc(pp['cta']['button_label'])}</a></div></section></main>{footer(home,'/')}<script src="/js/main.js" defer></script></body></html>'''
def legal_page(home,d):
    sections=''.join(f'<section><h2>{esc(k.replace("_"," ").title())}</h2><p>{esc(v)}</p></section>' for k,v in d['sections'].items())
    return head(home,d['title'])+f'<body id="top"><a class="skip-link" href="#main">Skip to content</a>{header(home,"/")}<main id="main" class="legal-page"><p><a href="/">← Homepage</a></p><h1>{esc(d["title"])}</h1><p class="draft-warning">{esc(d["draft_warning"])}</p>{sections}</main>{footer(home,"/")}<script src="/js/main.js" defer></script></body></html>'
def main():
    for rel in REQUIRED_FILES:
        if not (CONTENT/rel).exists(): err('content/'+rel,'$','missing required file')
    home=read_json(Path('homepage.json')); validate_home(home)
    pkgs=validate_packages(read_json(Path('packages.json'))); pkg_ids={p['id'] for p in pkgs}
    addons=validate_rows('addons.csv',['title','description','available_for','price_note'],'addon')
    gallery=validate_rows('gallery.csv',['category','image','alt','caption'],'gallery')
    faq_rows=validate_rows('faq.csv',['question','answer'],'faq')
    live=validate_rows('testimonials.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    demo=validate_rows('testimonials.example.csv',['quote','name','image','alt'],'testimonial',pkg_ids)
    terms=validate_legal('terms','terms'); privacy=validate_legal('privacy','privacy')
    if ERRORS:
        print('Build failed with content validation errors:',file=sys.stderr); print('\n'.join('- '+e for e in ERRORS),file=sys.stderr); sys.exit(1)
    copy_assets()
    (DIST/'index.html').write_text(home_page(home,gallery,faq_rows,live),encoding='utf-8')
    (DIST/'demo-testimonials.html').write_text(home_page(home,gallery,faq_rows,demo),encoding='utf-8')
    (DIST/'packages').mkdir(); (DIST/'packages'/'index.html').write_text(package_page(home,pkgs,addons),encoding='utf-8')
    (DIST/'terms').mkdir(); (DIST/'terms'/'index.html').write_text(legal_page(home,terms),encoding='utf-8')
    (DIST/'privacy').mkdir(); (DIST/'privacy'/'index.html').write_text(legal_page(home,privacy),encoding='utf-8')
    print(f'Built dist with homepage, packages page, {len(addons)} add-ons, {len(gallery)} gallery items, {len(live)} live testimonials and {len(faq_rows)} FAQs.')
if __name__=='__main__': main()
