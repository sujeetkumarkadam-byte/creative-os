import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from utils.sheets import load_assets
from utils.taxonomy import PRODUCTS, CREATIVE_TYPES, BELIEFS, FUNNEL_STAGES

st.set_page_config(page_title="Weekly Dashboard — Creative OS", layout="wide")
st.title("Weekly Dashboard")
st.caption("Monday meeting view. Volume shipped last week by product, type, belief, cohort.")

assets_df = load_assets()

if assets_df.empty:
    st.info("No assets logged yet. Head to Log Asset to add your first creative.")
    st.stop()

# ── DATE FILTER ───────────────────────────────────────────────────────────────
today = date.today()
last_monday = today - timedelta(days=today.weekday() + 7)
last_sunday  = last_monday + timedelta(days=6)

st.sidebar.header("Date range")
start = st.sidebar.date_input("From", value=last_monday)
end   = st.sidebar.date_input("To",   value=last_sunday)

assets_df["Published Date"] = pd.to_datetime(assets_df["Published Date"], errors="coerce")
start_ts = pd.Timestamp(start)
end_ts   = pd.Timestamp(end)
mask = (
    (assets_df["Published Date"] >= start_ts) &
    (assets_df["Published Date"] <= end_ts)
)
df = assets_df[mask].copy()

st.sidebar.markdown("---")
prod_filter = st.sidebar.multiselect("Product", PRODUCTS, default=PRODUCTS)
df = df[df["Product"].isin(prod_filter)]

# ── HEADER METRICS ────────────────────────────────────────────────────────────
total   = len(df)
videos  = df["Creative Type"].isin({"Consumer Testimonial","Brand-Led","Founder-Led","Skit","Event Coverage","AI-Video"}).sum()
statics = total - videos

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Assets", total)
m2.metric("Videos", int(videos))
m3.metric("Statics", int(statics))

if total > 0:
    unique_angles  = df["Marketing Angle"].nunique()
    unique_cohorts = df["Cohort"].nunique()
    raw_score = round((unique_angles / max(df["Marketing Angle"].count(), 1) * 50) +
                      (unique_cohorts / max(df["Cohort"].count(), 1) * 50))
    m4.metric("Diversity Score", f"{raw_score}/100",
              help="Blend of unique angles + cohorts covered this week (0–100).")
else:
    m4.metric("Diversity Score", "—")

st.markdown("---")

if df.empty:
    st.warning(f"No assets logged between {start} and {end}.")
    st.stop()

# ── CHARTS ────────────────────────────────────────────────────────────────────
row1_l, row1_r = st.columns(2)

with row1_l:
    st.subheader("By Product")
    prod_counts = df["Product"].value_counts().reset_index()
    prod_counts.columns = ["Product", "Count"]
    fig = px.bar(prod_counts, x="Product", y="Count", color="Product",
                 color_discrete_sequence=["#0F6E56","#2EA882","#A8D5C6"],
                 text="Count")
    fig.update_layout(showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

with row1_r:
    st.subheader("By Creative Type")
    type_counts = df["Creative Type"].value_counts().reset_index()
    type_counts.columns = ["Creative Type", "Count"]
    fig2 = px.pie(type_counts, names="Creative Type", values="Count",
                  color_discrete_sequence=px.colors.sequential.Teal)
    fig2.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig2, use_container_width=True)

row2_l, row2_r = st.columns(2)

with row2_l:
    st.subheader("By Marketing Angle")
    angle_counts = df["Marketing Angle"].value_counts().reset_index()
    angle_counts.columns = ["Angle", "Count"]
    fig3 = px.bar(angle_counts, x="Count", y="Angle", orientation="h",
                  color="Count", color_continuous_scale="Teal", text="Count")
    fig3.update_layout(yaxis={"categoryorder": "total ascending"},
                       coloraxis_showscale=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig3, use_container_width=True)

with row2_r:
    st.subheader("By Cohort")
    cohort_counts = df["Cohort"].value_counts().reset_index()
    cohort_counts.columns = ["Cohort", "Count"]
    fig4 = px.bar(cohort_counts, x="Count", y="Cohort", orientation="h",
                  color="Count", color_continuous_scale="Teal", text="Count")
    fig4.update_layout(yaxis={"categoryorder": "total ascending"},
                       coloraxis_showscale=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig4, use_container_width=True)

row3_l, row3_r = st.columns(2)

with row3_l:
    st.subheader("By Belief")
    belief_counts = df["Belief"].value_counts().reset_index()
    belief_counts.columns = ["Belief", "Count"]
    fig5 = px.bar(belief_counts, x="Belief", y="Count", color="Belief",
                  color_discrete_sequence=px.colors.sequential.Teal_r, text="Count")
    fig5.update_layout(showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig5, use_container_width=True)

with row3_r:
    st.subheader("By Funnel Stage")
    funnel_counts = df["Funnel Stage"].value_counts().reset_index()
    funnel_counts.columns = ["Stage", "Count"]
    order = [s for s in FUNNEL_STAGES if s in funnel_counts["Stage"].values]
    funnel_counts["Stage"] = pd.Categorical(funnel_counts["Stage"], categories=order, ordered=True)
    funnel_counts = funnel_counts.sort_values("Stage")
    fig6 = px.bar(funnel_counts, x="Stage", y="Count",
                  color_discrete_sequence=["#0F6E56"], text="Count")
    fig6.update_layout(margin=dict(t=20, b=20))
    st.plotly_chart(fig6, use_container_width=True)

# ── ASSET TABLE ───────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Assets this period")
display_cols = [
    "Asset ID", "Creator / Consumer Name", "Product", "Creative Type", "Cohort",
    "Marketing Angle", "Belief", "Funnel Stage", "Status", "Published Date",
]
available = [c for c in display_cols if c in df.columns]
st.dataframe(df[available].sort_values("Published Date", ascending=False),
             use_container_width=True, hide_index=True)
