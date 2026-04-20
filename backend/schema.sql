
-- ============================================
-- RoomSync AI - Extended Database Schema
-- ============================================

CREATE DATABASE IF NOT EXISTS roomsync_ai;
USE roomsync_ai;

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
);

CREATE TABLE IF NOT EXISTS preferences (
    user_id INT PRIMARY KEY,
    sleep INT NOT NULL CHECK (sleep BETWEEN 0 AND 2),
    cleanliness INT NOT NULL CHECK (cleanliness BETWEEN 1 AND 5),
    noise INT NOT NULL CHECK (noise BETWEEN 1 AND 5),
    smoking INT NOT NULL CHECK (smoking BETWEEN 0 AND 2),
    guests INT NOT NULL CHECK (guests BETWEEN 0 AND 3),
    social INT NOT NULL CHECK (social BETWEEN 1 AND 5),
    cooking INT NOT NULL CHECK (cooking BETWEEN 0 AND 3),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS personality (
    user_id INT PRIMARY KEY,
    introvert_extrovert INT NOT NULL CHECK (introvert_extrovert BETWEEN 1 AND 5),
    conflict_style INT NOT NULL CHECK (conflict_style BETWEEN 0 AND 2),
    routine_level INT NOT NULL CHECK (routine_level BETWEEN 1 AND 5),
    sharing_level INT NOT NULL CHECK (sharing_level BETWEEN 1 AND 5),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_traits (
    user_id INT PRIMARY KEY,
    cleanliness_tolerance INT NOT NULL DEFAULT 3 CHECK (cleanliness_tolerance BETWEEN 1 AND 5),
    noise_tolerance INT NOT NULL DEFAULT 3 CHECK (noise_tolerance BETWEEN 1 AND 5),
    social_tolerance INT NOT NULL DEFAULT 3 CHECK (social_tolerance BETWEEN 1 AND 5),
    conflict_style INT NOT NULL DEFAULT 3 CHECK (conflict_style BETWEEN 1 AND 5),
    flexibility INT NOT NULL DEFAULT 3 CHECK (flexibility BETWEEN 1 AND 5),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS admins (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS weights (
    feature VARCHAR(50) PRIMARY KEY,
    value DECIMAL(10,2) NOT NULL DEFAULT 1.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

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
);

CREATE TABLE IF NOT EXISTS scenario_options (
    id INT AUTO_INCREMENT PRIMARY KEY,
    scenario_id INT NOT NULL,
    option_order INT NOT NULL DEFAULT 0,
    option_text VARCHAR(255) NOT NULL,
    emoji VARCHAR(20),
    trait_mapping_json JSON NOT NULL,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS scenario_responses (
    user_id INT NOT NULL,
    scenario_id INT NOT NULL,
    selected_option INT NOT NULL,
    PRIMARY KEY (user_id, scenario_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (scenario_id) REFERENCES scenarios(id) ON DELETE CASCADE
);

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
);

CREATE TABLE IF NOT EXISTS room_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    post_id INT NOT NULL,
    image_url TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES room_posts(id) ON DELETE CASCADE
);

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
);

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
);

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
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user1 (user1_id),
    INDEX idx_user2 (user2_id),
    INDEX idx_score (compatibility_score DESC)
);
