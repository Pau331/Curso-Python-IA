from datetime import datetime, timedelta

import pytest

import mascota as reglas
import niveles
import registro
from app import app
from mascota import Mascota, cargar_mascota

AHORA = datetime(2026, 11, 24, 12, 0, 0)


def en_verde(**cambios):
    """Una mascota con todas las barras en verde (salvo lo que se cambie)."""
    return Mascota("Bruno", **{"comida": 90, "energia": 90, "diversion": 90, "limpieza": 90, **cambios})


# --- El paso del tiempo ---------------------------------------------------------------


def test_el_tiempo_baja_las_necesidades():
    m = Mascota("Bruno", ultima_visita="2026-11-24T10:00:00")
    m.pasar_tiempo(AHORA)  # dos horas después
    assert m.comida == 80 - 6 * 2
    assert m.energia == 80 - 4 * 2


def test_las_necesidades_no_bajan_de_cero():
    m = Mascota("Bruno", ultima_visita="2026-11-01T10:00:00")
    m.pasar_tiempo(AHORA)
    assert m.comida == 0 and m.limpieza == 0


# --- Cuidados: cada uno tarda unos segundos ------------------------------------------------


def test_comer_gasta_la_comida_del_inventario():
    m = Mascota("Bruno", comida=50, inventario={"manzana": 2})
    m.comer("manzana", AHORA)
    assert m.comida == 50 + reglas.COMIDAS["manzana"]["comida"] and m.inventario["manzana"] == 1


def test_los_cuidados_tardan_entre_2_y_6_segundos():
    assert all(2 <= segundos <= 6 for segundos in reglas.DURACIONES.values())


def test_mientras_come_esta_ocupado():
    m = Mascota("Bruno", comida=10, inventario={"manzana": 2})
    m.comer("manzana", AHORA)
    accion, falta = m.ocupado(AHORA + timedelta(seconds=1))
    assert accion == "comer" and falta == reglas.DURACIONES["comer"] - 1
    assert m.ocupado(AHORA + timedelta(seconds=reglas.DURACIONES["comer"])) is None


def test_no_se_puede_hacer_otra_cosa_a_la_vez():
    m = Mascota("Bruno", limpieza=10, energia=30)
    m.banar(AHORA)
    mensaje = m.siesta(AHORA + timedelta(seconds=2))
    assert "bañándose" in mensaje
    assert m.energia == 30  # no ha dormido
    m.siesta(AHORA + timedelta(seconds=reglas.DURACIONES["banar"]))
    assert m.energia == 70


def test_no_puede_salir_de_aventura_a_mitad_de_un_cuidado():
    m = en_verde()
    m.banar()
    puede, motivo = m.puede_jugar()
    assert not puede and "bañándose" in motivo


def test_cara_de_dormido_durante_la_siesta():
    m = Mascota("Bruno", energia=30)
    m.siesta()
    assert m.animo() == "dormido"


def test_comprar_comida():
    m = Mascota("Bruno", monedas=12, inventario={})
    m.comprar("bocadillo")
    assert m.monedas == 0 and m.inventario["bocadillo"] == 1
    assert "No tienes monedas" in m.comprar("manzana")


# --- Decoración ---------------------------------------------------------------------------


def test_comprar_decoracion():
    m = Mascota("Bruno", monedas=100)
    m.comprar_decoracion("planta")
    assert "planta" in m.decoraciones and m.monedas == 60
    assert "Ya tienes" in m.comprar_decoracion("planta")


def test_el_castillo_exclusivo_es_caro():
    m = Mascota("Bruno", monedas=299)
    assert "Te faltan 1 monedas" in m.comprar_decoracion("castillo")
    assert "castillo" not in m.decoraciones


def test_el_trofeo_no_se_puede_comprar():
    m = Mascota("Bruno", monedas=10_000)
    assert "hay que ganárselo" in m.comprar_decoracion("trofeo")


def test_ganar_el_trofeo_por_velocidad():
    m = en_verde(nivel_desbloqueado=5,
                 mejores_tiempos={"1": 30, "2": 30, "3": 30, "4": 30})
    novedades = m.terminar_nivel(5, True, 0, segundos=40, vidas_perdidas=0, total_niveles=5)
    assert m.tiempo_total(5) == 160
    assert "trofeo" in m.decoraciones
    assert any("Trofeo" in n for n in novedades)


def test_sin_trofeo_si_es_demasiado_lento():
    m = en_verde(nivel_desbloqueado=5,
                 mejores_tiempos={"1": 50, "2": 50, "3": 50, "4": 50})
    m.terminar_nivel(5, True, 0, segundos=50, vidas_perdidas=0, total_niveles=5)
    assert "trofeo" not in m.decoraciones


def test_las_gafas_no_se_pueden_comprar():
    m = Mascota("Bruno", monedas=10_000)
    assert "hay que ganárselo" in m.comprar_decoracion("gafas")


