import streamlit as st

st.set_page_config(
    page_title="Bat Survey Planner",
    page_icon="🦇",
    layout="wide"
)

st.title("🦇 Bat Survey Planner")

st.markdown(
    """
    Welcome to the Bat Survey Planning Tool.

    This application helps ecologists:

    - Create survey projects
    - Select species and functions
    - Generate compliant survey schedules
    - Validate survey protocols
    - Optimize survey effort across multiple species

    Use the menu on the left to get started.
    """
)

col1, col2, col3 = st.columns(3)

with col1:
    st.info("📋 Create Projects")

with col2:
    st.info("📅 Generate Planning")

with col3:
    st.info("✅ Validate Protocols")
