"""Собирает английскую страницу vitrina-web.com/en/ из главной (папка _tools на сайт не публикуется).
Перевод лежит в index.html (словарь EN в скрипте). Скрипт открывает главную в Chrome с ?lang=en,
забирает готовую страницу и сохраняет её как en/index.html с правильными адресами.
Запуск после любой правки index.html: python _tools/make_en.py"""
import html, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://vitrina-web.com"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

src = ROOT / "index.html"
url = src.as_uri() + "?lang=en"
dom = subprocess.run(
    [CHROME, "--headless=new", "--disable-gpu", "--virtual-time-budget=5000", "--dump-dom", url],
    capture_output=True, check=True, timeout=120).stdout.decode("utf-8")
if "<html" not in dom or 'lang="en"' not in dom:
    sys.exit("Chrome не вернул английскую страницу, файл не изменён")

def one(pattern, repl, text, flags=0):
    new, n = re.subn(pattern, repl, text, count=1, flags=flags)
    if n != 1:
        sys.exit(f"Не нашла в странице: {pattern}")
    return new

title = re.search(r"<title>(.*?)</title>", dom, re.S).group(1).strip()
desc = re.search(r'<meta name="description" content="(.*?)">', dom, re.S).group(1)

page = dom.lstrip() if dom.lstrip().lower().startswith("<!doctype") else "<!DOCTYPE html>\n" + dom.lstrip()
page = one(r"<html lang=\"en\"[^>]*>", '<html lang="en" data-page-lang="en">', page)
page = one(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{SITE}/en/">', page)
page = one(r'<meta property="og:url" content="[^"]*">', f'<meta property="og:url" content="{SITE}/en/">', page)
page = one(r'<meta property="og:title" content="[^"]*">', f'<meta property="og:title" content="{title}">', page)
page = one(r'<meta property="og:description" content="[^"]*">', f'<meta property="og:description" content="{desc}">', page)
page = one(r'(<meta property="og:type"[^>]*>)', r'\1\n  <meta property="og:locale" content="en_US">', page)
# Данные для Google (JSON-LD) на английской странице тоже по-английски
JSON_LD_EN = {
    '"name": "Витрина"': '"name": "Vitrina"',
    '"url": "https://vitrina-web.com/"': f'"url": "{SITE}/en/"',
    '"description": "Создание сайтов и Telegram-ботов для бизнеса и обучение: научу делать сайты и ботов самостоятельно. Дизайн под ваш стиль, сайты на любом языке."':
        '"description": "Websites and Telegram bots for business, and training: I teach you to build websites and bots yourself. Custom design, websites in any language."',
    '"name": "Сайты"': '"name": "Websites"',
    '"name": "Сайт-визитка на шаблоне"': '"name": "Business-card website on a template"',
    '"name": "Сайт с дизайном под ваш стиль"': '"name": "Website with a design in your style"',
    '"name": "Сайт под ключ с доменом и Google"': '"name": "Turnkey website with domain and Google setup"',
}
for ru, en in JSON_LD_EN.items():
    if ru not in page:
        sys.exit(f"Не нашла в данных для Google: {ru[:50]}")
    page = page.replace(ru, en, 1)
# страница лежит в /en/, поэтому относительные адреса картинок и работ делаем от корня сайта
page = re.sub(r'(src|href)="(images|work|demo)/', r'\1="/\2/', page)

out = ROOT / "en" / "index.html"
out.parent.mkdir(exist_ok=True)
out.write_text(page, encoding="utf-8", newline="\n")
print("готово:", out, f"({len(page)//1024} КБ)")
