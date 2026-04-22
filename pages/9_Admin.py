import pandas as pd
import streamlit as st

from utils.sheets import (
    _client,
    _ws,
    EXPERIMENT_HEADERS,
    INHOUSE_LIVE_HEADERS,
    SHEET_ASSETS,
    SHEET_INHOUSE,
    backlog_tag_candidates,
    build_classified_meta_view,
    ensure_inhouse_sheet,
    load_inhouse_live,
    migrate_master_to_inhouse,
    next_asset_id,
    normalize_ad_code,
    save_inhouse_live,
)
from utils.taxonomy import (
    CTA_STYLES,
    FORMATS,
    HOOK_TYPES,
    EMOTIONAL_ARCS,
    FUNNEL_STAGES,
    ARCHETYPES,
    INFLUENCE_MODES,
    PRODUCTS,
    STATIC_SUBTYPES,
    VIDEO_SUBTYPES,
    VISUAL_STYLES,
    get_angles,
    get_beliefs,
    get_cohorts,
    get_drivers,
)

st.set_page_config(page_title="Admin / Diagnostics — Creative OS", layout="wide")
st.title("Admin / Diagnostics")
st.caption("Sheet inspection, one-off migration, and retro-tagging for already-live inhouse backlog assets.")

st.header("1. Spreadsheet schema")
if st.button("🔍 Scan all tabs", type="primary"):
    try:
        ss = _client().open(st.secrets["spreadsheet_name"])
        worksheets = ss.worksheets()
        st.success(f"Found **{len(worksheets)}** tabs in *{st.secrets['spreadsheet_name']}*")

        for ws in worksheets:
            with st.expander(f"📄 **{ws.title}** — {ws.row_count:,} rows × {ws.col_count} cols", expanded=False):
                raw = ws.get_values("A1:BU5")
                if not raw:
                    st.info("Empty sheet.")
                    continue

                st.markdown("**First 5 rows**")
                st.dataframe(pd.DataFrame(raw), use_container_width=True, hide_index=True)

                for idx in [0, 1]:
                    if idx < len(raw):
                        headers = [header for header in raw[idx] if str(header).strip()]
                        if headers:
                            st.markdown(f"**Detected headers (row {idx + 1})**")
                            st.code(" | ".join(headers), language=None)
                            break
    except Exception as exc:
        st.error(f"Scan failed: {exc}")

st.markdown("---")
st.header("2. One-off migrations")

st.markdown(f"**Create `{SHEET_INHOUSE}`**")
if st.button("🏗️ Create Inhouse_Live_Assets sheet"):
    try:
        created = ensure_inhouse_sheet()
        if created:
            st.success(f"Created `{SHEET_INHOUSE}`.")
        else:
            st.info(f"`{SHEET_INHOUSE}` already exists.")
    except Exception as exc:
        st.error(f"Failed: {exc}")

st.markdown(f"**Migrate `{SHEET_ASSETS}` → `{SHEET_INHOUSE}`**")
st.caption("Use this only once. Clicking it repeatedly will duplicate rows.")
confirm = st.checkbox("I understand this should only be run once")
if st.button("📦 Run migration", disabled=not confirm):
    try:
        with st.spinner("Migrating legacy rows..."):
            migrated, skipped, errors = migrate_master_to_inhouse()
        st.success(f"Migrated {migrated} rows. Skipped {skipped}.")
        if errors:
            st.warning("Some rows failed:")
            for error in errors:
                st.write(f"- {error}")
    except Exception as exc:
        st.error(f"Migration failed: {exc}")

st.markdown("---")
st.header("3. Retro-tag already-live inhouse backlog")
st.caption(
    "This is only for historical inhouse ads that are already live in Meta Ads but still missing taxonomy "
    "inside Inhouse_Live_Assets. New content should not go through here."
)

if st.button("🔄 Load backlog candidates"):
    st.session_state.admin_backlog = backlog_tag_candidates()

backlog = st.session_state.get("admin_backlog")
if backlog is None:
    st.info("Click **Load backlog candidates** to scan Meta Ads for residual live ads that are not yet tagged as Inhouse or Influencer.")
