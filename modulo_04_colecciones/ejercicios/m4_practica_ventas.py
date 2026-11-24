"""Módulo 4 - Práctica 4: análisis de ventas en memoria.

Cada venta es un diccionario con las claves "fecha", "vendedor", "region",
"producto", "categoria", "unidades" y "precio". Ninguna función modifica la
lista de ventas que recibe.
"""

from datetime import date, timedelta

from m4_datos_ventas import VENTAS

ANCHO = 44
ANCHO_VALOR = 14
ANCHO_ETIQUETA = ANCHO - ANCHO_VALOR
SANGRIA = "  "
DESGLOSES = (("Por región", "region"), ("Por categoría", "categoria"), ("Por vendedor", "vendedor"))


def importe(venta: dict) -> float:
    """Devuelve el importe de una venta: unidades por precio, con dos decimales.

    >>> importe({"unidades": 3, "precio": 19.9})
    59.7
    """
    return round(venta["unidades"] * venta["precio"], 2)


def unidades(venta: dict) -> int:
    """Devuelve las unidades de una venta. Sirve como medida para agrupar."""
    return venta["unidades"]


def total_ventas(ventas: list[dict]) -> float:
    """Devuelve la suma de los importes de todas las ventas, con dos decimales."""
    return round(sum(importe(venta) for venta in ventas), 2)


def filtrar_ventas(ventas: list[dict], *, region: str | None = None,
                   categoria: str | None = None, vendedor: str | None = None,
                   desde: str | None = None, hasta: str | None = None) -> list[dict]:
    """Devuelve las ventas que cumplen todos los criterios indicados.

    Un criterio que vale ``None`` no se aplica. ``desde`` y ``hasta`` son
    fechas ISO y las dos están incluidas en el intervalo.
    """
    exactos = {"region": region, "categoria": categoria, "vendedor": vendedor}
    criterios = {campo: valor for campo, valor in exactos.items() if valor is not None}

    def cumple(venta: dict) -> bool:
        if any(venta[campo] != valor for campo, valor in criterios.items()):
            return False
        # Las fechas ISO se pueden comparar como texto.
        if desde is not None and venta["fecha"] < desde:
            return False
        if hasta is not None and venta["fecha"] > hasta:
            return False
        return True

    return [venta for venta in ventas if cumple(venta)]


def sumar_por(ventas: list[dict], clave, medida) -> dict:
    """Agrupa las ventas con la función ``clave`` y suma ``medida`` en cada grupo.

    Es la pieza común de ``importe_por``, ``unidades_por_producto`` y
    ``importe_por_semana``: solo cambia cómo se agrupa y qué se suma.
    """
    totales = {}
    for venta in ventas:
        grupo = clave(venta)
        totales[grupo] = totales.get(grupo, 0) + medida(venta)
    return totales


def importe_por(ventas: list[dict], campo: str) -> dict[str, float]:
    """Agrupa las ventas por ``campo`` y devuelve el importe total de cada grupo.

    Los importes van redondeados a dos decimales.

    >>> importe_por([{"region": "Norte", "unidades": 2, "precio": 10.0}], "region")
    {'Norte': 20.0}
    """
    totales = sumar_por(ventas, lambda venta: venta[campo], importe)
    return {grupo: round(total, 2) for grupo, total in totales.items()}


def unidades_por_producto(ventas: list[dict]) -> dict[str, int]:
    """Devuelve las unidades totales vendidas de cada producto."""
    return sumar_por(ventas, lambda venta: venta["producto"], unidades)


def ordenar_de_mayor_a_menor(totales: dict) -> list[tuple]:
    """Devuelve los pares (clave, valor) de mayor a menor valor y, a igualdad, por clave."""
    return sorted(totales.items(), key=lambda par: (-par[1], par[0]))


def ranking(ventas: list[dict], campo: str, cantidad: int | None = 3,
            medida: str = "importe") -> list[tuple[str, float]]:
    """Devuelve los ``cantidad`` grupos con mayor importe, como tuplas (clave, importe).

    De mayor a menor importe. A igual importe, por orden alfabético de la clave.
    Con ``cantidad=None`` devuelve todos los grupos.

    Ampliación: ``medida="unidades"`` ordena por unidades en lugar de importe.
    """
    if medida == "unidades":
        totales = sumar_por(ventas, lambda venta: venta[campo], unidades)
    else:
        totales = importe_por(ventas, campo)
    return ordenar_de_mayor_a_menor(totales)[:cantidad]


