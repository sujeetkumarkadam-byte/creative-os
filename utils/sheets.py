import re

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ASSETS = "Master_Asset_Registry"
SHEET_INHOUSE = "Inhouse_Live_Assets"
SHEET_EXPERIMENTS = "Experiment_Log"
SHEET_SOURCES = "Source_Story_Library"
SHEET_WEEKLY = "Weekly_Volume"
SHEET_META_ADS = "Meta Ads"
SHEET_INFLUENCER = "Live Entries 2026"

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
    "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach",
    "CTR", "CPC", "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
    "ROAS (L7)", "Amount Spent (L7)", "Revenue (L7)", "Avg Cost Per Reach (L7)",
    "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)",
    "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
]

EXPERIMENT_HEADERS = [
    "Experiment ID", "Product", "Core Message", "Belief", "Cohort",
    "Funnel Stage", "Variable Being Tested", "What Stays Fixed", "Hypothesis",
    "Control Asset ID", "Variant Asset IDs", "Decision Rule",
    "Start Date", "Review Date", "Status", "Result", "Next Action", "Notes",
    "Marketing Angle", "Situational Driver", "AI Tool Used",
    "Reference Image Link", "Promoted To Asset ID",
]

INHOUSE_LIVE_HEADERS = [
    "Asset ID", "AD CODE", "Published Date",
    "Parent Asset ID", "Variant #", "What's Different", "A/B Pair ID",
    "Product", "Bucket", "Format", "Video Subtype", "Static Subtype",
    "Cohort", "Belief", "Marketing Angle", "Situational Driver",
    "Funnel Stage", "Influence Mode", "CTA Style",
    "Hook Type", "Emotional Arc", "Creator Archetype",
    "Visual Style",
    "Creator / Consumer Name", "Source Interview ID", "Experiment ID",
    "Campaign Name", "Ad Set Name", "Drive Link", "Brief Link",
    "Reference Image Link", "Notes",
    "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach",
    "CTR", "CPC", "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
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

AD_CODE_RE = re.compile(r"\bAD\s*[-_]?\s*(\d+)\b", re.IGNORECASE)


@st.cache_resource
def _client():
    creds = Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )
    return gspread.authorize(creds)


def _ws(sheet_name: str):
    return _client().open(st.secrets["spreadsheet_name"]).worksheet(sheet_name)


def _clean_header(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("|", " ")).strip()


def normalize_ad_code(value) -> str:
    raw = str(value or "").strip()
    if not raw or raw.lower() in {"nan", "none"}:
        return ""
    match = AD_CODE_RE.search(raw)
    if match:
        return f"AD {int(match.group(1))}"
    digits = re.fullmatch(r"\d+", raw.replace(",", ""))
    if digits:
        return f"AD {int(raw.replace(',', ''))}"
    return re.sub(r"\s+", " ", raw).upper()


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    if series is None or len(series) == 0:
        return pd.Series(dtype="datetime64[ns]")
    cleaned = series.astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA})
    parsed = pd.to_datetime(cleaned, errors="coerce", dayfirst=True)
    return parsed


def first_present_column(df: pd.DataFrame, *candidates: str):
    for candidate in candidates:
        if candidate and candidate in df.columns:
            return candidate
    return None


