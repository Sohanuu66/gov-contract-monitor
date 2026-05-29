"""
seen_ids.py
Tracks already-alerted Award IDs with a timestamp.
Entries older than SEEN_IDS_TTL_DAYS are automatically pruned on every run
so the JSON never grows unboundedly.

Storage format:
  {
    "CONT_AWD_XXXXX": "2026-05-27",
    ...
  }
"""

import json
import os
from datetime import datetime, timedelta, timezone
from config import SEEN_IDS_FILE, SEEN_IDS_TTL_DAYS


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _cutoff_date() -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(days=SEEN_IDS_TTL_DAYS)
    return cutoff.strftime("%Y-%m-%d")


def load_seen() -> dict[str, str]:
    """Load seen IDs from disk. Returns {award_id: date_alerted}."""
    if not os.path.exists(SEEN_IDS_FILE):
        return {}
    with open(SEEN_IDS_FILE, "r") as f:
        try:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
        except json.JSONDecodeError:
            return {}


def save_seen(seen: dict[str, str]) -> None:
    """Persist seen IDs to disk."""
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(seen, f, indent=2, sort_keys=True)


def prune_old_entries(seen: dict[str, str]) -> dict[str, str]:
    """
    Remove entries older than SEEN_IDS_TTL_DAYS.
    Called automatically on every run to keep the file lean.
    """
    cutoff = _cutoff_date()
    before = len(seen)
    seen = {k: v for k, v in seen.items() if v >= cutoff}
    pruned = before - len(seen)
    if pruned:
        print(f"[seen_ids] Pruned {pruned} entries older than {SEEN_IDS_TTL_DAYS} days.")
    return seen


def filter_new(awards: list[dict], seen: dict[str, str]) -> list[dict]:
    """Return only awards not previously alerted."""
    return [a for a in awards if a.get("Award ID") not in seen]


def mark_seen(awards: list[dict], seen: dict[str, str]) -> dict[str, str]:
    """Add new award IDs to seen with today's date."""
    today = _today()
    for award in awards:
        award_id = award.get("Award ID")
        if award_id:
            seen[award_id] = today
    return seen