import streamlit as st


st.set_page_config(
    page_title="Creative OS - The Solved Skin",
    page_icon="TSS",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stSidebar"] { background: #10251c; }
    [data-testid="stSidebar"] * { color: white !important; }
    .block-container { padding-top: 1.5rem; max-width: 1280px; }
    h1 { color: #18251f; letter-spacing: -0.05em; font-size: 4rem !important; }
    h2, h3 { color: #18251f; }
    .home-card {
        min-height: 180px;
        border: 1px solid #dae8de;
        border-radius: 22px;
        padding: 1.25rem;
        background: linear-gradient(145deg, #ffffff 0%, #f3faf6 100%);
        box-shadow: 0 14px 34px rgba(31, 49, 39, 0.07);
    }
    .home-card h3 { margin-top: 0; }
    .hero {
        border-radius: 28px;
        padding: 2rem;
        background:
            radial-gradient(circle at 12% 10%, rgba(237, 191, 93, 0.35), transparent 28%),
            radial-gradient(circle at 88% 12%, rgba(77, 156, 127, 0.25), transparent 24%),
            linear-gradient(135deg, #fbfaf4 0%, #edf7f1 100%);
        border: 1px solid #dce9df;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="hero">', unsafe_allow_html=True)
st.title("Creative OS")
st.caption("The Solved Skin creative volume, quality, taxonomy, and performance operating system.")
st.markdown(
    "Track what went live, who made it, what belief it tested, where the source asset lives, "
    "and how it performed without digging through five different sheets."
)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Workflows")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(
        """
        <div class="home-card">
        <h3>Dashboard</h3>
        <p>Choose any date range and review live creative volume across Inhouse, Influencer, and Porcellia.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
        <div class="home-card">
        <h3>Log Live Asset</h3>
        <p>Save in-house videos or promote Stage-1 statics into Master_Asset_Registry with AD CODE and links.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
        <div class="home-card">
        <h3>Asset Registry</h3>
        <p>Deep-dive into in-house assets with taxonomy, previews, source stories, and performance metrics.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with col4:
    st.markdown(
        """
        <div class="home-card">
        <h3>Admin</h3>
        <p>Inspect sheet health, audit mismatches, and review Drive static backlog candidates before writing.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("---")
if st.button("Initialise Google Sheet structure"):
    from utils.sheets import initialise_sheets

    with st.spinner("Checking sheet tabs and Master headers..."):
        try:
            initialise_sheets()
            st.success("Sheet structure is ready.")
        except Exception as exc:
            st.error(f"Setup failed: {exc}")
            st.info("Check Streamlit secrets and ensure the service account has edit access to the spreadsheet.")