def infer_format(value: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    video_words = ("video", "reel", "testimonial", "founder", "skit", "ugc", "event")
    static_words = ("static", "carousel", "gif", "image", "banner", "card")
    if any(word in text for word in video_words):
        return "Video"
    if any(word in text for word in static_words):
        return "Static"
    return ""


def _dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    deduped: list[str] = []
    for header in headers:
        key = header or "_blank"
        count = seen.get(key, 0) + 1
        seen[key] = count
        deduped.append(key if count == 1 else f"{key}_{count}")
    return deduped


def _detect_ad_code_index(rows: list[list[str]], headers: list[str]):
    best_idx = None
    best_score = 0
    width = max((len(r) for r in rows), default=len(headers))

    for idx in range(width):
        header = headers[idx] if idx < len(headers) else ""
        values = [
            row[idx].strip() for row in rows[:80]
            if idx < len(row) and str(row[idx]).strip()
        ]
        match_count = sum(1 for value in values if AD_CODE_RE.search(value))
        if "ad code" in header.lower():
            match_count += 100
        if match_count > best_score:
            best_idx = idx
            best_score = match_count

    if best_idx is not None and best_score > 0:
        return best_idx

    # Fallback to the legacy guessed column if detection finds nothing.
    return 37 if len(headers) > 37 else None


def _drop_truly_blank_columns(df: pd.DataFrame) -> pd.DataFrame:
    keep = []
    for column in df.columns:
        if column == "AD CODE":
            keep.append(column)
            continue
        if column.startswith("_blank"):
            values = df[column].astype(str).str.strip()
            if (values != "").any():
                keep.append(column)
            continue
        keep.append(column)
    return df[keep]


def load_assets() -> pd.DataFrame:
    try:
        records = _ws(SHEET_ASSETS).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=ASSET_HEADERS)
    except Exception as exc:
        st.error(f"Could not load assets: {exc}")
        return pd.DataFrame(columns=ASSET_HEADERS)


def load_inhouse_live() -> pd.DataFrame:
    try:
        records = _ws(SHEET_INHOUSE).get_all_records()
        df = pd.DataFrame(records) if records else pd.DataFrame(columns=INHOUSE_LIVE_HEADERS)
        if "AD CODE" in df.columns:
            df["AD CODE"] = df["AD CODE"].map(normalize_ad_code)
        return df
    except Exception as exc:
        st.error(f"Could not load inhouse live assets: {exc}")
        return pd.DataFrame(columns=INHOUSE_LIVE_HEADERS)


def save_inhouse_live(data: dict):
    row = [data.get(header, "") for header in INHOUSE_LIVE_HEADERS]
    _ws(SHEET_INHOUSE).append_row(row, value_input_option="USER_ENTERED")


def ensure_inhouse_sheet():
    spreadsheet = _client().open(st.secrets["spreadsheet_name"])
    existing = {ws.title for ws in spreadsheet.worksheets()}
    if SHEET_INHOUSE in existing:
        return False
    ws = spreadsheet.add_worksheet(
        title=SHEET_INHOUSE,
        rows=2000,
        cols=len(INHOUSE_LIVE_HEADERS) + 2,
    )
    ws.append_row(INHOUSE_LIVE_HEADERS)
    return True


def load_meta_ads() -> pd.DataFrame:
    try:
        values = _ws(SHEET_META_ADS).get_all_values()
        if len(values) < 3:
            return pd.DataFrame()

        header_row_idx = 1 if len(values) > 1 else 0
        raw_headers = [_clean_header(value) for value in values[header_row_idx]]
        rows = values[header_row_idx + 1:]

        ad_code_idx = _detect_ad_code_index(rows, raw_headers)
        if ad_code_idx is not None and ad_code_idx < len(raw_headers):
            raw_headers[ad_code_idx] = "AD CODE"

        headers = _dedupe_headers(raw_headers)
        df = pd.DataFrame(rows, columns=headers)
        df = _drop_truly_blank_columns(df)
        if "AD CODE" in df.columns:
            df["AD CODE"] = df["AD CODE"].map(normalize_ad_code)
        return df
    except Exception as exc:
        st.warning(f"Could not load Meta Ads sheet: {exc}")
        return pd.DataFrame()


def load_influencer_ads() -> pd.DataFrame:
    try:
        values = _ws(SHEET_INFLUENCER).get_all_values()
        if len(values) < 2:
            return pd.DataFrame()

        header_row_idx = 0
        if len(values) > 1:
            row0_count = sum(1 for value in values[0] if str(value).strip())
            row1_count = sum(1 for value in values[1] if str(value).strip())
            if row1_count > row0_count:
                header_row_idx = 1

        headers = [_clean_header(value) for value in values[header_row_idx]]
        rows = values[header_row_idx + 1:]
        headers = _dedupe_headers(headers)
        df = pd.DataFrame(rows, columns=headers)
        df = df.loc[:, [column for column in df.columns if column.strip()]]
        ad_col = first_present_column(df, "Ad Code", "AD CODE", "Ad code", "AdCode")
        if ad_col and ad_col != "Ad Code":
            df = df.rename(columns={ad_col: "Ad Code"})
            ad_col = "Ad Code"
        if ad_col:
            df[ad_col] = df[ad_col].map(normalize_ad_code)
        return df
    except Exception as exc:
        st.warning(f"Could not load Live Entries 2026 sheet: {exc}")
        return pd.DataFrame()


