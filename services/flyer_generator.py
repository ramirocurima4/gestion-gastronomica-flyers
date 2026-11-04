"""
Servicio generador de flyers gastronómicos en formato vertical (9:16 - 1080x1920 px)
optimizado para Estados de WhatsApp e Historias de Instagram utilizando Pillow (PIL).

Características:
1. Motor multi-plantillas enriquecido con 5 estilos programáticos de alta gama:
   - 'Pizarra Burguer (Dark & Red)': Grafito profundo con acentos rojo brasa y cheddar.
   - 'Pizzería Rústica (Madera & Blanco)': Horno de barro y madera con tarjetas claras y acentos rústicos.
   - 'Fast Food Mostaza (Pop & Cards)': Fondo ámbar oscuro, tarjetas pop y precios en amarillo mostaza brillante.
   - 'Turquesa Glass (Cards Modernas)': Glassmorphism en tonos petróleo, acentos turquesa y menta brillante.
   - 'Gourmet Bistró (Elegante & Minimal)': Fondo obsidiana/grafito con filetes dorados y tipografía serif refinada.
2. Incorporación de tipografías TTF libres ('assets/fonts/') con fallback seguro sin excepciones:
   - Titulares: 'Bebas Neue' y 'Playfair Display'
   - Textos y Precios: 'Montserrat Bold' e 'Inter Regular'
3. Logo institucional y marca de agua decorativa:
   - Estampado proporcional en el header
   - Marca de agua translúcida (alpha compositing al 10%-15%) fundida en el fondo
4. Dos modalidades de maquetación:
   - 'Modo Promos Destacadas': 1 a 6 tarjetas grandes con foto/badge, descripción y precio destacado.
   - 'Modo Menú Completo': Carta completa clasificada por categorías en 2 columnas verticales
     balanceadas, con renglones compactos ('Plato . . . . . $ Precio') e interlineado dinámico.
5. Pie de página dinámico: Barra de contacto con ícono de WhatsApp, número y aviso de retiro / delivery.
"""

from datetime import datetime
import logging
import math
import os
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from models.producto import Producto
from scripts.download_fonts import asegurar_fuentes_ttf

logger = logging.getLogger(__name__)


