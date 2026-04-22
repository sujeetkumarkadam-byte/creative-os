import gspread
from google.oauth2.service_account import Credentials
import streamlit as st
import pandas as pd
from datetime import datetime

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ASSETS      = "Master_Asset_Registry"       # legacy — archived read-only
SHEET_INHOUSE     = "Inhouse_Live_Assets"         # new — only inhouse ads that went live
SHEET_EXPERIMENTS = "Experiment_Log"              # now: Stage 1 briefs for statics
SHEET_SOURCES     = "Source_Story_Library"
SHEET_WEEKLY      = "Weekly_Volume"
SHEET_META_ADS    = "Meta Ads"                    # IMPORTRANGE'd — all Perf ads
SHEET_INFLUENCER  = "Live Entries 2026"           # IMPORTRANGE'd — influencer ads only

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
    # Stage-1 brief fields (for statics flow)
    "Marketing Angle", "Situational Driver", "AI Tool Used",
    "Reference Image Link", "Promoted To Asset ID",
]

# Inhouse live assets — the only place we track live inhouse ads going forward.
# Scoped to "this went live" → no drafts, no variants pending, no briefs.
# Format drives which subtype column matters: Video → Video Subtype,
# Static → Static Subtype. Hook/Emotional Arc/Archetype apply to video only.
INHOUSE_LIVE_HEADERS = [
    # Identity
    "Asset ID", "AD CODE", "Published Date",
    "Parent Asset ID", "Variant #", "What's Different", "A/B Pair ID",
    # Format & type
    "Product", "Bucket", "Format", "Video Subtype", "Static Subtype",
    # Taxonomy — all formats
    "Cohort", "Belief", "Marketing Angle", "Situational Driver",
    "Funnel Stage", "Influence Mode", "CTA Style",
    # Video-only
    "Hook Type", "Emotional Arc", "Creator Archetype",
    # Static-only
    "Visual Style",
    # People & provenance
    "Creator / Consumer Name", "Source Interview ID", "Experiment ID",
    # Publishing
    "Campaign Name", "Ad Set Name", "Drive Link", "Brief Link",
    "Reference Image Link", "Notes",
    # Performance — all-time
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
    """Legacy — reads the old Master_Asset_Registry. Prefer load_inhouse_live()."""
    try:
        records = _ws(SHEET_ASSETS).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=ASSET_HEADERS)
    except Exception as e:
        st.error(f"Could not load assets: {e}")
        return pd.DataFrame(columns=ASSET_HEADERS)


def load_inhouse_live() -> pd.DataFrame:
    """Reads the new Inhouse_Live_Assets sheet (post-migration source of truth)."""
    try:
        records = _ws(SHEET_INHOUSE).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=INHOUSE_LIVE_HEADERS)
    except Exception as e:
        st.error(f"Could not load inhouse live assets: {e}")
        return pd.DataFrame(columns=INHOUSE_LIVE_HEADERS)


def save_inhouse_live(data: dict):
    """Append one inhouse-live-asset row."""
    row = [data.get(h, "") for h in INHOUSE_LIVE_HEADERS]
    _ws(SHEET_INHOUSE).append_row(row, value_input_option="USER_ENTERED")


def ensure_inhouse_sheet():
    """Create Inhouse_Live_Assets with headers if it doesn't exist yet."""
    ss = _client().open(st.secrets["spreadsheet_name"])
    existing = {w.title for w in ss.worksheets()}
    if SHEET_INHOUSE in existing:
        return False  # already exists
    ws = ss.add_worksheet(
        title=SHEET_INHOUSE,
        rows=2000,
        cols=len(INHOUSE_LIVE_HEADERS) + 2,
    )
    ws.append_row(INHOUSE_LIVE_HEADERS)
    return True


def load_meta_ads() -> pd.DataFrame:
    """Reads the IMPORTRANGE'd Meta Ads sheet. Columns detected dynamically."""
    try:
        vals = _ws(SHEET_META_ADS).get_all_values()
        if not vals or len(vals) < 2:
            return pd.DataFrame()
        # Find the header row — try row 1 first, fall back to row 2
        for hdr_idx in [0, 1]:
            hdrs = vals[hdr_idx]
            if sum(1 for h in hdrs if h.strip()) >= 3:
                df = pd.DataFrame(vals[hdr_idx + 1:], columns=hdrs)
                # Drop fully-empty columns (from IMPORTRANGE padding)
                df = df.loc[:, [c for c in df.columns if c.strip()]]
                return df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Could not load Meta Ads sheet: {e}")
        return pd.DataFrame()


