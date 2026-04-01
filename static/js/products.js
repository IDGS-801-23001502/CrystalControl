document.addEventListener('DOMContentLoaded', () => {
    //Selectores de Elementos
    const rows = document.querySelectorAll('.product-row');
    const pills = document.querySelectorAll('.filter-pill');
    const searchInput = document.getElementById('product-search');
    const noResults = document.getElementById('no-results');

    // Estado inicial del filtro
    let currentFilter = 'all';

    function updateCounts() {
        const total = rows.length;
        const activos = [...rows].filter(r => r.dataset.status === 'Activo').length;
        const inactivos = [...rows].filter(r => r.dataset.status === 'Inactivo').length;

        // Intentamos actualizar solo si los elementos existen en el HTML
        if(document.getElementById('count-all')) document.getElementById('count-all').textContent = total;
        if(document.getElementById('count-active')) document.getElementById('count-active').textContent = activos;
        if(document.getElementById('count-inactive')) document.getElementById('count-inactive').textContent = inactivos;
    }

    function applyFilters() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        let visibleCount = 0;

        rows.forEach(row => {
            // Filtro por Estatus (Activo/Inactivo/Todos)
            const matchesFilter = currentFilter === 'all' || row.dataset.status === currentFilter;
            
            // Filtro por Nombre (Buscamos en el atributo data-name que pusimos en el HTML)
            const matchesSearch = !searchTerm || row.dataset.name.includes(searchTerm);

            // Si cumple ambas condiciones, se muestra
            if (matchesFilter && matchesSearch) {
                row.style.display = '';
                visibleCount++;
            } else {
                row.style.display = 'none';
            }
        });

        // Mostrar u ocultar mensaje de "No hay resultados"
        if (noResults) {
            noResults.classList.toggle('hidden', visibleCount > 0);
        }
    }

    pills.forEach(pill => {
        pill.addEventListener('click', () => {
            currentFilter = pill.dataset.filter;

            // Limpiar clases de "activo" en todos los botones
            pills.forEach(p => {
                p.classList.remove('active-all', 'active-active', 'active-inactive');
            });

            // Añadir la clase de estilo según el filtro seleccionado
            if (currentFilter === 'all')      pill.classList.add('active-all');
            if (currentFilter === 'Activo')   pill.classList.add('active-active');
            if (currentFilter === 'Inactivo') pill.classList.add('active-inactive');

            applyFilters();
        });
    });

    //Escuchar cuando el usuario escribe en la barra de búsqueda
    if (searchInput) {
        searchInput.addEventListener('input', applyFilters);
    }

    updateCounts();

    //Iniciar mostrando solo los activos
    const activePill = document.querySelector('[data-filter="Activo"]');
    if (activePill) activePill.click();
});