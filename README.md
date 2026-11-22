[English](README-en.md)

# ramtiin.ir — سورس وبلاگ شخصی رامتین رحمانی‌نژاد

سورس وبلاگ شخصی رامتین رحمانی‌نژاد — راهنمای کاربردی برای دنیای شبکه و دواپس.

- سایت زنده: https://ramtiin.ir
- وبلاگ انگلیسی: https://ramtin.zone
- دوره‌ها و آموزش‌ها: https://netadminplus.com

## ساختار ریپو

این ریپو سورس سایته؛ خروجی ساخته‌شده توی برنچ `gh-pages` هست و GitHub Pages از همون برنچ سرو می‌کنه.

- `build.py` — ژنراتور سایت: از داده‌های وردپرس سایت استاتیک می‌سازه
- `push.py` — پوش خروجی ساخته‌شده به برنچ `gh-pages`
- `posts.json` ،`pages.json` ،`categories.json` ،`tags.json` ،`comments.json` — داده‌های وردپرس
- `media.json` ،`media_urls.json` ،`post_meta.json` ،`yoast_posts.json` ،`yoast_pages.json` — متادیتا و سئو
- `media/` — تصاویر و فایل‌های آپلودی (بهینه‌شده)
- `theme/` — فونت وزیرمتن و فایل‌های قالب قدیمی
- `site/` — خروجی بیلد (توی گیت نیست؛ با `build.py` ساخته می‌شه)

## ساخت و انتشار

```bash
python3 build.py   # ساخت سایت توی site/ — ‏۴۰۸ فایل
python3 push.py    # پوش خروجی به برنچ gh-pages (پیش‌فرض)
```

> فایل‌های ساخته‌شده رو دستی ویرایش نکنید؛ تغییر رو توی `build.py` بدید و دوباره بیلد بگیرید.

## آمار سایت

- ۴۸ پست، ۸ صفحه، ۱۰ دسته
- فونت وزیرمتن (سلف‌هاست)؛ سایت کاملاً استاتیکه، بدون وردپرس

## تماس

- ایمیل: ramtin.rahmani@gmail.com
- یوتیوب و اینستاگرام: @netadminplus
