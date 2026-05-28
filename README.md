# Projet_GenAI
🎨 Avatar Generator AI

📋 Description du projet
Avatar Generator AI est une application web complète qui permet de générer des avatars personnalisés à partir d'une simple photo en utilisant l'intelligence artificielle. Le projet combine vision par ordinateur et génération d'images pour transformer vos photos en avatars uniques.

🎯 Objectifs du projet
Analyser automatiquement les traits du visage à partir d'une photo

Extraire les caractéristiques faciales (couleur des cheveux, des yeux, forme du visage, teint)

Générer des avatars dans différents styles artistiques

Proposer une interface web complète avec gestion des utilisateurs

🛠️ Technologies utilisées
Composant	Technologie	Rôle
Backend	Python + Flask	API et logique métier
Base de données	MySQL (XAMPP)	Stockage des utilisateurs et générations
Frontend	HTML5, CSS3, JavaScript	Interface utilisateur
Segmentation faciale	SegFormer (jonathandinu/face-parsing)	Extraction des traits du visage
Génération d'images	Stable Diffusion 1.5	Création des avatars
Détection faciale	OpenCV (Haar Cascade)	Localisation du visage

📁 Structure du projet

<img width="3120" height="332" alt="image" src="https://github.com/user-attachments/assets/8adf9ef1-5c4b-4b9e-8920-e5ca713a1c83" />
    
🧠 Modèles d'IA utilisés
1. Segmentation faciale - jonathandinu/face-parsing
Type : Segformer (Transformer-based)

Fonction : Découpe l'image en 19 régions différentes (peau, cheveux, yeux, nez, bouche, etc.)

Téléchargement : https://huggingface.co/jonathandinu/face-parsing/tree/main

Fichiers nécessaires : config.json, preprocessor_config.json, pytorch_model.bin

2. Génération d'images - runwayml/stable-diffusion-v1-5
Type : Modèle de diffusion

Fonction : Génère l'avatar à partir d'un prompt textuel

Poids : ~2GB (téléchargement automatique)

3. Détection faciale - OpenCV (Haar Cascade)
Bibliothèque : OpenCV

Fichier : haarcascade_frontalface_default.xml

Fonction : Détection de la position du visage dans l'image

✨ Fonctionnalités principales
🔐 Authentification utilisateur
Inscription et connexion sécurisées

Gestion des sessions (cookies)

Espace personnel avec tableau de bord

📸 Analyse faciale
Détection automatique du visage (OpenCV)

Extraction des caractéristiques :

Cheveux : couleur (blond/brun/noir/roux), type (lisse/ondulé/bouclé), longueur

Yeux : couleur (bleu/vert/marron), position

Visage : forme (ovale/rond/cœur), teint

Accessoires : lunettes, sourire

🎨 Génération d'avatars
#	Style	Rendu
1	REALISTIC	Photo réaliste, texture peau détaillée
2	CINEMATIC	Style cinéma, éclairage dramatique
3	STUDIO	Portrait studio, éclairage doux
4	CARTOON	Style Pixar, couleurs vives
5	ANIME	Style animation japonaise
6	FANTASY	Personnage fantastique, éthéré
💾 Gestion des données
Historique des générations

Système de favoris

Statistiques personnelles

🔄 Flux de l'application
text
1. Upload photo
       ↓
2. Détection du visage (OpenCV)
       ↓
3. Segmentation faciale (SegFormer - 19 classes)
       ↓
4. Extraction des caractéristiques
       ↓
5. Construction d'un prompt IA
       ↓
6. Génération de l'avatar (Stable Diffusion)
       ↓
7. Affichage et sauvegarde
   
🗄️ Base de données
Tables principales
Table	Description
users	Utilisateurs (id, username, email, password_hash)
user_sessions	Sessions de connexion
user_images	Photos uploadées
face_features	Caractéristiques extraites (cheveux, yeux, forme, teint)
generated_avatars	Avatars générés (style, qualité, prompt utilisé)
favorite_avatars	Favoris des utilisateurs

📡 API principales
Endpoint	Méthode	Description
/api/register	POST	Inscription
/api/login	POST	Connexion
/api/upload	POST	Upload photo
/api/extract	POST	Extraction des traits
/api/generate	POST	Génération avatar
/api/user/history	GET	Historique
/api/user/favorites	GET/POST/DELETE	Gestion favoris
/api/user/stats	GET	Statistiques

🚀 Installation (étapes clés)

Prérequis
Python 3.11+

MySQL (XAMPP)

8GB RAM minimum

Étapes
Cloner le dépôt

Créer environnement virtuel

Installer dépendances (pip install -r requirements.txt)

Configurer MySQL (exécuter le script SQL)

Télécharger le modèle de segmentation (Hugging Face)

Lancer le serveur (python app.py)


Fonctionnalités présentées dans la vidéo :

Création de compte et connexion

Upload de photo et extraction des traits

Génération d'avatars dans les 6 styles

Consultation de l'historique

Gestion des favoris

Tableau de bord des statistiques

📊 Performances
Opération	Durée moyenne
Extraction des traits	2-3 minutes
Génération (qualité standard)	1-2 min
Génération (qualité rapide)	2.5-3.5 min
Génération (qualité haute)	4< min
🔧 Défauts et limitations
Problèmes identifiés
Temps de calcul long : L'extraction et la génération prennent plusieurs minutes

Dépendance GPU : La génération est lente sans carte graphique dédiée

Modèle lourd : Nécessite ~4GB d'espace disque pour les modèles

Précision variable : L'extraction dépend de la qualité de la photo

Modèle de génération limité

Améliorations possibles

Intégrer un modèle de détection plus précis

Intégrer un modèle de génération plus efficace comme Nano Banana

👤 Auteur
Amine Ben Abdennour 2SIC

🙏 Ressources
Modèle de segmentation : jonathandinu/face-parsing

Stable Diffusion : Stability AI

OpenCV : OpenCV
