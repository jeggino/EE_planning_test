import streamlit as st

st.markdown("""
<style>
a[href*="github.com"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

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

