"""
Servicio de persistencia local en Excel ('data/datos_rotiseria.xlsx').
Gestiona de forma atómica y segura las hojas 'Menu' y 'Ventas' combinando
openpyxl (escritura atómica estilizada) y pandas (procesamiento tabular y arqueo).
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
import pandas as pd

from models.producto import Producto
from models.venta import Venta

logger = logging.getLogger(__name__)


class ExcelManager:
    """
    Gestor de persistencia local sobre archivo Excel (.xlsx).
    Garantiza la existencia del archivo, el estilizado profesional de cabeceras,
    la escritura atómica mediante archivo temporal (.tmp.xlsx) y el manejo defensivo
    de bloqueos (PermissionError cuando el archivo está abierto en Excel/Calc).
    """

    HOJA_MENU: str = "Menu"
    HOJA_VENTAS: str = "Ventas"
    HOJA_ARQUEOS: str = "Arqueos"

    ENCABEZADOS_MENU: List[str] = ["ID", "Nombre", "Categoria", "Precio", "Descripcion"]
    ANCHOS_MENU: List[int] = [10, 32, 22, 16, 48]
    ENCABEZADOS_VENTAS: List[str] = [
        "ID",
        "Fecha_Hora",
        "Detalle",
        "Total",
        "Medio_Pago",
        "Monto_Efectivo",
        "Monto_Transferencia",
        "Tipo_Entrega",
    ]
    ANCHOS_VENTAS: List[int] = [10, 22, 45, 16, 28, 18, 20, 18]
    ENCABEZADOS_ARQUEOS: List[str] = [
        "ID_Cierre",
        "Fecha_Hora_Cierre",
        "Fecha_Operativa",
        "Cant_Pedidos",
        "Mostrador",
        "Delivery",
        "Total_Efectivo",
        "Total_Transferencia",
        "Total_Recaudado",
    ]

    MENSAJE_ARCHIVO_ABIERTO: str = (
        "El archivo datos_rotiseria.xlsx está abierto. Por favor, ciérrelo para guardar los cambios"
    )

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
            raise PermissionError(self.MENSAJE_ARCHIVO_ABIERTO)

        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r+b"):
                    pass
            except PermissionError as exc:
                raise PermissionError(self.MENSAJE_ARCHIVO_ABIERTO) from exc

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
        temporal (.tmp.xlsx) en el mismo directorio y luego reemplazando el archivo destino.
        Esto evita pérdida o corrupción de datos ante cierres inesperados o cortes de energía.
        """
        self._verificar_bloqueo_archivo()
        directorio = os.path.dirname(self.filepath)
        fd, temp_path = tempfile.mkstemp(
            suffix=".tmp.xlsx", prefix=".rotiseria_", dir=directorio
        )
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
            raise PermissionError(self.MENSAJE_ARCHIVO_ABIERTO) from exc
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
                ws_menu = wb.active
                ws_menu.title = self.HOJA_MENU
                self._estilizar_hoja(ws_menu, self.ENCABEZADOS_MENU, [10, 32, 22, 16, 48])

                ws_ventas = wb.create_sheet(title=self.HOJA_VENTAS)
                self._estilizar_hoja(ws_ventas, self.ENCABEZADOS_VENTAS, self.ANCHOS_VENTAS)

                self._guardar_workbook_atomico(wb)
                wb.close()
                return

            wb = openpyxl.load_workbook(self.filepath)
            modificado = False

            if self.HOJA_MENU not in wb.sheetnames:
                ws_menu = wb.create_sheet(title=self.HOJA_MENU, index=0)
                self._estilizar_hoja(ws_menu, self.ENCABEZADOS_MENU, [10, 32, 22, 16, 48])
                modificado = True

            if self.HOJA_VENTAS not in wb.sheetnames:
                ws_ventas = wb.create_sheet(title=self.HOJA_VENTAS)
                self._estilizar_hoja(ws_ventas, self.ENCABEZADOS_VENTAS, self.ANCHOS_VENTAS)
                modificado = True
            else:
                ws_ventas = wb[self.HOJA_VENTAS]
                col_headers = [
                    ws_ventas.cell(row=1, column=c).value
                    for c in range(1, ws_ventas.max_column + 1)
                ]
                if "Monto_Efectivo" not in col_headers:
                    filas_existentes = []
                    for row in ws_ventas.iter_rows(min_row=2, values_only=True):
                        if row and any(c is not None for c in row):
                            filas_existentes.append(row)

                    ws_ventas.delete_rows(1, ws_ventas.max_row)
                    self._estilizar_hoja(ws_ventas, self.ENCABEZADOS_VENTAS, self.ANCHOS_VENTAS)
                    for f in filas_existentes:
                        id_v = f[0]
                        fh = f[1]
                        det = f[2]
                        tot = f[3]
                        mp = f[4] if len(f) > 4 and f[4] else "Efectivo"
                        te = f[5] if len(f) > 5 and f[5] else "Mostrador"
                        try:
                            tot_f = float(tot) if tot is not None else 0.0
                        except (ValueError, TypeError):
                            tot_f = 0.0
                        m_ef = tot_f if "efectivo" in str(mp).lower() else 0.0
                        m_tr = (
                            tot_f
                            if ("transf" in str(mp).lower() or "mp" in str(mp).lower())
                            else 0.0
                        )
                        ws_ventas.append([id_v, fh, det, tot, mp, m_ef, m_tr, te])
                        self._formatear_fila_datos(ws_ventas, ws_ventas.max_row, es_moneda_col=4)
                        for col_m in (6, 7):
                            celda = ws_ventas.cell(row=ws_ventas.max_row, column=col_m)
                            celda.number_format = "$ #,##0.00"
                            celda.alignment = Alignment(horizontal="right", vertical="center")
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
    # MÉTODOS DE GESTIÓN DE PRODUCTOS (HOJA 'Menu')
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
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
            logger.error("PermissionError al obtener productos: %s", exc)
            return []
        except Exception as exc:
            self.ultimo_error = f"Error al leer productos del archivo Excel: {exc}"
            logger.error("Error inesperado al obtener productos: %s", exc)
            return []

    def guardar_producto(self, producto: Producto) -> bool:
        """
        Guarda un nuevo producto en la hoja 'Menu'.
        Si el producto tiene ID 0 (o un ID ya existente), se le asigna
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
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
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
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
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
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
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
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
            logger.error("PermissionError al actualizar precios masivamente: %s", exc)
            return 0
        except Exception as exc:
            self.ultimo_error = f"Error al actualizar precios por porcentaje: {exc}"
            logger.error("Error al actualizar precios masivamente: %s", exc)
            return 0

    # =========================================================================
    # MÉTODOS DE GESTIÓN DE VENTAS Y CAJA (HOJA 'Ventas')
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
            for col_moneda in (6, 7):
                celda_m = ws.cell(row=ws.max_row, column=col_moneda)
                celda_m.number_format = "$ #,##0.00"
                celda_m.alignment = Alignment(horizontal="right", vertical="center")

            self._guardar_workbook_atomico(wb)
            wb.close()
            return True

        except PermissionError as exc:
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
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
        fecha_filtro = (
            fecha.strip()[:10]
            if fecha and str(fecha).strip()
            else datetime.now().strftime("%Y-%m-%d")
        )
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
                    # Soporta formato nuevo (8 columnas con desglose) y formato previo (6 columnas)
                    if len(row) >= 8:
                        venta = Venta(
                            id=row[0],
                            fecha_hora=row[1],
                            detalle=row[2],
                            total=row[3],
                            medio_pago=row[4] if row[4] else "Efectivo",
                            monto_efectivo=row[5],
                            monto_transferencia=row[6],
                            tipo_entrega=row[7] if row[7] else "Mostrador",
                        )
                    else:
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
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
            logger.error("PermissionError al obtener ventas diarias: %s", exc)
            return []
        except Exception as exc:
            self.ultimo_error = f"Error al leer ventas diarias: {exc}"
            logger.error("Error inesperado al obtener ventas diarias: %s", exc)
            return []

    # =========================================================================
    # MÉTODOS ANALÍTICOS (PANDAS) Y APOYO A LA INTERFAZ
    # =========================================================================

    def obtener_dataframe_menu(self) -> pd.DataFrame:
        """Retorna el catálogo actual de productos como un DataFrame de Pandas."""
        productos = self.obtener_productos()
        if not productos:
            return pd.DataFrame(columns=["id", "nombre", "categoria", "precio", "descripcion"])
        return pd.DataFrame([p.to_dict() for p in productos])

    def obtener_dataframe_ventas(self, fecha: str = "") -> pd.DataFrame:
        """Retorna las ventas de la fecha indicada como un DataFrame de Pandas."""
        ventas = self.obtener_ventas_diarias(fecha)
        if not ventas:
            return pd.DataFrame(
                columns=[
                    "id",
                    "fecha_hora",
                    "detalle",
                    "total",
                    "medio_pago",
                    "monto_efectivo",
                    "monto_transferencia",
                    "tipo_entrega",
                ]
            )
        return pd.DataFrame([v.to_dict() for v in ventas])

    def obtener_categorias_existentes(self) -> List[str]:
        """Retorna la lista ordenada de categorías únicas presentes en el menú."""
        productos = self.obtener_productos()
        categorias = sorted({p.categoria for p in productos if p.categoria})
        return categorias

    def calcular_resumen_diario(self, fecha: str = "") -> Dict[str, Any]:
        """
        Calcula los totales recaudados en el día discriminados por medio de pago
        (incluyendo desglose de ventas mixtas) y modalidad de entrega
        empleando Pandas para agregación vectorial.
        """
        df = self.obtener_dataframe_ventas(fecha)
        if df.empty:
            return {
                "cantidad_ventas": 0,
                "total_general": 0.0,
                "total_efectivo": 0.0,
                "total_transferencia": 0.0,
                "cant_mostrador": 0,
                "cant_delivery": 0,
                "cant_mixto": 0,
            }

        total_general = float(df["total"].sum())
        # El efectivo y transferencia consideran ventas puras y la porción correspondiente de ventas mixtas
        total_efectivo = float(df["monto_efectivo"].sum())
        total_transferencia = float(df["monto_transferencia"].sum())
        cant_mostrador = int((df["tipo_entrega"] == "Mostrador").sum())
        cant_delivery = int((df["tipo_entrega"] == "Delivery").sum())
        cant_mixto = int((df["medio_pago"] == Venta.MEDIO_MIXTO).sum())

        return {
            "cantidad_ventas": int(len(df)),
            "total_general": round(total_general, 2),
            "total_efectivo": round(total_efectivo, 2),
            "total_transferencia": round(total_transferencia, 2),
            "cant_mostrador": cant_mostrador,
            "cant_delivery": cant_delivery,
            "cant_mixto": cant_mixto,
        }

    def registrar_cierre_caja(self, fecha: str = "") -> bool:
        """
        Guarda un registro de Cierre de Caja / Arqueo Diario en la hoja 'Arqueos'
        del archivo Excel de forma atómica.

        Args:
            fecha (str): Fecha operativa del arqueo ('YYYY-MM-DD').

        Returns:
            bool: True si el arqueo se guardó exitosamente en Excel, False en caso contrario.
        """
        self.ultimo_error = None
        fecha_operativa = (
            fecha.strip()[:10]
            if fecha and str(fecha).strip()
            else datetime.now().strftime("%Y-%m-%d")
        )
        resumen = self.calcular_resumen_diario(fecha_operativa)

        try:
            wb = self._cargar_workbook()
            if self.HOJA_ARQUEOS not in wb.sheetnames:
                ws_arq = wb.create_sheet(title=self.HOJA_ARQUEOS)
                self._estilizar_hoja(
                    ws_arq,
                    self.ENCABEZADOS_ARQUEOS,
                    [12, 22, 18, 16, 14, 14, 18, 22, 18],
                )
            else:
                ws_arq = wb[self.HOJA_ARQUEOS]

            ids_existentes: List[int] = []
            for row in ws_arq.iter_rows(min_row=2, max_col=1, values_only=True):
                if row and row[0] is not None and str(row[0]).strip() != "":
                    try:
                        ids_existentes.append(int(float(row[0])))
                    except (ValueError, TypeError):
                        pass

            nuevo_id = (max(ids_existentes) + 1) if ids_existentes else 1
            ahora_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            fila_arqueo = [
                nuevo_id,
                ahora_str,
                fecha_operativa,
                resumen["cantidad_ventas"],
                resumen["cant_mostrador"],
                resumen["cant_delivery"],
                resumen["total_efectivo"],
                resumen["total_transferencia"],
                resumen["total_general"],
            ]
            ws_arq.append(fila_arqueo)
            self._formatear_fila_datos(ws_arq, ws_arq.max_row, es_moneda_col=9)
            for col_moneda in (7, 8, 9):
                celda_m = ws_arq.cell(row=ws_arq.max_row, column=col_moneda)
                celda_m.number_format = "$ #,##0.00"
                celda_m.alignment = Alignment(horizontal="right", vertical="center")

            self._guardar_workbook_atomico(wb)
            wb.close()
            return True

        except PermissionError as exc:
            self.ultimo_error = self.MENSAJE_ARCHIVO_ABIERTO
            logger.error("PermissionError al registrar cierre de caja: %s", exc)
            return False
        except Exception as exc:
            self.ultimo_error = f"Error al guardar el arqueo de caja en Excel: {exc}"
            logger.error("Error al registrar cierre de caja: %s", exc)
            return False

    CATALOGO_SEMILLA_ROTISERIA: List[Dict[str, Any]] = [
        # --- PIZZAS (6) ---
        {
            "nombre": "Pizza Muzzarella Clásica",
            "categoria": "Pizzas",
            "precio": 10500.0,
            "descripcion": "Salsa artesanal de tomates, abundante muzzarella de primera calidad, orégano y aceitunas verdes.",
        },
        {
            "nombre": "Pizza Fugazzeta Rellena",
            "categoria": "Pizzas",
            "precio": 13000.0,
            "descripcion": "Doble masa rellena con jamón cocido y queso fundido, cubierta con cebollas caramelizadas al oliva.",
        },
        {
            "nombre": "Pizza Especial (Jamón y Morrones)",
            "categoria": "Pizzas",
            "precio": 11500.0,
            "descripcion": "Muzzarella, jamón cocido seleccionado, morrones asados dulces y aceitunas descarozadas.",
        },
        {
            "nombre": "Pizza Napolitana con Ajo",
            "categoria": "Pizzas",
            "precio": 11800.0,
            "descripcion": "Muzzarella, rodajas finas de tomate natural, provenzal fresca con ajo suave y aceitunas negras.",
        },
        {
            "nombre": "Pizza Calabresa Picantita",
            "categoria": "Pizzas",
            "precio": 12200.0,
            "descripcion": "Muzzarella, longaniza artesanal estacionada en rodajas, ají molido y aceite de oliva.",
        },
        {
            "nombre": "Pizza Cuatro Quesos",
            "categoria": "Pizzas",
            "precio": 13500.0,
            "descripcion": "Muzzarella, queso azul patagónico, provolone curado y parmesano gratinado al horno.",
        },
        # --- EMPANADAS (6) ---
        {
            "nombre": "Docena Carne Suave Tradicional",
            "categoria": "Empanadas",
            "precio": 13500.0,
            "descripcion": "Carne picada de ternera, cebolla rehogada, huevo duro y especias criollas al horno.",
        },
        {
            "nombre": "Docena Jamón y Queso",
            "categoria": "Empanadas",
            "precio": 13500.0,
            "descripcion": "Abundante jamón cocido en cubos y muzzarella cremosa de fundido suave.",
        },
        {
            "nombre": "Docena Pollo al Verdeo",
            "categoria": "Empanadas",
            "precio": 13800.0,
            "descripcion": "Pechuga desmenuzada marinada con crema suave de cebollas de verdeo y vino blanco.",
        },
        {
            "nombre": "Docena Carne Cortada a Cuchillo",
            "categoria": "Empanadas",
            "precio": 14200.0,
            "descripcion": "Lomo tierno cortado a cuchillo con cebolla de verdeo, pimentón dulce y comino.",
        },
        {
            "nombre": "Docena Humita Cremosa del Norte",
            "categoria": "Empanadas",
            "precio": 13000.0,
            "descripcion": "Maíz dulce amarillo cremoso con queso mantecoso y toque de nuez moscada.",
        },
        {
            "nombre": "Docena Acelga y Ricota al Horno",
            "categoria": "Empanadas",
            "precio": 12800.0,
            "descripcion": "Acelga fresca de quinta salteada con ricota casera y queso sardo rallado.",
        },
        # --- HAMBURGUESAS (4) ---
        {
            "nombre": "Promo 2 Burgers Doble Cheddar + Papas",
            "categoria": "Hamburguesas",
            "precio": 16500.0,
            "descripcion": "2 hamburguesas con doble medallón de 220g en pan brioche, 4 fetas cheddar, panceta crocante y papas.",
        },
        {
            "nombre": "Burger Bacon Crispy & BBQ",
            "categoria": "Hamburguesas",
            "precio": 11500.0,
            "descripcion": "Medallón casero de 180g, doble panceta crocante, cebolla crispy y salsa barbacoa ahumada.",
        },
        {
            "nombre": "Burger Blue Cheese & Malbec",
            "categoria": "Hamburguesas",
            "precio": 12000.0,
            "descripcion": "Medallón 180g, queso azul fundido, cebollas caramelizadas al malbec y rúcula fresca.",
        },
        {
            "nombre": "Burger Clásica Completa c/ Fritas",
            "categoria": "Hamburguesas",
            "precio": 9800.0,
            "descripcion": "Medallón de ternera 150g, jamón, queso, huevo a la plancha, lechuga, tomate y papas fritas.",
        },
        # --- SÁNDWICHES Y LOMITOS (4) ---
        {
            "nombre": "Sándwich de Milanesa Completo",
            "categoria": "Sándwiches y Lomitos",
            "precio": 12000.0,
            "descripcion": "Milanesa de ternera XL en pan francés crocante con jamón, queso, huevo frito, lechuga y tomate.",
        },
        {
            "nombre": "Lomito Completo Especial",
            "categoria": "Sándwiches y Lomitos",
            "precio": 14500.0,
            "descripcion": "Bife de lomo tiernizado a la plancha con jamón cocido, queso, huevo frito y papas fritas.",
        },
        {
            "nombre": "Tostado Carlitos Especial",
            "categoria": "Sándwiches y Lomitos",
            "precio": 8500.0,
            "descripcion": "Pan de miga triple tostado con manteca dorada, doble jamón, queso derretido y salsa tártara.",
        },
        {
            "nombre": "Sándwich de Bondiola Braseada",
            "categoria": "Sándwiches y Lomitos",
            "precio": 13200.0,
            "descripcion": "Bondiola desmenuzada cocinada a fuego lento con barbacoa y ensalada coleslaw en pan de papa.",
        },
        # --- MINUTAS Y AL PLATO (6) ---
        {
            "nombre": "Milanesa a la Napolitana c/ Fritas",
            "categoria": "Minutas y Al Plato",
            "precio": 15900.0,
            "descripcion": "Milanesa de ternera gigante con salsa fileto casera, jamón cocido, muzzarella gratinada y papas fritas.",
        },
        {
            "nombre": "Suprema Suiza con Puré Mixto",
            "categoria": "Minutas y Al Plato",
            "precio": 14800.0,
            "descripcion": "Pechuga de pollo gratinada con salsa bechamel, queso provolone fundido y puré de papas y calabaza.",
        },
        {
            "nombre": "Tortilla de Papas y Cebolla Babé",
            "categoria": "Minutas y Al Plato",
            "precio": 9200.0,
            "descripcion": "Tortilla española clásica con papas doradas, cebollas caramelizadas y centro cremoso jugoso.",
        },
        {
            "nombre": "Matambre a la Pizza con Papas Cuña",
            "categoria": "Minutas y Al Plato",
            "precio": 17500.0,
            "descripcion": "Matambre vacuno tiernizado al horno con salsa de tomate, muzzarella derretida y orégano.",
        },
        {
            "nombre": "Bife de Chorizo a Caballo c/ Fritas",
            "categoria": "Minutas y Al Plato",
            "precio": 18500.0,
            "descripcion": "Corte premium de 400g a la chapa coronado con dos huevos fritos y guarnición de fritas.",
        },
        {
            "nombre": "Porción de Rabas a la Romana",
            "categoria": "Minutas y Al Plato",
            "precio": 14000.0,
            "descripcion": "Aros de calamar crocantes rebozados en harina y pimentón, servidos con limón y salsa tártara.",
        },
        # --- POLLO AL SPIEDO Y PARRILLA (3) ---
        {
            "nombre": "Pollo al Spiedo Entero con Papas",
            "categoria": "Pollo al Spiedo y Parrilla",
            "precio": 18200.0,
            "descripcion": "Pollo asado al spiedo dorado y jugoso con chimichurri casero, limón y bandeja familiar de papas.",
        },
        {
            "nombre": "Medio Pollo al Spiedo c/ Ensalada Rusa",
            "categoria": "Pollo al Spiedo y Parrilla",
            "precio": 10500.0,
            "descripcion": "Medio pollo dorado al spiedo acompañado de ensalada rusa artesanal con mayonesa suave.",
        },
        {
            "nombre": "Asado de Tira al Horno con Papas",
            "categoria": "Pollo al Spiedo y Parrilla",
            "precio": 19000.0,
            "descripcion": "Costillar vacuno tiernizado a baja temperatura con papas rústicas al romero y sal marina.",
        },
        # --- TARTAS Y CALZONES (2) ---
        {
            "nombre": "Tarta Pascualina de Acelga y Huevo",
            "categoria": "Tartas y Calzones",
            "precio": 8900.0,
            "descripcion": "Masa hojaldrada casera rellena con acelga salteada, queso cremoso y huevos enteros al horno.",
        },
        {
            "nombre": "Calzone Napolitano Gigante",
            "categoria": "Tartas y Calzones",
            "precio": 12800.0,
            "descripcion": "Masa de pizza doblada rellena con jamón cocido, ricota, muzzarella, tomates frescos y albahaca.",
        },
        # --- GUARNICIONES (4) ---
        {
            "nombre": "Porción de Papas Fritas Cheddar y Bacon",
            "categoria": "Guarniciones",
            "precio": 7500.0,
            "descripcion": "Papas bastón crujientes con abundante salsa cheddar fundida, panceta crocante y ciboulette.",
        },
        {
            "nombre": "Papas Fritas Tradicionales en Cono XL",
            "categoria": "Guarniciones",
            "precio": 5500.0,
            "descripcion": "Bandeja grande de papas fritas clásicas recién hechas, crocantes por fuera y tiernas por dentro.",
        },
        {
            "nombre": "Ensalada Mixta Familiar",
            "categoria": "Guarniciones",
            "precio": 4800.0,
            "descripcion": "Lechuga capuchina crujiente, tomates redondos maduros y cebolla morada fresca con oliva.",
        },
        {
            "nombre": "Puré de Papas Casero a la Manteca",
            "categoria": "Guarniciones",
            "precio": 4500.0,
            "descripcion": "Papas seleccionadas pisadas a mano con crema de leche fresca, manteca y nuez moscada.",
        },
        # --- BEBIDAS (5) ---
        {
            "nombre": "Gaseosa 1.5L Línea Coca-Cola",
            "categoria": "Bebidas",
            "precio": 3500.0,
            "descripcion": "Botella de 1.5 litros bien fría (Coca-Cola, Coca Zero, Sprite o Fanta).",
        },
        {
            "nombre": "Cerveza Quilmes Clásica 1L",
            "categoria": "Bebidas",
            "precio": 4200.0,
            "descripcion": "Cerveza rubia tradicional argentina en botella de vidrio retornable de 1 litro helada.",
        },
        {
            "nombre": "Cerveza IPA Artesanal 500ml",
            "categoria": "Bebidas",
            "precio": 4800.0,
            "descripcion": "Cerveza artesanal de alta graduación lupulada con notas cítricas en lata de medio litro.",
        },
        {
            "nombre": "Agua Mineral sin Gas 500ml",
            "categoria": "Bebidas",
            "precio": 2000.0,
            "descripcion": "Agua pura de manantial embotellada de origen en presentación individual fresca.",
        },
        {
            "nombre": "Vino Malbec Selección 750ml",
            "categoria": "Bebidas",
            "precio": 6500.0,
            "descripcion": "Vino tinto varietal mendocino con paso por roble, ideal para acompañar carnes y empanadas.",
        },
        # --- POSTRES (2) ---
        {
            "nombre": "Flan Casero Mixto (Dulce y Crema)",
            "categoria": "Postres",
            "precio": 4500.0,
            "descripcion": "Flan tradicional de 8 huevos bañado en caramelo con dulce de leche repostero y crema chantilly.",
        },
        {
            "nombre": "Tiramisú Artesanal Italiano",
            "categoria": "Postres",
            "precio": 5200.0,
            "descripcion": "Capas de vainillas embebidas en café espresso y licor amaretto con suave crema mascarpone.",
        },
    ]

    def sembrar_datos_ejemplo_si_vacio(self, forzar: bool = False) -> int:
        """
        Carga el catálogo completo de demostración gastronómica (42 platos y bebidas)
        si la hoja 'Menu' tiene menos de 15 productos o si forzar=True.

        Returns:
            int: Cantidad de productos guardados en el menú.
        """
        productos_actuales = self.obtener_productos()
        if productos_actuales and len(productos_actuales) >= 15 and not forzar:
            return 0

        # Si se fuerza o hay pocos productos, sembrar el catálogo completo
        insertados = 0
        id_actual = 1
        for datos in self.CATALOGO_SEMILLA_ROTISERIA:
            prod = Producto(
                id=id_actual,
                nombre=datos["nombre"],
                categoria=datos["categoria"],
                precio=datos["precio"],
                descripcion=datos["descripcion"],
            )
            if self.guardar_producto(prod):
                insertados += 1
                id_actual += 1

        logger.info(
            "Catálogo gastronómico de demostración sembrado con éxito: %d productos.",
            insertados,
        )
        return insertados

    def poblar_catalogo_demostracion(self) -> int:
        """
        Sobrescribe o regenera la hoja 'Menu' con los 42 productos de muestra
        y asegura el guardado atómico en el archivo Excel.
        """
        wb = self._cargar_workbook()
        if self.HOJA_MENU in wb.sheetnames:
            del wb[self.HOJA_MENU]
        ws_menu = wb.create_sheet(title=self.HOJA_MENU, index=0)
        self._estilizar_hoja(ws_menu, self.ENCABEZADOS_MENU, self.ANCHOS_MENU)

        for idx, datos in enumerate(self.CATALOGO_SEMILLA_ROTISERIA, start=1):
            fila = idx + 1
            ws_menu.cell(row=fila, column=1, value=idx)
            ws_menu.cell(row=fila, column=2, value=datos["nombre"])
            ws_menu.cell(row=fila, column=3, value=datos["categoria"])
            ws_menu.cell(row=fila, column=4, value=float(datos["precio"]))
            ws_menu.cell(row=fila, column=5, value=datos["descripcion"])
            ws_menu.cell(row=fila, column=6, value=datos.get("stock", 0))
            self._formatear_fila_datos(ws_menu, fila, es_moneda_col=4)

        self._guardar_workbook_atomico(wb)
        return len(self.CATALOGO_SEMILLA_ROTISERIA)
