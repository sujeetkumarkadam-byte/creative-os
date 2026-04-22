import streamlit as st
from datetime import datetime
from utils.sheets import load_assets, load_sources, load_experiments, save_asset, next_asset_id
from utils.taxonomy import (
    PRODUCTS, BUCKETS, CHANNELS, CREATIVE_TYPES, VIDEO_TYPES,
    HOOK_TYPES, EMOTIONAL_ARCS, FUNNEL_STAGES,
    ARCHETYPES, INFLUENCE_MODES, VISUAL_STYLES, CTA_STYLES,
    STATUSES, VARIANT_LETTERS,
    get_cohorts, get_angles, get_drivers, get_beliefs,
)

st.set_page_config(page_title="Log Asset — Creative OS", layout="wide")
st.title("Log New Asset")
st.caption("One row = one asset. Fill in all required fields, then hit Log Asset.")

assets_df    = load_assets()
sources_df   = load_sources()
experiments_df = load_experiments()

existing_ids = assets_df["Asset ID"].tolist() if not assets_df.empty else []

source_opts = ["None"] + (
    [f"{r['Source ID']} — {r['Consumer Name/Code']} ({r['Product']})"
     for _, r in sources_df.iterrows()]
    if not sources_df.empty else []
)

exp_opts = ["None"] + (
    [f"{r['Experiment ID']} — {r['Core Message']}"
     for _, r in experiments_df.iterrows()]
    if not experiments_df.empty else []
)

