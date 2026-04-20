
"""
RoomSync AI - Scenario Management and Seed Data
"""

import json
from db import execute_insert, execute_query, execute_update

DEFAULT_SCENARIOS = [
    {
        "slug": "dishes_overnight",
        "title": "The Unwashed Dishes",
        "question": "Your roommate leaves dishes unwashed in the sink overnight. What do you do?",
        "description": "A small mess can reveal a lot about shared-space expectations.",
        "icon": "🍽️",
        "category": "cleanliness",
        "options": [
            {"text": "Do not even notice - no big deal", "emoji": "😌", "traits": {"cleanliness_tolerance": 5, "conflict_style": 5, "flexibility": 5}},
            {"text": "Clean them yourself without saying anything", "emoji": "🧹", "traits": {"cleanliness_tolerance": 2, "conflict_style": 4, "flexibility": 4}},
            {"text": "Politely ask them to wash up next time", "emoji": "💬", "traits": {"cleanliness_tolerance": 2, "conflict_style": 3, "flexibility": 3}},
            {"text": "Get annoyed - this should not happen", "emoji": "😤", "traits": {"cleanliness_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
        ],
    },
    {
        "slug": "loud_music_night",
        "title": "Late Night Beats",
        "question": "It is 11 PM on a weeknight and your roommate starts playing loud music. How do you react?",
        "description": "Noise tolerance matters more than people think.",
        "icon": "🎵",
        "category": "noise",
        "options": [
            {"text": "Join in - the more the merrier", "emoji": "🎉", "traits": {"noise_tolerance": 5, "social_tolerance": 5, "flexibility": 5}},
            {"text": "Put on headphones and ignore it", "emoji": "🎧", "traits": {"noise_tolerance": 4, "conflict_style": 5, "flexibility": 4}},
            {"text": "Ask them to lower the volume a bit", "emoji": "🤫", "traits": {"noise_tolerance": 2, "conflict_style": 3, "flexibility": 3}},
            {"text": "Tell them to stop immediately", "emoji": "🛑", "traits": {"noise_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
        ],
    },
    {
        "slug": "surprise_guests",
        "title": "Unexpected Visitors",
        "question": "Your roommate invites 5 friends over without telling you. You planned a quiet evening. What do you do?",
        "description": "Social energy can make or break a roommate fit.",
        "icon": "🚪",
        "category": "social",
        "options": [
            {"text": "Awesome - more people to hang out with", "emoji": "🥳", "traits": {"social_tolerance": 5, "flexibility": 5, "conflict_style": 5}},
            {"text": "Join for a bit, then retreat to your room", "emoji": "👋", "traits": {"social_tolerance": 3, "flexibility": 4, "conflict_style": 4}},
            {"text": "Say you would appreciate a heads up next time", "emoji": "📱", "traits": {"social_tolerance": 2, "conflict_style": 3, "flexibility": 2}},
            {"text": "Confront them - this is your space too", "emoji": "😠", "traits": {"social_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
        ],
    },
    {
        "slug": "fridge_food",
        "title": "The Missing Leftovers",
        "question": "You discover your roommate ate your leftover food without asking. How do you handle it?",
        "description": "Shared boundaries often show up in everyday moments.",
        "icon": "🍕",
        "category": "sharing",
        "options": [
            {"text": "No worries - food is meant to be shared", "emoji": "😊", "traits": {"flexibility": 5, "conflict_style": 5, "social_tolerance": 5}},
            {"text": "Mention it casually, but do not make a big deal", "emoji": "🤷", "traits": {"flexibility": 3, "conflict_style": 3, "social_tolerance": 3}},
            {"text": "Set a clear rule: ask before taking", "emoji": "📋", "traits": {"flexibility": 2, "conflict_style": 2, "social_tolerance": 2}},
            {"text": "Label everything - boundaries are important", "emoji": "🏷️", "traits": {"flexibility": 1, "conflict_style": 2, "social_tolerance": 1}},
        ],
    },
    {
        "slug": "early_alarm",
        "title": "The Early Alarm",
        "question": "Your roommate's alarm goes off at 5:30 AM every day and wakes you up. What is your approach?",
        "description": "Sleep compatibility is a classic roommate issue.",
        "icon": "⏰",
        "category": "routine",
        "options": [
            {"text": "Might as well start the day early too", "emoji": "🌅", "traits": {"flexibility": 5, "noise_tolerance": 4, "conflict_style": 5}},
            {"text": "Use earplugs and adapt", "emoji": "😴", "traits": {"flexibility": 4, "noise_tolerance": 3, "conflict_style": 4}},
            {"text": "Ask for a vibrating alarm instead", "emoji": "📳", "traits": {"flexibility": 2, "noise_tolerance": 2, "conflict_style": 3}},
            {"text": "This needs to change right away", "emoji": "⚠️", "traits": {"flexibility": 1, "noise_tolerance": 1, "conflict_style": 1}},
        ],
    },
]


def seed_default_scenarios():
    existing = execute_query("SELECT id FROM scenarios LIMIT 1", fetch_one=True)
    if existing:
        return

    for scenario in DEFAULT_SCENARIOS:
        scenario_id = execute_insert(
            "INSERT INTO scenarios (slug, title, question, description, icon, category) VALUES (%s, %s, %s, %s, %s, %s)",
            (scenario["slug"], scenario["title"], scenario["question"], scenario.get("description"), scenario.get("icon"), scenario.get("category")),
        )
        for index, option in enumerate(scenario["options"]):
            execute_insert(
                "INSERT INTO scenario_options (scenario_id, option_order, option_text, emoji, trait_mapping_json) VALUES (%s, %s, %s, %s, %s)",
                (scenario_id, index, option["text"], option.get("emoji"), json.dumps(option["traits"])),
            )


def _parse_scenarios(rows):
    scenarios = []
    current = None
    current_id = None
    for row in rows:
        if current_id != row["scenario_db_id"]:
            current_id = row["scenario_db_id"]
            current = {
                "scenario_id": row["scenario_db_id"],
                "db_id": row["scenario_db_id"],
                "id": row["slug"],
                "slug": row["slug"],
                "title": row["title"],
                "question": row["question"],
                "description": row.get("description"),
                "icon": row.get("icon") or "SCENARIO",
                "category": row.get("category") or "general",
                "options": [],
            }
            scenarios.append(current)
        if row.get("option_id") is not None:
            trait_mapping = row.get("trait_mapping_json")
            if isinstance(trait_mapping, str):
                trait_mapping = json.loads(trait_mapping)
            current["options"].append({
                "id": row["option_id"],
                "text": row["option_text"],
                "emoji": row.get("emoji") or "OPTION",
                "traits": trait_mapping or {},
            })
    return scenarios


def get_all_scenarios(include_db_ids=False):
    rows = execute_query(
        """
        SELECT s.id AS scenario_db_id, s.slug, s.title, s.question, s.description, s.icon, s.category,
               o.id AS option_id, o.option_order, o.option_text, o.emoji, o.trait_mapping_json
        FROM scenarios s
        LEFT JOIN scenario_options o ON s.id = o.scenario_id
        ORDER BY s.id, o.option_order, o.id
        """,
        fetch_all=True,
    ) or []
    scenarios = _parse_scenarios(rows)
    if include_db_ids:
        return scenarios
    return [{
        "id": scenario["slug"],
        "title": scenario["title"],
        "description": scenario["question"],
        "icon": scenario.get("icon") or "SCENARIO",
        "category": scenario.get("category") or "general",
        "options": [{"text": option["text"], "emoji": option.get("emoji") or "OPTION", "traits": option["traits"]} for option in scenario["options"]],
    } for scenario in scenarios]


def get_scenario_by_id(identifier):
    rows = execute_query(
        """
        SELECT s.id AS scenario_db_id, s.slug, s.title, s.question, s.description, s.icon, s.category,
               o.id AS option_id, o.option_order, o.option_text, o.emoji, o.trait_mapping_json
        FROM scenarios s
        LEFT JOIN scenario_options o ON s.id = o.scenario_id
        WHERE s.slug = %s OR s.id = %s
        ORDER BY o.option_order, o.id
        """,
        (str(identifier), identifier if str(identifier).isdigit() else -1),
        fetch_all=True,
    ) or []
    scenarios = _parse_scenarios(rows)
    return scenarios[0] if scenarios else None


def create_scenario(payload):
    scenario_id = execute_insert(
        "INSERT INTO scenarios (slug, title, question, description, icon, category) VALUES (%s, %s, %s, %s, %s, %s)",
        (payload["slug"], payload["title"], payload["question"], payload.get("description"), payload.get("icon"), payload.get("category")),
    )
    for index, option in enumerate(payload.get("options", [])):
        execute_insert(
            "INSERT INTO scenario_options (scenario_id, option_order, option_text, emoji, trait_mapping_json) VALUES (%s, %s, %s, %s, %s)",
            (scenario_id, index, option["text"], option.get("emoji"), json.dumps(option.get("traits", {}))),
        )
    return get_scenario_by_id(scenario_id)


def update_scenario(scenario_id, payload):
    execute_update(
        "UPDATE scenarios SET slug=%s, title=%s, question=%s, description=%s, icon=%s, category=%s WHERE id=%s",
        (payload["slug"], payload["title"], payload["question"], payload.get("description"), payload.get("icon"), payload.get("category"), scenario_id),
    )
    execute_update("DELETE FROM scenario_options WHERE scenario_id=%s", (scenario_id,))
    for index, option in enumerate(payload.get("options", [])):
        execute_insert(
            "INSERT INTO scenario_options (scenario_id, option_order, option_text, emoji, trait_mapping_json) VALUES (%s, %s, %s, %s, %s)",
            (scenario_id, index, option["text"], option.get("emoji"), json.dumps(option.get("traits", {}))),
        )
    return get_scenario_by_id(scenario_id)
