document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('.material-row');
    const pills = document.querySelectorAll('.filter-pill');
    const searchInput = document.getElementById('supplier-search'); // Mantengo tu ID del HTML
    const noResults = document.getElementById('no-results-materials');

    let currentFilter = 'all';

    function updateCounts() {
        const total = rows.length;
        const activos = [...rows].filter(r => r.dataset.status === 'Activo').length;
        const inactivos = [...rows].filter(r => r.dataset.status === 'Inactivo').length;
        
        if(document.getElementById('count-all')) document.getElementById('count-all').textContent = total;
        if(document.getElementById('count-active')) document.getElementById('count-active').textContent = activos;
        if(document.getElementById('count-inactive')) document.getElementById('count-inactive').textContent = inactivos;
    }

    function applyFilters() {
        const search = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        rows.forEach(row => {
            const status = row.dataset.status;
            const name = row.dataset.name;

            const matchFilter = (currentFilter === 'all' || status === currentFilter);
            const matchSearch = (!search || name.includes(search));

            if (matchFilter && matchSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Mostrar/Ocultar mensaje de no resultados
        if (noResults) {
            noResults.classList.toggle('hidden', visibleCount > 0);
        }
    }

    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            currentFilter = pill.dataset.filter;

            // Gestionar clases visuales de los botones
            pills.forEach(p => p.classList.remove('active-all', 'active-active', 'active-inactive'));
            
            if (currentFilter === 'all') pill.classList.add('active-all');
            else if (currentFilter === 'Activo') pill.classList.add('active-active');
            else if (currentFilter === 'Inactivo') pill.classList.add('active-inactive');

            applyFilters();
        });
    });

    searchInput.addEventListener('input', applyFilters);

    // Inicialización
    updateCounts();
    // Por defecto mostrar activos como en tu ejemplo de proveedores
    const activeBtn = document.querySelector('[data-filter="Activo"]');
    if (activeBtn) activeBtn.click();
});