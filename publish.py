"""latest.json'daki postu doğrudan Instagram'a yayınlar."""
import json
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).parent
LATEST = ROOT / "latest.json"

IG_USER = os.getenv("IG_USER_ID", "")
IG_TOKEN = os.getenv("IG_ACCESS_TOKEN", "")
REPO = os.getenv("GITHUB_REPOSITORY", "")
BRANCH = os.getenv("GITHUB_REF_NAME", "main")
# Instagram Login ile alınan token için graph.instagram.com kullanılır
GRAPH = os.getenv("IG_GRAPH_HOST", "https://graph.instagram.com/v21.0")


def wait_for_url(url, tries=12):
    for _ in range(tries):
        try:
            if requests.get(url, timeout=30).status_code == 200:
                return True
        except requests.RequestException:
            pass
        time.sleep(10)
    return False


def check(r):
    if not r.ok:
        sys.exit(f"Instagram API hatası {r.status_code}: {r.text}")
    return r.json()


def publish_instagram(image_url, caption):
    created = check(
        requests.post(
            f"{GRAPH}/{IG_USER}/media",
            data={"image_url": image_url, "caption": caption, "access_token": IG_TOKEN},
            timeout=60,
        )
    )
    creation_id = created["id"]

    # Instagram görseli işlerken biraz bekle
    for _ in range(10):
        time.sleep(6)
        st = requests.get(
            f"{GRAPH}/{creation_id}",
            params={"fields": "status_code", "access_token": IG_TOKEN},
            timeout=30,
        ).json()
        if st.get("status_code") == "FINISHED":
            break
        if st.get("status_code") == "ERROR":
            sys.exit(f"Instagram görseli reddetti: {st}")

    result = check(
        requests.post(
            f"{GRAPH}/{IG_USER}/media_publish",
            data={"creation_id": creation_id, "access_token": IG_TOKEN},
            timeout=60,
        )
    )
    print("Instagram'da yayınlandı:", result)


def main():
    if not LATEST.exists():
        print("Yayınlanacak yeni post yok.")
        return
    if not (IG_USER and IG_TOKEN):
        sys.exit("IG_USER_ID / IG_ACCESS_TOKEN tanımlı değil.")

    data = json.loads(LATEST.read_text(encoding="utf-8"))
    image_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{data['image']}"
    if not wait_for_url(image_url):
        sys.exit(f"Görsel URL'si açılmadı (repo public mi?): {image_url}")
    publish_instagram(image_url, data["caption"])


if __name__ == "__main__":
    main()
