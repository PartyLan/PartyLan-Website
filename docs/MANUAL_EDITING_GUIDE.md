# Party.LAN owner maintenance and manual editing guide

This is the main owner-facing guide for changing the Party.LAN website. It explains how to request or make a change, find the correct source file, preview the result, maintain SEO, diagnose common problems, test mobile layouts, and submit a safe pull request. It covers simple content edits as well as visual and structural code changes.

## Guide contents

- [Quick start for any future change](#quick-start-for-any-future-change)
- [The rule that prevents lost work](#the-one-rule-that-prevents-lost-work)
- [Editing setup and first-time setup](#recommended-editing-setup)
- [Build and preview loop](#build-and-preview-loop)
- [Source file map](#source-file-map)
- [Writing a future change request](#how-to-write-a-future-change-request)
- [Visual and CSS changes](#how-to-make-a-visual-adjustment-safely)
- [Content editing](#editing-content)
- [SEO and search-preview maintenance](#seo-and-search-preview-maintenance)
- [Images and mobile performance](#replacing-or-adding-images)
- [Troubleshooting](#troubleshooting-common-problems)
- [Validation, Git and pull requests](#validation-checklist-before-a-pull-request)

## Quick start for any future change

Use this order every time:

1. Decide whether the request is content, imagery, styling, behaviour, SEO, legal wording, or page structure.
2. Create a new Git branch from the latest `main` unless the work belongs to an existing open pull request.
3. Edit the source of truth listed in the file map below. Never make the only copy of a change in `dist/`.
4. Run `python build.py`.
5. Run `python -m unittest discover -s tests -v`.
6. Preview the affected page at `http://127.0.0.1:8010/` and test the required widths and themes.
7. Review the Git diff so unrelated files, private data, temporary files, and secrets are not included.
8. Commit, push, open a pull request, and test its deployment preview before merging.

### Choose the correct change type

| Requested change | Usual source | Risk level | Minimum verification |
| --- | --- | --- | --- |
| Edit public wording, heading, CTA, FAQ, package or add-on | `content/*.json` or `content/*.csv` | Low | Build, tests, affected page |
| Replace or add an approved photograph | `content/images/` plus its JSON/CSV reference | Low–medium | Build, image loading, desktop/mobile crop |
| Change colour, spacing, size, alignment or responsive layout | `static/css/styles.css` | Medium | Build, light/dark, hover/focus, multiple widths |
| Change gallery timing, tabs, forms or another interaction | `static/js/main.js` | Medium–high | Build, tests, mouse, keyboard and touch |
| Change page/component structure | `build.py` | High | Build, full test suite, all public pages |
| Change titles, descriptions, canonicals, sharing image or business schema | `content/homepage.json` `meta` block; sometimes the `SEO:` section in `build.py` | High | SEO tests, page source, sitemap and robots |
| Change Terms or Privacy wording | `content/legal/*.json` | High | Owner/legal review, build, affected legal page |
| Add, remove or rename a public page | `build.py`, navigation content, `meta.pages`, tests and generated output | High | Full site, internal links, canonical, sitemap |

“Risk level” describes how widely a mistake can affect the site, not how difficult the edit looks. A one-line shared renderer change can affect every page.

## The one rule that prevents lost work

`dist/` is generated output. Never make the only copy of a change inside `dist/` because the next `python build.py` run deletes and recreates that folder.

Make changes in the source files first:

- Content and image references: `content/`
- Styling: `static/css/styles.css`
- Browser behaviour: `static/js/main.js`
- Generated page structure and shared components: `build.py`
- Original image files: `content/images/`

Then run `python build.py`. The build copies CSS and JavaScript into `dist/` and generates the HTML pages.

> `templates/index.html` is an older prototype and is not used by the current build. Changing it will not change the live site. Current page markup is rendered by functions in `build.py`.

## Recommended editing setup

The safest primary workflow for this repository is:

1. Use [Visual Studio Code](https://code.visualstudio.com/) to edit the source files and review Git changes.
2. Run the local Python build and preview server from the VS Code terminal.
3. Use [Firefox Responsive Design Mode](https://firefox-source-docs.mozilla.org/devtools-user/responsive_design_mode/) to experiment with spacing, sizes, gradients, colours, and image crops visually.
4. Copy successful values from Firefox's Rules panel back into `static/css/styles.css`.
5. Optionally use [Responsively App](https://responsively.app/) to view several phone widths side by side.

This is a better fit than moving the site into a hosted drag-and-drop builder because the existing content validation, Git history, Render deployment, accessibility markup, and Python generation remain intact.

### Optional visual editor

[Pinegrow Web Editor](https://pinegrow.com/) is the closest visual editor for this type of ordinary HTML/CSS site. It can inspect active CSS rules and show multiple responsive sizes. However, open the generated `dist/` pages for visual experimentation only. Copy final CSS values into `static/css/styles.css` and structural changes into `build.py`, then rebuild. Saving only Pinegrow's edits to `dist/` will lose them on the next build.

## First-time setup

Requirements:

- Git
- Python 3
- A current desktop browser
- VS Code or another plain-text code editor

Clone the repository and enter it:

```bash
git clone https://github.com/PartyLan/PartyLan-Website.git
cd PartyLan-Website
```

For an existing checkout, update `main` without creating a merge commit:

```bash
git switch main
git pull --ff-only
```

Create a branch before editing:

```bash
git switch -c your-name/short-change-description
```

No Node.js or npm install is required. The website build uses Python's standard library.

## Build and preview loop

Run the build from the repository root:

```bash
python build.py
```

Start a local server:

```bash
python -m http.server 8010 --bind 127.0.0.1 --directory dist
```

Open these useful pages:

- Homepage: `http://127.0.0.1:8010/`
- Packages: `http://127.0.0.1:8010/packages/`
- Contact: `http://127.0.0.1:8010/contact/`
- Terms: `http://127.0.0.1:8010/terms/`
- Privacy: `http://127.0.0.1:8010/privacy/`

After a source change:

1. Save the file.
2. Run `python build.py` again.
3. Refresh the browser. Use a hard refresh if CSS appears cached.
4. Check both light and dark themes.
5. Check desktop and phone widths.

The optional Microsoft [Live Preview extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode.live-server) can host simple pages, but this project still needs `python build.py` whenever content or generated markup changes. The explicit Python server command above is the most predictable preview method.

## Source file map

| What you want to change | Source of truth |
| --- | --- |
| Homepage wording, section headings, navigation labels | `content/homepage.json` |
| Package names, descriptions, facts, included items | `content/packages.json` |
| Gallery items, captions, categories and image paths | `content/gallery.csv` |
| Homepage questions and answers | `content/faq.csv` |
| Packages-page questions and answers | `content/packages_faq.csv` |
| Add-ons | `content/addons.csv` |
| Approved testimonials | `content/testimonials.csv` |
| Terms and privacy wording | `content/legal/*.json` |
| Photos and logos | `content/images/` |
| Colours, spacing, layout, crops, responsive rules | `static/css/styles.css` |
| Gallery timing and browser interactions | `static/js/main.js` |
| HTML/component structure for generated pages | `build.py` |
| Generated site to deploy | `dist/` — do not edit directly |

For content-only work, also read `content/CONTENT_GUIDE.md`.

## How to write a future change request

A precise request prevents accidental changes outside the intended area. Screenshots are useful, but always accompany them with a short written description.

Include:

- **Repository and branch:** say whether the work starts from `main` or continues an existing branch/PR.
- **Page and element:** identify the page, visible heading, button label, section name, or CSS selector.
- **Current behaviour:** explain what is wrong now.
- **Desired behaviour:** explain the exact result rather than only saying “fix it” or “make it better.”
- **Responsive scope:** state desktop, mobile, both, or a particular breakpoint/viewport.
- **Theme scope:** state light mode, dark mode, or both.
- **What must remain unchanged:** list nearby content, layout, behaviour, images, or business facts that must be preserved.
- **Maintainability requirement:** mention when a value should be exposed as an easy-to-edit variable or content field.
- **Publishing permission:** state whether the branch may be committed, pushed, and added to a new or existing PR.
- **Acceptance criteria:** list the checks that prove the change is finished.

Copy and complete this template:

```text
Repository: PartyLan/PartyLan-Website
Base branch or existing PR:

Goal:

Page/section:
Current result:
Desired result:

Desktop behaviour:
Mobile behaviour:
Light-mode behaviour:
Dark-mode behaviour:

Must preserve:
Values that should remain easy to edit:

Acceptance criteria:
-
-

Publishing approval:
```

For a visual change, attach a current screenshot and mark the affected area. If possible, include one reference or rough drawing showing the desired spacing, alignment, scale, or colour relationship.

## How to make a visual adjustment safely

Use this repeatable process when a change is easier to judge visually than describe:

1. Build and open the page locally.
2. Right-click the element and choose **Inspect**.
3. In the Rules panel, identify the selector controlling it.
4. Tick rules on and off before changing values. This reveals which effect actually causes the problem.
5. Edit one value at a time in the browser, such as `padding`, `gap`, `width`, `object-position`, `background`, or `border-radius`.
6. Test at 360, 390, 430, 768, 920, 1180, and 1440 CSS pixels.
7. Copy the working declaration into the source stylesheet.
8. Rebuild and retest. Browser DevTools edits disappear on refresh, so they are never the final source.

In Firefox Responsive Design Mode, start with these practical profiles:

- 360 × 800: narrow Android-sized viewport
- 390 × 844: common modern phone viewport
- 430 × 932: large phone viewport
- 768 × 1024: tablet portrait
- 1440 × 900: desktop

Always drag slowly through widths around 920px as well. That is the main mobile/desktop breakpoint and is where layout jumps are most likely.

## CSS organisation and the final override block

`static/css/styles.css` contains historical revision layers. When two selectors have similar specificity, a rule later in the file wins. This is why a visually correct change can appear to do nothing if an older selector is later overridden.

The final section is deliberately named:

```css
/* STATIC MEDIA AND MOBILE PERFORMANCE OVERRIDES */
```

Keep that section at the end of the stylesheet. It is the authoritative guard that:

- disables all hero, gallery, and testimonial pan/zoom/breathing transforms;
- keeps image wrappers at `inset: 0`;
- removes the left-edge mobile hero gradient seam;
- removes expensive phone-sized parallax, blur, oversized shadows, and reveal transforms.

Do not add a new image animation above or below this block. The design decision is that photos remain static. Gallery items may cross-fade when the active slide changes, but an individual photo must not move.

### Long-term cleanup recommendation

Before a large redesign, split the stylesheet into small source files such as `tokens.css`, `header.css`, `hero.css`, `gallery.css`, `packages.css`, `forms.css`, and `mobile.css`, then concatenate them during the build. That removes the need for stacked correction blocks and makes visual adjustments much easier to locate. This should be a separate refactor, not mixed into a small design fix.

## Common visual changes

### Change global colours

Find the later authoritative `:root` token block in `static/css/styles.css`. Light mode uses variables such as:

```css
:root {
  --page-bg: #f7efe5;
  --surface: rgba(255, 250, 242, .86);
  --text: #172238;
  --text-muted: #626a7c;
  --accent-shared: #8667a7;
  --accent-jade: #4d937d;
}
```

Dark-mode overrides are under `html[data-theme="dark"]`. Change both modes and verify readable contrast before committing.

### Change overall page width

The shared shell uses `--container`. Search for its final declaration and adjust the clamp carefully. Major sections inherit it. Test 921–1180px after changing it because the hero has a dedicated intermediate layout in that range.

### Change section spacing

Prefer the existing spacing variables and `clamp()` values. For example:

```css
.showcase-section {
  margin-top: clamp(3rem, 6vw, 6rem);
}
```

`clamp(minimum, fluid value, maximum)` keeps the change responsive. Avoid fixed large pixel margins that work at only one screen width.

### Change only the phone layout

Put the adjustment in the final phone media query:

```css
@media (max-width: 920px) {
  .your-selector {
    /* phone-only value */
  }
}
```

For very small phones, use the existing `430px` breakpoint only when necessary. Fewer breakpoints make the layout easier to maintain.

### Change an image crop without animating it

Keep `object-fit: cover` and adjust `object-position`:

```css
.hero--home .hero__image {
  object-position: 62% 45%;
}
```

- First value: horizontal focus. `0%` is left, `50%` centre, `100%` right.
- Second value: vertical focus. `0%` is top, `50%` centre, `100%` bottom.

Use a separate mobile value if the subject needs a different crop:

```css
@media (max-width: 920px) {
  .hero--home .hero__image {
    object-position: 58% 40%;
  }
}
```

For a particular How it works image, prefer the `image_position` field in `content/homepage.json`. Accepted values are `center`, `top`, `bottom`, `left`, and `right`.

### Adjust the mobile hero panel

The final mobile hero rule intentionally bleeds two pixels beyond the viewport:

```css
.hero--home .hero__picture {
  right: -2px !important;
  left: -2px !important;
  width: auto !important;
}
```

Do not change these back to `left: 0; width: 100%` unless the left and right edges have been checked on a real phone. The two-pixel bleed prevents browser rounding from exposing a sharp seam. Mobile also disables `::before` and uses only `::after` for the bottom fade.

### Adjust the homepage and packages hero fades

The authoritative fade controls are grouped at the end of
`static/css/styles.css` under `HERO IMAGE OPACITY FADES`. Both effects use CSS
alpha masks, so the image itself becomes transparent instead of being covered
with a rectangle in the page background colour.

For the desktop homepage hero, these are the main controls:

```css
--home-hero-media-top: 0px;       /* aligns the photograph with the hero top */
--home-hero-media-side-gap: clamp(1.5rem, 4vw, 5rem);
--home-hero-media-bottom-bleed: clamp(8rem, 12vw, 14rem);
--home-hero-fade-centre-x: 50%;   /* keep the fade centred while resizing */
--home-hero-fade-centre-y: 28%;   /* move the radial fade up or down */
--home-hero-fade-solid: 30%;      /* fully visible inner area */
--home-hero-fade-soft: 58%;       /* partly transparent transition */
```

The media is centred in the hero and keeps the same gap on both sides, so it
does not drift out of the viewport as the window is resized. Reduce
`--home-hero-media-side-gap` for a wider image. Increase
`--home-hero-media-bottom-bleed` to carry the fade farther beneath the
reassurance panel. Lower `--home-hero-fade-centre-x` to shift the strongest
part of the image toward the text. Increase `--home-hero-fade-solid` for more
fully visible image, or decrease it for a softer fade.

The packages hero uses three controls:

```css
--packages-hero-fade-extension: 10%;
--packages-hero-fade-start: 62%;
--packages-hero-fade-soft: 82%;
```

`--packages-hero-fade-extension` is how far the photograph and its fade extend
below the hero. The default is the requested extra 10%. The other two values
control where transparency starts and how quickly it becomes softer. Keep the
final mask stop at `transparent 100%`; replacing that with `var(--bg)` brings
back the hard horizontal seam, especially when switching themes.

### Change the gallery crop

Apply an `object-position` to an individual gallery row through code only if all items share the same crop. If different items need different focal points, add a dedicated content field and render it in `build.py`; do not pile `nth-child()` rules into CSS.

### Change gallery timing

In `static/js/main.js`, find the comment:

```js
// Gallery images remain completely static; only the active slide cross-fades.
```

The nearby final `9000` is milliseconds, so it changes slides every nine seconds. Changing this value does not re-enable image movement.

### Change a button or control

Reuse existing classes such as `.button`, `.button--key`, `.button--secondary`, and `.button--small`. Do not create one-off inline styles in generated HTML. Test keyboard focus, hover, and touch states.

### Change the logo alignment

Logo alignment is controlled by `.brand__mark` and `.brand__logo`. The source
PNGs are 2048×950 files with transparent padding around artwork that is much
wider than it is tall. The final CSS block crops that padding using the measured
artwork bounds.

To change the visible logo size without disturbing its alignment, edit only:

```css
:root {
  --brand-logo-width: 104px;
}
```

There is a separate responsive value under `@media (max-width: 920px)`. Keep
the crop percentages unchanged unless the underlying PNG artwork is replaced.

## Editing content

### JSON

- Keep keys in double quotes.
- Keep commas between properties.
- Use `true` and `false` without quotes.
- Do not paste HTML into content fields; the build escapes imported text.

After a JSON edit, `python build.py` reports the file and field if validation fails.

### CSV

- Keep the header row unchanged.
- Wrap a value in double quotes if it contains a comma.
- Use unique `id` and `display_order` values.
- Use `visible=true` to publish a row and `visible=false` to keep it as a draft.

### Structural HTML changes

Current pages are assembled by functions in `build.py`, including `header`, `footer`, `home_page`, `package_page`, `contact_page`, and `legal_page`. Edit the smallest relevant function. Preserve semantic elements, labels, `aria-*` attributes, and keyboard controls.

Because much of the generated HTML is assembled as Python strings, make a small change, build immediately, and inspect the generated HTML before continuing.

## SEO and search-preview maintenance

SEO is generated as part of the normal site build. Do not paste separate metadata directly into files under `dist/`; the next build will replace it.

The editable SEO identity and page records are grouped at the top of `content/homepage.json` under `meta`. The implementation is grouped under comments beginning with `SEO:` in `build.py`. Automated coverage lives in `tests/test_seo.py`.

### SEO file map

| SEO responsibility | Source of truth |
| --- | --- |
| Site name, production domain, share image, logo, email and locale | `content/homepage.json` → `meta` |
| Unique title, description and canonical route for each public page | `content/homepage.json` → `meta.pages` |
| Canonical, robots, Open Graph and X/Twitter tag generation | `build.py` → `SEO: metadata, canonical URLs and structured data` |
| Organization, website, FAQ and package/service JSON-LD | `seo_*` functions in `build.py` |
| Complete list of indexable public page keys | `SEO_PAGE_KEYS` in `build.py` |
| Search crawler rules | generated `dist/robots.txt` via `write_seo_files()` |
| Canonical URL discovery | generated `dist/sitemap.xml` via `write_seo_files()` |
| SEO regression tests | `tests/test_seo.py` |

### Change a search-result title or description

Open `content/homepage.json`, find `meta.pages`, then edit only the matching page record:

```json
"packages": {
  "path": "/packages/",
  "title": "Gaming Party Packages and Prices | Party.LAN",
  "description": "Compare Party.LAN's hosted gaming party packages."
}
```

Use these rules:

- Every public page must have a unique title and description.
- Put the page's real subject first and the brand near the end of the title.
- Write for a potential customer, not a list of repeated keywords.
- Keep the description accurate to content visible on that page.
- Do not promise locations, equipment, availability, pricing, age suitability, licensing, safety credentials or service features that are not approved and visible.
- Do not add a `meta keywords` tag; it is not part of this implementation.

Run the build and inspect the generated page source. For the Packages page, for example:

```bash
python build.py
rg -n "<title>|name=\"description\"|rel=\"canonical\"|property=\"og:" dist/packages/index.html
```

### Change the social sharing image

The default Open Graph and X/Twitter image is `meta.og_image`. Its description is `meta.og_image_alt`.

1. Add the approved image under `content/images/`.
2. Use an absolute site path in JSON, such as `/content/images/new-share-image.jpg`.
3. Write concise alternative text describing the image rather than advertising copy.
4. If the new image is not 1576 × 941 pixels, update the `og:image:width` and `og:image:height` values in the shared `head()` function or ask for that code adjustment.
5. Build and confirm that `og:image` and `twitter:image` use an absolute `https://partylan.co.uk/...` URL.
6. After deployment, test the public URL with the relevant social sharing debugger; local `127.0.0.1` images cannot be fetched by external preview tools.

Use a wide, clear image with enough resolution for a large preview. Avoid important text near the edges because different platforms crop previews differently.

### Change the production domain

Only change `meta.canonical_url` when the public production domain has genuinely changed. Keep HTTPS and the trailing slash:

```json
"canonical_url": "https://partylan.co.uk/"
```

After changing it:

1. Build the whole site.
2. Inspect canonical and `og:url` values on every public page.
3. Inspect `dist/robots.txt` and `dist/sitemap.xml`.
4. Confirm the old hostname no longer appears in generated HTML:

```bash
rg -n "old-domain.example" dist
```

Do not change DNS, Render settings, email MX records, SPF, DKIM or DMARC as part of a metadata-only code edit.

### Add, remove or rename a public page

This is a structural change, not a simple content edit. Keep all of these in sync:

1. Add or change the page renderer and output path in `build.py`.
2. Add or change navigation and footer links in `content/homepage.json`.
3. Add or change the page record under `meta.pages`.
4. Add or change its key in `SEO_PAGE_KEYS`.
5. Pass the correct page key into `head()` so the page receives its own canonical and metadata.
6. Update `tests/test_seo.py` expected routes.
7. Build and confirm the page appears once in `sitemap.xml`.
8. Check all internal links and decide whether the old URL needs a redirect in hosting configuration.

Never publish two different pages with the same canonical URL. Never add query strings or `#fragment` values to sitemap entries.

### Maintain robots.txt, sitemap.xml and the demo page

`robots.txt` and `sitemap.xml` are generated files. Change `write_seo_files()` or the canonical page configuration, then rebuild.

Current intent:

- public canonical pages are crawlable and listed in the sitemap;
- `demo-testimonials.html` contains example content, is marked `noindex,follow`, and is excluded from the sitemap;
- the demo page remains crawlable so search engines can read its `noindex` instruction;
- URL query variations such as contact-form intent parameters resolve to the clean page canonical.

Do not block a `noindex` page in `robots.txt`; a crawler must be able to load the page to see the instruction.

### Maintain structured data safely

The JSON-LD describes only information supported by the public page content:

- `Organization` for Party.LAN's approved identity and contact email;
- `WebSite` and page entities for site/page relationships;
- `FAQPage` questions copied from the visible FAQ data;
- `Service` and `Offer` entities generated from approved package records and prices;
- `ContactPage` for the contact route.

The site deliberately uses `Organization` instead of inventing a `LocalBusiness` address or unsupported local-business claims. Do not add any of the following until each value is confirmed, approved, and also visible to visitors:

- public business address;
- telephone number;
- service-area towns, radius or postcodes;
- opening hours;
- review or aggregate rating;
- social profile links;
- legal company identifier;
- awards, accreditations or safety claims.

If a package price, duration, capacity or name changes, update the approved source content first. Structured data must continue to be generated from the same records as the visible package cards; do not hard-code a second contradictory price inside the SEO functions.

### Verify SEO before merging

Run:

```bash
python build.py
python -m unittest discover -s tests -v
git diff --check
```

Open these locally:

- `http://127.0.0.1:8010/robots.txt`
- `http://127.0.0.1:8010/sitemap.xml`
- each public page, then **View Page Source** rather than only using Inspector

Confirm:

- each public page has one unique `<title>`, description and absolute canonical;
- `og:url` matches the canonical;
- Open Graph and Twitter image URLs are absolute and load successfully;
- public pages use `index,follow`;
- the demo page uses `noindex,follow` and has no JSON-LD;
- the sitemap contains only intended canonical public routes;
- all JSON-LD scripts parse as valid JSON;
- visible package prices match structured-data prices;
- no unapproved business claim appears in metadata or schema.

After deployment, validate the public pages with [Google's Rich Results Test](https://search.google.com/test/rich-results) and the [Schema.org Validator](https://validator.schema.org/). In [Google Search Console](https://search.google.com/search-console/), submit `https://partylan.co.uk/sitemap.xml`, inspect the canonical URLs, and request re-indexing for important changed pages. Search engines choose when to recrawl and may rewrite displayed titles or descriptions, so a correct implementation improves eligibility but does not guarantee a particular ranking or preview.

## Replacing or adding images

1. Put the original file in `content/images/`.
2. Use a clear lowercase filename with hyphens or underscores.
3. Reference it as `/content/images/filename.jpg` in JSON or CSV.
4. Add meaningful alternative text when the image communicates content.
5. Run `python build.py`; it validates and copies supported images to `dist/content/images/`. A compatibility copy may also exist under `dist/assets/images/`, but new content must use `/content/images/...`.

Supported image extensions are JPG/JPEG, PNG, WebP, and AVIF.

Performance guidelines:

- Resize photos close to the largest size they actually display; do not upload camera-original dimensions.
- Prefer WebP or a well-compressed progressive JPEG for photos.
- Keep PNG mainly for logos or transparency.
- Aim for roughly 150–300 KB for a large hero and under 150 KB for ordinary gallery images when quality allows.
- Keep `loading="lazy"` on below-the-fold images. The main hero should load eagerly.
- Avoid shipping separate near-identical images when CSS cropping is sufficient.

## Mobile performance rules

The current low-power path intentionally does the following at 920px and below:

- no image pan, zoom, or breathing animation;
- no decorative background parallax or its scroll listener;
- no reveal-on-scroll transforms;
- no backdrop blur on large translucent panels;
- no oversized panel shadows;
- short opacity-only gallery cross-fades;
- no touch-device hover transforms.

When adding a feature, avoid:

- `filter: blur()` on large fixed elements;
- large `backdrop-filter` areas;
- continuously animated gradients;
- full-page fixed layers with `will-change: transform`;
- JavaScript that reads layout and writes styles on every scroll event;
- multiple nested transforms on the same image;
- huge box shadows on full-width mobile panels.

If motion is ever reintroduced for another UI control, respect `prefers-reduced-motion`, animate only `opacity` or `transform`, keep the affected element small, and test on physical mid-range Android hardware.

## Troubleshooting common problems

### “I changed a file but nothing changed on the website”

Check these in order:

1. Confirm you edited a source file, not `dist/` or `templates/index.html`.
2. Save the file.
3. Run `python build.py` again.
4. Confirm the build completed without errors.
5. Hard-refresh the browser with `Ctrl+Shift+R`.
6. Check the correct local address and route.
7. Search the generated file to see whether the new value exists:

```bash
rg -n "a distinctive piece of the new text" dist
```

If the value exists in `dist` but the browser still shows an older result, stop and restart the preview server and clear or bypass the browser cache.

### CSS changes appear to have no effect

Use Inspector to check which selector wins. A later rule, stronger selector, media query, theme rule, or `!important` declaration may override your edit.

Search for every use of the selector or variable:

```bash
rg -n "selector-name|variable-name" static/css/styles.css
```

Fix the authoritative rule instead of adding another unexplained patch at the bottom. If a late compatibility block must remain authoritative, document why there.

### The layout works on desktop but breaks on mobile

Check the width immediately above, at, and below the main `920px` breakpoint. Verify that the problem is not caused by:

- fixed widths or large fixed margins;
- a grid minimum wider than the viewport;
- long unbroken text;
- absolute positioning inherited from desktop;
- hover transforms affecting touch devices;
- an image's intrinsic size or incorrect `object-position`;
- padding being applied by both a parent and child.

Do not solve a general layout issue with many device-specific breakpoints. Prefer one fluid rule and the established `920px` mobile transition.

### The build reports a JSON or CSV error

Read the complete error; the validator normally names the file, field, row, or duplicate value.

For JSON, check quotation marks, commas, braces, and whether booleans are unquoted. For CSV, check the header, commas inside unquoted text, duplicate IDs/orders, supported category/platform values, and image paths.

Use Python to confirm JSON syntax when needed:

```bash
python -m json.tool content/homepage.json > NUL
```

On macOS/Linux, replace `NUL` with `/dev/null`.

### Windows reports `PermissionError` while rebuilding `dist/`

The build deletes and recreates `dist/`. If another program has locked a generated file:

1. Stop the local server with `Ctrl+C`.
2. Close any editor, image viewer, terminal, sync tool, or antivirus dialog holding a file under `dist/`.
3. Run `python build.py` again.
4. Restart the server:

```bash
python -m http.server 8010 --bind 127.0.0.1 --directory dist
```

Do not manually delete source files to work around a lock.

### Port 8010 is already in use

Reuse the existing preview server if it is serving the current `dist/`. Otherwise stop the old terminal process with `Ctrl+C`, or choose another local port:

```bash
python -m http.server 8011 --bind 127.0.0.1 --directory dist
```

Then open `http://127.0.0.1:8011/`.

### An image is missing or returns 404

Confirm all of the following:

- the original exists under `content/images/`;
- the extension is supported;
- the JSON/CSV path begins `/content/images/`;
- uppercase/lowercase characters exactly match the filename;
- the build succeeds;
- the generated file exists under `dist/content/images/`.

Windows commonly hides case mismatches that fail after deployment to a case-sensitive host.

### The page source has the wrong canonical or social preview

Check the matching record under `content/homepage.json` → `meta.pages`, rebuild, and inspect **View Page Source**. Inspector may show runtime changes, while search engines initially receive the generated source.

External preview services cache metadata. Confirm the deployed HTML is correct first, then request a refresh through the platform's preview/debug tool. Do not keep changing correct metadata merely because a third-party cache is stale.

### Git shows files that do not belong to the request

Do not use `git add -A` in a mixed working tree. Review:

```bash
git status --short
git diff -- path/to/file
```

Stage only intended paths or hunks with `git add -p`. Temporary office lock files, Python caches, editor settings, local secrets, and unrelated generated experiments do not belong in the PR.

### A branch was created but is not visible on GitHub

A local branch is not published until it has been pushed:

```bash
git push -u origin your-name/short-change-description
```

After pushing, confirm the branch and latest commit on GitHub before opening or updating the PR.

## Validation checklist before a pull request

Run:

```bash
python build.py
python -m unittest discover -s tests -v
git status --short
git diff --check
git diff --stat
```

Then manually verify:

- Homepage, Packages, Contact, Terms, and Privacy pages load.
- Light and dark themes work.
- Header menu opens, closes, and works by keyboard.
- Gallery tabs and indicators work; photos remain static.
- Mobile hero has no sharp left or right line.
- No horizontal page scrolling appears at 360px.
- Package and FAQ accordions work.
- Form labels and visible error messages remain aligned.
- All new images load with no 404 response.
- Every public page has its own correct canonical URL.
- `robots.txt` and `sitemap.xml` load and contain the intended production domain.
- The demo testimonial page remains excluded from indexing and the sitemap.
- No secret, password, customer data, or private contact data is in the diff.

For performance, use the browser Performance panel or Lighthouse as a comparison tool. Record the same page, device emulation, and throttling settings before and after a large change. A real lower-end phone remains the most trustworthy final test.

## Git and pull request workflow

Review the diff before committing:

```bash
git diff -- static/css/styles.css
git diff -- static/js/main.js
git diff -- content/
```

Stage only the files that belong to the change. Interactive staging is safest
if the working tree contains other work:

```bash
git add -p
git status --short
git commit -m "Describe the page adjustment"
git push -u origin your-name/short-change-description
```

For a new file that does not appear in `git add -p`, add that exact path, for
example `git add docs/MANUAL_EDITING_GUIDE.md`. Do not stage unrelated files.

Open a pull request, use the deployment preview if available, and test the exact preview URL on a physical phone before merging.

## If a change is hard to describe

For future visual requests, provide any combination of:

- a screenshot with arrows or a rough drawing;
- the page URL and phone model;
- the viewport width shown in DevTools;
- “current” and “desired” screenshots;
- the element selected in Inspector and its CSS selector;
- a numeric adjustment discovered in DevTools, for example “`padding-top: 18px` looks right at 390px.”

That is enough to turn a visual preference into a precise, reviewable code change without needing specialised CSS terminology.

## Maintaining this guide

Update this document in the same pull request whenever a change alters:

- the source-of-truth file map;
- build, test, preview or deployment commands;
- public routes or SEO configuration;
- supported content fields or validation rules;
- responsive breakpoints or authoritative CSS controls;
- image locations or supported formats;
- branch, PR or hosting workflow.

Keep instructions tied to real repository behaviour. Remove obsolete guidance rather than adding a contradictory note later in the file. A future editor should be able to follow one current path from source edit to deployed verification without having to infer which instruction is newest.
