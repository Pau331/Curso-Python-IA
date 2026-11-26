"""La mascota: sus necesidades, sus vidas, la tienda, la decoración y cómo se guarda."""

import json
from datetime import datetime, timedelta
from pathlib import Path

RUTA_PARTIDA = Path(__file__).parent / "datos" / "partida.json"

# --- Reglas del juego (se pueden ajustar aquí) -----------------------------------------

NECESIDADES = ["comida", "energia", "diversion", "limpieza"]

# Cuánto baja cada necesidad por cada hora que pasa (de 0 a 100)
BAJADA_POR_HORA = {"comida": 6, "energia": 4, "diversion": 5, "limpieza": 3}

# Lo que gasta una aventura: tanto que, aunque salga con todo a 100, siempre vuelve con
# alguna barra fuera del verde (y no recupera vidas sin cuidarla). Los niveles avanzados cansan más:
# a esto se le suma EXTRA_POR_NIVEL por el número del nivel.
COSTE_AVENTURA = {"comida": 35, "energia": 40, "limpieza": 35}
EXTRA_POR_NIVEL = 2

VERDE = 60                 # a partir de aquí la barra está "en verde"
MINIMO_AVENTURA = 30       # con alguna barra por debajo, no puede salir de aventura
VIDAS_MAX = 3

# Segundos que tarda cada cuidado. Mientras tanto la mascota está ocupada
# y no se le puede mandar otra cosa.
DURACIONES = {"comer": 2, "jugar": 4, "banar": 5, "siesta": 6}
ACTIVIDADES = {  # cómo se describe en pantalla lo que está haciendo
    "comer": ("Comiendo", "🍽️"), "jugar": ("Jugando", "⚽"),
    "banar": ("Bañándose", "🫧"), "siesta": ("Durmiendo", "💤"),
}

COMIDAS = {
    "manzana": {"nombre": "Manzana", "icono": "🍎", "precio": 5, "comida": 20, "diversion": 0},
    "bocadillo": {"nombre": "Bocadillo", "icono": "🥪", "precio": 12, "comida": 55, "diversion": 0},
    "tarta": {"nombre": "Tarta", "icono": "🍰", "precio": 20, "comida": 45, "diversion": 20},
}

# Premio en monedas por llegar a la meta, además de las que recoja por el camino.
# Se gana cada vez (también al repetir un capítulo ya superado) y crece con el nivel,
# así que repetir los últimos capítulos es la forma de ahorrar para la decoración cara.
PREMIO_POR_NIVEL = 10


def premio_nivel(numero):
    """Monedas de premio por completar el nivel `numero` (10, 20, 30…)."""
    return PREMIO_POR_NIVEL * numero


LIMITE_TROFEO = 180  # segundos: sumando el mejor tiempo de cada nivel

DECORACIONES = {
    "planta": {"nombre": "Planta", "icono": "🪴", "precio": 40},
    "osito": {"nombre": "Osito de peluche", "icono": "🧸", "precio": 80},
    "pecera": {"nombre": "Pecera", "icono": "🐠", "precio": 150},
    "castillo": {"nombre": "Castillo de juguete", "icono": "🏰", "precio": 300, "exclusivo": True},
    "trofeo": {"nombre": "Trofeo de velocidad", "icono": "🏆", "precio": None, "exclusivo": True,
               "como": f"Supera los 5 capítulos en menos de {LIMITE_TROFEO // 60} minutos en total "
                       "(sumando tu mejor tiempo de cada uno)."},
    # Las gafas no se ponen en la habitación: las lleva puestas la mascota.
    "gafas": {"nombre": "Gafas de pro", "icono": "🕶️", "precio": None, "exclusivo": True,
              "como": "Supera los 5 capítulos sin perder ninguna vida en cada uno."},
}


def limitar(valor):
    """Redondea un valor a entero y lo recorta al rango 0-100 (el de las barras)."""
    return max(0, min(100, round(valor)))


def color_de(valor):
    """El color de una barra según su valor.

    "verde" si es >= VERDE (60), "amarillo" si es >= MINIMO_AVENTURA (30)
    y "rojo" por debajo. Se usa en la plantilla de casa para pintar las barras.
    """
    if valor >= VERDE:
        return "verde"
    if valor >= MINIMO_AVENTURA:
        return "amarillo"
    return "rojo"


