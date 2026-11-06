from datetime import datetime


def mmdd_to_int(mmdd):
    month, day = map(int, mmdd.split("-"))
    return month * 100 + day


def overlap(a_start, a_end, b_start, b_end):
    return a_start <= b_end and b_start <= a_end


def get_survey_demand(project, protocols):

    protocols_data = []

    for item in project["protocols"]:

        species = item["species"]
        function = item["function"]

        p = protocols[species][function]

        rounds = p["rounds"]

        protocols_data.append(
            {
                "species": species,
                "function": function,

                "start": p["survey_period"]["start"],
                "end": p["survey_period"]["end"],

                "start_num": mmdd_to_int(
                    p["survey_period"]["start"]
                ),

                "end_num": mmdd_to_int(
                    p["survey_period"]["end"]
                ),

                "evening": rounds["mandatory_evening"],
                "morning": rounds["mandatory_morning"],
                "free": rounds["free_rounds"],

                "min_days": p.get(
                    "min_days_between"
                ),

                "timing": p.get(
                    "timing",
                    "Any"
                )
            }
        )

    # --------------------------------------------------
    # BUILD CLUSTERS
    # --------------------------------------------------

    clusters = []

    for protocol in protocols_data:

        matched = None

        for cluster in clusters:

            if not overlap(
                protocol["start_num"],
                protocol["end_num"],
                cluster["start_num"],
                cluster["end_num"]
            ):
                continue

            overlap_start = max(
                protocol["start_num"],
                cluster["start_num"]
            )

            overlap_end = min(
                protocol["end_num"],
                cluster["end_num"]
            )

            overlap_days = overlap_end - overlap_start

            # --------------------------------------------------
            # IMPORTANT
            # Keep Meervleermuis Satelliet separate when
            # overlap is too small.
            # --------------------------------------------------

            is_satellite = (
                protocol["species"].lower()
                == "meervleermuis"
                and
                protocol["function"].lower()
                == "satelliet"
            )

            if (
                is_satellite
                and overlap_days < 20
            ):
                continue

            matched = cluster
            break

        if matched:

            matched["protocols"].append(protocol)

            matched["start_num"] = min(
                matched["start_num"],
                protocol["start_num"]
            )

            matched["end_num"] = max(
                matched["end_num"],
                protocol["end_num"]
            )

        else:

            clusters.append(
                {
                    "start_num": protocol["start_num"],
                    "end_num": protocol["end_num"],
                    "protocols": [protocol]
                }
            )

    # --------------------------------------------------
    # OPTIMIZE CLUSTERS
    # --------------------------------------------------

    cluster_results = []

    total_evening = 0
    total_morning = 0
    total_visits = 0

    for cluster in clusters:

        protocols_in_cluster = cluster["protocols"]

        cluster_start = max(
            p["start_num"]
            for p in protocols_in_cluster
        )

        cluster_end = min(
            p["end_num"]
            for p in protocols_in_cluster
        )

        evening_required = max(
            p["evening"]
            for p in protocols_in_cluster
        )

        morning_required = max(
            p["morning"]
            for p in protocols_in_cluster
        )

        free_required = max(
            p["free"]
            for p in protocols_in_cluster
        )

        valid_min_days = [
            p["min_days"]
            for p in protocols_in_cluster
            if p["min_days"] is not None
        ]

        min_days_required = (
            max(valid_min_days)
            if valid_min_days
            else None
        )

        covered_free = (
            evening_required
            + morning_required
        )

        additional_free = max(
            0,
            free_required - covered_free
        )

        minimum_visits = (
            evening_required
            + morning_required
            + additional_free
        )

        total_evening += evening_required
        total_morning += morning_required
        total_visits += minimum_visits

        start_month = cluster_start // 100
        start_day = cluster_start % 100

        end_month = cluster_end // 100
        end_day = cluster_end % 100

        coverage_start = min(
            p["start_num"]
            for p in protocols_in_cluster
        )

        coverage_end = max(
            p["end_num"]
            for p in protocols_in_cluster
        )

        cluster_results.append(
            {
                "Period":
                    f"{start_month:02d}-{start_day:02d}"
                    " → "
                    f"{end_month:02d}-{end_day:02d}",

                "Protocol Details": [
                    {
                        "species": p["species"],
                        "function": p["function"],

                        "start": p["start"],
                        "end": p["end"],

                        "evening": p["evening"],
                        "morning": p["morning"],
                        "free": p["free"],

                        "min_days": p["min_days"],

                        "timing": p["timing"]
                    }
                    for p in protocols_in_cluster
                ],

                "Evening Visits":
                    evening_required,

                "Morning Visits":
                    morning_required,

                "Additional Free Visits":
                    additional_free,

                "Minimum Visits":
                    minimum_visits,

                "Min Days Between":
                    min_days_required,

                "Overlap Window":
                    f"{start_month:02d}-{start_day:02d}"
                    " → "
                    f"{end_month:02d}-{end_day:02d}",

                "Overlap Start":
                    cluster_start,

                "Overlap End":
                    cluster_end,

                "Protocols":
                    len(protocols_in_cluster),

                "Window Coverage":
                    f"{coverage_start//100:02d}-"
                    f"{coverage_start%100:02d}"
                    " → "
                    f"{coverage_end//100:02d}-"
                    f"{coverage_end%100:02d}",
            }
        )

    return {
        "minimum_visits": total_visits,
        "evening_visits": total_evening,
        "morning_visits": total_morning,
        "clusters": cluster_results
    }
