from datetime import datetime

import streamlit as st

from utils.sheets import (
    load_assets,
    load_experiments,
    load_meta_ads,
    load_sources,
    next_asset_id,
    normalize_ad_code,
    save_asset,
    update_experiment,
)
from utils.taxonomy import (
    PRODUCTS, BUCKETS, FORMATS, VIDEO_SUBTYPES, STATIC_SUBTYPES,
    VISUAL_HOOK_TYPES, CONTENT_HOOK_TYPES, EMOTIONAL_ARCS, FUNNEL_STAGES,
    ARCHETYPES, INFLUENCE_MODES, VISUAL_TREATMENTS, CTA_FORMATS,
    CTA_MESSAGE_TYPES, STATIC_MESSAGE_TYPES, TAXONOMY_CONFIDENCE,
    AI_GENERATED_OPTIONS,
    VARIANT_LETTERS,
    get_cohorts, get_angles, get_drivers, get_beliefs, get_claims, product_label,
)


st.set_page_config(page_title="Log Live Asset - Creative OS", layout="wide")
st.title("Log Live Asset")
st.caption(
    "Use this only for in-house creatives. Videos are logged directly. Statics should usually be promoted from a Stage-1 brief."
)


def _idx(options: list[str], value: str, default: int = 0) -> int:
    return options.index(value) if value in options else default


def _meta_prefill(ad_code: str, meta_df):
    code = normalize_ad_code(ad_code)
    if not code or meta_df.empty or "AD CODE" not in meta_df.columns:
        return {}
    hit = meta_df[meta_df["AD CODE"].map(normalize_ad_code) == code]
    if hit.empty:
        return {}
    row = hit.iloc[-1]
    return {
        "Product": row.get("Product", ""),
        "Bucket": "Performance",
        "Creative Name": row.get("Creative Name", ""),
        "Creative Type": row.get("Creative Type", ""),
        "Marketing Angle": row.get("Marketing Angle", ""),
        "Funnel Stage": row.get("Funnel Level", ""),
        "Campaign Name": row.get("FB Ad Name", ""),
        "Drive Link": row.get("Creative Folder Link", "") or row.get("Creative Folder", ""),
        "Brief Link": row.get("Asana Link", ""),
        "Landing Page URL": row.get("Landing Page URL", ""),
    }


assets_df = load_assets()
experiments_df = load_experiments()
sources_df = load_sources()
meta_df = load_meta_ads()

existing_ids = assets_df["Asset ID"].dropna().astype(str).tolist() if not assets_df.empty and "Asset ID" in assets_df.columns else []
existing_codes = set()
if not assets_df.empty and "Meta Ad ID" in assets_df.columns:
    existing_codes = {
        normalize_ad_code(value)
        for value in assets_df["Meta Ad ID"].tolist()
        if normalize_ad_code(value)
    }

source_options = ["None"]
if not sources_df.empty:
    source_options += [
        f"{row.get('Source ID', '')} - {row.get('Consumer Name/Code', '')} ({row.get('Product', '')})"
        for _, row in sources_df.iterrows()
        if str(row.get("Source ID", "")).strip()
    ]


def _pending_experiments():
    if experiments_df.empty:
        return []
    df = experiments_df.copy()
    if "Promoted To Asset ID" in df.columns:
        df = df[df["Promoted To Asset ID"].astype(str).str.strip() == ""]
    if "Marketing Angle" in df.columns:
        df = df[df["Marketing Angle"].astype(str).str.strip() != ""]
    return df["Experiment ID"].dropna().astype(str).tolist() if "Experiment ID" in df.columns else []


tab_video, tab_static = st.tabs(["Log in-house video", "Promote static from Stage-1"])

