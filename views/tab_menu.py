"""
Vista de la pestaña 'Gestión de Menú y Precios' (Módulo 1).
Permite alta, edición, baja de productos en tabla interactiva y aumento porcentual masivo por categoría.
"""

from tkinter import messagebox, ttk
from typing import Callable, List, Optional

import customtkinter as ctk

from models.producto import Producto
from services.excel_manager import ExcelManager


class TabMenu(ctk.CTkFrame):
    """
    Componente gráfico para administrar el catálogo gastronómico y ejecutar
    actualizaciones masivas de precios por porcentaje.
    """

    def __init__(
        self,
        master: ctk.CTkBaseClass,
        excel_manager: ExcelManager,
        on_menu_change: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(master, fg_color="transparent")
        self.excel_manager: ExcelManager = excel_manager
        self.on_menu_change: Optional[Callable[[], None]] = on_menu_change
        self.producto_seleccionado_id: Optional[int] = None
        self.productos_cache: List[Producto] = []

        self._configurar_grilla()
        self._construir_panel_izquierdo()
        self._construir_panel_derecho()
        self.refrescar_datos()

    def _configurar_grilla(self) -> None:
        """Configura el diseño responsivo de 2 columnas (Formulario / Tabla)."""
        self.grid_columnconfigure(0, weight=0, minsize=370)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _construir_panel_izquierdo(self) -> None:
        """Construye la columna izquierda con el formulario CRUD y el panel de aumento masivo."""
        contenedor_izq = ctk.CTkFrame(self, fg_color="transparent")
        contenedor_izq.grid(row=0, column=0, sticky="nsew", padx=(4, 10), pady=4)
        contenedor_izq.grid_columnconfigure(0, weight=1)

        # --- Tarjeta 1: Formulario Alta / Edición de Producto ---
        card_form = ctk.CTkFrame(contenedor_izq, corner_radius=12)
        card_form.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        card_form.grid_columnconfigure(0, weight=1)

        header_form = ctk.CTkFrame(card_form, fg_color="transparent")
        header_form.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 6))
        header_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_form,
            text="Plato / Producto del Menú",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.lbl_modo_edicion = ctk.CTkLabel(
            header_form,
            text="MODO: NUEVO",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#38BDF8",
        )
        self.lbl_modo_edicion.grid(row=0, column=1, sticky="e")

        # Nombre
        ctk.CTkLabel(
            card_form,
            text="Nombre del Plato o Combo *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(4, 2))

        self.entry_nombre = ctk.CTkEntry(
            card_form,
            placeholder_text="Ej: Pizza Napolitana Especial",
            height=34,
        )
        self.entry_nombre.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 8))

        # Fila Categoría y Precio
        fila_cat_precio = ctk.CTkFrame(card_form, fg_color="transparent")
        fila_cat_precio.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        fila_cat_precio.grid_columnconfigure(0, weight=3)
        fila_cat_precio.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(
            fila_cat_precio,
            text="Categoría *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 2))

        ctk.CTkLabel(
            fila_cat_precio,
            text="Precio ($) *",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 2))

        self.combo_categoria = ctk.CTkComboBox(
            fila_cat_precio,
            values=Producto.CATEGORIAS_SUGERIDAS,
            height=34,
        )
        self.combo_categoria.set("Pizzas")
        self.combo_categoria.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        self.entry_precio = ctk.CTkEntry(
            fila_cat_precio,
            placeholder_text="Ej: 12500",
            height=34,
        )
        self.entry_precio.grid(row=1, column=1, sticky="ew", padx=(6, 0))

        # Descripción
        ctk.CTkLabel(
            card_form,
            text="Descripción / Ingredientes (para el Flyer)",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=4, column=0, sticky="w", padx=16, pady=(2, 2))

        self.txt_descripcion = ctk.CTkTextbox(card_form, height=68, corner_radius=8)
        self.txt_descripcion.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 12))

        # Botones CRUD
        frame_botones = ctk.CTkFrame(card_form, fg_color="transparent")
        frame_botones.grid(row=6, column=0, sticky="ew", padx=16, pady=(0, 14))
        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)

        self.btn_guardar = ctk.CTkButton(
            frame_botones,
            text="Guardar Producto",
            height=38,
            fg_color="#16A34A",
            hover_color="#15803D",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._accion_guardar_o_actualizar,
        )
        self.btn_guardar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 8))

        self.btn_limpiar = ctk.CTkButton(
            frame_botones,
            text="Limpiar / Nuevo",
            height=34,
            fg_color="#475569",
            hover_color="#334155",
            command=self.limpiar_formulario,
        )
        self.btn_limpiar.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.btn_eliminar = ctk.CTkButton(
            frame_botones,
            text="Eliminar Plato",
            height=34,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            state="disabled",
            command=self._accion_eliminar,
        )
        self.btn_eliminar.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # --- Tarjeta 2: Actualización Masiva de Precios por Porcentaje ---
        card_masivo = ctk.CTkFrame(contenedor_izq, corner_radius=12)
        card_masivo.grid(row=1, column=0, sticky="ew")
        card_masivo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_masivo,
            text="Actualización Masiva de Precios (%)",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#FBBF24",
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 2))

        ctk.CTkLabel(
            card_masivo,
            text="Aplique un ajuste porcentual por inflación a una categoría o a todo el menú.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            wraplength=330,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 8))

        fila_masivo = ctk.CTkFrame(card_masivo, fg_color="transparent")
        fila_masivo.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 10))
        fila_masivo.grid_columnconfigure(0, weight=3)
        fila_masivo.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(
            fila_masivo,
            text="Categoría objetivo:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 6), pady=(0, 2))

        ctk.CTkLabel(
            fila_masivo,
            text="Porcentaje (%):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=0, column=1, sticky="w", padx=(6, 0), pady=(0, 2))

        self.combo_cat_masiva = ctk.CTkComboBox(
            fila_masivo,
            values=["Todas las categorías"] + Producto.CATEGORIAS_SUGERIDAS,
            height=34,
        )
        self.combo_cat_masiva.set("Todas las categorías")
        self.combo_cat_masiva.grid(row=1, column=0, sticky="ew", padx=(0, 6))

        self.entry_porcentaje = ctk.CTkEntry(
            fila_masivo,
            placeholder_text="Ej: 15",
            height=34,
        )
        self.entry_porcentaje.grid(row=1, column=1, sticky="ew", padx=(6, 0))

        self.btn_aplicar_aumento = ctk.CTkButton(
            card_masivo,
            text="Aplicar Ajuste Porcentual",
            height=36,
            fg_color="#D97706",
            hover_color="#B45309",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._accion_aumento_masivo,
        )
        self.btn_aplicar_aumento.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))

    def _construir_panel_derecho(self) -> None:
        """Construye la tabla interactiva de productos con buscador en tiempo real."""
        card_tabla = ctk.CTkFrame(self, corner_radius=12)
        card_tabla.grid(row=0, column=1, sticky="nsew", padx=(0, 4), pady=4)
        card_tabla.grid_columnconfigure(0, weight=1)
        card_tabla.grid_rowconfigure(1, weight=1)

        # Barra superior de búsqueda y estadísticas
        barra_sup = ctk.CTkFrame(card_tabla, fg_color="transparent")
        barra_sup.grid(row=0, column=0, columnspan=2, sticky="ew", padx=16, pady=(14, 10))
        barra_sup.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            barra_sup,
            text="Catálogo Actual de Platos",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).grid(row=0, column=0, sticky="w", padx=(0, 14))

        self.entry_buscar = ctk.CTkEntry(
            barra_sup,
            placeholder_text="🔍 Filtrar por nombre o categoría...",
            height=34,
        )
        self.entry_buscar.grid(row=0, column=1, sticky="ew", padx=(0, 10))
        self.entry_buscar.bind("<KeyRelease>", lambda _e: self._poblar_treeview())

        self.lbl_contador = ctk.CTkLabel(
            barra_sup,
            text="0 productos",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94A3B8",
        )
        self.lbl_contador.grid(row=0, column=2, padx=(0, 10))

        btn_recargar = ctk.CTkButton(
            barra_sup,
            text="↻ Recargar",
            width=100,
            height=34,
            fg_color="#334155",
            hover_color="#475569",
            command=self.refrescar_datos,
        )
        btn_recargar.grid(row=0, column=3)

        # Configuración visual del Treeview adaptado a modo oscuro/moderno
        estilo = ttk.Style()
        estilo.theme_use("clam")
        estilo.configure(
            "Menu.Treeview",
            background="#1E293B",
            foreground="#F8FAFC",
            fieldbackground="#1E293B",
            rowheight=32,
            borderwidth=0,
            font=("Calibri", 11),
        )
        estilo.configure(
            "Menu.Treeview.Heading",
            background="#0F172A",
            foreground="#FBBF24",
            font=("Calibri", 11, "bold"),
            relief="flat",
            padding=(8, 6),
        )
        estilo.map(
            "Menu.Treeview",
            background=[("selected", "#2563EB")],
            foreground=[("selected", "#FFFFFF")],
        )
        estilo.map(
            "Menu.Treeview.Heading",
            background=[("active", "#1E293B")],
        )

        columnas = ("id", "nombre", "categoria", "precio", "descripcion")
        self.tree = ttk.Treeview(
            card_tabla,
            columns=columnas,
            show="headings",
            style="Menu.Treeview",
            selectmode="browse",
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("nombre", text="Nombre del Plato / Combo")
        self.tree.heading("categoria", text="Categoría")
        self.tree.heading("precio", text="Precio Unitario")
        self.tree.heading("descripcion", text="Descripción / Ingredientes")

        self.tree.column("id", width=55, minwidth=45, anchor="center", stretch=False)
        self.tree.column("nombre", width=220, minwidth=160, anchor="w")
        self.tree.column("categoria", width=150, minwidth=110, anchor="w")
        self.tree.column("precio", width=120, minwidth=100, anchor="e", stretch=False)
        self.tree.column("descripcion", width=280, minwidth=160, anchor="w")

        scrollbar = ctk.CTkScrollbar(card_tabla, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=1, column=0, sticky="nsew", padx=(16, 0), pady=(0, 12))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(4, 14), pady=(0, 12))

        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

        ctk.CTkLabel(
            card_tabla,
            text="💡 Haga clic sobre cualquier fila de la tabla para cargar el plato en el formulario de edición.",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

    # =========================================================================
    # LÓGICA DE INTERACCIÓN Y EVENTOS
    # =========================================================================

    def refrescar_datos(self) -> None:
        """Recarga la lista de productos desde Excel y actualiza combos y tabla."""
        self.productos_cache = self.excel_manager.obtener_productos()
        self._actualizar_opciones_categorias()
        self._poblar_treeview()

    def _actualizar_opciones_categorias(self) -> None:
        """Combina las categorías sugeridas con las personalizadas existentes en el Excel."""
        existentes = {p.categoria for p in self.productos_cache if p.categoria}
        todas = list(Producto.CATEGORIAS_SUGERIDAS)
        for cat in sorted(existentes):
            if cat not in todas:
                todas.append(cat)

        self.combo_categoria.configure(values=todas)

        opciones_masivas = ["Todas las categorías"] + sorted(existentes) if existentes else ["Todas las categorías"] + todas
        seleccion_previa = self.combo_cat_masiva.get()
        self.combo_cat_masiva.configure(values=opciones_masivas)
        if seleccion_previa not in opciones_masivas:
            self.combo_cat_masiva.set("Todas las categorías")

    def _poblar_treeview(self) -> None:
        """Vuelca los productos (aplicando filtro de búsqueda si existe) en el Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtro = self.entry_buscar.get().strip().lower() if hasattr(self, "entry_buscar") else ""
        mostrados = 0

        for prod in self.productos_cache:
            if filtro:
                coincide = (
                    filtro in prod.nombre.lower()
                    or filtro in prod.categoria.lower()
                    or filtro in prod.descripcion.lower()
                )
                if not coincide:
                    continue

            self.tree.insert(
                "",
                "end",
                iid=str(prod.id),
                values=(
                    prod.id,
                    prod.nombre,
                    prod.categoria,
                    prod.precio_formateado,
                    prod.descripcion,
                ),
            )
            mostrados += 1

        self.lbl_contador.configure(text=f"{mostrados} producto(s)")

    def _al_seleccionar_fila(self, _event: object) -> None:
        """Carga los datos del producto seleccionado en el formulario izquierdo."""
        seleccion = self.tree.selection()
        if not seleccion:
            return

        try:
            id_sel = int(seleccion[0])
        except ValueError:
            return

        producto = next((p for p in self.productos_cache if p.id == id_sel), None)
        if not producto:
            return

        self.producto_seleccionado_id = producto.id
        self.lbl_modo_edicion.configure(
            text=f"EDITANDO ID #{producto.id}",
            text_color="#FBBF24",
        )
        self.btn_guardar.configure(
            text=f"Actualizar Producto (#{producto.id})",
            fg_color="#2563EB",
            hover_color="#1D4ED8",
        )
        self.btn_eliminar.configure(state="normal")

        self.entry_nombre.delete(0, "end")
        self.entry_nombre.insert(0, producto.nombre)

        self.combo_categoria.set(producto.categoria)

        self.entry_precio.delete(0, "end")
        self.entry_precio.insert(0, f"{producto.precio:g}")

        self.txt_descripcion.delete("1.0", "end")
        self.txt_descripcion.insert("1.0", producto.descripcion)

    def limpiar_formulario(self) -> None:
        """Restablece el formulario al modo de alta de nuevo producto."""
        self.producto_seleccionado_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

        self.lbl_modo_edicion.configure(text="MODO: NUEVO", text_color="#38BDF8")
        self.btn_guardar.configure(
            text="Guardar Producto",
            fg_color="#16A34A",
            hover_color="#15803D",
        )
        self.btn_eliminar.configure(state="disabled")

        self.entry_nombre.delete(0, "end")
        self.entry_precio.delete(0, "end")
        self.txt_descripcion.delete("1.0", "end")

    def _accion_guardar_o_actualizar(self) -> None:
        """Valida los campos del formulario y ejecuta el alta o modificación en Excel."""
        nombre = self.entry_nombre.get().strip()
        categoria = self.combo_categoria.get().strip()
        precio_str = self.entry_precio.get().strip()
        descripcion = self.txt_descripcion.get("1.0", "end").strip()

        try:
            id_actual = self.producto_seleccionado_id if self.producto_seleccionado_id else 0
            producto = Producto(
                id=id_actual,
                nombre=nombre,
                categoria=categoria,
                precio=precio_str,
                descripcion=descripcion,
            )
        except (ValueError, TypeError) as err:
            messagebox.showwarning("Datos Inválidos", str(err))
            return

        if self.producto_seleccionado_id:
            exito = self.excel_manager.actualizar_producto(producto)
            mensaje_ok = f"El plato '{producto.nombre}' fue actualizado correctamente."
        else:
            exito = self.excel_manager.guardar_producto(producto)
            mensaje_ok = f"El plato '{producto.nombre}' fue agregado al menú con ID #{producto.id}."

        if not exito:
            messagebox.showerror(
                "Error de Persistencia",
                self.excel_manager.ultimo_error or "No se pudo guardar el producto en Excel.",
            )
            return

        self.limpiar_formulario()
        self.refrescar_datos()
        if self.on_menu_change:
            self.on_menu_change()
        messagebox.showinfo("Operación Exitosa", mensaje_ok)

    def _accion_eliminar(self) -> None:
        """Elimina el producto actualmente seleccionado previa confirmación del usuario."""
        if not self.producto_seleccionado_id:
            return

        nombre_actual = self.entry_nombre.get().strip() or f"ID #{self.producto_seleccionado_id}"
        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar '{nombre_actual}' del menú de forma permanente?",
        )
        if not confirmar:
            return

        exito = self.excel_manager.eliminar_producto(self.producto_seleccionado_id)
        if not exito:
            messagebox.showerror(
                "Error al Eliminar",
                self.excel_manager.ultimo_error or "No se pudo eliminar el producto.",
            )
            return

        self.limpiar_formulario()
        self.refrescar_datos()
        if self.on_menu_change:
            self.on_menu_change()
        messagebox.showinfo("Producto Eliminado", f"'{nombre_actual}' fue eliminado del menú.")

    def _accion_aumento_masivo(self) -> None:
        """Ejecuta el aumento o descuento porcentual masivo por categoría."""
        categoria = self.combo_cat_masiva.get().strip()
        porcentaje_str = self.entry_porcentaje.get().strip().replace(",", ".")

        if not porcentaje_str:
            messagebox.showwarning(
                "Porcentaje Requerido",
                "Ingrese un porcentaje numérico (ej. 15 para aumentar un 15%).",
            )
            return

        try:
            porcentaje = float(porcentaje_str)
        except ValueError:
            messagebox.showwarning(
                "Valor Inválido",
                f"'{porcentaje_str}' no es un porcentaje numérico válido.",
            )
            return

        if porcentaje == 0 or porcentaje <= -100:
            messagebox.showwarning(
                "Porcentaje Fuera de Rango",
                "El porcentaje debe ser distinto de 0% y mayor a -100%.",
            )
            return

        signo = "+" if porcentaje > 0 else ""
        confirmar = messagebox.askyesno(
            "Confirmar Actualización Masiva",
            f"¿Desea aplicar un ajuste de {signo}{porcentaje:g}% a '{categoria}'?\n\n"
            "Los nuevos precios se guardarán automáticamente en 'datos_rotiseria.xlsx'.",
        )
        if not confirmar:
            return

        afectados = self.excel_manager.actualizar_precios_porcentaje(categoria, porcentaje)
        if self.excel_manager.ultimo_error:
            messagebox.showerror("Error en Actualización", self.excel_manager.ultimo_error)
            return

        if afectados == 0:
            messagebox.showinfo(
                "Sin Cambios",
                f"No se encontraron productos dentro de la categoría '{categoria}'.",
            )
            return

        self.entry_porcentaje.delete(0, "end")
        self.limpiar_formulario()
        self.refrescar_datos()
        if self.on_menu_change:
            self.on_menu_change()

        messagebox.showinfo(
            "Precios Actualizados",
            f"Se actualizaron correctamente los precios de {afectados} producto(s) "
            f"en '{categoria}' ({signo}{porcentaje:g}%).",
        )
