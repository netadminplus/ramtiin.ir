#!/usr/bin/env python3
"""Static generator for ramtiin.ir — faithful rebuild of the WordPress site (Veen 2.2.0).

Reads the inventory JSONs in ~/workspace/ramtiin-migration/ and emits a static
site into ./site/ with IDENTICAL URLs, content, and SEO metadata — no WordPress.
Run:  python3 build.py
"""
import json, re, os, html, shutil, sys
from datetime import datetime
from urllib.parse import unquote, quote
from xml.sax.saxutils import escape as xml_escape

BASE = os.path.dirname(os.path.abspath(__file__))
MIG = os.path.dirname(BASE) if os.path.basename(BASE) == 'site' else BASE
# When run from the migration folder, BASE == MIG; site output goes to BASE/site
SRC = BASE if os.path.exists(os.path.join(BASE, 'posts.json')) else os.path.join(BASE, 'ramtiin-migration')
OUT = os.path.join(BASE, 'site')
SITE_URL = 'https://ramtiin.ir'

def load(name):
    with open(os.path.join(SRC, name), encoding='utf-8') as f:
        return json.load(f)

posts = load('posts.json')          # 48, newest first
pages = load('pages.json')          # 8
categories = load('categories.json')
tags = load('tags.json')            # 88
comments = load('comments.json')    # 93
media_urls = load('media_urls.json')  # id(str) -> source_url (216)
yoast_posts = load('yoast_posts.json')
yoast_pages = load('yoast_pages.json')
post_meta = load('post_meta.json')  # views / read_mins / related / siblings
comment_avatars = load('comment_avatars.json')

# id -> relative uploads path (for existence checks + local file mapping)
MEDIA_BY_ID = {str(k): v.replace('https://ramtiin.ir/', '') for k, v in media_urls.items()}
MEDIA_PATHS = set()
for _root, _dirs, _files in os.walk(os.path.join(SRC, 'media', 'wp-content', 'uploads')):
    for _fn in _files:
        MEDIA_PATHS.add(os.path.relpath(os.path.join(_root, _fn), os.path.join(SRC, 'media')))

FA_JALALI_MONTHS = ['فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
                    'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند']
FA_DIGITS = '۰۱۲۳۴۵۶۷۸۹'

def fa_digits(s):
    """Latin digits -> Persian digits ('2026' -> '۲۰۲۶')."""
    return ''.join(FA_DIGITS[int(ch)] if ch.isdigit() else ch for ch in str(s))

def gregorian_to_jalali(gy, gm, gd):
    """Standard Gregorian -> Jalali conversion (Pournader algorithm).
    Verified against the Figma design's dates, which Figma read from the
    live site: 2026-07-16 -> 25 Tir 1405, 2026-06-20 -> 30 Khordad 1405,
    2021-10-16 -> 24 Mehr 1400, 2026-11-21 -> 30 Aban 1405."""
    g_d_m = [0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334]
    if gy > 1600:
        jy = 979
        gy -= 1600
    else:
        jy = 0
        gy -= 621
    gy2 = gy + 1 if gm > 2 else gy
    days = (365 * gy + (gy2 + 3) // 4 - (gy2 + 99) // 100 + (gy2 + 399) // 400
            - 80 + gd + g_d_m[gm - 1])
    jy += 33 * (days // 12053)
    days %= 12053
    jy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        jy += (days - 1) // 365
        days = (days - 1) % 365
    if days < 186:
        jm = 1 + days // 31
        jd = 1 + days % 31
    else:
        jm = 7 + (days - 186) // 30
        jd = 1 + (days - 186) % 30
    return jy, jm, jd

def fa_date(iso, prefix=''):
    """'2026-07-16T...' -> '۲۵ تیر ۱۴۰۵' (Jalali, Persian digits).
    The old WP fa_IR style ('16 جولای, 2026') is gone: the Figma design
    uses Jalali dates everywhere, and the design is the spec now. The
    machine-readable date stays ISO in datetime attributes / feeds."""
    d = datetime.fromisoformat(iso.replace('Z', '+00:00')) if 'T' in iso else datetime.strptime(iso[:10], '%Y-%m-%d')
    jy, jm, jd = gregorian_to_jalali(d.year, d.month, d.day)
    return f"{prefix}{fa_digits(jd)} {FA_JALALI_MONTHS[jm - 1]} {fa_digits(jy)}"

def plain_text(html_s):
    t = re.sub(r'<[^>]+>', ' ', html_s or '')
    return html.unescape(re.sub(r'\s+', ' ', t)).strip()

def slug_path(slug):
    """Percent-encoded WP slug -> decoded path segment (as served on disk)."""
    return unquote(slug)

THUMB_RE = re.compile(r'-\d+x\d+(?=\.[A-Za-z0-9]+$)')

def original_uploads_url(url):
    """Map any wp-content/uploads URL (incl. -300x233 thumbnails) to its original file."""
    if 'wp-content/uploads/' not in url:
        return url
    base = url.split('?')[0]
    rel = base.replace('https://ramtiin.ir/', '')
    if rel in MEDIA_PATHS:
        return base
    stem = THUMB_RE.sub('', base)
    stem_rel = stem.replace('https://ramtiin.ir/', '')
    if stem_rel in MEDIA_PATHS:
        return stem
    # Some originals differ only by extension case or a trailing dot quirk; try harder:
    return base  # keep as-is; the verifier will flag it

def rewrite_uploads(html_s):
    """Rewrite every uploads URL in a chunk of HTML to its original file."""
    def rep(m):
        return original_uploads_url(m.group(0))
    return re.sub(r'https://ramtiin\.ir/wp-content/uploads/[^"\'\s<>)]+', rep, html_s)

def _vc_attr(attrs, name):
    """Read one attribute from a WPBakery shortcode tag: attribute quotes in
    the export are " or &#8221;/&#8243; (curly-quote entities)."""
    attrs = attrs.replace('&#8221;', '"').replace('&#8243;', '"').replace('&quot;', '"')
    m = re.search(r'%s="([^"]*)"' % re.escape(name), attrs)
    return html.unescape(m.group(1)) if m else ''

def _strip_wpbakery(h):
    """WPBakery pages ship raw [vc_*] shortcodes as visible text. The
    generator normalises them: tags are removed, inner text stays.
    vc_single_image -> real <img> (every attachment ID resolves via
    media_urls.json); vc_btn -> real button; vc_empty_space -> spacer;
    vc_separator -> <hr>. Anything else vc_* drops as a tag only."""
    def _btn(m):
        title = _vc_attr(m.group(1), 'title')
        link = _vc_attr(m.group(1), 'link')  # url:URL|title:...|target:_blank
        url = ''
        mm = re.search(r'url:([^|]+)', link)
        if mm:
            url = unquote(mm.group(1))
        if not url or not title:
            return ''
        return '<a class="epcl-button" href="%s" target="_blank" rel="noopener">%s</a>' % (
            html.escape(url, quote=True), html.escape(title))
    def _img(m):
        mid = _vc_attr(m.group(1), 'image')
        src = MEDIA_BY_ID.get(mid or '')
        if not src:
            return ''
        return '<img src="%s" alt="" loading="lazy">' % html.escape(src, quote=True)
    def _space(m):
        height = _vc_attr(m.group(1), 'height') or '32px'
        return '<span style="display:block;height:%s" aria-hidden="true"></span>' % html.escape(height, quote=True)
    h = re.sub(r'\[vc_btn([^\]]*)\]', _btn, h)
    h = re.sub(r'\[vc_single_image([^\]]*)\]', _img, h)
    h = re.sub(r'\[vc_empty_space([^\]]*)\]', _space, h)
    h = re.sub(r'\[vc_separator[^\]]*\]', '<hr>', h)
    # every other vc_* tag (vc_row, vc_column, vc_column_text, closers):
    # drop the tag, keep the text inside
    h = re.sub(r'\[/?vc_[^\]]*\]', '', h)
    return h

def _strip_inline_colors(h):
    """Content never sets its own colours — the design system owns colour.
    Strips color: declarations from inline styles (the old #00ccff blue
    headings came from WP); keeps everything else (e.g. background-image)."""
    def _clean(m):
        style = m.group(1)
        if 'color' not in style:
            return m.group(0)
        style = re.sub(r'(?:^|;)\s*color\s*:[^;]+;?', '', style).strip().strip(';').strip()
        return (' style="%s"' % style) if style else ''
    return re.sub(r'\sstyle="([^"]*)"', _clean, h)

def clean_content(html_s):
    """Make WP-rendered post content static-safe, preserving everything visible."""
    h = html_s or ''
    # WPBakery shortcodes + inline colours are normalised first, so the
    # URLs generated below get rewritten like everything else.
    h = _strip_wpbakery(h)
    h = _strip_inline_colors(h)
    # empty paragraphs left behind by stripped shortcode tags
    h = re.sub(r'<p>(\s|<br\s*/?>)*</p>', '', h)
    # a paragraph holding a single code-like value (hostname, IP, file
    # name, registry key, password) is code the reader copies — render
    # it as a code block so it gets the code styling + copy button.
    def _code_para(m):
        tok = m.group(2).strip()
        # a dot, underscore, slash or colon marks a hostname, IP, file
        # name, path or URL — a bare product/model name (OpenVPN,
        # RB951Ui-2HnD) has none of these and stays a plain paragraph.
        if (tok and re.fullmatch(r'[A-Za-z0-9._/:-]+', tok)
                and ('.' in tok or '_' in tok or '/' in tok or ':' in tok)):
            return '<pre>' + tok + '</pre>'
        return m.group(0)
    h = re.sub(r'(<p[^>]*>)([^<]+)(</p>)', _code_para, h)
    # lazy images: src="transparent.gif" data-src="REAL" -> src="REAL"
    h = re.sub(r'src="[^"]*transparent\.gif"([^>]*?)data-src="([^"]+)"', r'src="\2"\1', h)
    h = re.sub(r'data-src="([^"]+)"', r'src="\1"', h)
    # drop srcset / data-srcset (they point at WP thumbnails)
    h = re.sub(r'\s+srcset="[^"]*"', '', h)
    h = re.sub(r'\s+data-srcset="[^"]*"', '', h)
    h = re.sub(r'\s+data-lazy="[^"]*"', '', h)
    h = re.sub(r'<table[\s\S]*?</table>', lambda m: '<div class="table-wrap">' + m.group(0) + '</div>', h)
    h = rewrite_uploads(h)
    h = fix_internal_links(h)
    return h

KNOWN_URLS = set()
for _p in posts:
    KNOWN_URLS.add('/' + slug_path(_p['slug']) + '/')
for _pg in pages:
    KNOWN_URLS.add('/' + slug_path(_pg['slug']) + '/')
for _c in categories:
    KNOWN_URLS.add('/category/' + _c['slug'] + '/')
for _t in tags:
    KNOWN_URLS.add('/tag/' + _t['slug'] + '/')
KNOWN_URLS.add('/author/ramtin-rahmanigmail-com/')
KNOWN_URLS.add('/')
KNOWN_URLS.add('/search/')

def fix_internal_links(html_s):
    """Repair hand-typed internal links whose slug differs from the real one:
    ZWNJ differences, or a small typo (e.g. an extra '-به-'). Such links 404 on
    live WP too; a >=0.90 difflib match to a real URL is the same slug mistyped."""
    import difflib
    def rep(m):
        href = m.group(1)
        if href.startswith(('https://ramtiin.ir/', '/')) and '/wp-content/' not in href and '/assets/' not in href:
            path = href.replace('https://ramtiin.ir', '')
            base, sep, tail = path.partition('#')
            base2, qsep, query = base.partition('?')
            dec = unquote(base2)
            if dec not in KNOWN_URLS:
                if dec + '/' in KNOWN_URLS:
                    return 'href="' + dec + '/' + qsep + query + sep + tail + '"'
                fixed = dec.replace('\u200c', '')
                if fixed in KNOWN_URLS:
                    print(f'  fixed link: {href} -> {fixed}{qsep}{query}{sep}{tail}')
                    return 'href="' + fixed + qsep + query + sep + tail + '"'
                best = difflib.get_close_matches(dec, KNOWN_URLS, n=1, cutoff=0.90)
                if best:
                    print(f'  fixed link: {href} -> {best[0]}{qsep}{query}{sep}{tail}')
                    return 'href="' + best[0] + qsep + query + sep + tail + '"'
        return m.group(0)
    return re.sub(r'href="([^"]+)"', rep, html_s)

def yoast_head_for(kind, slug):
    """Yoast <head> block for a post/page, with uploads URLs rewritten to originals."""
    src = yoast_posts if kind == 'post' else yoast_pages
    head = src.get(slug, '') or ''
    # Yoast descriptions were generated from raw WP content, so the
    # WPBakery pages carry [vc_*] text in og:description too — same class
    # of defect as the visible shortcodes, fixed at the same layer.
    head = re.sub(r'\[/?vc_[^\]]*\]', '', head)
    return rewrite_uploads(head)

def head_html(title_text, yoast_head, extra=''):
    """Shared <head>: Yoast block verbatim + the Figma design system + favicon + RSS.
    The old Veen theme CSS (style.min.css, rtl.css, customizer.css,
    font-awesome) and SyntaxHighlighter are NOT loaded anymore — static.css
    (the Figma port) is the entire design system, icons are inline SVG."""
    return f"""<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{yoast_head}
<link rel="icon" href="/wp-content/uploads/2021/10/cropped-favicon-ramtiin.ir_.png" sizes="32x32">
<link rel="icon" href="/wp-content/uploads/2021/10/cropped-favicon-ramtiin.ir_.png" sizes="192x192">
<link rel="apple-touch-icon" href="/wp-content/uploads/2021/10/cropped-favicon-ramtiin.ir_.png">
<link rel="stylesheet" href="/assets/css/static.css">
<link rel="alternate" type="application/rss+xml" title="رامتین" href="/feed/">
{extra}"""

BIO = ('رامتین رحمانی نژاد از سال 1385 در حوزه آی‌تی و شبکه فعالیت می‌کنم. در راه اندازی و پشتیبانی شبکه‌ و سرویس‌های '
       'مایکروسافت، لینوکس، سیسکو، میکروتیک، VOIP، ارتباطات رادیویی و مدیریت سرور تخصص دارم. برای مشاوره، اجرای پروژه '
       'و پشتیبانی شبکه با من تماس بگیرین :)')

# Author-box bio (live site): same text without the name prefix — the name is
# already the box heading.
BIO_SHORT = ('از سال 1385 در حوزه آی‌تی و شبکه فعالیت می‌کنم. در راه اندازی و پشتیبانی شبکه‌ و سرویس‌های '
             'مایکروسافت، لینوکس، سیسکو، میکروتیک، VOIP، ارتباطات رادیویی و مدیریت سرور تخصص دارم. برای مشاوره، اجرای پروژه '
             'و پشتیبانی شبکه با من تماس بگیرین :)')

# Header menu — EXACTLY the WordPress menu (order, parents, children, labels),
# recovered from the saved WP-rendered HTML (pages_html/). Two dropdown parents:
# خدمات (3 children) and رامتین (3 children: درباره من، تماس با من، حمایت مالی).
# One deliberate difference from WP: «تماس با من» points to /درباره-من/#contact
# instead of /contact/ — /contact/ was removed 23 Nov 2026 by Ramtin's decision
# and now redirects there.
NAV = [
    ('صفحه اصلی', '/'),
    ('دوره‌های آموزش میکروتیک', '/آموزش-میکروتیک/'),
    ('میکروتیک', '/category/mikrotik/'),
    ('لینوکس', '/category/linux/'),
    ('ویندوز', '/category/windows/'),
    ('VOIP', '/category/voip/'),
    ('ترفند', '/category/tricks/'),
    ('خدمات', '#', [('پشتیبانی شبکه در شیراز', '/پشتیبانی-شبکه-در-شیراز/'),
                    ('راه‌اندازی شبکه در شیراز', '/راه-اندازی-شبکه-در-شیراز/'),
                    ('پشتیبانی تلفن ویپ', '/پشتیبانی-تلفن-ویپ/')]),
    ('رامتین', '#', [('درباره من', '/درباره-من/'),
                     ('تماس با من', '/درباره-من/#contact'),
                     ('حمایت مالی', '/donate/')]),
]

# Inline SVG icons (Figma's Icon set — the theme's Font Awesome + SVG sprite
# are gone; every icon is drawn here so nothing depends on an icon font).
ICON_PATHS = {
    'search': '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'close': '<path d="m6 6 12 12M18 6 6 18"/>',
    'arrow': '<path d="M19 12H5M11 18l-6-6 6-6"/>',
    'chevron': '<path d="m6 9 6 6 6-6"/>',
    'clock': '<circle cx="12" cy="12" r="8.5"/><path d="M12 7v5l3 2"/>',
    'instagram': '<rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/><path d="M17.5 6.5h.01"/>',
    'linkedin': '<path d="M7 9v9M7 6.5v.01M11 18v-5c0-2 1-3.5 3.2-3.5 2 0 2.8 1.5 2.8 3.5v5M11 10v8"/>',
    'youtube': '<path d="M21 12c0 3.7-.4 5.6-1.3 6.2-.9.6-3.4.8-7.7.8s-6.8-.2-7.7-.8C3.4 17.6 3 15.7 3 12s.4-5.6 1.3-6.2C5.2 5.2 7.7 5 12 5s6.8.2 7.7.8c.9.6 1.3 2.5 1.3 6.2Z"/><path d="m10 9 5 3-5 3Z"/>',
    'telegram': '<path d="m21 4-3 16-6-4-3 2v-4l8-7-10 6-4-2Z"/>',
    'mail': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m4 7 8 6 8-6"/>',
    'send': '<path d="m4 12 16-8-5 16-3-6Z"/><path d="m12 14 8-10"/>',
    'check': '<path d="m5 12 4 4L19 6"/>',
}

def icon(name, size=20):
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICON_PATHS[name]}</svg>')

