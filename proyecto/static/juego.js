// =============================================================================
// Motor de plataformas de "Rumbo a casa".
//
// Python prepara el nivel (el mapa de texto, los colores y las vidas) y lo deja en
// window.NIVEL. Este archivo solo se encarga de lo que tiene que pasar en tiempo
// real dentro del navegador: mover a la mascota, saltar, chocar y dibujar.
// Al terminar, envía el resultado a Python (/nivel/<n>/terminar).
// =============================================================================

const T = 32;                 // tamaño de cada casilla del mapa, en píxeles
const ANCHO_VISTA = 960;      // lo que se ve en pantalla (30 casillas)
const ALTO_VISTA = 480;       // (15 casillas)

// Física: valores ajustados para que salte unas 3,5 casillas de alto y 5 de largo
const GRAVEDAD = 0.55;
const FUERZA_SALTO = -11.5;
const VELOCIDAD_MAX = 4;
const ACELERACION = 0.6;
const FRENADO = 0.8;
const CAIDA_MAX = 12;
const INVULNERABLE = 90;      // fotogramas sin recibir daño tras un golpe

const SOLIDOS = new Set(["#", "="]);

/**
 * Una partida a un nivel: guarda el estado (jugador, monedas, bichos, cámara…),
 * lo avanza un paso cada fotograma con actualizar() y lo pinta con dibujar().
 */
class Juego {
  /**
   * @param {HTMLCanvasElement} canvas  Donde se dibuja el juego.
   * @param {object} datos  window.NIVEL, preparado por Python: filas, ancho, alto,
   *   tema, colores, vidas, vidas_max, gafas y url_terminar.
   * @param {function} alTerminar  Se llama una vez al acabar con
   *   {completado, monedas, segundos, vidas_perdidas}.
   */
  constructor(canvas, datos, alTerminar) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.datos = datos;
    this.alTerminar = alTerminar;
    this.filas = datos.filas;
    this.ancho = datos.ancho;
    this.alto = datos.alto;
    this.colores = datos.colores;

    this.entrada = { izquierda: false, derecha: false, saltar: false };
    this.monedas = [];
    this.enemigos = [];
    this.pinchos = [];
    this.leerMapa();

