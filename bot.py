import hashlib
import json
import os
import re
import sys
from pathlib import Path

import requests

BOT_TOKEN = os.environ["BOT_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]
WATCH_URL = os.environ.get("WATCH_URL", "").strip()
KEYWORD = os.environ.get("KEYWORD", "").strip()

STATE_FILE = Path("state.json")


def send(text: str) -> None:
    r = requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        json={"chat_id": CHAT_ID, "text": text, "disable_web_page_preview": True},
        timeout=15,
    )
    r.raise_for_status()


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2))


def fetch_signature(url: str) -> str:
    r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    r.raise_for_status()
    text = re.sub(r"<script.*?</script>|<style.*?</style>", "", r.text, flags=re.S)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if KEYWORD:
        return "found" if KEYWORD.lower() in text.lower() else "missing"
    return hashlib.sha256(text.encode()).hexdigest()


def main() -> None:
    if not WATCH_URL:
        send("Bot çalışıyor ✅ (WATCH_URL tanımlı değil, sadece test mesajı)")
        return

    state = load_state()
    try:
        sig = fetch_signature(WATCH_URL)
    except requests.RequestException as e:
        print(f"Sayfa alınamadı: {e}", file=sys.stderr)
        return

    old = state.get(WATCH_URL)
    if old is None:
        send(f"İzleme başladı ✅\n{WATCH_URL}")
    elif old != sig:
        if KEYWORD:
            durum = "göründü 🎉" if sig == "found" else "kayboldu"
            send(f"'{KEYWORD}' sayfada {durum}\n{WATCH_URL}")
        else:
            send(f"Sayfa değişti 🔔\n{WATCH_URL}")

    state[WATCH_URL] = sig
    save_state(state)


if __name__ == "__main__":
    main()