def socials_html(muted=False):
    cls = 'socials socials-muted' if muted else 'socials'
    return f'''<div class="{cls}">
<a href="https://www.linkedin.com/in/ramtin-rahmani" target="_blank" rel="noreferrer" aria-label="لینکدین">{icon('linkedin')}</a>
<a href="https://instagram.com/ramtiin.ir" target="_blank" rel="noreferrer" aria-label="اینستاگرام">{icon('instagram')}</a>
<a href="https://www.youtube.com/c/netadminplus" target="_blank" rel="noreferrer" aria-label="یوتیوب">{icon('youtube')}</a>
<a href="https://t.me/netadminplus" target="_blank" rel="noreferrer" aria-label="تلگرام">{icon('telegram')}</a>
</div>'''

# Desktop nav: dropdown parents render as hover/focus/click dropdowns (WP
# behaviour — the Figma flat nav dropped them, which hid 4 links on desktop).
# The drawer walks NAV in order, parents as group labels, children indented.
def desktop_nav_html(current=''):
    parts = []
    for e in NAV:
        if len(e) == 2:
            label, href = e
            parts.append(f'<a href="{href}">{label}</a>')
        else:
            label, _href, subs = e
            subs_html = ''.join(f'<a href="{h}">{l}</a>' for l, h in subs)
            parts.append(
                f'<span class="nav-drop"><button type="button" class="nav-parent" aria-haspopup="true" aria-expanded="false">{label}{icon("chevron", 14)}</button>'
                f'<span class="nav-sub">{subs_html}</span></span>')
    return f'<nav class="desktop-nav" aria-label="منوی اصلی">{''.join(parts)}</nav>'

def drawer_links_html():
    parts = []
    for e in NAV:
        if len(e) == 2:
            label, href = e
            parts.append(f'<a href="{href}" data-close-drawer>{label}</a>')
        else:
            label, _href, subs = e
            parts.append(f'<span class="drawer-group">{label}</span>')
            for l, h in subs:
                parts.append(f'<a href="{h}" data-close-drawer class="drawer-sub">{l}</a>')
    return ''.join(parts)

def header_html(current=''):
    drawer_links = drawer_links_html()
    return f"""<div class="topline"><div class="shell topline-inner"><span>راهنمای کاربردی برای دنیای شبکه و دواپس</span>{socials_html(muted=True)}</div></div>
<header class="site-header"><div class="shell header-inner">
<a class="brand" href="/" aria-label="رامتین، صفحه اصلی">رامتین<span>.</span></a>
{desktop_nav_html(current)}
<div class="header-actions">
<button class="icon-button search-button" data-open-search aria-label="باز کردن جست‌وجو">{icon('search')}</button>
<button class="icon-button menu-button" data-open-drawer aria-label="باز کردن منو">{icon('menu', 23)}</button>
</div></div></header>
<div class="overlay" data-close-drawer></div>
<aside class="drawer" aria-label="منو">
<div class="drawer-head">
<a class="brand" href="/" data-close-drawer>رامتین<span>.</span></a>
<button class="icon-button" data-close-drawer aria-label="بستن منو">{icon('close')}</button>
</div>
<nav class="drawer-nav">{drawer_links}</nav>
<div class="drawer-foot"><p>رامتین رحمانی‌نژاد</p>{socials_html()}</div>
</aside>
<div class="search-modal" role="dialog" aria-modal="true" aria-label="جست‌وجو">
<button class="search-backdrop" data-close-search aria-label="بستن جست‌وجو"></button>
<form class="search-panel" action="/search/" method="get">
<button type="button" class="icon-button search-close" data-close-search aria-label="بستن">{icon('close')}</button>
<label for="search">دنبال چه موضوعی می‌گردید؟</label>
<div class="search-field"><input id="search" name="q" aria-label="جست‌وجو" placeholder="مثلاً آموزش میکروتیک..."><button type="submit" aria-label="جست‌وجو">{icon('search')}</button></div>
<p>پیشنهاد: میکروتیک، OpenConnect، لینوکس، VPN</p>
</form></div>"""

# Footer quick links — the WordPress footer menu (exact labels, WP order).
# (WP's home link there was a literal '#'; '/' is the correct href.)
FOOTER_QUICK = [
    ('صفحه اصلی', '/'),
    ('دوره‌های آموزش میکروتیک', '/آموزش-میکروتیک/'),
    ('درباره من', '/درباره-من/'),
    ('تماس با من', '/درباره-من/#contact'),
    ('حمایت مالی', '/donate/'),
    ('پشتیبانی شبکه', '/پشتیبانی-شبکه-در-شیراز/'),
]

def footer_html():
    cats = [CAT_BY_SLUG[s] for s in ('mikrotik', 'linux', 'network', 'tricks') if s in CAT_BY_SLUG]
    topic_links = ''.join(f'<a href="{cat_url(c)}">{c["name"]}</a>' for c in cats)
    quick_links = ''.join(f'<a href="{h}">{l}</a>' for l, h in FOOTER_QUICK)
    now = datetime.now()
    jy = gregorian_to_jalali(now.year, now.month, now.day)[0]
    return f"""<footer><div class="shell footer-grid">
<section class="footer-about">
<a class="brand brand-light" href="/">رامتین<span>.</span></a>
<p>یادداشت‌ها و آموزش‌های کاربردی درباره شبکه و دواپس.</p>
{socials_html()}
</section>
<section><h3>دسترسی سریع</h3>{quick_links}</section>
<section><h3>موضوعات</h3>{topic_links}</section>
</div>
<div class="shell footer-bottom"><p>© {fa_digits(jy)} رامتین رحمانی‌نژاد — همه حقوق محفوظ است.</p><p>ساخته‌شده برای انتقال تجربه</p></div></footer>
<script src="/assets/js/site.js"></script>"""

