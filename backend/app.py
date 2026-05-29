# ============================================================
# app.py - API Flask principale
# ============================================================

from flask import Flask, request, jsonify, send_file, send_from_directory, redirect
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import mysql.connector
import os
import sys
import json
import uuid
import time
import subprocess
from datetime import datetime, timedelta
from functools import wraps

# ============================================================
# CONFIGURATION DES CHEMINS
# ============================================================
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BACKEND_DIR)

EXTRACTOR_SCRIPT = os.path.join(BACKEND_DIR, 'face_features_extractor.py')
GENERATOR_SCRIPT = os.path.join(BACKEND_DIR, 'face_avatar_creator.py')

print(f"[INFO] BACKEND_DIR: {BACKEND_DIR}")
print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")

if not os.path.exists(EXTRACTOR_SCRIPT):
    print(f"[ERREUR] Extracteur non trouve: {EXTRACTOR_SCRIPT}")
    sys.exit(1)

sys.path.append(BACKEND_DIR)

try:
    from face_avatar_creator import AvatarGenerator, STYLES
    print("[OK] Module face_avatar_creator charge")
except ImportError as e:
    print(f"[ERREUR] Erreur d'import: {e}")
    AvatarGenerator = None
    STYLES = {}

# ============================================================
# APPLICATION FLASK
# ============================================================
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev_secret_key')
CORS(app, supports_credentials=True, origins=['http://localhost:5000'])
bcrypt = Bcrypt(app)

# Configuration des dossiers
UPLOAD_FOLDER = os.path.join(PROJECT_ROOT, 'uploads')
OUTPUT_FOLDER = os.path.join(PROJECT_ROOT, 'output')
AVATAR_FOLDER = os.path.join(PROJECT_ROOT, 'avatars')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, AVATAR_FOLDER]:
    os.makedirs(folder, exist_ok=True)
    print(f"[INFO] Dossier: {folder}")

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# ============================================================
# CONFIGURATION MYSQL
# ============================================================
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'avatar_generator',
    'autocommit': True
}

def get_db():
    try:
        return mysql.connector.connect(**db_config)
    except mysql.connector.Error as e:
        print(f"[ERREUR] MySQL: {e}")
        return None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ============================================================
# INSTANCE DU GENERATEUR
# ============================================================
generator = None

def get_generator():
    global generator
    if generator is None and AvatarGenerator is not None:
        try:
            generator = AvatarGenerator()
            print("[OK] Generateur d'avatar initialise")
        except Exception as e:
            print(f"[ERREUR] Init generateur: {e}")
    return generator

