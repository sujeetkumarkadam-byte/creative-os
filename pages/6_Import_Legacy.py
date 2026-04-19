import streamlit as st
import pandas as pd
from utils.sheets import _client, load_assets, save_asset, next_asset_id, ASSET_HEADERS
from utils.taxonomy import ANGLES_RCF, HOOK_TYPES, COHORTS_RCF, BELIEFS, FUNNEL_STAGES

LEGACY_SHEET_ID = "1TJEVk4-mu4_y7F1OE3hyCGm9gcalJOPvL7_YbGFiftw"

# ── Best-guess mappings from old free-text → new taxonomy ─────────────────────
ANGLE_MAP = {
    "hormonal acne relief":           "MA-R1 — Wrong Tool (SA vs BPO mechanism)",
    "hormonal acne relief ":          "MA-R1 — Wrong Tool (SA vs BPO mechanism)",
    "it's just an acne":              "MA-R2 — Calm Before Clear",
    "rapid results":                  "MA-R4 — Early Signal Matters",
    "2 min routine":                  "MA-R5 — One Step, Right Problem",
    "2 min (easy) routine":           "MA-R5 — One Step, Right Problem",
    "brand care ":                    "MA-R5 — One Step, Right Problem",
    "brand care":                     "MA-R5 — One Step, Right Problem",
    "invisible acne":                 "MA-R6 — Barrier-First Design",
    "i did not feel like leaving the house": "MA-R2 — Calm Before Clear",
    "one call , one face wash":       "MA-R5 — One Step, Right Problem",
    "i've tried everything, nothing worked, this did": "MA-R4 — Early Signal Matters",
    "i've tried everything, nothing worked, this did (just a hook change)": "MA-R4 — Early Signal Matters",
    "i've tried everything, nothing worked, this did (hook and story change)": "MA-R4 — Early Signal Matters",
    "i used to think, why do only i get acne? ": "MA-R2 — Calm Before Clear",
    "i tried all the derma treatments, nothing worked": "MA-R4 — Early Signal Matters",
    "hormonal acne since 10th standard": "MA-R1 — Wrong Tool (SA vs BPO mechanism)",
    "i did all the skin treatments, but, nothing worked. with rcf, i saw results in 8 days": "MA-R4 — Early Signal Matters",
    "got acne night before my engagement": "MA-R2 — Calm Before Clear",
}

HOOK_MAP = {
    "negative": "H3 — Pain Statement",
    "positive": "H6 — Social Proof",
}

STATUS_MAP = {
    "published":   "Published",
    "with editor": "Draft",
    "":            "Draft",
}

PERF_COLS = [
    "ROAS", "Amount Spent", "Revenue", "Avg Cost Per Reach",
    "CTR", "CPC", "ATC Rate", "CVR", "AOV", "Hook Rate", "Hold Rate", "CAC",
    "ROAS (L30)", "Amount Spent (L30)", "Revenue (L30)", "Avg Cost Per Reach (L30)",
    "CTR (L30)", "CPC (L30)", "ATC Rate (L30)", "CVR (L30)", "AOV (L30)",
    "Hook Rate (L30)", "Hold Rate (L30)", "CAC (L30)",
    "ROAS (L7)", "Amount Spent (L7)", "Revenue (L7)", "Avg Cost Per Reach (L7)",
    "CTR (L7)", "CPC (L7)", "ATC Rate (L7)", "CVR (L7)", "AOV (L7)",
    "Hook Rate (L7)", "Hold Rate (L7)", "CAC (L7)",
]

st.set_page_config(page_title="Import Legacy Data — Creative OS", layout="wide")
st.title("Import Legacy Consumer Testimonials")
st.caption("One-time migration of your existing tracker into the new system.")

# ── STEP 1: load legacy sheet ──────────────────────────────────────────────────
st.info(
    "**Before importing:** Make sure you've shared the legacy Google Sheet with "
    "`creative-os-bot@streamlit-app-tss.iam.gserviceaccount.com` (Editor access)."
)

