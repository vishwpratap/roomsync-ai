"""
RoomSync AI - Risk Detection Engine
Detects potential conflicts between roommate pairs using preferences, personality, and traits.
"""


def detect_risks(pref_a: dict, pref_b: dict, pers_a: dict, pers_b: dict,
                 traits_a: dict = None, traits_b: dict = None) -> dict:
    """
    Analyze two users' profiles for potential conflicts.
    Returns risk_level and list of conflict details.
    """
    conflicts = []

    # ── Lifestyle Conflicts ──────────────────────────────

    # Cleanliness gap
    clean_diff = abs(pref_a.get("cleanliness", 3) - pref_b.get("cleanliness", 3))
    if clean_diff >= 4:
        conflicts.append({
            "field": "cleanliness",
            "severity": "HIGH",
            "description": f"Extreme cleanliness gap ({pref_a['cleanliness']} vs {pref_b['cleanliness']}). "
                           "This often causes major friction."
        })
    elif clean_diff >= 3:
        conflicts.append({
            "field": "cleanliness",
            "severity": "HIGH",
            "description": f"Significant cleanliness difference ({pref_a['cleanliness']} vs {pref_b['cleanliness']}). "
                           "Discuss cleaning expectations early."
        })
    elif clean_diff >= 2:
        conflicts.append({
            "field": "cleanliness",
            "severity": "MEDIUM",
            "description": "Moderate cleanliness difference. Set clear shared space rules."
        })

    # Smoking mismatch
    smoke_a = pref_a.get("smoking", 0)
    smoke_b = pref_b.get("smoking", 0)
    smoke_diff = abs(smoke_a - smoke_b)
    if smoke_diff == 2:
        conflicts.append({
            "field": "smoking",
            "severity": "HIGH",
            "description": f"Major smoking mismatch (non-smoker vs heavy smoker). "
                           "This is a dealbreaker for many people."
        })
    elif smoke_diff == 1:
        conflicts.append({
            "field": "smoking",
            "severity": "MEDIUM",
            "description": "Different smoking levels. Discuss indoor smoking rules."
        })

    # Sleep schedule mismatch
    sleep_diff = abs(pref_a.get("sleep", 1) - pref_b.get("sleep", 1))
    if sleep_diff == 2:
        conflicts.append({
            "field": "sleep",
            "severity": "MEDIUM",
            "description": "Opposite sleep schedules (early bird vs night owl). "
                           "This can disrupt each other's rest."
        })
    elif sleep_diff == 1:
        conflicts.append({
            "field": "sleep",
            "severity": "LOW",
            "description": "Slightly different sleep schedules. Generally manageable."
        })

    # Noise gap
    noise_diff = abs(pref_a.get("noise", 3) - pref_b.get("noise", 3))
    if noise_diff >= 3:
        conflicts.append({
            "field": "noise",
            "severity": "MEDIUM",
            "description": f"Large noise tolerance gap ({pref_a['noise']} vs {pref_b['noise']}). "
                           "Discuss quiet hours."
        })
    elif noise_diff >= 2:
        conflicts.append({
            "field": "noise",
            "severity": "LOW",
            "description": "Some difference in noise preferences. May need compromise."
        })

    # Guest frequency
    guest_diff = abs(pref_a.get("guests", 1) - pref_b.get("guests", 1))
    if guest_diff >= 2:
        conflicts.append({
            "field": "guests",
            "severity": "MEDIUM",
            "description": "Different guest preferences. Agree on a guest policy."
        })

    # Social energy
    social_diff = abs(pref_a.get("social", 3) - pref_b.get("social", 3))
    if social_diff >= 3:
        conflicts.append({
            "field": "social",
            "severity": "LOW",
            "description": "Different social energy levels. Respect each other's boundaries."
        })

    # ── Personality Conflicts ────────────────────────────

    # Conflict resolution style
    conflict_diff = abs(pers_a.get("conflict_style", 1) - pers_b.get("conflict_style", 1))
    if conflict_diff == 2:
        conflicts.append({
            "field": "conflict_style",
            "severity": "MEDIUM",
            "description": "Very different conflict resolution approaches. "
                           "One prefers avoidance while the other is confrontational."
        })

    # Sharing level
    share_diff = abs(pers_a.get("sharing_level", 3) - pers_b.get("sharing_level", 3))
    if share_diff >= 3:
        conflicts.append({
            "field": "sharing_level",
            "severity": "LOW",
            "description": "Different comfort levels with sharing belongings."
        })

    # ── Trait-Based Conflicts (new) ──────────────────────

    if traits_a and traits_b:
        # Cleanliness tolerance gap
        ct_diff = abs(traits_a.get("cleanliness_tolerance", 3) - traits_b.get("cleanliness_tolerance", 3))
        if ct_diff >= 3:
            conflicts.append({
                "field": "cleanliness_tolerance",
                "severity": "HIGH",
                "description": "Very different cleanliness tolerance levels. "
                               "One is very tolerant while the other expects high standards."
            })
        elif ct_diff >= 2:
            conflicts.append({
                "field": "cleanliness_tolerance",
                "severity": "MEDIUM",
                "description": "Moderate difference in cleanliness tolerance. Set expectations early."
            })

        # Noise tolerance gap
        nt_diff = abs(traits_a.get("noise_tolerance", 3) - traits_b.get("noise_tolerance", 3))
        if nt_diff >= 3:
            conflicts.append({
                "field": "noise_tolerance",
                "severity": "MEDIUM",
                "description": "Significant noise tolerance difference. One is much more sensitive to noise."
            })

        # Social tolerance gap
        st_diff = abs(traits_a.get("social_tolerance", 3) - traits_b.get("social_tolerance", 3))
        if st_diff >= 3:
            conflicts.append({
                "field": "social_tolerance",
                "severity": "MEDIUM",
                "description": "Very different social boundaries. One values privacy, the other is highly social."
            })

        # Conflict style (trait) gap
        cs_diff = abs(traits_a.get("conflict_style", 3) - traits_b.get("conflict_style", 3))
        if cs_diff >= 3:
            conflicts.append({
                "field": "conflict_approach",
                "severity": "MEDIUM",
                "description": "Opposite conflict approaches. May struggle to resolve disagreements constructively."
            })

        # Flexibility gap
        fl_diff = abs(traits_a.get("flexibility", 3) - traits_b.get("flexibility", 3))
        if fl_diff >= 3:
            conflicts.append({
                "field": "flexibility",
                "severity": "LOW",
                "description": "Different flexibility levels. One is very rigid while the other is easy-going."
            })

    # ── Determine Overall Risk Level ─────────────────────
    high_count = sum(1 for c in conflicts if c["severity"] == "HIGH")
    medium_count = sum(1 for c in conflicts if c["severity"] == "MEDIUM")

    if high_count >= 2:
        risk_level = "HIGH"
    elif high_count >= 1:
        risk_level = "HIGH"
    elif medium_count >= 2:
        risk_level = "MEDIUM"
    elif medium_count >= 1:
        risk_level = "MEDIUM"
    elif conflicts:
        risk_level = "LOW"
    else:
        risk_level = "LOW"

    return {
        "risk_level": risk_level,
        "conflicts": conflicts,
    }
