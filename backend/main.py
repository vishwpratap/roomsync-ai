"""
RoomSync AI - Extended FastAPI Application
"""

import json
import os
import shutil
import uuid
import bcrypt
from collections import Counter
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.classifier import classify_user_type
from backend.db import execute_insert, execute_query, execute_update, ensure_schema, get_match_score, get_top_matches_for_user, save_match_score, is_db_connected
from backend.logic import calculate_compatibility, generate_recommendation, get_runtime_weight_config
from backend.match_cache import precompute_matches_for_user
from backend.ml import run_clustering
from backend.models import AdminLogin, CompatibilityRequest, RoommateRequestInput, ScenarioCreateInput, ScenarioProfileInput, UserLogin, UserProfileInput, UserSignup, WeightsUpdateInput
from backend.risk import detect_risks
from backend.scenarios import create_scenario, get_all_scenarios, get_scenario_by_id, seed_default_scenarios, update_scenario
from backend.traits import compute_traits, derive_personality, derive_preferences, get_user_traits, save_scenario_responses, save_traits

app = FastAPI(title="RoomSync AI", description="Behavior-based roommate compatibility platform", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
UPLOADS_DIR = os.path.join(FRONTEND_DIR, "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")
if os.path.exists(UPLOADS_DIR):
    app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    # If the error is related to None/DB connection, return a safe response
    error_msg = str(exc).lower()
    if "none" in error_msg or "connection" in error_msg or "mysql" in error_msg:
        return JSONResponse(
            status_code=503,
            content={"detail": "Database not connected - temporarily disabled for cloud deployment"}
        )
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.on_event("startup")
async def startup_event():
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    try:
        # ensure_schema()
        # seed_default_scenarios()
        print("[Startup] Database initialization skipped (temporarily disabled for cloud deployment)")
    except Exception as exc:
        print(f"[Startup] Error initializing database: {exc}")


@app.get("/")
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "RoomSync AI API is running. Frontend not found."}


@app.post("/init-db")
async def init_db():
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    # ensure_schema()
    # seed_default_scenarios()
    return {"message": "Database initialization temporarily disabled for cloud deployment"}


def _parse_json_field(value, default=None):
    if value is None:
        return default if default is not None else {}
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return default if default is not None else {}


def _require_admin(x_admin_id: Optional[int] = Header(default=None, alias="X-Admin-Id")):
    if not x_admin_id:
        raise HTTPException(status_code=401, detail="Admin authentication required")
    admin = execute_query("SELECT id, email FROM admins WHERE id=%s", (x_admin_id,), fetch_one=True)
    if not admin:
        raise HTTPException(status_code=401, detail="Invalid admin session")
    return admin


def _get_user_data(user_id: int):
    user = execute_query("SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE id=%s", (user_id,), fetch_one=True)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    preferences = execute_query("SELECT sleep, cleanliness, noise, smoking, guests, social, cooking FROM preferences WHERE user_id=%s", (user_id,), fetch_one=True)
    personality = execute_query("SELECT introvert_extrovert, conflict_style, routine_level, sharing_level FROM personality WHERE user_id=%s", (user_id,), fetch_one=True)
    if not preferences or not personality:
        raise HTTPException(status_code=400, detail=f"User {user_id} has not completed their profile")
    traits = get_user_traits(user_id)
    return user, preferences, personality, traits


def _log_match(source_type: str, source_id: int, target_type: str, target_id: int, total_score: float, risk_level: str, conflicts: list):
    execute_insert(
        "INSERT INTO match_logs (source_type, source_id, target_type, target_id, compatibility_score, risk_level, conflict_types_json) VALUES (%s, %s, %s, %s, %s, %s, %s)",
        (source_type, source_id, target_type, target_id, total_score, risk_level, json.dumps([conflict["field"] for conflict in conflicts])),
    )


def _serialize_room_post(row):
    post = dict(row)
    post["lifestyle_preference"] = _parse_json_field(post.get("lifestyle_preference"), {})
    post["personality_preference"] = _parse_json_field(post.get("personality_preference"), {})
    images = execute_query("SELECT image_url FROM room_images WHERE post_id=%s ORDER BY id", (post["id"],), fetch_all=True) or []
    post["images"] = [image["image_url"] for image in images]
    return post


