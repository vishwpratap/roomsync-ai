
"""
RoomSync AI - Trait Computation Engine
"""

from backend.db import execute_insert, execute_query
from backend.scenarios import get_scenario_by_id

TRAIT_KEYS = [
    "cleanliness_tolerance",
    "noise_tolerance",
    "social_tolerance",
    "conflict_style",
    "flexibility",
]


def compute_traits(responses: list) -> dict:
    totals = {key: [] for key in TRAIT_KEYS}
    for response in responses:
        scenario = get_scenario_by_id(response["scenario_id"])
        if not scenario:
            continue
        option_idx = response["selected_option"]
        if option_idx < 0 or option_idx >= len(scenario["options"]):
            continue
        option = scenario["options"][option_idx]
        for trait_key, value in option.get("traits", {}).items():
            if trait_key in totals:
                totals[trait_key].append(value)

    traits = {}
    for key in TRAIT_KEYS:
        values = totals[key]
        traits[key] = max(1, min(5, round(sum(values) / len(values)))) if values else 3
    return traits


def derive_preferences(traits: dict) -> dict:
    cleanliness_tolerance = traits.get("cleanliness_tolerance", 3)
    noise_tolerance = traits.get("noise_tolerance", 3)
    social_tolerance = traits.get("social_tolerance", 3)
    flexibility = traits.get("flexibility", 3)

    cleanliness = max(1, min(5, 6 - cleanliness_tolerance))
    noise = max(1, min(5, noise_tolerance))
    social = max(1, min(5, social_tolerance))
    avg_routine = (6 - flexibility + noise_tolerance) / 2
    sleep = 0 if avg_routine <= 2 else (2 if avg_routine >= 4 else 1)
    guests = max(0, min(3, round((social_tolerance - 1) * 3 / 4)))

    return {
        "sleep": sleep,
        "cleanliness": cleanliness,
        "noise": noise,
        "smoking": 0,
        "guests": guests,
        "social": social,
        "cooking": 1,
    }


def derive_personality(traits: dict) -> dict:
    social_tolerance = traits.get("social_tolerance", 3)
    conflict_style = traits.get("conflict_style", 3)
    flexibility = traits.get("flexibility", 3)

    if conflict_style <= 2:
        conflict = 2
    elif conflict_style >= 4:
        conflict = 0
    else:
        conflict = 1

    return {
        "introvert_extrovert": max(1, min(5, social_tolerance)),
        "conflict_style": conflict,
        "routine_level": max(1, min(5, 6 - flexibility)),
        "sharing_level": max(1, min(5, round((social_tolerance + flexibility) / 2))),
    }


def save_traits(user_id: int, traits: dict):
    execute_insert(
        """
        INSERT INTO user_traits (user_id, cleanliness_tolerance, noise_tolerance, social_tolerance, conflict_style, flexibility)
        VALUES (%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            cleanliness_tolerance=VALUES(cleanliness_tolerance),
            noise_tolerance=VALUES(noise_tolerance),
            social_tolerance=VALUES(social_tolerance),
            conflict_style=VALUES(conflict_style),
            flexibility=VALUES(flexibility)
        """,
        (user_id, traits["cleanliness_tolerance"], traits["noise_tolerance"], traits["social_tolerance"], traits["conflict_style"], traits["flexibility"]),
    )


def save_scenario_responses(user_id: int, responses: list):
    for response in responses:
        scenario = get_scenario_by_id(response["scenario_id"])
        if not scenario:
            continue
        execute_insert(
            "INSERT INTO scenario_responses (user_id, scenario_id, selected_option) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE selected_option=VALUES(selected_option)",
            (user_id, scenario["scenario_id"], response["selected_option"]),
        )


def get_user_traits(user_id: int) -> dict:
    row = execute_query(
        "SELECT cleanliness_tolerance, noise_tolerance, social_tolerance, conflict_style, flexibility FROM user_traits WHERE user_id=%s",
        (user_id,),
        fetch_one=True,
    )
    return dict(row) if row else None
