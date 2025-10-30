let credentials = [];
let apiKey = null;

// Load credentials on page load
document.addEventListener('DOMContentLoaded', () => {
    loadConfig();
});

async function loadConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            apiKey = config.api_key;
        }
    } catch (error) {
        console.error('Failed to load config:', error);
    }
    loadCredentials();
}

async function loadCredentials() {
    try {
        const response = await fetch('/api/credentials', {
            headers: {
                ...(apiKey ? {'X-API-Key': apiKey} : {})
            }
        });
        if (response.ok) {
            credentials = await response.json();
            renderCredentials();
        }
    } catch (error) {
        console.error('Failed to load credentials:', error);
    }
}

function renderCredentials() {
    const container = document.getElementById('credentials-list');
    
    if (credentials.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i data-feather="key" style="width: 48px; height: 48px; margin-bottom: 16px; opacity: 0.5;"></i>
                <div>No credentials stored yet</div>
                <p style="margin-top: 8px; color: var(--text-secondary); font-size: 0.9rem;">
                    Click "Add New Site" to store your first credential
                </p>
            </div>`;
        feather.replace();
        return;
    }
    
    container.innerHTML = credentials.map(cred => `
        <div class="credential-item" style="border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: start;">
                <div style="flex: 1;">
                    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                        <h3 style="margin: 0; color: var(--primary);">${escapeHtml(cred.site_name)}</h3>
                        <span style="background: var(--primary-bg); color: var(--primary); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600;">
                            ACTIVE
                        </span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem; margin-bottom: 4px;">
                        <i data-feather="link" style="width: 14px; height: 14px;"></i>
                        <a href="${escapeHtml(cred.url)}" target="_blank" style="color: var(--text-secondary); text-decoration: none;">
                            ${escapeHtml(cred.url)}
                        </a>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 0.9rem;">
                        <i data-feather="user" style="width: 14px; height: 14px;"></i>
                        ${escapeHtml(cred.username)}
                    </div>
                    ${cred.keywords ? `
                        <div style="margin-top: 8px;">
                            ${cred.keywords.split(',').map(k => `
                                <span style="background: var(--panel-bg); padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; margin-right: 4px;">
                                    ${escapeHtml(k.trim())}
                                </span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
                <div style="display: flex; gap: 8px;">
                    <button class="icon-button" onclick="editSite(${cred.id})" title="Edit">
                        <i data-feather="edit-2"></i>
                    </button>
                    <button class="icon-button" onclick="deleteSite(${cred.id})" title="Delete" style="color: var(--error-text);">
                        <i data-feather="trash-2"></i>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
    
    feather.replace();
}

function showAddSiteModal() {
    document.getElementById('modal-title').textContent = 'Add New Site';
    document.getElementById('site-form').reset();
    document.getElementById('site-id').value = '';
    document.getElementById('site-modal').style.display = 'flex';
}

function closeSiteModal() {
    document.getElementById('site-modal').style.display = 'none';
}

function editSite(id) {
    const cred = credentials.find(c => c.id === id);
    if (!cred) return;
    
    document.getElementById('modal-title').textContent = 'Edit Site';
    document.getElementById('site-id').value = cred.id;
    document.getElementById('site-name').value = cred.site_name;
    document.getElementById('site-url').value = cred.url;
    document.getElementById('site-username').value = cred.username;
    document.getElementById('site-password').value = '';
    document.getElementById('site-keywords').value = cred.keywords || '';
    
    document.getElementById('site-modal').style.display = 'flex';
}

async function saveSite(event) {
    event.preventDefault();
    
    const id = document.getElementById('site-id').value;
    const data = {
        site_name: document.getElementById('site-name').value.toLowerCase().trim(),
        url: document.getElementById('site-url').value.trim(),
        username: document.getElementById('site-username').value.trim(),
        password: document.getElementById('site-password').value,
        keywords: document.getElementById('site-keywords').value.trim()
    };
    
    try {
        const url = id ? `/api/credentials/${id}` : '/api/credentials';
        const method = id ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                ...(apiKey ? {'X-API-Key': apiKey} : {})
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeSiteModal();
            await loadCredentials();
            showNotification(id ? 'Credential updated successfully' : 'Credential saved successfully', 'success');
        } else {
            const error = await response.json();
            showNotification(error.error || 'Failed to save credential', 'error');
        }
    } catch (error) {
        console.error('Failed to save credential:', error);
        showNotification('Failed to save credential', 'error');
    }
}

async function deleteSite(id) {
    if (!confirm('Are you sure you want to delete this credential?')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/credentials/${id}`, {
            method: 'DELETE',
            headers: {
                ...(apiKey ? {'X-API-Key': apiKey} : {})
            }
        });
        
        if (response.ok) {
            await loadCredentials();
            showNotification('Credential deleted successfully', 'success');
        } else {
            showNotification('Failed to delete credential', 'error');
        }
    } catch (error) {
        console.error('Failed to delete credential:', error);
        showNotification('Failed to delete credential', 'error');
    }
}

function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 24px;
        right: 24px;
        padding: 16px 24px;
        background: ${type === 'success' ? 'var(--success-bg)' : 'var(--error-bg)'};
        color: ${type === 'success' ? 'var(--success-text)' : 'var(--error-text)'};
        border: 1px solid ${type === 'success' ? 'var(--success-border)' : 'var(--error-border)'};
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
    `;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
