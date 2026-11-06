from datetime import datetime, timedelta

YEAR = 2025


def mmdd_to_date(mmdd):
    return datetime.strptime(
        f"{YEAR}-{mmdd}",
        "%Y-%m-%d"
    ).date()


def date_to_mmdd(date_obj):
    return date_obj.strftime("%m-%d")


def schedule_protocol(protocol):
    """
    Create survey visits for a protocol.

    Rules:
    - Free rounds become evening rounds whenever possible.
    - Minimum days applies to ALL visits.
    """

    visits = []

    start = protocol["start"]

    min_days = protocol.get("min_days")

    try:
        min_days = int(min_days)
    except:
        min_days = 0

    interval = min_days + 1

    sequence = []

    sequence.extend(
        ["evening"] * protocol["evening"]
    )

    sequence.extend(
        ["morning"] * protocol["morning"]
    )

    sequence.extend(
        ["evening"] * protocol["free"]
    )

    for idx, survey_type in enumerate(
        sequence
    ):

        survey_date = (
            start +
            timedelta(days=idx * interval)
        )

        if survey_date > protocol["end"]:
            survey_date = protocol["end"]

        visits.append(
            {
                "date": survey_date,
                "type": survey_type,
                "species": protocol["species"],
                "function": protocol["function"]
            }
        )

    return visits


def merge_visits(visits):
    """
    Merge surveys on same day + type.
    """

    grouped = {}

    for visit in visits:

        key = (
            visit["date"],
            visit["type"]
        )

        if key not in grouped:

            grouped[key] = {
                "date": visit["date"],
                "type": visit["type"],
                "protocols": []
            }

        grouped[key]["protocols"].append(
            f"{visit['species']} | "
            f"{visit['function']}"
        )

    merged = sorted(
        grouped.values(),
        key=lambda x: (
            x["date"],
            x["type"]
        )
    )

    return merged

from collections import defaultdict


def build_requirements(protocols_data):

    requirements = []

    for protocol_id, p in enumerate(
        protocols_data
    ):

        visit_number = 1

        # Evening visits

        for _ in range(
            p["evening"]
        ):

            requirements.append(
                {
                    "protocol_id":
                        protocol_id,

                    "species":
                        p["species"],

                    "function":
                        p["function"],

                    "type":
                        "evening",

                    "start":
                        p["start"],

                    "end":
                        p["end"],

                    "min_days":
                        p["min_days"]
                        or 0,

                    "visit_number":
                        visit_number
                }
            )

            visit_number += 1

        # Morning visits

        for _ in range(
            p["morning"]
        ):

            requirements.append(
                {
                    "protocol_id":
                        protocol_id,

                    "species":
                        p["species"],

                    "function":
                        p["function"],

                    "type":
                        "morning",

                    "start":
                        p["start"],

                    "end":
                        p["end"],

                    "min_days":
                        p["min_days"]
                        or 0,

                    "visit_number":
                        visit_number
                }
            )

            visit_number += 1

        # Free visits

        for _ in range(
            p["free"]
        ):

            requirements.append(
                {
                    "protocol_id":
                        protocol_id,

                    "species":
                        p["species"],

                    "function":
                        p["function"],

                    "type":
                        "free",

                    "start":
                        p["start"],

                    "end":
                        p["end"],

                    "min_days":
                        p["min_days"]
                        or 0,

                    "visit_number":
                        visit_number
                }
            )

            visit_number += 1

    return requirements


