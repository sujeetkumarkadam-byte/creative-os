import streamlit as st

st.set_page_config(
    page_title="Creative OS — The Solved Skin",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    [data-testid="stSidebar"] { background: #0F6E56; }
    [data-testid="stSidebar"] * { color: white !important; }
    [data-testid="stSidebar"] .stSelectbox label { color: white !important; }
    h1, h2, h3 { color: #0F6E56; }
    .block-container { padding-top: 2rem; }
    div[data-testid="metric-container"] {
        background: #F2FAF7;
        border: 1px solid #C8E6DF;
        border-radius: 10px;
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("Creative OS")
st.caption("The Solved Skin — Creative Intelligence Platform")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.info("**📋 Log Asset**\n\nAdd a new video or static with full taxonomy tags.")
with col2:
    st.info("**📊 Weekly Dashboard**\n\nVolume by product, type, angle and cohort. Built for Monday.")
with col3:
    st.info("**🗂 Asset Registry**\n\nFull filterable table of every asset ever logged.")
with col4:
    st.info("**🧪 Experiment Log**\n\nPlan and track intentional tests.")

st.markdown("---")
st.markdown("#### Navigate using the sidebar ←")
st.markdown(
    "First time? Run **Setup** from the sidebar to initialise your Google Sheet."
)

# First-run setup button
if st.button("⚙️ Initialise Google Sheet (run once on first setup)"):
    from utils.sheets import initialise_sheets
    with st.spinner("Creating sheets…"):
        try:
            initialise_sheets()
            st.success("All sheets created successfully. You're ready to go.")
        except Exception as e:
            st.error(f"Setup failed: {e}")
            st.info("Check that your secrets.toml is correct and the service account has edit access to the spreadsheet.")
