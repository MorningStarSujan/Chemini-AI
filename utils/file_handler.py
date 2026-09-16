import json
import os
import tempfile
from datetime import datetime, timedelta
from threading import Lock


HISTORY_RETENTION_DAYS = 30
_history_lock = Lock()


def load_json(filename):
    filepath = os.path.join("data", filename)

    if not os.path.exists(filepath):
        return []

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def save_json(filename, data):
    filepath = os.path.join("data", filename)
    directory = os.path.dirname(filepath)

    if directory:
        os.makedirs(directory, exist_ok=True)

    fd, temp_path = tempfile.mkstemp(prefix=".tmp_", dir=directory or ".")

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
            file.flush()
            os.fsync(file.fileno())

        os.replace(temp_path, filepath)

    except Exception:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _parse_history_datetime(item):
    """Return a history timestamp while supporting old history records."""
    created_at = item.get("created_at")

    if created_at:
        try:
            return datetime.fromisoformat(created_at)
        except (TypeError, ValueError):
            pass

    legacy_time = item.get("time")

    if legacy_time:
        try:
            return datetime.strptime(legacy_time, "%d-%m-%Y %I:%M %p")
        except (TypeError, ValueError):
            pass

    return None


def _cleanup_history(data, now=None):
    """Keep only history from the rolling 30-day retention window."""
    now = now or datetime.now()
    cutoff = now - timedelta(days=HISTORY_RETENTION_DAYS)
    cleaned = []

    for item in data:
        timestamp = _parse_history_datetime(item)
        if timestamp is not None and timestamp >= cutoff:
            cleaned.append(item)

    cleaned.sort(
        key=lambda item: _parse_history_datetime(item) or datetime.min,
        reverse=True,
    )
    return cleaned


def _normalize_history_item(item):
    """Normalize current and legacy records for the History UI/API."""
    normalized = dict(item)
    timestamp = _parse_history_datetime(normalized)

    if timestamp:
        normalized["created_at"] = timestamp.isoformat(timespec="seconds")
        normalized["time"] = timestamp.strftime("%d-%m-%Y %I:%M %p")

    normalized.setdefault("type", "opened")
    normalized.setdefault("status", "not_applicable")
    normalized.setdefault("status_message", "")

    # Records created before actor tracking existed are kept for admin review
    # but are not attributed to a current anonymous user.
    normalized.setdefault("actor_type", "legacy")
    normalized.setdefault("actor_id", "legacy")
    normalized.setdefault("actor_label", "Legacy User")

    if normalized.get("status") == "not_applicable" and normalized.get("module") == "AI Assistant":
        normalized["status"] = "legacy_unknown"
        normalized["status_message"] = "Response status not recorded"

    return normalized


def add_history(
    module,
    activity,
    history_type="opened",
    status="not_applicable",
    status_message=None,
    details=None,
    actor_type="user",
    actor_id="anonymous",
    actor_label="User",
):
    """Create a structured history record and return its unique id."""
    if not module or not activity:
        return None

    now = datetime.now()
    item = {
        "id": f"history-{now.strftime('%Y%m%d%H%M%S%f')}",
        "created_at": now.isoformat(timespec="seconds"),
        "time": now.strftime("%d-%m-%Y %I:%M %p"),
        "module": str(module),
        "type": str(history_type),
        "activity": str(activity),
        "status": str(status),
        "status_message": status_message or "",
        "actor_type": str(actor_type),
        "actor_id": str(actor_id),
        "actor_label": str(actor_label),
    }

    if details is not None:
        item["details"] = details

    with _history_lock:
        history = _cleanup_history(load_json("history.json"), now=now)
        history.append(item)
        history = _cleanup_history(history, now=now)
        save_json("history.json", history)

    return item["id"]


def update_history(history_id, status, status_message=None):
    """Update the outcome of an existing history record."""
    if not history_id:
        return False

    with _history_lock:
        history = _cleanup_history(load_json("history.json"))
        updated = False

        for item in history:
            if item.get("id") == history_id:
                item["status"] = str(status)
                item["status_message"] = status_message or ""
                updated = True
                break

        if updated:
            save_json("history.json", history)

        return updated


def get_history(actor_id=None, include_legacy=False, status_filter=None):
    """Return retained history, optionally scoped to an actor/status."""
    with _history_lock:
        history = _cleanup_history(load_json("history.json"))
        normalized = [_normalize_history_item(item) for item in history]

        if normalized != history:
            save_json("history.json", normalized)

    if actor_id is not None:
        normalized = [
            item
            for item in normalized
            if item.get("actor_id") == actor_id
            or (include_legacy and item.get("actor_type") == "legacy")
        ]

    if status_filter == "responded":
        normalized = [item for item in normalized if item.get("status") == "success"]
    elif status_filter == "not_responded":
        normalized = [
            item
            for item in normalized
            if item.get("status") in {"error", "pending", "legacy_unknown"}
        ]

    return normalized
