import streamlit as st
import pandas as pd
from datetime import datetime
from utils.sheets import (
    unimported_meta_candidates, load_inhouse_live, save_inhouse_live,
    next_asset_id, INHOUSE_LIVE_HEADERS,
)
from utils.taxonomy import (
    PRODUCTS, FORMATS, VIDEO_SUBTYPES, STATIC_SUBTYPES,
    HOOK_TYPES, EMOTIONAL_ARCS, FUNNEL_STAGES,
    ARCHETYPES, INFLUENCE_MODES, VISUAL_STYLES, CTA_STYLES,
    get_cohorts, get_angles, get_drivers, get_beliefs,
)

st.set_page_config(page_title="Batch Tag Backlog — Creative OS", layout="wide")
st.title("Batch Tag Backlog (one-time)")
st.caption(
    "Pulls every Meta Ads row whose AD CODE isn't yet in Inhouse_Live_Assets or "
    "Live Entries 2026. Use this ONCE to retro-tag your ~40 backlog inhouse assets. "
    "After this, log videos directly via *Log Live Asset → Video* and statics via "
    "*Stage-1 Brief → promote to live*."
)

# ── LOAD POOL ────────────────────────────────────────────────────────────────
if "batch_pool" not in st.session_state:
    st.session_state.batch_pool = None

col_a, col_b = st.columns([1, 3])
if col_a.button("🔄 Load / refresh pool", type="primary"):
    with st.spinner("Scanning Meta Ads…"):
        st.session_state.batch_pool = unimported_meta_candidates()

pool = st.session_state.batch_pool
if pool is None:
    st.info("Click **Load / refresh pool** to scan Meta Ads for untagged inhouse candidates.")
    st.stop()

if pool.empty:
    st.success("Nothing to tag — every Meta ad is already in Inhouse or Influencer.")
    st.stop()

st.markdown(f"**{len(pool)}** rows in the pool (Porcellia + untagged). "
            "Filter below, then pick one to tag as Inhouse.")

# ── SEARCH / FILTER POOL ─────────────────────────────────────────────────────
search = col_b.text_input("🔎 Search Creative Name / AD CODE / FB Ad Name", "")
f = pool.copy()
if search.strip():
    s = search.strip().lower()
    hit_cols = [c for c in ["Creative Name", "AD CODE", "FB Ad Name"] if c in f.columns]
    mask = pd.Series(False, index=f.index)
    for c in hit_cols:
        mask = mask | f[c].astype(str).str.lower().str.contains(s, na=False)
    f = f[mask]

preview_cols = [c for c in [
    "AD CODE", "Creative Name", "Creative Type", "Product", "Funnel Level",
    "Content Bucket", "Marketing Angle", "Date [Ad Taken Live]", "Status",
    "Creative Folder", "FB Ad Name",
] if c in f.columns]
st.dataframe(f[preview_cols], use_container_width=True, hide_index=True, height=220)

# ── PICK A ROW TO TAG ────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Tag one row as Inhouse")

code_options = f["AD CODE"].astype(str).tolist() if "AD CODE" in f.columns else []
if not code_options:
    st.info("No AD CODEs in current filter.")
    st.stop()

chosen_code = st.selectbox("AD CODE", ["— pick one —"] + code_options)
if chosen_code == "— pick one —":
    st.stop()

row = f[f["AD CODE"].astype(str) == chosen_code].iloc[0]

# Prefills from Meta Ads row
prefill_product = str(row.get("Product", "")).strip()
prefill_ctype = str(row.get("Creative Type", "")).strip().lower()
prefill_angle = str(row.get("Marketing Angle", "")).strip()
prefill_funnel = str(row.get("Funnel Level", "")).strip()
prefill_bucket = str(row.get("Content Bucket", "")).strip()
prefill_drive = str(row.get("Creative Folder", "")).strip()
prefill_name = str(row.get("Creative Name", "")).strip()
prefill_date = str(row.get("Date [Ad Taken Live]", "")).strip()

# Guess Format
if any(v in prefill_ctype for v in ["video", "reel", "testimonial"]):
    guess_format = "Video"
elif prefill_ctype:
    guess_format = "Static"
else:
    guess_format = "Video"

st.info(
    f"**Prefilled from Meta Ads:**  "
    f"Creative Name: `{prefill_name}`  |  Meta Creative Type: `{prefill_ctype or '—'}`  |  "
    f"Product: `{prefill_product or '—'}`  |  Funnel: `{prefill_funnel or '—'}`  |  "
    f"Angle: `{prefill_angle or '—'}`  |  Drive: "
    + (f"[open]({prefill_drive})" if prefill_drive else "`—`")
)

