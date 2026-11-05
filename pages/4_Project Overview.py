import streamlit as st

from database.supabase import get_supabase
from utils.protocol_loader import load_protocols
from planner.optimizer import get_survey_demand

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

# IMPORTANT:
# replace "project_name" with "name"
# if that's the column you actually have

project_names = [
    p["project_name"]
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
# OPTIMIZER
# ----------------------------------

result = get_survey_demand(
    project,      # <-- FIXED
    PROTOCOLS
)

st.metric(
    "Minimum Survey Visits",
    result["minimum_surveys"]
)

st.subheader("Optimizer Details")

st.json(result["details"])

# ----------------------------------
# PROJECT PROTOCOLS
# ----------------------------------

st.subheader("Protocols")

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

    overview.append(
        {
            "Species": species,
            "Function": function,
            "Required Surveys": n_surveys,
            "Period":
                f"{protocol['survey_period']['start']} "
                f"→ "
                f"{protocol['survey_period']['end']}",
            "Min Days":
                protocol["min_days_between"]
        }
    )

st.dataframe(
    overview,
    use_container_width=True
)
