document.addEventListener('DOMContentLoaded', () => {
    updateActiveNav();
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
