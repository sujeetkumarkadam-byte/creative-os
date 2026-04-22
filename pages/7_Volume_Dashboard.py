import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from utils.sheets import (
    load_meta_ads, load_inhouse_live, load_influencer_ads, classify_meta_ads,
)

st.set_page_config(page_title="Volume Dashboard — Creative OS", layout="wide")
st.title("Volume Dashboard")
st.caption(
    "Every ad that went live on Meta — classified as Inhouse / Influencer / Porcellia "
    "by AD CODE match. Slice by date, source, product, format, angle, cohort."
)

# ── LOAD ──────────────────────────────────────────────────────────────────────
with st.spinner("Loading Meta Ads + Inhouse + Influencer…"):
    meta = load_meta_ads()
    inhouse = load_inhouse_live()
    influencer = load_influencer_ads()

if meta.empty:
    st.error("Meta Ads sheet is empty or unreadable.")
    st.stop()

tagged = classify_meta_ads(meta, inhouse, influencer)

# Attempt to find standard columns by name (they exist in the first block of Meta Ads)
def _first_col(df, *candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

date_col = _first_col(tagged, "Date [Ad Taken Live]", "Date [Ad Taken Live] ")
prod_col = _first_col(tagged, "Product")
ctype_col = _first_col(tagged, "Creative Type")
funnel_col = _first_col(tagged, "Funnel Level")
angle_col = _first_col(tagged, "Marketing Angle")
bucket_col = _first_col(tagged, "Content Bucket")
status_col = _first_col(tagged, "Status")

# Parse dates
if date_col:
    tagged["_Date"] = pd.to_datetime(tagged[date_col], errors="coerce")
else:
    tagged["_Date"] = pd.NaT

# Enrich Inhouse rows with their taxonomy (cohort/belief/angle/format) from Inhouse_Live_Assets
if not inhouse.empty and "AD CODE" in inhouse.columns:
    inhouse_slim = inhouse[[c for c in [
        "AD CODE", "Format", "Video Subtype", "Static Subtype",
        "Cohort", "Belief", "Marketing Angle", "Situational Driver",
        "Funnel Stage", "Creator Archetype", "Product",
    ] if c in inhouse.columns]].copy()
    inhouse_slim["AD CODE"] = inhouse_slim["AD CODE"].astype(str).str.strip().str.upper()
    tagged["_code_up"] = tagged["AD CODE"].astype(str).str.strip().str.upper()
    enriched = tagged.merge(
        inhouse_slim, how="left", left_on="_code_up", right_on="AD CODE",
        suffixes=("", "_inhouse"),
    )
    tagged = enriched
else:
    tagged["Format"] = ""
    tagged["Cohort"] = ""
    tagged["Belief"] = ""

# ── SIDEBAR FILTERS ───────────────────────────────────────────────────────────
st.sidebar.header("Date range")
today = date.today()
default_start = today - timedelta(days=30)
start = st.sidebar.date_input("From", value=default_start)
end   = st.sidebar.date_input("To",   value=today)

st.sidebar.markdown("---")
sources = st.sidebar.multiselect(
    "Source", ["Inhouse", "Influencer", "Porcellia", "Unclassified"],
    default=["Inhouse", "Influencer", "Porcellia"],
)

products_all = sorted([p for p in tagged[prod_col].dropna().unique() if str(p).strip()]) if prod_col else []
products = st.sidebar.multiselect("Product", products_all, default=products_all)

formats_all = sorted([f for f in tagged.get("Format", pd.Series(dtype=str)).dropna().unique() if str(f).strip()])
formats = st.sidebar.multiselect("Format (Inhouse only)", formats_all, default=formats_all)

# ── APPLY FILTERS ─────────────────────────────────────────────────────────────
df = tagged.copy()
df = df[df["Source"].isin(sources)]
if date_col:
    mask = (df["_Date"].isna()) | ((df["_Date"] >= pd.Timestamp(start)) & (df["_Date"] <= pd.Timestamp(end)))
    df = df[mask]
if products and prod_col:
    df = df[df[prod_col].isin(products) | df[prod_col].isna() | (df[prod_col] == "")]
if formats and "Format" in df.columns:
    df = df[df["Format"].isin(formats) | (df["Format"].fillna("") == "")]

# ── HEADER METRICS ────────────────────────────────────────────────────────────
total = len(df)
n_inh = (df["Source"] == "Inhouse").sum()
n_inf = (df["Source"] == "Influencer").sum()
n_por = (df["Source"] == "Porcellia").sum()

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total ads live", total)
m2.metric("Inhouse", int(n_inh))
m3.metric("Influencer", int(n_inf))
m4.metric("Porcellia", int(n_por))

st.markdown("---")

if df.empty:
    st.warning("No rows match filters.")
    st.stop()

# ── CHART 1: BY SOURCE (pie) + BY DATE (line) ────────────────────────────────
c1, c2 = st.columns(2)

with c1:
    st.subheader("Ads by Source")
    src_counts = df["Source"].value_counts().reset_index()
    src_counts.columns = ["Source", "Count"]
    fig = px.pie(src_counts, names="Source", values="Count",
                 color="Source",
                 color_discrete_map={
                     "Inhouse": "#0F6E56", "Influencer": "#2EA882",
                     "Porcellia": "#A8D5C6", "Unclassified": "#cccccc",
                 })
    fig.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Ads over time (by Source)")
    if date_col and df["_Date"].notna().any():
        d = df.dropna(subset=["_Date"]).copy()
        d["Week"] = d["_Date"].dt.to_period("W").dt.start_time
        weekly = d.groupby(["Week", "Source"]).size().reset_index(name="Count")
        fig2 = px.line(weekly, x="Week", y="Count", color="Source", markers=True,
                       color_discrete_map={
                           "Inhouse": "#0F6E56", "Influencer": "#2EA882",
                           "Porcellia": "#A8D5C6", "Unclassified": "#cccccc",
                       })
        fig2.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No date column parsed — weekly trend unavailable.")

# ── CHART 2: BY PRODUCT + BY FORMAT (inhouse) ────────────────────────────────
c3, c4 = st.columns(2)

with c3:
    st.subheader("By Product × Source")
    if prod_col:
        pp = df.groupby([prod_col, "Source"]).size().reset_index(name="Count")
        fig3 = px.bar(pp, x=prod_col, y="Count", color="Source", barmode="group",
                      color_discrete_map={
                          "Inhouse": "#0F6E56", "Influencer": "#2EA882",
                          "Porcellia": "#A8D5C6", "Unclassified": "#cccccc",
                      })
        fig3.update_layout(margin=dict(t=20, b=20), xaxis_title="")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No Product column detected.")

with c4:
    st.subheader("Format split (Inhouse only)")
    inh_only = df[df["Source"] == "Inhouse"]
    if not inh_only.empty and "Format" in inh_only.columns:
        fc = inh_only["Format"].fillna("Untagged").replace("", "Untagged").value_counts().reset_index()
        fc.columns = ["Format", "Count"]
        fig4 = px.pie(fc, names="Format", values="Count",
                      color_discrete_sequence=px.colors.sequential.Teal)
        fig4.update_layout(margin=dict(t=20, b=20))
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("No inhouse rows (or no Format tagged) in filter.")

# ── CHART 3: ANGLE + COHORT (inhouse) ────────────────────────────────────────
c5, c6 = st.columns(2)

with c5:
    st.subheader("Top Marketing Angles (Inhouse)")
    inh = df[df["Source"] == "Inhouse"]
    angle_source_col = "Marketing Angle" if "Marketing Angle" in inh.columns else angle_col
    if not inh.empty and angle_source_col and angle_source_col in inh.columns:
        ac = inh[angle_source_col].dropna().replace("", pd.NA).dropna().value_counts().head(15).reset_index()
        ac.columns = ["Angle", "Count"]
        if not ac.empty:
            fig5 = px.bar(ac, x="Count", y="Angle", orientation="h",
                          color="Count", color_continuous_scale="Teal", text="Count")
            fig5.update_layout(yaxis={"categoryorder": "total ascending"},
                               coloraxis_showscale=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("No angles tagged yet on inhouse rows.")
    else:
        st.info("No inhouse angle data.")

with c6:
    st.subheader("Cohort distribution (Inhouse)")
    if not inh.empty and "Cohort" in inh.columns:
        cc = inh["Cohort"].dropna().replace("", pd.NA).dropna().value_counts().reset_index()
        cc.columns = ["Cohort", "Count"]
        if not cc.empty:
            fig6 = px.bar(cc, x="Count", y="Cohort", orientation="h",
                          color="Count", color_continuous_scale="Teal", text="Count")
            fig6.update_layout(yaxis={"categoryorder": "total ascending"},
                               coloraxis_showscale=False, margin=dict(t=20, b=20))
            st.plotly_chart(fig6, use_container_width=True)
        else:
            st.info("No cohorts tagged yet on inhouse rows.")
    else:
        st.info("No inhouse cohort data.")

# ── TABLE ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Raw classified ads")
display_cols = [c for c in [
    "Source", "AD CODE", date_col, "Creative Name", ctype_col, prod_col,
    funnel_col, bucket_col, angle_col, "Format", "Cohort", "Belief",
    "FB Ad Name", "Status", "Media Buyer Name",
] if c and c in df.columns]
# Dedupe
seen = set(); display_cols = [c for c in display_cols if not (c in seen or seen.add(c))]
st.dataframe(df[display_cols].sort_values("_Date", ascending=False) if "_Date" in df.columns else df[display_cols],
             use_container_width=True, hide_index=True)

csv = df[display_cols].to_csv(index=False).encode("utf-8")
st.download_button("⬇ Download filtered CSV", data=csv,
                   file_name="volume_dashboard.csv", mime="text/csv")
