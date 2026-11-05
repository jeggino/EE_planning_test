import streamlit as st

from utils.protocol_loader import load_protocols
from database.supabase import get_supabase

PROTOCOLS = load_protocols()
supabase = get_supabase()

st.title("📋 Projects")

project_name = st.text_input(
    "Project Name"
)

selected_species = st.multiselect(
    "Select Species",
    sorted(PROTOCOLS.keys())
)

project_protocols = []

for species in selected_species:

    functions = st.multiselect(
        f"Functions - {species}",
        list(PROTOCOLS[species].keys()),
        key=species
    )

    for function in functions:

        project_protocols.append(
            {
                "species": species,
                "function": function
            }
        )

st.divider()

st.subheader("Selected Protocols")
st.json(project_protocols)

# CREATE PROJECT
if st.button("Create Project"):

    if not project_name:
        st.error("Please enter a project name.")

    elif not project_protocols:
        st.error("Please select at least one protocol.")

    else:

        try:
        
            result = (
                supabase
                .table("planning_projects")
                .insert(
                    {
                        "name": project_name,
                        "protocols": project_protocols
                    }
                )
                .execute()
            )
        
            st.success(f"Project '{project_name}' created.")
        
        except Exception as e:
            st.error(str(e))
            st.write(e)
