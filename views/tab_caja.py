"""
Vista de la pestaña 'Registro Rápido de Ventas / Caja Diaria' (Módulo 3).
Incluye:
- Panel izquierdo scrollable (CTkScrollableFrame) con ancho adecuado y márgenes compactos.
- Buscador predictivo en tiempo real con autocompletado por nombre o categoría,
  navegación con flechas (↑/↓) y confirmación inmediata con tecla 'Enter'.
- Cálculo automático de Monto Total Cobrado ($) bloqueado (disabled) contra errores manuales.
- Calculadora de vuelto en tiempo real ('Paga con $').
- Soporte completo para Pago Mixto: 'Mixto (Efectivo + Transferencia)' con validación de suma.
- Tabla de movimientos con selección en Turquesa Noche (#0f766e) y texto blanco (#ffffff)
  de alto contraste y tipografía ampliada.
- Cierre de Caja / Generar Arqueo con persistencia en Excel y exportación de reporte.
"""

from datetime import datetime
import os
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional
import unicodedata

import customtkinter as ctk

from models.producto import Producto
from models.venta import Venta
from services.excel_manager import ExcelManager
from views.theme_manager import ThemeManager


class TabCaja(ctk.CTkFrame):
    """
    Componente gráfico para el arqueo diario de caja, registro ágil de ventas
    con buscador predictivo (autocompletado), pago Mixto y cierre de caja.
    """

    MAX_SUGERENCIAS_VISIBLES: int = 4

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        excel_manager: ExcelManager,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.excel_manager: ExcelManager = excel_manager
        self.productos_menu: List[Producto] = []
        self.sugerencias_filtradas: List[Producto] = []
        self.indice_sugerencia_activa: int = 0
        self._botones_sugerencia: List[ctk.CTkButton] = []

        self.total_acumulado_form: float = 0.0
        self._ventana_arqueo: Optional[ctk.CTkToplevel] = None

        self._configurar_grilla()
        self._construir_tarjetas_resumen()
        self._construir_formulario_venta()
        self._construir_tabla_ventas()
        self._configurar_atajos_teclado()

        self.refrescar_catalogo_productos()
        self.refrescar_ventas_diarias()

    @staticmethod
    def _formatear_pesos(monto: float) -> str:
        """Formatea un valor numérico al estilo moneda local ($ X.XXX)."""
        return f"$ {monto:,.0f}".replace(",", ".")

    @staticmethod
    def _normalizar_texto_busqueda(texto: str) -> str:
        """Elimina tildes y pasa a minúsculas para búsquedas predictivas tolerantes."""
        texto_nfd = unicodedata.normalize("NFD", str(texto).lower().strip())
        return "".join(c for c in texto_nfd if unicodedata.category(c) != "Mn")

    def _configurar_grilla(self) -> None:
        """Organiza la vista en fila superior (KPIs) y fila inferior (Formulario + Historial)."""
        self.grid_columnconfigure(0, weight=0, minsize=415)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

    def _construir_tarjetas_resumen(self) -> None:
        """Construye las tarjetas superiores de resumen de recaudación diaria."""
        frame_kpis = ctk.CTkFrame(self, fg_color="transparent")
        frame_kpis.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 6))
        for col in range(4):
            frame_kpis.grid_columnconfigure(col, weight=1)

        # KPI 1: Total General Recaudado
        card_total = ctk.CTkFrame(
            frame_kpis,
            corner_radius=10,
            fg_color=ThemeManager.BG_CARD,
            border_width=2,
            border_color=ThemeManager.COLOR_ACCENT[1],
        )
        card_total.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ctk.CTkLabel(
            card_total,
            text="TOTAL RECAUDADO DEL DÍA",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_total = ctk.CTkLabel(
            card_total,
            text="$ 0",
            font=ThemeManager.font_kpi_value(grande=True),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_kpi_total.pack(anchor="w", padx=14, pady=(0, 8))

        # KPI 2: Total Efectivo
        card_efectivo = ctk.CTkFrame(
            frame_kpis,
            corner_radius=10,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_efectivo.grid(row=0, column=1, sticky="ew", padx=4)
        ctk.CTkLabel(
            card_efectivo,
            text="CAJA EN EFECTIVO",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_efectivo = ctk.CTkLabel(
            card_efectivo,
            text="$ 0",
            font=ThemeManager.font_kpi_value(grande=False),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_kpi_efectivo.pack(anchor="w", padx=14, pady=(0, 8))

        # KPI 3: Total Transferencia / Mercado Pago
        card_transf = ctk.CTkFrame(
            frame_kpis,
            corner_radius=10,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_transf.grid(row=0, column=2, sticky="ew", padx=4)
        ctk.CTkLabel(
            card_transf,
            text="TRANSFERENCIA / MP",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_transferencia = ctk.CTkLabel(
            card_transf,
            text="$ 0",
            font=ThemeManager.font_kpi_value(grande=False),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_kpi_transferencia.pack(anchor="w", padx=14, pady=(0, 8))

        # KPI 4: Volumen de Operaciones
        card_ops = ctk.CTkFrame(
            frame_kpis,
            corner_radius=10,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_ops.grid(row=0, column=3, sticky="ew", padx=(4, 0))
        ctk.CTkLabel(
            card_ops,
            text="PEDIDOS REGISTRADOS",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MUTED,
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_operaciones = ctk.CTkLabel(
            card_ops,
            text="0 ventas (0 Mostr. | 0 Deliv.)",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        )
        self.lbl_kpi_operaciones.pack(anchor="w", padx=14, pady=(2, 8))

    def _construir_formulario_venta(self) -> None:
        """
        Construye el panel izquierdo de carga rápida de ventas dentro de un
        CTkScrollableFrame incorporando el Buscador Predictivo en tiempo real.
        """
        self.card_form = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            width=400,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        self.card_form.grid(row=1, column=0, sticky="nsew", padx=(4, 8), pady=2)
        self.card_form.grid_columnconfigure(0, weight=1)

        # Cabecera del formulario con botón rápido de limpiar
        header_form = ctk.CTkFrame(self.card_form, fg_color="transparent")
        header_form.grid(row=0, column=0, sticky="ew", padx=8, pady=(4, 4))
        header_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_form,
            text="Registro Rápido de Venta",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w")

        self.btn_limpiar = ctk.CTkButton(
            header_form,
            text="Limpiar Carrito",
            width=110,
            height=28,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_small_bold(),
            command=self.limpiar_formulario,
        )
        self.btn_limpiar.grid(row=0, column=1, sticky="e")

        # --- BUSCADOR PREDICTIVO DE PLATOS CON AUTOCOMPLETADO EN TIEMPO REAL ---
        box_asistente = ctk.CTkFrame(
            self.card_form,
            corner_radius=8,
            fg_color=ThemeManager.BG_BOX_INTERNO,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        box_asistente.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        box_asistente.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box_asistente,
            text="🔍 Buscador Predictivo (Nombre o Categoría + Enter):",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 2))

        self.entry_buscar_plato = ctk.CTkEntry(
            box_asistente,
            placeholder_text="Escriba plato o categoría (ej. Pizza, Empanada)...",
            height=34,
            font=ThemeManager.font_input(),
        )
        self.entry_buscar_plato.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 4)
        )

        # Contenedor de sugerencias de autocompletado en tiempo real
        self.frame_sugerencias = ctk.CTkFrame(
            box_asistente,
            corner_radius=6,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        self.frame_sugerencias.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5)
        )
        self.frame_sugerencias.grid_columnconfigure(0, weight=1)

        self.lbl_sin_sugerencias = ctk.CTkLabel(
            self.frame_sugerencias,
            text="Sin coincidencias en el menú",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
        )

        self._botones_sugerencia.clear()
        for slot_idx in range(self.MAX_SUGERENCIAS_VISIBLES):
            btn_sug = ctk.CTkButton(
                self.frame_sugerencias,
                text="",
                height=26,
                corner_radius=5,
                anchor="w",
                font=ThemeManager.font_small_bold(),
                fg_color="transparent",
                hover_color=("#CCFBF1", "#1E293B"),
                text_color=ThemeManager.TEXT_MAIN,
            )
            self._botones_sugerencia.append(btn_sug)

        fila_cant = ctk.CTkFrame(box_asistente, fg_color="transparent")
        fila_cant.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
        fila_cant.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila_cant,
            text="Cant.:",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, padx=(0, 6))

        self.combo_cantidad = ctk.CTkOptionMenu(
            fila_cant,
            values=["1", "2", "3", "4", "5", "6", "12"],
            width=70,
            height=30,
            font=ThemeManager.font_body_bold(),
            fg_color=ThemeManager.COLOR_ACCENT,
            button_color=ThemeManager.COLOR_ACCENT_HOVER,
        )
        self.combo_cantidad.set("1")
        self.combo_cantidad.grid(row=0, column=1, sticky="w")

        self.btn_sumar_item = ctk.CTkButton(
            fila_cant,
            text="+ Sumar Plato (Enter)",
            height=30,
            fg_color=ThemeManager.BTN_PRIMARY,
            hover_color=ThemeManager.BTN_PRIMARY_HOVER,
            font=ThemeManager.font_small_bold(),
            command=self._sumar_producto_al_detalle,
        )
        self.btn_sumar_item.grid(row=0, column=2, sticky="e")

        # Detalle del pedido
        ctk.CTkLabel(
            self.card_form,
            text="Detalle de la Venta / Ítems *",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(0, 2))

        self.entry_detalle = ctk.CTkEntry(
            self.card_form,
            placeholder_text="Ej: 1x Pizza Especial, 1x Doc. Empanadas",
            height=34,
            font=ThemeManager.font_input(),
        )
        self.entry_detalle.grid(row=3, column=0, sticky="ew", padx=8, pady=(0, 6))

        # Fila Monto Total Cobrado ($) [Disabled] + Paga con ($) [Opcional]
        fila_montos = ctk.CTkFrame(self.card_form, fg_color="transparent")
        fila_montos.grid(row=4, column=0, sticky="ew", padx=8, pady=(0, 4))
        fila_montos.grid_columnconfigure(0, weight=1)
        fila_montos.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            fila_montos,
            text="Monto Total Cobrado ($) *",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 2))

        ctk.CTkLabel(
            fila_montos,
            text="Paga con ($) [Opcional]:",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        ).grid(row=0, column=1, sticky="w", padx=(4, 0), pady=(0, 2))

        self.entry_total = ctk.CTkEntry(
            fila_montos,
            height=34,
            font=ThemeManager.font_price_highlight(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.entry_total.insert(0, "0")
        self.entry_total.configure(state="disabled")
        self.entry_total.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.entry_paga_con = ctk.CTkEntry(
            fila_montos,
            placeholder_text="Ej: 20000",
            height=34,
            font=ThemeManager.font_input(bold=True),
        )
        self.entry_paga_con.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        self.entry_paga_con.bind("<KeyRelease>", lambda _e: self._calcular_vuelto())

        # Barra de Vuelto en tiempo real
        box_vuelto = ctk.CTkFrame(
            self.card_form,
            corner_radius=6,
            fg_color=ThemeManager.BG_BOX_INTERNO,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        box_vuelto.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 6))
        self.lbl_vuelto = ctk.CTkLabel(
            box_vuelto,
            text="Vuelto: $ 0",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_vuelto.pack(anchor="center", padx=10, pady=4)

        # Medio de Pago
        ctk.CTkLabel(
            self.card_form,
            text="Medio de Pago *",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=6, column=0, sticky="w", padx=8, pady=(0, 2))

        self.seg_medio_pago = ctk.CTkSegmentedButton(
            self.card_form,
            values=[
                Venta.MEDIO_EFECTIVO,
                Venta.MEDIO_TRANSFERENCIA,
                Venta.MEDIO_MIXTO,
            ],
            height=32,
            font=ThemeManager.font_small_bold(),
            selected_color=ThemeManager.COLOR_ACCENT[1],
            selected_hover_color=ThemeManager.COLOR_ACCENT_HOVER[1],
            command=self._al_cambiar_medio_pago,
        )
        self.seg_medio_pago.set(Venta.MEDIO_EFECTIVO)
        self.seg_medio_pago.grid(row=7, column=0, sticky="ew", padx=8, pady=(0, 6))

        # --- SECCIÓN DINÁMICA DE PAGO MIXTO ---
        self.frame_pago_mixto = ctk.CTkFrame(
            self.card_form,
            corner_radius=8,
            fg_color=ThemeManager.BG_BOX_INTERNO,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        self.frame_pago_mixto.grid_columnconfigure(0, weight=1)
        self.frame_pago_mixto.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self.frame_pago_mixto,
            text="Desglose Pago Mixto (Efectivo + Transferencia):",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 2))

        ctk.CTkLabel(
            self.frame_pago_mixto,
            text="Monto Efectivo ($) *",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=1, column=0, sticky="w", padx=(10, 4), pady=(0, 2))

        ctk.CTkLabel(
            self.frame_pago_mixto,
            text="Monto Transferencia ($) *",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=1, column=1, sticky="w", padx=(4, 10), pady=(0, 2))

        self.entry_mixto_efectivo = ctk.CTkEntry(
            self.frame_pago_mixto,
            placeholder_text="Ej: 5000",
            height=34,
            font=ThemeManager.font_input(bold=True),
        )
        self.entry_mixto_efectivo.grid(row=2, column=0, sticky="ew", padx=(10, 4), pady=(0, 4))
        self.entry_mixto_efectivo.bind("<KeyRelease>", lambda _e: self._al_editar_desglose_mixto())

        self.entry_mixto_transferencia = ctk.CTkEntry(
            self.frame_pago_mixto,
            placeholder_text="Ej: 5000",
            height=34,
            font=ThemeManager.font_input(bold=True),
        )
        self.entry_mixto_transferencia.grid(row=2, column=1, sticky="ew", padx=(4, 10), pady=(0, 4))
        self.entry_mixto_transferencia.bind("<KeyRelease>", lambda _e: self._al_editar_desglose_mixto())

        self.lbl_estado_mixto = ctk.CTkLabel(
            self.frame_pago_mixto,
            text="Suma: $ 0 / Total: $ 0",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
        )
        self.lbl_estado_mixto.grid(row=3, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))

        # Modalidad de Entrega
        ctk.CTkLabel(
            self.card_form,
            text="Modalidad de Entrega *",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=9, column=0, sticky="w", padx=8, pady=(0, 2))

        self.seg_tipo_entrega = ctk.CTkSegmentedButton(
            self.card_form,
            values=list(Venta.TIPOS_ENTREGA_VALIDOS),
            height=32,
            font=ThemeManager.font_small_bold(),
            selected_color=ThemeManager.COLOR_ACCENT[1],
            selected_hover_color=ThemeManager.COLOR_ACCENT_HOVER[1],
        )
        self.seg_tipo_entrega.set("Mostrador")
        self.seg_tipo_entrega.grid(row=10, column=0, sticky="ew", padx=8, pady=(0, 8))

        # 1. BOTÓN PRINCIPAL DE ACCIÓN INMEDIATAMENTE DEBAJO DE MODALIDAD DE ENTREGA
        self.btn_registrar = ctk.CTkButton(
            self.card_form,
            text="✔ REGISTRAR VENTA (Ctrl + Enter)",
            height=42,
            fg_color=ThemeManager.BTN_SUCCESS,
            hover_color=ThemeManager.BTN_SUCCESS_HOVER,
            text_color="#FFFFFF",
            font=ThemeManager.font_body_bold(),
            command=self._accion_registrar_venta,
        )
        self.btn_registrar.grid(row=11, column=0, sticky="ew", padx=8, pady=(0, 6))

        # Acceso directo a Cierre de Caja
        self.btn_arqueo_izq = ctk.CTkButton(
            self.card_form,
            text="🔒 Cerrar Caja / Generar Arqueo",
            height=34,
            fg_color=ThemeManager.BTN_WARNING,
            hover_color=ThemeManager.BTN_WARNING_HOVER,
            text_color="#FFFFFF",
            font=ThemeManager.font_small_bold(),
            command=self._accion_cerrar_caja_arqueo,
        )
        self.btn_arqueo_izq.grid(row=12, column=0, sticky="ew", padx=8, pady=(0, 6))

    def _construir_tabla_ventas(self) -> None:
        """
        Construye el panel derecho con el listado de operaciones de la fecha seleccionada.
        Configura el estilo de selección en Turquesa Noche (#0f766e) con tipografía blanca (#ffffff).
        """
        card_historial = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_historial.grid(row=1, column=1, sticky="nsew", padx=(0, 4), pady=2)
        card_historial.grid_columnconfigure(0, weight=1)
        card_historial.grid_rowconfigure(1, weight=1)

        # Barra superior con título, filtro de fecha y botón de Arqueo
        barra_fecha = ctk.CTkFrame(card_historial, fg_color="transparent")
        barra_fecha.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(10, 8))
        barra_fecha.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            barra_fecha,
            text="Movimientos de Caja Diaria",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            barra_fecha,
            text="Fecha:",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=1, padx=(8, 4))

        self.entry_fecha_filtro = ctk.CTkEntry(
            barra_fecha, width=115, height=32, font=ThemeManager.font_input()
        )
        self.entry_fecha_filtro.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha_filtro.grid(row=0, column=2, padx=(0, 4))

        btn_filtrar = ctk.CTkButton(
            barra_fecha,
            text="Consultar",
            width=85,
            height=32,
            fg_color=ThemeManager.BTN_PRIMARY,
            hover_color=ThemeManager.BTN_PRIMARY_HOVER,
            font=ThemeManager.font_small_bold(),
            command=self.refrescar_ventas_diarias,
        )
        btn_filtrar.grid(row=0, column=3, padx=(0, 4))

        btn_hoy = ctk.CTkButton(
            barra_fecha,
            text="Hoy",
            width=55,
            height=32,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_small_bold(),
            command=self._ir_a_fecha_hoy,
        )
        btn_hoy.grid(row=0, column=4, padx=(0, 8))

        self.btn_cerrar_caja = ctk.CTkButton(
            barra_fecha,
            text="🔒 Cerrar Caja / Arqueo",
            height=32,
            fg_color=ThemeManager.BTN_WARNING,
            hover_color=ThemeManager.BTN_WARNING_HOVER,
            text_color="#FFFFFF",
            font=ThemeManager.font_small_bold(),
            command=self._accion_cerrar_caja_arqueo,
        )
        self.btn_cerrar_caja.grid(row=0, column=5)

        # Aplicar estilo centralizado de Treeview con selección en Turquesa Noche (#0f766e) y texto blanco
        ThemeManager.aplicar_estilo_treeview()
        estilo_caja = ttk.Style()
        estilo_caja.map(
            "Caja.Treeview",
            background=[("selected", "#0F766E")],
            foreground=[("selected", "#FFFFFF")],
        )

        columnas = ("id", "hora", "detalle", "medio_pago", "tipo_entrega", "total")
        self.tree_ventas = ttk.Treeview(
            card_historial,
            columns=columnas,
            show="headings",
            style="Caja.Treeview",
            selectmode="browse",
        )

        self.tree_ventas.heading("id", text="N° Op.")
        self.tree_ventas.heading("hora", text="Fecha y Hora")
        self.tree_ventas.heading("detalle", text="Detalle del Pedido")
        self.tree_ventas.heading("medio_pago", text="Medio de Pago / Desglose")
        self.tree_ventas.heading("tipo_entrega", text="Entrega")
        self.tree_ventas.heading("total", text="Total Cobrado")

        self.tree_ventas.column("id", width=60, anchor="center", stretch=False)
        self.tree_ventas.column("hora", width=150, anchor="center", stretch=False)
        self.tree_ventas.column("detalle", width=260, anchor="w")
        self.tree_ventas.column("medio_pago", width=190, anchor="w")
        self.tree_ventas.column("tipo_entrega", width=100, anchor="center", stretch=False)
        self.tree_ventas.column("total", width=120, anchor="e", stretch=False)

        scroll_v = ctk.CTkScrollbar(
            card_historial, orientation="vertical", command=self.tree_ventas.yview
        )
        self.tree_ventas.configure(yscrollcommand=scroll_v.set)

        self.tree_ventas.grid(row=1, column=0, sticky="nsew", padx=(14, 0), pady=(0, 10))
        scroll_v.grid(row=1, column=1, sticky="ns", padx=(4, 12), pady=(0, 10))

    def _configurar_atajos_teclado(self) -> None:
        """
        Vincula eventos de teclado para el buscador predictivo (KeyRelease, Up, Down, Return)
        y Ctrl+Enter / F5 para registrar la venta rápidamente.
        """
        self.entry_buscar_plato.bind("<KeyRelease>", self._al_escribir_busqueda_predictiva)
        self.entry_buscar_plato.bind("<Down>", self._al_presionar_flecha_abajo)
        self.entry_buscar_plato.bind("<Up>", self._al_presionar_flecha_arriba)
        self.entry_buscar_plato.bind("<Return>", self._atajo_sumar_plato)
        self.entry_buscar_plato.bind("<Control-Return>", self._atajo_registrar_venta)
        self.entry_buscar_plato.bind("<F5>", self._atajo_registrar_venta)

        for widget in (
            self.entry_detalle,
            self.entry_paga_con,
            self.entry_mixto_efectivo,
            self.entry_mixto_transferencia,
        ):
            widget.bind("<Return>", self._atajo_sumar_plato)
            widget.bind("<Control-Return>", self._atajo_registrar_venta)
            widget.bind("<F5>", self._atajo_registrar_venta)

        toplevel = self.winfo_toplevel()
        toplevel.bind("<Control-Return>", self._atajo_registrar_venta_global, add="+")
        toplevel.bind("<F5>", self._atajo_registrar_venta_global, add="+")

    # =========================================================================
    # LÓGICA DEL BUSCADOR PREDICTIVO Y AUTOCOMPLETADO EN TIEMPO REAL
    # =========================================================================

    def _al_escribir_busqueda_predictiva(self, event: Optional[ Any ] = None) -> None:
        """
        Filtra en tiempo real el catálogo de platos a medida que el usuario escribe
        (por coincidencia en nombre o categoría) y actualiza la lista de sugerencias.
        """
        if event is not None and getattr(event, "keysym", "") in (
            "Up",
            "Down",
            "Return",
            "KP_Enter",
            "Control_L",
            "Control_R",
            "Alt_L",
            "Alt_R",
            "Shift_L",
            "Shift_R",
            "Escape",
        ):
            return

        consulta = self._normalizar_texto_busqueda(self.entry_buscar_plato.get())
        if not consulta:
            self.sugerencias_filtradas = list(self.productos_menu)
        else:
            coincidencias: List[Producto] = []
            for prod in self.productos_menu:
                nombre_norm = self._normalizar_texto_busqueda(prod.nombre)
                cat_norm = self._normalizar_texto_busqueda(prod.categoria)
                if consulta in nombre_norm or consulta in cat_norm:
                    coincidencias.append(prod)
            self.sugerencias_filtradas = coincidencias

        self.indice_sugerencia_activa = 0 if self.sugerencias_filtradas else -1
        self._renderizar_sugerencias_predictivas()

    def _al_presionar_flecha_abajo(self, _event: Optional[object] = None) -> str:
        """Desplaza la selección activa hacia abajo en la lista de sugerencias."""
        if self.sugerencias_filtradas:
            self.indice_sugerencia_activa = (
                self.indice_sugerencia_activa + 1
            ) % len(self.sugerencias_filtradas)
            self._renderizar_sugerencias_predictivas()
        return "break"

    def _al_presionar_flecha_arriba(self, _event: Optional[object] = None) -> str:
        """Desplaza la selección activa hacia arriba en la lista de sugerencias."""
        if self.sugerencias_filtradas:
            self.indice_sugerencia_activa = (
                self.indice_sugerencia_activa - 1
            ) % len(self.sugerencias_filtradas)
            self._renderizar_sugerencias_predictivas()
        return "break"

    def _seleccionar_sugerencia_con_clic(self, indice_global: int) -> None:
        """
        Selecciona una sugerencia al hacer clic sobre ella, autocompleta el campo
        de búsqueda y mantiene el foco listo para confirmar con 'Enter'.
        """
        if 0 <= indice_global < len(self.sugerencias_filtradas):
            self.indice_sugerencia_activa = indice_global
            prod = self.sugerencias_filtradas[indice_global]
            self.entry_buscar_plato.delete(0, "end")
            self.entry_buscar_plato.insert(0, prod.nombre)
            self._renderizar_sugerencias_predictivas()
            self.entry_buscar_plato.focus_set()

    def _renderizar_sugerencias_predictivas(self) -> None:
        """
        Actualiza sin parpadeos las filas de sugerencias visibles debajo del buscador.
        La sugerencia activa se destaca en Turquesa Noche (#0f766e) con texto blanco.
        """
        total_sug = len(self.sugerencias_filtradas)
        if total_sug == 0:
            for btn in self._botones_sugerencia:
                btn.grid_remove()
            self.lbl_sin_sugerencias.grid(row=0, column=0, padx=8, pady=4, sticky="w")
            return

        self.lbl_sin_sugerencias.grid_remove()

        # Ventana deslizante alrededor del índice activo si hay más de MAX_SUGERENCIAS_VISIBLES
        if self.indice_sugerencia_activa < self.MAX_SUGERENCIAS_VISIBLES:
            inicio = 0
        else:
            inicio = min(
                self.indice_sugerencia_activa - self.MAX_SUGERENCIAS_VISIBLES + 1,
                max(0, total_sug - self.MAX_SUGERENCIAS_VISIBLES),
            )
        fin = min(total_sug, inicio + self.MAX_SUGERENCIAS_VISIBLES)
        visibles = self.sugerencias_filtradas[inicio:fin]

        for slot_idx, btn in enumerate(self._botones_sugerencia):
            if slot_idx < len(visibles):
                idx_global = inicio + slot_idx
                prod = visibles[slot_idx]
                es_activa = idx_global == self.indice_sugerencia_activa
                prefijo = "▸ " if es_activa else "   "
                etiqueta = f"{prefijo}[{prod.categoria}] {prod.nombre} ({prod.precio_formateado})"

                btn.configure(
                    text=etiqueta,
                    fg_color=ThemeManager.TREEVIEW_SEL_BG if es_activa else "transparent",
                    hover_color="#115E59" if es_activa else ("#CCFBF1", "#1E293B"),
                    text_color=ThemeManager.TREEVIEW_SEL_FG
                    if es_activa
                    else ThemeManager.TEXT_MAIN,
                    command=lambda i=idx_global: self._seleccionar_sugerencia_con_clic(i),
                )
                btn.grid(row=slot_idx, column=0, sticky="ew", padx=4, pady=1)
            else:
                btn.grid_remove()

    def obtener_plato_sugerido_actual(self) -> Optional[Producto]:
        """Retorna el plato actualmente resaltado en el buscador predictivo."""
        if not self.sugerencias_filtradas:
            return None
        if 0 <= self.indice_sugerencia_activa < len(self.sugerencias_filtradas):
            return self.sugerencias_filtradas[self.indice_sugerencia_activa]
        return self.sugerencias_filtradas[0]

    def _atajo_sumar_plato(self, _event: Optional[object] = None) -> str:
        """Manejador de teclado para confirmar la sugerencia y sumarla al pedido con Enter."""
        self._sumar_producto_al_detalle()
        return "break"

    def _atajo_registrar_venta(self, _event: Optional[object] = None) -> str:
        """Manejador directo de teclado para cobrar la venta con Ctrl+Enter o F5."""
        if self.winfo_ismapped():
            self._accion_registrar_venta()
        return "break"

    def _atajo_registrar_venta_global(self, _event: Optional[object] = None) -> None:
        """Ejecuta el cobro rápido si la pestaña de Caja se encuentra visible en pantalla."""
        if self.winfo_ismapped():
            self._accion_registrar_venta()

    # =========================================================================
    # LÓGICA DE MEDIOS DE PAGO Y PAGO MIXTO
    # =========================================================================

    def _al_cambiar_medio_pago(self, valor_seleccionado: str) -> None:
        """
        Habilita y muestra dinámicamente los campos de 'Monto Efectivo ($)' y
        'Monto Transferencia ($)' cuando se selecciona 'Mixto (Efectivo + Transferencia)'.
        """
        if valor_seleccionado == Venta.MEDIO_MIXTO:
            self.frame_pago_mixto.grid(row=8, column=0, sticky="ew", padx=8, pady=(0, 6))
            efec_txt = self.entry_mixto_efectivo.get().strip()
            transf_txt = self.entry_mixto_transferencia.get().strip()
            if not efec_txt and not transf_txt and self.total_acumulado_form > 0:
                mitad = round(self.total_acumulado_form / 2.0, 2)
                self.entry_mixto_efectivo.insert(0, f"{mitad:g}")
                self.entry_mixto_transferencia.insert(
                    0, f"{self.total_acumulado_form - mitad:g}"
                )
            self._al_editar_desglose_mixto()
        else:
            self.frame_pago_mixto.grid_remove()

        self._calcular_vuelto()

    def _al_editar_desglose_mixto(self) -> None:
        """
        Valida dinámicamente en tiempo real si la suma de efectivo + transferencia
        coincide con el total cobrado, actualizando la etiqueta de estado.
        """
        efec_txt = (
            self.entry_mixto_efectivo.get()
            .strip()
            .replace("$", "")
            .replace(" ", "")
            .replace(",", ".")
        )
        transf_txt = (
            self.entry_mixto_transferencia.get()
            .strip()
            .replace("$", "")
            .replace(" ", "")
            .replace(",", ".")
        )

        try:
            efec = float(efec_txt) if efec_txt else 0.0
        except ValueError:
            efec = -1.0

        try:
            transf = float(transf_txt) if transf_txt else 0.0
        except ValueError:
            transf = -1.0

        if efec < 0 or transf < 0:
            self.lbl_estado_mixto.configure(
                text="⚠ Montos numéricos inválidos",
                text_color=ThemeManager.BTN_DANGER[1],
            )
            return

        suma = round(efec + transf, 2)
        diferencia = round(self.total_acumulado_form - suma, 2)

        if abs(diferencia) < 0.01:
            self.lbl_estado_mixto.configure(
                text=f"✔ Suma: {self._formatear_pesos(suma)} / Total: {self._formatear_pesos(self.total_acumulado_form)} (Coincide)",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
        elif diferencia > 0:
            self.lbl_estado_mixto.configure(
                text=f"⚠ Suma: {self._formatear_pesos(suma)} (Faltan {self._formatear_pesos(diferencia)} para el total)",
                text_color=ThemeManager.BTN_WARNING[1],
            )
        else:
            self.lbl_estado_mixto.configure(
                text=f"⚠ Suma: {self._formatear_pesos(suma)} (Excede el total por {self._formatear_pesos(abs(diferencia))})",
                text_color=ThemeManager.BTN_DANGER[1],
            )

        self._calcular_vuelto()

    # =========================================================================
    # LÓGICA DE CAJA, CÁLCULO AUTOMÁTICO DE TOTAL Y VUELTO
    # =========================================================================

    def _actualizar_entry_total(self, nuevo_monto: float) -> None:
        """
        Actualiza el monto total acumulado en el campo deshabilitado ('disabled')
        para impedir errores de tipeo manual por parte del cajero.
        """
        self.total_acumulado_form = round(max(0.0, nuevo_monto), 2)
        self.entry_total.configure(state="normal")
        self.entry_total.delete(0, "end")
        self.entry_total.insert(0, f"{self.total_acumulado_form:g}")
        self.entry_total.configure(state="disabled")

        if self.seg_medio_pago.get() == Venta.MEDIO_MIXTO:
            self._al_editar_desglose_mixto()
        self._calcular_vuelto()

    def _calcular_vuelto(self) -> None:
        """
        Calcula y muestra en tiempo real el vuelto a entregar al cliente.
        Si el pago es Mixto, calcula el vuelto en base a la porción de efectivo.
        """
        texto_paga = (
            self.entry_paga_con.get().strip().replace("$", "").replace(" ", "")
            if hasattr(self, "entry_paga_con")
            else ""
        )
        if not texto_paga:
            self.lbl_vuelto.configure(
                text=f"Vuelto: {self._formatear_pesos(0)}",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
            return

        limpio = (
            texto_paga.replace(".", "").replace(",", ".")
            if "," in texto_paga
            else texto_paga.replace(",", "")
        )
        try:
            monto_pagado = float(limpio)
        except ValueError:
            self.lbl_vuelto.configure(
                text="Vuelto: Monto inválido",
                text_color=ThemeManager.BTN_DANGER[1],
            )
            return

        monto_a_cubrir = self.total_acumulado_form
        if self.seg_medio_pago.get() == Venta.MEDIO_MIXTO:
            try:
                efec_txt = self.entry_mixto_efectivo.get().strip().replace(",", ".")
                monto_a_cubrir = float(efec_txt) if efec_txt else self.total_acumulado_form
            except ValueError:
                pass

        diferencia = monto_pagado - monto_a_cubrir
        if diferencia >= 0:
            self.lbl_vuelto.configure(
                text=f"Vuelto: {self._formatear_pesos(diferencia)}",
                text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
            )
        else:
            self.lbl_vuelto.configure(
                text=f"Faltan: {self._formatear_pesos(abs(diferencia))}",
                text_color=ThemeManager.BTN_DANGER[1],
            )

    def refrescar_catalogo_productos(self) -> None:
        """Actualiza el catálogo del buscador predictivo con el menú vigente en Excel."""
        self.productos_menu = self.excel_manager.obtener_productos()
        self._al_escribir_busqueda_predictiva()

    def _sumar_producto_al_detalle(self) -> None:
        """
        Toma la sugerencia activa del buscador predictivo, la suma al detalle del pedido,
        actualiza automáticamente el Monto Total Cobrado ($) y limpia el buscador para
        la siguiente carga.
        """
        prod = self.obtener_plato_sugerido_actual()
        if not prod:
            return

        try:
            cantidad = int(self.combo_cantidad.get())
        except ValueError:
            cantidad = 1

        nuevo_fragmento = f"{cantidad}x {prod.nombre}"
        detalle_actual = self.entry_detalle.get().strip()
        detalle_combinado = (
            f"{detalle_actual}, {nuevo_fragmento}" if detalle_actual else nuevo_fragmento
        )

        self.entry_detalle.delete(0, "end")
        self.entry_detalle.insert(0, detalle_combinado)

        nuevo_total = self.total_acumulado_form + (prod.precio * cantidad)
        self._actualizar_entry_total(nuevo_total)

        # Limpiar el buscador predictivo y restaurar sugerencias para el próximo ítem
        self.entry_buscar_plato.delete(0, "end")
        self._al_escribir_busqueda_predictiva()

    def limpiar_formulario(self) -> None:
        """Limpia el carrito del pedido, resetea el total, vuelto y pago mixto tras una operación."""
        self.entry_buscar_plato.delete(0, "end")
        self.entry_detalle.delete(0, "end")
        self.entry_paga_con.delete(0, "end")
        self.entry_mixto_efectivo.delete(0, "end")
        self.entry_mixto_transferencia.delete(0, "end")
        self.frame_pago_mixto.grid_remove()
        self._actualizar_entry_total(0.0)
        self.combo_cantidad.set("1")
        self.seg_medio_pago.set(Venta.MEDIO_EFECTIVO)
        self.seg_tipo_entrega.set("Mostrador")
        self._al_escribir_busqueda_predictiva()

    def _ir_a_fecha_hoy(self) -> None:
        """Restablece el filtro de fecha al día actual y recarga la tabla."""
        hoy = datetime.now().strftime("%Y-%m-%d")
        self.entry_fecha_filtro.delete(0, "end")
        self.entry_fecha_filtro.insert(0, hoy)
        self.refrescar_ventas_diarias()

    def refrescar_ventas_diarias(self) -> None:
        """Consulta las ventas de la fecha activa y actualiza la tabla y los KPIs en tiempo real."""
        fecha = self.entry_fecha_filtro.get().strip() or datetime.now().strftime("%Y-%m-%d")
        ventas = self.excel_manager.obtener_ventas_diarias(fecha)
        resumen = self.excel_manager.calcular_resumen_diario(fecha)

        for item in self.tree_ventas.get_children():
            self.tree_ventas.delete(item)

        for v in ventas:
            self.tree_ventas.insert(
                "",
                "end",
                values=(
                    f"#{v.id}",
                    v.fecha_hora,
                    v.detalle_texto,
                    v.medio_pago_resumen,
                    v.tipo_entrega,
                    v.total_formateado,
                ),
            )

        self.lbl_kpi_total.configure(text=self._formatear_pesos(resumen["total_general"]))
        self.lbl_kpi_efectivo.configure(text=self._formatear_pesos(resumen["total_efectivo"]))
        self.lbl_kpi_transferencia.configure(
            text=self._formatear_pesos(resumen["total_transferencia"])
        )
        self.lbl_kpi_operaciones.configure(
            text=(
                f"{resumen['cantidad_ventas']} venta(s)  "
                f"({resumen['cant_mostrador']} Mostr. | {resumen['cant_delivery']} Deliv.)"
            )
        )

    def _accion_registrar_venta(self) -> None:
        """
        Valida los ítems, total y medio de pago (incluyendo el desglose exacto
        en caso de Pago Mixto), registra la venta en Excel y refresca las métricas.
        """
        detalle = self.entry_detalle.get().strip()
        monto_total = self.total_acumulado_form
        medio_pago = self.seg_medio_pago.get()
        tipo_entrega = self.seg_tipo_entrega.get()

        if not detalle or monto_total <= 0:
            messagebox.showwarning(
                "Pedido Incompleto",
                "Debe sumar al menos un plato del menú (total > $ 0) antes de registrar la venta.",
            )
            return

        monto_efectivo: Optional[float] = None
        monto_transferencia: Optional[float] = None

        if medio_pago == Venta.MEDIO_MIXTO:
            efec_str = (
                self.entry_mixto_efectivo.get()
                .strip()
                .replace("$", "")
                .replace(" ", "")
                .replace(",", ".")
            )
            transf_str = (
                self.entry_mixto_transferencia.get()
                .strip()
                .replace("$", "")
                .replace(" ", "")
                .replace(",", ".")
            )

            if not efec_str or not transf_str:
                messagebox.showwarning(
                    "Desglose Mixto Incompleto",
                    "Para cobrar con Pago Mixto debe ingresar tanto el 'Monto Efectivo ($)' "
                    "como el 'Monto Transferencia ($)'.",
                )
                return

            try:
                monto_efectivo = float(efec_str)
                monto_transferencia = float(transf_str)
            except ValueError:
                messagebox.showwarning(
                    "Valores Numéricos Inválidos",
                    "Los importes de efectivo y transferencia deben ser valores numéricos válidos.",
                )
                return

            suma = round(monto_efectivo + monto_transferencia, 2)
            if abs(suma - monto_total) > 0.01:
                messagebox.showwarning(
                    "Suma No Coincide",
                    f"La suma de Efectivo ({self._formatear_pesos(monto_efectivo)}) + "
                    f"Transferencia ({self._formatear_pesos(monto_transferencia)}) = "
                    f"{self._formatear_pesos(suma)} debe coincidir exactamente con el "
                    f"Total Cobrado ({self._formatear_pesos(monto_total)}).",
                )
                return

        try:
            nueva_venta = Venta(
                id=0,
                detalle=detalle,
                total=monto_total,
                medio_pago=medio_pago,
                tipo_entrega=tipo_entrega,
                monto_efectivo=monto_efectivo,
                monto_transferencia=monto_transferencia,
            )
        except (ValueError, TypeError) as err:
            messagebox.showwarning("Datos de Venta Inválidos", str(err))
            return

        exito = self.excel_manager.registrar_venta(nueva_venta)
        if not exito:
            messagebox.showerror(
                "Error al Registrar Venta",
                self.excel_manager.ultimo_error or ExcelManager.MENSAJE_ARCHIVO_ABIERTO,
            )
            return

        self.limpiar_formulario()
        self.entry_fecha_filtro.delete(0, "end")
        self.entry_fecha_filtro.insert(0, nueva_venta.fecha)
        self.refrescar_ventas_diarias()

        detalle_cobro = (
            f"Pago Mixto (Ef: {self._formatear_pesos(nueva_venta.monto_efectivo)} | "
            f"Tr: {self._formatear_pesos(nueva_venta.monto_transferencia)})"
            if nueva_venta.medio_pago == Venta.MEDIO_MIXTO
            else nueva_venta.medio_pago
        )

        messagebox.showinfo(
            "Venta Registrada",
            f"Operación #{nueva_venta.id} registrada correctamente por {nueva_venta.total_formateado} "
            f"({detalle_cobro} - {nueva_venta.tipo_entrega}).",
        )

    # =========================================================================
    # MÓDULO DE CIERRE DE CAJA Y GENERACIÓN DE ARQUEO DIARIO
    # =========================================================================

    def _accion_cerrar_caja_arqueo(self) -> None:
        """
        Despliega el cuadro de diálogo modal de Cierre de Caja / Arqueo Diario
        con el desglose de Efectivo, Transferencias/MP, Total Recaudado y Pedidos,
        permitiendo guardar el arqueo en la planilla Excel y exportar un reporte.
        """
        fecha = self.entry_fecha_filtro.get().strip() or datetime.now().strftime("%Y-%m-%d")
        resumen = self.excel_manager.calcular_resumen_diario(fecha)

        if self._ventana_arqueo is not None and self._ventana_arqueo.winfo_exists():
            self._ventana_arqueo.focus()
            return

        modal = ctk.CTkToplevel(self)
        modal.title(f"Cierre de Caja / Arqueo Diario — {fecha}")
        modal.geometry("500x440")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        self._ventana_arqueo = modal

        modal.grid_columnconfigure(0, weight=1)

        # Encabezado del modal
        header_modal = ctk.CTkFrame(modal, corner_radius=0, fg_color=ThemeManager.BG_HEADER[1])
        header_modal.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header_modal,
            text=f"🔒  CIERRE DE CAJA / ARQUEO DIARIO ({fecha})",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        ).pack(padx=20, pady=14)

        # Tarjeta de resumen de arqueo
        card_resumen = ctk.CTkFrame(
            modal,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_resumen.grid(row=1, column=0, sticky="ew", padx=20, pady=(14, 10))
        card_resumen.grid_columnconfigure(0, weight=1)

        lineas_resumen = [
            (
                f"Total Efectivo en Caja: {self._formatear_pesos(resumen['total_efectivo'])}",
                ThemeManager.COLOR_NUMEROS_DESTACADOS,
                15,
            ),
            (
                f"Total Transferencias / MP: {self._formatear_pesos(resumen['total_transferencia'])}",
                ThemeManager.COLOR_ACCENT,
                15,
            ),
            (
                f"Total Recaudado: {self._formatear_pesos(resumen['total_general'])}",
                ThemeManager.COLOR_NUMEROS_DESTACADOS,
                18,
            ),
            (
                f"Cantidad de Pedidos: {resumen['cantidad_ventas']} "
                f"(Mostrador: {resumen['cant_mostrador']} | Delivery: {resumen['cant_delivery']})",
                ThemeManager.TEXT_MAIN,
                13,
            ),
        ]

        if resumen.get("cant_mixto", 0) > 0:
            lineas_resumen.append(
                (
                    f"Operaciones con Pago Mixto: {resumen['cant_mixto']}",
                    ThemeManager.TEXT_MUTED,
                    12,
                )
            )

        for idx, (texto, color, tamano) in enumerate(lineas_resumen):
            ctk.CTkLabel(
                card_resumen,
                text=texto,
                font=ThemeManager.get_font(tamano, weight="bold"),
                text_color=color,
                anchor="w",
            ).grid(
                row=idx,
                column=0,
                sticky="w",
                padx=18,
                pady=(10 if idx == 0 else 4, 10 if idx == len(lineas_resumen) - 1 else 3),
            )

        ctk.CTkLabel(
            modal,
            text="¿Desea confirmar el cierre, registrar el arqueo en Excel\ny generar el reporte del día?",
            font=ThemeManager.font_body(),
            text_color=ThemeManager.TEXT_MUTED,
            justify="center",
        ).grid(row=2, column=0, padx=20, pady=(0, 10))

        frame_acciones = ctk.CTkFrame(modal, fg_color="transparent")
        frame_acciones.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
        frame_acciones.grid_columnconfigure(0, weight=1)
        frame_acciones.grid_columnconfigure(1, weight=1)

        btn_exportar = ctk.CTkButton(
            frame_acciones,
            text="💾 Guardar Arqueo y Exportar",
            height=38,
            fg_color=ThemeManager.BTN_SUCCESS,
            hover_color=ThemeManager.BTN_SUCCESS_HOVER,
            text_color="#FFFFFF",
            font=ThemeManager.font_body_bold(),
            command=lambda: self._confirmar_y_exportar_arqueo(fecha, resumen, modal),
        )
        btn_exportar.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        btn_cancelar = ctk.CTkButton(
            frame_acciones,
            text="Cerrar",
            height=38,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_body_bold(),
            command=modal.destroy,
        )
        btn_cancelar.grid(row=0, column=1, sticky="ew", padx=(6, 0))

    def _confirmar_y_exportar_arqueo(
        self,
        fecha: str,
        resumen: Dict[str, Any],
        modal: ctk.CTkToplevel,
    ) -> None:
        """
        Persiste el arqueo diario en la planilla Excel ('datos_rotiseria.xlsx')
        y genera un reporte de cierre en la carpeta 'output/'.
        """
        guardado_excel = True
        if hasattr(self.excel_manager, "registrar_cierre_caja"):
            guardado_excel = self.excel_manager.registrar_cierre_caja(fecha)

        if not guardado_excel:
            messagebox.showerror(
                "Error al Guardar Arqueo",
                self.excel_manager.ultimo_error or ExcelManager.MENSAJE_ARCHIVO_ABIERTO,
                parent=modal,
            )
            return

        base_dir = os.path.dirname(os.path.dirname(self.excel_manager.filepath))
        output_dir = os.path.join(base_dir, "output")
        os.makedirs(output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ruta_reporte = os.path.join(output_dir, f"arqueo_caja_{fecha}_{timestamp}.txt")

        contenido_reporte = (
            "============================================================\n"
            "       REPORTE DE CIERRE DE CAJA / ARQUEO DIARIO\n"
            "============================================================\n"
            f"Fecha Operativa : {fecha}\n"
            f"Hora de Cierre  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            "------------------------------------------------------------\n"
            f"Total Efectivo en Caja     : {self._formatear_pesos(resumen['total_efectivo'])}\n"
            f"Total Transferencias / MP  : {self._formatear_pesos(resumen['total_transferencia'])}\n"
            f"Total Recaudado            : {self._formatear_pesos(resumen['total_general'])}\n"
            f"Cantidad de Pedidos        : {resumen['cantidad_ventas']} "
            f"(Mostrador: {resumen['cant_mostrador']} | Delivery: {resumen['cant_delivery']})\n"
            f"Operaciones Pago Mixto     : {resumen.get('cant_mixto', 0)}\n"
            "============================================================\n"
        )

        try:
            with open(ruta_reporte, "w", encoding="utf-8") as archivo_rep:
                archivo_rep.write(contenido_reporte)
        except OSError:
            ruta_reporte = self.excel_manager.filepath

        modal.destroy()
        messagebox.showinfo(
            "Arqueo de Caja Registrado",
            f"El Cierre de Caja del día {fecha} se guardó exitosamente.\n\n"
            f"• Total Efectivo en Caja: {self._formatear_pesos(resumen['total_efectivo'])}\n"
            f"• Total Transferencias / MP: {self._formatear_pesos(resumen['total_transferencia'])}\n"
            f"• Total Recaudado: {self._formatear_pesos(resumen['total_general'])}\n"
            f"• Cantidad de Pedidos: {resumen['cantidad_ventas']} "
            f"(Mostrador: {resumen['cant_mostrador']} | Delivery: {resumen['cant_delivery']})\n"
            f"• Pagos Mixtos: {resumen.get('cant_mixto', 0)}\n\n"
            f"Reporte exportado en:\n{ruta_reporte}",
        )
