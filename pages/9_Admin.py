import streamlit as st
import pandas as pd
from utils.sheets import _client

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

# ── PLACEHOLDER: Migration button (coming next) ──────────────────────────────
st.header("2. One-off migrations")
st.info("_Migration buttons will appear here once schema is confirmed._")

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