    this.jugador = {
      x: this.inicio.x, y: this.inicio.y, ancho: 24, alto: 26,
      vx: 0, vy: 0, enSuelo: false, mirando: 1, invulnerable: 0,
    };
    this.seguro = { x: this.inicio.x, y: this.inicio.y };  // último sitio seguro pisado
    this.vidas = datos.vidas;
    this.vidasPerdidas = 0;
    this.monedasCogidas = 0;
    this.fotogramas = 0;
    this.camara = 0;
    this.empezado = false;
    this.terminado = false;
  }

  // --- Leer el mapa de texto ---------------------------------------------------

  /**
   * Recorre el mapa de texto y crea los objetos del nivel en píxeles:
   * el punto de inicio (P), la meta (M), las monedas (o), los pinchos (^)
   * y los bichos (E). El suelo (#) y las plataformas (=) se quedan en
   * this.filas y se consultan con esSolido().
   */
  leerMapa() {
    this.filas.forEach((fila, y) => {
      [...fila].forEach((letra, x) => {
        const px = x * T, py = y * T;
        if (letra === "P") this.inicio = { x: px + 4, y: py + 6 };
        if (letra === "M") this.meta = { x: px, y: py - T * 2, ancho: T, alto: T * 3 };
        if (letra === "o") this.monedas.push({ x: px + 8, y: py + 8, ancho: 16, alto: 16, cogida: false });
        if (letra === "^") this.pinchos.push({ x: px + 4, y: py + 16, ancho: T - 8, alto: 16 });
        if (letra === "E") {
          this.enemigos.push({ x: px + 3, y: py + 10, ancho: 26, alto: 22, vx: -1, vy: 0, vivo: true, aplastado: 0 });
        }
      });
    });
  }

  /**
   * ¿Hay algo sólido en esa casilla? Fuera del mapa por los lados cuenta como
   * pared (para no salirse); por arriba o por abajo, como aire (para poder
   * caer por los agujeros).
   * @returns {boolean}
   */
  esSolido(columna, fila) {
    if (columna < 0 || columna >= this.ancho) return true;   // paredes invisibles a los lados
    if (fila < 0 || fila >= this.alto) return false;
    return SOLIDOS.has(this.filas[fila][columna]);
  }

  // --- Movimiento y choques con el suelo -----------------------------------------

  /**
   * Mueve un objeto (jugador o bicho) según su velocidad vx/vy y lo frena
   * contra el suelo y las paredes. Primero resuelve el eje X y luego el Y,
   * para que no se quede enganchado en las esquinas.
   * Actualiza cosa.enSuelo.
   * @returns {boolean} true si ha chocado de lado con una pared.
   */
  mover(cosa) {
    // Primero en horizontal…
    cosa.x += cosa.vx;
    let choqueLateral = false;
    for (const [col, fila] of this.casillasQueToca(cosa)) {
      if (!this.esSolido(col, fila)) continue;
      if (cosa.vx > 0) cosa.x = col * T - cosa.ancho - 0.01;
      if (cosa.vx < 0) cosa.x = (col + 1) * T + 0.01;
      cosa.vx = 0;
      choqueLateral = true;
    }
    // …y luego en vertical
    cosa.y += cosa.vy;
    cosa.enSuelo = false;
    for (const [col, fila] of this.casillasQueToca(cosa)) {
      if (!this.esSolido(col, fila)) continue;
      if (cosa.vy > 0) { cosa.y = fila * T - cosa.alto - 0.01; cosa.enSuelo = true; }
      if (cosa.vy < 0) cosa.y = (fila + 1) * T + 0.01;
      cosa.vy = 0;
    }
    return choqueLateral;
  }

  /**
   * Lista de casillas [columna, fila] que ocupa el rectángulo de un objeto.
   * @returns {Array<[number, number]>}
   */
  casillasQueToca(c) {
    const casillas = [];
    for (let fila = Math.floor(c.y / T); fila <= Math.floor((c.y + c.alto) / T); fila++) {
      for (let col = Math.floor(c.x / T); col <= Math.floor((c.x + c.ancho) / T); col++) {
        casillas.push([col, fila]);
      }
    }
    return casillas;
  }

  /**
   * ¿Se solapan dos rectángulos {x, y, ancho, alto}? (choque AABB)
   * @returns {boolean}
   */
  tocan(a, b) {
    return a.x < b.x + b.ancho && a.x + a.ancho > b.x && a.y < b.y + b.alto && a.y + a.alto > b.y;
  }

  // --- Un paso del juego (60 veces por segundo) ---------------------------------

  /**
   * Avanza el juego un fotograma (1/60 s). No hace nada hasta que el jugador
   * pulsa una tecla por primera vez, ni después de terminar.
   *
   * En orden: mueve a la mascota (correr, saltar, gravedad), recuerda el último
   * sitio seguro, comprueba caídas y pinchos, recoge monedas, mueve los bichos
   * (y mira si los aplasta o le hacen daño), comprueba la meta y mueve la cámara.
   */
  actualizar() {
    if (this.terminado) return;
    const j = this.jugador;
    const e = this.entrada;
    if (!this.empezado && (e.izquierda || e.derecha || e.saltar)) this.empezado = true;
    if (!this.empezado) return;
    this.fotogramas++;

    // Correr
    const direccion = (e.derecha ? 1 : 0) - (e.izquierda ? 1 : 0);
    if (direccion !== 0) {
      j.vx = Math.max(-VELOCIDAD_MAX, Math.min(VELOCIDAD_MAX, j.vx + ACELERACION * direccion));
      j.mirando = direccion;
    } else {
      j.vx *= FRENADO;
      if (Math.abs(j.vx) < 0.1) j.vx = 0;
    }

    // Saltar (si sueltas pronto el botón, el salto es más corto)
    if (e.saltar && j.enSuelo) j.vy = FUERZA_SALTO;
    if (!e.saltar && j.vy < -4) j.vy = -4;

    j.vy = Math.min(CAIDA_MAX, j.vy + GRAVEDAD);
    this.mover(j);
    if (j.invulnerable > 0) j.invulnerable--;

    const enPinchos = this.pinchos.some((p) => this.tocan(j, p));
    if (j.enSuelo && !enPinchos && j.invulnerable === 0) this.seguro = { x: j.x, y: j.y };

    // Caer por un agujero o pisar pinchos
    if (j.y > this.alto * T) this.herir(true);
    else if (enPinchos && j.invulnerable === 0) this.herir(true);

    // Monedas
    for (const moneda of this.monedas) {
      if (!moneda.cogida && this.tocan(j, moneda)) {
        moneda.cogida = true;
        this.monedasCogidas++;
      }
    }

    // Bichos: caminan de un lado a otro y se dan la vuelta en paredes y bordes
    for (const bicho of this.enemigos) {
      if (!bicho.vivo) { if (bicho.aplastado > 0) bicho.aplastado--; continue; }
      bicho.vy = Math.min(CAIDA_MAX, bicho.vy + GRAVEDAD);
      const velocidad = bicho.vx;
      if (this.mover(bicho)) bicho.vx = -velocidad;
      if (bicho.enSuelo) {
        const delante = bicho.vx > 0 ? bicho.x + bicho.ancho + 2 : bicho.x - 2;
        const filaDebajo = Math.floor((bicho.y + bicho.alto + 4) / T);
        if (!this.esSolido(Math.floor(delante / T), filaDebajo)) bicho.vx = -bicho.vx;
      }
      if (bicho.y > this.alto * T) bicho.vivo = false;

      if (this.tocan(j, bicho)) {
        const cayendoEncima = j.vy > 0 && j.y + j.alto - bicho.y < 14;
        if (cayendoEncima) {
          bicho.vivo = false;
          bicho.aplastado = 30;
          j.vy = FUERZA_SALTO * 0.6;    // rebote
        } else if (j.invulnerable === 0) {
          this.herir(false, bicho.x < j.x ? 1 : -1);
        }
      }
    }

    // ¿Ha llegado a la meta?
    if (this.tocan(j, this.meta)) this.terminar(true);

    // La cámara sigue a la mascota
    const objetivo = j.x - ANCHO_VISTA / 3;
    this.camara = Math.max(0, Math.min(this.ancho * T - ANCHO_VISTA, objetivo));
  }

  /**
   * Quita una vida a la mascota. Si se queda sin vidas, termina el nivel (perdido).
   * Si no, la hace invulnerable un rato y:
   * @param {boolean} volverAlSitioSeguro  true (caída o pinchos): la devuelve
   *   al último suelo seguro que pisó.
   * @param {number} empujarHacia  -1 o 1 (golpe de un bicho): la empuja hacia
   *   ese lado con un saltito.
   */
  herir(volverAlSitioSeguro, empujarHacia = 0) {
    this.vidas--;
    this.vidasPerdidas++;
    const j = this.jugador;
    if (this.vidas <= 0) { this.terminar(false); return; }
    j.invulnerable = INVULNERABLE;
    if (volverAlSitioSeguro) {
      j.x = this.seguro.x; j.y = this.seguro.y; j.vx = 0; j.vy = 0;
    } else {
      j.vx = 5 * empujarHacia; j.vy = -6;
    }
  }

  /**
   * Acaba la partida (solo la primera vez que se llama) y avisa con alTerminar
   * del resultado: completado, monedas cogidas, segundos jugados y vidas perdidas.
   * @param {boolean} completado  true si ha llegado a la meta.
   */
  terminar(completado) {
    if (this.terminado) return;
    this.terminado = true;
    this.completado = completado;
    this.alTerminar({
      completado,
      monedas: this.monedasCogidas,
      segundos: this.fotogramas / 60,
      vidas_perdidas: this.vidasPerdidas,
    });
  }

  // --- Dibujar ---------------------------------------------------------------

  /**
   * Pinta un fotograma completo: fondo, casillas visibles (solo las que caben
   * en la cámara), pinchos, monedas, meta, bichos, mascota y, encima de todo
   * y sin desplazar con la cámara, el marcador.
   */
  dibujar() {
    const c = this.ctx;
    c.save();
    this.dibujarFondo(c);
    c.translate(-Math.round(this.camara), 0);

    const primera = Math.floor(this.camara / T), ultima = primera + ANCHO_VISTA / T + 1;
    for (let fila = 0; fila < this.alto; fila++) {
      for (let col = primera; col <= Math.min(ultima, this.ancho - 1); col++) {
        const letra = this.filas[fila][col];
        if (letra === "#") this.dibujarSuelo(c, col, fila);
        if (letra === "=") this.dibujarPlataforma(c, col, fila);
      }
    }
    this.pinchos.forEach((p) => this.dibujarPinchos(c, p));
    this.monedas.forEach((m) => !m.cogida && this.dibujarMoneda(c, m));
    this.dibujarMeta(c);
    this.enemigos.forEach((b) => (b.vivo || b.aplastado > 0) && this.dibujarBicho(c, b));
    this.dibujarMascota(c);
    c.restore();
    this.dibujarMarcador(c);
  }

  /**
   * Pinta el cielo y el paisaje lejano según el tema del nivel (cueva,
   * parque, bosque, ciudad o casa). El paisaje se desplaza más despacio que
   * la cámara (efecto parallax) para dar sensación de profundidad.
   */
  dibujarFondo(c) {
    c.fillStyle = this.colores.cielo;
    c.fillRect(0, 0, ANCHO_VISTA, ALTO_VISTA);
    // El paisaje de fondo se mueve más despacio que el nivel: así parece que está lejos
    const lejos = this.camara * 0.25, medio = this.camara * 0.5;
    const repetir = (separacion, desplazamiento, dibujar) => {
      for (let i = -1; i < ANCHO_VISTA / separacion + 2; i++) {
        const indice = i + Math.floor(desplazamiento / separacion);
        dibujar(i * separacion - (desplazamiento % separacion), indice);
      }
    };
    const tema = this.datos.tema;

    if (tema === "cueva") {
      c.fillStyle = "rgba(0,0,0,0.25)";
      repetir(120, medio, (x, i) => {
        const largo = 40 + ((i * 37) % 60);
        c.beginPath(); c.moveTo(x, 64); c.lineTo(x + 18, 64 + largo); c.lineTo(x + 36, 64); c.fill();
      });
      return;
    }
    // Colinas lejanas (todos los niveles de exterior)
    c.fillStyle = "rgba(255,255,255,0.35)";
    repetir(260, lejos, (x, i) => {
      c.beginPath(); c.ellipse(x + 130, ALTO_VISTA - 50, 170, 110 + (i % 2) * 40, 0, Math.PI, 0); c.fill();
    });
    if (tema === "parque" || tema === "casa") {
      c.fillStyle = "rgba(255,255,255,0.85)";
      repetir(340, lejos * 0.6, (x, i) => {
        const y = 60 + (i % 3) * 30;
        c.beginPath(); c.ellipse(x + 40, y, 40, 16, 0, 0, Math.PI * 2); c.ellipse(x + 70, y - 8, 30, 18, 0, 0, Math.PI * 2); c.fill();
      });
    }
    if (tema === "bosque") {
      repetir(110, medio, (x, i) => {
        const alto = 120 + ((i * 53) % 80);
        c.fillStyle = "rgba(59,110,69,0.35)";
        c.fillRect(x + 50, ALTO_VISTA - alto, 10, alto);
        c.beginPath(); c.arc(x + 55, ALTO_VISTA - alto, 42, 0, Math.PI * 2); c.fill();
      });
    }
    if (tema === "ciudad") {
      repetir(90, medio, (x, i) => {
        const alto = 140 + ((i * 71) % 140);
        c.fillStyle = "rgba(108,110,133,0.35)";
        c.fillRect(x + 6, ALTO_VISTA - alto, 76, alto);
        c.fillStyle = "rgba(255,240,200,0.5)";
        for (let v = 0; v < alto - 30; v += 34) { c.fillRect(x + 18, ALTO_VISTA - alto + 16 + v, 14, 16); c.fillRect(x + 54, ALTO_VISTA - alto + 16 + v, 14, 16); }
      });
    }
    if (tema === "casa") {
      repetir(200, medio, (x) => {
        c.fillStyle = "rgba(160,106,66,0.3)";
        c.fillRect(x + 40, ALTO_VISTA - 150, 80, 70);
        c.beginPath(); c.moveTo(x + 30, ALTO_VISTA - 150); c.lineTo(x + 80, ALTO_VISTA - 190); c.lineTo(x + 130, ALTO_VISTA - 150); c.fill();
      });
    }
  }

  /** Pinta una casilla de suelo (#). Si no tiene nada encima, le pone la capa de "césped". */
  dibujarSuelo(c, col, fila) {
    const x = col * T, y = fila * T;
    const arribaLibre = fila === 0 || !SOLIDOS.has(this.filas[fila - 1][col]);
    c.fillStyle = this.colores.suelo_oscuro;
    c.fillRect(x, y, T, T);
    if (arribaLibre) {
      c.fillStyle = this.colores.suelo;
      c.fillRect(x, y, T, 10);
    }
    c.fillStyle = "rgba(0,0,0,0.08)";
    c.fillRect(x + 6, y + 16, 4, 4);
    c.fillRect(x + 20, y + 24, 4, 4);
  }

  /** Pinta una casilla de plataforma de madera (=). */
  dibujarPlataforma(c, col, fila) {
    const x = col * T, y = fila * T;
    c.fillStyle = "#b07a4a";
    c.fillRect(x, y + 4, T, 14);
    c.fillStyle = "#d39a62";
    c.fillRect(x, y + 4, T, 5);
    c.fillStyle = "#8a5c34";
    c.fillRect(x + T - 2, y + 4, 2, 14);
  }

  /** Pinta un grupo de pinchos (^) como tres triángulos. */
  dibujarPinchos(c, p) {
    c.fillStyle = "#c9ced8";
    c.strokeStyle = "#7d8494";
    for (let i = 0; i < 3; i++) {
      const x = p.x + i * (p.ancho / 3);
      c.beginPath();
      c.moveTo(x, p.y + p.alto);
      c.lineTo(x + p.ancho / 6, p.y);
      c.lineTo(x + p.ancho / 3, p.y + p.alto);
      c.closePath();
      c.fill();
      c.stroke();
    }
  }

  /** Pinta una moneda que flota arriba y abajo (cada una con su propio desfase). */
  dibujarMoneda(c, m) {
    const flotar = Math.sin((this.fotogramas + m.x) / 12) * 2;
    c.fillStyle = "#f6c445";
    c.beginPath();
    c.arc(m.x + 8, m.y + 8 + flotar, 8, 0, Math.PI * 2);
    c.fill();
    c.fillStyle = "#fde68f";
    c.beginPath();
    c.arc(m.x + 6, m.y + 6 + flotar, 3, 0, Math.PI * 2);
    c.fill();
  }

  /** Pinta la meta: una bandera ondeando o, en el último nivel (tema "casa"), la casa del dueño. */
  dibujarMeta(c) {
    const m = this.meta;
    if (this.datos.tema === "casa") {
      // En el último nivel, la meta es la casa del dueño
      const x = m.x - 24, base = m.y + m.alto;
      c.fillStyle = "#f4e3c6"; c.fillRect(x, base - 64, 80, 64);
      c.fillStyle = "#c0504d";
      c.beginPath(); c.moveTo(x - 8, base - 64); c.lineTo(x + 40, base - 100); c.lineTo(x + 88, base - 64); c.fill();
      c.fillStyle = "#7a4a2b"; c.fillRect(x + 30, base - 36, 20, 36);
      c.fillStyle = "#8fc6e8"; c.fillRect(x + 8, base - 52, 16, 14); c.fillRect(x + 56, base - 52, 16, 14);
      return;
    }
    c.fillStyle = "#6b6f7b";
    c.fillRect(m.x + 14, m.y, 4, m.alto);
    const ondear = Math.sin(this.fotogramas / 8) * 3;
    c.fillStyle = "#ff7a59";
    c.beginPath();
    c.moveTo(m.x + 18, m.y + 4);
    c.lineTo(m.x + 46, m.y + 14 + ondear);
    c.lineTo(m.x + 18, m.y + 26);
    c.fill();
  }

  /**
   * Pinta un bicho caminando (patas animadas, ojos mirando hacia donde va)
   * o, si lo han aplastado, una mancha plana durante unos fotogramas.
   */
  dibujarBicho(c, b) {
    const x = b.x, y = b.y;
    if (!b.vivo) {  // aplastado
      c.fillStyle = "#6c4a8c";
      c.beginPath(); c.ellipse(x + 13, y + 19, 14, 4, 0, 0, Math.PI * 2); c.fill();
      return;
    }
    const paso = Math.floor(this.fotogramas / 8) % 2;
    c.fillStyle = "#3d2a52";
    c.fillRect(x + 5, y + 18, 5, 4 + paso * 2);
    c.fillRect(x + 16, y + 18, 5, 6 - paso * 2);
    c.fillStyle = "#8a5cb8";
    c.beginPath(); c.ellipse(x + 13, y + 11, 13, 11, 0, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#fff";
    const ojo = b.vx > 0 ? 2 : -2;
    c.beginPath(); c.arc(x + 9 + ojo, y + 9, 3.5, 0, Math.PI * 2); c.arc(x + 17 + ojo, y + 9, 3.5, 0, Math.PI * 2); c.fill();
    c.fillStyle = "#1d1426";
    c.beginPath(); c.arc(x + 9 + ojo * 1.4, y + 10, 1.8, 0, Math.PI * 2); c.arc(x + 17 + ojo * 1.4, y + 10, 1.8, 0, Math.PI * 2); c.fill();
    c.strokeStyle = "#1d1426"; c.lineWidth = 2;
    c.beginPath(); c.moveTo(x + 5, y + 3); c.lineTo(x + 11, y + 6); c.moveTo(x + 21, y + 3); c.lineTo(x + 15, y + 6); c.stroke();
  }

  /** Pinta a la mascota con dibujarCriatura(). Mientras es invulnerable, parpadea. */
  dibujarMascota(c) {
    const j = this.jugador;
    if (j.invulnerable > 0 && Math.floor(j.invulnerable / 5) % 2 === 0) return;  // parpadea
    dibujarCriatura(c, j.x + j.ancho / 2, j.y + j.alto, j.ancho + 12, j.mirando, !j.enSuelo, j.vy,
                    Boolean(this.datos.gafas));
  }

  /**
   * Pinta el marcador de arriba a la izquierda (vidas, monedas cogidas/total
   * y segundos) y, antes de empezar, el cartel con las instrucciones.
   */
  dibujarMarcador(c) {
    c.fillStyle = "rgba(255,255,255,0.85)";
    c.beginPath(); c.roundRect(12, 12, 280, 40, 12); c.fill();
    c.font = "bold 20px 'Poppins', sans-serif";
    c.textBaseline = "middle";
    c.fillStyle = "#e0485f";
    c.fillText("♥".repeat(Math.max(0, this.vidas)) + "♡".repeat(Math.max(0, this.datos.vidas_max - this.vidas)), 26, 33);
    c.fillStyle = "#b8860b";
    c.fillText(`● ${this.monedasCogidas}/${this.monedas.length}`, 120, 33);
    c.fillStyle = "#3b3550";
    c.fillText(`${Math.floor(this.fotogramas / 60)} s`, 222, 33);
    if (!this.empezado) {
      c.fillStyle = "rgba(29,24,44,0.75)";
      c.beginPath(); c.roundRect(ANCHO_VISTA / 2 - 230, ALTO_VISTA / 2 - 40, 460, 80, 16); c.fill();
      c.fillStyle = "#fff";
      c.textAlign = "center";
      c.font = "bold 22px 'Poppins', sans-serif";
      c.fillText("← → para moverte · espacio para saltar", ANCHO_VISTA / 2, ALTO_VISTA / 2 - 8);
      c.font = "16px 'Poppins', sans-serif";
      c.fillText("Pulsa cualquiera para empezar", ANCHO_VISTA / 2, ALTO_VISTA / 2 + 20);
      c.textAlign = "left";
    }
  }
}

