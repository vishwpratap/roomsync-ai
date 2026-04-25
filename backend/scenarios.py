
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
    {
        "slug": "bathroom_schedule",
        "title": "Bathroom Rush Hour",
        "question": "You both need to get ready at 8 AM for work/school. How do you handle the bathroom situation?",
        "description": "Morning routines can make or break the day.",
        "icon": "🚿",
        "category": "routine",
        "options": [
            {"text": "Wake up earlier to avoid conflict", "emoji": "⏰", "traits": {"flexibility": 5, "planning": 5, "conflict_style": 5}},
            {"text": "Alternate days - fair is fair", "emoji": "📅", "traits": {"flexibility": 3, "planning": 4, "conflict_style": 3}},
            {"text": "Discuss and create a schedule", "emoji": "📝", "traits": {"flexibility": 2, "planning": 3, "conflict_style": 2}},
            {"text": "I need my time - they can adjust", "emoji": "😤", "traits": {"flexibility": 1, "planning": 2, "conflict_style": 1}},
        ],
    },
    {
        "slug": "shared_expenses",
        "title": "Bill Splitting",
        "question": "Your roommate forgets to pay their share of the electricity bill for the second month. What do you do?",
        "description": "Money matters can strain even the best friendships.",
        "icon": "💰",
        "category": "financial",
        "options": [
            {"text": "Pay it for them - no big deal", "emoji": "💸", "traits": {"flexibility": 5, "conflict_style": 5, "trust": 5}},
            {"text": "Remind them gently, but don't stress", "emoji": "🤝", "traits": {"flexibility": 3, "conflict_style": 3, "trust": 3}},
            {"text": "Set up automatic payments together", "emoji": "📱", "traits": {"flexibility": 2, "conflict_style": 2, "trust": 2}},
            {"text": "This is unacceptable - need a serious talk", "emoji": "😠", "traits": {"flexibility": 1, "conflict_style": 1, "trust": 1}},
        ],
    },
    {
        "slug": "study_focus",
        "title": "Study Time",
        "question": "You have an important exam tomorrow. Your roommate wants to watch a movie in the living room. What happens?",
        "description": "Focus needs and social balance are key.",
        "icon": "📚",
        "category": "routine",
        "options": [
            {"text": "Study at the library - they can enjoy their time", "emoji": "🏛️", "traits": {"flexibility": 5, "conflict_style": 5, "social_tolerance": 4}},
            {"text": "Ask them to use headphones, stay in the room", "emoji": "🎧", "traits": {"flexibility": 3, "conflict_style": 3, "social_tolerance": 3}},
            {"text": "Suggest they watch it another day", "emoji": "📅", "traits": {"flexibility": 2, "conflict_style": 2, "social_tolerance": 2}},
            {"text": "I need quiet - they need to leave", "emoji": "🚫", "traits": {"flexibility": 1, "conflict_style": 1, "social_tolerance": 1}},
        ],
    },
]


