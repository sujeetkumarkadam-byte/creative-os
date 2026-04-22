import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import load_experiments, save_experiment, next_experiment_id, _ws, EXPERIMENT_HEADERS
from utils.taxonomy import (
    PRODUCTS, FUNNEL_STAGES, EXPERIMENT_STATUSES,
    get_cohorts, get_angles, get_drivers, get_beliefs,
)

st.set_page_config(page_title="Stage-1 Briefs — Creative OS", layout="wide")
st.title("Stage-1 Briefs (Static Experiments)")
st.caption("Plan WHAT you want to test — angle, cohort, belief. Take this to Claude / MJ for copy & visuals. "
           "Once the static goes live on Meta, promote it via *Log Live Asset → Static* tab.")

experiments_df = load_experiments()
existing_exp_ids = experiments_df["Experiment ID"].tolist() if not experiments_df.empty else []

# ── NEW BRIEF ─────────────────────────────────────────────────────────────────
with st.expander("➕ Create new Stage-1 brief", expanded=True):
    with st.form("new_brief", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        product = c1.selectbox("Product *", PRODUCTS)
        planned_date = c2.date_input("Planned Date", value=datetime.now().date())
        funnel = c3.selectbox("Funnel Stage *", FUNNEL_STAGES)

        cohorts = get_cohorts(product)
        angles  = get_angles(product)
        drivers = get_drivers(product)
        beliefs = get_beliefs(product)

        t1, t2 = st.columns(2)
        cohort = t1.selectbox("Cohort *", cohorts)
        belief = t1.selectbox("Belief *", beliefs)
        angle  = t2.selectbox("Marketing Angle *", angles)
        driver = t2.selectbox("Situational Driver", drivers)

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
