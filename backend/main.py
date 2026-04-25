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
import psycopg2
from psycopg2.extras import RealDictCursor

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from classifier import classify_user_type
from db import execute_insert, execute_query, execute_update, ensure_schema, get_match_score, get_top_matches_for_user, save_match_score
from logic import calculate_compatibility, generate_recommendation, get_runtime_weight_config
from match_cache import precompute_matches_for_user
from ml import run_clustering
from models import AdminLogin, CompatibilityRequest, RoommateRequestInput, ScenarioCreateInput, ScenarioProfileInput, UserLogin, UserProfileInput, UserSignup, WeightsUpdateInput
from risk import detect_risks
from scenarios import create_scenario, get_all_scenarios, get_scenario_by_id, seed_default_scenarios, update_scenario
from traits import compute_traits, derive_personality, derive_preferences, get_user_traits, save_scenario_responses, save_traits

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
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.on_event("startup")
async def startup_event():
    try:
        # Skip ensure_schema - use /setup-db endpoint for PostgreSQL
        seed_default_scenarios()
        print("[Startup] Default scenarios seeded successfully")
    except Exception as exc:
        print(f"[Startup] Error seeding scenarios: {exc}")


@app.get("/")
async def serve_frontend():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "RoomSync AI API is running. Frontend not found."}


@app.post("/init-db")
async def init_db():
    ensure_schema()
    seed_default_scenarios()
    return {"message": "Database schema and seed data are ready."}


