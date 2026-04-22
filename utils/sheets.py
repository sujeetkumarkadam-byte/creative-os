import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ASSETS      = "Master_Asset_Registry"
SHEET_EXPERIMENTS = "Experiment_Log"
SHEET_SOURCES     = "Source_Story_Library"
SHEET_WEEKLY      = "Weekly_Volume"

ASSET_HEADERS = [
    "Asset ID", "Parent Asset ID", "Variant #", "What's Different",
    "A/B Pair ID", "Status", "Created Date", "Published Date",
    "Product", "Bucket", "Channel", "Creative Type",
    "Cohort", "Belief", "Marketing Angle", "Situational Driver",
    "Hook Type", "Emotional Arc", "Funnel Stage",
    "Creator Archetype", "Influence Mode", "Visual Style", "CTA Style",
    "Source Interview ID", "Creator / Consumer Name", "Experiment ID",
    "Meta Ad ID", "Campaign Name", "Ad Set Name",
    "Drive Link", "Brief Link", "Notes",
    # All-time performance
    "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach",
    "CTR", "CPC", "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    # L30
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
    # L7
    "ROAS (L7)", "Amount Spent (L7)", "Revenue (L7)", "Avg Cost Per Reach (L7)",
    "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)",
    "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
]

EXPERIMENT_HEADERS = [
    "Experiment ID", "Product", "Core Message", "Belief", "Cohort",
    "Funnel Stage", "Variable Being Tested", "What Stays Fixed", "Hypothesis",
    "Control Asset ID", "Variant Asset IDs", "Decision Rule",
    "Start Date", "Review Date", "Status", "Result", "Next Action", "Notes",
]

SOURCE_HEADERS = [
    "Source ID", "Consumer Name/Code", "Product", "Source Type",
    "Recording Link", "Transcript Link", "Story Strength",
    "Before-State Summary", "Trigger / Context", "Key Quotes",
    "Cohort Match", "Beliefs Supported",
    "Total Angles Extracted", "Total Variants Published",
    "Unused Angles Remaining", "Best Asset ID", "Notes",
]


@st.cache_resource
def _client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]), scopes=SCOPES
    )
    return gspread.authorize(creds)


def _ws(sheet_name: str):
    return _client().open(st.secrets["spreadsheet_name"]).worksheet(sheet_name)


# ── READ ──────────────────────────────────────────────────────────────────────

def load_assets() -> pd.DataFrame:
    try:
        records = _ws(SHEET_ASSETS).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=ASSET_HEADERS)
    except Exception as e:
        st.error(f"Could not load assets: {e}")
        return pd.DataFrame(columns=ASSET_HEADERS)


def load_experiments() -> pd.DataFrame:
    try:
        records = _ws(SHEET_EXPERIMENTS).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=EXPERIMENT_HEADERS)
    except Exception as e:
        st.error(f"Could not load experiments: {e}")
        return pd.DataFrame(columns=EXPERIMENT_HEADERS)


def load_sources() -> pd.DataFrame:
    try:
        records = _ws(SHEET_SOURCES).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=SOURCE_HEADERS)
    except Exception as e:
        st.error(f"Could not load sources: {e}")
        return pd.DataFrame(columns=SOURCE_HEADERS)


# ── WRITE ─────────────────────────────────────────────────────────────────────

def save_asset(data: dict):
    row = [data.get(h, "") for h in ASSET_HEADERS]
    _ws(SHEET_ASSETS).append_row(row, value_input_option="USER_ENTERED")


def save_experiment(data: dict):
    row = [data.get(h, "") for h in EXPERIMENT_HEADERS]
    _ws(SHEET_EXPERIMENTS).append_row(row, value_input_option="USER_ENTERED")


def save_source(data: dict):
    row = [data.get(h, "") for h in SOURCE_HEADERS]
    _ws(SHEET_SOURCES).append_row(row, value_input_option="USER_ENTERED")


def update_asset(asset_id: str, field: str, value):
    ws = _ws(SHEET_ASSETS)
    cell = ws.find(asset_id)
    if cell:
        col = ASSET_HEADERS.index(field) + 1
        ws.update_cell(cell.row, col, value)


# ── ID GENERATION ─────────────────────────────────────────────────────────────

_PRODUCT_CODE = {
    "RCF": "RCF",
    "Clear Protect Gel Sunscreen": "CPGS",
    "Barrier Repair Gel Moisturiser": "BRGM",
    "Liquid Pimple Patch": "LPP",
    "Effortless Melting Cleanser": "EMC",
    "Spot Fade Serum": "SFS",
}

_VIDEO_TYPES = {
    "Consumer Testimonial", "Brand-Led", "Founder-Led",
    "Skit", "Event Coverage", "AI-Video",
}


def next_asset_id(product: str, creative_type: str, existing: list) -> str:
    p = _PRODUCT_CODE.get(product, "TSS")
    f = "V" if creative_type in _VIDEO_TYPES else "S"
    prefix = f"{p}-{f}-"
    nums = [int(i.split("-")[-1]) for i in existing
            if i.startswith(prefix) and i.split("-")[-1].isdigit()]
    return f"{prefix}{str(max(nums, default=0) + 1).zfill(3)}"


def next_experiment_id(existing: list) -> str:
    nums = [int(i.split("-")[-1]) for i in existing
            if i.startswith("EXP-") and i.split("-")[-1].isdigit()]
    return f"EXP-{str(max(nums, default=0) + 1).zfill(3)}"


def next_source_id(existing: list) -> str:
    nums = [int(i.split("-")[-1]) for i in existing
            if i.startswith("SRC-") and i.split("-")[-1].isdigit()]
    return f"SRC-{str(max(nums, default=0) + 1).zfill(3)}"


# ── SHEET INITIALISATION ──────────────────────────────────────────────────────

def initialise_sheets():
    """Create all sheets with headers on first run."""
    spreadsheet = _client().open(st.secrets["spreadsheet_name"])
    existing = {ws.title for ws in spreadsheet.worksheets()}

    to_create = {
        SHEET_ASSETS:      ASSET_HEADERS,
        SHEET_EXPERIMENTS: EXPERIMENT_HEADERS,
        SHEET_SOURCES:     SOURCE_HEADERS,
        SHEET_WEEKLY: [
            "Week Start", "Week End", "Total", "Videos", "Statics",
            "RCF", "CPGS", "BRGM", "Diversity Score", "Notes",
        ],
    }

    for name, headers in to_create.items():
        if name not in existing:
            ws = spreadsheet.add_worksheet(title=name, rows=2000, cols=len(headers) + 5)
            ws.append_row(headers)
    return True
