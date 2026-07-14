# Party.LAN Website

A small static homepage prototype for Party.LAN, a hosted gaming-party service. The first build establishes visual identity, bright/dark themes, reusable homepage components, and a content model that can grow into future Pricing, About, FAQ and Contact pages.

## Structure

```text
build.py                 # standard-library static build and validation
content/site.json        # editable general homepage content
content/packages.json    # editable package content
content/gallery.csv      # editable gallery entries
content/testimonials.csv # future real testimonials only
templates/index.html     # semantic homepage template
static/                  # CSS, JavaScript and local assets
dist/                    # generated static site
```

## Content and presentation

Editable business copy lives in `content/`. The template keeps the document structure, accessibility attributes, theme controls and component classes. The build script escapes imported text before writing `dist/index.html`, so JSON and CSV content should be treated as plain text rather than HTML.

## Editing JSON

Use stable keys in `content/site.json` for metadata, navigation, hero content, reassurance items, section headings, how-it-works steps, the final call to action and footer placeholders. Use `content/packages.json` for package names, prices, durations, capacities, features and package actions.

## Editing CSV

`content/gallery.csv` supports `id,image_light,image_dark,alt,caption,href,visible,display_order`. Set `visible=false` for draft rows. Visible image paths must point to local assets and include useful alternative text.

`content/testimonials.csv` must only contain real, permitted customer testimonials. It starts with only a header, and the generated testimonial section is hidden until visible entries exist.

Never store live customer data, private contact details or sensitive booking information in public JSON or CSV files. These files are intended for public website copy only.

## Build and preview

```bash
python build.py
python -m http.server 8000 --directory dist
```

Then open `http://localhost:8000`.

## Render static hosting

Suggested Render configuration:

- Build command: `python build.py`
- Publish directory: `dist`

The browser receives static HTML, CSS, JavaScript and local assets. There are no runtime dependencies, framework bundles, live CMS calls or database connections.

## Future Google Sheets workflow

A future owner-approved synchronisation process could export curated Google Sheets rows into the local JSON and CSV files before `python build.py` runs. The live site should still publish generated static files from `dist/`, not fetch essential homepage text from Google Sheets in the visitor browser.

## Owner confirmation still required

Domain-dependent metadata, contact details, service area, real photography, customer testimonials and any trust or safety claims must be confirmed by the owner before launch.
