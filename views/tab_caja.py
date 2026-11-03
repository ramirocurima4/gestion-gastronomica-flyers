"""
Vista de la pestaña 'Registro Rápido de Ventas / Caja Diaria' (Módulo 3 / 4).
Incluye:
- Panel izquierdo scrollable (CTkScrollableFrame) con márgenes compactos para garantizar
  la visibilidad completa en cualquier resolución de pantalla.
- Cálculo automático de Monto Total Cobrado ($) bloqueado (disabled) contra errores manuales.
- Calculadora de vuelto en tiempo real ('Paga con $').
- Botón principal verde (#28a745) '✔ REGISTRAR VENTA (Ctrl + Enter)' debajo de Modalidad de Entrega.
- Módulo y diálogo de '🔒 Cerrar Caja / Generar Arqueo' con persistencia en Excel y exportación de reporte.
"""

from datetime import datetime
import os
from tkinter import messagebox, ttk
from typing import Any, Dict, List, Optional

import customtkinter as ctk

from models.producto import Producto
from models.venta import Venta
from services.excel_manager import ExcelManager


class TabCaja(ctk.CTkFrame):
    """
    Componente gráfico para el arqueo diario de caja, registro ágil de ventas
    y cierre de caja con generación de reporte.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        excel_manager: ExcelManager,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.excel_manager: ExcelManager = excel_manager
        self.productos_menu: List[Producto] = []
        self.mapa_productos_combo: Dict[str, Producto] = {}
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

    def _configurar_grilla(self) -> None:
        """Organiza la vista en fila superior (KPIs) y fila inferior (Formulario + Historial)."""
        self.grid_columnconfigure(0, weight=0, minsize=405)
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
            frame_kpis, corner_radius=10, border_width=2, border_color="#22C55E"
        )
        card_total.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        ctk.CTkLabel(
            card_total,
            text="TOTAL RECAUDADO DEL DÍA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_total = ctk.CTkLabel(
            card_total,
            text="$ 0",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#4ADE80",
        )
        self.lbl_kpi_total.pack(anchor="w", padx=14, pady=(0, 8))

        # KPI 2: Total Efectivo
        card_efectivo = ctk.CTkFrame(
            frame_kpis, corner_radius=10, border_width=1, border_color="#38BDF8"
        )
        card_efectivo.grid(row=0, column=1, sticky="ew", padx=5)
        ctk.CTkLabel(
            card_efectivo,
            text="CAJA EN EFECTIVO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_efectivo = ctk.CTkLabel(
            card_efectivo,
            text="$ 0",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38BDF8",
        )
        self.lbl_kpi_efectivo.pack(anchor="w", padx=14, pady=(0, 8))

        # KPI 3: Total Transferencia / Mercado Pago
        card_transf = ctk.CTkFrame(
            frame_kpis, corner_radius=10, border_width=1, border_color="#A855F7"
        )
        card_transf.grid(row=0, column=2, sticky="ew", padx=5)
        ctk.CTkLabel(
            card_transf,
            text="TRANSFERENCIA / MERCADO PAGO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_transferencia = ctk.CTkLabel(
            card_transf,
            text="$ 0",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#C084FC",
        )
        self.lbl_kpi_transferencia.pack(anchor="w", padx=14, pady=(0, 8))

        # KPI 4: Volumen de Operaciones
        card_ops = ctk.CTkFrame(
            frame_kpis, corner_radius=10, border_width=1, border_color="#F59E0B"
        )
        card_ops.grid(row=0, column=3, sticky="ew", padx=(5, 0))
        ctk.CTkLabel(
            card_ops,
            text="PEDIDOS REGISTRADOS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=14, pady=(8, 0))
        self.lbl_kpi_operaciones = ctk.CTkLabel(
            card_ops,
            text="0 ventas (0 Mostr. | 0 Deliv.)",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#FBBF24",
        )
        self.lbl_kpi_operaciones.pack(anchor="w", padx=14, pady=(2, 8))

    def _construir_formulario_venta(self) -> None:
        """
        Construye el panel izquierdo de carga rápida de ventas dentro de un
        CTkScrollableFrame con espaciado compacto para que el botón verde
        '✔ REGISTRAR VENTA (Ctrl + Enter)' sea siempre visible en pantalla.
        """
        self.card_form = ctk.CTkScrollableFrame(
            self,
            corner_radius=12,
            width=385,
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
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.btn_limpiar = ctk.CTkButton(
            header_form,
            text="Limpiar Carrito",
            width=105,
            height=26,
            fg_color="#475569",
            hover_color="#334155",
            font=ctk.CTkFont(size=11),
            command=self.limpiar_formulario,
        )
        self.btn_limpiar.grid(row=0, column=1, sticky="e")

        # Asistente rápido de producto del menú
        box_asistente = ctk.CTkFrame(self.card_form, corner_radius=8, fg_color="#0F172A")
        box_asistente.grid(row=1, column=0, sticky="ew", padx=8, pady=(0, 6))
        box_asistente.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box_asistente,
            text="Asistente Rápido: Sumar plato del menú (Enter)",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38BDF8",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(6, 2))

        self.combo_producto_rapido = ctk.CTkComboBox(
            box_asistente,
            values=["Sin productos"],
            height=30,
        )
        self.combo_producto_rapido.grid(
            row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 5)
        )

        fila_cant = ctk.CTkFrame(box_asistente, fg_color="transparent")
        fila_cant.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 6))
        fila_cant.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fila_cant, text="Cant.:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=(0, 6)
        )

        self.combo_cantidad = ctk.CTkOptionMenu(
            fila_cant,
            values=["1", "2", "3", "4", "5", "6", "12"],
            width=70,
            height=28,
        )
        self.combo_cantidad.set("1")
        self.combo_cantidad.grid(row=0, column=1, sticky="w")

        self.btn_sumar_item = ctk.CTkButton(
            fila_cant,
            text="+ Sumar al Pedido",
            height=28,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._sumar_producto_al_detalle,
        )
        self.btn_sumar_item.grid(row=0, column=2, sticky="e")

        # Detalle del pedido
        ctk.CTkLabel(
            self.card_form,
            text="Detalle de la Venta / Ítems *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=8, pady=(0, 2))

        self.entry_detalle = ctk.CTkEntry(
            self.card_form,
            placeholder_text="Ej: 1x Pizza Especial, 1x Doc. Empanadas",
            height=32,
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
            font=ctk.CTkFont(size=11, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 2))

        ctk.CTkLabel(
            fila_montos,
            text="Paga con ($) [Opcional]:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38BDF8",
        ).grid(row=0, column=1, sticky="w", padx=(4, 0), pady=(0, 2))

        self.entry_total = ctk.CTkEntry(
            fila_montos,
            height=32,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4ADE80",
        )
        self.entry_total.insert(0, "0")
        self.entry_total.configure(state="disabled")
        self.entry_total.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.entry_paga_con = ctk.CTkEntry(
            fila_montos,
            placeholder_text="Ej: 20000",
            height=32,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.entry_paga_con.grid(row=1, column=1, sticky="ew", padx=(4, 0))
        self.entry_paga_con.bind("<KeyRelease>", lambda _e: self._calcular_vuelto())

        # Barra de Vuelto en tiempo real
        box_vuelto = ctk.CTkFrame(self.card_form, corner_radius=6, fg_color="#0F172A")
        box_vuelto.grid(row=5, column=0, sticky="ew", padx=8, pady=(0, 6))
        self.lbl_vuelto = ctk.CTkLabel(
            box_vuelto,
            text="Vuelto: $ 0",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#FBBF24",
        )
        self.lbl_vuelto.pack(anchor="center", padx=10, pady=4)

        # Medio de Pago
        ctk.CTkLabel(
            self.card_form,
            text="Medio de Pago *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=6, column=0, sticky="w", padx=8, pady=(0, 2))

        self.seg_medio_pago = ctk.CTkSegmentedButton(
            self.card_form,
            values=list(Venta.MEDIOS_PAGO_VALIDOS),
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda _val: self._calcular_vuelto(),
        )
        self.seg_medio_pago.set("Efectivo")
        self.seg_medio_pago.grid(row=7, column=0, sticky="ew", padx=8, pady=(0, 6))

        # Modalidad de Entrega
        ctk.CTkLabel(
            self.card_form,
            text="Modalidad de Entrega *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=8, column=0, sticky="w", padx=8, pady=(0, 2))

        self.seg_tipo_entrega = ctk.CTkSegmentedButton(
            self.card_form,
            values=list(Venta.TIPOS_ENTREGA_VALIDOS),
            height=30,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.seg_tipo_entrega.set("Mostrador")
        self.seg_tipo_entrega.grid(row=9, column=0, sticky="ew", padx=8, pady=(0, 10))

        # 1. BOTÓN PRINCIPAL DE ACCIÓN INMEDIATAMENTE DEBAJO DE MODALIDAD DE ENTREGA
        self.btn_registrar = ctk.CTkButton(
            self.card_form,
            text="✔ REGISTRAR VENTA (Ctrl + Enter)",
            height=44,
            fg_color="#28a745",
            hover_color="#218838",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._accion_registrar_venta,
        )
        self.btn_registrar.grid(row=10, column=0, sticky="ew", padx=8, pady=(0, 6))

        # Acceso directo adicional a Cierre de Caja también desde el panel izquierdo
        self.btn_arqueo_izq = ctk.CTkButton(
            self.card_form,
            text="🔒 Cerrar Caja / Generar Arqueo",
            height=34,
            fg_color="#D97706",
            hover_color="#B45309",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._accion_cerrar_caja_arqueo,
        )
        self.btn_arqueo_izq.grid(row=11, column=0, sticky="ew", padx=8, pady=(0, 6))

    def _construir_tabla_ventas(self) -> None:
        """
        Construye el panel derecho con el listado de operaciones de la fecha seleccionada
        y el botón destacado '🔒 Cerrar Caja / Generar Arqueo' junto al filtro de fechas.
        """
        card_historial = ctk.CTkFrame(self, corner_radius=12)
        card_historial.grid(row=1, column=1, sticky="nsew", padx=(0, 4), pady=2)
        card_historial.grid_columnconfigure(0, weight=1)
        card_historial.grid_rowconfigure(1, weight=1)

        # Barra superior con título, filtro de fecha y botón de Cierre de Caja / Arqueo
        barra_fecha = ctk.CTkFrame(card_historial, fg_color="transparent")
        barra_fecha.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(12, 8))
        barra_fecha.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            barra_fecha,
            text="Movimientos de Caja Diaria",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            barra_fecha,
            text="Fecha:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, padx=(8, 4))

        self.entry_fecha_filtro = ctk.CTkEntry(barra_fecha, width=105, height=30)
        self.entry_fecha_filtro.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha_filtro.grid(row=0, column=2, padx=(0, 4))

        btn_filtrar = ctk.CTkButton(
            barra_fecha,
            text="Consultar",
            width=80,
            height=30,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.refrescar_ventas_diarias,
        )
        btn_filtrar.grid(row=0, column=3, padx=(0, 4))

        btn_hoy = ctk.CTkButton(
            barra_fecha,
            text="Hoy",
            width=55,
            height=30,
            fg_color="#334155",
            hover_color="#475569",
            command=self._ir_a_fecha_hoy,
        )
        btn_hoy.grid(row=0, column=4, padx=(0, 8))

        # 2. BOTÓN SECUNDARIO DESTACADO: CERRAR CAJA / GENERAR ARQUEO
        self.btn_cerrar_caja = ctk.CTkButton(
            barra_fecha,
            text="🔒 Cerrar Caja / Generar Arqueo",
            height=32,
            fg_color="#D97706",
            hover_color="#B45309",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._accion_cerrar_caja_arqueo,
        )
        self.btn_cerrar_caja.grid(row=0, column=5)

        columnas = ("id", "hora", "detalle", "medio_pago", "tipo_entrega", "total")
        self.tree_ventas = ttk.Treeview(
            card_historial,
            columns=columnas,
            show="headings",
            style="Menu.Treeview",
            selectmode="browse",
        )

        self.tree_ventas.heading("id", text="N° Op.")
        self.tree_ventas.heading("hora", text="Fecha y Hora")
        self.tree_ventas.heading("detalle", text="Detalle del Pedido")
        self.tree_ventas.heading("medio_pago", text="Medio de Pago")
        self.tree_ventas.heading("tipo_entrega", text="Entrega")
        self.tree_ventas.heading("total", text="Total Cobrado")

        self.tree_ventas.column("id", width=65, anchor="center", stretch=False)
        self.tree_ventas.column("hora", width=145, anchor="center", stretch=False)
        self.tree_ventas.column("detalle", width=260, anchor="w")
        self.tree_ventas.column("medio_pago", width=130, anchor="center", stretch=False)
        self.tree_ventas.column("tipo_entrega", width=105, anchor="center", stretch=False)
        self.tree_ventas.column("total", width=120, anchor="e", stretch=False)

        scroll_v = ctk.CTkScrollbar(
            card_historial, orientation="vertical", command=self.tree_ventas.yview
        )
        self.tree_ventas.configure(yscrollcommand=scroll_v.set)

        self.tree_ventas.grid(row=1, column=0, sticky="nsew", padx=(14, 0), pady=(0, 12))
        scroll_v.grid(row=1, column=1, sticky="ns", padx=(4, 12), pady=(0, 12))

    def _configurar_atajos_teclado(self) -> None:
        """
        Vincula la tecla Enter para sumar platos al pedido y Ctrl+Enter / F5
        para confirmar y registrar la venta cuando la pestaña de Caja está activa.
        """
        for widget in (self.combo_producto_rapido, self.entry_detalle, self.entry_paga_con):
            widget.bind("<Return>", self._atajo_sumar_plato)
            widget.bind("<Control-Return>", self._atajo_registrar_venta)
            widget.bind("<F5>", self._atajo_registrar_venta)

        toplevel = self.winfo_toplevel()
        toplevel.bind("<Control-Return>", self._atajo_registrar_venta_global, add="+")
        toplevel.bind("<F5>", self._atajo_registrar_venta_global, add="+")

    def _atajo_sumar_plato(self, _event: Optional[object] = None) -> str:
        """Manejador de teclado para sumar el plato seleccionado con Enter."""
        if self.winfo_ismapped():
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
        self._calcular_vuelto()

    def _calcular_vuelto(self) -> None:
        """
        Calcula y muestra en tiempo real el vuelto a entregar al cliente
        en base al campo opcional 'Paga con ($)' y al monto total acumulado.
        """
        texto_paga = (
            self.entry_paga_con.get().strip().replace("$", "").replace(" ", "")
            if hasattr(self, "entry_paga_con")
            else ""
        )
        if not texto_paga:
            self.lbl_vuelto.configure(
                text=f"Vuelto: {self._formatear_pesos(0)}",
                text_color="#FBBF24",
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
                text_color="#F87171",
            )
            return

        diferencia = monto_pagado - self.total_acumulado_form
        if diferencia >= 0:
            self.lbl_vuelto.configure(
                text=f"Vuelto: {self._formatear_pesos(diferencia)}",
                text_color="#4ADE80",
            )
        else:
            self.lbl_vuelto.configure(
                text=f"Faltan: {self._formatear_pesos(abs(diferencia))}",
                text_color="#F87171",
            )

    def refrescar_catalogo_productos(self) -> None:
        """Actualiza el selector rápido de platos con el menú vigente en Excel."""
        self.productos_menu = self.excel_manager.obtener_productos()
        self.mapa_productos_combo.clear()

        if not self.productos_menu:
            self.combo_producto_rapido.configure(values=["Sin productos en el menú"])
            self.combo_producto_rapido.set("Sin productos en el menú")
            return

        etiquetas: List[str] = []
        for prod in self.productos_menu:
            etiqueta = f"{prod.nombre} ({prod.precio_formateado})"
            self.mapa_productos_combo[etiqueta] = prod
            etiquetas.append(etiqueta)

        self.combo_producto_rapido.configure(values=etiquetas)
        self.combo_producto_rapido.set(etiquetas[0])

    def _sumar_producto_al_detalle(self) -> None:
        """
        Agrega el plato seleccionado al detalle del pedido y actualiza
        automáticamente el campo deshabilitado de Monto Total Cobrado ($).
        """
        seleccion = self.combo_producto_rapido.get()
        prod = self.mapa_productos_combo.get(seleccion)
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

    def limpiar_formulario(self) -> None:
        """Limpia el carrito del pedido, resetea el total y el vuelto tras una operación."""
        self.entry_detalle.delete(0, "end")
        self.entry_paga_con.delete(0, "end")
        self._actualizar_entry_total(0.0)
        self.combo_cantidad.set("1")
        self.seg_medio_pago.set("Efectivo")
        self.seg_tipo_entrega.set("Mostrador")

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
                    v.medio_pago,
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
        Valida que exista al menos un ítem y un total > 0, registra la venta en Excel,
        limpia el carrito, resetea el vuelto y actualiza las tarjetas de recaudación.
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

        try:
            nueva_venta = Venta(
                id=0,
                detalle=detalle,
                total=monto_total,
                medio_pago=medio_pago,
                tipo_entrega=tipo_entrega,
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

        messagebox.showinfo(
            "Venta Registrada",
            f"Operación #{nueva_venta.id} registrada correctamente por {nueva_venta.total_formateado} "
            f"({nueva_venta.medio_pago} - {nueva_venta.tipo_entrega}).",
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
        modal.geometry("480x420")
        modal.resizable(False, False)
        modal.transient(self.winfo_toplevel())
        modal.grab_set()
        self._ventana_arqueo = modal

        modal.grid_columnconfigure(0, weight=1)

        # Encabezado del modal
        header_modal = ctk.CTkFrame(modal, corner_radius=0, fg_color="#0F172A")
        header_modal.grid(row=0, column=0, sticky="ew")
        ctk.CTkLabel(
            header_modal,
            text=f"🔒  CIERRE DE CAJA / ARQUEO DIARIO ({fecha})",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FBBF24",
        ).pack(padx=20, pady=14)

        # Tarjeta de resumen de arqueo
        card_resumen = ctk.CTkFrame(
            modal, corner_radius=12, fg_color="#1E293B", border_width=1, border_color="#334155"
        )
        card_resumen.grid(row=1, column=0, sticky="ew", padx=20, pady=(16, 12))
        card_resumen.grid_columnconfigure(0, weight=1)

        lineas_resumen = [
            (
                f"Total Efectivo en Caja: {self._formatear_pesos(resumen['total_efectivo'])}",
                "#38BDF8",
                15,
            ),
            (
                f"Total Transferencias / MP: {self._formatear_pesos(resumen['total_transferencia'])}",
                "#C084FC",
                15,
            ),
            (
                f"Total Recaudado: {self._formatear_pesos(resumen['total_general'])}",
                "#4ADE80",
                18,
            ),
            (
                f"Cantidad de Pedidos: {resumen['cantidad_ventas']} "
                f"(Mostrador: {resumen['cant_mostrador']} | Delivery: {resumen['cant_delivery']})",
                "#F8FAFC",
                14,
            ),
        ]

        for idx, (texto, color, tamano) in enumerate(lineas_resumen):
            ctk.CTkLabel(
                card_resumen,
                text=texto,
                font=ctk.CTkFont(size=tamano, weight="bold"),
                text_color=color,
                anchor="w",
            ).grid(row=idx, column=0, sticky="w", padx=18, pady=(12 if idx == 0 else 6, 12 if idx == 3 else 4))

        ctk.CTkLabel(
            modal,
            text="¿Desea confirmar el cierre, registrar el arqueo en Excel\ny generar el reporte del día?",
            font=ctk.CTkFont(size=12),
            text_color="#CBD5E1",
            justify="center",
        ).grid(row=2, column=0, padx=20, pady=(0, 12))

        frame_acciones = ctk.CTkFrame(modal, fg_color="transparent")
        frame_acciones.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
        frame_acciones.grid_columnconfigure(0, weight=1)
        frame_acciones.grid_columnconfigure(1, weight=1)

        btn_exportar = ctk.CTkButton(
            frame_acciones,
            text="💾 Guardar Arqueo y Exportar",
            height=40,
            fg_color="#28a745",
            hover_color="#218838",
            text_color="#FFFFFF",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._confirmar_y_exportar_arqueo(fecha, resumen, modal),
        )
        btn_exportar.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        btn_cancelar = ctk.CTkButton(
            frame_acciones,
            text="Cerrar",
            height=40,
            fg_color="#475569",
            hover_color="#334155",
            font=ctk.CTkFont(size=13),
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

        # Generar reporte visual simple en output/
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
            f"(Mostrador: {resumen['cant_mostrador']} | Delivery: {resumen['cant_delivery']})\n\n"
            f"Reporte exportado en:\n{ruta_reporte}",
        )
