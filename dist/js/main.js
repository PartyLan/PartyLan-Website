// The outer function creates a private scope. Names declared in this file stay
// inside it instead of becoming global variables that other scripts could alter.
(function(){
'use strict';

// BROWSER BEHAVIOUR MAP
// ---------------------
// This single dependency-free script controls theme persistence, navigation,
// accordions, sliders, package selection, enquiry forms, decorative parallax
// and reveal-on-scroll effects. Each feature checks for its own markup first,
// so the same file can run safely on every generated page.

// BEGINNER'S JAVASCRIPT / BROWSER GLOSSARY
// ----------------------------------------
// The DOM is the browser's in-memory version of the HTML page. JavaScript finds
// DOM elements, reads their state, and changes classes/attributes when visitors
// interact with them. It does not permanently edit the generated HTML files.
//
// document.querySelector('.name') finds the first element with class="name".
// document.querySelectorAll(...)   finds every matching element.
// .addEventListener('click', ...)  says what should happen after an event.
// .classList.add/remove/toggle     changes CSS classes on an element.
// .getAttribute/.setAttribute     reads or changes an HTML attribute.
// [data-example] / element.dataset are custom labels joining HTML and JavaScript.
// aria-expanded="true/false"      tells assistive software if a control is open.
// hidden                          removes content from display/accessibility flow.
// disabled                        prevents a form control being used or submitted.
// matchMedia(...)                 checks screen width or reduced-motion preference.
// requestAnimationFrame(...)      waits for the browser's next visual update.
// Promise / .then(...)            waits for asynchronous work such as image decode.
//
// var introduces a stored value; function introduces reusable instructions.
// if chooses whether code runs, and forEach repeats code for matching elements.
// A leading dot in a selector means a CSS class; # means a unique HTML id.
//
// MOST FEATURES FOLLOW THE SAME FOUR STEPS
// 1. Find the relevant HTML elements with querySelector/querySelectorAll.
// 2. Define small functions that describe possible state changes.
// 3. Attach those functions to click, keyboard, scroll or form events.
// 4. Set a correct initial state before the visitor interacts with the page.

// The .js class lets CSS progressively enhance controls only when JavaScript is
// available. This is called progressive enhancement: without JavaScript, the
// core page content remains readable rather than becoming a blank/broken page.
document.documentElement.classList.add('js');

// The query flag is a convenience preview route for example testimonials.
if(new URLSearchParams(location.search).get('demo')==='testimonials' && !location.pathname.includes('demo-testimonials')){ location.replace('/demo-testimonials.html'); return; }

// ================================================================
// Theme selection
// ================================================================

// localStorage is a small browser-owned store that survives page changes and
// return visits. Keep the chosen theme there, then synchronise the visible icon
// and accessible labels every time the theme changes.
var key='partyLanTheme', toggle=document.querySelector('.theme-toggle');
function apply(t,save){document.documentElement.dataset.theme=t;if(toggle){var d=t==='dark', label=d?'Dark mode active. Switch to light mode':'Light mode active. Switch to dark mode', icon=d?'☾':'☀';toggle.setAttribute('aria-pressed',String(d));toggle.setAttribute('aria-label',label);toggle.setAttribute('title',label);var i=toggle.querySelector('.theme-toggle__icon'); if(i)i.textContent=icon;} if(save)try{localStorage.setItem(key,t)}catch(e){}}
apply(document.documentElement.dataset.theme||'light',false); if(toggle)toggle.addEventListener('click',function(){apply(document.documentElement.dataset.theme==='dark'?'light':'dark',true)});

// ================================================================
// Header and complete navigation menu
// ================================================================

// Save references to the menu button and menu so later functions can reuse them
// without searching the DOM repeatedly. isMobile() is retained for compatibility
// with earlier menu logic; current responsive behaviour is primarily CSS-led.
var mt=document.querySelector('.menu-toggle'), menu=document.getElementById('site-menu');
function isMobile(){return matchMedia('(max-width: 920px)').matches;}
function closeMenu(focus){if(!mt||!menu)return;menu.classList.remove('is-open');mt.setAttribute('aria-expanded','false');mt.setAttribute('aria-label','Open navigation menu');document.body.classList.remove('nav-open');if(focus)mt.focus();}
function openMenu(){menu.classList.add('is-open');mt.setAttribute('aria-expanded','true');mt.setAttribute('aria-label','Close navigation menu');document.body.classList.add('nav-open');var first=menu.querySelector('a'); if(first)first.focus({preventScroll:true});}

// Hide the header while scrolling down and reveal it while scrolling up. The
// ticking flag allows only one calculation per animation frame, which prevents
// a fast scroll from queueing hundreds of layout updates. Keyboard focus and an
// open menu always force the header to stay visible.
var header=document.querySelector('.site-header');
if(header){var lastY=window.pageYOffset||0,ticking=false,threshold=10,topLimit=80,reducedMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;function forceHeader(){header.classList.remove('is-hidden')}function canHide(){return !document.body.classList.contains('nav-open')&&!header.contains(document.activeElement)}function onScroll(){var y=window.pageYOffset||document.documentElement.scrollTop||0,delta=y-lastY;if(y<topLimit||!canHide()){forceHeader();lastY=y;ticking=false;return;}if(Math.abs(delta)>=threshold){if(delta>0){header.classList.add('is-hidden')}else{forceHeader()}lastY=y;}ticking=false;}window.addEventListener('scroll',function(){if(!ticking){ticking=true;requestAnimationFrame(onScroll)}},{passive:true});header.addEventListener('focusin',forceHeader);if(mt){mt.addEventListener('click',forceHeader)}document.addEventListener('keydown',function(e){if(e.key==='Tab')forceHeader});if(reducedMotion){header.style.transition='none';}}

// Open/close the menu from its button, links, outside clicks or Escape.
if(mt&&menu){mt.addEventListener('click',function(e){e.stopPropagation();menu.classList.contains('is-open')?closeMenu(false):openMenu();}); menu.addEventListener('click',function(e){if(e.target.tagName==='A')closeMenu(false)}); document.addEventListener('click',function(e){if(menu.classList.contains('is-open')&&!e.target.closest('.site-header'))closeMenu(false)}); document.addEventListener('keydown',function(e){if(e.key==='Escape'&&menu.classList.contains('is-open'))closeMenu(true)});}

// ================================================================
// Reusable rollout controls and accordions
// ================================================================

// Change a rollout button's text to its data-label-open/closed value. The HTML
// stores both possible labels; this helper chooses the one matching aria-expanded.
function syncRolloutLabel(button){var label=button&&button.querySelector('[data-rollout-label]');if(!button||!label)return;var open=button.getAttribute('aria-expanded')==='true';label.textContent=open?(button.dataset.labelOpen||label.textContent):(button.dataset.labelClosed||label.textContent);}
document.querySelectorAll('[data-label-open][data-label-closed]').forEach(syncRolloutLabel);

// Each package card expands independently to expose its detailed description.
document.querySelectorAll('.package-expand').forEach(function(b){syncRolloutLabel(b);b.addEventListener('click',function(){var c=b.closest('.package-card'),open=!c.classList.contains('is-expanded');c.classList.toggle('is-expanded',open);b.setAttribute('aria-expanded',String(open));syncRolloutLabel(b);});});

// The add-on panel can also open from /packages/#make-your-own. The delayed
// scroll runs after layout updates so the sticky-header offset is accurate.
var addonsToggle=document.querySelector('.addons-toggle'), addonsPanel=document.querySelector('.addons-panel');
function setAddons(open){if(!addonsToggle||!addonsPanel)return;addonsPanel.classList.toggle('is-open',open);addonsToggle.setAttribute('aria-expanded',String(open));syncRolloutLabel(addonsToggle);}
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

// Landing-page FAQs use a single-open accordion pattern: opening one answer
// closes the others, and the CSS reads .is-open to animate the visible answer.
document.querySelectorAll('.faq-item button').forEach(function(b){b.addEventListener('click',function(){document.querySelectorAll('.faq-item button').forEach(function(x){if(x!==b){x.setAttribute('aria-expanded','false');x.closest('.faq-item').classList.remove('is-open')}});var open=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(open));b.closest('.faq-item').classList.toggle('is-open',open);});});

// ================================================================
// Shared testimonial and gallery slider
// ================================================================

// Build a slider controller around existing slides. "root" is the outer carousel
// element; the selector arguments tell the same reusable function where its
// slides and dot container live. It provides dots, timed advance, pause/play,
// pointer dragging, touch swipes and reduced-motion support.
function makeSlider(root, slideSelector, dotBoxSelector, labelFn, interval){
  var all=[].slice.call(root.querySelectorAll(slideSelector));
  var dotBox=root.querySelector(dotBoxSelector),slides=all,idx=0,timer;
  var reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var sx=0,sy=0,dragging=false,paused=reduced,activationToken=0;
  var toggle=root.querySelector('.showcase-toggle');
  var feedback=root.querySelector('.showcase-feedback');

  // Keep visual paused state, aria-pressed, label and icon in sync.
  function updateToggle(){
    root.classList.toggle('is-paused',paused);
    if(toggle){
      var noun=root.classList.contains('testimonial-stage')?'testimonials':'gallery';
      toggle.setAttribute('aria-pressed',String(paused));
      toggle.setAttribute('aria-label',paused?'Play '+noun:'Pause '+noun);
      toggle.querySelector('span').textContent=paused?'▶':'Ⅱ';
    }
  }
  // Briefly show touch/click feedback without announcing decorative content.
  function pulse(icon){
    if(feedback){
      feedback.textContent=icon;
      feedback.classList.add('is-visible');
      setTimeout(function(){feedback.classList.remove('is-visible')},520);
    }
  }
  // Rebuild navigation dots whenever a gallery category changes its slide set.
  function renderDots(){
    if(!dotBox)return;
    dotBox.innerHTML='';
    slides.forEach(function(_,i){
      var b=document.createElement('button');
      b.type='button';
      b.className='slider-dot';
      b.setAttribute('aria-label',labelFn(i));
      b.innerHTML='<span></span>';
      b.addEventListener('click',function(){paused=true;go(i,true);updateToggle();});
      dotBox.appendChild(b);
    });
  }

  /*
   * Keep the currently visible slide in place until the requested image has
   * loaded and decoded. Switching classes first can briefly expose an empty
   * image box, then make the decoded pixels appear to jump into position.
   */
  function prepareSlide(slide){
    var image=slide&&slide.querySelector('img');
    if(!image)return Promise.resolve();
    image.loading='eager';
    if(image.complete){
      if(!image.naturalWidth)return Promise.resolve();
      return image.decode?image.decode().catch(function(){}):Promise.resolve();
    }
    return new Promise(function(resolve){
      function ready(){image.removeEventListener('load',ready);image.removeEventListener('error',ready);resolve();}
      image.addEventListener('load',ready,{once:true});
      image.addEventListener('error',ready,{once:true});
    }).then(function(){return image.decode?image.decode().catch(function(){}):undefined;});
  }
  // Only the newest async image request may activate a slide. The token avoids
  // an older slow decode overriding a more recent manual selection.
  function activate(target,token){
    if(token!==activationToken||!slides[target])return;
    idx=target;
    all.forEach(function(s){s.classList.remove('is-active');s.setAttribute('aria-hidden','true')});
    slides[idx].classList.add('is-active');
    slides[idx].setAttribute('aria-hidden','false');
    [].slice.call(dotBox?dotBox.children:[]).forEach(function(d,i){d.setAttribute('aria-current',String(i===idx))});
  }
  // Wrap the requested index and wait until its image is ready before swapping.
  // The modulo (%) calculation turns an index after the last slide back into 0,
  // and an index before 0 back into the final slide.
  function go(n,manual){
    if(!slides.length)return;
    var target=(n+slides.length)%slides.length;
    var token=++activationToken;
    if(manual)stop();
    prepareSlide(slides[target]).then(function(){activate(target,token)});
  }
  // Automatic playback stops during interaction and restarts only when allowed.
  function stop(){clearInterval(timer);timer=null;}
  function start(){stop();if(!paused&&!reduced&&slides.length>1)timer=setInterval(function(){go(idx+1,false)},interval||8500);}
  function togglePaused(){paused=!paused;updateToggle();pulse(paused?'Ⅱ':'▶');start();}

  // Mouse, keyboard, touch and pointer interactions all share the same state.
  root.addEventListener('mouseenter',function(){stop();});
  root.addEventListener('focusin',function(){stop();});
  root.addEventListener('mouseleave',start);
  root.addEventListener('touchstart',function(e){sx=e.touches[0].clientX;sy=e.touches[0].clientY},{passive:true});
  root.addEventListener('touchend',function(e){var dx=e.changedTouches[0].clientX-sx;if(Math.abs(dx)>40){paused=true;go(idx+(dx<0?1:-1),true);updateToggle();}},{passive:true});
  root.addEventListener('pointerdown',function(e){if(e.target.closest('button'))return;dragging=true;sx=e.clientX;sy=e.clientY;root.setPointerCapture&&root.setPointerCapture(e.pointerId)});
  root.addEventListener('pointerup',function(e){
    if(!dragging)return;
    dragging=false;
    var dx=e.clientX-sx,dy=e.clientY-sy;
    if(Math.abs(dx)>50){paused=true;go(idx+(dx<0?1:-1),true);updateToggle();}
    else if(Math.abs(dx)<8&&Math.abs(dy)<8&&root.classList.contains('showcase'))togglePaused();
  });
  if(toggle)toggle.addEventListener('click',togglePaused);

  /* Start fetching every carousel image while the first slide is visible. */
  all.forEach(prepareSlide);
  updateToggle();
  return{setSlides:function(next){slides=next;idx=0;renderDots();go(0,false);start();}};
}

// Every testimonial stage uses the same slider with an eight-second interval.
document.querySelectorAll('.testimonial-stage').forEach(function(stage){var slider=makeSlider(stage,'.testimonial-slide','.testimonial-dots',function(i){return 'Show testimonial '+(i+1);},8000);slider.setSlides([].slice.call(stage.querySelectorAll('.testimonial-slide')));});
// Gallery images remain completely static; only the active slide cross-fades.
// This final argument is the automatic slide-change interval in milliseconds.
document.querySelectorAll('.showcase').forEach(function(showcase){var section=showcase.closest('.showcase-section'), tabs=[].slice.call(section.querySelectorAll('[data-gallery-tab]')), all=[].slice.call(showcase.querySelectorAll('.showcase-slide')), activeCat='experience', slider=makeSlider(showcase,'.showcase-slide','.showcase-indicators',function(i){return 'Show '+activeCat+' image '+(i+1);},9000); function select(cat){activeCat=cat;tabs.forEach(function(t){t.setAttribute('aria-selected',String(t.dataset.galleryTab===cat))});slider.setSlides(all.filter(function(s){return s.dataset.category===cat}));} tabs.forEach(function(t,i){t.addEventListener('click',function(){select(t.dataset.galleryTab)});t.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();var n=(i+(e.key==='ArrowRight'?1:-1)+tabs.length)%tabs.length;tabs[n].focus();tabs[n].click();}})});select(activeCat);});

