"""
main.py
Entrypoint for the USAspending contract alert system.

Flow:
  1. Fetch transactions from /api/v2/search/spending_by_transaction/
  2. Filter Mod == "0" (base contracts only — no modifications to old contracts)
  3. Filter out already-alerted Award IDs via seen_ids.json
  4. Send email alert if new contracts found
  5. Update seen_ids.json (GitHub Actions commits this back to the repo)
"""

import sys
from dotenv import load_dotenv

# Loads .env when running locally — no-op in GitHub Actions (secrets are already env vars)
load_dotenv()

from fetch_awards import fetch_awards
from seen_ids import load_seen, save_seen, filter_new, mark_seen, prune_old_entries
from alert import send_alert
from config import AMOUNT_THRESHOLD_LABEL


def main():
    print(f"[main] Fetching new base contracts (Mod==0) > ${AMOUNT_THRESHOLD_LABEL} from USAspending...")
    try:
        awards = fetch_awards()
    except RuntimeError as e:
        print(f"[main] ERROR: {e}")
        sys.exit(1)

    print(f"[main] {len(awards)} fresh contract(s) found after Mod==0 filter.")

    seen = load_seen()
    new_awards = filter_new(awards, seen)
    print(f"[main] {len(new_awards)} not previously alerted.")

    if not new_awards:
        print("[main] Nothing new to alert. Exiting.")
        return

    print(f"[main] Sending alert for {len(new_awards)} contract(s)...")
    send_alert(new_awards)

    seen = mark_seen(new_awards, seen)
    seen = prune_old_entries(seen)
    save_seen(seen)
    print(f"[main] seen_ids.json updated ({len(seen)} total tracked IDs).")


if __name__ == "__main__":
    main()