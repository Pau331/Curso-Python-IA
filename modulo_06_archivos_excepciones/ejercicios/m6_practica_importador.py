"""Módulo 6 - Práctica 6: importador de ventas en CSV.

Lee un CSV de ventas, valida cada fila, registra las que no valen y exporta
un resumen por región.
"""

import csv
import logging
import sys
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

CAMPOS = ["fecha", "vendedor", "region", "producto", "categoria", "unidades", "precio"]
CAMPOS_RESUMEN = ["region", "ventas", "unidades", "importe"]
CARPETA_PRACTICA_4 = Path(__file__).parent.parent.parent / "modulo_04_colecciones" / "ejercicios"


class ErrorDeImportacion(Exception):
    """Base de los errores del importador."""


class FicheroNoValido(ErrorDeImportacion):
    """El fichero no existe o le faltan columnas. No es recuperable."""


class FilaNoValida(ErrorDeImportacion):
    """Una fila tiene un dato incorrecto. Se anota y se sigue con la siguiente."""


# ----------------------------------------------------------- validación
def _a_numero(texto: str, convertir, coma_decimal: bool):
    """Convierte el texto con ``convertir`` (int o float) y comprueba que sea positivo.

    Lanza ``ValueError`` si no se puede convertir o si no es mayor que cero.
    """
    if coma_decimal:
        texto = texto.replace(",", ".")
    numero = convertir(texto)
    if numero <= 0:
        raise ValueError(f"{numero} no es mayor que cero")
    return numero


def validar_fila(fila: dict, *, coma_decimal: bool = False) -> dict:
    """Devuelve la venta de una fila con los tipos convertidos.

    Recibe un diccionario de cadenas y devuelve uno NUEVO con los mismos
    campos sin espacios alrededor, ``unidades`` como ``int`` y ``precio``
    como ``float``. Lanza ``FilaNoValida`` con uno de estos mensajes,
    comprobados en este orden:

    - "falta el campo <nombre>" si algún campo de ``CAMPOS`` está vacío
    - "fecha no válida: <valor>" si la fecha no es una fecha ISO
    - "unidades no válidas: <valor>" si no es un entero mayor que cero
    - "precio no válido: <valor>" si no es un número mayor que cero

    Ampliación 1: con ``coma_decimal=True`` el precio admite coma decimal.
    """
    venta = {}
    for campo in CAMPOS:
        valor = (fila.get(campo) or "").strip()
        if not valor:
            raise FilaNoValida(f"falta el campo {campo}")
        venta[campo] = valor

    try:
        date.fromisoformat(venta["fecha"])
    except ValueError as error:
        raise FilaNoValida(f"fecha no válida: {venta['fecha']}") from error

    try:
        venta["unidades"] = _a_numero(venta["unidades"], int, coma_decimal=False)
    except ValueError as error:
        raise FilaNoValida(f"unidades no válidas: {venta['unidades']}") from error

    try:
        venta["precio"] = _a_numero(venta["precio"], float, coma_decimal)
    except ValueError as error:
        raise FilaNoValida(f"precio no válido: {venta['precio']}") from error

    return venta


# ----------------------------------------------------------- importación
def _detectar_delimitador(primera_linea: str) -> str:
    """Ampliación 1: devuelve ";" si la cabecera usa punto y coma y "," si no."""
    return ";" if primera_linea.count(";") > primera_linea.count(",") else ","


def importar_ventas(ruta) -> tuple[list[dict], list[str]]:
    """Lee el CSV y devuelve una tupla (ventas válidas, errores).

    Cada error es un texto "Línea N: motivo", donde N es el número de línea
    en el fichero (la cabecera es la línea 1) y el motivo es el mensaje de
    ``FilaNoValida``. Por cada fila descartada se registra además un aviso
    con ``logger.warning``.

    Lanza ``FicheroNoValido``:

    - "No existe el fichero <ruta>" si no se encuentra, encadenada con el
      ``FileNotFoundError`` original
    - "Faltan columnas: <nombres separados por coma y espacio>" si a la
      cabecera le falta alguna de ``CAMPOS``, en el orden de ``CAMPOS``

    Ampliaciones: detecta el punto y coma como delimitador (y entonces
    admite la coma decimal) y descarta las filas repetidas.
    """
    try:
        fichero = open(ruta, encoding="utf-8", newline="")
    except FileNotFoundError as error:
        raise FicheroNoValido(f"No existe el fichero {ruta}") from error

    ventas = []
    errores = []
    vistas = set()
    with fichero:
        delimitador = _detectar_delimitador(fichero.readline())
        fichero.seek(0)
        lector = csv.DictReader(fichero, delimiter=delimitador)

        faltan = [campo for campo in CAMPOS if campo not in (lector.fieldnames or [])]
        if faltan:
            raise FicheroNoValido(f"Faltan columnas: {', '.join(faltan)}")

        # La cabecera es la línea 1, así que la primera fila de datos es la 2.
        for numero_linea, fila in enumerate(lector, start=2):
            try:
                venta = validar_fila(fila, coma_decimal=(delimitador == ";"))
                _comprobar_repetida(venta, vistas)
            except FilaNoValida as error:
                errores.append(f"Línea {numero_linea}: {error}")
                logger.warning("Línea %d descartada: %s", numero_linea, error)
                continue
            ventas.append(venta)

    return ventas, errores