// ================================================================
// Package selection and decision panel
// ================================================================

// On small screens one package tab/panel is shown at a time because two wide
// cards would be cramped. Desktop keeps both visible for direct comparison while
// retaining the same accessible tab controls and keyboard arrow navigation.
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

// Each packages-decision section owns its expansion, content and form state.
document.querySelectorAll('.packages-decision').forEach(initPackagesDecision);

// Coordinate the Reserve, Ask and Common questions modes. currentMode is the
// single source of truth for which content is open. Only enquiry modes enable
// form controls, preventing fields hidden in other modes from being submitted.
function initPackagesDecision(section){
  var currentMode='none';
  var controls=[].slice.call(section.querySelectorAll('[data-decision-mode]'));
  var expansion=section.querySelector('[data-decision-expansion]');
  var copies=[].slice.call(section.querySelectorAll('[data-decision-copy]'));
  var contact=section.querySelector('[data-decision-contact]');
  var closeTimer=null;
  var closeTransitionHandler=null;
  var scrollCorrectionTimer=null;
  var scrollTransitionHandler=null;

  // Read the current mobile tab selection for pre-filling booking enquiries.
  function currentPackage(){
    var selected=document.querySelector('.package-tab[aria-selected="true"]');
    return selected?selected.dataset.packageTab:'unsure';
  }

  // Reveal only the copy and contact area required by the selected mode.
  function renderDecisionContent(mode){
    copies.forEach(function(copy){copy.hidden=copy.dataset.decisionCopy!==mode;});
    if(contact)contact.hidden=!(mode==='booking'||mode==='question');
  }

  // Disabled form controls are excluded from FormData and browser submission.
  function setContactContext(mode){
    if(!contact)return;
    var form=contact.querySelector('form');
    if(form){
      [].slice.call(form.elements).forEach(function(control){control.disabled=!(mode==='booking'||mode==='question');});
    }
    if(!(mode==='booking'||mode==='question'))return;
    if(form&&form.setContactIntent){
      form.setContactIntent(mode==='booking'?'booking':'party_question',mode==='booking'?currentPackage():'unsure');
    }
  }

  // Synchronise visual active state with each control's aria-expanded value.
  function syncControls(mode){
    controls.forEach(function(control){
      var active=control.dataset.decisionMode===mode;
      control.setAttribute('aria-expanded',String(active));
      control.classList.toggle('is-active',active);
    });
  }

  // Choose the useful part of the expanded panel to centre in the viewport.
  function getDecisionScrollTarget(mode){
    if(mode==='booking'||mode==='question')return section.querySelector('[data-decision-contact] .contact-form-shell');
    if(mode==='questions')return section.querySelector('.package-faq-list');
    return expansion;
  }

  // Use two animation frames so the browser first applies the new content, then
  // calculates its final size. Measuring immediately would use the old height.
  function scrollDecisionContentIntoView(mode, correctionOnly){
    requestAnimationFrame(function(){requestAnimationFrame(function(){
      if(currentMode!==mode)return;
      var target=getDecisionScrollTarget(mode);
      if(!target)return;
      var header=document.querySelector('.site-header');
      var headerRect=header?header.getBoundingClientRect():null;
      var headerHeight=headerRect&&headerRect.bottom>0?Math.min(headerRect.height,headerRect.bottom):0;
      var rect=target.getBoundingClientRect();
      var usableHeight=window.innerHeight-headerHeight;
      var usableCentre=headerHeight+(usableHeight/2);
      var difference=(rect.top+(rect.height/2))-usableCentre;
      if(correctionOnly&&Math.abs(difference)<=14)return;
      var targetScroll;
      if(mode==='questions'&&rect.height>usableHeight){targetScroll=window.scrollY+rect.top-headerHeight-24;}
      else{targetScroll=window.scrollY+rect.top+(rect.height/2)-usableCentre;}
      window.scrollTo({top:Math.max(0,targetScroll),behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});
    });});
  }

  // Remove pending transition/timer callbacks before changing mode again.
  function cancelScrollCorrection(){
    if(scrollCorrectionTimer!==null){window.clearTimeout(scrollCorrectionTimer);scrollCorrectionTimer=null;}
    if(scrollTransitionHandler){expansion.removeEventListener('transitionend',scrollTransitionHandler);scrollTransitionHandler=null;}
  }

  // Correct the scroll position when the height transition completes, with a
  // timer fallback for browsers that do not emit transitionend as expected.
  function scheduleScrollCorrection(mode){
    function correct(){cancelScrollCorrection();scrollDecisionContentIntoView(mode,true);}
    scrollTransitionHandler=function(event){if(event.target===expansion&&event.propertyName==='grid-template-rows')correct();};
    expansion.addEventListener('transitionend',scrollTransitionHandler);
    scrollCorrectionTimer=window.setTimeout(correct,340);
  }

  // Prevent an earlier close animation from hiding newly opened content.
  function cancelCloseCleanup(){
    if(closeTimer!==null){window.clearTimeout(closeTimer);closeTimer=null;}
    if(closeTransitionHandler){expansion.removeEventListener('transitionend',closeTransitionHandler);closeTransitionHandler=null;}
  }

  // Hide content only after its closing animation has finished.
  function finishClose(){
    if(currentMode!=='none')return;
    cancelCloseCleanup();
    renderDecisionContent('none');
    setContactContext('none');
    expansion.hidden=true;
  }

  // Clicking the active mode closes it; clicking another mode swaps content.
  function setDecisionMode(requestedMode){
    var nextMode=currentMode===requestedMode?'none':requestedMode;
    var wasClosed=currentMode==='none';
    cancelCloseCleanup();
    cancelScrollCorrection();
    currentMode=nextMode;
    section.dataset.activeMode=nextMode;
    syncControls(nextMode);
    if(nextMode==='none'){
      expansion.classList.remove('is-open');
      if(matchMedia('(prefers-reduced-motion: reduce)').matches){finishClose();return;}
      closeTransitionHandler=function(event){if(event.target===expansion&&event.propertyName==='grid-template-rows')finishClose();};
      expansion.addEventListener('transitionend',closeTransitionHandler);
      closeTimer=window.setTimeout(finishClose,340);
      return;
    }
    renderDecisionContent(nextMode);
    setContactContext(nextMode);
    expansion.hidden=false;
    if(wasClosed){
      requestAnimationFrame(function(){expansion.classList.add('is-open');scrollDecisionContentIntoView(nextMode,false);scheduleScrollCorrection(nextMode);});
    }else{
      expansion.classList.add('is-open');
      scrollDecisionContentIntoView(nextMode,false);
      scheduleScrollCorrection(nextMode);
    }
  }

  section.addEventListener('click',function(event){
    var control=event.target.closest('[data-decision-mode]');
    if(!control||!section.contains(control))return;
    setDecisionMode(control.dataset.decisionMode);
  });
  syncControls('none');
  renderDecisionContent('none');
  setContactContext('none');
  expansion.hidden=true;
}

