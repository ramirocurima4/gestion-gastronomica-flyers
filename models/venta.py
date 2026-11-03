"""
Módulo de modelo de dominio para Ventas y Arqueo de Caja Diario.
Implementa validaciones de medios de pago, modalidades de entrega y montos.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union
import math


class Venta:
    """
    Representa una operación de venta registrada en la caja diaria de la rotisería.

    Atributos:
        id (int): Identificador único de la venta (0 si aún no fue persistida).
        fecha_hora (str): Fecha y hora en formato ISO legible ('YYYY-MM-DD HH:MM:SS').
        detalle (Union[str, List[str]]): Descripción o lista de ítems vendidos.
        total (float): Monto total cobrado en pesos (debe ser mayor a 0).
        medio_pago (str): Medio de cobro ('Efectivo' o 'Transferencia/MP').
        tipo_entrega (str): Modalidad de entrega ('Mostrador' o 'Delivery').
    """

    MEDIOS_PAGO_VALIDOS: Tuple[str, ...] = ("Efectivo", "Transferencia/MP")
    TIPOS_ENTREGA_VALIDOS: Tuple[str, ...] = ("Mostrador", "Delivery")

    def __init__(
        self,
        id: int,
        detalle: Union[str, List[str]],
        total: float,
        medio_pago: str = "Efectivo",
        tipo_entrega: str = "Mostrador",
        fecha_hora: Optional[str] = None,
    ) -> None:
        self.id: int = self._validar_id(id)
        self.fecha_hora: str = self._validar_fecha_hora(fecha_hora)
        self.detalle: Union[str, List[str]] = self._validar_detalle(detalle)
        self.total: float = self._validar_total(total)
        self.medio_pago: str = self._validar_medio_pago(medio_pago)
        self.tipo_entrega: str = self._validar_tipo_entrega(tipo_entrega)

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
            raise TypeError(f"El ID de la venta debe ser un entero válido. Recibido: {valor!r}") from exc
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
        # Reemplazar separador 'T' ISO 8601 si viniera con 'T'
        texto_normalizado = texto.replace("T", " ")
        # Si solo viene la fecha YYYY-MM-DD, anexar hora 00:00:00
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
        if valor is None:
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
    def _validar_medio_pago(cls, valor: Any) -> str:
        """Valida que el medio de pago sea uno de los permitidos por el negocio."""
        if valor is None:
            raise ValueError("El medio de pago es obligatorio.")
        texto = str(valor).strip()
        # Normalización amigable por si viene con distinta capitalización
        mapa = {
            "efectivo": "Efectivo",
            "transferencia/mp": "Transferencia/MP",
            "transferencia": "Transferencia/MP",
            "mercado pago": "Transferencia/MP",
            "mercadopago": "Transferencia/MP",
            "mp": "Transferencia/MP",
        }
        normalizado = mapa.get(texto.lower(), texto)
        if normalizado not in cls.MEDIOS_PAGO_VALIDOS:
            raise ValueError(
                f"Medio de pago inválido: '{texto}'. "
                f"Valores permitidos: {', '.join(cls.MEDIOS_PAGO_VALIDOS)}."
            )
        return normalizado

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

    @property
    def detalle_texto(self) -> str:
        """Retorna el detalle como texto plano, uniendo los ítems si es una lista."""
        if isinstance(self.detalle, list):
            return ", ".join(str(x) for x in self.detalle)
        return str(self.detalle)

    @property
    def fecha(self) -> str:
        """Extrae la fecha en formato 'YYYY-MM-DD' del atributo fecha_hora."""
        return self.fecha_hora.split(" ")[0]

    @property
    def hora(self) -> str:
        """Extrae la hora en formato 'HH:MM:SS' (o 'HH:MM') del atributo fecha_hora."""
        partes = self.fecha_hora.split(" ")
        return partes[1] if len(partes) > 1 else "00:00:00"

    @property
    def total_formateado(self) -> str:
        """Retorna el total formateado en pesos argentinos ($ {:,.0f})."""
        return f"$ {self.total:,.0f}"

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la instancia de Venta a un diccionario estándar."""
        return {
            "id": self.id,
            "fecha_hora": self.fecha_hora,
            "detalle": self.detalle_texto,
            "total": self.total,
            "medio_pago": self.medio_pago,
            "tipo_entrega": self.tipo_entrega,
        }

    def to_excel_row(self) -> List[Any]:
        """Retorna una lista ordenada para insertar como fila en la hoja 'Ventas' de Excel."""
        return [
            self.id,
            self.fecha_hora,
            self.detalle_texto,
            self.total,
            self.medio_pago,
            self.tipo_entrega,
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Venta":
        """Construye una instancia de Venta desde un diccionario (ej. fila de Excel)."""
        if not isinstance(data, dict):
            raise TypeError("Se esperaba un diccionario para deserializar una Venta.")

        id_val = data.get("id", data.get("ID", 0))
        fecha_hora_val = data.get("fecha_hora", data.get("Fecha_Hora", data.get("Fecha y Hora", None)))
        detalle_val = data.get("detalle", data.get("Detalle", ""))
        total_val = data.get("total", data.get("Total", 0.0))
        medio_pago_val = data.get("medio_pago", data.get("Medio_Pago", data.get("Medio de Pago", "Efectivo")))
        tipo_entrega_val = data.get(
            "tipo_entrega", data.get("Tipo_Entrega", data.get("Tipo de Entrega", "Mostrador"))
        )

        return cls(
            id=id_val,
            fecha_hora=fecha_hora_val,
            detalle=detalle_val,
            total=total_val,
            medio_pago=medio_pago_val,
            tipo_entrega=tipo_entrega_val,
        )

    def __repr__(self) -> str:
        return (
            f"Venta(id={self.id}, fecha_hora={self.fecha_hora!r}, "
            f"detalle={self.detalle_texto!r}, total={self.total}, "
            f"medio_pago={self.medio_pago!r}, tipo_entrega={self.tipo_entrega!r})"
        )
