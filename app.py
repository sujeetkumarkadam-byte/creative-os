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
    st.info("**📋 Log Live Asset**\n\nLog new inhouse videos directly or promote statics from Stage-1 briefs.")
with col2:
    st.info("**📊 Dashboard**\n\nOne merged live view for volume, source split, format mix, and inhouse taxonomy coverage.")
with col3:
    st.info("**🗂 Asset Registry**\n\nClean detailed inspector for any live inhouse asset, including links and performance.")
with col4:
    st.info("**🛠 Admin / Backlog**\n\nRun migrations, inspect sheets, and retro-tag already-live inhouse backlog assets.")

st.markdown("---")
st.markdown("#### Navigate using the sidebar ←")
st.markdown(
    "For taxonomy definitions, use **Taxonomy Reference**. For one-off live backlog cleanup, use **Admin / Diagnostics**."
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