# ============================================================
# DECORATEUR D'AUTHENTIFICATION
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_token = request.cookies.get('session_token')
        
        if not session_token:
            return jsonify({'error': 'Non authentifie'}), 401
        
        conn = get_db()
        if not conn:
            return jsonify({'error': 'Erreur base de donnees'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.* FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = %s AND s.expires_at > NOW()
        """, (session_token,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if not user:
            return jsonify({'error': 'Session expiree'}), 401
        
        request.user = user
        return f(*args, **kwargs)
    return decorated_function

# ============================================================
# VERIFICATION AUTH PAGES
# ============================================================
def check_page_auth():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return False
    
    conn = get_db()
    if not conn:
        return False
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id FROM users u
        JOIN user_sessions s ON u.id = s.user_id
        WHERE s.session_token = %s AND s.expires_at > NOW()
    """, (session_token,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    return user is not None

# ============================================================
# ROUTES PAGES HTML
# ============================================================

@app.route('/')
def serve_root():
    return redirect('/login.html')

@app.route('/login.html')
def serve_login_page():
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend'), 'login.html')

@app.route('/register.html')
def serve_register_page():
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend'), 'register.html')

@app.route('/app')
def serve_app():
    if not check_page_auth():
        return redirect('/login.html')
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend'), 'index.html')

@app.route('/dashboard')
def serve_dashboard():
    if not check_page_auth():
        return redirect('/login.html')
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend'), 'dashboard.html')

@app.route('/history')
def serve_history():
    if not check_page_auth():
        return redirect('/login.html')
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend'), 'history.html')

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend', 'css'), path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory(os.path.join(PROJECT_ROOT, 'frontend', 'js'), path)

# ============================================================
# ROUTES AUTHENTIFICATION
# ============================================================

@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not all([username, email, password]):
        return jsonify({'error': 'Tous les champs sont requis'}), 400
    
    if len(password) < 6:
        return jsonify({'error': 'Mot de passe trop court (min 6 caracteres)'}), 400
    
    password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash)
        )
        conn.commit()
        return jsonify({'success': True, 'message': 'Inscription reussie'})
    except mysql.connector.IntegrityError as e:
        if 'Duplicate entry' in str(e):
            return jsonify({'error': 'Nom d\'utilisateur ou email deja utilise'}), 400
        return jsonify({'error': str(e)}), 400
    finally:
        cursor.close()
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    
    if not user or not bcrypt.check_password_hash(user['password_hash'], password):
        return jsonify({'error': 'Identifiants invalides'}), 401
    
    session_token = str(uuid.uuid4())
    expires_at = datetime.now() + timedelta(days=7)
    
    cursor.execute(
        "INSERT INTO user_sessions (user_id, session_token, expires_at) VALUES (%s, %s, %s)",
        (user['id'], session_token, expires_at)
    )
    conn.commit()
    cursor.close()
    conn.close()
    
    response = jsonify({
        'success': True,
        'user_id': user['id'],
        'username': user['username'],
        'session_token': session_token,
        'expires_at': expires_at.isoformat()
    })
    
    response.set_cookie('session_token', session_token, max_age=7*24*60*60, httponly=False, path='/', samesite='Lax')
    
    return response

@app.route('/api/logout', methods=['POST'])
def logout():
    session_token = request.cookies.get('session_token')
    if session_token:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE session_token = %s", (session_token,))
            conn.commit()
            cursor.close()
            conn.close()
    
    response = jsonify({'success': True})
    response.set_cookie('session_token', '', expires=0, path='/')
    return response

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    session_token = request.cookies.get('session_token')
    if not session_token:
        return jsonify({'authenticated': False, 'user': None})
    
    conn = get_db()
    if not conn:
        return jsonify({'authenticated': False, 'user': None})
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT u.id, u.username FROM users u
        JOIN user_sessions s ON u.id = s.user_id
        WHERE s.session_token = %s AND s.expires_at > NOW()
    """, (session_token,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if user:
        return jsonify({'authenticated': True, 'user': user})
    return jsonify({'authenticated': False, 'user': None})

# ============================================================
# ROUTES API (protégées)
# ============================================================

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'Aucune image'}), 400
    
    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': 'Fichier vide'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Format non supporte'}), 400
    
    original_filename = file.filename
    ext = original_filename.rsplit('.', 1)[1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
    file.save(filepath)
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_images (user_id, original_filename, stored_filename, file_path)
        VALUES (%s, %s, %s, %s)
    """, (request.user['id'], original_filename, stored_filename, filepath))
    conn.commit()
    image_id = cursor.lastrowid
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'image_id': image_id, 'path': filepath})

