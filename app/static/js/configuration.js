// Initialize detection when script loads
detectClientEnvironment();

// Also initialize on DOMContentLoaded for direct page loads
document.addEventListener('DOMContentLoaded', () => {
    detectClientEnvironment();
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

// Make function globally available for manual calls
window.detectClientEnvironment = detectClientEnvironment;
