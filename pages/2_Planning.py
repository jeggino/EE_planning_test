import streamlit as st

st.title("📅 Planning")

st.info(
    "Scheduling engine will be added here."
)

st.subheader("Future Features")

st.checkbox(
    "Generate minimum survey rounds",
    value=True,
    disabled=True
)

st.checkbox(
    "Optimize across multiple species",
    value=True,
    disabled=True
)

st.checkbox(
    "Validate June requirements",
    value=True,
    disabled=True
)

st.checkbox(
    "Validate minimum survey interval",
    value=True,
    disabled=True
)
