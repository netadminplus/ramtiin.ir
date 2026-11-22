# Figma Make prompt — ramtiin.ir redesign (2026-11-21)

Ramtin asked for this prompt in English. He will paste it into Figma Make,
take its output, and bring it back to Muse, who ports the DESIGN into the
current static template / GitHub Pages project (React output cannot be
dropped in directly; RTL and content structure are kept).

---

Design a complete, professional redesign for my Persian (Farsi) tech blog — https://ramtiin.ir — as a working prototype with 4 pages. Look at the live site first to understand the content and structure.

## About the site

- Personal blog of Ramtin Rahmani Nejad, a network engineer and educator (in IT since 2006). Persian-language tutorials and articles about computer networking: MikroTik RouterOS, VPNs (OpenConnect, WireGuard, OpenVPN), network support and consulting, online courses.
- Audience: Persian-speaking network engineers, IT admins, and students. Tone: professional, trustworthy, practical — a teacher's blog, not a startup landing page.
- The site is a static blog (GitHub Pages). The final design will be ported by a developer into plain HTML/CSS, so design with standard, portable web components — no exotic interactions that can't be rebuilt in static HTML/CSS.
- This is a redesign of the look, not a restructuring: keep the content structure, the existing pages, and the real navigation items from the live site. My current design was rejected for not looking professional and standard enough — that is the bar to beat.

## Pages to design (4)

1. **Homepage** — blog listing: header, a short intro strip (who the author is, what the blog covers), a grid of article cards (3 columns on desktop), pagination below the grid.
2. **Article page** — a full post: title, author/date/reading-time meta, category, featured image, well-formatted body (headings, paragraphs, code blocks, lists, tables, callouts), author box, comments section, related posts.
3. **Category / archive page** — category header (name + short description), grid of article cards, pagination.
4. **About / Contact page** — author bio, services (network support, consulting, courses), contact form, social links.

## Design requirements

- Fully RTL (right-to-left), Persian language. Use the Vazirmatn font (or a similar clean Persian font) throughout.
- Light, clean, professional theme. A modern tech-blog standard — a polished editorial blog, not a dashboard and not a landing page.
- One strong accent color, used consistently (links, buttons, category chips, highlights). The current brand accent is pink #FF486A — keep it or refine it into a more professional shade.
- Article cards: featured image (16:9), one unified category chip style (the same color for every category), clear title, a 2-line excerpt, a meta line (date, reading time), and a visible "read more" link. All cards in a row must be the same height, with the "read more" pinned to the bottom of the card.
- Desktop grid: 3 columns. Tablet: 2 columns. Mobile: 1 column. Generous whitespace, consistent spacing, no overlapping elements.
- Header: logo/site name, main navigation menu, search icon, social icons. On mobile the hamburger menu must open a working slide-in navigation drawer — this is a must.
- Footer: short about blurb, quick links, categories, social links, copyright.
- Typography: clear hierarchy, generous line-height for Persian text, readable body size (16–18px).
- Dates in Persian format (Jalali calendar) with Persian digits.
- Use REAL content from the live site: real Persian post titles (for example about OpenConnect, MikroTik, WireGuard, VPN), real category names, real excerpts — not lorem ipsum, not invented English text.
- Do NOT redesign the logo. Do NOT add dark mode. Do NOT add animations that distract from reading.

## Deliverable

- A working prototype of the 4 pages, linked together: clicking a card opens the article page, category chips open the category page, navigation links work. Fully responsive (desktop + tablet + mobile).

---

## Short version (under Figma Make 2,000-char limit: 1,816 chars)

Redesign my Persian tech blog https://ramtiin.ir as a working, responsive prototype with 4 linked pages. Look at the live site first and use its real content.

Site: personal blog of Ramtin Rahmani Nejad, network engineer and educator. Persian tutorials on networking: MikroTik RouterOS, VPNs (OpenConnect, WireGuard, OpenVPN), support, consulting, courses. Audience: Persian-speaking network engineers, IT admins, students. Tone: professional, trustworthy, practical. Current design was rejected as unprofessional — beat that bar. It will be ported to plain HTML/CSS — use standard, portable components.

Pages: 1) Homepage — header, short intro strip, article-card grid (3 cols desktop), pagination below. 2) Article page — title, author/date/reading time, category, featured image, body (headings, code, lists, tables), author box, comments, related posts. 3) Category page — header with name + description, card grid, pagination. 4) About/Contact — bio, services, contact form, social links.

Requirements: fully RTL, Persian, Vazirmatn font. Light, clean, modern editorial tech-blog theme. One accent color (current: pink #FF486A — keep or refine). Cards: 16:9 image, one unified category-chip color, title, 2-line excerpt, date/reading time, visible 'read more'; equal heights per row, 'read more' pinned to bottom. Grid: 3 cols desktop, 2 tablet, 1 mobile. Header: logo, nav, search, socials; mobile hamburger must open a working slide-in drawer. Footer: about, links, categories, socials. Body text 16–18px, generous line-height. Dates in Jalali calendar with Persian digits. Real Persian titles and excerpts from the site — no lorem ipsum. No logo redesign, no dark mode, no distracting animations. Deliverable: 4 linked pages (card → article, chip → category, nav works), responsive.
