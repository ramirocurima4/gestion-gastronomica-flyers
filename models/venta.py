"""
Módulo de modelo de dominio para Ventas y Arqueo de Caja Diario.
Implementa encapsulamiento POO mediante propiedades (@property / @setter),
validaciones de medios de pago (incluyendo Pago Mixto Efectivo + Transferencia),
modalidades de entrega y montos positivos.
"""

from datetime import datetime
import math
from typing import Any, Dict, List, Optional, Tuple, Union


class Venta:
    """
    Representa una operación de venta registrada en la caja diaria de la rotisería.

    Atributos encapsulados (accesibles vía @property):
        id (int): Identificador único de la venta (0 si aún no fue persistida).
        fecha_hora (str): Fecha y hora en formato ISO legible ('YYYY-MM-DD HH:MM:SS').
        detalle (Union[str, List[str]]): Descripción o lista de ítems vendidos (no vacío).
        total (float): Monto total cobrado en pesos (estrictamente > 0).
        medio_pago (str): Medio de cobro ('Efectivo', 'Transferencia/MP' o 'Mixto (Efectivo + Transferencia)').
        monto_efectivo (float): Porción cobrada en efectivo (>= 0).
        monto_transferencia (float): Porción cobrada por transferencia/MP (>= 0).
        tipo_entrega (str): Modalidad de entrega ('Mostrador' o 'Delivery').
    """

    MEDIO_EFECTIVO: str = "Efectivo"
    MEDIO_TRANSFERENCIA: str = "Transferencia/MP"
    MEDIO_MIXTO: str = "Mixto (Efectivo + Transferencia)"

    MEDIOS_PAGO_VALIDOS: Tuple[str, ...] = (
        MEDIO_EFECTIVO,
        MEDIO_TRANSFERENCIA,
        MEDIO_MIXTO,
    )
    TIPOS_ENTREGA_VALIDOS: Tuple[str, ...] = ("Mostrador", "Delivery")

    def __init__(
        self,
        id: int,
        detalle: Union[str, List[str]],
        total: float,
        medio_pago: str = "Efectivo",
        tipo_entrega: str = "Mostrador",
        fecha_hora: Optional[str] = None,
        monto_efectivo: Optional[float] = None,
        monto_transferencia: Optional[float] = None,
    ) -> None:
        self._id: int = 0
        self._fecha_hora: str = ""
        self._detalle: Union[str, List[str]] = ""
        self._total: float = 0.0
        self._medio_pago: str = self.MEDIO_EFECTIVO
        self._monto_efectivo: float = 0.0
        self._monto_transferencia: float = 0.0
        self._tipo_entrega: str = "Mostrador"

        # Asignación a través de setters con validación defensiva
        self.id = id
        self.fecha_hora = fecha_hora  # type: ignore[assignment]
        self.detalle = detalle
        self.total = total
        self.tipo_entrega = tipo_entrega

        # Asignar medio de pago y desgloses
        self.establecer_medio_pago_y_desglose(
            medio_pago=medio_pago,
            monto_efectivo=monto_efectivo,
            monto_transferencia=monto_transferencia,
        )

    # =========================================================================
    # PROPIEDADES Y SETTERS (ENCAPSULAMIENTO POO)
    # =========================================================================

    @property
    def id(self) -> int:
        """Retorna el identificador único de la venta."""
        return self._id

    @id.setter
    def id(self, valor: Any) -> None:
        """Valida que el ID de la venta sea un número entero no negativo."""
        self._id = self._validar_id(valor)

    @property
    def fecha_hora(self) -> str:
        """Retorna la marca de tiempo de la venta ('YYYY-MM-DD HH:MM:SS')."""
        return self._fecha_hora

    @fecha_hora.setter
    def fecha_hora(self, valor: Optional[Any]) -> None:
        """Valida o genera el timestamp en formato ISO legible."""
        self._fecha_hora = self._validar_fecha_hora(valor)

    @property
    def detalle(self) -> Union[str, List[str]]:
        """Retorna el detalle de los productos vendidos."""
        return self._detalle

    @detalle.setter
    def detalle(self, valor: Union[str, List[str], Any]) -> None:
        """Valida que el detalle de la venta no sea nulo ni vacío."""
        self._detalle = self._validar_detalle(valor)

    @property
    def total(self) -> float:
        """Retorna el monto total cobrado en la operación."""
        return self._total

    @total.setter
    def total(self, valor: Any) -> None:
        """Valida que el monto total sea numérico y estrictamente mayor a 0."""
        self._total = self._validar_total(valor)

    @property
    def medio_pago(self) -> str:
        """Retorna el medio de pago utilizado."""
        return self._medio_pago

    @property
    def monto_efectivo(self) -> float:
        """Retorna el monto abonado en efectivo."""
        return self._monto_efectivo

    @property
    def monto_transferencia(self) -> float:
        """Retorna el monto abonado mediante transferencia o Mercado Pago."""
        return self._monto_transferencia

    @property
    def tipo_entrega(self) -> str:
        """Retorna la modalidad de entrega ('Mostrador' o 'Delivery')."""
        return self._tipo_entrega

    @tipo_entrega.setter
    def tipo_entrega(self, valor: Any) -> None:
        """Valida que la modalidad de entrega sea válida."""
        self._tipo_entrega = self._validar_tipo_entrega(valor)

    # =========================================================================
    # GESTIÓN Y VALIDACIÓN DE PAGO Y DESGLOSE MIXTO
    # =========================================================================

    def establecer_medio_pago_y_desglose(
        self,
        medio_pago: Any,
        monto_efectivo: Optional[Any] = None,
        monto_transferencia: Optional[Any] = None,
    ) -> None:
        """
        Configura el medio de pago validando defensivamente el desglose en efectivo
        y transferencia. Si el pago es 'Mixto (Efectivo + Transferencia)', verifica
        estrictamente que la suma de ambas partes coincida con el total de la venta.
        """
        normalizado = self._validar_medio_pago(medio_pago)
        self._medio_pago = normalizado

        if normalizado == self.MEDIO_EFECTIVO:
            self._monto_efectivo = self._total
            self._monto_transferencia = 0.0
        elif normalizado == self.MEDIO_TRANSFERENCIA:
            self._monto_efectivo = 0.0
            self._monto_transferencia = self._total
        else:  # MEDIO_MIXTO
            efectivo_val = (
                self._limpiar_numero_positivo_o_cero(monto_efectivo, "Monto Efectivo")
                if monto_efectivo is not None
                else 0.0
            )
            transf_val = (
                self._limpiar_numero_positivo_o_cero(monto_transferencia, "Monto Transferencia")
                if monto_transferencia is not None
                else 0.0
            )

            # Validar que la suma coincida con el total de la venta (tolerancia a float de 1 centavo)
            suma = round(efectivo_val + transf_val, 2)
            if abs(suma - self._total) > 0.01:
                raise ValueError(
                    f"En pago Mixto, la suma de Efectivo (${efectivo_val:,.0f}) y "
                    f"Transferencia (${transf_val:,.0f}) es ${suma:,.0f}, y debe coincidir "
                    f"exactamente con el Total Cobrado (${self._total:,.0f})."
                )

            self._monto_efectivo = round(efectivo_val, 2)
            self._monto_transferencia = round(transf_val, 2)

    @classmethod
    def _validar_medio_pago(cls, valor: Any) -> str:
        """Valida que el medio de pago sea uno de los permitidos por el negocio."""
        if valor is None:
            raise ValueError("El medio de pago es obligatorio.")
        texto = str(valor).strip()
        mapa = {
            "efectivo": cls.MEDIO_EFECTIVO,
            "transferencia/mp": cls.MEDIO_TRANSFERENCIA,
            "transferencia": cls.MEDIO_TRANSFERENCIA,
            "mercado pago": cls.MEDIO_TRANSFERENCIA,
            "mercadopago": cls.MEDIO_TRANSFERENCIA,
            "mp": cls.MEDIO_TRANSFERENCIA,
            "mixto": cls.MEDIO_MIXTO,
            "mixto (efectivo + transferencia)": cls.MEDIO_MIXTO,
            "mixto (efectivo + mp)": cls.MEDIO_MIXTO,
            "mixto (efectivo/transferencia)": cls.MEDIO_MIXTO,
            "efectivo + transferencia": cls.MEDIO_MIXTO,
            "efectivo y transferencia": cls.MEDIO_MIXTO,
        }
        normalizado = mapa.get(texto.lower(), texto)
        if normalizado not in cls.MEDIOS_PAGO_VALIDOS:
            raise ValueError(
                f"Medio de pago inválido: '{texto}'. "
                f"Valores permitidos: {', '.join(cls.MEDIOS_PAGO_VALIDOS)}."
            )
        return normalizado

    @staticmethod
    def _limpiar_numero_positivo_o_cero(valor: Any, nombre_campo: str) -> float:
        """Valida que un valor numérico sea mayor o igual a cero."""
        if isinstance(valor, bool) or valor is None:
            raise TypeError(f"El campo '{nombre_campo}' debe ser numérico.")
        if isinstance(valor, str):
            limpio = valor.replace("$", "").replace(" ", "").strip()
            if "," in limpio and "." in limpio:
                if limpio.rfind(",") > limpio.rfind("."):
                    limpio = limpio.replace(".", "").replace(",", ".")
                else:
                    limpio = limpio.replace(",", "")
            elif "," in limpio:
                limpio = limpio.replace(",", ".")
            valor = limpio
        try:
            num_float = float(valor)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"'{nombre_campo}' debe ser un número válido. Recibido: {valor!r}") from exc

        if math.isnan(num_float) or math.isinf(num_float):
            raise ValueError(f"'{nombre_campo}' no puede ser NaN ni infinito.")
        if num_float < 0:
            raise ValueError(f"'{nombre_campo}' no puede ser negativo.")
        return round(num_float, 2)

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN DEFENSIVA ADICIONALES
    # =========================================================================

    @staticmethod
    def _validar_id(valor: Any) -> int:
        """Valida que el ID de la venta sea un entero no negativo."""
        if valor is None or valor == "":
            return 0
        if isinstance(valor, bool):
            raise TypeError("El ID de la venta debe ser un número entero.")
        try:
            id_int = int(float(valor))
        except (ValueError, TypeError) as exc:
            raise TypeError(
                f"El ID de la venta debe ser un entero válido. Recibido: {valor!r}"
            ) from exc
        if id_int < 0:
            raise ValueError("El ID de la venta no puede ser negativo.")
        return id_int

    @staticmethod
    def _validar_fecha_hora(valor: Optional[Any]) -> str:
        """Valida o genera el timestamp en formato ISO legible 'YYYY-MM-DD HH:MM:SS'."""
        if valor is None or str(valor).strip() == "" or str(valor).strip().lower() == "nan":
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(valor, datetime):
            return valor.strftime("%Y-%m-%d %H:%M:%S")

        texto = str(valor).strip()
        texto_normalizado = texto.replace("T", " ")
        if len(texto_normalizado) == 10:
            try:
                datetime.strptime(texto_normalizado, "%Y-%m-%d")
                return f"{texto_normalizado} 00:00:00"
            except ValueError:
                pass
        return texto_normalizado

    @staticmethod
    def _validar_detalle(valor: Union[str, List[str], Any]) -> Union[str, List[str]]:
        """Valida que el detalle de la venta sea un string no vacío o una lista de ítems."""
        if valor is None or isinstance(valor, bool):
            raise ValueError("El detalle de la venta no puede ser nulo.")

        if isinstance(valor, list):
            items_limpios = [str(item).strip() for item in valor if str(item).strip()]
            if not items_limpios:
                raise ValueError("La lista de ítems del detalle no puede estar vacía.")
            return items_limpios

        texto = str(valor).strip()
        if not texto or texto.lower() == "nan":
            raise ValueError("El detalle de la venta no puede estar vacío.")
        return texto

    @staticmethod
    def _validar_total(valor: Any) -> float:
        """Valida que el total de la operación sea numérico y estrictamente positivo."""
        if isinstance(valor, bool) or valor is None:
            raise TypeError("El total de la venta debe ser un valor numérico.")
        if isinstance(valor, str):
            limpio = valor.replace("$", "").replace(" ", "").strip()
            if "," in limpio and "." in limpio:
                if limpio.rfind(",") > limpio.rfind("."):
                    limpio = limpio.replace(".", "").replace(",", ".")
                else:
                    limpio = limpio.replace(",", "")
            elif "," in limpio:
                limpio = limpio.replace(",", ".")
            valor = limpio
        try:
            total_float = float(valor)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"El total debe ser un número válido. Recibido: {valor!r}") from exc

        if math.isnan(total_float) or math.isinf(total_float):
            raise ValueError("El total de la venta no puede ser NaN ni infinito.")
        if total_float <= 0:
            raise ValueError("El monto total de la venta debe ser mayor a cero ($ 0).")
        return round(total_float, 2)

    @classmethod
    def _validar_tipo_entrega(cls, valor: Any) -> str:
        """Valida que el tipo de entrega sea 'Mostrador' o 'Delivery'."""
        if valor is None:
            raise ValueError("El tipo de entrega es obligatorio.")
        texto = str(valor).strip()
        mapa = {
            "mostrador": "Mostrador",
            "delivery": "Delivery",
            "envio": "Delivery",
            "envío": "Delivery",
        }
        normalizado = mapa.get(texto.lower(), texto)
        if normalizado not in cls.TIPOS_ENTREGA_VALIDOS:
            raise ValueError(
                f"Tipo de entrega inválido: '{texto}'. "
                f"Valores permitidos: {', '.join(cls.TIPOS_ENTREGA_VALIDOS)}."
            )
        return normalizado

    # =========================================================================
    # PROPIEDADES CALCULADAS Y SERIALIZACIÓN
    # =========================================================================

    @property
    def detalle_texto(self) -> str:
        """Retorna el detalle como texto plano, uniendo los ítems si es una lista."""
        if isinstance(self._detalle, list):
            return ", ".join(str(x) for x in self._detalle)
        return str(self._detalle)

    @property
    def fecha(self) -> str:
        """Extrae la fecha en formato 'YYYY-MM-DD' del atributo fecha_hora."""
        return self._fecha_hora.split(" ")[0]

    @property
    def hora(self) -> str:
        """Extrae la hora en formato 'HH:MM:SS' del atributo fecha_hora."""
        partes = self._fecha_hora.split(" ")
        return partes[1] if len(partes) > 1 else "00:00:00"

    @property
    def total_formateado(self) -> str:
        """Retorna el total formateado en pesos argentinos ($ {:,.0f})."""
        return f"$ {self._total:,.0f}"

    @property
    def medio_pago_resumen(self) -> str:
        """
        Retorna una etiqueta concisa del medio de pago con desglose
        si la venta fue mixta (ej. 'Mixto (Ef: $10.000 / Tr: $5.000)').
        """
        if self._medio_pago == self.MEDIO_MIXTO:
            return f"Mixto (Ef: ${self._monto_efectivo:,.0f} | Tr: ${self._monto_transferencia:,.0f})"
        return self._medio_pago

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la instancia de Venta a un diccionario estándar."""
        return {
            "id": self._id,
            "fecha_hora": self._fecha_hora,
            "detalle": self.detalle_texto,
            "total": self._total,
            "medio_pago": self._medio_pago,
            "monto_efectivo": self._monto_efectivo,
            "monto_transferencia": self._monto_transferencia,
            "tipo_entrega": self._tipo_entrega,
        }

    def to_excel_row(self) -> List[Any]:
        """
        Retorna una lista ordenada para insertar como fila en la hoja 'Ventas' de Excel:
        [ID, Fecha_Hora, Detalle, Total, Medio_Pago, Monto_Efectivo, Monto_Transferencia, Tipo_Entrega].
        """
        return [
            self._id,
            self._fecha_hora,
            self.detalle_texto,
            self._total,
            self._medio_pago,
            self._monto_efectivo,
            self._monto_transferencia,
            self._tipo_entrega,
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Venta":
        """
        Construye una instancia de Venta desde un diccionario (ej. fila de Excel/Pandas).
        Mantiene retrocompatibilidad con esquemas anteriores sin desglose explícito.
        """
        if not isinstance(data, dict):
            raise TypeError("Se esperaba un diccionario para deserializar una Venta.")

        id_val = data.get("id", data.get("ID", 0))
        fecha_hora_val = data.get(
            "fecha_hora", data.get("Fecha_Hora", data.get("Fecha y Hora", None))
        )
        detalle_val = data.get("detalle", data.get("Detalle", ""))
        total_val = data.get("total", data.get("Total", 0.0))
        medio_pago_val = data.get(
            "medio_pago", data.get("Medio_Pago", data.get("Medio de Pago", cls.MEDIO_EFECTIVO))
        )
        tipo_entrega_val = data.get(
            "tipo_entrega", data.get("Tipo_Entrega", data.get("Tipo de Entrega", "Mostrador"))
        )

        monto_efectivo_val = data.get(
            "monto_efectivo",
            data.get("Monto_Efectivo", data.get("Monto Efectivo", None)),
        )
        monto_transferencia_val = data.get(
            "monto_transferencia",
            data.get("Monto_Transferencia", data.get("Monto Transferencia", None)),
        )

        return cls(
            id=id_val,
            fecha_hora=fecha_hora_val,
            detalle=detalle_val,
            total=total_val,
            medio_pago=medio_pago_val,
            tipo_entrega=tipo_entrega_val,
            monto_efectivo=monto_efectivo_val,
            monto_transferencia=monto_transferencia_val,
        )

    def __repr__(self) -> str:
        return (
            f"Venta(id={self._id}, fecha_hora={self._fecha_hora!r}, "
            f"detalle={self.detalle_texto!r}, total={self._total}, "
            f"medio_pago={self._medio_pago!r}, "
            f"efectivo={self._monto_efectivo}, transf={self._monto_transferencia}, "
            f"tipo_entrega={self._tipo_entrega!r})"
        )
