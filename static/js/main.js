(function(){
'use strict';
document.documentElement.classList.add('js');
if(new URLSearchParams(location.search).get('demo')==='testimonials' && !location.pathname.includes('demo-testimonials')){ location.replace('/demo-testimonials.html'); return; }
var key='partyLanTheme', toggle=document.querySelector('.theme-toggle');
function apply(t,save){document.documentElement.dataset.theme=t;if(toggle){var d=t==='dark', label=d?'Dark mode active. Switch to light mode':'Light mode active. Switch to dark mode', icon=d?'☾':'☀';toggle.setAttribute('aria-pressed',String(d));toggle.setAttribute('aria-label',label);toggle.setAttribute('title',label);var i=toggle.querySelector('.theme-toggle__icon'); if(i)i.textContent=icon;} if(save)try{localStorage.setItem(key,t)}catch(e){}}
apply(document.documentElement.dataset.theme||'light',false); if(toggle)toggle.addEventListener('click',function(){apply(document.documentElement.dataset.theme==='dark'?'light':'dark',true)});
var mt=document.querySelector('.menu-toggle'), menu=document.getElementById('site-menu');
function isMobile(){return matchMedia('(max-width: 920px)').matches;}
function closeMenu(focus){if(!mt||!menu)return;menu.classList.remove('is-open');mt.setAttribute('aria-expanded','false');mt.setAttribute('aria-label','Open navigation menu');document.body.classList.remove('nav-open');if(focus)mt.focus();}
function openMenu(){menu.classList.add('is-open');mt.setAttribute('aria-expanded','true');mt.setAttribute('aria-label','Close navigation menu');document.body.classList.add('nav-open');var first=menu.querySelector('a'); if(first)first.focus({preventScroll:true});}

var header=document.querySelector('.site-header');
if(header){var lastY=window.pageYOffset||0,ticking=false,threshold=10,topLimit=80,reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;function forceHeader(){header.classList.remove('is-hidden')}function canHide(){return !document.body.classList.contains('nav-open')&&!header.contains(document.activeElement)}function onScroll(){var y=window.pageYOffset||document.documentElement.scrollTop||0,delta=y-lastY;if(y<topLimit||!canHide()){forceHeader();lastY=y;ticking=false;return;}if(Math.abs(delta)>=threshold){if(delta>0){header.classList.add('is-hidden')}else{forceHeader()}lastY=y;}ticking=false;}window.addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(onScroll)}},{passive:true});header.addEventListener('focusin',forceHeader);if(mt){mt.addEventListener('click',forceHeader)}document.addEventListener('keydown',function(e){if(e.key==='Tab')forceHeader});if(reducedMotion){header.style.transition='none';}}