def _comprobar_repetida(venta: dict, vistas: set) -> None:
    """Ampliación 2: lanza ``FilaNoValida`` si ya se ha importado una venta idéntica."""
    clave = tuple(venta[campo] for campo in CAMPOS)
    if clave in vistas:
        raise FilaNoValida("fila repetida")
    vistas.add(clave)


# ----------------------------------------------------------- resultados
def resumen_por_region(ventas: list[dict]) -> list[dict]:
    """Agrupa las ventas por región.

    Devuelve una lista de diccionarios con las claves de ``CAMPOS_RESUMEN``:
    la región, el número de ventas, las unidades totales y el importe total
    con dos decimales. Ordenada de mayor a menor importe.
    """
    grupos = {}
    for venta in ventas:
        region = venta["region"]
        vacio = {"region": region, "ventas": 0, "unidades": 0, "importe": 0}
        grupo = grupos.setdefault(region, vacio)
        grupo["ventas"] += 1
        grupo["unidades"] += venta["unidades"]
        grupo["importe"] += venta["unidades"] * venta["precio"]

    for grupo in grupos.values():
        grupo["importe"] = round(grupo["importe"], 2)
    return sorted(grupos.values(), key=lambda grupo: grupo["importe"], reverse=True)


def exportar_resumen(ruta, ventas: list[dict]) -> None:
    """Escribe en un CSV el resumen por región, con la cabecera ``CAMPOS_RESUMEN``."""
    with open(ruta, "w", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=CAMPOS_RESUMEN)
        escritor.writeheader()
        escritor.writerows(resumen_por_region(ventas))


def escribir_errores(ruta, errores: list[str]) -> None:
    """Escribe los errores en un fichero de texto, uno por línea."""
    with open(ruta, "w", encoding="utf-8") as fichero:
        for error in errores:
            fichero.write(error + "\n")


def escribir_informe(ruta, ventas: list[dict]) -> None:
    """Ampliación 4: escribe el informe de la Práctica 4 con las ventas importadas.

    Reutiliza ``generar_informe`` de ``m4_practica_ventas``.
    """
    if str(CARPETA_PRACTICA_4) not in sys.path:
        sys.path.append(str(CARPETA_PRACTICA_4))
    from m4_practica_ventas import generar_informe

    with open(ruta, "w", encoding="utf-8") as fichero:
        fichero.write(generar_informe(ventas) + "\n")


def procesar(entrada, carpeta_salida, *, con_informe: bool = False) -> dict:
    """Importa el fichero y deja los resultados en la carpeta de salida.

    Crea la carpeta si no existe y escribe en ella ``resumen.csv`` y
    ``errores.txt``. Registra con ``logger.info`` un mensaje final con las
    cantidades. Devuelve un diccionario con las claves "leidas", "validas"
    y "descartadas".

    Si el fichero de entrada no vale, ``FicheroNoValido`` sube sin capturar
    y no se escribe nada.

    Ampliación 4: con ``con_informe=True`` escribe además ``informe.txt`` con
    el informe de la Práctica 4.
    """
    ventas, errores = importar_ventas(entrada)

    carpeta = Path(carpeta_salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    exportar_resumen(carpeta / "resumen.csv", ventas)
    escribir_errores(carpeta / "errores.txt", errores)
    if con_informe:
        escribir_informe(carpeta / "informe.txt", ventas)

    cantidades = {
        "leidas": len(ventas) + len(errores),
        "validas": len(ventas),
        "descartadas": len(errores),
    }
    logger.info(
        "Importación terminada: %d válidas y %d descartadas",
        cantidades["validas"], cantidades["descartadas"],
    )
    return cantidades


def main(argumentos: list[str] | None = None) -> int:
    """Punto de entrada. Se entrega hecho: es el único sitio donde se capturan
    los errores del importador y donde se configura el logging.

    Uso: python m6_practica_importador.py [entrada.csv] [carpeta_salida] [--log fichero]

    Ampliación 3: con ``--log fichero`` el registro se guarda también en ese fichero.
    """
    argumentos = list(sys.argv[1:] if argumentos is None else argumentos)
    manejadores = [logging.StreamHandler()]
    if "--log" in argumentos:
        posicion = argumentos.index("--log")
        ruta_log = argumentos[posicion + 1]
        del argumentos[posicion:posicion + 2]
        manejadores.append(logging.FileHandler(ruta_log, encoding="utf-8"))
    datos = Path(__file__).parent.parent / "datos"
    entrada = argumentos[0] if argumentos else datos / "ventas_con_errores.csv"
    salida = argumentos[1] if len(argumentos) > 1 else Path("salida_practica_6")

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s",
                        handlers=manejadores)
    try:
        cantidades = procesar(entrada, salida, con_informe=True)
    except ErrorDeImportacion as error:
        logger.error("No se ha podido importar: %s", error)
        return 1
    print(f"Leídas {cantidades['leidas']} filas: {cantidades['validas']} válidas "
          f"y {cantidades['descartadas']} descartadas. Resultados en {salida}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
