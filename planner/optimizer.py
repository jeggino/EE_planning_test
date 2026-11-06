# from datetime import datetime

# YEAR = 2025


# def mmdd_to_date(mmdd):
#     return datetime.strptime(
#         f"{YEAR}-{mmdd}",
#         "%Y-%m-%d"
#     ).date()


# def date_to_mmdd(date_obj):
#     return date_obj.strftime("%m-%d")


# def has_satellite(protocols):

#     return any(
#         p["species"].lower() == "meervleermuis"
#         and p["function"].lower() == "satelliet"
#         for p in protocols
#     )


# def get_survey_demand(
#     project,
#     protocols
# ):

#     protocols_data = []

#     # --------------------------------------
#     # LOAD PROTOCOLS
#     # --------------------------------------

#     for item in project["protocols"]:

#         species = item["species"]
#         function = item["function"]

#         p = protocols[species][function]

#         rounds = p["rounds"]

#         start_date = mmdd_to_date(
#             p["survey_period"]["start"]
#         )

#         end_date = mmdd_to_date(
#             p["survey_period"]["end"]
#         )

#         protocols_data.append(
#             {
#                 "species": species,
#                 "function": function,
        
#                 "start": start_date,
#                 "end": end_date,
        
#                 "evening":
#                     rounds["mandatory_evening"],
        
#                 "morning":
#                     rounds["mandatory_morning"],
        
#                 "free":
#                     rounds["free_rounds"],
        
#                 "min_days":
#                     p.get(
#                         "min_days_between"
#                     ),
        
#                 "timing":
#                     p.get(
#                         "timing",
#                         {}
#                     ),
        
#                 "weather":
#                     p.get(
#                         "weather",
#                         {}
#                     ),
        
#                 "special_requirements":
#                     p.get(
#                         "special_requirements",
#                         {}
#                     )
#             }
#         )
#     # Sort by start date

#     protocols_data.sort(
#         key=lambda x: x["start"]
#     )

#     # --------------------------------------
#     # BUILD CLUSTERS
#     # --------------------------------------

#     clusters = []

#     for protocol in protocols_data:

#         merged = False

#         for cluster in clusters:

#             proposed_overlap_start = max(
#                 cluster["overlap_start"],
#                 protocol["start"]
#             )

#             proposed_overlap_end = min(
#                 cluster["overlap_end"],
#                 protocol["end"]
#             )

#             # No true overlap

#             if (
#                 proposed_overlap_end
#                 < proposed_overlap_start
#             ):
#                 continue

#             overlap_days = (
#                 proposed_overlap_end
#                 - proposed_overlap_start
#             ).days

#             candidate_protocols = (
#                 cluster["protocols"]
#                 + [protocol]
#             )
            
#             cluster_has_satellite = (
#                 has_satellite(
#                     candidate_protocols
#                 )
#             )
            
#             # ------------------------------------------------
#             # SATELLIET RULE
#             # ------------------------------------------------
            
#             if (
#                 cluster_has_satellite
#                 and overlap_days < 20
#             ):
#                 continue
            
#             # ------------------------------------------------
#             # MIN DAYS FEASIBILITY RULE
#             # ------------------------------------------------
            
#             required_span = 0
            
#             for p in candidate_protocols:
            
#                 min_days = p.get("min_days")
            
#                 if min_days in [None, ""]:
#                     continue
            
#                 visits = (
#                     p["evening"]
#                     + p["morning"]
#                     + p["free"]
#                 )
            
#                 protocol_span = (
#                     max(0, visits - 1)
#                     * min_days
#                 )
            
#                 required_span = max(
#                     required_span,
#                     protocol_span
#                 )
            
#             # If there is not enough overlap to
#             # schedule the protocol correctly,
#             # don't merge it into this window.
            
#             if overlap_days < required_span:
#                 continue

#             cluster["protocols"].append(
#                 protocol
#             )

#             cluster["coverage_start"] = min(
#                 cluster["coverage_start"],
#                 protocol["start"]
#             )

#             cluster["coverage_end"] = max(
#                 cluster["coverage_end"],
#                 protocol["end"]
#             )

#             cluster["overlap_start"] = (
#                 proposed_overlap_start
#             )

#             cluster["overlap_end"] = (
#                 proposed_overlap_end
#             )

#             merged = True

#             break

#         if not merged:

#             clusters.append(
#                 {
#                     "protocols": [protocol],

