/**
 * Credential Manager
 * Handles secure credential storage and management UI
 */

const credentialManager = {
    /**
     * Initialize the credential manager
     */
    init() {
        this.loadCredentials();
    },

    /**
     * Load and display all credentials
     */
    async loadCredentials() {
        try {
            const response = await fetch('/api/credentials');
            const data = await response.json();

            if (data.success) {
                this.renderCredentials(data.credentials);
            } else {
                this.showError('Failed to load credentials: ' + data.message);
            }
        } catch (error) {
            console.error('Error loading credentials:', error);
            this.showError('Failed to load credentials. Please try again.');
        }
    },

    /**
     * Render credentials list
     */
    renderCredentials(credentials) {
        const container = document.getElementById('credentials-list');

        if (credentials.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i data-feather="key"></i>
                    <h3 style="color: var(--text-primary); margin: 16px 0 8px 0;">No credentials stored yet</h3>
                    <p style="max-width: 400px; margin: 0 auto;">
                        Add your first credential to start using secure placeholders in your automation prompts.
                    </p>
                </div>
            `;
            feather.replace();
            return;
        }

        container.innerHTML = credentials.map(cred => `
            <div class="credential-card">
                <div class="credential-header">
                    <div>
                        <div class="credential-name">${this.escapeHtml(cred.name)}</div>
                        <div class="credential-placeholder">{{${this.escapeHtml(cred.name)}}}</div>
                    </div>
                    <div class="credential-actions">
                        <button class="btn btn-secondary btn-icon-only" 
                                onclick="credentialManager.deleteCredential(${cred.id}, '${this.escapeHtml(cred.name)}')"
                                title="Delete credential">
                            <i data-feather="trash-2"></i>
                        </button>
                    </div>
                </div>
                ${cred.service || cred.username || cred.description ? `
                    <div class="credential-info">
                        ${cred.service ? `
                            <div class="credential-info-item">
                                <div class="credential-info-label">Service</div>
                                <div class="credential-info-value">${this.escapeHtml(cred.service)}</div>
                            </div>
                        ` : ''}
                        ${cred.username ? `
                            <div class="credential-info-item">
                                <div class="credential-info-label">Username</div>
                                <div class="credential-info-value">${this.escapeHtml(cred.username)}</div>
                            </div>
                        ` : ''}
                        ${cred.description ? `
                            <div class="credential-info-item">
                                <div class="credential-info-label">Description</div>
                                <div class="credential-info-value">${this.escapeHtml(cred.description)}</div>
                            </div>
                        ` : ''}
                    </div>
                ` : ''}
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 0.85rem; color: var(--text-secondary);">
                    <i data-feather="clock" style="width: 14px; height: 14px;"></i>
                    Created: ${new Date(cred.created_at).toLocaleString()}
                </div>
            </div>
        `).join('');

        feather.replace();
    },

    /**
     * Show the add credential modal
     */
    showAddCredentialModal() {
        document.getElementById('add-credential-modal').style.display = 'flex';
        document.getElementById('add-credential-form').reset();
        document.getElementById('credential-name').focus();
    },

    /**
     * Close the add credential modal
     */
    closeAddCredentialModal() {
        document.getElementById('add-credential-modal').style.display = 'none';
    },

    /**
     * Add a new credential
     */
    async addCredential(event) {
        event.preventDefault();

        const name = document.getElementById('credential-name').value.trim();
        const service = document.getElementById('credential-service').value.trim();
        const username = document.getElementById('credential-username').value.trim();
        const value = document.getElementById('credential-value').value.trim();
        const description = document.getElementById('credential-description').value.trim();

        if (!name || !value) {
            this.showError('Name and password/secret are required');
            return;
        }

        try {
            const response = await fetch('/api/credentials', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name,
                    service,
                    username,
                    value,
                    description
                })
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Credential added successfully');
                this.closeAddCredentialModal();
                this.loadCredentials();
            } else {
                this.showError(data.message || 'Failed to add credential');
            }
        } catch (error) {
            console.error('Error adding credential:', error);
            this.showError('Failed to add credential. Please try again.');
        }
    },

    /**
     * Delete a credential
     */
    async deleteCredential(id, name) {
        if (!confirm(`Are you sure you want to delete the credential "${name}"?\n\nThis action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/credentials/${id}`, {
                method: 'DELETE'
            });

            const data = await response.json();

            if (data.success) {
                this.showSuccess('Credential deleted successfully');
                this.loadCredentials();
            } else {
                this.showError(data.message || 'Failed to delete credential');
            }
        } catch (error) {
            console.error('Error deleting credential:', error);
            this.showError('Failed to delete credential. Please try again.');
        }
    },

    /**
     * Show error message
     */
    showError(message) {
        alert('Error: ' + message);
    },

    /**
     * Show success message
     */
    showSuccess(message) {
        // Simple alert for now - can be enhanced with a toast notification
        alert(message);
    },

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    credentialManager.init();

    // Close modal when clicking outside
    document.getElementById('add-credential-modal')?.addEventListener('click', function(e) {
        if (e.target === this) {
            credentialManager.closeAddCredentialModal();
        }
    });

    // Handle escape key to close modal
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            credentialManager.closeAddCredentialModal();
        }
    });
});
