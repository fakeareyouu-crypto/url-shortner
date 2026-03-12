const API_BASE = window.API_BASE || 'http://localhost:5000';

function token() { return localStorage.getItem('token'); }
function setMessage(text, isError = false) {
  const el = document.getElementById('message');
  if (!el) return;
  el.textContent = text;
  el.className = `mt-3 text-sm ${isError ? 'text-rose-400' : 'text-emerald-400'}`;
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token()) headers.Authorization = `Bearer ${token()}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || 'Request failed');
  return data;
}

const signupBtn = document.getElementById('signupBtn');
if (signupBtn) {
  signupBtn.onclick = async () => {
    try {
      const data = await api('/api/signup', { method: 'POST', body: JSON.stringify({
        username: document.getElementById('username').value,
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
      })});
      localStorage.setItem('token', data.token);
      setMessage('Signup successful. Redirecting...');
      setTimeout(() => location.href = 'dashboard.html', 600);
    } catch (e) { setMessage(e.message, true); }
  };
}

const loginBtn = document.getElementById('loginBtn');
if (loginBtn) {
  loginBtn.onclick = async () => {
    try {
      const data = await api('/api/login', { method: 'POST', body: JSON.stringify({
        email: document.getElementById('email').value,
        password: document.getElementById('password').value,
      })});
      localStorage.setItem('token', data.token);
      setMessage('Login successful. Redirecting...');
      setTimeout(() => location.href = 'dashboard.html', 600);
    } catch (e) { setMessage(e.message, true); }
  };
}

const shortenBtn = document.getElementById('shortenBtn');
if (shortenBtn) {
  shortenBtn.onclick = async () => {
    try {
      const payload = {
        original_url: document.getElementById('originalUrl').value,
        custom_alias: document.getElementById('customAlias').value,
        expire_hours: document.getElementById('expireHours').value || null,
      };
      const data = await api('/api/shorten', { method: 'POST', body: JSON.stringify(payload) });
      document.getElementById('result').classList.remove('hidden');
      document.getElementById('shortUrl').textContent = data.short_url;
      document.getElementById('shortUrl').href = data.short_url;
      document.getElementById('qrCode').src = data.qr_code;
      setMessage('Short link created!');
    } catch (e) { setMessage(e.message, true); }
  };
}

const copyBtn = document.getElementById('copyBtn');
if (copyBtn) {
  copyBtn.onclick = async () => {
    const url = document.getElementById('shortUrl').textContent;
    await navigator.clipboard.writeText(url);
    setMessage('Copied to clipboard!');
  };
}

const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
  logoutBtn.onclick = () => {
    localStorage.removeItem('token');
    location.href = 'login.html';
  };
}

async function loadDashboard() {
  const linksTable = document.getElementById('linksTable');
  if (!linksTable) return;

  try {
    const data = await api('/api/dashboard');
    document.getElementById('totalLinks').textContent = data.total_links;
    document.getElementById('totalClicks').textContent = data.total_clicks;

    linksTable.innerHTML = '';
    data.links.forEach(link => {
      const shortUrl = `${API_BASE}/r/${link.short_code}`;
      const row = document.createElement('div');
      row.className = 'bg-slate-800 border border-slate-700 rounded p-3';
      row.innerHTML = `
        <p class="break-all text-sm">${link.original_url}</p>
        <p class="text-indigo-300 text-sm mt-1">${shortUrl}</p>
        <p class="text-slate-400 text-xs mt-1">Clicks: ${link.clicks}</p>
        <div class="mt-2 flex gap-2">
          <button class="copyLink bg-emerald-600 px-2 py-1 rounded text-xs" data-url="${shortUrl}">Copy</button>
          <button class="deleteLink bg-rose-600 px-2 py-1 rounded text-xs" data-id="${link.id}">Delete</button>
        </div>
      `;
      linksTable.appendChild(row);
    });

    linksTable.querySelectorAll('.copyLink').forEach(btn => {
      btn.onclick = () => navigator.clipboard.writeText(btn.dataset.url);
    });
    linksTable.querySelectorAll('.deleteLink').forEach(btn => {
      btn.onclick = async () => {
        await api(`/api/link/${btn.dataset.id}`, { method: 'DELETE' });
        loadDashboard();
      };
    });
  } catch (e) {
    linksTable.innerHTML = `<p class="text-rose-400">${e.message}</p>`;
  }
}
loadDashboard();

async function loadAdmin() {
  const users = document.getElementById('users');
  if (!users) return;
  try {
    const data = await api('/api/admin/stats');
    document.getElementById('users').textContent = data.total_users;
    document.getElementById('links').textContent = data.total_links;
    document.getElementById('clicks').textContent = data.total_clicks;
    const topLinks = document.getElementById('topLinks');
    topLinks.innerHTML = data.top_links.map(l => `<div class="bg-slate-800 p-2 rounded text-sm">/${l.short_code} — ${l.clicks} clicks</div>`).join('');
  } catch (e) {
    document.getElementById('topLinks').innerHTML = `<p class="text-rose-400">${e.message}</p>`;
  }
}
loadAdmin();
