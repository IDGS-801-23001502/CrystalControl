const searchInput = document.getElementById('purchase-search');
const rows = document.querySelectorAll('.purchase-row');
const noResults = document.getElementById('no-results');

searchInput.addEventListener('input', function() {
    let hasVisibleRows = false;
    const filter = this.value.toLowerCase();

    rows.forEach(row => {
        const folio = row.getAttribute('data-folio');
        // Agrega aquí más campos si quieres buscar por usuario, etc.
        if (folio.includes(filter)) {
            row.style.display = '';
            hasVisibleRows = true;
        } else {
            row.style.display = 'none';
        }
    });

    // Mostrar u ocultar el mensaje de "No resultados"
    if (hasVisibleRows) {
        noResults.classList.add('hidden');
    } else {
        noResults.classList.remove('hidden');
    }
});