def page_shell(title, yoast_head, body, body_class='rtl'):
    return ('<!DOCTYPE html>\n<html dir="rtl" lang="fa-IR" prefix="og: http://ogp.me/ns#">\n<head>\n'
            + head_html(title, yoast_head) +
            f'\n</head>\n<body class="{body_class}">\n'
            + header_html() + '\n' + body + '\n' + footer_html() + '\n</body>\n</html>\n')

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8') as f:
        f.write(content)
    return full

# ---------------- data helpers ----------------
POSTS_BY_ID = {p['id']: p for p in posts}
POSTS_BY_LINK = {p['link']: p for p in posts}
CAT_BY_ID = {c['id']: c for c in categories}
CAT_BY_SLUG = {c['slug']: c for c in categories}
COMMENTS_BY_POST = {}
for _c in comments:
    COMMENTS_BY_POST.setdefault(_c['post'], []).append(_c)
for _lst in COMMENTS_BY_POST.values():
    _lst.sort(key=lambda c: c['date'])

def post_url(p):
    return '/' + slug_path(p['slug']) + '/'

def cat_url(c):
    return '/category/' + c['slug'] + '/'

def tag_url(t):
    return '/tag/' + t['slug'] + '/'

def comment_count(pid):
    return len(COMMENTS_BY_POST.get(pid, []))

def views_of(p):
    m = post_meta.get(str(p['id']), {})
    return m.get('views') or 0