// Compact package FAQs also allow only one answer to remain open.
document.querySelectorAll('.package-faq-item button').forEach(function(b){b.addEventListener('click',function(){var item=b.closest('.package-faq-item'),open=b.getAttribute('aria-expanded')!=='true';document.querySelectorAll('.package-faq-item').forEach(function(x){x.classList.remove('is-open');var xb=x.querySelector('button');if(xb)xb.setAttribute('aria-expanded','false')});item.classList.toggle('is-open',open);b.setAttribute('aria-expanded',String(open));});});

// ================================================================
// Legal-page accordions
// ================================================================

// Keep one legal section open at a time and mirror state through aria-expanded.
function initLegalAccordion(list){
  var items=[].slice.call(list.querySelectorAll('.legal-accordion__item'));
  items.forEach(function(item){
    var button=item.querySelector('button');
    if(!button)return;
    button.addEventListener('click',function(){
      var shouldOpen=button.getAttribute('aria-expanded')!=='true';
      items.forEach(function(otherItem){
        var otherButton=otherItem.querySelector('button');
        var active=otherItem===item&&shouldOpen;
        otherItem.classList.toggle('is-open',active);
        if(otherButton)otherButton.setAttribute('aria-expanded',String(active));
      });
    });
  });
}
document.querySelectorAll('[data-legal-accordion]').forEach(initLegalAccordion);

