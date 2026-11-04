"""
Vista de la pestaña 'Generador Gráfico de Flyers' (Módulo 2 / 3).
Soporta dos modos de generación gráfica:
1. 'Modo Promos Destacadas': 1 a 6 tarjetas grandes con descripción y precio destacado.
2. 'Modo Menú Completo': Exporta la carta entera clasificada automáticamente por categorías
   en un layout de 2 columnas verticales con encabezados en turquesa y renglones compactos.
Permite elegir entre 3 plantillas programáticas ('Pizarra Oscura', 'Turquesa Gourmet',
'Rojo Rústico') o cargar imagen propia, previsualizando en vivo en formato 9:16.
"""

import os
import subprocess
import sys
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional, Set

import customtkinter as ctk
from PIL import Image

from models.producto import Producto
from services.excel_manager import ExcelManager
from services.flyer_generator import FlyerGenerator
from views.theme_manager import ThemeManager


class TabFlyer(ctk.CTkFrame):
    """
    Interfaz de diseño y previsualización en vivo de flyers verticales (9:16) para
    Estados de WhatsApp e Historias de Instagram.
    """

    PREVIEW_WIDTH: int = 270
    PREVIEW_HEIGHT: int = 480

    TITULOS_SUGERIDOS: List[str] = [
        "PROMOS DE HOY",
        "NUESTRA CARTA COMPLETA",
        "MENÚ DEL DÍA",
        "ESPECIALES DE LA NOCHE",
        "COMBOS PARA COMPARTIR",
        "SUGERENCIAS DEL CHEF",
    ]

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        excel_manager: ExcelManager,
        flyer_generator: FlyerGenerator,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.excel_manager: ExcelManager = excel_manager
        self.flyer_generator: FlyerGenerator = flyer_generator

        self.productos_disponibles: List[Producto] = []
        self.checkbox_vars: Dict[int, ctk.BooleanVar] = {}
        self.plantilla_seleccionada: Optional[str] = None
        self.logo_path: Optional[str] = None
        self.ultimo_flyer_generado: Optional[str] = None
        self.modo_actual: str = FlyerGenerator.MODO_PROMOS_DESTACADAS
        self._seleccion_promos_backup: Set[int] = set()

        # Referencia persistente a la instancia de CTkImage para evitar que el
        # Garbage Collector (GC) de Python destruya la imagen del canvas en memoria
        self._ctk_preview_image: Optional[ctk.CTkImage] = None

        self._configurar_grilla()
        self._construir_panel_configuracion()
        self._construir_panel_previsualizacion()
        self.refrescar_productos()

    def _configurar_grilla(self) -> None:
        """Divide la pestaña en panel de configuración/selección (izq) y previsualización (der)."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=345)
        self.grid_rowconfigure(0, weight=1)

    def _construir_panel_configuracion(self) -> None:
        """Construye la zona izquierda con selector de modo, selección de platos y ajustes."""
        panel_izq = ctk.CTkScrollableFrame(self, fg_color="transparent")
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=(4, 10), pady=4)
        panel_izq.grid_columnconfigure(0, weight=1)
        panel_izq.grid_rowconfigure(1, weight=1)

        # --- Bloque 0: Selector de Modo de Generación (Promos Destacadas vs Menú Completo) ---
        card_modo = ctk.CTkFrame(
            panel_izq,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_modo.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        card_modo.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card_modo,
            text="Modo de Generación:",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", padx=(16, 12), pady=6)

        self.seg_modo_flyer = ctk.CTkSegmentedButton(
            card_modo,
            values=FlyerGenerator.MODOS_DISPONIBLES,
            height=32,
            font=ThemeManager.font_body_bold(),
            selected_color=ThemeManager.COLOR_ACCENT[1],
            selected_hover_color=ThemeManager.COLOR_ACCENT_HOVER[1],
            command=self._al_cambiar_modo_generacion,
        )
        self.seg_modo_flyer.set(FlyerGenerator.MODO_PROMOS_DESTACADAS)
        self.seg_modo_flyer.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=6)

        # --- Bloque 1: Selección de Productos mediante Checkboxes ---
        card_seleccion = ctk.CTkFrame(
            panel_izq,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_seleccion.grid(row=1, column=0, sticky="nsew", pady=(0, 6))
        card_seleccion.grid_columnconfigure(0, weight=1)
        card_seleccion.grid_rowconfigure(1, weight=1)

        header_sel = ctk.CTkFrame(card_seleccion, fg_color="transparent")
        header_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=(8, 4))
        header_sel.grid_columnconfigure(0, weight=1)

        self.lbl_titulo_seleccion = ctk.CTkLabel(
            header_sel,
            text="1. Seleccione los Productos a Destacar (Máximo 6)",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        )
        self.lbl_titulo_seleccion.grid(row=0, column=0, sticky="w")

        self.lbl_seleccionados = ctk.CTkLabel(
            header_sel,
            text="Seleccionados: 0 / 6",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_seleccionados.grid(row=0, column=1, padx=(10, 10))

        self.btn_accion_rapida_sel = ctk.CTkButton(
            header_sel,
            text="Marcar 4 primeros",
            width=135,
            height=30,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_small_bold(),
            command=self._accion_boton_marcar_rapido,
        )
        self.btn_accion_rapida_sel.grid(row=0, column=2, padx=(0, 6))

        btn_desmarcar = ctk.CTkButton(
            header_sel,
            text="Limpiar",
            width=80,
            height=30,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_small_bold(),
            command=self._desmarcar_todos,
        )
        btn_desmarcar.grid(row=0, column=3)

        self.scroll_productos = ctk.CTkScrollableFrame(
            card_seleccion,
            height=230,
            corner_radius=8,
            fg_color=ThemeManager.BG_BOX_INTERNO,
        )
        self.scroll_productos.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self.scroll_productos.grid_columnconfigure(0, weight=1)
        self.scroll_productos.grid_rowconfigure(0, weight=1)

        # --- Bloque 2: Personalización Visual y Generación ---
        card_ajustes = ctk.CTkFrame(
            panel_izq,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_ajustes.grid(row=2, column=0, sticky="ew")
        card_ajustes.grid_columnconfigure(0, weight=1)
        card_ajustes.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card_ajustes,
            text="2. Personalización del Flyer y Plantilla Visual",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(8, 4))

        # Fila 1: Título y WhatsApp
        ctk.CTkLabel(
            card_ajustes,
            text="Título del Encabezado:",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 1))

        ctk.CTkLabel(
            card_ajustes,
            text="WhatsApp de Pedidos (Pie de Página):",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=1, column=1, sticky="w", padx=16, pady=(0, 1))

        self.combo_titulo = ctk.CTkComboBox(
            card_ajustes,
            values=self.TITULOS_SUGERIDOS,
            height=32,
            font=ThemeManager.font_input(),
            command=lambda _val: self._actualizar_preview_en_vivo(),
        )
        self.combo_titulo.set("PROMOS DE HOY")
        self.combo_titulo.grid(row=2, column=0, sticky="ew", padx=(16, 8), pady=(0, 4))
        self.combo_titulo.bind("<KeyRelease>", lambda _e: self._actualizar_preview_en_vivo())

        self.entry_whatsapp = ctk.CTkEntry(
            card_ajustes,
            placeholder_text="Ej: 3794-123456",
            height=32,
            font=ThemeManager.font_input(),
        )
        self.entry_whatsapp.insert(0, "3794-556677")
        self.entry_whatsapp.grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(0, 4))
        self.entry_whatsapp.bind("<KeyRelease>", lambda _e: self._actualizar_preview_en_vivo())

        # Fila 2: Selector de Plantilla Predefinida (Multi-Plantillas) y Botón de Imagen Externa
        ctk.CTkLabel(
            card_ajustes,
            text="Plantilla de Diseño Programática (Pillow):",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=3, column=0, sticky="w", padx=16, pady=(0, 1))

        ctk.CTkLabel(
            card_ajustes,
            text="Imagen de Fondo Personalizada (Opcional):",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=3, column=1, sticky="w", padx=16, pady=(0, 1))

        self.combo_estilo = ctk.CTkOptionMenu(
            card_ajustes,
            values=FlyerGenerator.PLANTILLAS_DISPONIBLES,
            height=32,
            font=ThemeManager.font_body_bold(),
            fg_color=ThemeManager.COLOR_ACCENT,
            button_color=ThemeManager.COLOR_ACCENT_HOVER,
            command=self._al_cambiar_estilo_plantilla,
        )
        self.combo_estilo.set(FlyerGenerator.ESTILO_PIZARRA_BURGUER)
        self.combo_estilo.grid(row=4, column=0, sticky="ew", padx=(16, 8), pady=(0, 4))

        fila_btns_img = ctk.CTkFrame(card_ajustes, fg_color="transparent")
        fila_btns_img.grid(row=4, column=1, sticky="ew", padx=(8, 16), pady=(0, 4))
        fila_btns_img.grid_columnconfigure(0, weight=1)

        btn_elegir_plantilla = ctk.CTkButton(
            fila_btns_img,
            text="📂 Elegir Imagen (.png/.jpg)",
            height=32,
            font=ThemeManager.font_small_bold(),
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            command=self._seleccionar_archivo_plantilla,
        )
        btn_elegir_plantilla.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_reset_plantilla = ctk.CTkButton(
            fila_btns_img,
            text="Usar Estilo",
            width=85,
            height=32,
            font=ThemeManager.font_small_bold(),
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            command=self._restablecer_plantilla_default,
        )
        self.btn_reset_plantilla.grid(row=0, column=1)

        # Etiqueta de estado de plantilla activa
        self.lbl_plantilla_actual = ctk.CTkLabel(
            card_ajustes,
            text=f"Plantilla activa: {FlyerGenerator.ESTILO_PIZARRA_BURGUER} (Grafito, acentos rojos y Bebas Neue)",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            anchor="w",
        )
        self.lbl_plantilla_actual.grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 4)
        )

        # Fila 3: Logo del Comercio y Sello Promocional
        ctk.CTkLabel(
            card_ajustes,
            text="Logo del Comercio (Header & Marca de Agua):",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=6, column=0, sticky="w", padx=16, pady=(0, 1))

        ctk.CTkLabel(
            card_ajustes,
            text="Sello Promocional / Cinta de Oferta:",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=6, column=1, sticky="w", padx=16, pady=(0, 1))

        fila_btns_logo = ctk.CTkFrame(card_ajustes, fg_color="transparent")
        fila_btns_logo.grid(row=7, column=0, sticky="ew", padx=(16, 8), pady=(0, 4))
        fila_btns_logo.grid_columnconfigure(0, weight=1)

        btn_elegir_logo = ctk.CTkButton(
            fila_btns_logo,
            text="🖼 Elegir Logo (.png/.jpg)",
            height=32,
            font=ThemeManager.font_small_bold(),
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            command=self._seleccionar_archivo_logo,
        )
        btn_elegir_logo.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self.btn_quitar_logo = ctk.CTkButton(
            fila_btns_logo,
            text="Quitar",
            width=70,
            height=32,
            font=ThemeManager.font_small_bold(),
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            command=self._quitar_logo,
        )
        self.btn_quitar_logo.grid(row=0, column=1)

        self.combo_sello_promo = ctk.CTkOptionMenu(
            card_ajustes,
            values=FlyerGenerator.SELLOS_PROMO_DISPONIBLES,
            height=32,
            font=ThemeManager.font_body_bold(),
            fg_color=ThemeManager.COLOR_ACCENT,
            button_color=ThemeManager.COLOR_ACCENT_HOVER,
            command=lambda _val: self._actualizar_preview_en_vivo(),
        )
        self.combo_sello_promo.set(FlyerGenerator.SELLO_NINGUNO)
        self.combo_sello_promo.grid(row=7, column=1, sticky="ew", padx=(8, 16), pady=(0, 4))

        self.lbl_logo_actual = ctk.CTkLabel(
            card_ajustes,
            text="Sin logo (No se estampará marca de agua)",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
            anchor="w",
        )
        self.lbl_logo_actual.grid(row=8, column=0, sticky="ew", padx=(16, 8), pady=(0, 6))

        self.lbl_sello_info = ctk.CTkLabel(
            card_ajustes,
            text="Sticker visible en la esquina del flyer",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
            anchor="w",
        )
        self.lbl_sello_info.grid(row=8, column=1, sticky="ew", padx=(8, 16), pady=(0, 6))

        # Botón Principal de Generación
        self.btn_generar = ctk.CTkButton(
            card_ajustes,
            text="🎨  EXPORTAR FLYER PROMOCIONAL (1080x1920 px .PNG)",
            height=40,
            fg_color=ThemeManager.BTN_PRIMARY,
            hover_color=ThemeManager.BTN_PRIMARY_HOVER,
            font=ThemeManager.font_card_title(),
            command=self._accion_generar_flyer,
        )
        self.btn_generar.grid(
            row=9, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 10)
        )

    def _construir_panel_previsualizacion(self) -> None:
        """Construye la columna derecha con el lienzo escalado 9:16 de previsualización."""
        card_preview = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_preview.grid(row=0, column=1, sticky="nsew", padx=(0, 4), pady=4)
        card_preview.grid_columnconfigure(0, weight=1)
        card_preview.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card_preview,
            text="Vista Previa en Vivo (Formato 9:16)",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, padx=16, pady=(12, 4))

        marco_imagen = ctk.CTkFrame(
            card_preview,
            width=self.PREVIEW_WIDTH + 14,
            height=self.PREVIEW_HEIGHT + 14,
            corner_radius=12,
            fg_color=ThemeManager.BG_BOX_INTERNO,
        )
        marco_imagen.grid(row=1, column=0, padx=16, pady=4)

        self.lbl_imagen_preview = ctk.CTkLabel(
            marco_imagen,
            text="Previsualización\n1080 x 1920 px",
            width=self.PREVIEW_WIDTH,
            height=self.PREVIEW_HEIGHT,
        )
        self.lbl_imagen_preview.pack(padx=6, pady=6)

        self.lbl_ruta_exportada = ctk.CTkLabel(
            card_preview,
            text="Previsualización en vivo activa • Listo para exportar",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
            wraplength=300,
        )
        self.lbl_ruta_exportada.grid(row=2, column=0, padx=14, pady=(2, 6))

        self.btn_abrir_output = ctk.CTkButton(
            card_preview,
            text="📁 Abrir Carpeta output/",
            height=34,
            font=ThemeManager.font_small_bold(),
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            command=self._abrir_carpeta_output,
        )
        self.btn_abrir_output.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))

    # =========================================================================
    # LÓGICA DE MODOS DE GENERACIÓN, SELECCIÓN Y PREVISUALIZACIÓN EN VIVO
    # =========================================================================

    def _al_cambiar_modo_generacion(self, nuevo_modo: str) -> None:
        """
        Alterna entre 'Modo Promos Destacadas' (1 a 6 tarjetas grandes) y
        'Modo Menú Completo' (carta entera clasificada por categorías en 2 columnas).
        """
        modo_previo = self.modo_actual
        self.modo_actual = nuevo_modo

        if nuevo_modo == FlyerGenerator.MODO_MENU_COMPLETO:
            if modo_previo == FlyerGenerator.MODO_PROMOS_DESTACADAS:
                self._seleccion_promos_backup = {
                    pid for pid, var in self.checkbox_vars.items() if var.get()
                }
            # En Modo Menú Completo se marcan todos los platos por defecto
            for var in self.checkbox_vars.values():
                var.set(True)

            self.lbl_titulo_seleccion.configure(
                text="1. Carta Completa por Secciones (2 Columnas)"
            )
            self.btn_accion_rapida_sel.configure(text="Marcar Todos")
            self.btn_generar.configure(
                text="📋  EXPORTAR MENÚ COMPLETO POR SECCIONES (1080x1920 .PNG)"
            )
            if self.combo_titulo.get().strip().upper() == "PROMOS DE HOY":
                self.combo_titulo.set("NUESTRA CARTA COMPLETA")
        else:
            # Restaurar selección previa de Promos Destacadas (máximo 6)
            if self._seleccion_promos_backup:
                for pid, var in self.checkbox_vars.items():
                    var.set(pid in self._seleccion_promos_backup)
            else:
                for idx, prod in enumerate(self.productos_disponibles):
                    if prod.id in self.checkbox_vars:
                        self.checkbox_vars[prod.id].set(idx < 4)

            self.lbl_titulo_seleccion.configure(
                text="1. Seleccione los Productos a Destacar (Máximo 6)"
            )
            self.btn_accion_rapida_sel.configure(text="Marcar 4 primeros")
            self.btn_generar.configure(
                text="🎨  EXPORTAR FLYER PROMOCIONAL (1080x1920 px .PNG)"
            )
            if self.combo_titulo.get().strip().upper() == "NUESTRA CARTA COMPLETA":
                self.combo_titulo.set("PROMOS DE HOY")

        self._actualizar_contador_seleccion()
        self._actualizar_preview_en_vivo()

    def _obtener_productos_seleccionados(self) -> List[Producto]:
        """Retorna la lista de productos cuyos checkboxes están actualmente marcados."""
        marcados = [
            prod
            for prod in self.productos_disponibles
            if self.checkbox_vars.get(prod.id) and self.checkbox_vars[prod.id].get()
        ]
        # Si está en Modo Menú Completo y ningún checkbox quedó tildado, exportar la carta entera
        if self.modo_actual == FlyerGenerator.MODO_MENU_COMPLETO and not marcados:
            return list(self.productos_disponibles)
        return marcados

    def _al_cambiar_estilo_plantilla(self, nuevo_estilo: str) -> None:
        """Callback ejecutado al cambiar la plantilla desde el CTkOptionMenu."""
        desc_map = {
            FlyerGenerator.ESTILO_PIZARRA_BURGUER: "Grafito, acentos rojo brasa y tipografía Bebas Neue",
            FlyerGenerator.ESTILO_PIZZERIA_RUSTICA: "Horno de leña y terracota con tipografía Playfair",
            FlyerGenerator.ESTILO_FAST_FOOD_MOSTAZA: "Pop moderno amarillo mostaza con tarjetas contrastadas",
            FlyerGenerator.ESTILO_TURQUESA_GLASS: "Glassmorphism moderno en petróleo y menta brillante",
            FlyerGenerator.ESTILO_GOURMET_BISTRO: "Elegancia minimalista con filetes dorados y serif bistró",
        }
        detalle = desc_map.get(nuevo_estilo, nuevo_estilo)
        if self.plantilla_seleccionada:
            self.lbl_plantilla_actual.configure(
                text=f"Plantilla activa: {nuevo_estilo} (sobre imagen personalizada)",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
        else:
            self.lbl_plantilla_actual.configure(
                text=f"Plantilla activa: {nuevo_estilo} ({detalle})",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
        self._actualizar_preview_en_vivo()

    def _seleccionar_archivo_logo(self) -> None:
        """Abre un cuadro de diálogo para seleccionar el logo del comercio (.png / .jpg)."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar Logo del Comercio",
            filetypes=[
                ("Imágenes PNG / JPG", "*.png *.jpg *.jpeg *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if ruta and os.path.exists(ruta):
            self.logo_path = ruta
            nombre_corto = os.path.basename(ruta)
            self.lbl_logo_actual.configure(
                text=f"✔ Logo activo: {nombre_corto} (Header + Marca de agua)",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
            self._actualizar_preview_en_vivo()

    def _quitar_logo(self) -> None:
        """Remueve el logo activo y la marca de agua translúcida."""
        self.logo_path = None
        self.lbl_logo_actual.configure(
            text="Sin logo (No se estampará marca de agua)",
            text_color=ThemeManager.TEXT_MUTED,
        )
        self._actualizar_preview_en_vivo()

    def refrescar_productos(self) -> None:
        """
        Recarga los productos desde Excel preservando las selecciones previas
        que continúen existiendo y actualiza la vista previa en vivo.
        """
        ids_previamente_marcados = {
            pid for pid, var in self.checkbox_vars.items() if var.get()
        }

        for widget in self.scroll_productos.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        self.productos_disponibles = self.excel_manager.obtener_productos()

        if not self.productos_disponibles:
            ctk.CTkLabel(
                self.scroll_productos,
                text="No hay productos cargados en el menú. Agregue platos desde la pestaña 'Gestión de Menú'.",
                font=ThemeManager.font_body(),
                text_color=ThemeManager.TEXT_MUTED,
            ).grid(row=0, column=0, padx=10, pady=20)
            self._actualizar_contador_seleccion()
            self._actualizar_preview_en_vivo()
            return

        es_menu_completo = self.modo_actual == FlyerGenerator.MODO_MENU_COMPLETO
        preseleccionar_inicial = len(ids_previamente_marcados) == 0

        for idx, prod in enumerate(self.productos_disponibles):
            fila_item = ctk.CTkFrame(
                self.scroll_productos,
                height=34,
                corner_radius=6,
                fg_color=ThemeManager.BG_CARD,
                border_width=1,
                border_color=ThemeManager.BORDER_CARD,
            )
            fila_item.grid(row=idx, column=0, sticky="ew", padx=4, pady=2)
            fila_item.grid_columnconfigure(0, weight=1)

            if es_menu_completo:
                marcado = (
                    True
                    if preseleccionar_inicial
                    else (prod.id in ids_previamente_marcados)
                )
            else:
                marcado = (
                    (idx < 4)
                    if preseleccionar_inicial
                    else (prod.id in ids_previamente_marcados)
                )

            var = ctk.BooleanVar(value=marcado)
            self.checkbox_vars[prod.id] = var

            texto_cb = f"[{prod.categoria}]  {prod.nombre}"
            cb = ctk.CTkCheckBox(
                fila_item,
                text=texto_cb,
                variable=var,
                font=ThemeManager.font_product_name(),
                text_color=ThemeManager.TEXT_MAIN,
                command=lambda p_id=prod.id: self._al_cambiar_checkbox(p_id),
            )
            cb.grid(row=0, column=0, sticky="w", padx=10, pady=3)

            lbl_precio = ctk.CTkLabel(
                fila_item,
                text=prod.precio_formateado,
                font=ThemeManager.font_price_highlight(),
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
            lbl_precio.grid(row=0, column=1, sticky="e", padx=10, pady=3)

        self._actualizar_contador_seleccion()
        self._actualizar_preview_en_vivo()

    def _al_cambiar_checkbox(self, prod_id: int) -> None:
        """
        Verifica el cupo máximo de 6 productos en 'Modo Promos Destacadas'
        (sin límite en 'Modo Menú Completo') y actualiza la Vista Previa en vivo.
        """
        marcados = [pid for pid, var in self.checkbox_vars.items() if var.get()]
        if (
            self.modo_actual == FlyerGenerator.MODO_PROMOS_DESTACADAS
            and len(marcados) > FlyerGenerator.MAX_PRODUCTOS
        ):
            self.checkbox_vars[prod_id].set(False)
            messagebox.showwarning(
                "Límite de Promos Destacadas Alcanzado",
                f"En 'Modo Promos Destacadas' se permiten hasta {FlyerGenerator.MAX_PRODUCTOS} "
                f"productos para garantizar la legibilidad.\n\n"
                f"💡 Si desea exportar todos los platos, cambie a 'Modo Menú Completo'.",
            )
            return

        self._actualizar_contador_seleccion()
        self._actualizar_preview_en_vivo()

    def _actualizar_contador_seleccion(self) -> None:
        """Actualiza la etiqueta del contador según el modo de generación activo."""
        cant = sum(1 for var in self.checkbox_vars.values() if var.get())
        if self.modo_actual == FlyerGenerator.MODO_MENU_COMPLETO:
            prods_activos = self._obtener_productos_seleccionados()
            cats = len({p.categoria for p in prods_activos})
            self.lbl_seleccionados.configure(
                text=f"Carta: {len(prods_activos)} platos ({cats} secc.)",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
        else:
            color = (
                ThemeManager.COLOR_NUMEROS_DESTACADOS
                if 1 <= cant <= FlyerGenerator.MAX_PRODUCTOS
                else ("#DC2626", "#F87171")
            )
            self.lbl_seleccionados.configure(
                text=f"Seleccionados: {cant} / {FlyerGenerator.MAX_PRODUCTOS}",
                text_color=color,
            )

    def _accion_boton_marcar_rapido(self) -> None:
        """Marca todos los productos en Modo Menú Completo o los primeros 4 en Modo Promos."""
        if self.modo_actual == FlyerGenerator.MODO_MENU_COMPLETO:
            for var in self.checkbox_vars.values():
                var.set(True)
        else:
            for idx, prod in enumerate(self.productos_disponibles):
                if prod.id in self.checkbox_vars:
                    self.checkbox_vars[prod.id].set(idx < 4)
        self._actualizar_contador_seleccion()
        self._actualizar_preview_en_vivo()

    def _seleccionar_primeros_cuatro(self) -> None:
        """Marca automáticamente los primeros 4 productos de la lista y refresca la vista previa."""
        for idx, prod in enumerate(self.productos_disponibles):
            if prod.id in self.checkbox_vars:
                self.checkbox_vars[prod.id].set(idx < 4)
        self._actualizar_contador_seleccion()
        self._actualizar_preview_en_vivo()

    def _desmarcar_todos(self) -> None:
        """Limpia todos los checkboxes de productos y refresca la vista previa."""
        for var in self.checkbox_vars.values():
            var.set(False)
        self._actualizar_contador_seleccion()
        self._actualizar_preview_en_vivo()

    def _seleccionar_archivo_plantilla(self) -> None:
        """Abre un cuadro de diálogo para elegir una imagen de fondo (.png / .jpg)."""
        ruta = filedialog.askopenfilename(
            title="Seleccionar Plantilla de Fondo (1080x1920)",
            initialdir=self.flyer_generator.templates_dir,
            filetypes=[
                ("Imágenes PNG / JPG", "*.png *.jpg *.jpeg *.webp"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if ruta and os.path.exists(ruta):
            self.plantilla_seleccionada = ruta
            nombre_corto = os.path.basename(ruta)
            estilo_actual = self.combo_estilo.get()
            self.lbl_plantilla_actual.configure(
                text=f"Imagen activa: {nombre_corto} (Esquema: {estilo_actual})",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
            self._actualizar_preview_en_vivo()

    def _restablecer_plantilla_default(self) -> None:
        """Vuelve a configurar el fondo degradado programático de la plantilla elegida."""
        self.plantilla_seleccionada = None
        estilo = self.combo_estilo.get()
        self._al_cambiar_estilo_plantilla(estilo)

    def _renderizar_pil_en_preview(self, imagen_pil: Image.Image) -> None:
        """
        Escala una imagen PIL a (PREVIEW_WIDTH x PREVIEW_HEIGHT) y actualiza el widget
        CTkLabel manteniendo una referencia fija en `self._ctk_preview_image` para
        evitar que el recolector de basura (GC) de Python destruya el recurso en memoria.
        """
        try:
            copia_preview = imagen_pil.convert("RGBA").resize(
                (self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT),
                Image.Resampling.LANCZOS,
            )
            self._ctk_preview_image = ctk.CTkImage(
                light_image=copia_preview,
                dark_image=copia_preview,
                size=(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT),
            )
            self.lbl_imagen_preview.configure(image=self._ctk_preview_image, text="")
            self.lbl_imagen_preview.image = self._ctk_preview_image  # type: ignore[attr-defined]
        except Exception as err:
            self.lbl_imagen_preview.configure(text=f"No se pudo previsualizar:\n{err}")

    def _cargar_imagen_en_preview(self, ruta_imagen: str) -> None:
        """Carga una imagen desde disco y la muestra en el panel de vista previa."""
        try:
            with Image.open(ruta_imagen) as img:
                self._renderizar_pil_en_preview(img.copy())
        except Exception as err:
            self.lbl_imagen_preview.configure(text=f"No se pudo previsualizar:\n{err}")

    def _actualizar_preview_en_vivo(self) -> None:
        """
        Compone dinámicamente en memoria el flyer según el modo activo
        ('Modo Promos Destacadas' o 'Modo Menú Completo') y la plantilla seleccionada,
        actualizando en tiempo real la Vista Previa.
        """
        if not hasattr(self, "lbl_imagen_preview"):
            return

        productos_elegidos = self._obtener_productos_seleccionados()
        titulo = (
            self.combo_titulo.get().strip()
            if hasattr(self, "combo_titulo") and self.combo_titulo.get().strip()
            else "PROMOS DE HOY"
        )
        whatsapp = (
            self.entry_whatsapp.get().strip()
            if hasattr(self, "entry_whatsapp")
            else ""
        )
        estilo = (
            self.combo_estilo.get()
            if hasattr(self, "combo_estilo") and self.combo_estilo.get()
            else FlyerGenerator.ESTILO_PIZARRA_BURGUER
        )
        sello_promo = (
            self.combo_sello_promo.get()
            if hasattr(self, "combo_sello_promo")
            else None
        )

        try:
            lienzo_vivo = self.flyer_generator.componer_imagen_flyer(
                productos=productos_elegidos,
                plantilla_path=self.plantilla_seleccionada,
                estilo=estilo,
                titulo=titulo,
                whatsapp=whatsapp,
                modo=self.modo_actual,
                logo_path=self.logo_path,
                sello_promo=sello_promo,
            )
            self._renderizar_pil_en_preview(lienzo_vivo)
        except Exception as err:
            self.lbl_imagen_preview.configure(text=f"Error en vista previa:\n{err}")

    def _accion_generar_flyer(self) -> None:
        """Recopila los productos y exporta el flyer o carta completa en alta resolución."""
        productos_elegidos = self._obtener_productos_seleccionados()

        if not productos_elegidos:
            messagebox.showwarning(
                "Sin Productos Seleccionados",
                "Por favor, marque al menos 1 producto de la lista para exportar el flyer.",
            )
            return

        titulo = self.combo_titulo.get().strip() or "PROMOS DE HOY"
        whatsapp = self.entry_whatsapp.get().strip()
        estilo = (
            self.combo_estilo.get()
            if hasattr(self, "combo_estilo")
            else FlyerGenerator.ESTILO_PIZARRA_BURGUER
        )
        sello_promo = (
            self.combo_sello_promo.get()
            if hasattr(self, "combo_sello_promo")
            else None
        )

        try:
            ruta_exportada = self.flyer_generator.generar_flyer(
                productos=productos_elegidos,
                plantilla_path=self.plantilla_seleccionada,
                estilo=estilo,
                titulo=titulo,
                whatsapp=whatsapp,
                modo=self.modo_actual,
                logo_path=self.logo_path,
                sello_promo=sello_promo,
            )
            self.ultimo_flyer_generado = ruta_exportada
            self._cargar_imagen_en_preview(ruta_exportada)

            nombre_archivo = os.path.basename(ruta_exportada)
            self.lbl_ruta_exportada.configure(
                text=f"✔ Exportado: output/{nombre_archivo}",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
            messagebox.showinfo(
                "Flyer Generado con Éxito",
                f"El diseño [{self.modo_actual} — {estilo}] (1080x1920 px) se guardó en:\n\n{ruta_exportada}",
            )
        except Exception as err:
            messagebox.showerror(
                "Error al Generar Flyer",
                f"Ocurrió un problema durante el renderizado gráfico:\n{err}",
            )

    def _abrir_carpeta_output(self) -> None:
        """Abre el directorio `output/` en el explorador de archivos del sistema."""
        ruta = self.flyer_generator.output_dir
        os.makedirs(ruta, exist_ok=True)
        try:
            if sys.platform.startswith("win"):
                os.startfile(ruta)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", ruta])
            else:
                subprocess.Popen(["xdg-open", ruta])
        except Exception as err:
            messagebox.showinfo("Ruta de Exportación", f"Carpeta de salida:\n{ruta}\n({err})")