if st.button("🔄 Load legacy sheet"):
    try:
        ws = _client().open_by_key(LEGACY_SHEET_ID).sheet1
        raw = ws.get_all_values()
        st.session_state["legacy_raw"] = raw
        st.success(f"Loaded {len(raw)} rows.")
    except Exception as e:
        st.error(f"Could not load: {e}")

if "legacy_raw" not in st.session_state:
    st.stop()

raw = st.session_state["legacy_raw"]

# Find header row (the one containing "Client Details")
header_row_idx = next(
    (i for i, row in enumerate(raw) if "Client Details" in row), None
)
if header_row_idx is None:
    st.error("Could not find header row. Check the sheet structure.")
    st.stop()

headers = raw[header_row_idx]
data_rows = [r for r in raw[header_row_idx + 1:] if any(c.strip() for c in r)]

def cell(row, col_name):
    try:
        return row[headers.index(col_name)].strip()
    except (ValueError, IndexError):
        return ""

# ── STEP 2: build preview DataFrame ───────────────────────────────────────────
preview_rows = []
for row in data_rows:
    name     = cell(row, "Client Details")
    product_raw = cell(row, "Product")
    if not name:
        continue

    product = "RCF" if product_raw.upper() in ("RCF", "") else (
        "Clear Protect Gel Sunscreen" if "sunscreen" in product_raw.lower() else "RCF"
    )

    old_angle  = cell(row, "Marketing Angle").lower().strip()
    new_angle  = ANGLE_MAP.get(old_angle, ANGLES_RCF[0])
    hook_raw   = cell(row, "HOOK TYPE").lower().strip()
    hook       = HOOK_MAP.get(hook_raw, "H3 — Pain Statement")
    status_raw = cell(row, "Status").lower().strip()
    status     = STATUS_MAP.get(status_raw, "Draft")

    pub_date = cell(row, "Published date") or cell(row, "Publish Date")

    notes_parts = [
        f"Legacy name: {cell(row, 'Video name')}",
        f"Pillar: {cell(row, 'Pillar')}",
        f"Old angle: {cell(row, 'Marketing Angle')}",
        f"Situation: {cell(row, 'Situation')}",
        f"Hook script: {cell(row, 'HOOK')}",
        f"POC: {cell(row, 'POC')}",
        f"Notes: {cell(row, 'NOTES')}",
    ]
    notes = " | ".join(p for p in notes_parts if not p.endswith(": "))

    preview_rows.append({
        "Consumer": name,
        "Product": product,
        "Old Angle": cell(row, "Marketing Angle"),
        "→ New Angle": new_angle,
        "Hook Type": hook,
        "Status": status,
        "Published Date": pub_date,
        "Meta Ad ID": cell(row, "Perf AD Code"),
        "Drive Link": cell(row, "Video link"),
        "_notes": notes,
        "_row": row,
        "_old_angle_raw": old_angle,
        "_product_raw": product_raw,
    })

st.subheader(f"Preview — {len(preview_rows)} assets found")

st.dataframe(
    pd.DataFrame(preview_rows)[
        ["Consumer", "Product", "Old Angle", "→ New Angle", "Hook Type", "Status", "Published Date", "Meta Ad ID"]
    ],
    use_container_width=True,
    hide_index=True,
)

# ── MAPPING NOTICE ─────────────────────────────────────────────────────────────
with st.expander("ℹ️ What's been auto-mapped — review before importing"):
    st.markdown("""
| Field | How it's mapped |
|---|---|
| Creative Type | Consumer Testimonial (all) |
| Bucket | Performance |
| Channel | In-house |
| Product | RCF (default; update "LPP" / Kit rows after import) |
| Marketing Angle | Best-guess from old angle text — **review each one** |
| Hook Type | Negative → H3 Pain Statement, Positive → H6 Social Proof |
| Status | Published → Published, With Editor → Draft |
| Cohort | **C1 — Hormonal / Painful Inflamed (placeholder — update after import)** |
| Belief | **B1 — Wrong Tool, Not Wrong You (placeholder — update after import)** |
| Funnel Stage | TOFU |
| Creator Archetype | LEV — Lived Experience Validator |
| Influence Mode | M1 — Permission / De-risking |
| Emotional Arc | E1 — Pain → Relief |
| CTA Style | C2 — Creator Natural CTA |
| Visual Style | N/A — video |
| Performance columns | Copied directly |
| Notes | Legacy name + pillar + old angle + situation + hook script preserved |
""")

