# ramtiin.ir — Theme Analysis (for faithful static rebuild)

**Purpose:** document the live design of https://ramtiin.ir precisely enough to rebuild it as a static site — same look and structure, no WordPress, NOT a redesign, NOT a copy of ramtin.zone.

**Sources examined (2026-11-21, read-only, nothing changed on the live site):**
- Homepage HTML saved at `/tmp/ramtiin.html` (224 KB, fetched 2026-11-21 10:46 UTC)
- Post page `https://ramtiin.ir/container-mikrotik/` (273 KB)
- Commented post `https://ramtiin.ir/آموزش-راه-اندازی-openvpn-میکروتیک/` (38 comments, 341 KB)
- Category page `https://ramtiin.ir/category/mikrotik/` (224 KB)
- Contact page `https://ramtiin.ir/contact/` (223 KB)
- Theme CSS: `wp-content/themes/veen/style.css` (header comment only, 496 bytes),
  `wp-content/themes/veen/assets/dist/style.min.css` (147,342 bytes, also inlined in every page),
  `wp-content/themes/veen/rtl.css` (10,009 bytes),
  `wp-content/themes/veen/fonts/fonts.css` (1,305 bytes),
  `wp-content/themes/veen/assets/dist/fontawesome.min.css`, `plugins.min.css`
  (plus WP Fastest Cache minified bundles `wp-content/cache/wpfc-minified/*/ab97f.css` — cache copies, not source).

**Theme:** Veen 2.2.0 by EstudioPatagon (ThemeForest "Minimal Blog Theme for WordPress").
Body class on every page: `rtl ... wp-theme-veen enable-optimization wpb-js-composer js-comp-ver-6.6.0 vc_responsive`.

---

## 0. Global

- `<html dir="rtl" lang="fa-IR" prefix="og: http://ogp.me/ns#">`
- Layout grid: `.grid-container { max-width: 1200px; padding-left: 20px; padding-right: 20px; margin-left/right: auto }` — float-based grid (`.grid-25/30/33/70/100`, `float: left` with RTL overrides in `rtl.css`).
- Background: white `#fff`. Body text: `#596172`, `font: 16px "Nunito","Source Sans Pro",sans-serif; line-height: 1.8` (theme default — overridden, see fonts).
- Headings/links default color: `#242323` (`a{color:#242323}`).
- **Accent color: `#FF486A`** (pink-red) — used for `.button` background, the logo dot (`.dot{width:7px;height:7px;background-color:#FF486A;border-radius:50%}`), and several category chips.
- Borders/dividers: `#eeeeee` (`.epcl-border{background-color:#eeeeee}`, all widget list borders `border-color:#eeeeee !important`).
- Text selection: `::selection{background-color:#596172;color:white}`.
- Footer subscribe area background: `#252A40` (CSS rule exists; no subscribe form is actually rendered — see §7).
- Dates use Persian month names in Latin-style format: `16 جولای, 2026`, `23 ژوئن, 2026`, `در 29 آوریل, 2022` (day + transliterated month + year).

### Fonts

- `wp-content/themes/veen/fonts/fonts.css` defines 15 self-hosted `@font-face` families (all `.woff` under `wp-content/themes/veen/fonts/fonts/`): `IranSans`, `IRANSans-EN`, `Aviny`, `Kufi`, `Naskh`, `IranYekan`, `IranYekan-Bold`, `IranYekan-EN`, `Sahel`, `Parastoo`, `Samim`, `Shabnam`, `Vazir-Bold`, `Vazir-Light`, `Gandom`, `ANic`.
- **Actually applied everywhere is `IranYekan`** (weight `normal`), set by the theme-customizer inline CSS (`<style id="epcl-plugins-inline-css">`): `body, .epcl-button, .pagination ..., input, textarea, select, button, label, .wpcf7 label, #header nav ul.sub-menu li a { font-family: IranYekan; }` and the same for `.title, div.text h1–h6, #header nav ul.menu > li > a, .button, div.meta, div.tags, aside .widget, #footer .widget`.
- Theme defaults that the customizer overrides: body `"Nunito","Source Sans Pro"`, headings `"Josefin Sans",sans-serif`; code `font-family:'Consolas',Monaco,monospace`.
- Icons: FontAwesome 4 (`fontawesome.min.css`, `fa fa-facebook` etc.) + inline SVG sprite (`<use xlink:href="#search-icon">`, `#menu-icon`, `#close-icon`, `#comments-icon`, `#views-icon`, `#clock-fill-icon`, `#tag-icon`, `#copy-icon`).

