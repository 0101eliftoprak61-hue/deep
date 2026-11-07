# Deep – Kurulum (adım adım, hepsi ücretsiz)

Sistem her gün 5 kez (TR saatiyle 09, 12, 15, 18, 21) şunu yapar:
haber toplar → Gemini ile en ilginç olanı seçip özetler → dergi kapağı tarzı 1080x1080 görsel üretir → **doğrudan Instagram'a yayınlar**.

Yorum cevaplama ve onay adımı yok.

---

## 1. GitHub repo
1. github.com'da hesap aç, **New repository** de, adı `deep` olsun.
2. **Public** seç (Instagram görseli çekebilsin diye şart, Actions da public repoda sınırsız ücretsiz).
3. Bu klasördeki tüm dosyaları repoya yükle: **Add file → Upload files**.
   - `.github/workflows/post.yml` dosyası klasör yapısıyla yüklenmeli. Olmazsa **Add file → Create new file** de, adına `.github/workflows/post.yml` yaz, içeriği yapıştır.

## 2. Gemini API anahtarı (ücretsiz)
1. aistudio.google.com/apikey adresine git, **Create API key** de.
2. Repoda **Settings → Secrets and variables → Actions → New repository secret**
   - Name: `GEMINI_API_KEY`
   - Value: anahtarın

## 3. Instagram bağlantısı
1. Instagram'ı **Professional (Creator/Business)** hesaba çevir.
2. Bir **Facebook Page** oluştur ve Instagram hesabına bağla.
3. developers.facebook.com → **My Apps → Create App** (tür: Business) → **Instagram Graph API** ekle.
4. **Graph API Explorer**'dan şu izinlerle bir **kullanıcı token'ı** al:
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`
5. Bu kısa ömürlü token'ı uzun ömürlüye çevir (yaklaşık 60 gün geçerli). Takılırsan bu adımı birlikte yaparız.
6. Instagram hesabının **IG User ID**'sini bul (Graph API Explorer'da `me/accounts` → sayfa → `instagram_business_account`).
7. İki secret ekle (Gemini'yi eklediğin yere): `IG_USER_ID` ve `IG_ACCESS_TOKEN`.

Not: Token ~60 günde dolar. Yayın bir gün durursa ilk bakılacak yer burası, yenileyip secret'ı güncelle.

## 4. İlk çalıştırma
1. Repoda **Actions** sekmesi → **Deep post** → **Run workflow**.
2. 2-3 dakika sonra Instagram'da ilk post çıkmış olmalı.
3. Çalışma kırmızı biterse tıkla, hata satırını bana yapıştır, düzeltelim.

Bundan sonra kendi kendine çalışır. Yanlış ya da kötü bir post çıkarsa Instagram'dan silebilirsin.

---

## Durdurmak / ayarlamak
- **Durdurmak:** Actions → Deep post → sağ üstteki `...` → **Disable workflow**.
- **Haber kaynakları:** `main.py` başındaki `FEEDS` listesine RSS adresi ekle/çıkar.
- **Saatler:** `.github/workflows/post.yml` içindeki `cron` satırı UTC'dir (Türkiye = UTC+3). GitHub zamanlaması birkaç dakika kayabilir.
- **Sıklık:** Saatlik için cron'u `"0 * * * *"` yap. Günde 24 post spam riski ve Gemini ücretsiz limiti yüzünden zorlayıcı, 5 ile başla.
- **Tasarım:** `template.html` içindeki renk ve yazı tipleri değiştirilebilir.

## Bilmen gerekenler
- Onay adımı olmadığı için Gemini'nin yaptığı bir hata doğrudan yayına gider. Prompt'ta "sadece haber metnindeki bilgileri kullan" kuralı var ama ücretsiz modeller yine de arada yanlış özetleyebilir. İlk günler hesabı takip et.
- Görsellerde haber fotoğrafı kullanılmıyor, sadece tipografik tasarım var (telif sorunu yok). Her post kaynağı belirtiyor.
- Instagram AI üretimi içerik etiketleme kurallarını zaman zaman günceller, hesabında etiket seçeneği çıkarsa işaretle.