else:
    if backlog.empty:
        st.success("No backlog candidates found.")
    else:
        st.write(
            f"Found **{len(backlog)}** live Meta Ads rows that are currently residual "
            "(Porcellia or unclassified). Pick the ones that are actually inhouse and tag them here."
        )

        search = st.text_input("Search backlog", placeholder="AD CODE, creative name, product...")
        pool = backlog.copy()
        if search.strip():
            term = search.strip().lower()
            hit_cols = [
                column for column in [
                    "AD CODE", "Creative Name Derived", "Product Derived",
                    "Meta Creative Type", "Meta Creative Folder",
                ] if column in pool.columns
            ]
            mask = pd.Series(False, index=pool.index)
            for column in hit_cols:
                mask = mask | pool[column].astype(str).str.lower().str.contains(term, na=False)
            pool = pool[mask]

        preview_cols = [
            "AD CODE", "_Date", "Creative Name Derived", "Product Derived",
            "Meta Creative Type", "Meta Marketing Angle", "Meta Creative Folder",
        ]
        preview = pool[[column for column in preview_cols if column in pool.columns]].copy()
        preview = preview.rename(
            columns={
                "_Date": "Live Date",
                "Creative Name Derived": "Creative Name",
                "Product Derived": "Product",
                "Meta Creative Type": "Meta Creative Type",
                "Meta Marketing Angle": "Meta Marketing Angle",
                "Meta Creative Folder": "Meta Creative Folder",
            }
        )
        st.dataframe(preview.sort_values("Live Date", ascending=False), use_container_width=True, hide_index=True, height=260)

        code_options = pool["AD CODE"].dropna().astype(str).tolist()
        if code_options:
            chosen_code = st.selectbox("Choose AD CODE to tag", code_options)
            picked = pool[pool["AD CODE"].astype(str) == chosen_code].iloc[0]

            st.info(
                f"Creative: `{picked.get('Creative Name Derived', '—')}`  |  "
                f"Product: `{picked.get('Product Derived', '—')}`  |  "
                f"Meta type: `{picked.get('Meta Creative Type', '—')}`"
            )

            with st.form("retro_tag_form", clear_on_submit=True):
                default_product = picked.get("Product Derived", "")
                if default_product not in PRODUCTS:
                    default_product = PRODUCTS[0]

                top1, top2, top3 = st.columns(3)
                product = top1.selectbox("Product *", PRODUCTS, index=PRODUCTS.index(default_product))
                format_guess = picked.get("Format Derived", "") if picked.get("Format Derived", "") in FORMATS else FORMATS[0]
                fmt = top2.selectbox("Format *", FORMATS, index=FORMATS.index(format_guess))
                published_date = top3.text_input(
                    "Published Date",
                    value=picked.get("_Date").strftime("%Y-%m-%d") if pd.notna(picked.get("_Date")) else "",
                )

                if fmt == "Video":
                    video_subtype = st.selectbox("Video Subtype *", VIDEO_SUBTYPES)
                    static_subtype = ""
                else:
                    video_subtype = ""
                    static_subtype = st.selectbox("Static Subtype *", STATIC_SUBTYPES)

                cohorts = get_cohorts(product)
                beliefs = get_beliefs(product)
                angles = get_angles(product)
                drivers = get_drivers(product)

                mid1, mid2, mid3 = st.columns(3)
                cohort = mid1.selectbox("Cohort *", cohorts)
                belief = mid1.selectbox("Belief *", beliefs)
                angle = mid2.selectbox("Marketing Angle *", angles)
                driver = mid2.selectbox("Situational Driver", drivers)
                funnel = mid3.selectbox("Funnel Stage", FUNNEL_STAGES)
                influence = mid3.selectbox("Influence Mode", INFLUENCE_MODES)

                if fmt == "Video":
                    low1, low2, low3 = st.columns(3)
                    hook = low1.selectbox("Hook Type", HOOK_TYPES)
                    arc = low2.selectbox("Emotional Arc", EMOTIONAL_ARCS)
                    archetype = low3.selectbox("Creator Archetype", ARCHETYPES)
                    visual_style = "N/A — video"
                else:
                    hook = arc = archetype = ""
                    visual_style = st.selectbox("Visual Style", VISUAL_STYLES)

                cta = st.selectbox("CTA Style", CTA_STYLES)
                creator_name = st.text_input(
                    "Creator / Consumer Name",
                    value=str(picked.get("Creative Name Derived", "")),
                )
                drive_link = st.text_input(
                    "Drive Link",
                    value=str(picked.get("Meta Creative Folder", "")),
                )
                notes = st.text_area(
                    "Notes",
                    value="Retro-tagged from Admin backlog.",
                )

                submitted = st.form_submit_button("💾 Save into Inhouse_Live_Assets", type="primary", use_container_width=True)
                if submitted:
                    live_now = load_inhouse_live()
                    existing_codes = set()
                    existing_ids = []
                    if not live_now.empty:
                        if "AD CODE" in live_now.columns:
                            existing_codes = {
                                normalize_ad_code(value) for value in live_now["AD CODE"].tolist()
                                if normalize_ad_code(value)
                            }
                        if "Asset ID" in live_now.columns:
                            existing_ids = live_now["Asset ID"].dropna().astype(str).tolist()

                    normalized_code = normalize_ad_code(chosen_code)
                    if normalized_code in existing_codes:
                        st.error(f"{normalized_code} already exists in Inhouse_Live_Assets.")
                    else:
                        asset_id = next_asset_id(product, fmt, existing_ids)
                        payload = {header: "" for header in INHOUSE_LIVE_HEADERS}
                        payload.update({
                            "Asset ID": asset_id,
                            "AD CODE": normalized_code,
                            "Published Date": published_date,
                            "Product": product,
                            "Bucket": "Performance",
                            "Format": fmt,
                            "Video Subtype": video_subtype,
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
                            "Creator Archetype": archetype,
                            "Visual Style": visual_style,
                            "Creator / Consumer Name": creator_name,
                            "Drive Link": drive_link,
                            "Notes": notes,
                        })
                        try:
                            save_inhouse_live(payload)
                            st.success(f"Saved {asset_id} for {normalized_code}.")
                            if "admin_backlog" in st.session_state:
                                st.session_state.admin_backlog = st.session_state.admin_backlog[
                                    st.session_state.admin_backlog["AD CODE"].astype(str) != chosen_code
                                ]
                        except Exception as exc:
                            st.error(f"Save failed: {exc}")