def schedule_requirements(
    requirements
):

    survey_plan = []

    protocol_history = defaultdict(
        list
    )

    remaining = requirements.copy()

    while remaining:

        best_date = None

        best_type = None

        best_coverage = []

        candidate_dates = set()

        for req in remaining:

            candidate_dates.add(
                req["start"]
            )

            candidate_dates.add(
                req["end"]
            )

        for candidate_date in sorted(
            candidate_dates
        ):

            for survey_type in (
                "evening",
                "morning"
            ):

                covered = []

                for req in remaining:

                    if not (
                        req["start"]
                        <= candidate_date
                        <= req["end"]
                    ):
                        continue

                    req_type = req["type"]

                    if (
                        req_type ==
                        "evening"
                    ):
                        if (
                            survey_type
                            != "evening"
                        ):
                            continue

                    elif (
                        req_type ==
                        "morning"
                    ):
                        if (
                            survey_type
                            != "morning"
                        ):
                            continue

                    # free accepts
                    # evening or morning

                    history = (
                        protocol_history[
                            req[
                                "protocol_id"
                            ]
                        ]
                    )

                    if history:

                        last_visit = max(
                            history
                        )

                        minimum_gap = int(
                            req[
                                "min_days"
                            ]
                            or 0
                        )

                        if (
                            candidate_date
                            <=
                            last_visit
                            +
                            timedelta(
                                days=
                                minimum_gap
                            )
                        ):
                            continue

                    covered.append(
                        req
                    )

                if (
                    len(covered)
                    >
                    len(best_coverage)
                ):

                    best_date = (
                        candidate_date
                    )

                    best_type = (
                        survey_type
                    )

                    best_coverage = (
                        covered
                    )

        if not best_coverage:

            break

        survey_plan.append(
            {
                "date":
                    best_date,

                "type":
                    best_type,

                "protocols": [
                    (
                        f"{r['species']} "
                        f"| "
                        f"{r['function']}"
                    )
                    for r
                    in best_coverage
                ]
            }
        )

        for req in best_coverage:

            protocol_history[
                req["protocol_id"]
            ].append(
                best_date
            )

            remaining.remove(
                req
            )

    return sorted(
        survey_plan,
        key=lambda x: x["date"]
    )

def get_survey_demand(
    project,
    protocols
):

    protocols_data = []

    # --------------------------------------
    # LOAD PROTOCOLS
    # --------------------------------------

    for item in project["protocols"]:

        species = item["species"]
        function = item["function"]

        p = protocols[species][function]

        rounds = p["rounds"]

        protocols_data.append(
            {
                "species": species,
                "function": function,

                "start":
                    mmdd_to_date(
                        p["survey_period"]["start"]
                    ),

                "end":
                    mmdd_to_date(
                        p["survey_period"]["end"]
                    ),

                "evening":
                    rounds[
                        "mandatory_evening"
                    ],

                "morning":
                    rounds[
                        "mandatory_morning"
                    ],

                "free":
                    rounds[
                        "free_rounds"
                    ],

                "min_days":
                    p.get(
                        "min_days_between"
                    ),

                "timing":
                    p.get(
                        "timing",
                        {}
                    ),

                "weather":
                    p.get(
                        "weather",
                        {}
                    ),

                "special_requirements":
                    p.get(
                        "special_requirements",
                        {}
                    )
            }
        )

    # --------------------------------------
    # BUILD SURVEY PLAN
    # --------------------------------------
    # --------------------------------------
    # BUILD REQUIREMENTS
    # --------------------------------------
    
    requirements = build_requirements(
    protocols_data
    )
    
    # --------------------------------------
    # OPTIMIZE SURVEY COVERAGE
    # --------------------------------------

survey_plan = schedule_requirements(
    requirements
)


    evening_count = sum(
        1
        for v in survey_plan
        if v["type"] == "evening"
    )

    morning_count = sum(
        1
        for v in survey_plan
        if v["type"] == "morning"
    )

    free_count = 0

    # --------------------------------------
    # RETURN
    # --------------------------------------

    return {

        "minimum_visits":
            len(survey_plan),

        "evening_visits":
            evening_count,

        "morning_visits":
            morning_count,

        "free_visits":
            free_count,

        "survey_plan":
            survey_plan,

        "protocols":
            protocols_data
    }
