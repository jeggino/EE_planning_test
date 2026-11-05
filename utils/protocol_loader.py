import json


def load_protocols():

    with open(
        "data/protocols.json",
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)
