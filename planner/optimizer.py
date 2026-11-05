from datetime import datetime


def period_to_day(mmdd):
    month, day = map(int, mmdd.split("-"))
    return (month * 100) + day


def get_survey_demand(project, protocols):

    rows = []

    for item in project["protocols"]:

        species = item["species"]
        function = item["function"]

        p = protocols[species][function]

        rounds = p["rounds"]

        rows.append(
            {
                "species": species,
                "function": function,
                "start": p["survey_period"]["start"],
                "end": p["survey_period"]["end"],
                "start_num": period_to_day(
                    p["survey_period"]["start"]
                ),
                "end_num": period_to_day(
                    p["survey_period"]["end"]
                ),
                "evening": rounds["mandatory_evening"],
                "morning": rounds["mandatory_morning"],
                "free": rounds["free_rounds"],
                "min_days": p["min_days_between"]
            }
        )

    # -------------------------
    # COMMON WINDOW
    # -------------------------

    common_start = max(
        r["start_num"]
        for r in rows
    )

    common_end = min(
        r["end_num"]
        for r in rows
    )

    overlap_exists = common_start <= common_end

    # -------------------------
    # VISITS REQUIRED
    # -------------------------

    evening_needed = max(
        r["evening"]
        for r in rows
    )

    morning_needed = max(
        r["morning"]
        for r in rows
    )

    free_needed = max(
        r["free"]
        for r in rows
    )

    covered_by_specific = (
        evening_needed +
        morning_needed
    )

    extra_free = max(
        0,
        free_needed - covered_by_specific
    )

    total_visits = (
        evening_needed +
        morning_needed +
        extra_free
    )

    # -------------------------
    # MIN DAYS CHECK
    # -------------------------

    max_min_days = max(
        r["min_days"]
        for r in rows
    )

    details = []

    for r in rows:

        details.append(
            {
                "Species": r["species"],
                "Function": r["function"],
                "Period":
                    f"{r['start']} → {r['end']}",
                "Evening": r["evening"],
                "Morning": r["morning"],
                "Free": r["free"],
                "Min Days":
                    r["min_days"]
            }
        )

    return {
        "overlap": overlap_exists,
        "common_period": (
            f"{common_start // 100:02d}-{common_start % 100:02d}"
            " → "
            f"{common_end // 100:02d}-{common_end % 100:02d}"
        ) if overlap_exists else "No shared period",

        "evening_visits":
            evening_needed,

        "morning_visits":
            morning_needed,

        "free_visits":
            extra_free,

        "minimum_visits":
            total_visits,

        "min_days_between":
            max_min_days,

        "details":
            details
    }
