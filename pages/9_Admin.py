from datetime import datetime
import re

from google.auth.transport.requests import AuthorizedSession
import pandas as pd
import streamlit as st

from utils.sheets import (
    _client,
    _credentials,
    _ws,
    SHEET_ASSETS,
    SHEET_EXPERIMENTS,
    SHEET_INFLUENCER,
    SHEET_META_ADS,
    SHEET_PERFORMANCE,
    build_creative_ops_view,
    ensure_performance_import_sheet,
    folder_id_from_url,
    load_assets,
    load_performance_import,
    meta_inhouse_import_candidates,
    import_meta_inhouse_to_master,
    next_asset_id,
    normalize_ad_code,
    refresh_sheet_cache,
    upsert_asset_by_ad_code,
)
from utils.taxonomy import (
    CTA_STYLES,
    FUNNEL_STAGES,
    INFLUENCE_MODES,
    PRODUCTS,
    STATIC_SUBTYPES,
    VISUAL_STYLES,
    get_angles,
    get_beliefs,
    get_cohorts,
    get_drivers,
)


st.set_page_config(page_title="Admin - Creative OS", layout="wide")
st.title("Admin")
st.caption("Diagnostics, data audits, and one-off Drive backlog review. Nothing here auto-writes without approval.")


DRIVE_ROOT_DEFAULT = "https://drive.google.com/drive/folders/1PYQyc6oSod-Z0NCPUf3caUMnkJartSq5?usp=drive_link"


def _safe(value, fallback=""):
    text = str(value or "").strip()
    return text if text and text.lower() not in {"nan", "nat", "none"} else fallback


def _drive_session():
    return AuthorizedSession(_credentials())


