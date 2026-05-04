import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import load_experiments, save_experiment, next_experiment_id, _ws, EXPERIMENT_HEADERS
from utils.taxonomy import (
    PRODUCTS, FUNNEL_STAGES, EXPERIMENT_STATUSES,
    STATIC_SUBTYPES, VISUAL_HOOK_TYPES, CONTENT_HOOK_TYPES,
    VISUAL_TREATMENTS, STATIC_MESSAGE_TYPES, CTA_FORMATS, CTA_MESSAGE_TYPES,
    AI_GENERATED_OPTIONS, TAXONOMY_CONFIDENCE,
    get_cohorts, get_angles, get_drivers, get_beliefs,
    options_with_blank, selected_info,
)

st.set_page_config(page_title="Stage-1 Briefs — Creative OS", layout="wide")
st.title("Stage-1 Briefs (Static Experiments)")
st.caption("Plan WHAT you want to test — angle, cohort, belief. Take this to Claude / MJ for copy & visuals. "
           "Once the static goes live on Meta, promote it via *Log Live Asset → Static* tab.")

experiments_df = load_experiments()
existing_exp_ids = experiments_df["Experiment ID"].tolist() if not experiments_df.empty else []


def _idx(options: list[str], value: str, default: int = 0) -> int:
    return options.index(value) if value in options else default


def _tax_select(container, label: str, options: list[str], value: str = "", help_text: str = ""):
    opts = options_with_blank(options)
    picked = container.selectbox(label, opts, index=_idx(opts, value), help=help_text)
    info = selected_info(picked)
    if info:
        container.caption(info)
    return picked

