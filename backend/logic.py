
"""
RoomSync AI - Compatibility Scoring Engine
"""

from backend.db import DEFAULT_WEIGHT_VALUES, execute_query

LIFESTYLE_WEIGHTS = {
    "cleanliness": {"weight": 20, "max_range": 4},
    "smoking": {"weight": 20, "max_range": 2},
    "sleep": {"weight": 15, "max_range": 2},
    "noise": {"weight": 15, "max_range": 4},
    "social": {"weight": 10, "max_range": 4},
    "guests": {"weight": 5, "max_range": 3},
    "cooking": {"weight": 5, "max_range": 3},
}

PERSONALITY_WEIGHTS = {
    "introvert_extrovert": {"weight": 3.0, "max_range": 4},
    "conflict_style": {"weight": 2.5, "max_range": 2},
    "routine_level": {"weight": 2.5, "max_range": 4},
    "sharing_level": {"weight": 2.0, "max_range": 4},
}

TRAIT_WEIGHTS = {
    "cleanliness_tolerance": {"weight": 7.0, "max_range": 4},
    "noise_tolerance": {"weight": 6.0, "max_range": 4},
    "social_tolerance": {"weight": 5.0, "max_range": 4},
    "conflict_style": {"weight": 6.0, "max_range": 4},
    "flexibility": {"weight": 6.0, "max_range": 4},
}

CLUSTER_BONUS = 5.0
BASE_CATEGORY_FACTORS = {
    "lifestyle": 0.40,
    "personality": 0.25,
    "trait": 0.30,
    "cluster": 0.05,
}


def get_runtime_weight_config():
    rows = execute_query("SELECT feature, value FROM weights", fetch_all=True) or []
    config = dict(DEFAULT_WEIGHT_VALUES)
    for row in rows:
        try:
            config[row["feature"]] = float(row["value"])
        except (TypeError, ValueError):
            config[row["feature"]] = DEFAULT_WEIGHT_VALUES.get(row["feature"], 1.0)
    return config


def similarity(a: float, b: float, max_range: float) -> float:
    if max_range == 0:
        return 1.0
    return max(0.0, 1.0 - (abs(a - b) / max_range))


def calculate_lifestyle_score(pref_a: dict, pref_b: dict, weight_config: dict) -> tuple:
    score = 0.0
    max_score = 0.0
    highlights = []
    warnings = []

    for field, config in LIFESTYLE_WEIGHTS.items():
        multiplier = weight_config.get(field, 1.0) if field in ("cleanliness", "sleep") else 1.0
        field_weight = config["weight"] * multiplier
        max_score += field_weight

        value_a = pref_a.get(field, 0)
        value_b = pref_b.get(field, 0)
        sim = similarity(value_a, value_b, config["max_range"])
        score += sim * field_weight

        diff = abs(value_a - value_b)
        if field == "cleanliness":
            if diff == 0:
                highlights.append("Identical cleanliness standards")
            elif diff <= 1:
                highlights.append("Similar cleanliness expectations")
            elif diff >= 3:
                warnings.append(f"Large cleanliness gap ({value_a} vs {value_b})")
        elif field == "sleep":
            if diff == 0:
                highlights.append("Aligned sleep rhythm")
            elif diff == 2:
                warnings.append("Opposite sleep schedules may create friction")
        elif field == "smoking":
            if value_a == value_b:
                highlights.append("Matching smoking preference")
            else:
                warnings.append("Smoking preference mismatch")
        elif field == "noise" and diff <= 1:
            highlights.append("Compatible noise tolerance")
        elif field == "noise" and diff >= 3:
            warnings.append("Major noise expectation gap")
        elif field == "social" and diff <= 1:
            highlights.append("Similar social energy")
        elif field == "social" and diff >= 3:
            warnings.append("Different social energy levels")

    return score, max_score, highlights, warnings


def calculate_personality_score(profile_a: dict, profile_b: dict) -> tuple:
    score = 0.0
    max_score = 0.0
    for field, config in PERSONALITY_WEIGHTS.items():
        max_score += config["weight"]
        score += similarity(profile_a.get(field, 0), profile_b.get(field, 0), config["max_range"]) * config["weight"]
    return score, max_score


def calculate_trait_score(traits_a: dict, traits_b: dict) -> tuple:
    max_score = sum(item["weight"] for item in TRAIT_WEIGHTS.values())
    if not traits_a or not traits_b:
        return 0.0, max_score, [], []

    score = 0.0
    highlights = []
    warnings = []
    for field, config in TRAIT_WEIGHTS.items():
        value_a = traits_a.get(field, 3)
        value_b = traits_b.get(field, 3)
        diff = abs(value_a - value_b)
        score += similarity(value_a, value_b, config["max_range"]) * config["weight"]
        label = field.replace("_", " ")
        if diff == 0:
            highlights.append(f"Aligned {label}")
        elif diff >= 3:
            warnings.append(f"Strong mismatch in {label}")

    return score, max_score, highlights, warnings