### Category chip colors (from the customizer CSS)

| cat ID | slug | name | chip color |
|---|---|---|---|
| 1 | uncategorized | دسته بندی نشده | `#FF486A` |
| 2 | windows | ویندوز | `#7169fe` |
| 3 | mikrotik | میکروتیک | `#FF486A` |
| 4 | tricks | ترفند | `#1cbfc3` |
| 5 | network | شبکه | `#fdd948` |
| 6 | voip | VOIP | `#8338ec` |
| 27 | linux | لینوکس | `#17e863` |

Categories with **no** custom color in the customizer CSS: devops (103), openwrt (105), رادیو ترمینال (104). Rule form: `.widget_categories ul li.cat-item-6 span, div.tags a.tag-link-6, a.tag-link-6, .ctag-6 { background: #8338ec !important; }`.

---

## 1. Header

`<header id="header" class="classic enable-sticky enable-sticky-mobile">` — sticky on desktop **and** mobile. `#header{position:relative;margin-bottom:-20px}`, `#header .grid-container{padding:70px 0 0}`.

DOM order inside `.menu-wrapper > .grid-container`:
1. **Mobile menu button** — `<div class="menu-mobile">` with two SVGs: `<svg class="icon ularge open"><use xlink:href="#menu-icon"></use></svg>` and `<svg class="icon ularge close"><use xlink:href="#close-icon"></use></svg>`. CSS: `#header div.menu-mobile{display:none}` on desktop; on mobile `display:block; position:absolute; left:40px; top:50%; transform:translateY(-50%); z-index:200`. A `<div class="menu-overlay hide-on-desktop">` covers the page when the mobile menu is open (JS toggle, theme script).
2. **Logo — TEXT, not an image:** `<div class="logo text-logo"><a href="https://ramtiin.ir/" class="title ularge no-margin"> رامتین<span class="dot"></span></a></div>` — the word «رامتین» plus a pink dot. `#header .logo{text-align:center;margin:5px auto;float:left}`, `#header .logo a{color:#242323}`. On mobile sticky header the logo shrinks: `@media (max-width:767px){ #header.is-sticky div.menu-wrapper .logo a{ font-size: 40px; } }`.
3. **Social buttons** — `<div class="epcl-social-buttons fill-color hide-on-tablet hide-on-mobile hide-on-desktop-sm">`, circular brand-color buttons (`a.button.circle`), in this order:
   - LinkedIn → `https://www.linkedin.com/in/ramtin-rahmani` (`fa fa-linkedin`)
   - Instagram → `https://instagram.com/ramtiin.ir` (`fa fa-instagram`)
   - YouTube → `https://www.youtube.com/c/netadminplus` (`fa fa-youtube`)
   - Telegram → `https://t.me/netadminplus` (`fa fa-telegram`)
   - Email → `https://ramtiin.ir/contact/` (`fa fa-envelope-o`)
   All `target="_blank" rel="nofollow noopener"`. Note: Instagram here is `instagram.com/ramtiin.ir` (NOT `@netadminplus`); YouTube is the old `/c/netadminplus` URL.