def test_ganar_las_gafas_sin_perder_vidas():
    m = en_verde(nivel_desbloqueado=5, niveles_sin_fallos=["1", "2", "3", "4"])
    novedades = m.terminar_nivel(5, True, 0, segundos=60, vidas_perdidas=0, total_niveles=5)
    assert m.lleva_gafas()
    assert any("Gafas" in n for n in novedades)


def test_sin_gafas_si_pierde_una_vida():
    m = en_verde(nivel_desbloqueado=5, niveles_sin_fallos=["1", "2", "3", "4"])
    m.terminar_nivel(5, True, 0, segundos=60, vidas_perdidas=1, total_niveles=5)
    assert not m.lleva_gafas()
    assert "5" not in m.niveles_sin_fallos


def test_repetir_un_nivel_sin_fallos_cuenta_para_las_gafas():
    m = en_verde(historia_terminada=True, nivel_desbloqueado=5,
                 niveles_sin_fallos=["1", "2", "4", "5"])
    m.terminar_nivel(3, True, 0, segundos=60, vidas_perdidas=0, total_niveles=5)
    assert m.lleva_gafas()


def test_completar_da_premio_y_repetir_tambien():
    m = en_verde(monedas=0, historia_terminada=True, nivel_desbloqueado=5)
    m.terminar_nivel(5, True, 7, segundos=60, vidas_perdidas=0, total_niveles=5)
    assert m.monedas == 7 + reglas.premio_nivel(5)
    m.terminar_nivel(5, True, 7, segundos=60, vidas_perdidas=0, total_niveles=5)
    assert m.monedas == 2 * (7 + reglas.premio_nivel(5))


def test_sin_premio_si_no_llega_a_la_meta():
    m = en_verde(monedas=0)
    m.terminar_nivel(1, False, 3, segundos=20, vidas_perdidas=3, total_niveles=5)
    assert m.monedas == 3


def test_se_guarda_el_mejor_tiempo():
    m = en_verde()
    m.terminar_nivel(1, True, 0, segundos=50, vidas_perdidas=0, total_niveles=5)
    m.terminar_nivel(1, True, 0, segundos=40, vidas_perdidas=0, total_niveles=5)
    m.terminar_nivel(1, True, 0, segundos=45, vidas_perdidas=0, total_niveles=5)
    assert m.mejores_tiempos["1"] == 40


# --- Aventura: desgaste y vidas -----------------------------------------------------------


def test_una_aventura_desgasta_mucho():
    m = en_verde()
    m.terminar_nivel(1, True, 0, 30, 0, 5)
    gasto_esperado = reglas.COSTE_AVENTURA["energia"] + reglas.EXTRA_POR_NIVEL * 1
    assert m.energia == 90 - gasto_esperado
    assert not m.todas_en_verde()


def test_los_niveles_avanzados_cansan_mas():
    a, b = en_verde(), en_verde()
    a.terminar_nivel(1, True, 0, 30, 0, 5)
    b.terminar_nivel(5, True, 0, 30, 0, 5)
    assert b.energia < a.energia


def test_hay_que_cuidarla_entre_niveles():
    m = Mascota("Bruno")  # empieza con todo a 80
    m.terminar_nivel(1, True, 0, 30, 0, 5)
    m.terminar_nivel(2, True, 0, 30, 0, 5)
    puede, motivo = m.puede_jugar()
    assert not puede


def test_las_vidas_perdidas_no_se_recuperan_solas():
    m = en_verde()
    m.terminar_nivel(1, True, 0, 30, vidas_perdidas=2, total_niveles=5)
    assert m.vidas == 1
    assert not m.empezar_aventura()  # las barras ya no están en verde tras la aventura
    assert m.vidas == 1


def test_con_todo_en_verde_recupera_las_vidas():
    m = en_verde(vidas=1)
    assert m.empezar_aventura()
    assert m.vidas == reglas.VIDAS_MAX


def test_perder_el_nivel_deja_sin_vidas():
    m = en_verde()
    m.terminar_nivel(1, False, 3, 20, 3, 5)
    assert m.vidas == 0 and m.monedas == 10 + 3


def test_sin_vidas_solo_puede_salir_con_todo_en_verde():
    m = Mascota("Bruno", comida=50, energia=50, diversion=50, limpieza=50, vidas=0)
    puede, motivo = m.puede_jugar()
    assert not puede and "verde" in motivo
    assert en_verde(vidas=0).puede_jugar()[0]


@pytest.mark.parametrize("necesidad", reglas.NECESIDADES)
def test_cualquier_barra_en_rojo_impide_salir(necesidad):
    assert not en_verde(**{necesidad: 10}).puede_jugar()[0]


def test_completar_desbloquea_y_el_ultimo_termina_la_historia():
    m = en_verde()
    m.terminar_nivel(1, True, 0, 30, 0, 5)
    assert m.nivel_desbloqueado == 2
    m = en_verde(nivel_desbloqueado=5)
    m.terminar_nivel(5, True, 0, 30, 0, 5)
    assert m.historia_terminada


@pytest.mark.parametrize("valor, color", [(100, "verde"), (60, "verde"), (59, "amarillo"), (30, "amarillo"), (29, "rojo")])
def test_color_de_las_barras(valor, color):
    assert reglas.color_de(valor) == color


