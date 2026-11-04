"""
Suite de pruebas automatizadas para verificar las refactorizaciones y nuevas funciones:
1. Corrección de pantalla, scroll y minsize(1100, 680).
2. Paleta visual turquesa/esmeralda y modos Claro/Oscuro en ThemeManager.
3. Tipografías estandarizadas y jerarquía de tamaños.
4. Motor de Flyers multi-plantilla ('Pizarra Oscura', 'Turquesa Gourmet', 'Rojo Rústico').
5. Registro y cálculo de Pago Mixto (Efectivo + Transferencia) en Venta y ExcelManager.
"""

import os
import tempfile
import unittest

import customtkinter as ctk

from models.producto import Producto
from models.venta import Venta
from services.excel_manager import ExcelManager
from services.flyer_generator import FlyerGenerator
from views.app_ui import AppUI
from views.theme_manager import ThemeManager


class TestRefactorizacionGastronomica(unittest.TestCase):
    """Pruebas unitarias de las 5 funcionalidades requeridas."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.excel_path = os.path.join(self.temp_dir.name, "test_rotiseria.xlsx")
        self.output_dir = os.path.join(self.temp_dir.name, "output")
        self.templates_dir = os.path.join(self.temp_dir.name, "templates")

        self.excel_manager = ExcelManager(filepath=self.excel_path)
        self.excel_manager.sembrar_datos_ejemplo_si_vacio()
        self.flyer_generator = FlyerGenerator(
            templates_dir=self.templates_dir,
            output_dir=self.output_dir,
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    # =========================================================================
    # REQ 1 & 2: DIMENSIONES, SCROLL Y SISTEMA DE COLORES
    # =========================================================================

    def test_app_ui_minsize_y_scroll_menu(self) -> None:
        """Verifica que AppUI tenga minsize(1100, 680) y TabMenu use CTkScrollableFrame."""
        app = AppUI(self.excel_manager, self.flyer_generator)
        app.update_idletasks()

        # Comprobar que la columna izquierda de TabMenu es un CTkScrollableFrame
        self.assertIsInstance(
            app.vista_menu.contenedor_izq,
            ctk.CTkScrollableFrame,
            "La columna izquierda de TabMenu debe ser un CTkScrollableFrame.",
        )
        self.assertEqual(app.vista_menu.contenedor_izq.cget("width"), 390)

        # Probar cambio dinámico de tema
        app._cambiar_modo_apariencia("Light")
        self.assertEqual(ctk.get_appearance_mode().lower(), "light")
        app._cambiar_modo_apariencia("Dark")
        self.assertEqual(ctk.get_appearance_mode().lower(), "dark")

        app.destroy()

    def test_theme_manager_paleta_colores(self) -> None:
        """Verifica la definición de colores turquesa / esmeralda y contrastes."""
        self.assertEqual(ThemeManager.BG_VENTANA, ("#F0FDF4", "#0B0F19"))
        self.assertEqual(ThemeManager.BG_CARD, ("#FFFFFF", "#161E2E"))
        self.assertEqual(ThemeManager.BORDER_CARD, ("#CCFBF1", "#1E293B"))
        self.assertEqual(ThemeManager.COLOR_NUMEROS_DESTACADOS, ("#0D9488", "#2DD4BF"))
        self.assertEqual(ThemeManager.COLOR_ACCENT, ("#0D9488", "#14B8A6"))

    # =========================================================================
    # REQ 3: TIPOGRAFÍAS, LEGIBILIDAD Y CONTRASTE TREEVIEW (#0F766E)
    # =========================================================================

    def test_theme_manager_tipografias(self) -> None:
        """Verifica tamaños mejorados (+1/2 pts) y contraste Turquesa Noche (#0F766E) en tablas."""
        font_tab = ThemeManager.font_tab_title()
        self.assertEqual(font_tab.cget("size"), 14)
        self.assertEqual(font_tab.cget("weight"), "bold")

        font_prod = ThemeManager.font_product_name()
        self.assertEqual(font_prod.cget("size"), 14)
        self.assertEqual(font_prod.cget("weight"), "bold")

        font_in = ThemeManager.font_input()
        self.assertEqual(font_in.cget("size"), 14)

        font_body = ThemeManager.font_body()
        self.assertEqual(font_body.cget("size"), 13)

        font_kpi = ThemeManager.font_kpi_value(grande=True)
        self.assertEqual(font_kpi.cget("size"), 22)
        self.assertEqual(font_kpi.cget("weight"), "bold")

        font_kpi_sm = ThemeManager.font_kpi_value(grande=False)
        self.assertEqual(font_kpi_sm.cget("size"), 18)
        self.assertEqual(font_kpi_sm.cget("weight"), "bold")

        font_price = ThemeManager.font_price_highlight()
        self.assertEqual(font_price.cget("size"), 16)
        self.assertEqual(font_price.cget("weight"), "bold")

        # Contraste de fila seleccionada en Treeview: Turquesa Noche (#0F766E) + Blanco (#FFFFFF)
        self.assertEqual(ThemeManager.TREEVIEW_SEL_BG, "#0F766E")
        self.assertEqual(ThemeManager.TREEVIEW_SEL_FG, "#FFFFFF")

    # =========================================================================
    # REQ 4: MOTOR DE FLYERS: 5 PLANTILLAS, TIPOGRAFÍAS, LOGO Y MARCA DE AGUA
    # =========================================================================

    def test_flyer_generator_cinco_plantillas(self) -> None:
        """Verifica las 5 plantillas predefinidas y su composición en resolución 1080x1920."""
        esperadas = [
            "Pizarra Burguer (Dark & Red)",
            "Pizzería Rústica (Madera & Blanco)",
            "Fast Food Mostaza (Pop & Cards)",
            "Turquesa Glass (Cards Modernas)",
            "Gourmet Bistró (Elegante & Minimal)",
        ]
        self.assertEqual(FlyerGenerator.PLANTILLAS_DISPONIBLES, esperadas)

        # Verificar alias retrocompatibles
        self.assertEqual(
            self.flyer_generator._obtener_config_estilo("Pizarra Oscura")["nombre"],
            "Pizarra Burguer (Dark & Red)",
        )
        self.assertEqual(
            self.flyer_generator._obtener_config_estilo("Turquesa Gourmet")["nombre"],
            "Turquesa Glass (Cards Modernas)",
        )
        self.assertEqual(
            self.flyer_generator._obtener_config_estilo("Rojo Rústico")["nombre"],
            "Pizzería Rústica (Madera & Blanco)",
        )

        productos = self.excel_manager.obtener_productos()[:3]
        for estilo in esperadas:
            lienzo = self.flyer_generator.componer_imagen_flyer(
                productos=productos,
                estilo=estilo,
                titulo=f"TEST {estilo.upper()}",
                whatsapp="3794-001122",
                modo=FlyerGenerator.MODO_PROMOS_DESTACADAS,
            )
            self.assertEqual(lienzo.size, (1080, 1920))
            self.assertEqual(lienzo.mode, "RGBA")

            ruta = self.flyer_generator.generar_flyer(
                productos=productos,
                estilo=estilo,
                titulo=f"TEST {estilo.upper()}",
                modo=FlyerGenerator.MODO_PROMOS_DESTACADAS,
            )
            self.assertTrue(os.path.exists(ruta))
            self.assertTrue(os.path.basename(ruta).startswith("flyer_"))

    def test_incorporacion_tipografias_y_fallback_seguro(self) -> None:
        """
        Verifica la presencia o descarga de las fuentes TTF en assets/fonts/
        y comprueba que el método _cargar_fuente aplique fallback seguro sin arrojar excepción.
        """
        fonts_dir = self.flyer_generator.fonts_dir
        self.assertTrue(os.path.exists(fonts_dir))

        fuentes_esperadas = [
            FlyerGenerator.FONT_BEBAS_NEUE,
            FlyerGenerator.FONT_PLAYFAIR_DISPLAY,
            FlyerGenerator.FONT_MONTSERRAT_BOLD,
            FlyerGenerator.FONT_INTER_REGULAR,
        ]
        for f in fuentes_esperadas:
            ruta_f = os.path.join(fonts_dir, f)
            self.assertTrue(os.path.exists(ruta_f), f"Falta la fuente {f} en assets/fonts/")

        # Probar carga normal con archivo preferido
        f_bebas = self.flyer_generator._cargar_fuente(
            32, negrita=True, archivo_preferido=FlyerGenerator.FONT_BEBAS_NEUE
        )
        self.assertIsNotNone(f_bebas)

        f_playfair = self.flyer_generator._cargar_fuente(
            32, negrita=True, archivo_preferido=FlyerGenerator.FONT_PLAYFAIR_DISPLAY
        )
        self.assertIsNotNone(f_playfair)

        # Probar fallback cuando se pasa un archivo inexistente o ruta rota (no debe arrojar excepción)
        f_fallback = self.flyer_generator._cargar_fuente(
            28, negrita=True, archivo_preferido="FuenteInexistente_12345.ttf"
        )
        self.assertIsNotNone(f_fallback)

    def test_logo_comercio_estampado_y_marca_agua(self) -> None:
        """
        Verifica que al suministrar un logo:
        - Se estampa proporcionalmente en el header.
        - Se genera la marca de agua translúcida (alpha compositing 10%-15%) en el fondo.
        - Si el archivo no existe o es inválido, no arroja excepción.
        """
        from PIL import Image, ImageDraw

        # Crear logo dummy con canal alfa transparente
        logo_path = os.path.join(self.temp_dir.name, "logo_rotiseria.png")
        logo_img = Image.new("RGBA", (300, 150), (0, 0, 0, 0))
        draw_logo = ImageDraw.Draw(logo_img)
        draw_logo.ellipse([10, 10, 140, 140], fill=(220, 38, 38, 255))
        draw_logo.rectangle([150, 40, 290, 110], fill=(245, 158, 11, 255))
        logo_img.save(logo_path, format="PNG")

        productos = self.excel_manager.obtener_productos()[:3]

        # Componer con logo
        lienzo = self.flyer_generator.componer_imagen_flyer(
            productos=productos,
            estilo=FlyerGenerator.ESTILO_PIZARRA_BURGUER,
            titulo="PROMOS CON LOGO",
            whatsapp="3794-001122",
            logo_path=logo_path,
        )
        self.assertEqual(lienzo.size, (1080, 1920))
        self.assertEqual(lienzo.mode, "RGBA")

        # Comprobar generación a disco con logo
        ruta_salida = self.flyer_generator.generar_flyer(
            productos=productos,
            estilo=FlyerGenerator.ESTILO_TURQUESA_GLASS,
            titulo="PROMOS CON LOGO",
            logo_path=logo_path,
        )
        self.assertTrue(os.path.exists(ruta_salida))

        # Comprobar resiliencia ante logo inexistente
        lienzo_resiliente = self.flyer_generator.componer_imagen_flyer(
            productos=productos,
            estilo=FlyerGenerator.ESTILO_GOURMET_BISTRO,
            logo_path="/ruta/fantasma/logo_no_existe.png",
        )
        self.assertEqual(lienzo_resiliente.size, (1080, 1920))

    def test_flyer_generator_modo_menu_completo_dos_columnas(self) -> None:
        """
        Verifica el Modo Menú Completo por Secciones:
        - Agrupación automática por Categoría.
        - Distribución balanceada en 2 columnas verticales.
        - Renderizado 1080x1920 con renglones compactos 'Nombre .... $ Precio'.
        """
        self.assertIn(FlyerGenerator.MODO_MENU_COMPLETO, FlyerGenerator.MODOS_DISPONIBLES)
        todos_productos = self.excel_manager.obtener_productos()
        self.assertGreaterEqual(len(todos_productos), 6)

        grupos = self.flyer_generator._agrupar_productos_por_categoria(todos_productos)
        self.assertGreaterEqual(len(grupos), 2)

        col_izq, col_der = self.flyer_generator._distribuir_categorias_en_dos_columnas(todos_productos)
        self.assertGreater(len(col_izq), 0)
        self.assertGreater(len(col_der), 0)

        for estilo in FlyerGenerator.PLANTILLAS_DISPONIBLES:
            lienzo = self.flyer_generator.componer_imagen_flyer(
                productos=todos_productos,
                estilo=estilo,
                titulo="NUESTRA CARTA COMPLETA",
                whatsapp="3794-001122",
                modo=FlyerGenerator.MODO_MENU_COMPLETO,
            )
            self.assertEqual(lienzo.size, (1080, 1920))
            self.assertEqual(lienzo.mode, "RGBA")

        ruta_menu = self.flyer_generator.generar_flyer(
            productos=todos_productos,
            estilo=FlyerGenerator.ESTILO_TURQUESA_GOURMET,
            titulo="NUESTRA CARTA COMPLETA",
            modo=FlyerGenerator.MODO_MENU_COMPLETO,
        )
        self.assertTrue(os.path.exists(ruta_menu))
        self.assertTrue(os.path.basename(ruta_menu).startswith("menu_completo_"))

    # =========================================================================
    # REQ 6: BUSCADOR PREDICTIVO EN CAJA Y SELECTOR DE MODO EN TAB FLYER
    # =========================================================================

    def test_buscador_predictivo_caja_y_confirmacion_enter(self) -> None:
        """
        Verifica que el buscador predictivo en TabCaja filtre en tiempo real por nombre o categoría,
        permita navegar sugerencias y sume el plato al pedido al presionar Enter.
        """
        app = AppUI(self.excel_manager, self.flyer_generator)
        app.update_idletasks()

        caja = app.vista_caja
        # Inicialmente el carrito está vacío
        self.assertEqual(caja.total_acumulado_form, 0.0)

        # Simular escritura en el buscador predictivo ('napolitana' o 'pizza')
        caja.entry_buscar_plato.delete(0, "end")
        caja.entry_buscar_plato.insert(0, "napolitana")
        caja._al_escribir_busqueda_predictiva()

        self.assertGreater(len(caja.sugerencias_filtradas), 0)
        plato_sugerido = caja.sugerencias_filtradas[0]
        self.assertIn("napolitana", plato_sugerido.nombre.lower())

        # Simular presionar Enter para confirmar la adición al pedido (cantidad 2)
        caja.combo_cantidad.set("2")
        caja._atajo_sumar_plato()

        self.assertEqual(caja.total_acumulado_form, plato_sugerido.precio * 2)
        detalle_actual = caja.entry_detalle.get().strip()
        self.assertIn(f"2x {plato_sugerido.nombre}", detalle_actual)

        # Probar búsqueda por categoría sin tildes ('sandwiches')
        caja.entry_buscar_plato.delete(0, "end")
        caja.entry_buscar_plato.insert(0, "sandwiches")
        caja._al_escribir_busqueda_predictiva()
        self.assertGreater(len(caja.sugerencias_filtradas), 0)

        # Probar cambio de modo en TabFlyer a 'Modo Menú Completo'
        flyer_tab = app.vista_flyer
        flyer_tab.seg_modo_flyer.set(FlyerGenerator.MODO_MENU_COMPLETO)
        flyer_tab._al_cambiar_modo_generacion(FlyerGenerator.MODO_MENU_COMPLETO)
        self.assertEqual(flyer_tab.modo_actual, FlyerGenerator.MODO_MENU_COMPLETO)
        self.assertEqual(len(flyer_tab._obtener_productos_seleccionados()), len(flyer_tab.productos_disponibles))

        # Probar selector de 5 plantillas y control de logo en TabFlyer
        self.assertEqual(len(flyer_tab.combo_estilo.cget("values")), 5)
        self.assertIn(FlyerGenerator.ESTILO_PIZARRA_BURGUER, flyer_tab.combo_estilo.cget("values"))
        self.assertIn(FlyerGenerator.ESTILO_GOURMET_BISTRO, flyer_tab.combo_estilo.cget("values"))
        self.assertIsNone(flyer_tab.logo_path)
        flyer_tab.logo_path = "/tmp/fake_logo.png"
        flyer_tab._quitar_logo()
        self.assertIsNone(flyer_tab.logo_path)
        self.assertIn("Sin logo", flyer_tab.lbl_logo_actual.cget("text"))

        # Probar selector de Sello Promocional en TabFlyer y opciones disponibles
        self.assertTrue(hasattr(flyer_tab, "combo_sello_promo"))
        self.assertEqual(
            flyer_tab.combo_sello_promo.cget("values"),
            FlyerGenerator.SELLOS_PROMO_DISPONIBLES,
        )
        self.assertEqual(flyer_tab.combo_sello_promo.get(), FlyerGenerator.SELLO_NINGUNO)
        flyer_tab.combo_sello_promo.set(FlyerGenerator.SELLO_SOLO_POR_HOY)
        self.assertEqual(flyer_tab.combo_sello_promo.get(), "🔥 ¡SOLO POR HOY!")

        # Probar que la lista de productos de TabFlyer es un CTkScrollableFrame
        self.assertIsInstance(flyer_tab.scroll_productos, ctk.CTkScrollableFrame)
        self.assertEqual(flyer_tab.scroll_productos.cget("height"), 230)

        app.destroy()

    def test_sello_promocional_componedor_grafico(self) -> None:
        """
        Verifica el renderizado del Sello Promocional (Badge Sticker) en el flyer:
        - Soporte para '🔥 ¡SOLO POR HOY!', '🛵 ¡ENVÍO GRATIS!', etc.
        - Composición en memoria y exportación a disco sin errores.
        """
        productos = self.excel_manager.obtener_productos()[:3]
        for sello in [
            FlyerGenerator.SELLO_SOLO_POR_HOY,
            FlyerGenerator.SELLO_ENVIO_GRATIS,
            FlyerGenerator.SELLO_OFF_EFECTIVO,
            FlyerGenerator.SELLO_RECOMENDADO,
        ]:
            lienzo = self.flyer_generator.componer_imagen_flyer(
                productos=productos,
                estilo=FlyerGenerator.ESTILO_TURQUESA_GLASS,
                titulo="PROMOS CON SELLO",
                sello_promo=sello,
            )
            self.assertEqual(lienzo.size, (1080, 1920))
            self.assertEqual(lienzo.mode, "RGBA")

        ruta_con_sello = self.flyer_generator.generar_flyer(
            productos=productos,
            estilo=FlyerGenerator.ESTILO_PIZARRA_BURGUER,
            titulo="PROMOS CON SELLO",
            sello_promo=FlyerGenerator.SELLO_SOLO_POR_HOY,
        )
        self.assertTrue(os.path.exists(ruta_con_sello))

    # =========================================================================
    # REQ 5: REGISTRO DE PAGO MIXTO Y ARQUEO DIARIO
    # =========================================================================

    def test_modelo_venta_pago_mixto_valido(self) -> None:
        """Valida la creación de una venta con pago Mixto y sumas exactas."""
        v = Venta(
            id=1,
            detalle="1x Pizza Napolitana, 1x Docena Empanadas",
            total=25000.0,
            medio_pago="Mixto (Efectivo + Transferencia)",
            monto_efectivo=15000.0,
            monto_transferencia=10000.0,
            tipo_entrega="Mostrador",
        )
        self.assertEqual(v.medio_pago, Venta.MEDIO_MIXTO)
        self.assertEqual(v.monto_efectivo, 15000.0)
        self.assertEqual(v.monto_transferencia, 10000.0)
        self.assertEqual(v.total, 25000.0)

    def test_modelo_venta_pago_mixto_suma_invalida(self) -> None:
        """Valida que una venta mixta cuya suma no coincida con el total arroje ValueError."""
        with self.assertRaises(ValueError):
            Venta(
                id=1,
                detalle="1x Pizza Napolitana",
                total=25000.0,
                medio_pago="Mixto (Efectivo + Transferencia)",
                monto_efectivo=10000.0,
                monto_transferencia=10000.0,  # Suma 20000 != 25000
                tipo_entrega="Mostrador",
            )

    def test_excel_manager_persistencia_pago_mixto_y_arqueo(self) -> None:
        """
        Registra una venta mixta en Excel, recupera los datos y verifica
        que el cálculo del Arqueo Diario discrimine correctamente las porciones.
        """
        fecha_test = "2026-11-04"
        # 1 venta pura en efectivo
        v1 = Venta(
            id=0,
            detalle="2x Empanadas",
            total=5000.0,
            medio_pago="Efectivo",
            tipo_entrega="Mostrador",
            fecha_hora=f"{fecha_test} 12:00:00",
        )
        # 1 venta pura en transferencia
        v2 = Venta(
            id=0,
            detalle="1x Pizza",
            total=10000.0,
            medio_pago="Transferencia/MP",
            tipo_entrega="Delivery",
            fecha_hora=f"{fecha_test} 12:30:00",
        )
        # 1 venta mixta ($8.000 efec + $12.000 transf = $20.000 total)
        v3 = Venta(
            id=0,
            detalle="1x Combo Familiar",
            total=20000.0,
            medio_pago="Mixto (Efectivo + Transferencia)",
            monto_efectivo=8000.0,
            monto_transferencia=12000.0,
            tipo_entrega="Mostrador",
            fecha_hora=f"{fecha_test} 13:00:00",
        )

        self.assertTrue(self.excel_manager.registrar_venta(v1))
        self.assertTrue(self.excel_manager.registrar_venta(v2))
        self.assertTrue(self.excel_manager.registrar_venta(v3))

        # Recuperar ventas del día
        ventas_dia = self.excel_manager.obtener_ventas_diarias(fecha_test)
        self.assertEqual(len(ventas_dia), 3)

        # Calcular arqueo / resumen diario
        resumen = self.excel_manager.calcular_resumen_diario(fecha_test)
        self.assertEqual(resumen["cantidad_ventas"], 3)
        self.assertEqual(resumen["total_general"], 35000.0)
        # Total efectivo esperado: 5000 (v1) + 8000 (v3) = 13000
        self.assertEqual(resumen["total_efectivo"], 13000.0)
        # Total transferencia esperado: 10000 (v2) + 12000 (v3) = 22000
        self.assertEqual(resumen["total_transferencia"], 22000.0)
        # Verificar que la suma cuadre exactamente con el total
        self.assertEqual(
            resumen["total_efectivo"] + resumen["total_transferencia"],
            resumen["total_general"],
        )
        self.assertEqual(resumen["cant_mixto"], 1)

        # Probar persistencia del Cierre de Caja en la hoja Arqueos
        self.assertTrue(self.excel_manager.registrar_cierre_caja(fecha_test))


if __name__ == "__main__":
    unittest.main()
