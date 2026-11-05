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

# CHANGE project_name -> name if needed

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
# PROJECT INFO
# ----------------------------------

st.subheader("Project")

st.write(f"**Project:** {selected_project_name}")

# ----------------------------------
# PROTOCOLS TABLE
# ----------------------------------

overview = []

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    rounds = protocol["rounds"]

    overview.append(
        {
            "Species": species,
            "Function": function,
            "Evening": rounds["mandatory_evening"],
            "Morning": rounds["mandatory_morning"],
            "Free": rounds["free_rounds"],
            "Period":
                f"{protocol['survey_period']['start']} → "
                f"{protocol['survey_period']['end']}",
            "Min Days":
                protocol["min_days_between"]
        }
    )

st.subheader("Selected Protocols")

st.dataframe(
    overview,
    use_container_width=True
)

# ----------------------------------
# OPTIMIZER
# ----------------------------------

result = get_survey_demand(
    project,
    PROTOCOLS
)

st.subheader("Optimization Result")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Minimum Survey Visits",
        result["minimum_surveys"]
    )

with col2:
    st.metric(
        "Survey Clusters",
        len(result["clusters"])
    )

st.subheader("Survey Clusters")

st.dataframe(
    result["clusters"],
    use_container_width=True
)

# ----------------------------------
# RAW DEBUG
# ----------------------------------

with st.expander("Debug"):
    st.json(result)
