import streamlit as st
import pandas as pd
from utils.sheets import load_inhouse_live
from utils.taxonomy import PRODUCTS, FORMATS, VIDEO_SUBTYPES, STATIC_SUBTYPES, FUNNEL_STAGES

st.set_page_config(page_title="Asset Registry — Creative OS", layout="wide")
st.title("Inhouse Live Asset Registry")
st.caption("Every inhouse asset that went live on Meta. Filter, inspect, download.")

assets_df = load_inhouse_live()

if assets_df.empty:
    st.info("No assets logged yet.")
    st.stop()

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
st.sidebar.header("Filters")

products = st.sidebar.multiselect("Product", PRODUCTS, default=PRODUCTS)
formats  = st.sidebar.multiselect("Format", FORMATS, default=FORMATS)

search = st.sidebar.text_input("Search Asset ID, AD CODE, or Notes", placeholder="e.g. RCF-V-007 or AD 467")

df = assets_df.copy()
if "Product" in df.columns:
    df = df[df["Product"].isin(products)]
if "Format" in df.columns and formats:
    # Tolerate blank Format (legacy rows) — keep them unless user filters strictly
    df = df[df["Format"].isin(formats) | (df["Format"].astype(str).str.strip() == "")]

if search:
    search_cols = [c for c in ["Asset ID", "AD CODE", "Notes"] if c in df.columns]
    mask = False
    for c in search_cols:
        mask = mask | df[c].astype(str).str.contains(search, case=False, na=False)
    df = df[mask] if isinstance(mask, pd.Series) else df

# ── SUMMARY STRIP ─────────────────────────────────────────────────────────────
st.markdown(f"**{len(df)}** assets matching filters &nbsp;|&nbsp; "
            f"**{df['Product'].nunique()}** products &nbsp;|&nbsp; "
            f"**{df['Marketing Angle'].nunique()}** unique angles")
st.markdown("---")

# ── MAIN TABLE ────────────────────────────────────────────────────────────────
summary_cols = [
    "Asset ID", "AD CODE", "Creator / Consumer Name", "Product", "Format",
    "Video Subtype", "Static Subtype", "Bucket", "Cohort", "Marketing Angle",
    "Belief", "Hook Type", "Funnel Stage", "Influence Mode", "Creator Archetype",
    "Visual Style", "CTA Style", "Published Date",
    "ROAS", "Amount Spent", "CTR", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "ROAS (L7)", "Drive Link",
]
available = [c for c in summary_cols if c in df.columns]

st.dataframe(
    df[available].sort_values("Published Date", ascending=False),
    use_container_width=True,
    hide_index=True,
)

# ── DOWNLOAD ─────────────────────────────────────────────────────────────────
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇ Download filtered CSV",
    data=csv,
    file_name="asset_registry_export.csv",
    mime="text/csv",
)

# ── DETAIL EXPANDER ───────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Inspect a single asset")
asset_ids = df["Asset ID"].dropna().tolist()
if asset_ids:
    chosen = st.selectbox("Pick Asset ID", ["—"] + asset_ids)
    if chosen != "—":
        row = df[df["Asset ID"] == chosen].iloc[0]
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Identity**")
            for f in ["Asset ID","AD CODE","Parent Asset ID","Variant #","What's Different",
                      "A/B Pair ID","Published Date"]:
                st.write(f"**{f}:** {row.get(f,'')}")
        with c2:
            st.markdown("**Taxonomy**")
            for f in ["Product","Bucket","Format","Video Subtype","Static Subtype",
                      "Cohort","Belief","Marketing Angle","Situational Driver",
                      "Hook Type","Emotional Arc","Funnel Stage","Creator Archetype",
                      "Influence Mode","Visual Style","CTA Style"]:
                st.write(f"**{f}:** {row.get(f,'')}")
        with c3:
            st.markdown("**Publishing & Performance**")
            for f in ["Campaign Name","Ad Set Name","Drive Link","Brief Link",
                      "Reference Image Link","Experiment ID","Notes",
                      "ROAS","Amount Spent","CTR","Hook Rate","Hold Rate","CAC",
                      "ROAS (L30)","CTR (L30)","Hook Rate (L30)",
                      "ROAS (L7)","CTR (L7)","Hook Rate (L7)"]:
                st.write(f"**{f}:** {row.get(f,'')}")
