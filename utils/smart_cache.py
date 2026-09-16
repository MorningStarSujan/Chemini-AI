"""Persistent local Q&A cache for Chemini AI.

Stores successful Gemini answers on disk so repeated questions do not consume
Gemini quota. Entries are retained for six months and survive API-key changes
and application restarts.
"""
import json
import os
import re
import time
from threading import Lock

CACHE_TTL = 60 * 60 * 24 * 30 * 6
CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "ai_response_cache.json")
_lock = Lock()


def _normalize(text):
    text = str(text or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _load():
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def _save(data):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    tmp = CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, CACHE_FILE)


def get_cached_answer(question):
    """Return a persistent answer for an exact/near-identical question."""
    key = _normalize(question)
    if not key:
        return None
    now = time.time()
    with _lock:
        data = _load()
        changed = False
        for k in list(data):
            if now - float(data[k].get("timestamp", 0)) > CACHE_TTL:
                del data[k]
                changed = True
        if changed:
            _save(data)
        item = data.get(key)
        return item.get("answer") if item else None


def save_answer(question, answer):
    key = _normalize(question)
    answer = str(answer or "").strip()
    if not key or not answer or answer.startswith("⚠️"):
        return
    with _lock:
        data = _load()
        data[key] = {"question": str(question).strip(), "answer": answer, "timestamp": time.time()}
        _save(data)


def clear_expired():
    with _lock:
        data = _load()
        now = time.time()
        data = {k: v for k, v in data.items() if now - float(v.get("timestamp", 0)) <= CACHE_TTL}
        _save(data)
