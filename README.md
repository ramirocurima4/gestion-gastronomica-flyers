# 🍽️ Centro de Control Diario — Gestión Gastronómica y Generador de Flyers

Software comercial de escritorio en **Python** orientado a rotiserías, casas de comidas y locales gastronómicos de cercanía (enfoque *Offline-First*). Desarrollado como Proyecto Integrador para la cátedra **Prácticas Profesionalizantes II** de la **Tecnicatura Superior en Desarrollo de Software**.

---

## 👥 Equipo de Desarrollo

* **Sebastián Gauna** — *Product Owner (PO)*: Requerimientos del negocio, validación funcional y diseño de plantillas.
* **Ramiro Curimá** — *Scrum Master & QA*: Coordinación ágil, pruebas de persistencia, aseguramiento de calidad y documentación.
* **Antigravity** — *Lead Developer*: Diseño de arquitectura POO, implementación de servicios y GUI en CustomTkinter.

---

## 🚀 Características Principales (MVP Fase 1)

1. **Módulo 1 — Gestión de Menú y Precios (`views/tab_menu.py`)**:
   * Alta, edición y baja (CRUD) de platos, bebidas y combos.
   * Buscador interactivo en tiempo real por nombre, categoría o ingredientes.
   * **Actualización Masiva de Precios (%)**: Ajuste porcentual instantáneo por categoría o sobre todo el menú para responder rápidamente a cambios de costos.
2. **Módulo 2 — Persistencia Local Segura en Excel (`services/excel_manager.py`)**:
   * Almacenamiento centralizado en `data/datos_rotiseria.xlsx` con hojas independientes y estilizadas para **`Menu`** y **`Ventas`**.
   * Escritura atómica mediante archivo temporal para evitar pérdida o corrupción de datos.
   * Detección defensiva de bloqueos (`PermissionError`) cuando el archivo se encuentra abierto en Microsoft Excel o LibreOffice Calc.
3. **Módulo 3 — Generador Gráfico de Flyers 9:16 (`services/flyer_generator.py` & `views/tab_flyer.py`)**:
   * Renderizado automatizado con **Pillow (PIL)** en resolución vertical **1080x1920 px** (óptimo para Estados de WhatsApp e Historias de Instagram).
   * Tarjetas contenedoras con bordes redondeados y canal alfa semitransparente (**RGBA**) sobre plantillas personalizadas o fondo degradado oscuro generado programáticamente.
   * Cálculo dinámico de espaciado vertical (1 a 6 productos), precios destacados en formato pesos argentinos (`$ {:,.0f}`) y pie de página fijo con contacto de WhatsApp.
   * Previsualización escalada en vivo dentro de la aplicación.
4. **Módulo 4 — Registro Rápido de Ventas y Caja Diaria (`views/tab_caja.py`)**:
   * Asistente rápido para sumar platos del menú al pedido o carga directa de importe.
   * Clasificación por medio de pago (`Efectivo`, `Transferencia/MP`) y modalidad de entrega (`Mostrador`, `Delivery`).
   * Tablero de **Arqueo Diario** con indicadores de recaudación total, efectivo en caja y transferencias.

---

## 📁 Estructura del Proyecto

```text
├── main.py                  # Punto de entrada, verificación de carpetas e inicio de GUI
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Documentación técnica y guía de ejecución
├── .gitignore               # Exclusión de archivos temporales y caché
├── models/
│   ├── __init__.py
│   ├── producto.py          # Entidad Producto con validaciones y serialización
│   └── venta.py             # Entidad Venta con validaciones de caja
├── services/
│   ├── __init__.py
│   ├── excel_manager.py     # Persistencia atómica sobre data/datos_rotiseria.xlsx
│   └── flyer_generator.py   # Motor gráfico Pillow (1080x1920 px RGBA)
├── views/
│   ├── __init__.py
│   ├── app_ui.py            # Ventana principal CustomTkinter con CTkTabview
│   ├── tab_menu.py          # Pestaña 1: ABM de Menú y aumento porcentual masivo
│   ├── tab_flyer.py         # Pestaña 2: Selección de platos, generación y preview 9:16
│   └── tab_caja.py          # Pestaña 3: Registro de ventas y arqueo diario
├── templates/               # Plantillas base (incluye fallback oscuro automático)
├── output/                  # Destino de los flyers promocionales exportados (.png)
└── data/
    └── datos_rotiseria.xlsx # Base de datos local en Excel (hojas 'Menu' y 'Ventas')
```

---

## ⚙️ Instalación y Ejecución

### 1. Clonar el repositorio
```bash
git clone <URL_DEL_REPOSITORIO>
cd gestion-gastronomica-flyers
```

### 2. Crear un entorno virtual e instalar dependencias
```bash
python -m venv venv
# En Windows:
venv\Scripts\activate
# En Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Ejecutar la aplicación
```bash
python main.py
```
Al iniciar por primera vez, el sistema verificará las carpetas `data/`, `templates/` y `output/`, creará automáticamente el archivo `data/datos_rotiseria.xlsx` con las hojas estilizadas **`Menu`** y **`Ventas`**, y generará la plantilla base en `templates/`.
