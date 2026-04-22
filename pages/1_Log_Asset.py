import streamlit as st
from datetime import datetime
from utils.sheets import (
    load_inhouse_live, load_sources, load_experiments,
    save_inhouse_live, next_asset_id, ensure_inhouse_sheet,
)
from utils.taxonomy import (
    PRODUCTS, BUCKETS, FORMATS, VIDEO_SUBTYPES, STATIC_SUBTYPES,
    HOOK_TYPES, EMOTIONAL_ARCS, FUNNEL_STAGES,
    ARCHETYPES, INFLUENCE_MODES, VISUAL_STYLES, CTA_STYLES,
    STATUSES, VARIANT_LETTERS,
    get_cohorts, get_angles, get_drivers, get_beliefs,
)

st.set_page_config(page_title="Log Live Asset — Creative OS", layout="wide")
st.title("Log Live Asset")
st.caption("One row = one inhouse asset that went live on Meta. Choose Video (direct) or Static (from Stage-1 brief).")

# Ensure destination sheet exists
try:
    ensure_inhouse_sheet()
except Exception as e:
    st.warning(f"Could not verify `Inhouse_Live_Assets` exists: {e}")

live_df     = load_inhouse_live()
sources_df  = load_sources()
exp_df      = load_experiments()

existing_ids = live_df["Asset ID"].tolist() if not live_df.empty else []

source_opts = ["None"] + (
    [f"{r['Source ID']} — {r['Consumer Name/Code']} ({r['Product']})"
     for _, r in sources_df.iterrows()]
    if not sources_df.empty else []
)

# Stage-1 experiments that are planned/ready but not yet promoted
def _stage1_pending() -> list:
    if exp_df.empty:
        return []
    d = exp_df.copy()
    promoted_col = "Promoted To Asset ID" if "Promoted To Asset ID" in d.columns else None
    if promoted_col:
        d = d[d[promoted_col].astype(str).str.strip() == ""]
    # Only show those that look like Stage-1 briefs (have Marketing Angle)
    if "Marketing Angle" in d.columns:
        d = d[d["Marketing Angle"].astype(str).str.strip() != ""]
    return d["Experiment ID"].dropna().tolist()


tab_video, tab_static = st.tabs(["🎥 Log Video (direct)", "🖼️ Log Static (from Stage-1 brief)"])


