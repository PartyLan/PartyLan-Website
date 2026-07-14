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