def _drive_list(folder_id: str) -> list[dict]:
    session = _drive_session()
    files: list[dict] = []
    page_token = None
    while True:
        params = {
            "q": f"'{folder_id}' in parents and trashed=false",
            "fields": "nextPageToken, files(id,name,mimeType,webViewLink,thumbnailLink,createdTime,modifiedTime)",
            "pageSize": 1000,
            "supportsAllDrives": "true",
            "includeItemsFromAllDrives": "true",
        }
        if page_token:
            params["pageToken"] = page_token
        response = session.get("https://www.googleapis.com/drive/v3/files", params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        files.extend(payload.get("files", []))
        page_token = payload.get("nextPageToken")
        if not page_token:
            break
    return files


def _infer_product(path: str, filename: str) -> str:
    text = f"{path} {filename}".lower()
    if re.search(r"\brcf\b|rapid clear", text):
        return "RCF"
    if re.search(r"\bss\b|sunscreen|clear protect|cpgs", text):
        return "Clear Protect Gel Sunscreen"
    if re.search(r"\bsfs\b|spot fade", text):
        return "Spot Fade Serum"
    if re.search(r"\blpp\b|liquid pimple", text):
        return "Liquid Pimple Patch"
    if re.search(r"\bemc\b|melting cleanser", text):
        return "Effortless Melting Cleanser"
    return PRODUCTS[0]


def _infer_static_subtype(name: str, path: str) -> str:
    text = f"{path} {name}".lower()
    checks = [
        ("carousel", "SS2"),
        ("before", "SS3"),
        ("after", "SS3"),
        ("review", "SS4"),
        ("testimonial", "SS4"),
        ("comparison", "SS5"),
        ("ingredient", "SS9"),
        ("stat", "SS10"),
        ("proof", "SS10"),
        ("ai", "SS11"),
    ]
    code = next((result for needle, result in checks if needle in text), "SS1")
    return next((item for item in STATIC_SUBTYPES if item.startswith(code)), STATIC_SUBTYPES[0])


def _infer_angle(product: str, name: str, path: str) -> str:
    text = f"{path} {name}".lower()
    angles = get_angles(product)
    for angle in angles:
        label = angle.split(" - ", 1)[-1].lower()
        label = label.replace("/", " ").replace("(", " ").replace(")", " ")
        tokens = [token for token in re.split(r"\W+", label) if len(token) > 4]
        if tokens and any(token in text for token in tokens[:4]):
            return angle
    return angles[0] if angles else ""


def _scan_drive(folder_id: str, path: str, depth: int, max_depth: int) -> list[dict]:
    if depth > max_depth:
        return []
    output = []
    for item in _drive_list(folder_id):
        name = item.get("name", "")
        mime = item.get("mimeType", "")
        child_path = f"{path}/{name}" if path else name
        if mime == "application/vnd.google-apps.folder":
            output.extend(_scan_drive(item["id"], child_path, depth + 1, max_depth))
            continue
        if mime.startswith("image/") or name.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            product = _infer_product(path, name)
            output.append({
                "Product": product,
                "File Name": name,
                "Folder Path": path,
                "Drive Link": item.get("webViewLink", ""),
                "Thumbnail Link": item.get("thumbnailLink", ""),
                "File ID": item.get("id", ""),
                "Created Time": item.get("createdTime", ""),
                "Modified Time": item.get("modifiedTime", ""),
                "Suggested Static Subtype": _infer_static_subtype(name, path),
                "Suggested Marketing Angle": _infer_angle(product, name, path),
            })
    return output


def _scan_drive_cached(root_url: str, max_depth: int):
    folder_id = folder_id_from_url(root_url)
    if not folder_id:
        return pd.DataFrame()
    rows = _scan_drive(folder_id, "", 0, max_depth)
    return pd.DataFrame(rows)


tab_diag, tab_audit, tab_drive = st.tabs(["Sheet Diagnostics", "Creative Ops Audit", "Drive Static Review"])

with tab_diag:
    st.header("Spreadsheet schema")
    if st.button("Refresh cached sheet reads"):
        refresh_sheet_cache()
        st.success("Cleared sheet cache. Reload the page or rerun diagnostics for fresh data.")

    if st.button("Create Performance_Import tab for SyncWith"):
        try:
            created = ensure_performance_import_sheet()
            if created:
                st.success(f"Created `{SHEET_PERFORMANCE}`. Point SyncWith to this tab and include an `AD CODE` column.")
            else:
                st.info(f"`{SHEET_PERFORMANCE}` already exists.")
        except Exception as exc:
            st.error(f"Could not create performance tab: {exc}")

    perf_df = load_performance_import()
    if perf_df.empty:
        st.info("No performance import tab detected yet. Accepted tab names include `Performance_Import`, `Creative_Performance`, and `Meta Performance`.")
    else:
        st.success(f"Detected performance tab `{perf_df['Performance Sheet'].iloc[0]}` with {len(perf_df)} AD CODE rows.")

    if st.button("Scan all tabs", type="primary"):
        try:
            ss = _client().open(st.secrets["spreadsheet_name"])
            worksheets = ss.worksheets()
            st.success(f"Found {len(worksheets)} tabs in {st.secrets['spreadsheet_name']}")
            for ws in worksheets:
                with st.expander(f"{ws.title} - {ws.row_count:,} rows x {ws.col_count} cols", expanded=False):
                    raw = ws.get_values("A1:BU5")
                    if not raw:
                        st.info("Empty sheet.")
                        continue
                    st.dataframe(pd.DataFrame(raw), use_container_width=True, hide_index=True)
                    likely_header_idx = 1 if ws.title == SHEET_META_ADS and len(raw) > 1 else 0
                    headers = [h for h in raw[likely_header_idx] if str(h).strip()] if likely_header_idx < len(raw) else []
                    st.markdown(f"**Detected headers row {likely_header_idx + 1}**")
                    st.code(" | ".join(headers), language=None)
        except Exception as exc:
            st.error(f"Scan failed: {exc}")

    st.markdown("---")
    st.header("Quick row sample")
    tab_name = st.selectbox("Tab", [SHEET_META_ADS, SHEET_INFLUENCER, SHEET_ASSETS, SHEET_EXPERIMENTS])
    rows = st.number_input("Rows to show", min_value=1, max_value=50, value=10)
    if st.button("Fetch sample"):
        try:
            ws = _client().open(st.secrets["spreadsheet_name"]).worksheet(tab_name)
            data = ws.get_all_values()
            if not data:
                st.info("Tab is empty.")
            else:
                header_idx = 1 if tab_name == SHEET_META_ADS and len(data) > 1 else 0
                headers = data[header_idx]
                body = data[header_idx + 1:]
                st.dataframe(pd.DataFrame(body[: int(rows)], columns=headers), use_container_width=True, hide_index=True)
        except Exception as exc:
            st.error(f"Fetch failed: {exc}")

with tab_audit:
    st.header("Creative Ops data audit")
    st.subheader("One-time Meta Ads -> Master import")
    st.caption(
        "Finds Meta Ads rows where Creative Name contains `inhouse`, excludes rows already in Master, "
        "excludes influencer Perf AD Code matches, and excludes Kuhu-tagged rows. Imported taxonomy is conservative."
    )
    if st.button("Preview importable in-house Meta rows"):
        try:
            st.session_state.meta_inhouse_candidates = meta_inhouse_import_candidates()
        except Exception as exc:
            st.error(f"Preview failed: {exc}")

    meta_candidates = st.session_state.get("meta_inhouse_candidates")
    if meta_candidates is not None:
        if meta_candidates.empty:
            st.success("No importable in-house Meta rows found.")
        else:
            st.warning(f"{len(meta_candidates)} rows can be imported into Master_Asset_Registry.")
            cols = [
                "AD CODE", "Date [Ad Taken Live]", "Creative Name", "Creative Type",
                "Product", "Marketing Angle", "Funnel Level", "Content Bucket",
                "Creative Folder Link", "1:1 Creative Link", "9:16 Creative Link",
            ]
            st.dataframe(meta_candidates[[c for c in cols if c in meta_candidates.columns]], use_container_width=True, hide_index=True, height=260)
            confirm_import = st.checkbox("I confirm these should be imported into Master_Asset_Registry")
            if st.button("Import these rows into Master", type="primary", disabled=not confirm_import):
                try:
                    imported, errors = import_meta_inhouse_to_master()
                    st.success(f"Imported {imported} rows into Master_Asset_Registry.")
                    if errors:
                        st.warning("Some rows failed:")
                        for error in errors:
                            st.write(f"- {error}")
                    st.session_state.pop("meta_inhouse_candidates", None)
                    st.session_state.pop("audit_view", None)
                except Exception as exc:
                    st.error(f"Import failed: {exc}")

    st.markdown("---")
    if st.button("Build current dashboard dataset", type="primary"):
        try:
            view = build_creative_ops_view()
            if view.empty:
                st.warning("No rows built.")
            else:
                st.session_state.audit_view = view
        except Exception as exc:
            st.error(f"Build failed: {exc}")

    view = st.session_state.get("audit_view")
    if view is not None:
        st.metric("Rows built", len(view))
        if "Source" in view.columns:
            st.dataframe(view["Source"].value_counts().reset_index().rename(columns={"index": "Source", "Source": "Rows"}), use_container_width=True, hide_index=True)

        needs = view[view["Source"] == "Needs Logging"].copy() if "Source" in view.columns else pd.DataFrame()
        if not needs.empty:
            st.warning(f"{len(needs)} likely in-house Meta Ads rows are missing from Master_Asset_Registry.")
            cols = ["AD CODE", "_Date", "Creative Name", "Product", "Format", "Drive Link", "Needs Attention"]
            st.dataframe(needs[[c for c in cols if c in needs.columns]], use_container_width=True, hide_index=True)

        cols = [
            "Source", "Record Type", "AD CODE", "Perf AD Code", "_Date", "Creative Name",
            "Product", "Format", "Asset ID", "Creator", "Needs Attention",
        ]
        st.dataframe(view[[c for c in cols if c in view.columns]].head(1000), use_container_width=True, hide_index=True, height=420)

with tab_drive:
    st.header("Drive static review queue")
    st.caption(
        "This scans your static folders and creates suggested rows. It does not read text inside images yet, "
        "and it does not write to Master until you approve a candidate."
    )

    root_url = st.text_input("Drive root folder", value=DRIVE_ROOT_DEFAULT)
    depth = st.slider("Folder depth", min_value=1, max_value=5, value=3)
    if st.button("Scan Drive folder", type="primary"):
        try:
            with st.spinner("Scanning Drive folders and image files..."):
                st.session_state.drive_candidates = _scan_drive_cached(root_url, depth)
        except Exception as exc:
            st.error(f"Drive scan failed: {exc}")

    candidates = st.session_state.get("drive_candidates")
    if candidates is None:
        st.info("Scan the Drive folder to start building a review queue.")
    elif candidates.empty:
        st.warning("No image files found in this folder tree.")
    else:
        st.success(f"Found {len(candidates)} image candidates.")
        st.dataframe(
            candidates[["Product", "File Name", "Folder Path", "Suggested Static Subtype", "Suggested Marketing Angle", "Drive Link"]],
            use_container_width=True,
            hide_index=True,
            height=260,
        )

        labels = candidates.apply(lambda row: f"{row['Product']} | {row['Folder Path']} | {row['File Name']}", axis=1).tolist()
        selected = st.selectbox("Review candidate", labels)
        picked = candidates.iloc[labels.index(selected)]

        left, right = st.columns([0.8, 1.2])
        with left:
            if _safe(picked.get("Thumbnail Link")):
                st.image(picked["Thumbnail Link"], use_container_width=True)
            st.markdown(f"**File:** {picked['File Name']}")
            st.markdown(f"**Folder:** {picked['Folder Path']}")
            st.markdown(f"[Open in Drive]({picked['Drive Link']})")

        with right:
            assets = load_assets()
            existing_ids = assets["Asset ID"].dropna().astype(str).tolist() if not assets.empty and "Asset ID" in assets.columns else []

            with st.form("approve_drive_static"):
                default_product = picked.get("Product") if picked.get("Product") in PRODUCTS else PRODUCTS[0]
                product = st.selectbox("Product", PRODUCTS, index=PRODUCTS.index(default_product))
                subtype = st.selectbox(
                    "Static subtype",
                    STATIC_SUBTYPES,
                    index=STATIC_SUBTYPES.index(picked["Suggested Static Subtype"]) if picked["Suggested Static Subtype"] in STATIC_SUBTYPES else 0,
                )

                cohorts = get_cohorts(product)
                beliefs = get_beliefs(product)
                angles = get_angles(product)
                drivers = get_drivers(product)

                c1, c2 = st.columns(2)
                cohort = c1.selectbox("Cohort", cohorts)
                belief = c1.selectbox("Belief", beliefs)
                angle_default = picked.get("Suggested Marketing Angle", "")
                angle = c2.selectbox("Marketing angle", angles, index=angles.index(angle_default) if angle_default in angles else 0)
                driver = c2.selectbox("Situational driver", drivers)

                c3, c4 = st.columns(2)
                funnel = c3.selectbox("Funnel stage", FUNNEL_STAGES)
                influence = c3.selectbox("Influence mode", INFLUENCE_MODES)
                visual = c4.selectbox("Visual style", [v for v in VISUAL_STYLES if not v.startswith("N/A")])
                cta = c4.selectbox("CTA style", CTA_STYLES)

                ad_code = st.text_input("AD CODE if already live", placeholder="Optional, e.g. AD 512")
                creative_name = st.text_input("Creative name", value=picked["File Name"])
                notes = st.text_area(
                    "Notes",
                    value="Imported from Drive static review queue. Taxonomy approved manually.",
                    height=80,
                )

                submitted = st.form_submit_button("Approve and save/update Master_Asset_Registry", type="primary", use_container_width=True)
                if submitted:
                    normalized_code = normalize_ad_code(ad_code)
                    asset_id = next_asset_id(product, "Static", existing_ids)
                    row = {
                        "Asset ID": asset_id,
                        "Variant #": "A",
                        "Status": "Backlog Review" if not normalized_code else "Published",
                        "Created Date": datetime.now().strftime("%Y-%m-%d"),
                        "Published Date": "",
                        "Product": product,
                        "Bucket": "Performance",
                        "Channel": "In-house",
                        "Creative Type": subtype,
                        "Format": "Static",
                        "Static Subtype": subtype,
                        "Cohort": cohort,
                        "Belief": belief,
                        "Marketing Angle": angle,
                        "Situational Driver": driver,
                        "Funnel Stage": funnel,
                        "Influence Mode": influence,
                        "Visual Style": visual,
                        "CTA Style": cta,
                        "Creator / Consumer Name": creative_name,
                        "Meta Ad ID": normalized_code,
                        "Drive Link": picked["Drive Link"],
                        "Preview Asset Link": picked["Drive Link"],
                        "Source Folder Link": picked["Folder Path"],
                        "Thumbnail Link": picked.get("Thumbnail Link", ""),
                        "Notes": notes,
                        "Taxonomy Review Status": "Tagged",
                    }
                    try:
                        action, saved_asset_id = upsert_asset_by_ad_code(row)
                        if action == "updated":
                            st.success(f"Updated existing Master row for {normalized_code}. Filled the approved taxonomy and preview fields.")
                        else:
                            st.success(f"Saved {saved_asset_id} to Master_Asset_Registry.")
                    except Exception as exc:
                        st.error(f"Save/update failed: {exc}")
