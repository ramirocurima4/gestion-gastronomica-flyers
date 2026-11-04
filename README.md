# 🍽️ Centro de Control Diario — Gestión Gastronómica y Generador de Flyers

Software comercial de escritorio en **Python** orientado a rotiserías, casas de comidas y locales gastronómicos de cercanía (enfoque *Offline-First*). Desarrollado como Proyecto Integrador para la cátedra **Prácticas Profesionalizantes II** de la **Tecnicatura Superior en Desarrollo de Software**.

---

## 👥 Equipo de Desarrollo

* **Sebastián Gauna** — *Product Owner (PO)*: Requerimientos del negocio, validación funcional y diseño de plantillas.
* **Ramiro Curimá** — *Scrum Master & QA*: Coordinación ágil, pruebas de persistencia, aseguramiento de calidad y documentación.
* **Antigravity** — *Lead Developer*: Diseño de arquitectura POO, implementación de servicios y GUI en CustomTkinter.

---

## 🚀 Características Principales (Fase 2: Refactorización Visual & Accesibilidad)

1. **Módulo 1 — Gestión de Menú y Precios (`views/tab_menu.py`)**:
   * Alta, edición y baja (CRUD) de platos, bebidas y combos.
   * Buscador interactivo en tiempo real por nombre, categoría o ingredientes.
   * **Actualización Masiva de Precios (%)**: Ajuste porcentual instantáneo por categoría o sobre todo el menú.
   * **Accesibilidad y Scroll Adaptable**: Columna izquierda montada en un `CTkScrollableFrame` con márgenes compactos para garantizar visibilidad al 100% del botón de aplicar porcentaje en laptops y pantallas pequeñas.

2. **Módulo 2 — Persistencia Local Segura en Excel (`services/excel_manager.py`)**:
   * Almacenamiento centralizado en `data/datos_rotiseria.xlsx` con hojas estilizadas para **`Menu`**, **`Ventas`** y **`Arqueos`**.
   * Escritura atómica mediante archivo temporal para evitar pérdida o corrupción de datos.
   * Detección defensiva de bloqueos (`PermissionError`) si el archivo está abierto en Microsoft Excel o LibreOffice.
   * Migración y retrocompatibilidad automática con soporte para desglose de pagos mixtos.

3. **Módulo 3 — Motor Gráfico de Flyers Enriquecido y Menú Completo (`services/flyer_generator.py` & `views/tab_flyer.py`)**:
   * Renderizado automatizado con **Pillow (PIL)** en resolución vertical **1080x1920 px** (formato 9:16 para WhatsApp e Instagram) sin dependencias pesadas.
   * **Tipografías Libres Incorporadas (`assets/fonts/`)**:
     * Titulares: **`Bebas Neue`** y **`Playfair Display`**.
     * Textos y Precios: **`Montserrat Bold`** e **`Inter Regular`**.
     * Script utilitario y descarga automática transparente (`scripts/download_fonts.py`) con fallback defensivo a fuentes del sistema (`DejaVuSans`, `Arial`, etc.) o Pillow sin arrojar excepción.
   * **Selector de 5 Plantillas Visuales de Diseño (`CTkOptionMenu`)**:
     * **`Pizarra Burguer (Dark & Red)`**: Fondo grafito texturado, halo rojo brasa, acentos cheddar y tipografía contundente Bebas Neue.
     * **`Pizzería Rústica (Madera & Blanco)`**: Fondo cálido de horno de barro y madera, acentos rústicos y serif clásica Playfair Display.
     * **`Fast Food Mostaza (Pop & Cards)`**: Fondo ámbar tostado, tarjetas contrastadas y precios en amarillo mostaza brillante (`#facc15`).
     * **`Turquesa Glass (Cards Modernas)`**: Glassmorphism oscuro en petróleo/cian, tarjetas translúcidas y acentos menta brillante (`#2dd4bf`).
     * **`Gourmet Bistró (Elegante & Minimal)`**: Obsidiana pura, filetes dorados champagne y estética minimalista de alta cocina.
   * **Logo Institucional y Marca de Agua Decorativa**:
     * Selector de archivo de logo en la interfaz (`views/tab_flyer.py`).
     * Estampado proporcional automático en el encabezado institucional.
     * Marca de agua translúcida (alpha compositing al 10%-15%) fundida armónicamente en el fondo del lienzo detrás del contenido.
   * **Sello Promocional / Cinta de Oferta Especial (Promo Stickers & Ribbons)**:
     * Selector predefinido junto al control de logo con opciones de alto impacto: `🔥 ¡SOLO POR HOY!`, `🛵 ¡ENVÍO GRATIS!`, `💵 10% OFF EFECTIVO`, `⭐ RECOMENDADO DEL CHEF`, `🎉 PROMO DE LA SEMANA`, `🍔 2x1 EN SELECCIONADOS`, `⚡ ¡OFERTA LIMITADA!`.
     * Estampado programático con Pillow en la esquina superior del flyer con sombra, borde dorado/menta y fondo de alto contraste.
   * **Selector de Modo de Generación**:
     * **`Modo Promos Destacadas`**: 1 a 6 tarjetas grandes con descripción de ingredientes y badge de precio destacado.
     * **`Modo Menú Completo`**: Exporta la carta entera clasificada automáticamente por **Categoría** en un layout balanceado de **2 columnas verticales**, con títulos destacados de sección, renglones compactos con puntos guía (`Plato . . . . . $ Precio`) y ajuste dinámico de interlineado.
   * **Optimización de Pantalla y Visualización de Menú**:
     * Panel de configuración izquierdo montado sobre un `CTkScrollableFrame` fluido para garantizar compatibilidad con laptops.
     * Lista compacta de selección de platos en `scroll_productos` (34px de altura por fila) que permite visualizar de **5 a 6 productos simultáneamente** con deslizamiento suave.
   * **Pie de Página Dinámico**: Barra inferior de contacto con ícono de WhatsApp, número de pedidos y leyenda de entrega (*Mostrador / Delivery*).
   * Previsualización escalada en vivo dentro de la aplicación y botón de acceso directo a la carpeta de salida `output/`.

