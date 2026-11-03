"""
Módulo de modelo de dominio para Productos del menú gastronómico.
Implementa validaciones estrictas de tipos, valores positivos y serialización.
"""

from typing import Any, Dict, List
import math


class Producto:
    """
    Representa un plato, bebida o combo dentro del menú de la rotisería.

    Atributos:
        id (int): Identificador único del producto (0 si aún no fue persistido).
        nombre (str): Nombre comercial del plato o combo.
        categoria (str): Categoría gastronómica (ej. 'Pizzas', 'Empanadas', 'Combos').
        precio (float): Precio de venta unitario en pesos (debe ser mayor a 0).
        descripcion (str): Detalle de ingredientes o descripción promocional.
    """

    CATEGORIAS_SUGERIDAS: List[str] = [
        "Combos",
        "Pizzas",
        "Empanadas",
        "Hamburguesas",
        "Sándwiches y Lomitos",
        "Minutas y Al Plato",
        "Tartas y Calzones",
        "Pollo al Spiedo y Parrilla",
        "Guarniciones",
        "Bebidas",
        "Postres",
    ]

    def __init__(
        self,
        id: int,
        nombre: str,
        categoria: str,
        precio: float,
        descripcion: str = "",
    ) -> None:
        self.id: int = self._validar_id(id)
        self.nombre: str = self._validar_texto_obligatorio(nombre, "nombre")
        self.categoria: str = self._validar_texto_obligatorio(categoria, "categoría")
        self.precio: float = self._validar_precio(precio)
        self.descripcion: str = self._limpiar_descripcion(descripcion)

    @staticmethod
    def _validar_id(valor: Any) -> int:
        """Valida que el ID sea un número entero no negativo."""
        if valor is None or valor == "":
            return 0
        if isinstance(valor, bool):
            raise TypeError("El ID del producto debe ser un número entero, no booleano.")
        try:
            id_int = int(float(valor))
        except (ValueError, TypeError) as exc:
            raise TypeError(f"El ID del producto debe ser un número entero válido. Recibido: {valor!r}") from exc
        if id_int < 0:
            raise ValueError("El ID del producto no puede ser negativo.")
        return id_int

    @staticmethod
    def _validar_texto_obligatorio(valor: Any, nombre_campo: str) -> str:
        """Valida que un campo de texto sea string y no esté vacío."""
        if valor is None:
            raise ValueError(f"El campo '{nombre_campo}' es obligatorio y no puede ser nulo.")
        texto = str(valor).strip()
        if not texto or texto.lower() == "nan":
            raise ValueError(f"El campo '{nombre_campo}' no puede estar vacío.")
        return texto

    @staticmethod
    def _validar_precio(valor: Any) -> float:
        """Valida que el precio sea numérico y estrictamente positivo (> 0)."""
        if isinstance(valor, bool) or valor is None:
            raise TypeError("El precio debe ser un valor numérico válido.")
        if isinstance(valor, str):
            # Permitir formato con signo $, espacios o coma decimal
            limpio = valor.replace("$", "").replace(" ", "").strip()
            if "," in limpio and "." in limpio:
                # Si tiene punto de miles y coma decimal (ej. 12.500,50)
                if limpio.rfind(",") > limpio.rfind("."):
                    limpio = limpio.replace(".", "").replace(",", ".")
                else:
                    limpio = limpio.replace(",", "")
            elif "," in limpio:
                limpio = limpio.replace(",", ".")
            valor = limpio
        try:
            precio_float = float(valor)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"El precio debe ser un número válido. Recibido: {valor!r}") from exc

        if math.isnan(precio_float) or math.isinf(precio_float):
            raise ValueError("El precio no puede ser NaN ni infinito.")
        if precio_float <= 0:
            raise ValueError("El precio del producto debe ser mayor a cero ($ 0).")
        return round(precio_float, 2)

    @staticmethod
    def _limpiar_descripcion(valor: Any) -> str:
        """Normaliza la descripción tratando valores nulos o NaN como cadena vacía."""
        if valor is None:
            return ""
        if isinstance(valor, float) and math.isnan(valor):
            return ""
        texto = str(valor).strip()
        if texto.lower() == "nan":
            return ""
        return texto

    @property
    def precio_formateado(self) -> str:
        """Retorna el precio formateado en pesos argentinos ($ {:,.0f})."""
        return f"$ {self.precio:,.0f}"

    def aplicar_porcentaje(self, porcentaje: float) -> float:
        """
        Actualiza el precio del producto aplicando un porcentaje de aumento o descuento.

        Args:
            porcentaje (float): Porcentaje a aplicar (ej. 15.0 para +15%).

        Returns:
            float: El nuevo precio actualizado y redondeado.
        """
        try:
            pct = float(porcentaje)
        except (ValueError, TypeError) as exc:
            raise ValueError("El porcentaje debe ser un valor numérico.") from exc

        nuevo_precio = self.precio * (1.0 + (pct / 100.0))
        if nuevo_precio <= 0:
            raise ValueError("El precio resultante tras aplicar el porcentaje debe ser mayor a cero.")
        self.precio = round(nuevo_precio, 2)
        return self.precio

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la instancia de Producto a un diccionario estándar."""
        return {
            "id": self.id,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "precio": self.precio,
            "descripcion": self.descripcion,
        }

    def to_excel_row(self) -> List[Any]:
        """Retorna una lista ordenada para insertar como fila en la hoja 'Menu' de Excel."""
        return [
            self.id,
            self.nombre,
            self.categoria,
            self.precio,
            self.descripcion,
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Producto":
        """
        Construye una instancia de Producto a partir de un diccionario.
        Soporta claves en minúsculas o capitalizadas provenientes de Excel.
        """
        if not isinstance(data, dict):
            raise TypeError("Se esperaba un diccionario para deserializar un Producto.")

        id_val = data.get("id", data.get("ID", 0))
        nombre_val = data.get("nombre", data.get("Nombre", ""))
        categoria_val = data.get("categoria", data.get("Categoria", data.get("Categoría", "")))
        precio_val = data.get("precio", data.get("Precio", 0.0))
        descripcion_val = data.get("descripcion", data.get("Descripcion", data.get("Descripción", "")))

        return cls(
            id=id_val,
            nombre=nombre_val,
            categoria=categoria_val,
            precio=precio_val,
            descripcion=descripcion_val,
        )

    def __repr__(self) -> str:
        return (
            f"Producto(id={self.id}, nombre={self.nombre!r}, "
            f"categoria={self.categoria!r}, precio={self.precio}, "
            f"descripcion={self.descripcion!r})"
        )
