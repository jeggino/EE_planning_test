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

from datetime import timedelta


def build_optimized_periods(
    protocols_data,
    min_duration=30
):

    special = []
    normal = []

    # ----------------------------------
    # Separate meervleermuis satelliet
    # ----------------------------------

    for p in protocols_data:

        if (
            p["species"] == "meervleermuis"
            and
            p["function"] == "satelliet"
        ):
            special.append(p)

        else:
            normal.append(p)

    # ----------------------------------
    # Build boundaries
    # ----------------------------------

    boundaries = set()

    for p in normal:

        boundaries.add(
            p["start"]
        )

        boundaries.add(
            p["end"]
            + timedelta(days=1)
        )

    boundaries = sorted(boundaries)

    # ----------------------------------
    # Create atomic periods
    # ----------------------------------

    atomic_periods = []

    for i in range(
        len(boundaries) - 1
    ):

        start = boundaries[i]

        end = (
            boundaries[i + 1]
            - timedelta(days=1)
        )

        active = []

        for p in normal:

            if (
                p["start"] <= start
                and
                p["end"] >= end
            ):

                active.append(
                    f"{p['species']} | {p['function']}"
                )

        if active:

            atomic_periods.append(
                {
                    "start": start,
                    "end": end,
                    "protocols": set(active)
                }
            )

    # ----------------------------------
    # Create candidate merged periods
    # ----------------------------------

    candidates = []

    for i in range(
        len(atomic_periods)
    ):

        protocols = set()

        start = atomic_periods[i]["start"]

        end = atomic_periods[i]["end"]

        protocols.update(
            atomic_periods[i]["protocols"]
        )

        for j in range(
            i,
            len(atomic_periods)
        ):

            end = atomic_periods[j]["end"]

            protocols.update(
                atomic_periods[j]["protocols"]
            )

            duration = (
                end - start
            ).days + 1

            if duration >= min_duration:

        
    
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

    optimized_periods, special_protocols = (
        build_optimized_periods(
            protocols_data
        )
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
            protocols_data,

        "optimized_periods":
            optimized_periods,
    
        "special_protocols":
            special_protocols
    }


from datetime import timedelta



