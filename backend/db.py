
"""
RoomSync AI - Database Connection, Schema, and Seed Helpers
"""

import os
import bcrypt
import mysql.connector
from mysql.connector import pooling

DB_CONFIG = {
    "host": os.getenv("ROOMSYNC_DB_HOST", "localhost"),
    "user": os.getenv("ROOMSYNC_DB_USER", "root"),
    "password": os.getenv("ROOMSYNC_DB_PASSWORD", ""),
    "database": os.getenv("ROOMSYNC_DB_NAME", "roomsync_ai"),
    "pool_name": "roomsync_pool",
    "pool_size": 5,
    "pool_reset_session": True,
}

DEFAULT_WEIGHT_VALUES = {
    "cleanliness": 1.25,
    "sleep": 1.1,
    "personality": 0.95,
    "trait": 1.15,
}


def get_pool():
    try:
        return pooling.MySQLConnectionPool(**DB_CONFIG)
    except mysql.connector.Error as exc:
        print(f"[DB] Error creating connection pool: {exc}")
        raise


# TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
# pool = get_pool()
pool = None


def get_connection():
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    if pool is None:
        return None
    return pool.get_connection()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    conn = get_connection()
    if conn is None:
        return None
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch_one:
            return cursor.fetchone()
        if fetch_all:
            return cursor.fetchall()
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def execute_insert(query, params=None):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    conn = get_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.lastrowid
    finally:
        cursor.close()
        conn.close()


def execute_update(query, params=None):
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    conn = get_connection()
    if conn is None:
        return None
    cursor = conn.cursor()
    try:
        cursor.execute(query, params or ())
        conn.commit()
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()


def is_db_connected():
    # TEMPORARILY DISABLED FOR CLOUD DEPLOYMENT
    return pool is not None


