"""Rumbo a casa: la web. Ejecuta:  python app.py   y abre  http://127.0.0.1:5000"""

from io import BytesIO
from pathlib import Path

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, send_file, url_for

import niveles
import registro
import mascota as reglas
from mascota import COMIDAS, DECORACIONES, RUTA_PARTIDA, Mascota, cargar_mascota

app = Flask(__name__)
app.secret_key = "rumbo-a-casa"
app.config["RUTA_PARTIDA"] = RUTA_PARTIDA
app.config["RUTA_INTENTOS"] = registro.RUTA_INTENTOS


# --- Ayudantes ----------------------------------------------------------------------


def mascota_actual():
    """Carga la mascota y le aplica el tiempo que ha pasado desde la última visita.

    Guarda enseguida el resultado para que el descuento no se repita.
    Devuelve la Mascota, o None si todavía no hay partida.
    Casi todas las rutas empiezan llamando a esta función.
    """
    mascota = cargar_mascota(app.config["RUTA_PARTIDA"])
    if mascota:
        mascota.pasar_tiempo()
        mascota.guardar(app.config["RUTA_PARTIDA"])
    return mascota


def estado_nivel(mascota, numero):
    """Estado de un capítulo en el mapa de la historia para esta mascota.

    "completado" si ya lo superó (o terminó la historia entera),
    "disponible" si es el siguiente que le toca, y "bloqueado" si aún no llega.
    """
    if mascota.historia_terminada or numero < mascota.nivel_desbloqueado:
        return "completado"
    if numero == mascota.nivel_desbloqueado:
        return "disponible"
    return "bloqueado"


# --- Casa: cuidar a la mascota ---------------------------------------------------------


@app.route("/")
def casa():
    """GET / — Página principal: la casa con la mascota, sus barras, la tienda y la decoración.

    Si no hay partida, muestra el formulario para crear una mascota (nueva.html).
    Si la mascota está ocupada, pasa a la plantilla qué hace y cuánto le falta
    para dibujar la barra de progreso.
    """
    mascota = mascota_actual()
    if mascota is None:
        return render_template("nueva.html")
    en_curso = mascota.ocupado()
    actividad = None
    if en_curso:
        accion, falta = en_curso
        texto, icono = reglas.ACTIVIDADES[accion]
        actividad = {"accion": accion, "texto": texto, "icono": icono,
                     "falta": falta, "total": reglas.DURACIONES[accion]}
    return render_template(
        "casa.html", m=mascota, comidas=COMIDAS, decoraciones=DECORACIONES, actividad=actividad,
        duraciones=reglas.DURACIONES,
        color_de=reglas.color_de, vidas_max=reglas.VIDAS_MAX, verde=reglas.VERDE,
        tiempo_total=mascota.tiempo_total(niveles.total_niveles()), limite=reglas.LIMITE_TROFEO,
        total_niveles=niveles.total_niveles(),
    )


@app.post("/nueva")
def nueva():
    """POST /nueva — Crea una mascota con el nombre del formulario (máx. 15 letras).

    Si el nombre está vacío, avisa con flash. Sobrescribe la partida existente.
    """
    nombre = request.form.get("nombre", "").strip()[:15]
    if not nombre:
        flash("Ponle un nombre a tu mascota.")
        return redirect(url_for("casa"))
    Mascota(nombre).guardar(app.config["RUTA_PARTIDA"])
    return redirect(url_for("casa"))


@app.post("/cuidar")
def cuidar():
    """POST /cuidar — Ejecuta una acción de los botones de la casa.

    El campo "accion" del formulario decide qué método de Mascota se llama:
    comer (+ "comida"), banar, jugar, siesta, comprar (+ "comida") o
    decorar (+ "objeto"). Valida que la comida/objeto exista, guarda la
    partida, muestra el mensaje con flash y vuelve a la casa.
    """
    mascota = mascota_actual()
    if mascota is None:
        return redirect(url_for("casa"))
    accion = request.form.get("accion")
    if accion == "comer":
        clave = request.form.get("comida")
        mensaje = mascota.comer(clave) if clave in COMIDAS else "Esa comida no existe."
    elif accion == "banar":
        mensaje = mascota.banar()
    elif accion == "jugar":
        mensaje = mascota.jugar()
    elif accion == "siesta":
        mensaje = mascota.siesta()
    elif accion == "comprar":
        clave = request.form.get("comida")
        mensaje = mascota.comprar(clave) if clave in COMIDAS else "Ese producto no existe."
    elif accion == "decorar":
        clave = request.form.get("objeto")
        mensaje = mascota.comprar_decoracion(clave) if clave in DECORACIONES else "Ese objeto no existe."
    else:
        mensaje = "No sé hacer eso."
    mascota.guardar(app.config["RUTA_PARTIDA"])
    flash(mensaje)
    return redirect(url_for("casa"))


