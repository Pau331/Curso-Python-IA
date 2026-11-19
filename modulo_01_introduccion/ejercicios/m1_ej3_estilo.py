"""Módulo 1 - Ejercicio 3: código con estilo.

La función de abajo funciona, pero ignora PEP 8. Reescríbela siguiendo las
indicaciones del enunciado sin cambiar su comportamiento.
"""

IVA_GENERAL = 21

def precio_final(precio, iva=IVA_GENERAL, descuento=0):
    """Devuelve el precio final tras aplicar un descuento y el IVA.

    >>> precio_final(100)
    121.0
    >>> precio_final(100, descuento=10)
    108.9
    >>> precio_final(100, iva=10, descuento=10)
    99.0
    """
    precio_con_descuento = precio - precio * descuento / 100
    precio_con_iva = precio_con_descuento + precio_con_descuento * iva / 100
    return round(precio_con_iva, 2)