#                     "coverage_start":
#                         protocol["start"],

#                     "coverage_end":
#                         protocol["end"],

#                     "overlap_start":
#                         protocol["start"],

#                     "overlap_end":
#                         protocol["end"]
#                 }
#             )

#     # --------------------------------------
#     # CALCULATE DEMAND
#     # --------------------------------------

#     cluster_results = []

#     total_evening = 0
#     total_morning = 0
#     total_free = 0
#     total_visits = 0

#     for cluster in clusters:

#         protocols_in_cluster = (
#             cluster["protocols"]
#         )

#         evening_required = max(
#             p["evening"]
#             for p in protocols_in_cluster
#         )

#         morning_required = max(
#             p["morning"]
#             for p in protocols_in_cluster
#         )

#         free_required = max(
#             p["free"]
#             for p in protocols_in_cluster
#         )

#         valid_min_days = [
#             p["min_days"]
#             for p in protocols_in_cluster
#             if p["min_days"] is not None
#         ]

#         min_days_required = (
#             max(valid_min_days)
#             if valid_min_days
#             else None
#         )

#         covered_free = (
#             evening_required
#             + morning_required
#         )

#         additional_free = max(
#             0,
#             free_required - covered_free
#         )

#         minimum_visits = (
#             evening_required
#             + morning_required
#             + additional_free
#         )

#         total_evening += evening_required
#         total_morning += morning_required
#         total_visits += minimum_visits
#         total_free += additional_free


#         cluster_results.append(
#             {
#                 "Protocols":
#                     len(
#                         protocols_in_cluster
#                     ),

#                 "Minimum Visits":
#                     minimum_visits,

#                 "Evening Visits":
#                     evening_required,

#                 "Morning Visits":
#                     morning_required,

#                 "Additional Free Visits":
#                     additional_free,

#                 "Min Days Between":
#                     min_days_required,

#                 "Window Coverage":
#                     date_to_mmdd(
#                         cluster[
#                             "coverage_start"
#                         ]
#                     )
#                     + " → " +
#                     date_to_mmdd(
#                         cluster[
#                             "coverage_end"
#                         ]
#                     ),

#                 "Overlap Window":
#                     date_to_mmdd(
#                         cluster[
#                             "overlap_start"
#                         ]
#                     )
#                     + " → " +
#                     date_to_mmdd(
#                         cluster[
#                             "overlap_end"
#                         ]
#                     ),

#                 "Overlap Days":
#                     (
#                         cluster["overlap_end"]
#                         -
#                         cluster["overlap_start"]
#                     ).days,

#                 "Overlap Start":
#                     cluster[
#                         "overlap_start"
#                     ],

#                 "Overlap End":
#                     cluster[
#                         "overlap_end"
#                     ],

#                 "Protocol Details": [
#                     {
#                         "species":
#                             p["species"],

#                         "function":
#                             p["function"],

#                         "start":
#                             date_to_mmdd(
#                                 p["start"]
#                             ),

#                         "end":
#                             date_to_mmdd(
#                                 p["end"]
#                             ),

#                         "timing":
#                             p["timing"],
                        
#                         "weather":
#                             p["weather"],
                        
#                         "special_requirements":
#                             p["special_requirements"],
                        
#                         "evening":
#                             p["evening"],

#                         "morning":
#                             p["morning"],

#                         "free":
#                             p["free"],

#                         "min_days": (
#                             p["min_days"]
#                             if p["min_days"] not in [None, ""]
#                             else None
#                         ),
#                     }
#                     for p in protocols_in_cluster
#                 ]
#             }
#         )

#     return {
#         "minimum_visits":
#             total_visits,
    
#         "evening_visits":
#             total_evening,
    
#         "morning_visits":
#             total_morning,
    
#         "free_visits":
#             total_free,
    
#         "clusters":
#             cluster_results
#     }


from datetime import datetime

YEAR = 2025


def mmdd_to_date(mmdd):
    return datetime.strptime(
        f"{YEAR}-{mmdd}",
        "%Y-%m-%d"
    ).date()


def date_to_mmdd(date_obj):
    return date_obj.strftime("%m-%d")


