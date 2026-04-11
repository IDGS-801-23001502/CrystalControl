/**
 * Gestión de detalles de producción
 * Actualiza la tabla de insumos y proyecciones en tiempo real
 */

const recipeSelect = document.getElementById('recipe_select');
const qtyInput     = document.getElementById('requested_quantity');
const infoPanel    = document.getElementById('recipe-info');
const insumosTbody = document.getElementById('insumos-tbody');

let recipeData = null; // Memoria caché de la receta actual

// --- 1. CARGA DE DATOS (FETCH) ---
async function fetchRecipeData() {
    const id = recipeSelect.value;
    
    // Si no hay receta seleccionada, limpiamos la interfaz
    if (!id) {
        resetInterface();
        return;
    }

    try {
        // Mostrar un estado de "Cargando..." en la tabla
        insumosTbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-3 py-4 text-center text-slate-500">
                    <span class="inline-block animate-pulse">Cargando detalles de receta...</span>
                </td>
            </tr>`;

        const res = await fetch(`recipe_info/${id}`);
        if (!res.ok) throw new Error('Error en la respuesta del servidor');
        
        recipeData = await res.json();
        
        // Renderizar con la cantidad actual (mínimo 1)
        const currentQty = parseInt(qtyInput.value) || 1;
        renderInfo(recipeData, currentQty);

    } catch (e) {
        console.error('Error cargando receta:', e);
        insumosTbody.innerHTML = `
            <tr>
                <td colspan="4" class="px-3 py-4 text-center text-red-500 font-medium">
                    Error al conectar con el servidor. Reintente de nuevo.
                </td>
            </tr>`;
    }
}

// --- 2. RENDERIZADO DE LA INTERFAZ ---
function renderInfo(data, numLotes) {
    if (!data) return;

    const qtyTotal = numLotes * data.cantidad_base;

    // Actualizar encabezados de información general
    document.getElementById('info-producto').textContent  = data.producto_nombre;
    document.getElementById('info-cantidad').textContent  = `${data.cantidad_base} ${data.unidad} / lote`;
    document.getElementById('info-merma').textContent     = `${data.merma_estimada}%`;
    document.getElementById('info-tiempo').textContent    = data.tiempo_estimado ? `${data.tiempo_estimado} min` : '—';

    // Manejo de Instrucciones
    const instrWrap = document.getElementById('info-instrucciones-wrap');
    const instrText = document.getElementById('info-instrucciones');
    if (data.instrucciones) {
        instrText.textContent = data.instrucciones;
        instrWrap.classList.remove('hidden');
    } else {
        instrWrap.classList.add('hidden');
    }

    // Renderizar Insumos en la Tabla
    insumosTbody.innerHTML = '';
    data.insumos.forEach(ins => {
        const cantNecesaria  = ins.cantidad * numLotes;
        const lotesPosibles  = ins.cantidad > 0 ? Math.floor(ins.stock_disp / ins.cantidad) : '—';
        const sinStock       = ins.stock_disp < cantNecesaria;

        const row = document.createElement('tr');
        row.className = `${sinStock ? 'bg-red-50' : 'bg-white'} border-t border-slate-100 transition-colors`;
        
        row.innerHTML = `
            <td class="px-3 py-2 font-medium ${sinStock ? 'text-red-700' : 'text-slate-700'}">${ins.nombre}</td>
            <td class="px-3 py-2 text-right">${cantNecesaria.toFixed(2)} ${ins.unidad}</td>
            <td class="px-3 py-2 text-right ${sinStock ? 'text-red-600 font-semibold' : 'text-emerald-700'}">
                ${ins.stock_disp.toFixed(2)} ${ins.unidad}
                ${sinStock ? '<br><span class="text-[10px] text-red-500 uppercase">⚠ Insuficiente</span>' : ''}
            </td>
            <td class="px-3 py-2 text-right font-semibold ${sinStock ? 'text-red-600' : 'text-slate-900'}">
                ${lotesPosibles}
            </td>
        `;
        insumosTbody.appendChild(row);
    });

    // Renderizar Presentaciones (Proyección de empaquetado)
    const presWrap = document.getElementById('presentaciones-wrap');
    const presList = document.getElementById('presentaciones-list');
    
    if (data.presentaciones && data.presentaciones.length > 0) {
        presList.innerHTML = '';
        // Lógica de conversión (kg/L a gramos/ml si es necesario)
        const multiplicador = { 'kg': 1000, 'L': 1000 };
        const mult = multiplicador[data.unidad] || 1;
        const cantBaseEnGramosML = qtyTotal * mult;

        data.presentaciones.forEach(p => {
            const piezas = p.unit_size > 0 ? Math.floor(cantBaseEnGramosML / p.unit_size) : 0;
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

// --- 3. REINICIO DE INTERFAZ ---
function resetInterface() {
    recipeData = null;
    document.getElementById('info-producto').textContent = '—';
    document.getElementById('info-cantidad').textContent = '—';
    document.getElementById('info-merma').textContent    = '—';
    document.getElementById('info-tiempo').textContent   = '—';
    document.getElementById('info-instrucciones-wrap').classList.add('hidden');
    document.getElementById('presentaciones-wrap').classList.add('hidden');
    insumosTbody.innerHTML = `
        <tr>
            <td colspan="4" class="px-3 py-4 text-center text-slate-400 italic">
                Seleccione una receta para ver los detalles
            </td>
        </tr>`;
}

// --- 4. LISTENERS (EVENTOS) ---

// Cambio de receta
recipeSelect.addEventListener('change', fetchRecipeData);

// Cambio de cantidad (recalcula sin volver a consultar al servidor)
qtyInput.addEventListener('input', function () {
    if (recipeData) {
        const val = parseInt(this.value) || 1;
        renderInfo(recipeData, val);
    }
});

// Inicialización: Cargar datos si ya hay una receta seleccionada al abrir la página
document.addEventListener('DOMContentLoaded', () => {
    if (recipeSelect.value) {
        fetchRecipeData();
    }
});