with st.form("tag_form", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    product = c1.selectbox("Product *", PRODUCTS,
                           index=PRODUCTS.index(prefill_product) if prefill_product in PRODUCTS else 0)
    fmt = c2.selectbox("Format *", FORMATS,
                       index=FORMATS.index(guess_format) if guess_format in FORMATS else 0)
    pub_date_raw = c3.text_input("Published Date", value=prefill_date,
                                 help="YYYY-MM-DD preferred; whatever's in Meta Ads is fine.")

    if fmt == "Video":
        subtype = st.selectbox("Video Subtype *", VIDEO_SUBTYPES)
        static_subtype = ""
    else:
        static_subtype = st.selectbox("Static Subtype *", STATIC_SUBTYPES)
        subtype = ""

    cohorts = get_cohorts(product)
    beliefs = get_beliefs(product)
    angles  = get_angles(product)
    drivers = get_drivers(product)

    t1, t2 = st.columns(2)
    cohort = t1.selectbox("Cohort *", cohorts)
    belief = t1.selectbox("Belief *", beliefs)
    angle  = t2.selectbox("Marketing Angle *", angles)
    driver = t2.selectbox("Situational Driver", drivers)

    u1, u2, u3 = st.columns(3)
    funnel = u1.selectbox("Funnel Stage", FUNNEL_STAGES,
                          index=next((i for i, x in enumerate(FUNNEL_STAGES)
                                      if prefill_funnel.lower() in x.lower()), 0))
    influence = u2.selectbox("Influence Mode", INFLUENCE_MODES)
    cta = u3.selectbox("CTA Style", CTA_STYLES)

    # Format-specific extras
    if fmt == "Video":
        v1, v2, v3 = st.columns(3)
        hook = v1.selectbox("Hook Type", HOOK_TYPES)
        arc  = v2.selectbox("Emotional Arc", EMOTIONAL_ARCS)
        arch = v3.selectbox("Creator Archetype", ARCHETYPES)
        visual_style = ""
    else:
        visual_style = st.selectbox("Visual Style", VISUAL_STYLES)
        hook = arc = arch = ""

    creator = st.text_input("Creator / Consumer Name", value=prefill_name)
    drive_link = st.text_input("Drive Link", value=prefill_drive)
    notes = st.text_area("Notes", value=f"Retro-tagged from Meta Ads backlog. "
                                        f"Bucket: {prefill_bucket}. Meta CT: {prefill_ctype}.")

    submit = st.form_submit_button("💾 Save as Inhouse Live Asset", type="primary",
                                   use_container_width=True)

    if submit:
        inhouse_now = load_inhouse_live()
        existing_ids = inhouse_now["Asset ID"].tolist() if not inhouse_now.empty else []
        # Guard: don't double-write the same AD CODE
        if not inhouse_now.empty and "AD CODE" in inhouse_now.columns:
            if chosen_code.strip().upper() in set(
                inhouse_now["AD CODE"].astype(str).str.strip().str.upper()
            ):
                st.error(f"AD CODE `{chosen_code}` is already in Inhouse_Live_Assets. Skipping.")
                st.stop()

        aid = next_asset_id(product, fmt, existing_ids)
        data = {h: "" for h in INHOUSE_LIVE_HEADERS}
        data.update({
            "Asset ID": aid,
            "AD CODE": chosen_code,
            "Published Date": pub_date_raw,
            "Product": product,
            "Bucket": prefill_bucket or "Performance",
            "Format": fmt,
            "Video Subtype": subtype,
            "Static Subtype": static_subtype,
            "Cohort": cohort,
            "Belief": belief,
            "Marketing Angle": angle,
            "Situational Driver": driver,
            "Funnel Stage": funnel,
            "Influence Mode": influence,
            "CTA Style": cta,
            "Hook Type": hook,
            "Emotional Arc": arc,
            "Creator Archetype": arch,
            "Visual Style": visual_style,
            "Creator / Consumer Name": creator,
            "Drive Link": drive_link,
            "Notes": notes,
        })
        try:
            save_inhouse_live(data)
            st.success(f"✅ Saved `{aid}` (AD CODE `{chosen_code}`). Refresh the pool to continue.")
            st.balloons()
            # Drop the saved row from session pool so it vanishes from UI
            if st.session_state.batch_pool is not None:
                st.session_state.batch_pool = st.session_state.batch_pool[
                    st.session_state.batch_pool["AD CODE"].astype(str) != chosen_code
                ]
        except Exception as e:
            st.error(f"Save failed: {e}")
