import { siteContent } from './content.js';
import './styles.css';

const icons = ['🎮', '🏆', '👥', '🕹️', '✨', '📅'];
let theme = 'bright';

function render() {
  const root = document.getElementById('root');
  root.innerHTML = `
    <main class="app" data-theme="${theme}">
      <nav class="nav" aria-label="Primary navigation">
        <a class="brand" href="#top" aria-label="Party.LAN home"><span class="brand-mark">PL</span><span>${siteContent.brand.name}</span></a>
        <div class="nav-links">${siteContent.navigation.map((item) => `<a href="#${item.toLowerCase()}">${item}</a>`).join('')}</div>
        <button class="theme-toggle" type="button" data-theme-toggle>${theme === 'bright' ? '🌙 Dark' : '☀️ Bright'} mode</button>
      </nav>
      <section class="hero" id="top">
        <div class="hero-copy">
          <p class="eyebrow">${siteContent.hero.eyebrow}</p>
          <h1>${siteContent.hero.headline}</h1>
          <p class="hero-body">${siteContent.hero.body}</p>
          <div class="actions">${siteContent.hero.actions.map((action) => `<a class="button ${action.variant ?? 'primary'}" href="${action.href}">${action.label}</a>`).join('')}</div>
        </div>
        <aside class="hero-panel" aria-label="Party.LAN quick stats">${siteContent.hero.stats.map((stat) => `<div class="stat"><strong>${stat.value}</strong><span>${stat.label}</span></div>`).join('')}</aside>
      </section>
      <section class="section" id="experience">
        <p class="eyebrow">Experience</p><h2>Built as reusable content blocks.</h2>
        <div class="card-grid">${siteContent.experiences.map((experience, index) => `<article class="card"><span class="icon" aria-hidden="true">${icons[index % icons.length]}</span><h3>${experience}</h3><p>Prototype copy is centralized in <code>siteContent</code> so owners can update labels without touching layout code.</p></article>`).join('')}</div>
      </section>
      <section class="section split" id="schedule"><div><p class="eyebrow">Schedule</p><h2>Event flow ready for confirmed dates.</h2><p>The homepage foundation separates schedule data from presentation and highlights known owner-confirmation needs.</p></div><ol class="timeline">${siteContent.schedule.map((item) => `<li><span>${item.time}</span><strong>${item.title}</strong></li>`).join('')}</ol></section>
      <section class="section" id="tournaments"><p class="eyebrow">Tournaments</p><h2>Bracket cards with explicit status notes.</h2><div class="tournament-grid">${siteContent.tournaments.map((tournament) => `<article class="tournament"><span class="icon" aria-hidden="true">🏆</span><h3>${tournament.game}</h3><p>${tournament.format}</p><span>${tournament.status}</span></article>`).join('')}</div></section>
      <section class="section" id="sections"><p class="eyebrow">Sections completed</p><h2>Homepage coverage map.</h2><div class="section-list">${siteContent.sections.map((section) => `<article><h3>${section.title}</h3><p>${section.description}</p></article>`).join('')}</div></section>
      <section class="section split" id="sponsors"><div><p class="eyebrow">Sponsors</p><h2>Partner-ready placeholder system.</h2><p>Sponsor modules are intentionally neutral until approved logos, tier names, and legal language are supplied.</p></div><div class="sponsor-wall" aria-label="Sponsor placeholders">${['Presenting', 'Network', 'Prize', 'Community'].map((tier) => `<span>${tier} partner</span>`).join('')}</div></section>
      <section class="section" id="placeholders"><p class="eyebrow">Owner confirmation</p><h2>Known placeholders before launch.</h2><ul class="placeholder-list">${siteContent.placeholders.map((item) => `<li>${item}</li>`).join('')}</ul></section>
      <section class="section faq" id="faq"><p class="eyebrow">FAQ</p><h2>What is ready now?</h2><p>${siteContent.brand.description}</p><a class="button primary" href="mailto:hello@partylan.example">Confirm launch content</a></section>
    </main>`;
  root.querySelector('[data-theme-toggle]').addEventListener('click', () => {
    theme = theme === 'bright' ? 'dark' : 'bright';
    render();
  });
}

render();
