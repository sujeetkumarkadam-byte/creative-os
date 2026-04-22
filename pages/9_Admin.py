import streamlit as st
import pandas as pd
from utils.sheets import (
    _client, ensure_inhouse_sheet, migrate_master_to_inhouse,
    load_inhouse_live, load_assets, SHEET_INHOUSE, SHEET_ASSETS,
)

st.set_page_config(page_title="Admin / Diagnostics — Creative OS", layout="wide")
st.title("Admin / Diagnostics")
st.caption("Inspect spreadsheet structure, run one-off migrations, verify schema.")

# ── TAB INTROSPECTION ────────────────────────────────────────────────────────
st.header("1. Spreadsheet schema")

if st.button("🔍 Scan all tabs", type="primary"):
    try:
        ss = _client().open(st.secrets["spreadsheet_name"])
        tabs = ss.worksheets()
        st.success(f"Found **{len(tabs)}** tabs in *{st.secrets['spreadsheet_name']}*")

        for ws in tabs:
            with st.expander(f"📄 **{ws.title}**  —  {ws.row_count:,} rows × {ws.col_count} cols", expanded=False):
                # Read first 5 rows to detect header location
                raw = ws.get_values("A1:Z5")
                if not raw:
                    st.info("_Empty sheet_")
                    continue

                st.markdown("**First 5 rows (raw):**")
                st.dataframe(pd.DataFrame(raw), use_container_width=True, hide_index=True)

                # Try row 1 as header first, fall back to row 2
                for header_row_idx in [0, 1]:
                    if header_row_idx < len(raw):
                        headers = [h for h in raw[header_row_idx] if h]
                        if headers:
                            st.markdown(f"**Detected headers (row {header_row_idx + 1}):** `{len(headers)}` columns")
                            st.code(" | ".join(headers), language=None)
                            break

                # Non-empty data rows count estimate
                try:
                    all_vals = ws.get_all_values()
                    non_empty = sum(1 for r in all_vals if any(cell.strip() for cell in r))
                    st.markdown(f"**Non-empty rows:** {non_empty}")
                except Exception as e:
                    st.warning(f"Row count failed: {e}")

    except Exception as e:
        st.error(f"Scan failed: {e}")

st.markdown("---")

# ── MIGRATIONS ───────────────────────────────────────────────────────────────
st.header("2. One-off migrations")

st.markdown(f"**Step A — Create `{SHEET_INHOUSE}` sheet** (idempotent; safe to click even if it exists).")
if st.button("🏗️ Create Inhouse_Live_Assets sheet"):
    try:
        created = ensure_inhouse_sheet()
        if created:
            st.success(f"Created `{SHEET_INHOUSE}` with full header schema.")
        else:
            st.info(f"`{SHEET_INHOUSE}` already exists — no action taken.")
    except Exception as e:
        st.error(f"Failed: {e}")

st.markdown(f"**Step B — Copy existing rows from `{SHEET_ASSETS}` into `{SHEET_INHOUSE}`** "
            "(one-off; run once after Step A).")
st.caption(
    "Legacy Meta Ad ID → AD CODE. Legacy Creative Type auto-splits into Format + "
    "Video Subtype / Static Subtype. Reference Image Link is blank (new field). "
    "Double-clicking this button will duplicate rows — only click once."
)
confirm = st.checkbox("I understand clicking this twice duplicates rows")
if st.button("📦 Migrate Master_Asset_Registry → Inhouse_Live_Assets", disabled=not confirm):
    try:
        with st.spinner("Migrating..."):
            migrated, skipped, errors = migrate_master_to_inhouse()
        st.success(f"✅ Migrated {migrated} rows. Skipped: {skipped}.")
        if errors:
            st.warning("Some rows failed:")
            for e in errors:
                st.write(f"- {e}")

        # Show a preview
        live = load_inhouse_live()
        if not live.empty:
            st.markdown(f"**`{SHEET_INHOUSE}` now has {len(live)} rows.**")
            preview_cols = [
                "Asset ID", "AD CODE", "Published Date", "Product",
                "Format", "Video Subtype", "Static Subtype",
                "Cohort", "Marketing Angle", "Creator / Consumer Name",
            ]
            avail = [c for c in preview_cols if c in live.columns]
            st.dataframe(live[avail].head(10), use_container_width=True, hide_index=True)
    except Exception as e:
        st.error(f"Migration failed: {e}")

st.markdown("---")
st.header("3. Quick row sample")
tab_name = st.text_input("Tab name to sample", placeholder="e.g. Meta Ads")
n = st.number_input("Rows to show", min_value=1, max_value=50, value=5)
if tab_name and st.button("Fetch sample"):
    try:
        ws = _client().open(st.secrets["spreadsheet_name"]).worksheet(tab_name)
        data = ws.get_all_values()
        if data:
            df = pd.DataFrame(data[1:], columns=data[0]) if len(data) > 1 else pd.DataFrame(data)
            st.dataframe(df.head(int(n)), use_container_width=True, hide_index=True)
        else:
            st.info("Tab is empty.")
    except Exception as e:
        st.error(f"Failed: {e}")
