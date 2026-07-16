# Party.LAN manual page editing guide

This guide explains how to change the current Party.LAN website by hand, preview the result, test mobile layouts, and submit a safe pull request. It covers both content changes and visual/code changes.

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

Logo alignment is controlled by `.brand__mark` and `.brand__logo`. The logo pivot and crop are intentionally anchored to the centre-left:

```css
.brand__mark,
.brand__logo {
  transform-origin: left center;
  object-position: left center;
}
```

Keep the source PNG files unchanged unless the artwork itself is being replaced.

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

## Replacing or adding images

1. Put the original file in `content/images/`.
2. Use a clear lowercase filename with hyphens or underscores.
3. Reference it as `/assets/images/filename.jpg` in JSON or CSV.
4. Add meaningful alternative text when the image communicates content.
5. Run `python build.py`; it validates and copies supported images to `dist/assets/images/`.

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

## Validation checklist before a pull request

Run:

```bash
python build.py
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
