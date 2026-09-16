import json
import os

# Path to the chemicals folder
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHEMICALS_DIR = os.path.join(BASE_DIR, "data", "chemicals")


def load_all_chemicals():
    """
    Load all chemical JSON files and return a single list.
    """

    chemicals = []

    files = [
        "acids.json",
        "bases.json",
        "salts.json",
        "solvents.json",
        "indicators.json",
        "gases.json",
        "oxidizers.json",
        "reducing_agents.json",
    ]

    for file in files:
        path = os.path.join(CHEMICALS_DIR, file)

        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)

                    if isinstance(data, list):
                        chemicals.extend(data)

                except json.JSONDecodeError:
                    print(f"Error reading {file}")

    return chemicals


def search_chemical(name):
    """
    Search by chemical name.
    """

    chemicals = load_all_chemicals()

    for chemical in chemicals:
        if chemical["name"].lower() == name.lower():
            return chemical

    return None


def search_formula(formula):
    """
    Search by chemical formula.
    """

    chemicals = load_all_chemicals()

    for chemical in chemicals:
        if chemical["formula"].lower() == formula.lower():
            return chemical

    return None


def search_category(category):
    """
    Return all chemicals in a category.
    """

    chemicals = load_all_chemicals()

    return [
        chemical
        for chemical in chemicals
        if chemical["category"].lower() == category.lower()
    ]