4. **Search button** — `<a href="#search-lightbox" class="lightbox epcl-search-button button circle mfp-inline"><svg class="icon"><use xlink:href="#search-icon"></use></svg></a>` — opens a Magnific Popup lightbox (see §6).
5. **Main nav** — `<nav class="main-nav"><ul id="menu-اصلی-1" class="menu">`, items `display:inline-block; padding:20px 13px`, dropdown parents get `margin-right:10px; padding-right:15px`. Full menu in order:
   - صفحه اصلی → `https://ramtiin.ir` (current page)
   - دوره‌های آموزش میکروتیک → `https://ramtiin.ir/آموزش-میکروتیک/`
   - میکروتیک → `https://ramtiin.ir/category/mikrotik/`
   - لینوکس → `https://ramtiin.ir/category/linux/`
   - ویندوز → `https://ramtiin.ir/category/windows/`
   - VOIP → `https://ramtiin.ir/category/voip/`
   - ترفند → `https://ramtiin.ir/category/tricks/`
   - خدمات ▾ (`href="#"`, `menu-item-has-children`) →
     - پشتیبانی شبکه در شیراز → `https://ramtiin.ir/پشتیبانی-شبکه-در-شیراز/`
     - راه‌اندازی شبکه در شیراز → `https://ramtiin.ir/راه-اندازی-شبکه-در-شیراز/`
     - پشتیبانی تلفن ویپ → `https://ramtiin.ir/پشتیبانی-تلفن-ویپ/`
   - رامتین ▾ (`href="#"`) →
     - درباره من → `https://ramtiin.ir/درباره-من/`
     - تماس با من → `https://ramtiin.ir/contact/`
     - حمایت مالی → `https://ramtiin.ir/donate/`

---

## 2. Homepage — NO hero, NO services grid

The homepage is a plain blog loop. There is **no hero, no slider, no services section, no about block** above the posts. Structure:

```
<main id="home" class="main">
  <div class="grid-container">
    <div class="row module-wrapper" id="epcl-classic-posts-1">
      <div class="content-wrapper classic content">
        <div class="center left-content">
          <div class="articles classic">
            <article class="default classic-large index-N ..."> × 6
          </div>
          <div class="epcl-pagination section">…</div>
```

- **No sidebar on the homepage** (no `<aside>` anywhere in the file); cards are full-width `grid-100 tablet-grid-100`.
- **6 posts per page, 8 pages** (48 posts). Pagination: `<div class="epcl-pagination section"><div class="nav"><span class="page-number"> صفحه 1 از 8 </span><a href="https://ramtiin.ir/page/2/">بعدي</a></div></div>` (only a "next" link on page 1; URL pattern `/page/N/`).
- Between `</header>` and the first `<article>` there is nothing except the search lightbox markup.

### Post card (`article.default.classic-large`)

```
<article class="default classic-large index-0 odd grid-100 tablet-grid-100" post-1993 ...>
  <header>
    <div class="post-format-image post-format-wrapper">
      <div class="featured-image mask-effect">
        <a href="{post}" class="thumb epcl-loader">
          <span class="fullimage cover lazyload" role="img" aria-label="{title}"
                style="background-image:inherit;"
                data-bg-image="url({featured-image}.webp)"></span></a>
        <h1 class="post-title title"><a href="{post}" class="mask">{title}</a></h1>
        <a href="{post}" class="continue-reading button secondary hide-on-mobile">بیشتر بخوانید</a>
      </div>
    </div>
    <div class="meta absolute">
      <a href="{post}#show-comments" class="comments meta-info mobile" title="0 دیدگاه">
        <svg><use xlink:href="#comments-icon"></use></svg> <span class="comment-count">0</span></a>
      <span class="views-counter meta-info mobile comments" title="95 Views">
        <svg><use xlink:href="#views-icon"></use></svg> 95</span>
      <div class="min-read meta-info" title="17 Min Read">
        <svg><use xlink:href="#clock-fill-icon"></use></svg> 17</div>
    </div>
  </header>
  <div class="bottom grid-container grid-small np-mobile">
    <div class="meta">
      <a href="https://ramtiin.ir/author/ramtin-rahmanigmail-com/" class="author meta-info hide-on-mobile">
        <span class="author-image cover lazy" data-src=".../Ramtin-Rahmani-Nejad-Asil-96x96.jpg"></span>
        <span class="author-name">رامتین رحمانی نژاد</span></a>
      <time class="meta-info" datetime="2026-07-16">16 جولای, 2026</time>
      <div class="min-read"><span class="count">17</span> دقیقه مطالعه</div>
    </div>
    <div class="post-excerpt"><p>{excerpt…}</p></div>
  </div>
</article>
```

