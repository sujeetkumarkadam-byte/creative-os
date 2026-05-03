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
    first_present_column,
    folder_id_from_url,
    load_assets,
    load_meta_ads,
    load_performance_import,
    meta_inhouse_import_candidates,
    import_meta_inhouse_to_master,
    next_asset_id,
    normalize_ad_code,
    parse_mixed_dates,
    refresh_sheet_cache,
    upsert_asset_by_ad_code,
)
from utils.taxonomy import (
    ARCHETYPES,
    CTA_FORMATS,
    CTA_MESSAGE_TYPES,
    CONTENT_HOOK_TYPES,
    EMOTIONAL_ARCS,
    FUNNEL_STAGES,
    INFLUENCE_MODES,
    PRODUCTS,
    STATIC_SUBTYPES,
    STATIC_MESSAGE_TYPES,
    TAXONOMY_CONFIDENCE,
    VIDEO_SUBTYPES,
    VISUAL_HOOK_TYPES,
    VISUAL_TREATMENTS,
    get_angles,
    get_beliefs,
    get_cohorts,
    get_claims,
    get_drivers,
    product_label,
)


st.set_page_config(page_title="Admin - Creative OS", layout="wide")
st.title("Admin")
st.caption("Diagnostics, data audits, and one-off Drive backlog review. Nothing here auto-writes without approval.")


DRIVE_ROOT_DEFAULT = "https://drive.google.com/drive/folders/1PYQyc6oSod-Z0NCPUf3caUMnkJartSq5?usp=drive_link"
PERF_VIDEO_FOLDER_NAME = "Perf videos"
VIDEO_EXTENSIONS = (".mp4", ".mov", ".m4v", ".webm", ".avi", ".mpeg", ".mpg")


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
            "fields": "nextPageToken, files(id,name,mimeType,webViewLink,thumbnailLink,createdTime,modifiedTime,size,videoMediaMetadata)",
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


