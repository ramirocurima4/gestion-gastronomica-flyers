"""
Módulo de Gestión Centralizada de Temas, Paleta de Colores y Tipografías.
Implementa el sistema visual refinado con soporte para Modo Oscuro y Modo Claro:
- Paleta turquesa / esmeralda (#14b8a6 / #10b981 / #0ea5e9 / #2dd4bf).
- Selección de tablas de alto contraste en Turquesa Noche (#0f766e) con texto blanco (#ffffff).
- Modo Oscuro: Fondo grafito profundo (#0b0f19), tarjetas intermedias (#161e2e),
  textos blanco hueso (#f8fafc) y números destacados en turquesa brillante (#2dd4bf).
- Modo Claro: Fondo verde menta grisáceo suave (#f0fdf4), tarjetas blancas (#ffffff)
  con bordes turquesa sutil (#ccfbf1), textos gris oscuro (#0f172a) para máxima legibilidad.
- Tipografías sans-serif incrementadas en +1/+2 pts para óptima legibilidad en tablas y entradas.
"""

import logging
from tkinter import font as tkfont, ttk
from typing import Optional, Tuple
import customtkinter as ctk

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    Administrador centralizado de estilos visuales, colores y tipografías para CustomTkinter y TTK.
    """

    # =========================================================================
    # PALETA DE COLORES (Tuplas: [Modo Claro, Modo Oscuro])
    # =========================================================================

    # Fondos principales y encabezados
    BG_VENTANA: Tuple[str, str] = ("#F0FDF4", "#0B0F19")
    BG_HEADER: Tuple[str, str] = ("#0F172A", "#0B0F19")
    BG_FOOTER: Tuple[str, str] = ("#0F172A", "#0B0F19")

    # Tarjetas intermedias y contenedores
    BG_CARD: Tuple[str, str] = ("#FFFFFF", "#161E2E")
    BORDER_CARD: Tuple[str, str] = ("#CCFBF1", "#1E293B")
    BG_BOX_INTERNO: Tuple[str, str] = ("#F8FAFC", "#0D1117")

    # Acentos visuales (Turquesa / Verde Esmeralda)
    COLOR_ACCENT: Tuple[str, str] = ("#0D9488", "#14B8A6")
    COLOR_ACCENT_HOVER: Tuple[str, str] = ("#0F766E", "#0D9488")
    COLOR_NUMEROS_DESTACADOS: Tuple[str, str] = ("#0D9488", "#2DD4BF")  # Turquesa brillante

    # Selección de alto contraste (Turquesa Noche + Blanco)
    TREEVIEW_SEL_BG: str = "#0F766E"
    TREEVIEW_SEL_FG: str = "#FFFFFF"

    # Textos
    TEXT_MAIN: Tuple[str, str] = ("#0F172A", "#F8FAFC")
    TEXT_MUTED: Tuple[str, str] = ("#475569", "#94A3B8")
    TEXT_ACCENT: Tuple[str, str] = ("#0D9488", "#2DD4BF")

    # Estados semánticos y botones
    BTN_SUCCESS: Tuple[str, str] = ("#16A34A", "#10B981")
    BTN_SUCCESS_HOVER: Tuple[str, str] = ("#15803D", "#059669")

    BTN_PRIMARY: Tuple[str, str] = ("#0D9488", "#14B8A6")
    BTN_PRIMARY_HOVER: Tuple[str, str] = ("#0F766E", "#0D9488")

    BTN_WARNING: Tuple[str, str] = ("#D97706", "#F59E0B")
    BTN_WARNING_HOVER: Tuple[str, str] = ("#B45309", "#D97706")

    BTN_DANGER: Tuple[str, str] = ("#DC2626", "#EF4444")
    BTN_DANGER_HOVER: Tuple[str, str] = ("#B91C1C", "#DC2626")

    BTN_SECONDARY: Tuple[str, str] = ("#E2E8F0", "#334155")
    BTN_SECONDARY_HOVER: Tuple[str, str] = ("#CBD5E1", "#475569")
    BTN_SECONDARY_TEXT: Tuple[str, str] = ("#0F172A", "#F8FAFC")

    # Caché interna de la familia tipográfica seleccionada
    _familia_fuente: Optional[str] = None

    @classmethod
    def resolver_familia_fuente(cls) -> str:
        """
        Detecta y selecciona la mejor familia tipográfica sans-serif disponible en el sistema.
        Prioridad: Inter -> Montserrat -> Segoe UI -> Ubuntu Sans -> DejaVu Sans -> Liberation Sans -> Helvetica -> Arial.
        """
        if cls._familia_fuente is not None:
            return cls._familia_fuente

        candidatos = [
            "Inter",
            "Montserrat",
            "Segoe UI",
            "Ubuntu Sans",
            "Ubuntu",
            "DejaVu Sans",
            "Liberation Sans",
            "Helvetica",
            "Arial",
        ]

        try:
            familias_disponibles = set(tkfont.families())
            for candidato in candidatos:
                if any(
                    candidato.lower() == f.lower() or candidato.lower() in f.lower()
                    for f in familias_disponibles
                ):
                    cls._familia_fuente = candidato
                    return cls._familia_fuente
        except Exception as exc:
            logger.debug("No se pudo consultar tkfont.families: %s", exc)

        cls._familia_fuente = "DejaVu Sans"
        return cls._familia_fuente

    @classmethod
    def get_font(cls, size: int, weight: str = "normal") -> ctk.CTkFont:
        """
        Retorna un objeto `CTkFont` estandarizado con la familia sans-serif seleccionada.

        Args:
            size (int): Tamaño en puntos/píxeles de la fuente.
            weight (str): 'normal' o 'bold'.
        """
        try:
            import tkinter as tk

            if tk._default_root is None:
                root = tk.Tk()
                root.withdraw()
        except Exception:
            pass

        familia = cls.resolver_familia_fuente()
        return ctk.CTkFont(family=familia, size=size, weight=weight)

    # =========================================================================
    # FUENTES ESTANDARIZADAS REUTILIZABLES (AUMENTADAS +1/+2 PTS PARA LEGIBILIDAD)
    # =========================================================================

    @classmethod
    def font_tab_title(cls) -> ctk.CTkFont:
        """Título de pestañas: 14px negrita."""
        return cls.get_font(14, weight="bold")

    @classmethod
    def font_card_title(cls) -> ctk.CTkFont:
        """Título de tarjetas / módulos: 16px negrita."""
        return cls.get_font(16, weight="bold")

    @classmethod
    def font_product_name(cls) -> ctk.CTkFont:
        """Nombres de productos del menú: 14px negrita (+1 pt)."""
        return cls.get_font(14, weight="bold")

    @classmethod
    def font_input(cls, bold: bool = False) -> ctk.CTkFont:
        """Campos de entrada de datos (Entry, ComboBox, Textbox): 14px (+2 pts)."""
        return cls.get_font(14, weight="bold" if bold else "normal")

    @classmethod
    def font_kpi_value(cls, grande: bool = True) -> ctk.CTkFont:
        """Valores monetarios destacados: 18px o 22px negrita."""
        return cls.get_font(22 if grande else 18, weight="bold")

    @classmethod
    def font_price_highlight(cls) -> ctk.CTkFont:
        """Precios unitarios destacados: 16px negrita."""
        return cls.get_font(16, weight="bold")

    @classmethod
    def font_body(cls) -> ctk.CTkFont:
        """Texto estándar de cuerpo y etiquetas: 13px normal (+1 pt)."""
        return cls.get_font(13, weight="normal")

    @classmethod
    def font_body_bold(cls) -> ctk.CTkFont:
        """Texto estándar enfatizado: 13px negrita (+1 pt)."""
        return cls.get_font(13, weight="bold")

    @classmethod
    def font_small(cls) -> ctk.CTkFont:
        """Texto secundario, avisos y leyendas: 12px normal (+1 pt)."""
        return cls.get_font(12, weight="normal")

    @classmethod
    def font_small_bold(cls) -> ctk.CTkFont:
        """Texto secundario en negrita: 12px negrita (+1 pt)."""
        return cls.get_font(12, weight="bold")

    # =========================================================================
    # ESTILIZACIÓN DE TABLAS (TTK TREEVIEW)
    # =========================================================================

    @classmethod
    def aplicar_estilo_treeview(cls, modo: Optional[str] = None) -> None:
        """
        Aplica los estilos adaptados a ttk.Treeview según el modo de apariencia activo ('Dark' o 'Light').
        - Fuente de filas incrementada a 13pt (con rowheight=36) para máxima legibilidad.
        - Selección de fila en tono Turquesa Noche (#0f766e) con tipografía blanca (#ffffff)
          para evitar el encandilamiento y garantizar alto contraste.
        """
        if modo is None:
            modo = ctk.get_appearance_mode()
        es_oscuro = modo.lower() != "light"

        familia = cls.resolver_familia_fuente()
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except Exception:
            pass

        if es_oscuro:
            bg_tree = "#161E2E"
            fg_tree = "#F8FAFC"
            bg_head = "#0B0F19"
            fg_head = "#2DD4BF"  # Turquesa brillante
            bg_head_active = "#1E293B"
        else:
            bg_tree = "#FFFFFF"
            fg_tree = "#0F172A"
            bg_head = "#E6FFFA"  # Menta muy suave
            fg_head = "#0D9488"  # Turquesa oscuro
            bg_head_active = "#CCFBF1"

        # Alto contraste en selección: Turquesa Noche (#0f766e) + Texto Blanco (#ffffff)
        sel_bg = cls.TREEVIEW_SEL_BG
        sel_fg = cls.TREEVIEW_SEL_FG

        for nombre_estilo in ("Menu.Treeview", "Caja.Treeview"):
            estilo.configure(
                nombre_estilo,
                background=bg_tree,
                foreground=fg_tree,
                fieldbackground=bg_tree,
                rowheight=36,
                borderwidth=0,
                font=(familia, 13),
            )
            estilo.configure(
                f"{nombre_estilo}.Heading",
                background=bg_head,
                foreground=fg_head,
                font=(familia, 12, "bold"),
                relief="flat",
                padding=(10, 7),
            )
            estilo.map(
                nombre_estilo,
                background=[("selected", sel_bg)],
                foreground=[("selected", sel_fg)],
            )
            estilo.map(
                f"{nombre_estilo}.Heading",
                background=[("active", bg_head_active)],
            )
