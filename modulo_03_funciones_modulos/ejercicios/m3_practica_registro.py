"""Módulo 3 - Práctica 3: alta de usuarios con el paquete m3_validacion.

Este programa es el cliente de la librería: no valida nada por sí mismo,
solo combina las funciones del paquete.
"""

from datetime import date

from m3_validacion import (
    es_dni,
    es_email,
    es_fecha,
    es_mayor_de_edad,
    esta_vacio,
    normalizar_nombre,
)

# Orden en que se piden los datos y texto de cada pregunta.
PREGUNTAS = {
    "nombre": "Nombre: ",
    "email": "Correo: ",
    "dni": "DNI: ",
    "fecha_nacimiento": "Fecha de nacimiento (AAAA-MM-DD): ",
}


def errores_por_campo(nombre: str, email: str, dni: str, fecha_nacimiento: str,
                      hoy: date | None = None) -> dict[str, str]:
    """Devuelve un diccionario {campo: mensaje} con los campos que tienen error.

    El orden de las claves es el de los mensajes del enunciado.
    """
    errores = {}
    if esta_vacio(nombre):
        errores["nombre"] = "El nombre es obligatorio."
    if not es_email(email.strip()):
        errores["email"] = "El correo no es válido."
    if not es_dni(dni):
        errores["dni"] = "El DNI no es válido."
    if not es_fecha(fecha_nacimiento):
        errores["fecha_nacimiento"] = "La fecha de nacimiento no es válida."
    elif not es_mayor_de_edad(fecha_nacimiento, hoy):
        errores["fecha_nacimiento"] = "Hay que ser mayor de edad."
    return errores


def validar_registro(nombre: str, email: str, dni: str, fecha_nacimiento: str,
                     hoy: date | None = None) -> list[str]:
    """Valida los datos de un alta y devuelve la lista de errores encontrados.

    Los mensajes, en este orden, son:

    - "El nombre es obligatorio."
    - "El correo no es válido."
    - "El DNI no es válido."
    - "La fecha de nacimiento no es válida."
    - "Hay que ser mayor de edad."  (solo si la fecha es válida)

    Si todo es correcto devuelve una lista vacía.

    >>> validar_registro("Ada", "ada@ejemplo.com", "12345678Z", "1990-01-01")
    []
    """
    errores = errores_por_campo(nombre, email, dni, fecha_nacimiento, hoy)
    return list(errores.values())


def crear_ficha(nombre: str, email: str, dni: str, fecha_nacimiento: str) -> dict:
    """Devuelve un diccionario con los datos ya normalizados.

    El nombre se normaliza con ``normalizar_nombre``, el correo se pasa a
    minúsculas y el DNI a mayúsculas, todos sin espacios alrededor.

    >>> crear_ficha(" ada LOVELACE", "Ada@Ejemplo.com ", "12345678z", "1990-01-01")
    {'nombre': 'Ada Lovelace', 'email': 'ada@ejemplo.com', 'dni': '12345678Z', 'nacimiento': '1990-01-01'}
    """
    return {
        "nombre": normalizar_nombre(nombre),
        "email": email.strip().lower(),
        "dni": dni.strip().upper(),
        "nacimiento": fecha_nacimiento.strip(),
    }


def pedir_datos() -> dict[str, str]:
    """Pide por teclado todos los datos del alta, en orden."""
    datos = {}
    for campo, pregunta in PREGUNTAS.items():
        datos[campo] = input(pregunta)
    return datos


def mostrar_ficha(datos: dict[str, str]) -> None:
    """Imprime la ficha normalizada de un alta correcta."""
    print("Alta correcta:")
    for clave, valor in crear_ficha(**datos).items():
        print(f"{clave}: {valor}")


def main():
    """Pide los datos por teclado y muestra la ficha o los errores.

    Pide, en este orden: nombre, correo, DNI y fecha de nacimiento. Si hay
    errores imprime "No se puede completar el alta:" y después cada error en
    una línea que empieza por " - ". Si no los hay imprime "Alta correcta:" y
    después cada dato de la ficha con el formato "clave: valor".
    """
    datos = pedir_datos()
    errores = validar_registro(**datos)
    if errores:
        print("No se puede completar el alta:")
        for error in errores:
            print(f" - {error}")
        return
    mostrar_ficha(datos)


def main_repitiendo():
    """Ampliación 3: vuelve a pedir solo los datos erróneos hasta que todo es correcto."""
    datos = pedir_datos()
    errores = errores_por_campo(**datos)
    while errores:
        print("Corrige estos datos:")
        for campo, mensaje in errores.items():
            print(f" - {mensaje}")
            datos[campo] = input(PREGUNTAS[campo])
        errores = errores_por_campo(**datos)
    mostrar_ficha(datos)


if __name__ == "__main__":
    main_repitiendo()