Notes:
- Featured image is a **lazy-loaded CSS background** (`data-bg-image`), not an `<img>`; the title (`h1.post-title`) sits **overlaid on the image**, as does the "بیشتر بخوانید" button (`hide-on-mobile`).
- Category links **are** present on the card (e.g. «شبکه», «لینوکس» link to `/category/.../`), rendered as small chips above/around the title area.
- Meta overlay on the image: comment count (links to `{post}#show-comments`), **live view counter** (`95 Views`), read time in minutes.
- Bottom meta: author avatar (96×96, `Ramtin-Rahmani-Nejad-Asil-96x96.jpg`) + name «رامتین رحمانی نژاد» (links to `/author/ramtin-rahmanigmail-com/`), date, «۱۷ دقیقه مطالعه». Excerpt is a plain paragraph (no "[...]" suffix visible).
- Post title `line-height: 200%` (customizer CSS).

### Latest 6 posts on the homepage (2026-11-21)

1. مقایسه OpenConnect و WireGuard و OpenVPN و IPsec؛ کدام VPN برای شما مناسب‌تر است؟ (2026-07-16)
2. معماری OpenConnect: ارتباط بین OpenConnect Client، ocserv و Cisco AnyConnect (2026-07-02)
3. OpenConnect چیست؟ آشنایی با OpenConnect و ocserv قبل از نصب (2026-06-29)
4. دسترسی به سایت‌های ایرانی از خارج از کشور — راهنمای کامل ۱۴۰۵ (2026-06-26)
5. کانتینر در میکروتیک (2026-06-23)
6. Reverse Proxy میکروتیک (2026-06-20)

---

## 3. Category (archive) page

`<body class="rtl archive category category-mikrotik category-3 ...">`, title `بایگانی‌های میکروتیک - رامتین`.

```
<main id="archives" class="main">
  <div class="grid-container grid-medium tag-description section">
    <div class="left grid-35 tablet-grid-45 np-mobile">
      <span class="icon"><svg class="main-color"><use xlink:href="#tag-icon"></use></svg></span>
      <h1 class="title medium no-margin">میکروتیک</h1>
      <div class="total"><span class="dot"></span> 13 مقاله</div>
    </div>
    <div class="right grid-65 tablet-grid-55 np-tablet np-mobile">
      <p>آموزش میکروتیک</p>   ← category description
    </div>
  </div>
  <div class="grid-container module-wrapper grid-large" id="epcl-grid-posts-1">
    <div class="articles grid-posts columns-3"> …cards…
```

- Header: tag icon + `h1` category name + pink dot + «N مقاله» count; description paragraph on the left (in RTL: right column).
- **Different card layout from the homepage: 3-column grid** (`articles grid-posts columns-3`, cards `grid-33 tablet-grid-50 mobile-grid-100`), smaller thumbs (`-600x500.webp`), same card anatomy (featured image, title, meta).
- MikroTik category: 13 posts, 7 on page 1, pagination «صفحه 1 از 3» + «بعدي».
- Same header/footer as the homepage; no sidebar.

---

## 4. Post page (single)

`<body class="rtl ... single single-post postid-1946 single-format-standard ...">`, title `کانتینر در میکروتیک - رامتین`.

Structure inside `.content.row > .epcl-page-wrapper`:

```
<div class="left-content grid-70 np-mobile">     ← NO sidebar on posts (no <aside>; "grid-30" hits in the file are only inside the inlined grid CSS)
  <article class="main-article post-1946 ... category-linux category-mikrotik">
    <header>
      <div class="post-format-image post-format-wrapper">
        <div class="featured-image">
          <div class="epcl-loader">
            <img width="900" height="500" src=".../mikrotik-container-ramtiin.ir_.webp"
                 class="fullwidth wp-post-image no-lazyload" alt="کانتینر در میکروتیک"
                 srcset="... 900w, ...-300x167.webp 300w, ...-768x427.webp 768w" ...>
      <div class="info"><h1 class="main-title title">کانتینر در میکروتیک</h1></div>
      <div class="meta absolute"> comments (0 دیدگاه) · views (26 Views) · min-read (32) </div>
    </header>
    <div class="meta">
      author avatar + رامتین رحمانی نژاد · <time>23 ژوئن, 2026</time> · 32 دقیقه مطالعه
    </div>
    <section class="post-content"><div class="text">
      …content: h2/h3, paragraphs, images, 1 table, 22 code blocks…
    </div></section>
    <div class="tags textcenter"> لینوکس , میکروتیک </div>
    <div class="show-comments textcenter"><button id="show-comments">نمایش دیدگاه ها</button></div>
    <div class="epcl-comments hidden"> …comments + form… </div>
    <div class="share-buttons section np-bottom"> … </div>
    <div class="epcl-border"></div>
    <section id="author" class="author section with-avatar np-bottom"> … </section>
    <section class="related section"> … </section>
    <section class="siblings section"> … </section>
```

Details:
- **Featured image is a real `<img>` here** (900×500, `fetchpriority="high"`, with `srcset` 300/768/900w), unlike the homepage cards' background-image. Title `h1.main-title` sits **below** the image in `.info`; the comments/views/min-read meta is an **absolute overlay** on the image.
- Meta line under the header: author (avatar + name, link to author archive), date, «۳۲ دقیقه مطالعه».
- **Content** (`section.post-content > div.text`): the container post has 58 paragraphs, h2/h3 headings, 1 image, 1 table, **22 code blocks**. Headings in this post: «فهرست:», «Container چیست؟», «تفاوت Container با Virtual Machine», «میکروتیک Container رو از کِی اضافه کرد؟», «پیش‌نیازها و ارتباط شبکه Container میکروتیک», «فعال کردن Container روی MikroTik», «کانفیگ Container در میکروتیک» (h3 steps: `/interface/veth`, `/interface/bridge`, NAT, `/container`), «مثال اول: راه‌اندازی Nginx…», «مثال دوم: راه‌اندازی Uptime Kuma…», «محدودیت‌های کانتینر…», «نکات و ترفندهای کاربردی», «عیب‌یابی…».
- **Code blocks use SyntaxHighlighter:** `<div class="wp-block-syntaxhighlighter-code"><pre class="brush: plain; title: ; notranslate" title="">…` — 22 of them in this post; 144 `<pre>` across all posts. The static rebuild needs equivalent highlighting (same look or a matching replacement).
- **YouTube embeds** in 5 posts (`<iframe src="https://www.youtube.com/embed/…">`).
- **Tags row:** `div.tags.textcenter` — category names as links (e.g. «لینوکس , میکروتیک»).
- **Share buttons** (`.epcl-share-bottom`, circular brand-color buttons, FontAwesome): Facebook (`facebook.com/sharer/sharer.php?u={url}`), Telegram (`t.me/share/url?...`), WhatsApp (`api.whatsapp.com/send?text={url}`), Email (`mailto:?subject={title}&body={url}`). Plus a **permalink copy box:** `<div class="permalink"><input type="text" name="shortlink" value="{post-url}" id="copy-link" readonly aria-label="کپی لینک"><span class="copy"><svg><use xlink:href="#copy-icon"></use></svg></span></div>`.
- **Author box** (`section#author.author.section.with-avatar`): `h3.title.medium.bordered` «درباره نویسنده», avatar, `h4` «رامتین رحمانی نژاد», bio (same text as the footer bio), link «مشاهده تمام مقالات» → author archive.
- **Related posts** (`section.related.section`): heading «شاید دوست داشته باشید» + 3 articles (`article.prev.grid-33 tablet-grid-33 mobile-grid-50`, thumb + title + date). Example: the 3 newest OpenConnect posts.
- **Prev/next** (`section.siblings.section`): heading «سایر نوشته ها»; next article («نوشته بعدی»: «دسترسی به سایت‌های ایرانی از خارج از کشور — راهنمای کامل ۱۴۰۵») and previous («نوشته قبلي»: «Reverse Proxy میکروتیک»), each `article.mask-effect` with lazy thumb + title.

