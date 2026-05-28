# ============================================================
# face_features_extractor.py
# Extraction des caracteristiques faciales avec teintes par defaut
# ============================================================

import os
import sys
import json
import torch
import numpy as np
import cv2
from PIL import Image
from sklearn.cluster import KMeans

print("="*60)
print("EXTRACTEUR - EXTRACTION DES CARACTERISTIQUES FACIALES")
print("="*60)

# ============================================================
# CONFIGURATION - CHEMINS VERS LA RACINE
# ============================================================

# Determiner le chemin absolu de la racine du projet
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Dossiers de sortie (a la racine du projet)
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')
MASKS_DIR = os.path.join(OUTPUT_DIR, 'masks')

# Modele (a la racine du projet)
MODEL_DIR = os.path.join(PROJECT_ROOT, 'face_parsing_model')

print(f"[INFO] SCRIPT_DIR: {SCRIPT_DIR}")
print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[INFO] OUTPUT_DIR: {OUTPUT_DIR}")
print(f"[INFO] MASKS_DIR: {MASKS_DIR}")
print(f"[INFO] MODEL_DIR: {MODEL_DIR}")

# Creer les dossiers
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(MASKS_DIR, exist_ok=True)

if not os.path.exists(MODEL_DIR):
    print(f"\n[ERREUR] Dossier modele introuvable: {MODEL_DIR}")
    print("   Assurez-vous que le dossier 'face_parsing_model' est a la racine du projet")
    sys.exit(1)

# ============================================================
# IMPORTATIONS
# ============================================================
from transformers import SegformerImageProcessor, SegformerForSemanticSegmentation
import torch.nn.functional as F

# ============================================================
# LABELS
# ============================================================
LABELS = {
    0: "background", 1: "skin", 2: "nose", 3: "eye_g", 4: "l_eye", 5: "r_eye",
    6: "l_brow", 7: "r_brow", 8: "l_ear", 9: "r_ear", 10: "mouth", 11: "u_lip",
    12: "l_lip", 13: "hair", 14: "hat", 15: "ear_r", 16: "neck_l", 17: "neck", 18: "cloth"
}

# ============================================================
# COULEURS ET TEINTES PAR DEFAUT
# ============================================================

# Teintes par defaut pour chaque caracteristique
DEFAULT_COLORS = {
    "eyes": "brown",
    "hair": "brown",
    "skin": "medium",
    "clothing": "black"
}

DEFAULT_EYE_COLOR = "brown"
DEFAULT_HAIR_COLOR = "brown"
DEFAULT_SKIN_TONE = "medium"
DEFAULT_CLOTHING_COLOR = "black"

DEFAULT_EYE_WIDTH = 30
DEFAULT_EYE_HEIGHT = 20

# ============================================================
# REFERENCES DE COULEURS DES YEUX
# ============================================================

def rgb_to_lab(rgb):
    rgb_np = np.array([[[rgb[0], rgb[1], rgb[2]]]], dtype=np.uint8)
    lab = cv2.cvtColor(rgb_np, cv2.COLOR_RGB2LAB)
    return lab[0][0]

EYE_COLORS_REF = {
    "blue": {"rgb": [100, 150, 220], "lab": None},
    "green": {"rgb": [100, 180, 100], "lab": None},
    "brown": {"rgb": [100, 60, 40], "lab": None},
    "dark_brown": {"rgb": [70, 40, 30], "lab": None},
    "hazel": {"rgb": [120, 100, 60], "lab": None},
    "gray": {"rgb": [100, 100, 100], "lab": None}
}

for ref in EYE_COLORS_REF.values():
    ref["lab"] = rgb_to_lab(ref["rgb"])

def find_closest_eye_color(rgb):
    if rgb is None:
        return DEFAULT_EYE_COLOR
    
    lab = rgb_to_lab(rgb)
    best_match = DEFAULT_EYE_COLOR
    best_distance = float('inf')
    
    for name, ref in EYE_COLORS_REF.items():
        distance = np.linalg.norm(lab - ref["lab"])
        if distance < best_distance:
            best_distance = distance
            best_match = name
    
    if best_distance > 50:
        return DEFAULT_EYE_COLOR
    
    return best_match

# ============================================================
# FONCTIONS DE DETECTION AVEC TEINTES PAR DEFAUT
# ============================================================

