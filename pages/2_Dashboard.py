from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.sheets import build_classified_meta_view
from utils.taxonomy import PRODUCTS

st.set_page_config(page_title="Dashboard — Creative OS", layout="wide")
st.title("Dashboard")
st.caption(
    "Live performance volume comes from Meta Ads. Inhouse taxonomy comes from Inhouse_Live_Assets. "
    "Influencer is identified by Live Entries 2026, and everything left over is treated as Porcellia."
)

with st.spinner("Loading Meta Ads, Inhouse, and Influencer sheets..."):
    classified = build_classified_meta_view()

if classified.empty:
    st.error("Could not build the live dashboard view from the connected sheets.")
    st.stop()

classified = classified.copy()
classified = classified[classified["AD CODE"].astype(str).str.strip() != ""]
classified = classified[classified["_Date"].notna()]

# Defensive clamp: one malformed far-future/far-past parsed date in Meta Ads
# should not break the whole dashboard window logic.
reasonable_floor = pd.Timestamp("2020-01-01")
reasonable_ceiling = pd.Timestamp.today().normalize() + pd.Timedelta(days=365)
classified = classified[
    (classified["_Date"] >= reasonable_floor) &
    (classified["_Date"] <= reasonable_ceiling)
]

if classified.empty:
    st.warning("No live Meta Ads rows with both an AD CODE and a sane live date were found.")
    st.stop()

today = date.today()
anchor_ts = classified["_Date"].max().normalize()
anchor = anchor_ts.date()

st.sidebar.header("Date range")
window = st.sidebar.radio(
    "Window",
    ["Last 7 days", "Last 30 days", "Last 90 days", "All time", "Custom"],
    index=1,
)

if window == "Last 7 days":
    start, end = anchor - timedelta(days=7), anchor
elif window == "Last 30 days":
    start, end = anchor - timedelta(days=30), anchor
elif window == "Last 90 days":
    start, end = anchor - timedelta(days=90), anchor
elif window == "All time":
    start, end = classified["_Date"].min().date(), anchor
else:
    start = st.sidebar.date_input("From", value=anchor - timedelta(days=30))
    end = st.sidebar.date_input("To", value=max(anchor, today))

st.sidebar.caption(f"Anchored on most recent live date: **{anchor}**")

st.sidebar.markdown("---")
sources = st.sidebar.multiselect(
    "Source",
    ["Inhouse", "Influencer", "Porcellia", "Unclassified"],
    default=["Inhouse", "Influencer", "Porcellia"],
)

product_options = sorted(
    product for product in classified["Product Derived"].dropna().astype(str).unique()
    if product.strip()
)
selected_products = st.sidebar.multiselect(
    "Product",
    product_options or PRODUCTS,
    default=product_options or PRODUCTS,
)

format_options = ["Video", "Static"]
selected_formats = st.sidebar.multiselect("Format", format_options, default=format_options)

filtered = classified.copy()
filtered = filtered[
    (filtered["_Date"] >= pd.Timestamp(start)) &
    (filtered["_Date"] <= pd.Timestamp(end))
]
filtered = filtered[filtered["Source"].isin(sources)]
if selected_products:
    filtered = filtered[filtered["Product Derived"].isin(selected_products)]
if selected_formats:
    filtered = filtered[
        filtered["Format Derived"].isin(selected_formats) |
        (filtered["Format Derived"].astype(str).str.strip() == "")
    ]

if filtered.empty:
    st.warning("No live ads match the current filters.")
    st.stop()

inhouse = filtered[filtered["Source"] == "Inhouse"].copy()

top_metrics = st.columns(5)
top_metrics[0].metric("Total live ads", len(filtered))
top_metrics[1].metric("Inhouse", int((filtered["Source"] == "Inhouse").sum()))
top_metrics[2].metric("Influencer", int((filtered["Source"] == "Influencer").sum()))
top_metrics[3].metric("Porcellia", int((filtered["Source"] == "Porcellia").sum()))
top_metrics[4].metric(
    "Tagged inhouse",
    int(inhouse["Asset ID"].astype(str).str.strip().ne("").sum()) if "Asset ID" in inhouse.columns else 0,
    help="Inhouse live ads that already have a row in Inhouse_Live_Assets.",
)

tab_overview, tab_inhouse, tab_raw = st.tabs(["Overview", "Inhouse Detail", "Raw Live Ads"])

