from datetime import datetime, timedelta

YEAR = 2025


def mmdd_to_date(mmdd):
    return datetime.strptime(
        f"{YEAR}-{mmdd}",
        "%Y-%m-%d"
    ).date()


def date_to_mmdd(date_obj):
    return date_obj.strftime("%m-%d")


def protocols_overlap(a, b):

    return (
        a["start"] <= b["end"]
        and
        b["start"] <= a["end"]
    )


def build_windows(protocols_data):

    windows = []

    for protocol in protocols_data:

        added = False

        for window in windows:

            overlap_start = max(
                window["start"],
                protocol["start"]
            )

            overlap_end = min(
                window["end"],
                protocol["end"]
            )

            if overlap_start <= overlap_end:

                window["protocols"].append(
                    protocol
                )

                window["start"] = overlap_start

                window["end"] = overlap_end

                added = True

                break

        if not added:

            windows.append(
                {
                    "start":
                        protocol["start"],

                    "end":
                        protocol["end"],

                    "protocols":
                        [protocol]
                }
            )

    return windows


import math


def safe_min_days(value):

    if value is None:
        return 0

    try:

        if math.isnan(value):
            return 0

    except:
        pass

    try:
        return int(value)

    except:
        return 0


def calculate_requirements(
    window_protocols
):

    evening = max(
        p["evening"]
        for p in window_protocols
    )

    morning = max(
        p["morning"]
        for p in window_protocols
    )

    free = max(
        p["free"]
        for p in window_protocols
    )

    covered_free = (
        evening
        + morning
    )

    additional_free = max(
        0,
        free - covered_free
    )

    valid_days = [
        safe_min_days(
            p["min_days"]
        )
        for p in window_protocols
    ]

    min_days = max(valid_days)

    return {

        "evening":
            evening,

        "morning":
            morning,

        "free":
            additional_free,

        "min_days":
            min_days
    }


def schedule_window(
    window,
    requirements
):

    visits = []

    interval = (
        requirements["min_days"]
        + 1
    )

    current = window["start"]

    # evening surveys

    for _ in range(
        requirements["evening"]
    ):

        visits.append(
            {
                "date": current,
                "type": "evening",
                "protocols": [
                    f"{p['species']} | {p['function']}"
                    for p in window[
                        "protocols"
                    ]
                ]
            }
        )

        current += timedelta(
            days=interval
        )

    # morning surveys

    for _ in range(
        requirements["morning"]
    ):

        visits.append(
            {
                "date": current,
                "type": "morning",
                "protocols": [
                    f"{p['species']} | {p['function']}"
                    for p in window[
                        "protocols"
                    ]
                ]
            }
        )

        current += timedelta(
            days=interval
        )

    # additional free

    for _ in range(
        requirements["free"]
    ):

        visits.append(
            {
                "date": current,
                "type": "free",
                "protocols": [
                    f"{p['species']} | {p['function']}"
                    for p in window[
                        "protocols"
                    ]
                ]
            }
        )

        current += timedelta(
            days=interval
        )

    return visits


def get_survey_demand(
    project,
    protocols
):

    protocols_data = []

    for item in project["protocols"]:

        species = item["species"]

        function = item["function"]

        p = protocols[
            species
        ][
            function
        ]

        rounds = p["rounds"]

        protocols_data.append(
            {
                "species":
                    species,

                "function":
                    function,

                "start":
                    mmdd_to_date(
                        p[
                            "survey_period"
                        ][
                            "start"
                        ]
                    ),

                "end":
                    mmdd_to_date(
                        p[
                            "survey_period"
                        ][
                            "end"
                        ]
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

    windows = build_windows(
        protocols_data
    )

    survey_plan = []

    for window in windows:

        requirements = (
            calculate_requirements(
                window[
                    "protocols"
                ]
            )
        )

        survey_plan.extend(
            schedule_window(
                window,
                requirements
            )
        )

    survey_plan.sort(
        key=lambda x: x["date"]
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

    free_count = sum(
        1
        for v in survey_plan
        if v["type"] == "free"
    )

    return {
        "minimum_visits":
            len(
                survey_plan
            ),

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
