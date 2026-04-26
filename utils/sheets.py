import re
from urllib.parse import urlparse

import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_ASSETS = "Master_Asset_Registry"
SHEET_INHOUSE = "Inhouse_Live_Assets"  # Legacy tab. Kept untouched; no app flow writes here.
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

ASSET_EXTRA_HEADERS = [
    "Format", "Video Subtype", "Static Subtype",
    "Preview Asset Link", "Source Folder Link", "Thumbnail Link", "Reference Image Link",
    "Taxonomy Review Status",
]

MASTER_HEADERS = ASSET_HEADERS + ASSET_EXTRA_HEADERS

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

PERFORMANCE_COLUMNS = [
    "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach",
    "CTR", "CPC", "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
    "ROAS (L7)", "Amount Spent (L7)", "Revenue (L7)", "Avg Cost Per Reach (L7)",
    "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)",
    "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
]

AD_CODE_RE = re.compile(r"\bAD\s*[-_]?\s*0*(\d+)\b", re.IGNORECASE)
META_AD_CODE_COL_INDEX = 37  # Column AL, zero-based.
_ADNAME_DATE_RE = re.compile(r"\b(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})\b")
_LIKELY_INHOUSE_RE = re.compile(r"\b(in\s*house|in-house|inhouse)\b", re.IGNORECASE)
_KUHU_RE = re.compile(r"\bkuhu\b", re.IGNORECASE)


@st.cache_resource
def _credentials():
    return Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )


@st.cache_resource
def _client():
    return gspread.authorize(_credentials())


def _ws(sheet_name: str):
    return _client().open(st.secrets["spreadsheet_name"]).worksheet(sheet_name)


@st.cache_data(ttl=600, show_spinner=False)
def _sheet_values(sheet_name: str):
    return _ws(sheet_name).get_all_values()


def _clear_sheet_cache():
    _sheet_values.clear()


def _clean_header(value) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("|", " ")).strip()


def _dedupe_headers(headers: list[str]) -> list[str]:
    seen: dict[str, int] = {}
    deduped: list[str] = []
    for header in headers:
        key = header or "_blank"
        count = seen.get(key, 0) + 1
        seen[key] = count
        deduped.append(key if count == 1 else f"{key}_{count}")
    return deduped


def _records_from_values(values: list[list[str]], fallback_columns: list[str]) -> pd.DataFrame:
    if not values:
        return pd.DataFrame(columns=fallback_columns)
    headers = [_clean_header(value) for value in values[0]]
    if not any(headers):
        return pd.DataFrame(columns=fallback_columns)
    headers = _dedupe_headers(headers)
    rows = values[1:] if len(values) > 1 else []
    if not rows:
        return pd.DataFrame(columns=headers)
    width = len(headers)
    padded = [row + [""] * (width - len(row)) if len(row) < width else row[:width] for row in rows]
    return pd.DataFrame(padded, columns=headers)


def _ensure_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df.copy()
    for column in columns:
        if column not in out.columns:
            out[column] = ""
    return out


def _truthy(value) -> bool:
    return str(value or "").strip().lower() not in {"", "nan", "none", "nat"}


def first_present_column(df: pd.DataFrame, *candidates: str):
    lower_map = {str(column).strip().lower(): column for column in df.columns}
    for candidate in candidates:
        if not candidate:
            continue
        direct = str(candidate).strip()
        if direct in df.columns:
            return direct
        lowered = direct.lower()
        if lowered in lower_map:
            return lower_map[lowered]
    return None


def normalize_ad_code(value) -> str:
    raw = str(value or "").strip()
    if not raw or raw.lower() in {"nan", "none", "nat"}:
        return ""
    match = AD_CODE_RE.search(raw)
    if match:
        return f"AD {int(match.group(1))}"
    digits = re.fullmatch(r"\d+(\.0+)?", raw.replace(",", ""))
    if digits:
        return f"AD {int(float(raw.replace(',', '')))}"
    return re.sub(r"\s+", " ", raw).upper()


