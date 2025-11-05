// Theme handling
function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeButton(savedTheme);
}

function updateThemeButton(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    
    if (themeToggle && themeIcon && themeText) {
        if (theme === 'light') {
            themeIcon.setAttribute('data-feather', 'moon');
            themeText.textContent = 'Dark';
        } else {
            themeIcon.setAttribute('data-feather', 'sun');
            themeText.textContent = 'Light';
        }
        // Re-render feather icons
        if (typeof feather !== 'undefined') {
            feather.replace();
        }
    }
}

function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    
    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeButton(newTheme);
}

// Initialize theme immediately
initializeTheme();

// Navigation and theme handling
document.addEventListener('DOMContentLoaded', () => {
    updateActiveNav();
    initializeTheme();
    
    // Add theme toggle listener
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
});

function updateActiveNav() {
    const currentPath = window.location.pathname;
    const navItems = document.querySelectorAll('.nav-item');
    
    navItems.forEach(item => {
        const href = item.getAttribute('href');
        item.classList.remove('active');
        if (href === currentPath || (currentPath === '/' && href === '/')) {
            item.classList.add('active');
        }
    });
}
