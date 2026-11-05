import pandas as pd

overview = []

for item in project["protocols"]:

    species = item["species"]
    function = item["function"]

    protocol = PROTOCOLS[species][function]

    rounds = protocol["rounds"]

    overview.append(
        {
            "Species": species,
            "Function": function,
            "Start": protocol["survey_period"]["start"],
            "End": protocol["survey_period"]["end"],
            "Evening": rounds["mandatory_evening"],
            "Morning": rounds["mandatory_morning"],
            "Free": rounds["free_rounds"],
            "Min Days": protocol["min_days_between"]
        }
    )

df = pd.DataFrame(overview)

st.dataframe(
    df,
    use_container_width=True
)
