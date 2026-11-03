"""
Servicio de persistencia local en Excel ('data/datos_rotiseria.xlsx').
Gestiona de forma atómica y segura las hojas 'Menu' y 'Ventas' utilizando openpyxl.
"""

from datetime import datetime
import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

import openpyxl
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.utils.exceptions import InvalidFileException
from openpyxl.workbook import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from models.producto import Producto
from models.venta import Venta

logger = logging.getLogger(__name__)


class ExcelManager:
    """
    Gestor de persistencia local sobre archivo Excel (.xlsx).
    Garantiza la existencia del archivo, el estilizado de cabeceras,
    la escritura atómica mediante archivo temporal y el manejo defensivo
    de bloqueos (PermissionError cuando el archivo está abierto en Excel).
    """

    HOJA_MENU: str = "Menu"
    HOJA_VENTAS: str = "Ventas"

    ENCABEZADOS_MENU: List[str] = ["ID", "Nombre", "Categoria", "Precio", "Descripcion"]
    ENCABEZADOS_VENTAS: List[str] = [
        "ID",
        "Fecha_Hora",
        "Detalle",
        "Total",
        "Medio_Pago",
        "Tipo_Entrega",
    ]

    def __init__(self, filepath: str = "data/datos_rotiseria.xlsx") -> None:
        """
        Inicializa el gestor de Excel y asegura la estructura base del archivo.

        Args:
            filepath (str): Ruta hacia el archivo Excel de persistencia.
        """
        self.filepath: str = os.path.abspath(filepath)
        self.ultimo_error: Optional[str] = None
        self._asegurar_directorio()
        self._inicializar_archivo_si_no_existe()

    def _asegurar_directorio(self) -> None:
        """Crea el directorio contenedor del archivo Excel si no existe."""
        directorio = os.path.dirname(self.filepath)
        if directorio and not os.path.exists(directorio):
            os.makedirs(directorio, exist_ok=True)

    def _verificar_bloqueo_archivo(self) -> None:
        """
        Verifica preventivamente si el archivo Excel está bloqueado por otro proceso
        (como Microsoft Excel o LibreOffice Calc) antes de intentar sobrescribirlo.

        Raises:
            PermissionError: Si se detecta archivo lock o falta de permisos de escritura.
        """
        directorio = os.path.dirname(self.filepath)
        nombre_archivo = os.path.basename(self.filepath)

        # Verificar archivos temporales de bloqueo de MS Office (~$...) o LibreOffice (.~lock...)
        lock_ms = os.path.join(directorio, f"~${nombre_archivo}")
        lock_lo = os.path.join(directorio, f".~lock.{nombre_archivo}#")
        if os.path.exists(lock_ms) or os.path.exists(lock_lo):
            raise PermissionError(
                f"El archivo '{nombre_archivo}' se encuentra abierto en Excel u otro visor de hojas "
                "de cálculo. Por favor, ciérrelo antes de guardar cambios."
            )

        if os.path.exists(self.filepath):
            # Prueba de apertura en modo lectura/escritura binaria
            try:
                with open(self.filepath, "r+b"):
                    pass
            except PermissionError as exc:
                raise PermissionError(
                    f"Permiso denegado al acceder a '{nombre_archivo}'. "
                    "Verifique que el archivo no esté abierto en otro programa."
                ) from exc

    def _estilizar_hoja(self, ws: Worksheet, encabezados: List[str], anchos: List[int]) -> None:
        """
        Aplica formato profesional y sobrio a los encabezados de una hoja de Excel.
        """
        fuente_header = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
        relleno_header = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        alineacion_header = Alignment(horizontal="center", vertical="center", wrap_text=True)
        borde_fino = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="medium", color="0F172A"),
        )

        for idx, texto in enumerate(encabezados, start=1):
            ws.cell(row=1, column=idx, value=texto)

        ws.row_dimensions[1].height = 26

        for col_idx in range(1, len(encabezados) + 1):
            celda = ws.cell(row=1, column=col_idx)
            celda.font = fuente_header
            celda.fill = relleno_header
            celda.alignment = alineacion_header
            celda.border = borde_fino

            letra_col = get_column_letter(col_idx)
            ancho = anchos[col_idx - 1] if col_idx - 1 < len(anchos) else 18
            ws.column_dimensions[letra_col].width = ancho

        # Inmovilizar fila superior de encabezados
        ws.freeze_panes = "A2"

    def _guardar_workbook_atomico(self, wb: Workbook) -> None:
        """
        Guarda el Workbook de manera atómica escribiendo primero en un archivo
        temporal en el mismo directorio y luego reemplazando el archivo destino.
        Esto evita pérdida o corrupción de datos ante cierres inesperados.
        """
        self._verificar_bloqueo_archivo()
        directorio = os.path.dirname(self.filepath)
        fd, temp_path = tempfile.mkstemp(suffix=".tmp.xlsx", prefix=".rotiseria_", dir=directorio)
        os.close(fd)

        try:
            wb.save(temp_path)
            os.chmod(temp_path, 0o644)
            os.replace(temp_path, self.filepath)
        except PermissionError as exc:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise PermissionError(
                "No se pudo guardar 'datos_rotiseria.xlsx' porque está abierto o bloqueado "
                "por otro programa. Cierre el Excel e intente nuevamente."
            ) from exc
        except Exception:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError:
                    pass
            raise

    def _inicializar_archivo_si_no_existe(self) -> None:
        """
        Crea el archivo Excel con las hojas 'Menu' y 'Ventas' si no existe,
        o repara las hojas faltantes si el archivo ya existe.
        """
        try:
            if not os.path.exists(self.filepath):
                wb = Workbook()
                # Configurar hoja Menu usando la hoja activa inicial
                ws_menu = wb.active
                ws_menu.title = self.HOJA_MENU
                self._estilizar_hoja(ws_menu, self.ENCABEZADOS_MENU, [10, 32, 22, 16, 48])

                # Crear hoja Ventas
                ws_ventas = wb.create_sheet(title=self.HOJA_VENTAS)
                self._estilizar_hoja(ws_ventas, self.ENCABEZADOS_VENTAS, [10, 22, 45, 16, 20, 18])

                self._guardar_workbook_atomico(wb)
                wb.close()
                return

            # Si el archivo existe, verificar que contenga ambas hojas requeridas
            wb = openpyxl.load_workbook(self.filepath)
            modificado = False

            if self.HOJA_MENU not in wb.sheetnames:
                ws_menu = wb.create_sheet(title=self.HOJA_MENU, index=0)
                self._estilizar_hoja(ws_menu, self.ENCABEZADOS_MENU, [10, 32, 22, 16, 48])
                modificado = True

            if self.HOJA_VENTAS not in wb.sheetnames:
                ws_ventas = wb.create_sheet(title=self.HOJA_VENTAS)
                self._estilizar_hoja(ws_ventas, self.ENCABEZADOS_VENTAS, [10, 22, 45, 16, 20, 18])
                modificado = True

            if modificado:
                self._guardar_workbook_atomico(wb)
            wb.close()

        except PermissionError as exc:
            self.ultimo_error = str(exc)
            logger.error("Archivo Excel bloqueado durante la inicialización: %s", exc)
        except (InvalidFileException, OSError) as exc:
            self.ultimo_error = f"Error al inicializar el archivo Excel: {exc}"
            logger.error("Error de archivo Excel: %s", exc)

    def _cargar_workbook(self) -> Workbook:
        """Carga el Workbook asegurando previamente su estructura."""
        if not os.path.exists(self.filepath):
            self._inicializar_archivo_si_no_existe()
        return openpyxl.load_workbook(self.filepath)

    def _formatear_fila_datos(self, ws: Worksheet, fila_idx: int, es_moneda_col: int) -> None:
        """Aplica formato limpio de bordes y moneda a una fila de datos recién escrita."""
        borde_celda = Border(
            left=Side(style="thin", color="E2E8F0"),
            right=Side(style="thin", color="E2E8F0"),
            top=Side(style="thin", color="E2E8F0"),
            bottom=Side(style="thin", color="E2E8F0"),
        )
        fuente_datos = Font(name="Calibri", size=11, color="0F172A")

        for col_idx in range(1, ws.max_column + 1):
            celda = ws.cell(row=fila_idx, column=col_idx)
            celda.font = fuente_datos
            celda.border = borde_celda
            if col_idx == 1:
                celda.alignment = Alignment(horizontal="center", vertical="center")
            elif col_idx == es_moneda_col:
                celda.number_format = "$ #,##0.00"
                celda.alignment = Alignment(horizontal="right", vertical="center")
            else:
                celda.alignment = Alignment(horizontal="left", vertical="center")

    # =========================================================================
    # MÉTODOS OBLIGATORIOS DE GESTIÓN DE PRODUCTOS (HOJA 'Menu')
    # =========================================================================

    def obtener_productos(self) -> List[Producto]:
        """
        Lee todos los productos registrados en la hoja 'Menu'.

        Returns:
            List[Producto]: Lista de instancias de Producto ordenadas por ID.
        """
        self.ultimo_error = None
        productos: List[Producto] = []
        try:
            wb = self._cargar_workbook()
            if self.HOJA_MENU not in wb.sheetnames:
                wb.close()
                return []

            ws = wb[self.HOJA_MENU]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or all(celda is None or str(celda).strip() == "" for celda in row):
                    continue
                try:
                    prod = Producto(
                        id=row[0],
                        nombre=row[1],
                        categoria=row[2],
                        precio=row[3],
                        descripcion=row[4] if len(row) > 4 and row[4] is not None else "",
                    )
                    productos.append(prod)
                except (ValueError, TypeError) as err:
                    logger.warning("Fila de producto ignorada por formato inválido %s: %s", row, err)

            wb.close()
            productos.sort(key=lambda p: p.id)
            return productos

        except PermissionError as exc:
            self.ultimo_error = (
                "No se pudo leer 'datos_rotiseria.xlsx' porque está bloqueado por otro programa."
            )
            logger.error("PermissionError al obtener productos: %s", exc)
            return []
        except Exception as exc:
            self.ultimo_error = f"Error al leer productos del archivo Excel: {exc}"
            logger.error("Error inesperado al obtener productos: %s", exc)
            return []

    def guardar_producto(self, producto: Producto) -> bool:
        """
        Guarda un nuevo producto en la hoja 'Menu'.
        Si el producto tiene ID 0 (o un ID ya existente), se le asigna o valida
        el ID incremental correspondiente.

        Args:
            producto (Producto): Instancia validada de Producto a persistir.

        Returns:
            bool: True si se guardó correctamente, False en caso de error.
        """
        self.ultimo_error = None
        if not isinstance(producto, Producto):
            self.ultimo_error = "El objeto proporcionado no es una instancia válida de Producto."
            return False

        try:
            wb = self._cargar_workbook()
            ws = wb[self.HOJA_MENU]

            ids_existentes: List[int] = []
            for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
                if row and row[0] is not None and str(row[0]).strip() != "":
                    try:
                        ids_existentes.append(int(float(row[0])))
                    except (ValueError, TypeError):
                        pass

            if producto.id <= 0 or producto.id in ids_existentes:
                producto.id = (max(ids_existentes) + 1) if ids_existentes else 1

            ws.append(producto.to_excel_row())
            self._formatear_fila_datos(ws, ws.max_row, es_moneda_col=4)

            self._guardar_workbook_atomico(wb)
            wb.close()
            return True

        except PermissionError as exc:
            self.ultimo_error = str(exc)
            logger.error("PermissionError al guardar producto: %s", exc)
            return False
        except Exception as exc:
            self.ultimo_error = f"Error al guardar el producto en Excel: {exc}"
            logger.error("Error al guardar producto: %s", exc)
            return False

    def actualizar_producto(self, producto: Producto) -> bool:
        """
        Actualiza los datos de un producto existente identificado por su ID.

        Args:
            producto (Producto): Producto con los datos modificados y su ID original.

        Returns:
            bool: True si el producto fue encontrado y actualizado, False en caso contrario.
        """
        self.ultimo_error = None
        if not isinstance(producto, Producto) or producto.id <= 0:
            self.ultimo_error = "El producto a actualizar debe tener un ID válido mayor a 0."
            return False

        try:
            wb = self._cargar_workbook()
            ws = wb[self.HOJA_MENU]
            encontrado = False

            for row_idx in range(2, ws.max_row + 1):
                val_id = ws.cell(row=row_idx, column=1).value
                if val_id is None or str(val_id).strip() == "":
                    continue
                try:
                    id_actual = int(float(val_id))
                except (ValueError, TypeError):
                    continue

                if id_actual == producto.id:
                    ws.cell(row=row_idx, column=2, value=producto.nombre)
                    ws.cell(row=row_idx, column=3, value=producto.categoria)
                    ws.cell(row=row_idx, column=4, value=producto.precio)
                    ws.cell(row=row_idx, column=5, value=producto.descripcion)
                    self._formatear_fila_datos(ws, row_idx, es_moneda_col=4)
                    encontrado = True
                    break

            if not encontrado:
                wb.close()
                self.ultimo_error = f"No se encontró ningún producto con ID {producto.id}."
                return False

            self._guardar_workbook_atomico(wb)
            wb.close()
            return True

        except PermissionError as exc:
            self.ultimo_error = str(exc)
            logger.error("PermissionError al actualizar producto: %s", exc)
            return False
        except Exception as exc:
            self.ultimo_error = f"Error al actualizar el producto en Excel: {exc}"
            logger.error("Error al actualizar producto: %s", exc)
            return False

    def eliminar_producto(self, id_producto: int) -> bool:
        """
        Elimina un producto de la hoja 'Menu' según su ID.

        Args:
            id_producto (int): ID del producto a eliminar.

        Returns:
            bool: True si se eliminó exitosamente, False si no existe o hubo error.
        """
        self.ultimo_error = None
        try:
            id_buscado = int(id_producto)
        except (ValueError, TypeError):
            self.ultimo_error = "El ID del producto a eliminar no es válido."
            return False

        try:
            wb = self._cargar_workbook()
            ws = wb[self.HOJA_MENU]
            fila_a_borrar: Optional[int] = None

            for row_idx in range(2, ws.max_row + 1):
                val_id = ws.cell(row=row_idx, column=1).value
                if val_id is None or str(val_id).strip() == "":
                    continue
                try:
                    if int(float(val_id)) == id_buscado:
                        fila_a_borrar = row_idx
                        break
                except (ValueError, TypeError):
                    continue

            if fila_a_borrar is None:
                wb.close()
                self.ultimo_error = f"No se encontró el producto con ID {id_buscado}."
                return False

            ws.delete_rows(fila_a_borrar, 1)
            self._guardar_workbook_atomico(wb)
            wb.close()
            return True

        except PermissionError as exc:
            self.ultimo_error = str(exc)
            logger.error("PermissionError al eliminar producto: %s", exc)
            return False
        except Exception as exc:
            self.ultimo_error = f"Error al eliminar el producto en Excel: {exc}"
            logger.error("Error al eliminar producto: %s", exc)
            return False

    def actualizar_precios_porcentaje(self, categoria: str, porcentaje: float) -> int:
        """
        Aplica un aumento (o descuento) porcentual masivo a todos los productos
        de una categoría específica (o a todas si se indica 'Todas').

        Args:
            categoria (str): Nombre de la categoría o 'Todas' / 'Todas las categorías'.
            porcentaje (float): Porcentaje a aplicar (ej. 15.0 para +15%).

        Returns:
            int: Cantidad de productos cuyos precios fueron actualizados.
        """
        self.ultimo_error = None
        try:
            pct = float(porcentaje)
        except (ValueError, TypeError):
            self.ultimo_error = "El porcentaje ingresado debe ser un número válido."
            return 0

        if pct == 0:
            self.ultimo_error = "El porcentaje de actualización no puede ser 0%."
            return 0

        if pct <= -100:
            self.ultimo_error = "El porcentaje no puede reducir el precio a cero o negativo."
            return 0

        cat_limpia = str(categoria).strip().lower()
        aplicar_a_todas = cat_limpia in (
            "todas",
            "todas las categorías",
            "todas las categorias",
            "*",
            "all",
        )

        try:
            wb = self._cargar_workbook()
            ws = wb[self.HOJA_MENU]
            afectados = 0

            for row_idx in range(2, ws.max_row + 1):
                val_id = ws.cell(row=row_idx, column=1).value
                val_cat = ws.cell(row=row_idx, column=3).value
                val_precio = ws.cell(row=row_idx, column=4).value

                if val_id is None or val_precio is None:
                    continue

                cat_fila = str(val_cat or "").strip().lower()
                if aplicar_a_todas or cat_fila == cat_limpia:
                    try:
                        precio_actual = float(val_precio)
                        nuevo_precio = round(precio_actual * (1.0 + (pct / 100.0)), 2)
                        if nuevo_precio > 0:
                            ws.cell(row=row_idx, column=4, value=nuevo_precio)
                            ws.cell(row=row_idx, column=4).number_format = "$ #,##0.00"
                            afectados += 1
                    except (ValueError, TypeError):
                        continue

            if afectados > 0:
                self._guardar_workbook_atomico(wb)

            wb.close()
            return afectados

        except PermissionError as exc:
            self.ultimo_error = str(exc)
            logger.error("PermissionError al actualizar precios masivamente: %s", exc)
            return 0
        except Exception as exc:
            self.ultimo_error = f"Error al actualizar precios por porcentaje: {exc}"
            logger.error("Error al actualizar precios masivamente: %s", exc)
            return 0

    # =========================================================================
    # MÉTODOS OBLIGATORIOS DE GESTIÓN DE VENTAS Y CAJA (HOJA 'Ventas')
    # =========================================================================

    def registrar_venta(self, venta: Venta) -> bool:
        """
        Registra una nueva operación de venta en la hoja 'Ventas'.
        Asigna automáticamente el ID incremental si venta.id <= 0.

        Args:
            venta (Venta): Instancia validada de Venta a persistir.

        Returns:
            bool: True si se registró correctamente, False en caso de error.
        """
        self.ultimo_error = None
        if not isinstance(venta, Venta):
            self.ultimo_error = "El objeto proporcionado no es una instancia válida de Venta."
            return False

        try:
            wb = self._cargar_workbook()
            ws = wb[self.HOJA_VENTAS]

            ids_existentes: List[int] = []
            for row in ws.iter_rows(min_row=2, max_col=1, values_only=True):
                if row and row[0] is not None and str(row[0]).strip() != "":
                    try:
                        ids_existentes.append(int(float(row[0])))
                    except (ValueError, TypeError):
                        pass

            if venta.id <= 0 or venta.id in ids_existentes:
                venta.id = (max(ids_existentes) + 1) if ids_existentes else 1

            ws.append(venta.to_excel_row())
            self._formatear_fila_datos(ws, ws.max_row, es_moneda_col=4)

            self._guardar_workbook_atomico(wb)
            wb.close()
            return True

        except PermissionError as exc:
            self.ultimo_error = str(exc)
            logger.error("PermissionError al registrar venta: %s", exc)
            return False
        except Exception as exc:
            self.ultimo_error = f"Error al registrar la venta en Excel: {exc}"
            logger.error("Error al registrar venta: %s", exc)
            return False

    def obtener_ventas_diarias(self, fecha: str = "") -> List[Venta]:
        """
        Obtiene todas las ventas registradas correspondientes a una fecha específica.

        Args:
            fecha (str): Fecha a consultar en formato 'YYYY-MM-DD' (o prefijo de fecha).
                         Si se envía vacío, toma la fecha del día actual.

        Returns:
            List[Venta]: Lista de ventas registradas en esa fecha.
        """
        self.ultimo_error = None
        fecha_filtro = fecha.strip()[:10] if fecha and str(fecha).strip() else datetime.now().strftime("%Y-%m-%d")
        ventas: List[Venta] = []

        try:
            wb = self._cargar_workbook()
            if self.HOJA_VENTAS not in wb.sheetnames:
                wb.close()
                return []

            ws = wb[self.HOJA_VENTAS]
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row or all(celda is None or str(celda).strip() == "" for celda in row):
                    continue
                try:
                    venta = Venta(
                        id=row[0],
                        fecha_hora=row[1],
                        detalle=row[2],
                        total=row[3],
                        medio_pago=row[4] if len(row) > 4 and row[4] else "Efectivo",
                        tipo_entrega=row[5] if len(row) > 5 and row[5] else "Mostrador",
                    )
                    if venta.fecha == fecha_filtro:
                        ventas.append(venta)
                except (ValueError, TypeError) as err:
                    logger.warning("Fila de venta ignorada por formato inválido %s: %s", row, err)

            wb.close()
            ventas.sort(key=lambda v: v.id, reverse=True)
            return ventas

        except PermissionError as exc:
            self.ultimo_error = (
                "No se pudo leer las ventas porque el archivo Excel está bloqueado."
            )
            logger.error("PermissionError al obtener ventas diarias: %s", exc)
            return []
        except Exception as exc:
            self.ultimo_error = f"Error al leer ventas diarias: {exc}"
            logger.error("Error inesperado al obtener ventas diarias: %s", exc)
            return []

    # =========================================================================
    # MÉTODOS AUXILIARES Y DE APOYO A LA INTERFAZ
    # =========================================================================

    def obtener_categorias_existentes(self) -> List[str]:
        """Retorna la lista ordenada de categorías únicas presentes en el menú."""
        productos = self.obtener_productos()
        categorias = sorted({p.categoria for p in productos if p.categoria})
        return categorias

    def calcular_resumen_diario(self, fecha: str = "") -> Dict[str, Any]:
        """
        Calcula los totales recaudados en el día discriminados por medio de pago
        y modalidad de entrega.
        """
        ventas = self.obtener_ventas_diarias(fecha)
        total_general = sum(v.total for v in ventas)
        total_efectivo = sum(v.total for v in ventas if v.medio_pago == "Efectivo")
        total_transferencia = sum(v.total for v in ventas if v.medio_pago == "Transferencia/MP")
        cant_mostrador = sum(1 for v in ventas if v.tipo_entrega == "Mostrador")
        cant_delivery = sum(1 for v in ventas if v.tipo_entrega == "Delivery")

        return {
            "cantidad_ventas": len(ventas),
            "total_general": round(total_general, 2),
            "total_efectivo": round(total_efectivo, 2),
            "total_transferencia": round(total_transferencia, 2),
            "cant_mostrador": cant_mostrador,
            "cant_delivery": cant_delivery,
        }

    def sembrar_datos_ejemplo_si_vacio(self) -> int:
        """
        Carga un conjunto inicial de platos típicos de rotisería si la hoja 'Menu'
        se encuentra vacía, facilitando la prueba inmediata del sistema por QA.

        Returns:
            int: Cantidad de productos iniciales insertados.
        """
        productos_actuales = self.obtener_productos()
        if productos_actuales:
            return 0

        productos_semilla = [
            Producto(
                id=1,
                nombre="Pizza Napolitana Especial (8 Porc.)",
                categoria="Pizzas",
                precio=11500.0,
                descripcion="Salsa casera, abundante muzzarella, jamón cocido, rodajas de tomate fresco, ajo y aceitunas.",
            ),
            Producto(
                id=2,
                nombre="Docena de Empanadas Surtidas",
                categoria="Empanadas",
                precio=13800.0,
                descripcion="Carne cortada a cuchillo, pollo, jamón y queso o humita. Al horno o fritas a elección.",
            ),
            Producto(
                id=3,
                nombre="Milanesa a la Napolitana c/ Fritas (Para 2)",
                categoria="Minutas y Al Plato",
                precio=15900.0,
                descripcion="Milanesa de ternera XL con salsa fileto, jamón, muzzarella gratinada y porción grande de papas.",
            ),
            Producto(
                id=4,
                nombre="Promo 2 Burgers Doble Cheddar + Papas",
                categoria="Combos",
                precio=16500.0,
                descripcion="2 Hamburguesas dobles de 220g en pan de papa con cuádruple cheddar, panceta crocante y fritas.",
            ),
            Producto(
                id=5,
                nombre="Pollo al Spiedo Entero con Papas Fritas",
                categoria="Pollo al Spiedo y Parrilla",
                precio=18200.0,
                descripcion="Pollo dorado al spiedo con chimichurri casero, limón y bandeja familiar de papas fritas.",
            ),
            Producto(
                id=6,
                nombre="Sándwich de Lomito Completo con Fritas",
                categoria="Sándwiches y Lomitos",
                precio=12400.0,
                descripcion="Bife de lomo tiernizado en pan francés tostado con jamón, queso, huevo a la plancha, lechuga y tomate.",
            ),
        ]

        insertados = 0
        for prod in productos_semilla:
            if self.guardar_producto(prod):
                insertados += 1
        return insertados
