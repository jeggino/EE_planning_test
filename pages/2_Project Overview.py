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
            f"### 🪟 Window {i}}"
        )

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Protocols",
                cluster["Protocols"]
            )

        with col2:
            st.metric(
                "Minimum Visits",
                cluster["Minimum Visits"]
            )

        with col3:
            st.metric(
                "Evening Visits",
                cluster["Evening Visits"]
            )

        with col4:
            st.metric(
                "Morning Visits",
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
        
        st.write(
            f"📅 **Window Coverage:** "
            f"{pretty_date(cluster['Window Coverage'].split(' → ')[0])}"
            f" → "
            f"{pretty_date(cluster['Window Coverage'].split(' → ')[1])}"
        )
        
        overlap_days = (
            cluster["Overlap End"]
            - cluster["Overlap Start"]
        ).days
        
        st.write(
            f"🎯 **Overlap Window:** "
            f"{pretty_date(cluster['Overlap Window'].split(' → ')[0])}"
            f" → "
            f"{pretty_date(cluster['Overlap Window'].split(' → ')[1])}"
            f" ({overlap_days} days)"
        )
            

        # ------------------------------------------
        # TIMELINE DATA
        # ------------------------------------------

        timeline_rows = []

        for p in cluster["Protocol Details"]:

            min_days = p.get("min_days")
            
            try:
                min_days = int(min_days)
            except (TypeError, ValueError):
                min_days = "N/A"            

            timeline_rows.append(
                {
                    "Protocol":
                        f"{p['species']} | {p['function']}",

                    "Species":
                        p["species"],

                    "Function":
                        p["function"],

                    "Timing":
                        (
                            p.get("timing")
                            if p.get("timing")
                            else "Any"
                        ),

                    "Evening":
                        p["evening"],

                    "Morning":
                        p["morning"],

                    "Free":
                        p["free"],

                    "MinDays": min_days,

   
                    "SurveyPeriod":
                        f"{pretty_date(p['start'])}"
                        " → "
                        f"{pretty_date(p['end'])}",

                    "Start":
                        datetime.strptime(
                            p["start"],
                            "%m-%d"
                        ).replace(
                            year=2025
                        ),

                    "End":
                        datetime.strptime(
                            p["end"],
                            "%m-%d"
                        ).replace(
                            year=2025
                        ),
                }
            )

        timeline_df = pd.DataFrame(
            timeline_rows
        )

        overlap_start_str = (
            cluster["Overlap Window"]
            .split(" → ")[0]
        )

        overlap_end_str = (
            cluster["Overlap Window"]
            .split(" → ")[1]
        )

        overlap_start = datetime.strptime(
            overlap_start_str,
            "%m-%d"
        ).replace(year=2025)

        overlap_end = datetime.strptime(
            overlap_end_str,
            "%m-%d"
        ).replace(year=2025)

        with st.container(border=True):

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
                    "MinDays"
                ]
            )

            fig.update_traces(
                width=0.28,
                hovertemplate=
                "<b>%{customdata[0]}</b><br><br>"
                "Function: %{customdata[1]}<br>"
                "Survey Period: %{customdata[2]}<br>"
                "Timing: %{customdata[3]}<br><br>"
                "🌙 Evening: %{customdata[4]}<br>"
                "☀️ Morning: %{customdata[5]}<br>"
                "🔄 Free: %{customdata[6]}<br>"
                "⏱ Min Days: %{customdata[7]}"
                "<extra></extra>"

            )

            fig.add_vrect(
                x0=overlap_start,
                x1=overlap_end,
                fillcolor="#22c55e",
                opacity=0.25,
                line_width=2,
                line_color="#16a34a",
                layer="below"
            )

            fig.update_yaxes(
                autorange="reversed",
                title=None
            )

            fig.update_xaxes(
                tickformat="%b"
            )

            fig.update_layout(
                showlegend=True,
                legend_title="Species",
                height=max(
                    180,
                    len(timeline_df) * 42
                ),
                margin=dict(
                    l=10,
                    r=10,
                    t=10,
                    b=10
                )
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )



        if cluster["Additional Free Visits"] > 0:
            st.warning(
                f"Additional Free Visits Required: "
                f"{cluster['Additional Free Visits']}"
            )
