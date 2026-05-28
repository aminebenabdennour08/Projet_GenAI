// ============================================================
// history.js - Page d'historique
// ============================================================

let currentPage = 1;
const itemsPerPage = 10;
let totalPages = 1;

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
    
    loadHistory(1);
    
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

// Charger l'historique
async function loadHistory(page = 1) {
    const offset = (page - 1) * itemsPerPage;
    
    try {
        const response = await fetch(`/api/user/history?limit=${itemsPerPage}&offset=${offset}`, {
            credentials: 'include'
        });
        const data = await response.json();
        
        if (data.success) {
            displayHistory(data.history);
            totalPages = Math.ceil((data.total || data.history.length) / itemsPerPage);
            setupPagination(page);
        } else {
            showError(data.error);
        }
    } catch (error) {
        console.error('Erreur chargement historique:', error);
        showError(error.message);
    }
}

// Afficher l'historique
function displayHistory(history) {
    const container = document.getElementById('historyContainer');
    
    if (!history || history.length === 0) {
        container.innerHTML = '<p class="no-data">Aucun avatar généré pour le moment.</p>';
        return;
    }
    
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
    
    history.forEach(item => {
        const date = new Date(item.generation_date).toLocaleString();
        
        html += `
            <tr>
                <td>${date}</td>
                <td>
                    <img src="/avatars/${item.generated_filename}" alt="Avatar" style="width: 50px; height: 50px; object-fit: cover; border-radius: 10px;" onerror="this.src='/img/placeholder.png'">
                </td>
                <td>${item.style_name || '-'}</td>
                <td>${item.quality || '-'}</td>
                <td>${item.hair_color || '-'}</td>
                <td>${item.eyes_color || '-'}</td>
                <td>
                    <button onclick="viewAvatar('${item.generated_filename}')" class="btn-small">👁️ Voir</button>
                    <button onclick="addToFavorites(${item.id})" class="btn-small">❤️ Favori</button>
                    <button onclick="downloadAvatar('${item.generated_filename}')" class="btn-small">💾 Télécharger</button>
                </td>
            </tr>
        `;
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// Configuration de la pagination
function setupPagination(currentPage) {
    const paginationContainer = document.getElementById('pagination');
    
    if (!paginationContainer || totalPages <= 1) return;
    
    let html = '<div class="pagination">';
    
    if (currentPage > 1) {
        html += `<button onclick="goToPage(${currentPage - 1})" class="page-btn">◀ Précédent</button>`;
    }
    
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const activeClass = i === currentPage ? 'active' : '';
        html += `<button onclick="goToPage(${i})" class="page-btn ${activeClass}">${i}</button>`;
    }
    
    if (currentPage < totalPages) {
        html += `<button onclick="goToPage(${currentPage + 1})" class="page-btn">Suivant ▶</button>`;
    }
    
    html += '</div>';
    paginationContainer.innerHTML = html;
}

// Aller à une page
function goToPage(page) {
    currentPage = page;
    loadHistory(page);
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
            alert('Ajouté aux favoris !');
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

// Afficher une erreur
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    document.querySelector('.main-content').prepend(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}