def classify_meta_ads(meta_df: pd.DataFrame, inhouse_df: pd.DataFrame, influencer_df: pd.DataFrame) -> pd.DataFrame:
    if meta_df.empty:
        return meta_df.copy()

    out = meta_df.copy()
    if "AD CODE" in out.columns:
        out["AD CODE"] = out["AD CODE"].map(normalize_ad_code)
    else:
        out["AD CODE"] = ""

    inhouse_codes = set()
    if not inhouse_df.empty and "AD CODE" in inhouse_df.columns:
        inhouse_codes = {
            normalize_ad_code(value)
            for value in inhouse_df["AD CODE"].tolist()
            if normalize_ad_code(value)
        }

    influencer_codes = set()
    influencer_col = first_present_column(influencer_df, "Ad Code", "AD CODE", "Ad code", "AdCode")
    if not influencer_df.empty and influencer_col:
        influencer_codes = {
            normalize_ad_code(value)
            for value in influencer_df[influencer_col].tolist()
            if normalize_ad_code(value)
        }

    def _classify(code: str) -> str:
        normalized = normalize_ad_code(code)
        if not normalized:
            return "Unclassified"
        if normalized in influencer_codes:
            return "Influencer"
        if normalized in inhouse_codes:
            return "Inhouse"
        return "Porcellia"

    out["Source"] = out["AD CODE"].map(_classify)
    return out