// La mascota se dibuja igual en el juego y en casa: una criatura redonda con un brote.
// (x, y) es el punto de apoyo de sus pies; "tamano" es su anchura.
/**
 * @param {CanvasRenderingContext2D} c
 * @param {number} x  Centro horizontal de los pies.
 * @param {number} y  Altura de los pies.
 * @param {number} tamano  Anchura del cuerpo en píxeles.
 * @param {number} mirando  1 = derecha, -1 = izquierda (mueve ojos y mofletes).
 * @param {boolean} enElAire  Si está saltando o cayendo.
 * @param {number} vy  Velocidad vertical: en el aire, estira o aplasta el cuerpo.
 * @param {boolean} gafas  Si lleva puestas las gafas de pro.
 */
function dibujarCriatura(c, x, y, tamano, mirando = 1, enElAire = false, vy = 0, gafas = false) {
  const estirar = enElAire ? Math.max(-0.12, Math.min(0.12, -vy / 60)) : 0;
  const ancho = tamano * (1 - estirar), alto = tamano * 0.92 * (1 + estirar);
  const centroY = y - alto / 2;
  c.save();
  // brote de hojas
  c.strokeStyle = "#3f8a4f"; c.lineWidth = tamano / 14;
  c.beginPath(); c.moveTo(x, centroY - alto / 2 + 2); c.lineTo(x, centroY - alto / 2 - tamano * 0.18); c.stroke();
  c.fillStyle = "#5cb85c";
  c.beginPath(); c.ellipse(x - tamano * 0.11, centroY - alto / 2 - tamano * 0.2, tamano * 0.12, tamano * 0.06, -0.5, 0, Math.PI * 2); c.fill();
  c.beginPath(); c.ellipse(x + tamano * 0.11, centroY - alto / 2 - tamano * 0.22, tamano * 0.12, tamano * 0.06, 0.5, 0, Math.PI * 2); c.fill();
  // cuerpo
  c.fillStyle = "#ffb3a7";
  c.beginPath(); c.ellipse(x, centroY, ancho / 2, alto / 2, 0, 0, Math.PI * 2); c.fill();
  c.fillStyle = "#ffd3cb";
  c.beginPath(); c.ellipse(x - ancho * 0.12, centroY - alto * 0.18, ancho * 0.2, alto * 0.14, -0.4, 0, Math.PI * 2); c.fill();
  // ojos y mofletes, mirando hacia donde camina
  const mira = mirando * tamano * 0.08;
  c.fillStyle = "#2b2233";
  c.beginPath();
  c.arc(x - tamano * 0.14 + mira, centroY - alto * 0.02, tamano * 0.07, 0, Math.PI * 2);
  c.arc(x + tamano * 0.14 + mira, centroY - alto * 0.02, tamano * 0.07, 0, Math.PI * 2);
  c.fill();
  c.fillStyle = "#ff7f8c";
  c.globalAlpha = 0.6;
  c.beginPath();
  c.ellipse(x - tamano * 0.27 + mira, centroY + alto * 0.14, tamano * 0.08, tamano * 0.05, 0, 0, Math.PI * 2);
  c.ellipse(x + tamano * 0.27 + mira, centroY + alto * 0.14, tamano * 0.08, tamano * 0.05, 0, 0, Math.PI * 2);
  c.fill();
  c.globalAlpha = 1;
  if (gafas) dibujarGafas(c, x + mira, centroY - alto * 0.02, tamano);
  c.restore();
}

