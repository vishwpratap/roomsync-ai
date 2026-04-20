"""
RoomSync AI - User Type Classifier
Rule-based classification using preferences, personality, and behavioral traits.
"""


def classify_user_type(preferences: dict, personality: dict, traits: dict = None) -> str:
    """
    Classify a user into a roommate type based on their preferences, personality, and traits.
    Returns a descriptive label string.
    """
    sleep = preferences.get("sleep", 1)
    cleanliness = preferences.get("cleanliness", 3)
    noise = preferences.get("noise", 3)
    smoking = preferences.get("smoking", 0)
    guests = preferences.get("guests", 1)
    social = preferences.get("social", 3)
    cooking = preferences.get("cooking", 1)

    introvert = personality.get("introvert_extrovert", 3)
    routine = personality.get("routine_level", 3)
    sharing = personality.get("sharing_level", 3)

    flexibility = 3
    conflict = 3
    social_tol = 3
    clean_tol = 3
    noise_tol = 3
    if traits:
        flexibility = traits.get("flexibility", 3)
        conflict = traits.get("conflict_style", 3)
        social_tol = traits.get("social_tolerance", 3)
        clean_tol = traits.get("cleanliness_tolerance", 3)
        noise_tol = traits.get("noise_tolerance", 3)

    if sleep == 2 and social >= 4 and introvert >= 4:
        return "Night Owl Social"
    if sleep == 2 and introvert <= 2:
        return "Night Owl Introvert"
    if sleep == 2:
        return "Night Owl"
    if sleep == 0 and routine >= 4:
        return "Early Bird Planner"
    if sleep == 0:
        return "Early Riser"
    if cleanliness >= 4 and routine >= 4 and noise <= 2:
        return "Disciplined Minimalist"
    if social >= 4 and guests >= 2 and introvert >= 4:
        return "Social Explorer"
    if introvert <= 2 and noise <= 2 and social <= 2:
        return "Quiet Introvert"
    if cleanliness == 5 and routine >= 4:
        return "Clean & Organized"
    if social >= 4 and guests >= 2 and noise >= 4:
        return "Social Butterfly"
    if traits and flexibility >= 4 and conflict >= 4:
        return "The Peacekeeper"
    if traits and flexibility >= 4 and social_tol >= 4 and noise_tol >= 4:
        return "Adaptable Free Spirit"
    if traits and flexibility <= 2 and clean_tol <= 2:
        return "Boundary Setter"
    if cooking >= 2 and sharing >= 4:
        return "Home Chef"
    if noise >= 3 and social >= 3 and cleanliness <= 3:
        return "Easygoing Roommate"
    if noise <= 2 and routine >= 4 and social <= 2:
        return "Studious & Focused"
    return "Balanced Roommate"
