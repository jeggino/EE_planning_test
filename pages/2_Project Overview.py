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
            f"### 🪟 Window {i} | {cluster['Window Coverage']}"
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

        timeline_rows = []
        
        for p in cluster["Protocol Details"]:
        
            timeline_rows.append(
                {
                    "Protocol":
                        f"{p['species']} | {p['function']}",
        
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
        
        fig = px.timeline(
            timeline_df,
            x_start="Start",
            x_end="End",
            y="Protocol",
            color="Protocol"
        )
        
        fig.update_yaxes(
            autorange="reversed"
        )
        
        fig.update_layout(
            showlegend=False,
            height=max(
                250,
                len(timeline_df) * 60
            ),
            margin=dict(
                l=20,
                r=20,
                t=20,
                b=20
            )
        )
        
        st.plotly_chart(
            fig,
            use_container_width=True
        )

        

        with st.expander(
            f"Protocols Covered ({cluster['Protocols']})"
        ):
        
            for protocol in cluster["Protocol Details"]:
        
                with st.container(border=True):
                
                    st.markdown(
                        f"#### 🐾 {protocol['species']}"
                    )
                
                    st.write(
                        f"**Function:** {protocol['function']}"
                    )
                
                    st.write(
                        f"**Survey Period:** "
                        f"{pretty_date(protocol['start'])} → "
                        f"{pretty_date(protocol['end'])}"
                    )
                
                    details1, details2 = st.columns(2)
                
                    with details1:
                        st.write(
                            f"**Timing:** "
                            f"{protocol.get('timing', 'Any')}"
                        )
                
                    with details2:
                
                        min_days = protocol.get("min_days")
                
                        st.write(
                            f"**Min Days Between Visits:** "
                            f"{int(min_days)}"
                            if min_days is not None
                            else "N/A"
                        )
                
                    c1, c2, c3 = st.columns(3)
                
                    with c1:
                        st.metric(
                            "🌙 Evening",
                            protocol["evening"]
                        )
                
                    with c2:
                        st.metric(
                            "☀️ Morning",
                            protocol["morning"]
                        )
                
                    with c3:
                        st.metric(
                            "🔄 Free",
                            protocol["free"]
                        )
