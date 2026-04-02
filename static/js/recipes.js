document.addEventListener('DOMContentLoaded', function () {


  function updateIndices(containerSelector, rowSelector) {
    document.querySelectorAll(containerSelector + ' ' + rowSelector)
      .forEach((row, i) => {
        row.querySelectorAll('input, select, textarea').forEach(el => {
          ['name', 'id'].forEach(attr => {
            const v = el.getAttribute(attr);
            if (v) el.setAttribute(attr, v.replace(/-\d+-/, '-' + i + '-'));
          });
        });

        // 1. Actualizar el texto visual (PASO 1, PASO 2...)
        const num = row.querySelector('.step-num');
        if (num) num.textContent = 'PASO ' + (i + 1);

        // 2. NUEVO: Autocompletar el campo de orden (step_order)
        // Buscamos el input cuyo nombre termine en step_order dentro de esta fila
        const inputOrder = row.querySelector('input[name$="-step_order"]');
        if (inputOrder) {
            inputOrder.value = i + 1; // Asigna 1, 2, 3...
        }
      });
}

  function cloneLastRow(containerId, rowClass) {
    const c = document.getElementById(containerId);
    const rows = c.querySelectorAll('.' + rowClass);
    const lastRow = rows[rows.length - 1];
    const clone = lastRow.cloneNode(true);

    // Limpiar inputs y textareas
    clone.querySelectorAll('input, textarea').forEach(el => el.value = '');
    
    // IMPORTANTE: Resetear Selects al primer valor (el 'Seleccione...')
    clone.querySelectorAll('select').forEach(el => el.selectedIndex = 0);

    c.appendChild(clone);
    updateIndices('#' + containerId, '.' + rowClass);

    calcularTotalesDinamicos();
  }

  document.getElementById('add-material').addEventListener('click', () =>
    cloneLastRow('materials-container', 'material-row'));

  document.getElementById('add-step').addEventListener('click', () =>
    cloneLastRow('steps-container', 'step-row'));

  document.addEventListener('click', function (e) {
    if (!e.target.classList.contains('remove-row')) return;
    const row = e.target.closest('.material-row') || e.target.closest('.step-row');
    const container = row.parentNode;
    const cls = [...row.classList].find(x => x.endsWith('-row'));
    if (container.querySelectorAll('.' + cls).length > 1) {
      row.remove();
      updateIndices('#' + container.id, '.' + cls);
      calcularTotalesDinamicos();
    } else {
      alert('Debes mantener al menos un elemento.');
    }
  });


  // 

function calcularTotalesDinamicos() {
    let tiempoTotal = 0;
    
    // 1. Contar materiales actuales
    const numMateriales = document.querySelectorAll('.material-row').length;
    
    // 2. Obtener Unidad del Lote (para el extra_unidad de 0.3 si es Litros)
    const selectUnidadLote = document.getElementById('unit_med');
    const unidadLote = selectUnidadLote ? selectUnidadLote.value : "1";
    let extraUnidad = (unidadLote == "2") ? 0.3 : (unidadLote == "1" ? 0.2 : 0.05);

    let mermaAcumulada = 1.0 + (numMateriales * 0.2) + extraUnidad; 

    // 3. Tiempos y Merma por procesos
    const rowsPasos = document.querySelectorAll('.step-row');
    rowsPasos.forEach(row => {
        // Tiempo - Usamos querySelector exacto para evitar confusiones
        const inputTiempo = row.querySelector('input[name$="-estimated_time"]');
            if (inputTiempo) tiempoTotal += parseInt(inputTiempo.value) || 0;

        // Tipo de proceso
        const selectTipo = row.querySelector('select[name$="-process_type"]');
        const tipo = selectTipo.value;
        if (tipo == "1") mermaAcumulada += 1.2;      // Mezclado
        else if (tipo == "2") mermaAcumulada += 0.5; // Envasado
        else if (tipo == "3") mermaAcumulada += 0.1; // Reposo
    });

    // 4. Aplicar Factor de Escala (Lote)
    // IMPORTANTE: Asegúrate que el ID coincida con el de WTForms
    const inputLote = document.getElementById('produced_quantity');
    const lote = inputLote ? parseFloat(inputLote.value) || 0 : 0;
    
    let factor = 1.0;
    if (lote > 0 && lote < 15) factor = 1.25;
    else if (lote > 50) factor = 0.9;

    let mermaFinal = mermaAcumulada * factor;

    // 5. Mostrar en la interfaz
    const displayTiempo = document.getElementById('display-tiempo-total');
    const displayMerma = document.getElementById('display-merma-total');

    if(displayTiempo) displayTiempo.textContent = tiempoTotal + " min";
    if(displayMerma) displayMerma.textContent = mermaFinal.toFixed(2) + "%";
}

// --- LISTENERS GLOBALES ---

    // 1. Ejecutar numeración inicial (Esto pondrá el "1" en el primer paso de inmediato)
    updateIndices('#materials-container', '.material-row');
    updateIndices('#steps-container', '.step-row');

    // 2. Calcular totales por si ya hay datos (Edición)
    calcularTotalesDinamicos();


    const recipeForm = document.getElementById('recipe-form');
    if (recipeForm) {
        recipeForm.addEventListener('input', calcularTotalesDinamicos);
        recipeForm.addEventListener('change', calcularTotalesDinamicos);
    }

    // Ejecución inicial (Vital para el modo edición)
    calcularTotalesDinamicos();


});