const recipeSelect = document.getElementById('recipe_select');
const qtyInput     = document.getElementById('requested_quantity');
const infoPanel    = document.getElementById('recipe-info');

let recipeData = null;  // Guardamos los datos del fetch para recalcular al cambiar cantidad

// ── Fetch al cambiar receta ──────────────────────────────────
recipeSelect.addEventListener('change', async function () {
  const id = this.value;
  if (!id) { infoPanel.classList.add('hidden'); return; }

  try {
    const res  = await fetch(`/production/recipe_info/${id}`);
    const data = await res.json();
    recipeData = data;
    renderInfo(data, parseInt(qtyInput.value) || 1);
    infoPanel.classList.remove('hidden');
  } catch (e) {
    console.error('Error cargando receta:', e);
  }
});

// ── Recalcular lotes posibles al cambiar cantidad ────────────
qtyInput.addEventListener('input', function () {
  if (recipeData) {
    renderInfo(recipeData, parseInt(this.value) || 1);
  }
});

// ── Renderizar panel ─────────────────────────────────────────
function renderInfo(data, numLotes) {
  const qtyTotal = numLotes * data.cantidad_base;

  document.getElementById('info-producto').textContent  = data.producto_nombre;
  document.getElementById('info-cantidad').textContent  = `${data.cantidad_base} ${data.unidad} / lote`;
  document.getElementById('info-merma').textContent     = `${data.merma_estimada}%`;
  document.getElementById('info-tiempo').textContent    = data.tiempo_estimado ? `${data.tiempo_estimado} min` : '—';

  // Instrucciones
  const instrWrap = document.getElementById('info-instrucciones-wrap');
  if (data.instrucciones) {
    document.getElementById('info-instrucciones').textContent = data.instrucciones;
    instrWrap.classList.remove('hidden');
  } else {
    instrWrap.classList.add('hidden');
  }

  // Insumos
  const tbody = document.getElementById('insumos-tbody');
  tbody.innerHTML = '';
  data.insumos.forEach(ins => {
    const cantNecesaria  = ins.cantidad * numLotes;
    const lotesPosibles  = ins.cantidad > 0 ? Math.floor(ins.stock_disp / ins.cantidad) : '—';
    const sinStock       = ins.stock_disp < cantNecesaria;

    tbody.innerHTML += `
      <tr class="${sinStock ? 'bg-red-50' : 'bg-white'} border-t border-slate-100">
        <td class="px-3 py-2 font-medium ${sinStock ? 'text-red-700' : ''}">${ins.nombre}</td>
        <td class="px-3 py-2 text-right">${cantNecesaria.toFixed(2)} ${ins.unidad}</td>
        <td class="px-3 py-2 text-right ${sinStock ? 'text-red-600 font-semibold' : 'text-emerald-700'}">
          ${ins.stock_disp.toFixed(2)} ${ins.unidad}
          ${sinStock ? '<span class="ml-1 text-red-500">⚠ Insuficiente</span>' : ''}
        </td>
        <td class="px-3 py-2 text-right font-semibold ${sinStock ? 'text-red-600' : ''}">${lotesPosibles}</td>
      </tr>`;
  });

  // Presentaciones
  const presWrap = document.getElementById('presentaciones-wrap');
  const presList = document.getElementById('presentaciones-list');
  if (data.presentaciones.length > 0) {
    presList.innerHTML = '';
    const multiplicador = { 1: 1000, 2: 1000, 3: 1 };
    const mult = multiplicador[data.unidad === 'kg' ? 1 : data.unidad === 'L' ? 2 : 3] || 1;
    const cantBase = qtyTotal * mult;

    data.presentaciones.forEach(p => {
      const piezas = p.unit_size > 0 ? Math.floor(cantBase / p.unit_size) : '—';
      presList.innerHTML += `
        <span class="emerald-badge inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium border">
          ${p.nombre} — <strong>${piezas} uds</strong>
        </span>`;
    });
    presWrap.classList.remove('hidden');
  } else {
    presWrap.classList.add('hidden');
  }
}