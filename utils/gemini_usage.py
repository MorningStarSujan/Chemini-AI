"""Local Gemini API usage telemetry for the Chemini AI admin console.

This records usage returned by Gemini for requests made by this application.
It intentionally does NOT pretend to know Google's live remaining quota: Gemini
rate limits are enforced server-side and the public API does not provide a
reliable 'remaining quota' endpoint for the dashboard to poll.
"""

import json
import os
from datetime import datetime, timezone
from threading import Lock
from zoneinfo import ZoneInfo

USAGE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "gemini_usage.json")
_LOCK = Lock()
_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")


def _now():
    return datetime.now(timezone.utc)


def _period_key():
    # Gemini RPD resets at midnight Pacific Time, so use the same boundary for
    # the application's daily counters.
    try:
        return datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d")
    except Exception:
        return _now().strftime("%Y-%m-%d")


def _default():
    return {
        "period": _period_key(),
        "model": _MODEL,
        "requests": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "last_request_at": None,
        "last_status": "never",
        "last_error": None,
    }


def _load():
    if not os.path.exists(USAGE_FILE):
        return _default()
    try:
        with open(USAGE_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        if data.get("period") != _period_key():
            return _default()
        return {**_default(), **data}
    except (OSError, ValueError, TypeError):
        return _default()


def _save(data):
    os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
    tmp = USAGE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
    os.replace(tmp, USAGE_FILE)


def record_request(usage_metadata=None, status="success", error=None):
    """Record one actual Gemini API request.

    usage_metadata is the SDK response's usage_metadata object. If Google does
    not return token counts for a streaming response, the token fields remain
    unchanged rather than being estimated.
    """
    with _LOCK:
        data = _load()
        data["requests"] += 1
        data["last_request_at"] = _now().isoformat()
        data["last_status"] = status
        data["last_error"] = str(error)[:500] if error else None

        if status == "success":
            data["successful_requests"] += 1
        else:
            data["failed_requests"] += 1

        if usage_metadata is not None:
            input_tokens = int(getattr(usage_metadata, "prompt_token_count", 0) or 0)
            output_tokens = int(getattr(usage_metadata, "candidates_token_count", 0) or 0)
            total_tokens = int(getattr(usage_metadata, "total_token_count", 0) or 0)
            data["input_tokens"] += input_tokens
            data["output_tokens"] += output_tokens
            data["total_tokens"] += total_tokens

        _save(data)
        return data


def get_usage():
    with _LOCK:
        return _load()
