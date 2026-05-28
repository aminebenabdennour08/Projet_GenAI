// ============================================================
// dashboard.js - Tableau de bord
// ============================================================

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
    
    loadDashboard();
    
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

// Charger le tableau de bord
async function loadDashboard() {
    try {
        // Charger les statistiques
        const statsResponse = await fetch('/api/user/stats', {
            credentials: 'include'
        });
        const statsData = await statsResponse.json();
        
        if (statsData.success) {
            document.getElementById('totalGenerations').textContent = statsData.stats.total_generations || 0;
            displayTopStyles(statsData.stats.top_styles);
        }
        
        // Charger les favoris
        const favResponse = await fetch('/api/user/favorites', {
            credentials: 'include'
        });
        const favData = await favResponse.json();
        
        if (favData.success) {
            document.getElementById('favoritesCount').textContent = favData.favorites.length;
            displayFavorites(favData.favorites);
        }
        
    } catch (error) {
        console.error('Erreur chargement dashboard:', error);
        showError('Impossible de charger les données');
    }
}

// Afficher les styles populaires
function displayTopStyles(topStyles) {
    const container = document.getElementById('topStyles');
    
    if (!container) return;
    
    if (!topStyles || topStyles.length === 0) {
        container.innerHTML = '<p class="no-data">Aucune donnée disponible</p>';
        return;
    }
    
    let html = '';
    topStyles.forEach(style => {
        html += `
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <div class="stat-number">${style.count}</div>
                <div class="stat-label">${style.style_name || 'Style'}</div>
            </div>
        `;
    });
    container.innerHTML = html;
}

// Afficher les favoris
function displayFavorites(favorites) {
    const container = document.getElementById('favoritesList');
    
    if (!container) return;
    
    if (!favorites || favorites.length === 0) {
        container.innerHTML = '<p class="no-data">Aucun favori pour le moment</p>';
        return;
    }
    
    let html = '<div class="favorites-grid">';
    favorites.forEach(fav => {
        html += `
            <div class="favorite-card">
                <img src="/avatars/${fav.generated_filename}" alt="Avatar" onerror="this.src='/img/placeholder.png'">
                <div class="favorite-info">
                    <div class="favorite-style">${fav.style_name || 'Avatar'}</div>
                    <div class="favorite-date">${new Date(fav.added_date).toLocaleDateString()}</div>
                    <button onclick="removeFavorite(${fav.id})" class="btn-small">❤️ Retirer</button>
                </div>
            </div>
        `;
    });
    html += '</div>';
    container.innerHTML = html;
}

// Retirer des favoris
async function removeFavorite(favoriteId) {
    try {
        const response = await fetch('/api/user/favorites', {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ favorite_id: favoriteId }),
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            loadDashboard(); // Recharger
        } else {
            alert('Erreur: ' + (data.error || 'Impossible de retirer des favoris'));
        }
    } catch (error) {
        alert('Erreur: ' + error.message);
    }
}

// Afficher une erreur
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    document.querySelector('.main-content').prepend(errorDiv);
    setTimeout(() => errorDiv.remove(), 5000);
}