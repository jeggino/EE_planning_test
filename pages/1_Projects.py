import streamlit as st

from data.protocols import PROTOCOLS

st.title("📋 Projects")

project_name = st.text_input(
    "Project Name"
)

species = st.multiselect(
    "Select Species",
    sorted(PROTOCOLS.keys())
)

selected_protocols = []

for sp in species:

    functions = st.multiselect(
        f"Functions - {sp}",
        list(PROTOCOLS[sp].keys()),
        key=sp
    )

    for f in functions:

        selected_protocols.append(
            {
                "species": sp,
                "function": f
            }
        )

st.divider()

st.subheader("Selected Protocols")

st.json(selected_protocols)

if st.button("Create Project"):

    st.success(
        f"Project '{project_name}' created."
    )

    # save to supabase later