def has_satellite(protocols):

    return any(
        p["species"].lower() == "meervleermuis"
        and p["function"].lower() == "satelliet"
        for p in protocols
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

        start_date = mmdd_to_date(
            p["survey_period"]["start"]
        )

        end_date = mmdd_to_date(
            p["survey_period"]["end"]
        )

        protocols_data.append(
            {
                "species": species,
                "function": function,

                "start": start_date,
                "end": end_date,

                "evening":
                    rounds["mandatory_evening"],

                "morning":
                    rounds["mandatory_morning"],

                "free":
                    rounds["free_rounds"],

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

    protocols_data.sort(
        key=lambda x: x["start"]
    )

    # --------------------------------------
    # BUILD CLUSTERS
    # --------------------------------------

    clusters = []

    for protocol in protocols_data:

        merged = False

        for cluster in clusters:

            proposed_overlap_start = max(
                cluster["overlap_start"],
                protocol["start"]
            )

            proposed_overlap_end = min(
                cluster["overlap_end"],
                protocol["end"]
            )

            if (
                proposed_overlap_end
                < proposed_overlap_start
            ):
                continue

            overlap_days = (
                proposed_overlap_end
                - proposed_overlap_start
            ).days

            candidate_protocols = (
                cluster["protocols"]
                + [protocol]
            )

            cluster_has_satellite = (
                has_satellite(
                    candidate_protocols
                )
            )

            if (
                cluster_has_satellite
                and overlap_days < 20
            ):
                continue

            required_span = 0

            for p in candidate_protocols:

                min_days = p.get(
                    "min_days"
                )

                if min_days in [None, ""]:
                    continue

                visits = (
                    p["evening"]
                    + p["morning"]
                    + p["free"]
                )

                protocol_span = (
                    max(0, visits - 1)
                    * min_days
                )

                required_span = max(
                    required_span,
                    protocol_span
                )

            if overlap_days < required_span:
                continue

            cluster["protocols"].append(
                protocol
            )

            cluster["coverage_start"] = min(
                cluster["coverage_start"],
                protocol["start"]
            )

            cluster["coverage_end"] = max(
                cluster["coverage_end"],
                protocol["end"]
            )

            cluster["overlap_start"] = (
                proposed_overlap_start
            )

            cluster["overlap_end"] = (
                proposed_overlap_end
            )

            merged = True
            break

        if not merged:

            clusters.append(
                {
                    "protocols": [protocol],

                    "coverage_start":
                        protocol["start"],

                    "coverage_end":
                        protocol["end"],

                    "overlap_start":
                        protocol["start"],

                    "overlap_end":
                        protocol["end"]
                }
            )

    # --------------------------------------
    # CALCULATE DEMAND
    # --------------------------------------

    cluster_results = []

    total_evening = 0
    total_morning = 0
    total_free = 0
    total_visits = 0

    for cluster in clusters:

        protocols_in_cluster = (
            cluster["protocols"]
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
        total_free += additional_free
        total_visits += minimum_visits

        cluster_results.append(
            {
                "Protocols":
                    len(protocols_in_cluster),

                "Minimum Visits":
                    minimum_visits,

                "Evening Visits":
                    evening_required,

                "Morning Visits":
                    morning_required,

                "Additional Free Visits":
                    additional_free,

                "Min Days Between":
                    min_days_required,

                "Window Coverage":
                    date_to_mmdd(
                        cluster["coverage_start"]
                    )
                    + " → " +
                    date_to_mmdd(
                        cluster["coverage_end"]
                    ),

                "Overlap Window":
                    date_to_mmdd(
                        cluster["overlap_start"]
                    )
                    + " → " +
                    date_to_mmdd(
                        cluster["overlap_end"]
                    ),

                "Overlap Days":
                    (
                        cluster["overlap_end"]
                        -
                        cluster["overlap_start"]
                    ).days,

                "Overlap Start":
                    cluster["overlap_start"],

                "Overlap End":
                    cluster["overlap_end"],

                "Protocol Details": [
                    {
                        "species": p["species"],
                        "function": p["function"],
                        "start": date_to_mmdd(
                            p["start"]
                        ),
                        "end": date_to_mmdd(
                            p["end"]
                        ),
                        "timing": p["timing"],
                        "weather": p["weather"],
                        "special_requirements":
                            p["special_requirements"],
                        "evening": p["evening"],
                        "morning": p["morning"],
                        "free": p["free"],
                        "min_days": p["min_days"]
                    }
                    for p in protocols_in_cluster
                ]
            }
        )

    return {
        "minimum_visits":
            total_visits,
        "evening_visits":
            total_evening,
        "morning_visits":
            total_morning,
        "free_visits":
            total_free,
        "clusters":
            cluster_results
    }
