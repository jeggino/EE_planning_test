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
                "min_days": p["min_days_between"]
            }
        )

    # ------------------------
    # BUILD CLUSTERS
    # ------------------------

    clusters = []

    for protocol in protocols_data:

        matched = None

        for cluster in clusters:

            if overlap(
                protocol["start_num"],
                protocol["end_num"],
                cluster["start_num"],
                cluster["end_num"]
            ):
                matched = cluster
                break

        if matched:

            matched["protocols"].append(protocol)


        else:

            clusters.append(
                {
                    "start_num": protocol["start_num"],
                    "end_num": protocol["end_num"],
                    "protocols": [protocol]
                }
            )

    # ------------------------
    # OPTIMIZE EACH CLUSTER
    # ------------------------

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

        min_days_required = max(
            p["min_days"]
            for p in protocols_in_cluster
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

        cluster_results.append(
            {
                "Period":
                    f"{start_month:02d}-{start_day:02d}"
                    " → "
                    f"{end_month:02d}-{end_day:02d}",
        
                "Protocols":
                    len(protocols_in_cluster),
        
                "Protocol Details":
                    [
                        f"{p['species']} | "
                        f"{p['start']} -> {p['end']}"
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
                    min_days_required

                "Overlap Window":
                    f"{start_month:02d}-{start_day:02d}"
                    " → "
                    f"{end_month:02d}-{end_day:02d}",
                
                "Protocols":
                    len(protocols_in_cluster),
                
                "Window Coverage":
                    f"{min(p['start_num'] for p in protocols_in_cluster)//100:02d}-"
                    f"{min(p['start_num'] for p in protocols_in_cluster)%100:02d}"
                    " → "
                    f"{max(p['end_num'] for p in protocols_in_cluster)//100:02d}-"
                    f"{max(p['end_num'] for p in protocols_in_cluster)%100:02d}",
            }
        )

    return {
        "minimum_visits": total_visits,
        "evening_visits": total_evening,
        "morning_visits": total_morning,
        "clusters": cluster_results
    }
