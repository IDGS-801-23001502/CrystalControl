 const rows       = document.querySelectorAll('.supplier-row');
  const pills      = document.querySelectorAll('.filter-pill');
  const searchInput = document.getElementById('supplier-search');
  const noResults  = document.getElementById('no-results');

  let currentFilter = 'all';

  function updateCounts() {
    const total    = rows.length;
    const activos  = [...rows].filter(r => r.dataset.status === 'Activo').length;
    const inactivos = [...rows].filter(r => r.dataset.status === 'Inactivo').length;
    document.getElementById('count-all').textContent      = total;
    document.getElementById('count-active').textContent   = activos;
    document.getElementById('count-inactive').textContent = inactivos;
  }

  function applyFilters() {
    const search = searchInput.value.toLowerCase().trim();
    let visible = 0;

    rows.forEach(row => {
      const matchFilter = currentFilter === 'all' || row.dataset.status === currentFilter;
      const matchSearch = !search || row.dataset.name.includes(search) || row.dataset.code.includes(search);

      if (matchFilter && matchSearch) {
        row.style.display = '';
        visible++;
      } else {
        row.style.display = 'none';
      }
    });

    noResults.classList.toggle('hidden', visible > 0);
  }

  pills.forEach(pill => {
    pill.addEventListener('click', () => {
      currentFilter = pill.dataset.filter;

      pills.forEach(p => {
        p.classList.remove('active-all', 'active-active', 'active-inactive');
      });

      if (currentFilter === 'all')      pill.classList.add('active-all');
      if (currentFilter === 'Activo')   pill.classList.add('active-active');
      if (currentFilter === 'Inactivo') pill.classList.add('active-inactive');

      applyFilters();
    });
  });

  searchInput.addEventListener('input', applyFilters);

  updateCounts();
  document.querySelector('[data-filter="Activo"]').click();