if(mt&&menu){mt.addEventListener('click',function(e){e.stopPropagation();menu.classList.contains('is-open')?closeMenu(false):openMenu();}); menu.addEventListener('click',function(e){if(e.target.tagName==='A')closeMenu(false)}); document.addEventListener('click',function(e){if(menu.classList.contains('is-open')&&!e.target.closest('.site-header'))closeMenu(false)}); document.addEventListener('keydown',function(e){if(e.key==='Escape'&&menu.classList.contains('is-open'))closeMenu(true)});}
document.querySelectorAll('.package-expand').forEach(function(b){b.addEventListener('click',function(){var c=b.closest('.package-card'), open=!c.classList.contains('is-expanded'); c.classList.toggle('is-expanded',open); b.setAttribute('aria-expanded',String(open));});});
var addonsToggle=document.querySelector('.addons-toggle'), addonsPanel=document.querySelector('.addons-panel');
function setAddons(open){if(!addonsToggle||!addonsPanel)return;addonsPanel.classList.toggle('is-open',open);addonsToggle.setAttribute('aria-expanded',String(open));var label=addonsToggle.querySelector('.addons-toggle__label');if(label)label.textContent=open?'Hide add-ons':'Browse add-ons';}
if(addonsToggle){
  function openAddonsFromHash(){
    if(location.hash==='#make-your-own'){
      setAddons(true);
      setTimeout(function(){
        if(addonsPanel){
          var y=addonsPanel.getBoundingClientRect().top+window.pageYOffset-((header&&header.offsetHeight)||0)-18;
          window.scrollTo({top:Math.max(0,y),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
        }
      },0);
    }
  }
  setAddons(false);
  openAddonsFromHash();
  addonsToggle.addEventListener('click',function(){setAddons(addonsToggle.getAttribute('aria-expanded')!=='true')});
  window.addEventListener('hashchange',openAddonsFromHash);
}
document.querySelectorAll('.faq-item button').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.faq-item button').forEach(function(x){if(x!==b){x.setAttribute('aria-expanded','false');x.closest('.faq-item').classList.remove('is-open')}});var open=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(open));b.closest('.faq-item').classList.toggle('is-open',open);});});
function makeSlider(root, slideSelector, dotBoxSelector, labelFn, interval){var all=[].slice.call(root.querySelectorAll(slideSelector)), dotBox=root.querySelector(dotBoxSelector), slides=all, idx=0, timer, reduced=matchMedia('(prefers-reduced-motion: reduce)').matches, sx=0, sy=0, dragging=false, paused=reduced, toggle=root.querySelector('.showcase-toggle'), feedback=root.querySelector('.showcase-feedback'); function updateToggle(){root.classList.toggle('is-paused',paused);if(toggle){var noun=root.classList.contains('testimonial-stage')?'testimonials':'gallery';toggle.setAttribute('aria-pressed',String(paused));toggle.setAttribute('aria-label',paused?'Play '+noun:'Pause '+noun);toggle.querySelector('span').textContent=paused?'▶':'Ⅱ';}} function pulse(icon){if(feedback){feedback.textContent=icon;feedback.classList.add('is-visible');setTimeout(function(){feedback.classList.remove('is-visible')},520);}} function renderDots(){if(!dotBox)return; dotBox.innerHTML=''; slides.forEach(function(_,i){var b=document.createElement('button');b.type='button';b.className='slider-dot';b.setAttribute('aria-label',labelFn(i));b.innerHTML='<span></span>';b.addEventListener('click',function(){paused=true;go(i,true);updateToggle();});dotBox.appendChild(b);});} function go(n,manual){if(!slides.length)return;idx=(n+slides.length)%slides.length;all.forEach(function(s){s.classList.remove('is-active');s.setAttribute('aria-hidden','true')});slides[idx].classList.add('is-active');slides[idx].setAttribute('aria-hidden','false');[].slice.call(dotBox?dotBox.children:[]).forEach(function(d,i){d.setAttribute('aria-current',String(i===idx))}); if(manual)stop();} function stop(){clearInterval(timer);timer=null;} function start(){stop(); if(!paused&&!reduced&&slides.length>1)timer=setInterval(function(){go(idx+1,false)},interval||8500);} function togglePaused(){paused=!paused;updateToggle();pulse(paused?'Ⅱ':'▶');start();} root.addEventListener('mouseenter',function(){stop();});root.addEventListener('focusin',function(){stop();});root.addEventListener('mouseleave',start);root.addEventListener('touchstart',function(e){sx=e.touches[0].clientX;sy=e.touches[0].clientY},{passive:true});root.addEventListener('touchend',function(e){var dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>40){paused=true;go(idx+(dx<0?1:-1),true);updateToggle();}},{passive:true});root.addEventListener('pointerdown',function(e){if(e.target.closest('button'))return;dragging=true;sx=e.clientX;sy=e.clientY;root.setPointerCapture&&root.setPointerCapture(e.pointerId)});root.addEventListener('pointerup',function(e){if(!dragging)return;dragging=false;var dx=e.clientX-sx,dy=e.clientY-sy;if(Math.abs(dx)>50){paused=true;go(idx+(dx<0?1:-1),true);updateToggle();}else if(Math.abs(dx)<8&&Math.abs(dy)<8&&root.classList.contains('showcase')){togglePaused();}}); if(toggle){toggle.addEventListener('click',togglePaused);} updateToggle();return{setSlides:function(next){slides=next;idx=0;renderDots();go(0,false);start();}};}
document.querySelectorAll('.testimonial-stage').forEach(function(stage){var slider=makeSlider(stage,'.testimonial-slide','.testimonial-dots',function(i){return 'Show testimonial '+(i+1);},8000);slider.setSlides([].slice.call(stage.querySelectorAll('.testimonial-slide')));});
document.querySelectorAll('.showcase').forEach(function(showcase){var section=showcase.closest('.showcase-section'), tabs=[].slice.call(section.querySelectorAll('[data-gallery-tab]')), all=[].slice.call(showcase.querySelectorAll('.showcase-slide')), activeCat='experience', slider=makeSlider(showcase,'.showcase-slide','.showcase-indicators',function(i){return 'Show '+activeCat+' image '+(i+1);},9000); function select(cat){activeCat=cat;tabs.forEach(function(t){t.setAttribute('aria-selected',String(t.dataset.galleryTab===cat))});slider.setSlides(all.filter(function(s){return s.dataset.category===cat}));} tabs.forEach(function(t,i){t.addEventListener('click',function(){select(t.dataset.galleryTab)});t.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();var n=(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[n].focus();tabs[n].click();}})});select(activeCat);});

