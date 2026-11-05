import streamlit as st

st.title("✅ Validation")

st.info(
    "Protocol validation will be available here."
)

st.subheader("Validation Checks")

st.checkbox(
    "Survey Period",
    disabled=True
)

st.checkbox(
    "Required Number of Rounds",
    disabled=True
)

st.checkbox(
    "Minimum Days Between Surveys",
    disabled=True
)

st.checkbox(
    "June Requirement",
    disabled=True
)

st.checkbox(
    "Weather Requirements",
    disabled=True
)
