import streamlit as st

from database.supabase import get_supabase
from utils.protocol_loader import load_protocols

st.title("📊 Project Overview")

supabase = get_supabase()
PROTOCOLS = load_protocols()

# ----------------------------------
# LOAD PROJECTS
# ----------------------------------

projects = (
    supabase
    .table("planning_projects")
    .select("*")
    .execute()
)

if not projects.data:
    st.warning("No projects found.")
    st.stop()

project_names = [
    p["project_name"]  # replace with "name" if needed
    for p in projects.data
]

selected_project_name = st.selectbox(
    "Select Project",
    project_names
)

project = next(
    p for p in projects.data
    if p["project_name"] == selected_project_name
)

# ----------------------------------
# PROJECT INFO
# ----------------------------------

st.subheader("Protocols")

total_surveys = 0

overview = []

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    rounds = protocol["rounds"]

    n_surveys = (
        rounds["mandatory_evening"]
        + rounds["mandatory_morning"]
        + rounds["free_rounds"]
    )

    total_surveys += n_surveys

    overview.append({
        "Species": species,
        "Function": function,
        "Required Surveys": n_surveys,
        "Period":
            f"{protocol['survey_period']['start']} "
            f"→ "
            f"{protocol['survey_period']['end']}",
        "Min days":
            protocol["min_days_between"]
    })

st.dataframe(
    overview,
    use_container_width=True
)

st.metric(
    "Total Required Surveys",
    total_surveys
)