/**
 * Pinta las gafas de pro sobre los ojos de la mascota.
 * (x, y) es el punto entre los dos ojos; "tamano" es la anchura de la mascota.
 */
function dibujarGafas(c, x, y, tamano) {
  const separacion = tamano * 0.14;          // lo mismo que separa los ojos del centro
  const anchoLente = tamano * 0.22, altoLente = tamano * 0.16;
  c.strokeStyle = "#2b2233"; c.lineWidth = Math.max(1.5, tamano / 22); c.lineCap = "round";
  // patillas y puente
  c.beginPath();
  c.moveTo(x - separacion - anchoLente / 2, y - altoLente * 0.2); c.lineTo(x - tamano * 0.42, y - altoLente * 0.35);
  c.moveTo(x + separacion + anchoLente / 2, y - altoLente * 0.2); c.lineTo(x + tamano * 0.42, y - altoLente * 0.35);
  c.moveTo(x - separacion + anchoLente / 2, y - altoLente * 0.15); c.lineTo(x + separacion - anchoLente / 2, y - altoLente * 0.15);
  c.stroke();
  // cristales oscuros con un brillo
  for (const lado of [-1, 1]) {
    const cx = x + lado * separacion;
    c.fillStyle = "#2b2233";
    c.beginPath(); c.roundRect(cx - anchoLente / 2, y - altoLente / 2, anchoLente, altoLente, altoLente * 0.35); c.fill();
    c.strokeStyle = "#8fd3ff"; c.lineWidth = Math.max(1, tamano / 34);
    c.beginPath(); c.moveTo(cx - anchoLente * 0.3, y - altoLente * 0.1); c.lineTo(cx, y - altoLente * 0.25); c.stroke();
  }
}