with st.form("log_asset", clear_on_submit=True):

    # ── 1. WHAT IS THIS ───────────────────────────────────────────────
    st.subheader("1. What is this?")
    c1, c2, c3 = st.columns(3)
    product       = c1.selectbox("Product *", PRODUCTS)
    creative_type = c2.selectbox("Creative Type *", CREATIVE_TYPES)
    bucket        = c3.selectbox("Bucket *", BUCKETS)

    c4, c5 = st.columns(2)
    channel = c4.selectbox("Channel *", CHANNELS)
    status  = c5.selectbox("Status", STATUSES, index=1)

    is_video = creative_type in VIDEO_TYPES

    # ── 2. VARIANT ────────────────────────────────────────────────────
    st.subheader("2. Is this a variant?")
    is_variant = st.radio(
        "Variant?",
        ["No — original asset", "Yes — variant of an existing asset"],
        horizontal=True,
        label_visibility="collapsed",
    )

    parent_id, variant_letter, what_diff, ab_pair = "", "A", "", ""
    if is_variant.startswith("Yes"):
        cv1, cv2 = st.columns(2)
        parent_id     = cv1.text_input("Parent Asset ID *", placeholder="e.g. RCF-V-001")
        variant_letter = cv1.selectbox("Variant Letter *", VARIANT_LETTERS[1:])
        what_diff      = cv2.text_area("What's different? *",
                                       placeholder="e.g. Changed hook from Title Super to Pain Statement",
                                       height=80)
        ab_pair        = cv2.text_input("A/B Pair ID", placeholder="Asset ID of the other variant")

    # ── 3. TAXONOMY ───────────────────────────────────────────────────
    st.subheader("3. Taxonomy tags")

    cohorts = get_cohorts(product)
    angles  = get_angles(product)
    drivers = get_drivers(product)
    beliefs = get_beliefs(product)

    t1, t2, t3 = st.columns(3)
    cohort   = t1.selectbox("Cohort *", cohorts)
    belief   = t1.selectbox("Belief *", beliefs)
    angle    = t2.selectbox("Marketing Angle *", angles)
    driver   = t2.selectbox("Situational Driver", drivers)
    funnel   = t3.selectbox("Funnel Stage *", FUNNEL_STAGES)
    mode     = t3.selectbox("Influence Mode *", INFLUENCE_MODES)

    t4, t5, t6 = st.columns(3)
    hook      = t4.selectbox("Hook Type *", HOOK_TYPES)
    arc       = t5.selectbox("Emotional Arc *", EMOTIONAL_ARCS)
    cta       = t6.selectbox("CTA Style *", CTA_STYLES)

    t7, t8 = st.columns(2)
    archetype = t7.selectbox("Creator Archetype *", ARCHETYPES)

    if is_video:
        t8.selectbox("Visual Style", ["N/A — video"], disabled=True)
        visual = "N/A — video"
    else:
        visual = t8.selectbox("Visual Style *", VISUAL_STYLES)

    # ── 4. SOURCE / CREATOR ───────────────────────────────────────────
    st.subheader("4. Source & creator")
    source_id, creator = "", ""

    if creative_type == "Consumer Testimonial":
        s1, s2 = st.columns(2)
        src_sel   = s1.selectbox("Source Interview *", source_opts)
        source_id = "" if src_sel == "None" else src_sel.split(" — ")[0]
        creator   = s2.text_input("Consumer Name / Code *",
                                   placeholder="e.g. Priya S. or Anon-047")
    else:
        creator = st.text_input("Creator Name",
                                placeholder="Leave blank if AI-generated")

    # ── 5. EXPERIMENT LINK ────────────────────────────────────────────
    st.subheader("5. Experiment link (optional)")
    exp_sel    = st.selectbox("Linked Experiment", exp_opts)
    experiment = "" if exp_sel == "None" else exp_sel.split(" — ")[0]

    # ── 6. PUBLISHING ─────────────────────────────────────────────────
    st.subheader("6. Publishing")
    p1, p2 = st.columns(2)
    pub_date   = p1.date_input("Published Date", value=None)
    meta_ad_id = p1.text_input("Meta Ad ID",
                                placeholder="Add after publishing — SyncWith uses this")
    campaign   = p2.text_input("Meta Campaign Name")
    adset      = p2.text_input("Meta Ad Set Name")

    l1, l2 = st.columns(2)
    drive_link = l1.text_input("Drive Link (Final Asset)")
    brief_link = l2.text_input("Brief / Source Link")
    notes      = st.text_area("Notes", height=70)

    # ── SUBMIT ────────────────────────────────────────────────────────
    st.markdown("---")
    submitted = st.form_submit_button("✅ Log Asset", type="primary", use_container_width=True)

    if submitted:
        asset_id = next_asset_id(product, creative_type, existing_ids)

        row = {
            "Asset ID":               asset_id,
            "Parent Asset ID":        parent_id,
            "Variant #":              variant_letter if is_variant.startswith("Yes") else "A",
            "What's Different":       what_diff,
            "A/B Pair ID":            ab_pair,
            "Status":                 status,
            "Created Date":           datetime.now().strftime("%Y-%m-%d"),
            "Published Date":         pub_date.strftime("%Y-%m-%d") if pub_date else "",
            "Product":                product,
            "Bucket":                 bucket,
            "Channel":                channel,
            "Creative Type":          creative_type,
            "Cohort":                 cohort,
            "Belief":                 belief,
            "Marketing Angle":        angle,
            "Situational Driver":     driver,
            "Hook Type":              hook,
            "Emotional Arc":          arc,
            "Funnel Stage":           funnel,
            "Creator Archetype":      archetype,
            "Influence Mode":         mode,
            "Visual Style":           visual,
            "CTA Style":              cta,
            "Source Interview ID":    source_id,
            "Creator / Consumer Name": creator,
            "Experiment ID":          experiment,
            "Meta Ad ID":             meta_ad_id,
            "Campaign Name":          campaign,
            "Ad Set Name":            adset,
            "Drive Link":             drive_link,
            "Brief Link":             brief_link,
            "Notes":                  notes,
        }

        try:
            save_asset(row)
            st.success(f"✅ Logged! Asset ID: **{asset_id}**")
            if not meta_ad_id:
                st.info("💡 Once you publish on Meta, add the Meta Ad ID here — SyncWith will then auto-populate all performance columns.")
        except Exception as e:
            st.error(f"Save failed: {e}")