with tab_video:
    st.subheader("In-house video went live")
    st.caption("Examples: consumer testimonial, founder-led, brand-led, skit, AI video.")

    ad_code_lookup = st.text_input("AD CODE to prefill from Meta Ads", placeholder="AD 482", key="video_lookup")
    meta_hint = _meta_prefill(ad_code_lookup, meta_df)
    if ad_code_lookup and meta_hint:
        st.success("Found this AD CODE in Meta Ads. Product, campaign, and links will prefill where possible.")
    elif ad_code_lookup:
        st.info("No Meta Ads match found yet. You can still log the asset; performance will connect when the code appears.")

    with st.form("video_live_form", clear_on_submit=True):
        top1, top2, top3 = st.columns(3)
        default_product = product_label(meta_hint.get("Product", ""))
        product = top1.selectbox("Product", PRODUCTS, index=_idx(PRODUCTS, default_product))
        video_subtype = top2.selectbox("Video subtype", VIDEO_SUBTYPES)
        bucket = top3.selectbox("Bucket", BUCKETS, index=_idx(BUCKETS, meta_hint.get("Bucket", "Performance")))

        live1, live2, live3 = st.columns(3)
        ad_code = live1.text_input("AD CODE", value=normalize_ad_code(ad_code_lookup), placeholder="AD 482")
        published_date = live2.date_input("Published date", value=datetime.now().date())
        status = live3.selectbox("Status", ["Published", "Live", "Testing", "Paused"], index=0)

        variant_left, variant_right = st.columns(2)
        is_variant = variant_left.checkbox("This is a variant / A-B test")
        parent_id = variant_left.text_input("Parent Asset ID", disabled=not is_variant)
        variant_letter = variant_right.selectbox("Variant #", VARIANT_LETTERS, index=0, disabled=not is_variant)
        what_diff = variant_right.text_input("What changed?", disabled=not is_variant)

        st.markdown("#### Taxonomy")
        cohorts = get_cohorts(product)
        beliefs = get_beliefs(product)
        angles = get_angles(product)
        drivers = get_drivers(product)

        tax1, tax2, tax3 = st.columns(3)
        cohort = tax1.selectbox("Cohort", cohorts)
        belief = tax1.selectbox("Belief", beliefs)
        angle = tax2.selectbox("Marketing angle", angles)
        driver = tax2.selectbox("Situational driver", drivers)
        funnel = tax3.selectbox("Funnel stage", FUNNEL_STAGES, index=_idx(FUNNEL_STAGES, meta_hint.get("Funnel Stage", "")))
        influence = tax3.selectbox("Influence mode", INFLUENCE_MODES)

        v1, v2, v3 = st.columns(3)
        visual_hook = v1.selectbox("Visual hook type", VISUAL_HOOK_TYPES)
        content_hook = v1.selectbox("Content hook type", CONTENT_HOOK_TYPES)
        arc = v2.selectbox("Emotional arc", EMOTIONAL_ARCS)
        archetype = v2.selectbox("Creator archetype", ARCHETYPES)
        cta_format = v3.selectbox("CTA format", CTA_FORMATS)
        cta_message = v3.selectbox("CTA message type", CTA_MESSAGE_TYPES)

        claim_codes = st.multiselect("Approved claim codes used", get_claims(product), default=["None"])
        taxonomy_confidence = st.selectbox("Taxonomy confidence", TAXONOMY_CONFIDENCE, index=0)

        st.markdown("#### Source and files")
        source1, source2 = st.columns(2)
        creator = source1.text_input("Creator / consumer name", value=meta_hint.get("Creative Name", ""))
        source_choice = source2.selectbox("Source story", source_options)
        source_id = "" if source_choice == "None" else source_choice.split(" - ", 1)[0]

        link1, link2, link3 = st.columns(3)
        drive_link = link1.text_input("Final asset / Drive link", value=meta_hint.get("Drive Link", ""))
        preview_link = link2.text_input("Preview asset link", value=meta_hint.get("Drive Link", ""))
        brief_link = link3.text_input("Brief / source link", value=meta_hint.get("Brief Link", ""))

        camp1, camp2 = st.columns(2)
        campaign = camp1.text_input("Campaign / FB ad name", value=meta_hint.get("Campaign Name", ""))
        adset = camp2.text_input("Ad set name")
        notes = st.text_area("Notes", height=80)

        submitted = st.form_submit_button("Save video to Master_Asset_Registry", type="primary", use_container_width=True)
        if submitted:
            normalized_code = normalize_ad_code(ad_code)
            if not normalized_code:
                st.error("AD CODE is required.")
            elif normalized_code in existing_codes:
                st.error(f"{normalized_code} already exists in Master_Asset_Registry.")
            else:
                asset_id = next_asset_id(product, "Video", existing_ids)
                row = {
                    "Asset ID": asset_id,
                    "Parent Asset ID": parent_id if is_variant else "",
                    "Variant #": variant_letter if is_variant else "A",
                    "What's Different": what_diff if is_variant else "",
                    "Status": status,
                    "Created Date": datetime.now().strftime("%Y-%m-%d"),
                    "Published Date": published_date.strftime("%Y-%m-%d") if published_date else "",
                    "Product": product,
                    "Bucket": bucket,
                    "Channel": "In-house",
                    "Creative Type": video_subtype,
                    "Format": "Video",
                    "Video Subtype": video_subtype,
                    "Static Subtype": "",
                    "Cohort": cohort,
                    "Belief": belief,
                    "Marketing Angle": angle,
                    "Situational Driver": driver,
                    "Hook Type": content_hook,
                    "Visual Hook Type": visual_hook,
                    "Content Hook Type": content_hook,
                    "Emotional Arc": arc,
                    "Funnel Stage": funnel,
                    "Creator Archetype": archetype,
                    "Influence Mode": influence,
                    "Visual Style": "N/A - video",
                    "Visual Treatment": "",
                    "CTA Style": cta_message,
                    "CTA Format": cta_format,
                    "CTA Message Type": cta_message,
                    "Static Message Type": "",
                    "AI-Generated": "",
                    "Taxonomy Confidence": taxonomy_confidence,
                    "Claim Codes": ", ".join([c for c in claim_codes if c != "None"]),
                    "Source Interview ID": source_id,
                    "Creator / Consumer Name": creator,
                    "Meta Ad ID": normalized_code,
                    "Campaign Name": campaign,
                    "Ad Set Name": adset,
                    "Drive Link": drive_link,
                    "Preview Asset Link": preview_link,
                    "Source Folder Link": drive_link,
                    "Brief Link": brief_link,
                    "Notes": notes,
                    "Taxonomy Review Status": "Tagged",
                }
                try:
                    save_asset(row)
                    st.success(f"Saved {asset_id} to Master_Asset_Registry.")
                except Exception as exc:
                    st.error(f"Save failed: {exc}")

