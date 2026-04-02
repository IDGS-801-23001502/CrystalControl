document.addEventListener('DOMContentLoaded', () => {
    const rows = document.querySelectorAll('.material-row');
    const pills = document.querySelectorAll('.filter-pill');
    const searchInput = document.getElementById('material-search');
    const noResults = document.getElementById('no-results-materials');

    let currentFilter = 'all';

    function updateCounts() {
        const total = rows.length;
        // Trim y LowerCase para evitar errores de espacios o mayúsculas en el HTML
        const activos = [...rows].filter(r => r.dataset.status.trim() === 'Activo').length;
        const inactivos = [...rows].filter(r => r.dataset.status.trim() === 'Inactivo').length;
        
        if(document.getElementById('count-all')) document.getElementById('count-all').textContent = total;
        if(document.getElementById('count-active')) document.getElementById('count-active').textContent = activos;
        if(document.getElementById('count-inactive')) document.getElementById('count-inactive').textContent = inactivos;
    }

    function applyFilters() {
        const search = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        rows.forEach(row => {
            // Aseguramos que los valores del dataset existan y estén limpios
            const status = (row.dataset.status || '').trim();
            const name = (row.dataset.name || '').toLowerCase();

            const matchFilter = (currentFilter === 'all' || status === currentFilter);
            const matchSearch = (!search || name.includes(search));

            if (matchFilter && matchSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        if (noResults) {
            // Si no hay resultados visibles, removemos 'hidden' para mostrar el mensaje
            if (visibleCount === 0) {
                noResults.classList.remove('hidden');
            } else {
                noResults.classList.add('hidden');
            }
        }
    }

    pills.forEach(pill => {
        pill.addEventListener('click', (e) => {
            e.preventDefault(); // Evitar comportamientos extraños
            currentFilter = pill.dataset.filter;

            // Gestionar clases visuales
            pills.forEach(p => {
                p.classList.remove('active-all', 'active-active', 'active-inactive');
            });
            
            if (currentFilter === 'all') pill.classList.add('active-all');
            else if (currentFilter === 'Activo') pill.classList.add('active-active');
            else if (currentFilter === 'Inactivo') pill.classList.add('active-inactive');

            applyFilters();
        });
    });

    searchInput.addEventListener('input', applyFilters);

    // Inicialización
    updateCounts();
    
    // IMPORTANTE: Primero aplicar filtros para "Todos" antes de forzar el click
    applyFilters(); 
});