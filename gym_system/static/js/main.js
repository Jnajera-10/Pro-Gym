// Colombia time display
function updateColombiaTime() {
    const now = new Date();
    const opts = { timeZone: 'America/Bogota', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false };
    const timeStr = now.toLocaleTimeString('es-CO', opts);
    const dateOpts = { timeZone: 'America/Bogota', day: '2-digit', month: '2-digit', year: 'numeric' };
    const dateStr = now.toLocaleDateString('es-CO', dateOpts);
    document.querySelectorAll('#colombiaTime, #footerTime').forEach(el => {
        if (el) el.textContent = `${dateStr} ${timeStr}`;
    });
}
updateColombiaTime();
setInterval(updateColombiaTime, 1000);

// Auto-dismiss alerts
document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => el.classList.remove('show'), 4000);
});

// Confirm delete buttons
document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', e => {
        if (!confirm(btn.dataset.confirm)) e.preventDefault();
    });
});

// ── Sidebar móvil ────────────────────────────────────
(function () {
    const sidebar  = document.getElementById('mainSidebar');
    const overlay  = document.getElementById('sidebarOverlay');
    const toggleBtn = document.getElementById('sidebarToggle');
    const closeBtn  = document.getElementById('sidebarClose');

    if (!sidebar) return;

    function openSidebar() {
        sidebar.classList.add('sidebar-open');
        if (overlay) overlay.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    function closeSidebar() {
        sidebar.classList.remove('sidebar-open');
        if (overlay) overlay.classList.remove('active');
        document.body.style.overflow = '';
    }

    if (toggleBtn) toggleBtn.addEventListener('click', openSidebar);
    if (closeBtn)  closeBtn.addEventListener('click', closeSidebar);
    if (overlay)   overlay.addEventListener('click', closeSidebar);

    // Cerrar con Escape
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape') closeSidebar();
    });

    // Cerrar automáticamente al hacer clic en un enlace del sidebar (navega a otra página)
    sidebar.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth < 768) closeSidebar();
        });
    });
})();