// ================================================================
// Contact forms and Web3Forms submission
// ================================================================

// Initialise one standalone or inline form. "component" is the outer wrapper;
// the first lines find the form, status message and success panel inside it.
// The same component supports booking, general party, collaboration, venue,
// media and other enquiries without duplicating form-handling code.
function initContact(component){
  var form=component.querySelector('[data-contact-form]'), success=component.querySelector('[data-contact-success]'), status=component.querySelector('[data-contact-status]'); if(!form)return;
  form.noValidate=true;
  var intents=['booking','party_question','collaboration','venue_partnership','media','other'], packages=['onyx','jade','unsure'];
  var intent=form.elements.intent, pkg=form.elements.package, subject=form.elements.subject, fields=[].slice.call(form.querySelectorAll('.field--event')), disclosure=form.querySelector('.contact-disclosure'), eventToggle=form.querySelector('[data-event-toggle]'), eventDetailsRevealed=false, onlineEnabled=component.dataset.onlineEnabled==='true';
  // Translate legacy query-string values and reject unsupported prefill values.
  function supportedIntent(value){if(value==='availability')return 'booking'; if(value==='question')return 'party_question'; return intents.indexOf(value)>=0?value:'party_question';}
  function supportedPackage(value){return packages.indexOf(value)>=0?value:'unsure';}

  // URL values override component defaults. For example, the query string in
  // /contact/?intent=booking opens the same page with Booking already selected.
  var params=new URLSearchParams(location.search), resetIntent=supportedIntent(params.get('intent')||component.dataset.defaultIntent), resetPackage=supportedPackage(params.get('package')||component.dataset.defaultPackage);

  // Web3Forms receives a readable email subject based on the current context.
  function subjectForContext(){var map={booking:'New Party.LAN booking enquiry',party_question:'New Party.LAN party question',collaboration:'New Party.LAN collaboration enquiry',venue_partnership:'New Party.LAN venue partnership enquiry',media:'New Party.LAN press or media enquiry',other:'New Party.LAN general enquiry'};var base=map[intent.value]||map.party_question; if(intent.value==='booking'&&(pkg.value==='onyx'||pkg.value==='jade'))base+=' — '+pkg.value.toUpperCase(); return base;}

  // Hidden event controls are disabled as well as visually hidden, so they are
  // omitted from validation and the submitted FormData payload.
  function setEventFieldsVisible(show){fields.forEach(function(field){field.hidden=!show; field.setAttribute('aria-hidden',show?'false':'true'); [].slice.call(field.querySelectorAll('input, select, textarea')).forEach(function(control){control.disabled=!show;});});}

  // Booking always shows event fields. A general party question shows them only
  // after the visitor explicitly asks to add event details.
  function syncContactContext(){intent.value=supportedIntent(intent.value); var showEvents=intent.value==='booking'||eventDetailsRevealed; setEventFieldsVisible(showEvents); if(disclosure)disclosure.hidden=intent.value!=='party_question'||eventDetailsRevealed; if(eventToggle){eventToggle.setAttribute('aria-expanded',String(showEvents&&intent.value==='party_question'));syncRolloutLabel(eventToggle);} if(subject)subject.value=subjectForContext();}

  // Error states always provide the public email as a dependable fallback.
  function appendEmailFallback(message){status.textContent=''; if(message)status.appendChild(document.createTextNode(message+' ')); var link=document.createElement('a'); link.href='mailto:hello@partylan.co.uk'; link.textContent='Email Party.LAN directly.'; status.appendChild(link);}
  intent.value=resetIntent; pkg.value=resetPackage;
  eventDetailsRevealed=intent.value==='booking'; syncContactContext();
  if(!onlineEnabled){status.className='contact-status is-error'; appendEmailFallback('Online enquiry submissions are not configured.');}
  intent.addEventListener('change',function(){eventDetailsRevealed=false; syncContactContext();});
  if(pkg)pkg.addEventListener('change',syncContactContext);
  if(eventToggle)eventToggle.addEventListener('click',function(){eventDetailsRevealed=true; syncContactContext();});

  // Associate each validation message with its field and accessible invalid state.
  function err(name,msg){var el=form.elements[name], box=form.querySelector('[data-error-for="'+name+'"]'); if(el)el.setAttribute('aria-invalid',msg?'true':'false'); if(box)box.textContent=msg||''; return !!msg;}

  // Apply shared rules first, then booking-only date, venue, player and package
  // rules. Focus moves to the first invalid control to aid keyboard users.
  function validate(){syncContactContext(); var bad=[], data=Object.fromEntries(new FormData(form).entries()), currentIntent=supportedIntent(intent.value); ['intent','package','name','email','phone','location','players','message','privacy','preferred_date','alternative_date'].forEach(function(n){err(n,'')});
    if(intents.indexOf(currentIntent)<0)bad.push(['intent','Choose a supported enquiry type.']);
    if(!data.name||data.name.trim().length<2||data.name.length>80)bad.push(['name','Enter your name.']);
    if(!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email||''))bad.push(['email','Enter a valid email address.']);
    var msg=(data.message||'').trim(); if(msg && (msg.length<10||msg.length>2000))bad.push(['message','Use 10 to 2000 characters, or leave it blank when booking details explain enough.']);
    if(currentIntent!=='booking'&&!msg)bad.push(['message','Enter a message.']);
    if(currentIntent==='booking'){
      if(data.phone && (data.phone.length<7||data.phone.length>30))bad.push(['phone','Enter a valid phone number, or leave it blank.']);
      if(data.location && data.location.length<2)bad.push(['location','Enter a town or postcode, or leave it blank.']);
      if(packages.indexOf(data.package)<0)bad.push(['package','Choose a supported package option.']);
      if(data.players && (+data.players<1||+data.players>40))bad.push(['players','Enter a player count between 1 and 40.']);
      ['preferred_date','alternative_date'].forEach(function(n){if(data[n] && !/^\d{4}-\d{2}-\d{2}$/.test(data[n]))bad.push([n,'Enter a valid date.']);});
      if(!msg&&!data.preferred_date)bad.push(['preferred_date','Add a preferred date or explain what you need in the message.']);
      if(!msg&&!data.location)bad.push(['location','Add a town/postcode or explain what you need in the message.']);
    }
    if(!form.elements.privacy.checked)bad.push(['privacy','Please acknowledge the privacy notice.']);
    bad.forEach(function(x){err(x[0],x[1])}); if(bad[0]&&form.elements[bad[0][0]])form.elements[bad[0][0]].focus({preventScroll:false}); return !bad.length;
  }

  // FormData gathers the enabled named fields exactly as a normal browser form
  // would. fetch() sends them to Web3Forms without reloading the page. Both the
  // HTTP status and Web3Forms success flag must confirm success; any rejection
  // is handled through the visible email fallback.
  function submitWeb3Form(targetForm){
    syncContactContext();
    return fetch(targetForm.action,{method:'POST',body:new FormData(targetForm),headers:{'Accept':'application/json'}}).then(function(response){return response.json().then(function(payload){if(response.ok===true&&payload&&payload.success===true)return payload; throw {status:response.status,json:payload};});});
  }

  // Restore the initial URL/component context after a successful submission.
  function resetToInitialContext(){intent.value=resetIntent; pkg.value=resetPackage; eventDetailsRevealed=intent.value==='booking'; syncContactContext();}

  // Lock the submit button during the request, then show either the success
  // panel or a retry/email error without navigating away from the static page.
  form.addEventListener('submit',function(e){e.preventDefault(); if(!onlineEnabled){status.className='contact-status is-error'; appendEmailFallback('Online enquiry submissions are not configured.'); status.focus&&status.focus(); return;} status.className='contact-status is-loading'; status.textContent=''; if(!validate())return; var btn=form.querySelector('[type=submit]'); if(btn.disabled)return; var originalLabel=btn.textContent; btn.disabled=true; form.setAttribute('aria-busy','true'); btn.textContent='Sending enquiry…'; status.textContent='Sending enquiry…';
    submitWeb3Form(form).then(function(){form.reset(); resetToInitialContext(); status.className='contact-status'; status.textContent=''; form.hidden=true; success.hidden=false; success.focus&&success.focus();}).catch(function(ex){console.error('Web3Forms contact submission failed',ex); status.className='contact-status is-error'; appendEmailFallback('We couldn’t send your enquiry. Please try again, or'); status.focus&&status.focus();}).finally(function(){btn.disabled=false; form.removeAttribute('aria-busy'); btn.textContent=originalLabel||btn.dataset.submitLabel||'Send enquiry';});
  });

  // "Send another" clears success/error state but preserves the original route
  // context. The two methods below let the packages decision panel drive a form.
  var again=component.querySelector('[data-send-another]'); if(again)again.addEventListener('click',function(){success.hidden=true; form.hidden=false; status.className=onlineEnabled?'contact-status':'contact-status is-error'; status.textContent=''; if(!onlineEnabled)appendEmailFallback('Online enquiry submissions are not configured.'); form.querySelectorAll('[aria-invalid="true"]').forEach(function(el){el.setAttribute('aria-invalid','false')}); form.querySelectorAll('[data-error-for]').forEach(function(el){el.textContent=''}); resetToInitialContext(); form.focus();});
  form.syncContactContext=syncContactContext;
  form.setContactIntent=function(nextIntent,nextPackage){resetIntent=supportedIntent(nextIntent); resetPackage=supportedPackage(nextPackage); intent.value=resetIntent; pkg.value=resetPackage; eventDetailsRevealed=intent.value==='booking'; syncContactContext();};
}
document.querySelectorAll('[data-contact-component]').forEach(initContact);

