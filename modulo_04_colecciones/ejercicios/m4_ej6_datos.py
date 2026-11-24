"""Módulo 4 - Ejercicio 6: buscar, filtrar, ordenar y agrupar.

Todas las funciones trabajan con una lista de diccionarios como esta:

    empleados = [
        {"id": 1, "nombre": "Ada", "departamento": "IT", "salario": 52000},
        {"id": 2, "nombre": "Linus", "departamento": "IT", "salario": 48000},
        {"id": 3, "nombre": "Grace", "departamento": "Ventas", "salario": 45000},
    ]

Ninguna función modifica la lista que recibe.
"""


def buscar_por_id(registros: list[dict], identificador: int) -> dict | None:
    """Devuelve el registro cuyo campo "id" coincide, o ``None`` si no existe."""
    if not registros:
        return None
    for registro in registros:
        if registro.get("id") == identificador:
            return registro
    return None


def nombres(registros: list[dict]) -> list[str]:
    """Devuelve la lista con el campo "nombre" de cada registro, en el mismo orden."""
    if not registros:
        return []
    return [registro.get("nombre") for registro in registros]


def filtrar(registros: list[dict], campo: str, valor) -> list[dict]:
    """Devuelve los registros en los que ``campo`` vale ``valor``."""
    if not registros:
        return []
    return [registro for registro in registros if registro.get(campo) == valor]


def ordenar_por(registros: list[dict], campo: str, descendente: bool = False) -> list[dict]:
    """Devuelve una lista nueva con los registros ordenados por ``campo``."""
    if not registros:
        return []
    return sorted(registros, key=lambda r: r.get(campo), reverse=descendente)


def mejor_pagados(registros: list[dict], cantidad: int = 3) -> list[str]:
    """Devuelve los nombres de los ``cantidad`` empleados con mayor salario.

    De mayor a menor salario. A igual salario, por orden alfabético de nombre.
    """
    if not registros:
        return []
    empleados_ordenados = sorted(
        registros,
        key=lambda r: (-r.get("salario", 0), r.get("nombre", "")),
    )
    return [empleado.get("nombre") for empleado in empleados_ordenados[:cantidad]]


def agrupar_por(registros: list[dict], campo: str) -> dict[str, list[dict]]:
    """Agrupa los registros por el valor de ``campo``.

    Devuelve un diccionario que asocia cada valor distinto del campo con la
    lista de registros que lo tienen, en su orden original.
    """
    if not registros:
        return {}
    agrupados = {}
    for registro in registros:
        clave = registro.get(campo)
        if clave not in agrupados:
            agrupados[clave] = []
        agrupados[clave].append(registro)
    return agrupados


def salario_medio_por_departamento(registros: list[dict]) -> dict[str, float]:
    """Devuelve el salario medio de cada departamento, con dos decimales."""
    if not registros:
        return {}
    salario_medio = {}
    for registro in registros:
        departamento = registro.get("departamento")
        salario = registro.get("salario", 0)
        if departamento not in salario_medio:
            salario_medio[departamento] = []
        salario_medio[departamento].append(salario)
    return {dept: round(sum(salarios) / len(salarios), 2) for dept, salarios in salario_medio.items()}


def emparejar(claves: list[str], filas: list[list]) -> list[dict]:
    """Convierte filas de valores en diccionarios usando ``claves`` como nombres de campo.

    Es lo que hace un lector de CSV con la cabecera y las filas.

    >>> emparejar(["id", "nombre"], [[1, "Ada"], [2, "Linus"]])
    [{'id': 1, 'nombre': 'Ada'}, {'id': 2, 'nombre': 'Linus'}]
    """
    if not claves or not filas:
        return []
    return [dict(zip(claves, fila)) for fila in filas]