with tab_static:
    st.subheader("In-house static/carousel went live")
    st.caption("Pick the Stage-1 brief, then add AD CODE and the final creative link.")

    pending = _pending_experiments()
    if not pending:
        st.info("No pending Stage-1 briefs found. You can still use direct mode below.")

    mode = st.radio("Static logging mode", ["From Stage-1 brief", "Direct static"], horizontal=True)
    use_brief = mode == "From Stage-1 brief" and bool(pending)

    prefill = {}
    experiment_id = ""
    if use_brief:
        experiment_id = st.selectbox("Stage-1 brief", pending)
        exp_row = experiments_df[experiments_df["Experiment ID"].astype(str) == experiment_id].iloc[0]
        prefill = {
            "Product": exp_row.get("Product", ""),
            "Cohort": exp_row.get("Cohort", ""),
            "Belief": exp_row.get("Belief", ""),
            "Marketing Angle": exp_row.get("Marketing Angle", ""),
            "Situational Driver": exp_row.get("Situational Driver", ""),
            "Funnel Stage": exp_row.get("Funnel Stage", ""),
            "Static Subtype": exp_row.get("Static Subtype", ""),
            "Visual Hook Type": exp_row.get("Visual Hook Type", ""),
            "Content Hook Type": exp_row.get("Content Hook Type", ""),
            "Visual Treatment": exp_row.get("Visual Treatment", ""),
            "Static Message Type": exp_row.get("Static Message Type", ""),
            "CTA Format": exp_row.get("CTA Format", ""),
            "CTA Message Type": exp_row.get("CTA Message Type", ""),
            "AI-Generated": exp_row.get("AI-Generated", ""),
            "Taxonomy Confidence": exp_row.get("Taxonomy Confidence", ""),
            "Primary Proof Needed": exp_row.get("Primary Proof Needed", ""),
            "Reference Image Link": exp_row.get("Reference Image Link", ""),
            "Notes": exp_row.get("Hypothesis", ""),
        }
        with st.expander("Stage-1 brief preview", expanded=False):
            st.json(prefill)

    ad_code_lookup = st.text_input("AD CODE to prefill from Meta Ads", placeholder="AD 512", key="static_lookup")
    meta_hint = _meta_prefill(ad_code_lookup, meta_df)

    with st.form("static_live_form", clear_on_submit=True):
        default_product = product_label(prefill.get("Product") or meta_hint.get("Product", ""))
        top1, top2, top3 = st.columns(3)
        product = top1.selectbox("Product", PRODUCTS, index=_idx(PRODUCTS, default_product))
        static_subtype = top2.selectbox("Static subtype", STATIC_SUBTYPES, index=_idx(STATIC_SUBTYPES, prefill.get("Static Subtype", "")))
        bucket = top3.selectbox("Bucket", BUCKETS, index=_idx(BUCKETS, meta_hint.get("Bucket", "Performance")))

        live1, live2, live3 = st.columns(3)
        ad_code = live1.text_input("AD CODE", value=normalize_ad_code(ad_code_lookup), placeholder="AD 512")
        published_date = live2.date_input("Published date", value=datetime.now().date(), key="static_pub")
        status = live3.selectbox("Status", ["Published", "Live", "Testing", "Paused"], index=0, key="static_status")

        cohorts = get_cohorts(product)
        beliefs = get_beliefs(product)
        angles = get_angles(product)
        drivers = get_drivers(product)

        tax1, tax2, tax3 = st.columns(3)
        cohort = tax1.selectbox("Cohort", cohorts, index=_idx(cohorts, prefill.get("Cohort", "")))
        belief = tax1.selectbox("Belief", beliefs, index=_idx(beliefs, prefill.get("Belief", "")))
        angle = tax2.selectbox("Marketing angle", angles, index=_idx(angles, prefill.get("Marketing Angle", "")))
        driver = tax2.selectbox("Situational driver", drivers, index=_idx(drivers, prefill.get("Situational Driver", "")))
        funnel = tax3.selectbox("Funnel stage", FUNNEL_STAGES, index=_idx(FUNNEL_STAGES, prefill.get("Funnel Stage", "") or meta_hint.get("Funnel Stage", "")))
        influence = tax3.selectbox("Influence mode", INFLUENCE_MODES)

        vis1, vis2, vis3 = st.columns(3)
        visual_hook = vis1.selectbox("Visual hook type", VISUAL_HOOK_TYPES, index=_idx(VISUAL_HOOK_TYPES, prefill.get("Visual Hook Type", "")))
        content_hook = vis1.selectbox("Content hook / headline type", CONTENT_HOOK_TYPES, index=_idx(CONTENT_HOOK_TYPES, prefill.get("Content Hook Type", "")))
        visual_treatment = vis2.selectbox("Visual treatment", VISUAL_TREATMENTS, index=_idx(VISUAL_TREATMENTS, prefill.get("Visual Treatment", "")))
        static_message = vis2.selectbox("Static message type", STATIC_MESSAGE_TYPES, index=_idx(STATIC_MESSAGE_TYPES, prefill.get("Static Message Type", "")))
        cta_format = vis3.selectbox("CTA format", CTA_FORMATS, index=_idx(CTA_FORMATS, prefill.get("CTA Format", "")))
        cta_message = vis3.selectbox("CTA message type", CTA_MESSAGE_TYPES, index=_idx(CTA_MESSAGE_TYPES, prefill.get("CTA Message Type", "")))

        extra1, extra2, extra3 = st.columns(3)
        ai_generated = extra1.selectbox("AI-generated?", AI_GENERATED_OPTIONS, index=_idx(AI_GENERATED_OPTIONS, prefill.get("AI-Generated", "No")))
        taxonomy_confidence = extra2.selectbox("Taxonomy confidence", TAXONOMY_CONFIDENCE, index=_idx(TAXONOMY_CONFIDENCE, prefill.get("Taxonomy Confidence", "Medium")))
        claim_codes = extra3.multiselect("Approved claim codes used", get_claims(product), default=["None"])

        link1, link2, link3 = st.columns(3)
        drive_link = link1.text_input("Final static / Drive link", value=meta_hint.get("Drive Link", ""))
        preview_link = link2.text_input("Preview image link", value=meta_hint.get("Drive Link", ""))
        reference_link = link3.text_input("Reference image link", value=prefill.get("Reference Image Link", ""))

        brief_link = st.text_input("Brief / Asana link", value=meta_hint.get("Brief Link", ""))
        campaign = st.text_input("Campaign / FB ad name", value=meta_hint.get("Campaign Name", ""))
        notes = st.text_area("Notes", value=prefill.get("Notes", ""), height=80)

        submitted = st.form_submit_button("Save static to Master_Asset_Registry", type="primary", use_container_width=True)
        if submitted:
            normalized_code = normalize_ad_code(ad_code)
            if not normalized_code:
                st.error("AD CODE is required.")
            elif normalized_code in existing_codes:
                st.error(f"{normalized_code} already exists in Master_Asset_Registry.")
            else:
                asset_id = next_asset_id(product, "Static", existing_ids)
                row = {
                    "Asset ID": asset_id,
                    "Variant #": "A",
                    "Status": status,
                    "Created Date": datetime.now().strftime("%Y-%m-%d"),
                    "Published Date": published_date.strftime("%Y-%m-%d") if published_date else "",
                    "Product": product,
                    "Bucket": bucket,
                    "Channel": "In-house",
                    "Creative Type": static_subtype,
                    "Format": "Static",
                    "Video Subtype": "",
                    "Static Subtype": static_subtype,
                    "Cohort": cohort,
                    "Belief": belief,
                    "Marketing Angle": angle,
                    "Situational Driver": driver,
                    "Hook Type": content_hook,
                    "Visual Hook Type": visual_hook,
                    "Content Hook Type": content_hook,
                    "Funnel Stage": funnel,
                    "Influence Mode": influence,
                    "Visual Style": visual_treatment,
                    "Visual Treatment": visual_treatment,
                    "CTA Style": cta_message,
                    "CTA Format": cta_format,
                    "CTA Message Type": cta_message,
                    "Static Message Type": static_message,
                    "AI-Generated": ai_generated,
                    "Taxonomy Confidence": taxonomy_confidence,
                    "Claim Codes": ", ".join([c for c in claim_codes if c != "None"]),
                    "Experiment ID": experiment_id if use_brief else "",
                    "Meta Ad ID": normalized_code,
                    "Campaign Name": campaign,
                    "Drive Link": drive_link,
                    "Preview Asset Link": preview_link,
                    "Source Folder Link": drive_link,
                    "Brief Link": brief_link,
                    "Reference Image Link": reference_link,
                    "Notes": notes,
                    "Taxonomy Review Status": "Tagged",
                }
                try:
                    save_asset(row)
                    if use_brief and experiment_id:
                        update_experiment(experiment_id, {"Promoted To Asset ID": asset_id, "Status": "Published"})
                    st.success(f"Saved {asset_id} to Master_Asset_Registry.")
                except Exception as exc:
                    st.error(f"Save failed: {exc}")
