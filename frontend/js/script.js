// ============================================================
// script.js - Script principal
// ============================================================

// Variables globales
let currentImageId = null;
let currentFeaturesId = null;
let currentFeatures = null;
let selectedStyle = "1";

// Vérifier l'authentification au chargement
document.addEventListener('DOMContentLoaded', async () => {
    const isAuthenticated = await checkAuth();
    if (!isAuthenticated) {
        window.location.href = '/login.html';
        return;
    }
    
    // Afficher le nom d'utilisateur
    const username = localStorage.getItem('username');
    if (username) {
        const userInfoElements = document.querySelectorAll('#userInfo');
        userInfoElements.forEach(el => {
            if (el) el.textContent = username;
        });
    }
    
    setupEventListeners();
    loadUserStats();
});

// Vérifier l'authentification
async function checkAuth() {
    try {
        const response = await fetch('/api/check-auth', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.authenticated) {
            localStorage.setItem('username', data.user.username);
            return true;
        }
        return false;
    } catch (error) {
        console.error('Erreur auth:', error);
        return false;
    }
}

// Configuration des événements
function setupEventListeners() {
    // Upload image
    const imageInput = document.getElementById('imageInput');
    if (imageInput) {
        imageInput.addEventListener('change', handleImageUpload);
    }
    
    // Glisser-déposer
    const uploadArea = document.getElementById('uploadArea');
    if (uploadArea) {
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, preventDefaults, false);
        });
        
        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }
        
        uploadArea.addEventListener('drop', handleDrop, false);
        
        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;
            if (files.length > 0) {
                imageInput.files = files;
                handleImageUpload({ target: { files: files } });
            }
        }
    }
    
    // Supprimer image
    const removeImage = document.getElementById('removeImage');
    if (removeImage) {
        removeImage.addEventListener('click', resetUpload);
    }
    
    // Extraction
    const extractBtn = document.getElementById('extractBtn');
    if (extractBtn) {
        extractBtn.addEventListener('click', extractFeatures);
    }
    
    // Génération
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        generateBtn.addEventListener('click', generateAvatar);
    }
    
    // Téléchargement
    const downloadBtn = document.getElementById('downloadBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadAvatar);
    }
    
    // Reset
    const resetBtn = document.getElementById('resetBtn');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetAll);
    }
    
    // Déconnexion
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // Style cards
    document.querySelectorAll('.style-card').forEach(card => {
        card.addEventListener('click', () => {
            document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedStyle = card.dataset.style;
        });
    });
}

// Gestion de l'upload
async function handleImageUpload(event) {
    const file = event.target.files[0];
    if (!file) {
        console.error('Aucun fichier sélectionné');
        return;
    }
    
    console.log('Fichier sélectionné:', file.name, file.type, file.size);
    
    const formData = new FormData();
    formData.append('image', file);
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (response.status === 401) {
            alert('Session expirée, veuillez vous reconnecter');
            window.location.href = '/login.html';
            return;
        }
        
        if (data.success) {
            currentImageId = data.image_id;
            
            const preview = document.getElementById('preview');
            const previewImg = document.getElementById('previewImg');
            const uploadArea = document.getElementById('uploadArea');
            
            previewImg.src = URL.createObjectURL(file);
            preview.classList.remove('hidden');
            uploadArea.classList.add('hidden');
            
            document.getElementById('extractBtn').disabled = false;
            document.getElementById('step2').classList.remove('hidden');
            
            console.log('Upload réussi, image_id:', currentImageId);
        } else {
            alert('Erreur: ' + (data.error || 'Upload échoué'));
        }
    } catch (error) {
        console.error('Erreur upload:', error);
        alert('Erreur: ' + error.message);
    }
}

// Réinitialiser l'upload
function resetUpload() {
    currentImageId = null;
    document.getElementById('imageInput').value = '';
    document.getElementById('preview').classList.add('hidden');
    document.getElementById('uploadArea').classList.remove('hidden');
    document.getElementById('extractBtn').disabled = true;
    document.getElementById('step2').classList.add('hidden');
    document.getElementById('step3').classList.add('hidden');
    document.getElementById('step4').classList.add('hidden');
}

// Extraction des caractéristiques
async function extractFeatures() {
    if (!currentImageId) {
        alert('Veuillez d\'abord uploader une image');
        return;
    }
    
    const gender = document.querySelector('input[name="gender"]:checked').value;
    const age = document.getElementById('age').value;
    
    const extractBtn = document.getElementById('extractBtn');
    extractBtn.disabled = true;
    extractBtn.textContent = '⏳ Extraction en cours...';
    
    document.getElementById('featuresResult').innerHTML = '<div class="loading">Extraction des caractéristiques... (2-3 min)</div>';
    document.getElementById('step3').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                image_id: currentImageId,
                gender: gender,
                age: age
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            currentFeaturesId = data.features_id;
            currentFeatures = data.features;
            displayFeatures(data.features);
            document.getElementById('generateBtn').disabled = false;
        } else {
            document.getElementById('featuresResult').innerHTML = `<div class="loading">❌ Erreur: ${data.error}</div>`;
        }
    } catch (error) {
        document.getElementById('featuresResult').innerHTML = `<div class="loading">❌ Erreur: ${error.message}</div>`;
    } finally {
        extractBtn.disabled = false;
        extractBtn.textContent = '📊 Extraire les caractéristiques';
    }
}