def build_classified_meta_view(meta_df: pd.DataFrame | None = None,
                               inhouse_df: pd.DataFrame | None = None,
                               influencer_df: pd.DataFrame | None = None) -> pd.DataFrame:
    meta = load_meta_ads() if meta_df is None else meta_df.copy()
    inhouse = load_inhouse_live() if inhouse_df is None else inhouse_df.copy()
    influencer = load_influencer_ads() if influencer_df is None else influencer_df.copy()

    if meta.empty:
        return pd.DataFrame()

    tagged = classify_meta_ads(meta, inhouse, influencer)
    tagged["AD CODE"] = tagged["AD CODE"].map(normalize_ad_code)

    date_col = first_present_column(tagged, "Date [Ad Taken Live]", "Date [Ad Taken Live] ")
    product_col = first_present_column(tagged, "Product")
    creative_type_col = first_present_column(tagged, "Creative Type")
    creative_name_col = first_present_column(tagged, "Creative Name")
    fb_ad_name_col = first_present_column(tagged, "FB Ad Name")
    funnel_col = first_present_column(tagged, "Funnel Level")
    bucket_col = first_present_column(tagged, "Content Bucket")
    angle_col = first_present_column(tagged, "Marketing Angle")
    status_col = first_present_column(tagged, "Status")
    folder_col = first_present_column(tagged, "Creative Folder")
    ad_name_tss_col = first_present_column(tagged, "Ad Name (TSS)")
    ad_name_porcellia_col = first_present_column(tagged, "Ad Name (Porcellia)")

    tagged["_Date"] = parse_mixed_dates(tagged[date_col]) if date_col else pd.NaT
    tagged["Meta Product"] = tagged[product_col] if product_col else ""
    tagged["Meta Creative Type"] = tagged[creative_type_col] if creative_type_col else ""
    tagged["Meta Creative Name"] = tagged[creative_name_col] if creative_name_col else ""
    tagged["Meta Funnel Level"] = tagged[funnel_col] if funnel_col else ""
    tagged["Meta Content Bucket"] = tagged[bucket_col] if bucket_col else ""
    tagged["Meta Marketing Angle"] = tagged[angle_col] if angle_col else ""
    tagged["Meta Status"] = tagged[status_col] if status_col else ""
    tagged["Meta Creative Folder"] = tagged[folder_col] if folder_col else ""
    tagged["Meta FB Ad Name"] = tagged[fb_ad_name_col] if fb_ad_name_col else ""
    tagged["Meta Ad Name (TSS)"] = tagged[ad_name_tss_col] if ad_name_tss_col else ""
    tagged["Meta Ad Name (Porcellia)"] = tagged[ad_name_porcellia_col] if ad_name_porcellia_col else ""

    if not inhouse.empty and "AD CODE" in inhouse.columns:
        inhouse = inhouse.copy()
        inhouse["AD CODE"] = inhouse["AD CODE"].map(normalize_ad_code)
        join_cols = [column for column in [
            "AD CODE", "Asset ID", "Published Date", "Product", "Format",
            "Video Subtype", "Static Subtype", "Cohort", "Belief",
            "Marketing Angle", "Situational Driver", "Funnel Stage",
            "Influence Mode", "Creator Archetype", "Creator / Consumer Name",
            "Drive Link", "Reference Image Link",
        ] if column in inhouse.columns]
        tagged = tagged.merge(
            inhouse[join_cols],
            on="AD CODE",
            how="left",
            suffixes=("", "_inhouse"),
        )

    tagged["Format Derived"] = ""
    if "Format" in tagged.columns:
        tagged["Format Derived"] = tagged["Format"].fillna("")
    if creative_type_col:
        missing_mask = tagged["Format Derived"].astype(str).str.strip() == ""
        tagged.loc[missing_mask, "Format Derived"] = tagged.loc[missing_mask, creative_type_col].map(infer_format)

    tagged["Product Derived"] = ""
    if "Product" in tagged.columns:
        tagged["Product Derived"] = tagged["Product"].fillna("")
    if product_col:
        missing_mask = tagged["Product Derived"].astype(str).str.strip() == ""
        tagged.loc[missing_mask, "Product Derived"] = tagged.loc[missing_mask, product_col]

    tagged["Marketing Angle Derived"] = ""
    if "Marketing Angle" in tagged.columns:
        tagged["Marketing Angle Derived"] = tagged["Marketing Angle"].fillna("")
    if angle_col:
        missing_mask = tagged["Marketing Angle Derived"].astype(str).str.strip() == ""
        tagged.loc[missing_mask, "Marketing Angle Derived"] = tagged.loc[missing_mask, angle_col]

    tagged["Creative Name Derived"] = tagged["Meta Creative Name"].fillna("")
    for candidate in ["Meta FB Ad Name", "Meta Ad Name (TSS)", "Meta Ad Name (Porcellia)"]:
        missing_mask = tagged["Creative Name Derived"].astype(str).str.strip() == ""
        tagged.loc[missing_mask, "Creative Name Derived"] = tagged.loc[missing_mask, candidate]

    return tagged


def backlog_tag_candidates() -> pd.DataFrame:
    classified = build_classified_meta_view()
    if classified.empty:
        return classified

    candidates = classified.copy()
    candidates = candidates[candidates["AD CODE"].astype(str).str.strip() != ""]
    candidates = candidates[candidates["_Date"].notna()]
    candidates = candidates[candidates["Source"].isin(["Porcellia", "Unclassified"])]
    return candidates


def unimported_meta_candidates() -> pd.DataFrame:
    return backlog_tag_candidates()


