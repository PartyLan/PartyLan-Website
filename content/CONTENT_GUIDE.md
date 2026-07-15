# Party.LAN content editing guide

This site is built from editable files in `content/`. For ordinary wording updates, edit these files only, then run `python build.py` and preview `dist/` locally.

## Safe files to edit

- `content/homepage.json` — unique homepage copy: metadata, navigation, hero, reassurance strip, section introductions, add-on panel, how-it-works steps, gallery intro, room-planning copy, final CTA and footer.
- `content/packages.json` — ONYX and JADE package wording and expandable details. The fixed business details below must not change unless Party.LAN approves it.
- `content/addons.csv` — optional or planned add-ons. Do not add fixed prices unless approved.
- `content/testimonials.csv` — approved real testimonials for normal visitors.
- `content/testimonials.example.csv` — demo testimonials only. These appear only in demo mode (`?demo=testimonials`).
- `content/gallery.csv` — gallery images, captions and categories.
- `content/faq.csv` — FAQ questions and answers.
- `content/legal/terms.json` and `content/legal/privacy.json` — draft legal-page wording.

Do not edit `templates/`, `static/` or `build.py` unless changing site code.

## JSON basics

JSON uses pairs like `"title": "Text here"`. Keep quotation marks around text and keep commas between fields. Use `true` and `false` without quotes for switches. If text contains a quotation mark, either avoid it or escape it as `\"`.

Example:

```json
"hero": {
  "title": "Bring everyone together.",
  "description": "Hosted gaming parties delivered to your venue."
}
```

## CSV basics

CSV files have a header row. Keep the column names unchanged. If a value contains a comma, wrap the whole value in quotes:

```csv
id,title,description,available_for,price_note,visible,display_order
extra-time,Additional time,"Add time, if the diary allows.",both,Price confirmed during enquiry,true,1
```

## Visibility and ordering

- `visible` controls whether a record appears. Use `true` to show it and `false` to hide it without deleting it.
- `display_order` controls the order. Use positive whole numbers such as `1`, `2`, `3`. Avoid duplicate numbers in the same file.

## Accepted category values

- `content/addons.csv` `available_for`: `onyx`, `jade`, or `both`.
- `content/gallery.csv` `category`: `experience` or `equipment`.
- `content/testimonials.csv` `package`: `onyx` or `jade`.

## Fixed Party.LAN package details

These are currently fixed and validated by the build:

- ONYX: Premium Experience, £150, 2 hours, up to 6 players, includes PlayStation and Nintendo gaming, racing simulator, VR hardware, displays, party host/operator and free digital invitation.
- JADE: Big Party, £150, 2 hours, up to 10 players, includes multiplayer gaming across multiple stations, displays, party host/operator and free digital invitation.

## Common tasks

### Edit hero or CTA copy

Open `content/homepage.json`. Change `hero.title`, `hero.description`, `hero.primary_cta`, `hero.secondary_cta` or `final_cta`.

### Edit package wording

Open `content/packages.json`. You may edit `summary`, the `expanded` text, `addon_intro`, `enquiry_note` and `enquiry_button`. Do not change the fixed price, duration, capacity or included lists unless approved.

### Add an add-on

Add a row to `content/addons.csv` with a unique `id`, a title, description, `available_for`, a non-final `price_note`, `visible` and `display_order`.

### Add a gallery entry

Add a row to `content/gallery.csv`. Put the image file in `content/images/` first, then reference it as `/assets/images/file_name.jpg`. Choose `experience` for people and atmosphere, or `equipment` for setup and hardware.

### Add a real testimonial

Add it to `content/testimonials.csv` only when approved. Use a local existing image under `/assets/images/...`, add meaningful `alt` text, set `visible` to `true`, and choose package `onyx` or `jade` if relevant.

### Demo testimonials

`content/testimonials.example.csv` is only for clearly labelled demo examples. Normal visitors do not see this file. Demo mode is available at `/?demo=testimonials`.

### Add or edit FAQ entries

Edit `content/faq.csv`. Keep questions short and answers clear. Hide an FAQ with `visible=false`.

### Edit legal draft text

Edit `content/legal/terms.json` or `content/legal/privacy.json`. Keep the draft warning unless the legal text has been professionally reviewed. Do not present placeholders as final advice.

## Build and preview

Run:

```bash
python build.py
python -m http.server 8010 --bind 127.0.0.1 --directory dist
```

Preview:

- Homepage: `http://127.0.0.1:8010/`
- Demo testimonials: `http://127.0.0.1:8010/?demo=testimonials`
- Terms: `http://127.0.0.1:8010/terms/`
- Privacy: `http://127.0.0.1:8010/privacy/`

