import mysql.connector

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
}

def init_database():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    # Créer la base de données
    cursor.execute("CREATE DATABASE IF NOT EXISTS avatar_generator")
    cursor.execute("USE avatar_generator")
    
    # Créer les tables
    tables = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_sessions (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            session_token VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS user_images (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            stored_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS face_features (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            image_id INT NOT NULL,
            gender VARCHAR(20),
            age_range VARCHAR(50),
            face_shape VARCHAR(50),
            skin_tone VARCHAR(50),
            has_smile BOOLEAN,
            has_glasses BOOLEAN,
            hair_color VARCHAR(50),
            hair_type VARCHAR(50),
            hair_length VARCHAR(50),
            hair_length_pixels INT,
            eyes_color VARCHAR(50),
            left_eye_x INT,
            left_eye_y INT,
            right_eye_x INT,
            right_eye_y INT,
            nose_size VARCHAR(50),
            mouth_size VARCHAR(50),
            extraction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            extraction_time_seconds FLOAT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (image_id) REFERENCES user_images(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS generated_avatars (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            features_id INT NOT NULL,
            style VARCHAR(50),
            style_name VARCHAR(50),
            quality VARCHAR(20),
            steps INT,
            custom_prompt TEXT,
            generated_filename VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            generation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            generation_time_seconds FLOAT,
            prompt_used TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (features_id) REFERENCES face_features(id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS favorite_avatars (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            avatar_id INT NOT NULL,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (avatar_id) REFERENCES generated_avatars(id) ON DELETE CASCADE
        )
        """
    ]
    
    for table in tables:
        cursor.execute(table)
    
    print("✅ Base de données initialisée avec succès!")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_database()