def migrate_master_to_inhouse() -> tuple[int, int, list[str]]:
    ensure_inhouse_sheet()
    src = load_assets()
    if src.empty:
        return 0, 0, []

    dst_ws = _ws(SHEET_INHOUSE)
    migrated = 0
    skipped = 0
    errors: list[str] = []

    for _, row in src.iterrows():
        try:
            creative_type = str(row.get("Creative Type", "")).strip()
            if creative_type in {"Consumer Testimonial", "Brand-Led", "Founder-Led", "Skit", "Event Coverage", "AI-Video"}:
                fmt = "Video"
                video_subtype = creative_type
                static_subtype = ""
            elif creative_type in {"Static", "Carousel", "GIF", "AI-Static"}:
                fmt = "Static"
                video_subtype = ""
                static_subtype = creative_type
            else:
                fmt = ""
                video_subtype = creative_type
                static_subtype = ""

            new_row = {
                "Asset ID": row.get("Asset ID", ""),
                "AD CODE": normalize_ad_code(row.get("Meta Ad ID", "")),
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
                "Reference Image Link": "",
                "Notes": row.get("Notes", ""),
            }

            for column in INHOUSE_LIVE_HEADERS:
                if column not in new_row and column in src.columns:
                    new_row[column] = row.get(column, "")

            values = [new_row.get(header, "") for header in INHOUSE_LIVE_HEADERS]
            dst_ws.append_row(values, value_input_option="USER_ENTERED")
            migrated += 1
        except Exception as exc:
            errors.append(f"{row.get('Asset ID', '?')}: {exc}")
            skipped += 1

    return migrated, skipped, errors


def load_experiments() -> pd.DataFrame:
    try:
        records = _ws(SHEET_EXPERIMENTS).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=EXPERIMENT_HEADERS)
    except Exception as exc:
        st.error(f"Could not load experiments: {exc}")
        return pd.DataFrame(columns=EXPERIMENT_HEADERS)


def load_sources() -> pd.DataFrame:
    try:
        records = _ws(SHEET_SOURCES).get_all_records()
        return pd.DataFrame(records) if records else pd.DataFrame(columns=SOURCE_HEADERS)
    except Exception as exc:
        st.error(f"Could not load sources: {exc}")
        return pd.DataFrame(columns=SOURCE_HEADERS)


def save_asset(data: dict):
    row = [data.get(header, "") for header in ASSET_HEADERS]
    _ws(SHEET_ASSETS).append_row(row, value_input_option="USER_ENTERED")


def save_experiment(data: dict):
    row = [data.get(header, "") for header in EXPERIMENT_HEADERS]
    _ws(SHEET_EXPERIMENTS).append_row(row, value_input_option="USER_ENTERED")


def save_source(data: dict):
    row = [data.get(header, "") for header in SOURCE_HEADERS]
    _ws(SHEET_SOURCES).append_row(row, value_input_option="USER_ENTERED")


def update_asset(asset_id: str, field: str, value):
    ws = _ws(SHEET_ASSETS)
    cell = ws.find(asset_id)
    if cell:
        col = ASSET_HEADERS.index(field) + 1
        ws.update_cell(cell.row, col, value)


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
    prefix_product = _PRODUCT_CODE.get(product, "TSS")
    value = (creative_type_or_format or "").strip()
    creative_prefix = "V" if value == "Video" or value in _VIDEO_TYPES else "S"
    prefix = f"{prefix_product}-{creative_prefix}-"
    nums = [
        int(item.split("-")[-1]) for item in existing
        if item.startswith(prefix) and item.split("-")[-1].isdigit()
    ]
    return f"{prefix}{str(max(nums, default=0) + 1).zfill(3)}"


def next_experiment_id(existing: list) -> str:
    nums = [
        int(item.split("-")[-1]) for item in existing
        if item.startswith("EXP-") and item.split("-")[-1].isdigit()
    ]
    return f"EXP-{str(max(nums, default=0) + 1).zfill(3)}"


def next_source_id(existing: list) -> str:
    nums = [
        int(item.split("-")[-1]) for item in existing
        if item.startswith("SRC-") and item.split("-")[-1].isdigit()
    ]
    return f"SRC-{str(max(nums, default=0) + 1).zfill(3)}"


def initialise_sheets():
    spreadsheet = _client().open(st.secrets["spreadsheet_name"])
    existing = {ws.title for ws in spreadsheet.worksheets()}

    to_create = {
        SHEET_ASSETS: ASSET_HEADERS,
        SHEET_INHOUSE: INHOUSE_LIVE_HEADERS,
        SHEET_EXPERIMENTS: EXPERIMENT_HEADERS,
        SHEET_SOURCES: SOURCE_HEADERS,
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