@pytest.mark.parametrize("cambios, animo", [
    ({}, "feliz"), ({"limpieza": 10}, "sucio"), ({"comida": 10}, "triste"), ({"comida": 50}, "normal"),
])
def test_animo(cambios, animo):
    assert en_verde(**cambios).animo() == animo


def test_guardar_y_cargar(tmp_path):
    ruta = tmp_path / "partida.json"
    m = Mascota("Bruno", monedas=42)
    m.comer("manzana", AHORA)
    m.guardar(ruta)
    copia = cargar_mascota(ruta)
    assert copia.monedas == 42 and copia.actividad == m.actividad


def test_partida_estropeada(tmp_path):
    ruta = tmp_path / "partida.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    assert cargar_mascota(ruta) is None


# --- Los niveles ----------------------------------------------------------------------


@pytest.mark.parametrize("numero", range(1, niveles.total_niveles() + 1))
def test_los_mapas_estan_bien(numero):
    nivel = niveles.obtener_nivel(numero)
    assert niveles.comprobar_mapa(nivel["mapa"]) == []
    mapa = niveles.preparar_mapa(nivel["mapa"])
    assert mapa["alto"] == 15
    assert all(len(fila) == mapa["ancho"] for fila in mapa["filas"])


def test_detecta_mapas_mal_hechos():
    assert len(niveles.comprobar_mapa(["P  X", "####"])) == 2


# --- El registro ----------------------------------------------------------------------


def test_registro_y_resumen(tmp_path):
    ruta = tmp_path / "intentos.csv"
    registro.guardar_intento(1, "El parque", False, 3, 20, 3, ruta)
    registro.guardar_intento(1, "El parque", True, 15, 41.5, 1, ruta)
    registro.guardar_intento(1, "El parque", True, 18, 35.0, 0, ruta)
    resumen = registro.resumen_por_nivel(registro.cargar_intentos(ruta)).iloc[0]
    assert resumen["intentos"] == 3 and resumen["completados"] == 2
    assert resumen["exito"] == 67 and resumen["mejor_tiempo"] == 35.0


# --- La web -----------------------------------------------------------------------------


@pytest.fixture
def cliente(tmp_path):
    app.config.update(TESTING=True, RUTA_PARTIDA=tmp_path / "partida.json",
                      RUTA_INTENTOS=tmp_path / "intentos.csv")
    cliente = app.test_client()
    cliente.post("/nueva", data={"nombre": "Bruno"})
    return cliente


def partida():
    return cargar_mascota(app.config["RUTA_PARTIDA"])


def test_cuidar_y_esperar_a_que_termine(cliente):
    cliente.post("/cuidar", data={"accion": "jugar"})
    diversion = partida().diversion
    html = cliente.post("/cuidar", data={"accion": "banar"}, follow_redirects=True).get_data(as_text=True)
    assert "Espera a que termine" in html
    assert "Jugando…" in html and "progreso" in html
    assert partida().diversion == diversion


def test_aventura_bloqueada_mientras_hace_algo(cliente):
    cliente.post("/cuidar", data={"accion": "siesta"})
    html = cliente.get("/").get_data(as_text=True)
    assert "bloqueada" in html and 'href="/historia"><span class="icono-accion">' not in html
    respuesta = cliente.get("/nivel/1")
    assert respuesta.status_code == 302  # no deja entrar en el nivel
    assert "durmiendo" in cliente.get("/historia").get_data(as_text=True)


def test_comprar_decoracion_desde_la_web(cliente):
    m = partida(); m.monedas = 100; m.guardar(app.config["RUTA_PARTIDA"])
    cliente.post("/cuidar", data={"accion": "decorar", "objeto": "planta"})
    assert "planta" in partida().decoraciones
    assert "deco-planta" in cliente.get("/").get_data(as_text=True)


def test_niveles_bloqueados(cliente):
    assert cliente.get("/nivel/1").status_code == 200
    assert cliente.get("/nivel/3").status_code == 302


def test_terminar_nivel_sin_trampas(cliente):
    respuesta = cliente.post("/nivel/1/terminar", json={
        "completado": True, "monedas": 9999, "segundos": 30, "vidas_perdidas": 1})
    assert respuesta.status_code == 200
    total = niveles.preparar_mapa(niveles.obtener_nivel(1)["mapa"])["monedas"]
    m = partida()
    assert m.monedas == 10 + total + reglas.premio_nivel(1) and m.vidas == 2 and m.nivel_desbloqueado == 2


def test_resultado_mal_formado(cliente):
    assert cliente.post("/nivel/1/terminar", json={"hola": 1}).status_code == 400


def test_estadisticas_y_final(cliente):
    assert "Todavía no has jugado" in cliente.get("/estadisticas").get_data(as_text=True)
    cliente.post("/nivel/1/terminar", json={"completado": False, "monedas": 2, "segundos": 9, "vidas_perdidas": 3})
    assert cliente.get("/grafica.png").mimetype == "image/png"
    assert cliente.get("/final").status_code == 302