document.querySelectorAll('.package-tabs').forEach(function(tablist){
  var tabs=[].slice.call(tablist.querySelectorAll('[role="tab"]'));
  var panels=tabs.map(function(t){return document.getElementById(t.getAttribute('aria-controls'));});
  function select(tab, focus){
    tabs.forEach(function(t,i){var on=t===tab;t.setAttribute('aria-selected',String(on));if(panels[i]){panels[i].hidden=!on;}});
    if(focus)tab.focus({preventScroll:true});
  }
  tabs.forEach(function(tab,i){tab.addEventListener('click',function(){select(tab,false)});tab.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();select(tabs[(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length],true);}});});
  function syncPackageMode(){if(matchMedia('(max-width: 920px)').matches){var current=tabs.find(function(t){return t.getAttribute('aria-selected')==='true'})||tabs[0];if(current)select(current,false);}else{panels.forEach(function(p){if(p)p.hidden=false;});}}
  syncPackageMode();
  window.addEventListener('resize',syncPackageMode,{passive:true});
});
document.querySelectorAll('.packages-decision').forEach(function(section){
  var toggles=[].slice.call(section.querySelectorAll('[data-support-toggle]'));
  var panels={ask:section.querySelector('#packages-ask-panel'),questions:section.querySelector('#packages-questions-panel')};
  function setPanel(name){
    toggles.forEach(function(t){var on=t.dataset.supportToggle===name && t.getAttribute('aria-expanded')!=='true';t.setAttribute('aria-expanded',String(on));if(panels[t.dataset.supportToggle])panels[t.dataset.supportToggle].classList.toggle('is-open',on);});
  }
  toggles.forEach(function(t){t.addEventListener('click',function(){setPanel(t.dataset.supportToggle)});});
});
document.querySelectorAll('.package-faq-item button').forEach(function(b){b.addEventListener('click',function(){var item=b.closest('.package-faq-item'),open=b.getAttribute('aria-expanded')!=='true';document.querySelectorAll('.package-faq-item').forEach(function(x){x.classList.remove('is-open');var xb=x.querySelector('button');if(xb)xb.setAttribute('aria-expanded','false')});item.classList.toggle('is-open',open);b.setAttribute('aria-expanded',String(open));});});

