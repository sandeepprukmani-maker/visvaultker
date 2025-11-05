// Crawler.js - Site Crawler & Knowledge Base Management

// Load credentials for dropdown
async function loadCredentials() {
    try {
        const response = await fetch('/api/credentials');
        const data = await response.json();
        
        if (data.success) {
            const select = document.getElementById('credentialId');
            // Keep the "None" option
            select.innerHTML = '<option value="">None - Public site</option>';
            
            data.credentials.forEach(cred => {
                const option = document.createElement('option');
                option.value = cred.id;
                option.textContent = `${cred.name} (${cred.service || cred.url || 'No service'})`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Failed to load credentials:', error);
    }
}

// Create new crawl
document.getElementById('createCrawlForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = {
        name: formData.get('name'),
        start_url: formData.get('start_url'),
        credential_id: formData.get('credential_id') ? parseInt(formData.get('credential_id')) : null,
        max_pages: parseInt(formData.get('max_pages')),
        max_depth: parseInt(formData.get('max_depth')),
        same_domain_only: formData.get('same_domain_only') === 'on',
        auto_start: true
    };
    
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<span class="btn-icon">⏳</span> Creating...';
    
    try {
        const response = await fetch('/api/crawls', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ Crawl created and started successfully!', 'success');
            e.target.reset();
            loadCrawls();
        } else {
            showNotification(`❌ Failed to create crawl: ${result.message}`, 'error');
        }
    } catch (error) {
        showNotification(`❌ Error: ${error.message}`, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<span class="btn-icon">🕷️</span> Create & Start Crawl';
    }
});

// Load crawls list
async function loadCrawls() {
    const container = document.getElementById('crawlsList');
    container.innerHTML = '<p class="text-muted">Loading crawls...</p>';
    
    try {
        const response = await fetch('/api/crawls');
        const data = await response.json();
        
        if (data.success && data.crawls.length > 0) {
            container.innerHTML = data.crawls.map(crawl => `
                <div class="crawl-item">
                    <div class="crawl-header">
                        <div class="crawl-title">${escapeHtml(crawl.name)}</div>
                        <span class="crawl-status status-${crawl.status}">${crawl.status.toUpperCase()}</span>
                    </div>
                    
                    <a href="${escapeHtml(crawl.start_url)}" target="_blank" class="crawl-url">${escapeHtml(crawl.start_url)}</a>
                    
                    <div class="crawl-meta">
                        <span>📄 ${crawl.pages_crawled}/${crawl.max_pages} pages</span>
                        <span>📊 Depth: ${crawl.max_depth}</span>
                        <span>📅 ${new Date(crawl.created_at).toLocaleDateString()}</span>
                    </div>
                    
                    ${crawl.status === 'running' ? `
                        <div class="progress-bar">
                            <div class="progress-fill" style="width: ${crawl.progress}%"></div>
                        </div>
                        <small class="text-muted">${crawl.progress}% complete</small>
                    ` : ''}
                    
                    <div class="crawl-actions">
                        ${crawl.status === 'completed' ? `
                            <button class="btn btn-sm btn-primary" onclick="viewKnowledge(${crawl.id})">
                                <span class="btn-icon">🧠</span> View Knowledge
                            </button>
                        ` : ''}
                        ${crawl.status === 'pending' ? `
                            <button class="btn btn-sm btn-primary" onclick="startCrawl(${crawl.id})">
                                <span class="btn-icon">▶️</span> Start
                            </button>
                        ` : ''}
                        ${crawl.status !== 'running' ? `
                            <button class="btn btn-sm btn-danger" onclick="deleteCrawl(${crawl.id})">
                                <span class="btn-icon">🗑️</span> Delete
                            </button>
                        ` : ''}
                    </div>
                </div>
            `).join('');
        } else {
            container.innerHTML = '<p class="text-muted">No crawls yet. Create your first site crawl above!</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="text-danger">Error loading crawls: ${error.message}</p>`;
    }
}

// Start a crawl
async function startCrawl(crawlId) {
    try {
        const response = await fetch(`/api/crawls/${crawlId}/start`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ Crawl started!', 'success');
            loadCrawls();
        } else {
            showNotification(`❌ Failed to start: ${result.message}`, 'error');
        }
    } catch (error) {
        showNotification(`❌ Error: ${error.message}`, 'error');
    }
}

// View knowledge
async function viewKnowledge(crawlId) {
    const modal = document.getElementById('knowledgeModal');
    const content = document.getElementById('knowledgeContent');
    
    modal.classList.add('show');
    content.textContent = 'Loading knowledge...';
    
    try {
        const response = await fetch(`/api/crawls/${crawlId}/knowledge`);
        const data = await response.json();
        
        if (data.success) {
            content.textContent = data.knowledge_summary;
        } else {
            content.textContent = `Error: ${data.error}`;
        }
    } catch (error) {
        content.textContent = `Error: ${error.message}`;
    }
}

// Close knowledge modal
function closeKnowledgeModal() {
    document.getElementById('knowledgeModal').classList.remove('show');
}

// Delete crawl
async function deleteCrawl(crawlId) {
    if (!confirm('Are you sure you want to delete this crawl? This will remove all crawled data and knowledge.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/crawls/${crawlId}`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('✅ Crawl deleted', 'success');
            loadCrawls();
        } else {
            showNotification(`❌ Failed to delete: ${result.message}`, 'error');
        }
    } catch (error) {
        showNotification(`❌ Error: ${error.message}`, 'error');
    }
}

// Notification helper
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 4px;
        z-index: 10000;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        animation: slideIn 0.3s ease;
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// HTML escape helper
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Auto-refresh running crawls
setInterval(() => {
    const runningCrawls = document.querySelectorAll('.status-running');
    if (runningCrawls.length > 0) {
        loadCrawls();
    }
}, 5000);

// Close modal on outside click
document.getElementById('knowledgeModal')?.addEventListener('click', (e) => {
    if (e.target.id === 'knowledgeModal') {
        closeKnowledgeModal();
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadCredentials();
    loadCrawls();
});
