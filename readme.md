# 🧼 CrystalControl

**CrystalControl** es un sistema integral desarrollado en Flask para la gestión de producción y venta de productos de limpieza. El sistema permite el control total desde la adquisición de materia prima (químicos, envases) hasta la venta final, calculando automáticamente costos de producción y utilidades netas.

---

## 🏗️ Arquitectura del Proyecto

El proyecto utiliza una estructura modular plana basada en **Blueprints**, facilitando la escalabilidad y el mantenimiento de cada requerimiento funcional (RDF).

```text
/CrystalControl
├── modules/                # Lógica de negocio (Blueprints)
│   ├── users.py            # RDF 1: Gestión de Usuarios
│   ├── suppliers.py        # RDF 2: Gestión de Proveedores
│   ├── raw_materials.py    # RDF 3 y 11: Inventario de Insumos
│   ├── purchases.py        # RDF 4: Gestión de Compras
│   ├── recipes.py          # RDF 5: Explosión de Materiales
│   ├── production.py       # RDF 6: Órdenes de Producción
│   ├── products.py         # RDF 7 y 10: Producto Terminado
│   ├── analytics.py        # RDF 8: Inteligencia de Negocio
│   └── sales.py            # RDF 9: Punto de Venta y Caja
├── templates/              # Vistas HTML (Jinja2) organizadas por módulo
│   ├── base.html           # Layout principal
│   ├── users/              # Vistas de usuarios
│   ├── production/         # Vistas de procesos
│   └── ...                 # (Resto de carpetas de módulos)
├── static/                 # CSS, JS, Imágenes y Assets
├── models.py               # Definición de Base de Datos (SQLAlchemy)
├── config.py               # Configuración de App y DB
├── main.py                 # Factory de la aplicación
└── run.py                  # Script de ejecución

```

# Crear y activar entorno virtual
```bash
py -m venv .env
.env\Scripts\activate     # En Windows
```

**No olvidemos activar los cambios en las clases de Tailwind**
```bash
npx @tailwindcss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```

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