def execute_many(query, data_list):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data_list)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def ensure_schema():
    ddls = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            age INT,
            profession VARCHAR(100),
            gender VARCHAR(20),
            password_hash VARCHAR(255) NOT NULL,
            roommate_type VARCHAR(100) DEFAULT 'Balanced Roommate',
            cluster_id INT DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS preferences (
            user_id INT PRIMARY KEY,
            sleep INT NOT NULL,
            cleanliness INT NOT NULL,
            noise INT NOT NULL,
            smoking INT NOT NULL,
            guests INT NOT NULL,
            social INT NOT NULL,
            cooking INT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS personality (
            user_id INT PRIMARY KEY,
            introvert_extrovert INT NOT NULL,
            conflict_style INT NOT NULL,
            routine_level INT NOT NULL,
            sharing_level INT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_traits (
            user_id INT PRIMARY KEY,
            cleanliness_tolerance INT NOT NULL DEFAULT 3,
            noise_tolerance INT NOT NULL DEFAULT 3,
            social_tolerance INT NOT NULL DEFAULT 3,
            conflict_style INT NOT NULL DEFAULT 3,
            flexibility INT NOT NULL DEFAULT 3,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS admins (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS weights (
            feature VARCHAR(50) PRIMARY KEY,
            value DECIMAL(10,2) NOT NULL DEFAULT 1.00,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scenarios (
            id INT AUTO_INCREMENT PRIMARY KEY,
            slug VARCHAR(100) NOT NULL UNIQUE,
            title VARCHAR(150) NOT NULL,
            question TEXT NOT NULL,
            description TEXT,
            icon VARCHAR(20),
            category VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scenario_options (
            id INT AUTO_INCREMENT PRIMARY KEY,
            scenario_id INT NOT NULL,
            option_order INT NOT NULL DEFAULT 0,
            option_text VARCHAR(255) NOT NULL,
            emoji VARCHAR(20),
            trait_mapping_json JSON NOT NULL,
            FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scenario_responses (
            user_id INT NOT NULL,
            scenario_id INT NOT NULL,
            selected_option INT NOT NULL,
            PRIMARY KEY (user_id, scenario_id),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS room_posts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            title VARCHAR(150) NOT NULL,
            description TEXT,
            rent DECIMAL(10,2) NOT NULL,
            location VARCHAR(255) NOT NULL,
            gender_preference VARCHAR(50),
            lifestyle_preference JSON NOT NULL,
            personality_preference JSON,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS room_images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            post_id INT NOT NULL,
            image_url TEXT NOT NULL,
            FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS roommate_requests (
            id INT AUTO_INCREMENT PRIMARY KEY,
            post_id INT NOT NULL,
            requester_user_id INT NOT NULL,
            owner_user_id INT NOT NULL,
            message VARCHAR(255),
            status VARCHAR(30) NOT NULL DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE,
            FOREIGN KEY (requester_user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (owner_user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS match_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            source_type VARCHAR(30) NOT NULL,
            source_id INT NOT NULL,
            target_type VARCHAR(30) NOT NULL,
            target_id INT NOT NULL,
            compatibility_score DECIMAL(5,2) NOT NULL,
            risk_level VARCHAR(10) NOT NULL,
            conflict_types_json JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS match_scores (
            user1_id INT NOT NULL,
            user2_id INT NOT NULL,
            compatibility_score DECIMAL(5,2) NOT NULL,
            lifestyle_score DECIMAL(5,2) NOT NULL,
            personality_score DECIMAL(5,2) NOT NULL,
            trait_score DECIMAL(5,2) NOT NULL,
            risk_level VARCHAR(10) NOT NULL,
            highlights_json JSON,
            warnings_json JSON,
            conflicts_json JSON,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            PRIMARY KEY (user1_id, user2_id),
            INDEX idx_user1 (user1_id),
            INDEX idx_user2 (user2_id),
            INDEX idx_score (compatibility_score DESC)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user1_id INT NOT NULL,
            user2_id INT NOT NULL,
            post_id INT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE,
            UNIQUE KEY unique_conversation (user1_id, user2_id, post_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            conversation_id INT NOT NULL,
            sender_id INT NOT NULL,
            message_content TEXT NOT NULL,
            read_status BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_conversation (conversation_id),
            INDEX idx_sender (sender_id),
            INDEX idx_created (created_at)
        )
        """,
    ]

    for ddl in ddls:
        execute_update(ddl)

    seed_default_weights()
    seed_default_admin()


def seed_default_weights():
    existing = execute_query("SELECT feature, value FROM weights", fetch_all=True) or []
    existing_map = {row["feature"]: float(row["value"]) for row in existing}
    for feature, value in DEFAULT_WEIGHT_VALUES.items():
        if feature not in existing_map:
            execute_insert("INSERT INTO weights (feature, value) VALUES (%s, %s)", (feature, value))

    # If the system is still on the original flat 1.0 defaults, upgrade it once to
    # the recommended balance so compatibility scores do not feel artificially muted.
    if existing_map and all(abs(existing_map.get(feature, 1.0) - 1.0) < 0.001 for feature in DEFAULT_WEIGHT_VALUES):
        for feature, value in DEFAULT_WEIGHT_VALUES.items():
            execute_update("UPDATE weights SET value=%s WHERE feature=%s", (value, feature))


def seed_default_admin():
    admin_exists = execute_query("SELECT id FROM admins LIMIT 1", fetch_one=True)
    if admin_exists:
        return

    default_email = os.getenv("ROOMSYNC_ADMIN_EMAIL", "admin@roomsync.ai")
    default_password = os.getenv("ROOMSYNC_ADMIN_PASSWORD", "admin123")
    password_hash = bcrypt.hashpw(default_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    execute_insert("INSERT INTO admins (email, password_hash) VALUES (%s, %s)", (default_email, password_hash))


# Match Scores Cache Functions
def save_match_score(user1_id, user2_id, compatibility_score, lifestyle_score, personality_score, trait_score, risk_level, highlights=None, warnings=None, conflicts=None):
    """Save or update a compatibility score in the cache"""
    import json
    # Always store with smaller user_id first to ensure symmetry
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id
    
    query = """
    INSERT INTO match_scores (user1_id, user2_id, compatibility_score, lifestyle_score, personality_score, trait_score, risk_level, highlights_json, warnings_json, conflicts_json)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE
    compatibility_score = VALUES(compatibility_score),
    lifestyle_score = VALUES(lifestyle_score),
    personality_score = VALUES(personality_score),
    trait_score = VALUES(trait_score),
    risk_level = VALUES(risk_level),
    highlights_json = VALUES(highlights_json),
    warnings_json = VALUES(warnings_json),
    conflicts_json = VALUES(conflicts_json),
    calculated_at = CURRENT_TIMESTAMP
    """
    return execute_update(query, (user1_id, user2_id, compatibility_score, lifestyle_score, personality_score, trait_score, risk_level,
                                  json.dumps(highlights) if highlights else None,
                                  json.dumps(warnings) if warnings else None,
                                  json.dumps(conflicts) if conflicts else None))


def get_match_score(user1_id, user2_id):
    """Retrieve a cached compatibility score"""
    # Always query with smaller user_id first to ensure symmetry
    if user1_id > user2_id:
        user1_id, user2_id = user2_id, user1_id
    
    query = """
    SELECT user1_id, user2_id, compatibility_score, lifestyle_score, personality_score, trait_score, risk_level,
           highlights_json, warnings_json, conflicts_json, calculated_at
    FROM match_scores
    WHERE user1_id = %s AND user2_id = %s
    """
    return execute_query(query, (user1_id, user2_id), fetch_one=True)


def get_top_matches_for_user(user_id, limit=5):
    """Get top N matches for a user from cache"""
    query = """
    SELECT 
        CASE WHEN user1_id = %s THEN user2_id ELSE user1_id END as other_user_id,
        compatibility_score, lifestyle_score, personality_score, trait_score, risk_level,
        highlights_json, warnings_json, conflicts_json, calculated_at
    FROM match_scores
    WHERE user1_id = %s OR user2_id = %s
    ORDER BY compatibility_score DESC
    LIMIT %s
    """
    return execute_query(query, (user_id, user_id, user_id, limit), fetch_all=True)


def invalidate_user_matches(user_id):
    """Delete all cached matches for a user (when preferences are updated)"""
    query = "DELETE FROM match_scores WHERE user1_id = %s OR user2_id = %s"
    return execute_update(query, (user_id, user_id))