If the build fails, read the validation message. It names the file, row or field that needs fixing.

## Homepage versus Packages page

The homepage is now focused on emotion, trust and enquiry. It does **not** show ONYX or JADE package cards or prices. The hero `View packages` button links to `/packages/`, where package comparison and pricing live.

### Edit Packages-page copy

Open `content/homepage.json` and edit the `packages_page` section:

- `packages_page.hero.heading` controls the Packages-page hero heading.
- `packages_page.hero.description` controls the supporting sentence.
- `packages_page.hero.media.light` and `.dark` control the existing local hero images.
- `packages_page.guidance` controls the guidance section beneath add-ons.
- `packages_page.cta` controls the Packages-page final enquiry section.

### Edit package detail buttons

Open `content/packages.json`. The `details_button` field controls the large package detail control, for example `Explore ONYX`. The `enquiry_button` field controls the enquiry link, for example `Ask about ONYX`.

### FAQ Terms link

Open `content/homepage.json` and edit `faq_section.terms_link.text` for the visible Terms & Conditions prompt below the FAQ. Keep `faq_section.terms_link.href` as `/terms/` unless the Terms page route changes.

### Preview the Packages page

After running `python build.py`, preview `http://127.0.0.1:8010/packages/` as well as the homepage.

## Optional future Packages-page hero image

The Packages page supports a future hero image without requiring one today. In `content/homepage.json`, edit `packages_page.hero`:

- Leave `image` as an empty string (`""`) to use the existing fallback.
- `fallback_image` and `fallback_image_dark` must always point to valid existing images.
- When a new approved image is added later, put it in `content/images/` and set `image` to `/assets/images/new-file-name.jpg`.
- The build validates a non-empty `image`, but it will not fail just because `image` is empty.
- Do not add or rename image files unless the site is being deliberately updated with approved assets.

## Gallery autoplay, indicators and play/pause

The Shared Moments gallery shows one large image at a time. JavaScript creates one indicator button per visible item in the selected category. Changing between `experience` and `equipment` resets the gallery to the first item in that category.

The small circular control on the image pauses or plays automatic advancement. Clicking an indicator, swiping or dragging pauses the gallery. Under reduced-motion settings, automatic advancement remains off, but indicators and tabs still work.

## Add-on grouping

`content/addons.csv` still controls add-ons. Rows with `available_for` set to `both` are shown first, followed by package-specific rows for `onyx` and `jade`. The Packages page displays add-ons as one structured list rather than separate cards.

## Subpage Home navigation

The homepage header intentionally shows only Packages, FAQ and Check availability. Subpages automatically add a visible Home link before those items, so editors do not need to duplicate navigation content.

## Wider fluid layout

The site uses wider fluid containers for visual sections on large CSS viewports. This does not require content changes. Keep normal paragraph copy concise so it remains readable inside the designed text measures.

## Header and theme button

The visible header navigation is Home, Packages and FAQ, with Check availability as the separate action button. The Party.LAN logo still links home, but it is not the only Home route. The theme control is icon-only: moon means it will switch to dark mode, and sun means it will switch to light mode. Screen readers use the button's accessible label.

## Hero secondary CTA

The homepage hero secondary CTA now points to the Shared Moments gallery. Edit `hero.secondary_cta.label` and `hero.secondary_cta.href` in `content/homepage.json`; the approved default is `See the experience` linking to `#gallery`.

## How it works optional images

Each `how_it_works.steps` entry can include an optional future image:

```json
"image": "",
"image_alt": "Party.LAN package choices.",
"image_position": "center"
```

Leave `image` empty until an approved asset exists. The build will render a polished placeholder area and will not output a broken image. When adding an approved future image, place it under `content/images/`, reference it as `/assets/images/file-name.jpg`, and write meaningful `image_alt` text. Accepted `image_position` values are `center`, `top`, `bottom`, `left`, and `right`.

## Testimonial layout and controls

Testimonials use centred text over the image with a local readability scrim rather than a full-image dark wash. The indicator buttons sit inside a frosted capsule at the bottom of the image, and the play/pause button sits at the bottom-right. Clicking an indicator pauses autoplay. Dragging or swiping changes slides without accidentally toggling play/pause.

## Logo source and generated paths

The authoritative logo files live in `content/images/Logo_Black_T.png` and `content/images/Logo_White_T.png`. The build validates and copies them through the content-image pipeline to `dist/assets/images/`, and rendered pages use `/assets/images/Logo_Black_T.png` and `/assets/images/Logo_White_T.png`. Do not edit, rename or duplicate the logo binaries.