# ── NEW BRIEF ─────────────────────────────────────────────────────────────────
with st.expander("➕ Create new Stage-1 brief", expanded=True):
    with st.form("new_brief", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        product = c1.selectbox("Product *", PRODUCTS)
        planned_date = c2.date_input("Planned Date", value=datetime.now().date())
        funnel = _tax_select(c3, "Funnel Stage *", FUNNEL_STAGES, help_text="Where this static sits in the buying journey.")

        cohorts = get_cohorts(product)
        angles  = get_angles(product)
        drivers = get_drivers(product)
        beliefs = get_beliefs(product)

        t1, t2 = st.columns(2)
        cohort = _tax_select(t1, "Cohort *", cohorts, help_text="Who this creative is speaking to.")
        belief = _tax_select(t1, "Belief *", beliefs, help_text="The belief shift this creative is trying to create.")
        angle = _tax_select(t2, "Marketing Angle *", angles, help_text="The message route. Exact MD columns appear below after selection.")
        driver = _tax_select(t2, "Situational Driver", drivers, help_text="The trigger or moment that makes the need active now.")

        add_execution = st.checkbox(
            "Add optional execution cuts now",
            value=False,
            help="Keep this off if you only want to brief the angle/persona/belief. Fill these later when the static is generated or goes live.",
        )
        static_subtype = visual_hook = content_hook = visual_treatment = static_message = cta_format = cta_message = ""
        ai_generated = ""
        taxonomy_confidence = "Needs Review"
        primary_proof = ""
        if add_execution:
            with st.expander("Optional static execution plan", expanded=True):
                s1, s2, s3 = st.columns(3)
                static_subtype = _tax_select(s1, "Static Subtype", STATIC_SUBTYPES, help_text="The structural type of static/carousel.")
                visual_hook = _tax_select(s1, "Visual Hook Type", VISUAL_HOOK_TYPES, help_text="What is shown first in the first static impression.")
                content_hook = _tax_select(s2, "Content Hook / Headline Type", CONTENT_HOOK_TYPES, help_text="What the headline/opening idea communicates.")
                visual_treatment = _tax_select(s2, "Visual Treatment", VISUAL_TREATMENTS, help_text="The dominant visual treatment of the static.")
                static_message = _tax_select(s3, "Static Message Type", STATIC_MESSAGE_TYPES, help_text="What the body of the static primarily communicates.")
                cta_format = _tax_select(s3, "CTA Format", CTA_FORMATS, help_text="How the CTA is delivered.")

                s4, s5, s6 = st.columns(3)
                cta_message = _tax_select(s4, "CTA Message Type", CTA_MESSAGE_TYPES, help_text="What the CTA is communicating.")
                ai_generated = s5.selectbox("AI-Generated?", AI_GENERATED_OPTIONS)
                taxonomy_confidence = s6.selectbox("Taxonomy Confidence", TAXONOMY_CONFIDENCE, index=1)
                primary_proof = st.text_input(
                    "Primary Proof Needed",
                    placeholder="e.g. RCF-CLM-04, review screenshot, product demo, before/after",
                )

        core_msg = st.text_input(
            "Core Message (1-line) *",
            placeholder="e.g. Clinical early proof — 4-day signal reassures long-term burnt out users",
        )
        hypothesis = st.text_area(
            "Hypothesis *",
            placeholder="If we test [angle] with [cohort] via a static, we expect [outcome] because [reason]",
            height=80,
        )
        ai_tool = st.selectbox(
            "AI Tool Used",
            ["None", "Claude", "ChatGPT", "Midjourney", "DALL-E", "Ideogram", "Other"],
        )
        ref_link = st.text_input(
            "Reference Image Link (optional)",
            placeholder="URL or Drive link to the inspiration you fed into the AI",
        )
        notes = st.text_area("Notes", height=60)

        submitted = st.form_submit_button("✅ Save Brief", type="primary", use_container_width=True)

        if submitted:
            if not core_msg.strip() or not hypothesis.strip():
                st.error("Core Message and Hypothesis are required.")
            else:
                exp_id = next_experiment_id(existing_exp_ids)
                row = {
                    "Experiment ID": exp_id,
                    "Product": product,
                    "Core Message": core_msg,
                    "Belief": belief,
                    "Cohort": cohort,
                    "Funnel Stage": funnel,
                    "Marketing Angle": angle,
                    "Situational Driver": driver,
                    "Static Subtype": static_subtype,
                    "Visual Hook Type": visual_hook,
                    "Content Hook Type": content_hook,
                    "Visual Treatment": visual_treatment,
                    "Static Message Type": static_message,
                    "CTA Format": cta_format,
                    "CTA Message Type": cta_message,
                    "AI-Generated": ai_generated,
                    "Taxonomy Confidence": taxonomy_confidence,
                    "Primary Proof Needed": primary_proof,
                    "Hypothesis": hypothesis,
                    "AI Tool Used": ai_tool,
                    "Reference Image Link": ref_link,
                    "Start Date": planned_date.strftime("%Y-%m-%d") if planned_date else "",
                    "Status": "Planning",
                    "Promoted To Asset ID": "",
                    "Notes": notes,
                }
                try:
                    save_experiment(row)
                    st.success(f"✅ Brief saved. ID: **{exp_id}** — now go generate with AI, "
                               "publish on Meta, then come back to *Log Live Asset* to promote.")
                except Exception as e:
                    st.error(f"Save failed: {e}")

# ── BRIEF LIST ────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("All Stage-1 briefs")

if experiments_df.empty:
    st.info("No briefs yet.")
    st.stop()

status_options = ["Planning", "Live", "In Review", "Decided", "Published"]
status_filter = st.multiselect(
    "Filter by status",
    status_options,
    default=["Planning", "Live", "In Review"],
)

filtered = experiments_df.copy()
if status_filter and "Status" in filtered.columns:
    filtered = filtered[filtered["Status"].isin(status_filter)]

show_cols = [
    "Experiment ID", "Product", "Cohort", "Belief", "Marketing Angle",
    "Static Subtype", "Content Hook Type", "Static Message Type",
    "Core Message", "Status", "Promoted To Asset ID", "Start Date",
]
available = [c for c in show_cols if c in filtered.columns]
st.dataframe(
    filtered[available].sort_values("Start Date", ascending=False) if "Start Date" in available else filtered[available],
    use_container_width=True, hide_index=True,
)

# ── UPDATE STATUS ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Update brief status / record result")

with st.form("update_brief"):
    u1, u2 = st.columns(2)
    exp_ids = experiments_df["Experiment ID"].dropna().tolist()
    chosen_id = u1.selectbox("Brief ID", exp_ids)
    new_status = u1.selectbox("New Status", status_options)
    result = u2.text_area("Result notes", height=80,
                          placeholder="What happened? Was it promoted? Killed? Learnings?")
    save_result = st.form_submit_button("💾 Save")

    if save_result:
        try:
            ws = _ws("Experiment_Log")
            cell = ws.find(chosen_id)
            if cell:
                col_status = EXPERIMENT_HEADERS.index("Status") + 1
                ws.update_cell(cell.row, col_status, new_status)
                if result.strip() and "Result" in EXPERIMENT_HEADERS:
                    col_result = EXPERIMENT_HEADERS.index("Result") + 1
                    ws.update_cell(cell.row, col_result, result)
                st.success(f"Saved. `{chosen_id}` → {new_status}.")
            else:
                st.error("Brief ID not found.")
        except Exception as e:
            st.error(f"Update failed: {e}")