@app.post("/reiniciar")
def reiniciar():
    """POST /reiniciar — Borra la partida guardada (el registro de intentos se conserva)."""
    Path(app.config["RUTA_PARTIDA"]).unlink(missing_ok=True)
    return redirect(url_for("casa"))


# --- Historia y niveles ---------------------------------------------------------------


@app.route("/historia")
def historia():
    """GET /historia — El camino de capítulos con el estado de cada uno.

    También indica si la mascota puede salir de aventura ahora (y si no, por
    qué) y si al salir recuperará las vidas por tener todo en verde.
    """
    mascota = mascota_actual()
    if mascota is None:
        return redirect(url_for("casa"))
    capitulos = [
        {"numero": i, "nombre": n["nombre"], "tema": n["tema"], "estado": estado_nivel(mascota, i),
         "premio": reglas.premio_nivel(i), "monedas": niveles.preparar_mapa(n["mapa"])["monedas"]}
        for i, n in enumerate(niveles.NIVELES, start=1)
    ]
    puede, motivo = mascota.puede_jugar()
    return render_template(
        "historia.html", m=mascota, capitulos=capitulos, puede=puede, motivo=motivo,
        vidas_max=reglas.VIDAS_MAX, recuperara=mascota.todas_en_verde() and mascota.vidas < reglas.VIDAS_MAX,
    )


@app.route("/nivel/<int:numero>")
def nivel(numero):
    """GET /nivel/<numero> — Abre la página del juego de plataformas para ese nivel.

    404 si no hay mascota o el nivel no existe. Redirige a /historia si el
    nivel está bloqueado o la mascota no puede salir (cansada, ocupada…).
    Si puede: llama a empezar_aventura() (recuperar vidas), guarda, y pasa
    a la plantilla `para_el_juego`, que acaba en window.NIVEL para juego.js.
    """
    mascota = mascota_actual()
    datos_nivel = niveles.obtener_nivel(numero)
    if mascota is None or datos_nivel is None:
        abort(404)
    if estado_nivel(mascota, numero) == "bloqueado":
        flash("Ese capítulo todavía está bloqueado: supera antes los anteriores.")
        return redirect(url_for("historia"))
    puede, _motivo = mascota.puede_jugar()
    if not puede:  # la página de la aventura ya explica el motivo
        return redirect(url_for("historia"))

    recuperadas = mascota.empezar_aventura()
    mascota.guardar(app.config["RUTA_PARTIDA"])
    mapa = niveles.preparar_mapa(datos_nivel["mapa"])
    para_el_juego = {
        **mapa,
        "tema": datos_nivel["tema"],
        "colores": datos_nivel["colores"],
        "vidas": mascota.vidas,
        "vidas_max": reglas.VIDAS_MAX,
        "gafas": mascota.lleva_gafas(),
        "url_terminar": url_for("terminar_nivel", numero=numero),
    }
    return render_template(
        "nivel.html", m=mascota, numero=numero, nivel=datos_nivel,
        historia=datos_nivel["historia"].format(nombre=mascota.nombre),
        para_el_juego=para_el_juego, total=niveles.total_niveles(), recuperadas=recuperadas,
    )


