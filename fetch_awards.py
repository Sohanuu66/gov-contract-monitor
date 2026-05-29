"""
fetch_awards.py
Queries USAspending API for NEW base contracts (Mod == "0") exceeding the
configured minimum amount. Paginates automatically until all results are fetched.

Why spending_by_transaction?
- Transaction-level endpoint — each new contract = one transaction
- Mod == "0" is FPDS-documented as the base contract (never a modification)
"""

import requests
from datetime import datetime, timedelta, timezone
from config import (
    API_URL,
    API_HEADERS,
    AWARD_TYPE_CODES,
    MIN_CONTRACT_AMOUNT,
    API_FIELDS,
    PAGE_LIMIT,
    HOURS_BACK,
    API_TIMEOUT,
)


def build_payload(start_date: str, end_date: str, page: int = 1) -> dict:
    return {
        "limit": PAGE_LIMIT,
        "page": page,
        "sort": "Action Date",
        "order": "desc",
        "filters": {
            "award_type_codes": AWARD_TYPE_CODES,
            "time_period": [{"start_date": start_date, "end_date": end_date}],
            "award_amounts": [{"lower_bound": MIN_CONTRACT_AMOUNT}],
        },
        "fields": API_FIELDS,
    }


def filter_new_contracts(transactions: list[dict]) -> list[dict]:
    """
    Keep only base contracts (Mod == "0").
    FPDS documentation: Mod defaults to "0" on a base contract.
    Any other value = modification to an existing contract.
    """
    return [t for t in transactions if str(t.get("Mod", "")).strip() == "0"]


def fetch_awards(hours_back: int = HOURS_BACK) -> list[dict]:
    """
    Fetch all new base contracts > MIN_CONTRACT_AMOUNT in the last `hours_back` hours.
    Paginates until page_metadata.hasNext == False.
    """
    now = datetime.now(timezone.utc)
    start_date = (now - timedelta(hours=hours_back)).strftime("%Y-%m-%d")
    end_date = now.strftime("%Y-%m-%d")

    print(f"[fetch] Querying {start_date} → {end_date} ...")

    all_transactions = []
    page = 1

    while True:
        payload = build_payload(start_date, end_date, page)

        try:
            response = requests.post(API_URL, json=payload, headers=API_HEADERS, timeout=API_TIMEOUT)
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

    print(f"[fetch] Total across all pages: {len(all_transactions)}")

    fresh = filter_new_contracts(all_transactions)
    print(f"[fetch] After Mod==0 filter: {len(fresh)} new base contracts")

    return fresh