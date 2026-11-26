# Rumbo a casa

Juego web hecho con Python y Flask. Mezcla una **mascota virtual** a la que hay que cuidar
con un **juego de plataformas** por capítulos: la mascota se ha perdido en una excursión
y tiene que cruzar cinco niveles para volver con su dueño.

## Cómo se usa

```powershell
pip install -r requirements.txt
python app.py
```

Abre **http://127.0.0.1:5000** en el navegador.

- **Casa**: ves cómo está tu mascota (comida, energía, diversión y limpieza) y sus vidas.
  Puedes darle de comer, bañarla, jugar con ella o echarle una siesta. Cada cuidado
  **tarda unos segundos** (se ve lo que está haciendo) y mientras tanto no se le puede
  mandar otra cosa. En la tienda compras comida y
  **decoración** para su casa con las monedas de los niveles.
- **Aventura**: el camino con los 5 capítulos (el parque, el bosque, la cueva, la ciudad y
  el camino a casa). Cada uno se desbloquea al superar el anterior.
- **Niveles**: ← → para moverte y espacio (o ↑) para saltar. En el móvil salen botones.
  Salta encima de los bichos, esquiva pinchos y agujeros, recoge monedas y llega a la bandera.
- **Estadísticas**: intentos, % de éxito, mejores tiempos y monedas de cada nivel.

Tests: `pytest`

### Las reglas

- **Barras**: verde (60 o más), amarillo (30-59) y rojo (menos de 30). Bajan con el **tiempo
  real**, aunque cierres el juego.
- **Cada aventura desgasta mucho** comida, energía y limpieza, y más cuanto más avanzado es
  el nivel. Con **alguna barra en rojo no puede salir**, así que hay que cuidarla entre niveles.
- **Vidas (3 como máximo)**: las que pierdes en un nivel **no se recuperan** en el siguiente.
  Solo vuelve a tener las 3 si sale de aventura con **las cuatro barras en verde**. Si se queda
  sin vidas, no puede salir hasta ponerlo todo en verde.
- **Cada cuidado tarda un poco**: comer 2 s, jugar 4 s, bañarse 5 s y siesta 6 s. Mientras
  lo hace se ve en un bocadillo con una barra de progreso, la mascota se anima (mastica,
  salta, se sacude o duerme) y Python no deja mandarle otra cosa ni **salir de aventura**
  hasta que termina.
- **Decoración**: planta, osito y pecera se compran con monedas. Hay dos **exclusivos**: el
  castillo de juguete (300 monedas) y el **trofeo de velocidad**, que no se compra: se gana
  superando los 5 capítulos en menos de 3 minutos en total (sumando tu mejor tiempo de cada uno),
  y las **gafas de pro**, que se ganan superando cada capítulo sin perder ninguna vida.
- **Premio por meta**: cada vez que llega a la meta gana `10 × nº de capítulo` monedas, además de
  las que recoge por el camino. Vale también al **repetir** capítulos ya superados, así que
  repetir los últimos es la forma de ahorrar para la decoración cara.

Todos estos números están al principio de `mascota.py` (`DURACIONES`, `COSTE_AVENTURA`,
`VERDE`, `DECORACIONES`…) y se pueden cambiar sin tocar nada más.

## Ficheros

```
app.py              la web (Flask): casa, aventura, niveles, final y estadísticas
mascota.py          la clase Mascota y las reglas: necesidades, vidas, duración de los cuidados, tienda, decoración, trofeo
niveles.py          los 5 niveles dibujados con letras, la historia y la comprobación de que todo se alcanza
registro.py         guarda cada intento en un CSV y lo analiza con pandas y matplotlib
static/juego.js     el motor del plataformas (JavaScript): movimiento, saltos, choques y dibujo
static/estilo.css   el diseño
templates/          el HTML (_mascota.html: la mascota dibujada en SVG con sus caras)
datos/              partida.json (la mascota guardada) e intentos.csv (se crean al jugar)
tests/              las pruebas con pytest
```

---

## Guía para explicarlo en la presentación

### En una frase

> "Es una mascota virtual a la que cuidas como en un Tamagotchi, pero también tienes que
> llevarla de vuelta a casa superando niveles de plataformas. Cada aventura la agota, así que
> hay que cuidarla entre niveles; si no está bien cuidada, no recupera las vidas perdidas."

### ¿Qué hace Python y qué hace JavaScript?

Es lo primero que te van a preguntar, así que conviene dejarlo claro:

- **Python** lleva **toda la lógica del juego**: la mascota y sus necesidades, el paso del
  tiempo, la tienda, qué niveles están desbloqueados, cuántas vidas tiene, el guardado de la
  partida, los mapas de los niveles, comprobar los resultados y las estadísticas.
- **JavaScript** (`static/juego.js`) solo hace lo que **tiene que pasar dentro del navegador
  en tiempo real**: mover a la mascota 60 veces por segundo, detectar choques y dibujar.
  Python le pasa el nivel ya preparado y, al terminar, JavaScript le devuelve el resultado.
  Python lo **comprueba** antes de guardarlo: por ejemplo, no deja apuntar más monedas de las
  que hay en el nivel.

### El recorrido de una partida

1. Al entrar en la web, `mascota_actual()` carga `partida.json` y llama a `pasar_tiempo()`:
   calcula las horas desde la última visita y baja las necesidades.
