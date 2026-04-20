"""
RoomSync AI - Match Cache Module
Precomputes and caches compatibility scores for performance optimization
"""

import json
from backend.db import execute_query, execute_update, save_match_score, invalidate_user_matches
from backend.logic import calculate_compatibility, generate_recommendation
from backend.risk import detect_risks
from backend.traits import get_user_traits


def precompute_matches_for_user(user_id):
    """
    Calculate compatibility between a user and all other users,
    then cache the results in the match_scores table.
    Called when:
    - User completes questionnaire
    - New user is added
    - User updates preferences
    - Admin updates weights
    """
    # Get user data
    user, user_preferences, user_personality, user_traits = _get_user_data(user_id)
    
    # Get all other users
    all_users = execute_query(
        """
        SELECT u.id, u.name, u.age, u.profession, u.gender, u.roommate_type, u.cluster_id,
               p.sleep, p.cleanliness, p.noise, p.smoking, p.guests, p.social, p.cooking,
               pe.introvert_extrovert, pe.conflict_style, pe.routine_level, pe.sharing_level
        FROM users u
        JOIN preferences p ON u.id = p.user_id
        JOIN personality pe ON u.id = pe.user_id
        WHERE u.id != %s AND u.age IS NOT NULL
        """,
        (user_id,),
        fetch_all=True
    ) or []
    
    # Invalidate old cached matches for this user
    invalidate_user_matches(user_id)
    
    # Calculate and cache compatibility with each user
    for other in all_users:
        other_preferences = {key: other[key] for key in ["sleep", "cleanliness", "noise", "smoking", "guests", "social", "cooking"]}
        other_personality = {key: other[key] for key in ["introvert_extrovert", "conflict_style", "routine_level", "sharing_level"]}
        other_traits = get_user_traits(other["id"])
        
        result = calculate_compatibility(
            user_preferences, other_preferences,
            user_personality, other_personality,
            user.get("cluster_id"), other.get("cluster_id"),
            user_traits, other_traits
        )
        
        risk_info = detect_risks(
            user_preferences, other_preferences,
            user_personality, other_personality,
            user_traits, other_traits
        )
        
        recommendation = generate_recommendation(result["total_score"], risk_info["risk_level"])
        
        # Save to cache
        save_match_score(
            user_id, other["id"],
            result["total_score"],
            result["lifestyle_score"],
            result["personality_score"],
            result["trait_score"],
            risk_info["risk_level"],
            result["highlights"][:3],
            result["warnings"][:2],
            risk_info["conflicts"]
        )
    
    return len(all_users)


def _get_user_data(user_id):
    """Helper function to get complete user data including preferences and personality"""
    user = execute_query(
        "SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE id=%s",
        (user_id,),
        fetch_one=True
    )
    if not user:
        raise ValueError(f"User {user_id} not found")
    
    preferences = execute_query(
        "SELECT sleep, cleanliness, noise, smoking, guests, social, cooking FROM preferences WHERE user_id=%s",
        (user_id,),
        fetch_one=True
    )
    
    personality = execute_query(
        "SELECT introvert_extrovert, conflict_style, routine_level, sharing_level FROM personality WHERE user_id=%s",
        (user_id,),
        fetch_one=True
    )
    
    traits = get_user_traits(user_id)
    
    return user, preferences, personality, traits


def recompute_all_matches():
    """
    Recompute all compatibility scores for all users.
    Called when admin updates weight configuration.
    """
    all_users = execute_query("SELECT id FROM users WHERE age IS NOT NULL", fetch_all=True) or []
    
    total_computed = 0
    for user in all_users:
        count = precompute_matches_for_user(user["id"])
        total_computed += count
    
    return {"total_users": len(all_users), "total_computed": total_computed}
