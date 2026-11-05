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

# ----------------------------------
# OPTIMIZER INPUT
# ----------------------------------

st.subheader("🧠 Optimizer Input")

optimizer_rows = []

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    rounds = protocol["rounds"]

    optimizer_rows.append(
        {
            "Species": species,
            "Function": function,
            "Start": protocol["survey_period"]["start"],
            "End": protocol["survey_period"]["end"],
            "Evening": rounds["mandatory_evening"],
            "Morning": rounds["mandatory_morning"],
            "Free": rounds["free_rounds"],
            "Min Days": protocol["min_days_between"]
        }
    )

optimizer_df = pd.DataFrame(optimizer_rows)

st.dataframe(
    optimizer_df,
    use_container_width=True
)

# ----------------------------------
# SIMPLE FIRST OPTIMIZATION
# ----------------------------------

st.subheader("📈 Preliminary Optimization")

max_evening = optimizer_df["Evening"].max()
max_morning = optimizer_df["Morning"].max()
max_free = optimizer_df["Free"].max()

covered_free = max_evening + max_morning

remaining_free = max(
    0,
    max_free - covered_free
)

minimum_visits = (
    max_evening
    + max_morning
    + remaining_free
)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Evening Visits",
        max_evening
    )

with col2:
    st.metric(
        "Morning Visits",
        max_morning
    )

with col3:
    st.metric(
        "Free Visits",
        max_free
    )

with col4:
    st.metric(
        "Minimum Visits",
        minimum_visits
    )

st.info(
    """
    This is only a preliminary calculation.

    Next version:
    - Detect overlapping survey periods
    - Build survey clusters
    - Respect min_days_between
    - Respect June requirements
    - Respect kraamperiode requirements
    - Generate actual survey dates
    """
)

st.subheader("Protocol Matrix")

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    st.write(
        species,
        function,
        protocol["survey_period"]["start"],
        protocol["survey_period"]["end"],
        protocol["rounds"]
    )