st.markdown("---")
st.header("4. Quick diagnostics")

if st.button("🧪 Build classified live view"):
    try:
        diagnostic = build_classified_meta_view()
        st.write(f"Rows loaded: {len(diagnostic)}")
        show_cols = [
            "Source", "AD CODE", "_Date", "Product Derived",
            "Format Derived", "Creative Name Derived", "Asset ID",
        ]
        frame = diagnostic[[column for column in show_cols if column in diagnostic.columns]].copy()
        frame = frame.rename(
            columns={
                "_Date": "Live Date",
                "Product Derived": "Product",
                "Format Derived": "Format",
                "Creative Name Derived": "Creative Name",
            }
        )
        st.dataframe(frame.sort_values("Live Date", ascending=False), use_container_width=True, hide_index=True, height=320)
    except Exception as exc:
        st.error(f"Diagnostic build failed: {exc}")

st.markdown("---")
st.header("5. Quick row sample")
tab_name = st.text_input("Tab name to sample", placeholder="e.g. Meta Ads")
rows = st.number_input("Rows to show", min_value=1, max_value=50, value=5)
if tab_name and st.button("Fetch sample"):
    try:
        ws = _client().open(st.secrets["spreadsheet_name"]).worksheet(tab_name)
        data = ws.get_all_values()
        if data:
            df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(data)
            st.dataframe(df.head(int(rows)), use_container_width=True, hide_index=True)
        else:
            st.info("Tab is empty.")
    except Exception as exc:
        st.error(f"Failed: {exc}")