def producto_mas_vendido(ventas: list[dict]) -> str | None:
    """Devuelve el producto con más unidades vendidas, o ``None`` si no hay ventas.

    En caso de empate, el primero por orden alfabético.
    """
    mas_vendidos = ranking(ventas, "producto", 1, medida="unidades")
    return mas_vendidos[0][0] if mas_vendidos else None


def ticket_medio(ventas: list[dict]) -> float:
    """Devuelve el importe medio por venta, con dos decimales. Sin ventas, 0.0."""
    if not ventas:
        return 0.0
    return round(total_ventas(ventas) / len(ventas), 2)


# ----------------------------------------------------------------- Informe
def linea_resumen(etiqueta: str, valor: str) -> str:
    """Línea de resumen: etiqueta a la izquierda y valor a la derecha."""
    return f"{etiqueta:<{ANCHO_ETIQUETA}}{valor:>{ANCHO_VALOR}}"


def lineas_desglose(titulo: str, pares: list[tuple]) -> list[str]:
    """Devuelve el título de un desglose seguido de una línea por grupo."""
    ancho_clave = ANCHO_ETIQUETA - len(SANGRIA)
    return [titulo] + [
        f"{SANGRIA}{clave:<{ancho_clave}}{valor:>{ANCHO_VALOR},.2f}" for clave, valor in pares
    ]


def generar_informe(ventas: list[dict], *, por_semana: bool = False) -> str:
    """Devuelve el informe de ventas como texto, con el formato del enunciado.

    Ampliación: con ``por_semana=True`` añade un desglose por semana.
    """
    doble, simple = "=" * ANCHO, "-" * ANCHO
    lineas = [
        doble,
        "INFORME DE VENTAS".center(ANCHO).rstrip(),
        doble,
        linea_resumen("Ventas registradas", str(len(ventas))),
        linea_resumen("Importe total", f"{total_ventas(ventas):,.2f}"),
        linea_resumen("Ticket medio", f"{ticket_medio(ventas):,.2f}"),
        linea_resumen("Producto más vendido", producto_mas_vendido(ventas) or "-"),
    ]
    for titulo, campo in DESGLOSES:
        lineas.append(simple)
        lineas += lineas_desglose(titulo, ranking(ventas, campo, cantidad=None))
    if por_semana:
        lineas.append(simple)
        lineas += lineas_desglose("Por semana", importe_por_semana(ventas).items())
    lineas.append(doble)
    return "\n".join(lineas)


# ------------------------------------------------------------ Ampliaciones
def semana(venta: dict) -> str:
    """Devuelve la semana ISO de una venta como texto, por ejemplo "Semana 40"."""
    numero = date.fromisoformat(venta["fecha"]).isocalendar().week
    return f"Semana {numero:02d}"


def importe_por_semana(ventas: list[dict]) -> dict[str, float]:
    """Ampliación 1: importe total de cada semana, en orden cronológico."""
    totales = sumar_por(ventas, semana, importe)
    return {grupo: round(totales[grupo], 2) for grupo in sorted(totales)}


def comparar_periodos(ventas: list[dict], corte: str) -> float | None:
    """Ampliación 2: variación en % del importe posterior a ``corte`` respecto al anterior.

    Las ventas anteriores son las de antes del día ``corte``; las posteriores,
    las de ese día en adelante. Si antes no hubo ventas devuelve ``None``.
    """
    dia_anterior = (date.fromisoformat(corte) - timedelta(days=1)).isoformat()
    antes = total_ventas(filtrar_ventas(ventas, hasta=dia_anterior))
    despues = total_ventas(filtrar_ventas(ventas, desde=corte))
    if antes == 0:
        return None
    return round((despues - antes) / antes * 100, 2)


def mejor_vendedor_por_region(ventas: list[dict]) -> dict[str, str]:
    """Ampliación 4: el vendedor con mayor importe en cada región."""
    return {
        region: ranking(filtrar_ventas(ventas, region=region), "vendedor", 1)[0][0]
        for region in importe_por(ventas, "region")
    }


def main():
    print(generar_informe(VENTAS))
    print()
    print("Solo la región Sur, segunda quincena:")
    print(generar_informe(filtrar_ventas(VENTAS, region="Sur", desde="2026-10-16")))


if __name__ == "__main__":
    main()