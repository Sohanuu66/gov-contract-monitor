"""
config.py
Central configuration for the USAspending Contract Alert system.
All editable values live here — the rest of the code stays untouched.
"""

# ─────────────────────────────────────────────
# API
# ─────────────────────────────────────────────

API_URL = "https://api.usaspending.gov/api/v2/search/spending_by_transaction/"

API_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "contract-alert/1.0 (github-actions)",
}

# Contract type codes to monitor
# A = BPA Call, B = Purchase Order, C = Delivery Order, D = Definitive Contract
AWARD_TYPE_CODES = ["A", "B", "C", "D"]

# Only alert on contracts above this value (in USD)
MIN_CONTRACT_AMOUNT = 50_000_000  # $50M

# Fields to request from the API
API_FIELDS = [
    "Award ID",
    "Recipient Name",
    "Action Date",
    "Transaction Amount",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Award Type",
    "Transaction Description",
    "Mod",
]

# Results per page (API max is 100)
PAGE_LIMIT = 100

# How many hours back to query (7 * 24 = 168 hours / 7 days)
HOURS_BACK = 7 * 24

# Timeout for API requests in seconds
API_TIMEOUT = 30


# ─────────────────────────────────────────────
# FEATURES: SUMMARY & CSV
# ─────────────────────────────────────────────

# Toggle executive summary at the top of emails
ENABLE_EXECUTIVE_SUMMARY = True

# Toggle CSV attachment
ENABLE_CSV_ATTACHMENT = True
CSV_ATTACHMENT_FILENAME = "usaspending_contracts_{date}.csv"

# Columns to include in the CSV attachment
# Format: (CSV_Header, API_Field_Key)
CSV_COLUMNS = [
    ("Award Date",          "Action Date"),
    ("Recipient Name",      "Recipient Name"),
    ("Transaction Amount",  "Transaction Amount"),
    ("Award ID",            "Award ID"),
    ("Awarding Agency",      "Awarding Agency"),
    ("Description",         "Transaction Description"),
]


# ─────────────────────────────────────────────
# DEDUPLICATION
# ─────────────────────────────────────────────

SEEN_IDS_FILE = "seen_ids.json"

# Delete seen IDs older than this many days to prevent the JSON from growing forever
# Rationale: USAspending typically posts contracts within 3 days of award.
# 30 days gives a safe buffer — any contract older than that won't re-appear as new.
SEEN_IDS_TTL_DAYS = 30


# ─────────────────────────────────────────────
# EMAIL ALERT
# ─────────────────────────────────────────────

EMAIL_SUBJECT_TEMPLATE = "🚨 {count} New US Gov Contract{plural} > ${threshold}"

# Threshold label shown in email subject (human-readable)
AMOUNT_THRESHOLD_LABEL = "50M"

# Footer source link shown in email
SOURCE_URL = "https://www.usaspending.gov"

# HTML table columns to show in the alert email
# Each entry: (header_label, data_key)
EMAIL_TABLE_COLUMNS = [
    ("Company",      "Recipient Name"),
    ("Amount",       "Transaction Amount"),
    ("Action Date",  "Action Date"),
    ("Award ID",     "Award ID"),
    ("Agency",       "Awarding Agency"),
    ("Type",         "Award Type"),
]

# Plain text fields shown in email body
EMAIL_PLAIN_FIELDS = [
    ("Company",      "Recipient Name"),
    ("Amount",       "Transaction Amount"),
    ("Action Date",  "Action Date"),
    ("Award ID",     "Award ID"),
    ("Agency",       "Awarding Agency"),
    ("Sub-Agency",   "Awarding Sub Agency"),
    ("Type",         "Award Type"),
    ("Description",  "Transaction Description"),
]