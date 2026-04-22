import streamlit as st
from utils.taxonomy import (
    PRODUCTS, FORMATS, VIDEO_SUBTYPES, STATIC_SUBTYPES,
    HOOK_TYPES, EMOTIONAL_ARCS, FUNNEL_STAGES,
    ARCHETYPES, INFLUENCE_MODES, VISUAL_STYLES, CTA_STYLES,
    get_cohorts, get_angles, get_drivers, get_beliefs,
    code_of, label_of, define,
)

st.set_page_config(page_title="Taxonomy Reference — Creative OS", layout="wide")
st.title("Taxonomy Reference")
st.caption("Every dropdown value in the system, with its definition. Pick a product to scope.")

product = st.selectbox("Product", PRODUCTS, index=0)

st.markdown("---")


def render_section(title: str, items: list, help_text: str = ""):
    """Render a taxonomy section as a clean 3-column table."""
    st.subheader(title)
    if help_text:
        st.caption(help_text)

    rows = []
    for item in items:
        code = code_of(item)
        label = label_of(item)
        definition = define(item) or "_(not defined yet)_"
        rows.append({"Code": code, "Label": label, "Definition": definition})

    if rows:
        import pandas as pd
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("_No entries in this section for this product._")
    st.markdown("")


# ── Product-scoped sections ──────────────────────────────────────────────────
st.header(f"🎯 Scoped to: {product}")

render_section(
    "Cohorts",
    get_cohorts(product),
    "Who is this creative speaking to? The audience segment.",
)

render_section(
    "Beliefs",
    get_beliefs(product),
    "What belief does the creative install / reinforce in the viewer?",
)

render_section(
    "Marketing Angles",
    get_angles(product),
    "The specific message or argument the creative is making.",
)

render_section(
    "Situational Drivers",
    get_drivers(product),
    "The life moment or trigger that brought the consumer to the product today.",
)

# ── Universal sections ───────────────────────────────────────────────────────
st.markdown("---")
st.header("🌐 Universal (all products)")

render_section(
    "Formats",
    FORMATS,
    "Top-level split. Drives which subtype + taxonomy fields the Log form shows.",
)

render_section(
    "Video Subtypes",
    VIDEO_SUBTYPES,
    "Used when Format = Video. What kind of video is it?",
)

render_section(
    "Static Subtypes",
    STATIC_SUBTYPES,
    "Used when Format = Static. What kind of static is it?",
)

render_section(
    "Hook Types (video)",
    HOOK_TYPES,
    "How the first 3 seconds of a video stop the scroll.",
)

render_section(
    "Emotional Arcs",
    EMOTIONAL_ARCS,
    "The emotional journey the creative takes the viewer on — start to end.",
)

render_section(
    "Funnel Stages",
    FUNNEL_STAGES,
    "Where in the buying journey the creative lands.",
)

render_section(
    "Creator Archetypes",
    ARCHETYPES,
    "Who is delivering the message — and why the audience trusts them.",
)

render_section(
    "Influence Modes",
    INFLUENCE_MODES,
    "The psychological job the creative is doing for the viewer.",
)

render_section(
    "Visual Styles (statics)",
    VISUAL_STYLES,
    "The aesthetic treatment of a static. N/A for videos.",
)

render_section(
    "CTA Styles",
    CTA_STYLES,
    "How the creative asks the viewer to take action at the end.",
)

st.markdown("---")
st.caption(
    "Definitions live in `utils/taxonomy.py` → `DEFINITIONS` dict. "
    "Edit that file + push to update. Blank definitions show as _(not defined yet)_."
)
