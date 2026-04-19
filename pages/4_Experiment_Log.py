import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import load_experiments, load_assets, save_experiment, next_experiment_id
from utils.taxonomy import (
    PRODUCTS, BELIEFS, FUNNEL_STAGES, EXPERIMENT_VARIABLES,
    EXPERIMENT_STATUSES, NEXT_ACTIONS, get_cohorts,
)

st.set_page_config(page_title="Experiment Log — Creative OS", layout="wide")
st.title("Experiment Log")
st.caption("Plan intentional tests. One row = one hypothesis. Link assets as control / variants.")

experiments_df = load_experiments()
assets_df      = load_assets()

existing_exp_ids = experiments_df["Experiment ID"].tolist() if not experiments_df.empty else []

asset_opts = ["None"] + (
    [f"{r['Asset ID']} — {r['Creative Type']} | {r.get('Marketing Angle','')}"
     for _, r in assets_df.iterrows()]
    if not assets_df.empty else []
)

# ── LOG NEW EXPERIMENT ────────────────────────────────────────────────────────
with st.expander("➕ Log new experiment", expanded=False):
    with st.form("log_experiment", clear_on_submit=True):
        st.subheader("What are we testing?")
        e1, e2, e3 = st.columns(3)
        product     = e1.selectbox("Product *", PRODUCTS)
        cohort      = e2.selectbox("Cohort *", get_cohorts(product))
        belief      = e3.selectbox("Belief *", BELIEFS)

        e4, e5 = st.columns(2)
        funnel   = e4.selectbox("Funnel Stage *", FUNNEL_STAGES)
        variable = e5.selectbox("Variable Being Tested *", EXPERIMENT_VARIABLES)

        core_msg   = st.text_input("Core Message *", placeholder="One-line summary of what you're testing")
        fixed      = st.text_area("What Stays Fixed *",
                                  placeholder="List every element that does NOT change between variants",
                                  height=70)
        hypothesis = st.text_area("Hypothesis *",
                                  placeholder="If we change [X], we expect [Y] because [Z]",
                                  height=70)

        st.subheader("Assets")
        ctrl_sel = st.selectbox("Control Asset *", asset_opts)
        control  = "" if ctrl_sel == "None" else ctrl_sel.split(" — ")[0]
        variant_ids = st.text_input("Variant Asset IDs",
                                    placeholder="Comma-separated, e.g. RCF-V-002, RCF-V-003")

        st.subheader("Timeline & decision rule")
        d1, d2 = st.columns(2)
        start_date  = d1.date_input("Start Date", value=None)
        review_date = d2.date_input("Review Date", value=None)
        decision    = st.text_input("Decision Rule",
                                    placeholder="e.g. If variant ROAS > control by ≥20% over 7 days → scale variant")
        notes       = st.text_area("Notes", height=60)

        submitted = st.form_submit_button("✅ Save Experiment", type="primary",
                                          use_container_width=True)

        if submitted:
            if not core_msg:
                st.error("Core Message is required.")
            else:
                exp_id = next_experiment_id(existing_exp_ids)
                row = {
                    "Experiment ID":        exp_id,
                    "Product":              product,
                    "Core Message":         core_msg,
                    "Belief":               belief,
                    "Cohort":               cohort,
                    "Funnel Stage":         funnel,
                    "Variable Being Tested": variable,
                    "What Stays Fixed":     fixed,
                    "Hypothesis":           hypothesis,
                    "Control Asset ID":     control,
                    "Variant Asset IDs":    variant_ids,
                    "Decision Rule":        decision,
                    "Start Date":           start_date.strftime("%Y-%m-%d") if start_date else "",
                    "Review Date":          review_date.strftime("%Y-%m-%d") if review_date else "",
                    "Status":               "Planning",
                    "Result":               "",
                    "Next Action":          "",
                    "Notes":                notes,
                }
                try:
                    save_experiment(row)
                    st.success(f"✅ Saved! Experiment ID: **{exp_id}**")
                except Exception as e:
                    st.error(f"Save failed: {e}")

# ── ACTIVE EXPERIMENTS TABLE ──────────────────────────────────────────────────
st.markdown("---")

if experiments_df.empty:
    st.info("No experiments logged yet.")
    st.stop()

status_filter = st.multiselect(
    "Filter by status",
    EXPERIMENT_STATUSES,
    default=["Planning", "Live", "In Review"],
)
filtered = experiments_df[experiments_df["Status"].isin(status_filter)] if status_filter else experiments_df

st.dataframe(filtered, use_container_width=True, hide_index=True)

# ── UPDATE RESULT ─────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Record result")

if not experiments_df.empty:
    from utils.sheets import _ws, EXPERIMENT_HEADERS
    exp_ids = experiments_df["Experiment ID"].tolist()

    with st.form("update_experiment"):
        u1, u2 = st.columns(2)
        chosen_id   = u1.selectbox("Experiment ID", exp_ids)
        new_status  = u1.selectbox("New Status", EXPERIMENT_STATUSES)
        next_action = u2.selectbox("Next Action", ["—"] + NEXT_ACTIONS)
        result      = st.text_area("Result summary", height=80,
                                   placeholder="What happened? Which variant won and by how much?")
        save_result = st.form_submit_button("💾 Save Result")

        if save_result:
            try:
                ws   = _ws("Experiment_Log")
                cell = ws.find(chosen_id)
                if cell:
                    col_status  = EXPERIMENT_HEADERS.index("Status") + 1
                    col_result  = EXPERIMENT_HEADERS.index("Result") + 1
                    col_next    = EXPERIMENT_HEADERS.index("Next Action") + 1
                    ws.update_cell(cell.row, col_status, new_status)
                    ws.update_cell(cell.row, col_result, result)
                    if next_action != "—":
                        ws.update_cell(cell.row, col_next, next_action)
                    st.success("Result saved.")
                else:
                    st.error("Experiment ID not found in sheet.")
            except Exception as e:
                st.error(f"Update failed: {e}")
