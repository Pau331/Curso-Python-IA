"""Módulo 1 - Práctica 1: conversor de unidades.

Lee el enunciado en PRACTICA_1.md.
"""

KM_POR_MILLA = 1.609344
KG_POR_LIBRA = 0.45359237
M_POR_PIE = 0.3048

MENU = """Conversor de unidades
1. Celsius a Fahrenheit
2. Fahrenheit a Celsius
3. Kilómetros a millas
4. Millas a kilómetros
5. Kilogramos a libras
6. Libras a kilogramos
7. Metros a pies
0. Salir"""


def celsius_a_fahrenheit(grados):
    """Convierte grados Celsius a Fahrenheit."""
    return grados * 9 / 5 + 32


def fahrenheit_a_celsius(grados):
    """Convierte grados Fahrenheit a Celsius."""
    return (grados - 32) * 5 / 9


def km_a_millas(km):
    """Convierte kilómetros a millas."""
    return km / KM_POR_MILLA


def millas_a_km(millas):
    """Convierte millas a kilómetros."""
    return millas * KM_POR_MILLA


def kg_a_libras(kg):
    """Convierte kilogramos a libras."""
    return kg / KG_POR_LIBRA


def libras_a_kg(libras):
    """Convierte libras a kilogramos."""
    return libras * KG_POR_LIBRA


def metros_a_pies(metros):
    """Convierte metros a pies."""
    return metros / M_POR_PIE


# Cada opción del menú: (unidad de origen, unidad de destino, función).
CONVERSIONES = {
    "1": ("°C", "°F", celsius_a_fahrenheit),
    "2": ("°F", "°C", fahrenheit_a_celsius),
    "3": ("km", "mi", km_a_millas),
    "4": ("mi", "km", millas_a_km),
    "5": ("kg", "lb", kg_a_libras),
    "6": ("lb", "kg", libras_a_kg),
    "7": ("m", "ft", metros_a_pies),
}


def formatear(valor, unidad_origen, resultado, unidad_destino):
    """Devuelve el texto de la conversión con dos decimales.

    >>> formatear(100, "°C", 212.0, "°F")
    '100.00 °C = 212.00 °F'
    """
    return f"{valor:.2f} {unidad_origen} = {resultado:.2f} {unidad_destino}"


def main():
    """Muestra el menú, pide los datos e imprime el resultado.

    Hace una sola conversión. Devuelve False si el usuario elige 0 para
    salir y True en cualquier otro caso, para que ``bucle`` sepa si debe
    seguir preguntando.
    """
    print(MENU)
    opcion = input("Elige una opción (0-7): ").strip()

    if opcion == "0":
        print("¡Hasta luego!")
        return False

    if opcion not in CONVERSIONES:
        print("Opción no válida")
        return True

    unidad_origen, unidad_destino, convertir = CONVERSIONES[opcion]
    valor = float(input("Valor a convertir: "))
    resultado = convertir(valor)
    print(formatear(valor, unidad_origen, resultado, unidad_destino))
    return True


def bucle():
    """Repite el menú hasta que el usuario elige 0 (ampliación opcional)."""
    while main():
        print()


if __name__ == "__main__":
    bucle()