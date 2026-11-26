"""Guarda cada intento de nivel en un CSV y lo analiza con pandas."""

import csv
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # para dibujar sin abrir ventanas
import matplotlib.pyplot as plt
import pandas as pd

RUTA_INTENTOS = Path(__file__).parent / "datos" / "intentos.csv"
COLUMNAS = ["fecha", "nivel", "nombre_nivel", "completado", "monedas", "segundos", "vidas_perdidas"]


def guardar_intento(nivel, nombre_nivel, completado, monedas, segundos, vidas_perdidas,
                    ruta=RUTA_INTENTOS):
    """Añade una fila al CSV de intentos con el resultado de una partida a un nivel.

    Si el fichero no existe, lo crea (junto con su carpeta) y escribe primero la
    cabecera. La fecha se pone sola con la hora actual.

    Args:
        nivel: número del nivel (empezando en 1).
        nombre_nivel: nombre legible del nivel, p. ej. "El parque".
        completado: True si llegó a la meta, False si se quedó sin vidas.
        monedas: monedas recogidas en ese intento.
        segundos: duración del intento (se redondea a 1 decimal).
        vidas_perdidas: vidas que perdió durante el intento.
        ruta: dónde está el CSV (por defecto datos/intentos.csv; los tests usan otra).
    """
    ruta = Path(ruta)
    existia = ruta.exists()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8", newline="") as fichero:
        escritor = csv.DictWriter(fichero, fieldnames=COLUMNAS)
        if not existia:
            escritor.writeheader()
        escritor.writerow({
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "nivel": nivel,
            "nombre_nivel": nombre_nivel,
            "completado": completado,
            "monedas": monedas,
            "segundos": round(segundos, 1),
            "vidas_perdidas": vidas_perdidas,
        })


def cargar_intentos(ruta=RUTA_INTENTOS):
    """Lee el CSV de intentos y lo devuelve como DataFrame de pandas.

    Devuelve None si el fichero no existe o está vacío, para que quien la llame
    pueda mostrar "todavía no has jugado" en lugar de una tabla vacía.
    """
    if not Path(ruta).exists():
        return None
    df = pd.read_csv(ruta)
    return df if not df.empty else None


def resumen_por_nivel(df):
    """Agrupa los intentos por nivel y calcula sus estadísticas.

    Devuelve un DataFrame con una fila por nivel y las columnas:
    nivel, nombre_nivel, intentos, completados, monedas_medias, vidas_perdidas,
    exito (% de intentos completados) y mejor_tiempo (solo de los completados;
    NaN si ese nivel nunca se ha superado).
    """
    completados = df[df["completado"]]
    tabla = df.groupby(["nivel", "nombre_nivel"]).agg(
        intentos=("completado", "count"),
        completados=("completado", "sum"),
        monedas_medias=("monedas", "mean"),
        vidas_perdidas=("vidas_perdidas", "sum"),
    )
    tabla["exito"] = (tabla["completados"] / tabla["intentos"] * 100).round()
    # El mejor tiempo solo tiene sentido en los intentos que llegaron a la meta
    tabla["mejor_tiempo"] = completados.groupby(["nivel", "nombre_nivel"])["segundos"].min()
    return tabla.round(1).reset_index()


def totales(df):
    """Cifras globales de todos los intentos juntos, para la página de estadísticas.

    Devuelve un diccionario con: intentos (número de filas), monedas (suma),
    vidas_perdidas (suma) y minutos_jugados (suma de segundos pasada a minutos).
    """
    return {
        "intentos": len(df),
        "monedas": int(df["monedas"].sum()),
        "vidas_perdidas": int(df["vidas_perdidas"].sum()),
        "minutos_jugados": round(float(df["segundos"].sum()) / 60, 1),
    }


def crear_grafica(resumen, destino):
    """Dibuja un gráfico de barras dobles (intentos vs. completados) por nivel.

    Args:
        resumen: el DataFrame que devuelve resumen_por_nivel().
        destino: ruta de fichero o buffer (p. ej. BytesIO) donde guardar el PNG.
            La web usa un BytesIO para enviarlo sin escribir en disco.

    El PNG se guarda con fondo transparente y la figura se cierra al acabar
    para no acumular memoria.
    """
    fig, ax = plt.subplots(figsize=(7, 3.6))
    posiciones = range(len(resumen))
    ax.bar([p - 0.2 for p in posiciones], resumen["intentos"], width=0.4,
           color="#f2a65a", label="Intentos")
    ax.bar([p + 0.2 for p in posiciones], resumen["completados"], width=0.4,
           color="#4fa37b", label="Completados")
    ax.set_xticks(list(posiciones), resumen["nombre_nivel"])
    ax.set_ylabel("Veces")
    ax.yaxis.get_major_locator().set_params(integer=True)  # "veces" siempre son números enteros
    # La leyenda va fuera, encima de la gráfica, para que nunca tape las barras
    ax.legend(frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 1.02))
    for lado in ("top", "right"):
        ax.spines[lado].set_visible(False)
    fig.tight_layout()
    fig.savefig(destino, format="png", dpi=110, transparent=True)
    plt.close(fig)
