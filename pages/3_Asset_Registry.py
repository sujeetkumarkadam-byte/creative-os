import re

import pandas as pd
import streamlit as st

from utils.sheets import load_assets, normalize_ad_code, parse_mixed_dates
from utils.taxonomy import FORMATS, PRODUCTS


st.set_page_config(page_title="Asset Registry - Creative OS", layout="wide")
st.title("Asset Registry")
st.caption("Primary in-house creative library from Master_Asset_Registry.")

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


assets = load_assets()
if assets.empty:
    st.info("No in-house assets are logged in Master_Asset_Registry yet.")
    st.stop()

df = assets.copy()
df["Meta Ad ID"] = df["Meta Ad ID"].map(normalize_ad_code) if "Meta Ad ID" in df.columns else ""
df["_Published Date"] = parse_mixed_dates(df["Published Date"]) if "Published Date" in df.columns else pd.NaT
if "Format" not in df.columns:
    df["Format"] = ""
if "Creative Type" in df.columns:
    missing = df["Format"].astype(str).str.strip() == ""
    df.loc[missing, "Format"] = df.loc[missing, "Creative Type"].map(
        lambda value: "Video" if str(value).lower() in {"consumer testimonial", "brand-led", "founder-led", "skit", "event coverage", "ai-video"} else "Static"
    )

with st.sidebar:
    st.header("Filters")
    product_options = sorted(v for v in df["Product"].dropna().astype(str).unique() if v.strip()) or PRODUCTS
    selected_products = st.multiselect("Product", product_options, default=product_options)
    format_options = sorted(v for v in df["Format"].dropna().astype(str).unique() if v.strip()) or FORMATS
    selected_formats = st.multiselect("Format", format_options, default=format_options)
    status_options = sorted(v for v in df["Status"].dropna().astype(str).unique() if v.strip()) if "Status" in df.columns else []
    selected_status = st.multiselect("Status", status_options, default=status_options)
    search = st.text_input("Search", placeholder="asset, AD CODE, creator, angle...")

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
        "Belief", "Cohort", "Notes", "Drive Link", "Experiment ID", "Source Interview ID",
    ]
    mask = pd.Series(False, index=filtered.index)
    for col in [c for c in cols if c in filtered.columns]:
        mask = mask | filtered[col].astype(str).str.lower().str.contains(term, na=False)
    filtered = filtered[mask]

if filtered.empty:
    st.warning("No assets match these filters.")
    st.stop()

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
        "Asset ID", "Meta Ad ID", "Published Date", "Product", "Format", "Creative Type",
        "Creator / Consumer Name", "Marketing Angle", "Cohort", "ROAS", "CTR", "Drive Link",
    ]
    table = filtered[[c for c in table_cols if c in filtered.columns]].copy()
    if "_Published Date" in filtered.columns:
        table["_sort"] = filtered["_Published Date"]
        table = table.sort_values("_sort", ascending=False).drop(columns="_sort")
    st.dataframe(table, use_container_width=True, hide_index=True, height=520)

    csv = filtered.drop(columns=["_Published Date"], errors="ignore").to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", data=csv, file_name="master_asset_registry_filtered.csv", mime="text/csv")

with right:
    st.subheader("Creative detail")
    labels = filtered.apply(
        lambda row: f"{_safe(row.get('Asset ID'))} | {_safe(row.get('Meta Ad ID'))} | {_safe(row.get('Creator / Consumer Name'), _safe(row.get('Marketing Angle')))}",
        axis=1,
    ).tolist()
    selected = st.selectbox("Pick an asset", labels)
    row = filtered.iloc[labels.index(selected)]

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
            "Campaign Name", "Ad Set Name", "Notes",
        ]
        for field in fields:
            if field in row.index:
                st.write(f"**{field}:** {_safe(row.get(field))}")

    with tab_taxonomy:
        fields = [
            "Marketing Angle", "Belief", "Cohort", "Situational Driver", "Funnel Stage",
            "Hook Type", "Emotional Arc", "Creator Archetype", "Influence Mode",
            "Visual Style", "CTA Style", "Video Subtype", "Static Subtype",
            "Taxonomy Review Status",
        ]
        for field in fields:
            if field in row.index:
                st.write(f"**{field}:** {_safe(row.get(field))}")

    with tab_perf:
        st.caption("These values are read from Master_Asset_Registry metric columns. They are not calculated or invented by the app.")
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
