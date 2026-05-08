from datetime import date, timedelta
import re

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.sheets import build_creative_ops_view, load_performance_import, normalize_ad_code, refresh_sheet_cache


st.set_page_config(page_title="Dashboard - Creative OS", layout="wide")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.25rem; max-width: 1400px; }
    h1 { letter-spacing: -0.04em; color: #18251f; }
    h2, h3 { color: #18251f; }
    div[data-testid="metric-container"] {
        background: linear-gradient(135deg, #f7fbf4 0%, #edf6f2 100%);
        border: 1px solid #d8e9df;
        border-radius: 18px;
        padding: 1rem 1.05rem;
        box-shadow: 0 8px 26px rgba(30, 71, 50, 0.06);
    }
    .asset-card {
        border: 1px solid #dce8df;
        border-radius: 18px;
        padding: 1rem;
        background: #ffffff;
        box-shadow: 0 10px 30px rgba(31, 49, 39, 0.06);
        margin-bottom: 0.75rem;
    }
    .pill {
        display: inline-block;
        padding: 0.18rem 0.55rem;
        border-radius: 999px;
        background: #eaf5ef;
        color: #174834;
        font-size: 0.78rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
    }
    .muted { color: #6d756f; }
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe_text(value, fallback="-"):
    text = str(value or "").strip()
    return text if text and text.lower() not in {"nan", "nat", "none"} else fallback


def _file_id_from_drive_url(url: str) -> str:
    text = str(url or "")
    patterns = [
        r"/file/d/([a-zA-Z0-9_-]+)",
        r"/folders/([a-zA-Z0-9_-]+)",
        r"[?&]id=([a-zA-Z0-9_-]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def _thumbnail_url(row: pd.Series) -> str:
    for column in ["Thumbnail Link", "Preview Asset Link", "Drive Link", "Source Folder Link"]:
        value = str(row.get(column, "") or "").strip()
        if not value:
            continue
        if value.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return value
        file_id = _file_id_from_drive_url(value)
        if file_id and "/folders/" not in value:
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w900"
    return ""


def _fmt_date(value) -> str:
    if pd.isna(value):
        return "-"
    try:
        return pd.Timestamp(value).strftime("%d %b %Y")
    except Exception:
        return _safe_text(value)


def _metric_value(row: pd.Series, field: str):
    value = row.get(field, "")
    return _safe_text(value)


def _link(label: str, url: str):
    if _safe_text(url, ""):
        st.markdown(f"[{label}]({url})")


PERFORMANCE_STAT_ORDER = [
    ("Amount spent", "Amount Spent"),
    ("Revenue", "Revenue"),
    ("ROAS", "ROAS"),
    ("CPM", "CPM"),
    ("CPR", "CPR"),
    ("CTR", "CTR"),
    ("CPC", "CPC"),
    ("ATC rate", "ATC Rate"),
    ("CVR", "CVR"),
    ("AOV", "AOV"),
    ("ROAS", "ROAS"),
    ("CAC", "CAC"),
]

PERFORMANCE_COLUMN_ORDER = []
for _, metric_field in PERFORMANCE_STAT_ORDER:
    if metric_field not in PERFORMANCE_COLUMN_ORDER:
        PERFORMANCE_COLUMN_ORDER.append(metric_field)

GLOBAL_SEARCH_COLUMNS = [
    "AD CODE", "Perf AD Code", "Asset ID", "Creative Name", "Creator", "Creator / Consumer Name",
    "Product", "Format", "Creative Type", "Video Subtype", "Static Subtype", "Source",
    "Marketing Angle", "Cohort", "Belief", "Situational Driver", "Visual Hook Type",
    "Content Hook Type", "Static Message Type", "CTA Message Type", "Drive Link",
    "Source Folder Link", "Transcript Link", "Instagram / Live Link", "Campaign Name",
    "Notes", "Taxonomy Review Status", "Post-CRAN Parent AD CODE", "Post-CRAN Change Summary",
]


NUMERIC_SORT_COLUMNS = {
    "ROAS", "Amount Spent", "Revenue", "CPM", "CPR", "Avg Cost Per Reach", "CTR", "CPC",
    "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "CPM (L30)", "CPR (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
    "ROAS (L7)", "Amount Spent (L7)", "Revenue (L7)", "CPM (L7)", "CPR (L7)", "Avg Cost Per Reach (L7)",
    "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)",
    "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
    "Views", "Likes", "Comments", "Shares", "Saves", "Total Engagement",
    "Engagement Rate (%)", "Followers", "Creatives", "Filled", "Total", "Coverage",
}


def _row_key(row: pd.Series) -> str:
    parts = [
        row.get("Source", ""),
        row.get("AD CODE", ""),
        row.get("Perf AD Code", ""),
        row.get("Asset ID", ""),
        row.get("Creative Name", ""),
        _fmt_date(row.get("_Date", "")),
    ]
    return "|".join(str(part) for part in parts)


def _number(value):
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "nat", "none", "#div/0!"}:
        return pd.NA
    cleaned = re.sub(r"[₹,%\s]", "", text.replace(",", ""))
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", ".", "-", "-."}:
        return pd.NA
    return pd.to_numeric(cleaned, errors="coerce")


def _float(value) -> float | None:
    parsed = _number(value)
    return None if pd.isna(parsed) else float(parsed)


def _pct_delta(current, previous, inverse_good: bool = False) -> tuple[str, str]:
    cur = _float(current)
    prev = _float(previous)
    if cur is None or prev is None or prev == 0:
        return "not enough data", "flat"
    change = (cur - prev) / abs(prev)
    if inverse_good:
        good = change < 0
    else:
        good = change > 0
    direction = "up" if change > 0 else "down"
    quality = "good" if good else "bad"
    return f"{direction} {abs(change) * 100:.0f}% ({prev:g} -> {cur:g})", quality


def _dedupe_columns(data: pd.DataFrame) -> pd.DataFrame:
    """Keep the first copy of any duplicate display column name."""
    if data.columns.duplicated().any():
        return data.loc[:, ~data.columns.duplicated()].copy()
    return data


def _series(data: pd.DataFrame, column: str) -> pd.Series:
    values = data.loc[:, column]
    if isinstance(values, pd.DataFrame):
        return values.iloc[:, 0]
    return values


def _with_live_date(data: pd.DataFrame) -> pd.DataFrame:
    output = data.copy()
    if "_Date" in output.columns:
        output = output.drop(columns=["Live Date"], errors="ignore")
        output = output.rename(columns={"_Date": "Live Date"})
    return _dedupe_columns(output)


def _prepare_performance_metrics(data: pd.DataFrame) -> pd.DataFrame:
    output = data.copy()
    for metric in PERFORMANCE_COLUMN_ORDER:
        if metric not in output.columns:
            output[metric] = ""
    if "Avg Cost Per Reach" in output.columns:
        cpr_blank = output["CPR"].astype(str).str.strip().isin(["", "nan", "None", "NaT"])
        output.loc[cpr_blank, "CPR"] = output.loc[cpr_blank, "Avg Cost Per Reach"]
    return output


def _apply_global_search(data: pd.DataFrame, search_value: str) -> pd.DataFrame:
    if data.empty or not str(search_value or "").strip():
        return data
    terms = [term.lower() for term in re.split(r"\s+", search_value.strip()) if term.strip()]
    if not terms:
        return data
    searchable = [column for column in GLOBAL_SEARCH_COLUMNS if column in data.columns]
    if not searchable:
        return data
    haystack = data[searchable].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
    mask = pd.Series(True, index=data.index)
    for term in terms:
        mask = mask & haystack.str.contains(re.escape(term), na=False)
    return data[mask].copy()


def _is_yes(value) -> bool:
    return str(value or "").strip().lower() in {"yes", "true", "1", "y"}


def _is_post_cran_row(row: pd.Series) -> bool:
    if _is_yes(row.get("Is Post-CRAN", "")):
        return True
    text = " ".join(str(row.get(column, "") or "") for column in [
        "Creative Name", "Campaign Name", "Drive Link", "Source Folder Link",
        "Notes", "Post-CRAN Change Summary",
    ])
    return bool(re.search(r"\bpost\s*[-_ ]?\s*cran\b", text, flags=re.IGNORECASE))


def _add_post_cran_flag(data: pd.DataFrame) -> pd.DataFrame:
    output = data.copy()
    if "Is Post-CRAN" not in output.columns:
        output["Is Post-CRAN"] = ""
    output["Post-CRAN"] = output.apply(lambda row: "Yes" if _is_post_cran_row(row) else "", axis=1)
    return output


def _add_performance_buckets(data: pd.DataFrame, low_spend: float, top_roas: float, potential_roas: float, low_roas: float) -> pd.DataFrame:
    output = data.copy()
    spend = output["Amount Spent"].map(_number) if "Amount Spent" in output.columns else pd.Series(pd.NA, index=output.index)
    roas = output["ROAS"].map(_number) if "ROAS" in output.columns else pd.Series(pd.NA, index=output.index)
    ctr = output["CTR"].map(_number) if "CTR" in output.columns else pd.Series(pd.NA, index=output.index)
    atc = output["ATC Rate"].map(_number) if "ATC Rate" in output.columns else pd.Series(pd.NA, index=output.index)
    cvr = output["CVR"].map(_number) if "CVR" in output.columns else pd.Series(pd.NA, index=output.index)

    enough_spend = spend.fillna(0) >= low_spend
    ctr_med = ctr[enough_spend].dropna().median()
    atc_med = atc[enough_spend].dropna().median()
    cvr_med = cvr[enough_spend].dropna().median()

    buckets = []
    reasons = []
    for idx in output.index:
        row_spend = spend.loc[idx]
        row_roas = roas.loc[idx]
        strong_signal = False
        signal_bits = []
        for label, series, median in [("CTR", ctr, ctr_med), ("ATC", atc, atc_med), ("CVR", cvr, cvr_med)]:
            value = series.loc[idx]
            if pd.notna(value) and pd.notna(median) and median > 0 and value >= median:
                strong_signal = True
                signal_bits.append(f"{label} above median")

        if pd.isna(row_spend) or row_spend < low_spend:
            buckets.append("Still Learning (Low Spend)")
            reasons.append(f"Spend below {low_spend:g}; do not judge too early.")
        elif pd.notna(row_roas) and row_roas >= top_roas:
            buckets.append("Top Performer")
            reasons.append(f"ROAS {row_roas:g} is at/above top threshold {top_roas:g}.")
        elif pd.notna(row_roas) and row_roas >= potential_roas:
            buckets.append("Potential Performer")
            reasons.append(f"ROAS {row_roas:g} is usable but not top yet.")
        elif strong_signal and (pd.isna(row_roas) or row_roas >= low_roas):
            buckets.append("Potential Performer")
            reasons.append("; ".join(signal_bits) + ".")
        elif pd.notna(row_roas) and row_roas < low_roas:
            buckets.append("Low Performer")
            reasons.append(f"ROAS {row_roas:g} is below low threshold {low_roas:g} after enough spend.")
        else:
            buckets.append("Still Learning (Low Spend)")
            reasons.append("Performance signal is not decisive yet.")

    output["Performance Bucket"] = buckets
    output["Performance Read"] = reasons
    return output


def _find_post_cran_parent(data: pd.DataFrame, row: pd.Series) -> pd.Series | None:
    if data.empty or not _is_post_cran_row(row):
        return None
    candidates = data.copy()
    current_code = normalize_ad_code(row.get("AD CODE", ""))
    parent_code = normalize_ad_code(row.get("Post-CRAN Parent AD CODE", ""))
    if parent_code:
        hits = candidates[candidates["AD CODE"].map(normalize_ad_code) == parent_code]
        if not hits.empty:
            return hits.iloc[-1]

    parent_asset = str(row.get("Post-CRAN Parent Asset ID", "") or "").strip()
    if parent_asset and "Asset ID" in candidates.columns:
        hits = candidates[candidates["Asset ID"].astype(str).str.strip() == parent_asset]
        if not hits.empty:
            return hits.iloc[-1]

    candidates = candidates[candidates["AD CODE"].map(normalize_ad_code) != current_code]
    candidates = candidates[~candidates.apply(_is_post_cran_row, axis=1)]
    if "Product" in candidates.columns and _safe_text(row.get("Product"), ""):
        candidates = candidates[candidates["Product"].astype(str) == str(row.get("Product"))]
    if "Format" in candidates.columns and _safe_text(row.get("Format"), ""):
        candidates = candidates[candidates["Format"].astype(str) == str(row.get("Format"))]

    creator = str(row.get("Creator") or row.get("Creator / Consumer Name") or "").strip().lower()
    if creator:
        creator_cols = [column for column in ["Creator", "Creator / Consumer Name", "Creative Name"] if column in candidates.columns]
        mask = pd.Series(False, index=candidates.index)
        for column in creator_cols:
            mask = mask | candidates[column].astype(str).str.lower().str.contains(re.escape(creator), na=False)
        candidates = candidates[mask]

    if "_Date" in candidates.columns and pd.notna(row.get("_Date")):
        candidates = candidates[candidates["_Date"] < row.get("_Date")]
        candidates = candidates.sort_values("_Date", ascending=False)

    return None if candidates.empty else candidates.iloc[0]


def _post_cran_insight(row: pd.Series, parent: pd.Series | None) -> str:
    if parent is None:
        return "Post-CRAN version detected, but no parent version could be matched yet. Add Parent AD CODE for a clean comparison."
    parts = []
    for label, field, inverse in [
        ("ROAS", "ROAS", False),
        ("CTR", "CTR", False),
        ("CPC", "CPC", True),
        ("CAC", "CAC", True),
    ]:
        text, quality = _pct_delta(row.get(field), parent.get(field), inverse_good=inverse)
        if text != "not enough data":
            parts.append(f"{label} is {text}")
    if not parts:
        return f"Matched to parent {normalize_ad_code(parent.get('AD CODE', ''))}, but performance fields are not populated enough yet."
    return f"Compared with {normalize_ad_code(parent.get('AD CODE', ''))}: " + "; ".join(parts[:3]) + "."


def _sort_dataframe(data: pd.DataFrame, sort_by: str, descending: bool) -> pd.DataFrame:
    if data.empty or sort_by not in data.columns:
        return data
    sortable = _dedupe_columns(data.copy())
    sort_values = _series(sortable, sort_by)
    if sort_by in NUMERIC_SORT_COLUMNS:
        sortable["_sort_key"] = sort_values.map(_number)
    elif sort_by in {"_Date", "Live Date", "Date", "Published Date"}:
        sortable["_sort_key"] = pd.to_datetime(sort_values, errors="coerce", dayfirst=True)
    else:
        sortable["_sort_key"] = sort_values.astype(str).str.lower()
    return sortable.sort_values("_sort_key", ascending=not descending, na_position="last").drop(columns="_sort_key")


def _table_controls(
    data: pd.DataFrame,
    key: str,
    search_columns: list[str],
    filter_columns: list[str],
    default_sort: str,
    expanded: bool = False,
) -> pd.DataFrame:
    if data.empty:
        return data

    working = data.copy()
    with st.expander("Search, filter, and sort this table", expanded=expanded):
        search_value = st.text_input("Search", key=f"{key}_search", placeholder="name, AD CODE, creator, angle, product...")
        if search_value.strip():
            term = search_value.strip().lower()
            mask = pd.Series(False, index=working.index)
            for column in [c for c in search_columns if c in working.columns]:
                mask = mask | working[column].astype(str).str.lower().str.contains(term, na=False)
            working = working[mask]

        filter_cols = st.columns(3)
        for idx, column in enumerate([c for c in filter_columns if c in working.columns]):
            options = sorted(v for v in working[column].dropna().astype(str).unique() if v.strip())
            if not options:
                continue
            selected = filter_cols[idx % 3].multiselect(column, options, key=f"{key}_filter_{column}", placeholder=f"All {column}")
            if selected:
                working = working[working[column].astype(str).isin(selected)]

        sort_options = [c for c in working.columns if not str(c).startswith("_")]
        fallback_sort = default_sort if default_sort in sort_options else (sort_options[0] if sort_options else "")
        if sort_options:
            s1, s2 = st.columns([0.7, 0.3])
            sort_by = s1.selectbox("Sort by", sort_options, index=sort_options.index(fallback_sort), key=f"{key}_sort_by")
            descending = s2.toggle("Descending", value=True, key=f"{key}_sort_desc")
            working = _sort_dataframe(working, sort_by, descending)

    return working


def _numeric_display(data: pd.DataFrame) -> pd.DataFrame:
    output = data.copy()
    for column in [c for c in output.columns if c in NUMERIC_SORT_COLUMNS]:
        output[column] = output[column].map(_number).astype("Float64")
    return output


st.title("Dashboard")
st.caption(
    "One Creative Ops view across Inhouse, Influencer, and Porcellia. "
    "Dates are driven by live dates: Meta Ads for performance ads, Live Entries 2026 for influencer creator-live rows."
)

top_refresh, top_note = st.columns([0.22, 0.78])
with top_refresh:
    if st.button("Refresh sheet data", type="primary", use_container_width=True):
        refresh_sheet_cache()
        st.rerun()
with top_note:
    perf_df = load_performance_import()
    if perf_df.empty:
        st.caption("Performance source: no `Performance_Import` / performance SyncWith tab found yet.")
    else:
        source_name = perf_df["Performance Sheet"].iloc[0] if "Performance Sheet" in perf_df.columns else "Performance_Import"
        st.caption(f"Performance source: `{source_name}` with {len(perf_df)} AD CODE rows. Click refresh after SyncWith updates.")

with st.spinner("Loading Master, Meta Ads, and Live Entries 2026..."):
    raw = build_creative_ops_view()

if raw.empty:
    st.error("No usable Creative OS data could be built from the connected sheets.")
    st.stop()

df = raw.copy()
df = df[df["_Date"].notna()]
reasonable_floor = pd.Timestamp("2020-01-01")
reasonable_ceiling = pd.Timestamp.today().normalize() + pd.Timedelta(days=7)
df = df[(df["_Date"] >= reasonable_floor) & (df["_Date"] <= reasonable_ceiling)]
df = _prepare_performance_metrics(df)
df = _add_post_cran_flag(df)

if df.empty:
    st.warning("Rows loaded, but none had a usable live date after parsing.")
    with st.expander("Data audit", expanded=True):
        st.write(f"Raw rows built: {len(raw)}")
        st.dataframe(raw.head(50), use_container_width=True, hide_index=True)
    st.stop()

latest = df["_Date"].max().date()
earliest = df["_Date"].min().date()

with st.sidebar:
    st.header("Find Creatives")
    simple_search = st.text_input(
        "Simple search",
        placeholder="consumer name, AD CODE, product, static/video...",
        help="Searches across all dashboard tabs: consumer, creator, creative name, AD CODE, product, format, taxonomy, links, and notes.",
    )
    if simple_search.strip():
        st.caption("Tip: search `laxmi`, `AD 568`, `RCF`, `postcran`, `video`, etc.")

    st.header("Date")
    preset = st.radio(
        "Date range",
        ["Last 7 days", "Last 14 days", "Last 30 days", "This month", "All time", "Custom"],
        index=2,
    )
    today = date.today()
    if preset == "Last 7 days":
        start, end = latest - timedelta(days=6), latest
    elif preset == "Last 14 days":
        start, end = latest - timedelta(days=13), latest
    elif preset == "Last 30 days":
        start, end = latest - timedelta(days=29), latest
    elif preset == "This month":
        start, end = latest.replace(day=1), latest
    elif preset == "All time":
        start, end = earliest, latest
    else:
        start = st.date_input("From", value=max(earliest, latest - timedelta(days=29)))
        end = st.date_input("To", value=latest if latest <= today + timedelta(days=365) else today)

    st.caption(f"Available data: {earliest.strftime('%d %b %Y')} to {latest.strftime('%d %b %Y')}")

    with st.expander("Performer logic", expanded=False):
        low_spend_threshold = st.number_input("Still learning below spend", min_value=0.0, value=3000.0, step=500.0)
        top_roas_threshold = st.number_input("Top performer ROAS >=", min_value=0.0, value=1.5, step=0.1)
        potential_roas_threshold = st.number_input("Potential performer ROAS >=", min_value=0.0, value=1.0, step=0.1)
        low_roas_threshold = st.number_input("Low performer ROAS <", min_value=0.0, value=0.8, step=0.1)
        st.caption("Potential also includes creatives with enough spend and strong CTR/ATC/CVR vs the current loaded dataset.")

df = _add_performance_buckets(df, low_spend_threshold, top_roas_threshold, potential_roas_threshold, low_roas_threshold)

with st.sidebar:
    st.header("Filters")
    source_order = ["Inhouse", "Influencer", "Porcellia", "Needs Logging", "Unclassified"]
    sources_present = [source for source in source_order if source in set(df["Source"].astype(str))]
    selected_sources = st.multiselect("Source", sources_present, default=[s for s in sources_present if s != "Unclassified"])

    product_options = sorted(v for v in df["Product"].dropna().astype(str).unique() if v.strip())
    selected_products = st.multiselect("Product", product_options, default=product_options)

    format_options = sorted(v for v in df["Format"].dropna().astype(str).unique() if v.strip())
    selected_formats = st.multiselect("Format", format_options, default=format_options)

    bucket_options = ["Top Performer", "Potential Performer", "Low Performer", "Still Learning (Low Spend)"]
    selected_buckets = st.multiselect("Performer bucket", [b for b in bucket_options if b in set(df["Performance Bucket"])], default=[])

    angle_options = sorted(v for v in df["Marketing Angle"].dropna().astype(str).unique() if v.strip()) if "Marketing Angle" in df.columns else []
    selected_angles = st.multiselect("Marketing angle", angle_options, default=[])

    content_options = sorted(v for v in df["Content Hook Type"].dropna().astype(str).unique() if v.strip()) if "Content Hook Type" in df.columns else []
    selected_content_hooks = st.multiselect("Content hook", content_options, default=[])

    review_options = sorted(v for v in df["Taxonomy Review Status"].dropna().astype(str).unique() if v.strip()) if "Taxonomy Review Status" in df.columns else []
    selected_review_status = st.multiselect("Taxonomy review", review_options, default=[])

    postcran_filter = st.selectbox("Post-CRAN", ["All", "Post-CRAN only", "Exclude Post-CRAN"])


filtered = df.copy()
filtered = filtered[(filtered["_Date"] >= pd.Timestamp(start)) & (filtered["_Date"] <= pd.Timestamp(end))]
filtered = _apply_global_search(filtered, simple_search)
if selected_sources:
    filtered = filtered[filtered["Source"].isin(selected_sources)]
if selected_products:
    filtered = filtered[filtered["Product"].isin(selected_products) | filtered["Product"].astype(str).str.strip().eq("")]
if selected_formats:
    filtered = filtered[filtered["Format"].isin(selected_formats) | filtered["Format"].astype(str).str.strip().eq("")]
if selected_buckets:
    filtered = filtered[filtered["Performance Bucket"].isin(selected_buckets)]
if selected_angles:
    filtered = filtered[filtered["Marketing Angle"].isin(selected_angles)]
if selected_content_hooks:
    filtered = filtered[filtered["Content Hook Type"].isin(selected_content_hooks)]
if selected_review_status:
    filtered = filtered[filtered["Taxonomy Review Status"].isin(selected_review_status)]
if postcran_filter == "Post-CRAN only":
    filtered = filtered[filtered["Post-CRAN"] == "Yes"]
elif postcran_filter == "Exclude Post-CRAN":
    filtered = filtered[filtered["Post-CRAN"] != "Yes"]

if filtered.empty:
    st.warning("No creatives match the current filters.")
    st.stop()

st.markdown(f"### {len(filtered)} creatives live from {_fmt_date(pd.Timestamp(start))} to {_fmt_date(pd.Timestamp(end))}")

source_counts = filtered["Source"].value_counts()
metrics = st.columns(6)
metrics[0].metric("Total creatives", len(filtered))
metrics[1].metric("Inhouse", int(source_counts.get("Inhouse", 0)))
metrics[2].metric("Influencer", int(source_counts.get("Influencer", 0)))
metrics[3].metric("Porcellia", int(source_counts.get("Porcellia", 0)))
metrics[4].metric("Needs logging", int(source_counts.get("Needs Logging", 0)))
metrics[5].metric("With AD CODE", int(filtered["AD CODE"].astype(str).str.contains("AD ", na=False).sum()))

bucket_counts = filtered["Performance Bucket"].value_counts() if "Performance Bucket" in filtered.columns else pd.Series(dtype=int)
bucket_cards = st.columns(4)
bucket_cards[0].metric("Top performers", int(bucket_counts.get("Top Performer", 0)))
bucket_cards[1].metric("Potential", int(bucket_counts.get("Potential Performer", 0)))
bucket_cards[2].metric("Low performers", int(bucket_counts.get("Low Performer", 0)))
bucket_cards[3].metric("Still learning", int(bucket_counts.get("Still Learning (Low Spend)", 0)))

tab_overview, tab_assets, tab_performers, tab_quality, tab_audit = st.tabs(
    ["Overview", "Creative Deep Dive", "Performer View", "Quality & Taxonomy", "Data Audit"]
)

color_map = {
    "Inhouse": "#0f6e56",
    "Influencer": "#2b8fd8",
    "Porcellia": "#e2a33a",
    "Needs Logging": "#d85542",
    "Unclassified": "#8c9490",
}

with tab_overview:
    left, right = st.columns([1.05, 1])
    with left:
        timeline = filtered.copy()
        timeline["Day"] = timeline["_Date"].dt.date
        daily = timeline.groupby(["Day", "Source"]).size().reset_index(name="Creatives")
        fig = px.bar(
            daily,
            x="Day",
            y="Creatives",
            color="Source",
            barmode="stack",
            color_discrete_map=color_map,
        )
        fig.update_layout(margin=dict(l=10, r=10, t=20, b=10), xaxis_title="", yaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        split = filtered["Source"].value_counts().reset_index()
        split.columns = ["Source", "Creatives"]
        fig = px.pie(split, names="Source", values="Creatives", color="Source", color_discrete_map=color_map, hole=0.45)
        fig.update_layout(margin=dict(l=10, r=10, t=20, b=10))
        st.plotly_chart(fig, use_container_width=True)

    left, mid, right = st.columns(3)
    with left:
        product = filtered["Product"].replace("", "Unknown").value_counts().head(12).reset_index()
        product.columns = ["Product", "Creatives"]
        st.subheader("Product mix")
        st.dataframe(product, use_container_width=True, hide_index=True)
    with mid:
        fmt = filtered["Format"].replace("", "Unknown").value_counts().reset_index()
        fmt.columns = ["Format", "Creatives"]
        st.subheader("Format mix")
        st.dataframe(fmt, use_container_width=True, hide_index=True)
    with right:
        perf_ready = filtered[filtered["Perf AD Code"].astype(str).str.contains("AD ", na=False)]
        st.subheader("Performance readiness")
        st.metric("Rows with Perf AD Code", len(perf_ready))
        st.metric("Rows missing Perf AD Code", len(filtered) - len(perf_ready))

with tab_assets:
    st.subheader("Creative gallery")
    st.caption("Use the table controls below to narrow the list. Select a row in the table and it will pin into this detail view.")

    sort_cols = ["_Date", "Source", "Creative Name"]
    gallery = filtered.sort_values([c for c in sort_cols if c in filtered.columns], ascending=[False, True, True]).copy()
    gallery["_Row Key"] = gallery.apply(_row_key, axis=1)
    gallery["_Preview"] = gallery.apply(_thumbnail_url, axis=1)

    gallery_table = _with_live_date(gallery)
    table_cols = [
        "_Preview", "Source", "Record Type", "AD CODE", "Perf AD Code", "Live Date", "Creative Name", "Product",
        "Format", "Marketing Angle", "Cohort", "Belief", "Content Hook Type", "Static Message Type",
        "Funnel Stage", "Creator", "Performance Bucket", "Post-CRAN", "Post-CRAN Parent AD CODE", *PERFORMANCE_COLUMN_ORDER,
        "Drive Link", "Transcript Link", "Instagram / Live Link", "_Row Key",
    ]
    gallery_table = gallery_table[[c for c in table_cols if c in gallery_table.columns]]
    gallery_table = _table_controls(
        gallery_table,
        key="dashboard_deep_dive",
        search_columns=[
            "AD CODE", "Perf AD Code", "Asset ID", "Creative Name", "Creator", "Creator / Consumer Name",
            "Marketing Angle", "Cohort", "Belief", "Visual Hook Type", "Content Hook Type",
            "Static Message Type", "CTA Message Type", "Product", "Format", "Source", "Drive Link", "Transcript Link", "Instagram / Live Link",
        ],
        filter_columns=["Source", "Record Type", "Product", "Format", "Performance Bucket", "Post-CRAN", "Marketing Angle", "Cohort", "Belief", "Funnel Stage", "Content Hook Type", "Static Message Type", "Creator"],
        default_sort="Live Date",
        expanded=True,
    )

    if gallery_table.empty:
        st.warning("No creatives match the Creative Deep Dive table filters.")
        st.stop()

    selected_key = st.session_state.get("dashboard_selected_row_key")
    if selected_key not in set(gallery_table["_Row Key"].astype(str)):
        selected_key = str(gallery_table.iloc[0]["_Row Key"])
        st.session_state["dashboard_selected_row_key"] = selected_key
    picked = gallery[gallery["_Row Key"].astype(str) == selected_key].iloc[0]

    hero, detail = st.columns([0.9, 1.35])
    with hero:
        st.markdown('<div class="asset-card">', unsafe_allow_html=True)
        thumb = _thumbnail_url(picked)
        if thumb:
            st.image(thumb, use_container_width=True)
        else:
            st.info("No preview thumbnail available yet. Add a Preview Asset Link or Drive image link in Master.")

        st.markdown(f"### {_safe_text(picked.get('Creative Name'))}")
        st.markdown(
            f"<span class='pill'>{_safe_text(picked.get('Source'))}</span>"
            f"<span class='pill'>{_safe_text(picked.get('Product'))}</span>"
            f"<span class='pill'>{_safe_text(picked.get('Format'))}</span>",
            unsafe_allow_html=True,
        )
        st.write(f"**Live date:** {_fmt_date(picked.get('_Date'))}")
        st.write(f"**AD CODE:** {_safe_text(picked.get('AD CODE'))}")
        st.write(f"**Perf AD Code:** {_safe_text(picked.get('Perf AD Code'))}")
        _link("Open Drive / Creative Link", picked.get("Drive Link", ""))
        _link("Open Source Folder", picked.get("Source Folder Link", ""))
        _link("Open Transcript", picked.get("Transcript Link", ""))
        _link("Open Instagram / Live Link", picked.get("Instagram / Live Link", ""))
        _link("Open Brief / Asana", picked.get("Brief Link", ""))
        st.markdown("</div>", unsafe_allow_html=True)

    with detail:
        id_tab, tax_tab, perf_tab = st.tabs(["Identity", "Taxonomy", "Performance"])
        with id_tab:
            cols = st.columns(2)
            identity_fields = [
                "Asset ID", "Record Type", "Status", "Creator", "Creator / Consumer Name",
                "Agency", "POC", "Followers", "Platform", "Language", "Campaign Name",
                "Ad Set Name", "Landing Page URL", "Performance Bucket", "Performance Read",
                "Post-CRAN", "Post-CRAN Parent AD CODE", "Post-CRAN Parent Asset ID",
                "Post-CRAN Change Summary",
            ]
            for idx, field in enumerate(identity_fields):
                with cols[idx % 2]:
                    if field in picked.index:
                        st.write(f"**{field}:** {_safe_text(picked.get(field))}")

        with tax_tab:
            taxonomy_fields = [
                "Creative Type", "Video Subtype", "Static Subtype", "Content Bucket",
                "Marketing Angle", "Belief", "Cohort", "Situational Driver",
                "Funnel Stage", "Visual Hook Type", "Content Hook Type", "Emotional Arc",
                "Creator Archetype", "Influence Mode", "Visual Treatment", "Static Message Type",
                "CTA Format", "CTA Message Type", "AI-Generated", "Taxonomy Confidence",
                "Claim Codes", "Visual Style", "CTA Style", "Hook Type", "Source Interview ID", "Experiment ID",
                "Transcript Notes", "Aspect Ratio Links",
            ]
            cols = st.columns(2)
            for idx, field in enumerate(taxonomy_fields):
                with cols[idx % 2]:
                    if field in picked.index:
                        st.write(f"**{field}:** {_safe_text(picked.get(field))}")
            if _safe_text(picked.get("Needs Attention"), ""):
                st.warning(picked.get("Needs Attention"))

        with perf_tab:
            st.caption(f"Metric source: {_safe_text(picked.get('Metric Source'), 'No metric columns populated yet')}")
            if _is_post_cran_row(picked):
                parent_row = _find_post_cran_parent(df, picked)
                insight = _post_cran_insight(picked, parent_row)
                st.info(insight)
                if parent_row is not None:
                    st.caption(
                        f"Parent matched: {_safe_text(parent_row.get('Creative Name'))} "
                        f"({normalize_ad_code(parent_row.get('AD CODE', ''))})"
                    )
            for offset in range(0, len(PERFORMANCE_STAT_ORDER), 4):
                metric_cards = st.columns(4)
                for idx, (label, field) in enumerate(PERFORMANCE_STAT_ORDER[offset:offset + 4]):
                    metric_cards[idx].metric(label, _metric_value(picked, field))

            perf_cols = [
                *PERFORMANCE_COLUMN_ORDER,
                "Hook Rate", "Hold Rate",
                "Amount Spent (L30)", "Revenue (L30)", "ROAS (L30)", "CPM (L30)", "CPR (L30)",
                "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)", "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
                "Amount Spent (L7)", "Revenue (L7)", "ROAS (L7)", "CPM (L7)", "CPR (L7)",
                "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)", "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
                "Views", "Likes", "Comments", "Shares", "Saves", "Total Engagement", "Engagement Rate (%)",
            ]
            perf_table = pd.DataFrame(
                [{"Metric": field, "Value": picked.get(field, "")} for field in perf_cols if field in picked.index and _safe_text(picked.get(field), "")]
            )
            if perf_table.empty:
                st.info("No performance metrics are populated for this creative yet.")
            else:
                st.dataframe(perf_table, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**Filtered creative table**")
    table_display = gallery_table.drop(columns=["_Row Key"], errors="ignore").rename(columns={"_Preview": "Preview"})
    table_display = _numeric_display(table_display)
    table_event = st.dataframe(
        table_display,
        use_container_width=True,
        hide_index=True,
        height=420,
        on_select="rerun",
        selection_mode="single-row",
        key="dashboard_deep_dive_table",
        column_config={
            "Preview": st.column_config.ImageColumn("Preview", width="small"),
            "Drive Link": st.column_config.LinkColumn("Drive Link", display_text="Open"),
            "Transcript Link": st.column_config.LinkColumn("Transcript", display_text="Open"),
            "Instagram / Live Link": st.column_config.LinkColumn("Instagram", display_text="Open"),
        },
    )
    if table_event.selection.rows:
        selected_pos = table_event.selection.rows[0]
        new_key = str(gallery_table.iloc[selected_pos]["_Row Key"])
        if st.session_state.get("dashboard_selected_row_key") != new_key:
            st.session_state["dashboard_selected_row_key"] = new_key
            st.rerun()

with tab_performers:
    st.subheader("Creative analysis buckets")
    st.caption(
        "Use this for the creative analysis meeting: Top = scale/learn from it, Potential = improve and re-run, "
        "Low = diagnose or pause, Still Learning = don't judge yet because spend is low."
    )
    st.info(
        f"Current logic: Still Learning below spend {low_spend_threshold:g}; "
        f"Top if ROAS >= {top_roas_threshold:g}; Potential if ROAS >= {potential_roas_threshold:g} "
        "or leading indicators are strong; Low if enough spend and ROAS is weak."
    )

    performer_cols = [
        "Performance Bucket", "Performance Read", "Source", "AD CODE", "Live Date", "Creative Name",
        "Product", "Format", "Creator", "Marketing Angle", "Content Hook Type",
        "Post-CRAN", "Post-CRAN Parent AD CODE", *PERFORMANCE_COLUMN_ORDER,
        "Drive Link", "_Row Key",
    ]
    performer_table = _with_live_date(filtered[[c for c in performer_cols if c in filtered.columns]].copy())
    performer_table = _table_controls(
        performer_table,
        key="performer_view",
        search_columns=GLOBAL_SEARCH_COLUMNS + ["Performance Bucket", "Performance Read"],
        filter_columns=["Performance Bucket", "Source", "Product", "Format", "Marketing Angle", "Content Hook Type", "Post-CRAN"],
        default_sort="ROAS",
        expanded=False,
    )
    if performer_table.empty:
        st.warning("No creatives match the performer view filters.")
    else:
        bucket_order = ["Top Performer", "Potential Performer", "Low Performer", "Still Learning (Low Spend)"]
        cols = st.columns(4)
        for idx, bucket in enumerate(bucket_order):
            subset = performer_table[performer_table["Performance Bucket"] == bucket] if "Performance Bucket" in performer_table.columns else pd.DataFrame()
            cols[idx].metric(bucket.replace(" (Low Spend)", ""), len(subset))

        for bucket in bucket_order:
            subset = performer_table[performer_table["Performance Bucket"] == bucket] if "Performance Bucket" in performer_table.columns else pd.DataFrame()
            if subset.empty:
                continue
            with st.expander(f"{bucket} ({len(subset)})", expanded=bucket in {"Top Performer", "Potential Performer"}):
                sort_by = "Amount Spent" if bucket == "Still Learning (Low Spend)" else "ROAS"
                subset = _sort_dataframe(subset, sort_by, descending=bucket != "Low Performer")
                st.dataframe(
                    _numeric_display(subset.drop(columns=["_Row Key"], errors="ignore")),
                    use_container_width=True,
                    hide_index=True,
                    height=320,
                    column_config={"Drive Link": st.column_config.LinkColumn("Drive Link", display_text="Open")},
                )

with tab_quality:
    st.subheader("Quality and taxonomy coverage")
    inhouse = filtered[filtered["Source"] == "Inhouse"].copy()
    if inhouse.empty:
        st.info("No in-house creatives in this filter window.")
    else:
        required = ["Marketing Angle", "Belief", "Cohort", "Funnel Stage", "Content Hook Type", "Drive Link"]
        coverage = []
        for field in required:
            if field in inhouse.columns:
                coverage.append({
                    "Field": field,
                    "Filled": int(inhouse[field].astype(str).str.strip().ne("").sum()),
                    "Total": len(inhouse),
                    "Coverage": round(inhouse[field].astype(str).str.strip().ne("").mean() * 100, 1),
                })
        st.dataframe(pd.DataFrame(coverage), use_container_width=True, hide_index=True)

        left, right = st.columns(2)
        with left:
            angle_counts = inhouse["Marketing Angle"].replace("", pd.NA).dropna().value_counts().head(12).reset_index()
            angle_counts.columns = ["Marketing Angle", "Creatives"]
            st.markdown("**Top in-house marketing angles**")
            st.dataframe(angle_counts, use_container_width=True, hide_index=True)
        with right:
            cohort_counts = inhouse["Cohort"].replace("", pd.NA).dropna().value_counts().head(12).reset_index()
            cohort_counts.columns = ["Cohort", "Creatives"]
            st.markdown("**Top in-house cohorts**")
            st.dataframe(cohort_counts, use_container_width=True, hide_index=True)

    needs = filtered[filtered["Source"] == "Needs Logging"].copy()
    if not needs.empty:
        st.warning(f"{len(needs)} likely in-house rows are live in Meta Ads but missing from Master_Asset_Registry.")
        needs_table = _with_live_date(needs[["AD CODE", "_Date", "Creative Name", "Product", "Format", "Drive Link", "Needs Attention"]])
        needs_table = _table_controls(
            needs_table,
            key="quality_needs_logging",
            search_columns=["AD CODE", "Creative Name", "Product", "Format", "Drive Link", "Needs Attention"],
            filter_columns=["Product", "Format"],
            default_sort="Live Date",
        )
        st.dataframe(
            needs_table,
            use_container_width=True,
            hide_index=True,
            column_config={"Drive Link": st.column_config.LinkColumn("Drive Link", display_text="Open")},
        )

    if not inhouse.empty:
        st.markdown("---")
        st.markdown("**In-house taxonomy table**")
        taxonomy_cols = [
            "_Date", "AD CODE", "Creative Name", "Product", "Format", "Creative Type",
            "Marketing Angle", "Belief", "Cohort", "Situational Driver", "Funnel Stage",
            "Visual Hook Type", "Content Hook Type", "Static Message Type", "CTA Message Type",
            "Performance Bucket", "Post-CRAN", "Post-CRAN Parent AD CODE", *PERFORMANCE_COLUMN_ORDER, "Drive Link",
        ]
        taxonomy_table = _with_live_date(inhouse[[c for c in taxonomy_cols if c in inhouse.columns]])
        taxonomy_table = _table_controls(
            taxonomy_table,
            key="quality_taxonomy_table",
            search_columns=[
                "AD CODE", "Creative Name", "Product", "Format", "Creative Type",
                "Marketing Angle", "Belief", "Cohort", "Situational Driver", "Funnel Stage",
                "Visual Hook Type", "Content Hook Type", "Static Message Type", "CTA Message Type", "Drive Link",
            ],
            filter_columns=["Product", "Format", "Marketing Angle", "Belief", "Cohort", "Funnel Stage", "Content Hook Type", "Static Message Type"],
            default_sort="Live Date",
        )
        st.dataframe(
            _numeric_display(taxonomy_table),
            use_container_width=True,
            hide_index=True,
            height=420,
            column_config={"Drive Link": st.column_config.LinkColumn("Drive Link", display_text="Open")},
        )

with tab_audit:
    st.subheader("Data audit")
    st.caption("This is the boring plumbing view. Useful when counts look off.")
    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Rows before filters", len(df))
    a2.metric("Rows after filters", len(filtered))
    a3.metric("Missing date rows", int(raw["_Date"].isna().sum()) if "_Date" in raw.columns else 0)
    a4.metric("Needs logging rows", int((df["Source"] == "Needs Logging").sum()))

    audit_cols = [
        "Source", "Record Type", "AD CODE", "Perf AD Code", "_Date", "Creative Name", "Product",
        "Format", "Asset ID", "Creator", "Marketing Angle", "Content Hook Type",
        "Performance Bucket", "Post-CRAN", "Post-CRAN Parent AD CODE", *PERFORMANCE_COLUMN_ORDER,
        "Needs Attention", "Drive Link", "Instagram / Live Link",
    ]
    audit = _with_live_date(filtered[[c for c in audit_cols if c in filtered.columns]])
    audit = _table_controls(
        audit,
        key="dashboard_data_audit",
        search_columns=[
            "Source", "Record Type", "AD CODE", "Perf AD Code", "Creative Name", "Product",
            "Format", "Asset ID", "Creator", "Marketing Angle", "Content Hook Type", "Static Message Type",
            "Needs Attention", "Drive Link", "Instagram / Live Link",
        ],
        filter_columns=["Source", "Record Type", "Product", "Format", "Marketing Angle", "Content Hook Type", "Static Message Type"],
        default_sort="Live Date",
        expanded=True,
    )
    st.dataframe(
        _numeric_display(audit),
        use_container_width=True,
        hide_index=True,
        height=520,
        column_config={
            "Drive Link": st.column_config.LinkColumn("Drive Link", display_text="Open"),
            "Instagram / Live Link": st.column_config.LinkColumn("Instagram", display_text="Open"),
        },
    )
