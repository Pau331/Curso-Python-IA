"""Los niveles de la historia. Cada nivel es un dibujo hecho con letras:

    #  suelo            =  plataforma       o  moneda
    E  bicho enemigo    ^  pinchos          P  donde empieza la mascota
    M  meta (bandera)      (espacio) aire
"""

LEYENDA = {"#": "suelo", "=": "plataforma", "o": "moneda", "E": "enemigo",
           "^": "pinchos", "P": "inicio", "M": "meta"}

NIVELES = [
    {
        "nombre": "El parque",
        "tema": "parque",
        "historia": "Durante una excursión, {nombre} persigue una mariposa y, cuando se da cuenta, ya no ve a nadie. Su dueño le estará buscando. ¡Hay que volver a casa! Primero, cruzar el parque.",
        "colores": {"cielo": "#bfe3f5", "suelo": "#7cc46b", "suelo_oscuro": "#5a9e4b"},
        "mapa": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                                                  oooo",
            "              oooo                       oo       ====",
            "        oooo  ====   oo                                                   oooo",
            "",
            "  P                              E         ##################         E              M",
            "#####################  ##################  ###############################################",
            "#####################  ##################  ###############################################",
        ],
    },
    {
        "nombre": "El bosque",
        "tema": "bosque",
        "historia": "Al salir del parque empieza un bosque espeso. Huele a casa al otro lado… pero hay bichos merodeando entre los árboles.",
        "colores": {"cielo": "#cfe8d5", "suelo": "#4f8f5a", "suelo_oscuro": "#3b6e45"},
        "mapa": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                                 oooo",
            "                                 ====                          ooo",
            "               ooo                             ooo        oooo                   ooo",
            "      oooo                                                ====",
            "                               ########                                   E",
            "  P                     E      ########    E            E         ###############         E    M",
            "###############   #############################   #############   ###############   ################",
            "###############   #############################   #############   ###############   ################",
        ],
    },
    {
        "nombre": "La cueva",
        "tema": "cueva",
        "historia": "El camino más corto pasa por una cueva oscura. Cuidado con los pinchos del suelo: aquí no se ve muy bien.",
        "colores": {"cielo": "#3a3547", "suelo": "#7d6e9e", "suelo_oscuro": "#5d5078"},
        "mapa": [
            "####################################################################################################",
            "####################################################################################################",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                   oo              ooo      oo      oooo        oooo   ooo",
            "        ooo                                                     ====",
            "                                                   ######",
            "  P          E     ^^        E              ^^     ######     E   E             ^^     E       M",
            "###################################   #################################   ##########################",
            "###################################   #################################   ##########################",
        ],
    },
    {
        "nombre": "La ciudad",
        "tema": "ciudad",
        "historia": "¡Por fin la ciudad! Desde los tejados se ve el barrio de casa. Toca saltar de edificio en edificio.",
        "colores": {"cielo": "#ffd9b8", "suelo": "#8d8fa6", "suelo_oscuro": "#6c6e85"},
        "mapa": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                                         ooo           ooo",
            "                           ooo                                                     ooo",
            "             ooo                               ^   E       ooooo                               ooo",
            "                      E                     ###########                     E",
            "                ###########        E        ###########       E       #############       E",
            "  P             ###########   ###########   ###########   #########   #############   #########         M",
            "#############   ###########   ###########   ###########   #########   #############   #########   ############",
            "#############   ###########   ###########   ###########   #########   #############   #########   ############",
        ],
    },
    {
        "nombre": "El camino a casa",
        "tema": "casa",
        "historia": "Ya se ve su calle. Solo queda el último tramo, el más difícil. Al final, alguien le está esperando…",
        "colores": {"cielo": "#ffc9a8", "suelo": "#c98a5a", "suelo_oscuro": "#a06a42"},
        "mapa": [
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "                            oooooo ooo            oo                         ooo         ooo",
            "               ooo             E                               ooo",
            "                           ########                                                 E",
            "                       E   ########        E  E           E                     #########",
            "  P      E        #################   ########### ^^ ##########       E  ^E     #########        E  E    M",
            "###############   #################   #########################   ###########   #########   ##################",
            "###############   #################   #########################   ###########   #########   ##################",
        ],
    },
]


FINAL = ("Al doblar la esquina, {nombre} reconoce la puerta de casa. Su dueño está en el umbral, "
         "con los brazos abiertos y los ojos llorosos. ¡Por fin juntos otra vez!")


def total_niveles():
    """Cuántos niveles (capítulos) tiene la historia."""
    return len(NIVELES)


def obtener_nivel(numero):
    """Devuelve el diccionario del nivel `numero` (empezando a contar en 1).

    El diccionario tiene: nombre, tema, historia (con {nombre} para formatear),
    colores y mapa. Devuelve None si el número está fuera de rango.
    """
    if 1 <= numero <= len(NIVELES):
        return NIVELES[numero - 1]
    return None


def preparar_mapa(mapa):
    """Prepara un mapa de texto para enviarlo al juego (juego.js).

    Rellena con espacios las filas cortas para que todas midan lo mismo
    (el JS asume una cuadrícula rectangular) y cuenta monedas y enemigos.

    Returns:
        {"filas": [...], "ancho": columnas, "alto": filas,
         "monedas": nº de "o", "enemigos": nº de "E"}.
        El total de monedas también lo usa app.py para evitar trampas.
    """
    ancho = max(len(fila) for fila in mapa)
    filas = [fila.ljust(ancho) for fila in mapa]
    texto = "".join(filas)
    return {
        "filas": filas,
        "ancho": ancho,
        "alto": len(filas),
        "monedas": texto.count("o"),
        "enemigos": texto.count("E"),
    }


def comprobar_mapa(mapa):
    """Revisa que un mapa esté bien formado. La usan los tests.

    Comprueba que haya exactamente un inicio (P), exactamente una meta (M)
    y ningún símbolo que no esté en LEYENDA.
    Devuelve una lista de frases con los problemas (vacía si está bien).
    """
    problemas = []
    texto = "".join(mapa)
    if texto.count("P") != 1:
        problemas.append("Tiene que haber exactamente un inicio (P)")
    if texto.count("M") != 1:
        problemas.append("Tiene que haber exactamente una meta (M)")
    simbolos_raros = set(texto) - set(LEYENDA) - {" "}
    if simbolos_raros:
        problemas.append(f"Símbolos desconocidos: {sorted(simbolos_raros)}")
    return problemas
