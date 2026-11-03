"""
Vista de la pestaña 'Generador Gráfico de Flyers' (Módulo 3).
Permite seleccionar productos del menú, personalizar plantilla/título/WhatsApp,
generar el flyer en 1080x1920 px y previsualizarlo escalado en pantalla.
"""

import os
import subprocess
import sys
from tkinter import filedialog, messagebox
from typing import Dict, List, Optional

import customtkinter as ctk
from PIL import Image

from models.producto import Producto
from services.excel_manager import ExcelManager
from services.flyer_generator import FlyerGenerator


class TabFlyer(ctk.CTkFrame):
    """
    Interfaz de diseño y previsualización de flyers verticales (9:16) para
    Estados de WhatsApp e Historias de Instagram.
    """

    PREVIEW_WIDTH: int = 270
    PREVIEW_HEIGHT: int = 480

    TITULOS_SUGERIDOS: List[str] = [
        "PROMOS DE HOY",
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
        self.ultimo_flyer_generado: Optional[str] = None
        self._ctk_preview_image: Optional[ctk.CTkImage] = None

        self._configurar_grilla()
        self._construir_panel_configuracion()
        self._construir_panel_previsualizacion()
        self.refrescar_productos()
        self._mostrar_preview_inicial()

    def _configurar_grilla(self) -> None:
        """Divide la pestaña en panel de configuración/selección (izq) y previsualización (der)."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=345)
        self.grid_rowconfigure(0, weight=1)

    def _construir_panel_configuracion(self) -> None:
        """Construye la zona izquierda con selección de platos y ajustes del flyer."""
        panel_izq = ctk.CTkFrame(self, fg_color="transparent")
        panel_izq.grid(row=0, column=0, sticky="nsew", padx=(4, 10), pady=4)
        panel_izq.grid_columnconfigure(0, weight=1)
        panel_izq.grid_rowconfigure(0, weight=1)

        # --- Bloque 1: Selección de Productos mediante Checkboxes ---
        card_seleccion = ctk.CTkFrame(panel_izq, corner_radius=12)
        card_seleccion.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        card_seleccion.grid_columnconfigure(0, weight=1)
        card_seleccion.grid_rowconfigure(1, weight=1)

        header_sel = ctk.CTkFrame(card_seleccion, fg_color="transparent")
        header_sel.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        header_sel.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_sel,
            text="1. Seleccione los Productos a Destacar (Máximo 6)",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, sticky="w")

        self.lbl_seleccionados = ctk.CTkLabel(
            header_sel,
            text="Seleccionados: 0 / 6",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#FBBF24",
        )
        self.lbl_seleccionados.grid(row=0, column=1, padx=(10, 10))

        btn_sel_4 = ctk.CTkButton(
            header_sel,
            text="Marcar 4 primeros",
            width=125,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=11),
            command=self._seleccionar_primeros_cuatro,
        )
        btn_sel_4.grid(row=0, column=2, padx=(0, 6))

        btn_desmarcar = ctk.CTkButton(
            header_sel,
            text="Limpiar",
            width=80,
            height=28,
            fg_color="#475569",
            hover_color="#334155",
            font=ctk.CTkFont(size=11),
            command=self._desmarcar_todos,
        )
        btn_desmarcar.grid(row=0, column=3)

        self.scroll_productos = ctk.CTkScrollableFrame(
            card_seleccion,
            corner_radius=8,
            label_text="Platos disponibles en 'datos_rotiseria.xlsx'",
        )
        self.scroll_productos.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 14))
        self.scroll_productos.grid_columnconfigure(0, weight=1)

        # --- Bloque 2: Personalización Visual y Generación ---
        card_ajustes = ctk.CTkFrame(panel_izq, corner_radius=12)
        card_ajustes.grid(row=1, column=0, sticky="ew")
        card_ajustes.grid_columnconfigure(0, weight=1)
        card_ajustes.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card_ajustes,
            text="2. Personalización del Flyer y Datos de Contacto",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 8))

        # Título y WhatsApp
        ctk.CTkLabel(
            card_ajustes,
            text="Título Principal del Encabezado:",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 2))

        ctk.CTkLabel(
            card_ajustes,
            text="WhatsApp de Pedidos (Pie de Página):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=1, column=1, sticky="w", padx=16, pady=(0, 2))

        self.combo_titulo = ctk.CTkComboBox(
            card_ajustes,
            values=self.TITULOS_SUGERIDOS,
            height=34,
        )
        self.combo_titulo.set("PROMOS DE HOY")
        self.combo_titulo.grid(row=2, column=0, sticky="ew", padx=(16, 8), pady=(0, 10))

        self.entry_whatsapp = ctk.CTkEntry(
            card_ajustes,
            placeholder_text="Ej: 3794-123456 / 11-4455-6677",
            height=34,
        )
        self.entry_whatsapp.insert(0, "3794-556677")
        self.entry_whatsapp.grid(row=2, column=1, sticky="ew", padx=(8, 16), pady=(0, 10))

        # Selector de plantilla (.png / .jpg)
        ctk.CTkLabel(
            card_ajustes,
            text="Imagen de Plantilla Base (1080x1920 px):",
            font=ctk.CTkFont(size=12, weight="bold"),
        ).grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 2))

        fila_plantilla = ctk.CTkFrame(card_ajustes, fg_color="transparent")
        fila_plantilla.grid(row=4, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 12))
        fila_plantilla.grid_columnconfigure(0, weight=1)

        self.lbl_plantilla_actual = ctk.CTkLabel(
            fila_plantilla,
            text="Fondo degradado oscuro elegante (Por defecto)",
            font=ctk.CTkFont(size=12),
            text_color="#38BDF8",
            anchor="w",
        )
        self.lbl_plantilla_actual.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        btn_elegir_plantilla = ctk.CTkButton(
            fila_plantilla,
            text="📂 Elegir Imagen (.png/.jpg)",
            width=185,
            height=32,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            command=self._seleccionar_archivo_plantilla,
        )
        btn_elegir_plantilla.grid(row=0, column=1, padx=(0, 6))

        btn_reset_plantilla = ctk.CTkButton(
            fila_plantilla,
            text="Usar Default",
            width=105,
            height=32,
            fg_color="#475569",
            hover_color="#334155",
            command=self._restablecer_plantilla_default,
        )
        btn_reset_plantilla.grid(row=0, column=2)

        # Botón Principal de Generación
        self.btn_generar = ctk.CTkButton(
            card_ajustes,
            text="🎨  GENERAR FLYER PROMOCIONAL (1080x1920 px)",
            height=44,
            fg_color="#EA580C",
            hover_color="#C2410C",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._accion_generar_flyer,
        )
        self.btn_generar.grid(row=5, column=0, columnspan=2, sticky="ew", padx=16, pady=(2, 14))

    def _construir_panel_previsualizacion(self) -> None:
        """Construye la columna derecha con el lienzo escalado 9:16 de previsualización."""
        card_preview = ctk.CTkFrame(self, corner_radius=12)
        card_preview.grid(row=0, column=1, sticky="nsew", padx=(0, 4), pady=4)
        card_preview.grid_columnconfigure(0, weight=1)
        card_preview.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            card_preview,
            text="Vista Previa (Formato 9:16)",
            font=ctk.CTkFont(size=15, weight="bold"),
        ).grid(row=0, column=0, padx=16, pady=(14, 4))

        marco_imagen = ctk.CTkFrame(
            card_preview,
            width=self.PREVIEW_WIDTH + 16,
            height=self.PREVIEW_HEIGHT + 16,
            corner_radius=12,
            fg_color="#0F172A",
        )
        marco_imagen.grid(row=1, column=0, padx=18, pady=6)

        self.lbl_imagen_preview = ctk.CTkLabel(
            marco_imagen,
            text="Previsualización\n1080 x 1920 px",
            width=self.PREVIEW_WIDTH,
            height=self.PREVIEW_HEIGHT,
        )
        self.lbl_imagen_preview.pack(padx=8, pady=8)

        self.lbl_ruta_exportada = ctk.CTkLabel(
            card_preview,
            text="Listo para exportar en carpeta 'output/'",
            font=ctk.CTkFont(size=11),
            text_color="#94A3B8",
            wraplength=300,
        )
        self.lbl_ruta_exportada.grid(row=2, column=0, padx=14, pady=(2, 6))

        self.btn_abrir_output = ctk.CTkButton(
            card_preview,
            text="📁 Abrir Carpeta output/",
            height=34,
            fg_color="#334155",
            hover_color="#475569",
            command=self._abrir_carpeta_output,
        )
        self.btn_abrir_output.grid(row=3, column=0, sticky="ew", padx=18, pady=(0, 14))

    # =========================================================================
    # LÓGICA DE SELECCIÓN Y RENDERIZADO
    # =========================================================================

    def refrescar_productos(self) -> None:
        """
        Recarga los productos desde Excel preservando las selecciones previas
        que continúen existiendo.
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
                text_color="#94A3B8",
            ).grid(row=0, column=0, padx=10, pady=20)
            self._actualizar_contador_seleccion()
            return

        # Si es la primera carga y no había selección, preseleccionar hasta los primeros 4
        preseleccionar_inicial = len(ids_previamente_marcados) == 0

        for idx, prod in enumerate(self.productos_disponibles):
            fila_item = ctk.CTkFrame(self.scroll_productos, corner_radius=8, fg_color="#1E293B")
            fila_item.grid(row=idx, column=0, sticky="ew", padx=4, pady=4)
            fila_item.grid_columnconfigure(0, weight=1)

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
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda p_id=prod.id: self._al_cambiar_checkbox(p_id),
            )
            cb.grid(row=0, column=0, sticky="w", padx=12, pady=(8, 4))

            lbl_precio = ctk.CTkLabel(
                fila_item,
                text=prod.precio_formateado,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="#FBBF24",
            )
            lbl_precio.grid(row=0, column=1, sticky="e", padx=12, pady=(8, 4))

            if prod.descripcion:
                lbl_desc = ctk.CTkLabel(
                    fila_item,
                    text=prod.descripcion,
                    font=ctk.CTkFont(size=11),
                    text_color="#94A3B8",
                    anchor="w",
                )
                lbl_desc.grid(row=1, column=0, columnspan=2, sticky="w", padx=38, pady=(0, 6))

        self._actualizar_contador_seleccion()

    def _al_cambiar_checkbox(self, prod_id: int) -> None:
        """Verifica que no se seleccionen más de 6 productos por flyer."""
        marcados = [pid for pid, var in self.checkbox_vars.items() if var.get()]
        if len(marcados) > FlyerGenerator.MAX_PRODUCTOS:
            self.checkbox_vars[prod_id].set(False)
            messagebox.showwarning(
                "Límite de Diseño Alcanzado",
                f"Para garantizar la legibilidad en celulares, se permiten hasta "
                f"{FlyerGenerator.MAX_PRODUCTOS} productos por flyer.",
            )
        self._actualizar_contador_seleccion()

    def _actualizar_contador_seleccion(self) -> None:
        """Actualiza la etiqueta del contador de productos marcados."""
        cant = sum(1 for var in self.checkbox_vars.values() if var.get())
        color = "#4ADE80" if 1 <= cant <= FlyerGenerator.MAX_PRODUCTOS else "#F87171"
        self.lbl_seleccionados.configure(
            text=f"Seleccionados: {cant} / {FlyerGenerator.MAX_PRODUCTOS}",
            text_color=color,
        )

    def _seleccionar_primeros_cuatro(self) -> None:
        """Marca automáticamente los primeros 4 productos de la lista."""
        for idx, prod in enumerate(self.productos_disponibles):
            if prod.id in self.checkbox_vars:
                self.checkbox_vars[prod.id].set(idx < 4)
        self._actualizar_contador_seleccion()

    def _desmarcar_todos(self) -> None:
        """Limpia todos los checkboxes de productos."""
        for var in self.checkbox_vars.values():
            var.set(False)
        self._actualizar_contador_seleccion()

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
            self.lbl_plantilla_actual.configure(
                text=f"Plantilla activa: {nombre_corto}",
                text_color="#4ADE80",
            )

    def _restablecer_plantilla_default(self) -> None:
        """Vuelve a configurar el fondo degradado oscuro programático por defecto."""
        self.plantilla_seleccionada = None
        self.lbl_plantilla_actual.configure(
            text="Fondo degradado oscuro elegante (Por defecto)",
            text_color="#38BDF8",
        )

    def _mostrar_preview_inicial(self) -> None:
        """Muestra la plantilla oscura por defecto en el panel de previsualización."""
        ruta_default = self.flyer_generator.default_template_path
        if os.path.exists(ruta_default):
            self._cargar_imagen_en_preview(ruta_default)

    def _cargar_imagen_en_preview(self, ruta_imagen: str) -> None:
        """Carga y escala proporcionalmente una imagen en el widget CTkLabel de vista previa."""
        try:
            with Image.open(ruta_imagen) as img:
                copia_preview = img.convert("RGBA").resize(
                    (self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT),
                    Image.Resampling.LANCZOS,
                )
            self._ctk_preview_image = ctk.CTkImage(
                light_image=copia_preview,
                dark_image=copia_preview,
                size=(self.PREVIEW_WIDTH, self.PREVIEW_HEIGHT),
            )
            self.lbl_imagen_preview.configure(image=self._ctk_preview_image, text="")
        except Exception as err:
            self.lbl_imagen_preview.configure(text=f"No se pudo previsualizar:\n{err}")

    def _accion_generar_flyer(self) -> None:
        """Recopila los productos seleccionados y genera el flyer promocional."""
        productos_elegidos = [
            prod
            for prod in self.productos_disponibles
            if self.checkbox_vars.get(prod.id) and self.checkbox_vars[prod.id].get()
        ]

        if not productos_elegidos:
            messagebox.showwarning(
                "Sin Productos Seleccionados",
                "Por favor, marque al menos 1 producto de la lista para generar el flyer.",
            )
            return

        titulo = self.combo_titulo.get().strip() or "PROMOS DE HOY"
        whatsapp = self.entry_whatsapp.get().strip()

        try:
            ruta_exportada = self.flyer_generator.generar_flyer(
                productos=productos_elegidos,
                plantilla_path=self.plantilla_seleccionada,
                titulo=titulo,
                whatsapp=whatsapp,
            )
            self.ultimo_flyer_generado = ruta_exportada
            self._cargar_imagen_en_preview(ruta_exportada)

            nombre_archivo = os.path.basename(ruta_exportada)
            self.lbl_ruta_exportada.configure(
                text=f"✔ Exportado: output/{nombre_archivo}",
                text_color="#4ADE80",
            )
            messagebox.showinfo(
                "Flyer Generado con Éxito",
                f"El flyer promocional (1080x1920 px) se guardó en:\n\n{ruta_exportada}",
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
