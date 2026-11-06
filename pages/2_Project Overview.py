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
    
for i, cluster in enumerate(result["clusters"], start=1):
    st.divider()
    
    timeline_rows = []
    
    for cluster_idx, cluster in enumerate(
        result["clusters"],
        start=1
    ):
    
        for p in cluster["Protocol Details"]:
    
            min_days = p.get("min_days")
    
            try:
                min_days = int(min_days)
            except:
                min_days = "N/A"
    
            timing = p.get(
                "timing",
                {}
            )
    
            timing_text = (
                "None"
                if not timing else
                f"Start Rule: {timing.get('start_rule', '-')}"
                f" | End Rule: {timing.get('end_rule', '-')}"
            )
    
            weather = p.get(
                "weather",
                {}
            )
    
            weather_text = (
                f"Temp: {weather.get('temperature', '-')}"
                f" | Wind: {weather.get('wind', '-')}"
                f" | Rain: {weather.get('precipitation', '-')}"
            )
    
            special = p.get(
                "special_requirements",
                {}
            )
    
            special_text = ", ".join(
                f"{k}: {v}"
                for k, v in special.items()
            )
    
            if not special_text:
                special_text = "None"
    
            timeline_rows.append(
                {
                    "Protocol":
                        f"{p['species']} | {p['function']}",
    
                    "Species":
                        p["species"],
    
                    "Cluster":
                        f"Window {cluster_idx}",
    
                    "Function":
                        p["function"],
    
                    "Timing":
                        timing_text,
    
                    "Requirements":
                        special_text,
    
                    "Weather":
                        weather_text,
    
                    "Evening":
                        p["evening"],
    
                    "Morning":
                        p["morning"],
    
                    "Free":
                        p["free"],
    
                    "MinDays":
                        min_days,
    
                    "SurveyPeriod":
                        f"{pretty_date(p['start'])}"
                        f" → "
                        f"{pretty_date(p['end'])}",
    
                    "Start":
                        datetime.strptime(
                            p["start"],
                            "%m-%d"
                        ).replace(year=2025),
    
                    "End":
                        datetime.strptime(
                            p["end"],
                            "%m-%d"
                        ).replace(year=2025)
                }
            )
    
    timeline_df = pd.DataFrame(
        timeline_rows
    )
    
    st.subheader(
        "📅 Survey Timeline"
    )
    
    fig = px.timeline(
        timeline_df,
        x_start="Start",
        x_end="End",
        y="Protocol",
        color="Species",
        color_discrete_sequence=
            px.colors.qualitative.Set2,
        custom_data=[
            "Species",
            "Function",
            "SurveyPeriod",
            "Timing",
            "Evening",
            "Morning",
            "Free",
            "MinDays",
            "Requirements",
            "Weather",
            "Cluster"
        ]
    )
    
    fig.update_traces(
        width=0.30,
        hovertemplate=
        "<b>%{customdata[0]}</b><br><br>"
    
        "Function: %{customdata[1]}<br>"
        "Survey Period: %{customdata[2]}<br>"
        "Window: %{customdata[10]}<br><br>"
    
        "<b>Timing</b><br>"
        "%{customdata[3]}<br><br>"
    
        "🌙 Evening: %{customdata[4]}<br>"
        "☀️ Morning: %{customdata[5]}<br>"
        "🔄 Free: %{customdata[6]}<br>"
        "⏱ Min Days: %{customdata[7]}<br><br>"
    
        "<b>Requirements</b><br>"
        "%{customdata[8]}<br><br>"
    
        "<b>Weather</b><br>"
        "%{customdata[9]}"
    
        "<extra></extra>"
    )
    
    for i, cluster in enumerate(
        result["clusters"],
        start=1
    ):
    
        fig.add_vrect(
            x0=cluster["Overlap Start"],
            x1=cluster["Overlap End"],
            fillcolor="green",
            opacity=0.12,
            line_width=0,
            annotation_text=f"W{i}",
            annotation_position="top left"
        )
    
    fig.update_yaxes(
        autorange="reversed",
        title=None
    )
    
    fig.update_layout(
        showlegend=True,
        legend_title="Species",
        height=max(
            450,
            len(timeline_df) * 42
        )
    )
    
    st.plotly_chart(
        fig,
        use_container_width=True
    )
    
    st.subheader(
        "🪟 Survey Windows"
    )
    
    summary_df = pd.DataFrame(
        [
            {
                "Window": f"Window {i}",
                "Protocols":
                    cluster["Protocols"],
                "Minimum Visits":
                    cluster["Minimum Visits"],
                "Evening":
                    cluster["Evening Visits"],
                "Morning":
                    cluster["Morning Visits"],
                "Free":
                    cluster["Additional Free Visits"],
                "Overlap":
                    cluster["Overlap Window"],
                "Coverage":
                    cluster["Window Coverage"]
            }
            for i, cluster in enumerate(
                result["clusters"],
                start=1
            )
        ]
    )
    
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )





