"""
Vista de la pestaña 'Registro Rápido de Ventas / Caja Diaria' (Módulo 4).
Permite registrar pedidos de mostrador y delivery, y visualizar el arqueo diario
discriminado por medio de pago (Efectivo vs Transferencia/MP).
"""

from datetime import datetime
from tkinter import messagebox, ttk
from typing import Dict, List

import customtkinter as ctk

from models.producto import Producto
from models.venta import Venta
from services.excel_manager import ExcelManager


class TabCaja(ctk.CTkFrame):
    """
    Componente gráfico para el arqueo diario de caja y registro ágil de ventas.
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

        self._configurar_grilla()
        self._construir_tarjetas_resumen()
        self._construir_formulario_venta()
        self._construir_tabla_ventas()

        self.refrescar_catalogo_productos()
        self.refrescar_ventas_diarias()

    def _configurar_grilla(self) -> None:
        """Organiza la vista en fila superior (KPIs) y fila inferior (Formulario + Historial)."""
        self.grid_columnconfigure(0, weight=0, minsize=380)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)

    def _construir_tarjetas_resumen(self) -> None:
        """Construye las tarjetas superiores de resumen de recaudación diaria."""
        frame_kpis = ctk.CTkFrame(self, fg_color="transparent")
        frame_kpis.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(4, 10))
        for col in range(4):
            frame_kpis.grid_columnconfigure(col, weight=1)

        # KPI 1: Total General Recaudado
        card_total = ctk.CTkFrame(frame_kpis, corner_radius=12, border_width=2, border_color="#22C55E")
        card_total.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        ctk.CTkLabel(
            card_total,
            text="TOTAL RECAUDADO DEL DÍA",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=16, pady=(10, 2))
        self.lbl_kpi_total = ctk.CTkLabel(
            card_total,
            text="$ 0",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#4ADE80",
        )
        self.lbl_kpi_total.pack(anchor="w", padx=16, pady=(0, 10))

        # KPI 2: Total Efectivo
        card_efectivo = ctk.CTkFrame(frame_kpis, corner_radius=12, border_width=1, border_color="#38BDF8")
        card_efectivo.grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkLabel(
            card_efectivo,
            text="CAJA EN EFECTIVO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=16, pady=(10, 2))
        self.lbl_kpi_efectivo = ctk.CTkLabel(
            card_efectivo,
            text="$ 0",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#38BDF8",
        )
        self.lbl_kpi_efectivo.pack(anchor="w", padx=16, pady=(0, 10))

        # KPI 3: Total Transferencia / Mercado Pago
        card_transf = ctk.CTkFrame(frame_kpis, corner_radius=12, border_width=1, border_color="#A855F7")
        card_transf.grid(row=0, column=2, sticky="ew", padx=6)
        ctk.CTkLabel(
            card_transf,
            text="TRANSFERENCIA / MERCADO PAGO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=16, pady=(10, 2))
        self.lbl_kpi_transferencia = ctk.CTkLabel(
            card_transf,
            text="$ 0",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#C084FC",
        )
        self.lbl_kpi_transferencia.pack(anchor="w", padx=16, pady=(0, 10))

        # KPI 4: Volumen de Operaciones
        card_ops = ctk.CTkFrame(frame_kpis, corner_radius=12, border_width=1, border_color="#F59E0B")
        card_ops.grid(row=0, column=3, sticky="ew", padx=(6, 0))
        ctk.CTkLabel(
            card_ops,
            text="PEDIDOS REGISTRADOS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#94A3B8",
        ).pack(anchor="w", padx=16, pady=(10, 2))
        self.lbl_kpi_operaciones = ctk.CTkLabel(
            card_ops,
            text="0 ventas (0 Mostr. | 0 Deliv.)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FBBF24",
        )
        self.lbl_kpi_operaciones.pack(anchor="w", padx=16, pady=(4, 10))

    def _construir_formulario_venta(self) -> None:
        """Construye el panel izquierdo de carga rápida de ventas."""
        card_form = ctk.CTkFrame(self, corner_radius=12)
        card_form.grid(row=1, column=0, sticky="nsew", padx=(4, 10), pady=4)
        card_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_form,
            text="Registro Rápido de Venta",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 8))

        # Selector rápido de producto del menú para autocompletar
        box_asistente = ctk.CTkFrame(card_form, corner_radius=8, fg_color="#0F172A")
        box_asistente.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))
        box_asistente.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            box_asistente,
            text="Asistente Rápido: Sumar plato del menú al pedido",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38BDF8",
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=12, pady=(8, 4))

        self.combo_producto_rapido = ctk.CTkComboBox(
            box_asistente,
            values=["Sin productos"],
            height=32,
        )
        self.combo_producto_rapido.grid(row=1, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 6))

        fila_cant = ctk.CTkFrame(box_asistente, fg_color="transparent")
        fila_cant.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 10))
        fila_cant.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(fila_cant, text="Cant.:", font=ctk.CTkFont(size=12)).grid(
            row=0, column=0, padx=(0, 6)
        )

        self.combo_cantidad = ctk.CTkOptionMenu(
            fila_cant,
            values=["1", "2", "3", "4", "5", "6", "12"],
            width=75,
            height=30,
        )
        self.combo_cantidad.set("1")
        self.combo_cantidad.grid(row=0, column=1, sticky="w")

        btn_sumar_item = ctk.CTkButton(
            fila_cant,
            text="+ Sumar al Pedido",
            height=30,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=self._sumar_producto_al_detalle,
        )
        btn_sumar_item.grid(row=0, column=2, sticky="e")

        # Detalle del pedido
        ctk.CTkLabel(
            card_form,
            text="Detalle de la Venta / Ítems *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=2, column=0, sticky="w", padx=16, pady=(2, 2))

        self.entry_detalle = ctk.CTkEntry(
            card_form,
            placeholder_text="Ej: 1x Pizza Especial, 1x Doc. Empanadas",
            height=36,
        )
        self.entry_detalle.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Monto Total
        ctk.CTkLabel(
            card_form,
            text="Monto Total Cobrado ($) *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=4, column=0, sticky="w", padx=16, pady=(2, 2))

        self.entry_total = ctk.CTkEntry(
            card_form,
            placeholder_text="Ej: 25300",
            height=36,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self.entry_total.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Medio de Pago
        ctk.CTkLabel(
            card_form,
            text="Medio de Pago *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=6, column=0, sticky="w", padx=16, pady=(2, 4))

        self.seg_medio_pago = ctk.CTkSegmentedButton(
            card_form,
            values=list(Venta.MEDIOS_PAGO_VALIDOS),
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.seg_medio_pago.set("Efectivo")
        self.seg_medio_pago.grid(row=7, column=0, sticky="ew", padx=16, pady=(0, 10))

        # Tipo de Entrega
        ctk.CTkLabel(
            card_form,
            text="Modalidad de Entrega *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=8, column=0, sticky="w", padx=16, pady=(2, 4))

        self.seg_tipo_entrega = ctk.CTkSegmentedButton(
            card_form,
            values=list(Venta.TIPOS_ENTREGA_VALIDOS),
            height=36,
            font=ctk.CTkFont(size=12, weight="bold"),
        )
        self.seg_tipo_entrega.set("Mostrador")
        self.seg_tipo_entrega.grid(row=9, column=0, sticky="ew", padx=16, pady=(0, 14))

        # Botones de Acción
        self.btn_registrar = ctk.CTkButton(
            card_form,
            text="✔  REGISTRAR VENTA EN CAJA",
            height=42,
            fg_color="#16A34A",
            hover_color="#15803D",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._accion_registrar_venta,
        )
        self.btn_registrar.grid(row=10, column=0, sticky="ew", padx=16, pady=(0, 8))

        self.btn_limpiar = ctk.CTkButton(
            card_form,
            text="Limpiar Campos",
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self.limpiar_formulario,
        )
        self.btn_limpiar.grid(row=11, column=0, sticky="ew", padx=16, pady=(0, 14))

    def _construir_tabla_ventas(self) -> None:
        """Construye el panel derecho con el listado de operaciones de la fecha seleccionada."""
        card_historial = ctk.CTkFrame(self, corner_radius=12)
        card_historial.grid(row=1, column=1, sticky="nsew", padx=(0, 4), pady=4)
        card_historial.grid_columnconfigure(0, weight=1)
        card_historial.grid_rowconfigure(1, weight=1)

        # Barra superior con filtro de fecha
        barra_fecha = ctk.CTkFrame(card_historial, fg_color="transparent")
        barra_fecha.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 10))
        barra_fecha.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            barra_fecha,
            text="Movimientos de Caja Diaria",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            barra_fecha,
            text="Fecha (YYYY-MM-DD):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, padx=(10, 6))

        self.entry_fecha_filtro = ctk.CTkEntry(barra_fecha, width=120, height=32)
        self.entry_fecha_filtro.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.entry_fecha_filtro.grid(row=0, column=2, padx=(0, 6))

        btn_filtrar = ctk.CTkButton(
            barra_fecha,
            text="Consultar",
            width=90,
            height=32,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self.refrescar_ventas_diarias,
        )
        btn_filtrar.grid(row=0, column=3, padx=(0, 6))

        btn_hoy = ctk.CTkButton(
            barra_fecha,
            text="Hoy",
            width=65,
            height=32,
            fg_color="#334155",
            hover_color="#475569",
            command=self._ir_a_fecha_hoy,
        )
        btn_hoy.grid(row=0, column=4)

        # Tabla Treeview de Ventas
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
        self.tree_ventas.column("hora", width=150, anchor="center", stretch=False)
        self.tree_ventas.column("detalle", width=280, anchor="w")
        self.tree_ventas.column("medio_pago", width=135, anchor="center", stretch=False)
        self.tree_ventas.column("tipo_entrega", width=110, anchor="center", stretch=False)
        self.tree_ventas.column("total", width=125, anchor="e", stretch=False)

        scroll_v = ctk.CTkScrollbar(card_historial, orientation="vertical", command=self.tree_ventas.yview)
        self.tree_ventas.configure(yscrollcommand=scroll_v.set)

        self.tree_ventas.grid(row=1, column=0, sticky="nsew", padx=(16, 0), pady=(0, 14))
        scroll_v.grid(row=1, column=1, sticky="ns", padx=(4, 14), pady=(0, 14))

    # =========================================================================
    # LÓGICA DE CAJA Y EVENTOS
    # =========================================================================

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
        """Agrega el plato seleccionado y su subtotal al formulario de venta actual."""
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
        detalle_combinado = f"{detalle_actual}, {nuevo_fragmento}" if detalle_actual else nuevo_fragmento

        self.entry_detalle.delete(0, "end")
        self.entry_detalle.insert(0, detalle_combinado)

        # Sumar al monto total actual
        total_str = self.entry_total.get().strip().replace("$", "").replace(",", ".")
        try:
            monto_base = float(total_str) if total_str else 0.0
        except ValueError:
            monto_base = 0.0

        nuevo_total = monto_base + (prod.precio * cantidad)
        self.entry_total.delete(0, "end")
        self.entry_total.insert(0, f"{nuevo_total:g}")

    def limpiar_formulario(self) -> None:
        """Limpia los campos del formulario tras registrar una operación."""
        self.entry_detalle.delete(0, "end")
        self.entry_total.delete(0, "end")
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
        """Consulta las ventas de la fecha activa y actualiza la tabla y los KPIs."""
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

        self.lbl_kpi_total.configure(text=f"$ {resumen['total_general']:,.0f}")
        self.lbl_kpi_efectivo.configure(text=f"$ {resumen['total_efectivo']:,.0f}")
        self.lbl_kpi_transferencia.configure(text=f"$ {resumen['total_transferencia']:,.0f}")
        self.lbl_kpi_operaciones.configure(
            text=(
                f"{resumen['cantidad_ventas']} venta(s)  "
                f"({resumen['cant_mostrador']} Mostr. | {resumen['cant_delivery']} Deliv.)"
            )
        )

    def _accion_registrar_venta(self) -> None:
        """Valida los datos ingresados y persiste la venta en la hoja 'Ventas' de Excel."""
        detalle = self.entry_detalle.get().strip()
        total_str = self.entry_total.get().strip()
        medio_pago = self.seg_medio_pago.get()
        tipo_entrega = self.seg_tipo_entrega.get()

        try:
            nueva_venta = Venta(
                id=0,
                detalle=detalle,
                total=total_str,
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
                self.excel_manager.ultimo_error or "No se pudo guardar la venta en Excel.",
            )
            return

        self.limpiar_formulario()
        # Asegurar que se esté visualizando la fecha de la venta recién cargada
        self.entry_fecha_filtro.delete(0, "end")
        self.entry_fecha_filtro.insert(0, nueva_venta.fecha)
        self.refrescar_ventas_diarias()

        messagebox.showinfo(
            "Venta Registrada",
            f"Operación #{nueva_venta.id} registrada correctamente por {nueva_venta.total_formateado} "
            f"({nueva_venta.medio_pago} - {nueva_venta.tipo_entrega}).",
        )
