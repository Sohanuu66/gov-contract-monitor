"""
fetch_awards.py
Queries USAspending API for NEW contracts (Mod == "0") exceeding $50M.
Endpoint: POST /api/v2/search/spending_by_transaction/

Why this endpoint?
- Operates at transaction level — every new contract = a new transaction
- "Mod" field: "0" = base contract (FPDS documented), anything else = modification
- Pagination: loops until page_metadata.hasNext == False
"""

import requests
from datetime import datetime, timedelta, timezone

API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"
MIN_AMOUNT = 50_000_000
PAGE_LIMIT = 100  # max per page
HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "contract-alert/1.0 (github-actions)",
}


def build_payload(start_date: str, end_date: str, page: int = 1) -> dict:
    return {
        "limit": PAGE_LIMIT,
        "page": page,
        "sort": "Action Date",
        "order": "desc",
        "filters": {
            # A=BPA/Call, B=Purchase Order, C=Delivery Order, D=Definitive Contract
            "award_type_codes": ["A", "B", "C", "D"],
            "time_period": [{"start_date": start_date, "end_date": end_date}],
            "award_amounts": [{"lower_bound": MIN_AMOUNT}],
        },
        "fields": [
            "Award ID",
            "Recipient Name",
            "Action Date",
            "Transaction Amount",
            "Awarding Agency",
            "Awarding Sub Agency",
            "Award Type",
            "Transaction Description",
            "Mod",
        ],
    }


def filter_new_contracts(transactions: list[dict]) -> list[dict]:
    """
    Keep only base contracts (Mod == "0").
    FPDS docs: Mod defaults to "0" on a base contract.
    Any other value (P00001, P00022, 621 etc.) = modification to existing contract.
    """
    return [t for t in transactions if str(t.get("Mod", "")).strip() == "0"]


def fetch_awards(hours_back: int = 25) -> list[dict]:
    """
    Fetch all NEW contracts (Mod == "0") > $50M actioned in the last `hours_back` hours.

    Uses a 25h window (not 2h) because:
    - API date filters are date-only (YYYY-MM-DD), not datetime
    - 25h ensures we always cover yesterday + today regardless of run time
    - seen_ids.json deduplication guarantees no duplicate alerts

    Paginates automatically — calls API repeatedly until hasNext == False.
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours_back)

    start_date = start.strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    print(f"[fetch] Querying {start_date} → {end_date} (page by page, 100/page)...")

    all_transactions = []
    page = 1

    while True:
        payload = build_payload(start_date, end_date, page)

        try:
            response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise RuntimeError(f"USAspending API request failed (page {page}): {e}") from e

        data = response.json()
        results = data.get("results", [])
        all_transactions.extend(results)

        has_next = data.get("page_metadata", {}).get("hasNext", False)
        print(f"[fetch] Page {page} → {len(results)} results | hasNext: {has_next}")

        if not has_next or not results:
            break

        page += 1

    print(f"[fetch] Total fetched across all pages: {len(all_transactions)}")

    # Filter to base contracts only
    fresh = filter_new_contracts(all_transactions)
    print(f"[fetch] After Mod==0 filter: {len(fresh)} new base contracts")

    return fresh