def force_seed_demo_scenarios():
    """Force insert 4 demo scenarios regardless of existing data"""
    demo_scenarios = [
        {
            "slug": "cleanliness_kitchen",
            "title": "Shared Kitchen Cleanup",
            "question": "Your roommate keeps leaving the shared kitchen a little messy after cooking. What feels most natural to you?",
            "description": "Use this when you want to measure cleanliness expectations in shared spaces.",
            "icon": "🧹",
            "category": "cleanliness",
            "options": [
                {"text": "It does not bother me much.", "emoji": "😌", "traits": {"cleanliness_tolerance": 5, "conflict_style": 5, "flexibility": 5}},
                {"text": "I will usually tidy up and move on.", "emoji": "🧹", "traits": {"cleanliness_tolerance": 3, "conflict_style": 4, "flexibility": 4}},
                {"text": "I would ask for a cleaner routine.", "emoji": "💬", "traits": {"cleanliness_tolerance": 2, "conflict_style": 3, "flexibility": 3}},
                {"text": "I expect the kitchen to stay clean every time.", "emoji": "⚠️", "traits": {"cleanliness_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
            ],
        },
        {
            "slug": "noise_late_night",
            "title": "Late-Night Noise",
            "question": "It is getting late and your roommate starts making more noise than usual. What do you usually do?",
            "description": "Use this to capture sound sensitivity and quiet-hour expectations.",
            "icon": "🔊",
            "category": "noise",
            "options": [
                {"text": "I can usually ignore it.", "emoji": "😌", "traits": {"noise_tolerance": 5, "conflict_style": 5, "flexibility": 5}},
                {"text": "I adjust first and see if it settles down.", "emoji": "🎧", "traits": {"noise_tolerance": 4, "conflict_style": 4, "flexibility": 4}},
                {"text": "I ask them to lower the noise a little.", "emoji": "💬", "traits": {"noise_tolerance": 2, "conflict_style": 3, "flexibility": 3}},
                {"text": "I want strict quiet hours at night.", "emoji": "🚫", "traits": {"noise_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
            ],
        },
        {
            "slug": "social_guests",
            "title": "Unexpected Guests",
            "question": "Your roommate invites friends over without much notice. What feels closest to your reaction?",
            "description": "Use this to evaluate guest comfort and social energy.",
            "icon": "👥",
            "category": "social",
            "options": [
                {"text": "I am usually happy to roll with it.", "emoji": "🎉", "traits": {"social_tolerance": 5, "conflict_style": 5, "flexibility": 5}},
                {"text": "I can adapt, even if I need a little space.", "emoji": "🏠", "traits": {"social_tolerance": 3, "conflict_style": 4, "flexibility": 4}},
                {"text": "I would like a heads-up next time.", "emoji": "💬", "traits": {"social_tolerance": 2, "conflict_style": 3, "flexibility": 2}},
                {"text": "I need firm guest boundaries.", "emoji": "🚫", "traits": {"social_tolerance": 1, "conflict_style": 1, "flexibility": 1}},
            ],
        },
        {
            "slug": "sharing_items",
            "title": "Shared Items",
            "question": "Your roommate uses something of yours without asking. How do you handle it?",
            "description": "Use this to measure boundaries and shared-property expectations.",
            "icon": "🤝",
            "category": "sharing",
            "options": [
                {"text": "I am pretty relaxed about sharing.", "emoji": "😊", "traits": {"flexibility": 5, "conflict_style": 5, "social_tolerance": 5}},
                {"text": "I usually let it go once or twice.", "emoji": "🤷", "traits": {"flexibility": 3, "conflict_style": 3, "social_tolerance": 3}},
                {"text": "I remind them to ask first next time.", "emoji": "💬", "traits": {"flexibility": 2, "conflict_style": 2, "social_tolerance": 2}},
                {"text": "I want very clear personal boundaries.", "emoji": "🚫", "traits": {"flexibility": 1, "conflict_style": 1, "social_tolerance": 1}},
            ],
        },
    ]
    
    for scenario in demo_scenarios:
        print(f"[Force Seed] Processing scenario: {scenario['slug']}")
        # Check if scenario already exists by slug
        existing = execute_query("SELECT id FROM scenarios WHERE slug=%s", (scenario["slug"],), fetch_one=True)
        if existing:
            # Update existing scenario
            scenario_id = existing["id"]
            print(f"[Force Seed] Updating existing scenario with ID: {scenario_id}")
            execute_update(
                "UPDATE scenarios SET title=%s, question=%s, description=%s, icon=%s, category=%s WHERE id=%s",
                (scenario["title"], scenario["question"], scenario.get("description"), scenario.get("icon"), scenario.get("category"), scenario_id),
            )
            execute_update("DELETE FROM scenario_options WHERE scenario_id=%s", (scenario_id,))
            print(f"[Force Seed] Deleted old options for scenario ID: {scenario_id}")
        else:
            # Insert new scenario
            print(f"[Force Seed] Inserting new scenario: {scenario['slug']}")
            scenario_id = execute_insert(
                "INSERT INTO scenarios (slug, title, question, description, icon, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                (scenario["slug"], scenario["title"], scenario["question"], scenario.get("description"), scenario.get("icon"), scenario.get("category")),
            )
            print(f"[Force Seed] Inserted scenario with ID: {scenario_id}")
        
        # Insert options
        print(f"[Force Seed] Inserting {len(scenario['options'])} options for scenario ID: {scenario_id}")
        for index, option in enumerate(scenario["options"]):
            try:
                option_id = execute_insert(
                    "INSERT INTO scenario_options (scenario_id, option_order, option_text, emoji, trait_mapping_json) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (scenario_id, index, option["text"], option.get("emoji"), json.dumps(option["traits"])),
                )
                print(f"[Force Seed] Inserted option {index} with ID: {option_id}")
            except Exception as e:
                print(f"[Force Seed] Error inserting option {index}: {str(e)}")
                import traceback
                traceback.print_exc()
    
    return {"message": "Demo scenarios seeded successfully"}


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
                "icon": row.get("icon") or "",
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
                "emoji": row.get("emoji") or "",
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
        "icon": scenario.get("icon") or "",
        "category": scenario.get("category") or "general",
        "options": [{"text": option["text"], "emoji": option.get("emoji") or "", "traits": option["traits"]} for option in scenario["options"]],
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
