[فارسی](README.md)

# ramtiin.ir — source of Ramtin Rahmani Nejad's personal blog

Source of Ramtin Rahmani Nejad's personal blog — a practical guide to the world of networking and DevOps. (Persian)

- Live site: https://ramtiin.ir
- English blog: https://ramtin.zone
- Courses: https://netadminplus.com

## Repo layout

This repo holds the source of the site; the built output lives on the `gh-pages` branch, which is what GitHub Pages serves.

- `build.py` — the site generator: builds the static site from the WordPress data
- `push.py` — pushes the built output to the `gh-pages` branch
- `posts.json`, `pages.json`, `categories.json`, `tags.json`, `comments.json` — WordPress data
- `media.json`, `media_urls.json`, `post_meta.json`, `yoast_posts.json`, `yoast_pages.json` — metadata and SEO
- `media/` — images and uploads (optimized)
- `theme/` — the Vazirmatn font and the old theme files
- `site/` — build output (not in git; produced by `build.py`)

## Build and deploy

```bash
python3 build.py   # builds the site into site/ — 408 files
python3 push.py    # pushes the output to the gh-pages branch (default)
```

> Do not edit the built files by hand; change `build.py` and rebuild.

## Site stats

- 48 posts, 8 pages, 10 categories
- Self-hosted Vazirmatn font; fully static site, no WordPress

## Contact

- Email: ramtin.rahmani@gmail.com
- YouTube and Instagram: @netadminplus