---

## 5. Comments block (static-looking, read-only in the rebuild)

- Comments are **hidden by default**: `<div class="epcl-comments hidden">`, revealed by the «نمایش دیدگاه ها» button (`id="show-comments"`) or by the `#show-comments` anchor used in card meta links (`{post}#show-comments`).
- A post **with** comments (OpenVPN setup post, 38 comments) renders `<ol class="comment-list">` (no pagination — all 38 on one page).
- **One comment item:**
  ```html
  <li class="comment even thread-even depth-1 count-1" id="comment-28">
    <div class="avatar grid-10 tablet-grid-15 mobile-grid-15">
      <img ... src="https://secure.gravatar.com/avatar/{hash}?s=96&d=mm&r=g" class="avatar avatar-96 photo" height="96" width="96"></div>
    <div class="right grid-90 tablet-grid-85 mobile-grid-85">
      <cite class="comment-author">Poria</cite>
      <span class="date">در 29 آوریل, 2022</span>
      <div class="text"><p>برای کانفیگ OpenVPN میکروتیک بهتره یا لینوکس؟</p></div>
      <a rel="nofollow" class="comment-reply-link" href="#comment-28"
         data-commentid="28" data-postid="946" data-replyto="پاسخ به Poria">پاسخ</a>
    </div>
    <ul class="children"> …nested replies… </ul>
  ```
- Avatars: Gravatar (`secure.gravatar.com/avatar/{md5}?s=96&d=mm&r=g`, `d=mm` mystery-man fallback). The author's own replies use his local avatar (`.../Ramtin-Rahmani-Nejad-Asil-96x96.jpg`) and the item carries classes `byuser comment-author-ramtin-rahmanigmail-com bypostauthor`.
- No comments-title heading was found on the commented post; the count appears in the meta («38 دیدگاه») and in the card meta.
- **Comment form** (`#respond`, `h3#reply-title` «دیدگاهتان را بنویسید» + «لغو پاسخ» cancel link), posts to `https://ramtiin.ir/wp-comments-post.php`, fields: `comment` (textarea), `author`, `email`, `url`, `wp-comment-cookies-consent` (checkbox), `submit`; plus Akismet honeypot fields `ak_hp_textarea`, `ak_js`. **This form cannot work on a static site — render the existing 93 comments as static HTML and drop (or visibly disable) the form.**

---

## 6. Pages: contact page + its sidebar

Contact page (`/contact/`, title «تماس با من - رامتین»): `article.main-article.post-43.page`, `section.post-content` contains only the heading «تماس با من» and the form. **Unlike posts, pages DO have a sidebar:**

```
<div class="content no-thumb">
  <div class="epcl-page-wrapper clearfix row">
    <div class="left-content grid-70 np-mobile"> <article …page…> … </article></div>
    <aside class="grid-30 no-sidebar sticky-enabled">
      <div class="sidebar-wrapper default-sidebar">
        <section class="widget widget_epcl_posts_thumbs">  ← latest posts with thumbnails (4 items)
        <section class="widget widget_epcl_social">        ← social icons
        <section class="widget widget_recent_comments">    ← recent comments
```

