# Party.LAN Homepage Foundation Prototype

## Architecture summary

The homepage is implemented as a dependency-free static single-page application. Presentation lives in `src/main.js`, styling and theme tokens live in `src/styles.css`, and editable copy/content arrays live in `src/content.js`.

## Data-driven content structure

The `siteContent` export drives navigation, hero copy, statistics, experiences, schedule rows, tournament cards, section coverage, and owner-confirmation placeholders. This keeps prototype content centralized for review and future CMS migration.

## Bright and dark theme implementation

The theme toggle swaps a `data-theme` attribute between `bright` and `dark`. CSS custom properties define shared color roles for backgrounds, surfaces, text, muted copy, primary accents, secondary accents, and highlights.

## Sections completed

- Sticky navigation with theme toggle
- Hero with calls to action and quick stats
- Experience card grid
- Schedule timeline
- Tournament status cards
- Completed-section coverage map
- Sponsor placeholder wall
- Owner-confirmation placeholder list
- FAQ/final call to action

## Known placeholders

- Event date, venue, and ticket URL
- Tournament titles, rulesets, and prize language
- Sponsor logos, tiers, and legal copy
- Organizer-approved policies
- Discord, volunteer, streaming, and newsletter links

## Content still requiring owner confirmation

Owners should confirm all event logistics, partner commitments, tournament details, policy copy, and external URLs before public launch.