def parse_mixed_dates(series: pd.Series) -> pd.Series:
    if series is None or len(series) == 0:
        return pd.Series(dtype="datetime64[ns]")
    cleaned = series.astype(str).str.strip().replace({"": pd.NA, "nan": pd.NA, "None": pd.NA, "NaT": pd.NA})
    parsed = pd.Series(pd.NaT, index=series.index, dtype="datetime64[ns]")

    # ISO-style dates from our own app must be parsed month-safe before
    # dayfirst parsing, otherwise pandas can read 2026-04-10 as 4 Oct 2026.
    iso_mask = cleaned.str.match(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", na=False)
    if iso_mask.any():
        parsed.loc[iso_mask] = pd.to_datetime(cleaned[iso_mask], errors="coerce", dayfirst=False)

    remaining_idx = cleaned[parsed.isna()].dropna().index
    if len(remaining_idx) > 0:
        parsed_dayfirst = pd.to_datetime(cleaned.loc[remaining_idx], errors="coerce", dayfirst=True)
        parsed.loc[remaining_idx] = parsed_dayfirst

    remaining = cleaned[parsed.isna()].dropna()
    if not remaining.empty:
        trimmed = (
            remaining
            .str.replace(r"\s+\d{1,2}:\d{2}(:\d{2})?(\s*[APMapm]{2})?$", "", regex=True)
            .str.replace(r"T\d{2}:\d{2}(:\d{2})?.*$", "", regex=True)
            .str.replace(r"\s+UTC.*$", "", regex=True)
            .str.strip()
        )
        reparsed_dayfirst = pd.to_datetime(trimmed, errors="coerce", dayfirst=True)
        parsed.loc[reparsed_dayfirst.index] = reparsed_dayfirst

    remaining = cleaned[parsed.isna()].dropna()
    if not remaining.empty:
        serial_mask = remaining.str.fullmatch(r"\d+(\.\d+)?")
        if serial_mask.any():
            serial_values = pd.to_numeric(remaining[serial_mask], errors="coerce")
            serial_values = serial_values[(serial_values >= 30000) & (serial_values <= 70000)]
            if not serial_values.empty:
                serial_dates = pd.to_datetime(serial_values, unit="D", origin="1899-12-30", errors="coerce")
                parsed.loc[serial_dates.index] = serial_dates
    return parsed


def extract_date_from_name(value) -> pd.Timestamp:
    text = str(value or "")
    if not text.strip():
        return pd.NaT
    for match in _ADNAME_DATE_RE.finditer(text):
        day, month, year = [int(part) for part in match.groups()]
        if year < 100:
            year += 2000
        if not (2020 <= year <= 2035):
            continue
        if not (1 <= month <= 12):
            if 1 <= day <= 12 and 1 <= month <= 31:
                day, month = month, day
            else:
                continue
        try:
            return pd.Timestamp(year=year, month=month, day=day)
        except (ValueError, OverflowError):
            continue
    return pd.NaT


def infer_format(value: str) -> str:
    text = str(value or "").strip().lower()
    if not text:
        return ""
    video_words = ("video", "reel", "testimonial", "founder", "skit", "ugc", "event", "creator")
    static_words = ("static", "carousel", "gif", "image", "banner", "card", "1x1", "9x16", "4x5")
    if any(word in text for word in video_words):
        return "Video"
    if any(word in text for word in static_words):
        return "Static"
    return ""


def infer_static_subtype(value: str) -> str:
    text = str(value or "").lower()
    if "carousel" in text:
        return "SS2 - Carousel"
    if "review" in text or "dm" in text or "screenshot" in text:
        return "SS4 - Proof Screenshot"
    if "comparison" in text or " vs " in text:
        return "SS5 - Comparison"
    if "ingredient" in text:
        return "SS9 - Ingredient Focus"
    if "data" in text or "stat" in text or "%" in text:
        return "SS10 - Data / Stats Card"
    if "ai" in text:
        return "SS11 - AI-Generated Static"
    return "SS1 - Single Image"


def _detect_ad_code_index(rows: list[list[str]], headers: list[str]):
    best_idx = None
    best_score = 0
    width = max((len(r) for r in rows), default=len(headers))
    for idx in range(width):
        header = headers[idx] if idx < len(headers) else ""
        values = [row[idx].strip() for row in rows[:120] if idx < len(row) and str(row[idx]).strip()]
        score = sum(1 for value in values if AD_CODE_RE.search(value))
        if "ad code" in header.lower():
            score += 100
        if score > best_score:
            best_idx = idx
            best_score = score
    if best_idx is not None and best_score > 0:
        return best_idx
    return META_AD_CODE_COL_INDEX if len(headers) > META_AD_CODE_COL_INDEX else None


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


def _combine_text(row: pd.Series, columns: list[str]) -> str:
    return " ".join(str(row.get(column, "")) for column in columns if column in row.index)


def _coalesce(row: pd.Series, *columns: str) -> str:
    for column in columns:
        if column in row.index and _truthy(row.get(column)):
            return str(row.get(column)).strip()
    return ""


def _first_non_empty(*values) -> str:
    for value in values:
        if _truthy(value):
            return str(value).strip()
    return ""


def _add_metric_fields(target: dict, *rows: pd.Series):
    metric_source = ""
    for metric in PERFORMANCE_COLUMNS:
        for row in rows:
            if row is not None and metric in row.index and _truthy(row.get(metric)):
                target[metric] = row.get(metric)
                if not metric_source:
                    metric_source = "Sheet metric columns"
                break
        target.setdefault(metric, "")
    target["Metric Source"] = metric_source


def load_assets() -> pd.DataFrame:
    try:
        values = _sheet_values(SHEET_ASSETS)
        df = _records_from_values(values, MASTER_HEADERS)
        df = _ensure_columns(df, MASTER_HEADERS)
        if "Meta Ad ID" in df.columns:
            df["Meta Ad ID"] = df["Meta Ad ID"].map(normalize_ad_code)
        if "Format" in df.columns:
            missing = df["Format"].astype(str).str.strip() == ""
            if "Creative Type" in df.columns:
                df.loc[missing, "Format"] = df.loc[missing, "Creative Type"].map(infer_format)
        return df
    except Exception as exc:
        st.error(f"Could not load Master_Asset_Registry: {exc}")
        return pd.DataFrame(columns=MASTER_HEADERS)


def load_inhouse_live() -> pd.DataFrame:
    """Legacy reader retained only for old diagnostics. New app logic uses Master_Asset_Registry."""
    try:
        values = _sheet_values(SHEET_INHOUSE)
        df = _records_from_values(values, INHOUSE_LIVE_HEADERS)
        if "AD CODE" in df.columns:
            df["AD CODE"] = df["AD CODE"].map(normalize_ad_code)
        return df
    except Exception:
        return pd.DataFrame(columns=INHOUSE_LIVE_HEADERS)


def load_meta_ads() -> pd.DataFrame:
    try:
        values = _sheet_values(SHEET_META_ADS)
        if len(values) < 3:
            return pd.DataFrame()

        header_row_idx = 1
        raw_headers = [_clean_header(value) for value in values[header_row_idx]]
        rows = values[header_row_idx + 1:]

        ad_code_idx = _detect_ad_code_index(rows, raw_headers)
        if ad_code_idx is not None:
            while len(raw_headers) <= ad_code_idx:
                raw_headers.append("")
            raw_headers[ad_code_idx] = "AD CODE"

        headers = _dedupe_headers(raw_headers)
        width = len(headers)
        padded = [row + [""] * (width - len(row)) if len(row) < width else row[:width] for row in rows]
        df = pd.DataFrame(padded, columns=headers)
        df = _drop_truly_blank_columns(df)
        if "AD CODE" in df.columns:
            df["AD CODE"] = df["AD CODE"].map(normalize_ad_code)
        return df
    except Exception as exc:
        st.warning(f"Could not load Meta Ads sheet: {exc}")
        return pd.DataFrame()


def load_influencer_ads() -> pd.DataFrame:
    try:
        values = _sheet_values(SHEET_INFLUENCER)
        if len(values) < 2:
            return pd.DataFrame()

        header_row_idx = 0
        if len(values) > 1:
            row0_count = sum(1 for value in values[0] if str(value).strip())
            row1_count = sum(1 for value in values[1] if str(value).strip())
            if row1_count > row0_count:
                header_row_idx = 1

        headers = _dedupe_headers([_clean_header(value) for value in values[header_row_idx]])
        rows = values[header_row_idx + 1:]
        width = len(headers)
        padded = [row + [""] * (width - len(row)) if len(row) < width else row[:width] for row in rows]
        df = pd.DataFrame(padded, columns=headers)
        df = df.loc[:, [column for column in df.columns if column.strip()]]

        perf_col = first_present_column(df, "Perf AD Code", "Perf Ad Code", "Perf AD code", "Perf Ad code")
        if perf_col and perf_col != "Perf AD Code":
            df = df.rename(columns={perf_col: "Perf AD Code"})
            perf_col = "Perf AD Code"
        if perf_col:
            df[perf_col] = df[perf_col].map(normalize_ad_code)

        ad_col = first_present_column(df, "Ad Code", "AD CODE", "Ad code", "AdCode")
        if ad_col and ad_col != "Ad Code":
            df = df.rename(columns={ad_col: "Ad Code"})
            ad_col = "Ad Code"
        if ad_col:
            # This may be a platform ad-rights code, not always AD ###. Keep normalized only when applicable.
            df[ad_col] = df[ad_col].map(lambda value: normalize_ad_code(value) if AD_CODE_RE.search(str(value or "")) else str(value or "").strip())
        return df
    except Exception as exc:
        st.warning(f"Could not load Live Entries 2026 sheet: {exc}")
        return pd.DataFrame()


def load_experiments() -> pd.DataFrame:
    try:
        values = _sheet_values(SHEET_EXPERIMENTS)
        return _records_from_values(values, EXPERIMENT_HEADERS)
    except Exception as exc:
        st.error(f"Could not load experiments: {exc}")
        return pd.DataFrame(columns=EXPERIMENT_HEADERS)


def load_sources() -> pd.DataFrame:
    try:
        values = _sheet_values(SHEET_SOURCES)
        return _records_from_values(values, SOURCE_HEADERS)
    except Exception as exc:
        st.error(f"Could not load sources: {exc}")
        return pd.DataFrame(columns=SOURCE_HEADERS)


def _current_headers(sheet_name: str, fallback: list[str]) -> list[str]:
    values = _sheet_values(sheet_name)
    if values and values[0]:
        return [_clean_header(value) for value in values[0]]
    return fallback


def ensure_master_asset_schema() -> list[str]:
    ws = _ws(SHEET_ASSETS)
    headers = [_clean_header(value) for value in ws.row_values(1)]
    if not headers:
        ws.append_row(MASTER_HEADERS)
        _clear_sheet_cache()
        return MASTER_HEADERS

    missing = [header for header in ASSET_EXTRA_HEADERS if header not in headers]
    if missing:
        needed_cols = len(headers) + len(missing)
        if ws.col_count < needed_cols:
            ws.add_cols(needed_cols - ws.col_count)
        for offset, header in enumerate(missing, start=1):
            ws.update_cell(1, len(headers) + offset, header)
        headers = headers + missing
        _clear_sheet_cache()
    return headers


def save_asset(data: dict):
    headers = ensure_master_asset_schema()
    row = [data.get(header, "") for header in headers]
    _ws(SHEET_ASSETS).append_row(row, value_input_option="USER_ENTERED")
    _clear_sheet_cache()


def _product_from_meta(value: str) -> str:
    text = str(value or "").strip()
    lowered = text.lower()
    if "sunscreen" in lowered or "cpgs" in lowered:
        return "Clear Protect Gel Sunscreen"
    if "lpp" in lowered or "liquid pimple" in lowered:
        return "Liquid Pimple Patch"
    if "emc" in lowered or "melting cleanser" in lowered:
        return "Effortless Melting Cleanser"
    if "sfar" in lowered or "spot fade" in lowered or "serum" in lowered:
        return "Spot Fade Serum"
    if "rcf" in lowered or "rapid clear" in lowered or "acne combo" in lowered:
        return "RCF"
    return text


def _video_subtype_from_meta(row: pd.Series) -> str:
    text = _combine_text(row, ["Creative Name", "Content Bucket", "Creative Type"]).lower()
    if "founder" in text:
        return "Founder-Led"
    if "testimonial" in text or "social proof" in text:
        return "Consumer Testimonial"
    if "skit" in text:
        return "Skit"
    if "ai" in text:
        return "AI-Video"
    return "Brand-Led"


def _creator_from_inhouse_name(name: str) -> str:
    text = re.sub(r"\bin\s*house\b|\binhouse\b|in-house", "", str(name or ""), flags=re.IGNORECASE)
    text = re.sub(r"\b(video|static|statics|testimonial|brand|founderled|founder led)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    # Keep this conservative; names are often followed by angle descriptors.
    words = text.split()
    return " ".join(words[:3]) if words else ""


def _master_row_from_meta_inhouse(meta_row: pd.Series, existing_ids: list[str]) -> dict:
    raw_type = _coalesce(meta_row, "Creative Type")
    fmt = infer_format(raw_type) or infer_format(_coalesce(meta_row, "Creative Name"))
    if fmt not in {"Video", "Static"}:
        fmt = "Static" if "static" in _coalesce(meta_row, "Creative Name").lower() else "Video"

    product = _product_from_meta(_coalesce(meta_row, "Product"))
    asset_id = next_asset_id(product, fmt, existing_ids)
    existing_ids.append(asset_id)

    live_date = _meta_live_date(pd.DataFrame([meta_row])).iloc[0]
    published_date = live_date.strftime("%Y-%m-%d") if pd.notna(live_date) else ""
    creative_name = _coalesce(meta_row, "Creative Name")
    drive_link = _coalesce(meta_row, "Creative Folder Link", "Creative Folder", "1:1 Creative Link", "4:5 Creative Link", "9:16 Creative Link")
    preview_link = _coalesce(meta_row, "1:1 Creative Link", "4:5 Creative Link", "9:16 Creative Link", "Creative Folder Link", "Creative Folder")

    row = {
        "Asset ID": asset_id,
        "Variant #": "A",
        "Status": "Published",
        "Created Date": datetime_now_string(),
        "Published Date": published_date,
        "Product": product,
        "Bucket": "Performance",
        "Channel": "In-house",
        "Creative Type": _video_subtype_from_meta(meta_row) if fmt == "Video" else infer_static_subtype(creative_name),
        "Format": fmt,
        "Video Subtype": _video_subtype_from_meta(meta_row) if fmt == "Video" else "",
        "Static Subtype": infer_static_subtype(_combine_text(meta_row, ["Creative Name", "Creative Type", "Content Bucket"])) if fmt == "Static" else "",
        "Marketing Angle": _coalesce(meta_row, "Marketing Angle"),
        "Funnel Stage": _coalesce(meta_row, "Funnel Level"),
        "Creator / Consumer Name": _creator_from_inhouse_name(creative_name),
        "Meta Ad ID": normalize_ad_code(meta_row.get("AD CODE", "")),
        "Campaign Name": _coalesce(meta_row, "FB Ad Name", "Ad Name (TSS)"),
        "Drive Link": drive_link,
        "Preview Asset Link": preview_link,
        "Source Folder Link": _coalesce(meta_row, "Creative Folder Link", "Creative Folder"),
        "Brief Link": _coalesce(meta_row, "Asana Link"),
        "Notes": f"One-time import from Meta Ads. Meta Creative Name: {creative_name}",
        "Taxonomy Review Status": "Needs Review",
    }
    return row


def datetime_now_string() -> str:
    return pd.Timestamp.now(tz=None).strftime("%Y-%m-%d")


def meta_inhouse_import_candidates() -> pd.DataFrame:
    meta = load_meta_ads()
    assets = load_assets()
    influencers = load_influencer_ads()
    if meta.empty or "Creative Name" not in meta.columns:
        return pd.DataFrame()

    existing_codes = set()
    if not assets.empty and "Meta Ad ID" in assets.columns:
        existing_codes = {normalize_ad_code(value) for value in assets["Meta Ad ID"].tolist() if normalize_ad_code(value)}

    influencer_codes = set()
    if not influencers.empty and "Perf AD Code" in influencers.columns:
        influencer_codes = {normalize_ad_code(value) for value in influencers["Perf AD Code"].tolist() if normalize_ad_code(value)}

    creative_name = meta["Creative Name"].astype(str)
    has_inhouse = creative_name.str.contains(r"\bin\s*house\b|\binhouse\b|in-house", case=False, regex=True, na=False)
    has_kuhu = creative_name.str.contains(r"\bkuhu\b", case=False, regex=True, na=False)
    out = meta[has_inhouse & ~has_kuhu].copy()
    out["AD CODE"] = out["AD CODE"].map(normalize_ad_code) if "AD CODE" in out.columns else ""
    out = out[out["AD CODE"].astype(str).str.strip() != ""]
    out["Already In Master"] = out["AD CODE"].isin(existing_codes)
    out["Matched Influencer"] = out["AD CODE"].isin(influencer_codes)
    return out[~out["Already In Master"] & ~out["Matched Influencer"]].copy()


def import_meta_inhouse_to_master() -> tuple[int, list[str]]:
    candidates = meta_inhouse_import_candidates()
    if candidates.empty:
        return 0, []

    assets = load_assets()
    existing_ids = assets["Asset ID"].dropna().astype(str).tolist() if not assets.empty and "Asset ID" in assets.columns else []
    ws = _ws(SHEET_ASSETS)
    headers = ensure_master_asset_schema()
    imported = 0
    errors: list[str] = []

    for _, meta_row in candidates.iterrows():
        try:
            row = _master_row_from_meta_inhouse(meta_row, existing_ids)
            ws.append_row([row.get(header, "") for header in headers], value_input_option="USER_ENTERED")
            imported += 1
        except Exception as exc:
            errors.append(f"{normalize_ad_code(meta_row.get('AD CODE', ''))}: {exc}")

    _clear_sheet_cache()
    return imported, errors


def save_experiment(data: dict):
    row = [data.get(header, "") for header in EXPERIMENT_HEADERS]
    _ws(SHEET_EXPERIMENTS).append_row(row, value_input_option="USER_ENTERED")
    _clear_sheet_cache()


def save_source(data: dict):
    row = [data.get(header, "") for header in SOURCE_HEADERS]
    _ws(SHEET_SOURCES).append_row(row, value_input_option="USER_ENTERED")
    _clear_sheet_cache()


def update_asset(asset_id: str, field: str, value):
    ws = _ws(SHEET_ASSETS)
    cell = ws.find(asset_id)
    if cell:
        headers = ensure_master_asset_schema()
        if field not in headers:
            return
        ws.update_cell(cell.row, headers.index(field) + 1, value)
        _clear_sheet_cache()


def update_experiment(experiment_id: str, updates: dict):
    ws = _ws(SHEET_EXPERIMENTS)
    cell = ws.find(experiment_id)
    if not cell:
        return False
    for field, value in updates.items():
        if field in EXPERIMENT_HEADERS:
            ws.update_cell(cell.row, EXPERIMENT_HEADERS.index(field) + 1, value)
    _clear_sheet_cache()
    return True


def classify_meta_ads(meta_df: pd.DataFrame, assets_df: pd.DataFrame, influencer_df: pd.DataFrame) -> pd.DataFrame:
    if meta_df.empty:
        return meta_df.copy()

    out = meta_df.copy()
    if "AD CODE" not in out.columns:
        out["AD CODE"] = ""
    out["AD CODE"] = out["AD CODE"].map(normalize_ad_code)

    inhouse_codes = set()
    if not assets_df.empty and "Meta Ad ID" in assets_df.columns:
        inhouse_codes = {normalize_ad_code(value) for value in assets_df["Meta Ad ID"].tolist() if normalize_ad_code(value)}

    influencer_codes = set()
    if not influencer_df.empty and "Perf AD Code" in influencer_df.columns:
        influencer_codes = {normalize_ad_code(value) for value in influencer_df["Perf AD Code"].tolist() if normalize_ad_code(value)}

    likely_mask = out.apply(_is_likely_inhouse_meta_row, axis=1)

    def _classify(row: pd.Series) -> str:
        code = normalize_ad_code(row.get("AD CODE"))
        if not code:
            return "Unclassified"
        if code in influencer_codes:
            return "Influencer"
        if _is_kuhu_meta_row(row):
            return "Influencer"
        if code in inhouse_codes:
            return "Inhouse"
        if bool(likely_mask.loc[row.name]):
            return "Needs Logging"
        return "Porcellia"

    out["Source"] = out.apply(_classify, axis=1)
    return out


def _meta_live_date(meta: pd.DataFrame) -> pd.Series:
    if meta.empty:
        return pd.Series(dtype="datetime64[ns]")
    date_col = first_present_column(meta, "Date [Ad Taken Live]", "Date [Ad Taken Live] ")
    parsed = parse_mixed_dates(meta[date_col]) if date_col else pd.Series(pd.NaT, index=meta.index)
    fallback_cols = [
        first_present_column(meta, "FB Ad Name"),
        first_present_column(meta, "Ad Name (TSS)"),
        first_present_column(meta, "Ad Name (Porcellia)"),
        first_present_column(meta, "Creative Name"),
    ]
    for column in [c for c in fallback_cols if c]:
        missing = parsed.isna()
        if not missing.any():
            break
        parsed.loc[missing] = meta.loc[missing, column].map(extract_date_from_name)
    return parsed


def _is_likely_inhouse_meta_row(row: pd.Series) -> bool:
    columns = [
        "Creative Name", "FB Ad Name", "Comment", "Creative Folder Link", "Creative Folder",
        "Ad Name (TSS)", "Ad Name (Porcellia)", "Growth SPOC/Project Manager", "Creative Strategist",
    ]
    text = _combine_text(row, columns)
    if _KUHU_RE.search(text):
        return False
    return bool(_LIKELY_INHOUSE_RE.search(text))


def _is_kuhu_meta_row(row: pd.Series) -> bool:
    columns = [
        "Creative Name", "FB Ad Name", "Comment", "Creative Folder Link", "Creative Folder",
        "Ad Name (TSS)", "Ad Name (Porcellia)", "Growth SPOC/Project Manager", "Creative Strategist",
    ]
    return bool(_KUHU_RE.search(_combine_text(row, columns)))


def _normalized_master_row(asset: pd.Series, meta_row: pd.Series | None) -> dict:
    creative_type = _coalesce(asset, "Creative Type")
    fmt = _first_non_empty(asset.get("Format", ""), infer_format(creative_type))
    static_subtype = _coalesce(asset, "Static Subtype")
    video_subtype = _coalesce(asset, "Video Subtype")
    if not video_subtype and fmt == "Video":
        video_subtype = creative_type
    if not static_subtype and fmt == "Static":
        static_subtype = creative_type if creative_type and creative_type != "Static" else infer_static_subtype(asset.get("Drive Link", ""))

    meta_date = meta_row.get("_Meta Live Date") if meta_row is not None and "_Meta Live Date" in meta_row.index else pd.NaT
    master_date = parse_mixed_dates(pd.Series([asset.get("Published Date", "")])).iloc[0]
    live_date = meta_date if pd.notna(meta_date) else master_date

    row = {
        "Source": "Inhouse",
        "Record Type": "Performance Live",
        "Asset ID": asset.get("Asset ID", ""),
        "AD CODE": normalize_ad_code(asset.get("Meta Ad ID", "")),
        "Perf AD Code": normalize_ad_code(asset.get("Meta Ad ID", "")),
        "Live Date": live_date,
        "Perf Live Date": meta_date,
        "Creator Live Date": pd.NaT,
        "Creative Name": _first_non_empty(
            asset.get("Creator / Consumer Name", ""),
            asset.get("Asset ID", ""),
            meta_row.get("Creative Name", "") if meta_row is not None else "",
        ),
        "Product": _first_non_empty(asset.get("Product", ""), meta_row.get("Product", "") if meta_row is not None else ""),
        "Format": fmt,
        "Creative Type": creative_type,
        "Video Subtype": video_subtype,
        "Static Subtype": static_subtype,
        "Bucket": asset.get("Bucket", ""),
        "Funnel Stage": _first_non_empty(asset.get("Funnel Stage", ""), meta_row.get("Funnel Level", "") if meta_row is not None else ""),
        "Content Bucket": meta_row.get("Content Bucket", "") if meta_row is not None else "",
        "Marketing Angle": _first_non_empty(asset.get("Marketing Angle", ""), meta_row.get("Marketing Angle", "") if meta_row is not None else ""),
        "Belief": asset.get("Belief", ""),
        "Cohort": asset.get("Cohort", ""),
        "Situational Driver": asset.get("Situational Driver", ""),
        "Hook Type": asset.get("Hook Type", ""),
        "Emotional Arc": asset.get("Emotional Arc", ""),
        "Creator Archetype": asset.get("Creator Archetype", ""),
        "Influence Mode": asset.get("Influence Mode", ""),
        "Visual Style": asset.get("Visual Style", ""),
        "CTA Style": asset.get("CTA Style", ""),
        "Creator / Consumer Name": asset.get("Creator / Consumer Name", ""),
        "Creator": asset.get("Creator / Consumer Name", ""),
        "Source Interview ID": asset.get("Source Interview ID", ""),
        "Experiment ID": asset.get("Experiment ID", ""),
        "Drive Link": _first_non_empty(asset.get("Drive Link", ""), asset.get("Preview Asset Link", ""), meta_row.get("Creative Folder Link", "") if meta_row is not None else ""),
        "Preview Asset Link": _first_non_empty(asset.get("Preview Asset Link", ""), asset.get("Drive Link", "")),
        "Source Folder Link": _first_non_empty(asset.get("Source Folder Link", ""), meta_row.get("Creative Folder Link", "") if meta_row is not None else ""),
        "Thumbnail Link": asset.get("Thumbnail Link", ""),
        "Brief Link": asset.get("Brief Link", ""),
        "Reference Image Link": asset.get("Reference Image Link", ""),
        "Landing Page URL": meta_row.get("Landing Page URL", "") if meta_row is not None else "",
        "Instagram / Live Link": "",
        "Campaign Name": _first_non_empty(asset.get("Campaign Name", ""), meta_row.get("FB Ad Name", "") if meta_row is not None else ""),
        "Ad Set Name": asset.get("Ad Set Name", ""),
        "Status": _first_non_empty(asset.get("Status", ""), meta_row.get("Status", "") if meta_row is not None else ""),
        "Notes": asset.get("Notes", ""),
        "Needs Attention": "",
    }
    _add_metric_fields(row, asset, meta_row)
    return row


def _normalized_influencer_row(influencer: pd.Series, meta_row: pd.Series | None) -> dict:
    creator_date = parse_mixed_dates(pd.Series([influencer.get("Date", "")])).iloc[0]
    ad_started = parse_mixed_dates(pd.Series([influencer.get("Ad Started On", "")])).iloc[0]
    meta_date = meta_row.get("_Meta Live Date") if meta_row is not None and "_Meta Live Date" in meta_row.index else pd.NaT
    perf_live_date = meta_date if pd.notna(meta_date) else ad_started
    perf_code = normalize_ad_code(influencer.get("Perf AD Code", ""))
    internal_code = influencer.get("Ad Code", "")

    row = {
        "Source": "Influencer",
        "Record Type": "Creator Live" if not perf_code else "Creator + Perf Live",
        "Asset ID": "",
        "AD CODE": perf_code or str(internal_code or "").strip(),
        "Perf AD Code": perf_code,
        "Influencer Ad Code": internal_code,
        "Live Date": creator_date,
        "Creator Live Date": creator_date,
        "Perf Live Date": perf_live_date,
        "Creative Name": _first_non_empty(influencer.get("Creator", ""), meta_row.get("Creative Name", "") if meta_row is not None else ""),
        "Product": _first_non_empty(influencer.get("Product", ""), influencer.get("Product ", ""), meta_row.get("Product", "") if meta_row is not None else ""),
        "Format": "Video",
        "Creative Type": _first_non_empty(meta_row.get("Creative Type", "") if meta_row is not None else "", "Influencer Video"),
        "Video Subtype": "Influencer Video",
        "Static Subtype": "",
        "Bucket": "Performance" if perf_code else "Influencer Content",
        "Funnel Stage": meta_row.get("Funnel Level", "") if meta_row is not None else "",
        "Content Bucket": meta_row.get("Content Bucket", "") if meta_row is not None else "",
        "Marketing Angle": meta_row.get("Marketing Angle", "") if meta_row is not None else "",
        "Belief": "",
        "Cohort": "",
        "Situational Driver": "",
        "Hook Type": "",
        "Emotional Arc": "",
        "Creator Archetype": "Influencer",
        "Influence Mode": "",
        "Visual Style": "",
        "CTA Style": "",
        "Creator / Consumer Name": influencer.get("Creator", ""),
        "Creator": influencer.get("Creator", ""),
        "Agency": influencer.get("Agency", ""),
        "POC": influencer.get("POC", ""),
        "Followers": influencer.get("Followers", ""),
        "Platform": influencer.get("Platform", ""),
        "Language": influencer.get("Language", ""),
        "Instagram / Live Link": influencer.get("Live Link", ""),
        "Drive Link": influencer.get("Live Link", ""),
        "Preview Asset Link": influencer.get("Live Link", ""),
        "Source Folder Link": "",
        "Thumbnail Link": "",
        "Brief Link": "",
        "Reference Image Link": "",
        "Landing Page URL": meta_row.get("Landing Page URL", "") if meta_row is not None else "",
        "Campaign Name": meta_row.get("FB Ad Name", "") if meta_row is not None else "",
        "Ad Set Name": "",
        "Status": "Perf live" if perf_code else "Creator live, no Perf AD Code",
        "Notes": influencer.get("Comments on the video", "") if "Comments on the video" in influencer.index else "",
        "Needs Attention": "" if perf_code else "No Perf AD Code yet",
        "Views": influencer.get("Views", ""),
        "Likes": influencer.get("Likes", ""),
        "Comments": influencer.get("Comments", ""),
        "Shares": influencer.get("Shares", ""),
        "Saves": influencer.get("Saves", ""),
        "Total Engagement": influencer.get("Total Engagement", ""),
        "Engagement Rate (%)": influencer.get("Engagement Rate (%)", ""),
    }
    _add_metric_fields(row, influencer, meta_row)
    return row


def _normalized_meta_row(meta: pd.Series, source: str) -> dict:
    text_for_format = _combine_text(meta, ["Creative Type", "Visual format", "Creative Name", "FB Ad Name", "Ad Name (TSS)", "Ad Name (Porcellia)"])
    row = {
        "Source": source,
        "Record Type": "Needs Inhouse Logging" if source == "Needs Logging" else "Performance Live",
        "Asset ID": "",
        "AD CODE": normalize_ad_code(meta.get("AD CODE", "")),
        "Perf AD Code": normalize_ad_code(meta.get("AD CODE", "")),
        "Live Date": meta.get("_Meta Live Date", pd.NaT),
        "Perf Live Date": meta.get("_Meta Live Date", pd.NaT),
        "Creator Live Date": pd.NaT,
        "Creative Name": _coalesce(meta, "Creative Name", "FB Ad Name", "Ad Name (TSS)", "Ad Name (Porcellia)"),
        "Product": _coalesce(meta, "Product"),
        "Format": _first_non_empty(infer_format(meta.get("Creative Type", "")), infer_format(text_for_format)),
        "Creative Type": _coalesce(meta, "Creative Type"),
        "Video Subtype": "",
        "Static Subtype": infer_static_subtype(text_for_format) if infer_format(text_for_format) == "Static" else "",
        "Bucket": "Performance",
        "Funnel Stage": _coalesce(meta, "Funnel Level"),
        "Content Bucket": _coalesce(meta, "Content Bucket"),
        "Marketing Angle": _coalesce(meta, "Marketing Angle"),
        "Belief": "",
        "Cohort": _coalesce(meta, "Persona"),
        "Situational Driver": "",
        "Hook Type": _coalesce(meta, "Creative Hook"),
        "Emotional Arc": "",
        "Creator Archetype": "",
        "Influence Mode": "",
        "Visual Style": _coalesce(meta, "Visual format"),
        "CTA Style": "",
        "Creator / Consumer Name": _coalesce(meta, "Creator"),
        "Creator": _coalesce(meta, "Creator"),
        "Drive Link": _coalesce(meta, "Creative Folder Link", "Creative Folder", "1:1 Creative Link", "4:5 Creative Link", "9:16 Creative Link"),
        "Preview Asset Link": _coalesce(meta, "1:1 Creative Link", "4:5 Creative Link", "9:16 Creative Link", "Creative Folder Link", "Creative Folder"),
        "Source Folder Link": _coalesce(meta, "Creative Folder Link", "Creative Folder"),
        "Thumbnail Link": "",
        "Brief Link": _coalesce(meta, "Asana Link"),
        "Reference Image Link": "",
        "Landing Page URL": _coalesce(meta, "Landing Page URL"),
        "Instagram / Live Link": "",
        "Campaign Name": _coalesce(meta, "FB Ad Name", "Ad Name (TSS)", "Ad Name (Porcellia)"),
        "Ad Set Name": "",
        "Status": _coalesce(meta, "Status"),
        "Notes": _coalesce(meta, "Comment", "Comments"),
        "Needs Attention": "Likely in-house row missing from Master_Asset_Registry" if source == "Needs Logging" else "",
    }
    _add_metric_fields(row, meta)
    return row


def build_creative_ops_view(meta_df: pd.DataFrame | None = None,
                            assets_df: pd.DataFrame | None = None,
                            influencer_df: pd.DataFrame | None = None) -> pd.DataFrame:
    meta = load_meta_ads() if meta_df is None else meta_df.copy()
    assets = load_assets() if assets_df is None else assets_df.copy()
    influencers = load_influencer_ads() if influencer_df is None else influencer_df.copy()

    if not meta.empty:
        if "AD CODE" not in meta.columns:
            meta["AD CODE"] = ""
        meta["AD CODE"] = meta["AD CODE"].map(normalize_ad_code)
        meta["_Meta Live Date"] = _meta_live_date(meta)

    if not assets.empty:
        assets = _ensure_columns(assets, MASTER_HEADERS)
        assets["Meta Ad ID"] = assets["Meta Ad ID"].map(normalize_ad_code)

    if not influencers.empty:
        if "Perf AD Code" not in influencers.columns:
            influencers["Perf AD Code"] = ""
        influencers["Perf AD Code"] = influencers["Perf AD Code"].map(normalize_ad_code)

    meta_by_code = {}
    if not meta.empty and "AD CODE" in meta.columns:
        meta_valid = meta[meta["AD CODE"].astype(str).str.strip() != ""].copy()
        meta_by_code = {
            code: row for code, row in meta_valid.drop_duplicates("AD CODE", keep="last").set_index("AD CODE").iterrows()
        }

    master_codes = set()
    rows: list[dict] = []

    if not assets.empty:
        for _, asset in assets.iterrows():
            code = normalize_ad_code(asset.get("Meta Ad ID", ""))
            if not code:
                continue
            master_codes.add(code)
            rows.append(_normalized_master_row(asset, meta_by_code.get(code)))

    influencer_perf_codes = set()
    if not influencers.empty:
        for _, influencer in influencers.iterrows():
            perf_code = normalize_ad_code(influencer.get("Perf AD Code", ""))
            if perf_code:
                influencer_perf_codes.add(perf_code)
            # Keep creator-live rows even when Perf AD Code is blank.
            if _truthy(influencer.get("Date")) or perf_code:
                rows.append(_normalized_influencer_row(influencer, meta_by_code.get(perf_code)))

    if not meta.empty:
        classified = classify_meta_ads(meta, assets, influencers)
        for _, meta_row in classified.iterrows():
            code = normalize_ad_code(meta_row.get("AD CODE", ""))
            if not code or code in master_codes or code in influencer_perf_codes:
                continue
            source = meta_row.get("Source", "Porcellia")
            if source in {"Porcellia", "Needs Logging", "Unclassified", "Influencer"}:
                rows.append(_normalized_meta_row(meta_row, source))

    out = pd.DataFrame(rows)
    if out.empty:
        return pd.DataFrame()

    out["AD CODE Normalized"] = out["AD CODE"].map(normalize_ad_code)
    out["_Date"] = parse_mixed_dates(out["Live Date"]) if "Live Date" in out.columns else pd.NaT
    out["Date"] = out["_Date"]
    out["Product Derived"] = out["Product"].fillna("") if "Product" in out.columns else ""
    out["Format Derived"] = out["Format"].fillna("") if "Format" in out.columns else ""
    out["Marketing Angle Derived"] = out["Marketing Angle"].fillna("") if "Marketing Angle" in out.columns else ""
    out["Creative Name Derived"] = out["Creative Name"].fillna("") if "Creative Name" in out.columns else ""
    return out


def build_classified_meta_view(meta_df: pd.DataFrame | None = None,
                               inhouse_df: pd.DataFrame | None = None,
                               influencer_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Backward-compatible name now returns the full Creative Ops view."""
    return build_creative_ops_view(meta_df=meta_df, assets_df=inhouse_df, influencer_df=influencer_df)


def backlog_tag_candidates() -> pd.DataFrame:
    view = build_creative_ops_view()
    if view.empty or "Source" not in view.columns:
        return view
    return view[view["Source"].isin(["Needs Logging"])].copy()


def unimported_meta_candidates() -> pd.DataFrame:
    return backlog_tag_candidates()


def save_inhouse_live(data: dict):
    """Legacy writer redirected to Master to avoid creating a second source of truth."""
    mapped = {header: data.get(header, "") for header in MASTER_HEADERS}
    mapped.update({
        "Meta Ad ID": data.get("AD CODE", data.get("Meta Ad ID", "")),
        "Creative Type": data.get("Video Subtype") or data.get("Static Subtype") or data.get("Creative Type", ""),
        "Channel": "In-house",
        "Status": data.get("Status", "Published"),
        "Preview Asset Link": data.get("Reference Image Link", data.get("Preview Asset Link", "")),
    })
    save_asset(mapped)


def ensure_inhouse_sheet():
    return False


def migrate_master_to_inhouse() -> tuple[int, int, list[str]]:
    return 0, 0, ["Disabled: Master_Asset_Registry is now the primary in-house source."]


def folder_id_from_url(url: str) -> str:
    text = str(url or "").strip()
    if not text:
        return ""
    match = re.search(r"/folders/([a-zA-Z0-9_-]+)", text)
    if match:
        return match.group(1)
    parsed = urlparse(text)
    if parsed.path:
        parts = [part for part in parsed.path.split("/") if part]
        if parts:
            return parts[-1]
    return text


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
    "Skit", "Event Coverage", "AI-Video", "Influencer Video",
}


def next_asset_id(product: str, creative_type_or_format: str, existing: list) -> str:
    prefix_product = _PRODUCT_CODE.get(product, "TSS")
    value = (creative_type_or_format or "").strip()
    creative_prefix = "V" if value == "Video" or value in _VIDEO_TYPES else "S"
    prefix = f"{prefix_product}-{creative_prefix}-"
    nums = [
        int(str(item).split("-")[-1]) for item in existing
        if str(item).startswith(prefix) and str(item).split("-")[-1].isdigit()
    ]
    return f"{prefix}{str(max(nums, default=0) + 1).zfill(3)}"


def next_experiment_id(existing: list) -> str:
    nums = [
        int(str(item).split("-")[-1]) for item in existing
        if str(item).startswith("EXP-") and str(item).split("-")[-1].isdigit()
    ]
    return f"EXP-{str(max(nums, default=0) + 1).zfill(3)}"


def next_source_id(existing: list) -> str:
    nums = [
        int(str(item).split("-")[-1]) for item in existing
        if str(item).startswith("SRC-") and str(item).split("-")[-1].isdigit()
    ]
    return f"SRC-{str(max(nums, default=0) + 1).zfill(3)}"


def initialise_sheets():
    spreadsheet = _client().open(st.secrets["spreadsheet_name"])
    existing = {ws.title for ws in spreadsheet.worksheets()}
    to_create = {
        SHEET_ASSETS: MASTER_HEADERS,
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
    if SHEET_ASSETS in existing:
        ensure_master_asset_schema()
    _clear_sheet_cache()
    return True