`no-sidebar` means no custom sidebar is assigned, so these three **default widgets** render. (Post pages have no `<aside>` at all.)

### Contact form (Contact Form 7, form ID 582, v6.1.6)

`<form action="/contact/#wpcf7-f582-p43-o1" method="post" class="wpcf7-form init" aria-label="Contact form" novalidate>`. Fields (all placeholders, no visible `<label>` text):
- `your-name` — text, required, placeholder «نام شما *»
- `your-email` — email, required, placeholder «ایمیل شما *»
- `your-subject` — text, required, placeholder «موضوع»
- `your-message` — textarea (rows 10, maxlength 2000), placeholder «متن پیام»
- submit button «ارسال»
- Hidden: `_wpcf7=582`, `_wpcf7_version=6.1.6`, `_wpcf7_locale=en_US`, `_wpcf7_unit_tag=wpcf7-f582-p43-o1`, `_wpcf7_container_post=43`, `_wpcf7_recaptcha_response` (empty), Akismet `_wpcf7_ak_hp_textarea`, `_wpcf7_ak_js`.
- **CF7 is server-side — the static rebuild must replace it** (form backend such as Formspree, or a mailto/Telegram link). The recipient address is not visible in the HTML (CF7 mail settings live in the admin).

### Search (header lightbox)

`<div id="search-lightbox" class="mfp-hide grid-container grid-small grid-parent">` with `h4.title` «برای بستن ESC را فشار دهید» and:
```html
<form action="https://ramtiin.ir/" method="get" class="search-form">
  <input type="text" name="s" id="s" class="search-field"
         placeholder="برای شروع جستجو تایپ کنید ..." required>
  <button type="submit" class="submit" aria-label="تایید">
    <svg class="icon main-color"><use xlink:href="#search-icon"></use></svg></button>
</form>
```
WordPress search (`?s=query`). **Static replacement needed** (client-side search index, same pattern as ramtin.zone).

---

## 7. Sidebar widgets (summary) and footer

**Sidebar widgets** (only on pages like Contact; posts and homepage have none):
- Latest posts with thumbnails (`widget_epcl_posts_thumbs`, 4 items: thumb + title + date)
- Social icons (`widget_epcl_social`)
- Recent comments (`widget_recent_comments`)

**Footer** (`<footer id="footer">`, `margin-top:50px`): a `.widgets.grid-container.grid-large > .row.large` with **3 widgets** (`grid-25 tablet-grid-50 mobile-grid-100` each):

1. **دسته بندی ها** (`section.widget_tag_cloud` — despite the class, it lists categories, linking to `/category/{slug}/`): DevOps, OpenWrt, VOIP, ترفند, دسته بندی نشده, شبکه, لینوکس, میکروتیک, ویندوز (9 links).
2. **فهرست** (`section.widget_nav_menu`, menu «فوتر»): صفحه اصلی (`href="#"` — note: literal `#`, not `/`), دوره‌های آموزش میکروتیک, درباره من, تماس با من, حمایت مالی, پشتیبانی شبکه (→ `/پشتیبانی-شبکه-در-شیراز/`).
3. **درباره من** (`section.widget_epcl_about`): avatar + name «رامتین رحمانی نژاد» (link to author archive) + bio + social icons. Bio text (identical in the author box):
   > «رامتین رحمانی نژاد از سال 1385 در حوزه آی‌تی و شبکه فعالیت می‌کنم. در راه اندازی و پشتیبانی شبکه‌ و سرویس‌های مایکروسافت، لینوکس، سیسکو، میکروتیک، VOIP، ارتباطات رادیویی و مدیریت سرور تخصص دارم. برای مشاوره، اجرای پروژه و پشتیبانی شبکه با من تماس بگیرین :)»