class Mascota:
    """Todo el estado de la partida: la mascota, su dinero, su casa y su progreso.

    Los métodos que cambian el estado no guardan nada: hay que llamar a
    guardar() después. Los que dependen de la hora aceptan un parámetro
    `ahora` opcional para que los tests puedan fijar el reloj.
    """

    def __init__(self, nombre, comida=80, energia=80, diversion=80, limpieza=80,
                 monedas=10, inventario=None, vidas=VIDAS_MAX, actividad=None,
                 decoraciones=None, mejores_tiempos=None, nivel_desbloqueado=1,
                 historia_terminada=False, niveles_sin_fallos=None, ultima_visita=None):
        """Crea una mascota nueva o reconstruye una guardada.

        Los nombres de los parámetros coinciden con las claves del JSON de la
        partida, por eso cargar_mascota() puede hacer Mascota(**datos).

        Args:
            nombre: nombre que le ha puesto el jugador.
            comida, energia, diversion, limpieza: necesidades de 0 a 100.
            monedas: dinero para la tienda.
            inventario: {clave_de_comida: cantidad}. Por defecto, 2 manzanas.
            vidas: vidas para los niveles (máximo VIDAS_MAX).
            actividad: {"accion": ..., "hasta": fecha ISO} si está ocupada, o None.
            decoraciones: lista de claves de DECORACIONES que tiene en casa.
            mejores_tiempos: {"número de nivel" (texto): segundos}.
            nivel_desbloqueado: el nivel más alto al que puede entrar.
            historia_terminada: True cuando ha superado el último nivel.
            niveles_sin_fallos: números de nivel (texto) superados sin perder ninguna vida.
            ultima_visita: fecha ISO de la última vez que se calculó el paso del tiempo.
        """
        self.nombre = nombre
        self.comida = comida
        self.energia = energia
        self.diversion = diversion
        self.limpieza = limpieza
        self.monedas = monedas
        self.inventario = inventario or {"manzana": 2}
        self.vidas = vidas
        self.actividad = actividad                    # lo que está haciendo y hasta cuándo
        self.decoraciones = decoraciones or []        # lo que tiene puesto en casa
        self.mejores_tiempos = mejores_tiempos or {}  # nivel -> mejor tiempo en segundos
        self.nivel_desbloqueado = nivel_desbloqueado
        self.historia_terminada = historia_terminada
        self.niveles_sin_fallos = niveles_sin_fallos or []  # para las gafas de pro
        self.ultima_visita = ultima_visita or datetime.now().isoformat(timespec="seconds")

    # --- El paso del tiempo ---------------------------------------------------------

    def pasar_tiempo(self, ahora=None):
        """Baja las necesidades según las horas que han pasado desde la última visita.

        Cada necesidad baja BAJADA_POR_HORA[necesidad] puntos por hora (admite
        fracciones de hora) y nunca baja de 0. Después actualiza ultima_visita
        a `ahora`, así que llamarla dos veces seguidas no descuenta dos veces.
        """
        ahora = ahora or datetime.now()
        horas = (ahora - datetime.fromisoformat(self.ultima_visita)).total_seconds() / 3600
        if horas > 0:
            for necesidad, bajada in BAJADA_POR_HORA.items():
                setattr(self, necesidad, limitar(getattr(self, necesidad) - bajada * horas))
        self.ultima_visita = ahora.isoformat(timespec="seconds")

    # --- Lo que está haciendo (cada cuidado tarda unos segundos) ---------------------

    def ocupado(self, ahora=None):
        """Comprueba si la mascota está en mitad de un cuidado.

        Devuelve (accion, segundos_que_faltan) si está ocupada, o None si está
        libre. Si la actividad ya terminó, la borra (efecto secundario) y
        devuelve None.
        """
        if not self.actividad:
            return None
        ahora = ahora or datetime.now()
        falta = (datetime.fromisoformat(self.actividad["hasta"]) - ahora).total_seconds()
        if falta <= 0:
            self.actividad = None  # ya ha terminado
            return None
        return self.actividad["accion"], falta

    def _empezar(self, accion, ahora):
        """Marca a la mascota como ocupada con `accion` durante DURACIONES[accion] segundos."""
        hasta = ahora + timedelta(seconds=DURACIONES[accion])
        self.actividad = {"accion": accion, "hasta": hasta.isoformat(timespec="milliseconds")}

    def _aviso_ocupado(self, ahora):
        """Frase para el jugador si está ocupada (p. ej. "Bruno está comiendo. Espera…").

        Devuelve None si está libre. La usan todos los cuidados para no
        solaparse entre sí.
        """
        en_curso = self.ocupado(ahora)
        if en_curso:
            texto = ACTIVIDADES[en_curso[0]][0].lower()
            return f"{self.nombre} está {texto}. Espera a que termine."
        return None

    # --- Cuidados ---------------------------------------------------------------------

    def comer(self, clave, ahora=None):
        """Le da de comer una unidad de la comida `clave` del inventario.

        No hace nada (y explica por qué) si está ocupada, si no queda esa comida
        o si ya está llena. Si come: gasta 1 del inventario, sube comida y
        diversión según COMIDAS[clave] y la deja ocupada "comiendo".
        Devuelve siempre el mensaje que se mostrará en pantalla.
        """
        ahora = ahora or datetime.now()
        if self._aviso_ocupado(ahora):
            return self._aviso_ocupado(ahora)
        if self.inventario.get(clave, 0) == 0:
            return "No te queda esa comida. Cómprala en la tienda."
        if self.comida >= 100:
            return f"{self.nombre} está lleno. ¡No puede más!"
        comida = COMIDAS[clave]
        self.inventario[clave] -= 1
        self.comida = limitar(self.comida + comida["comida"])
        self.diversion = limitar(self.diversion + comida["diversion"])
        self._empezar("comer", ahora)
        return f"¡Ñam! {self.nombre} se ha comido {comida['nombre'].lower()}."

    def banar(self, ahora=None):
        """La baña: limpieza a 100, diversión -5 y queda ocupada "bañándose".

        Si ya está ocupada, no hace nada. Devuelve el mensaje para el jugador.
        """
        ahora = ahora or datetime.now()
        if self._aviso_ocupado(ahora):
            return self._aviso_ocupado(ahora)
        self.limpieza = 100
        self.diversion = limitar(self.diversion - 5)  # no le encanta el agua
        self._empezar("banar", ahora)
        return f"{self.nombre} está limpísimo (aunque refunfuña un poco)."

    def jugar(self, ahora=None):
        """Juega con ella: diversión +25, energía -8, comida -5; queda ocupada "jugando".

        No juega si está ocupada o si tiene menos de 10 de energía.
        Devuelve el mensaje para el jugador.
        """
        ahora = ahora or datetime.now()
        if self._aviso_ocupado(ahora):
            return self._aviso_ocupado(ahora)
        if self.energia < 10:
            return f"{self.nombre} está demasiado cansado para jugar."
        self.diversion = limitar(self.diversion + 25)
        self.energia = limitar(self.energia - 8)
        self.comida = limitar(self.comida - 5)
        self._empezar("jugar", ahora)
        return f"¡{self.nombre} persigue la pelota encantado!"

    def siesta(self, ahora=None):
        """Echa una siesta: energía +40, comida -5; queda ocupada "durmiendo".

        No duerme si está ocupada o si ya tiene la energía a 100.
        Devuelve el mensaje para el jugador.
        """
        ahora = ahora or datetime.now()
        if self._aviso_ocupado(ahora):
            return self._aviso_ocupado(ahora)
        if self.energia >= 100:
            return f"{self.nombre} no tiene sueño."
        self.energia = limitar(self.energia + 40)
        self.comida = limitar(self.comida - 5)
        self._empezar("siesta", ahora)
        return f"{self.nombre} se echa una siesta y recupera energía. Zzz…"

    # --- Tienda -------------------------------------------------------------------------

    def comprar(self, clave):
        """Compra una unidad de la comida `clave` y la añade al inventario.

        Resta su precio de las monedas; si no llega, no compra nada.
        Comprar no cuenta como cuidado, así que se puede hacer aunque esté ocupada.
        Devuelve el mensaje para el jugador.
        """
        comida = COMIDAS[clave]
        if self.monedas < comida["precio"]:
            return "No tienes monedas suficientes. Consíguelas en los niveles."
        self.monedas -= comida["precio"]
        self.inventario[clave] = self.inventario.get(clave, 0) + 1
        return f"Has comprado {comida['nombre'].lower()}."

    def comprar_decoracion(self, clave):
        """Compra el objeto de decoración `clave` y lo pone en la casa.

        No lo compra si ya lo tiene, si no se vende (precio None, como el
        trofeo, que hay que ganarse) o si faltan monedas (dice cuántas).
        Devuelve el mensaje para el jugador.
        """
        objeto = DECORACIONES[clave]
        if clave in self.decoraciones:
            return f"Ya tienes {objeto['nombre'].lower()} en casa."
        if objeto["precio"] is None:
            return f"{objeto['nombre']} no se puede comprar: hay que ganárselo."
        if self.monedas < objeto["precio"]:
            return f"Te faltan {objeto['precio'] - self.monedas} monedas para {objeto['nombre'].lower()}."
        self.monedas -= objeto["precio"]
        self.decoraciones.append(clave)
        return f"¡{objeto['nombre']} ya decora la casa de {self.nombre}!"

    # --- Aventura ------------------------------------------------------------------------

    def necesidades(self):
        """Las cuatro barras como diccionario: {"comida": 80, "energia": 75, ...}."""
        return {n: getattr(self, n) for n in NECESIDADES}

    def todas_en_verde(self):
        """True si las cuatro necesidades están en VERDE (>= 60) o más."""
        return all(valor >= VERDE for valor in self.necesidades().values())

    def puede_jugar(self):
        """Decide si puede salir de aventura (entrar en un nivel) ahora mismo.

        No puede si: está en mitad de un cuidado, alguna necesidad está por
        debajo de MINIMO_AVENTURA (30), o no le quedan vidas y no tiene todas
        las barras en verde (con todo en verde las recuperará al salir).

        Devuelve (True, "") o (False, motivo) con la frase que se muestra.
        """
        if self._aviso_ocupado(datetime.now()):  # no puede irse a mitad de un cuidado
            return False, self._aviso_ocupado(datetime.now())
        motivos = {
            "comida": "tiene demasiada hambre", "energia": "está demasiado cansado",
            "diversion": "está demasiado triste", "limpieza": "está demasiado sucio",
        }
        for necesidad, valor in self.necesidades().items():
            if valor < MINIMO_AVENTURA:
                return False, f"{self.nombre} {motivos[necesidad]} para salir de aventura."
        if self.vidas == 0 and not self.todas_en_verde():
            return False, (f"A {self.nombre} no le quedan vidas. Pon todas sus barras en verde "
                           "y las recuperará al salir.")
        return True, ""

    def empezar_aventura(self):
        """Se llama al entrar en un nivel: si todo está en verde, recupera todas las vidas.

        Es la única forma de recuperar vidas: tenerla bien cuidada al salir.
        Devuelve True si ha recuperado vidas (para avisar al jugador).
        """
        if self.todas_en_verde() and self.vidas < VIDAS_MAX:
            self.vidas = VIDAS_MAX
            return True
        return False

    def terminar_nivel(self, numero, completado, monedas, segundos, vidas_perdidas, total_niveles):
        """Aplica a la mascota el resultado de jugar un nivel.

        Siempre: gasta comida, energía y limpieza (COSTE_AVENTURA + EXTRA_POR_NIVEL
        por el número del nivel) y suma las monedas recogidas.

        Si lo completó: suma el premio del nivel (premio_nivel), resta las vidas perdidas, diversión +10, desbloquea el
        siguiente nivel (si era el último desbloqueado), marca la historia como
        terminada (si era el último nivel), guarda el mejor tiempo y, si cumple
        el límite, le da el trofeo. Si no perdió ninguna vida, apunta el nivel
        como "sin fallos" y, cuando lo están todos, le da las gafas de pro.
        Si no: se queda con 0 vidas y diversión -15.

        Args:
            numero: número del nivel jugado (desde 1).
            completado: si llegó a la meta.
            monedas, segundos, vidas_perdidas: lo que envía el juego (ya validado).
            total_niveles: cuántos niveles hay en total.

        Returns:
            Lista de frases extra para mostrar (p. ej. que ha ganado el trofeo).
        """
        novedades = []
        for necesidad, gasto in COSTE_AVENTURA.items():
            nuevo = getattr(self, necesidad) - gasto - EXTRA_POR_NIVEL * numero
            setattr(self, necesidad, limitar(nuevo))
        self.monedas += monedas

        if completado:
            self.monedas += premio_nivel(numero)
            self.vidas = max(0, self.vidas - vidas_perdidas)
            self.diversion = limitar(self.diversion + 10)
            if numero == self.nivel_desbloqueado and numero < total_niveles:
                self.nivel_desbloqueado += 1
            if numero == total_niveles:
                self.historia_terminada = True
            clave = str(numero)  # en JSON las claves siempre son texto
            if clave not in self.mejores_tiempos or segundos < self.mejores_tiempos[clave]:
                self.mejores_tiempos[clave] = round(segundos, 1)
            if self.gana_trofeo(total_niveles):
                self.decoraciones.append("trofeo")
                novedades.append("¡Has ganado el Trofeo de velocidad! Ya está en su casa.")
            if vidas_perdidas == 0 and clave not in self.niveles_sin_fallos:
                self.niveles_sin_fallos.append(clave)
            if self.gana_gafas(total_niveles):
                self.decoraciones.append("gafas")
                novedades.append(f"¡{self.nombre} ha ganado las Gafas de pro por no perder ni una vida!")
        else:
            self.vidas = 0
            self.diversion = limitar(self.diversion - 15)
        return novedades

    def tiempo_total(self, total_niveles):
        """Suma de los mejores tiempos, o None si aún no ha superado todos los niveles."""
        if len(self.mejores_tiempos) < total_niveles:
            return None
        return round(sum(self.mejores_tiempos.values()), 1)

    def gana_trofeo(self, total_niveles):
        """True si merece el trofeo ahora: aún no lo tiene, ha superado todos los
        niveles y la suma de sus mejores tiempos es <= LIMITE_TROFEO segundos."""
        total = self.tiempo_total(total_niveles)
        return "trofeo" not in self.decoraciones and total is not None and total <= LIMITE_TROFEO

    def gana_gafas(self, total_niveles):
        """True si merece las gafas de pro ahora: aún no las tiene y ha superado
        todos los niveles sin perder ninguna vida (cada uno, en algún intento)."""
        return "gafas" not in self.decoraciones and len(self.niveles_sin_fallos) >= total_niveles

    def lleva_gafas(self):
        """True si la mascota lleva puestas las gafas de pro."""
        return "gafas" in self.decoraciones

    # --- Cómo se siente --------------------------------------------------------------

    def animo(self):
        """Decide qué cara pone la mascota en casa.

        Por orden de prioridad: "dormido" (si está en la siesta), "sucio"
        (limpieza < 30), "triste" (cualquier otra barra < 30), "feliz" (todas
        en verde) o "normal" en el resto de casos.
        """
        en_curso = self.ocupado()
        if en_curso and en_curso[0] == "siesta":
            return "dormido"
        valores = self.necesidades()
        if self.limpieza < MINIMO_AVENTURA:
            return "sucio"
        if min(valores.values()) < MINIMO_AVENTURA:
            return "triste"
        if self.todas_en_verde():
            return "feliz"
        return "normal"

    def aviso(self):
        """El "bocadillo de texto" de la mascota: lo que más necesita ahora mismo.

        Mira la necesidad más baja; si no está en verde devuelve su frase
        (p. ej. "Tengo hambre…"). Si todo está en verde, devuelve None.
        """
        frases = {
            "comida": "Tengo hambre…", "energia": "Tengo mucho sueño…",
            "diversion": "Me aburro… ¿jugamos?", "limpieza": "¡Necesito un baño!",
        }
        necesidad, valor = min(self.necesidades().items(), key=lambda par: par[1])
        if valor < VERDE:
            return frases[necesidad]
        return None

    # --- Guardar y cargar ---------------------------------------------------------

    def guardar(self, ruta=RUTA_PARTIDA):
        """Escribe todos los atributos de la mascota en un JSON (sobrescribe la partida).

        Crea la carpeta si no existe. Lo que se guarda es vars(self), así que
        cualquier atributo nuevo que se añada en __init__ se guardará solo.
        """
        Path(ruta).parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as fichero:
            json.dump(vars(self), fichero, ensure_ascii=False, indent=2)


def cargar_mascota(ruta=RUTA_PARTIDA):
    """Lee la partida guardada y devuelve la Mascota.

    Devuelve None si no hay partida, si el JSON está estropeado o si tiene
    claves que Mascota no reconoce. La web interpreta None como "crear
    una mascota nueva".
    """
    try:
        with open(ruta, encoding="utf-8") as fichero:
            return Mascota(**json.load(fichero))
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return None