class FlyerGenerator:
    """
    Motor gráfico desacoplado basado en funciones nativas de Pillow (ImageDraw, ImageFont)
    para el diseño y renderizado automatizado de flyers publicitarios y menús completos.
    """

    ANCHO: int = 1080
    ALTO: int = 1920
    MAX_PRODUCTOS: int = 6

    # Modos de maquetación disponibles
    MODO_PROMOS_DESTACADAS: str = "Modo Promos Destacadas"
    MODO_MENU_COMPLETO: str = "Modo Menú Completo"

    MODOS_DISPONIBLES: List[str] = [
        MODO_PROMOS_DESTACADAS,
        MODO_MENU_COMPLETO,
    ]

    # 5 Plantillas visuales predefinidas
    ESTILO_PIZARRA_BURGUER: str = "Pizarra Burguer (Dark & Red)"
    ESTILO_PIZZERIA_RUSTICA: str = "Pizzería Rústica (Madera & Blanco)"
    ESTILO_FAST_FOOD_MOSTAZA: str = "Fast Food Mostaza (Pop & Cards)"
    ESTILO_TURQUESA_GLASS: str = "Turquesa Glass (Cards Modernas)"
    ESTILO_GOURMET_BISTRO: str = "Gourmet Bistró (Elegante & Minimal)"

    PLANTILLAS_DISPONIBLES: List[str] = [
        ESTILO_PIZARRA_BURGUER,
        ESTILO_PIZZERIA_RUSTICA,
        ESTILO_FAST_FOOD_MOSTAZA,
        ESTILO_TURQUESA_GLASS,
        ESTILO_GOURMET_BISTRO,
    ]

    # Sellos y Cintas de Oferta Especial (Promo Stickers / Ribbons)
    SELLO_NINGUNO: str = "Sin Sello Especial"
    SELLO_SOLO_POR_HOY: str = "🔥 ¡SOLO POR HOY!"
    SELLO_ENVIO_GRATIS: str = "🛵 ¡ENVÍO GRATIS!"
    SELLO_OFF_EFECTIVO: str = "💵 10% OFF EFECTIVO"
    SELLO_RECOMENDADO: str = "⭐ RECOMENDADO DEL CHEF"
    SELLO_PROMO_SEMANA: str = "🎉 PROMO DE LA SEMANA"
    SELLO_DOS_POR_UNO: str = "🍔 2x1 EN SELECCIONADOS"
    SELLO_OFERTA_LIMITADA: str = "⚡ ¡OFERTA LIMITADA!"

    SELLOS_PROMO_DISPONIBLES: List[str] = [
        SELLO_NINGUNO,
        SELLO_SOLO_POR_HOY,
        SELLO_ENVIO_GRATIS,
        SELLO_OFF_EFECTIVO,
        SELLO_RECOMENDADO,
        SELLO_PROMO_SEMANA,
        SELLO_DOS_POR_UNO,
        SELLO_OFERTA_LIMITADA,
    ]

    # Alias de compatibilidad hacia atrás
    ESTILO_PIZARRA_OSCURA: str = ESTILO_PIZARRA_BURGUER
    ESTILO_TURQUESA_GOURMET: str = ESTILO_TURQUESA_GLASS
    ESTILO_ROJO_RUSTICO: str = ESTILO_PIZZERIA_RUSTICA

    # Nombres de archivos TTF en assets/fonts/
    FONT_BEBAS_NEUE: str = "BebasNeue-Regular.ttf"
    FONT_PLAYFAIR_DISPLAY: str = "PlayfairDisplay-Regular.ttf"
    FONT_MONTSERRAT_BOLD: str = "Montserrat-Bold.ttf"
    FONT_INTER_REGULAR: str = "Inter-Regular.ttf"

    # Configuraciones cromáticas y tipográficas por plantilla
    ESTILOS_CONFIG: Dict[str, Dict[str, Any]] = {
        ESTILO_PIZARRA_BURGUER: {
            "nombre": "Pizarra Burguer (Dark & Red)",
            # Fondo degradado vertical grafito y rojo brasa
            "fondo_top": (15, 17, 26),
            "fondo_mid": (28, 20, 26),
            "fondo_bot": (10, 10, 16),
            "halo_1": (220, 38, 38, 26),
            "halo_2": (245, 158, 11, 18),
            "borde_marco": (220, 38, 38, 65),
            # Tipografías preferidas
            "fuente_titular": FONT_BEBAS_NEUE,
            "fuente_subtitulo": FONT_MONTSERRAT_BOLD,
            "fuente_nombre": FONT_MONTSERRAT_BOLD,
            "fuente_precio": FONT_MONTSERRAT_BOLD,
            "fuente_cuerpo": FONT_INTER_REGULAR,
            # Encabezado
            "badge_bg": (36, 14, 18, 230),
            "badge_border": (239, 68, 68, 255),
            "badge_texto": (254, 202, 202, 255),
            "titulo_texto": (255, 255, 255, 255),
            "titulo_sombra": (0, 0, 0, 225),
            "linea_separadora": (220, 38, 38, 255),
            # Tarjetas de productos
            "tarjeta_bg": (22, 24, 34, 225),
            "tarjeta_borde": (220, 38, 38, 85),
            "tarjeta_lateral": (220, 38, 38, 255),
            "sombra_card": (0, 0, 0, 135),
            # Precios y textos
            "precio_caja_bg": (220, 38, 38, 48),
            "precio_caja_border": (248, 113, 113, 195),
            "precio_texto": (254, 240, 138, 255),
            "cat_texto": (248, 113, 113, 255),
            "nombre_texto": (255, 255, 255, 255),
            "desc_texto": (209, 213, 219, 235),
            # Columnas Carta Completa
            "col_panel_bg": (18, 20, 29, 232),
            "col_panel_border": (220, 38, 38, 90),
            "col_cat_header_bg": (42, 16, 22, 235),
            "col_cat_bar": (220, 38, 38, 255),
            "col_cat_texto": (254, 202, 202, 255),
            "col_puntos": (120, 53, 53, 175),
            # Pie de contacto
            "footer_bg": (18, 20, 30, 245),
            "footer_border": (220, 38, 38, 255),
            "footer_wa_icon": (34, 197, 94, 255),
            "footer_aviso": (254, 240, 138, 255),
        },
        ESTILO_PIZZERIA_RUSTICA: {
            "nombre": "Pizzería Rústica (Madera & Blanco)",
            # Fondo degradado vertical terracota y madera oscura
            "fondo_top": (48, 22, 14),
            "fondo_mid": (68, 30, 20),
            "fondo_bot": (26, 12, 8),
            "halo_1": (249, 115, 22, 24),
            "halo_2": (217, 119, 6, 20),
            "borde_marco": (254, 243, 199, 60),
            # Tipografías preferidas
            "fuente_titular": FONT_PLAYFAIR_DISPLAY,
            "fuente_subtitulo": FONT_MONTSERRAT_BOLD,
            "fuente_nombre": FONT_MONTSERRAT_BOLD,
            "fuente_precio": FONT_MONTSERRAT_BOLD,
            "fuente_cuerpo": FONT_INTER_REGULAR,
            # Encabezado
            "badge_bg": (42, 18, 12, 235),
            "badge_border": (234, 88, 12, 255),
            "badge_texto": (254, 240, 138, 255),
            "titulo_texto": (255, 253, 245, 255),
            "titulo_sombra": (15, 6, 4, 220),
            "linea_separadora": (234, 88, 12, 255),
            # Tarjetas de productos
            "tarjeta_bg": (34, 18, 14, 230),
            "tarjeta_borde": (254, 243, 199, 80),
            "tarjeta_lateral": (234, 88, 12, 255),
            "sombra_card": (12, 5, 3, 140),
            # Precios y textos
            "precio_caja_bg": (234, 88, 12, 45),
            "precio_caja_border": (251, 146, 60, 185),
            "precio_texto": (254, 240, 138, 255),
            "cat_texto": (251, 146, 60, 255),
            "nombre_texto": (255, 253, 245, 255),
            "desc_texto": (254, 237, 213, 230),
            # Columnas Carta Completa
            "col_panel_bg": (30, 15, 12, 235),
            "col_panel_border": (234, 88, 12, 90),
            "col_cat_header_bg": (54, 24, 18, 240),
            "col_cat_bar": (234, 88, 12, 255),
            "col_cat_texto": (254, 240, 138, 255),
            "col_puntos": (180, 83, 9, 170),
            # Pie de contacto
            "footer_bg": (32, 16, 12, 245),
            "footer_border": (234, 88, 12, 255),
            "footer_wa_icon": (34, 197, 94, 255),
            "footer_aviso": (254, 240, 138, 255),
        },
        ESTILO_FAST_FOOD_MOSTAZA: {
            "nombre": "Fast Food Mostaza (Pop & Cards)",
            # Fondo degradado vertical ámbar tostado profundo
            "fondo_top": (26, 20, 8),
            "fondo_mid": (38, 28, 10),
            "fondo_bot": (15, 12, 5),
            "halo_1": (234, 179, 8, 30),
            "halo_2": (220, 38, 38, 22),
            "borde_marco": (234, 179, 8, 85),
            # Tipografías preferidas
            "fuente_titular": FONT_BEBAS_NEUE,
            "fuente_subtitulo": FONT_MONTSERRAT_BOLD,
            "fuente_nombre": FONT_MONTSERRAT_BOLD,
            "fuente_precio": FONT_MONTSERRAT_BOLD,
            "fuente_cuerpo": FONT_INTER_REGULAR,
            # Encabezado
            "badge_bg": (234, 179, 8, 235),
            "badge_border": (202, 138, 4, 255),
            "badge_texto": (24, 18, 5, 255),
            "titulo_texto": (254, 240, 138, 255),
            "titulo_sombra": (10, 8, 2, 230),
            "linea_separadora": (234, 179, 8, 255),
            # Tarjetas de productos
            "tarjeta_bg": (26, 22, 14, 235),
            "tarjeta_borde": (234, 179, 8, 85),
            "tarjeta_lateral": (234, 179, 8, 255),
            "sombra_card": (10, 8, 2, 140),
            # Precios y textos
            "precio_caja_bg": (234, 179, 8, 55),
            "precio_caja_border": (250, 204, 21, 205),
            "precio_texto": (250, 204, 21, 255),
            "cat_texto": (250, 204, 21, 255),
            "nombre_texto": (255, 255, 255, 255),
            "desc_texto": (229, 231, 235, 230),
            # Columnas Carta Completa
            "col_panel_bg": (24, 20, 12, 235),
            "col_panel_border": (234, 179, 8, 95),
            "col_cat_header_bg": (48, 38, 14, 240),
            "col_cat_bar": (234, 179, 8, 255),
            "col_cat_texto": (250, 204, 21, 255),
            "col_puntos": (161, 98, 7, 180),
            # Pie de contacto
            "footer_bg": (24, 20, 10, 245),
            "footer_border": (234, 179, 8, 255),
            "footer_wa_icon": (34, 197, 94, 255),
            "footer_aviso": (250, 204, 21, 255),
        },
        ESTILO_TURQUESA_GLASS: {
            "nombre": "Turquesa Glass (Cards Modernas)",
            # Fondo degradado vertical petróleo / abisal
            "fondo_top": (4, 47, 46),
            "fondo_mid": (13, 76, 82),
            "fondo_bot": (2, 28, 30),
            "halo_1": (20, 184, 166, 24),
            "halo_2": (45, 212, 191, 18),
            "borde_marco": (45, 212, 191, 70),
            # Tipografías preferidas
            "fuente_titular": FONT_MONTSERRAT_BOLD,
            "fuente_subtitulo": FONT_MONTSERRAT_BOLD,
            "fuente_nombre": FONT_MONTSERRAT_BOLD,
            "fuente_precio": FONT_MONTSERRAT_BOLD,
            "fuente_cuerpo": FONT_INTER_REGULAR,
            # Encabezado
            "badge_bg": (4, 47, 46, 230),
            "badge_border": (45, 212, 191, 255),
            "badge_texto": (94, 234, 212, 255),
            "titulo_texto": (240, 253, 250, 255),
            "titulo_sombra": (2, 20, 22, 220),
            "linea_separadora": (20, 184, 166, 255),
            # Tarjetas de productos (Cristal satinado)
            "tarjeta_bg": (8, 48, 55, 205),
            "tarjeta_borde": (94, 234, 212, 100),
            "tarjeta_lateral": (45, 212, 191, 255),
            "sombra_card": (2, 16, 18, 130),
            # Precios y textos
            "precio_caja_bg": (20, 184, 166, 45),
            "precio_caja_border": (45, 212, 191, 185),
            "precio_texto": (45, 212, 191, 255),
            "cat_texto": (94, 234, 212, 255),
            "nombre_texto": (255, 255, 255, 255),
            "desc_texto": (204, 251, 241, 230),
            # Columnas Carta Completa
            "col_panel_bg": (7, 42, 48, 230),
            "col_panel_border": (45, 212, 191, 90),
            "col_cat_header_bg": (12, 60, 68, 240),
            "col_cat_bar": (45, 212, 191, 255),
            "col_cat_texto": (94, 234, 212, 255),
            "col_puntos": (15, 118, 110, 175),
            # Pie de contacto
            "footer_bg": (4, 47, 46, 245),
            "footer_border": (20, 184, 166, 255),
            "footer_wa_icon": (34, 197, 94, 255),
            "footer_aviso": (94, 234, 212, 255),
        },
        ESTILO_GOURMET_BISTRO: {
            "nombre": "Gourmet Bistró (Elegante & Minimal)",
            # Fondo degradado vertical medianoche y grafito puro
            "fondo_top": (12, 14, 20),
            "fondo_mid": (20, 22, 30),
            "fondo_bot": (8, 9, 14),
            "halo_1": (212, 175, 55, 18),
            "halo_2": (245, 230, 200, 12),
            "borde_marco": (212, 175, 55, 70),
            # Tipografías preferidas
            "fuente_titular": FONT_PLAYFAIR_DISPLAY,
            "fuente_subtitulo": FONT_MONTSERRAT_BOLD,
            "fuente_nombre": FONT_MONTSERRAT_BOLD,
            "fuente_precio": FONT_MONTSERRAT_BOLD,
            "fuente_cuerpo": FONT_INTER_REGULAR,
            # Encabezado
            "badge_bg": (18, 20, 28, 235),
            "badge_border": (212, 175, 55, 255),
            "badge_texto": (245, 230, 200, 255),
            "titulo_texto": (255, 252, 245, 255),
            "titulo_sombra": (0, 0, 0, 225),
            "linea_separadora": (212, 175, 55, 255),
            # Tarjetas de productos
            "tarjeta_bg": (18, 20, 28, 220),
            "tarjeta_borde": (212, 175, 55, 85),
            "tarjeta_lateral": (212, 175, 55, 255),
            "sombra_card": (0, 0, 0, 140),
            # Precios y textos
            "precio_caja_bg": (212, 175, 55, 32),
            "precio_caja_border": (212, 175, 55, 165),
            "precio_texto": (245, 230, 200, 255),
            "cat_texto": (212, 175, 55, 255),
            "nombre_texto": (255, 252, 245, 255),
            "desc_texto": (226, 232, 240, 225),
            # Columnas Carta Completa
            "col_panel_bg": (16, 18, 25, 230),
            "col_panel_border": (212, 175, 55, 80),
            "col_cat_header_bg": (28, 30, 42, 240),
            "col_cat_bar": (212, 175, 55, 255),
            "col_cat_texto": (245, 230, 200, 255),
            "col_puntos": (161, 134, 53, 175),
            # Pie de contacto
            "footer_bg": (14, 16, 24, 245),
            "footer_border": (212, 175, 55, 255),
            "footer_wa_icon": (34, 197, 94, 255),
            "footer_aviso": (245, 230, 200, 255),
        },
    }

    def __init__(
        self,
        templates_dir: str = "templates",
        output_dir: str = "output",
        fonts_dir: str = "assets/fonts",
    ) -> None:
        """
        Inicializa el generador de flyers asegurando los directorios de entrada, salida y fuentes.
        Verifica o descarga las fuentes tipográficas en `assets/fonts/` de manera transparente.
        """
        self.templates_dir: str = os.path.abspath(templates_dir)
        self.output_dir: str = os.path.abspath(output_dir)
        self.fonts_dir: str = os.path.abspath(fonts_dir)

        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.fonts_dir, exist_ok=True)

        # Descarga o verificación automática de fuentes TTF libres
        try:
            asegurar_fuentes_ttf(self.fonts_dir)
        except Exception as exc:
            logger.warning("Verificación de fuentes TTF diferida: %s", exc)

        self._cache_fondos: Dict[str, Image.Image] = {}
        self.default_template_path: str = os.path.join(
            self.templates_dir, "plantilla_oscura_default.png"
        )
        self.asegurar_plantilla_por_defecto()

    def _obtener_config_estilo(self, nombre_estilo: str) -> Dict[str, Any]:
        """
        Retorna la configuración cromática y tipográfica del estilo solicitado.
        Acepta alias retrocompatibles ('Pizarra Oscura', 'Turquesa Gourmet', 'Rojo Rústico').
        """
        mapeo_retrocompatible = {
            "Pizarra Oscura": self.ESTILO_PIZARRA_BURGUER,
            "Turquesa Gourmet": self.ESTILO_TURQUESA_GLASS,
            "Rojo Rústico": self.ESTILO_PIZZERIA_RUSTICA,
        }
        estilo_resuelto = mapeo_retrocompatible.get(nombre_estilo, nombre_estilo)
        return self.ESTILOS_CONFIG.get(
            estilo_resuelto, self.ESTILOS_CONFIG[self.ESTILO_PIZARRA_BURGUER]
        )

    def _cargar_fuente(
        self,
        tamano: int,
        negrita: bool = False,
        archivo_preferido: Optional[str] = None,
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """
        Carga una fuente TrueType priorizando la carpeta 'assets/fonts/'.
        Si la fuente solicitada o las de la carpeta local no están disponibles,
        aplica un fallback robusto a fuentes del sistema ('DejaVuSans', 'Arial', etc.)
        o a la fuente por defecto de Pillow, garantizando que NUNCA se arroje excepción.
        """
        # 1. Intentar con el archivo preferido en 'assets/fonts/'
        if archivo_preferido:
            ruta_preferida = os.path.join(self.fonts_dir, archivo_preferido)
            if os.path.exists(ruta_preferida):
                try:
                    return ImageFont.truetype(ruta_preferida, tamano)
                except (OSError, ValueError):
                    pass

        # 2. Intentar con las fuentes estándar del proyecto en 'assets/fonts/'
        nombres_locales = (
            [self.FONT_MONTSERRAT_BOLD, self.FONT_BEBAS_NEUE, self.FONT_PLAYFAIR_DISPLAY]
            if negrita
            else [self.FONT_INTER_REGULAR, self.FONT_PLAYFAIR_DISPLAY, self.FONT_MONTSERRAT_BOLD]
        )
        for nombre in nombres_locales:
            ruta = os.path.join(self.fonts_dir, nombre)
            if os.path.exists(ruta):
                try:
                    return ImageFont.truetype(ruta, tamano)
                except (OSError, ValueError):
                    continue

        # 3. Fallback a fuentes TrueType del sistema operativo (Linux, Windows, macOS)
        candidatos_bold = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "DejaVuSans-Bold.ttf",
            "arialbd.ttf",
        ]
        candidatos_regular = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "DejaVuSans.ttf",
            "arial.ttf",
        ]

        lista_busqueda = candidatos_bold if negrita else candidatos_regular
        for ruta in lista_busqueda:
            try:
                if os.path.exists(ruta):
                    return ImageFont.truetype(ruta, tamano)
            except (OSError, ValueError):
                continue

        for nombre_alt in (
            ["DejaVuSans-Bold.ttf", "arialbd.ttf"]
            if negrita
            else ["DejaVuSans.ttf", "arial.ttf"]
        ):
            try:
                return ImageFont.truetype(nombre_alt, tamano)
            except (OSError, ValueError):
                continue

        # 4. Fallback final infalible de Pillow
        try:
            return ImageFont.load_default(size=tamano)
        except TypeError:
            return ImageFont.load_default()

    def _renderizar_fondo_programatico(self, estilo: str) -> Image.Image:
        """
        Genera programáticamente un lienzo vertical 1080x1920 con el degradado vertical
        y geometrías decorativas correspondientes a la plantilla elegida.
        Utiliza caché en memoria para previsualización inmediata.
        """
        cfg = self._obtener_config_estilo(estilo)
        clave_cache = cfg["nombre"]
        if clave_cache in self._cache_fondos:
            return self._cache_fondos[clave_cache].copy()

        base = Image.new("RGBA", (self.ANCHO, self.ALTO), cfg["fondo_top"] + (255,))
        draw = ImageDraw.Draw(base)

        r_ini, g_ini, b_ini = cfg["fondo_top"]
        r_med, g_med, b_med = cfg["fondo_mid"]
        r_fin, g_fin, b_fin = cfg["fondo_bot"]

        # Degradado vertical tricolor
        paso_y = 2
        for y in range(0, self.ALTO, paso_y):
            t = y / float(self.ALTO)
            if t < 0.5:
                factor = t / 0.5
                r = int(r_ini + (r_med - r_ini) * factor)
                g = int(g_ini + (g_med - g_ini) * factor)
                b = int(b_ini + (b_med - b_ini) * factor)
            else:
                factor = (t - 0.5) / 0.5
                r = int(r_med + (r_fin - r_med) * factor)
                g = int(g_med + (g_fin - g_med) * factor)
                b = int(b_med + (b_fin - b_med) * factor)
            draw.rectangle([0, y, self.ANCHO, y + paso_y], fill=(r, g, b, 255))

        # Capa de halos luminosos decorativos
        capa_halos = Image.new("RGBA", (self.ANCHO, self.ALTO), (0, 0, 0, 0))
        draw_halos = ImageDraw.Draw(capa_halos)

        # Halo superior
        cx1, cy1, r1 = 180, 240, 480
        draw_halos.ellipse(
            [cx1 - r1, cy1 - r1, cx1 + r1, cy1 + r1],
            fill=cfg["halo_1"],
        )

        # Halo inferior opuesto
        cx2, cy2, r2 = self.ANCHO - 160, self.ALTO - 380, 520
        draw_halos.ellipse(
            [cx2 - r2, cy2 - r2, cx2 + r2, cy2 + r2],
            fill=cfg["halo_2"],
        )

        # Marco interior elegante
        draw_halos.rounded_rectangle(
            [28, 28, self.ANCHO - 28, self.ALTO - 28],
            radius=36,
            outline=cfg["borde_marco"],
            width=2,
        )

        base.alpha_composite(capa_halos)
        self._cache_fondos[clave_cache] = base
        return base.copy()

    def _preparar_lienzo_base(
        self, plantilla_path: Optional[str] = None, estilo: str = ESTILO_PIZARRA_BURGUER
    ) -> Image.Image:
        """
        Prepara el lienzo base (1080x1920 px RGBA). Si no se proporciona imagen externa
        o no existe, utiliza la plantilla programática correspondiente al estilo.
        """
        if plantilla_path and os.path.exists(plantilla_path):
            try:
                with Image.open(plantilla_path) as img:
                    convertida = img.convert("RGBA")
                    if convertida.size != (self.ANCHO, self.ALTO):
                        return ImageOps.fit(
                            convertida,
                            (self.ANCHO, self.ALTO),
                            method=Image.Resampling.LANCZOS,
                            centering=(0.5, 0.5),
                        )
                    return convertida
            except Exception as exc:
                logger.warning(
                    "Error al cargar la plantilla externa '%s': %s. Usando estilo programático.",
                    plantilla_path,
                    exc,
                )

        return self._renderizar_fondo_programatico(estilo)

    def _aplicar_marca_agua(
        self,
        lienzo: Image.Image,
        logo: Image.Image,
        opacidad: float = 0.12,
        max_tam: Tuple[int, int] = (620, 620),
        y_centro: int = 980,
    ) -> None:
        """
        Genera y fusiona una capa decorativa translúcida del logo comercial (10%-15% de opacidad)
        en el fondo del lienzo mediante alpha compositing, por debajo de las tarjetas de contenido.
        """
        try:
            marca = logo.copy().convert("RGBA")
            marca.thumbnail(max_tam, Image.Resampling.LANCZOS)
            r, g, b, a = marca.split()

            # Multiplicar el canal alfa por el factor de opacidad deseado (0.10 a 0.15)
            factor = max(0.08, min(0.20, opacidad))
            a_translucida = a.point(lambda p: int(p * factor))
            marca.putalpha(a_translucida)

            mw, mh = marca.size
            pos_x = (self.ANCHO - mw) // 2
            pos_y = max(240, y_centro - (mh // 2))

            capa_marca = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
            capa_marca.paste(marca, (pos_x, pos_y), marca)
            lienzo.alpha_composite(capa_marca)
        except Exception as exc:
            logger.warning("No se pudo aplicar la marca de agua translúcida: %s", exc)

    def _medir_texto(
        self,
        draw: ImageDraw.ImageDraw,
        texto: str,
        fuente: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> Tuple[int, int]:
        """Calcula el ancho y alto en píxeles de una cadena con la fuente dada."""
        bbox = draw.textbbox((0, 0), str(texto), font=fuente)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _ajustar_texto_multilinea(
        self,
        draw: ImageDraw.ImageDraw,
        texto: str,
        fuente: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        max_ancho: int,
        max_lineas: int = 2,
    ) -> List[str]:
        """
        Divide un texto en múltiples líneas que no superen `max_ancho` en píxeles,
        truncando con '...' si excede `max_lineas`.
        """
        texto_limpio = " ".join(str(texto).strip().split())
        if not texto_limpio:
            return []

        palabras = texto_limpio.split(" ")
        lineas: List[str] = []
        linea_actual = ""

        for palabra in palabras:
            prueba = f"{linea_actual} {palabra}".strip() if linea_actual else palabra
            ancho_prueba, _ = self._medir_texto(draw, prueba, fuente)
            if ancho_prueba <= max_ancho:
                linea_actual = prueba
            else:
                if linea_actual:
                    lineas.append(linea_actual)
                    linea_actual = palabra
                else:
                    lineas.append(palabra)
                    linea_actual = ""

        if linea_actual:
            lineas.append(linea_actual)

        if len(lineas) > max_lineas:
            lineas = lineas[:max_lineas]
            ultima = lineas[-1]
            while ultima and self._medir_texto(draw, ultima + "...", fuente)[0] > max_ancho:
                ultima = ultima[:-1].rstrip()
            lineas[-1] = f"{ultima}..."

        return lineas

    def _dibujar_encabezado(
        self,
        lienzo: Image.Image,
        titulo: str,
        config: Dict[str, Any],
        texto_badge: str = "•  MENÚ & PROMOCIONES DEL DÍA  •",
        logo_img: Optional[Image.Image] = None,
    ) -> int:
        """
        Dibuja el bloque superior de encabezado institucional. Si existe un logo,
        lo estampa de forma proporcional en la parte superior y ajusta armónicamente
        la posición del badge y el título.
        """
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        y_cursor = 48

        # 1. Estampado de logo comercial si está cargado
        if logo_img is not None:
            try:
                logo_hdr = logo_img.copy().convert("RGBA")
                logo_hdr.thumbnail((260, 110), Image.Resampling.LANCZOS)
                lw, lh = logo_hdr.size
                lx = (self.ANCHO - lw) // 2
                ly = y_cursor
                capa.paste(logo_hdr, (lx, ly), logo_hdr)
                y_cursor = ly + lh + 16
            except Exception as exc:
                logger.warning("No se pudo estampar el logo en el header: %s", exc)

        # 2. Badge superior
        fuente_badge = self._cargar_fuente(
            24,
            negrita=True,
            archivo_preferido=config.get("fuente_subtitulo", self.FONT_MONTSERRAT_BOLD),
        )
        ancho_b, alto_b = self._medir_texto(draw, texto_badge, fuente_badge)
        pad_x, pad_y = 34, 14
        bx1 = (self.ANCHO - (ancho_b + pad_x * 2)) // 2
        by1 = y_cursor
        bx2 = bx1 + ancho_b + pad_x * 2
        by2 = by1 + alto_b + pad_y * 2

        draw.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=26,
            fill=config["badge_bg"],
            outline=config["badge_border"],
            width=2,
        )
        draw.text(
            (self.ANCHO // 2, (by1 + by2) // 2),
            texto_badge,
            font=fuente_badge,
            fill=config["badge_texto"],
            anchor="mm",
        )

        # 3. Título principal
        titulo_limpio = (titulo.strip() if titulo and titulo.strip() else "PROMOS DE HOY").upper()
        tamano_titulo = 76 if config.get("fuente_titular") == self.FONT_BEBAS_NEUE else 64
        fuente_titulo = self._cargar_fuente(
            tamano_titulo,
            negrita=True,
            archivo_preferido=config.get("fuente_titular", self.FONT_BEBAS_NEUE),
        )
        while tamano_titulo > 36:
            ancho_t, _ = self._medir_texto(draw, titulo_limpio, fuente_titulo)
            if ancho_t <= (self.ANCHO - 120):
                break
            tamano_titulo -= 4
            fuente_titulo = self._cargar_fuente(
                tamano_titulo,
                negrita=True,
                archivo_preferido=config.get("fuente_titular", self.FONT_BEBAS_NEUE),
            )

        y_titulo = by2 + 54
        draw.text(
            (self.ANCHO // 2 + 3, y_titulo + 4),
            titulo_limpio,
            font=fuente_titulo,
            fill=config["titulo_sombra"],
            anchor="mm",
        )
        draw.text(
            (self.ANCHO // 2, y_titulo),
            titulo_limpio,
            font=fuente_titulo,
            fill=config["titulo_texto"],
            anchor="mm",
        )

        # 4. Línea divisoria decorativa
        y_linea = y_titulo + 48
        ancho_linea = 280
        draw.rounded_rectangle(
            [
                (self.ANCHO - ancho_linea) // 2,
                y_linea,
                (self.ANCHO + ancho_linea) // 2,
                y_linea + 6,
            ],
            radius=3,
            fill=config["linea_separadora"],
        )

        lienzo.alpha_composite(capa)
        return y_linea + 28

    def _dibujar_bloque_productos(
        self,
        lienzo: Image.Image,
        productos: List[Producto],
        y_inicio: int,
        y_fin: int,
        config: Dict[str, Any],
    ) -> None:
        """
        Renderiza las tarjetas de los productos seleccionados en 'Modo Promos Destacadas'
        (1 a 6 tarjetas grandes con nombre, ingredientes y precio destacado).
        """
        items = productos[: self.MAX_PRODUCTOS]
        cantidad = len(items)
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        if cantidad == 0:
            fuente_vacio = self._cargar_fuente(
                34,
                negrita=True,
                archivo_preferido=config.get("fuente_titular", self.FONT_BEBAS_NEUE),
            )
            y_centro = (y_inicio + y_fin) // 2
            draw.text(
                (self.ANCHO // 2, y_centro),
                "Seleccione hasta 6 platos del menú",
                font=fuente_vacio,
                fill=config["desc_texto"],
                anchor="mm",
            )
            lienzo.alpha_composite(capa)
            return

        alto_disponible = y_fin - y_inicio
        margen_x = 64
        x1_card = margen_x
        x2_card = self.ANCHO - margen_x

        if cantidad == 1:
            alto_card = 270
            espacio = 0
        elif cantidad == 2:
            alto_card = 250
            espacio = 44
        elif cantidad == 3:
            alto_card = 235
            espacio = 36
        elif cantidad == 4:
            alto_card = 220
            espacio = 28
        elif cantidad == 5:
            alto_card = 196
            espacio = 22
        else:
            espacio = 18
            alto_card = min(176, (alto_disponible - (espacio * (cantidad - 1))) // cantidad)

        alto_bloque_total = (alto_card * cantidad) + (espacio * (cantidad - 1))
        y_actual = y_inicio + max(0, (alto_disponible - alto_bloque_total) // 2)

        es_compacto = cantidad >= 5
        fuente_cat = self._cargar_fuente(
            20 if es_compacto else 22,
            negrita=True,
            archivo_preferido=config.get("fuente_subtitulo", self.FONT_MONTSERRAT_BOLD),
        )
        fuente_nombre = self._cargar_fuente(
            32 if es_compacto else 36,
            negrita=True,
            archivo_preferido=config.get("fuente_nombre", self.FONT_MONTSERRAT_BOLD),
        )
        fuente_desc = self._cargar_fuente(
            23 if es_compacto else 25,
            negrita=False,
            archivo_preferido=config.get("fuente_cuerpo", self.FONT_INTER_REGULAR),
        )
        fuente_precio = self._cargar_fuente(
            44 if es_compacto else 50,
            negrita=True,
            archivo_preferido=config.get("fuente_precio", self.FONT_MONTSERRAT_BOLD),
        )

        for prod in items:
            y1 = y_actual
            y2 = y1 + alto_card

            # Sombra suave
            draw.rounded_rectangle(
                [x1_card + 6, y1 + 8, x2_card + 6, y2 + 8],
                radius=26,
                fill=config["sombra_card"],
            )

            # Tarjeta principal
            draw.rounded_rectangle(
                [x1_card, y1, x2_card, y2],
                radius=26,
                fill=config["tarjeta_bg"],
                outline=config["tarjeta_borde"],
                width=2,
            )

            # Barra lateral de acento
            draw.rounded_rectangle(
                [x1_card, y1 + 18, x1_card + 12, y2 - 18],
                radius=6,
                fill=config["tarjeta_lateral"],
            )

            # Caja destacada de precio
            texto_precio = f"$ {prod.precio:,.0f}"
            ancho_precio, alto_precio = self._medir_texto(draw, texto_precio, fuente_precio)

            pad_precio_x = 24
            caja_precio_w = ancho_precio + (pad_precio_x * 2)
            caja_precio_h = min(alto_card - 36, max(78, alto_precio + 34))
            px2 = x2_card - 26
            px1 = px2 - caja_precio_w
            py1 = y1 + (alto_card - caja_precio_h) // 2
            py2 = py1 + caja_precio_h

            draw.rounded_rectangle(
                [px1, py1, px2, py2],
                radius=20,
                fill=config["precio_caja_bg"],
                outline=config["precio_caja_border"],
                width=2,
            )
            draw.text(
                ((px1 + px2) // 2, (py1 + py2) // 2),
                texto_precio,
                font=fuente_precio,
                fill=config["precio_texto"],
                anchor="mm",
            )

            x_texto = x1_card + 36
            max_ancho_texto = max(280, px1 - x_texto - 26)
            y_cursor = y1 + (16 if es_compacto else 22)

            # Categoría
            cat_upper = prod.categoria.strip().upper()
            draw.text(
                (x_texto, y_cursor),
                cat_upper,
                font=fuente_cat,
                fill=config["cat_texto"],
            )
            _, alto_cat = self._medir_texto(draw, cat_upper, fuente_cat)
            y_cursor += alto_cat + (6 if es_compacto else 10)

            # Nombre del producto
            lineas_nombre = self._ajustar_texto_multilinea(
                draw,
                prod.nombre,
                fuente_nombre,
                max_ancho=max_ancho_texto,
                max_lineas=1 if es_compacto else 2,
            )
            for linea_n in lineas_nombre:
                draw.text(
                    (x_texto, y_cursor),
                    linea_n,
                    font=fuente_nombre,
                    fill=config["nombre_texto"],
                )
                _, alto_n = self._medir_texto(draw, linea_n, fuente_nombre)
                y_cursor += alto_n + 4

            # Descripción de ingredientes
            if prod.descripcion and y_cursor + 24 < (y2 - 14):
                y_cursor += 4
                max_lineas_desc = 1 if (es_compacto or len(lineas_nombre) > 1) else 2
                lineas_desc = self._ajustar_texto_multilinea(
                    draw,
                    prod.descripcion,
                    fuente_desc,
                    max_ancho=max_ancho_texto,
                    max_lineas=max_lineas_desc,
                )
                for linea_d in lineas_desc:
                    if y_cursor + 22 > (y2 - 10):
                        break
                    draw.text(
                        (x_texto, y_cursor),
                        linea_d,
                        font=fuente_desc,
                        fill=config["desc_texto"],
                    )
                    _, alto_d = self._medir_texto(draw, linea_d, fuente_desc)
                    y_cursor += alto_d + 4

            y_actual += alto_card + espacio

        lienzo.alpha_composite(capa)

    # =========================================================================
    # MODO MENÚ COMPLETO POR SECCIONES (2 COLUMNAS VERTICALES BALANCEADAS)
    # =========================================================================

    @staticmethod
    def _agrupar_productos_por_categoria(
        productos: List[Producto],
    ) -> List[Tuple[str, List[Producto]]]:
        """
        Agrupa los productos por 'Categoría', respetando el orden sugerido
        en Producto.CATEGORIAS_SUGERIDAS y luego alfabético.
        """
        mapa: Dict[str, List[Producto]] = {}
        for prod in productos:
            cat = (
                prod.categoria.strip()
                if prod.categoria and prod.categoria.strip()
                else "Especialidades"
            )
            mapa.setdefault(cat, []).append(prod)

        orden_sugerido = {
            cat_sug: idx for idx, cat_sug in enumerate(Producto.CATEGORIAS_SUGERIDAS)
        }

        def _criterio_orden(cat_nombre: str) -> Tuple[int, str]:
            return (orden_sugerido.get(cat_nombre, 999), cat_nombre.lower())

        categorias_ordenadas = sorted(mapa.keys(), key=_criterio_orden)
        return [(cat, mapa[cat]) for cat in categorias_ordenadas]

    @classmethod
    def _distribuir_categorias_en_dos_columnas(
        cls,
        productos: List[Producto],
    ) -> Tuple[List[Tuple[str, List[Producto]]], List[Tuple[str, List[Producto]]]]:
        """
        Distribuye balanceadamente las categorías en 2 columnas verticales
        para equilibrar la altura visual de ambos bloques.
        """
        secciones_base = cls._agrupar_productos_por_categoria(productos)
        if not secciones_base:
            return [], []
        if len(secciones_base) == 1:
            return secciones_base, []

        def _peso_seccion(sec: Tuple[str, List[Producto]]) -> int:
            return 2 + len(sec[1])

        peso_total = sum(_peso_seccion(s) for s in secciones_base)
        mitad = peso_total / 2.0

        col_izq: List[Tuple[str, List[Producto]]] = []
        col_der: List[Tuple[str, List[Producto]]] = []
        acum_izq = 0

        for sec in secciones_base:
            peso_actual = _peso_seccion(sec)
            if not col_izq:
                col_izq.append(sec)
                acum_izq += peso_actual
            elif abs((acum_izq + peso_actual) - mitad) < abs(acum_izq - mitad) or len(col_der) == 0:
                if len(col_izq) < len(secciones_base) - 1:
                    col_izq.append(sec)
                    acum_izq += peso_actual
                else:
                    col_der.append(sec)
            else:
                col_der.append(sec)

        return col_izq, col_der

    def _dibujar_renglon_compacto_menu(
        self,
        draw: ImageDraw.ImageDraw,
        nombre_plato: str,
        precio: float,
        x_izq: int,
        x_der: int,
        y_centro: int,
        fuente_plato: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        fuente_precio: ImageFont.FreeTypeFont | ImageFont.ImageFont,
        color_plato: Tuple[int, int, int, int],
        color_puntos: Tuple[int, int, int, int],
        color_precio: Tuple[int, int, int, int],
    ) -> None:
        """
        Dibuja un renglón compacto con puntos guía alineados:
        'Nombre del Plato . . . . . $ Precio'
        """
        texto_precio = f"$ {precio:,.0f}"
        ancho_precio, alto_precio = self._medir_texto(draw, texto_precio, fuente_precio)
        draw.text(
            (x_der, y_centro),
            texto_precio,
            font=fuente_precio,
            fill=color_precio,
            anchor="rm",
        )

        ancho_disp_plato = max(120, (x_der - ancho_precio - 20) - x_izq)
        nombre_ajustado = str(nombre_plato).strip()
        while (
            nombre_ajustado
            and self._medir_texto(draw, nombre_ajustado, fuente_plato)[0] > ancho_disp_plato
        ):
            nombre_ajustado = nombre_ajustado[:-1].rstrip()
            if self._medir_texto(draw, nombre_ajustado + "...", fuente_plato)[0] <= ancho_disp_plato:
                nombre_ajustado = f"{nombre_ajustado}..."
                break

        draw.text(
            (x_izq, y_centro),
            nombre_ajustado,
            font=fuente_plato,
            fill=color_plato,
            anchor="lm",
        )

        ancho_plato_real, _ = self._medir_texto(draw, nombre_ajustado, fuente_plato)
        inicio_puntos = x_izq + ancho_plato_real + 10
        fin_puntos = x_der - ancho_precio - 10

        if fin_puntos > inicio_puntos + 14:
            ancho_punto, _ = self._medir_texto(draw, ". ", fuente_plato)
            ancho_punto = max(6, ancho_punto)
            cant_puntos = max(1, int((fin_puntos - inicio_puntos) // ancho_punto))
            cadena_puntos = ". " * cant_puntos
            while (
                cadena_puntos
                and self._medir_texto(draw, cadena_puntos, fuente_plato)[0] > (fin_puntos - inicio_puntos)
            ):
                cadena_puntos = cadena_puntos[:-2]

            draw.text(
                (inicio_puntos, y_centro - 1),
                cadena_puntos,
                font=fuente_plato,
                fill=color_puntos,
                anchor="lm",
            )

    def _dibujar_bloque_menu_completo(
        self,
        lienzo: Image.Image,
        productos: List[Producto],
        y_inicio: int,
        y_fin: int,
        config: Dict[str, Any],
    ) -> None:
        """
        Renderiza la carta completa clasificada por categorías en un layout de
        2 columnas verticales balanceadas con interlineado dinámico.
        """
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        if not productos:
            fuente_vacio = self._cargar_fuente(
                32,
                negrita=True,
                archivo_preferido=config.get("fuente_titular", self.FONT_BEBAS_NEUE),
            )
            draw.text(
                (self.ANCHO // 2, (y_inicio + y_fin) // 2),
                "No hay productos disponibles para exportar el Menú Completo",
                font=fuente_vacio,
                fill=config["desc_texto"],
                anchor="mm",
            )
            lienzo.alpha_composite(capa)
            return

        col_izq, col_der = self._distribuir_categorias_en_dos_columnas(productos)

        margen_ext = 48
        gap_columnas = 28
        ancho_col = (self.ANCHO - (margen_ext * 2) - gap_columnas) // 2
        alto_disponible = y_fin - y_inicio

        x1_col_izq = margen_ext
        x2_col_izq = x1_col_izq + ancho_col
        x1_col_der = x2_col_izq + gap_columnas
        x2_col_der = x1_col_der + ancho_col

        color_panel = config["col_panel_bg"]
        color_borde = config["col_panel_border"]
        color_header_bg = config["col_cat_header_bg"]
        color_header_bar = config["col_cat_bar"]
        color_texto_cat = config["col_cat_texto"]
        color_texto_plato = config["nombre_texto"]
        color_puntos = config["col_puntos"]
        color_precio = config["precio_texto"]

        # Dibujar contenedores de ambas columnas
        for cx1, cx2 in ((x1_col_izq, x2_col_izq), (x1_col_der, x2_col_der)):
            draw.rounded_rectangle(
                [cx1 + 5, y_inicio + 7, cx2 + 5, y_fin + 7],
                radius=24,
                fill=config["sombra_card"],
            )
            draw.rounded_rectangle(
                [cx1, y_inicio, cx2, y_fin],
                radius=24,
                fill=color_panel,
                outline=color_borde,
                width=2,
            )

        pad_v = 24
        alto_util = max(200, alto_disponible - (pad_v * 2))

        base_alto_cat = 46
        base_alto_renglon = 40
        base_gap_cat = 22

        def _altura_requerida(
            secciones_col: List[Tuple[str, List[Producto]]],
            h_cat: int,
            h_row: int,
            g_cat: int,
        ) -> int:
            if not secciones_col:
                return 0
            cant_cats = len(secciones_col)
            cant_items = sum(len(items) for _, items in secciones_col)
            return (cant_cats * h_cat) + (max(0, cant_cats - 1) * g_cat) + (cant_items * h_row)

        req_izq = _altura_requerida(col_izq, base_alto_cat, base_alto_renglon, base_gap_cat)
        req_der = _altura_requerida(col_der, base_alto_cat, base_alto_renglon, base_gap_cat)
        max_req = max(req_izq, req_der, 1)

        if max_req > alto_util:
            escala = alto_util / float(max_req)
        else:
            escala = min(1.20, max(1.0, (alto_util * 0.80) / float(max_req)))

        tam_fuente_cat = max(16, min(28, int(23 * escala)))
        tam_fuente_plato = max(13, min(22, int(19 * escala)))
        tam_fuente_precio = max(14, min(24, int(20 * escala)))

        alto_cat = max(26, int(base_alto_cat * escala))
        alto_renglon_base = max(20, int(base_alto_renglon * escala))
        gap_cat_base = max(8, int(base_gap_cat * escala))

        fuente_cat = self._cargar_fuente(
            tam_fuente_cat,
            negrita=True,
            archivo_preferido=config.get("fuente_titular", self.FONT_BEBAS_NEUE),
        )
        fuente_plato = self._cargar_fuente(
            tam_fuente_plato,
            negrita=False,
            archivo_preferido=config.get("fuente_cuerpo", self.FONT_INTER_REGULAR),
        )
        fuente_precio = self._cargar_fuente(
            tam_fuente_precio,
            negrita=True,
            archivo_preferido=config.get("fuente_precio", self.FONT_MONTSERRAT_BOLD),
        )

        for secciones_col, cx1, cx2 in (
            (col_izq, x1_col_izq, x2_col_izq),
            (col_der, x1_col_der, x2_col_der),
        ):
            if not secciones_col:
                continue

            cant_cats = len(secciones_col)
            cant_items = sum(len(items) for _, items in secciones_col)
            altura_col = _altura_requerida(
                secciones_col, alto_cat, alto_renglon_base, gap_cat_base
            )
            sobrante = max(0, alto_util - altura_col)

            extra_por_renglon = 0
            extra_por_cat = 0
            if sobrante > 0 and cant_items > 0:
                extra_por_renglon = min(16, int((sobrante * 0.45) // max(1, cant_items)))
                if cant_cats > 1:
                    extra_por_cat = min(28, int((sobrante * 0.35) // (cant_cats - 1)))

            alto_renglon_col = alto_renglon_base + extra_por_renglon
            gap_cat_col = gap_cat_base + extra_por_cat

            altura_final_col = _altura_requerida(
                secciones_col, alto_cat, alto_renglon_col, gap_cat_col
            )
            offset_centrado = max(0, (alto_util - altura_final_col) // 3)
            y_cursor = y_inicio + pad_v + offset_centrado

            x_int_izq = cx1 + 20
            x_int_der = cx2 - 20

            for idx_sec, (nombre_cat, items_cat) in enumerate(secciones_col):
                hy1 = y_cursor
                hy2 = hy1 + alto_cat - 4

                draw.rounded_rectangle(
                    [x_int_izq, hy1, x_int_der, hy2],
                    radius=10,
                    fill=color_header_bg,
                )
                draw.rounded_rectangle(
                    [x_int_izq, hy1 + 4, x_int_izq + 6, hy2 - 4],
                    radius=3,
                    fill=color_header_bar,
                )
                draw.line(
                    [(x_int_izq, hy2), (x_int_der, hy2)],
                    fill=color_borde,
                    width=1,
                )

                texto_cat = f"▸  {nombre_cat.strip().upper()}"
                draw.text(
                    (x_int_izq + 16, (hy1 + hy2) // 2),
                    texto_cat,
                    font=fuente_cat,
                    fill=color_texto_cat,
                    anchor="lm",
                )

                y_cursor += alto_cat + 4

                for prod in items_cat:
                    y_centro_fila = y_cursor + (alto_renglon_col // 2) - 2
                    self._dibujar_renglon_compacto_menu(
                        draw=draw,
                        nombre_plato=prod.nombre,
                        precio=prod.precio,
                        x_izq=x_int_izq + 6,
                        x_der=x_int_der - 4,
                        y_centro=y_centro_fila,
                        fuente_plato=fuente_plato,
                        fuente_precio=fuente_precio,
                        color_plato=color_texto_plato,
                        color_puntos=color_puntos,
                        color_precio=color_precio,
                    )
                    y_cursor += alto_renglon_col

                if idx_sec < cant_cats - 1:
                    y_cursor += gap_cat_col

        lienzo.alpha_composite(capa)

    def _dibujar_footer(
        self, lienzo: Image.Image, whatsapp: str, config: Dict[str, Any]
    ) -> None:
        """
        Dibuja la barra inferior fija de contacto con el número de WhatsApp,
        ícono de mensajería y la leyenda de entrega adaptada a la plantilla.
        """
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        margen_x = 64
        fy1 = 1672
        fy2 = 1852

        draw.rounded_rectangle(
            [margen_x + 4, fy1 + 6, self.ANCHO - margen_x + 4, fy2 + 6],
            radius=28,
            fill=config["sombra_card"],
        )
        draw.rounded_rectangle(
            [margen_x, fy1, self.ANCHO - margen_x, fy2],
            radius=28,
            fill=config["footer_bg"],
            outline=config["footer_border"],
            width=3,
        )

        fuente_wa = self._cargar_fuente(
            36, negrita=True, archivo_preferido=self.FONT_MONTSERRAT_BOLD
        )
        fuente_aviso = self._cargar_fuente(
            24, negrita=False, archivo_preferido=self.FONT_INTER_REGULAR
        )

        wa_limpio = whatsapp.strip() if whatsapp and whatsapp.strip() else ""
        if wa_limpio:
            texto_principal = f"PEDIDOS WHATSAPP: {wa_limpio}"
        else:
            texto_principal = "¡HACÉ TU PEDIDO POR WHATSAPP!"

        ancho_txt, _ = self._medir_texto(draw, texto_principal, fuente_wa)
        radio_icono = 24
        espacio_icono = 18
        ancho_conjunto = (radio_icono * 2) + espacio_icono + ancho_txt
        x_inicio = (self.ANCHO - ancho_conjunto) // 2
        y_centro_wa = fy1 + 62

        cx = x_inicio + radio_icono
        cy = y_centro_wa
        draw.ellipse(
            [cx - radio_icono, cy - radio_icono, cx + radio_icono, cy + radio_icono],
            fill=config["footer_wa_icon"],
        )
        fuente_wa_simbolo = self._cargar_fuente(
            22, negrita=True, archivo_preferido=self.FONT_MONTSERRAT_BOLD
        )
        draw.text((cx, cy), "WA", font=fuente_wa_simbolo, fill=(255, 255, 255, 255), anchor="mm")

        draw.text(
            (x_inicio + (radio_icono * 2) + espacio_icono, y_centro_wa),
            texto_principal,
            font=fuente_wa,
            fill=config["nombre_texto"],
            anchor="lm",
        )

        texto_entrega = "Envíos rápidos a domicilio (Delivery)  •  Retiro en Mostrador"
        draw.text(
            (self.ANCHO // 2, fy1 + 132),
            texto_entrega,
            font=fuente_aviso,
            fill=config["footer_aviso"],
            anchor="mm",
        )

        lienzo.alpha_composite(capa)

    def _dibujar_sello_promocional(
        self, lienzo: Image.Image, sello: Optional[str], config: Dict[str, Any]
    ) -> None:
        """
        Dibuja un sticker o cinta de oferta especial (Promo Badge / Ribbon)
        en la esquina superior derecha del lienzo, resaltando promociones clave
        ('¡SOLO POR HOY!', '¡ENVÍO GRATIS!', '10% OFF EFECTIVO', etc.).
        """
        if not sello or sello == self.SELLO_NINGUNO or not sello.strip():
            return

        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        fuente_sello = self._cargar_fuente(
            26, negrita=True, archivo_preferido=self.FONT_MONTSERRAT_BOLD
        )
        ancho_txt, alto_txt = self._medir_texto(draw, sello, fuente_sello)

        pad_x, pad_y = 28, 14
        ancho_badge = ancho_txt + (pad_x * 2)
        alto_badge = alto_txt + (pad_y * 2)

        x2 = self.ANCHO - 56
        x1 = x2 - ancho_badge
        y1 = 44
        y2 = y1 + alto_badge

        # Sombra profunda del sello
        draw.rounded_rectangle(
            [x1 + 4, y1 + 5, x2 + 4, y2 + 5],
            radius=22,
            fill=(0, 0, 0, 160),
        )

        # Fondo del sello según tipo de oferta o estilo
        if any(token in sello for token in ("🔥", "⚡", "2x1")):
            color_bg = (220, 38, 38, 248)  # Rojo brasa vibrante
            color_borde = (254, 240, 138, 255)  # Borde amarillo oro
            color_texto = (255, 255, 255, 255)
        elif any(token in sello for token in ("💵", "🛵")):
            color_bg = (13, 148, 136, 248)  # Turquesa esmeralda
            color_borde = (204, 251, 241, 255)  # Menta clara
            color_texto = (255, 255, 255, 255)
        else:
            color_bg = (217, 119, 6, 248)  # Ámbar dorado
            color_borde = (254, 243, 199, 255)
            color_texto = (255, 255, 255, 255)

        draw.rounded_rectangle(
            [x1, y1, x2, y2],
            radius=22,
            fill=color_bg,
            outline=color_borde,
            width=2,
        )

        draw.text(
            ((x1 + x2) // 2, (y1 + y2) // 2),
            sello,
            font=fuente_sello,
            fill=color_texto,
            anchor="mm",
        )

        lienzo.alpha_composite(capa)

    def componer_imagen_flyer(
        self,
        productos: List[Producto],
        plantilla_path: Optional[str] = None,
        estilo: str = ESTILO_PIZARRA_BURGUER,
        titulo: str = "PROMOS DE HOY",
        whatsapp: str = "",
        modo: str = MODO_PROMOS_DESTACADAS,
        logo_path: Optional[str] = None,
        sello_promo: Optional[str] = None,
    ) -> Image.Image:
        """
        Compone en memoria el lienzo completo del flyer (1080x1920 px) según la plantilla,
        el modo activo ('Modo Promos Destacadas' o 'Modo Menú Completo'), y estampa el logo,
        la marca de agua translúcida y el sello de oferta especial si fue seleccionado.
        """
        config = self._obtener_config_estilo(estilo)
        lienzo = self._preparar_lienzo_base(plantilla_path, estilo=estilo)

        # Cargar imagen del logo comercial si fue provista
        logo_img: Optional[Image.Image] = None
        if logo_path and os.path.exists(logo_path):
            try:
                with Image.open(logo_path) as raw_logo:
                    logo_img = raw_logo.convert("RGBA")
            except Exception as exc:
                logger.warning("No se pudo cargar el archivo de logo '%s': %s", logo_path, exc)
                logo_img = None

        # 1. Aplicar marca de agua translúcida decorativa (10%-15%) en el fondo del lienzo
        if logo_img is not None:
            self._aplicar_marca_agua(lienzo, logo_img, opacidad=0.12)

        # 2. Renderizar encabezado institucional y estampar logo en el header
        es_menu_completo = modo == self.MODO_MENU_COMPLETO
        badge_sup = (
            "•  CARTA COMPLETA POR SECCIONES  •"
            if es_menu_completo
            else "•  MENÚ & PROMOCIONES DEL DÍA  •"
        )
        y_inicio_productos = self._dibujar_encabezado(
            lienzo, titulo, config, texto_badge=badge_sup, logo_img=logo_img
        )
        y_fin_productos = 1648

        # 3. Renderizar contenido según la modalidad seleccionada
        if es_menu_completo:
            self._dibujar_bloque_menu_completo(
                lienzo=lienzo,
                productos=productos,
                y_inicio=y_inicio_productos,
                y_fin=y_fin_productos,
                config=config,
            )
        else:
            self._dibujar_bloque_productos(
                lienzo=lienzo,
                productos=productos[: self.MAX_PRODUCTOS],
                y_inicio=y_inicio_productos,
                y_fin=y_fin_productos,
                config=config,
            )

        # 4. Barra inferior de contacto con WhatsApp y modalidad de entrega
        self._dibujar_footer(lienzo, whatsapp, config)

        # 5. Estampado de sello promocional / cinta de oferta si está activo
        self._dibujar_sello_promocional(lienzo, sello_promo, config)

        return lienzo

    def generar_flyer(
        self,
        productos: List[Producto],
        plantilla_path: Optional[str] = None,
        estilo: str = ESTILO_PIZARRA_BURGUER,
        titulo: str = "PROMOS DE HOY",
        whatsapp: str = "",
        modo: str = MODO_PROMOS_DESTACADAS,
        logo_path: Optional[str] = None,
        sello_promo: Optional[str] = None,
    ) -> str:
        """
        Genera el flyer promocional o carta completa en resolución 1080x1920 px y lo exporta en `output/`.

        Args:
            productos (List[Producto]): Lista de objetos Producto a renderizar.
            plantilla_path (Optional[str]): Ruta opcional a una imagen de fondo (.png/.jpg).
            estilo (str): Nombre de una de las 5 plantillas predefinidas.
            titulo (str): Encabezado principal del flyer.
            whatsapp (str): Número de WhatsApp para el pie de página.
            modo (str): 'Modo Promos Destacadas' o 'Modo Menú Completo'.
            logo_path (Optional[str]): Ruta al archivo del logo comercial.
            sello_promo (Optional[str]): Texto del sello o sticker de oferta especial.

        Returns:
            str: Ruta absoluta del archivo de imagen PNG exportado en `output/`.
        """
        if not productos:
            raise ValueError("Debe disponer de al menos un producto para generar el flyer.")

        os.makedirs(self.output_dir, exist_ok=True)
        lienzo = self.componer_imagen_flyer(
            productos=productos,
            plantilla_path=plantilla_path,
            estilo=estilo,
            titulo=titulo,
            whatsapp=whatsapp,
            modo=modo,
            logo_path=logo_path,
            sello_promo=sello_promo,
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug_estilo = (
            estilo.lower()
            .replace(" ", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("&", "y")
        )
        prefijo = "menu_completo" if modo == self.MODO_MENU_COMPLETO else "flyer"
        nombre_archivo = f"{prefijo}_{slug_estilo}_{timestamp}.png"
        ruta_salida = os.path.abspath(os.path.join(self.output_dir, nombre_archivo))

        imagen_final = lienzo.convert("RGB")
        imagen_final.save(ruta_salida, format="PNG", optimize=True)

        return ruta_salida

    def asegurar_plantilla_por_defecto(self) -> str:
        """
        Asegura que exista la plantilla base por defecto en `templates/`.
        Si no existe, la crea con el estilo de Pizarra Burguer.
        """
        if not os.path.exists(self.default_template_path):
            img_default = self._renderizar_fondo_programatico(self.ESTILO_PIZARRA_BURGUER)
            img_default.save(self.default_template_path, format="PNG")
        return self.default_template_path