@app.post("/nivel/<int:numero>/terminar")
def terminar_nivel(numero):
    """POST /nivel/<numero>/terminar — El navegador avisa de cómo ha ido el nivel.

    Recibe un JSON {completado, monedas, segundos, vidas_perdidas} desde
    juego.js. Lo valida y lo recorta para evitar trampas (no más monedas de
    las que hay en el mapa, no más vidas perdidas de las que tiene); si falta
    algo o no es un número, responde 400.

    Después aplica el resultado a la mascota (terminar_nivel), guarda la
    partida, apunta el intento en el CSV y responde con un JSON
    {titulo, mensaje, botones} que juego.js muestra en el panel final.
    """
    mascota = mascota_actual()
    datos_nivel = niveles.obtener_nivel(numero)
    if mascota is None or datos_nivel is None:
        abort(404)

    resultado = request.get_json(silent=True) or {}
    total_monedas = niveles.preparar_mapa(datos_nivel["mapa"])["monedas"]
    try:
        completado = bool(resultado["completado"])
        monedas = max(0, min(total_monedas, int(resultado["monedas"])))  # sin trampas
        segundos = max(0.0, float(resultado["segundos"]))
        vidas_perdidas = max(0, min(mascota.vidas, int(resultado["vidas_perdidas"])))
    except (KeyError, TypeError, ValueError):
        return jsonify({"error": "Resultado no válido"}), 400

    total = niveles.total_niveles()
    novedades = mascota.terminar_nivel(numero, completado, monedas, segundos, vidas_perdidas, total)
    mascota.guardar(app.config["RUTA_PARTIDA"])
    registro.guardar_intento(numero, datos_nivel["nombre"], completado, monedas, segundos,
                             vidas_perdidas, app.config["RUTA_INTENTOS"])

    nombre = mascota.nombre
    premio = reglas.premio_nivel(numero)
    estado = f" Vuelve con {mascota.vidas} {'vida' if mascota.vidas == 1 else 'vidas'} y bastante cansado: cuídale antes del siguiente."
    if completado and numero == total:
        respuesta = {"titulo": "¡Lo has conseguido!",
                     "mensaje": f"{nombre} ha llegado a casa con {monedas} monedas y {premio} de premio.",
                     "botones": [{"texto": "Ver el final", "url": url_for("final"), "principal": True}]}
    elif completado:
        respuesta = {"titulo": "¡Capítulo superado!",
                     "mensaje": f"{nombre} ha conseguido {monedas} monedas (+{premio} de premio) en {round(segundos)} segundo{'' if round(segundos) == 1 else 's'}." + estado,
                     "botones": [{"texto": "Volver a casa", "url": url_for("casa"), "principal": True},
                                 {"texto": "Ver el camino", "url": url_for("historia")}]}
    else:
        respuesta = {"titulo": f"{nombre} necesita descansar",
                     "mensaje": f"Se ha quedado sin vidas, pero guarda las {monedas} monedas que ha recogido. "
                                "Pon todas sus barras en verde para que recupere las vidas.",
                     "botones": [{"texto": "Volver a casa", "url": url_for("casa"), "principal": True}]}
    if novedades:
        respuesta["mensaje"] += " " + " ".join(novedades)
    return jsonify(respuesta)


@app.route("/final")
def final():
    """GET /final — Escena final de la historia. Solo si ya terminó todos los niveles."""
    mascota = mascota_actual()
    if mascota is None or not mascota.historia_terminada:
        return redirect(url_for("historia"))
    recuerdos = [
        {"numero": i, "nombre": n["nombre"], "tema": n["tema"], "colores": n["colores"],
         "tiempo": mascota.mejores_tiempos.get(str(i)), "sin_fallos": str(i) in mascota.niveles_sin_fallos}
        for i, n in enumerate(niveles.NIVELES, start=1)
    ]
    logros = [
        {"icono": DECORACIONES[clave]["icono"], "nombre": DECORACIONES[clave]["nombre"],
         "conseguido": clave in mascota.decoraciones, "como": DECORACIONES[clave]["como"]}
        for clave in ("trofeo", "gafas")
    ]
    return render_template("final.html", m=mascota, texto=niveles.FINAL.format(nombre=mascota.nombre),
                           recuerdos=recuerdos, logros=logros,
                           tiempo_total=mascota.tiempo_total(niveles.total_niveles()))


# --- Estadísticas --------------------------------------------------------------------


@app.route("/estadisticas")
def estadisticas():
    """GET /estadisticas — Tabla por nivel y totales a partir del CSV de intentos.

    Si aún no hay intentos, la plantilla muestra "Todavía no has jugado".
    `version` (nº de intentos) se añade a la URL de la gráfica para que el
    navegador no muestre una imagen vieja de la caché.
    """
    mascota = mascota_actual()
    df = registro.cargar_intentos(app.config["RUTA_INTENTOS"])
    if df is None:
        return render_template("estadisticas.html", m=mascota, hay_datos=False)
    return render_template(
        "estadisticas.html", m=mascota, hay_datos=True,
        resumen=registro.resumen_por_nivel(df).to_dict("records"),
        totales=registro.totales(df), version=len(df),
    )


@app.route("/grafica.png")
def grafica():
    """GET /grafica.png — Genera al momento el PNG de la gráfica de intentos (404 si no hay datos)."""
    df = registro.cargar_intentos(app.config["RUTA_INTENTOS"])
    if df is None:
        abort(404)
    imagen = BytesIO()
    registro.crear_grafica(registro.resumen_por_nivel(df), imagen)
    imagen.seek(0)
    return send_file(imagen, mimetype="image/png")


if __name__ == "__main__":
    app.run(debug=True)
