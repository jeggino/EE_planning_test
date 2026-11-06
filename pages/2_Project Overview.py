import streamlit as st
import pandas as pd

from database.supabase import get_supabase
from utils.protocol_loader import load_protocols
from planner.optimizer import get_survey_demand 

from datetime import date, timedelta, datetime
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Project Overview",
    layout="wide"
)


def pretty_date(mmdd):
    try:
        return datetime.strptime(
            mmdd,
            "%m-%d"
        ).strftime("%b %d")
    except:
        return mmdd

st.title("🧠 Project Overview")

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


result = get_survey_demand(
    project,
    PROTOCOLS
)

col1, col2, col3, col4 = st.columns(4)

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

with col4:
    st.metric(
        "Free Visits",
        result["free_visits"]
    )
    
# --------------------------------------------------
# PROTOCOL TIMELINE
# --------------------------------------------------

st.divider()

timeline_rows = []

for p in result["protocols"]:

    min_days = p.get("min_days")

    try:
        min_days = int(min_days)
    except:
        min_days = "N/A"

    timing = p.get(
        "timing",
        {}
    )

    if timing:
        timing_text = (
            f"Start Rule: "
            f"{timing.get('start_rule', '-')}"
            f" | End Rule: "
            f"{timing.get('end_rule', '-')}"
        )
    else:
        timing_text = "None"

    weather = p.get(
        "weather",
        {}
    )

    weather_text = (
        f"Temp: {weather.get('temperature', '-')}"
        f" | Wind: {weather.get('wind', '-')}"
        f" | Rain: {weather.get('precipitation', '-')}"
    )

    timeline_rows.append(
        {
            "Protocol":
                f"{p['species']} | {p['function']}",

            "Species":
                p["species"],

            "SurveyPeriod":
                f"{p['start'].strftime('%d %b')}"
                f" → "
                f"{p['end'].strftime('%d %b')}",


            "Start": pd.to_datetime(
                p["start"]
            ),
            
            "End": pd.to_datetime(
                p["end"]
            ),

            "Evening":
                p["evening"],

            "Morning":
                p["morning"],

            "Free":
                p["free"],

            "MinDays":
                min_days,

            "Timing":
                timing_text,

            "Weather":
                weather_text
        }
    )

timeline_df = pd.DataFrame(
    timeline_rows
)

st.subheader(
    "📅 Protocol Survey Periods"
)

fig = px.timeline(
    timeline_df,
    x_start="Start",
    x_end="End",
    y="Protocol",
    color="Species",
    custom_data=[
        "SurveyPeriod",
        "Evening",
        "Morning",
        "Free",
        "MinDays",
        "Timing",
        "Weather"
    ]
)

fig.update_traces(
    hovertemplate=
        "<b>%{y}</b><br><br>"

        "Survey Period: %{customdata[0]}<br><br>"

        "🌙 Evening: %{customdata[1]}<br>"
        "☀️ Morning: %{customdata[2]}<br>"
        "🔄 Free: %{customdata[3]}<br>"
        "⏱ Min Days: %{customdata[4]}<br><br>"

        "<b>Timing</b><br>"
        "%{customdata[5]}<br><br>"

        "<b>Weather</b><br>"
        "%{customdata[6]}"

        "<extra></extra>"
)

fig.update_yaxes(
    autorange="reversed"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------------------------
# OPTIMIZED SURVEY PLAN
# --------------------------------------------------

st.subheader(
    "🎯 Optimized Survey Plan"
)

survey_rows = []

for survey in result["survey_plan"]:

    survey_rows.append(
        {
            "Date":
                survey["date"],

            "Type":
                survey["type"].capitalize(),

            "Protocols Covered":
                len(
                    survey["protocols"]
                ),

            "Protocols":
                ", ".join(
                    sorted(
                        survey["protocols"]
                    )
                )
        }
    )

survey_df = pd.DataFrame(
    survey_rows
)

survey_df = survey_df.sort_values(
    "Date"
)

edited_plan = st.data_editor(
    survey_df,
    use_container_width=True,
    num_rows="dynamic",
    hide_index=True
)

# --------------------------------------------------
# SURVEY TIMELINE
# --------------------------------------------------

if not edited_plan.empty:

    chart_df = edited_plan.copy()

    chart_df["Date"] = pd.to_datetime(
        chart_df["Date"]
    )

    st.subheader(
        "📍 Planned Survey Schedule"
    )

    survey_fig = px.scatter(
        chart_df,
        x="Date",
        y="Type",
        color="Type",
        size="Protocols Covered",
        hover_data=[
            "Protocols Covered",
            "Protocols"
        ]
    )
    
    survey_fig.update_traces(
        marker=dict(
            size=18,
            line=dict(width=1)
        )
    )
    
    survey_fig.update_layout(
        height=600,
        xaxis_title="Survey Date",
        yaxis_title="Survey Type"
    )


    survey_fig.update_layout(
        height=500
    )

    st.plotly_chart(
        survey_fig,
        use_container_width=True
    )

# --------------------------------------------------
# PLAN SUMMARY
# --------------------------------------------------

st.subheader(
    "📊 Plan Summary"
)

st.dataframe(
    pd.DataFrame(
        [
            {
                "Protocol":
                    f"{p['species']} | {p['function']}",

                "Evening":
                    p["evening"],

                "Morning":
                    p["morning"],

                "Free":
                    p["free"],

                "Min Days":
                    p["min_days"]
            }
            for p in result["protocols"]
        ]
    ),
    use_container_width=True,
    hide_index=True
)

summary_col1, summary_col2, summary_col3 = (
    st.columns(3)
)

with summary_col1:
    st.metric(
        "Survey Visits",
        len(
            result["survey_plan"]
        )
    )

with summary_col2:
    st.metric(
        "Evening Surveys",
        len(
            [
                s
                for s in result["survey_plan"]
                if s["type"] == "evening"
            ]
        )
    )

with summary_col3:
    st.metric(
        "Morning Surveys",
        len(
            [
                s
                for s in result["survey_plan"]
                if s["type"] == "morning"
            ]
        )
    )





