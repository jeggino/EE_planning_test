from datetime import datetime


def parse_period(period):

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

    # ------------------------------------
    # LOAD PROTOCOLS
    # ------------------------------------

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

    # ------------------------------------
    # PERIOD CLUSTERS
    # ------------------------------------

    clusters = []

    for protocol in protocols_data:

        matched_cluster = None

        for cluster in clusters:

            if periods_overlap(
                protocol["start"],
                protocol["end"],
                cluster["start"],
                cluster["end"]
            ):

                matched_cluster = cluster
                break

        if matched_cluster:

            matched_cluster["protocols"].append(
                protocol
            )

            matched_cluster["start"] = max(
                matched_cluster["start"],
                protocol["start"]
            )

            matched_cluster["end"] = min(
                matched_cluster["end"],
                protocol["end"]
            )

        else:

            clusters.append(
                {
                    "start": protocol["start"],
                    "end": protocol["end"],
                    "protocols": [protocol]
                }
            )

    # ------------------------------------
    # OPTIMIZATION
    # ------------------------------------

    cluster_results = []
    total_visits = 0

    for cluster in clusters:

        max_evening = max(
            p["evening"]
            for p in cluster["protocols"]
        )

        max_morning = max(
            p["morning"]
            for p in cluster["protocols"]
        )

        max_free = max(
            p["free"]
            for p in cluster["protocols"]
        )

        # free rounds can be covered
        # by evening or morning rounds

        covered_free = (
            max_evening
            + max_morning
        )

        remaining_free = max(
            0,
            max_free - covered_free
        )

        minimum_visits = (
            max_evening
            + max_morning
            + remaining_free
        )

        total_visits += minimum_visits

        cluster_results.append(
            {
                "Period":
                    f"{cluster['start'].strftime('%m-%d')} → "
                    f"{cluster['end'].strftime('%m-%d')}",

                "Evening":
                    max_evening,

                "Morning":
                    max_morning,

                "Free":
                    max_free,

                "Minimum Visits":
                    minimum_visits,

                "Protocols":
                    len(cluster["protocols"])
            }
        )

    return {
        "minimum_surveys": total_visits,
        "clusters": cluster_results
    }
