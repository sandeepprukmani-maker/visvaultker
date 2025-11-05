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
    // Load saved settings from localStorage
    const savedMode = localStorage.getItem('browserMode') || 'headful';
    const savedEngine = localStorage.getItem('automationEngine') || 'browser_use';
    
    const headlessBtn = document.getElementById('headless-btn');
    const headfulBtn = document.getElementById('headful-btn');
    const browserUseBtn = document.getElementById('browser-use-btn');
    const playwrightMcpBtn = document.getElementById('playwright-mcp-btn');
    
    // Set initial states based on saved settings
    if (headlessBtn && headfulBtn) {
        if (savedMode === 'headless') {
            headlessBtn.classList.add('active');
            headfulBtn.classList.remove('active');
        } else {
            headfulBtn.classList.add('active');
            headlessBtn.classList.remove('active');
        }
        
        headlessBtn.addEventListener('click', () => {
            localStorage.setItem('browserMode', 'headless');
            headlessBtn.classList.add('active');
            headfulBtn.classList.remove('active');
        });
        
        headfulBtn.addEventListener('click', () => {
            localStorage.setItem('browserMode', 'headful');
            headfulBtn.classList.add('active');
            headlessBtn.classList.remove('active');
        });
    }
    
    if (browserUseBtn && playwrightMcpBtn) {
        if (savedEngine === 'playwright_mcp') {
            playwrightMcpBtn.classList.add('active');
            browserUseBtn.classList.remove('active');
        } else {
            browserUseBtn.classList.add('active');
            playwrightMcpBtn.classList.remove('active');
        }
        
        browserUseBtn.addEventListener('click', () => {
            localStorage.setItem('automationEngine', 'browser_use');
            browserUseBtn.classList.add('active');
            playwrightMcpBtn.classList.remove('active');
        });
        
        playwrightMcpBtn.addEventListener('click', () => {
            localStorage.setItem('automationEngine', 'playwright_mcp');
            playwrightMcpBtn.classList.add('active');
            browserUseBtn.classList.remove('active');
        });
    }
}

// Make function globally available for manual calls
window.detectClientEnvironment = detectClientEnvironment;
