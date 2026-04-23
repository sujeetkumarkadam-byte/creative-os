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

raw_classified = classified.copy()
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

    total_rows = len(raw_classified)
    rows_with_code = int(raw_classified["AD CODE"].astype(str).str.strip().ne("").sum()) if "AD CODE" in raw_classified.columns else 0
    rows_with_date = int(raw_classified["_Date"].notna().sum()) if "_Date" in raw_classified.columns else 0

    st.info(
        f"Diagnostics: total rows loaded = {total_rows}, rows with AD CODE = {rows_with_code}, "
        f"rows with parsed live date = {rows_with_date}."
    )

    with st.expander("Show Meta Ads diagnostics", expanded=True):
        # Directly inspect the raw date column so we can see what's failing
        from utils.sheets import load_meta_ads, first_present_column, extract_date_from_name
        meta_raw = load_meta_ads()

        # Test the ad-name fallback extractor — how many dates can we salvage?
        st.markdown("**Ad-name date extraction (fallback):**")
        for candidate in ["FB Ad Name", "Ad Name (TSS)", "Ad Name (Porcellia)"]:
            if candidate in meta_raw.columns:
                with_code_rows = meta_raw[meta_raw.get("AD CODE", pd.Series(dtype=str)).astype(str).str.strip() != ""]
                extracted = with_code_rows[candidate].map(extract_date_from_name)
                hits = extracted.notna().sum()
                st.write(f"- `{candidate}` → **{int(hits)}** dates extracted (of {len(with_code_rows)} rows with AD CODE)")
        st.markdown("---")

        st.markdown("**All date-looking columns detected in Meta Ads:**")
        date_like_cols = [c for c in meta_raw.columns if "date" in c.lower()]
        st.code("\n".join(date_like_cols) or "(none)")

        primary_date_col = first_present_column(
            meta_raw, "Date [Ad Taken Live]", "Date [Ad Taken Live] ",
        )
        st.markdown(f"**Primary date column being read:** `{primary_date_col or 'NONE FOUND'}`")

        if primary_date_col and "AD CODE" in meta_raw.columns:
            # Filter to rows that have an AD CODE — those are the ads that matter
            with_code = meta_raw[meta_raw["AD CODE"].astype(str).str.strip() != ""].copy()

            live_dates_raw = with_code[primary_date_col].astype(str).str.strip()
            non_empty_dates = live_dates_raw[live_dates_raw != ""]

            st.markdown(
                f"**Of {len(with_code)} rows with AD CODE:** "
                f"`{len(non_empty_dates)}` have *any* value in `{primary_date_col}`."
            )

            if len(non_empty_dates) > 0:
                st.markdown("**First 15 raw date values (these are what parse_mixed_dates sees):**")
                sample = non_empty_dates.head(15).tolist()
                st.code("\n".join(f"{i+1:2}. {repr(v)}" for i, v in enumerate(sample)))
                st.caption(
                    "The `repr()` shows exact whitespace / quotes. If these look like real dates "
                    "but only 2 of them parse, paste this block back and I'll fix the parser."
                )
            else:
                st.warning(
                    "NO rows with AD CODE have anything in the 'Date [Ad Taken Live]' column. "
                    "Either the media buyer isn't populating it, or the actual live-date is "
                    "stored under a different column name. Check which of the date-like columns "
                    "above actually has values."
                )

            # Also sample some of the other date columns to see if ANY of them has the real date
            st.markdown("---")
            st.markdown(
                "**Sanity check — non-empty value counts across every date-like column "
                "(for rows with AD CODE):**"
            )
            counts = {}
            for c in date_like_cols:
                v = with_code[c].astype(str).str.strip()
                counts[c] = int((v != "").sum())
            st.dataframe(
                pd.DataFrame([{"Column": k, "Non-empty count": v} for k, v in counts.items()])
                  .sort_values("Non-empty count", ascending=False),
                use_container_width=True, hide_index=True,
            )
            st.caption(
                "If one of the other Date columns has ~542 non-empty values while "
                "'Date [Ad Taken Live]' has ~2, THAT is the real live-date column — we're "
                "reading the wrong one."
            )

        st.markdown("---")
        st.markdown("**Sample of first 25 classified rows:**")
        sample_cols = [
            "AD CODE", "Meta Product", "Meta Creative Type", "Meta Creative Name",
            "_Date", "Meta FB Ad Name", "Meta Ad Name (TSS)", "Meta Ad Name (Porcellia)",
        ]
        debug = raw_classified[[c for c in sample_cols if c in raw_classified.columns]].copy().head(25)
        if "_Date" in debug.columns:
            debug = debug.rename(columns={"_Date": "Parsed Live Date"})
        st.dataframe(debug, use_container_width=True, hide_index=True)
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

angle_options = sorted(
    value for value in classified["Marketing Angle Derived"].dropna().astype(str).unique()
    if value.strip()
) if "Marketing Angle Derived" in classified.columns else []
selected_angles = st.sidebar.multiselect("Marketing Angle", angle_options, default=angle_options)

cohort_options = sorted(
    value for value in classified["Cohort"].dropna().astype(str).unique()
    if value.strip()
) if "Cohort" in classified.columns else []
selected_cohorts = st.sidebar.multiselect("Cohort", cohort_options, default=cohort_options)

