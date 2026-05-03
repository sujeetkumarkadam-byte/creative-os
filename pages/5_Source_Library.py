import streamlit as st
import pandas as pd
from utils.sheets import load_sources, save_source, next_source_id
from utils.taxonomy import PRODUCTS, SOURCE_TYPES, STORY_STRENGTHS, get_cohorts, get_beliefs

st.set_page_config(page_title="Source Library — Creative OS", layout="wide")
st.title("Source Story Library")
st.caption("One row = one consumer interview or review. Track angles extracted, variants published, unused angles remaining.")

sources_df = load_sources()
existing_src_ids = sources_df["Source ID"].tolist() if not sources_df.empty else []

# ── LOG NEW SOURCE ────────────────────────────────────────────────────────────
with st.expander("➕ Log new source interview / review", expanded=False):
    with st.form("log_source", clear_on_submit=True):
        s1, s2, s3 = st.columns(3)
        product     = s1.selectbox("Product *", PRODUCTS)
        source_type = s2.selectbox("Source Type *", SOURCE_TYPES)
        strength    = s3.selectbox("Story Strength (1–5)", STORY_STRENGTHS, index=2,
                                   help="1 = weak / vague, 5 = exceptional clarity + emotion")

        name_code  = st.text_input("Consumer Name / Code *",
                                   placeholder="e.g. Priya S. or Anon-047")
        cohort     = st.selectbox("Cohort Match *", get_cohorts(product))
        beliefs    = st.multiselect("Beliefs Supported", get_beliefs(product))

        s4, s5 = st.columns(2)
        recording = s4.text_input("Recording Link",  placeholder="Drive / Zoom / Meet link")
        transcript = s5.text_input("Transcript Link", placeholder="Drive doc link")

        before_state = st.text_area("Before-State Summary",
                                    placeholder="What was their skin like before? What had they tried?",
                                    height=80)
        trigger      = st.text_area("Trigger / Context",
                                    placeholder="What made them try RCF / Sunscreen / BRGM?",
                                    height=60)
        quotes       = st.text_area("Key Quotes",
                                    placeholder="Paste 2–5 verbatim quotes that could become hooks",
                                    height=100)
        notes        = st.text_area("Notes", height=60)

        submitted = st.form_submit_button("✅ Save Source", type="primary", use_container_width=True)

        if submitted:
            if not name_code:
                st.error("Consumer Name / Code is required.")
            else:
                src_id = next_source_id(existing_src_ids)
                row = {
                    "Source ID":              src_id,
                    "Consumer Name/Code":     name_code,
                    "Product":                product,
                    "Source Type":            source_type,
                    "Recording Link":         recording,
                    "Transcript Link":        transcript,
                    "Story Strength":         strength,
                    "Before-State Summary":   before_state,
                    "Trigger / Context":      trigger,
                    "Key Quotes":             quotes,
                    "Cohort Match":           cohort,
                    "Beliefs Supported":      ", ".join(beliefs),
                    "Total Angles Extracted":  0,
                    "Total Variants Published": 0,
                    "Unused Angles Remaining": 0,
                    "Best Asset ID":          "",
                    "Notes":                  notes,
                }
                try:
                    save_source(row)
                    st.success(f"✅ Saved! Source ID: **{src_id}**")
                except Exception as e:
                    st.error(f"Save failed: {e}")

# ── SOURCE TABLE ──────────────────────────────────────────────────────────────
st.markdown("---")

if sources_df.empty:
    st.info("No sources logged yet.")
    st.stop()

prod_filter = st.multiselect("Filter by Product", PRODUCTS, default=PRODUCTS)
df = sources_df[sources_df["Product"].isin(prod_filter)]

st.markdown(f"**{len(df)}** sources &nbsp;|&nbsp; "
            f"Total angles extracted: **{pd.to_numeric(df.get('Total Angles Extracted', pd.Series()), errors='coerce').sum():.0f}** &nbsp;|&nbsp; "
            f"Unused angles: **{pd.to_numeric(df.get('Unused Angles Remaining', pd.Series()), errors='coerce').sum():.0f}**")

display_cols = [
    "Source ID", "Consumer Name/Code", "Product", "Source Type",
    "Story Strength", "Cohort Match", "Beliefs Supported",
    "Total Angles Extracted", "Total Variants Published", "Unused Angles Remaining",
    "Best Asset ID",
]
available = [c for c in display_cols if c in df.columns]
st.dataframe(df[available].sort_values("Story Strength", ascending=False),
             use_container_width=True, hide_index=True)

# ── UPDATE USAGE COUNTS ───────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Update angle / variant counts")

src_ids = df["Source ID"].tolist()
if src_ids:
    with st.form("update_source"):
        from utils.sheets import _ws, SOURCE_HEADERS
        u1, u2, u3 = st.columns(3)
        chosen_src  = u1.selectbox("Source ID", src_ids)
        angles_ext  = u2.number_input("Total Angles Extracted", min_value=0, step=1)
        variants_pub = u3.number_input("Total Variants Published", min_value=0, step=1)
        unused      = st.number_input("Unused Angles Remaining", min_value=0, step=1)
        best_id     = st.text_input("Best Asset ID", placeholder="e.g. RCF-V-004")
        save_btn    = st.form_submit_button("💾 Save counts")

        if save_btn:
            try:
                ws   = _ws("Source_Story_Library")
                cell = ws.find(chosen_src)
                if cell:
                    for field, val in [
                        ("Total Angles Extracted",   angles_ext),
                        ("Total Variants Published",  variants_pub),
                        ("Unused Angles Remaining",   unused),
                        ("Best Asset ID",             best_id),
                    ]:
                        col = SOURCE_HEADERS.index(field) + 1
                        ws.update_cell(cell.row, col, val)
                    st.success("Counts updated.")
                else:
                    st.error("Source ID not found in sheet.")
            except Exception as e:
                st.error(f"Update failed: {e}")