Footer bottom: logo `<h2 class="logo"><a href="https://ramtiin.ir/" class="title ularge no-margin"> رامتین<span class="dot"></span></a></h2>`, then `<div class="published"><a href="https://wordpress.org/" target="_blank" rel="noopener">با افتخار قدرت گرفته از وردپرس</a></div>`, then `<a id="back-to-top" class="button ...">` (back-to-top button). **No subscribe/newsletter form is rendered** (only the unused `#footer .subscribe{background:#252A40}` CSS rule). No other copyright line.

---

## 8. Dynamic things a static rebuild must replace or drop

| Live behaviour | Static handling |
|---|---|
| WordPress search `GET /?s=query` (lightbox form) | Replace with a client-side search index (same approach as ramtin.zone) |
| Comment form → `POST /wp-comments-post.php` (+ Akismet `ak_hp_textarea`/`ak_js`) | Drop the form. Render the existing 93 comments as static HTML in the exact item structure above (avatar, `<cite class="comment-author">`, date «در …», text, «پاسخ» link kept as a visual element only). Comments stay hidden until «نمایش دیدگاه ها» / `#show-comments` |
| Contact Form 7 → `POST /contact/#wpcf7-f582-p43-o1` | Replace with a form backend (e.g. Formspree) or mailto/Telegram link; keep the 4 fields + «ارسال» |
| Live view counter («95 Views», «26 Views» in card/post meta) | Dynamic per-view count — freeze at migration-time value or drop |
| «{N} دقیقه مطالعه» read time | Computable statically from word count (keep the same numbers) |
| Gravatar avatars (`secure.gravatar.com/avatar/{md5}?s=96&d=mm&r=g`) | Keep as external images, or download at build time |
| Lazy-load (`lazyload`/`data-bg-image`/`data-src`, Smush placeholders) | Replace with native `loading="lazy"` or keep the same classes with a small JS shim |
| Sticky header, mobile menu toggle, search lightbox (Magnific Popup), back-to-top, copy-link button, show/hide comments | Small vanilla JS (or the theme's own `plugins.min.js` equivalent) |
| WP Fastest Cache minified bundles (`/wp-content/cache/wpfc-minified/*/ab97f.css`) | Do not copy — rebuild from the theme CSS (`style.min.css`, `rtl.css`, `fonts.css`, customizer block) |
| RSS feeds (`/feed/`, `/comments/feed/`, author feed) | Generate static RSS |
| «با افتخار قدرت گرفته از وردپرس» footer line | Goes away with WordPress (replace with nothing, or the site's own line — Ramtin's call) |
| WPBakery (`vc_responsive`, `wpb-js-composer`) page-builder markup on pages | Pages are simple (contact = heading + form); rebuild as plain HTML |
| Yoast SEO sitemaps (`/sitemap_index.xml`, post/page/category sitemaps) + meta tags | Generate a static sitemap + keep the same `<title>` / meta description pattern (`{title} - رامتین`, description «پشتیبانی شبکه» on home) |

## 9. URL inventory (for the "no link changes" requirement)

- Home: `https://ramtiin.ir/` · pagination `/page/N/` (8 pages)
- Posts: `https://ramtiin.ir/{slug}/` — slug-only, no date prefix (48 posts)
- Pages: `/آموزش-میکروتیک/`, `/پشتیبانی-تلفن-ویپ/`, `/راه-اندازی-شبکه-در-شیراز/`, `/پشتیبانی-شبکه-در-شیراز/`, `/مشارکت-در-ترجمه-کتاب-comptia-serverplus/`, `/donate/`, `/درباره-من/`, `/contact/`
- Categories: `/category/{devops,openwrt,voip,tricks,uncategorized,network,linux,mikrotik,windows}/` (+ رادیو-ترمینال, 0 posts)
- Author: `/author/ramtin-rahmanigmail-com/`
- Feeds: `/feed/`, `/comments/feed/`
- Anchor used across the site: `{post}#show-comments`
