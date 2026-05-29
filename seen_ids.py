"""
seen_ids.py
Tracks already-alerted Award IDs using a local JSON file.
This file is committed back to the repo by the GitHub Actions workflow,
so state persists across hourly runs.
"""

import json
import os

SEEN_FILE = "seen_ids.json"


def load_seen() -> set[str]:
    if not os.path.exists(SEEN_FILE):
        return set()
    with open(SEEN_FILE, "r") as f:
        return set(json.load(f))


def save_seen(seen: set[str]) -> None:
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen), f, indent=2)


def filter_new(awards: list[dict], seen: set[str]) -> list[dict]:
    """Return only awards not previously alerted."""
    return [a for a in awards if a.get("Award ID") not in seen]


def mark_seen(awards: list[dict], seen: set[str]) -> set[str]:
    """Add new award IDs to the seen set."""
    for award in awards:
        award_id = award.get("Award ID")
        if award_id:
            seen.add(award_id)
    return seen