def load_influencer_ads() -> pd.DataFrame:
    """Reads the Live Entries 2026 sheet. Columns detected dynamically."""
    try:
        vals = _ws(SHEET_INFLUENCER).get_all_values()
        if not vals or len(vals) < 2:
            return pd.DataFrame()
        for hdr_idx in [0, 1]:
            hdrs = vals[hdr_idx]
            if sum(1 for h in hdrs if h.strip()) >= 3:
                df = pd.DataFrame(vals[hdr_idx + 1:], columns=hdrs)
                df = df.loc[:, [c for c in df.columns if c.strip()]]
                return df
        return pd.DataFrame()
    except Exception as e:
        st.warning(f"Could not load Live Entries 2026 sheet: {e}")
        return pd.DataFrame()


def migrate_master_to_inhouse() -> tuple[int, int, list]:
    """One-off: copy every row from Master_Asset_Registry → Inhouse_Live_Assets.
    Maps legacy columns onto new schema. Returns (migrated, skipped, errors)."""
    ensure_inhouse_sheet()
    src = load_assets()
    if src.empty:
        return 0, 0, []

    dst_ws = _ws(SHEET_INHOUSE)
    migrated, skipped, errors = 0, 0, []

    # Legacy column → new column mapping (where they differ)
    for _, row in src.iterrows():
        try:
            creative_type = str(row.get("Creative Type", "")).strip()
            # Infer Format from legacy Creative Type
            if creative_type in {"Consumer Testimonial", "Brand-Led", "Founder-Led",
                                 "Skit", "Event Coverage", "AI-Video"}:
                fmt = "Video"
                video_subtype = creative_type
                static_subtype = ""
            elif creative_type in {"Static", "Carousel", "GIF", "AI-Static"}:
                fmt = "Static"
                video_subtype = ""
                static_subtype = creative_type  # rough — user can retag
            else:
                fmt = ""
                video_subtype = creative_type
                static_subtype = ""

            new_row = {
                "Asset ID": row.get("Asset ID", ""),
                "AD CODE": row.get("Meta Ad ID", ""),
                "Published Date": row.get("Published Date", ""),
                "Parent Asset ID": row.get("Parent Asset ID", ""),
                "Variant #": row.get("Variant #", ""),
                "What's Different": row.get("What's Different", ""),
                "A/B Pair ID": row.get("A/B Pair ID", ""),
                "Product": row.get("Product", ""),
                "Bucket": row.get("Bucket", ""),
                "Format": fmt,
                "Video Subtype": video_subtype,
                "Static Subtype": static_subtype,
                "Cohort": row.get("Cohort", ""),
                "Belief": row.get("Belief", ""),
                "Marketing Angle": row.get("Marketing Angle", ""),
                "Situational Driver": row.get("Situational Driver", ""),
                "Funnel Stage": row.get("Funnel Stage", ""),
                "Influence Mode": row.get("Influence Mode", ""),
                "CTA Style": row.get("CTA Style", ""),
                "Hook Type": row.get("Hook Type", ""),
                "Emotional Arc": row.get("Emotional Arc", ""),
                "Creator Archetype": row.get("Creator Archetype", ""),
                "Visual Style": row.get("Visual Style", ""),
                "Creator / Consumer Name": row.get("Creator / Consumer Name", ""),
                "Source Interview ID": row.get("Source Interview ID", ""),
                "Experiment ID": row.get("Experiment ID", ""),
                "Campaign Name": row.get("Campaign Name", ""),
                "Ad Set Name": row.get("Ad Set Name", ""),
                "Drive Link": row.get("Drive Link", ""),
                "Brief Link": row.get("Brief Link", ""),
                "Reference Image Link": "",  # new field — legacy had none
                "Notes": row.get("Notes", ""),
            }
            # Copy all performance columns through (same names)
            for col in INHOUSE_LIVE_HEADERS:
                if col not in new_row and col in src.columns:
                    new_row[col] = row.get(col, "")

            values = [new_row.get(h, "") for h in INHOUSE_LIVE_HEADERS]
            dst_ws.append_row(values, value_input_option="USER_ENTERED")
            migrated += 1
        except Exception as e:
            errors.append(f"{row.get('Asset ID', '?')}: {e}")
            skipped += 1

    return migrated, skipped, errors


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


def next_asset_id(product: str, creative_type_or_format: str, existing: list) -> str:
    """Generate next Asset ID. Accepts either a legacy Creative Type or the
    new Format string ('Video' / 'Static'). Both map to V or S prefix."""
    p = _PRODUCT_CODE.get(product, "TSS")
    val = (creative_type_or_format or "").strip()
    if val == "Video" or val in _VIDEO_TYPES:
        f = "V"
    else:
        f = "S"
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
        SHEET_INHOUSE:     INHOUSE_LIVE_HEADERS,
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
