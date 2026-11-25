"""Módulo 5 - Ejercicio 6: dataclasses y composición.

En este ejercicio las clases se escriben enteras: no hay plantilla. El
enunciado está en ejercicios/README.md.
"""

import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Punto:
    """Un punto del plano. Es inmutable."""

    x: float = 0.0
    y: float = 0.0

    def distancia(self, otro: "Punto") -> float:
        """Devuelve la distancia hasta ``otro``, con dos decimales.

        >>> Punto(0, 0).distancia(Punto(3, 4))
        5.0
        """
        return round(math.hypot(otro.x - self.x, otro.y - self.y), 2)


@dataclass
class LineaPedido:
    """Una línea de pedido: un producto, sus unidades y su precio unitario."""

    producto: str
    unidades: int
    precio: float

    def __post_init__(self):
        """Comprueba que las unidades son positivas."""
        if self.unidades <= 0:
            raise ValueError("Las unidades tienen que ser positivas.")

    @property
    def importe(self) -> float:
        """Unidades por precio, con dos decimales."""
        return round(self.unidades * self.precio, 2)


@dataclass
class Pedido:
    """Un pedido de un cliente, formado por varias líneas."""

    numero: int
    cliente: str
    lineas: list[LineaPedido] = field(default_factory=list)

    def anadir(self, producto: str, unidades: int, precio: float) -> LineaPedido:
        """Crea una línea, la añade al pedido y la devuelve.

        >>> pedido = Pedido(1042, "Ada")
        >>> pedido.anadir("Teclado", 2, 45.0)
        LineaPedido(producto='Teclado', unidades=2, precio=45.0)
        """
        linea = LineaPedido(producto, unidades, precio)
        self.lineas.append(linea)
        return linea

    @property
    def total(self) -> float:
        """Suma de los importes de las líneas, con dos decimales."""
        return round(sum(linea.importe for linea in self.lineas), 2)

    def __len__(self) -> int:
        """Número de líneas del pedido."""
        return len(self.lineas)

    def productos(self) -> list[str]:
        """Nombres de los productos, sin repetir y en orden alfabético."""
        return sorted({linea.producto for linea in self.lineas})