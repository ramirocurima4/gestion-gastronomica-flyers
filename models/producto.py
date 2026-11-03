"""
Módulo de modelo de dominio para Productos del menú gastronómico.
Implementa encapsulamiento POO mediante propiedades (@property / @setter),
validaciones estrictas de tipos, valores positivos y serialización.
"""

import math
from typing import Any, Dict, List


class Producto:
    """
    Representa un plato, bebida o combo dentro del menú de la rotisería.

    Atributos encapsulados (accesibles vía @property):
        id (int): Identificador único del producto (0 si aún no fue persistido).
        nombre (str): Nombre comercial del plato o combo (no vacío).
        categoria (str): Categoría gastronómica válida (ej. 'Pizzas', 'Empanadas').
        precio (float): Precio de venta unitario en pesos (estrictamente > 0).
        descripcion (str): Detalle de ingredientes o descripción promocional.
        stock (int): Cantidad disponible o stock referencial (>= 0).
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
        stock: int = 0,
    ) -> None:
        self._id: int = 0
        self._nombre: str = ""
        self._categoria: str = ""
        self._precio: float = 0.0
        self._descripcion: str = ""
        self._stock: int = 0

        # Asignación a través de setters con validación defensiva
        self.id = id
        self.nombre = nombre
        self.categoria = categoria
        self.precio = precio
        self.descripcion = descripcion
        self.stock = stock

    # =========================================================================
    # PROPIEDADES Y SETTERS (ENCAPSULAMIENTO POO)
    # =========================================================================

    @property
    def id(self) -> int:
        """Retorna el identificador único del producto."""
        return self._id

    @id.setter
    def id(self, valor: Any) -> None:
        """Valida que el ID sea un número entero no negativo (>= 0)."""
        self._id = self._validar_id(valor)

    @property
    def nombre(self) -> str:
        """Retorna el nombre comercial del plato o combo."""
        return self._nombre

    @nombre.setter
    def nombre(self, valor: Any) -> None:
        """Valida que el nombre no sea nulo ni una cadena vacía."""
        self._nombre = self._validar_texto_obligatorio(valor, "nombre")

    @property
    def categoria(self) -> str:
        """Retorna la categoría gastronómica del producto."""
        return self._categoria

    @categoria.setter
    def categoria(self, valor: Any) -> None:
        """Valida y normaliza la categoría del producto."""
        self._categoria = self._validar_categoria(valor)

    @property
    def precio(self) -> float:
        """Retorna el precio unitario del producto."""
        return self._precio

    @precio.setter
    def precio(self, valor: Any) -> None:
        """Valida que el precio sea numérico y estrictamente mayor a 0."""
        self._precio = self._validar_precio(valor)

    @property
    def descripcion(self) -> str:
        """Retorna la descripción o ingredientes del producto."""
        return self._descripcion

    @descripcion.setter
    def descripcion(self, valor: Any) -> None:
        """Limpia y normaliza la descripción del producto."""
        self._descripcion = self._limpiar_descripcion(valor)

    @property
    def stock(self) -> int:
        """Retorna el stock disponible del producto."""
        return self._stock

    @stock.setter
    def stock(self, valor: Any) -> None:
        """Valida que el stock sea un número entero no negativo (>= 0)."""
        self._stock = self._validar_stock(valor)

    # =========================================================================
    # MÉTODOS DE VALIDACIÓN DEFENSIVA
    # =========================================================================

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
            raise TypeError(
                f"El ID del producto debe ser un número entero válido. Recibido: {valor!r}"
            ) from exc
        if id_int < 0:
            raise ValueError("El ID del producto no puede ser negativo.")
        return id_int

    @staticmethod
    def _validar_texto_obligatorio(valor: Any, nombre_campo: str) -> str:
        """Valida que un campo de texto sea string y no esté vacío."""
        if valor is None or isinstance(valor, bool):
            raise ValueError(f"El campo '{nombre_campo}' es obligatorio y no puede ser nulo.")
        texto = str(valor).strip()
        if not texto or texto.lower() == "nan":
            raise ValueError(f"El campo '{nombre_campo}' no puede estar vacío.")
        return texto

    @classmethod
    def _validar_categoria(cls, valor: Any) -> str:
        """
        Valida que la categoría no esté vacía y la normaliza si coincide
        con alguna de las categorías sugeridas del sistema.
        """
        texto = cls._validar_texto_obligatorio(valor, "categoría")
        for sugerida in cls.CATEGORIAS_SUGERIDAS:
            if sugerida.lower() == texto.lower():
                return sugerida
        return texto

    @staticmethod
    def _validar_precio(valor: Any) -> float:
        """Valida que el precio sea numérico y estrictamente positivo (> 0)."""
        if isinstance(valor, bool) or valor is None:
            raise TypeError("El precio debe ser un valor numérico válido.")
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
            precio_float = float(valor)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"El precio debe ser un número válido. Recibido: {valor!r}") from exc

        if math.isnan(precio_float) or math.isinf(precio_float):
            raise ValueError("El precio no puede ser NaN ni infinito.")
        if precio_float <= 0:
            raise ValueError("El precio del producto debe ser mayor a cero ($ 0).")
        return round(precio_float, 2)

    @staticmethod
    def _validar_stock(valor: Any) -> int:
        """Valida que el stock sea un entero mayor o igual a cero."""
        if valor is None or valor == "":
            return 0
        if isinstance(valor, bool):
            raise TypeError("El stock debe ser un número entero, no booleano.")
        try:
            stock_int = int(float(valor))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"El stock debe ser un número entero válido. Recibido: {valor!r}") from exc
        if stock_int < 0:
            raise ValueError("El stock del producto no puede ser negativo.")
        return stock_int

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

    # =========================================================================
    # MÉTODOS DE NEGOCIO Y SERIALIZACIÓN
    # =========================================================================

    @property
    def precio_formateado(self) -> str:
        """Retorna el precio formateado en pesos argentinos ($ {:,.0f})."""
        return f"$ {self._precio:,.0f}"

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

        nuevo_precio = self._precio * (1.0 + (pct / 100.0))
        if nuevo_precio <= 0:
            raise ValueError("El precio resultante tras aplicar el porcentaje debe ser mayor a cero.")
        self.precio = round(nuevo_precio, 2)
        return self._precio

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la instancia de Producto a un diccionario estándar."""
        return {
            "id": self._id,
            "nombre": self._nombre,
            "categoria": self._categoria,
            "precio": self._precio,
            "descripcion": self._descripcion,
        }

    def to_excel_row(self) -> List[Any]:
        """Retorna una lista ordenada para insertar como fila en la hoja 'Menu' de Excel."""
        return [
            self._id,
            self._nombre,
            self._categoria,
            self._precio,
            self._descripcion,
        ]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Producto":
        """
        Construye una instancia de Producto a partir de un diccionario.
        Soporta claves en minúsculas o capitalizadas provenientes de Excel/Pandas.
        """
        if not isinstance(data, dict):
            raise TypeError("Se esperaba un diccionario para deserializar un Producto.")

        id_val = data.get("id", data.get("ID", 0))
        nombre_val = data.get("nombre", data.get("Nombre", ""))
        categoria_val = data.get("categoria", data.get("Categoria", data.get("Categoría", "")))
        precio_val = data.get("precio", data.get("Precio", 0.0))
        descripcion_val = data.get(
            "descripcion", data.get("Descripcion", data.get("Descripción", ""))
        )
        stock_val = data.get("stock", data.get("Stock", 0))

        return cls(
            id=id_val,
            nombre=nombre_val,
            categoria=categoria_val,
            precio=precio_val,
            descripcion=descripcion_val,
            stock=stock_val,
        )

    def __repr__(self) -> str:
        return (
            f"Producto(id={self._id}, nombre={self._nombre!r}, "
            f"categoria={self._categoria!r}, precio={self._precio}, "
            f"descripcion={self._descripcion!r})"
        )
