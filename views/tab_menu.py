"""
Vista de la pestaña 'Gestión de Menú y Precios' (Módulo 1).
Permite alta, edición y baja de productos en tabla interactiva, con transición
dinámica de estado en el formulario (Modo Nuevo vs Modo Edición) y confirmación
defensiva en el aumento porcentual masivo por categoría.
Panel izquierdo scrollable (CTkScrollableFrame) y paddings optimizados para garantizar
visibilidad al 100% en pantallas de laptops y resoluciones reducidas.
"""

from tkinter import messagebox, ttk
from typing import Callable, List, Optional

import customtkinter as ctk

from models.producto import Producto
from services.excel_manager import ExcelManager
from views.theme_manager import ThemeManager


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
        """Configura el diseño responsivo de 2 columnas (Formulario scrollable / Tabla)."""
        self.grid_columnconfigure(0, weight=0, minsize=390)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def _construir_panel_izquierdo(self) -> None:
        """
        Construye la columna izquierda como un CTkScrollableFrame con ancho fijo adecuado
        y paddings compactos para asegurar que todos los controles (incluyendo el botón
        de ajuste porcentual) sean 100% visibles y accesibles en laptops.
        """
        self.contenedor_izq = ctk.CTkScrollableFrame(
            self,
            width=390,
            corner_radius=12,
            fg_color="transparent",
        )
        self.contenedor_izq.grid(row=0, column=0, sticky="nsew", padx=(4, 8), pady=2)
        self.contenedor_izq.grid_columnconfigure(0, weight=1)

        # --- Tarjeta 1: Formulario Alta / Edición de Producto ---
        card_form = ctk.CTkFrame(
            self.contenedor_izq,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_form.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        card_form.grid_columnconfigure(0, weight=1)

        header_form = ctk.CTkFrame(card_form, fg_color="transparent")
        header_form.grid(row=0, column=0, sticky="ew", padx=14, pady=(10, 4))
        header_form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_form,
            text="Plato / Producto del Menú",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w")

        self.lbl_modo_edicion = ctk.CTkLabel(
            header_form,
            text="MODO: NUEVO",
            font=ThemeManager.font_small_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_modo_edicion.grid(row=0, column=1, sticky="e")

        # Nombre del Plato
        ctk.CTkLabel(
            card_form,
            text="Nombre del Plato o Combo *",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(2, 2))

        self.entry_nombre = ctk.CTkEntry(
            card_form,
            placeholder_text="Ej: Pizza Napolitana Especial",
            height=34,
            font=ThemeManager.font_input(),
        )
        self.entry_nombre.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))

        # Fila Categoría y Precio
        fila_cat_precio = ctk.CTkFrame(card_form, fg_color="transparent")
        fila_cat_precio.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 6))
        fila_cat_precio.grid_columnconfigure(0, weight=3)
        fila_cat_precio.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(
            fila_cat_precio,
            text="Categoría *",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 2))

        ctk.CTkLabel(
            fila_cat_precio,
            text="Precio ($) *",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=1, sticky="w", padx=(4, 0), pady=(0, 2))

        self.combo_categoria = ctk.CTkComboBox(
            fila_cat_precio,
            values=Producto.CATEGORIAS_SUGERIDAS,
            height=34,
            font=ThemeManager.font_input(),
        )
        self.combo_categoria.set("Pizzas")
        self.combo_categoria.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.entry_precio = ctk.CTkEntry(
            fila_cat_precio,
            placeholder_text="Ej: 12500",
            height=34,
            font=ThemeManager.font_input(bold=True),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.entry_precio.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        # Descripción
        ctk.CTkLabel(
            card_form,
            text="Descripción / Ingredientes (para el Flyer)",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=4, column=0, sticky="w", padx=14, pady=(2, 2))

        self.txt_descripcion = ctk.CTkTextbox(
            card_form,
            height=58,
            corner_radius=8,
            font=ThemeManager.font_input(),
        )
        self.txt_descripcion.grid(row=5, column=0, sticky="ew", padx=14, pady=(0, 8))

        # Botones CRUD
        frame_botones = ctk.CTkFrame(card_form, fg_color="transparent")
        frame_botones.grid(row=6, column=0, sticky="ew", padx=14, pady=(0, 10))
        frame_botones.grid_columnconfigure(0, weight=1)
        frame_botones.grid_columnconfigure(1, weight=1)

        self.btn_guardar = ctk.CTkButton(
            frame_botones,
            text="Guardar Producto",
            height=36,
            fg_color=ThemeManager.BTN_SUCCESS,
            hover_color=ThemeManager.BTN_SUCCESS_HOVER,
            font=ThemeManager.font_body_bold(),
            command=self._accion_guardar_o_actualizar,
        )
        self.btn_guardar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 6))

        self.btn_limpiar = ctk.CTkButton(
            frame_botones,
            text="Limpiar / Nuevo",
            height=30,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_small_bold(),
            command=self.limpiar_formulario,
        )
        self.btn_limpiar.grid(row=1, column=0, sticky="ew", padx=(0, 3))

        self.btn_eliminar = ctk.CTkButton(
            frame_botones,
            text="Eliminar Plato",
            height=30,
            fg_color=ThemeManager.BTN_DANGER,
            hover_color=ThemeManager.BTN_DANGER_HOVER,
            font=ThemeManager.font_small_bold(),
            state="disabled",
            command=self._accion_eliminar,
        )
        self.btn_eliminar.grid(row=1, column=1, sticky="ew", padx=(3, 0))

        # --- Tarjeta 2: Actualización Masiva de Precios por Porcentaje ---
        card_masivo = ctk.CTkFrame(
            self.contenedor_izq,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_masivo.grid(row=1, column=0, sticky="ew", pady=(0, 4))
        card_masivo.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card_masivo,
            text="Actualización Masiva de Precios (%)",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        ).grid(row=0, column=0, sticky="w", padx=14, pady=(10, 2))

        ctk.CTkLabel(
            card_masivo,
            text="Aplique un ajuste porcentual por inflación a una categoría o a todo el menú.",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
            wraplength=340,
            justify="left",
        ).grid(row=1, column=0, sticky="w", padx=14, pady=(0, 6))

        fila_masivo = ctk.CTkFrame(card_masivo, fg_color="transparent")
        fila_masivo.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        fila_masivo.grid_columnconfigure(0, weight=3)
        fila_masivo.grid_columnconfigure(1, weight=2)

        ctk.CTkLabel(
            fila_masivo,
            text="Categoría objetivo:",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", padx=(0, 4), pady=(0, 2))

        ctk.CTkLabel(
            fila_masivo,
            text="Porcentaje (%):",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=1, sticky="w", padx=(4, 0), pady=(0, 2))

        self.combo_cat_masiva = ctk.CTkComboBox(
            fila_masivo,
            values=["Todas las categorías"] + Producto.CATEGORIAS_SUGERIDAS,
            height=34,
            font=ThemeManager.font_input(),
        )
        self.combo_cat_masiva.set("Todas las categorías")
        self.combo_cat_masiva.grid(row=1, column=0, sticky="ew", padx=(0, 4))

        self.entry_porcentaje = ctk.CTkEntry(
            fila_masivo,
            placeholder_text="Ej: 15",
            height=34,
            font=ThemeManager.font_input(bold=True),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.entry_porcentaje.grid(row=1, column=1, sticky="ew", padx=(4, 0))

        self.btn_aplicar_aumento = ctk.CTkButton(
            card_masivo,
            text="Aplicar Ajuste Porcentual",
            height=34,
            fg_color=ThemeManager.BTN_WARNING,
            hover_color=ThemeManager.BTN_WARNING_HOVER,
            font=ThemeManager.font_body_bold(),
            command=self._accion_aumento_masivo,
        )
        self.btn_aplicar_aumento.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 12))

    def _construir_panel_derecho(self) -> None:
        """Construye la tabla interactiva de productos con buscador en tiempo real."""
        card_tabla = ctk.CTkFrame(
            self,
            corner_radius=12,
            fg_color=ThemeManager.BG_CARD,
            border_width=1,
            border_color=ThemeManager.BORDER_CARD,
        )
        card_tabla.grid(row=0, column=1, sticky="nsew", padx=(0, 4), pady=2)
        card_tabla.grid_columnconfigure(0, weight=1)
        card_tabla.grid_rowconfigure(1, weight=1)

        barra_sup = ctk.CTkFrame(card_tabla, fg_color="transparent")
        barra_sup.grid(row=0, column=0, columnspan=2, sticky="ew", padx=14, pady=(10, 8))
        barra_sup.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            barra_sup,
            text="Catálogo Actual de Platos",
            font=ThemeManager.font_card_title(),
            text_color=ThemeManager.TEXT_MAIN,
        ).grid(row=0, column=0, sticky="w", padx=(0, 12))

        self.entry_buscar = ctk.CTkEntry(
            barra_sup,
            placeholder_text="🔍 Filtrar por nombre o categoría...",
            height=34,
            font=ThemeManager.font_input(),
        )
        self.entry_buscar.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        self.entry_buscar.bind("<KeyRelease>", lambda _e: self._poblar_treeview())

        self.lbl_contador = ctk.CTkLabel(
            barra_sup,
            text="0 productos",
            font=ThemeManager.font_body_bold(),
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.lbl_contador.grid(row=0, column=2, padx=(0, 8))

        btn_recargar = ctk.CTkButton(
            barra_sup,
            text="↻ Recargar",
            width=90,
            height=32,
            fg_color=ThemeManager.BTN_SECONDARY,
            hover_color=ThemeManager.BTN_SECONDARY_HOVER,
            text_color=ThemeManager.BTN_SECONDARY_TEXT,
            font=ThemeManager.font_small_bold(),
            command=self.refrescar_datos,
        )
        btn_recargar.grid(row=0, column=3)

        # Aplicar estilizado de tabla acorde al tema actual
        ThemeManager.aplicar_estilo_treeview()

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

        self.tree.column("id", width=50, minwidth=40, anchor="center", stretch=False)
        self.tree.column("nombre", width=220, minwidth=150, anchor="w")
        self.tree.column("categoria", width=140, minwidth=100, anchor="w")
        self.tree.column("precio", width=110, minwidth=90, anchor="e", stretch=False)
        self.tree.column("descripcion", width=260, minwidth=140, anchor="w")

        scrollbar = ctk.CTkScrollbar(card_tabla, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=1, column=0, sticky="nsew", padx=(14, 0), pady=(0, 8))
        scrollbar.grid(row=1, column=1, sticky="ns", padx=(4, 12), pady=(0, 8))

        self.tree.bind("<<TreeviewSelect>>", self._al_seleccionar_fila)

        ctk.CTkLabel(
            card_tabla,
            text="💡 Haga clic sobre cualquier fila de la tabla para pasar a Modo Edición ('Actualizar Producto').",
            font=ThemeManager.font_small(),
            text_color=ThemeManager.TEXT_MUTED,
        ).grid(row=2, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 8))

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

        opciones_masivas = (
            ["Todas las categorías"] + sorted(existentes)
            if existentes
            else ["Todas las categorías"] + todas
        )
        seleccion_previa = self.combo_cat_masiva.get()
        self.combo_cat_masiva.configure(values=opciones_masivas)
        if seleccion_previa not in opciones_masivas:
            self.combo_cat_masiva.set("Todas las categorías")

    def _poblar_treeview(self) -> None:
        """Vuelca los productos (aplicando filtro de búsqueda si existe) en el Treeview."""
        for item in self.tree.get_children():
            self.tree.delete(item)

        filtro = (
            self.entry_buscar.get().strip().lower() if hasattr(self, "entry_buscar") else ""
        )
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
        """
        Carga los datos del producto seleccionado en el formulario izquierdo y cambia
        dinámicamente el botón principal de 'Guardar Producto' (Modo Nuevo) a
        'Actualizar Producto' (Modo Edición).
        """
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
            text=f"MODO: EDICIÓN (#{producto.id})",
            text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS,
        )
        self.btn_guardar.configure(
            text="Actualizar Producto",
            fg_color=ThemeManager.BTN_PRIMARY,
            hover_color=ThemeManager.BTN_PRIMARY_HOVER,
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
        """Restablece el formulario al modo de alta de nuevo producto ('Guardar Producto')."""
        self.producto_seleccionado_id = None
        if self.tree.selection():
            self.tree.selection_remove(self.tree.selection())

        self.lbl_modo_edicion.configure(
            text="MODO: NUEVO", text_color=ThemeManager.COLOR_NUMEROS_DESTACADOS
        )
        self.btn_guardar.configure(
            text="Guardar Producto",
            fg_color=ThemeManager.BTN_SUCCESS,
            hover_color=ThemeManager.BTN_SUCCESS_HOVER,
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
                self.excel_manager.ultimo_error or ExcelManager.MENSAJE_ARCHIVO_ABIERTO,
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
                self.excel_manager.ultimo_error or ExcelManager.MENSAJE_ARCHIVO_ABIERTO,
            )
            return

        self.limpiar_formulario()
        self.refrescar_datos()
        if self.on_menu_change:
            self.on_menu_change()
        messagebox.showinfo("Producto Eliminado", f"'{nombre_actual}' fue eliminado del menú.")

    def _accion_aumento_masivo(self) -> None:
        """
        Ejecuta el aumento o descuento porcentual masivo por categoría tras desplegar
        un cuadro emergente de confirmación defensiva.
        """
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

        confirmar = messagebox.askyesno(
            "Confirmar Ajuste Porcentual Masivo",
            f"¿Está seguro de aplicar un incremento del {porcentaje:g}% en la categoría '{categoria}'?",
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

        signo = "+" if porcentaje > 0 else ""
        messagebox.showinfo(
            "Precios Actualizados",
            f"Se actualizaron correctamente los precios de {afectados} producto(s) "
            f"en '{categoria}' ({signo}{porcentaje:g}%).",
        )
