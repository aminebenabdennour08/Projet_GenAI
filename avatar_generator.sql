-- ============================================================
-- BASE DE DONNÉES AVATAR GENERATOR
-- ============================================================

CREATE DATABASE IF NOT EXISTS avatar_generator;
USE avatar_generator;

-- ============================================================
-- TABLE DES UTILISATEURS
-- ============================================================
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL
);

-- ============================================================
-- TABLE DES SESSIONS
-- ============================================================
CREATE TABLE user_sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    session_token VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_token (session_token),
    INDEX idx_expires_at (expires_at)
);

-- ============================================================
-- TABLE DES IMAGES UPLOADÉES
-- ============================================================
CREATE TABLE user_images (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    mime_type VARCHAR(50),
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_upload_date (upload_date)
);

-- ============================================================
-- TABLE DES CARACTÉRISTIQUES FACIALES
-- ============================================================
CREATE TABLE face_features (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    image_id INT NOT NULL,
    
    -- Paramètres utilisateur
    gender VARCHAR(20),
    age_range VARCHAR(50),
    
    -- Traits du visage
    face_shape VARCHAR(50),
    skin_tone VARCHAR(50),
    has_smile BOOLEAN DEFAULT FALSE,
    has_glasses BOOLEAN DEFAULT FALSE,
    
    -- Cheveux
    hair_color VARCHAR(50),
    hair_type VARCHAR(50),
    hair_length VARCHAR(50),
    hair_length_pixels INT,
    
    -- Yeux
    eyes_color VARCHAR(50),
    left_eye_x INT,
    left_eye_y INT,
    left_eye_width INT,
    left_eye_height INT,
    right_eye_x INT,
    right_eye_y INT,
    right_eye_width INT,
    right_eye_height INT,
    
    -- Nez
    nose_size VARCHAR(50),
    nose_x INT,
    nose_y INT,
    
    -- Bouche
    mouth_size VARCHAR(50),
    mouth_x INT,
    mouth_y INT,
    
    -- Métadonnées
    extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    extraction_time_seconds FLOAT,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (image_id) REFERENCES user_images(id) ON DELETE CASCADE,
    INDEX idx_user_features (user_id),
    INDEX idx_extraction_date (extraction_date)
);

-- ============================================================
-- TABLE DES AVATARS GÉNÉRÉS
-- ============================================================
CREATE TABLE generated_avatars (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    features_id INT NOT NULL,
    
    -- Paramètres de génération
    style VARCHAR(50),
    style_name VARCHAR(50),
    quality VARCHAR(20),
    steps INT,
    custom_prompt TEXT,
    age_input VARCHAR(50),
    clothing_description TEXT,
    
    -- Résultat
    generated_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INT,
    
    -- Métadonnées
    generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    generation_time_seconds FLOAT,
    prompt_used TEXT,
    
    -- Statut
    is_public BOOLEAN DEFAULT FALSE,
    download_count INT DEFAULT 0,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (features_id) REFERENCES face_features(id) ON DELETE CASCADE,
    INDEX idx_user_avatars (user_id),
    INDEX idx_generation_date (generation_date),
    INDEX idx_style (style)
);

-- ============================================================
-- TABLE DES FAVORIS
-- ============================================================
CREATE TABLE favorite_avatars (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    avatar_id INT NOT NULL,
    notes TEXT,
    added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (avatar_id) REFERENCES generated_avatars(id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, avatar_id),
    INDEX idx_user_favorites (user_id)
);

-- ============================================================
-- TRIGGERS
-- ============================================================

-- Trigger pour mettre à jour last_login
DELIMITER //
CREATE TRIGGER update_last_login
AFTER INSERT ON user_sessions
FOR EACH ROW
BEGIN
    UPDATE users SET last_login = NOW() WHERE id = NEW.user_id;
END//
DELIMITER ;

-- ============================================================
-- VUES UTILES
-- ============================================================

-- Vue des avatars avec détails
CREATE VIEW v_user_avatars AS
SELECT 
    a.id as avatar_id,
    a.user_id,
    u.username,
    a.style_name,
    a.quality,
    a.generation_date,
    a.generated_filename,
    a.download_count,
    f.hair_color,
    f.eyes_color,
    f.face_shape,
    f.gender
FROM generated_avatars a
JOIN users u ON a.user_id = u.id
JOIN face_features f ON a.features_id = f.id;

-- ============================================================
-- INDEX POUR OPTIMISATION
-- ============================================================
CREATE INDEX idx_features_eyes ON face_features(eyes_color);
CREATE INDEX idx_features_hair ON face_features(hair_color, hair_length);
CREATE INDEX idx_avatars_style_date ON generated_avatars(style, generation_date);