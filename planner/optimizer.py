from datetime import datetime


def periods_overlap(start1, end1, start2, end2):
    return start1 <= end2 and start2 <= end1


def parse_period(period, year=2027):

    start = datetime.strptime(
        f"{year}-{period['start']}",
        "%Y-%m-%d"
    )

    end = datetime.strptime(
        f"{year}-{period['end']}",
        "%Y-%m-%d"
    )

    return start, end


def get_survey_demand(project, protocols):

    protocols_data = []

    # ------------------------------------
    # LOAD PROTOCOLS
    # ------------------------------------

    for item in project["protocols"]:

        species = item["species"]
        function = item["function"]

        p = protocols[species][function]

        start, end = parse_period(
            p["survey_period"]
        )

        rounds = p["rounds"]

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

    # ------------------------------------
    # CREATE PERIOD CLUSTERS
    # ------------------------------------

    clusters = []

    for protocol in protocols_data:

        added = False

        for cluster in clusters:

            if periods_overlap(
                protocol["start"],
                protocol["end"],
                cluster["start"],
                cluster["end"]
            ):

                cluster["protocols"].append(protocol)

                cluster["start"] = max(
                    cluster["start"],
                    protocol["start"]
                )

                cluster["end"] = min(
                    cluster["end"],
                    protocol["end"]
                )

                added = True
                break

        if not added:

            clusters.append(
                {
                    "start": protocol["start"],
                    "end": protocol["end"],
                    "protocols": [protocol]
                }
            )

    # ------------------------------------
    # OPTIMIZE EACH CLUSTER
    # ------------------------------------

    total_surveys = 0
    cluster_results = []

    for cluster in clusters:

        evening = max(
            p["evening"]
            for p in cluster["protocols"]
        )

        morning = max(
            p["morning"]
            for p in cluster["protocols"]
        )

        free = max(
            p["free"]
            for p in cluster["protocols"]
        )

        #
        # logic:
        #
        # evening covers free
        # morning covers free
        #
        # so free only adds visits
        # if evening+morning aren't enough
        #

        used_free_capacity = evening + morning

        extra_free_needed = max(
            0,
            free - used_free_capacity
        )

        minimum_visits = (
            evening
            + morning
            + extra_free_needed
        )

        total_surveys += minimum_visits

        cluster_results.append(
            {
                "period":
                    f"{cluster['start'].strftime('%d-%m')} → "
                    f"{cluster['end'].strftime('%d-%m')}",
                "evening": evening,
                "morning": morning,
                "free": free,
                "minimum_visits": minimum_visits
            }
        )

    return {
        "minimum_surveys": total_surveys,
        "clusters": cluster_results
    }
