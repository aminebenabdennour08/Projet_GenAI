// ============================================================
// auth.js - Gestion de l'authentification
// ============================================================

const AUTH_TOKEN_KEY = 'session_token';
const USER_KEY = 'user_data';

class Auth {
    constructor() {
        this.token = localStorage.getItem(AUTH_TOKEN_KEY);
        this.user = null;
    }
    
    isAuthenticated() {
        return !!this.token;
    }
    
    async login(username, password) {
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.token = data.session_token;
                this.user = {
                    id: data.user_id,
                    username: data.username,
                    email: data.email
                };
                localStorage.setItem(AUTH_TOKEN_KEY, this.token);
                localStorage.setItem(USER_KEY, JSON.stringify(this.user));
                return { success: true };
            }
            
            return { success: false, error: data.error };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
    
    async logout() {
        if (this.token) {
            await fetch('/api/logout', {
                method: 'POST',
                headers: { 'Authorization': this.token }
            });
        }
        
        this.token = null;
        this.user = null;
        localStorage.removeItem(AUTH_TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        
        window.location.href = '/login.html';
    }
    
    getToken() {
        return this.token;
    }
    
    getUser() {
        if (!this.user && localStorage.getItem(USER_KEY)) {
            this.user = JSON.parse(localStorage.getItem(USER_KEY));
        }
        return this.user;
    }
    
    async checkSession() {
        if (!this.token) return false;
        
        try {
            const response = await fetch('/api/user/profile', {
                headers: { 'Authorization': this.token }
            });
            const data = await response.json();
            return data.success;
        } catch {
            return false;
        }
    }
}

// Instance globale
const auth = new Auth();

// Vérifier l'authentification sur chaque page
async function requireAuth() {
    if (!auth.isAuthenticated() || !(await auth.checkSession())) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

// Initialiser l'interface utilisateur
function initUserInterface() {
    const user = auth.getUser();
    if (user) {
        const userElements = document.querySelectorAll('.user-name');
        userElements.forEach(el => el.textContent = user.username);
        
        const logoutBtns = document.querySelectorAll('.logout-btn');
        logoutBtns.forEach(btn => {
            btn.addEventListener('click', () => auth.logout());
        });
    }
}

// Exporter pour utilisation
window.auth = auth;
window.requireAuth = requireAuth;
window.initUserInterface = initUserInterface;