4. **Módulo 4 — Registro Rápido de Ventas con Buscador Predictivo, Pago Mixto y Arqueo (`views/tab_caja.py`)**:
   * **Buscador Predictivo en Tiempo Real**: Campo de búsqueda con autocompletado instantáneo (filtro insensible a tildes por nombre o categoría al presionar teclas), navegación con flechas `↑`/`↓` o clic, y confirmación directa de adición al pedido presionando **`Enter`**.
   * **Registro de Pago Mixto**: Opción `'Mixto (Efectivo + Transferencia)'` con activación dinámica de campos `Monto Efectivo ($)` y `Monto Transferencia ($)`, con validación en tiempo real de coincidencia con el total.
   * Modalidad de entrega (`Mostrador`, `Delivery`) y calculadora de vuelto en tiempo real.
   * Tablero de **Arqueo Diario** con discriminación exacta de montos en efectivo y transferencias (integrando operaciones puras y mixtas) con guardado en Excel y exportación de reportes.
   * **Alto Contraste en Tabla de Movimientos**: Selección de filas estilizada en **Turquesa Noche (`#0f766e`)** con tipografía blanca (`#ffffff`) para máxima legibilidad sin empastar el texto.

5. **Sistema de Temas y Tipografías Estandarizadas (`theme_manager.py` / `views/theme_manager.py`)**:
   * **Paleta Turquesa / Verde Esmeralda**: Colores de acento `#14b8a6` / `#0d9488` / `#2dd4bf`.
   * **Modo Oscuro ('Dark')**: Fondo grafito profundo (`#0b0f19`), tarjetas intermedias (`#161e2e`), textos blanco hueso y números destacados en turquesa brillante.
   * **Modo Claro ('Light')**: Fondo verde menta grisáceo suave (`#f0fdf4`), tarjetas blancas (`#ffffff`) con bordes suaves turquesa (`#ccfbf1`) y textos gris oscuro de alta legibilidad (`#0f172a`).
   * **Estandarización Tipográfica Mejorada**: Familias sans-serif legibles ('Inter', 'Segoe UI', 'Ubuntu Sans', 'DejaVu Sans') con incremento de +1/+2 puntos en tablas (`Treeview` 13pt con `rowheight=36`) y campos de entrada de datos (`14pt`), títulos de pestañas (`14px` negrita), nombres de productos (`14px` negrita) y valores monetarios destacados (`16px` a `22px` negrita).
   * **Resolución Mínima**: Tamaño mínimo garantizado de `1100x680` con adaptación fluida de componentes.

---

## 📁 Estructura del Proyecto

```text
├── main.py                  # Punto de entrada, verificación de carpetas e inicio de GUI
├── requirements.txt         # Dependencias del proyecto
├── README.md                # Documentación técnica y guía de ejecución
├── .gitignore               # Exclusión de archivos temporales y caché
├── assets/
│   └── fonts/               # Tipografías TTF libres (Bebas Neue, Playfair, Montserrat, Inter)
├── scripts/
│   ├── __init__.py
│   └── download_fonts.py    # Script de descarga y verificación de fuentes TTF
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
    └── datos_rotiseria.xlsx # Base de datos local en Excel (hojas 'Menu', 'Ventas', 'Arqueos')
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