st.warning(
    "⚠️ After importing, go to Asset Registry and update **Cohort** and **Belief** "
    "for each asset — these can't be auto-mapped reliably."
)

# ── STEP 3: import ─────────────────────────────────────────────────────────────
st.markdown("---")

existing_assets = load_assets()
existing_ids = existing_assets["Asset ID"].tolist() if not existing_assets.empty else []

if st.button("✅ Import all assets", type="primary"):
    errors = []
    success_count = 0
    running_ids = list(existing_ids)

    progress = st.progress(0)
    status_text = st.empty()

    for i, p in enumerate(preview_rows):
        row = p["_row"]
        progress.progress((i + 1) / len(preview_rows))
        status_text.text(f"Importing {i+1}/{len(preview_rows)}: {p['Consumer']}…")

        asset_id = next_asset_id(p["Product"], "Consumer Testimonial", running_ids)
        running_ids.append(asset_id)

        def perf(col):
            try:
                val = row[headers.index(col)].strip().replace("₹", "").replace(",", "").replace("%", "")
                return float(val) if val else ""
            except (ValueError, IndexError):
                return ""

        record = {
            "Asset ID":                asset_id,
            "Parent Asset ID":         "",
            "Variant #":               "A",
            "What's Different":        "",
            "A/B Pair ID":             "",
            "Status":                  p["Status"],
            "Created Date":            "",
            "Published Date":          p["Published Date"],
            "Product":                 p["Product"],
            "Bucket":                  "Performance",
            "Channel":                 "In-house",
            "Creative Type":           "Consumer Testimonial",
            "Cohort":                  "C1 — Hormonal / Painful Inflamed",
            "Belief":                  "B1 — Wrong Tool, Not Wrong You",
            "Marketing Angle":         p["→ New Angle"],
            "Situational Driver":      "None",
            "Hook Type":               p["Hook Type"],
            "Emotional Arc":           "E1 — Pain → Relief",
            "Funnel Stage":            "TOFU",
            "Creator Archetype":       "LEV — Lived Experience Validator",
            "Influence Mode":          "M1 — Permission / De-risking",
            "Visual Style":            "N/A — video",
            "CTA Style":               "C2 — Creator Natural CTA",
            "Source Interview ID":     "",
            "Creator / Consumer Name": p["Consumer"],
            "Experiment ID":           "",
            "Meta Ad ID":              p["Meta Ad ID"],
            "Campaign Name":           "",
            "Ad Set Name":             "",
            "Drive Link":              p["Drive Link"],
            "Brief Link":              "",
            "Notes":                   p["_notes"],
            **{col: perf(col) for col in PERF_COLS},
        }

        try:
            save_asset(record)
            success_count += 1
        except Exception as e:
            errors.append(f"{p['Consumer']}: {e}")

    progress.progress(1.0)
    status_text.empty()

    if success_count:
        st.success(f"✅ Imported {success_count} assets successfully.")
        st.info(
            "Next steps:\n"
            "1. Go to **Asset Registry** and filter by Cohort = C1 to see all imported assets\n"
            "2. Update **Cohort** and **Belief** for each asset based on the consumer's story\n"
            "3. Check **Marketing Angle** mappings — highlighted in the preview above\n"
            "4. Add **Source Interview** records in Source Library for each unique consumer"
        )
    if errors:
        st.error("Some rows failed:")
        for e in errors:
            st.write(e)