def read_mins_of(p):
    m = post_meta.get(str(p['id']), {})
    r = m.get('read_mins') or []
    return r[0] if r else max(1, len(plain_text(p['content']['rendered']).split()) // 200)

def featured_url(p):
    mid = p.get('featured_media')
    if mid and str(mid) in MEDIA_BY_ID:
        return '/' + MEDIA_BY_ID[str(mid)]
    return ''

def excerpt_of(p):
    return plain_text(p['excerpt']['rendered'])

def cat_chips(p):
    """One chip component for every category: same tinted pill everywhere.
    The old per-category background colors are gone on purpose — 7 arbitrary
    colours (pink/yellow/green…) failed contrast with any text colour and
    made chips unreadable (white on yellow, dark on pink). The per-category
    class (ctag-N) is gone too: customizer.css colours it with !important
    and the chips on cards stayed yellow/green despite the unified rule."""
    out = []
    for cid in p.get('categories', []):
        c = CAT_BY_ID.get(cid)
        if not c:
            continue
        out.append(f'<a href="{cat_url(c)}" class="ctag">{c["name"]}</a>')
    return ''.join(out)

AVATAR = '/wp-content/uploads/2021/10/Ramtin-Rahmani-Nejad-Asil.jpg'
# About hero photo (23 Nov 2026): Ramtin with his cats Jose + Enzo, from
# ramtin.zone. About-only — the post author boxes keep AVATAR.
ABOUT_PHOTO = '/wp-content/uploads/2021/10/ramtin-jose-enzo-netadminhub.com_-768x1024.webp'
AUTHOR_URL = '/author/ramtin-rahmanigmail-com/'

def card_html(p, index=0, grid=False):
    """Figma PostCard: image, one category chip, title, 2-line excerpt,
    date + read time, read-more link. Cards in a row are the same height
    (CSS grid + flex column); the chip is the FIRST category only — the
    design has one chip per card. Dates are Jalali (fa_date)."""
    feat = featured_url(p)
    url = post_url(p)
    mins = read_mins_of(p)
    cats = [CAT_BY_ID[cid] for cid in p.get('categories', []) if cid in CAT_BY_ID]
    chip = f'<a class="chip" href="{cat_url(cats[0])}">{cats[0]["name"]}</a>' if cats else ''
    return f"""<article class="post-card">
<a href="{url}" class="card-image"><img src="{feat}" alt="{html.escape(plain_text(p['title']['rendered']))}" loading="lazy"><span class="image-arrow">{icon('arrow')}</span></a>
<div class="card-body">
{chip}
<h3><a href="{url}">{p['title']['rendered']}</a></h3>
<p class="excerpt">{html.escape(excerpt_of(p))}</p>
<div class="card-meta"><time datetime="{p['date'][:10]}">{fa_date(p['date'])}</time><span>{icon('clock', 16)}{fa_digits(mins)} دقیقه مطالعه</span></div>
<a class="read-more" href="{url}">ادامه مطلب {icon('arrow', 17)}</a>
</div></article>"""

def pagination_html(base, page, total_pages):
    """Figma pagination: 39px squares, current = accent fill, Persian
    digits, 'صفحه بعد' / 'صفحه قبل' pills. Same collapsing range logic
    as before ([prev] 1 … c-1 [c] c+1 … N [next]) so it stays one row.
    The prev arrow is flipped (RTL: previous points right)."""
    def href(n):
        return base if n == 1 else f"{base}page/{n}/"
    def num(n):
        if n == page:
            return f'<span class="active" aria-current="page">{fa_digits(n)}</span>'
        return f'<a href="{href(n)}">{fa_digits(n)}</a>'
    shown = sorted(set([1, total_pages] + [n for n in (page - 1, page, page + 1) if 1 <= n <= total_pages]))
    parts = []
    if page > 1:
        parts.append(f'<a href="{href(page - 1)}" class="next prev" aria-label="صفحه قبلی">صفحه قبل {icon("arrow", 17)}</a>')
    prev_n = 0
    for n in shown:
        if prev_n and n - prev_n > 1:
            parts.append('<span aria-hidden="true">…</span>')
        parts.append(num(n))
        prev_n = n
    if page < total_pages:
        parts.append(f'<a href="{href(page + 1)}" class="next" aria-label="صفحه بعدی">صفحه بعد {icon("arrow", 17)}</a>')
    return '<nav class="pagination" aria-label="صفحه‌بندی">' + ''.join(parts) + '</nav>'

def comments_html(post):
    """Figma comments: heading 'دیدگاه‌ها (n)' + the real list, shown
    directly (no show/hide toggle — the design shows them). Nested
    replies are indented. The static site takes no new comments, so the
    empty state says so instead of offering a dead button."""
    items = COMMENTS_BY_POST.get(post['id'], [])
    by_parent = {}
    for c in items:
        by_parent.setdefault(c.get('parent', 0), []).append(c)

    def render_list(parent, depth):
        cls = 'comment-list' if depth == 1 else 'comment-children'
        out = [f'<ol class="{cls}">']
        for c in by_parent.get(parent, []):
            cid = str(c['id'])
            avatar = original_uploads_url(comment_avatars.get(cid, 'https://secure.gravatar.com/avatar/00000000000000000000000000000000?s=96&d=mm&r=g'))
            author = html.escape(c.get('author_name', ''))
            date_s = fa_date(c['date'], prefix='در ')
            text = c['content']['rendered']
            kids = render_list(c['id'], depth + 1) if by_parent.get(c['id']) else ''
            out.append(f"""<li class="comment-item" id="comment-{cid}">
<div class="comment-head"><img src="{avatar}" class="comment-avatar" height="45" width="45" alt=""><div><span class="comment-author">{author}</span><br><span class="comment-date">{date_s}</span></div></div>
<div class="comment-text">{text}</div>{kids}</li>""")
        out.append('</ol>')
        return ''.join(out)

    n = len(items)
    if n:
        inner = render_list(0, 1)
    else:
        inner = '<p class="no-comments-note">هنوز دیدگاهی ثبت نشده است. اولین نفری باشید که درباره این مقاله نظر می‌دهد.</p>'
    return f"""<section class="comments"><div><span class="eyebrow">گفت‌وگو</span><h2>دیدگاه‌ها <small>{fa_digits(n)}</small></h2></div>{inner}
<p class="static-comments-note">در نسخه استاتیک سایت، ثبت دیدگاه جدید امکان‌پذیر نیست.</p></section>"""

# Figma author-box bio (his own bio, polished — same facts as BIO_SHORT).
AUTHOR_BOX_BIO = ('از سال ۱۳۸۵ در حوزه آی‌تی و شبکه فعالیت می‌کنم. در راه‌اندازی و پشتیبانی شبکه، سرویس‌های '
                  'مایکروسافت، لینوکس، سیسکو، میکروتیک، VOIP و مدیریت سرور تخصص دارم.')

def _trunc(s, n=40):
    """Plain text truncated at a word boundary + … (breadcrumb crumbs)."""
    s = plain_text(s)
    if len(s) <= n:
        return s
    return s[:n].rsplit(' ', 1)[0] + '…'

def post_page(p):
    url = post_url(p)
    mins = read_mins_of(p)
    ncom = comment_count(p['id'])
    feat = featured_url(p)
    cats = [CAT_BY_ID[cid] for cid in p.get('categories', []) if cid in CAT_BY_ID]
    meta = post_meta.get(str(p['id']), {})
    related = [POSTS_BY_LINK[u] for u in meta.get('related', []) if u in POSTS_BY_LINK][:3]
    content = clean_content(p['content']['rendered'])
    # TOC: h2 headings get ids and are listed in the sticky aside.
    # Posts with no h2s get the single-column layout (no-toc).
    toc_items = []
    def _h2(m):
        attrs, inner = m.group(1), m.group(2)
        m_id = re.search(r'id="([^"]*)"', attrs)
        if m_id:
            toc_items.append((m_id.group(1), html.escape(plain_text(inner))))
            return m.group(0)
        tid = f'toc-{len(toc_items) + 1}'
        toc_items.append((tid, html.escape(plain_text(inner))))
        return f'<h2 id="{tid}"{attrs}>{inner}</h2>'
    content = re.sub(r'<h2([^>]*)>(.*?)</h2>', _h2, content, flags=re.S)
    toc_html = ''
    layout_cls = 'article-layout shell'
    if toc_items:
        links = ''.join(f'<a href="#{tid}">{label}</a>' for tid, label in toc_items)
        toc_html = f'<aside class="toc"><span>در این مقاله</span>{links}</aside>'
    else:
        layout_cls += ' no-toc'
    chip = f'<a class="chip" href="{cat_url(cats[0])}">{cats[0]["name"]}</a>' if cats else ''
    crumb_cat = (f'<a href="{cat_url(cats[0])}">{cats[0]["name"]}</a><span>/</span>'
                 if cats else '')
    lead = excerpt_of(p) or plain_text(content)[:160]
    rel_html = ''
    if related:
        cards = ''.join(card_html(q) for q in related)
        rel_html = f"""<section class="related-section"><div class="shell"><div class="section-heading"><div><span class="eyebrow">پیشنهاد مطالعه</span><h2>نوشته‌های مرتبط</h2></div></div><div class="post-grid related-grid">{cards}</div></div></section>"""
    body = f"""<main id="single" class="main"><article class="article-page">
<header class="article-head shell article-width">
<div class="breadcrumbs"><a href="/">خانه</a><span>/</span>{crumb_cat}<span>{html.escape(_trunc(p['title']['rendered']))}</span></div>
{chip}
<h1>{p['title']['rendered']}</h1>
<p class="article-lead">{html.escape(lead)}</p>
<div class="article-meta"><div class="author-mini"><img src="{AVATAR}" alt=""><span><strong>رامتین رحمانی‌نژاد</strong><small>نویسنده و مدرس شبکه</small></span></div><div><time datetime="{p['date'][:10]}">{fa_date(p['date'])}</time><span>{icon('clock', 17)}{fa_digits(mins)} دقیقه مطالعه</span></div></div>
</header>
<figure class="featured shell"><img src="{feat}" alt="{html.escape(plain_text(p['title']['rendered']))}" fetchpriority="high"></figure>
<div class="{layout_cls}">{toc_html}<div class="article-content">{content}
<section class="author-box">
<img src="{AVATAR}" alt="رامتین رحمانی‌نژاد">
<div><span class="eyebrow">درباره نویسنده</span><h3>رامتین رحمانی‌نژاد</h3><p>{AUTHOR_BOX_BIO}</p><a href="/درباره-من/">بیشتر درباره من {icon('arrow', 17)}</a></div>
</section>
{comments_html(p)}
</div></div>
</article>{rel_html}</main>"""
    return page_shell(plain_text(p['title']['rendered']), yoast_head_for('post', p['slug']), body,
                      body_class=f"rtl single single-post postid-{p['id']} single-format-standard")

def contact_section_html():
    """Contact section (info only). The form was removed 22 Nov 2026: it
    had no backend, only a mailto hack that opened the visitor's mail
    client — not a working form. Visitors email directly via the mailto
    link below. Used on the about page (the standalone /contact/ page was
    removed 23 Nov 2026 — its content was identical to this section)."""
    return f"""<section class="contact-section shell" id="contact">
<div class="contact-info"><span class="eyebrow">تماس با من</span><h2>برای همکاری یا مشاوره، پیام بفرستید.</h2>
<p>اگر فکر می‌کنید می‌تونم در پروژه، زیرساخت یا آموزش به شما کمک کنم، بهم ایمیل بزنید. در اولین فرصت پاسخ می‌دم.</p>
<a href="mailto:ramtin.rahmani@gmail.com"><span>{icon('mail')}</span><div><small>ایمیل</small><b dir="ltr">ramtin.rahmani@gmail.com</b></div></a>
<div class="contact-social"><small>من رو دنبال کنید</small>{socials_html()}</div></div>
</section>"""

def page_page(pg):
    slug = unquote(pg['slug'])
    title = plain_text(pg['title']['rendered'])
    content = clean_content(pg['content']['rendered'])
    if slug == 'درباره-من':
        # Figma About page: hero + bio (Figma copy + the real lists from
        # his about content: traits, services, credentials) + services +
        # contact section. The real intro paragraph duplicates Figma's
        # lead and the closing email line duplicates the contact section,
        # so both are left out; the LinkedIn line is Figma's link below.
        parts = content.split('<hr />')
        bio_extra = '<hr>'.join(parts[1:4]) if len(parts) >= 4 else content
        body = f"""<main class="main">
<section class="about-hero page-hero"><h1 class="sr-only">درباره من</h1><div class="shell about-hero-grid">
<div><div class="breadcrumbs"><a href="/">خانه</a><span>/</span><span>درباره من</span></div>
<span class="eyebrow">سلام، من رامتین هستم</span>
<p>از سال ۱۳۸۵ در حوزه فناوری اطلاعات و شبکه فعالیت می‌کنم و تجربه‌م رو از دل پروژه‌های واقعی، ساده و کاربردی به اشتراک میذارم.</p>
<a class="primary-button" href="#contact">تماس با من {icon('arrow')}</a></div>
<figure><div class="portrait-frame"><img src="{ABOUT_PHOTO}" alt="رامتین رحمانی‌نژاد"></div></figure>
</div></section>
<section class="shell bio-section"><div class="bio-title"><span class="eyebrow">مسیر حرفه‌ای من</span><h2>از یادگیری تا<br>انتقال تجربه</h2></div>
<div class="bio-copy"><p class="lead">سلام. من <strong>رامتین رحمانی‌نژاد اصیل</strong> هستم. از سال ۱۳۸۵ در حوزه آی‌تی فعال هستم.</p>
<p>در راه‌اندازی و پشتیبانی شبکه و سرویس‌های مایکروسافت، لینوکس، سیسکو، میکروتیک، VOIP، ارتباطات رادیویی و مدیریت سرور تخصص دارم. در این سال‌ها کنار اجرای پروژه‌ها، آموزش و مستندسازی رو هم جدی دنبال کردم.</p>
<p>هدفم اینه که راه‌حل‌ها فقط کار نکنن؛ قابل فهم، امن، پایدار و قابل نگهداری هم باشن.</p>
{bio_extra}
<a href="https://www.linkedin.com/in/ramtin-rahmani" target="_blank" rel="noreferrer">مشاهده پروفایل لینکدین {icon('arrow', 17)}</a></div></section>
<section class="services"><div class="shell"><div class="section-heading"><div><span class="eyebrow">زمینه‌های همکاری</span><h2>چطور می‌تونم کمک کنم؟</h2></div></div>
<div class="service-grid">
<div><span>۰۱</span><h3>مشاوره شبکه</h3><p>بررسی وضعیت موجود، طراحی معماری و انتخاب راهکار متناسب با نیاز واقعی سازمان.</p></div>
<div><span>۰۲</span><h3>اجرا و پشتیبانی</h3><p>راه‌اندازی و نگهداری شبکه، سرورها، میکروتیک، لینوکس، سرویس‌های مایکروسافت و VOIP.</p></div>
<div><span>۰۳</span><h3>آموزش تخصصی</h3><p>دوره‌ها و آموزش‌های پروژه‌محور برای مهندسان شبکه، مدیران IT و علاقه‌مندان زیرساخت.</p></div>
</div></div></section>
{contact_section_html()}
</main>"""
        return page_shell(title, yoast_head_for('page', pg['slug']), body,
                          body_class=f"rtl page page-id-{pg['id']}")
    if slug == 'donate':
        # Wallet address: copyable block with a copy button (same address is
        # correct for both TRC20 and TRX — one Tron address serves both).
        addr = 'TCYrKuMPLYEoSWms2ZLZseTDcRPoYJR1fW'
        content = content.replace(
            addr,
            f'<span class="wallet-wrap"><code class="wallet-address" dir="ltr">{addr}</code>'
            f'<button type="button" class="copy-address primary-button" data-copy="{addr}">کپی آدرس</button></span>')
        # Obfuscated email (his own wording): keep it, but never break it
        # across two lines.
        content = content.replace(
            'ramtin.rahmani توی gmail',
            '<span class="email-inline">ramtin.rahmani توی gmail</span>')
    body = f"""<main class="main">
<section class="page-hero category-hero"><div class="shell">
<div class="breadcrumbs"><a href="/">خانه</a><span>/</span><span>{html.escape(title)}</span></div>
<h1>{html.escape(title)}</h1>
</div></section>
<div class="shell"><div class="page-body article-content">{content}</div></div>
</main>"""
    return page_shell(title, yoast_head_for('page', pg['slug']), body,
                      body_class=f"rtl page page-id-{pg['id']}")

# ---------------- home / archives / search ----------------
PER_PAGE = 6

def home_pages():
    total = (len(posts) + PER_PAGE - 1) // PER_PAGE
    for page in range(1, total + 1):
        chunk = posts[(page - 1) * PER_PAGE: page * PER_PAGE]
        cards = ''.join(card_html(p, i, grid=True) for i, p in enumerate(chunk))
        body = f"""<main id="home" class="main">
<h1 class="sr-only">راهنمای کاربردی برای دنیای شبکه و دواپس</h1>
<section class="shell listing-section">
<div class="post-grid">{cards}</div>
{pagination_html('/', page, total)}
</section></main>"""
        canon = SITE_URL + ('/' if page == 1 else f'/page/{page}/')
        yoast = ('<title>رامتین - پشتیبانی شبکه</title>\n'
                 '<meta name="description" content="پشتیبانی شبکه">\n'
                 f'<link rel="canonical" href="{canon}">\n')
        html_s = page_shell('رامتین - پشتیبانی شبکه', yoast, body, body_class='rtl home blog')
        write('index.html' if page == 1 else f'page/{page}/index.html', html_s)
    return total

# Figma's MikroTik category description — the only category description
# that exists anywhere (categories.json has none for any category).
# It is accurate generic RouterOS copy; Ramtin can correct it.
MIKROTIK_DESC = 'آموزش‌های کاربردی RouterOS؛ از مفاهیم پایه و راه‌اندازی تا سناریوهای حرفه‌ای، امنیت، VPN، کانتینر و عیب‌یابی شبکه.'

def archive_pages(items, base, title, desc='', kind='category'):
    """Paginated Figma archive: category hero (breadcrumbs, eyebrow, h1,
    description, count) + post grid + pagination. Other archives than
    MikroTik show no description line (none exists in the data)."""
    total = max(1, (len(items) + PER_PAGE - 1) // PER_PAGE)
    eyebrow = {'category': 'دسته‌بندی', 'tag': 'برچسب', 'author': 'نویسنده'}.get(kind, 'دسته‌بندی')
    count_label = 'مقاله آموزشی' if kind == 'category' else 'مقاله'
    if kind == 'category' and not desc and base == '/category/mikrotik/':
        desc = MIKROTIK_DESC
    desc_html = f'<p>{html.escape(desc)}</p>' if desc else ''
    for page in range(1, total + 1):
        chunk = items[(page - 1) * PER_PAGE: page * PER_PAGE]
        cards = ''.join(card_html(p, i, grid=True) for i, p in enumerate(chunk))
        body = f"""<main id="archives" class="main">
<section class="page-hero category-hero"><div class="shell">
<div class="breadcrumbs"><a href="/">خانه</a><span>/</span><span>{html.escape(title)}</span></div>
<span class="eyebrow">{eyebrow}</span><h1>{html.escape(title)}</h1>
{desc_html}
<div class="category-count"><strong>{fa_digits(len(items))}</strong><span>{count_label}</span></div>
</div></section>
<section class="shell listing-section category-listing">
<div class="section-heading compact"><div><h2>همه نوشته‌ها</h2><p>مرتب‌شده بر اساس تازه‌ترین مطالب</p></div></div>
<div class="post-grid">{cards}</div>
{pagination_html(base, page, total)}
</section></main>"""
        yoast = (f'<title>{html.escape(title)} - رامتین</title>\n'
                 f'<meta name="description" content="{html.escape(desc or title)}">\n'
                 f'<link rel="canonical" href="{SITE_URL}{base if page == 1 else base + f"page/{page}/"}">\n')
        html_s = page_shell(f'{title} - رامتین', yoast, body,
                            body_class=f'rtl archive {kind}')
        # files live under DECODED directories; hrefs/canonicals keep the encoded form
        dir_base = unquote(base.strip('/'))
        write(f'{dir_base}/index.html' if page == 1 else f'{dir_base}/page/{page}/index.html', html_s)
    return total

SITE_JS = """// ramtiin.ir static — vanilla JS for the Figma design behaviours.
document.addEventListener('DOMContentLoaded', function () {
  // mobile drawer (Figma: .overlay + .drawer with .is-open, body scroll lock)
  var drawer = document.querySelector('.drawer');
  var overlay = document.querySelector('.overlay');
  function openDrawer() {
    if (drawer) drawer.classList.add('is-open');
    if (overlay) overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  }
  function closeDrawer() {
    if (drawer) drawer.classList.remove('is-open');
    if (overlay) overlay.classList.remove('is-open');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-open-drawer]').forEach(function (b) {
    b.addEventListener('click', openDrawer);
  });
  document.querySelectorAll('[data-close-drawer]').forEach(function (b) {
    b.addEventListener('click', closeDrawer);
  });
  // desktop dropdowns: click toggles (touch), hover/focus handled by CSS
  document.querySelectorAll('.nav-drop').forEach(function (d) {
    var btn = d.querySelector('.nav-parent');
    if (!btn) return;
    btn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      var open = d.classList.contains('is-open');
      document.querySelectorAll('.nav-drop.is-open').forEach(function (o) {
        o.classList.remove('is-open');
        var b = o.querySelector('.nav-parent');
        if (b) b.setAttribute('aria-expanded', 'false');
      });
      if (!open) {
        d.classList.add('is-open');
        btn.setAttribute('aria-expanded', 'true');
      }
    });
  });
  document.addEventListener('click', function () {
    document.querySelectorAll('.nav-drop.is-open').forEach(function (o) {
      o.classList.remove('is-open');
      var b = o.querySelector('.nav-parent');
      if (b) b.setAttribute('aria-expanded', 'false');
    });
  });
  // search modal (Figma: .search-modal with .open; the form submits to /search/?q=)
  var modal = document.querySelector('.search-modal');
  function openSearch() {
    if (!modal) return;
    modal.classList.add('open');
    document.body.style.overflow = 'hidden';
    var i = modal.querySelector('input');
    if (i) i.focus();
  }
  function closeSearch() {
    if (!modal) return;
    modal.classList.remove('open');
    document.body.style.overflow = '';
  }
  document.querySelectorAll('[data-open-search]').forEach(function (b) {
    b.addEventListener('click', openSearch);
  });
  document.querySelectorAll('[data-close-search]').forEach(function (b) {
    b.addEventListener('click', closeSearch);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') { closeDrawer(); closeSearch(); }
  });
  // generic copy buttons (donate wallet addresses)
  document.querySelectorAll('[data-copy]').forEach(function (b) {
    b.addEventListener('click', function () {
      var done = function () { var t = b.textContent; b.textContent = 'کپی شد!'; setTimeout(function(){ b.textContent = t; }, 2000); };
      if (navigator.clipboard) navigator.clipboard.writeText(b.getAttribute('data-copy')).then(done);
      else { var ta = document.createElement('textarea'); ta.value = b.getAttribute('data-copy'); document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta); done(); }
    });
  });
  // code blocks: a copy button on EVERY <pre> (design-system rule —
  // every code block on the blog must be copyable, no exceptions).
  document.querySelectorAll('pre').forEach(function (pre) {
    var wrap = document.createElement('div');
    wrap.className = 'codeblock';
    pre.parentNode.insertBefore(wrap, pre);
    wrap.appendChild(pre);
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'copy-code';
    b.textContent = 'کپی';
    b.setAttribute('aria-label', 'کپی کد');
    b.addEventListener('click', function () {
      var text = pre.textContent.replace(/\\n$/, '');
      var done = function () { b.textContent = 'کپی شد!'; setTimeout(function(){ b.textContent = 'کپی'; }, 2000); };
      var fallback = function () { var ta = document.createElement('textarea'); ta.value = text; document.body.appendChild(ta); ta.select(); try { document.execCommand('copy'); } catch (e) {} document.body.removeChild(ta); done(); };
      if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(text).then(done, fallback);
      else fallback();
    });
    wrap.appendChild(b);
});
});"""

STATIC_CSS = """/* ============================================================
   DESIGN SYSTEM — ramtiin.ir (Figma Make redesign, 2026-11-21)
   Ported from the Figma Make output (Persian_Tech_Blog_Redesign.zip):
   tokens, header/drawer/search, intro, cards, pagination, footer,
   category hero, article, about, contact. The theme CSS files
   (style.min.css, rtl.css, customizer.css, font-awesome, sh) are NOT
   loaded anymore — this file is the entire design system.
   Vazirmatn is self-hosted (Google Fonts is unreliable from Iran).
   ============================================================ */
@font-face{font-family:'Vazirmatn';src:url('../fonts/Vazirmatn-Variable.woff2') format('woff2-variations');font-weight:100 900;font-style:normal;font-display:swap}

:root {
  --ink: #17202a;
  --muted: #66717e;
  --accent: #f54868;
  --accent-dark: #d92f51;
  --paper: #fff;
  --soft: #f5f7f8;
  --line: #e5e9ec;
  --navy: #131c25;
  --shell: 1180px;
}

@layer base {
  * { box-sizing: border-box; }
  html { scroll-behavior: smooth; }
  body { direction: rtl; margin: 0; background: var(--paper); color: var(--ink); font-family: 'Vazirmatn', sans-serif; font-size: 16px; line-height: 1.8; -webkit-font-smoothing: antialiased; }
  a { color: inherit; text-decoration: none; }
  button, input, textarea, select { font-family: inherit; }
  button { cursor: pointer; }
  img { max-width: 100%; display: block; }
}

.shell { width: min(var(--shell), calc(100% - 48px)); margin-inline: auto; }
.topline { background: var(--navy); color: #c8cfd5; font-size: 12px; }
.topline-inner { height: 36px; display: flex; align-items: center; justify-content: space-between; }
.socials { display: flex; gap: 8px; align-items: center; }
.socials a { width: 36px; height: 36px; display: grid; place-items: center; border: 1px solid #34404b; color: white; transition: .2s; }
.socials a:hover { background: var(--accent); border-color: var(--accent); }
.socials-muted a { width: 26px; height: 26px; border: 0; color: #aab3bb; }
.socials-muted svg { width: 16px; }
.site-header { position: sticky; top: 0; z-index: 30; background: rgba(255,255,255,.96); border-bottom: 1px solid var(--line); backdrop-filter: blur(10px); }
.header-inner { height: 78px; display: flex; align-items: center; }
.brand { font-size: 29px; line-height: 1; font-weight: 800; letter-spacing: -.8px; }
.brand span { color: var(--accent); }
.desktop-nav { display: flex; align-items: center; gap: 29px; margin-right: 70px; font-size: 14px; font-weight: 600; }
.desktop-nav a { position: relative; padding: 28px 0; }
.desktop-nav a::after { content: ''; position: absolute; right: 0; left: 100%; bottom: 18px; height: 2px; background: var(--accent); transition: .2s; }
.desktop-nav a:hover::after { left: 0; }
.desktop-nav .nav-drop { position: relative; }
.desktop-nav .nav-parent { display: inline-flex; align-items: center; gap: 5px; background: none; border: 0; padding: 28px 0; font: inherit; font-weight: 600; color: inherit; cursor: pointer; }
.desktop-nav .nav-parent svg { transition: transform .2s; }
.desktop-nav .nav-drop:hover .nav-parent svg, .desktop-nav .nav-drop:focus-within .nav-parent svg, .desktop-nav .nav-drop.is-open .nav-parent svg { transform: rotate(180deg); }
.desktop-nav .nav-sub { position: absolute; top: 100%; right: 0; min-width: 230px; display: none; flex-direction: column; background: white; border: 1px solid var(--line); border-radius: 12px; box-shadow: 0 18px 45px rgba(25,37,48,.12); padding: 8px; z-index: 70; }
.desktop-nav .nav-sub a { padding: 10px 14px; font-weight: 500; }
.desktop-nav .nav-sub a::after { display: none; }
.desktop-nav .nav-drop:hover .nav-sub, .desktop-nav .nav-drop:focus-within .nav-sub, .desktop-nav .nav-drop.is-open .nav-sub { display: flex; }
.header-actions { margin-right: auto; display: flex; gap: 8px; }
.icon-button { border: 0; background: transparent; padding: 0; width: 40px; height: 40px; display: grid; place-items: center; color: var(--ink); }
.icon-button:hover { color: var(--accent); }
.menu-button { display: none; }
.overlay { position: fixed; inset: 0; background: rgba(11,17,23,.52); z-index: 50; opacity: 0; pointer-events: none; visibility: hidden; transition: opacity .25s, visibility 0s .25s; }
.overlay.is-open { opacity: 1; pointer-events: auto; visibility: visible; transition: opacity .25s; }
.drawer { position: fixed; top: 0; right: 0; z-index: 60; width: min(360px, 88vw); height: 100dvh; background: white; padding: 24px 28px; transform: translateX(105%); visibility: hidden; transition: transform .3s ease, visibility 0s .3s; display: flex; flex-direction: column; }
.drawer.is-open { transform: none; visibility: visible; transition: transform .3s ease; }
.drawer-head { display: flex; justify-content: space-between; align-items: center; padding-bottom: 25px; border-bottom: 1px solid var(--line); }
.drawer-nav { display: flex; flex-direction: column; padding: 25px 0; }
.drawer-nav a { padding: 12px 0; border-bottom: 1px solid #eef0f2; font-weight: 600; }
.drawer-nav .drawer-group { display: block; font-size: 13px; font-weight: 700; color: var(--muted); padding: 18px 0 4px; }
.drawer-nav .drawer-sub { padding-right: 18px; font-size: 14px; font-weight: 500; }
.drawer-foot { margin-top: auto; color: var(--muted); font-size: 14px; }
.drawer-foot .socials { margin-top: 16px; }
.drawer-foot .socials a { color: var(--ink); border-color: var(--line); }
.search-modal { position: fixed; inset: 0; z-index: 70; display: grid; place-items: start center; padding-top: 13vh; }
.search-backdrop { position: absolute; inset: 0; background: rgba(12,18,24,.86); border: 0; width: 100%; height: 100%; }
.search-panel { position: relative; z-index: 1; width: min(680px, calc(100% - 32px)); background: white; padding: 45px; }
.search-panel label { display: block; font-weight: 700; font-size: 23px; margin-bottom: 22px; }
.search-close { position: absolute; left: 12px; top: 12px; }
.search-field { display: flex; border-bottom: 2px solid var(--ink); }
.search-field input { border: 0; outline: 0; flex: 1; min-width: 0; padding: 14px 2px; font-size: 17px; }
.search-field button { width: 50px; border: 0; background: transparent; display: grid; place-items: center; }
.search-panel p { color: var(--muted); font-size: 13px; margin: 14px 0 0; }
.intro-strip { border-bottom: 1px solid var(--line); background: linear-gradient(90deg,#fff 0%,#fff 55%,#f8f9fa 55%); }
.intro-inner { min-height: 270px; display: grid; grid-template-columns: 1.15fr 1fr; gap: 90px; align-items: center; }
.eyebrow { display: block; color: var(--accent-dark); font-size: 12px; font-weight: 800; letter-spacing: .04em; margin-bottom: 10px; }
.intro-inner h1 { font-size: clamp(35px, 4vw, 54px); line-height: 1.35; letter-spacing: -1.8px; margin: 0; font-weight: 800; }
.intro-inner h1 strong { color: var(--accent); }
.intro-inner p { color: #4d5965; font-size: 17px; line-height: 2.05; margin: 0; padding-right: 35px; border-right: 2px solid var(--accent); }
.listing-section { padding-block: 75px 90px; }
.section-heading { display: flex; justify-content: space-between; align-items: end; margin-bottom: 34px; }
.section-heading h2 { margin: 0; font-size: 31px; line-height: 1.3; letter-spacing: -.7px; }
.section-heading > a, .bio-copy > a { display: flex; align-items: center; gap: 9px; color: var(--muted); font-size: 14px; font-weight: 600; border-bottom: 1px solid var(--line); padding-bottom: 5px; }
.section-heading > a:hover, .bio-copy > a:hover { color: var(--accent); border-color: var(--accent); }
.post-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 30px; }
.post-card { border: 1px solid var(--line); background: white; min-width: 0; display: flex; flex-direction: column; transition: transform .2s, box-shadow .2s; }
.post-card:hover { transform: translateY(-4px); box-shadow: 0 18px 45px rgba(25,37,48,.08); }
.card-image { position: relative; display: block; aspect-ratio: 16 / 9; overflow: hidden; background: #e9ecef; }
.card-image img { width: 100%; height: 100%; object-fit: cover; transition: transform .4s ease; }
.post-card:hover .card-image img { transform: scale(1.035); }
.image-arrow { position: absolute; left: 0; bottom: 0; width: 42px; height: 42px; display: grid; place-items: center; color: white; background: var(--accent); transform: translateY(100%); transition: .2s; }
.post-card:hover .image-arrow { transform: none; }
.card-body { padding: 22px 23px 21px; display: flex; flex: 1; flex-direction: column; align-items: flex-start; }
.chip { display: inline-flex; align-items: center; min-height: 25px; padding: 3px 10px; color: var(--accent-dark); background: #fff0f3; font-size: 11px; font-weight: 800; border-radius: 2px; }
.card-body h3 { font-size: 18px; line-height: 1.75; margin: 12px 0 8px; font-weight: 750; }
.card-body h3 a:hover { color: var(--accent); }
.excerpt { color: var(--muted); font-size: 14px; line-height: 1.85; margin: 0 0 19px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.card-meta { width: 100%; display: flex; align-items: center; gap: 14px; padding-top: 14px; border-top: 1px solid #edf0f2; color: var(--muted); font-size: 11.5px; margin-top: auto; }
.card-meta span { display: flex; align-items: center; gap: 5px; }
.read-more { display: flex; align-items: center; gap: 8px; margin-top: 17px; color: var(--ink); font-size: 13px; font-weight: 700; }
.read-more svg { color: var(--accent); transition: .2s; }
.read-more:hover { color: var(--accent); }
.read-more:hover svg { transform: translateX(-4px); }
.pagination { display: flex; align-items: center; justify-content: center; gap: 8px; margin-top: 55px; direction: rtl; }
.pagination a, .pagination > span { width: 39px; height: 39px; display: grid; place-items: center; border: 1px solid var(--line); font-size: 13px; }
.pagination .active { color: white; background: var(--accent); border-color: var(--accent); }
.pagination a:hover { border-color: var(--ink); }
.pagination .next { width: auto; padding-inline: 15px; display: flex; gap: 7px; }
footer { background: var(--navy); color: #aeb7bf; padding-top: 70px; }
.footer-grid { display: grid; grid-template-columns: 1.45fr .7fr .7fr 1.15fr; gap: 70px; padding-bottom: 55px; }
.brand-light { color: white; display: inline-block; margin-bottom: 22px; }
.footer-grid section { display: flex; flex-direction: column; align-items: flex-start; }
.footer-grid h3 { color: white; font-size: 15px; margin: 5px 0 22px; }
.footer-grid p { font-size: 13px; line-height: 2; margin: 0 0 20px; }
.footer-grid section > a:not(.brand) { font-size: 13px; padding: 4px 0; }
.footer-grid section > a:hover { color: white; }
.footer-about .socials { margin-top: 8px; }
.newsletter { height: 46px; display: flex; width: 100%; border: 1px solid #39434c; }
.newsletter input { flex: 1; width: 100%; min-width: 0; background: transparent; border: 0; outline: 0; color: white; padding: 0 13px; font-size: 12px; }
.newsletter button { width: 46px; display: grid; place-items: center; background: var(--accent); color: white; border: 0; }
.footer-bottom { min-height: 70px; border-top: 1px solid #2a343d; display: flex; justify-content: space-between; align-items: center; font-size: 11.5px; }
.footer-bottom p { margin: 0; }
.page-hero { background: var(--soft); border-bottom: 1px solid var(--line); }
.category-hero .shell { position: relative; padding-block: 54px 64px; }
.breadcrumbs { display: flex; gap: 9px; align-items: center; color: var(--muted); font-size: 11px; margin-bottom: 35px; }
.breadcrumbs a:hover { color: var(--accent); }
.category-hero h1 { font-size: 45px; margin: 0 0 12px; line-height: 1.3; }
.category-hero p { max-width: 700px; font-size: 16px; color: var(--muted); line-height: 2; margin: 0; }
.category-count { position: absolute; left: 0; bottom: 66px; text-align: center; padding-right: 28px; border-right: 1px solid #d9dde0; }
.category-count strong { display: block; font-size: 34px; line-height: 1; }
.category-count span { font-size: 11px; color: var(--muted); }
.category-listing { padding-top: 60px; }
.section-heading.compact { margin-bottom: 28px; }
.section-heading.compact h2 { font-size: 23px; }
.section-heading.compact p { margin: 4px 0 0; font-size: 12px; color: var(--muted); }
.article-head { text-align: center; padding-top: 50px; }
.article-width { max-width: 900px; }
.article-head .breadcrumbs { justify-content: center; margin-bottom: 28px; }
.article-head h1 { font-size: clamp(31px, 4.1vw, 49px); line-height: 1.55; letter-spacing: -1.4px; margin: 16px auto 14px; }
.article-lead { max-width: 720px; color: var(--muted); font-size: 17px; margin: 0 auto 28px; }
.article-meta { border-top: 1px solid var(--line); padding-top: 22px; display: flex; justify-content: space-between; align-items: center; text-align: right; }
.author-mini { display: flex; align-items: center; gap: 12px; }
.author-mini img { width: 45px; height: 45px; border-radius: 50%; object-fit: cover; }
.author-mini span { display: flex; flex-direction: column; }
.author-mini strong { font-size: 13px; }
.author-mini small { color: var(--muted); font-size: 10px; }
.article-meta > div:last-child { display: flex; gap: 24px; color: var(--muted); font-size: 12px; }
.article-meta > div:last-child span { display: flex; align-items: center; gap: 6px; }
.featured { margin-top: 42px; max-width: 1100px; }
.featured img { width: 100%; aspect-ratio: 16 / 8.2; object-fit: cover; }
.featured figcaption { color: #89919a; font-size: 10px; margin-top: 7px; text-align: center; }
.article-layout { max-width: 1040px; display: grid; grid-template-columns: 180px minmax(0, 720px); gap: 65px; justify-content: center; padding-block: 50px 85px; direction: ltr; }
.toc { direction: rtl; align-self: start; position: sticky; top: 110px; border-right: 2px solid var(--line); display: flex; flex-direction: column; }
.toc span { padding: 0 15px 10px; font-size: 12px; font-weight: 800; }
.toc a { padding: 6px 15px; color: var(--ink); font-size: 11px; border-right: 2px solid transparent; margin-right: -2px; }
.toc a:hover { color: var(--accent); border-color: var(--accent); }
.article-content { direction: rtl; font-size: 17px; line-height: 2.15; }
.article-content > p { color: #3e4954; margin: 0 0 25px; }
.article-content h2 { font-size: 27px; line-height: 1.6; margin: 50px 0 16px; scroll-margin-top: 110px; }
.article-content h3 { font-size: 21px; margin: 36px 0 10px; }
.article-content blockquote { margin: 34px 0; padding: 24px 28px 24px 22px; border-right: 3px solid var(--accent); background: #fff5f7; color: #3e4852; font-weight: 500; }
.article-content ul, .article-content ol { padding-right: 24px; color: #3e4954; }
.article-content li { padding-right: 7px; margin: 4px 0; }
.article-content li::marker { color: var(--accent); font-weight: 700; }
.table-wrap { width: 100%; overflow-x: auto; margin: 25px 0 35px; border: 1px solid var(--line); }
.article-content table { border-collapse: collapse; width: 100%; min-width: 670px; font-size: 13px; }
.article-content th, .article-content td { text-align: right; padding: 13px 15px; border-bottom: 1px solid var(--line); }
.article-content th { background: var(--navy); color: white; }
.article-content tr:nth-child(even) td { background: #f7f8f9; }
.article-content pre { direction: ltr; text-align: left; background: #17212a; color: #d8e2e9; padding: 23px 25px; overflow-x: auto; font: 14px/1.8 ui-monospace, SFMono-Regular, Menlo, monospace; border-right: 3px solid var(--accent); }
.article-note { display: flex; gap: 14px; align-items: flex-start; background: var(--soft); border: 1px solid var(--line); padding: 20px 22px; margin-top: 35px; }
.article-note svg { color: var(--accent); flex: 0 0 auto; margin-top: 6px; }
.article-note p { margin: 0; font-size: 15px; line-height: 1.9; }
.author-box { margin-top: 65px; padding: 28px; background: var(--navy); color: white; display: grid; grid-template-columns: 110px 1fr; gap: 26px; }
.author-box img { width: 110px; height: 135px; object-fit: cover; }
.author-box .eyebrow { margin-bottom: 2px; color: #ff8ba0; }
.author-box h3 { font-size: 20px; margin: 0 0 6px; }
.author-box p { color: #bdc5cb; font-size: 13px; line-height: 1.9; margin: 0 0 10px; }
.author-box a { display: inline-flex; align-items: center; gap: 7px; color: white; font-size: 12px; border-bottom: 1px solid #fff; }
.comments { margin-top: 65px; }
.comments h2 { margin: 0; }
.comments h2 small { font-size: 13px; color: var(--muted); }
.empty-comments { margin-top: 20px; padding: 38px; border: 1px solid var(--line); text-align: center; }
.empty-comments svg { color: #a2aab1; margin: 0 auto 10px; }
.empty-comments p { margin: 0; font-weight: 700; }
.empty-comments span { display: block; color: var(--muted); font-size: 12px; }
.empty-comments button { background: transparent; border: 1px solid var(--ink); padding: 8px 16px; margin-top: 16px; font-size: 12px; font-weight: 700; }
.empty-comments button:hover { background: var(--ink); color: white; }
.related-section { background: var(--soft); border-top: 1px solid var(--line); padding: 65px 0 80px; }
.related-grid .card-body { padding-bottom: 18px; }
.about-hero { padding-block: 55px 70px; }
.about-hero-grid { display: grid; grid-template-columns: 1.25fr .75fr; align-items: center; gap: 100px; }
.about-hero .breadcrumbs { margin-bottom: 50px; }
.about-hero h1 { font-size: clamp(37px, 4.5vw, 56px); line-height: 1.55; letter-spacing: -2px; margin: 4px 0 19px; }
.about-hero h1 strong { color: var(--accent); }
.about-hero p { color: var(--muted); max-width: 620px; font-size: 17px; line-height: 2.1; }
.primary-button { display: inline-flex; align-items: center; justify-content: center; gap: 11px; background: var(--accent); color: white; border: 0; min-height: 48px; padding: 0 22px; font-size: 13px; font-weight: 700; }
.primary-button:hover { background: var(--accent-dark); }
.about-hero .primary-button { margin-top: 14px; }
.about-hero figure { position: relative; margin: 25px 0 0; }
.portrait-frame { position: relative; padding: 0 20px 20px 0; }
.portrait-frame::before { content: ''; position: absolute; right: 0; bottom: 0; width: 72%; height: 72%; border: 2px solid var(--accent); }
.portrait-frame img { position: relative; width: 100%; aspect-ratio: .82; object-fit: cover; filter: saturate(.85); }
.about-hero figcaption { position: absolute; left: -30px; bottom: 50px; background: var(--navy); color: white; padding: 17px 22px; min-width: 125px; }
.about-hero figcaption strong, .about-hero figcaption span { display: block; }
.about-hero figcaption strong { font-size: 23px; }
.about-hero figcaption span { color: #b6bec5; font-size: 10px; }
.bio-section { display: grid; grid-template-columns: .8fr 1.2fr; gap: 100px; padding-block: 90px; max-width: 1040px; }
.bio-title h2 { font-size: 38px; line-height: 1.55; margin: 0; }
.bio-copy p { color: var(--muted); font-size: 15px; line-height: 2.1; }
.bio-copy .lead { color: var(--ink); font-size: 18px; }
.bio-copy > a { width: max-content; margin-top: 25px; }
.services { background: var(--soft); border-block: 1px solid var(--line); padding-block: 75px 85px; }
.service-grid { display: grid; grid-template-columns: repeat(3,1fr); border: 1px solid var(--line); }
.service-grid > div { background: white; padding: 35px; min-height: 220px; border-left: 1px solid var(--line); }
.service-grid > div:last-child { border-left: 0; }
.service-grid > div > span { color: var(--accent); font-size: 12px; font-weight: 800; }
.service-grid h3 { font-size: 20px; margin: 24px 0 9px; }
.service-grid p { color: var(--muted); font-size: 13px; line-height: 2; margin: 0; }
.contact-section { display: grid; grid-template-columns: minmax(0, 640px); justify-content: center; padding-block: 90px 100px; }
.contact-info h2 { font-size: 33px; line-height: 1.6; margin: 0 0 14px; }
.contact-info > p { color: var(--muted); font-size: 14px; }
.contact-info > a { display: flex; align-items: center; gap: 13px; margin-top: 30px; }
.contact-info > a > span { width: 43px; height: 43px; display: grid; place-items: center; border: 1px solid var(--line); color: var(--accent); }
.contact-info > a b { color: var(--accent-dark); text-decoration: underline; text-underline-offset: 3px; }
.contact-info > a div { display: flex; flex-direction: column; }
.contact-info small { color: var(--muted); font-size: 10px; }
.contact-info b { font-size: 13px; }
.contact-social { margin-top: 30px; padding-top: 22px; border-top: 1px solid var(--line); }
.contact-social .socials { margin-top: 9px; }
.contact-social .socials a { color: var(--ink); border-color: var(--line); }

@media (max-width: 960px) {
  .desktop-nav { gap: 18px; margin-right: 35px; }
  .desktop-nav a:nth-child(3), .desktop-nav a:nth-child(4) { display: none; }
  .post-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
  .footer-grid { grid-template-columns: 1.4fr 1fr 1fr; gap: 45px; }
  .footer-grid section:last-child { grid-column: 1 / -1; }
  .article-layout { grid-template-columns: 150px minmax(0, 1fr); gap: 35px; }
  .about-hero-grid { gap: 55px; }
  .contact-section { gap: 45px; }
}

@media (max-width: 720px) {
  .shell { width: min(100% - 32px, var(--shell)); }
  .topline { display: none; }
  .site-header { top: 0; }
  .header-inner { height: 68px; }
  .desktop-nav { display: none; }
  .menu-button { display: grid; }
  .search-button { border-left: 1px solid var(--line); }
  .brand { font-size: 27px; }
  .intro-strip { background: var(--soft); }
  .intro-inner { display: block; padding-block: 48px; min-height: 0; }
  .intro-inner h1 { font-size: 35px; }
  .intro-inner p { margin-top: 25px; padding-right: 18px; font-size: 15px; }
  .listing-section { padding-block: 52px 65px; }
  .section-heading { align-items: center; margin-bottom: 25px; }
  .section-heading h2 { font-size: 25px; }
  .section-heading > a { font-size: 0; border: 0; }
  .section-heading > a svg { width: 22px; }
  .post-grid { grid-template-columns: 1fr; gap: 22px; }
  .card-body h3 { font-size: 17px; }
  .pagination { margin-top: 38px; }
  .pagination a, .pagination > span { width: 35px; height: 35px; }
  .pagination .next { font-size: 0; padding: 0; width: 35px; }
  .footer-grid { grid-template-columns: 1fr 1fr; gap: 38px 25px; padding-bottom: 45px; }
  .footer-about, .footer-grid section:last-child { grid-column: 1 / -1; }
  .footer-bottom { padding-block: 20px; flex-direction: column; gap: 3px; text-align: center; }
  .category-hero .shell { padding-block: 34px 45px; }
  .breadcrumbs { margin-bottom: 25px; }
  .category-hero h1 { font-size: 34px; }
  .category-hero p { font-size: 14px; padding-left: 0; }
  .category-count { position: static; border: 0; border-top: 1px solid var(--line); padding: 18px 0 0; margin-top: 25px; text-align: right; display: flex; align-items: center; gap: 8px; }
  .category-count strong { font-size: 23px; }
  .article-head { padding-top: 35px; }
  .article-head h1 { font-size: 29px; line-height: 1.65; }
  .article-lead { font-size: 15px; }
  .article-meta { align-items: flex-start; gap: 14px; }
  .article-meta > div:last-child { flex-direction: column; gap: 2px; text-align: left; }
  .featured { width: 100%; margin-top: 30px; }
  .featured figcaption { padding-inline: 16px; }
  .article-layout { display: block; padding-block: 32px 65px; }
  .toc { display: none; }
  .article-content { font-size: 16px; line-height: 2.05; }
  .article-content h2 { font-size: 23px; margin-top: 40px; }
  .article-content blockquote { margin-inline: 0; }
  .author-box { grid-template-columns: 75px 1fr; gap: 18px; padding: 22px; }
  .author-box img { width: 75px; height: 90px; }
  .author-box p { display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
  .related-grid .post-card:nth-child(3) { display: none; }
  .about-hero { padding-block: 34px 55px; }
  .about-hero-grid { grid-template-columns: 1fr; gap: 45px; }
  .about-hero .breadcrumbs { margin-bottom: 34px; }
  .about-hero h1 { font-size: 35px; }
  .about-hero p { font-size: 15px; }
  .about-hero figure { width: 80%; margin-inline: auto; }
  .about-hero figcaption { left: -20px; }
  .bio-section { grid-template-columns: 1fr; gap: 30px; padding-block: 60px; }
  .bio-title h2 { font-size: 30px; }
  .service-grid { grid-template-columns: 1fr; }
  .service-grid > div { border-left: 0; border-bottom: 1px solid var(--line); min-height: 0; }
  .contact-section { grid-template-columns: 1fr; gap: 40px; padding-block: 60px 70px; }
  .contact-info h2 { font-size: 28px; }
}

@media (max-width: 390px) {
  .article-meta { flex-direction: column; }
  .article-meta > div:last-child { flex-direction: row; }
  .footer-grid { grid-template-columns: 1fr; }
  .footer-grid section { grid-column: 1 !important; }
  .about-hero figure { width: 92%; }
}

/* ---------- Port additions: static-site necessities ----------
   (appended to the Figma CSS; unlayered, so these beat Figma's
   @layer base rules where they overlap.) */
:focus-visible{outline:2px solid var(--accent-dark);outline-offset:2px;border-radius:4px}
html,body{overflow-x:clip}
/* Content never sets its own colours — the design system owns colour
   (the old #00ccff blue headings came from WP inline styles). */
.article-content h1,.article-content h2,.article-content h3,.article-content h4{color:var(--ink)!important}
.article-content .author-box h3{color:#fff!important}
.article-content h1{font-size:clamp(28px,4vw,38px);line-height:1.5;font-weight:800;color:var(--ink);margin:0 0 20px}
/* Article body links must read as links. */
.article-content a{color:var(--accent-dark);text-decoration:underline;text-underline-offset:3px}
.article-content a:hover{color:var(--accent)}
.article-content img{max-width:100%;height:auto}
.article-content figure{margin:0 0 25px}
.article-content figcaption{color:#89919a;font-size:12px;margin-top:7px;text-align:center}
.article-content hr{border:0;border-top:1px solid var(--line);margin:30px 0}
.article-content iframe{max-width:100%;width:100%;height:auto;aspect-ratio:16/9;border:0}
.article-content code{font:13.5px/1.7 ui-monospace,SFMono-Regular,Menlo,monospace;background:#f5f7f8;border:1px solid var(--line);border-radius:4px;padding:1px 6px;direction:ltr;unicode-bidi:embed}
.article-content pre code{background:none;border:0;padding:0;font:inherit}
/* Code blocks: copy button on every <pre> (design-system rule). */
.codeblock{position:relative}
.codeblock pre{padding-top:42px}
.copy-code{position:absolute;top:9px;right:10px;z-index:1;min-height:28px;padding:2px 12px;border:0;border-radius:6px;background:var(--accent);color:#fff;font-size:12px;font-weight:700}
.copy-code:hover{background:var(--accent-dark)}
/* Bio links must read as links, same as article body links. */
.bio-copy a{color:var(--accent-dark);text-decoration:underline;text-underline-offset:3px}
.bio-copy a:hover{color:var(--accent)}
.bio-copy > a{border-bottom-color:transparent}
/* Posts with no h2 headings have no TOC — single centred column. */
.article-layout.no-toc{grid-template-columns:minmax(0,720px)}
/* Generic pages (course landing, service pages, donate): hero + centred body. */
.page-body{max-width:720px;margin-inline:auto;padding-block:50px 85px}
/* WPBakery buttons become the Figma primary button. */
.epcl-button{display:inline-flex;align-items:center;justify-content:center;gap:11px;background:var(--accent);color:#fff;border:0;min-height:48px;padding:0 22px;font-size:13px;font-weight:700}
.epcl-button:hover{background:var(--accent-dark);color:#fff}
/* Course CTA buttons live inside .article-content, whose link rule
   (.article-content a, accent-dark) otherwise beats .epcl-button's white. */
.article-content a.epcl-button,.article-content a.primary-button{color:#fff;text-decoration:none}
.article-content a.epcl-button:hover,.article-content a.primary-button:hover{color:#fff}
.epcl-button:hover{background:var(--accent-dark);color:#fff}
/* Donate page: copyable wallet + unbreakable email. */
.wallet-wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:center;gap:10px;margin:10px 0}
.wallet-address{display:inline-block;direction:ltr;background:var(--soft);border:1px solid var(--line);border-radius:6px;padding:8px 12px;font-size:13px;overflow-wrap:anywhere;max-width:100%}
.copy-address{flex:none}
.email-inline{white-space:nowrap}
/* Comments: real list, Figma-clean. */
.comment-list{list-style:none;margin:0;padding:0}
.comment-item{border-top:1px solid var(--line);padding:20px 0}
.comment-item:first-child{border-top:0}
.comment-head{display:flex;align-items:center;gap:12px}
.comment-avatar{width:45px;height:45px;border-radius:50%;object-fit:cover;flex:none}
.comment-author{font-weight:700;font-size:13px}
.comment-date{color:var(--muted);font-size:11px}
.comment-text{color:#3e4954;font-size:15px;line-height:1.9;margin-top:10px}
.comment-text p{margin:0 0 10px}
.comment-children{list-style:none;margin:14px 57px 0 0;padding:0}
.comment-children .comment-item{border-top:1px solid #eef0f2;padding:14px 0 0}
.static-comments-note{font-size:13px;color:var(--muted);text-align:center;margin-top:18px}
.no-comments-note{color:var(--muted);text-align:center;padding:18px 0}
/* Search page results. */
.search-results article{margin-bottom:18px;border-top:1px solid var(--line);padding-top:18px}
.search-results .result-title{font-size:18px;margin:0 0 6px}
.search-results .result-title a:hover{color:var(--accent)}
.search-results p{color:var(--muted);font-size:14px;margin:0}
/* Footer is 3 columns now (newsletter removed 2026-11-21 — no newsletter exists). */
.footer-grid{grid-template-columns:1.45fr .7fr .7fr}
@media (max-width:960px){.footer-grid section:last-child{grid-column:auto}}
/* Bio lists (real about-page content inside the Figma bio section). */
.bio-copy ul{padding-right:24px;color:var(--muted);font-size:15px;line-height:2.1}
.bio-copy li{margin:4px 0}
.bio-copy li::marker{color:var(--accent);font-weight:700}
.bio-copy hr{border:0;border-top:1px solid var(--line);margin:24px 0}
/* Long drawer menu scrolls. */
.drawer-nav{overflow-y:auto}
.pagination .prev svg{transform:scaleX(-1)}
.search-modal{display:none}
.search-modal.open{display:grid}
/* Screen-reader-only headings (pages whose visible design has no h1:
   home and About) + readable form placeholders. */
.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap;border:0}
input::placeholder,textarea::placeholder{color:var(--muted)}
"""

SEARCH_JS = """(function(){
  var q = new URLSearchParams(location.search).get('q') || '';
  var box = document.getElementById('search-results');
  var input = document.querySelector('.search-form input[name="q"]');
  if (input) input.value = q;
  if (!q || !box) return;
  fetch('/search.json').then(function(r){ return r.json(); }).then(function(items){
    var needle = q.trim();
    var hits = items.filter(function(it){ return (it.title + ' ' + it.excerpt).indexOf(needle) !== -1; });
    if (!hits.length) { box.innerHTML = '<p>چیزی پیدا نشد.</p>'; return; }
    var fa = function(n){ return String(n).replace(/\\d/g, function(d){ return '۰۱۲۳۴۵۶۷۸۹'[d]; }); };
    box.innerHTML = '<p>' + fa(hits.length) + ' نتیجه برای «' + needle.replace(/</g,'&lt;') + '»</p>' +
      hits.map(function(it){ return '<article><h3 class="result-title"><a href="' + it.url + '">' + it.title.replace(/</g,'&lt;') + '</a></h3><p>' + it.excerpt.replace(/</g,'&lt;') + '</p></article>'; }).join('');
  });
})();"""

def build_search():
    index = [{'title': plain_text(p['title']['rendered']),
              'url': post_url(p),
              'excerpt': excerpt_of(p),
              'date': p['date'][:10],
              'cats': [CAT_BY_ID[c]['name'] for c in p.get('categories', []) if c in CAT_BY_ID]}
             for p in posts]
    write('search.json', json.dumps(index, ensure_ascii=False))
    body = f"""<main class="main"><div class="shell"><div class="page-body article-content">
<h1>جستجو</h1>
<form action="/search/" method="get" class="search-form"><div class="search-field"><input type="text" name="q" placeholder="برای شروع جستجو تایپ کنید ..."><button type="submit" aria-label="جستجو">{icon('search')}</button></div></form>
<div class="search-results" id="search-results"></div>
</div></div></main>
<script>{SEARCH_JS}</script>"""
    yoast = ('<title>جستجو - رامتین</title>\n<meta name="robots" content="noindex, follow">\n'
             f'<link rel="canonical" href="{SITE_URL}/search/">\n')
    write('search/index.html', page_shell('جستجو - رامتین', yoast, body, body_class='rtl search'))

def rfc822(iso):
    d = datetime.fromisoformat(iso.replace('Z', '+00:00')) if 'T' in iso else datetime.strptime(iso[:10], '%Y-%m-%d')
    return d.strftime('%a, %d %b %Y %H:%M:%S +0330')

def build_feeds():
    items = []
    for p in posts:
        cats = ''.join(f'<category>{xml_escape(CAT_BY_ID[c]["name"])}</category>' for c in p.get('categories', []) if c in CAT_BY_ID)
        items.append(f"""<item><title>{xml_escape(plain_text(p['title']['rendered']))}</title><link>{SITE_URL}{post_url(p)}</link><guid isPermaLink="true">{SITE_URL}{post_url(p)}</guid><pubDate>{rfc822(p['date'])}</pubDate><description>{xml_escape(excerpt_of(p))}</description><content:encoded xmlns:content="http://purl.org/rss/1.0/modules/content/">{xml_escape(clean_content(p['content']['rendered']))}</content:encoded>{cats}</item>""")
    feed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">\n<channel>\n'
            f'<title>رامتین</title><link>{SITE_URL}</link><description>پشتیبانی شبکه</description><language>fa-IR</language>\n'
            + '\n'.join(items) + '\n</channel>\n</rss>\n')
    write('feed/index.html', feed)
    citems = []
    for c in sorted(comments, key=lambda x: x['date'], reverse=True):
        post = POSTS_BY_ID.get(c['post'])
        if not post:
            continue
        citems.append(f"""<item><title>دیدگاه {xml_escape(c.get('author_name',''))} در {xml_escape(plain_text(post['title']['rendered']))}</title><link>{SITE_URL}{post_url(post)}#comment-{c['id']}</link><guid isPermaLink="false">{SITE_URL}{post_url(post)}#comment-{c['id']}</guid><pubDate>{rfc822(c['date'])}</pubDate><description>{xml_escape(plain_text(c['content']['rendered']))}</description></item>""")
    cfeed = ('<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n<channel>\n'
             f'<title>دیدگاه‌ها — رامتین</title><link>{SITE_URL}</link><description>پشتیبانی شبکه</description><language>fa-IR</language>\n'
             + '\n'.join(citems) + '\n</channel>\n</rss>\n')
    write('comments/feed/index.html', cfeed)

def build_sitemaps():
    def urlset(urls):
        body = ''.join(f'<url><loc>{SITE_URL}{u}</loc><lastmod>{lm}</lastmod></url>' for u, lm in urls)
        return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + body + '</urlset>'
    post_urls = [(post_url(p), p['modified'][:10]) for p in posts]
    page_urls = [('/' + slug_path(pg['slug']) + '/', pg['modified'][:10]) for pg in pages
                 if unquote(pg['slug']) != 'contact']  # /contact/ removed 23 Nov 2026
    cat_urls = [(cat_url(c), max([p['modified'][:10] for p in posts if c['id'] in p.get('categories', [])] or ['2026-07-16']))
                for c in categories if c['count'] > 0]
    write('post-sitemap.xml', urlset(post_urls))
    write('page-sitemap.xml', urlset(page_urls))
    write('category-sitemap.xml', urlset(cat_urls))
    lastmods = [max([lm for _, lm in post_urls]), max([lm for _, lm in page_urls]), max([lm for _, lm in cat_urls])]
    idx = ('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
           + ''.join(f'<sitemap><loc>{SITE_URL}/{n}</loc><lastmod>{lm}</lastmod></sitemap>'
                     for n, lm in zip(['post-sitemap.xml', 'page-sitemap.xml', 'category-sitemap.xml'], lastmods))
           + '</sitemapindex>')
    write('sitemap_index.xml', idx)

ROBOTS = """# START YOAST BLOCK
# ---------------------------
User-agent: *
Disallow:

Sitemap: https://ramtiin.ir/sitemap_index.xml
# ---------------------------
# END YOAST BLOCK
"""

def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    # assets: only the Figma design CSS, the self-hosted Vazirmatn font,
    # and site.js. The old theme CSS / Font Awesome / SyntaxHighlighter
    # files are not copied anymore — nothing references them.
    css_out = os.path.join(OUT, 'assets', 'css')
    os.makedirs(css_out, exist_ok=True)
    os.makedirs(os.path.join(OUT, 'assets', 'fonts'), exist_ok=True)
    shutil.copy(os.path.join(SRC, 'theme', 'fonts-vazirmatn', 'Vazirmatn-Variable.woff2'),
                os.path.join(OUT, 'assets', 'fonts', 'Vazirmatn-Variable.woff2'))
    os.makedirs(os.path.join(OUT, 'assets', 'js'), exist_ok=True)
    open(os.path.join(OUT, 'assets', 'js', 'site.js'), 'w').write(SITE_JS)
    open(os.path.join(css_out, 'static.css'), 'w').write(STATIC_CSS)
    # media (uploads tree, originals only)
    shutil.copytree(os.path.join(SRC, 'media', 'wp-content'), os.path.join(OUT, 'wp-content'))
    # pages
    home_pages()
    for p in posts:
        write(slug_path(p['slug']) + '/index.html', post_page(p))
    for pg in pages:
        # /contact/ removed 23 Nov 2026: its content (the contact section)
        # already lives on About (/درباره-من/#contact). Skip it here so no
        # standalone page is generated; a redirect stub is written below.
        if unquote(pg['slug']) == 'contact':
            continue
        write(slug_path(pg['slug']) + '/index.html', page_page(pg))
    # Redirect stub for the removed /contact/ page: old links, bookmarks
    # and Google land here instead of a 404. The contact section lives on
    # About (/درباره-من/#contact). noindex so the stub itself is not indexed.
    write('contact/index.html', """<!DOCTYPE html>
<html dir="rtl" lang="fa-IR">
<head>
<meta charset="utf-8">
<title>تماس با من - رامتین</title>
<meta name="robots" content="noindex">
<link rel="canonical" href="https://ramtiin.ir/درباره-من/#contact">
<meta http-equiv="refresh" content="0; url=https://ramtiin.ir/درباره-من/#contact">
</head>
<body>
<p>این صفحه منتقل شد — <a href="https://ramtiin.ir/درباره-من/#contact">تماس با من در صفحه درباره من</a></p>
</body>
</html>
""")
    for c in categories:
        items = [p for p in posts if c['id'] in p.get('categories', [])]
        archive_pages(items, cat_url(c), c['name'], c.get('description') or '', kind='category')
    for t in tags:
        items = [p for p in posts if t['id'] in p.get('tags', [])]
        archive_pages(items, tag_url(t), t['name'], kind='tag')
    archive_pages(posts, AUTHOR_URL, 'رامتین رحمانی نژاد', BIO, kind='author')
    build_search()
    build_feeds()
    build_sitemaps()
    write('robots.txt', ROBOTS)
    write('CNAME', 'ramtiin.ir\n')
    write('.nojekyll', '')
    write('README.md', "# ramtiin.ir — generated output\n\nThis branch (`gh-pages`) holds the generated static site served by GitHub Pages at https://ramtiin.ir — do not edit by hand. The source (generator + WordPress data) lives on the `main` branch.\n")
    # ---- verification ----
    problems = []
    # 1) every internal /... link in generated HTML must resolve to a file
    generated = set()
    for root, _dirs, files in os.walk(OUT):
        for fn in files:
            generated.add(os.path.relpath(os.path.join(root, fn), OUT))
    def resolves(link):
        link = link.split('#')[0].split('?')[0]
        if not link or link.startswith(('http://', 'https://', 'mailto:', 'tel:')):
            return True
        if link.startswith('//'):
            return True
        path = unquote(link.lstrip('/'))
        if path == '':
            return 'index.html' in generated
        if path in generated:
            return True
        if (path.rstrip('/') + '/index.html') in generated:
            return True
        if (path + '.html') in generated:
            return True
        return False
    checked = 0
    for root, _dirs, files in os.walk(OUT):
        for fn in files:
            if not fn.endswith(('.html', '.xml')):
                continue
            text = open(os.path.join(root, fn), encoding='utf-8', errors='ignore').read()
            for link in set(re.findall(r'(?:href|src)="([^"]+)"', text)):
                if ' ' in link or '+' in link or '{' in link:
                    continue  # JS-concatenated href in the search page, not a real link
                checked += 1
                if link.startswith('https://ramtiin.ir/'):
                    link = link.replace('https://ramtiin.ir', '')
                if not resolves(link):
                    problems.append(f'BROKEN LINK in {os.path.relpath(os.path.join(root, fn), OUT)}: {link}')
    # 2) every uploads URL referenced must exist on disk
    for root, _dirs, files in os.walk(OUT):
        for fn in files:
            if not fn.endswith('.html'):
                continue
            text = open(os.path.join(root, fn), encoding='utf-8', errors='ignore').read()
            for u in set(re.findall(r'/wp-content/uploads/[^"\'\s<>)]+', text)):
                if unquote(u.lstrip('/')) not in generated:
                    problems.append(f'MISSING FILE {u} (referenced in {os.path.relpath(os.path.join(root, fn), OUT)})')
    print(f'generated files: {len(generated)} | links checked: {checked} | problems: {len(problems)}')
    for pr in sorted(set(problems))[:60]:
        print('  !', pr)
    if len(set(problems)) > 60:
        print(f'  ... and {len(set(problems)) - 60} more')

if __name__ == '__main__':
    main()