def _build_room_match_payload(user, user_preferences, user_personality, user_traits, room_post):
    owner_user, owner_preferences, owner_personality, owner_traits = _get_user_data(room_post["user_id"])
    result = calculate_compatibility(
        user_preferences,
        owner_preferences,
        user_personality,
        owner_personality,
        user.get("cluster_id"),
        owner_user.get("cluster_id"),
        user_traits,
        owner_traits,
    )
    risk_info = detect_risks(user_preferences, owner_preferences, user_personality, owner_personality, user_traits, owner_traits)
    recommendation = generate_recommendation(result["total_score"], risk_info["risk_level"])
    _log_match("user", user["id"], "room_post", room_post["id"], result["total_score"], risk_info["risk_level"], risk_info["conflicts"])
    room_post["compatibility"] = {
        "match": round(result["total_score"]),
        "total_score": result["total_score"],
        "risk_level": risk_info["risk_level"],
        "recommendation": recommendation,
        "breakdown": {"lifestyle": result["lifestyle_score"], "personality": result["personality_score"], "traits": result["trait_score"]},
        "highlights": result["highlights"][:4],
        "warnings": result["warnings"][:4],
        "conflicts": risk_info["conflicts"],
        "insights": [
            f"Compatibility is calculated against {room_post.get('owner_name') or owner_user['name']}'s profile.",
            f"Room location: {room_post['location']}",
            f"Rent expectation: ₹{room_post['rent']}",
        ],
        "owner": {
            "user_id": owner_user["id"],
            "name": owner_user["name"],
            "roommate_type": owner_user.get("roommate_type"),
            "cluster_id": owner_user.get("cluster_id"),
        },
    }
    return room_post


def _save_uploaded_images(files: list[UploadFile]) -> list[str]:
    image_urls = []
    for upload in files:
        if not upload or not upload.filename:
            continue
        extension = os.path.splitext(upload.filename)[1].lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            continue
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = os.path.join(UPLOADS_DIR, filename)
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        image_urls.append(f"/uploads/{filename}")
    return image_urls


def _analytics_snapshot():
    stats = {
        "total_users": execute_query("SELECT COUNT(*) AS total FROM users", fetch_one=True)["total"],
        "total_room_posts": execute_query("SELECT COUNT(*) AS total FROM room_posts", fetch_one=True)["total"],
        "total_matches_generated": execute_query("SELECT COUNT(*) AS total FROM match_logs", fetch_one=True)["total"],
    }
    logs = execute_query("SELECT compatibility_score, risk_level, conflict_types_json FROM match_logs", fetch_all=True) or []
    if not logs:
        stats["risk_distribution"] = {"LOW": 0, "MEDIUM": 0, "HIGH": 0}
        stats["analytics"] = {"high_risk_matches_percent": 0, "most_common_conflict_types": [], "average_compatibility_score": 0}
        return stats

    risk_counts = Counter(log["risk_level"] for log in logs)
    conflict_counts = Counter()
    for log in logs:
        for conflict in _parse_json_field(log.get("conflict_types_json"), []):
            conflict_counts[conflict] += 1

    total_logs = len(logs)
    stats["risk_distribution"] = {"LOW": risk_counts.get("LOW", 0), "MEDIUM": risk_counts.get("MEDIUM", 0), "HIGH": risk_counts.get("HIGH", 0)}
    stats["analytics"] = {
        "high_risk_matches_percent": round((risk_counts.get("HIGH", 0) / total_logs) * 100, 1),
        "most_common_conflict_types": [{"type": key, "count": value} for key, value in conflict_counts.most_common(5)],
        "average_compatibility_score": round(sum(float(log["compatibility_score"]) for log in logs) / total_logs, 1),
    }
    return stats


@app.post("/signup")
async def signup(data: UserSignup):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        raise HTTPException(status_code=503, detail="Database not connected - temporarily disabled for cloud deployment")
    existing = execute_query("SELECT id FROM users WHERE name=%s", (data.name,), fetch_one=True)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    password_hash = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = execute_insert("INSERT INTO users (name, password_hash) VALUES (%s, %s)", (data.name, password_hash))
    return {"message": "Account created successfully", "user_id": user_id, "name": data.name}