creator_query = st.sidebar.text_input("Creator / Creative Search", placeholder="creator, creative name, ad code...")

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
if selected_angles:
    filtered = filtered[filtered["Marketing Angle Derived"].isin(selected_angles)]
if selected_cohorts:
    filtered = filtered[
        filtered["Cohort"].astype(str).str.strip().eq("") |
        filtered["Cohort"].isin(selected_cohorts)
    ]
if creator_query.strip():
    term = creator_query.strip().lower()
    search_cols = [
        column for column in [
            "AD CODE", "Creative Name Derived", "Creator / Consumer Name",
            "Meta FB Ad Name", "Meta Ad Name (TSS)", "Meta Ad Name (Porcellia)",
        ] if column in filtered.columns
    ]
    mask = pd.Series(False, index=filtered.index)
    for column in search_cols:
        mask = mask | filtered[column].astype(str).str.lower().str.contains(term, na=False)
    filtered = filtered[mask]

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

tab_overview, tab_assets, tab_raw = st.tabs(["Overview", "Asset Deep Dive", "Raw Live Ads"])

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

with tab_assets:
    st.subheader("Filtered asset view")
    metrics = st.columns(5)
    metrics[0].metric("Filtered live ads", len(filtered))
    metrics[1].metric("Inhouse", int((filtered["Source"] == "Inhouse").sum()))
    metrics[2].metric("Influencer", int((filtered["Source"] == "Influencer").sum()))
    metrics[3].metric("Porcellia", int((filtered["Source"] == "Porcellia").sum()))
    metrics[4].metric(
        "Tagged taxonomy rows",
        int(filtered["Marketing Angle Derived"].astype(str).str.strip().ne("").sum()) if "Marketing Angle Derived" in filtered.columns else 0,
    )

    display_cols = [
        "Source", "AD CODE", "_Date", "Creative Name Derived", "Product Derived", "Format Derived",
        "Video Subtype", "Static Subtype", "Creator / Consumer Name", "Marketing Angle Derived",
        "Belief", "Cohort", "Funnel Stage", "Meta Status", "Drive Link", "Reference Image Link",
        "ROAS", "CTR", "Hook Rate", "Hold Rate", "CAC",
    ]
    show = filtered[[column for column in display_cols if column in filtered.columns]].copy()
    show = show.rename(columns={
        "_Date": "Live Date",
        "Creative Name Derived": "Creative Name",
        "Product Derived": "Product",
        "Format Derived": "Format",
        "Marketing Angle Derived": "Marketing Angle",
        "Meta Status": "Status",
    })
    if "Live Date" in show.columns:
        show = show.sort_values("Live Date", ascending=False)
    st.dataframe(show, use_container_width=True, hide_index=True, height=360)

    inspect_choices = filtered.copy()
    inspect_choices["_label"] = inspect_choices.apply(
        lambda row: f"{row.get('AD CODE', '')} | {row.get('Creative Name Derived', '') or row.get('Meta FB Ad Name', '') or row.get('Meta Ad Name (TSS)', '') or row.get('Meta Ad Name (Porcellia)', '')}",
        axis=1,
    )
    selected_label = st.selectbox("Inspect a filtered asset", inspect_choices["_label"].tolist())
    picked = inspect_choices[inspect_choices["_label"] == selected_label].iloc[0]

    left, right = st.columns(2)
    with left:
        st.markdown("**Identity & live info**")
        for field, label in [
            ("Source", "Source"), ("AD CODE", "AD CODE"), ("_Date", "Live Date"),
            ("Creative Name Derived", "Creative Name"), ("Product Derived", "Product"),
            ("Format Derived", "Format"), ("Meta Creative Type", "Creative Type"),
            ("Meta Status", "Status"), ("Meta Funnel Level", "Funnel Level"),
        ]:
            if field in picked.index:
                value = picked.get(field, "")
                if field == "_Date" and pd.notna(value):
                    value = value.strftime("%Y-%m-%d")
                st.write(f"**{label}:** {value or '?'}")
        if picked.get("Drive Link", ""):
            st.markdown(f"**Drive Link:** [Open asset]({picked['Drive Link']})")
        elif picked.get("Meta Creative Folder", ""):
            st.markdown(f"**Drive Link:** [Open folder]({picked['Meta Creative Folder']})")
        else:
            st.write("**Drive Link:** ?")

    with right:
        st.markdown("**Taxonomy & performance**")
        for field, label in [
            ("Marketing Angle Derived", "Marketing Angle"), ("Belief", "Belief"),
            ("Cohort", "Cohort"), ("Situational Driver", "Situational Driver"),
            ("Creator / Consumer Name", "Creator / Consumer Name"),
            ("Video Subtype", "Video Subtype"), ("Static Subtype", "Static Subtype"),
            ("ROAS", "ROAS"), ("CTR", "CTR"), ("Hook Rate", "Hook Rate"),
            ("Hold Rate", "Hold Rate"), ("CAC", "CAC"),
        ]:
            if field in picked.index:
                st.write(f"**{label}:** {picked.get(field, '') or '?'}")
        if picked.get("Reference Image Link", ""):
            st.markdown(f"**Reference Image:** [Open reference]({picked['Reference Image Link']})")
        else:
            st.write("**Reference Image:** ?")

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
