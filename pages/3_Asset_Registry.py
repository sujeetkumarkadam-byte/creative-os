import pandas as pd
import streamlit as st

from utils.sheets import load_inhouse_live, normalize_ad_code, parse_mixed_dates
from utils.taxonomy import FORMATS, PRODUCTS

st.set_page_config(page_title="Asset Registry — Creative OS", layout="wide")
st.title("Inhouse Live Asset Registry")
st.caption("Every inhouse creative that has gone live on Meta, with taxonomy, links, and performance in one place.")

assets_df = load_inhouse_live()
if assets_df.empty:
    st.info("No inhouse live assets are logged yet.")
    st.stop()

assets_df = assets_df.copy()
if "AD CODE" in assets_df.columns:
    assets_df["AD CODE"] = assets_df["AD CODE"].map(normalize_ad_code)
if "Published Date" in assets_df.columns:
    assets_df["_Published Date"] = parse_mixed_dates(assets_df["Published Date"])

st.sidebar.header("Filters")
selected_products = st.sidebar.multiselect("Product", PRODUCTS, default=PRODUCTS)
selected_formats = st.sidebar.multiselect("Format", FORMATS, default=FORMATS)
search = st.sidebar.text_input(
    "Search",
    placeholder="Asset ID, AD CODE, creator, notes, angle...",
)

df = assets_df.copy()
if "Product" in df.columns:
    df = df[df["Product"].isin(selected_products)]
if "Format" in df.columns:
    df = df[df["Format"].isin(selected_formats) | (df["Format"].astype(str).str.strip() == "")]

if search.strip():
    search_term = search.strip().lower()
    search_cols = [
        column for column in [
            "Asset ID", "AD CODE", "Creator / Consumer Name", "Notes",
            "Marketing Angle", "Belief", "Cohort",
        ] if column in df.columns
    ]
    mask = pd.Series(False, index=df.index)
    for column in search_cols:
        mask = mask | df[column].astype(str).str.lower().str.contains(search_term, na=False)
    df = df[mask]

metrics = st.columns(4)
metrics[0].metric("Assets", len(df))
metrics[1].metric(
    "Videos",
    int((df["Format"] == "Video").sum()) if "Format" in df.columns else 0,
)
metrics[2].metric(
    "Statics",
    int((df["Format"] == "Static").sum()) if "Format" in df.columns else 0,
)
metrics[3].metric(
    "Unique angles",
    int(df["Marketing Angle"].replace("", pd.NA).dropna().nunique()) if "Marketing Angle" in df.columns else 0,
)

st.markdown("---")
st.subheader("Registry")

table_cols = [
    "Asset ID", "AD CODE", "Published Date", "Product", "Format",
    "Video Subtype", "Static Subtype", "Creator / Consumer Name",
    "Marketing Angle", "Belief", "Cohort", "Funnel Stage",
    "ROAS", "CTR", "Hook Rate", "Hold Rate", "CAC",
]
available = [column for column in table_cols if column in df.columns]

table = df[available].copy()
if "_Published Date" in df.columns:
    table["_sort"] = df["_Published Date"]
    table = table.sort_values("_sort", ascending=False).drop(columns="_sort")

st.dataframe(table, use_container_width=True, hide_index=True, height=380)

csv = df.drop(columns=["_Published Date"], errors="ignore").to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇ Download filtered CSV",
    data=csv,
    file_name="inhouse_live_asset_registry.csv",
    mime="text/csv",
)

st.markdown("---")
st.subheader("Asset Inspector")

asset_ids = df["Asset ID"].dropna().astype(str).tolist() if "Asset ID" in df.columns else []
if not asset_ids:
    st.info("No Asset IDs available in this filtered view.")
    st.stop()

selected_asset = st.selectbox("Pick an asset", asset_ids)
row = df[df["Asset ID"].astype(str) == selected_asset].iloc[0]

hero_left, hero_right = st.columns([2, 1])
with hero_left:
    st.markdown(f"### {row.get('Asset ID', '')}")
    st.caption(
        f"{row.get('Product', '—')} • {row.get('Format', '—')} • "
        f"{row.get('Video Subtype', '') or row.get('Static Subtype', '') or 'Subtype not tagged'}"
    )
with hero_right:
    st.metric("AD CODE", row.get("AD CODE", "—"))

section1, section2 = st.columns(2)
with section1:
    st.markdown("**Identity & publishing**")
    for field in [
        "Published Date", "Parent Asset ID", "Variant #", "What's Different",
        "A/B Pair ID", "Campaign Name", "Ad Set Name",
    ]:
        if field in row.index:
            st.write(f"**{field}:** {row.get(field, '') or '—'}")

    if row.get("Drive Link", ""):
        st.markdown(f"**Drive Link:** [Open asset]({row['Drive Link']})")
    else:
        st.write("**Drive Link:** —")

    if row.get("Reference Image Link", ""):
        st.markdown(f"**Reference Image:** [Open reference]({row['Reference Image Link']})")
    else:
        st.write("**Reference Image:** —")

with section2:
    st.markdown("**Taxonomy & provenance**")
    for field in [
        "Bucket", "Marketing Angle", "Belief", "Cohort", "Situational Driver",
        "Funnel Stage", "Influence Mode", "CTA Style", "Hook Type",
        "Emotional Arc", "Creator Archetype", "Visual Style",
        "Creator / Consumer Name", "Source Interview ID", "Experiment ID",
    ]:
        if field in row.index:
            st.write(f"**{field}:** {row.get(field, '') or '—'}")

st.markdown("---")

perf_left, perf_mid, perf_right = st.columns(3)

with perf_left:
    st.markdown("**All-time performance**")
    for field in ["ROAS", "Amount Spent", "Revenue", "CTR", "CPC", "ATC Rate", "CVR", "AOV", "CAC"]:
        if field in row.index:
            st.write(f"**{field}:** {row.get(field, '') or '—'}")

with perf_mid:
    st.markdown("**Creative performance**")
    for field in ["Hook Rate", "Hold Rate", "ROAS (L30)", "CTR (L30)", "Hook Rate (L30)", "Hold Rate (L30)"]:
        if field in row.index:
            st.write(f"**{field}:** {row.get(field, '') or '—'}")

with perf_right:
    st.markdown("**Recent windows & notes**")
    for field in ["ROAS (L7)", "CTR (L7)", "Hook Rate (L7)", "Hold Rate (L7)", "Brief Link", "Notes"]:
        if field in row.index:
            value = row.get(field, "") or "—"
            if field == "Brief Link" and value != "—":
                st.markdown(f"**Brief Link:** [Open brief]({value})")
            else:
                st.write(f"**{field}:** {value}")
