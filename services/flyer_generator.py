"""
Servicio generador de flyers promocionales en formato vertical (9:16 - 1080x1920 px)
optimizado para Estados de WhatsApp e Historias de Instagram utilizando Pillow (PIL).
"""

from datetime import datetime
import logging
import os
from typing import List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from models.producto import Producto

logger = logging.getLogger(__name__)


class FlyerGenerator:
    """
    Motor gráfico para el diseño y renderizado automatizado de flyers gastronómicos.
    Compone encabezados, tarjetas semitransparentes RGBA con espaciado dinámico,
    precios formateados y pie de página de contacto sobre plantillas o fondos degradados.
    """

    ANCHO: int = 1080
    ALTO: int = 1920
    MAX_PRODUCTOS: int = 6

    # Paleta de colores RGBA
    COLOR_ACENTO_AMBAR: Tuple[int, int, int, int] = (245, 158, 11, 255)      # #F59E0B
    COLOR_ACENTO_NARANJA: Tuple[int, int, int, int] = (234, 88, 12, 255)     # #EA580C
    COLOR_PRECIO_ORO: Tuple[int, int, int, int] = (251, 191, 36, 255)        # #FBBF24
    COLOR_WHATSAPP: Tuple[int, int, int, int] = (34, 197, 94, 255)           # #22C55E
    COLOR_TARJETA_FONDO: Tuple[int, int, int, int] = (17, 24, 39, 222)       # RGBA semitransparente
    COLOR_TARJETA_BORDE: Tuple[int, int, int, int] = (255, 255, 255, 55)     # Borde sutil cristal
    COLOR_SOMBRA: Tuple[int, int, int, int] = (0, 0, 0, 115)
    COLOR_TEXTO_BLANCO: Tuple[int, int, int, int] = (255, 255, 255, 255)
    COLOR_TEXTO_GRIS: Tuple[int, int, int, int] = (203, 213, 225, 255)

    def __init__(
        self,
        templates_dir: str = "templates",
        output_dir: str = "output",
    ) -> None:
        """
        Inicializa el generador de flyers asegurando los directorios de entrada y salida.
        """
        self.templates_dir: str = os.path.abspath(templates_dir)
        self.output_dir: str = os.path.abspath(output_dir)
        os.makedirs(self.templates_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.default_template_path: str = os.path.join(
            self.templates_dir, "plantilla_oscura_default.png"
        )
        self.asegurar_plantilla_por_defecto()

    def _cargar_fuente(
        self, tamano: int, negrita: bool = False
    ) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        """
        Busca y carga una fuente TrueType del sistema (compatible con Linux, Windows y macOS).
        Si ninguna está disponible, recurre al fallback seguro de Pillow.
        """
        candidatos_bold = [
            "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-B.ttf",
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "DejaVuSans-Bold.ttf",
            "arialbd.ttf",
        ]
        candidatos_regular = [
            "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            "/usr/share/fonts/truetype/ubuntu/Ubuntu-R.ttf",
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
            except OSError:
                continue

        # Segundo intento por nombre directo en el path de Pillow
        for nombre in (["DejaVuSans-Bold.ttf", "arialbd.ttf"] if negrita else ["DejaVuSans.ttf", "arial.ttf"]):
            try:
                return ImageFont.truetype(nombre, tamano)
            except OSError:
                continue

        try:
            return ImageFont.load_default(size=tamano)
        except TypeError:
            return ImageFont.load_default()

    def _renderizar_fondo_degradado_oscuro(self) -> Image.Image:
        """
        Genera programáticamente un lienzo vertical 1080x1920 con un degradado oscuro
        elegante y detalles geométricos sutiles de estética gastronómica.
        """
        base = Image.new("RGBA", (self.ANCHO, self.ALTO), (12, 16, 28, 255))
        draw = ImageDraw.Draw(base)

        # Degradado vertical suave en escala oscura (#0F172A -> #181826 -> #090D16)
        r_ini, g_ini, b_ini = (15, 23, 42)
        r_med, g_med, b_med = (26, 24, 41)
        r_fin, g_fin, b_fin = (9, 13, 22)

        mitad = self.ALTO // 2
        for y in range(self.ALTO):
            if y < mitad:
                t = y / float(mitad)
                r = int(r_ini + (r_med - r_ini) * t)
                g = int(g_ini + (g_med - g_ini) * t)
                b = int(b_ini + (b_med - b_ini) * t)
            else:
                t = (y - mitad) / float(self.ALTO - mitad)
                r = int(r_med + (r_fin - r_med) * t)
                g = int(g_med + (g_fin - g_med) * t)
                b = int(b_med + (b_fin - b_med) * t)
            draw.line([(0, y), (self.ANCHO, y)], fill=(r, g, b, 255))

        # Capa decorativa con acentos cálidos sutiles en esquinas y bordes
        decoracion = Image.new("RGBA", (self.ANCHO, self.ALTO), (0, 0, 0, 0))
        d_draw = ImageDraw.Draw(decoracion)

        # Círculos decorativos traslúcidos (halo cálido superior e inferior)
        for radio, alpha in [(520, 14), (380, 18), (240, 22)]:
            d_draw.ellipse(
                [self.ANCHO // 2 - radio, -radio // 2, self.ANCHO // 2 + radio, radio + radio // 2],
                fill=(245, 158, 11, alpha),
            )
            d_draw.ellipse(
                [self.ANCHO // 2 - radio, self.ALTO - radio, self.ANCHO // 2 + radio, self.ALTO + radio],
                fill=(234, 88, 12, alpha),
            )

        # Marco interior fino dorado muy sutil
        margen_marco = 28
        d_draw.rounded_rectangle(
            [margen_marco, margen_marco, self.ANCHO - margen_marco, self.ALTO - margen_marco],
            radius=36,
            outline=(245, 158, 11, 55),
            width=2,
        )

        return Image.alpha_composite(base, decoracion)

    def asegurar_plantilla_por_defecto(self) -> str:
        """
        Si no existe una plantilla base en la carpeta `templates/`, genera y guarda
        una plantilla oscura por defecto para que el usuario disponga de un archivo base.
        """
        try:
            if not os.path.exists(self.default_template_path):
                img_fondo = self._renderizar_fondo_degradado_oscuro()
                img_fondo.convert("RGB").save(self.default_template_path, "PNG", optimize=True)
        except OSError as exc:
            logger.warning("No se pudo guardar la plantilla por defecto en templates/: %s", exc)
        return self.default_template_path

    def _preparar_lienzo_base(self, plantilla_path: Optional[str] = None) -> Image.Image:
        """
        Carga la plantilla indicada por el usuario adaptándola a 1080x1920 px sin deformarla,
        o genera el fondo degradado oscuro por defecto si no se provee plantilla.
        """
        ruta_a_usar: Optional[str] = None
        if plantilla_path and str(plantilla_path).strip() and os.path.exists(str(plantilla_path).strip()):
            ruta_a_usar = str(plantilla_path).strip()

        if ruta_a_usar:
            try:
                with Image.open(ruta_a_usar) as img_origen:
                    img_rgba = img_origen.convert("RGBA")
                    lienzo = ImageOps.fit(
                        img_rgba,
                        (self.ANCHO, self.ALTO),
                        method=Image.Resampling.LANCZOS,
                    )
                # Aplicar un velo oscuro suave para asegurar contraste de lectura
                velo = Image.new("RGBA", (self.ANCHO, self.ALTO), (10, 14, 24, 75))
                return Image.alpha_composite(lienzo, velo)
            except Exception as exc:
                logger.warning(
                    "No se pudo cargar la plantilla '%s' (%s). Usando fondo degradado por defecto.",
                    ruta_a_usar,
                    exc,
                )

        return self._renderizar_fondo_degradado_oscuro()

    @staticmethod
    def _medir_texto(
        draw: ImageDraw.ImageDraw,
        texto: str,
        fuente: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    ) -> Tuple[int, int]:
        """Calcula el ancho y alto en píxeles de un texto para la fuente dada."""
        bbox = draw.textbbox((0, 0), texto, font=fuente)
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
                    # Palabra individual demasiado larga
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

    def _dibujar_encabezado(self, lienzo: Image.Image, titulo: str) -> int:
        """
        Dibuja el bloque superior de encabezado institucional y el título adaptable.

        Returns:
            int: Coordenada Y donde finaliza el encabezado para dar comienzo a los productos.
        """
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        # Badge superior "MENÚ & PROMOCIONES DEL DÍA"
        fuente_badge = self._cargar_fuente(24, negrita=True)
        texto_badge = "•  MENÚ & PROMOCIONES DEL DÍA  •"
        ancho_b, alto_b = self._medir_texto(draw, texto_badge, fuente_badge)
        pad_x, pad_y = 34, 14
        bx1 = (self.ANCHO - (ancho_b + pad_x * 2)) // 2
        by1 = 68
        bx2 = bx1 + ancho_b + pad_x * 2
        by2 = by1 + alto_b + pad_y * 2

        draw.rounded_rectangle(
            [bx1, by1, bx2, by2],
            radius=26,
            fill=(15, 23, 42, 210),
            outline=self.COLOR_ACENTO_AMBAR,
            width=2,
        )
        draw.text(
            (self.ANCHO // 2, (by1 + by2) // 2),
            texto_badge,
            font=fuente_badge,
            fill=self.COLOR_PRECIO_ORO,
            anchor="mm",
        )

        # Título principal adaptable ("PROMOS DE HOY" / "MENÚ DEL DÍA")
        titulo_limpio = (titulo.strip() if titulo and titulo.strip() else "PROMOS DE HOY").upper()
        tamano_titulo = 74
        fuente_titulo = self._cargar_fuente(tamano_titulo, negrita=True)
        while tamano_titulo > 42:
            ancho_t, _ = self._medir_texto(draw, titulo_limpio, fuente_titulo)
            if ancho_t <= (self.ANCHO - 130):
                break
            tamano_titulo -= 4
            fuente_titulo = self._cargar_fuente(tamano_titulo, negrita=True)

        y_titulo = by2 + 68
        # Sombra del título
        draw.text(
            (self.ANCHO // 2 + 4, y_titulo + 4),
            titulo_limpio,
            font=fuente_titulo,
            fill=(0, 0, 0, 190),
            anchor="mm",
        )
        draw.text(
            (self.ANCHO // 2, y_titulo),
            titulo_limpio,
            font=fuente_titulo,
            fill=self.COLOR_TEXTO_BLANCO,
            anchor="mm",
        )

        # Línea divisoria decorativa
        y_linea = y_titulo + 58
        ancho_linea = 280
        draw.rounded_rectangle(
            [
                (self.ANCHO - ancho_linea) // 2,
                y_linea,
                (self.ANCHO + ancho_linea) // 2,
                y_linea + 8,
            ],
            radius=4,
            fill=self.COLOR_ACENTO_AMBAR,
        )

        lienzo.alpha_composite(capa)
        return y_linea + 36

    def _dibujar_bloque_productos(
        self,
        lienzo: Image.Image,
        productos: List[Producto],
        y_inicio: int,
        y_fin: int,
    ) -> None:
        """
        Renderiza las tarjetas semitransparentes RGBA de los productos seleccionados,
        calculando dinámicamente la altura y el espaciado vertical según la cantidad de ítems.
        """
        items = productos[: self.MAX_PRODUCTOS]
        cantidad = len(items)
        if cantidad == 0:
            return

        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        alto_disponible = y_fin - y_inicio
        margen_x = 64
        x1_card = margen_x
        x2_card = self.ANCHO - margen_x

        # Cálculo dinámico de altura de tarjeta y espaciado vertical
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
            # 6 productos
            espacio = 18
            alto_card = min(176, (alto_disponible - (espacio * (cantidad - 1))) // cantidad)

        alto_bloque_total = (alto_card * cantidad) + (espacio * (cantidad - 1))
        y_actual = y_inicio + max(0, (alto_disponible - alto_bloque_total) // 2)

        # Tamaños tipográficos adaptados a la densidad de tarjetas
        es_compacto = cantidad >= 5
        fuente_cat = self._cargar_fuente(20 if es_compacto else 22, negrita=True)
        fuente_nombre = self._cargar_fuente(32 if es_compacto else 36, negrita=True)
        fuente_desc = self._cargar_fuente(23 if es_compacto else 25, negrita=False)
        fuente_precio = self._cargar_fuente(44 if es_compacto else 50, negrita=True)

        for prod in items:
            y1 = y_actual
            y2 = y1 + alto_card

            # 1. Sombra proyectada de la tarjeta
            draw.rounded_rectangle(
                [x1_card + 6, y1 + 8, x2_card + 6, y2 + 8],
                radius=26,
                fill=self.COLOR_SOMBRA,
            )

            # 2. Cuerpo principal semitransparente RGBA
            draw.rounded_rectangle(
                [x1_card, y1, x2_card, y2],
                radius=26,
                fill=self.COLOR_TARJETA_FONDO,
                outline=self.COLOR_TARJETA_BORDE,
                width=2,
            )

            # 3. Barra lateral izquierda de acento cálido
            draw.rounded_rectangle(
                [x1_card, y1 + 18, x1_card + 12, y2 - 18],
                radius=6,
                fill=self.COLOR_ACENTO_AMBAR,
            )

            # 4. Precio formateado en pesos argentinos ($ {:,.0f}) a la derecha
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
                fill=(245, 158, 11, 32),
                outline=(245, 158, 11, 155),
                width=2,
            )
            draw.text(
                ((px1 + px2) // 2, (py1 + py2) // 2),
                texto_precio,
                font=fuente_precio,
                fill=self.COLOR_PRECIO_ORO,
                anchor="mm",
            )

            # 5. Bloque izquierdo: Categoría, Nombre y Descripción
            x_texto = x1_card + 36
            max_ancho_texto = max(280, px1 - x_texto - 26)
            y_cursor = y1 + (16 if es_compacto else 22)

            # Etiqueta de categoría
            cat_upper = prod.categoria.strip().upper()
            draw.text(
                (x_texto, y_cursor),
                cat_upper,
                font=fuente_cat,
                fill=self.COLOR_ACENTO_AMBAR,
            )
            _, alto_cat = self._medir_texto(draw, cat_upper, fuente_cat)
            y_cursor += alto_cat + (6 if es_compacto else 10)

            # Nombre del producto (1 o 2 líneas según longitud)
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
                    fill=self.COLOR_TEXTO_BLANCO,
                )
                _, alto_n = self._medir_texto(draw, linea_n, fuente_nombre)
                y_cursor += alto_n + 4

            # Descripción del producto (si existe y hay espacio vertical)
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
                        fill=self.COLOR_TEXTO_GRIS,
                    )
                    _, alto_d = self._medir_texto(draw, linea_d, fuente_desc)
                    y_cursor += alto_d + 4

            y_actual += alto_card + espacio

        lienzo.alpha_composite(capa)

    def _dibujar_footer(self, lienzo: Image.Image, whatsapp: str) -> None:
        """
        Dibuja la barra inferior fija de contacto con el número de WhatsApp
        y el aviso de modalidades de entrega (Delivery y Mostrador).
        """
        capa = Image.new("RGBA", lienzo.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(capa)

        margen_x = 64
        fy1 = 1672
        fy2 = 1852

        # Sombra y contenedor principal del footer
        draw.rounded_rectangle(
            [margen_x + 4, fy1 + 6, self.ANCHO - margen_x + 4, fy2 + 6],
            radius=28,
            fill=self.COLOR_SOMBRA,
        )
        draw.rounded_rectangle(
            [margen_x, fy1, self.ANCHO - margen_x, fy2],
            radius=28,
            fill=(15, 23, 42, 238),
            outline=self.COLOR_WHATSAPP,
            width=3,
        )

        fuente_wa = self._cargar_fuente(36, negrita=True)
        fuente_aviso = self._cargar_fuente(24, negrita=False)

        wa_limpio = whatsapp.strip() if whatsapp and whatsapp.strip() else ""
        if wa_limpio:
            texto_principal = f"PEDIDOS WHATSAPP: {wa_limpio}"
        else:
            texto_principal = "¡HACÉ TU PEDIDO POR WHATSAPP!"

        # Ícono circular de WhatsApp + texto centrado
        ancho_txt, _ = self._medir_texto(draw, texto_principal, fuente_wa)
        radio_icono = 24
        espacio_icono = 18
        ancho_conjunto = (radio_icono * 2) + espacio_icono + ancho_txt
        x_inicio = (self.ANCHO - ancho_conjunto) // 2
        y_centro_wa = fy1 + 62

        # Círculo verde WhatsApp
        cx = x_inicio + radio_icono
        cy = y_centro_wa
        draw.ellipse(
            [cx - radio_icono, cy - radio_icono, cx + radio_icono, cy + radio_icono],
            fill=self.COLOR_WHATSAPP,
        )
        fuente_wa_simbolo = self._cargar_fuente(24, negrita=True)
        draw.text((cx, cy), "WA", font=fuente_wa_simbolo, fill=(255, 255, 255, 255), anchor="mm")

        # Texto principal de WhatsApp
        draw.text(
            (x_inicio + (radio_icono * 2) + espacio_icono, y_centro_wa),
            texto_principal,
            font=fuente_wa,
            fill=self.COLOR_TEXTO_BLANCO,
            anchor="lm",
        )

        # Subtítulo de entregas
        texto_entrega = "Envíos rápidos a domicilio (Delivery)  •  Retiro en Mostrador"
        draw.text(
            (self.ANCHO // 2, fy1 + 132),
            texto_entrega,
            font=fuente_aviso,
            fill=self.COLOR_PRECIO_ORO,
            anchor="mm",
        )

        lienzo.alpha_composite(capa)

    def generar_flyer(
        self,
        productos: List[Producto],
        plantilla_path: Optional[str] = None,
        titulo: str = "PROMOS DE HOY",
        whatsapp: str = "",
    ) -> str:
        """
        Genera el flyer promocional en resolución 1080x1920 px y lo exporta en `output/`.

        Args:
            productos (List[Producto]): Lista de entre 1 y 6 objetos Producto a destacar.
            plantilla_path (Optional[str]): Ruta opcional a una imagen de fondo (.png/.jpg).
            titulo (str): Encabezado principal del flyer.
            whatsapp (str): Número de WhatsApp para mostrar en el pie de página.

        Returns:
            str: Ruta absoluta del archivo de imagen PNG exportado.

        Raises:
            ValueError: Si la lista de productos está vacía.
        """
        if not productos:
            raise ValueError("Debe seleccionar al menos un producto para generar el flyer.")

        os.makedirs(self.output_dir, exist_ok=True)

        # 1. Preparar lienzo base 1080x1920 (plantilla de usuario o degradado oscuro)
        lienzo = self._preparar_lienzo_base(plantilla_path)

        # 2. Dibujar encabezado
        y_inicio_productos = self._dibujar_encabezado(lienzo, titulo)

        # 3. Dibujar bloque de tarjetas de productos (máximo 6 items)
        y_fin_productos = 1645
        self._dibujar_bloque_productos(
            lienzo=lienzo,
            productos=productos[: self.MAX_PRODUCTOS],
            y_inicio=y_inicio_productos,
            y_fin=y_fin_productos,
        )

        # 4. Dibujar pie de página fijo con WhatsApp y aviso de entrega
        self._dibujar_footer(lienzo, whatsapp)

        # 5. Exportar imagen final en alta calidad
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"flyer_{timestamp}.png"
        ruta_salida = os.path.abspath(os.path.join(self.output_dir, nombre_archivo))

        imagen_final = lienzo.convert("RGB")
        imagen_final.save(ruta_salida, format="PNG", optimize=True)

        return ruta_salida
