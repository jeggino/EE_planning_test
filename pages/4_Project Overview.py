import streamlit as st
import pandas as pd

from database.supabase import get_supabase
from utils.protocol_loader import load_protocols
from datetime import date, timedelta, datetime

st.set_page_config(
    page_title="Project Overview",
    layout="wide"
)

st.title("📊 Project Overview")

# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

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

# --------------------------------------------------
# PROJECT SELECTOR
# --------------------------------------------------

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

# --------------------------------------------------
# BUILD PROTOCOL TABLE
# --------------------------------------------------

overview = []

total_evening = 0
total_morning = 0
total_free = 0

starts = []
ends = []
min_days = []

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    rounds = protocol["rounds"]

    evening = rounds["mandatory_evening"]
    morning = rounds["mandatory_morning"]
    free = rounds["free_rounds"]

    start = protocol["survey_period"]["start"]
    end = protocol["survey_period"]["end"]

    min_days_between = protocol["min_days_between"]

    starts.append(start)
    ends.append(end)
    min_days.append(min_days_between)

    total_evening += evening
    total_morning += morning
    total_free += free

    overview.append(
        {
            "Species": species,
            "Function": function,
            "Survey Start": start,
            "Survey End": end,
            "Evening": evening,
            "Morning": morning,
            "Free": free,
            "Min Days": min_days_between
        }
    )

df = pd.DataFrame(overview)

from planner.optimizer import get_survey_demand

result = get_survey_demand(
    project,
    PROTOCOLS
)

st.subheader("🧠 Optimizer")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Minimum Visits",
        result["minimum_visits"]
    )

with col2:
    st.metric(
        "Evening Visits",
        result["evening_visits"]
    )

with col3:
    st.metric(
        "Morning Visits",
        result["morning_visits"]
    )

st.subheader("🗓️ Survey Windows")

for i, cluster in enumerate(result["clusters"], start=1):

    with st.container(border=True):

        st.markdown(
            f"### Window {i}  |  {cluster['Window Coverage']}"
        )

        col1, col2, col3, col4 = st.columns(4)

        col1.metric(
            "Protocols",
            cluster["Protocols"]
        )

        col2.metric(
            "Minimum Visits",
            cluster["Minimum Visits"]
        )

        col3.metric(
            "Evening",
            cluster["Evening Visits"]
        )

        col4.metric(
            "Morning",
            cluster["Morning Visits"]
        )

        st.caption(
            f"Overlap Window: {cluster['Overlap Window']}"
        )

        if cluster["Additional Free Visits"] > 0:
            st.info(
                f"Additional Free Visits Required: "
                f"{cluster['Additional Free Visits']}"
            )

        with st.expander("Protocols Covered"):
            for protocol in cluster["Protocol Details"]:
                st.write(f"• {protocol}")