## Temporary How it works placeholder images

The How it works cards currently use existing repository images as temporary placeholders. These paths live in `content/homepage.json` under each `how_it_works.steps` item. They must use generated browser paths such as `/assets/images/gallery_group-fun_01.jpg`, not `content/images/...` paths. Replace them later only with approved images already added to `content/images/`.

## Reassurance icon slots

Each reassurance item may include an optional `icon` path and `icon_alt`. Leave `icon` empty to show the current polished placeholder slot. If a future approved icon is added, reference it as `/assets/images/file-name.png` or another supported generated asset path. The build validates non-empty icon paths.

## FAQ links and Terms entry

FAQ rows may include optional `link_label` and `link_href` columns. Use both columns together or leave both empty. The Terms & Conditions link is now part of the Terms FAQ item rather than a separate button beneath the accordion.

## Motion and reduced motion

Hero and Shared Experience images use slow CSS pan/breathing animations. These are decorative and use transform/opacity only. Reduced-motion users keep all content and manual controls, but decorative pan/breathing and autoplay are disabled or paused.


## Latest layout and interaction notes

- Header navigation is intentionally limited to **Home**, **Packages** and **FAQ**, with **Check availability** as the separate header CTA. Do not add permanent How it works or Gallery links.
- The Packages page uses a shared enquiry block in `packages_page.shared_enquiry` for “Not sure which package fits?” and the `Ask about packages` CTA. Individual package cards should not carry separate ONYX/JADE enquiry buttons.
- How it works image fields currently use existing repository images as temporary placeholders. Replace each `image` value with a future `/assets/images/<filename>` path only after adding the source file to `content/images/`; keep `image_alt` meaningful and adjust `image_position` only to `center`, `top`, `bottom`, `left` or `right`.
- Reassurance items reserve an icon-ready slot. Leave `icon` empty for the CSS placeholder, or set it to an existing `/assets/images/<filename>` asset when a future approved graphic is available.
- FAQ records may include `link_label` and `link_href` together. The Terms & Conditions link is part of the FAQ answer itself, not a separate button below the accordion.
- The wide visual container scales major image-led compositions for large CSS viewports; ordinary body copy remains constrained, so content editors do not need to shorten text for wide screens.
- Hero, testimonial and showcase motion is decorative CSS transform/opacity animation only and is disabled for `prefers-reduced-motion`.

## Navigation, package accordions and mobile utility controls

- Desktop navigation keeps the short primary `navigation` list (`Home`, `Packages`, `FAQ`) in the header and also exposes the complete hamburger dropdown.
- The hamburger dropdown is edited in `content/homepage.json` under `navigation_groups`. Keep three groups in this order:
  1. `How it works`, `Shared Moments`, `FAQ`
  2. `Packages`, `Make your own`
  3. `Contact`, `Terms of Service`, `Privacy Policy`
- Use the full local hrefs already in the file, especially homepage-prefixed anchors such as `/#faq` and the package anchor `/packages/#make-your-own`, so links work from subpages.
- On mobile the header is a single utility row: logo, `Check availability`, theme icon and menu button. This layout is generated from the existing header and navigation content.
- Package cards use `summary` for the compact collapsed copy and `details_button` for the accordion control. Keep these short so ONYX and JADE remain easy to scan.
- Full package detail content lives in each package's `expanded` object and the `included` list in `content/packages.json`; this content is shown only after expanding the package accordion.
- The `Make it your own` section uses `addons_section.accordion_label` and `addons_section.description` from `content/homepage.json`. It is expanded by default on desktop and collapsed by default on mobile. Add-on rows still come only from `content/addons.csv`.
- FAQ rows may include `link_label` and `link_href`. Both fields must be filled together or both left blank. The Terms FAQ uses `Read full Terms & Conditions` with `/terms/`, which renders as a button inside the expanded FAQ answer.
- The sticky mobile `Check availability` control is behavioural chrome, not editable content. It hides when the booking section, footer or navigation menu is visible and page padding is handled in CSS.

## Packages final decision section

Edit `content/homepage.json` under `packages_page.final_decision` to control the final Packages-page decision section. The editable fields are `eyebrow`, `heading`, `description`, `reserve_label`, `reserve_href`, `ask_label`, `questions_label`, `ask_heading`, `ask_description`, `contact_label`, and `contact_href`. Keep reservation/contact hrefs on existing local destinations such as `/#booking` unless the booking route changes.
