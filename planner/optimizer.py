def get_survey_demand(project, protocols):

    evening = 0
    morning = 0
    free = 0

    details = []

    for item in project["protocols"]:

        species = item["species"]
        function = item["function"]

        protocol = protocols[species][function]

        rounds = protocol["rounds"]

        evening = max(
            evening,
            rounds["mandatory_evening"]
        )

        morning = max(
            morning,
            rounds["mandatory_morning"]
        )

        free = max(
            free,
            rounds["free_rounds"]
        )

        details.append(
            {
                "species": species,
                "function": function,
                "evening": rounds["mandatory_evening"],
                "morning": rounds["mandatory_morning"],
                "free": rounds["free_rounds"]
            }
        )

    minimum_surveys = max(
        evening,
        morning,
        free
    )

    return {
        "minimum_surveys": minimum_surveys,
        "evening_needed": evening,
        "morning_needed": morning,
        "free_needed": free,
        "details": details
    }