def calculate_penalties(pref_a: dict, pref_b: dict) -> float:
    penalties = 0.0
    smoke_diff = abs(pref_a.get("smoking", 0) - pref_b.get("smoking", 0))
    if smoke_diff == 2:
        penalties -= 10.0
    elif smoke_diff == 1:
        penalties -= 4.0

    clean_diff = abs(pref_a.get("cleanliness", 1) - pref_b.get("cleanliness", 1))
    if clean_diff >= 4:
        penalties -= 8.0
    elif clean_diff >= 3:
        penalties -= 5.0

    sleep_diff = abs(pref_a.get("sleep", 0) - pref_b.get("sleep", 0))
    if sleep_diff == 2:
        penalties -= 5.0

    return penalties


def generate_recommendation(total_score: float, risk_level: str) -> str:
    if total_score >= 80 and risk_level != "HIGH":
        return "Highly Recommended"
    if total_score >= 65 and risk_level != "HIGH":
        return "Recommended"
    if total_score >= 45:
        return "Proceed with Caution"
    return "Not Recommended"


def build_room_requirement_profile(lifestyle_preference: dict, personality_preference: dict | None = None) -> tuple:
    lifestyle = dict(lifestyle_preference or {})
    personality = dict(personality_preference or {})

    room_prefs = {
        "sleep": lifestyle.get("sleep", 1),
        "cleanliness": lifestyle.get("cleanliness", 3),
        "noise": lifestyle.get("noise", 3),
        "smoking": lifestyle.get("smoking", 0),
        "guests": lifestyle.get("guests", 1),
        "social": lifestyle.get("social", 3),
        "cooking": lifestyle.get("cooking", 1),
    }
    room_personality = {
        "introvert_extrovert": personality.get("introvert_extrovert", room_prefs["social"]),
        "conflict_style": personality.get("conflict_style", 1),
        "routine_level": personality.get("routine_level", 4 if room_prefs["sleep"] == 0 else 2 if room_prefs["sleep"] == 2 else 3),
        "sharing_level": personality.get("sharing_level", 3),
    }
    room_traits = {
        "cleanliness_tolerance": max(1, min(5, 6 - room_prefs["cleanliness"])),
        "noise_tolerance": room_prefs["noise"],
        "social_tolerance": room_prefs["social"],
        "conflict_style": max(1, min(5, 5 - room_personality["conflict_style"])),
        "flexibility": max(1, min(5, 6 - room_personality["routine_level"])),
    }
    return room_prefs, room_personality, room_traits


def calculate_compatibility(pref_a: dict, pref_b: dict, pers_a: dict, pers_b: dict, cluster_a: int = None, cluster_b: int = None, traits_a: dict = None, traits_b: dict = None) -> dict:
    weight_config = get_runtime_weight_config()

    lifestyle_raw, lifestyle_max, highlights, warnings = calculate_lifestyle_score(pref_a, pref_b, weight_config)
    personality_raw, personality_max = calculate_personality_score(pers_a, pers_b)
    trait_raw, trait_max, trait_highlights, trait_warnings = calculate_trait_score(traits_a, traits_b)
    highlights.extend(trait_highlights)
    warnings.extend(trait_warnings)

    lifestyle_pct = (lifestyle_raw / lifestyle_max) * 100 if lifestyle_max else 0.0
    personality_pct = (personality_raw / personality_max) * 100 if personality_max else 0.0
    trait_pct = (trait_raw / trait_max) * 100 if trait_max else 0.0
    penalties = calculate_penalties(pref_a, pref_b)

    cluster_bonus = 0.0
    if cluster_a is not None and cluster_b is not None and cluster_a == cluster_b:
        cluster_bonus = CLUSTER_BONUS
        highlights.append("Same lifestyle cluster gives an extra fit boost")

    category_factors = {
        "lifestyle": BASE_CATEGORY_FACTORS["lifestyle"],
        "personality": BASE_CATEGORY_FACTORS["personality"] * weight_config.get("personality", 1.0),
        "trait": BASE_CATEGORY_FACTORS["trait"] * weight_config.get("trait", 1.0),
        "cluster": BASE_CATEGORY_FACTORS["cluster"],
    }
    factor_sum = sum(category_factors.values()) or 1.0

    total = (
        lifestyle_pct * (category_factors["lifestyle"] / factor_sum)
        + personality_pct * (category_factors["personality"] / factor_sum)
        + trait_pct * (category_factors["trait"] / factor_sum)
        + (100.0 if cluster_bonus else 0.0) * (category_factors["cluster"] / factor_sum)
        + penalties
    )
    total = max(0.0, min(100.0, total))

    return {
        "total_score": round(total, 1),
        "lifestyle_score": round(lifestyle_pct, 1),
        "personality_score": round(personality_pct, 1),
        "trait_score": round(trait_pct, 1),
        "cluster_bonus": cluster_bonus,
        "penalties": round(penalties, 1),
        "highlights": highlights,
        "warnings": warnings,
        "weights": weight_config,
        "recommendation": generate_recommendation(total, "LOW"),
    }
