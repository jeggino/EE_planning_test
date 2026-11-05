import streamlit as st
import pandas as pd

from database.supabase import get_supabase
from utils.protocol_loader import load_protocols

st.set_page_config(
    page_title="Project Overview",
    layout="wide"
)

st.title("📊 Project Overview")

# ----------------------------------
# LOAD DATA
# ----------------------------------

supabase = get_supabase()
PROTOCOLS = load_protocols()

projects = (
    supabase
    .table("planning_projects")
    .select("*")
    .execute()
)

if not projects.data:
    st.warning("No projects found.")
    st.stop()

# ----------------------------------
# SELECT PROJECT
# ----------------------------------

project_names = [
    p["project_name"]
    for p in projects.data
]

selected_project_name = st.selectbox(
    "Select Project",
    project_names
)

project = next(
    p
    for p in projects.data
    if p["project_name"] == selected_project_name
)

# ----------------------------------
# PROJECT DETAILS
# ----------------------------------

st.subheader("Project")

st.write(f"**Name:** {selected_project_name}")

# ----------------------------------
# PROTOCOL TABLE
# ----------------------------------

overview = []

total_evening = 0
total_morning = 0
total_free = 0

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    rounds = protocol["rounds"]

    evening = rounds["mandatory_evening"]
    morning = rounds["mandatory_morning"]
    free = rounds["free_rounds"]

    total_evening += evening
    total_morning += morning
    total_free += free

    overview.append(
        {
            "Species": species,
            "Function": function,
            "Survey Start":
                protocol["survey_period"]["start"],

            "Survey End":
                protocol["survey_period"]["end"],

            "Evening":
                evening,

            "Morning":
                morning,

            "Free":
                free,

            "Min Days":
                protocol.get(
                    "min_days_between",
                    "-"
                )
        }
    )

df = pd.DataFrame(overview)

# ----------------------------------
# SUMMARY
# ----------------------------------

st.subheader("Protocol Summary")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Evening Rounds",
        total_evening
    )

with col2:
    st.metric(
        "Morning Rounds",
        total_morning
    )

with col3:
    st.metric(
        "Free Rounds",
        total_free
    )

# ----------------------------------
# PROTOCOL TABLE
# ----------------------------------

st.subheader("Selected Protocols")

st.dataframe(
    df,
    use_container_width=True
)

# ----------------------------------
# DEBUG
# ----------------------------------

with st.expander("Project JSON"):

    st.json(project)
