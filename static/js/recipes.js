document.addEventListener('DOMContentLoaded', function () {
    // 1. Cargar el mapa de unidades desde el atributo data del HTML
    const containerMateriales = document.getElementById('materials-container');
    const unidadesMap = JSON.parse(containerMateriales.getAttribute('data-unidades') || '{}');

    /**
     * Actualiza el texto visual de la unidad de medida según el material seleccionado
     */
    function actualizarUnidadReferencia(row) {
        // Buscamos el select del material (usando el final del nombre para que sea dinámico)
        const selectMaterial = row.querySelector('select[name$="-material_id"]');
        const displayUnidad = row.querySelector('.unit-text');

        if (selectMaterial && displayUnidad) {
            const materialId = selectMaterial.value;
            displayUnidad.textContent = unidadesMap[materialId] || '---';
        }
    }

    
    function updateIndices(containerSelector, rowSelector) {
        document.querySelectorAll(containerSelector + ' ' + rowSelector)
            .forEach((row, i) => {
                row.querySelectorAll('input, select, textarea').forEach(el => {
                    ['name', 'id'].forEach(attr => {
                        const v = el.getAttribute(attr);
                        if (v) el.setAttribute(attr, v.replace(/-\d+-/, '-' + i + '-'));
                    });
                });

                // Actualizar texto visual del paso
                const num = row.querySelector('.step-num');
                if (num) num.textContent = 'PASO ' + (i + 1);

                // Autocompletar el campo hidden de orden
                const inputOrder = row.querySelector('input[name$="-step_order"]');
                if (inputOrder) {
                    inputOrder.value = i + 1;
                }

                // Si es fila de material, refrescar la unidad de medida
                if (rowSelector === '.material-row') {
                    actualizarUnidadReferencia(row);
                }
            });
    }

    /**
     * Clona la última fila de un contenedor
     */
    function cloneLastRow(containerId, rowClass) {
        const c = document.getElementById(containerId);
        const rows = c.querySelectorAll('.' + rowClass);
        const lastRow = rows[rows.length - 1];
        const clone = lastRow.cloneNode(true);

        // Limpiar valores
        clone.querySelectorAll('input, textarea').forEach(el => el.value = '');
        clone.querySelectorAll('select').forEach(el => el.selectedIndex = 0);

        // Si es material, resetear el texto de la unidad
        const unitTxt = clone.querySelector('.unit-text');
        if (unitTxt) unitTxt.textContent = '---';

        c.appendChild(clone);
        updateIndices('#' + containerId, '.' + rowClass);
        calcularTotalesDinamicos();
    }

    /**
     * Calcula tiempos y mermas
     */
    function calcularTotalesDinamicos() {
        let tiempoTotal = 0;
        const numMateriales = document.querySelectorAll('.material-row').length;

        const selectUnidadLote = document.getElementById('unit_med');
        const unidadLote = selectUnidadLote ? selectUnidadLote.value : "1";
        let extraUnidad = (unidadLote == "2") ? 0.3 : (unidadLote == "1" ? 0.2 : 0.05);

        let mermaAcumulada = 1.0 + (numMateriales * 0.2) + extraUnidad;

        const rowsPasos = document.querySelectorAll('.step-row');
        rowsPasos.forEach(row => {
            const inputTiempo = row.querySelector('input[name$="-estimated_time"]');
            if (inputTiempo) tiempoTotal += parseInt(inputTiempo.value) || 0;

            const selectTipo = row.querySelector('select[name$="-process_type"]');
            if (selectTipo) {
                const tipo = selectTipo.value;
                if (tipo == "1") mermaAcumulada += 1.2;
                else if (tipo == "2") mermaAcumulada += 0.5;
                else if (tipo == "3") mermaAcumulada += 0.1;
            }
        });

        const inputLote = document.getElementById('produced_quantity');
        const lote = inputLote ? parseFloat(inputLote.value) || 0 : 0;

        let factor = 1.0;
        if (lote > 0 && lote < 15) factor = 1.25;
        else if (lote > 50) factor = 0.9;

        let mermaFinal = mermaAcumulada * factor;

        const displayTiempo = document.getElementById('display-tiempo-total');
        const displayMerma = document.getElementById('display-merma-total');

        if (displayTiempo) displayTiempo.textContent = tiempoTotal + " min";
        if (displayMerma) displayMerma.textContent = mermaFinal.toFixed(2) + "%";
    }

    // --- EVENT LISTENERS ---

    document.getElementById('add-material').addEventListener('click', () =>
        cloneLastRow('materials-container', 'material-row'));

    document.getElementById('add-step').addEventListener('click', () =>
        cloneLastRow('steps-container', 'step-row'));

    // Delegación de eventos para eliminar filas y cambiar unidades
    document.addEventListener('click', function (e) {
        if (e.target.classList.contains('remove-row')) {
            const row = e.target.closest('.material-row') || e.target.closest('.step-row');
            const container = row.parentNode;
            const cls = row.classList.contains('material-row') ? 'material-row' : 'step-row';

            if (container.querySelectorAll('.' + cls).length > 1) {
                row.remove();
                updateIndices('#' + container.id, '.' + cls);
                calcularTotalesDinamicos();
            } else {
                alert('Debes mantener al menos un elemento.');
            }
        }
    });

    // Detectar cambios en los selectores de material para actualizar la unidad
    document.addEventListener('change', function (e) {
        if (e.target.name && e.target.name.endsWith('-material_id')) {
            actualizarUnidadReferencia(e.target.closest('.material-row'));
        }

        // Recalcular mermas si cambia cualquier input relevante
        if (e.target.id === 'unit_med' || e.target.id === 'produced_quantity' || e.target.closest('.step-row')) {
            calcularTotalesDinamicos();
        }
    });

    // Soporte para inputs (mientras escriben)
    document.getElementById('recipe-form').addEventListener('input', calcularTotalesDinamicos);

    // --- INICIALIZACIÓN ---
    updateIndices('#materials-container', '.material-row');
    updateIndices('#steps-container', '.step-row');

    // Forzar la carga inicial de unidades 
    document.querySelectorAll('.material-row').forEach(row => actualizarUnidadReferencia(row));

    calcularTotalesDinamicos();
});