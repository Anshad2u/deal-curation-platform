let token = localStorage.getItem(CONFIG.TOKEN_KEY);
let currentDeals = [];
let currentIndex = 0;

function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast toast-${type} show`;
    setTimeout(() => toast.classList.remove('show'), 3000);
}

async function apiCall(endpoint, options = {}) {
    const url = CONFIG.API_BASE + endpoint;
    const headers = {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
    };
    
    try {
        const response = await fetch(url, { ...options, headers });
        if (response.status === 401) {
            showPage('login');
            return null;
        }
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('API Error:', error);
        showToast('Connection failed. Check backend URL.', 'error');
        updateConnectionStatus(false);
        return null;
    }
}

function updateConnectionStatus(connected) {
    const status = document.getElementById('connectionStatus');
    if (connected) {
        status.innerHTML = '<span class="status-dot connected"></span><span class="status-text">Connected</span>';
    } else {
        status.innerHTML = '<span class="status-dot disconnected"></span><span class="status-text">Disconnected</span>';
    }
}

function showPage(page) {
    document.querySelectorAll('.page').forEach(p => p.style.display = 'none');
    document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
    
    if (page === 'login') {
        document.getElementById('loginPage').style.display = 'flex';
    } else {
        if (!token) {
            showPage('login');
            return;
        }
        document.getElementById(`${page}Page`).style.display = 'block';
        document.getElementById(`nav-${page}`).classList.add('active');
        
        if (page === 'dashboard') loadDashboard();
        if (page === 'scrapers') loadScrapers();
        if (page === 'deals') loadDeals();
        if (page === 'rate') loadRatingStats(); loadDealsToRate();
    }
}

document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    try {
        const response = await fetch(CONFIG.API_BASE + '/auth/login', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            token = data.access_token;
            localStorage.setItem(CONFIG.TOKEN_KEY, token);
            document.getElementById('userName').textContent = username;
            showPage('dashboard');
            showToast('Welcome back!', 'success');
            updateConnectionStatus(true);
        } else {
            document.getElementById('errorMsg').textContent = data.detail || 'Login failed';
        }
    } catch (error) {
        document.getElementById('errorMsg').textContent = 'Cannot connect to backend';
        updateConnectionStatus(false);
    }
});

async function loadDashboard() {
    const stats = await apiCall('/dashboard/stats');
    if (stats) {
        document.getElementById('totalDeals').textContent = stats.total_deals;
        document.getElementById('newDeals').textContent = stats.new_deals;
        document.getElementById('goodDeals').textContent = stats.good_deals;
        document.getElementById('totalStructured').textContent = stats.total_structured;
        updateConnectionStatus(true);
    }
    
    const sources = await apiCall('/dashboard/sources-status');
    if (sources) {
        const tbody = document.querySelector('#sourcesTable tbody');
        tbody.innerHTML = sources.map(s => `
            <tr>
                <td>${s.name}</td>
                <td>${s.type}</td>
                <td>${s.deal_count}</td>
                <td>${s.last_scraped ? new Date(s.last_scraped).toLocaleString() : 'Never'}</td>
            </tr>
        `).join('');
    }
}

async function loadScrapers() {
    const sources = await apiCall('/sources');
    if (sources) {
        const tbody = document.querySelector('#scrapersTable tbody');
        tbody.innerHTML = sources.map(s => `
            <tr>
                <td>${s.name}</td>
                <td>${s.type}</td>
                <td>${s.last_scraped ? new Date(s.last_scraped).toLocaleString() : 'Never'}</td>
                <td><button class="btn btn-primary" onclick="runScraper(${s.id}, '${s.name}')">🔍 Scrape</button></td>
            </tr>
        `).join('');
    }
}

async function runScraper(id, name) {
    const resultDiv = document.getElementById('scrapeResult');
    const contentDiv = document.getElementById('resultContent');
    
    resultDiv.style.display = 'block';
    contentDiv.innerHTML = '<p class="loading">Scraping ' + name + '...</p>';
    
    const result = await apiCall(`/sources/${id}/scrape`, { method: 'POST', body: '{}' });
    
    if (result) {
        if (result.success) {
            contentDiv.innerHTML = `
                <div class="alert alert-success">
                    <strong>Success!</strong><br>
                    Total: ${result.total_found} | New: ${result.new_deals} | Duplicates: ${result.duplicates}
                </div>
            `;
            loadScrapers();
        } else {
            contentDiv.innerHTML = `<div class="alert alert-error">Error: ${result.error}</div>`;
        }
    }
}

async function loadDeals() {
    const search = document.getElementById('searchInput')?.value || '';
    const category = document.getElementById('categoryFilter')?.value || '';
    
    let url = `/deals?limit=100`;
    if (search) url += `&search=${encodeURIComponent(search)}`;
    if (category) url += `&category=${category}`;
    
    const data = await apiCall(url);
    if (data) {
        document.getElementById('dealCount').textContent = data.total;
        const tbody = document.querySelector('#dealsTable tbody');
        tbody.innerHTML = data.deals.map(d => `
            <tr>
                <td><strong>${d.merchant_name}</strong></td>
                <td>${d.offer_title}</td>
                <td>${d.discount_value || 'N/A'}</td>
                <td><span class="badge">${d.category || 'other'}</span></td>
            </tr>
        `).join('') || '<tr><td colspan="4">No deals found</td></tr>';
    }
}

async function loadRatingStats() {
    const stats = await apiCall('/ratings/stats');
    if (stats) {
        document.getElementById('goodCount').textContent = stats.good;
        document.getElementById('mediocreCount').textContent = stats.mediocre;
        document.getElementById('badCount').textContent = stats.bad;
    }
}

async function loadDealsToRate() {
    const data = await apiCall('/ratings/pending?limit=20');
    if (data && data.deals.length > 0) {
        currentDeals = data.deals;
        currentIndex = 0;
        showDeal();
    } else {
        document.getElementById('dealContent').innerHTML = `
            <div style="text-align: center; padding: 40px;">
                <h3>All deals rated! 🎉</h3>
            </div>
        `;
    }
}

function showDeal() {
    if (currentIndex >= currentDeals.length) {
        loadDealsToRate();
        return;
    }
    
    const deal = currentDeals[currentIndex];
    document.getElementById('dealContent').innerHTML = `
        <div class="deal-card">
            <p style="color: #7f8c8d;">Deal ${currentIndex + 1} of ${currentDeals.length}</p>
            <h2>${deal.merchant_name}</h2>
            <p style="font-size: 18px;">${deal.offer_title}</p>
            <div class="deal-info">
                <div><strong>Discount:</strong> <span style="color: #27ae60;">${deal.discount_value || 'N/A'}</span></div>
                <div><strong>Category:</strong> <span class="badge">${deal.category || 'other'}</span></div>
            </div>
            ${deal.description ? `<p style="color: #7f8c8d; margin-top: 15px;">${deal.description}</p>` : ''}
            
            <textarea id="reasonInput" placeholder="Why this rating? (optional)" style="margin-top: 15px; width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;"></textarea>
            
            <div class="rating-buttons">
                <button class="rating-btn good" onclick="rateDeal(${deal.id}, 'good')">⭐ Good</button>
                <button class="rating-btn mediocre" onclick="rateDeal(${deal.id}, 'mediocre')">⭐⭐ Mediocre</button>
                <button class="rating-btn bad" onclick="rateDeal(${deal.id}, 'bad')">⭐⭐⭐ Bad</button>
            </div>
            <button class="btn btn-secondary" onclick="skipDeal()" style="margin-top: 10px;">Skip</button>
        </div>
    `;
}

async function rateDeal(dealId, quality) {
    const reason = document.getElementById('reasonInput')?.value || '';
    const result = await apiCall(`/ratings/deals/${dealId}/rate?quality_score=${quality}&reason=${encodeURIComponent(reason)}`, { method: 'POST', body: '{}' });
    
    if (result) {
        currentIndex++;
        loadRatingStats();
        showDeal();
    }
}

function skipDeal() {
    currentIndex++;
    showDeal();
}

// Check connection on load
async function checkConnection() {
    try {
        const response = await fetch(CONFIG.API_BASE.replace('/api', '/') + 'docs', { method: 'HEAD' });
        updateConnectionStatus(response.ok);
    } catch {
        updateConnectionStatus(false);
    }
}

// Initialize
checkConnection();
if (token) {
    document.getElementById('userName').textContent = 'User';
    showPage('dashboard');
} else {
    showPage('login');
}

// Add styles for toast and status
const style = document.createElement('style');
style.textContent = `
    .toast {
        position: fixed;
        bottom: 20px;
        right: 20px;
        padding: 15px 25px;
        background: #333;
        color: white;
        border-radius: 5px;
        display: none;
        z-index: 9999;
    }
    .toast.show { display: block; }
    .toast-success { background: #27ae60; }
    .toast-error { background: #e74c3c; }
    
    .connection-status {
        position: absolute;
        bottom: 20px;
        left: 20px;
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
    }
    .status-dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: #95a5a6;
    }
    .status-dot.connected { background: #27ae60; }
    .status-dot.disconnected { background: #e74c3c; }
    
    .alert-success { background: #d4edda; color: #155724; padding: 15px; border-radius: 5px; }
    .alert-error { background: #f8d7da; color: #721c24; padding: 15px; border-radius: 5px; }
    
    .deal-card { background: #f8f9fa; padding: 25px; border-radius: 8px; }
    .deal-info { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 15px 0; }
    
    .filters { display: flex; gap: 10px; }
    .filters input, .filters select { padding: 10px; border: 1px solid #ddd; border-radius: 5px; flex: 1; }
    
    #loginPage { display: flex; justify-content: center; align-items: center; min-height: 80vh; }
    .login-box { background: white; padding: 40px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
    .login-box h1 { text-align: center; margin-bottom: 30px; }
    .error { color: #e74c3c; text-align: center; margin-top: 15px; }
`;
document.head.appendChild(style);