@app.post("/cleanup-duplicate-posts")
async def cleanup_duplicate_posts():
    """Delete duplicate room posts (keep only the oldest one per user/title)"""
    try:
        # First, delete duplicate room_images
        execute_query(
            """
            DELETE FROM room_images
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM room_images
                GROUP BY post_id, image_url
            )
            """
        )
        # Then delete duplicate posts by user_id and title (most common duplicates)
        duplicates = execute_query(
            """
            DELETE FROM room_posts
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM room_posts
                GROUP BY user_id, title
            )
            RETURNING id
            """,
            fetch_all=True
        ) or []
        deleted_count = len(duplicates)
        return {"message": f"Deleted {deleted_count} duplicate room posts", "deleted_ids": [d["id"] for d in duplicates]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cleanup duplicates: {str(e)}")


@app.get("/debug-uploads")
async def debug_uploads():
    """Debug endpoint to check uploads directory"""
    try:
        if not os.path.exists(UPLOADS_DIR):
            return {"exists": False, "path": UPLOADS_DIR, "files": []}
        files = os.listdir(UPLOADS_DIR)
        return {"exists": True, "path": UPLOADS_DIR, "file_count": len(files), "files": files[:20]}
    except Exception as e:
        return {"error": str(e)}


@app.get("/debug-posts")
async def debug_posts():
    """Debug endpoint to check room posts in database"""
    try:
        posts = execute_query("SELECT id, user_id, title, location, rent, image_url FROM room_posts ORDER BY id", fetch_all=True) or []
        images = execute_query("SELECT id, post_id, image_url FROM room_images ORDER BY id", fetch_all=True) or []
        return {
            "total_posts": len(posts),
            "total_images": len(images),
            "posts": posts,
            "images": images
        }
    except Exception as e:
        return {"error": str(e)}


@app.post("/cleanup-incomplete-profiles")
async def cleanup_incomplete_profiles():
    """Delete users who haven't completed onboarding (no preferences/personality data)"""
    try:
        # Get users without preferences or personality data
        incomplete_users = execute_query(
            """
            SELECT u.id, u.name
            FROM users u
            LEFT JOIN preferences p ON u.id = p.user_id
            LEFT JOIN personality per ON u.id = per.user_id
            WHERE p.user_id IS NULL OR per.user_id IS NULL
            """,
            fetch_all=True
        ) or []

        deleted_count = 0
        for user in incomplete_users:
            # Delete user (cascades to related tables)
            execute_update("DELETE FROM users WHERE id=%s", (user["id"],))
            deleted_count += 1

        return {"message": f"Deleted {deleted_count} incomplete profiles", "deleted_count": deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


@app.get("/setup-db")
async def setup_db():
    """Setup PostgreSQL database schema for cloud deployment"""
    # Get PostgreSQL connection string from environment (Render provides DATABASE_URL)
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise HTTPException(status_code=500, detail="DATABASE_URL environment variable not set")

    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Execute PostgreSQL schema
        cursor.execute("""
            -- ==============================
            -- RoomSync AI PostgreSQL Schema
            -- ==============================

            -- USERS
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                age INTEGER,
                profession VARCHAR(100),
                gender VARCHAR(20),
                password_hash VARCHAR(255) NOT NULL,
                roommate_type VARCHAR(100) DEFAULT 'Balanced Roommate',
                cluster_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- ADMINS
            CREATE TABLE IF NOT EXISTS admins (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- PREFERENCES
            CREATE TABLE IF NOT EXISTS preferences (
                user_id INTEGER PRIMARY KEY,
                sleep INTEGER CHECK (sleep BETWEEN 0 AND 2),
                cleanliness INTEGER CHECK (cleanliness BETWEEN 1 AND 5),
                noise INTEGER CHECK (noise BETWEEN 1 AND 5),
                smoking INTEGER CHECK (smoking BETWEEN 0 AND 2),
                guests INTEGER CHECK (guests BETWEEN 0 AND 3),
                social INTEGER CHECK (social BETWEEN 1 AND 5),
                cooking INTEGER CHECK (cooking BETWEEN 0 AND 3),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- PERSONALITY
            CREATE TABLE IF NOT EXISTS personality (
                user_id INTEGER PRIMARY KEY,
                introvert_extrovert INTEGER CHECK (introvert_extrovert BETWEEN 1 AND 5),
                conflict_style INTEGER CHECK (conflict_style BETWEEN 0 AND 2),
                routine_level INTEGER CHECK (routine_level BETWEEN 1 AND 5),
                sharing_level INTEGER CHECK (sharing_level BETWEEN 1 AND 5),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- USER TRAITS
            CREATE TABLE IF NOT EXISTS user_traits (
                user_id INTEGER PRIMARY KEY,
                cleanliness_tolerance INTEGER DEFAULT 3,
                noise_tolerance INTEGER DEFAULT 3,
                social_tolerance INTEGER DEFAULT 3,
                conflict_style INTEGER DEFAULT 3,
                flexibility INTEGER DEFAULT 3,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- WEIGHTS
            CREATE TABLE IF NOT EXISTS weights (
                feature VARCHAR(50) PRIMARY KEY,
                value NUMERIC(10,2) DEFAULT 1.00,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- SCENARIOS
            CREATE TABLE IF NOT EXISTS scenarios (
                id SERIAL PRIMARY KEY,
                slug VARCHAR(100) UNIQUE NOT NULL,
                title VARCHAR(150) NOT NULL,
                question TEXT NOT NULL,
                description TEXT,
                icon VARCHAR(20),
                category VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- SCENARIO OPTIONS
            CREATE TABLE IF NOT EXISTS scenario_options (
                id SERIAL PRIMARY KEY,
                scenario_id INTEGER,
                option_order INTEGER DEFAULT 0,
                option_text VARCHAR(255),
                emoji VARCHAR(20),
                trait_mapping_json JSONB,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
            );

            -- SCENARIO RESPONSES
            CREATE TABLE IF NOT EXISTS scenario_responses (
                user_id INTEGER,
                scenario_id INTEGER,
                selected_option INTEGER,
                PRIMARY KEY (user_id, scenario_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
            );

            -- ROOM POSTS
            CREATE TABLE IF NOT EXISTS room_posts (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                title VARCHAR(150),
                description TEXT,
                rent NUMERIC(10,2),
                location VARCHAR(255),
                gender_preference VARCHAR(50),
                lifestyle_preference JSONB DEFAULT '{}',
                personality_preference JSONB DEFAULT '{}',
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT unique_user_post UNIQUE (user_id, title, location, rent),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- ROOM IMAGES
            CREATE TABLE IF NOT EXISTS room_images (
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                image_url TEXT,
                FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE
            );

            -- ROOMMATE REQUESTS
            CREATE TABLE IF NOT EXISTS roommate_requests (
                id SERIAL PRIMARY KEY,
                post_id INTEGER,
                requester_user_id INTEGER,
                owner_user_id INTEGER,
                message VARCHAR(255),
                status VARCHAR(30) DEFAULT 'PENDING',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE,
                FOREIGN KEY (requester_user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            -- MATCH LOGS
            CREATE TABLE IF NOT EXISTS match_logs (
                id SERIAL PRIMARY KEY,
                source_type VARCHAR(30),
                source_id INTEGER,
                target_type VARCHAR(30),
                target_id INTEGER,
                compatibility_score NUMERIC(5,2),
                risk_level VARCHAR(10),
                conflict_types_json JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- MATCH SCORES
            CREATE TABLE IF NOT EXISTS match_scores (
                user1_id INTEGER,
                user2_id INTEGER,
                compatibility_score NUMERIC(5,2),
                lifestyle_score NUMERIC(5,2),
                personality_score NUMERIC(5,2),
                trait_score NUMERIC(5,2),
                risk_level VARCHAR(10),
                highlights_json JSONB,
                warnings_json JSONB,
                conflicts_json JSONB,
                calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user1_id, user2_id)
            );

            CREATE INDEX IF NOT EXISTS idx_match_user1 ON match_scores(user1_id);
            CREATE INDEX IF NOT EXISTS idx_match_user2 ON match_scores(user2_id);

            -- CONVERSATIONS
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                user1_id INTEGER,
                user2_id INTEGER,
                post_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user1_id, user2_id, post_id),
                FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE
            );

            -- MESSAGES
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                conversation_id INTEGER,
                sender_id INTEGER,
                message_content TEXT,
                read_status BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
                FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id);
            CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender_id);
            CREATE INDEX IF NOT EXISTS idx_messages_created ON messages(created_at);
        """)

        conn.commit()

        # Seed default scenarios
        from scenarios import DEFAULT_SCENARIOS
        import json

        # Check if scenarios already exist
        cursor.execute("SELECT id FROM scenarios LIMIT 1")
        if cursor.fetchone():
            print("[Setup] Scenarios already exist, skipping seed")
        else:
            for scenario in DEFAULT_SCENARIOS:
                cursor.execute(
                    "INSERT INTO scenarios (slug, title, question, description, icon, category) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (scenario["slug"], scenario["title"], scenario["question"], scenario.get("description"), scenario.get("icon"), scenario.get("category"))
                )
                scenario_id = cursor.fetchone()[0]
                for index, option in enumerate(scenario["options"]):
                    cursor.execute(
                        "INSERT INTO scenario_options (scenario_id, option_order, option_text, emoji, trait_mapping_json) VALUES (%s, %s, %s, %s, %s)",
                        (scenario_id, index, option["text"], option.get("emoji"), json.dumps(option["traits"]))
                    )
            conn.commit()
            print(f"[Setup] Seeded {len(DEFAULT_SCENARIOS)} scenarios")

        # Seed admin user
        cursor.execute("SELECT id FROM admins WHERE email=%s", ("admin@roomsync.ai",))
        if not cursor.fetchone():
            admin_password_hash = bcrypt.hashpw("admin123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            cursor.execute(
                "INSERT INTO admins (email, password_hash) VALUES (%s, %s)",
                ("admin@roomsync.ai", admin_password_hash)
            )
            conn.commit()
            print("[Setup] Seeded admin user (admin@roomsync.ai / admin123)")
        else:
            print("[Setup] Admin user already exists, skipping seed")

        # Seed demo users
        demo_users = [
            {
                "name": "demo1",
                "password": "demo123",
                "age": 24,
                "profession": "Software Engineer",
                "gender": "Male",
                "preferences": {"sleep": 1, "cleanliness": 4, "noise": 3, "smoking": 0, "guests": 1, "social": 3, "cooking": 2},
                "personality": {"introvert_extrovert": 3, "conflict_style": 2, "routine_level": 4, "sharing_level": 3},
                "traits": {"cleanliness_tolerance": 4, "noise_tolerance": 3, "social_tolerance": 3, "conflict_style": 2, "flexibility": 3}
            },
            {
                "name": "demo2",
                "password": "demo123",
                "age": 22,
                "profession": "Student",
                "gender": "Female",
                "preferences": {"sleep": 2, "cleanliness": 5, "noise": 1, "smoking": 0, "guests": 0, "social": 2, "cooking": 1},
                "personality": {"introvert_extrovert": 2, "conflict_style": 1, "routine_level": 5, "sharing_level": 2},
                "traits": {"cleanliness_tolerance": 5, "noise_tolerance": 1, "social_tolerance": 2, "conflict_style": 1, "flexibility": 2}
            },
            {
                "name": "demo3",
                "password": "demo123",
                "age": 26,
                "profession": "Designer",
                "gender": "Non-binary",
                "preferences": {"sleep": 0, "cleanliness": 3, "noise": 5, "smoking": 1, "guests": 3, "social": 5, "cooking": 3},
                "personality": {"introvert_extrovert": 5, "conflict_style": 3, "routine_level": 2, "sharing_level": 5},
                "traits": {"cleanliness_tolerance": 3, "noise_tolerance": 5, "social_tolerance": 5, "conflict_style": 3, "flexibility": 5}
            }
        ]

        for demo in demo_users:
            cursor.execute("SELECT id FROM users WHERE name=%s", (demo["name"],))
            if not cursor.fetchone():
                password_hash = bcrypt.hashpw(demo["password"].encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                cursor.execute(
                    "INSERT INTO users (name, password_hash, age, profession, gender, roommate_type) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                    (demo["name"], password_hash, demo["age"], demo["profession"], demo["gender"], "Balanced Roommate")
                )
                user_id = cursor.fetchone()[0]
                
                # Insert preferences
                cursor.execute(
                    "INSERT INTO preferences (user_id, sleep, cleanliness, noise, smoking, guests, social, cooking) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (user_id, demo["preferences"]["sleep"], demo["preferences"]["cleanliness"], demo["preferences"]["noise"],
                     demo["preferences"]["smoking"], demo["preferences"]["guests"], demo["preferences"]["social"], demo["preferences"]["cooking"])
                )
                
                # Insert personality
                cursor.execute(
                    "INSERT INTO personality (user_id, introvert_extrovert, conflict_style, routine_level, sharing_level) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, demo["personality"]["introvert_extrovert"], demo["personality"]["conflict_style"],
                     demo["personality"]["routine_level"], demo["personality"]["sharing_level"])
                )
                
                # Insert traits
                cursor.execute(
                    "INSERT INTO user_traits (user_id, cleanliness_tolerance, noise_tolerance, social_tolerance, conflict_style, flexibility) VALUES (%s, %s, %s, %s, %s, %s)",
                    (user_id, demo["traits"]["cleanliness_tolerance"], demo["traits"]["noise_tolerance"],
                     demo["traits"]["social_tolerance"], demo["traits"]["conflict_style"], demo["traits"]["flexibility"])
                )
                
                conn.commit()
                print(f"[Setup] Seeded demo user: {demo['name']}")
            else:
                print(f"[Setup] Demo user {demo['name']} already exists, skipping seed")

        cursor.close()
        conn.close()

        return {"status": "done", "message": "PostgreSQL database schema created and scenarios seeded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database setup failed: {str(e)}")


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
    # Ensure traits is always a dict, even if None (use default values)
    if traits is None:
        traits = {"cleanliness_tolerance": 3, "noise_tolerance": 3, "social_tolerance": 3, "conflict_style": 3, "flexibility": 3}
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
    print(f"[Image Upload] Processing {len(files) if files else 0} files")
    for upload in files:
        if not upload or not upload.filename:
            print(f"[Image Upload] Skipping invalid file")
            continue
        extension = os.path.splitext(upload.filename)[1].lower()
        if extension not in {".jpg", ".jpeg", ".png", ".webp", ".gif"}:
            print(f"[Image Upload] Skipping invalid extension: {extension}")
            continue
        filename = f"{uuid.uuid4().hex}{extension}"
        destination = os.path.join(UPLOADS_DIR, filename)
        print(f"[Image Upload] Saving {upload.filename} to {destination}")
        with open(destination, "wb") as buffer:
            shutil.copyfileobj(upload.file, buffer)
        image_urls.append(f"/uploads/{filename}")
        print(f"[Image Upload] Saved image URL: /uploads/{filename}")
    print(f"[Image Upload] Total saved: {len(image_urls)} images")
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
    existing = execute_query("SELECT id FROM users WHERE name=%s", (data.name,), fetch_one=True)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    password_hash = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user_id = execute_insert("INSERT INTO users (name, password_hash) VALUES (%s, %s) RETURNING id", (data.name, password_hash))
    return {"message": "Account created successfully", "user_id": user_id, "name": data.name}


@app.post("/login")
async def login(data: UserLogin):
    user = execute_query("SELECT id, name, password_hash, age, roommate_type FROM users WHERE name=%s", (data.name,), fetch_one=True)
    if not user or not bcrypt.checkpw(data.password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"message": "Login successful", "user_id": user["id"], "name": user["name"], "has_profile": user["age"] is not None, "roommate_type": user.get("roommate_type"), "role": "user"}


@app.post("/admin/login")
async def admin_login(data: AdminLogin):
    admin = execute_query("SELECT id, email, password_hash FROM admins WHERE email=%s", (data.email,), fetch_one=True)
    if not admin or not bcrypt.checkpw(data.password.encode("utf-8"), admin["password_hash"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Invalid admin credentials")
    return {"message": "Admin login successful", "admin_id": admin["id"], "email": admin["email"], "role": "admin"}


@app.get("/scenarios")
async def list_scenarios():
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
    execute_insert("INSERT INTO preferences (user_id, sleep, cleanliness, noise, smoking, guests, social, cooking) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO UPDATE SET sleep=EXCLUDED.sleep, cleanliness=EXCLUDED.cleanliness, noise=EXCLUDED.noise, smoking=EXCLUDED.smoking, guests=EXCLUDED.guests, social=EXCLUDED.social, cooking=EXCLUDED.cooking", (data.user_id, preferences["sleep"], preferences["cleanliness"], preferences["noise"], preferences["smoking"], preferences["guests"], preferences["social"], preferences["cooking"]))
    execute_insert("INSERT INTO personality (user_id, introvert_extrovert, conflict_style, routine_level, sharing_level) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO UPDATE SET introvert_extrovert=EXCLUDED.introvert_extrovert, conflict_style=EXCLUDED.conflict_style, routine_level=EXCLUDED.routine_level, sharing_level=EXCLUDED.sharing_level", (data.user_id, personality["introvert_extrovert"], personality["conflict_style"], personality["routine_level"], personality["sharing_level"]))
    
    # Mark user as having completed profile
    execute_update("UPDATE users SET has_profile=TRUE WHERE id=%s", (data.user_id,))
    
    # Precompute matches with all other users
    from match_cache import precompute_matches_for_user
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
    execute_insert("INSERT INTO preferences (user_id, sleep, cleanliness, noise, smoking, guests, social, cooking) VALUES (%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO UPDATE SET sleep=EXCLUDED.sleep, cleanliness=EXCLUDED.cleanliness, noise=EXCLUDED.noise, smoking=EXCLUDED.smoking, guests=EXCLUDED.guests, social=EXCLUDED.social, cooking=EXCLUDED.cooking", (data.user_id, preferences["sleep"], preferences["cleanliness"], preferences["noise"], preferences["smoking"], preferences["guests"], preferences["social"], preferences["cooking"]))
    execute_insert("INSERT INTO personality (user_id, introvert_extrovert, conflict_style, routine_level, sharing_level) VALUES (%s,%s,%s,%s,%s) ON CONFLICT (user_id) DO UPDATE SET introvert_extrovert=EXCLUDED.introvert_extrovert, conflict_style=EXCLUDED.conflict_style, routine_level=EXCLUDED.routine_level, sharing_level=EXCLUDED.sharing_level", (data.user_id, personality["introvert_extrovert"], personality["conflict_style"], personality["routine_level"], personality["sharing_level"]))
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
    if search:
        users = execute_query("SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE age IS NOT NULL AND name LIKE %s ORDER BY name", (f"%{search}%",), fetch_all=True)
    else:
        users = execute_query("SELECT id, name, age, profession, gender, roommate_type, cluster_id FROM users WHERE age IS NOT NULL ORDER BY name", fetch_all=True)
    return users or []


@app.get("/matches/{user_id}")
async def get_matches(user_id: int):
    # Try to get cached matches first
    cached_matches = get_top_matches_for_user(user_id, limit=5)
    
    # If no cached matches, precompute them now
    if not cached_matches:
        from match_cache import precompute_matches_for_user
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
                try:
                    if isinstance(cached["highlights_json"], str):
                        highlights = json.loads(cached["highlights_json"])
                    else:
                        highlights = cached["highlights_json"] if cached["highlights_json"] else []
                except (json.JSONDecodeError, TypeError):
                    highlights = []
                
                try:
                    if isinstance(cached["warnings_json"], str):
                        warnings = json.loads(cached["warnings_json"])
                    else:
                        warnings = cached["warnings_json"] if cached["warnings_json"] else []
                except (json.JSONDecodeError, TypeError):
                    warnings = []
                
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
    try:
        if data.user1_id == data.user2_id:
            raise HTTPException(status_code=400, detail="Cannot compare a user with themselves")

        # Check cache first
        cached = get_match_score(data.user1_id, data.user2_id)
        if cached:
            import json
            try:
                # Handle both JSON strings and already-parsed data
                if isinstance(cached["highlights_json"], str):
                    highlights = json.loads(cached["highlights_json"])
                else:
                    highlights = cached["highlights_json"] if cached["highlights_json"] else []
            except (json.JSONDecodeError, TypeError):
                highlights = []
            
            try:
                if isinstance(cached["warnings_json"], str):
                    warnings = json.loads(cached["warnings_json"])
                else:
                    warnings = cached["warnings_json"] if cached["warnings_json"] else []
            except (json.JSONDecodeError, TypeError):
                warnings = []
            
            try:
                if isinstance(cached["conflicts_json"], str):
                    conflicts = json.loads(cached["conflicts_json"])
                else:
                    conflicts = cached["conflicts_json"] if cached["conflicts_json"] else []
            except (json.JSONDecodeError, TypeError):
                conflicts = []
            
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Compatibility Error] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Compatibility calculation failed: {str(e)}")


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
    try:
        user = execute_query("SELECT id FROM users WHERE id=%s", (user_id,), fetch_one=True)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        image_urls = _save_uploaded_images(images)
        primary_image = image_urls[0] if image_urls else None
        post_id = execute_insert(
            "INSERT INTO room_posts (user_id, title, description, rent, location, gender_preference, lifestyle_preference, personality_preference, image_url) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (user_id, title, description, rent, location, gender_preference, json.dumps({}), json.dumps({}), primary_image),
        )
        for image_url in image_urls:
            execute_insert("INSERT INTO room_images (post_id, image_url) VALUES (%s, %s) RETURNING id", (post_id, image_url))
        row = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.id=%s", (post_id,), fetch_one=True)
        return {"message": "Room post created successfully", "post": _serialize_room_post(row)}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Create Room Post Error] {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create room post: {str(e)}")


@app.get("/room-posts/{user_id}")
async def list_room_posts(user_id: int):
    # Simple query: get all posts except this user's, then fetch user info separately
    posts = execute_query("SELECT * FROM room_posts WHERE user_id != %s ORDER BY created_at DESC", (user_id,), fetch_all=True) or []
    result = []
    for post in posts:
        user = execute_query("SELECT name, roommate_type FROM users WHERE id=%s", (post["user_id"],), fetch_one=True)
        if user:
            post["owner_name"] = user["name"]
            post["owner_roommate_type"] = user.get("roommate_type")
        serialized = _serialize_room_post(post)
        result.append(serialized)
    print(f"[Browse Rooms Debug] User {user_id}: returning {len(result)} posts")
    return result


@app.get("/room-post/{post_id}")
async def get_room_post(post_id: int, user_id: Optional[int] = Query(default=None)):
    row = execute_query("SELECT rp.*, u.name AS owner_name, u.roommate_type AS owner_roommate_type FROM room_posts rp JOIN users u ON u.id = rp.user_id WHERE rp.id=%s", (post_id,), fetch_one=True)
    if not row:
        raise HTTPException(status_code=404, detail="Room post not found")
    post = _serialize_room_post(row)
    print(f"[Room Post Debug] Post {post_id}: image_url={post.get('image_url')}, images={post.get('images')}")
    if user_id is None:
        return post
    try:
        user, user_preferences, user_personality, user_traits = _get_user_data(user_id)
        return _build_room_match_payload(user, user_preferences, user_personality, user_traits, post)
    except HTTPException:
        # If user hasn't completed profile, return post without compatibility
        return post


@app.get("/my-room-posts/{user_id}")
async def my_room_posts(user_id: int):
    # Simple query: get posts for this user, then fetch user info separately
    posts = execute_query("SELECT * FROM room_posts WHERE user_id=%s ORDER BY created_at DESC", (user_id,), fetch_all=True) or []
    result = []
    for post in posts:
        user = execute_query("SELECT name, roommate_type FROM users WHERE id=%s", (post["user_id"],), fetch_one=True)
        if user:
            post["owner_name"] = user["name"]
            post["owner_roommate_type"] = user.get("roommate_type")
        result.append(_serialize_room_post(post))
    print(f"[My Posts Debug] User {user_id}: returning {len(result)} posts")
    return result


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
            execute_insert("INSERT INTO room_images (post_id, image_url) VALUES (%s, %s) RETURNING id", (post_id, image_url))
    
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
    from match_cache import recompute_all_matches
    for feature, value in data.model_dump().items():
        execute_insert("INSERT INTO weights (feature, value) VALUES (%s, %s) ON CONFLICT (feature) DO UPDATE SET value=EXCLUDED.value", (feature, value))
    
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
