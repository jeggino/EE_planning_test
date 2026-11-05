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

# --------------------------------------------------
# DISPLAY PROTOCOLS
# --------------------------------------------------

st.subheader("Selected Protocols")

st.dataframe(
    df,
    use_container_width=True
)

# --------------------------------------------------
# OPTIMIZER
# --------------------------------------------------

st.subheader("🧠 Optimization")

# Free rounds can be covered by
# evening or morning surveys

evening_required = max(df["Evening"])
morning_required = max(df["Morning"])
free_required = max(df["Free"])

covered_free = (
    evening_required +
    morning_required
)

remaining_free = max(
    0,
    free_required - covered_free
)

minimum_visits = (
    evening_required +
    morning_required +
    remaining_free
)

maximum_min_days = max(
    min_days
)

# --------------------------------------------------
# METRICS
# --------------------------------------------------

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Minimum Visits",
        minimum_visits
    )

with col2:
    st.metric(
        "Evening Visits",
        evening_required
    )

with col3:
    st.metric(
        "Morning Visits",
        morning_required
    )

with col4:
    st.metric(
        "Min Days Between",
        maximum_min_days
    )

# --------------------------------------------------
# EXPLANATION TABLE
# --------------------------------------------------

optimizer_table = pd.DataFrame(
    [
        {
            "Visit Type": "Evening",
            "Visits Needed": evening_required
        },
        {
            "Visit Type": "Morning",
            "Visits Needed": morning_required
        },
        {
            "Visit Type": "Free",
            "Visits Needed": remaining_free
        }
    ]
)

st.subheader("How the optimizer calculated the visits")

st.dataframe(
    optimizer_table,
    use_container_width=True
)

# --------------------------------------------------
# IMPORTANT NOTE
# --------------------------------------------------

st.info(
    """
    Current optimizer version:

    ✅ Considers:
    - Survey period
    - Mandatory evening rounds
    - Mandatory morning rounds
    - Free rounds
    - Minimum days between visits

    ❌ Not yet implemented:
    - Actual date generation
    - June requirements
    - Kraamperiode requirements
    - Multiple overlapping period clusters
    - Automatic calendar creation
    """
)

st.subheader("📅 Proposed Schedule")

year = datetime.now().year

# Use overlap window from all protocols
starts = []
ends = []

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    starts.append(
        datetime.strptime(
            f"{year}-{protocol['survey_period']['start']}",
            "%Y-%m-%d"
        ).date()
    )

    ends.append(
        datetime.strptime(
            f"{year}-{protocol['survey_period']['end']}",
            "%Y-%m-%d"
        ).date()
    )

common_start = max(starts)
common_end = min(ends)

if common_start <= common_end:

    visits = []

    current_date = common_start

    for i in range(evening_required):

        visits.append(
            {
                "Date": current_date,
                "Type": "Evening"
            }
        )

        current_date += timedelta(
            days=maximum_min_days
        )

    for i in range(morning_required):

        visits.append(
            {
                "Date": current_date,
                "Type": "Morning"
            }
        )

        current_date += timedelta(
            days=maximum_min_days
        )

    for i in range(remaining_free):

        visits.append(
            {
                "Date": current_date,
                "Type": "Free"
            }
        )

        current_date += timedelta(
            days=maximum_min_days
        )

    schedule_df = pd.DataFrame(visits)

    st.dataframe(
        schedule_df,
        use_container_width=True
    )

else:

    st.error(
        "No common survey period found."
    )

