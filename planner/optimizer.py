from datetime import datetime


def parse_period(period):
    """
    Converts:
    {
        "start": "08-15",
        "end": "10-01"
    }

    into datetime objects.
    """

    start = datetime.strptime(
        period["start"],
        "%m-%d"
    )

    end = datetime.strptime(
        period["end"],
        "%m-%d"
    )

    return start, end


def periods_overlap(start1, end1, start2, end2):

    return (
        start1 <= end2
        and
        start2 <= end1
    )


def get_survey_demand(project, protocols):

    protocols_data = []

    # -----------------------------
    # LOAD PROTOCOLS
    # -----------------------------

    for item in project["protocols"]:

        species = item["species"]
        function = item["function"]

        protocol = protocols[species][function]

        start, end = parse_period(
            protocol["survey_period"]
        )

        rounds = protocol["rounds"]

        protocols_data.append(
            {
                "species": species,
                "function": function,
                "start": start,
                "end": end,
                "evening": rounds["mandatory_evening"],
                "morning": rounds["mandatory_morning"],
                "free": rounds["free_rounds"]
            }
        )

    # -----------------------------
    # FIND TRUE INTERSECTION
    # -----------------------------

    latest_start = max(
        p["start"]
        for p in protocols_data
    )

    earliest_end = min(
        p["end"]
        for p in protocols_data
    )

    overlap_exists = latest_start <= earliest_end

    # -----------------------------
    # NO OVERLAP
    # -----------------------------

    if not overlap_exists:

        return {
            "minimum_surveys": "No shared period",
            "clusters": [],
            "overlap": "None"
        }

    # -----------------------------
    # ROUND REQUIREMENTS
    # -----------------------------

    max_evening = max(
        p["evening"]
        for p in protocols_data
    )

    max_morning = max(
        p["morning"]
        for p in protocols_data
    )

    max_free = max(
        p["free"]
        for p in protocols_data
    )

    # ---------------------------------
    # FREE ROUNDS CAN BE EVENING OR MORNING
    # ---------------------------------

    capacity = (
        max_evening +
        max_morning
    )

    extra_free = max(
        0,
        max_free - capacity
    )

    minimum_visits = (
        max_evening +
        max_morning +
        extra_free
    )

    cluster = {
        "Overlap":
            f"{latest_start.strftime('%m-%d')} → "
            f"{earliest_end.strftime('%m-%d')}",

        "Evening":
            max_evening,

        "Morning":
            max_morning,

        "Free":
            max_free,

        "Minimum Visits":
            minimum_visits
    }

    return {
        "minimum_surveys": minimum_visits,
        "overlap":
            f"{latest_start.strftime('%m-%d')} → "
            f"{earliest_end.strftime('%m-%d')}",
        "clusters": [cluster]
    }
