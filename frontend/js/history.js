// ============================================================
// history.js - Page d'historique optimisée
// ============================================================

let currentPage = 1;
let totalPages = 1;
const itemsPerPage = 10;
let isLoading = false;

// Vérifier l'authentification
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
    
    // Charger l'historique
    await loadHistory(1);
    
    // Déconnexion
    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
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

// Déconnexion
async function logout() {
    await fetch('/api/logout', {
        method: 'POST',
        credentials: 'include'
    });
    localStorage.removeItem('username');
    window.location.href = '/login.html';
}

// Charger l'historique avec pagination
async function loadHistory(page = 1) {
    if (isLoading) return;
    isLoading = true;
    
    const offset = (page - 1) * itemsPerPage;
    
    // Afficher l'indicateur de chargement
    const loadingIndicator = document.getElementById('loadingIndicator');
    const historyContainer = document.getElementById('historyContainer');
    
    loadingIndicator.style.display = 'block';
    historyContainer.innerHTML = '';
    
    try {
        const response = await fetch(`/api/user/history?limit=${itemsPerPage}&offset=${offset}`, {
            credentials: 'include'
        });
        
        if (!response.ok) {
            throw new Error('Erreur de chargement');
        }
        
        const data = await response.json();
        
        loadingIndicator.style.display = 'none';
        
        if (data.success && data.history && data.history.length > 0) {
            displayHistory(data.history);
            totalPages = Math.ceil((data.total || data.history.length) / itemsPerPage);
            setupPagination(page);
        } else {
            historyContainer.innerHTML = '<div class="no-data">📭 Aucun avatar généré pour le moment.</div>';
            document.getElementById('pagination').innerHTML = '';
        }
        
    } catch (error) {
        console.error('Erreur chargement historique:', error);
        loadingIndicator.style.display = 'none';
        historyContainer.innerHTML = '<div class="no-data">❌ Erreur de chargement. Veuillez réessayer.</div>';
    } finally {
        isLoading = false;
    }
}

// Afficher l'historique avec lazy loading des images
function displayHistory(history) {
    const container = document.getElementById('historyContainer');
    
    let html = `
        <table class="history-table">
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Aperçu</th>
                    <th>Style</th>
                    <th>Qualité</th>
                    <th>Cheveux</th>
                    <th>Yeux</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
    `;
    
    history.forEach((item, index) => {
        const date = new Date(item.generation_date).toLocaleString();
        const imgId = `img_${index}_${Date.now()}`;
        
        html += `
            <tr>
                <td style="white-space: nowrap;">${date}</td>
                <td>
                    <img id="${imgId}" 
                         class="avatar-thumb" 
                         data-src="/avatars/${item.generated_filename}"
                         alt="Avatar"
                         style="width: 50px; height: 50px; object-fit: cover; border-radius: 10px; background: #f0f0f0;">
                </td>
                <td>${item.style_name || '-'}</td>
                <td>${item.quality || '-'}</td>
                <td>${item.hair_color || '-'}</td>
                <td>${item.eyes_color || '-'}</td>
                <td class="action-buttons">
                    <button onclick="viewAvatar('${item.generated_filename}')" class="btn-icon" title="Voir">👁️</button>
                    <button onclick="addToFavorites(${item.id})" class="btn-icon" title="Favori">❤️</button>
                    <button onclick="downloadAvatar('${item.generated_filename}')" class="btn-icon" title="Télécharger">💾</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
    
    // Lazy loading des images
    lazyLoadImages();
}

// Lazy loading des images
function lazyLoadImages() {
    const images = document.querySelectorAll('.avatar-thumb');
    
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                const src = img.getAttribute('data-src');
                if (src) {
                    img.src = src;
                    img.removeAttribute('data-src');
                }
                observer.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Configuration de la pagination
function setupPagination(currentPage) {
    const paginationContainer = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }
    
    let html = '<div class="pagination">';
    
    // Bouton précédent
    html += `<button class="page-btn" onclick="goToPage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>◀ Précédent</button>`;
    
    // Pages
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    if (startPage > 1) {
        html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
        if (startPage > 2) html += '<span class="page-dots">...</span>';
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        html += `<button class="page-btn ${activeClass}" onclick="goToPage(${i})">${i}</button>`;
    }
    
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += '<span class="page-dots">...</span>';
        html += `<button class="page-btn" onclick="goToPage(${totalPages})">${totalPages}</button>`;
    }
    
    // Bouton suivant
    html += `<button class="page-btn" onclick="goToPage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>Suivant ▶</button>`;
    
    html += '</div>';
    paginationContainer.innerHTML = html;
}

// Aller à une page
async function goToPage(page) {
    if (page < 1 || page > totalPages || page === currentPage) return;
    currentPage = page;
    await loadHistory(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Voir l'avatar
function viewAvatar(filename) {
    window.open(`/avatars/${filename}`, '_blank');
}

// Ajouter aux favoris
async function addToFavorites(avatarId) {
    try {
        const response = await fetch('/api/user/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ avatar_id: avatarId }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('❤️ Ajouté aux favoris !');
        } else {
            alert('Erreur: ' + (data.error || 'Déjà dans les favoris'));
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

// Télécharger l'avatar
function downloadAvatar(filename) {
    const link = document.createElement('a');
    link.href = `/avatars/${filename}`;
    link.download = filename;
    link.click();
}

// Raccourci clavier pour rafraîchir (F5)
document.addEventListener('keydown', (e) => {
    if (e.key === 'F5') {
        e.preventDefault();
        loadHistory(currentPage);
    }
});
