# 🧼 CrystalControl

**CrystalControl** es un sistema integral desarrollado en Flask para la gestión de producción y venta de productos de limpieza. El sistema permite el control total desde la adquisición de materia prima (químicos, envases) hasta la venta final, calculando automáticamente costos de producción y utilidades netas.

---

## 🏗️ Arquitectura del Proyecto

El proyecto utiliza una estructura modular plana basada en **Blueprints**, facilitando la escalabilidad y el mantenimiento de cada requerimiento funcional (RDF).

```text
/CrystalControl
├── modules/                # Lógica de negocio (Blueprints en caso de que nos deje)
│   ├── users.py            # RDF 1: Gestión de Usuarios
│   ├── suppliers.py        # RDF 2: Gestión de Proveedores
│   ├── raw_materials.py    # RDF 3 y 11: Inventario de Insumos
│   ├── purchases.py        # RDF 4: Gestión de Compras
│   ├── recipes.py          # RDF 5: Explosión de Materiales
│   ├── production.py       # RDF 6: Órdenes de Producción
│   ├── products.py         # RDF 7 y 10: Producto Terminado
│   ├── analytics.py        # RDF 8: Inteligencia de Negocio
│   └── sales.py            # RDF 9: Punto de Venta y Caja
├── templates/
│   ├── base.html                 # Estructura principal (Navbar, Sidebar, Footer)
│   ├── index.html                # Dashboard principal con resumen de métricas
│   │
│   ├── users/                    # RDF 1: Gestión de Usuarios
│   │   ├── list.html             # RDF 1.3: Buscar y listar usuarios
│   │   ├── create.html           # RDF 1.2: Formulario de alta
│   │   ├── edit.html             # RDF 1.4: Actualizar datos
│   │   └── password_modal.html   # RDF 1.1: Mostrar contraseña generada
│   │
│   ├── suppliers/                # RDF 2: Gestión de Proveedores
│   │   ├── list.html             # RDF 2.2: Buscar proveedores
│   │   ├── create.html           # RDF 2.1: Registro de nuevo proveedor
│   │   └── edit.html             # RDF 2.3: Modificar datos
│   │
│   ├── inventory/                # RDF 3 y 11: Materias Primas
│   │   ├── raw_materials.html    # RDF 11.1: Catálogo de insumos
│   │   ├── movements.html        # RDF 3.1: Entradas y salidas (merma, abasto)
│   │   ├── stock_report.html     # RDF 3.3: Reporte de Stock Bajo
│   │   └── requests.html         # RDF 3.2: Reporte de solicitudes de consumo
│   │
│   ├── purchases/                # RDF 4: Compras
│   │   ├── create_request.html   # RDF 4.1: Generar solicitud de compra
│   │   ├── list_purchases.html   # RDF 4.2: Listado de folios de compra
│   │   └── delivery_report.html  # RDF 4.3: Reporte de entrega por proveedor
│   │
│   ├── recipes/                  # RDF 5: Explosión de Materiales
│   │   ├── list.html             # RDF 5.3: Buscador de recetas
│   │   ├── create.html           # RDF 5.1: Registro de fórmulas y mermas
│   │   └── edit.html             # RDF 5.2: Actualización de pasos y cantidades
│   │
│   ├── production/               # RDF 6: Producción
│   │   ├── orders.html           # RDF 6.1: Generar y listar órdenes
│   │   ├── check_stock.html      # RDF 6.2: Validación de disponibilidad
│   │   └── traceability.html     # RDF 6.3: Registro de lotes y operadores
│   │
│   ├── products/                 # RDF 7 y 10: Producto Terminado
│   │   ├── catalog.html          # RDF 10.1: Registro y precios (men/may)
│   │   ├── stock.html            # RDF 7.3: Consulta por presentación (litros/galón)
│   │   └── adjustments.html      # RDF 7.2: Ajustes manuales por daño o auditoría
│   │
│   ├── sales/                    # RDF 9: Ventas
│   │   ├── pos.html              # RDF 9.2: Punto de venta (Generación de ticket)
│   │   ├── daily_cash.html       # RDF 9.3: Corte de caja diario
│   │   ├── cash_out.html         # RDF 9.4: Registro de salidas (pago proveedores)
│   │   └── utility_report.html   # RDF 9.5: Ganancia real del día
│   │
│   └── analytics/                # RDF 8: Análisis
│       ├── costs.html            # RDF 8.1: Costo real vs Precio de venta
│       ├── efficiency.html       # RDF 8.3: Gráficos de rotación y mermas
│       └── dashboard_pro.html    # Vista general de inteligencia de negocio
├── static/                 # CSS, JS, Imágenes y Assets
├── models.py               # Definición de Base de Datos (SQLAlchemy)
├── config.py               # Configuración de App y DB
├── main.py                 # Factory de la aplicación
└── run.py                  # Script de ejecución

```

---

# Crear y activar entorno virtual
```bash
py -m venv .env
.env\Scripts\activate     # En Windows
```

**No olvidemos activar los cambios en las clases de Tailwind**
```bash
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```

---

# Dependencias
Las dependencias de flask estan enumeradas en el archivo **requirements.txt**, las de node estan en el archivo **packaje.json**
para instalar las dependencias

**Python**
```bash
pip install [nombre-dependencia]
```

**Node**
```
npm install
```

