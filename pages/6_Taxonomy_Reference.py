import pandas as pd
import streamlit as st

from utils.taxonomy import (
    PRODUCTS,
    PRODUCT_META,
    table_rows_for_product,
    universal_table_rows,
)


st.set_page_config(page_title="Taxonomy Reference - Creative OS", layout="wide")
st.title("Taxonomy Reference")
st.caption("Exact approved taxonomy from the MD handover. Rows and columns are not rewritten or simplified.")

product = st.selectbox("Product", PRODUCTS, index=0)
meta = PRODUCT_META.get(product, {})

top1, top2, top3 = st.columns(3)
top1.metric("Product Code", meta.get("code", ""))
top2.metric("Priority", meta.get("priority", ""))
top3.metric("Taxonomy Confidence", meta.get("confidence", ""))
if meta.get("notes"):
    st.info(meta["notes"])


def render_exact_table(title: str, headers: list[str], rows: list[dict], empty_text: str):
    st.subheader(title)
    if not rows:
        st.info(empty_text)
        return
    columns = headers or list(rows[0].keys())
    df = pd.DataFrame(rows)
    for column in columns:
        if column not in df.columns:
            df[column] = ""
    st.dataframe(df[columns], use_container_width=True, hide_index=True)


st.markdown("---")
st.header(f"Product-Specific Taxonomy: {product}")

PRODUCT_SECTIONS = [
    ("Marketing Angles", "angles", "No approved marketing angle rows exist for this product in the handover."),
    ("Beliefs", "beliefs", "No approved belief rows exist for this product in the handover."),
    ("Consumer Cohorts / Personas", "cohorts", "No approved cohort rows exist for this product in the handover."),
    ("Situational Drivers", "drivers", "No approved situational driver rows exist for this product in the handover."),
    ("Product-Specific Proof / Claims", "claims", "No approved proof/claim rows exist for this product in the handover."),
]

for title, kind, empty in PRODUCT_SECTIONS:
    headers, rows = table_rows_for_product(product, kind)
    render_exact_table(title, headers, rows, empty)


st.markdown("---")
st.header("Universal Creative Cuts")

UNIVERSAL_SECTIONS = [
    ("Formats", "formats"),
    ("Video Subtypes", "video_subtypes"),
    ("Static Subtypes", "static_subtypes"),
    ("Visual Hook Types", "visual_hook_types"),
    ("Content Hook Types", "content_hook_types"),
    ("Emotional Arcs", "emotional_arcs"),
    ("Funnel Stages", "funnel_stages"),
    ("Creator Archetypes", "creator_archetypes"),
    ("Influence Modes", "influence_modes"),
    ("Visual Treatment (Statics)", "visual_treatments"),
    ("CTA Format", "cta_formats"),
    ("CTA Message Type", "cta_message_types"),
    ("Static Message Type", "static_message_types"),
]

for title, kind in UNIVERSAL_SECTIONS:
    headers, rows = universal_table_rows(kind)
    render_exact_table(title, headers, rows, "No rows found in the approved handover.")

st.caption("Source: data/approved_taxonomy.json generated from Creative_OS_Approved_Taxonomy_Handover.md.")
