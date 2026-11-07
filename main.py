"""Deep: haber topla -> Gemini ile seç/özetle -> dergi tarzı kare görsel üret."""
import base64
import datetime
import html
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import feedparser
import requests

ROOT = Path(__file__).parent
IMAGES = ROOT / "images"
POSTED = ROOT / "posted.json"
LATEST = ROOT / "latest.json"
TEMPLATE = ROOT / "template.html"

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Çalışmayan bir besleme olursa atlanır, sistem durmaz. İstediğini ekleyip çıkarabilirsin.
FEEDS = [
    "https://feeds.bbci.co.uk/turkce/rss.xml",        # BBC Türkçe
    "https://rss.dw.com/rdf/rss-tr-all",              # DW Türkçe
    "https://tr.euronews.com/rss",                    # Euronews Türkçe
    "https://www.trthaber.com/manset_articles.rss",   # TRT Haber
    "https://www.ntv.com.tr/gundem.rss",              # NTV Gündem
    "https://www.webtekno.com/rss.xml",               # Webtekno
    "https://shiftdelete.net/feed",                   # ShiftDelete
    "https://feeds.bbci.co.uk/news/world/rss.xml",    # BBC World (İngilizce, Türkçeye çevrilir)
]

ACCENTS = {
    "GÜNDEM": "#d62828",
    "DÜNYA": "#1d4e89",
    "TEKNOLOJİ": "#6a2fd6",
    "BİLİM": "#0b8a6b",
    "EKONOMİ": "#b8860b",
    "KÜLTÜR": "#c2185b",
    "SPOR": "#e85d04",
    "İLGİNÇ": "#0077b6",
}


def load_posted():
    if POSTED.exists():
        return json.loads(POSTED.read_text(encoding="utf-8"))
    return []


def collect(posted):
    items = []
    for url in FEEDS:
        try:
            feed = feedparser.parse(url)
            source = feed.feed.get("title", url)
            for e in feed.entries[:6]:
                link = e.get("link")
                if not link or link in posted:
                    continue
                summary = re.sub(r"<[^>]+>", " ", html.unescape(e.get("summary", "")))
                summary = re.sub(r"\s+", " ", summary).strip()[:500]
                items.append(
                    {"title": e.get("title", "").strip(), "summary": summary,
                     "link": link, "source": source}
                )
        except Exception as ex:  # noqa: BLE001
            print(f"Besleme okunamadı: {url} ({ex})")
    random.shuffle(items)
    return items[:30]


PROMPT = """Sen "Deep" adlı Türkçe bir Instagram dergi sayfasının editörüsün.
Aşağıdaki haber adaylarından genel bir Türk okuyucu için EN İLGİ ÇEKİCİ olanı seç
(Türkiye veya dünyadan; merak uyandıran, şaşırtan, öğretici olsun; magazin dedikoduları,
şiddet ayrıntıları, siyasi parti propagandası ve kışkırtıcı konulardan kaçın).

KURALLAR:
- SADECE aday metinlerde yazan bilgileri kullan. Bilgi uydurma, tahmin ekleme.
- Kendi cümlelerinle yaz, haber metnini kopyalama.
- Dil sade, akıcı ve dergi tadında olsun.

Sadece şu JSON'u döndür:
{{
  "index": seçilen adayın numarası (tam sayı),
  "kategori": "GÜNDEM" | "DÜNYA" | "TEKNOLOJİ" | "BİLİM" | "EKONOMİ" | "KÜLTÜR" | "SPOR" | "İLGİNÇ",
  "baslik": "en fazla 70 karakter, çarpıcı başlık",
  "ozet": "en fazla 260 karakter, 2-3 cümlelik özet",
  "caption": "Instagram açıklaması: 2-4 cümle, sonda 5-8 ilgili hashtag"
}}

ADAYLAR:
{adaylar}
"""


def ask_gemini(items):
    adaylar = "\n".join(
        f"[{i}] ({it['source']}) {it['title']} — {it['summary']}" for i, it in enumerate(items)
    )
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    body = {
        "contents": [{"parts": [{"text": PROMPT.format(adaylar=adaylar)}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.7},
    }
    last = None
    for attempt in range(3):
        try:
            r = requests.post(url, params={"key": API_KEY}, json=body, timeout=90)
            r.raise_for_status()
            text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            data = json.loads(text)
            if isinstance(data, list):
                data = data[0]
            for k in ("index", "kategori", "baslik", "ozet", "caption"):
                assert k in data, f"eksik alan: {k}"
            assert 0 <= int(data["index"]) < len(items)
            return data
        except Exception as ex:  # noqa: BLE001
            last = ex
            print(f"Gemini denemesi {attempt + 1} başarısız: {ex}")
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"Gemini yanıt vermedi: {last}")


def render(data, out_path):
    from playwright.sync_api import sync_playwright

    kategori = str(data["kategori"]).upper()
    accent = ACCENTS.get(kategori, "#222222")
    months = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
              "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
    now = datetime.datetime.utcnow() + datetime.timedelta(hours=3)
    tarih = f"{now.day} {months[now.month - 1]} {now.year}"

    logo_b64 = base64.b64encode((ROOT / "logo_white.png").read_bytes()).decode()
    logo_uri = f"data:image/png;base64,{logo_b64}"

    page_html = (
        TEMPLATE.read_text(encoding="utf-8")
        .replace("{{LOGO}}", logo_uri)
        .replace("{{KATEGORI}}", html.escape(kategori))
        .replace("{{BASLIK}}", html.escape(data["baslik"]))
        .replace("{{OZET}}", html.escape(data["ozet"]))
        .replace("{{KAYNAK}}", html.escape(data["kaynak"]))
        .replace("{{TARIH}}", tarih)
        .replace("{{ACCENT}}", accent)
    )
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})
        page.set_content(page_html, wait_until="networkidle")
        page.evaluate("document.fonts.ready")
        page.wait_for_timeout(600)  # otomatik sığdırma (fit) çalışsın
        page.screenshot(path=str(out_path), type="jpeg", quality=92)
        browser.close()


def cleanup_images(keep=30):
    files = sorted(IMAGES.glob("*.jpg"))
    for f in files[:-keep]:
        f.unlink()


def main():
    if not API_KEY:
        sys.exit("GEMINI_API_KEY tanımlı değil.")
    IMAGES.mkdir(exist_ok=True)
    LATEST.unlink(missing_ok=True)

    posted = load_posted()
    items = collect(posted)
    if not items:
        print("Yeni haber bulunamadı, çıkılıyor.")
        return

    data = ask_gemini(items)
    chosen = items[int(data["index"])]
    data["kaynak"] = chosen["source"]

    stamp = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%Y%m%d-%H%M%S")
    out_path = IMAGES / f"{stamp}.jpg"
    render(data, out_path)

    caption = f"{data['caption'].strip()}\n\nKaynak: {chosen['source']}"
    LATEST.write_text(
        json.dumps(
            {"image": f"images/{out_path.name}", "caption": caption, "link": chosen["link"]},
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    posted.append(chosen["link"])
    POSTED.write_text(json.dumps(posted[-300:], ensure_ascii=False, indent=2), encoding="utf-8")
    cleanup_images()
    print("Görsel hazır:", out_path.name)


if __name__ == "__main__":
    main()