// Affichage des caractéristiques
function displayFeatures(features) {
    const hair = features.hair || {};
    const eyes = features.eyes || {};
    
    let html = `
        <div class="feature-item">
            <span class="feature-label">💇 Cheveux:</span>
            <span class="feature-value">${hair.color || '?'} (${hair.type || '?'})</span>
        </div>
        <div class="feature-item">
            <span class="feature-label">📏 Longueur:</span>
            <span class="feature-value">${hair.length_pixels || 0} pixels → ${hair.length || '?'}</span>
        </div>
        <div class="feature-item">
            <span class="feature-label">👁️ Yeux:</span>
            <span class="feature-value">${eyes.color || '?'}</span>
        </div>
        <div class="feature-item">
            <span class="feature-label">👤 Forme visage:</span>
            <span class="feature-value">${features.face_shape || '?'}</span>
        </div>
        <div class="feature-item">
            <span class="feature-label">🎨 Teint:</span>
            <span class="feature-value">${features.skin_tone || '?'}</span>
        </div>
        <div class="feature-item">
            <span class="feature-label">😊 Sourire:</span>
            <span class="feature-value">${features.has_smile ? 'Oui' : 'Non'}</span>
        </div>
        <div class="feature-item">
            <span class="feature-label">👓 Lunettes:</span>
            <span class="feature-value">${features.has_glasses ? 'Oui' : 'Non'}</span>
        </div>
    `;
    
    document.getElementById('featuresResult').innerHTML = html;
}

// Génération de l'avatar
async function generateAvatar() {
    if (!currentFeaturesId) {
        alert('Veuillez d\'abord extraire les caractéristiques');
        return;
    }
    
    const age = document.getElementById('age').value;
    const custom = document.getElementById('custom').value;
    const quality = document.getElementById('quality').value;
    
    const generateBtn = document.getElementById('generateBtn');
    generateBtn.disabled = true;
    generateBtn.textContent = '⏳ Génération en cours...';
    
    document.getElementById('avatarResult').innerHTML = '<div class="loading">Génération de l\'avatar... (20-30s)</div>';
    document.getElementById('step4').classList.remove('hidden');
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                features_id: currentFeaturesId,
                style: selectedStyle,
                age: age,
                custom: custom,
                quality: quality
            }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success && data.image_url) {
            document.getElementById('avatarResult').innerHTML = `
                <div style="text-align: center;">
                    <img src="${data.image_url}" alt="Avatar généré" style="max-width: 100%; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
                    ${data.prompt ? `<p style="margin-top: 15px; font-size: 12px; color: #666;">📝 Prompt: ${data.prompt.substring(0, 100)}...</p>` : ''}
                </div>
            `;
            document.getElementById('downloadBtn').disabled = false;
            window.currentAvatarUrl = data.image_url;
        } else {
            document.getElementById('avatarResult').innerHTML = `<div class="loading">❌ Erreur: ${data.error || 'Erreur inconnue'}</div>`;
        }
    } catch (error) {
        document.getElementById('avatarResult').innerHTML = `<div class="loading">❌ Erreur: ${error.message}</div>`;
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = '🎨 Générer l\'avatar';
    }
}

// Téléchargement
function downloadAvatar() {
    if (window.currentAvatarUrl) {
        const link = document.createElement('a');
        link.href = window.currentAvatarUrl;
        link.download = 'avatar.png';
        link.click();
    }
}

// Réinitialisation
function resetAll() {
    resetUpload();
    currentFeaturesId = null;
    currentFeatures = null;
    selectedStyle = "1";
    document.querySelector('input[name="gender"][value="personne"]').checked = true;
    document.getElementById('age').value = '';
    document.getElementById('custom').value = '';
    document.getElementById('quality').value = 'standard';
    document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
    document.querySelector('.style-card').classList.add('selected');
}

// Déconnexion
async function logout() {
    await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
    });
    localStorage.removeItem('username');
    window.location.href = '/login.html';
}

// Charger les statistiques
async function loadUserStats() {
    try {
        const response = await fetch('/api/user/stats', {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            const totalSpan = document.getElementById('totalGenerations');
            if (totalSpan) {
                totalSpan.textContent = data.stats.total_generations || 0;
            }
        }
    } catch (error) {
        console.error('Erreur chargement stats:', error);
    }
}