2. En casa, cada botón envía un formulario a `/cuidar`, que llama al método de la mascota
   (`comer`, `banar`, `jugar`, `siesta` o `comprar`) y vuelve a guardar.
3. Al entrar en un nivel, Python comprueba que esté desbloqueado y que la mascota pueda
   jugar (`puede_jugar`), le devuelve las vidas si todo está en verde (`empezar_aventura`)
   y prepara el mapa (`preparar_mapa`).
4. JavaScript lee ese mapa de letras y monta el nivel: cada `#` es suelo, cada `o` una moneda…
5. Al terminar, JavaScript envía el resultado a `/nivel/<n>/terminar`. Python lo valida,
   actualiza la mascota (`terminar_nivel`: desgaste, vidas, monedas, mejor tiempo y trofeo),
   lo apunta en el CSV y responde qué mostrar.
6. En Estadísticas, pandas lee el CSV y agrupa por nivel.

### Qué parte del temario está en cada sitio

| Tema del curso | Dónde está | Qué decir |
|---|---|---|
| Condiciones | `animo()`, `puede_jugar()`, `empezar_aventura()` | "Solo recupera las vidas si las cuatro barras están en verde" |
| Bucles | `pasar_tiempo()` recorre las necesidades | "Para cada necesidad, resto lo que baja por hora multiplicado por las horas" |
| Funciones | `limitar()`, `preparar_mapa()`, `comprobar_mapa()`… | "`limitar` asegura que ningún valor sale de 0 a 100" |
| Colecciones | `COMIDAS` y `BAJADA_POR_HORA` (diccionarios), `NIVELES` (lista), el inventario | "Para añadir una comida a la tienda basta con añadir una línea al diccionario" |
| Clases y objetos | `Mascota` | "La mascota es un objeto con sus datos y todo lo que se puede hacer con ella" |
| Ficheros | `partida.json` y `intentos.csv` | "La partida se guarda en JSON y el historial de intentos en CSV" |
| Excepciones | `cargar_mascota()` y `terminar_nivel` | "Si el JSON está estropeado o el navegador envía datos raros, no se rompe: empieza de cero o responde con un error" |
| Fechas | `datetime` y `timedelta` en `pasar_tiempo()` y en `ocupado()` | "Guardo la hora de la última visita y hasta qué hora está ocupada con un cuidado" |
| pandas | `registro.py` | "`groupby('nivel')` con `agg` para intentos y completados; el mejor tiempo solo cuenta los intentos que llegaron a la meta" |
| matplotlib | `crear_grafica()` | "Barras de intentos frente a completados en cada nivel" |
| Tests | `tests/test_juego.py` (58 pruebas) | "Compruebo que los cuidados tardan lo que deben, que las vidas no se recuperan sin cuidarla, el trofeo, las gafas, el premio por capítulo y que no se pueden hacer trampas" |

### Cómo se dibuja un nivel

Los niveles están en `niveles.py` como dibujos de texto: `#` suelo, `=` plataforma, `o`
moneda, `E` bicho, `^` pinchos, `P` inicio y `M` meta. Para crear un nivel nuevo basta con
añadir otro dibujo a la lista `NIVELES`: el juego lo coge solo y la historia pasa a tener
un capítulo más.

`comprobar_mapa()` revisa que cada mapa tenga un inicio, una meta y ninguna letra rara.
La mascota salta unas 3,7 casillas, así que las plataformas están como mucho a 3 casillas
del suelo. Los niveles se han jugado de principio a fin con un jugador automático.

### Para enseñar en directo (3-4 minutos)

1. Adopta una mascota y ponle nombre.
2. En casa, enseña las barras y el bocadillo con lo que necesita. Dale de comer o juega con
   ella y fíjate en cómo cambian las barras y su cara.
3. Ve a **Aventura**: "Con su energía tiene 3 vidas". Juega el primer nivel.
4. Al volver, enseña que tiene más monedas pero las barras han bajado mucho: "Ahora tengo
   que cuidarla antes del siguiente capítulo". Échale una siesta y enseña cómo duerme.
5. Enseña la decoración y explica el trofeo de velocidad.
6. Termina en **Estadísticas**.

### Preguntas que te pueden hacer

- **¿Cómo sabe cuánto tiempo ha pasado si el programa está cerrado?** Guarda la fecha y la
  hora de la última visita en el JSON. Al volver, resta y calcula las horas.
- **¿Por qué la parte del plataformas está en JavaScript?** Porque tiene que ir a 60
  imágenes por segundo dentro del navegador. Python está en el servidor y no puede mover
  cosas en la pantalla en tiempo real. Toda la lógica que no es de tiempo real está en Python.
- **¿Por qué no se recuperan las vidas?** Para obligar a cuidar a la mascota: si sale de
  aventura con todo en verde, recupera las 3; si no, sigue con las que tenía.
- **¿Cómo sabe que está ocupada?** Al empezar un cuidado, Python guarda en el JSON qué está
  haciendo y hasta qué hora. Si le mandas otra cosa antes, compara con la hora actual y no te
  deja. La barra de progreso de la pantalla es solo visual.
- **¿Se pueden hacer trampas?** Python no se fía del navegador: si este dice que ha cogido
  más monedas de las que hay en el nivel, solo cuenta las que existen.
- **¿La mascota es Pou?** No: es un diseño original (una criatura con un brote en la
  cabeza), dibujada con SVG en la web y con formas en el juego.
