"""Módulo 4 - Ejercicio 3: conjuntos."""

import string


def elementos_comunes(a: list, b: list) -> list:
    """Devuelve, ordenados y sin repetir, los elementos que están en las dos listas.

    >>> elementos_comunes([1, 2, 3, 4], [3, 4, 5, 6])
    [3, 4]
    """
    return sorted(set(a) & set(b))


def solo_en_una(a: list, b: list) -> list:
    """Devuelve, ordenados, los elementos que están en una lista pero no en las dos.

    >>> solo_en_una([1, 2, 3], [3, 4])
    [1, 2, 4]
    """
    return sorted(set(a) ^ set(b))


def tiene_duplicados(elementos: list) -> bool:
    """Indica si algún elemento aparece más de una vez.

    >>> tiene_duplicados([1, 2, 1])
    True
    """
    return len(elementos) != len(set(elementos))


def duplicados(elementos: list) -> list:
    """Devuelve, ordenados y sin repetir, los elementos que aparecen más de una vez.

    >>> duplicados([3, 1, 3, 2, 1, 3])
    [1, 3]
    """
    duplicados_set = set()
    vistos = set()
    for elemento in elementos:
        if elemento in vistos:
            duplicados_set.add(elemento)
        else:
            vistos.add(elemento)
    return sorted(duplicados_set)


def es_pangrama(frase: str) -> bool:
    """Indica si la frase contiene todas las letras de la «a» a la «z».

    No distingue mayúsculas de minúsculas y no tiene en cuenta la «ñ».

    >>> es_pangrama("The quick brown fox jumps over the lazy dog")
    True
    >>> es_pangrama("Hola mundo")
    False
    """
    alfabeto = set(string.ascii_lowercase)
    frase_sin_espacios = frase.lower().strip().split()
    letras_en_frase = set()
    for palabra in frase_sin_espacios:
        letras_en_frase.update(palabra)
    return alfabeto.issubset(letras_en_frase)


def permisos_que_faltan(requeridos: list[str], concedidos: list[str]) -> list[str]:
    """Devuelve, ordenados, los permisos requeridos que no están concedidos.

    >>> permisos_que_faltan(["leer", "escribir", "borrar"], ["leer", "admin"])
    ['borrar', 'escribir']
    """
    return sorted(set(requeridos) - set(concedidos))


def habilidades_compartidas(equipo: dict[str, list[str]]) -> list[str]:
    """Devuelve, ordenadas, las habilidades que tienen todas las personas del equipo.

    ``equipo`` asocia cada nombre con su lista de habilidades. Con el equipo
    vacío devuelve una lista vacía.

    >>> habilidades_compartidas({"Ada": ["python", "sql"], "Linus": ["c", "python"]})
    ['python']
    """
    if not equipo:
        return []
    listas = list(equipo.values())
    comunes = set(listas[0])
    for habilidades in listas[1:]:
        comunes &= set(habilidades)
    return sorted(comunes)
    # En una línea: sorted(set.intersection(*conjuntos))