def get_eye_position_from_mask(eye_mask, face_bbox=None, is_left=True):
    if eye_mask is not None and np.sum(eye_mask) > 0:
        contours, _ = cv2.findContours(eye_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            contour = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(contour)
            return {
                "x": int(x), "y": int(y), "width": int(w), "height": int(h),
                "center_x": int(x + w//2), "center_y": int(y + h//2),
                "detected": True
            }
    
    if face_bbox:
        face_x, face_y, face_w, face_h = face_bbox
        if is_left:
            default_x = face_x + int(face_w * 0.25)
            default_y = face_y + int(face_h * 0.35)
        else:
            default_x = face_x + int(face_w * 0.6)
            default_y = face_y + int(face_h * 0.35)
        
        return {
            "x": default_x, "y": default_y,
            "width": DEFAULT_EYE_WIDTH, "height": DEFAULT_EYE_HEIGHT,
            "center_x": default_x + DEFAULT_EYE_WIDTH//2,
            "center_y": default_y + DEFAULT_EYE_HEIGHT//2,
            "detected": False
        }
    
    if is_left:
        return {"x": 100, "y": 150, "width": DEFAULT_EYE_WIDTH, "height": DEFAULT_EYE_HEIGHT,
                "center_x": 115, "center_y": 160, "detected": False}
    else:
        return {"x": 200, "y": 150, "width": DEFAULT_EYE_WIDTH, "height": DEFAULT_EYE_HEIGHT,
                "center_x": 215, "center_y": 160, "detected": False}

def get_eye_color_from_mask(image_np, eye_mask):
    # Teinte par defaut
    if eye_mask is None or np.sum(eye_mask) == 0:
        return DEFAULT_EYE_COLOR
    
    eye_pixels = image_np[eye_mask > 0]
    if len(eye_pixels) == 0:
        return DEFAULT_EYE_COLOR
    
    brightness = np.mean(eye_pixels, axis=1)
    mask_filter = (brightness > 40) & (brightness < 200)
    filtered_pixels = eye_pixels[mask_filter]
    
    if len(filtered_pixels) < 20:
        filtered_pixels = eye_pixels
    
    if len(filtered_pixels) > 2000:
        indices = np.random.choice(len(filtered_pixels), 2000, replace=False)
        filtered_pixels = filtered_pixels[indices]
    
    if len(filtered_pixels) == 0:
        return DEFAULT_EYE_COLOR
    
    try:
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(filtered_pixels)
        labels = kmeans.labels_
        cluster_sizes = np.bincount(labels)
        largest_idx = np.argmax(cluster_sizes)
        dominant_color = kmeans.cluster_centers_[largest_idx]
        return find_closest_eye_color(dominant_color)
    except:
        return DEFAULT_EYE_COLOR

def get_face_bounding_box(skin_mask):
    if skin_mask is None or np.sum(skin_mask) == 0:
        return None
    contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)
    return (x, y, w, h)

def get_dominant_color_kmeans(image_np, mask, default_color="unknown"):
    if mask is None or np.sum(mask) == 0:
        return default_color, None
    
    pixels = image_np[mask > 0]
    if len(pixels) == 0:
        return default_color, None
    
    if len(pixels) > 5000:
        indices = np.random.choice(len(pixels), 5000, replace=False)
        pixels = pixels[indices]
    
    try:
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        kmeans.fit(pixels)
        labels = kmeans.labels_
        cluster_sizes = np.bincount(labels)
        largest_idx = np.argmax(cluster_sizes)
        color_rgb = kmeans.cluster_centers_[largest_idx]
        r, g, b = color_rgb
        
        # Classification des couleurs
        if r < 80 and g < 80 and b < 80:
            color_name = "black"
        elif r > 200 and g > 180 and b > 150:
            color_name = "blond"
        elif r > 150 and g > 100 and b > 80:
            color_name = "brown"
        else:
            color_name = "other"
        return color_name, color_rgb.tolist()
    except:
        return default_color, None

def get_region_properties(mask):
    if mask is None or np.sum(mask) == 0:
        return None
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None
    contour = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(contour)
    return {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}

def calculate_hair_length(hair_mask, gender):
    if hair_mask is None or np.sum(hair_mask) == 0:
        return 0, "medium"  # Longueur par defaut
    
    coords = np.where(hair_mask > 0)
    if len(coords[0]) == 0:
        return 0, "medium"
    
    hair_height = coords[0].max() - coords[0].min()
    
    if gender == "homme":
        if hair_height > 400:
            length = "long"
        elif hair_height > 200:
            length = "medium"
        else:
            length = "short"
    else:
        if hair_height > 550:
            length = "long"
        elif hair_height > 300:
            length = "medium"
        else:
            length = "short"
    return int(hair_height), length

def get_hair_type(hair_mask):
    if hair_mask is None or np.sum(hair_mask) == 0:
        return "straight"  # Type par defaut
    
    h, w = hair_mask.shape
    sample = hair_mask[:min(100, h), :min(100, w)]
    variance = np.var(sample[sample > 0]) if np.sum(sample > 0) > 0 else 0
    
    if variance > 800:
        return "curly"
    elif variance > 400:
        return "wavy"
    return "straight"

def get_skin_tone(image_np, skin_mask):
    # Teint par defaut
    if skin_mask is None or np.sum(skin_mask) == 0:
        return DEFAULT_SKIN_TONE
    
    skin_pixels = image_np[skin_mask > 0]
    if len(skin_pixels) == 0:
        return DEFAULT_SKIN_TONE
    
    if len(skin_pixels) > 5000:
        indices = np.random.choice(len(skin_pixels), 5000, replace=False)
        skin_pixels = skin_pixels[indices]
    
    try:
        avg_color = np.mean(skin_pixels, axis=0)
        r, g, b = avg_color
        
        if r > 200 and g > 170 and b > 150:
            return "fair"
        elif r > 170 and g > 130 and b > 100:
            return "light"
        elif r > 140 and g > 100 and b > 70:
            return "medium"
        elif r > 100 and g > 70 and b > 50:
            return "tan"
        else:
            return "dark"
    except:
        return DEFAULT_SKIN_TONE

def get_clothing_color(image_np, cloth_mask):
    # Couleur de vetement par defaut
    if cloth_mask is None or np.sum(cloth_mask) == 0:
        return DEFAULT_CLOTHING_COLOR
    
    cloth_pixels = image_np[cloth_mask > 0]
    if len(cloth_pixels) == 0:
        return DEFAULT_CLOTHING_COLOR
    
    if len(cloth_pixels) > 5000:
        indices = np.random.choice(len(cloth_pixels), 5000, replace=False)
        cloth_pixels = cloth_pixels[indices]
    
    try:
        avg_color = np.mean(cloth_pixels, axis=0)
        r, g, b = avg_color
        
        if r < 80 and g < 80 and b < 80:
            return "black"
        elif r > 200 and g > 200 and b > 200:
            return "white"
        elif r > 150 and g < 100 and b < 100:
            return "red"
        elif r < 100 and g > 100 and b < 100:
            return "green"
        elif r > 100 and g > 100 and b < 100:
            return "yellow"
        elif r < 100 and g < 100 and b > 100:
            return "blue"
        else:
            return DEFAULT_CLOTHING_COLOR
    except:
        return DEFAULT_CLOTHING_COLOR

# ============================================================
# EXTRACTEUR PRINCIPAL
# ============================================================

class FaceExtractor:
    def __init__(self, model_dir):
        print(f"\n[LOAD] Chargement...")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.image_processor = SegformerImageProcessor.from_pretrained(model_dir)
        self.model = SegformerForSemanticSegmentation.from_pretrained(model_dir)
        self.model.to(self.device)
        self.model.eval()
        print("[OK] Modele charge")
    
    def segment(self, image_path):
        image = Image.open(image_path).convert("RGB")
        inputs = self.image_processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
        upsampled = F.interpolate(logits, size=image.size[::-1], mode='bilinear', align_corners=False)
        labels = upsampled.argmax(dim=1)[0].cpu().numpy()
        masks = {}
        for label_id, name in LABELS.items():
            masks[name] = (labels == label_id).astype(np.uint8) * 255
        return masks, labels, np.array(image)
    
    def extract_features(self, image_path, gender):
        print(f"\n[EXTRACTION] Analyse de {image_path}...")
        masks, labels, image_np = self.segment(image_path)
        
        # Sauvegarde des masques dans MASKS_DIR
        for name, mask in masks.items():
            if mask is not None and np.sum(mask) > 0:
                mask_path = os.path.join(MASKS_DIR, f"{name}.png")
                cv2.imwrite(mask_path, mask)
        
        skin_mask = masks.get("skin")
        face_bbox = get_face_bounding_box(skin_mask)
        
        left_eye_mask = masks.get("l_eye")
        right_eye_mask = masks.get("r_eye")
        
        left_eye_pos = get_eye_position_from_mask(left_eye_mask, face_bbox, is_left=True)
        right_eye_pos = get_eye_position_from_mask(right_eye_mask, face_bbox, is_left=False)
        eye_color = get_eye_color_from_mask(image_np, left_eye_mask)
        
        hair_mask = masks.get("hair")
        hair_color, _ = get_dominant_color_kmeans(image_np, hair_mask, DEFAULT_HAIR_COLOR)
        hair_type = get_hair_type(hair_mask)
        hair_length_px, hair_length = calculate_hair_length(hair_mask, gender)
        
        hair = {
            "detected": hair_mask is not None and np.sum(hair_mask) > 0,
            "color": hair_color, "type": hair_type,
            "length_pixels": hair_length_px, "length": hair_length if hair_length != "unknown" else "medium"
        }
        
        left_brow = get_region_properties(masks.get("l_brow"))
        right_brow = get_region_properties(masks.get("r_brow"))
        
        nose = get_region_properties(masks.get("nose"))
        nose_size = "medium"
        if nose:
            if nose["width"] > 50:
                nose_size = "large"
            elif nose["width"] < 30:
                nose_size = "small"
        
        mouth = get_region_properties(masks.get("mouth"))
        mouth_size = "medium"
        if mouth:
            if mouth["width"] > 60:
                mouth_size = "wide"
            elif mouth["width"] < 40:
                mouth_size = "small"
        
        mouth_mask = masks.get("mouth")
        has_smile = mouth_mask is not None and np.sum(mouth_mask) > 300
        
        face_shape = "oval"
        if skin_mask is not None and np.sum(skin_mask) > 0:
            contours, _ = cv2.findContours(skin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(contour)
                ratio = h / w if w > 0 else 1
                if ratio > 1.35:
                    face_shape = "oval"
                elif ratio < 1.15:
                    face_shape = "round"
                else:
                    face_shape = "heart"
        
        skin_tone = get_skin_tone(image_np, skin_mask)
        glasses = masks.get("eye_g") is not None and np.sum(masks.get("eye_g")) > 0
        clothing_color = get_clothing_color(image_np, masks.get("cloth"))
        
        features = {
            "eyes": {"left_position": left_eye_pos, "right_position": right_eye_pos, "color": eye_color},
            "hair": hair,
            "eyebrows_detected": left_brow is not None and right_brow is not None,
            "nose_size": nose_size, "mouth_size": mouth_size,
            "has_smile": has_smile, "face_shape": face_shape,
            "skin_tone": skin_tone, "has_glasses": glasses,
            "clothing_color": clothing_color
        }
        
        # Sauvegarde de la visualisation
        h, w = image_np.shape[:2]
        colored = np.zeros((h, w, 3), dtype=np.uint8)
        color_map = {
            "background": (0,0,0), "skin": (255,220,180), "hair": (60,40,30),
            "nose": (255,150,100), "l_eye": (255,255,255), "r_eye": (255,255,255),
            "l_brow": (50,50,50), "r_brow": (50,50,50), "mouth": (180,80,60)
        }
        for label_id, name in LABELS.items():
            mask = (labels == label_id)
            color = color_map.get(name, (128,128,128))
            colored[mask] = color
        result = cv2.addWeighted(image_np, 0.4, colored, 0.6, 0)
        vis_path = os.path.join(OUTPUT_DIR, "segmentation.png")
        cv2.imwrite(vis_path, cv2.cvtColor(result, cv2.COLOR_RGB2BGR))
        
        return features

# ============================================================
# MAIN
# ============================================================

def convert_to_serializable(obj):
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    return obj

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\n[USAGE] python face_features_extractor.py photo.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"[ERREUR] Image introuvable: {image_path}")
        sys.exit(1)
    
    print("\n[GENRE]")
    print("1. Homme")
    print("2. Femme")
    print("3. Non specifie")
    gender_choice = input("Choix (1-3): ")
    gender = "homme" if gender_choice == "1" else "femme" if gender_choice == "2" else "unknown"
    
    extractor = FaceExtractor(MODEL_DIR)
    features = extractor.extract_features(image_path, gender)
    
    # Sauvegarde du fichier features.json dans OUTPUT_DIR
    features_path = os.path.join(OUTPUT_DIR, "features.json")
    with open(features_path, "w", encoding="utf-8") as f:
        json.dump(convert_to_serializable(features), f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] EXTRACTION TERMINEE")
    print(f"   Fichier: {features_path}")
    print(f"   Yeux: {features['eyes']['color']}")
    print(f"   Cheveux: {features['hair']['color']} ({features['hair']['type']})")
    print(f"   Teint: {features['skin_tone']}")
    print(f"   Vetements: {features.get('clothing_color', 'black')}")