function initContact(component){
  var form=component.querySelector('[data-contact-form]'), success=component.querySelector('[data-contact-success]'), status=component.querySelector('[data-contact-status]'); if(!form)return;
  var intents=['availability','booking','question'], packages=['onyx','jade','unsure'];
  var intent=form.elements.intent, pkg=form.elements.package, fields=[].slice.call(form.querySelectorAll('.field--event')), disclosure=form.querySelector('.contact-disclosure'), eventToggle=form.querySelector('[data-event-toggle]');
  var params=new URLSearchParams(location.search), qi=params.get('intent'), qp=params.get('package');
  intent.value=intents.indexOf(qi)>=0?qi:(intents.indexOf(component.dataset.defaultIntent)>=0?component.dataset.defaultIntent:'question');
  pkg.value=packages.indexOf(qp)>=0?qp:(packages.indexOf(component.dataset.defaultPackage)>=0?component.dataset.defaultPackage:'unsure');
  function setEvents(show){fields.forEach(function(f){f.hidden=!show}); if(disclosure)disclosure.hidden=intent.value!=='question'||show; if(eventToggle)eventToggle.setAttribute('aria-expanded',String(show));}
  setEvents(intent.value!=='question'); intent.addEventListener('change',function(){setEvents(intent.value!=='question')}); if(eventToggle)eventToggle.addEventListener('click',function(){setEvents(true)});
  function err(name,msg){var el=form.elements[name], box=form.querySelector('[data-error-for="'+name+'"]'); if(el)el.setAttribute('aria-invalid',msg?'true':'false'); if(box)box.textContent=msg||''; return !!msg;}
  function validate(){var bad=[], data=Object.fromEntries(new FormData(form).entries()); ['intent','package','name','email','phone','location','players','message','privacy','preferred_date','alternative_date'].forEach(function(n){err(n,'')});
    if(intents.indexOf(data.intent)<0)bad.push(['intent','Choose a supported enquiry type.']);
    if(!data.name||data.name.trim().length<2||data.name.length>80)bad.push(['name','Enter your name.']);
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email||''))bad.push(['email','Enter a valid email address.']);
    if(data.phone && (data.phone.length<7||data.phone.length>30))bad.push(['phone','Enter a valid phone number, or leave it blank.']);
    if(data.location && data.location.length<2)bad.push(['location','Enter a town or postcode, or leave it blank.']);
    if(packages.indexOf(data.package)<0)bad.push(['package','Choose a supported package option.']);
    if(data.players && (+data.players<1||+data.players>40))bad.push(['players','Enter a player count between 1 and 40.']);
    ['preferred_date','alternative_date'].forEach(function(n){if(data[n] && !/^\d{4}-\d{2}-\d{2}$/.test(data[n]))bad.push([n,'Enter a valid date.']);});
    var msg=(data.message||'').trim(); if(msg && (msg.length<10||msg.length>2000))bad.push(['message','Use 10 to 2000 characters, or leave it blank when event details explain enough.']);
    if(data.intent==='question'&&!msg)bad.push(['message','Enter a message.']);
    if(data.intent!=='question'&&!msg&&!data.preferred_date)bad.push(['preferred_date','Add a preferred date or explain what you need in the message.']);
    if(data.intent!=='question'&&!msg&&!data.location)bad.push(['location','Add a town/postcode or explain what you need in the message.']);
    if(!form.elements.privacy.checked)bad.push(['privacy','Please acknowledge the privacy notice.']);
    bad.forEach(function(x){err(x[0],x[1])}); if(bad[0]&&form.elements[bad[0][0]])form.elements[bad[0][0]].focus({preventScroll:false}); return !bad.length;
  }
  form.addEventListener('submit',function(e){e.preventDefault(); status.className='contact-status'; status.textContent=''; if(!validate())return; var btn=form.querySelector('[type=submit]'); btn.disabled=true; form.setAttribute('aria-busy','true'); btn.textContent='Sending…';
    fetch(form.action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(Object.fromEntries(new FormData(form).entries()))}).then(function(r){return r.json().catch(function(){return{}}).then(function(j){if(!r.ok)throw {status:r.status,json:j}; return j;});}).then(function(){form.hidden=true; success.hidden=false; success.focus&&success.focus();}).catch(function(ex){var unavailable=!ex.status||ex.status>=500; status.className='contact-status is-error'; status.innerHTML=unavailable?'Service unavailable. Please email <a href="mailto:hello@partylan.co.uk">hello@partylan.co.uk</a>.':'We couldn’t send your enquiry. Please check your details and try again.';}).finally(function(){btn.disabled=false; form.removeAttribute('aria-busy'); btn.textContent=btn.dataset.submitLabel||'Send enquiry';});
  });
  var again=component.querySelector('[data-send-another]'); if(again)again.addEventListener('click',function(){success.hidden=true; form.hidden=false; status.textContent=''; form.focus();});
}
document.querySelectorAll('[data-contact-component]').forEach(initContact);
document.querySelectorAll('.packages-decision').forEach(function(section){
  var inline=document.getElementById('packages-contact'); if(!inline)return;
  function currentPackage(){var selected=document.querySelector('.package-tab[aria-selected="true"]'); return matchMedia('(max-width: 920px)').matches && selected ? selected.dataset.packageTab : 'unsure';}
  function open(intent){inline.hidden=false; var form=inline.querySelector('form'); if(form){form.elements.intent.value=intent; form.elements.intent.dispatchEvent(new Event('change')); form.elements.package.value=currentPackage();} document.querySelectorAll('.package-faq-item').forEach(function(x){x.classList.remove('is-open'); var b=x.querySelector('button'); if(b)b.setAttribute('aria-expanded','false')}); inline.scrollIntoView({block:'nearest',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});}
  var reserve=section.querySelector('.packages-decision__reserve'); if(reserve)reserve.addEventListener('click',function(e){e.preventDefault(); open('booking')});
  section.querySelectorAll('[data-support-toggle="ask"]').forEach(function(b){b.addEventListener('click',function(){open('question')});});
});

var atmosphere=document.querySelector('.site-background__middle');
if(atmosphere){
  var reduceBg=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var bgY=window.pageYOffset||0, bgTick=false, bgLimit=1200;
  function measureAtmosphere(){
    var maxScroll=Math.max(0,document.documentElement.scrollHeight-window.innerHeight);
    bgLimit=Math.max(480,Math.ceil(maxScroll*.5)+240);
  }
  function updateAtmosphere(){
    var offset=Math.max(-bgLimit,Math.min(bgLimit,bgY*-0.5));
    atmosphere.style.transform='translate3d(0,'+offset.toFixed(1)+'px,0)';
    bgTick=false;
  }
  if(!reduceBg){
    measureAtmosphere();
    window.addEventListener('resize',measureAtmosphere,{passive:true});
    window.addEventListener('scroll',function(){bgY=window.pageYOffset||document.documentElement.scrollTop||0;if(!bgTick){bgTick=true;requestAnimationFrame(updateAtmosphere);}},{passive:true});
    updateAtmosphere();
  }
}

var io=('IntersectionObserver'in window&&!matchMedia('(prefers-reduced-motion: reduce)').matches)?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target)}})},{threshold:.12}):null;document.querySelectorAll('.reveal').forEach(function(el){io?io.observe(el):el.classList.add('is-visible')});
}());
