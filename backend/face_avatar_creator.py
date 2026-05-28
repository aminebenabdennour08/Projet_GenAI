# ============================================================
# face_avatar_creator.py
# Générateur d'avatar avec Stable Diffusion
# ============================================================

import os
import sys
import json
import torch
import time
import uuid
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler

print("="*60)
print("GENERATEUR D'AVATAR - STABLE DIFFUSION")
print("="*60)

# ============================================================
# CONFIGURATION DES CHEMINS - VERS LA RACINE
# ============================================================

# Determiner le chemin absolu de la racine du projet
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Dossier des avatars (a la racine)
AVATAR_DIR = os.path.join(PROJECT_ROOT, 'avatars')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output')

print(f"[INFO] SCRIPT_DIR: {SCRIPT_DIR}")
print(f"[INFO] PROJECT_ROOT: {PROJECT_ROOT}")
print(f"[INFO] AVATAR_DIR: {AVATAR_DIR}")
print(f"[INFO] OUTPUT_DIR: {OUTPUT_DIR}")

# Creer les dossiers
os.makedirs(AVATAR_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# STYLES DISPONIBLES
# ============================================================
STYLES = {
    "1": {"name": "REALISTIC", "prompt": "photorealistic, 8K, detailed skin texture, natural lighting"},
    "2": {"name": "CINEMATIC", "prompt": "cinematic, dramatic lighting, film grain"},
    "3": {"name": "STUDIO", "prompt": "studio portrait, soft professional lighting"},
    "4": {"name": "CARTOON", "prompt": "cartoon, Pixar style, vibrant colors"},
    "5": {"name": "ANIME", "prompt": "anime, Japanese animation style"},
    "6": {"name": "FANTASY", "prompt": "fantasy character, ethereal, magical"}
}

# ============================================================
# CHARGEMENT DU MODELE
# ============================================================

def load_pipeline():
    print("\n[LOAD] Chargement Stable Diffusion...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"   Device: {device}")
    
    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=torch.float16 if device == "cuda" else torch.float32
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to(device)
    
    print("[OK] Modele charge")
    return pipe

# ============================================================
# CONSTRUCTION DU PROMPT
# ============================================================

def build_prompt(features, style_prompt, gender, age, custom):
    parts = []
    
    if gender == "homme":
        parts.append(f"portrait of a {age} man" if age else "portrait of a man")
    elif gender == "femme":
        parts.append(f"portrait of a {age} woman" if age else "portrait of a woman")
    else:
        parts.append(f"portrait of a {age} person" if age else "portrait of a person")
    
    hair = features.get("hair", {})
    if hair.get("color") not in ["unknown", None]:
        desc = []
        if hair.get("length") not in ["unknown", "medium", None]:
            desc.append(hair["length"])
        if hair.get("type") not in ["unknown", "straight", None]:
            desc.append(hair["type"])
        desc.append(hair["color"])
        parts.append(f"with {' '.join(desc)} hair")
    
    eyes = features.get("eyes", {})
    eye_color = eyes.get("color", "unknown")
    if eye_color not in ["unknown", None]:
        parts.append(f"{eye_color} eyes")
    
    face_shape = features.get("face_shape")
    if face_shape not in ["unknown", None]:
        parts.append(f"{face_shape} face")
    
    skin_tone = features.get("skin_tone")
    if skin_tone not in ["unknown", None]:
        parts.append(f"{skin_tone} skin")
    
    if features.get("has_smile"):
        parts.append("smiling")
    
    if features.get("has_glasses"):
        parts.append("wearing glasses")
    
    parts.append(style_prompt)
    parts.append("high quality, detailed face, centered, looking at viewer")
    
    if custom and custom.strip():
        parts.append(custom.strip())
    
    return ", ".join(parts)

# ============================================================
# GÉNÉRATION
# ============================================================

class AvatarGenerator:
    def __init__(self):
        self.pipe = None
        self.load_model()
    
    def load_model(self):
        self.pipe = load_pipeline()
    
    def generate(self, features, style_key, gender, age, custom, quality="standard"):
        steps_map = {'rapide': 20, 'standard': 35, 'haute': 50}
        steps = steps_map.get(quality, 35)
        
        style = STYLES.get(style_key, STYLES["1"])
        prompt = build_prompt(features, style["prompt"], gender, age, custom)
        
        output_filename = f"avatar_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(AVATAR_DIR, output_filename)
        
        print(f"\n[GENERATION] Style: {style['name']}")
        print(f"   Output: {output_path}")
        print(f"   Prompt: {prompt[:100]}...")
        
        start_time = time.time()
        
        try:
            result = self.pipe(
                prompt=prompt,
                negative_prompt="deformed, ugly, bad anatomy, low quality, blurry",
                num_inference_steps=steps,
                guidance_scale=7.5,
                width=512,
                height=512
            )
            
            generation_time = time.time() - start_time
            result.images[0].save(output_path)
            
            print(f"   [OK] Genere en {generation_time:.1f}s")
            
            return {
                'success': True,
                'filename': output_filename,
                'path': output_path,
                'prompt': prompt,
                'generation_time': generation_time
            }
        except Exception as e:
            print(f"   [ERREUR] {e}")
            return {'success': False, 'error': str(e)}

# ============================================================
# MAIN (pour test independant)
# ============================================================

if __name__ == "__main__":
    # Chercher le fichier features.json dans OUTPUT_DIR
    features_path = os.path.join(OUTPUT_DIR, 'features.json')
    
    if len(sys.argv) > 1:
        features_path = sys.argv[1]
    
    if not os.path.exists(features_path):
        print(f"\n[ERREUR] Fichier non trouve: {features_path}")
        print("   Assurez-vous que le fichier features.json existe dans le dossier output/")
        print("   Ou passez le chemin en argument: python face_avatar_creator.py chemin/vers/features.json")
        sys.exit(1)
    
    print(f"\n[FEATURES] Chargement: {features_path}")
    
    with open(features_path, 'r', encoding='utf-8') as f:
        features = json.load(f)
    
    print(f"\n[FEATURES]")
    hair = features.get("hair", {})
    print(f"   Cheveux: {hair.get('color', '?')} ({hair.get('type', '?')})")
    eyes = features.get("eyes", {})
    print(f"   Yeux: {eyes.get('color', '?')}")
    
    print("\n[PARAMETRES]")
    print("1. Homme   2. Femme   3. Non specifie")
    g = input("Genre (1-3): ")
    gender = {"1": "homme", "2": "femme", "3": "personne"}.get(g, "personne")
    
    age = input("Age (ex: 25, young, middle-aged): ")
    custom = input("Vetements (ex: wearing a black suit): ")
    
    print("\n[QUALITE]")
    print("1. Rapide   2. Standard   3. Haute")
    q = input("Choix (1-3): ")
    quality = {"1": "rapide", "2": "standard", "3": "haute"}.get(q, "standard")
    
    print("\n[STYLES]")
    for k, v in STYLES.items():
        print(f"   {k}. {v['name']}")
    s = input("Style (1-6): ")
    
    generator = AvatarGenerator()
    result = generator.generate(features, s, gender, age, custom, quality)
    
    if result['success']:
        print(f"\n[OK] Avatar genere: {result['filename']}")
        print(f"   Chemin: {result['path']}")
    else:
        print(f"\n[ERREUR] {result['error']}")