// ================================================================
// Decorative atmosphere and progressive reveal
// ================================================================

// Move the oversized middle background layer at half scroll speed on desktop.
// This creates the subtle parallax effect. The offset is clamped to keep the
// decorative layer covering the viewport at the top and bottom of the page.
var atmosphere=document.querySelector('.site-background__middle');
if(atmosphere){
  var reduceBg=matchMedia('(prefers-reduced-motion: reduce)').matches;
  var compactViewport=matchMedia('(max-width: 920px)').matches;
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
  // The large parallax layer is decorative. Do not create its scroll and
  // resize listeners on phones, where it costs battery and can drop frames.
  if(!reduceBg&&!compactViewport){
    measureAtmosphere();
    window.addEventListener('resize',measureAtmosphere,{passive:true});
    window.addEventListener('scroll',function(){bgY=window.pageYOffset||document.documentElement.scrollTop||0;if(!bgTick){bgTick=true;requestAnimationFrame(updateAtmosphere);}},{passive:true});
    updateAtmosphere();
  }else{
    atmosphere.style.transform='none';
  }
}

// On phones, content is visible immediately instead of animating into view.
// This avoids extra transform/compositing work during scrolling.
var allowReveal=!matchMedia('(max-width: 920px)').matches&&!matchMedia('(prefers-reduced-motion: reduce)').matches;

// IntersectionObserver reports when an element enters the viewport. Observe each
// .reveal element once, then stop observing after it appears. Browsers without
// support—and visitors requesting reduced motion—receive the visible state at once.
var io=('IntersectionObserver'in window&&allowReveal)?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('is-visible');io.unobserve(e.target)}})},{threshold:.12}):null;document.querySelectorAll('.reveal').forEach(function(el){io?io.observe(el):el.classList.add('is-visible')});
}());
