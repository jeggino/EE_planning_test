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
    remaining = []

    # ----------------------------------
    # Separate satellite surveys
    # ----------------------------------

    for p in protocols_data:

        if (
            p["species"] == "meervleermuis"
            and
            p["function"] == "satelliet"
        ):
            special.append(p)

        else:
            remaining.append(p)

    selected_periods = []

    period_number = 1

    while remaining:

        best_period = None

        # ----------------------------------
        # Generate all candidate overlaps
        # ----------------------------------

        for protocol in remaining:

            overlap_start = protocol["start"]
            overlap_end = protocol["end"]

            covered = [
                protocol
            ]

            for other in remaining:

                if other is protocol:
                    continue

                start = max(
                    overlap_start,
                    other["start"]
                )

                end = min(
                    overlap_end,
                    other["end"]
                )

                duration = (
                    end - start
                ).days + 1

                if duration >= min_duration:

                    overlap_start = start
                    overlap_end = end

                    covered.append(
                        other
                    )

            duration = (
                overlap_end
                - overlap_start
            ).days + 1

            if duration < min_duration:
                continue

            protocol_names = sorted(
                [
                    f"{p['species']} | {p['function']}"
                    for p in covered
                ]
            )

            candidate = {
                "Period":
                    f"Period {period_number}",

                "Start":
                    overlap_start,

                "End":
                    overlap_end,

                "Days":
                    duration,

                "Protocols":
                    protocol_names,

                "ProtocolCount":
                    len(protocol_names)
            }

            # ----------------------------------
            # Select best:
            # 1. Most protocols
            # 2. Then longest period
            # ----------------------------------

            if best_period is None:

                best_period = candidate

            elif (
                candidate["ProtocolCount"]
                >
                best_period["ProtocolCount"]
            ):

                best_period = candidate

            elif (
                candidate["ProtocolCount"]
                ==
                best_period["ProtocolCount"]
                and
                candidate["Days"]
                >
                best_period["Days"]
            ):

                best_period = candidate

        if best_period is None:
            break

        selected_periods.append(
            best_period
        )

        covered_set = set(
            best_period["Protocols"]
        )

        remaining = [
            p
            for p in remaining
            if (
                f"{p['species']} | "
                f"{p['function']}"
            )
            not in covered_set
        ]

        period_number += 1

    return (
        selected_periods,
        special
    )
    
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



