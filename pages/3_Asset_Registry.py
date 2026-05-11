import re

import pandas as pd
import streamlit as st

from utils.sheets import (
    PERFORMANCE_COLUMNS,
    load_assets,
    load_performance_import,
    normalize_ad_code,
    parse_mixed_dates,
    refresh_sheet_cache,
)
from utils.taxonomy import FORMATS, PRODUCTS


st.set_page_config(page_title="Asset Registry - Creative OS", layout="wide")
st.title("Asset Registry")
st.caption("Primary in-house creative library from Master_Asset_Registry.")

refresh_col, source_col = st.columns([0.2, 0.8])
with refresh_col:
    if st.button("Refresh sheet data", type="primary", use_container_width=True):
        refresh_sheet_cache()
        st.rerun()
with source_col:
    performance_df = load_performance_import()
    if performance_df.empty:
        st.caption("Performance source: Master metric columns only. Add `Performance_Import` for fresh SyncWith metrics.")
    else:
        st.caption(f"Performance source: `{performance_df['Performance Sheet'].iloc[0]}` via AD CODE.")

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.25rem; max-width: 1400px; }
    div[data-testid="metric-container"] {
        background: #f5faf7;
        border: 1px solid #dbe9e0;
        border-radius: 16px;
        padding: 0.9rem;
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
    </style>
    """,
    unsafe_allow_html=True,
)


def _safe(value, fallback="-"):
    text = str(value or "").strip()
    return text if text and text.lower() not in {"nan", "nat", "none"} else fallback


def _file_id_from_drive_url(url: str) -> str:
    text = str(url or "")
    for pattern in [r"/file/d/([a-zA-Z0-9_-]+)", r"[?&]id=([a-zA-Z0-9_-]+)"]:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return ""


def _thumb(row: pd.Series) -> str:
    for column in ["Thumbnail Link", "Preview Asset Link", "Drive Link"]:
        value = str(row.get(column, "") or "").strip()
        if not value:
            continue
        if value.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            return value
        file_id = _file_id_from_drive_url(value)
        if file_id:
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w900"
    return ""


NUMERIC_SORT_COLUMNS = {
    "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach", "CTR", "CPC",
    "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
    "ROAS (L7)", "Amount Spent (L7)", "Revenue (L7)", "Avg Cost Per Reach (L7)",
    "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)",
    "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
}


def _row_key(row: pd.Series) -> str:
    return "|".join(
        str(row.get(field, ""))
        for field in ["Asset ID", "Meta Ad ID", "Creator / Consumer Name", "Product", "Published Date"]
    )


def _number(value):
    text = str(value or "").strip()
    if not text or text.lower() in {"nan", "nat", "none", "#div/0!"}:
        return pd.NA
    cleaned = re.sub(r"[₹,%\s]", "", text.replace(",", ""))
    cleaned = re.sub(r"[^0-9.\-]", "", cleaned)
    if cleaned in {"", ".", "-", "-."}:
        return pd.NA
    return pd.to_numeric(cleaned, errors="coerce")


def _sort_dataframe(data: pd.DataFrame, sort_by: str, descending: bool) -> pd.DataFrame:
    if data.empty or sort_by not in data.columns:
        return data
    sortable = data.copy()
    if sort_by in NUMERIC_SORT_COLUMNS:
        sortable["_sort_key"] = sortable[sort_by].map(_number)
    elif sort_by in {"Published Date", "Created Date"}:
        sortable["_sort_key"] = pd.to_datetime(sortable[sort_by], errors="coerce", dayfirst=True)
    else:
        sortable["_sort_key"] = sortable[sort_by].astype(str).str.lower()
    return sortable.sort_values("_sort_key", ascending=not descending, na_position="last").drop(columns="_sort_key")


def _table_controls(data: pd.DataFrame, key: str) -> pd.DataFrame:
    if data.empty:
        return data
    working = data.copy()
    with st.expander("Search, filter, and sort this table", expanded=False):
        search_value = st.text_input("Search table", key=f"{key}_search", placeholder="name, AD CODE, asset ID, angle, consumer...")
        if search_value.strip():
            term = search_value.strip().lower()
            search_cols = [
                "Asset ID", "Meta Ad ID", "Creator / Consumer Name", "Marketing Angle", "Belief",
                "Cohort", "Visual Hook Type", "Content Hook Type", "Static Message Type",
                "CTA Message Type", "Notes", "Drive Link", "Transcript Link", "Experiment ID", "Source Interview ID",
                "Product", "Format", "Creative Type", "Status",
            ]
            mask = pd.Series(False, index=working.index)
            for column in [c for c in search_cols if c in working.columns]:
                mask = mask | working[column].astype(str).str.lower().str.contains(term, na=False)
            working = working[mask]

        filter_cols = st.columns(3)
        for idx, column in enumerate([c for c in ["Product", "Format", "Status", "Marketing Angle", "Cohort", "Content Hook Type", "Static Message Type", "Creative Type"] if c in working.columns]):
            options = sorted(v for v in working[column].dropna().astype(str).unique() if v.strip())
            if not options:
                continue
            selected = filter_cols[idx % 3].multiselect(column, options, key=f"{key}_filter_{column}", placeholder=f"All {column}")
            if selected:
                working = working[working[column].astype(str).isin(selected)]

        sort_options = [c for c in working.columns if not str(c).startswith("_")]
        fallback = "Published Date" if "Published Date" in sort_options else (sort_options[0] if sort_options else "")
        if sort_options:
            s1, s2 = st.columns([0.7, 0.3])
            sort_by = s1.selectbox("Sort by", sort_options, index=sort_options.index(fallback), key=f"{key}_sort_by")
            descending = s2.toggle("Descending", value=True, key=f"{key}_sort_desc")
            working = _sort_dataframe(working, sort_by, descending)
    return working


def _numeric_display(data: pd.DataFrame) -> pd.DataFrame:
    output = data.copy()
    for column in [c for c in output.columns if c in NUMERIC_SORT_COLUMNS]:
        output[column] = output[column].map(_number).astype("Float64")
    return output


assets = load_assets()
if assets.empty:
    st.info("No in-house assets are logged in Master_Asset_Registry yet.")
    st.stop()

df = assets.copy()
df["Meta Ad ID"] = df["Meta Ad ID"].map(normalize_ad_code) if "Meta Ad ID" in df.columns else ""
if not performance_df.empty and "AD CODE" in performance_df.columns:
    perf = performance_df.copy()
    perf["AD CODE"] = perf["AD CODE"].map(normalize_ad_code)
    perf = perf.drop_duplicates(subset=["AD CODE"], keep="last").set_index("AD CODE")
    for idx, row in df.iterrows():
        code = normalize_ad_code(row.get("Meta Ad ID", ""))
        if not code or code not in perf.index:
            continue
        perf_row = perf.loc[code]
        touched = False
        for metric in PERFORMANCE_COLUMNS:
            if metric in perf_row.index and str(perf_row.get(metric, "")).strip():
                df.at[idx, metric] = perf_row.get(metric)
                touched = True
        if touched:
            df.at[idx, "Metric Source"] = f"{perf_row.get('Performance Sheet', 'Performance_Import')} via AD CODE"
df["_Published Date"] = parse_mixed_dates(df["Published Date"]) if "Published Date" in df.columns else pd.NaT
if "Format" not in df.columns:
    df["Format"] = ""
if "Creative Type" in df.columns:
    missing = df["Format"].astype(str).str.strip() == ""
    df.loc[missing, "Format"] = df.loc[missing, "Creative Type"].map(
        lambda value: "Video" if str(value).lower() in {"consumer testimonial", "brand-led", "founder-led", "skit", "event coverage", "ai-video"} else "Static"
    )

with st.sidebar:
    st.header("Find Creatives")
    search = st.text_input(
        "Simple search",
        placeholder="consumer name, AD CODE, product, angle...",
        help="Searches asset ID, AD CODE, consumer/creator, product, format, taxonomy, links, notes, and post-CRAN fields.",
    )

    st.header("Filters")
    product_options = sorted(v for v in df["Product"].dropna().astype(str).unique() if v.strip()) or PRODUCTS
    selected_products = st.multiselect("Product", product_options, default=product_options)
    format_options = sorted(v for v in df["Format"].dropna().astype(str).unique() if v.strip()) or FORMATS
    selected_formats = st.multiselect("Format", format_options, default=format_options)
    status_options = sorted(v for v in df["Status"].dropna().astype(str).unique() if v.strip()) if "Status" in df.columns else []
    selected_status = st.multiselect("Status", status_options, default=status_options)

filtered = df.copy()
if selected_products and "Product" in filtered.columns:
    filtered = filtered[filtered["Product"].isin(selected_products)]
if selected_formats and "Format" in filtered.columns:
    filtered = filtered[filtered["Format"].isin(selected_formats) | filtered["Format"].astype(str).str.strip().eq("")]
if selected_status and "Status" in filtered.columns:
    filtered = filtered[filtered["Status"].isin(selected_status)]
if search.strip():
    term = search.strip().lower()
    cols = [
        "Asset ID", "Meta Ad ID", "Creator / Consumer Name", "Marketing Angle",
        "Belief", "Cohort", "Visual Hook Type", "Content Hook Type", "Static Message Type",
        "CTA Message Type", "Notes", "Drive Link", "Transcript Link", "Experiment ID", "Source Interview ID",
        "Product", "Format", "Creative Type", "Static Subtype", "Video Subtype", "Status",
        "Taxonomy Review Status", "Post-CRAN Parent AD CODE", "Post-CRAN Change Summary",
    ]
    mask = pd.Series(False, index=filtered.index)
    for col in [c for c in cols if c in filtered.columns]:
        mask = mask | filtered[col].astype(str).str.lower().str.contains(term, na=False)
    filtered = filtered[mask]

if filtered.empty:
    st.warning("No assets match these filters.")
    st.stop()

filtered["_Preview"] = filtered.apply(_thumb, axis=1)
filtered["_Row Key"] = filtered.apply(_row_key, axis=1)

m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("Assets", len(filtered))
m2.metric("Videos", int((filtered["Format"] == "Video").sum()) if "Format" in filtered.columns else 0)
m3.metric("Statics", int((filtered["Format"] == "Static").sum()) if "Format" in filtered.columns else 0)
m4.metric("With AD CODE", int(filtered["Meta Ad ID"].astype(str).str.contains("AD ", na=False).sum()))
m5.metric("Unique angles", int(filtered["Marketing Angle"].replace("", pd.NA).dropna().nunique()) if "Marketing Angle" in filtered.columns else 0)

st.markdown("---")

left, right = st.columns([0.95, 1.35])

with left:
    st.subheader("In-house assets")
    table_cols = [
        "_Preview", "Asset ID", "Meta Ad ID", "Published Date", "Product", "Format", "Creative Type",
        "Creator / Consumer Name", "Marketing Angle", "Cohort", "Content Hook Type", "ROAS", "Amount Spent", "Revenue",
        "CTR", "Taxonomy Review Status", "Is Post-CRAN", "Post-CRAN Parent AD CODE", "Drive Link", "Transcript Link", "_Row Key",
    ]
    table = filtered[[c for c in table_cols if c in filtered.columns]].copy()
    table = _table_controls(table, key="asset_registry")
    if table.empty:
        st.warning("No rows match the table search/filters.")
        st.stop()

    table = table.rename(columns={"_Preview": "Preview"})
    table_display = _numeric_display(table.drop(columns=["_Row Key"], errors="ignore"))
    table_event = st.dataframe(
        table_display,
        use_container_width=True,
        hide_index=True,
        height=520,
        on_select="rerun",
        selection_mode="single-row",
        key="asset_registry_table",
        column_config={
            "Preview": st.column_config.ImageColumn("Preview", width="small"),
            "Drive Link": st.column_config.LinkColumn("Drive Link", display_text="Open"),
            "Transcript Link": st.column_config.LinkColumn("Transcript", display_text="Open"),
        },
    )
    if table_event.selection.rows:
        selected_pos = table_event.selection.rows[0]
        st.session_state["asset_registry_selected_row_key"] = str(table.iloc[selected_pos]["_Row Key"])
    elif "asset_registry_selected_row_key" not in st.session_state:
        st.session_state["asset_registry_selected_row_key"] = str(table.iloc[0]["_Row Key"])

    csv = filtered.drop(columns=["_Published Date", "_Preview", "_Row Key"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", data=csv, file_name="master_asset_registry_filtered.csv", mime="text/csv")

with right:
    st.subheader("Creative detail")
    st.caption("Select a row in the table to open its full asset view here.")
    table_keys = set(table["_Row Key"].astype(str)) if "table" in locals() and "_Row Key" in table.columns else set()
    selected_key = st.session_state.get("asset_registry_selected_row_key")
    if selected_key not in table_keys and table_keys:
        selected_key = str(table.iloc[0]["_Row Key"])
        st.session_state["asset_registry_selected_row_key"] = selected_key
    row = filtered[filtered["_Row Key"].astype(str) == selected_key].iloc[0]

    preview = _thumb(row)
    if preview:
        st.image(preview, use_container_width=True)
    else:
        st.info("No preview available yet. Add a Preview Asset Link, Thumbnail Link, or Drive file link.")

    st.markdown(f"### {_safe(row.get('Asset ID'))}")
    st.markdown(
        f"<span class='pill'>{_safe(row.get('Product'))}</span>"
        f"<span class='pill'>{_safe(row.get('Format'))}</span>"
        f"<span class='pill'>{_safe(row.get('Creative Type'))}</span>",
        unsafe_allow_html=True,
    )
    st.write(f"**AD CODE:** {_safe(row.get('Meta Ad ID'))}")
    st.write(f"**Published:** {_safe(row.get('Published Date'))}")

    link_cols = [
        ("Open creative", "Drive Link"),
        ("Open preview", "Preview Asset Link"),
        ("Open source folder", "Source Folder Link"),
        ("Open transcript", "Transcript Link"),
        ("Open brief", "Brief Link"),
    ]
    links = [f"[{label}]({row.get(col)})" for label, col in link_cols if _safe(row.get(col), "")]
    if links:
        st.markdown(" | ".join(links))

    tab_identity, tab_taxonomy, tab_perf = st.tabs(["Identity", "Taxonomy", "Performance"])
    with tab_identity:
        fields = [
            "Status", "Channel", "Bucket", "Parent Asset ID", "Variant #", "What's Different",
            "A/B Pair ID", "Creator / Consumer Name", "Source Interview ID", "Experiment ID",
            "Campaign Name", "Ad Set Name", "Is Post-CRAN", "Post-CRAN Parent AD CODE",
            "Post-CRAN Parent Asset ID", "Post-CRAN Change Summary", "Notes",
        ]
        for field in fields:
            if field in row.index:
                st.write(f"**{field}:** {_safe(row.get(field))}")

    with tab_taxonomy:
        fields = [
            "Marketing Angle", "Belief", "Cohort", "Situational Driver", "Funnel Stage",
            "Visual Hook Type", "Content Hook Type", "Emotional Arc", "Creator Archetype", "Influence Mode",
            "Visual Treatment", "Static Message Type", "CTA Format", "CTA Message Type",
            "AI-Generated", "Taxonomy Confidence", "Claim Codes",
            "Visual Style", "CTA Style", "Hook Type", "Video Subtype", "Static Subtype",
            "Transcript Notes", "Aspect Ratio Links", "Taxonomy Review Status",
        ]
        for field in fields:
            if field in row.index:
                st.write(f"**{field}:** {_safe(row.get(field))}")

    with tab_perf:
        st.caption(f"Metric source: {_safe(row.get('Metric Source'), 'Master_Asset_Registry metric columns')}. These values are read from sheets, not calculated by the app.")
        perf_cols = [
            "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach", "CTR", "CPC",
            "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
            "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "CTR (L30)",
            "Hook Rate (L30)", "Hold Rate (L30)", "ROAS (L7)", "Amount Spent (L7)",
            "Revenue (L7)", "CTR (L7)", "Hook Rate (L7)", "Hold Rate (L7)",
        ]
        perf = pd.DataFrame(
            [{"Metric": col, "Value": row.get(col, "")} for col in perf_cols if col in row.index and _safe(row.get(col), "")]
        )
        if perf.empty:
            st.info("No performance metrics populated yet.")
        else:
            st.dataframe(perf, use_container_width=True, hide_index=True)
