import streamlit as st
import json
from datetime import datetime

from database.supabase import get_supabase
from utils.protocol_loader import load_protocols


st.title("📅 Planning")

supabase = get_supabase()
PROTOCOLS = load_protocols()


def validate_period(protocol, survey_date):

    start = protocol["survey_period"]["start"]
    end = protocol["survey_period"]["end"]

    year = survey_date.year

    start_date = datetime.strptime(
        f"{year}-{start}",
        "%Y-%m-%d"
    ).date()

    end_date = datetime.strptime(
        f"{year}-{end}",
        "%Y-%m-%d"
    ).date()

    return start_date <= survey_date <= end_date


# --------------------------------
# LOAD PROJECTS
# --------------------------------

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
    p["project_name"]
    for p in projects.data
]

selected_project_name = st.selectbox(
    "Select Project",
    project_names
)

selected_project = next(
    p for p in projects.data
    if p["project_name"] == selected_project_name
)

st.subheader("Selected Protocols")

# --------------------------------
# SELECT DATE
# --------------------------------

survey_date = st.date_input(
    "Survey Date"
)

# --------------------------------
# VALIDATE
# --------------------------------

if st.button("Validate Survey"):

    st.subheader("Validation Results")

    for p in selected_project["protocols"]:

        species = p["species"]
        function = p["function"]

        protocol = PROTOCOLS[species][function]

        valid = validate_period(
            protocol,
            survey_date
        )

        if valid:

            st.success(
                f"{species} - {function}: VALID"
            )

        else:

            start = protocol["survey_period"]["start"]
            end = protocol["survey_period"]["end"]

            st.error(
                f"{species} - {function}: INVALID "
                f"(allowed period: {start} to {end})"
            )
            