@app.post("/login")
async def login(data: UserLogin):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        raise HTTPException(status_code=503, detail="Database not connected - temporarily disabled for cloud deployment")
    user = execute_query("SELECT id, name, password_hash, age, roommate_type FROM users WHERE name=%s", (data.name,), fetch_one=True)
    if not user or not bcrypt.checkpw(data.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful", "user_id": user["id"], "name": user["name"], "has_profile": user["age"] is not None, "roommate_type": user.get("roommate_type"), "role": "user"}


@app.post("/admin/login")
async def admin_login(data: AdminLogin):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        raise HTTPException(status_code=503, detail="Database not connected - temporarily disabled for cloud deployment")
    admin = execute_query("SELECT id, email, password_hash FROM admins WHERE email=%s", (data.email,), fetch_one=True)
    if not admin or not bcrypt.checkpw(data.password.encode("utf-8"), admin["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    return {"message": "Admin login successful", "admin_id": admin["id"], "email": admin["email"], "role": "admin"}


@app.get("/scenarios")
async def list_scenarios():
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        return []
    return get_all_scenarios()


@app.post("/add-user")
async def add_user(data: UserProfileInput):
    user = execute_query("SELECT id FROM users WHERE id=%s", (data.user_id,), fetch_one=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    preferences = data.preferences.model_dump()
    personality = data.personality.model_dump()
    roommate_type = classify_user_type(preferences, personality)
    execute_update("UPDATE users SET age=%s, profession=%s, gender=%s, roommate_type=%s WHERE id=%s", (data.age, data.profession, data.gender, roommate_type, data.user_id))
    execute_insert("INSERT INTO preferences (user_id, sleep, cleanliness, noise, smoking, guests, social, cooking) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE sleep=VALUES(sleep), cleanliness=VALUES(cleanliness), noise=VALUES(noise), smoking=VALUES(smoking), guests=VALUES(guests), social=VALUES(social), cooking=VALUES(cooking)", (data.user_id, preferences["sleep"], preferences["cleanliness"], preferences["noise"], preferences["smoking"], preferences["guests"], preferences["social"], preferences["cooking"]))
    execute_insert("INSERT INTO personality (user_id, introvert_extrovert, conflict_style, routine_level, sharing_level) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE introvert_extrovert=VALUES(introvert_extrovert), conflict_style=VALUES(conflict_style), routine_level=VALUES(routine_level), sharing_level=VALUES(sharing_level)", (data.user_id, personality["introvert_extrovert"], personality["conflict_style"], personality["routine_level"], personality["sharing_level"]))
    
    # Mark user as having completed profile
    execute_update("UPDATE users SET has_profile=TRUE WHERE id=%s", (data.user_id,))
    
    # Precompute matches with all other users
    from backend.match_cache import precompute_matches_for_user
    precompute_matches_for_user(data.user_id)
    
    return {"message": "Profile saved successfully", "user_id": data.user_id, "roommate_type": roommate_type}


@app.post("/add-user-scenarios")
async def add_user_scenarios(data: ScenarioProfileInput):
    user = execute_query("SELECT id FROM users WHERE id=%s", (data.user_id,), fetch_one=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    responses = [{"scenario_id": item.scenario_id, "selected_option": item.selected_option} for item in data.responses]
    traits = compute_traits(responses)
    preferences = derive_preferences(traits)
    personality = derive_personality(traits)
    roommate_type = classify_user_type(preferences, personality, traits)
    execute_update("UPDATE users SET age=%s, profession=%s, gender=%s, roommate_type=%s WHERE id=%s", (data.age, data.profession, data.gender, roommate_type, data.user_id))
    execute_insert("INSERT INTO preferences (user_id, sleep, cleanliness, noise, smoking, guests, social, cooking) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE sleep=VALUES(sleep), cleanliness=VALUES(cleanliness), noise=VALUES(noise), smoking=VALUES(smoking), guests=VALUES(guests), social=VALUES(social), cooking=VALUES(cooking)", (data.user_id, preferences["sleep"], preferences["cleanliness"], preferences["noise"], preferences["smoking"], preferences["guests"], preferences["social"], preferences["cooking"]))
    execute_insert("INSERT INTO personality (user_id, introvert_extrovert, conflict_style, routine_level, sharing_level) VALUES (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE introvert_extrovert=VALUES(introvert_extrovert), conflict_style=VALUES(conflict_style), routine_level=VALUES(routine_level), sharing_level=VALUES(sharing_level)", (data.user_id, personality["introvert_extrovert"], personality["conflict_style"], personality["routine_level"], personality["sharing_level"]))
    save_traits(data.user_id, traits)
    save_scenario_responses(data.user_id, responses)
    
    # Precompute matches for this user against all other users
    try:
        precompute_matches_for_user(data.user_id)
    except Exception as exc:
        print(f"[Match Cache] Precomputation skipped: {exc}")
    try:
        run_clustering()
    except Exception as exc:
        print(f"[ML] Clustering skipped: {exc}")
    return {"message": "Profile saved successfully", "user_id": data.user_id, "roommate_type": roommate_type, "traits": traits}


@app.get("/user/{user_id}")
async def get_user(user_id: int):
    user, preferences, personality, traits = _get_user_data(user_id)
    return {**user, "preferences": preferences, "personality": personality, "traits": traits}


@app.put("/user/{user_id}")
async def update_user_profile(user_id: int, age: Optional[int] = None, profession: Optional[str] = None, gender: Optional[str] = None):
    user = execute_query("SELECT id FROM users WHERE id=%s", (user_id,), fetch_one=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    updates = []
    params = []
    if age is not None:
        updates.append("age=%s")
        params.append(age)
    if profession is not None:
        updates.append("profession=%s")
        params.append(profession)
    if gender is not None:
        updates.append("gender=%s")
        params.append(gender)
    
    if updates:
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id=%s"
        execute_update(query, tuple(params))
    
    return {"message": "Profile updated successfully"}


@app.get("/users")
async def list_users(search: str = Query(default="")):
    """Return all users without compatibility scores for the Explore Users section"""
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        return []
    if search:
        users = execute_query("SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE age IS NOT NULL AND name LIKE %s ORDER BY name", (f"%{search}%",), fetch_all=True)
    else:
        users = execute_query("SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE age IS NOT NULL ORDER BY name", fetch_all=True)
    return users or []


@app.get("/matches/{user_id}")
async def get_matches(user_id: int):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        return []
    # Try to get cached matches first
    cached_matches = get_top_matches_for_user(user_id, limit=5)
    
    # If no cached matches, precompute them now
    if not cached_matches:
        from backend.match_cache import precompute_matches_for_user
        precompute_matches_for_user(user_id)
        cached_matches = get_top_matches_for_user(user_id, limit=5)
    
    if cached_matches:
        # Return cached matches with user details
        matches = []
        for cached in cached_matches:
            other_user_id = cached["other_user_id"]
            other_user = execute_query(
                "SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE id=%s",
                (other_user_id,),
                fetch_one=True
            )
            if other_user:
                import json
                highlights = json.loads(cached["highlights_json"]) if cached["highlights_json"] else []
                warnings = json.loads(cached["warnings_json"]) if cached["warnings_json"] else []
                recommendation = generate_recommendation(cached["compatibility_score"], cached["risk_level"])
                
                matches.append({
                    "user_id": other_user["id"],
                    "name": other_user["name"],
                    "age": other_user["age"],
                    "profession": other_user["profession"],
                    "gender": other_user["gender"],
                    "roommate_type": other_user["roommate_type"],
                    "cluster_id": other_user["cluster_id"],
                    "match": round(cached["compatibility_score"]),
                    "risk": cached["risk_level"],
                    "breakdown": {
                        "lifestyle": cached["lifestyle_score"],
                        "personality": cached["personality_score"],
                        "traits": cached["trait_score"]
                    },
                    "total_score": cached["compatibility_score"],
                    "lifestyle_score": cached["lifestyle_score"],
                    "personality_score": cached["personality_score"],
                    "trait_score": cached["trait_score"],
                    "risk_level": cached["risk_level"],
                    "recommendation": recommendation,
                    "highlights": highlights,
                    "warnings": warnings,
                })
        return matches
    
    # Fallback: calculate in real-time if cache is empty (first time)
    user, user_preferences, user_personality, user_traits = _get_user_data(user_id)
    all_users = execute_query("SELECT u.id, u.name, u.age, u.profession, u.gender, u.roommate_type, u.cluster_id, p.sleep, p.cleanliness, p.noise, p.smoking, p.guests, p.social, p.cooking, pe.introvert_extrovert, pe.conflict_style, pe.routine_level, pe.sharing_level FROM users u JOIN preferences p ON u.id = p.user_id JOIN personality pe ON u.id = pe.user_id WHERE u.id != %s AND u.age IS NOT NULL", (user_id,), fetch_all=True) or []
    matches = []
    for other in all_users:
        other_preferences = {key: other[key] for key in ["sleep", "cleanliness", "noise", "smoking", "guests", "social", "cooking"]}
        other_personality = {key: other[key] for key in ["introvert_extrovert", "conflict_style", "routine_level", "sharing_level"]}
        other_traits = get_user_traits(other["id"])
        result = calculate_compatibility(user_preferences, other_preferences, user_personality, other_personality, user.get("cluster_id"), other.get("cluster_id"), user_traits, other_traits)
        risk_info = detect_risks(user_preferences, other_preferences, user_personality, other_personality, user_traits, other_traits)
        recommendation = generate_recommendation(result["total_score"], risk_info["risk_level"])
        _log_match("user", user_id, "user", other["id"], result["total_score"], risk_info["risk_level"], risk_info["conflicts"])
        
        # Cache the result
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
        
        matches.append({
            "user_id": other["id"], "name": other["name"], "age": other["age"], "profession": other["profession"], "gender": other["gender"], "roommate_type": other["roommate_type"], "cluster_id": other["cluster_id"],
            "match": round(result["total_score"]), "risk": risk_info["risk_level"],
            "breakdown": {"lifestyle": result["lifestyle_score"], "personality": result["personality_score"], "traits": result["trait_score"]},
            "total_score": result["total_score"], "lifestyle_score": result["lifestyle_score"], "personality_score": result["personality_score"], "trait_score": result["trait_score"],
            "risk_level": risk_info["risk_level"], "recommendation": recommendation, "highlights": result["highlights"][:3], "warnings": result["warnings"][:2],
        })
    matches.sort(key=lambda item: item["total_score"], reverse=True)
    return matches[:5]


@app.post("/compatibility")
async def check_compatibility(data: CompatibilityRequest):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if not is_db_connected():
        raise HTTPException(status_code=503, detail="Database not connected - temporarily disabled for cloud deployment")
    if data.user1_id == data.user2_id:
        raise HTTPException(status_code=400, detail="Cannot compare a user with themselves")
    
    # Check cache first
    cached = get_match_score(data.user1_id, data.user2_id)
    if cached:
        import json
        highlights = json.loads(cached["highlights_json"]) if cached["highlights_json"] else []
        warnings = json.loads(cached["warnings_json"]) if cached["warnings_json"] else []
        conflicts = json.loads(cached["conflicts_json"]) if cached["conflicts_json"] else []
        recommendation = generate_recommendation(cached["compatibility_score"], cached["risk_level"])
        
        user1, _, _, _ = _get_user_data(data.user1_id)
        user2, _, _, _ = _get_user_data(data.user2_id)
        
        return {
            "match": round(cached["compatibility_score"]),
            "breakdown": {
                "lifestyle": cached["lifestyle_score"],
                "personality": cached["personality_score"],
                "traits": cached["trait_score"]
            },
            "risk": cached["risk_level"],
            "total_score": cached["compatibility_score"],
            "lifestyle_score": cached["lifestyle_score"],
            "personality_score": cached["personality_score"],
            "trait_score": cached["trait_score"],
            "risk_level": cached["risk_level"],
            "conflicts": conflicts,
            "recommendation": recommendation,
            "highlights": highlights,
            "warnings": warnings,
            "user1_name": user1["name"],
            "user2_name": user2["name"],
            "user1_type": user1.get("roommate_type"),
            "user2_type": user2.get("roommate_type"),
            "cached": True
        }
    
    # Calculate if not in cache
    user1, preferences1, personality1, traits1 = _get_user_data(data.user1_id)
    user2, preferences2, personality2, traits2 = _get_user_data(data.user2_id)
    result = calculate_compatibility(preferences1, preferences2, personality1, personality2, user1.get("cluster_id"), user2.get("cluster_id"), traits1, traits2)
    risk_info = detect_risks(preferences1, preferences2, personality1, personality2, traits1, traits2)
    recommendation = generate_recommendation(result["total_score"], risk_info["risk_level"])
    _log_match("user", data.user1_id, "user", data.user2_id, result["total_score"], risk_info["risk_level"], risk_info["conflicts"])
    
    # Cache the result
    save_match_score(
        data.user1_id, data.user2_id,
        result["total_score"],
        result["lifestyle_score"],
        result["personality_score"],
        result["trait_score"],
        risk_info["risk_level"],
        result["highlights"][:3],
        result["warnings"][:2],
        risk_info["conflicts"]
    )
    
    return {"match": round(result["total_score"]), "breakdown": {"lifestyle": result["lifestyle_score"], "personality": result["personality_score"], "traits": result["trait_score"]}, "risk": risk_info["risk_level"], **result, "risk_level": risk_info["risk_level"], "conflicts": risk_info["conflicts"], "recommendation": recommendation, "user1_name": user1["name"], "user2_name": user2["name"], "user1_type": user1.get("roommate_type"), "user2_type": user2.get("roommate_type"), "cached": False}


@app.post("/room-post")
async def create_room_post(
    user_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    rent: float = Form(...),
    location: str = Form(...),
    gender_preference: str = Form("Any"),
    images: list[UploadFile] = File(default=[]),
):
    user = execute_query("SELECT id FROM users WHERE id=%s", (user_id,), fetch_one=True)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    image_urls = _save_uploaded_images(images)
    primary_image = image_urls[0] if image_urls else None
    post_id = execute_insert(
        "INSERT INTO room_posts (user_id, title, description, rent, location, gender_preference, lifestyle_preference, personality_preference, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
        (user_id, title, description, rent, location, gender_preference, json.dumps({}), json.dumps({}), primary_image),
    )
    for image_url in image_urls:
        execute_insert("INSERT INTO room_images (post_id, image_url) VALUES (%s, %s)", (post_id, image_url))
    row = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.id=%s", (post_id,), fetch_one=True)
    return {"message": "Room post created successfully", "post": _serialize_room_post(row)}


@app.get("/room-posts/{user_id}")
async def list_room_posts(user_id: int):
    user, user_preferences, user_personality, user_traits = _get_user_data(user_id)
    rows = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.user_id != %s ORDER BY rp.created_at DESC", (user_id,), fetch_all=True) or []
    posts = []
    for row in rows:
        post = _serialize_room_post(row)
        posts.append(_build_room_match_payload(user, user_preferences, user_personality, user_traits, post))
    posts.sort(key=lambda item: item["compatibility"]["total_score"], reverse=True)
    return posts


@app.get("/room-post/{post_id}")
async def get_room_post(post_id: int, user_id: Optional[int] = Query(default=None)):
    row = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.id=%s", (post_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=404, detail="Room post not found")
    post = _serialize_room_post(row)
    if user_id is None:
        return post
    user, user_preferences, user_personality, user_traits = _get_user_data(user_id)
    return _build_room_match_payload(user, user_preferences, user_personality, user_traits, post)


@app.get("/my-room-posts/{user_id}")
async def my_room_posts(user_id: int):
    rows = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.user_id=%s ORDER BY rp.created_at DESC", (user_id,), fetch_all=True) or []
    return [_serialize_room_post(row) for row in rows]


@app.post("/room-post/{post_id}/request")
async def request_roommate(post_id: int, data: RoommateRequestInput):
    post = execute_query("SELECT id, user_id FROM room_posts WHERE id=%s", (post_id,), fetch_one=True)
    if not post:
        raise HTTPException(status_code=404, detail="Room post not found")
    if post["user_id"] == data.requester_user_id:
        raise HTTPException(status_code=400, detail="You cannot request your own room post")
    
    # Check if conversation already exists
    existing_conv = execute_query(
        "SELECT id FROM conversations WHERE user1_id=%s AND user2_id=%s AND post_id=%s",
        (data.requester_user_id, post["user_id"], post_id),
        fetch_one=True
    )
    if existing_conv:
        conversation_id = existing_conv["id"]
    else:
        conversation_id = execute_insert(
            "INSERT INTO conversations (user1_id, user2_id, post_id) VALUES (%s, %s, %s)",
            (data.requester_user_id, post["user_id"], post_id)
        )
    
    # Add initial message if provided
    if data.message:
        execute_insert(
            "INSERT INTO messages (conversation_id, sender_id, message_content) VALUES (%s, %s, %s)",
            (conversation_id, data.requester_user_id, data.message)
        )
    
    return {"message": "Roommate request sent", "request_id": conversation_id}


@app.get("/conversations/{user_id}")
async def get_conversations(user_id: int):
    """Get all conversations for a user with unseen message count"""
    conversations = execute_query(
        """SELECT c.id, c.user1_id, c.user2_id, c.post_id, c.updated_at,
           u1.name AS user1_name, u2.name AS user2_name,
           rp.title AS post_title, rp.location AS post_location,
           (SELECT COUNT(*) FROM messages WHERE conversation_id=c.id AND sender_id!=%s AND read_status=FALSE) AS unseen_count
           FROM conversations c
           LEFT JOIN users u1 ON c.user1_id = u1.id
           LEFT JOIN users u2 ON c.user2_id = u2.id
           LEFT JOIN room_posts rp ON c.post_id = rp.id
           WHERE c.user1_id=%s OR c.user2_id=%s
           ORDER BY c.updated_at DESC""",
        (user_id, user_id, user_id),
        fetch_all=True
    ) or []
    return conversations


@app.get("/messages/{conversation_id}")
async def get_messages(conversation_id: int, user_id: Optional[int] = Query(default=None)):
    """Get all messages in a conversation"""
    messages = execute_query(
        """SELECT m.id, m.sender_id, m.message_content, m.read_status, m.created_at,
           u.name AS sender_name
           FROM messages m
           JOIN users u ON m.sender_id = u.id
           WHERE m.conversation_id=%s
           ORDER BY m.created_at ASC""",
        (conversation_id,),
        fetch_all=True
    ) or []
    
    # Mark messages as read if user_id is provided
    if user_id:
        execute_update(
            "UPDATE messages SET read_status=TRUE WHERE conversation_id=%s AND sender_id!=%s AND read_status=FALSE",
            (conversation_id, user_id)
        )
    
    return messages


@app.post("/messages")
async def send_message(conversation_id: int = Form(...), sender_id: int = Form(...), message_content: str = Form(...)):
    """Send a message in a conversation"""
    # Verify conversation exists and user is part of it
    conv = execute_query(
        "SELECT id FROM conversations WHERE id=%s AND (user1_id=%s OR user2_id=%s)",
        (conversation_id, sender_id, sender_id),
        fetch_one=True
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    message_id = execute_insert(
        "INSERT INTO messages (conversation_id, sender_id, message_content) VALUES (%s, %s, %s)",
        (conversation_id, sender_id, message_content)
    )
    
    # Update conversation timestamp
    execute_update("UPDATE conversations SET updated_at=CURRENT_TIMESTAMP WHERE id=%s", (conversation_id,))
    
    return {"message": "Message sent successfully", "message_id": message_id}


@app.get("/unseen-count/{user_id}")
async def get_unseen_count(user_id: int):
    """Get total unseen message count for a user"""
    result = execute_query(
        """SELECT COUNT(*) as count
           FROM messages m
           JOIN conversations c ON m.conversation_id = c.id
           WHERE (c.user1_id=%s OR c.user2_id=%s) AND m.sender_id!=%s AND m.read_status=FALSE""",
        (user_id, user_id, user_id),
        fetch_one=True
    )
    return {"unseen_count": result["count"] if result else 0}


@app.get("/conversation/{conversation_id}")
async def get_conversation_by_id(conversation_id: int):
    """Get a single conversation by ID"""
    conversation = execute_query(
        """SELECT c.id, c.user1_id, c.user2_id, c.post_id, c.created_at, c.updated_at,
           u1.name AS user1_name, u2.name AS user2_name,
           rp.title AS post_title, rp.location AS post_location
           FROM conversations c
           LEFT JOIN users u1 ON c.user1_id = u1.id
           LEFT JOIN users u2 ON c.user2_id = u2.id
           LEFT JOIN room_posts rp ON c.post_id = rp.id
           WHERE c.id=%s""",
        (conversation_id,),
        fetch_one=True
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@app.put("/room-post/{post_id}")
async def update_room_post(
    post_id: int,
    user_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(...),
    rent: float = Form(...),
    location: str = Form(...),
    gender_preference: str = Form("Any"),
    images: list[UploadFile] = File(default=[]),
):
    post = execute_query("SELECT id, user_id FROM room_posts WHERE id=%s", (post_id,), fetch_one=True)
    if not post:
        raise HTTPException(status_code=404, detail="Room post not found")
    if post["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only edit your own posts")
    
    image_urls = _save_uploaded_images(images) if images else None
    primary_image = image_urls[0] if image_urls else None
    
    execute_update(
        "UPDATE room_posts SET title=%s, description=%s, rent=%s, location=%s, gender_preference=%s, image_url=COALESCE(%s, image_url) WHERE id=%s",
        (title, description, rent, location, gender_preference, primary_image, post_id)
    )
    
    if image_urls:
        execute_update("DELETE FROM room_images WHERE post_id=%s", (post_id,))
        for image_url in image_urls:
            execute_insert("INSERT INTO room_images (post_id, image_url) VALUES (%s, %s)", (post_id, image_url))
    
    row = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.id=%s", (post_id,), fetch_one=True)
    return {"message": "Room post updated successfully", "post": _serialize_room_post(row)}


@app.delete("/room-post/{post_id}")
async def delete_room_post(post_id: int, user_id: int = Query(...)):
    post = execute_query("SELECT id, user_id FROM room_posts WHERE id=%s", (post_id,), fetch_one=True)
    if not post:
        raise HTTPException(status_code=404, detail="Room post not found")
    if post["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own posts")
    
    execute_update("DELETE FROM room_images WHERE post_id=%s", (post_id,))
    execute_update("DELETE FROM roommate_requests WHERE post_id=%s", (post_id,))
    execute_update("DELETE FROM room_posts WHERE id=%s", (post_id,))
    
    return {"message": "Room post deleted successfully"}


@app.get("/admin/dashboard")
async def admin_dashboard(admin=Depends(_require_admin)):
    return _analytics_snapshot()


@app.get("/admin/users")
async def admin_list_users(search: str = Query(default=""), admin=Depends(_require_admin)):
    return execute_query("SELECT id, name, age, profession, gender, roommate_type, cluster_id, created_at FROM users WHERE name LIKE %s ORDER BY created_at DESC", (f"%{search}%",), fetch_all=True) or []


@app.get("/admin/users/{user_id}")
async def admin_user_detail(user_id: int, admin=Depends(_require_admin)):
    user, preferences, personality, traits = _get_user_data(user_id)
    responses = execute_query("SELECT s.slug, s.title, sr.selected_option FROM scenario_responses sr JOIN scenarios s ON s.id = sr.scenario_id WHERE sr.user_id=%s ORDER BY s.id", (user_id,), fetch_all=True) or []
    return {**user, "preferences": preferences, "personality": personality, "traits": traits, "responses": responses}


@app.delete("/admin/users/{user_id}")
async def admin_delete_user(user_id: int, admin=Depends(_require_admin)):
    deleted = execute_update("DELETE FROM users WHERE id=%s", (user_id,))
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


@app.get("/admin/weights")
async def admin_get_weights(admin=Depends(_require_admin)):
    return get_runtime_weight_config()


@app.put("/admin/weights")
async def admin_update_weights(data: WeightsUpdateInput, admin=Depends(_require_admin)):
    from backend.match_cache import recompute_all_matches
    for feature, value in data.model_dump().items():
        execute_insert("INSERT INTO weights (feature, value) VALUES (%s, %s) ON DUPLICATE KEY UPDATE value=VALUES(value)", (feature, value))
    
    # Recompute all matches when weights are updated
    try:
        result = recompute_all_matches()
        return {"message": "Weights updated successfully", "weights": get_runtime_weight_config(), "recomputed": result}
    except Exception as exc:
        print(f"[Match Cache] Full recomputation skipped: {exc}")
        return {"message": "Weights updated successfully", "weights": get_runtime_weight_config()}


@app.get("/admin/scenarios")
async def admin_get_scenarios(admin=Depends(_require_admin)):
    return get_all_scenarios(include_db_ids=True)


@app.post("/admin/scenarios")
async def admin_create_scenario(data: ScenarioCreateInput, admin=Depends(_require_admin)):
    return create_scenario(data.model_dump())


@app.put("/admin/scenarios/{scenario_id}")
async def admin_update_scenario(scenario_id: int, data: ScenarioCreateInput, admin=Depends(_require_admin)):
    existing = get_scenario_by_id(scenario_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return update_scenario(scenario_id, data.model_dump())


@app.get("/admin/analytics")
async def admin_analytics(admin=Depends(_require_admin)):
    return _analytics_snapshot()["analytics"]


@app.post("/recluster")
async def recluster():
    try:
        result = run_clustering()
        if result is None:
            return {"message": "Not enough users for clustering (need at least 3)"}
        return {"message": "Clustering complete", **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Clustering failed: {exc}")


@app.post("/update-scenario-emojis")
async def update_scenario_emojis():
    """Update scenario icons and option emojis to use actual emoji characters"""
    emoji_updates = {
        # Scenario icons
        "PLATE": "🍽️",
        "MUSIC": "🎵",
        "DOOR": "🚪",
        "FOOD": "🍕",
        "ALARM": "⏰",
        # Option emojis
        "CALM": "😌",
        "CLEAN": "🧹",
        "TALK": "💬",
        "UPSET": "😤",
        "PARTY": "🎉",
        "HEADPHONES": "🎧",
        "QUIET": "🤫",
        "STOP": "🛑",
        "CHEER": "🥳",
        "WAVE": "👋",
        "PHONE": "📱",
        "ANGRY": "😠",
        "SMILE": "😊",
        "SHRUG": "🤷",
        "LIST": "📋",
        "LABEL": "🏷️",
        "SUN": "🌅",
        "SLEEP": "😴",
        "ALERT": "⚠️",
    }
    
    try:
        # Update scenario icons
        for old_emoji, new_emoji in emoji_updates.items():
            execute_update("UPDATE scenarios SET icon=%s WHERE icon=%s", (new_emoji, old_emoji))
        
        # Update option emojis
        for old_emoji, new_emoji in emoji_updates.items():
            execute_update("UPDATE scenario_options SET emoji=%s WHERE emoji=%s", (new_emoji, old_emoji))
        
        return {"message": "Scenario emojis updated successfully"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to update emojis: {exc}")
