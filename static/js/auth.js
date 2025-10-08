// Authentication JavaScript
const AUTH_API = {
    login: '/api/auth/login/',
    register: '/api/auth/register/',
    logout: '/api/auth/logout/',
    profile: '/api/auth/profile/',
    stats: '/api/users/me/stats/'
};

// Check if user is logged in
function isAuthenticated() {
    return localStorage.getItem('access_token') !== null;
}

// Get current user
function getCurrentUser() {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
}

// Update UI based on auth status
function updateAuthUI() {
    const authSection = document.getElementById('auth-section');
    const userSection = document.getElementById('user-section');
    const uploadSection = document.getElementById('upload-section');
    const uploadLoginMsg = document.getElementById('upload-login-msg');
    const dashboardBtn = document.getElementById('dashboard-btn');
    const roleBadge = document.getElementById('role-badge');

    if (isAuthenticated()) {
        const user = getCurrentUser();

        // Hide auth buttons, show user section
        if (authSection) authSection.style.display = 'none';
        if (userSection) userSection.style.display = 'flex';

        // Set username
        const userNameEl = document.getElementById('user-name');
        if (userNameEl) userNameEl.textContent = user.username;

        // Set role badge
        if (roleBadge) {
            if (user.is_admin) {
                roleBadge.className = 'role-badge admin';
                roleBadge.innerHTML = '👑 Admin';
            } else {
                roleBadge.className = 'role-badge student';
                roleBadge.innerHTML = '🎓 Student';
            }
        }

        // Show upload section for authenticated users
        if (uploadSection) uploadSection.style.display = 'block';
        if (uploadLoginMsg) uploadLoginMsg.style.display = 'none';

        // Show dashboard button only for admins
        if (dashboardBtn && user.is_admin) {
            dashboardBtn.style.display = 'inline-flex';
        }
    } else {
        // Show auth buttons, hide user section
        if (authSection) authSection.style.display = 'flex';
        if (userSection) userSection.style.display = 'none';

        // Hide upload section for anonymous users
        if (uploadSection) uploadSection.style.display = 'none';
        if (uploadLoginMsg) uploadLoginMsg.style.display = 'block';
    }
}

// Refresh access token
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;

    try {
        const response = await fetch('/api/auth/token/refresh/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ refresh: refreshToken })
        });

        if (response.ok) {
            const data = await response.json();
            localStorage.setItem('access_token', data.access);
            return true;
        }
    } catch (error) {
        console.error('Token refresh failed:', error);
    }

    return false;
}

// API call with auth
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('access_token');

    const defaultHeaders = {
        'Content-Type': 'application/json',
    };

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };

    let response = await fetch(url, config);

    // If token expired, try to refresh
    if (response.status === 401) {
        const refreshed = await refreshAccessToken();
        if (refreshed) {
            // Retry with new token
            const newToken = localStorage.getItem('access_token');
            config.headers['Authorization'] = `Bearer ${newToken}`;
            response = await fetch(url, config);
        } else {
            // Refresh failed, logout
            logout();
            window.location.href = '/api/auth/login-page/';
        }
    }

    return response;
}

// Logout function
async function logout() {
    const refreshToken = localStorage.getItem('refresh_token');
    const accessToken = localStorage.getItem('access_token');

    if (refreshToken && accessToken) {
        try {
            await fetch(AUTH_API.logout, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${accessToken}`
                },
                body: JSON.stringify({ refresh: refreshToken })
            });
        } catch (error) {
            console.error('Logout error:', error);
        }
    }

    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');

    window.location.href = '/api/';
}

// Initialize auth UI on page load
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();

    // Login button
    const loginBtn = document.getElementById('login-btn');
    if (loginBtn) {
        loginBtn.addEventListener('click', () => {
            window.location.href = '/api/auth/login-page/';
        });
    }

    // Register button
    const registerBtn = document.getElementById('register-btn');
    if (registerBtn) {
        registerBtn.addEventListener('click', () => {
            window.location.href = '/api/auth/register-page/';
        });
    }

    // Logout button
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }

    // Dashboard button
    const dashboardBtn = document.getElementById('dashboard-btn');
    if (dashboardBtn) {
        dashboardBtn.addEventListener('click', () => {
            window.location.href = '/api/developer/';
        });
    }

    // Stats button
    const statsBtn = document.getElementById('stats-btn');
    if (statsBtn) {
        statsBtn.addEventListener('click', showStats);
    }
});

// Show user stats modal
async function showStats() {
    const modal = document.getElementById('stats-modal');
    if (!modal) return;

    modal.style.display = 'block';

    try {
        const response = await authenticatedFetch(AUTH_API.stats);
        if (response.ok) {
            const data = await response.json();

            document.getElementById('stat-queries').textContent = data.statistics.total_queries;
            document.getElementById('stat-tokens').textContent = data.statistics.total_tokens.toLocaleString();
            document.getElementById('stat-cost').textContent = `$${parseFloat(data.statistics.total_cost_usd).toFixed(4)}`;
            document.getElementById('stat-time').textContent = `${data.statistics.avg_response_time_ms} ms`;
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Close modal
document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('stats-modal');
    if (modal) {
        const closeBtn = modal.querySelector('.close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                modal.style.display = 'none';
            });
        }

        window.addEventListener('click', (event) => {
            if (event.target === modal) {
                modal.style.display = 'none';
            }
        });
    }
});
