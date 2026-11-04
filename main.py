"""
Punto de entrada principal del sistema de Gestión Gastronómica y Generación de Flyers.
Proyecto Integrador — Prácticas Profesionalizantes II.

Verifica la estructura de directorios del sistema, inicializa los servicios de
persistencia en Excel y renderizado gráfico con Pillow, e inicia el loop principal
de la interfaz gráfica en CustomTkinter.
"""

import logging
import os
import sys

from services.excel_manager import ExcelManager
from services.flyer_generator import FlyerGenerator


BASE_DIR: str = os.path.dirname(os.path.abspath(__file__))


def configurar_logging() -> None:
    """Configura el registro de eventos y errores en consola."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def verificar_directorios_sistema(base_dir: str = BASE_DIR) -> dict[str, str]:
    """
    Asegura la existencia de las carpetas críticas del sistema:
    `data/`, `output/`, `templates/` y `assets/fonts/`.

    Returns:
        dict[str, str]: Diccionario con las rutas absolutas verificadas.
    """
    rutas = {
        "data": os.path.join(base_dir, "data"),
        "output": os.path.join(base_dir, "output"),
        "templates": os.path.join(base_dir, "templates"),
        "fonts": os.path.join(base_dir, "assets", "fonts"),
    }
    for nombre, ruta in rutas.items():
        os.makedirs(ruta, exist_ok=True)
        logging.getLogger(__name__).info("Directorio verificado [%s]: %s", nombre, ruta)
    return rutas


def inicializar_servicios(rutas: dict[str, str]) -> tuple[ExcelManager, FlyerGenerator]:
    """
    Instancia e inicializa los servicios centrales de la aplicación (`ExcelManager`
    y `FlyerGenerator`), poblando datos de ejemplo si el archivo Excel se crea por primera vez
    o si dispone de un surtido inicial incompleto.
    """
    ruta_excel = os.path.join(rutas["data"], "datos_rotiseria.xlsx")
    primer_inicio = not os.path.exists(ruta_excel)

    excel_manager = ExcelManager(filepath=ruta_excel)
    if primer_inicio or len(excel_manager.obtener_productos()) < 15:
        insertados = excel_manager.poblar_catalogo_demostracion()
        logging.getLogger(__name__).info(
            "Catálogo gastronómico de demostración poblado con %d platos y bebidas.",
            insertados,
        )

    flyer_generator = FlyerGenerator(
        templates_dir=rutas["templates"],
        output_dir=rutas["output"],
        fonts_dir=rutas["fonts"],
    )
    return excel_manager, flyer_generator


def main() -> None:
    """Función principal de arranque de la aplicación de escritorio."""
    configurar_logging()
    logger = logging.getLogger(__name__)
    logger.info("Iniciando Centro de Control Diario — Gestión Gastronómica...")

    rutas = verificar_directorios_sistema(BASE_DIR)
    excel_manager, flyer_generator = inicializar_servicios(rutas)

    try:
        from views.app_ui import AppUI
    except ImportError as exc:
        logger.error(
            "No se pudo cargar la interfaz gráfica (CustomTkinter / Tkinter): %s. "
            "Asegúrese de haber instalado las dependencias con 'pip install -r requirements.txt'.",
            exc,
        )
        sys.exit(1)

    app = AppUI(
        excel_manager=excel_manager,
        flyer_generator=flyer_generator,
    )
    app.mainloop()


if __name__ == "__main__":
    main()
