(function(){
  'use strict';
  document.documentElement.classList.add('js');
  var storageKey='partyLanTheme';
  var toggle=document.querySelector('.theme-toggle');
  var menuToggle=document.querySelector('.menu-toggle');
  var menu=document.getElementById('site-menu');
  function preferred(){try{return localStorage.getItem(storageKey)||(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light');}catch(e){return 'light';}}
  function setImages(theme){document.querySelectorAll('img.theme-image').forEach(function(img){var next=img.dataset[theme+'Src']; if(next && img.getAttribute('src')!==next){img.setAttribute('src',next);}});}
  function apply(theme,save){document.documentElement.dataset.theme=theme;setImages(theme);if(toggle){var dark=theme==='dark';toggle.setAttribute('aria-pressed',String(dark));toggle.textContent=dark?'Use bright theme':'Use dark theme';toggle.setAttribute('aria-label',dark?'Switch to bright theme':'Switch to dark theme');}if(save){try{localStorage.setItem(storageKey,theme);}catch(e){}}}
  apply(document.documentElement.dataset.theme || preferred(), false);
  if(toggle){toggle.addEventListener('click',function(){apply(document.documentElement.dataset.theme==='dark'?'light':'dark',true);});}
  if(menuToggle && menu){menuToggle.addEventListener('click',function(){var open=menu.classList.toggle('is-open');menuToggle.setAttribute('aria-expanded',String(open));});menu.addEventListener('click',function(e){if(e.target.tagName==='A'){menu.classList.remove('is-open');menuToggle.setAttribute('aria-expanded','false');}});}
  if('IntersectionObserver' in window && !matchMedia('(prefers-reduced-motion: reduce)').matches){var io=new IntersectionObserver(function(entries){entries.forEach(function(entry){if(entry.isIntersecting){entry.target.classList.add('is-visible');io.unobserve(entry.target);}});},{threshold:.14});document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});}else{document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('is-visible');});}
  try{matchMedia('(prefers-color-scheme: dark)').addEventListener('change',function(e){if(!localStorage.getItem(storageKey)){apply(e.matches?'dark':'light',false);}});}catch(e){}
}());
