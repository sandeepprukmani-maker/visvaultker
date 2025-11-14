// Initialize detection when script loads
detectClientEnvironment();

// Also initialize on DOMContentLoaded for direct page loads
document.addEventListener('DOMContentLoaded', () => {
    detectClientEnvironment();
    initializeSettings();
});

function detectClientEnvironment() {
    const userAgent = navigator.userAgent;
    const platform = navigator.platform;
    
    // Detect Operating System
    let os = 'Unknown';
    if (platform.indexOf('Win') !== -1) {
        os = 'Windows';
    } else if (platform.indexOf('Mac') !== -1) {
        os = 'macOS';
    } else if (platform.indexOf('Linux') !== -1) {
        os = 'Linux';
    } else if (/Android/.test(userAgent)) {
        os = 'Android';
    } else if (/iPhone|iPad|iPod/.test(userAgent)) {
        os = 'iOS';
    }
    
    // Detect Browser
    let browser = 'Unknown';
    if (/Edg/.test(userAgent)) {
        browser = 'Microsoft Edge';
    } else if (/Chrome/.test(userAgent) && !/Edg/.test(userAgent)) {
        browser = 'Google Chrome';
    } else if (/Safari/.test(userAgent) && !/Chrome/.test(userAgent)) {
        browser = 'Safari';
    } else if (/Firefox/.test(userAgent)) {
        browser = 'Firefox';
    } else if (/MSIE|Trident/.test(userAgent)) {
        browser = 'Internet Explorer';
    }
    
    // Update the page
    const osElement = document.getElementById('client-os');
    const browserElement = document.getElementById('client-browser');
    
    if (osElement) {
        osElement.textContent = os;
    }
    
    if (browserElement) {
        browserElement.textContent = browser;
    }
}

function initializeSettings() {
    const headlessBtn = document.getElementById('headless-btn');
    const headfulBtn = document.getElementById('headful-btn');
    const browserUseBtn = document.getElementById('browser-use-btn');
    const playwrightMcpBtn = document.getElementById('playwright-mcp-btn');
    
    // Load saved settings or use defaults
    const savedMode = localStorage.getItem('automation_mode') || 'headful';
    const savedEngine = localStorage.getItem('automation_engine') || 'browser_use';
    
    // Set initial button states
    if (savedMode === 'headless') {
        headlessBtn.classList.add('active');
        headfulBtn.classList.remove('active');
    } else {
        headfulBtn.classList.add('active');
        headlessBtn.classList.remove('active');
    }
    
    if (savedEngine === 'playwright_mcp') {
        playwrightMcpBtn.classList.add('active');
        browserUseBtn.classList.remove('active');
    } else {
        browserUseBtn.classList.add('active');
        playwrightMcpBtn.classList.remove('active');
    }
    
    // Add event listeners for mode toggle
    if (headlessBtn) {
        headlessBtn.addEventListener('click', () => {
            localStorage.setItem('automation_mode', 'headless');
            headlessBtn.classList.add('active');
            headfulBtn.classList.remove('active');
            showSavedNotification();
        });
    }
    
    if (headfulBtn) {
        headfulBtn.addEventListener('click', () => {
            localStorage.setItem('automation_mode', 'headful');
            headfulBtn.classList.add('active');
            headlessBtn.classList.remove('active');
            showSavedNotification();
        });
    }
    
    // Add event listeners for engine toggle
    if (browserUseBtn) {
        browserUseBtn.addEventListener('click', () => {
            localStorage.setItem('automation_engine', 'browser_use');
            browserUseBtn.classList.add('active');
            playwrightMcpBtn.classList.remove('active');
            showSavedNotification();
        });
    }
    
    if (playwrightMcpBtn) {
        playwrightMcpBtn.addEventListener('click', () => {
            localStorage.setItem('automation_engine', 'playwright_mcp');
            playwrightMcpBtn.classList.add('active');
            browserUseBtn.classList.remove('active');
            showSavedNotification();
        });
    }
}

function showSavedNotification() {
    // Simple visual feedback that settings were saved
    const notification = document.createElement('div');
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; background: var(--success-bg); color: var(--success-text); padding: 12px 20px; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); z-index: 10000; font-weight: 500;';
    notification.textContent = '✓ Settings saved';
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transition = 'opacity 0.3s';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 2000);
}

// Make function globally available for manual calls
window.detectClientEnvironment = detectClientEnvironment;
