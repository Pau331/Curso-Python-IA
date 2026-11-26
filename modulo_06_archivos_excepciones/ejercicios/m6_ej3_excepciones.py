"""Módulo 6 - Ejercicio 3: excepciones.

Incluye las ampliaciones 1 (logging en ``convertir_todos``) y 2 (JSON).
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EDAD_MINIMA = 0
EDAD_MAXIMA = 130


def a_entero(texto, por_defecto=None):
    """Convierte a entero con ``int()``. Si no se puede, devuelve ``por_defecto``.

    Es la versión con ``try``/``except`` de la función del módulo 2. Tiene que
    funcionar también si ``texto`` es ``None``.

    >>> a_entero("42"), a_entero("abc"), a_entero(None, 0)
    (42, None, 0)
    """
    try:
        return int(texto)
    except (ValueError, TypeError):
        return por_defecto


def dividir(a: float, b: float) -> float | None:
    """Devuelve ``a / b``, o ``None`` si ``b`` es cero.

    Solo captura la división por cero: cualquier otro error tiene que subir.
    """
    try:
        return a / b
    except ZeroDivisionError:
        return None


def leer_o_vacio(ruta) -> str:
    """Devuelve el contenido del fichero, o la cadena vacía si no existe."""
    try:
        with open(ruta, encoding="utf-8") as fichero:
            return fichero.read()
    except FileNotFoundError:
        return ""


def validar_edad(edad) -> int:
    """Devuelve la edad si es válida y, si no, lanza una excepción.

    - ``TypeError`` si no es un ``int`` (un ``bool`` tampoco vale).
    - ``ValueError`` si no está entre 0 y 130, ambos incluidos. El mensaje
      tiene que contener el valor recibido.

    >>> validar_edad(36)
    36
    """
    if isinstance(edad, bool) or not isinstance(edad, int):
        raise TypeError(f"La edad tiene que ser un entero, no {type(edad).__name__}")
    if not EDAD_MINIMA <= edad <= EDAD_MAXIMA:
        raise ValueError(f"Edad fuera de rango: {edad}")
    return edad


class ErrorDeCuenta(Exception):
    """Base de los errores de las operaciones con cuentas."""


class ImporteNoValido(ErrorDeCuenta):
    """El importe de la operación no es positivo."""


class SaldoInsuficiente(ErrorDeCuenta):
    """El importe supera el saldo disponible."""

    def __init__(self, saldo: float, importe: float):
        super().__init__(f"Saldo insuficiente: hay {saldo} y se piden {importe}")
        self.saldo = saldo
        self.importe = importe


def retirar(saldo: float, importe: float) -> float:
    """Devuelve el saldo que queda tras retirar el importe.

    Lanza ``ImporteNoValido`` si el importe no es positivo y
    ``SaldoInsuficiente`` si supera el saldo.

    >>> retirar(100, 30)
    70
    """
    if importe <= 0:
        raise ImporteNoValido(f"El importe tiene que ser positivo: {importe}")
    if importe > saldo:
        raise SaldoInsuficiente(saldo, importe)
    return saldo - importe


def convertir_todos(textos: list[str]) -> tuple[list[float], list[str]]:
    """Convierte cada texto a ``float`` y separa los que no se pueden convertir.

    Devuelve una tupla (números, textos rechazados). Un texto no válido no
    interrumpe el proceso de los siguientes. Ampliación 1: por cada texto
    rechazado registra un aviso con ``logger.warning``.

    >>> convertir_todos(["1.5", "x", "2"])
    ([1.5, 2.0], ['x'])
    """
    numeros = []
    rechazados = []
    for texto in textos:
        try:
            numeros.append(float(texto))
        except ValueError:
            logger.warning("Texto rechazado: %r no es un número", texto)
            rechazados.append(texto)
    return numeros, rechazados


def ejecutar(accion, registro: list[str]):
    """Llama a ``accion()`` anotando lo que ocurre en la lista ``registro``.

    Añade "inicio" antes de llamar; después "ok" si termina bien o "error"
    si lanza cualquier excepción; y "fin" en todos los casos. Devuelve lo que
    devuelva la acción. Si la acción falla, la excepción tiene que seguir
    subiendo después de anotar "error" y "fin".
    """
    registro.append("inicio")
    try:
        resultado = accion()
    except Exception:
        registro.append("error")
        raise
    else:
        registro.append("ok")
        return resultado
    finally:
        registro.append("fin")


class ErrorDeConfiguracion(Exception):
    """La configuración falta o tiene un valor incorrecto."""


def puerto_configurado(configuracion: dict) -> int:
    """Devuelve el puerto de la configuración como entero.

    Si falta la clave "puerto" o su valor no se puede convertir a entero,
    lanza ``ErrorDeConfiguracion`` encadenada con la excepción original
    mediante ``raise ... from``.

    >>> puerto_configurado({"puerto": "8080"})
    8080
    """
    try:
        return int(configuracion["puerto"])
    except KeyError as error:
        raise ErrorDeConfiguracion("Falta el puerto en la configuración") from error
    except ValueError as error:
        valor = configuracion["puerto"]
        raise ErrorDeConfiguracion(f"Puerto no válido: {valor}") from error


# ------------------------------------------------------ Ampliación 2: JSON
def guardar_json(ruta, datos) -> None:
    """Guarda ``datos`` en un fichero JSON legible, con tildes y eñes tal cual."""
    with open(ruta, "w", encoding="utf-8") as fichero:
        json.dump(datos, fichero, ensure_ascii=False, indent=2)


def cargar_json(ruta):
    """Devuelve los datos guardados en un fichero JSON."""
    with open(ruta, encoding="utf-8") as fichero:
        return json.load(fichero)


def csv_a_json(origen, destino) -> int:
    """Convierte un CSV de ventas en JSON, con los números ya convertidos.

    Reutiliza ``leer_ventas`` del ejercicio 2. Devuelve el número de ventas.
    """
    from m6_ej2_csv import leer_ventas

    ventas = leer_ventas(origen)
    guardar_json(destino, ventas)
    return len(ventas)


# ------------------------------------------------------ Ampliación 1: main
def main(nivel: str = "WARNING") -> None:
    """Configura el logging con el nivel indicado y prueba las ampliaciones."""
    logging.basicConfig(level=nivel, format="%(levelname)s %(message)s")
    numeros, rechazados = convertir_todos(["1.5", "x", "2", "1,5"])
    print(f"Convertidos: {numeros} | Rechazados: {rechazados}")

    datos = Path(__file__).parent.parent / "datos"
    cantidad = csv_a_json(datos / "ventas.csv", datos / "ventas.json")
    print(f"{cantidad} ventas guardadas en {datos / 'ventas.json'}")
    print(f"Comprobación: {len(cargar_json(datos / 'ventas.json'))} ventas leídas del JSON")


if __name__ == "__main__":
    main()