# ══════════════════════════════════════════════════════════════════════════════
# VIDEO FLOW
# ══════════════════════════════════════════════════════════════════════════════
with tab_video:
    st.subheader("Video asset that just went live")

    with st.form("log_video", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        product = c1.selectbox("Product *", PRODUCTS, key="v_product")
        video_subtype = c2.selectbox("Video Subtype *", VIDEO_SUBTYPES, key="v_subtype")
        bucket = c3.selectbox("Bucket *", BUCKETS, key="v_bucket")

        c4, c5 = st.columns(2)
        ad_code = c4.text_input("AD CODE *", placeholder="e.g. AD 467",
                                help="The Meta Ad ID / AD CODE. Links to Meta Ads sheet for perf auto-sync.")
        pub_date = c5.date_input("Published Date *", value=None, key="v_pubdate")

        # Variant block
        st.markdown("**Variant (optional)**")
        vcol1, vcol2 = st.columns(2)
        is_variant = vcol1.checkbox("This is a variant of another live asset", key="v_isvar")
        parent_id, variant_letter, what_diff, ab_pair = "", "A", "", ""
        if is_variant:
            parent_id = vcol1.text_input("Parent Asset ID", placeholder="e.g. RCF-V-007",
                                         key="v_parent")
            variant_letter = vcol2.selectbox("Variant #", VARIANT_LETTERS[1:], key="v_vlet")
            what_diff = vcol2.text_input("What's different?",
                                         placeholder="e.g. Changed visual hook", key="v_wdiff")
            ab_pair = vcol1.text_input("A/B Pair ID", placeholder="Other variant's Asset ID",
                                       key="v_abp")

        st.markdown("---")
        st.markdown("**Taxonomy**")
        cohorts = get_cohorts(product)
        angles  = get_angles(product)
        drivers = get_drivers(product)
        beliefs = get_beliefs(product)

        t1, t2, t3 = st.columns(3)
        cohort = t1.selectbox("Cohort *", cohorts, key="v_cohort")
        belief = t1.selectbox("Belief *", beliefs, key="v_belief")
        angle  = t2.selectbox("Marketing Angle *", angles, key="v_angle")
        driver = t2.selectbox("Situational Driver", drivers, key="v_driver")
        funnel = t3.selectbox("Funnel Stage *", FUNNEL_STAGES, key="v_funnel")
        mode   = t3.selectbox("Influence Mode *", INFLUENCE_MODES, key="v_mode")

        t4, t5, t6 = st.columns(3)
        hook = t4.selectbox("Hook Type *", HOOK_TYPES, key="v_hook")
        arc  = t5.selectbox("Emotional Arc *", EMOTIONAL_ARCS, key="v_arc")
        archetype = t6.selectbox("Creator Archetype *", ARCHETYPES, key="v_arch")

        cta = st.selectbox("CTA Style *", CTA_STYLES, key="v_cta")

        st.markdown("---")
        st.markdown("**People & source**")
        s1, s2 = st.columns(2)
        creator = s1.text_input("Creator / Consumer Name",
                                placeholder="e.g. Priyanka Yadav, or leave blank for AI",
                                key="v_creator")
        src_sel = s2.selectbox("Source Interview (if from consumer)",
                               source_opts, key="v_src")
        source_id = "" if src_sel == "None" else src_sel.split(" — ")[0]

        st.markdown("**Publishing**")
        p1, p2 = st.columns(2)
        campaign = p1.text_input("Meta Campaign Name", key="v_camp")
        adset    = p2.text_input("Meta Ad Set Name", key="v_adset")

        l1, l2 = st.columns(2)
        drive_link = l1.text_input("Drive Link (final asset)", key="v_drive")
        brief_link = l2.text_input("Brief / Source Link", key="v_brief")
        notes = st.text_area("Notes", height=70, key="v_notes")

        submitted_v = st.form_submit_button("✅ Log Video", type="primary",
                                            use_container_width=True)

        if submitted_v:
            if not ad_code.strip():
                st.error("AD CODE is required — we need it to link performance data.")
            else:
                asset_id = next_asset_id(product, "Video", existing_ids)
                row = {
                    "Asset ID": asset_id,
                    "AD CODE": ad_code.strip(),
                    "Published Date": pub_date.strftime("%Y-%m-%d") if pub_date else "",
                    "Parent Asset ID": parent_id,
                    "Variant #": variant_letter if is_variant else "A",
                    "What's Different": what_diff,
                    "A/B Pair ID": ab_pair,
                    "Product": product,
                    "Bucket": bucket,
                    "Format": "Video",
                    "Video Subtype": video_subtype,
                    "Static Subtype": "",
                    "Cohort": cohort,
                    "Belief": belief,
                    "Marketing Angle": angle,
                    "Situational Driver": driver,
                    "Funnel Stage": funnel,
                    "Influence Mode": mode,
                    "CTA Style": cta,
                    "Hook Type": hook,
                    "Emotional Arc": arc,
                    "Creator Archetype": archetype,
                    "Visual Style": "N/A — video",
                    "Creator / Consumer Name": creator,
                    "Source Interview ID": source_id,
                    "Experiment ID": "",
                    "Campaign Name": campaign,
                    "Ad Set Name": adset,
                    "Drive Link": drive_link,
                    "Brief Link": brief_link,
                    "Reference Image Link": "",
                    "Notes": notes,
                }
                try:
                    save_inhouse_live(row)
                    st.success(f"✅ Logged! Asset ID: **{asset_id}** — SyncWith will now "
                               "auto-populate performance via AD CODE `{ad_code.strip()}`.")
                except Exception as e:
                    st.error(f"Save failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# STATIC FLOW (from Stage-1 brief)
# ══════════════════════════════════════════════════════════════════════════════
with tab_static:
    st.subheader("Static asset promoted from a Stage-1 brief")
    st.caption("Pick the experiment brief you created, then add AD CODE + visual fields. "
               "Stage-1 taxonomy fields auto-fill.")

    pending = _stage1_pending()
    if not pending:
        st.info("No pending Stage-1 briefs. Create one in **Experiment Log → Stage 1 Brief** first, "
                "then come back here after publishing the static on Meta.")
        st.markdown("---")
        st.markdown("**Or log a static directly** (rare — bypasses the experiment trail):")
        use_direct = st.checkbox("I want to log a static without a Stage-1 brief")
        if not use_direct:
            st.stop()
        pending = []  # direct mode

    mode_exp = len(pending) > 0 and st.radio(
        "Source",
        ["From Stage-1 brief", "Direct (no brief)"],
        horizontal=True,
        key="s_mode",
    ) == "From Stage-1 brief"

    prefill = {}
    exp_id_sel = ""
    if mode_exp:
        exp_id_sel = st.selectbox("Pending Stage-1 brief", pending, key="s_exp")
        if exp_id_sel:
            row = exp_df[exp_df["Experiment ID"] == exp_id_sel].iloc[0]
            prefill = {
                "Product": row.get("Product", ""),
                "Cohort": row.get("Cohort", ""),
                "Belief": row.get("Belief", ""),
                "Marketing Angle": row.get("Marketing Angle", ""),
                "Situational Driver": row.get("Situational Driver", ""),
                "Funnel Stage": row.get("Funnel Stage", ""),
                "Reference Image Link": row.get("Reference Image Link", ""),
            }
            with st.expander("📄 Stage-1 brief preview", expanded=False):
                st.json(prefill)

    with st.form("log_static", clear_on_submit=True):
        default_product = prefill.get("Product") if prefill.get("Product") in PRODUCTS else PRODUCTS[0]
        c1, c2, c3 = st.columns(3)
        product = c1.selectbox("Product *", PRODUCTS,
                               index=PRODUCTS.index(default_product), key="s_product")
        static_subtype = c2.selectbox("Static Subtype *", STATIC_SUBTYPES, key="s_subtype")
        bucket = c3.selectbox("Bucket *", BUCKETS, key="s_bucket")

        c4, c5 = st.columns(2)
        ad_code = c4.text_input("AD CODE *", placeholder="e.g. AD 471", key="s_adcode")
        pub_date = c5.date_input("Published Date *", value=None, key="s_pubdate")

        st.markdown("---")
        st.markdown("**Taxonomy** (prefilled from brief — edit if needed)")

        cohorts = get_cohorts(product)
        angles  = get_angles(product)
        drivers = get_drivers(product)
        beliefs = get_beliefs(product)

        def _idx(lst, val, default=0):
            return lst.index(val) if val in lst else default

        t1, t2, t3 = st.columns(3)
        cohort = t1.selectbox("Cohort *", cohorts,
                              index=_idx(cohorts, prefill.get("Cohort", "")), key="s_cohort")
        belief = t1.selectbox("Belief *", beliefs,
                              index=_idx(beliefs, prefill.get("Belief", "")), key="s_belief")
        angle  = t2.selectbox("Marketing Angle *", angles,
                              index=_idx(angles, prefill.get("Marketing Angle", "")), key="s_angle")
        driver = t2.selectbox("Situational Driver", drivers,
                              index=_idx(drivers, prefill.get("Situational Driver", "")),
                              key="s_driver")
        funnel = t3.selectbox("Funnel Stage *", FUNNEL_STAGES,
                              index=_idx(FUNNEL_STAGES, prefill.get("Funnel Stage", "")),
                              key="s_funnel")
        mode   = t3.selectbox("Influence Mode *", INFLUENCE_MODES, key="s_mode_inf")

        t4, t5 = st.columns(2)
        visual = t4.selectbox("Visual Style *",
                              [v for v in VISUAL_STYLES if not v.startswith("N/A")],
                              key="s_vis")
        cta = t5.selectbox("CTA Style *", CTA_STYLES, key="s_cta")
        # Note: Hook Type + Emotional Arc + Creator Archetype intentionally omitted for statics

        st.markdown("---")
        st.markdown("**Publishing**")
        p1, p2 = st.columns(2)
        campaign = p1.text_input("Meta Campaign Name", key="s_camp")
        adset    = p2.text_input("Meta Ad Set Name", key="s_adset")

        l1, l2 = st.columns(2)
        drive_link = l1.text_input("Drive Link (final asset) *", key="s_drive")
        ref_link = l2.text_input("Reference Image Link",
                                 value=prefill.get("Reference Image Link", ""),
                                 placeholder="What you fed into Claude/MJ as inspiration",
                                 key="s_ref")
        brief_link = st.text_input("Brief / Source Link (optional)", key="s_brief")
        notes = st.text_area("Notes", height=70, key="s_notes")

        submitted_s = st.form_submit_button("✅ Log Static", type="primary",
                                            use_container_width=True)

        if submitted_s:
            if not ad_code.strip():
                st.error("AD CODE is required.")
            else:
                asset_id = next_asset_id(product, "Static", existing_ids)
                row = {
                    "Asset ID": asset_id,
                    "AD CODE": ad_code.strip(),
                    "Published Date": pub_date.strftime("%Y-%m-%d") if pub_date else "",
                    "Parent Asset ID": "",
                    "Variant #": "A",
                    "What's Different": "",
                    "A/B Pair ID": "",
                    "Product": product,
                    "Bucket": bucket,
                    "Format": "Static",
                    "Video Subtype": "",
                    "Static Subtype": static_subtype,
                    "Cohort": cohort,
                    "Belief": belief,
                    "Marketing Angle": angle,
                    "Situational Driver": driver,
                    "Funnel Stage": funnel,
                    "Influence Mode": mode,
                    "CTA Style": cta,
                    "Hook Type": "",
                    "Emotional Arc": "",
                    "Creator Archetype": "",
                    "Visual Style": visual,
                    "Creator / Consumer Name": "",
                    "Source Interview ID": "",
                    "Experiment ID": exp_id_sel if mode_exp else "",
                    "Campaign Name": campaign,
                    "Ad Set Name": adset,
                    "Drive Link": drive_link,
                    "Brief Link": brief_link,
                    "Reference Image Link": ref_link,
                    "Notes": notes,
                }
                try:
                    save_inhouse_live(row)
                    # Mark the Stage-1 brief as promoted
                    if mode_exp and exp_id_sel:
                        try:
                            from utils.sheets import _ws, EXPERIMENT_HEADERS
                            ws = _ws("Experiment_Log")
                            cell = ws.find(exp_id_sel)
                            if cell and "Promoted To Asset ID" in EXPERIMENT_HEADERS:
                                col = EXPERIMENT_HEADERS.index("Promoted To Asset ID") + 1
                                ws.update_cell(cell.row, col, asset_id)
                                col_status = EXPERIMENT_HEADERS.index("Status") + 1
                                ws.update_cell(cell.row, col_status, "Published")
                        except Exception as e:
                            st.warning(f"Saved the static, but couldn't mark the brief promoted: {e}")
                    st.success(f"✅ Logged! Asset ID: **{asset_id}**. "
                               f"Brief `{exp_id_sel}` marked as Promoted." if mode_exp
                               else f"✅ Logged! Asset ID: **{asset_id}**.")
                except Exception as e:
                    st.error(f"Save failed: {e}")
