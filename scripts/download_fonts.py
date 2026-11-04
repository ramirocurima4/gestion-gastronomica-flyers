"""
Script utilitario para descargar o asegurar la presencia de fuentes TTF libres
en 'assets/fonts/' para el motor de generación de flyers:
- Titulares: 'Bebas Neue' y 'Playfair Display'
- Textos y Precios: 'Montserrat Bold' e 'Inter Regular'

Permite ejecución manual o llamada automática desde el ciclo de vida de la aplicación.
"""

import logging
import os
import urllib.error
import urllib.request
from typing import Dict

logger = logging.getLogger(__name__)

FUENTES_URLS: Dict[str, str] = {
    "BebasNeue-Regular.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/ofl/bebasneue/BebasNeue-Regular.ttf"
    ),
    "PlayfairDisplay-Regular.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/ofl/playfairdisplay/PlayfairDisplay%5Bwght%5D.ttf"
    ),
    "Montserrat-Bold.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf"
    ),
    "Inter-Regular.ttf": (
        "https://raw.githubusercontent.com/google/fonts/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf"
    ),
}


def asegurar_fuentes_ttf(directorio_destino: str = "assets/fonts") -> Dict[str, str]:
    """
    Verifica que las fuentes TTF existan en `directorio_destino`. Si alguna falta,
    intenta descargarla desde el repositorio oficial de Google Fonts.
    Si la conexión a internet no está disponible, captura el error de forma segura
    para permitir el funcionamiento mediante las fuentes de respaldo del sistema.

    Args:
        directorio_destino (str): Carpeta donde se almacenan las fuentes TTF.

    Returns:
        Dict[str, str]: Mapeo de nombre de archivo a ruta absoluta existente.
    """
    ruta_dir = os.path.abspath(directorio_destino)
    os.makedirs(ruta_dir, exist_ok=True)

    rutas_confirmadas: Dict[str, str] = {}

    for nombre_archivo, url in FUENTES_URLS.items():
        ruta_archivo = os.path.join(ruta_dir, nombre_archivo)
        if os.path.exists(ruta_archivo) and os.path.getsize(ruta_archivo) > 1024:
            rutas_confirmadas[nombre_archivo] = ruta_archivo
            continue

        try:
            logger.info("Descargando fuente tipográfica: %s...", nombre_archivo)
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Gestión Gastronómica Flyer Generator)"},
            )
            with urllib.request.urlopen(req, timeout=8) as response, open(
                ruta_archivo, "wb"
            ) as f_out:
                f_out.write(response.read())

            if os.path.exists(ruta_archivo) and os.path.getsize(ruta_archivo) > 1024:
                rutas_confirmadas[nombre_archivo] = ruta_archivo
                logger.info("Fuente guardada exitosamente: %s", ruta_archivo)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            logger.warning(
                "No se pudo descargar la fuente '%s' (%s). "
                "El generador utilizará el fallback automático de fuentes del sistema.",
                nombre_archivo,
                exc,
            )

    return rutas_confirmadas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    print("Asegurando fuentes tipográficas en assets/fonts/...")
    fuentes = asegurar_fuentes_ttf()
    print(f"Fuentes disponibles en disco: {len(fuentes)} / {len(FUENTES_URLS)}")
    for f, p in fuentes.items():
        print(f"  ✔ {f} -> {p}")