@app.route('/api/extract', methods=['POST'])
@login_required
def extract_features():
    data = request.json
    image_id = data.get('image_id')
    gender = data.get('gender', 'unknown')
    age_range = data.get('age', '')
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_images WHERE id = %s AND user_id = %s", (image_id, request.user['id']))
    image = cursor.fetchone()
    cursor.close()
    
    if not image:
        conn.close()
        return jsonify({'error': 'Image introuvable'}), 404
    
    gender_map = {"homme": "1", "femme": "2", "unknown": "3"}
    gender_code = gender_map.get(gender, "3")
    
    try:
        process = subprocess.Popen(
            [sys.executable, EXTRACTOR_SCRIPT, image['file_path']],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=BACKEND_DIR
        )
        stdout, stderr = process.communicate(input=f"{gender_code}\n", timeout=300)
        
        if process.returncode == 0:
            features_path = os.path.join(OUTPUT_FOLDER, 'features.json')
            
            if not os.path.exists(features_path):
                conn.close()
                return jsonify({'error': 'Fichier features non genere'}), 500
            
            with open(features_path, 'r', encoding='utf-8') as f:
                features = json.load(f)
            
            hair = features.get('hair', {})
            eyes = features.get('eyes', {})
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO face_features (
                    user_id, image_id, gender, age_range, face_shape, skin_tone,
                    has_smile, has_glasses, hair_color, hair_type, hair_length,
                    hair_length_pixels, eyes_color
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.user['id'], image_id, gender, age_range,
                features.get('face_shape'), features.get('skin_tone'),
                features.get('has_smile'), features.get('has_glasses'),
                hair.get('color'), hair.get('type'), hair.get('length'),
                hair.get('length_pixels'), eyes.get('color')
            ))
            conn.commit()
            features_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            return jsonify({'success': True, 'features_id': features_id, 'features': features})
        else:
            conn.close()
            return jsonify({'error': stderr}), 500
            
    except subprocess.TimeoutExpired:
        process.kill()
        conn.close()
        return jsonify({'error': 'Timeout'}), 500
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
@login_required
def generate_avatar():
    if get_generator() is None:
        return jsonify({'error': 'Generateur non disponible'}), 500
    
    data = request.json
    features_id = data.get('features_id')
    style_key = data.get('style', '1')
    age = data.get('age', '')
    custom = data.get('custom', '')
    quality = data.get('quality', 'standard')
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_features WHERE id = %s AND user_id = %s", (features_id, request.user['id']))
    features_db = cursor.fetchone()
    
    if not features_db:
        cursor.close()
        conn.close()
        return jsonify({'error': 'Caracteristiques introuvables'}), 404
    
    features = {
        'hair': {'color': features_db['hair_color'], 'type': features_db['hair_type'], 'length': features_db['hair_length']},
        'eyes': {'color': features_db['eyes_color']},
        'face_shape': features_db['face_shape'],
        'skin_tone': features_db['skin_tone'],
        'has_smile': features_db['has_smile'],
        'has_glasses': features_db['has_glasses']
    }
    
    generator = get_generator()
    result = generator.generate(features, style_key, features_db['gender'], age, custom, quality)
    
    if result['success']:
        if os.path.exists(result['path']):
            cursor.execute("""
                INSERT INTO generated_avatars (
                    user_id, features_id, style, style_name, quality,
                    generated_filename, file_path, prompt_used
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                request.user['id'], features_id, style_key,
                STYLES.get(style_key, {}).get('name', ''),
                quality, result['filename'], result['path'], result['prompt']
            ))
            conn.commit()
            avatar_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            return jsonify({
                'success': True,
                'avatar_id': avatar_id,
                'image_url': f'/avatars/{result["filename"]}',
                'prompt': result['prompt']
            })
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Fichier avatar non genere'}), 500
    else:
        cursor.close()
        conn.close()
        return jsonify({'error': result.get('error', 'Erreur de generation')}), 500

@app.route('/avatars/<filename>')
def serve_avatar(filename):
    filepath = os.path.join(AVATAR_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath)
    else:
        return jsonify({'error': 'Fichier non trouve'}), 404

@app.route('/api/user/history', methods=['GET'])
@login_required
def get_history():
    limit = request.args.get('limit', 10, type=int)
    offset = request.args.get('offset', 0, type=int)
    
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    # Compter le total
    cursor.execute("SELECT COUNT(*) as total FROM generated_avatars WHERE user_id = %s", (request.user['id'],))
    total = cursor.fetchone()['total']
    
    # Récupérer les avatars avec pagination
    cursor.execute("""
        SELECT a.*, f.hair_color, f.eyes_color, f.face_shape
        FROM generated_avatars a
        JOIN face_features f ON a.features_id = f.id
        WHERE a.user_id = %s
        ORDER BY a.generation_date DESC
        LIMIT %s OFFSET %s
    """, (request.user['id'], limit, offset))
    
    history = cursor.fetchall()
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'history': history, 'total': total})

@app.route('/api/user/favorites', methods=['GET', 'POST', 'DELETE'])
@login_required
def manage_favorites():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'GET':
        cursor.execute("""
            SELECT f.*, a.style_name, a.generated_filename, a.generation_date
            FROM favorite_avatars f
            JOIN generated_avatars a ON f.avatar_id = a.id
            WHERE f.user_id = %s
            ORDER BY f.added_date DESC
        """, (request.user['id'],))
        favorites = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'favorites': favorites})
    
    elif request.method == 'POST':
        data = request.json
        avatar_id = data.get('avatar_id')
        notes = data.get('notes', '')
        
        try:
            cursor.execute(
                "INSERT INTO favorite_avatars (user_id, avatar_id, notes) VALUES (%s, %s, %s)",
                (request.user['id'], avatar_id, notes)
            )
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({'success': True})
        except mysql.connector.IntegrityError:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Deja dans les favoris'}), 400
    
    elif request.method == 'DELETE':
        data = request.json
        favorite_id = data.get('favorite_id')
        
        cursor.execute(
            "DELETE FROM favorite_avatars WHERE id = %s AND user_id = %s",
            (favorite_id, request.user['id'])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_stats():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Erreur base de donnees'}), 500
    
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("SELECT COUNT(*) as total FROM generated_avatars WHERE user_id = %s", (request.user['id'],))
    total = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT style_name, COUNT(*) as count
        FROM generated_avatars WHERE user_id = %s
        GROUP BY style_name ORDER BY count DESC LIMIT 5
    """, (request.user['id'],))
    top_styles = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return jsonify({'success': True, 'stats': {'total_generations': total, 'top_styles': top_styles}})

# ============================================================
# LANCEMENT
# ============================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("SERVEUR DEMARRE")
    print("="*60)
    print(f"Application: http://localhost:5000/app")
    print(f"Login: http://localhost:5000/login.html")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
