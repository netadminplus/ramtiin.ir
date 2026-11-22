#!/usr/bin/env python3
"""Full live verification for ramtiin.ir — every URL must return 200 and
carry its expected content. Run AFTER a push. Writes verify_report.json."""
import json, os, re, sys, urllib.request, urllib.error
from urllib.parse import quote, unquote

BASE = 'https://ramtiin.ir'
SRC = '/home/hatch/workspace/ramtiin-migration'

def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={'User-Agent': 'ramtiin-verify/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        return e.code, ''
    except Exception as e:
        return 0, str(e)

def slug_path(slug):
    return quote(unquote(slug), safe='')

posts = json.load(open(f'{SRC}/posts.json'))
pages = json.load(open(f'{SRC}/pages.json'))
cats = json.load(open(f'{SRC}/categories.json'))
tags = json.load(open(f'{SRC}/tags.json'))
media_urls = json.load(open(f'{SRC}/media_urls.json'))

results = {'ok': [], 'fail': []}
def check(url, expect=None, label=''):
    st, body = fetch(url)
    good = st == 200 and (expect is None or expect in body)
    (results['ok'] if good else results['fail']).append(
        {'url': url, 'status': st, 'expect': expect, 'label': label})
    return good

# homepage + pagination (8 pages)
check(BASE + '/', 'رامتین', 'homepage')
n_pages = (len(posts) + 5) // 6
for n in range(2, n_pages + 1):
    check(f'{BASE}/page/{n}/', 'رامتین', f'home page {n}')
# posts
for p in posts:
    url = f"{BASE}/{slug_path(p['slug'])}/"
    title = re.sub(r'<[^>]+>', '', p['title']['rendered'])[:25]
    check(url, title, f"post {p['id']}")
# pages
for pg in pages:
    url = f"{BASE}/{slug_path(pg['slug'])}/"
    title = re.sub(r'<[^>]+>', '', pg['title']['rendered'])[:20]
    check(url, title, f"page {pg['slug'][:20]}")
# categories (+ pagination where needed)
for c in cats:
    items = [p for p in posts if c['id'] in p.get('categories', [])]
    npg = max(1, (len(items) + 5) // 6)
    check(f"{BASE}/category/{c['slug']}/", c['name'], f"cat {c['slug']}")
    for n in range(2, npg + 1):
        check(f"{BASE}/category/{c['slug']}/page/{n}/", c['name'], f"cat {c['slug']} p{n}")
# tags (81 with posts)
for t in tags:
    items = [p for p in posts if t['id'] in p.get('tags', [])]
    if not items:
        continue
    npg = max(1, (len(items) + 5) // 6)
    check(f"{BASE}/tag/{t['slug']}/", t['name'], f"tag {t['slug'][:20]}")
    for n in range(2, npg + 1):
        check(f"{BASE}/tag/{t['slug']}/page/{n}/", t['name'], f"tag {t['slug'][:20]} p{n}")
# author
check(BASE + '/author/ramtin-rahmanigmail-com/', 'رامتین رحمانی نژاد', 'author')
# infra
for u, exp in [('/robots.txt', 'Sitemap:'), ('/sitemap_index.xml', 'sitemap'),
               ('/post-sitemap.xml', 'urlset'), ('/page-sitemap.xml', 'urlset'),
               ('/category-sitemap.xml', 'urlset'), ('/feed/', 'rss'),
               ('/comments/feed/', 'rss'), ('/search/', 'جستجو'),
               ('/assets/css/static.css', 'card-clean'),
               ('/assets/css/font-awesome.min.css', 'FontAwesome'),
               ('/assets/fonts/fontawesome-webfont.woff2', None),
               ('/assets/fonts/Vazirmatn-Variable.woff2', None),
               ('/assets/js/site.js', 'menu-open')]:
    check(BASE + u, exp, 'infra ' + u)
# media files (sample: all 216 via HEAD would be slow; check every file with GET but short timeout)
media = json.load(open(f'{SRC}/media.json'))
print(f"checking {len(media)} media files...", flush=True)
for m in media:
    src = m.get('source_url', '')
    path = '/' + src.split('ramtiin.ir/')[-1] if 'ramtiin.ir/' in src else None
    if not path:
        continue
    st, _ = fetch(BASE + quote(path, safe='/%'), timeout=20)
    (results['ok'] if st == 200 else results['fail']).append(
        {'url': BASE + path, 'status': st, 'expect': None, 'label': 'media'})

json.dump(results, open(f'{SRC}/verify_report.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
fails = results['fail']
print(f"\nTOTAL: {len(results['ok'])} ok, {len(fails)} FAIL")
for f in fails[:60]:
    print('FAIL:', f['status'], f['url'], '|', f['label'], '| expect:', (f['expect'] or '')[:40])