def _drive_find_folders_by_name(folder_name: str) -> list[dict]:
    session = _drive_session()
    safe_name = str(folder_name or "").replace("\\", "\\\\").replace("'", "\\'")
    params = {
        "q": f"name = '{safe_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed=false",
        "fields": "files(id,name,webViewLink,createdTime,modifiedTime)",
        "pageSize": 20,
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }
    response = session.get("https://www.googleapis.com/drive/v3/files", params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("files", [])


def _is_video_file(item: dict) -> bool:
    name = str(item.get("name", "")).lower()
    mime = str(item.get("mimeType", "")).lower()
    return mime.startswith("video/") or name.endswith(VIDEO_EXTENSIONS)


def _extract_ad_code_from_text(*values) -> str:
    for value in values:
        normalized = normalize_ad_code(value)
        if normalized.startswith("AD "):
            return normalized
    return ""


def _clean_consumer_name(segment: str) -> str:
    text = str(segment or "")
    text = re.sub(r"(?i)^perf\s*videos?\s*[-_:]*", "", text)
    text = re.sub(r"(?i)\bAD\s*[-_]?\s*0*\d+\b", "", text)
    text = re.sub(r"[_\-]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" -_/")
    return text.strip()


def _aspect_ratio_guess(name: str) -> str:
    text = str(name or "").lower()
    if re.search(r"9\s*[:x]\s*16|916|vertical|reel", text):
        return "9:16"
    if re.search(r"4\s*[:x]\s*5|45", text):
        return "4:5"
    if re.search(r"1\s*[:x]\s*1|11|square", text):
        return "1:1"
    return ""


def _scan_drive_videos(
    folder_id: str,
    path: str,
    depth: int,
    max_depth: int,
    inherited_ad_code: str = "",
    consumer_name: str = "",
    folder_link: str = "",
) -> list[dict]:
    if depth > max_depth:
        return []

    output = []
    for item in _drive_list(folder_id):
        name = item.get("name", "")
        mime = item.get("mimeType", "")
        child_path = f"{path}/{name}" if path else name
        item_ad_code = _extract_ad_code_from_text(name)
        active_ad_code = item_ad_code or inherited_ad_code

        if mime == "application/vnd.google-apps.folder":
            child_consumer = consumer_name or _clean_consumer_name(name)
            output.extend(_scan_drive_videos(
                item["id"],
                child_path,
                depth + 1,
                max_depth,
                active_ad_code,
                child_consumer,
                item.get("webViewLink", "") or folder_link,
            ))
            continue

        if not _is_video_file(item):
            continue

        ad_code = item_ad_code or active_ad_code
        if not ad_code:
            continue

        output.append({
            "AD CODE": ad_code,
            "Consumer / Creator Name": consumer_name,
            "Variation Name": _clean_consumer_name(path.split("/")[-1] if path else name) or name,
            "Product": _infer_product(path, name),
            "File Name": name,
            "Folder Path": path,
            "Representative Link": item.get("webViewLink", ""),
            "Thumbnail Link": item.get("thumbnailLink", ""),
            "Source Folder Link": folder_link,
            "File ID": item.get("id", ""),
            "Aspect Ratio": _aspect_ratio_guess(name),
            "Created Time": item.get("createdTime", ""),
            "Modified Time": item.get("modifiedTime", ""),
        })
    return output


def _group_video_candidates(rows: list[dict]) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    if df.empty:
        return df

    priority = {"9:16": 0, "1:1": 1, "4:5": 2, "": 3}
    df["_priority"] = df["Aspect Ratio"].map(priority).fillna(9)
    candidates = []
    for ad_code, group in df.sort_values("_priority").groupby("AD CODE", sort=False):
        picked = group.iloc[0].copy()
        links = [
            f"{row.get('Aspect Ratio') or 'video'}: {row.get('Representative Link')}"
            for _, row in group.iterrows()
            if _safe(row.get("Representative Link"))
        ]
        picked["Video Count"] = len(group)
        picked["Aspect Ratio Links"] = "\n".join(links)
        picked["All File Names"] = "\n".join(group["File Name"].astype(str).tolist())
        picked["All Folder Paths"] = "\n".join(sorted(set(group["Folder Path"].astype(str).tolist())))
        candidates.append(picked.drop(labels=["_priority"], errors="ignore").to_dict())
    return pd.DataFrame(candidates)


def _scan_drive_videos_cached(root_url_or_id: str, max_depth: int):
    folder_id = folder_id_from_url(root_url_or_id) or str(root_url_or_id or "").strip()
    if not folder_id:
        return pd.DataFrame()
    rows = _scan_drive_videos(folder_id, "", 0, max_depth)
    return _group_video_candidates(rows)


def _meta_row_by_ad_code(meta: pd.DataFrame, ad_code: str) -> pd.Series | None:
    if meta.empty or "AD CODE" not in meta.columns:
        return None
    code = normalize_ad_code(ad_code)
    matches = meta[meta["AD CODE"].map(normalize_ad_code) == code]
    if matches.empty:
        return None
    return matches.iloc[-1]


def _pick_from_row(row: pd.Series | None, *columns: str) -> str:
    if row is None:
        return ""
    for column in columns:
        if column in row.index and _safe(row.get(column)):
            return str(row.get(column)).strip()
    return ""


def _published_date_from_meta(row: pd.Series | None) -> str:
    if row is None:
        return ""
    date_col = first_present_column(pd.DataFrame([row]), "Date [Ad Taken Live]", "Date [Ad Taken Live] ")
    if not date_col:
        return ""
    parsed = parse_mixed_dates(pd.Series([row.get(date_col, "")]))
    if parsed.empty or pd.isna(parsed.iloc[0]):
        return ""
    return parsed.iloc[0].strftime("%Y-%m-%d")


def _choice_index(options: list[str], *values) -> int:
    for value in values:
        safe_value = _safe(value)
        if safe_value in options:
            return options.index(safe_value)
    return 0


def _infer_product(path: str, filename: str) -> str:
    text = f"{path} {filename}".lower()
    if re.search(r"\brcf\b|rapid clear", text):
        return "RCF"
    if re.search(r"\bss\b|sunscreen|clear protect|cpgs", text):
        return "Clear Protect Sunscreen"
    if re.search(r"\bsfs\b|spot fade", text):
        return "SpotFade Serum"
    if re.search(r"\blpp\b|liquid pimple", text):
        return "Liquid Pimple Patch"
    if re.search(r"\bemc\b|melting cleanser", text):
        return "Effortless Melting Cleanser"
    if re.search(r"\bbrgm\b|barrier repair", text):
        return "Barrier Repair Moisturiser"
    if re.search(r"emergency acne|\beak\b", text):
        return "Emergency Acne Kit"
    if re.search(r"combo|kit|clear repair|clear protect", text):
        return "Acne Kits"
    if re.search(r"mini|bundle", text):
        return "Minis"
    if re.search(r"barrier soothing|\bbsc\b", text):
        return "Barrier Soothing Cleanser"
    if re.search(r"ultra smooth|\busc\b|\busdc\b", text):
        return "Ultra Smooth Cleanser"
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
        ("meme", "SS6"),
        ("offer", "SS9"),
        ("discount", "SS9"),
        ("b2g", "SS9"),
        ("ingredient", "SS8"),
        ("stats", "SS7"),
        ("clinical", "SS7"),
        ("proof", "SS7"),
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


tab_diag, tab_audit, tab_drive, tab_video = st.tabs([
    "Sheet Diagnostics",
    "Creative Ops Audit",
    "Drive Static Review",
    "Drive Video Review",
])

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
                default_product = product_label(picked.get("Product"))
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
                visual_hook = c4.selectbox("Visual hook type", VISUAL_HOOK_TYPES)
                content_hook = c4.selectbox("Content hook type", CONTENT_HOOK_TYPES)

                c5, c6 = st.columns(2)
                visual = c5.selectbox("Visual treatment", VISUAL_TREATMENTS)
                static_message = c5.selectbox("Static message type", STATIC_MESSAGE_TYPES)
                cta_format = c6.selectbox("CTA format", CTA_FORMATS)
                cta_message = c6.selectbox("CTA message type", CTA_MESSAGE_TYPES)
                taxonomy_confidence = st.selectbox("Taxonomy confidence", TAXONOMY_CONFIDENCE, index=2)

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
                        "Hook Type": content_hook,
                        "Visual Hook Type": visual_hook,
                        "Content Hook Type": content_hook,
                        "Funnel Stage": funnel,
                        "Influence Mode": influence,
                        "Visual Style": visual,
                        "Visual Treatment": visual,
                        "Static Message Type": static_message,
                        "CTA Style": cta_message,
                        "CTA Format": cta_format,
                        "CTA Message Type": cta_message,
                        "AI-Generated": "Yes" if "ai" in f"{picked.get('Folder Path', '')} {picked.get('File Name', '')}".lower() else "",
                        "Taxonomy Confidence": taxonomy_confidence,
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

with tab_video:
    st.header("Drive video review queue")
    st.caption(
        "Scans the `Perf videos` Drive tree, detects AD CODEs from folder/file names, "
        "groups 1:1 and 9:16 duplicates, and lets you update Master only after review."
    )
    st.info(
        "No fake auto-tagging here: the app can save hard facts from Drive/Meta and your approved taxonomy. "
        "If you paste a transcript or transcript link, it stores that context, but visual hook fields still need human review."
    )

    find_col, paste_col = st.columns([0.9, 1.1])
    with find_col:
        folder_name = st.text_input("Find Drive folder by exact name", value=PERF_VIDEO_FOLDER_NAME)
        if st.button("Find Perf videos folder"):
            try:
                matches = _drive_find_folders_by_name(folder_name)
                st.session_state.perf_video_folder_matches = matches
                if not matches:
                    st.warning("No matching folder found for the service account. Paste the folder URL/ID below if needed.")
            except Exception as exc:
                st.error(f"Folder search failed: {exc}")

        matches = st.session_state.get("perf_video_folder_matches", [])
        chosen_match = None
        if matches:
            labels = [f"{match.get('name')} | {match.get('id')}" for match in matches]
            chosen_label = st.selectbox("Matching folders", labels)
            chosen_match = matches[labels.index(chosen_label)]
            st.markdown(f"[Open selected folder]({chosen_match.get('webViewLink', '')})")

    with paste_col:
        default_video_root = chosen_match.get("id", "") if chosen_match else ""
        video_root = st.text_input(
            "Or paste Perf videos folder URL / ID",
            value=default_video_root,
            placeholder="Google Drive folder URL or folder ID",
        )
        video_depth = st.slider("Video folder depth", min_value=1, max_value=7, value=5)
        if st.button("Scan Perf videos", type="primary"):
            try:
                with st.spinner("Scanning Drive videos and grouping aspect-ratio duplicates..."):
                    st.session_state.video_drive_candidates = _scan_drive_videos_cached(video_root, video_depth)
            except Exception as exc:
                st.error(f"Video Drive scan failed: {exc}")

    video_candidates = st.session_state.get("video_drive_candidates")
    if video_candidates is None:
        st.info("Find or paste the `Perf videos` folder, then scan to build the review queue.")
    elif video_candidates.empty:
        st.warning("No AD CODE-tagged video files found. Check that AD CODE is at the start of the variation folder or video filename.")
    else:
        st.success(f"Found {len(video_candidates)} AD CODE video candidates.")
        preview_cols = [
            "AD CODE", "Consumer / Creator Name", "Variation Name", "Product",
            "Video Count", "Aspect Ratio", "Representative Link", "Folder Path",
        ]
        st.dataframe(
            video_candidates[[c for c in preview_cols if c in video_candidates.columns]],
            use_container_width=True,
            hide_index=True,
            height=260,
        )

        assets = load_assets()
        meta = load_meta_ads()
        existing_ids = assets["Asset ID"].dropna().astype(str).tolist() if not assets.empty and "Asset ID" in assets.columns else []

        review_labels = video_candidates.apply(
            lambda row: f"{row.get('AD CODE')} | {row.get('Consumer / Creator Name') or 'Unknown'} | {row.get('Variation Name')}",
            axis=1,
        ).tolist()
        selected_video = st.selectbox("Review video candidate", review_labels)
        video_row = video_candidates.iloc[review_labels.index(selected_video)]
        normalized_code = normalize_ad_code(video_row.get("AD CODE"))

        existing_asset = None
        if not assets.empty and "Meta Ad ID" in assets.columns:
            matches = assets[assets["Meta Ad ID"].map(normalize_ad_code) == normalized_code]
            if not matches.empty:
                existing_asset = matches.iloc[-1]

        meta_row = _meta_row_by_ad_code(meta, normalized_code)
        if existing_asset is not None:
            st.success(f"{normalized_code} already exists in Master. Approval will update that row, not create a duplicate.")
        elif meta_row is not None:
            st.info(f"{normalized_code} matched Meta Ads. Approval will create a new Master row.")
        else:
            st.warning(f"{normalized_code} was found in Drive but not matched in Meta Ads yet. You can still save it for review.")

        left, right = st.columns([0.75, 1.25])
        with left:
            if _safe(video_row.get("Thumbnail Link")):
                st.image(video_row["Thumbnail Link"], use_container_width=True)
            st.markdown(f"**AD CODE:** {normalized_code}")
            st.markdown(f"**Consumer:** {_safe(video_row.get('Consumer / Creator Name'), 'Unknown')}")
            st.markdown(f"**Variation:** {_safe(video_row.get('Variation Name'), 'Unknown')}")
            st.markdown(f"**Video files grouped:** {int(video_row.get('Video Count', 1))}")
            if _safe(video_row.get("Representative Link")):
                st.markdown(f"[Open representative video]({video_row.get('Representative Link')})")
            if _safe(video_row.get("Source Folder Link")):
                st.markdown(f"[Open source folder]({video_row.get('Source Folder Link')})")
            if _safe(video_row.get("Aspect Ratio Links")):
                st.text_area("Aspect-ratio links", value=video_row.get("Aspect Ratio Links"), height=110, disabled=True)

        with right:
            meta_product = product_label(_pick_from_row(meta_row, "Product"))
            existing_product = product_label(existing_asset.get("Product")) if existing_asset is not None else ""
            candidate_product = product_label(video_row.get("Product"))
            default_product = existing_product or meta_product or candidate_product

            with st.form("approve_drive_video"):
                product = st.selectbox("Product", PRODUCTS, index=_choice_index(PRODUCTS, default_product))
                video_subtype = st.selectbox(
                    "Video subtype",
                    VIDEO_SUBTYPES,
                    index=_choice_index(VIDEO_SUBTYPES, existing_asset.get("Video Subtype") if existing_asset is not None else "", "VS1 - Consumer Testimonial"),
                )

                cohorts = get_cohorts(product)
                beliefs = get_beliefs(product)
                angles = get_angles(product)
                drivers = get_drivers(product)
                claims = get_claims(product)

                c1, c2 = st.columns(2)
                cohort = c1.selectbox("Cohort", cohorts, index=_choice_index(cohorts, existing_asset.get("Cohort") if existing_asset is not None else ""))
                belief = c1.selectbox("Belief", beliefs, index=_choice_index(beliefs, existing_asset.get("Belief") if existing_asset is not None else ""))
                angle = c2.selectbox(
                    "Marketing angle",
                    angles,
                    index=_choice_index(angles, existing_asset.get("Marketing Angle") if existing_asset is not None else "", _pick_from_row(meta_row, "Marketing Angle")),
                )
                driver = c2.selectbox("Situational driver", drivers, index=_choice_index(drivers, existing_asset.get("Situational Driver") if existing_asset is not None else ""))

                c3, c4 = st.columns(2)
                visual_hook = c3.selectbox("Visual hook type", VISUAL_HOOK_TYPES, index=_choice_index(VISUAL_HOOK_TYPES, existing_asset.get("Visual Hook Type") if existing_asset is not None else ""))
                content_hook = c3.selectbox("Content hook type", CONTENT_HOOK_TYPES, index=_choice_index(CONTENT_HOOK_TYPES, existing_asset.get("Content Hook Type") if existing_asset is not None else ""))
                emotional_arc = c4.selectbox("Emotional arc", EMOTIONAL_ARCS, index=_choice_index(EMOTIONAL_ARCS, existing_asset.get("Emotional Arc") if existing_asset is not None else ""))
                creator_arch = c4.selectbox("Creator archetype", ARCHETYPES, index=_choice_index(ARCHETYPES, existing_asset.get("Creator Archetype") if existing_asset is not None else "", "LEV - Lived Experience Validator"))

                c5, c6 = st.columns(2)
                funnel_default = _pick_from_row(meta_row, "Funnel Level") or (existing_asset.get("Funnel Stage") if existing_asset is not None else "")
                funnel = c5.selectbox("Funnel stage", FUNNEL_STAGES, index=_choice_index(FUNNEL_STAGES, funnel_default))
                influence = c5.selectbox("Influence mode", INFLUENCE_MODES, index=_choice_index(INFLUENCE_MODES, existing_asset.get("Influence Mode") if existing_asset is not None else ""))
                cta_format = c6.selectbox("CTA format", CTA_FORMATS, index=_choice_index(CTA_FORMATS, existing_asset.get("CTA Format") if existing_asset is not None else ""))
                cta_message = c6.selectbox("CTA message type", CTA_MESSAGE_TYPES, index=_choice_index(CTA_MESSAGE_TYPES, existing_asset.get("CTA Message Type") if existing_asset is not None else ""))

                claim_codes = st.multiselect(
                    "Approved claim codes used",
                    claims,
                    default=[value for value in str(existing_asset.get("Claim Codes", "") if existing_asset is not None else "").split(", ") if value in claims] or ["None"],
                )
                taxonomy_confidence = st.selectbox(
                    "Taxonomy confidence",
                    TAXONOMY_CONFIDENCE,
                    index=_choice_index(TAXONOMY_CONFIDENCE, existing_asset.get("Taxonomy Confidence") if existing_asset is not None else "", "Needs Review"),
                )

                creative_name_default = (
                    existing_asset.get("Creator / Consumer Name") if existing_asset is not None and _safe(existing_asset.get("Creator / Consumer Name")) else
                    video_row.get("Consumer / Creator Name")
                )
                consumer_name = st.text_input("Creator / consumer name", value=_safe(creative_name_default))
                source_story_id = st.text_input(
                    "Source story / interview ID",
                    value=_safe(existing_asset.get("Source Interview ID") if existing_asset is not None else ""),
                    placeholder="Optional source story ID",
                )
                transcript_link = st.text_input(
                    "Transcript link",
                    value=_safe(existing_asset.get("Transcript Link") if existing_asset is not None else ""),
                    placeholder="Optional Google Doc / transcript URL",
                )
                transcript_notes = st.text_area(
                    "Transcript notes / proof lines",
                    value=_safe(existing_asset.get("Transcript Notes") if existing_asset is not None else ""),
                    placeholder="Paste transcript summary or key proof lines. Full transcription can live in a Doc link.",
                    height=90,
                )
                notes = st.text_area(
                    "Review notes",
                    value=_safe(
                        existing_asset.get("Notes") if existing_asset is not None else "",
                        "Tagged from Drive video review queue. Transcript and visual hook require human approval.",
                    ),
                    height=80,
                )

                submitted = st.form_submit_button("Approve and save/update Master_Asset_Registry", type="primary", use_container_width=True)
                if submitted:
                    asset_id = existing_asset.get("Asset ID") if existing_asset is not None and _safe(existing_asset.get("Asset ID")) else next_asset_id(product, "Video", existing_ids)
                    published_date = _safe(
                        existing_asset.get("Published Date") if existing_asset is not None else "",
                        _published_date_from_meta(meta_row),
                    )
                    campaign_name = _pick_from_row(meta_row, "FB Ad Name", "Ad Name (TSS)", "Ad Name (Porcellia)")
                    row = {
                        "Asset ID": asset_id,
                        "Variant #": _safe(existing_asset.get("Variant #") if existing_asset is not None else "", "A"),
                        "Status": "Published" if published_date else "Backlog Review",
                        "Created Date": datetime.now().strftime("%Y-%m-%d"),
                        "Published Date": published_date,
                        "Product": product,
                        "Bucket": "Performance",
                        "Channel": "In-house",
                        "Creative Type": video_subtype,
                        "Format": "Video",
                        "Video Subtype": video_subtype,
                        "Cohort": cohort,
                        "Belief": belief,
                        "Marketing Angle": angle,
                        "Situational Driver": driver,
                        "Hook Type": content_hook,
                        "Visual Hook Type": visual_hook,
                        "Content Hook Type": content_hook,
                        "Emotional Arc": emotional_arc,
                        "Funnel Stage": funnel,
                        "Creator Archetype": creator_arch,
                        "Influence Mode": influence,
                        "CTA Style": cta_message,
                        "CTA Format": cta_format,
                        "CTA Message Type": cta_message,
                        "Taxonomy Confidence": taxonomy_confidence,
                        "Claim Codes": ", ".join([claim for claim in claim_codes if claim != "None"]),
                        "Creator / Consumer Name": consumer_name,
                        "Source Interview ID": source_story_id,
                        "Meta Ad ID": normalized_code,
                        "Campaign Name": campaign_name,
                        "Drive Link": video_row.get("Representative Link", ""),
                        "Preview Asset Link": video_row.get("Representative Link", ""),
                        "Source Folder Link": video_row.get("Source Folder Link", "") or video_row.get("Folder Path", ""),
                        "Thumbnail Link": video_row.get("Thumbnail Link", ""),
                        "Transcript Link": transcript_link,
                        "Transcript Notes": transcript_notes,
                        "Aspect Ratio Links": video_row.get("Aspect Ratio Links", ""),
                        "Notes": notes,
                        "Taxonomy Review Status": "Tagged" if taxonomy_confidence != "Needs Review" else "Needs Review",
                    }
                    try:
                        action, saved_asset_id = upsert_asset_by_ad_code(row)
                        if action == "updated":
                            st.success(f"Updated existing Master row for {normalized_code}.")
                        else:
                            st.success(f"Saved {saved_asset_id} to Master_Asset_Registry.")
                    except Exception as exc:
                        st.error(f"Save/update failed: {exc}")