// --- Arranque: teclado, botones táctiles y bucle principal ------------------------

/**
 * Arranca el nivel: crea el Juego con window.NIVEL, conecta el teclado
 * (flechas/WASD/espacio) y los botones táctiles [data-control], y lanza el
 * bucle principal, que hace siempre 60 actualizaciones por segundo aunque la
 * pantalla refresque a otra velocidad.
 */
function iniciarJuego() {
  const canvas = document.getElementById("pantalla");
  const juego = new Juego(canvas, window.NIVEL, enviarResultado);
  window.juego = juego;   // accesible desde la consola (y para las pruebas automáticas)

  const teclas = {
    ArrowLeft: "izquierda", KeyA: "izquierda",
    ArrowRight: "derecha", KeyD: "derecha",
    Space: "saltar", ArrowUp: "saltar", KeyW: "saltar",
  };
  addEventListener("keydown", (ev) => {
    if (teclas[ev.code]) { juego.entrada[teclas[ev.code]] = true; ev.preventDefault(); }
  });
  addEventListener("keyup", (ev) => {
    if (teclas[ev.code]) juego.entrada[teclas[ev.code]] = false;
  });
  document.querySelectorAll("[data-control]").forEach((boton) => {
    const accion = boton.dataset.control;
    const pulsar = (valor) => (ev) => { ev.preventDefault(); juego.entrada[accion] = valor; };
    boton.addEventListener("pointerdown", pulsar(true));
    boton.addEventListener("pointerup", pulsar(false));
    boton.addEventListener("pointerleave", pulsar(false));
  });

  // Bucle a 60 pasos por segundo, aunque la pantalla vaya más rápida o más lenta
  let anterior = performance.now(), acumulado = 0;
  function bucle(ahora) {
    acumulado += Math.min(100, ahora - anterior);
    anterior = ahora;
    while (acumulado >= 1000 / 60) { juego.actualizar(); acumulado -= 1000 / 60; }
    juego.dibujar();
    if (!juego.terminado) requestAnimationFrame(bucle);
    else juego.dibujar();
  }
  requestAnimationFrame(bucle);
}

/**
 * Envía el resultado del nivel a Python (POST a window.NIVEL.url_terminar)
 * y muestra la respuesta en el panel #resultado: título, mensaje y botones
 * (p. ej. "Volver a casa"). Es el callback alTerminar del Juego.
 * @param {{completado: boolean, monedas: number, segundos: number, vidas_perdidas: number}} resultado
 */
async function enviarResultado(resultado) {
  const respuesta = await fetch(window.NIVEL.url_terminar, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(resultado),
  });
  const datos = await respuesta.json();
  const panel = document.getElementById("resultado");
  panel.querySelector("h2").textContent = datos.titulo;
  panel.querySelector("p").textContent = datos.mensaje;
  const botones = panel.querySelector(".botones");
  botones.innerHTML = "";
  for (const boton of datos.botones) {
    const enlace = document.createElement("a");
    enlace.href = boton.url;
    enlace.textContent = boton.texto;
    enlace.className = "boton" + (boton.principal ? "" : " secundario");
    botones.appendChild(enlace);
  }
  panel.hidden = false;
  panel.classList.add(resultado.completado ? "gana" : "pierde");
  botones.querySelector("a")?.focus();
}

if (document.getElementById("pantalla")) iniciarJuego();