with tab_overview:
    left, right = st.columns(2)

    with left:
        st.subheader("Live ads by source")
        source_counts = filtered["Source"].value_counts().reset_index()
        source_counts.columns = ["Source", "Count"]
        fig = px.pie(
            source_counts,
            names="Source",
            values="Count",
            color="Source",
            color_discrete_map={
                "Inhouse": "#0F6E56",
                "Influencer": "#2EA882",
                "Porcellia": "#A8D5C6",
                "Unclassified": "#D7E6E1",
            },
        )
        fig.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Live ads over time")
        timeline = filtered.copy()
        timeline["Week"] = timeline["_Date"].dt.to_period("W").dt.start_time
        weekly = timeline.groupby(["Week", "Source"]).size().reset_index(name="Count")
        fig = px.bar(
            weekly,
            x="Week",
            y="Count",
            color="Source",
            barmode="stack",
            color_discrete_map={
                "Inhouse": "#0F6E56",
                "Influencer": "#2EA882",
                "Porcellia": "#A8D5C6",
                "Unclassified": "#D7E6E1",
            },
        )
        fig.update_layout(margin=dict(t=10, b=10), xaxis_title="", yaxis_title="Ads live")
        st.plotly_chart(fig, use_container_width=True)

    left, right = st.columns(2)

    with left:
        st.subheader("Source × product")
        source_product = (
            filtered.groupby(["Product Derived", "Source"])
            .size()
            .reset_index(name="Count")
        )
        fig = px.bar(
            source_product,
            x="Product Derived",
            y="Count",
            color="Source",
            barmode="group",
            color_discrete_map={
                "Inhouse": "#0F6E56",
                "Influencer": "#2EA882",
                "Porcellia": "#A8D5C6",
                "Unclassified": "#D7E6E1",
            },
        )
        fig.update_layout(margin=dict(t=10, b=10), xaxis_title="", yaxis_title="Ads live")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Format split")
        format_counts = (
            filtered["Format Derived"]
            .replace("", "Unknown")
            .fillna("Unknown")
            .value_counts()
            .reset_index()
        )
        format_counts.columns = ["Format", "Count"]
        fig = px.pie(format_counts, names="Format", values="Count", color_discrete_sequence=px.colors.sequential.Teal)
        fig.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig, use_container_width=True)

    if not inhouse.empty:
        left, right = st.columns(2)

        with left:
            st.subheader("Top inhouse marketing angles")
            angle_counts = (
                inhouse["Marketing Angle Derived"]
                .replace("", pd.NA)
                .dropna()
                .value_counts()
                .head(15)
                .reset_index()
            )
            angle_counts.columns = ["Marketing Angle", "Count"]
            if angle_counts.empty:
                st.info("No inhouse marketing angles tagged yet.")
            else:
                fig = px.bar(
                    angle_counts,
                    x="Count",
                    y="Marketing Angle",
                    orientation="h",
                    color="Count",
                    color_continuous_scale="Teal",
                    text="Count",
                )
                fig.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    coloraxis_showscale=False,
                    margin=dict(t=10, b=10),
                )
                st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Top inhouse cohorts")
            cohort_counts = (
                inhouse["Cohort"]
                .replace("", pd.NA)
                .dropna()
                .value_counts()
                .head(15)
                .reset_index()
            )
            cohort_counts.columns = ["Cohort", "Count"]
            if cohort_counts.empty:
                st.info("No inhouse cohorts tagged yet.")
            else:
                fig = px.bar(
                    cohort_counts,
                    x="Count",
                    y="Cohort",
                    orientation="h",
                    color="Count",
                    color_continuous_scale="Teal",
                    text="Count",
                )
                fig.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    coloraxis_showscale=False,
                    margin=dict(t=10, b=10),
                )
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No inhouse live ads match this window yet, so the taxonomy deep dive is empty.")

with tab_inhouse:
    st.subheader("Inhouse live assets")
    if inhouse.empty:
        st.info("No inhouse live ads match the current filters.")
    else:
        metrics = st.columns(4)
        metrics[0].metric("Inhouse live ads", len(inhouse))
        metrics[1].metric("Videos", int((inhouse["Format Derived"] == "Video").sum()))
        metrics[2].metric("Statics", int((inhouse["Format Derived"] == "Static").sum()))
        metrics[3].metric(
            "Unique angles",
            int(
                inhouse["Marketing Angle Derived"]
                .replace("", pd.NA)
                .dropna()
                .nunique()
            ),
        )

        display_cols = [
            "Asset ID", "AD CODE", "_Date", "Product Derived", "Format Derived",
            "Video Subtype", "Static Subtype", "Creator / Consumer Name",
            "Marketing Angle Derived", "Belief", "Cohort", "Funnel Stage",
            "Drive Link", "Reference Image Link",
        ]
        show = inhouse[[column for column in display_cols if column in inhouse.columns]].copy()
        if "_Date" in show.columns:
            show = show.rename(columns={"_Date": "Live Date"})
        if "Product Derived" in show.columns:
            show = show.rename(columns={"Product Derived": "Product"})
        if "Format Derived" in show.columns:
            show = show.rename(columns={"Format Derived": "Format"})
        if "Marketing Angle Derived" in show.columns:
            show = show.rename(columns={"Marketing Angle Derived": "Marketing Angle"})

        st.dataframe(
            show.sort_values("Live Date", ascending=False) if "Live Date" in show.columns else show,
            use_container_width=True,
            hide_index=True,
            height=420,
        )

        st.caption("For a cleaner single-asset inspection, use Asset Registry.")

with tab_raw:
    st.subheader("Raw classified Meta Ads rows")
    raw_cols = [
        "Source", "AD CODE", "_Date", "Creative Name Derived",
        "Meta Creative Type", "Product Derived", "Format Derived",
        "Meta Funnel Level", "Meta Marketing Angle", "Meta Status",
        "Asset ID", "Creator / Consumer Name", "Meta Creative Folder",
    ]
    raw = filtered[[column for column in raw_cols if column in filtered.columns]].copy()
    raw = raw.rename(
        columns={
            "_Date": "Live Date",
            "Creative Name Derived": "Creative Name",
            "Product Derived": "Product",
            "Format Derived": "Format",
            "Meta Creative Type": "Meta Creative Type",
            "Meta Funnel Level": "Meta Funnel Level",
            "Meta Marketing Angle": "Meta Marketing Angle",
            "Meta Status": "Meta Status",
            "Meta Creative Folder": "Meta Creative Folder",
        }
    )
    st.dataframe(
        raw.sort_values("Live Date", ascending=False) if "Live Date" in raw.columns else raw,
        use_container_width=True,
        hide_index=True,
        height=460,
    )

    st.caption(
        "If a row is Inhouse but has blank taxonomy fields, it means the AD CODE matched but the asset still "
        "needs richer tagging in Inhouse_Live_Assets."
    )
