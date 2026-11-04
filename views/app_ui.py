"""
Ventana principal de la aplicación de escritorio ('Centro de Control Diario').
Coordina el encabezado institucional, el selector de modo visual (Dark / Light / System),
la paleta turquesa/esmeralda y la navegación por pestañas mediante CTkTabview.
"""

from datetime import datetime
import customtkinter as ctk

from services.excel_manager import ExcelManager
from services.flyer_generator import FlyerGenerator
from views.tab_caja import TabCaja
from views.tab_flyer import TabFlyer
from views.tab_menu import TabMenu
from views.theme_manager import ThemeManager


class AppUI(ctk.CTk):
    """
    Ventana raíz de CustomTkinter que integra los tres módulos operativos:
    1. Gestión de Menú y Precios
    2. Generador Gráfico de Flyers (9:16)
    3. Registro Rápido de Ventas / Caja Diaria
    """

    def __init__(
        self,
        excel_manager: ExcelManager,
        flyer_generator: FlyerGenerator,
    ) -> None:
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
        super().__init__()

        self.excel_manager: ExcelManager = excel_manager
        self.flyer_generator: FlyerGenerator = flyer_generator

        self.title("Centro de Control Diario — Gestión Gastronómica & Generador de Flyers")
        self.geometry("1240x760")
        self.minsize(1100, 680)

        # Configuración fluida de la grilla principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Encabezado fijo
        self.grid_rowconfigure(1, weight=1)  # Contenido fluido de pestañas
        self.grid_rowconfigure(2, weight=0)  # Pie fijo

        # Configurar color de fondo de la ventana principal
        self.configure(fg_color=ThemeManager.BG_VENTANA)

        # Aplicar estilo inicial a Treeviews
        ThemeManager.aplicar_estilo_treeview("Dark")

        self._construir_encabezado()
        self._construir_navegacion_pestanas()
        self._construir_barra_estado()

    def _construir_encabezado(self) -> None:
        """Crea el encabezado institucional con título, fecha operativa y selector de tema."""
        header = ctk.CTkFrame(
            self,
            corner_radius=0,
            height=64,
            fg_color=ThemeManager.BG_HEADER,
        )
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        bloque_titulo = ctk.CTkFrame(header, fg_color="transparent")
        bloque_titulo.grid(row=0, column=0, sticky="w", padx=22, pady=10)

        ctk.CTkLabel(
            bloque_titulo,
            text="🍽️  CENTRO DE CONTROL DIARIO  |  GESTIÓN GASTRONÓMICA",
            font=ThemeManager.get_font(18, weight="bold"),
            text_color="#F8FAFC",
        ).pack(anchor="w")

        ctk.CTkLabel(
            bloque_titulo,
            text="Administración de Menú en Excel • Automatización de Flyers 9:16 • Arqueo de Caja y Pagos Mixtos",
            font=ThemeManager.font_body(),
            text_color="#2DD4BF",  # Turquesa brillante
        ).pack(anchor="w")

        # Selector de tema visual (Dark / Light / System) y fecha actual
        bloque_der = ctk.CTkFrame(header, fg_color="transparent")
        bloque_der.grid(row=0, column=1, sticky="e", padx=22, pady=10)

        fecha_hoy = datetime.now().strftime("%d/%m/%Y")
        ctk.CTkLabel(
            bloque_der,
            text=f"📅 Fecha: {fecha_hoy}",
            font=ThemeManager.font_body_bold(),
            text_color="#CBD5E1",
        ).grid(row=0, column=0, padx=(0, 14))

        ctk.CTkLabel(
            bloque_der,
            text="Tema:",
            font=ThemeManager.font_body(),
            text_color="#94A3B8",
        ).grid(row=0, column=1, padx=(0, 6))

        self.combo_tema = ctk.CTkOptionMenu(
            bloque_der,
            values=["Dark", "Light", "System"],
            width=100,
            height=30,
            font=ThemeManager.font_small_bold(),
            fg_color=ThemeManager.COLOR_ACCENT,
            button_color=ThemeManager.COLOR_ACCENT_HOVER,
            command=self._cambiar_modo_apariencia,
        )
        self.combo_tema.set("Dark")
        self.combo_tema.grid(row=0, column=2)

    def _construir_navegacion_pestanas(self) -> None:
        """Inicializa el CTkTabview e instancia las vistas modulares de cada pestaña con títulos en 14px bold."""
        self.tabview = ctk.CTkTabview(
            self,
            corner_radius=12,
            fg_color=ThemeManager.BG_VENTANA,
            segmented_button_selected_color=ThemeManager.COLOR_ACCENT[1],
            segmented_button_selected_hover_color=ThemeManager.COLOR_ACCENT_HOVER[1],
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=14, pady=(4, 6))

        # Personalizar tipografía de los botones de pestañas a 14px negrita
        try:
            self.tabview._segmented_button.configure(
                font=ThemeManager.font_tab_title(),
            )
        except Exception:
            pass

        nombre_tab_menu = "📋  1. Menú y Precios"
        nombre_tab_flyer = "🎨  2. Generador de Flyers (9:16)"
        nombre_tab_caja = "💰  3. Caja y Arqueo Diario"

        tab_1 = self.tabview.add(nombre_tab_menu)
        tab_2 = self.tabview.add(nombre_tab_flyer)
        tab_3 = self.tabview.add(nombre_tab_caja)

        for tab in (tab_1, tab_2, tab_3):
            tab.grid_columnconfigure(0, weight=1)
            tab.grid_rowconfigure(0, weight=1)

        # Instanciar las vistas conectando el callback de sincronización
        self.vista_menu = TabMenu(
            master=tab_1,
            excel_manager=self.excel_manager,
            on_menu_change=self._sincronizar_modulos_tras_cambio_menu,
        )
        self.vista_menu.grid(row=0, column=0, sticky="nsew")

        self.vista_flyer = TabFlyer(
            master=tab_2,
            excel_manager=self.excel_manager,
            flyer_generator=self.flyer_generator,
        )
        self.vista_flyer.grid(row=0, column=0, sticky="nsew")

        self.vista_caja = TabCaja(
            master=tab_3,
            excel_manager=self.excel_manager,
        )
        self.vista_caja.grid(row=0, column=0, sticky="nsew")

    def _construir_barra_estado(self) -> None:
        """Construye el pie institucional con información del archivo de persistencia."""
        footer = ctk.CTkFrame(
            self,
            corner_radius=0,
            height=28,
            fg_color=ThemeManager.BG_FOOTER,
        )
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            footer,
            text=f"Persistencia Local: {self.excel_manager.filepath}",
            font=ThemeManager.font_small(),
            text_color="#94A3B8",
        ).grid(row=0, column=0, sticky="w", padx=18, pady=3)

        ctk.CTkLabel(
            footer,
            text="Prácticas Profesionalizantes II • Tecnicatura Superior en Desarrollo de Software",
            font=ThemeManager.font_small(),
            text_color="#64748B",
        ).grid(row=0, column=1, sticky="e", padx=18, pady=3)

    def _sincronizar_modulos_tras_cambio_menu(self) -> None:
        """
        Callback reactivo ejecutado cuando se crea, edita, elimina o actualiza
        el precio de productos en el menú, refrescando el Generador de Flyers y la Caja.
        """
        self.vista_flyer.refrescar_productos()
        self.vista_caja.refrescar_catalogo_productos()

    def _cambiar_modo_apariencia(self, nuevo_modo: str) -> None:
        """
        Cambia dinámicamente entre modo Oscuro, Claro o del Sistema,
        actualizando simultáneamente los estilos ttk de las tablas.
        """
        ctk.set_appearance_mode(nuevo_modo)
        ThemeManager.aplicar_estilo_treeview(nuevo_modo)
