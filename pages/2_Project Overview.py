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

st.caption(
    """
    Select a project to open its planning dashboard. After choosing a project, three sections will appear below. The first section shows all species and ecological functions that must be surveyed, together with their survey windows and protocol requirements. The second section provides an overview of the optimized survey periods, helping you understand when fieldwork can be planned most efficiently. The third section allows you to schedule individual survey rounds by selecting a period, survey type, and date. This planning information enables project managers and ecologists to monitor survey progress and track the status of the research throughout the season.
    """
)

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

# col1, col2, col3, col4 = st.columns(4)

# with col1:
#     st.metric(
#         "Minimum Visits",
#         result["minimum_visits"]
#     )

# with col2:
#     st.metric(
#         "Evening Visits",
#         result["evening_visits"]
#     )

# with col3:
#     st.metric(
#         "Morning Visits",
#         result["morning_visits"]
#     )

# with col4:
#     st.metric(
#         "Free Visits",
#         result["free_visits"]
#     )
    
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

st.caption(
    """
    This timeline displays the survey windows defined by the applicable protocols. Each bar represents a species-function combination and indicates the period in which surveys are allowed. Hover over a timeline item to view survey requirements, timing rules, weather conditions, and minimum intervals between survey rounds.
    """
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

fig.update_xaxes(
    tickformat="%b"
)

fig.update_yaxes(
    autorange="reversed"
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# --------------------------------------------------
# OPTIMIZED SURVEY PERIODS
# --------------------------------------------------

optimized_periods = result["optimized_periods"]
special_protocols = result["special_protocols"]

period_rows = []

for p in optimized_periods:

    period_rows.append(
        {
            "Period": p["Period"],
            "Start": p["Start"],
            "End": p["End"],
            "Days": p["Days"],
            "Protocols": "<br>".join(
                p["Protocols"]
            ),
            "Type": "Period"
        }
    )

for p in special_protocols:

    period_rows.append(
        {
            "Period":
                "Meervleermuis | satelliet",

            "Start":
                p["start"],

            "End":
                p["end"],

            "Days":
                (
                    p["end"] - p["start"]
                ).days + 1,

            "Score":
                0,

            "Protocols":
                "meervleermuis | satelliet",

            "Type":
                "Special"
        }
    )

periods_df = pd.DataFrame(
    period_rows
)

# --------------------------------------------------
# OPTIMIZED SURVEY PERIODS
# --------------------------------------------------

period_rows = []

for period in result["optimized_periods"]:

    for p in result["special_protocols"]:
    
        period_rows.append(
            {
                "Period": "Special",
    
                "Label":
                    "Meervleermuis | satelliet",
    
                "Start":
                    pd.to_datetime(
                        p["start"]
                    ),
    
                "End":
                    pd.to_datetime(
                        p["end"]
                    ),
    
                "PeriodLabel":
                    f"{p['start'].strftime('%d %b')} → "
                    f"{p['end'].strftime('%d %b')}",
    
                "Days":
                    (
                        p["end"]
                        - p["start"]
                    ).days + 1,
    
                "Morning": 1,
                "Evening": 0,
                "Flexible": 0,    
                "Protocols":
                    "meervleermuis | satelliet"
            }
        )

    info = period["SurveyInfo"]

    period_rows.append(
        {
            "Period": period["Period"],

            "Label":
                f"{period['Period']} • "
                f"{len(period['Protocols'])} protocols",

            "Start":
                pd.to_datetime(
                    period["Start"]
                ),

            "End":
                pd.to_datetime(
                    period["End"]
                ),

            "PeriodLabel":
                f"{period['Start'].strftime('%d %b')} → "
                f"{period['End'].strftime('%d %b')}",

            "Days":
                period["Days"],

            "Morning":
                info["morning"],

            "Evening":
                info["evening"],

            "Flexible":
                info["extra"],

            "Total":
                info["total"],

            "Protocols":
                "<br>".join(
                    period["Protocols"]
                )
        }
    )

periods_df = pd.DataFrame(
    period_rows
)

if not periods_df.empty:

    periods_df["ProtocolsTooltip"] = (
        "• "
        + periods_df["Protocols"].str.replace(
            "<br>",
            "<br>• "
        )
    )

    period_fig = px.timeline(
        periods_df,
        x_start="Start",
        x_end="End",
        y="Label",
        color="Period",
        custom_data=[
            "PeriodLabel",
            "Days",
            "Morning",
            "Evening",
            "Flexible",
            "Total",
            "ProtocolsTooltip"
        ]
    )

    period_fig.update_traces(
        width=0.25,
        hovertemplate=
            "<b>%{y}</b><br><br>"

            "📅 %{customdata[0]}<br>"
            "⏱ %{customdata[1]} days"

            "<br><br>"

            "<b>Survey Requirements</b><br>"

            "☀️ Morning: %{customdata[2]}<br>"
            "🌙 Evening: %{customdata[3]}<br>"
            "🔄 Flexible: %{customdata[4]}<br>"

            "<br><br>"

            "<b>Protocols</b><br>"
            "%{customdata[6]}"

            "<extra></extra>"
    )

    period_fig.update_xaxes(
        tickformat="%b",
        dtick="M1",
    
        range=[
            datetime(2025, 1, 1),
            datetime(2025, 12, 31)
        ],
    
        ticks="outside",
        ticklen=8,
    
        showgrid=True,
        gridwidth=1,
        gridcolor="rgba(180,180,180,0.25)",
    
        title=None
    )

    period_fig.update_yaxes(
        autorange="reversed",
        title=None
    )

    period_fig.update_layout(
        height=max(
            400,
            len(periods_df) * 110
        ),
        showlegend=False,
        bargap=0.75,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10
        ),
        hoverlabel=dict(
            bgcolor="white",
            font_size=13
        )
    )

    st.subheader(
        "🎯 Optimized Survey Periods"
    )

    st.caption(
        """
        The optimized periods combine overlapping protocol requirements into practical fieldwork windows. These periods help reduce the number of site visits by identifying opportunities to survey multiple species or functions during the same timeframe. Hover over a period to see the required number of morning, evening, and flexible surveys, together with the covered protocols.
        """
    )

    st.plotly_chart(
        period_fig,
        use_container_width=True
    )
# st.subheader(
#     "🎯 Optimized Survey Periods"
# )



# for period in result[
#     "optimized_periods"
# ]:

#     info = period[
#         "SurveyInfo"
#     ]

#     st.markdown(
#         f"### {period['Period']}"
#     )
    
#     col1, col2, col3 = (
#         st.columns(3)
#     )


#     with col1:
#         st.metric(
#             "☀️ Morning",
#             info["morning"]
#         )

#     with col2:
#         st.metric(
#             "🌙 Evening",
#             info["evening"]
#         )

#     with col3:
#         st.metric(
#             "🔄 Flexible",
#             info["extra"]
#         )

#     st.caption(
#         f"📅 "
#         f"{period['Start'].strftime('%d %b')} → "
#         f"{period['End'].strftime('%d %b')}"
#         f" • "
#         f"{period['Days']} days"
#     )

#     st.markdown("---")


# periods_df["Start"] = pd.to_datetime(
#     periods_df["Start"]
# )

# periods_df["End"] = pd.to_datetime(
#     periods_df["End"]
# )


# if periods_df.empty:

#     st.warning(
#         "No optimized periods found."
#     )

# else:

#     periods_df["PeriodLabel"] = (
#         periods_df["Start"].dt.strftime("%d %b")
#         + " → "
#         + periods_df["End"].dt.strftime("%d %b")
#     )

#     periods_df["Morning"] = periods_df.apply(
#         lambda r: next(
#             p["SurveyInfo"]["morning"]
#             for p in result["optimized_periods"]
#             if p["Period"] == r["Period"]
#         ),
#         axis=1
#     )
    
#     periods_df["Evening"] = periods_df.apply(
#         lambda r: next(
#             p["SurveyInfo"]["evening"]
#             for p in result["optimized_periods"]
#             if p["Period"] == r["Period"]
#         ),
#         axis=1
#     )
    
#     periods_df["Flexible"] = periods_df.apply(
#         lambda r: next(
#             p["SurveyInfo"]["extra"]
#             for p in result["optimized_periods"]
#             if p["Period"] == r["Period"]
#         ),
#         axis=1
#     )
    
#     periods_df["Total"] = periods_df.apply(
#         lambda r: next(
#             p["SurveyInfo"]["total"]
#             for p in result["optimized_periods"]
#             if p["Period"] == r["Period"]
#         ),
#         axis=1
#     )

#     periods_df["Label"] = (
#         periods_df["Period"]
#         + " ("
#         + periods_df["Total"].astype(str)
#         + " surveys)"
#     )
    
#     periods_df["ProtocolsTooltip"] = (
#         periods_df["Protocols"]
#         .str.replace("<br>", "<br>• ")
#     )
    
#     periods_df["ProtocolsTooltip"] = (
#         "• "
#         + periods_df["ProtocolsTooltip"]
#     )

#     period_fig = px.timeline(
#         periods_df,
#         x_start="Start",
#         x_end="End",
#         y="Label",
#         color="Period",
#         custom_data=[
#             "PeriodLabel",
#             "Days",
#             "Morning",
#             "Evening",
#             "Flexible",
#             "Total",
#             "ProtocolsTooltip"
#         ]
#     )
    
#     period_fig.update_traces(
#         width=0.28,
#         hovertemplate=
#             "<b>%{y}</b><br><br>"
    
#             "📅 %{customdata[0]}<br>"
#             "⏱ %{customdata[1]} days"
    
#             "<br><br>"
    
#             "<b>Survey Requirements</b><br>"
#             "☀️ Morning: %{customdata[2]}<br>"
#             "🌙 Evening: %{customdata[3]}<br>"
#             "🔄 Flexible: %{customdata[4]}<br>"
#             "🎯 Total: %{customdata[5]}"
    
#             "<br><br>"
    
#             "<b>Protocols</b><br>"
#             "%{customdata[6]}"
    
#             "<extra></extra>"
#     )
    
#     period_fig.update_xaxes(
#         tickformat="%b",
#         dtick="M1",
#         ticks="outside",
#         ticklen=8,
#         showgrid=True,
#         gridwidth=1,
#         gridcolor="rgba(200,200,200,0.25)"
#     )
    
#     period_fig.update_yaxes(
#         autorange="reversed"
#     )
    
#     period_fig.update_layout(
#         height=250,
#         showlegend=False,
#         plot_bgcolor="white",
#         paper_bgcolor="white",
#         bargap=0.65,
#         xaxis_title=None,
#         yaxis_title=None,
#         hoverlabel=dict(
#             bgcolor="white",
#             font_size=13,
#             font_family="Arial"
#         )
#     )
    
#     st.plotly_chart(
#         period_fig,
#         use_container_width=True
#     )

# --------------------------------------------------
# OPTIMIZED SURVEY PLAN
# --------------------------------------------------

# st.subheader(
#     "🎯 Optimized Survey Plan"
# )

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

# edited_plan = st.data_editor(
#     survey_df,
#     use_container_width=True,
#     num_rows="dynamic",
#     hide_index=True
# )

edited_plan = survey_df

# --------------------------------------------------
# SURVEY TIMELINE
# --------------------------------------------------

st.subheader("📍 Planned Survey Schedule")

st.caption(
    """
    Use this section to plan individual survey visits. First select an available survey period, then choose one of the survey rounds required within that period, and finally select a survey date. Only dates within the selected survey period can be chosen, ensuring that all planned visits remain compliant with the survey protocol requirements.
    """
)


# --------------------------------------------------
# BUILD PERIOD DATA
# --------------------------------------------------

period_data = {}

# Normal optimized periods
for period in result["optimized_periods"]:

    info = period["SurveyInfo"]

    surveys = []

    for i in range(info["morning"]):
        surveys.append(f"Morning {i+1}")

    for i in range(info["evening"]):
        surveys.append(f"Evening {i+1}")

    for i in range(info["extra"]):
        surveys.append(f"Flexible {i+1}")

    period_data[period["Period"]] = {
        "surveys": surveys,
        "start": period["Start"],
        "end": period["End"]
    }

# Special protocols
for special in result["special_protocols"]:

    period_data["Meervleermuis | satelliet"] = {
        "surveys": ["Morning 1"],
        "start": special["start"],
        "end": special["end"]
    }

# --------------------------------------------------
# STEP 1 - PERIOD
# --------------------------------------------------

selected_period = st.selectbox(
    "1️⃣ Select Period",
    list(period_data.keys())
)

period_info = period_data[selected_period]

# --------------------------------------------------
# STEP 2 - SURVEY
# --------------------------------------------------

selected_survey = st.selectbox(
    "2️⃣ Select Survey",
    period_info["surveys"]
)

# --------------------------------------------------
# STEP 3 - DATE
# --------------------------------------------------

date_label = (
    f"3️⃣ Select Date "
    f"({period_info['start'].strftime('%d %b')} → "
    f"{period_info['end'].strftime('%d %b')})"
)

selected_date = st.date_input(
    date_label,
    value=period_info["start"],
    min_value=period_info["start"],
    max_value=period_info["end"]
)


# --------------------------------------------------
# SAVE TO SUPABASE
# --------------------------------------------------

if st.button("💾 Save Survey Planning"):

    try:

        supabase.table(
            "planning_surveys"
        ).insert(
            {
                "project": selected_project_name,
                "period": selected_period,
                "survey": selected_survey,
                "date": selected_date.isoformat(),
                "user": "unknown"
            }
        ).execute()

        st.success(
            f"""
            "Survey planning successfully saved."
            
            Period: **{selected_period}**
        
            Survey: **{selected_survey}**
        
            Date: **{selected_date.strftime('%d %b %Y')}**
            """
        )
        
    except Exception:

        st.error(
            "This survey has already been planned for this project and period."
        )




# if not edited_plan.empty:

#     chart_df = edited_plan.copy()

#     chart_df["Date"] = pd.to_datetime(
#         chart_df["Date"]
#     )

#     st.subheader(
#         "📍 Planned Survey Schedule"
#     )

#     survey_fig = px.strip(
#         chart_df,
#         x="Date",
#         y="Type",
#         color="Type",
#         hover_data=[
#             "Protocols Covered",
#             "Protocols"
#         ]
#     )
    
#     survey_fig.update_traces(
#         marker=dict(
#             size=15,
#             line=dict(width=1)
#         )
#     )
    
#     survey_fig.update_xaxes(
#         tickformat="%d-%b"
#     )
    
#     survey_fig.update_layout(
#         height=300,
#         xaxis_title="Survey Date",
#         yaxis_title="Survey Type"
#     )
    
#     st.plotly_chart(
#         survey_fig,
#         use_container_width=True
#     )

