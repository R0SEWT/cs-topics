// Lógica del cliente móvil KenKen (TB1)

document.addEventListener("DOMContentLoaded", () => {
  // Constantes de almacenamiento local
  const CLAVE_MODO = "kenken_modo";
  const CLAVE_URL_NODO = "kenken_url_nodo";
  const URL_POR_DEFECTO = "http://localhost:8723";

  // Estado en memoria
  let modoActual = localStorage.getItem(CLAVE_MODO) || "asistencia";
  let ultimaFoto = null;
  let ultimoResultado = null;
  let controladorActual = null;
  const celdasReveladas = new Set();

  // Elementos de la interfaz
  const puntoEstado = document.getElementById("punto-estado");
  const textoEstado = document.getElementById("texto-estado");
  const btnAjustes = document.getElementById("btn-ajustes");

  // Vistas
  const vistaCaptura = document.getElementById("vista-captura");
  const vistaLeyendo = document.getElementById("vista-leyendo");
  const vistaResultado = document.getElementById("vista-resultado");
  const vistaError = document.getElementById("vista-error");

  // Captura
  const btnModoAsistencia = document.getElementById("btn-modo-asistencia");
  const btnModoRapido = document.getElementById("btn-modo-rapido");
  const modoExplicacion = document.getElementById("modo-explicacion");
  const btnTomarFoto = document.getElementById("btn-tomar-foto");
  const btnGaleria = document.getElementById("btn-galeria");
  const inputCamara = document.getElementById("input-camara");
  const inputGaleria = document.getElementById("input-galeria");

  // Leyendo
  const miniaturaFoto = document.getElementById("miniatura-foto");
  const btnCancelarLectura = document.getElementById("btn-cancelar-lectura");

  // Resultado
  const resultadoTitulo = document.getElementById("resultado-titulo");
  const resultadoMeta = document.getElementById("resultado-meta");
  const tableroEnvoltura = document.getElementById("tablero-envoltura");
  const mensajeEnvoltura = document.getElementById("mensaje-envoltura");
  const mensajeTexto = document.getElementById("mensaje-texto");
  const avisosEnvoltura = document.getElementById("avisos-envoltura");
  const avisosLista = document.getElementById("avisos-lista");
  const btnRevelarTodo = document.getElementById("btn-revelar-todo");
  const btnOtraFoto = document.getElementById("btn-otra-foto");

  // Error de red
  const errorDetalle = document.getElementById("error-detalle");
  const btnReintentar = document.getElementById("btn-reintentar");
  const btnAjustesDesdeError = document.getElementById("btn-ajustes-desde-error");
  const btnOtraFotoError = document.getElementById("btn-otra-foto-error");

  // Diálogos modales
  const dialogoAjustes = document.getElementById("dialogo-ajustes");
  const btnCerrarAjustes = document.getElementById("btn-cerrar-ajustes");
  const btnCancelarAjustes = document.getElementById("btn-cancelar-ajustes");
  const formAjustes = document.getElementById("form-ajustes");
  const inputUrlNodo = document.getElementById("input-url-nodo");
  const resultadoPrueba = document.getElementById("resultado-prueba");

  const dialogoConfirmar = document.getElementById("dialogo-confirmar-revelar");
  const btnCancelarRevelar = document.getElementById("btn-cancelar-revelar");
  const btnConfirmarRevelar = document.getElementById("btn-confirmar-revelar");

  // Utilidades para diálogos nativos
  function abrirDialogo(d) {
    if (typeof d.showModal === "function") {
      d.showModal();
    } else {
      d.setAttribute("open", "");
    }
  }

  function cerrarDialogo(d) {
    if (typeof d.close === "function") {
      d.close();
    } else {
      d.removeAttribute("open");
    }
  }

  // Cambio de pantalla activa
  function mostrarVista(nombre) {
    vistaCaptura.classList.toggle("vista-oculta", nombre !== "captura");
    vistaLeyendo.classList.toggle("vista-oculta", nombre !== "leyendo");
    vistaResultado.classList.toggle("vista-oculta", nombre !== "resultado");
    vistaError.classList.toggle("vista-oculta", nombre !== "error");
  }

  // Normalización y lectura de la URL del nodo
  function limpiarUrl(url) {
    let u = (url || "").trim();
    if (!u) return URL_POR_DEFECTO;
    if (!/^https?:\/\//i.test(u)) {
      u = "http://" + u;
    }
    return u.replace(/\/+$/, "");
  }

  function obtenerUrlNodo() {
    return limpiarUrl(localStorage.getItem(CLAVE_URL_NODO));
  }

  function guardarUrlNodo(url) {
    localStorage.setItem(CLAVE_URL_NODO, limpiarUrl(url));
  }

  // Comprobación de salud del nodo (GET /salud)
  async function comprobarSalud() {
    const url = obtenerUrlNodo();
    try {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 4000);
      const res = await fetch(`${url}/salud`, { signal: controller.signal });
      clearTimeout(timer);

      if (res.ok) {
        const datos = await res.json();
        if (datos.ok && datos.nodo) {
          puntoEstado.className = "punto-estado conectado";
          textoEstado.textContent = `Conectado a ${datos.nodo}`;
          return { ok: true, nodo: datos.nodo };
        }
      }
    } catch (_) {
      // Error de red o tiempo de espera
    }

    puntoEstado.className = "punto-estado desconectado";
    textoEstado.textContent = "Sin conexión con el nodo";
    return { ok: false };
  }

  // Gestión del conmutador de modo (Asistencia vs Rápido)
  function actualizarModoUI(modo) {
    modoActual = modo;
    localStorage.setItem(CLAVE_MODO, modo);

    const esAsistencia = modo === "asistencia";
    btnModoAsistencia.classList.toggle("activo", esAsistencia);
    btnModoAsistencia.setAttribute("aria-checked", esAsistencia ? "true" : "false");

    btnModoRapido.classList.toggle("activo", !esAsistencia);
    btnModoRapido.setAttribute("aria-checked", !esAsistencia ? "true" : "false");

    modoExplicacion.textContent = esAsistencia
      ? "Toca cada casilla para ver su número. No revela la solución de golpe."
      : "Muestra la solución completa de inmediato.";
  }

  btnModoAsistencia.addEventListener("click", () => actualizarModoUI("asistencia"));
  btnModoRapido.addEventListener("click", () => actualizarModoUI("rapido"));
  actualizarModoUI(modoActual);

  // Apertura y guardado de ajustes de conexión
  btnAjustes.addEventListener("click", () => {
    inputUrlNodo.value = obtenerUrlNodo();
    resultadoPrueba.textContent = "";
    resultadoPrueba.className = "resultado-prueba";
    abrirDialogo(dialogoAjustes);
  });

  btnCerrarAjustes.addEventListener("click", () => {
    cerrarDialogo(dialogoAjustes);
    comprobarSalud();
  });

  btnCancelarAjustes.addEventListener("click", () => {
    cerrarDialogo(dialogoAjustes);
    comprobarSalud();
  });

  formAjustes.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nuevaUrl = inputUrlNodo.value;
    guardarUrlNodo(nuevaUrl);

    resultadoPrueba.textContent = "Probando conexión…";
    resultadoPrueba.className = "resultado-prueba probando";

    const salud = await comprobarSalud();
    if (salud.ok) {
      resultadoPrueba.textContent = `Conectado a ${salud.nodo}`;
      resultadoPrueba.className = "resultado-prueba exito";
      setTimeout(() => {
        cerrarDialogo(dialogoAjustes);
      }, 500);
    } else {
      resultadoPrueba.textContent = "Sin conexión con el nodo en esa dirección.";
      resultadoPrueba.className = "resultado-prueba fallo";
    }
  });

  // Captura de imagen (Capacitor nativo o navegador web)
  async function iniciarCaptura(origen) {
    if (window.Capacitor?.isNativePlatform?.()) {
      try {
        const Camera = window.Capacitor.Plugins?.Camera;
        if (!Camera) throw new Error("Plugin Camera no disponible");
        const foto = await Camera.getPhoto({
          quality: 85,
          resultType: "base64",
          source: origen === "camera" ? "CAMERA" : "PHOTOS",
          width: 2000,
          correctOrientation: true,
        });
        const dataUrl = `data:image/${foto.format || "jpeg"};base64,${foto.base64String}`;
        procesarFoto(dataUrl);
      } catch (err) {
        console.warn("Captura cancelada o no completada:", err);
      }
    } else {
      if (origen === "camera") {
        inputCamara.click();
      } else {
        inputGaleria.click();
      }
    }
  }

  btnTomarFoto.addEventListener("click", () => iniciarCaptura("camera"));
  btnGaleria.addEventListener("click", () => iniciarCaptura("photos"));

  function leerArchivoSeleccionado(e) {
    const archivo = e.target.files?.[0];
    if (!archivo) return;
    const lector = new FileReader();
    lector.onload = () => {
      procesarFoto(lector.result);
    };
    lector.readAsDataURL(archivo);
    e.target.value = "";
  }

  inputCamara.addEventListener("change", leerArchivoSeleccionado);
  inputGaleria.addEventListener("change", leerArchivoSeleccionado);

  // Procesamiento de foto en el nodo (POST /resolver)
  async function procesarFoto(dataUrl) {
    ultimaFoto = dataUrl;
    celdasReveladas.clear();

    miniaturaFoto.src = dataUrl;
    mostrarVista("leyendo");

    controladorActual = new AbortController();
    const timeoutId = setTimeout(() => {
      controladorActual.abort();
    }, 30000);

    try {
      const respuesta = await fetch(`${obtenerUrlNodo()}/resolver`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imagen: dataUrl }),
        signal: controladorActual.signal,
      });
      clearTimeout(timeoutId);

      if (!respuesta.ok) {
        let detalle = "";
        try {
          const errJson = await respuesta.json();
          detalle = errJson.detail || errJson.mensaje || JSON.stringify(errJson);
        } catch (_) {
          detalle = await respuesta.text();
        }
        mostrarPantallaError(detalle || `Error del servidor (${respuesta.status})`);
        return;
      }

      const datos = await respuesta.json();
      ultimoResultado = datos;
      renderizarResultado(datos);
    } catch (err) {
      clearTimeout(timeoutId);
      if (err.name === "AbortError") {
        mostrarPantallaError("Tiempo de espera agotado (30 s). El nodo no respondió a tiempo.");
      } else {
        mostrarPantallaError();
      }
    }
  }

  btnCancelarLectura.addEventListener("click", () => {
    if (controladorActual) {
      controladorActual.abort();
    }
    mostrarVista("captura");
  });

  // Pantalla de error de red
  function mostrarPantallaError(detalle) {
    mostrarVista("error");
    if (detalle) {
      errorDetalle.textContent = detalle;
      errorDetalle.classList.remove("vista-oculta");
    } else {
      errorDetalle.textContent = "";
      errorDetalle.classList.add("vista-oculta");
    }
  }

  btnReintentar.addEventListener("click", () => {
    if (ultimaFoto) {
      procesarFoto(ultimaFoto);
    } else {
      comprobarSalud();
      mostrarVista("captura");
    }
  });

  btnAjustesDesdeError.addEventListener("click", () => {
    inputUrlNodo.value = obtenerUrlNodo();
    resultadoPrueba.textContent = "";
    resultadoPrueba.className = "resultado-prueba";
    abrirDialogo(dialogoAjustes);
  });

  btnOtraFotoError.addEventListener("click", () => {
    mostrarVista("captura");
  });

  // Formato matemático y metadatos
  function formatearOperador(op) {
    switch (op) {
      case "+": return "+";
      case "-": return "−";
      case "*": return "×";
      case "/": return "÷";
      case "=": return "";
      default: return op || "";
    }
  }

  function formatearMetadatos(ms) {
    if (!ms) return "Solución única";
    const vision = typeof ms.vision === "number" ? ms.vision : "—";
    const solver = typeof ms.solver === "number" ? ms.solver : "—";
    return `Leído en ${vision} ms · resuelto en ${solver} ms · solución única`;
  }

  // Dibujado del tablero KenKen vectorial (SVG)
  function dibujarTablero(n, jaulas, solucion, modo, corregidas = new Set()) {
    tableroEnvoltura.innerHTML = "";

    const S = 60;
    const W = n * S;
    const H = n * S;
    const grosorBorde = 3.5;
    const margenExterior = grosorBorde / 2;

    // Mapa de pertenencia celda -> índice de jaula
    const mapaJaula = Array.from({ length: n }, () => Array(n).fill(-1));
    jaulas.forEach((jaula, idx) => {
      if (Array.isArray(jaula.celdas)) {
        jaula.celdas.forEach(([r, c]) => {
          if (r >= 0 && r < n && c >= 0 && c < n) {
            mapaJaula[r][c] = idx;
          }
        });
      }
    });

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
    svg.setAttribute("class", "tablero-svg");
    svg.setAttribute("role", "grid");
    svg.setAttribute("aria-label", `Tablero KenKen de ${n} por ${n}`);

    // 1. Capa de celdas
    const capaCeldas = document.createElementNS("http://www.w3.org/2000/svg", "g");
    capaCeldas.setAttribute("class", "capa-celdas");

    const tamNumero = Math.round(S * 0.48);

    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        const gCelda = document.createElementNS("http://www.w3.org/2000/svg", "g");
        const valor = solucion ? solucion[r][c] : null;
        const revelada = modo === "rapido" || !solucion || celdasReveladas.has(`${r},${c}`);

        gCelda.setAttribute("class", `celda ${revelada ? "revelada" : "oculta"}`);
        gCelda.setAttribute("data-r", r);
        gCelda.setAttribute("data-c", c);
        gCelda.setAttribute("role", "gridcell");
        gCelda.setAttribute("tabindex", "0");
        gCelda.setAttribute(
          "aria-label",
          valor !== null
            ? (revelada ? `Fila ${r + 1}, columna ${c + 1}, número ${valor}` : `Fila ${r + 1}, columna ${c + 1}, toca para revelar`)
            : `Fila ${r + 1}, columna ${c + 1}`
        );

        const fondo = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        fondo.setAttribute("x", c * S);
        fondo.setAttribute("y", r * S);
        fondo.setAttribute("width", S);
        fondo.setAttribute("height", S);
        fondo.setAttribute("class", "fondo-celda");
        gCelda.appendChild(fondo);

        if (valor !== null) {
          const textoVal = document.createElementNS("http://www.w3.org/2000/svg", "text");
          textoVal.setAttribute("x", c * S + S / 2);
          textoVal.setAttribute("y", r * S + S / 2 + 1);
          textoVal.setAttribute("font-size", tamNumero);
          textoVal.setAttribute("text-anchor", "middle");
          textoVal.setAttribute("dominant-baseline", "central");
          textoVal.setAttribute("class", `valor-celda ${revelada ? "" : "texto-oculto"}`);
          textoVal.textContent = valor;
          gCelda.appendChild(textoVal);

          const punto = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          punto.setAttribute("cx", c * S + S / 2);
          punto.setAttribute("cy", r * S + S / 2);
          punto.setAttribute("r", "3");
          punto.setAttribute("class", `punto-oculto ${revelada ? "vista-oculta" : ""}`);
          gCelda.appendChild(punto);

          if (modo === "asistencia" && solucion) {
            const revelarCelda = () => {
              if (!celdasReveladas.has(`${r},${c}`)) {
                celdasReveladas.add(`${r},${c}`);
                gCelda.classList.remove("oculta");
                gCelda.classList.add("revelada");
                textoVal.classList.remove("texto-oculto");
                punto.classList.add("vista-oculta");
                gCelda.setAttribute("aria-label", `Fila ${r + 1}, columna ${c + 1}, número ${valor}`);

                if (navigator.vibrate) {
                  try { navigator.vibrate(25); } catch (_) {}
                }

                if (celdasReveladas.size >= n * n) {
                  btnRevelarTodo.classList.add("vista-oculta");
                }
              }
            };

            gCelda.addEventListener("click", revelarCelda);
            gCelda.addEventListener("keydown", (evt) => {
              if (evt.key === "Enter" || evt.key === " ") {
                evt.preventDefault();
                revelarCelda();
              }
            });
          }
        }

        capaCeldas.appendChild(gCelda);
      }
    }
    svg.appendChild(capaCeldas);

    // 2. Capa de divisiones y bordes
    const capaLineas = document.createElementNS("http://www.w3.org/2000/svg", "g");
    capaLineas.setAttribute("class", "capa-lineas");
    capaLineas.style.pointerEvents = "none";

    // Divisiones verticales
    for (let c = 0; c < n - 1; c++) {
      const x = (c + 1) * S;
      for (let r = 0; r < n; r++) {
        const y1 = r * S;
        const y2 = (r + 1) * S;
        const mismaJaula = mapaJaula[r][c] !== -1 && mapaJaula[r][c] === mapaJaula[r][c + 1];

        const linea = document.createElementNS("http://www.w3.org/2000/svg", "line");
        linea.setAttribute("x1", x);
        linea.setAttribute("y1", y1);
        linea.setAttribute("x2", x);
        linea.setAttribute("y2", y2);
        linea.setAttribute("class", mismaJaula ? "linea-fina" : "linea-gruesa");
        capaLineas.appendChild(linea);
      }
    }

    // Divisiones horizontales
    for (let r = 0; r < n - 1; r++) {
      const y = (r + 1) * S;
      for (let c = 0; c < n; c++) {
        const x1 = c * S;
        const x2 = (c + 1) * S;
        const mismaJaula = mapaJaula[r][c] !== -1 && mapaJaula[r][c] === mapaJaula[r + 1][c];

        const linea = document.createElementNS("http://www.w3.org/2000/svg", "line");
        linea.setAttribute("x1", x1);
        linea.setAttribute("y1", y);
        linea.setAttribute("x2", x2);
        linea.setAttribute("y2", y);
        linea.setAttribute("class", mismaJaula ? "linea-fina" : "linea-gruesa");
        capaLineas.appendChild(linea);
      }
    }

    // Contorno exterior continuo
    const contorno = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    contorno.setAttribute("x", margenExterior);
    contorno.setAttribute("y", margenExterior);
    contorno.setAttribute("width", W - grosorBorde);
    contorno.setAttribute("height", H - grosorBorde);
    contorno.setAttribute("class", "borde-exterior");
    capaLineas.appendChild(contorno);

    svg.appendChild(capaLineas);

    // 3. Capa de etiquetas de jaulas (esquina superior izquierda de celda ancla)
    const capaEtiquetas = document.createElementNS("http://www.w3.org/2000/svg", "g");
    capaEtiquetas.setAttribute("class", "capa-etiquetas");
    capaEtiquetas.style.pointerEvents = "none";

    const tamEtiqueta = Math.max(10, Math.round(S * 0.20));

    jaulas.forEach((jaula) => {
      if (!Array.isArray(jaula.celdas) || jaula.celdas.length === 0) return;
      // Celda ancla: mínima fila, y en empate, mínima columna
      const ordenadas = [...jaula.celdas].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      const [anclaR, anclaC] = ordenadas[0];

      const texto = `${jaula.objetivo ?? ""}${formatearOperador(jaula.op)}`;
      if (!texto) return;

      const textoEt = document.createElementNS("http://www.w3.org/2000/svg", "text");
      textoEt.setAttribute("x", anclaC * S + 4);
      textoEt.setAttribute("y", anclaR * S + tamEtiqueta + 3);
      textoEt.setAttribute("font-size", tamEtiqueta);
      // Las etiquetas que el solver corrigió se marcan con el color de acento.
      const corregida = corregidas.has(`${anclaR},${anclaC}`);
      textoEt.setAttribute("class", corregida ? "etiqueta-jaula etiqueta-corregida" : "etiqueta-jaula");
      textoEt.textContent = texto;
      capaEtiquetas.appendChild(textoEt);
    });

    svg.appendChild(capaEtiquetas);
    tableroEnvoltura.appendChild(svg);
  }

  // Revelado total con confirmación
  function revelarTodo() {
    if (!ultimoResultado || !ultimoResultado.solucion) return;
    const n = ultimoResultado.n;
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        celdasReveladas.add(`${r},${c}`);
      }
    }
    const celdas = tableroEnvoltura.querySelectorAll(".celda");
    celdas.forEach((el) => {
      el.classList.remove("oculta");
      el.classList.add("revelada");
      const val = el.querySelector(".valor-celda");
      if (val) val.classList.remove("texto-oculto");
      const p = el.querySelector(".punto-oculto");
      if (p) p.classList.add("vista-oculta");
    });
    btnRevelarTodo.classList.add("vista-oculta");
  }

  btnRevelarTodo.addEventListener("click", () => {
    abrirDialogo(dialogoConfirmar);
  });

  btnCancelarRevelar.addEventListener("click", () => {
    cerrarDialogo(dialogoConfirmar);
  });

  btnConfirmarRevelar.addEventListener("click", () => {
    revelarTodo();
    cerrarDialogo(dialogoConfirmar);
  });

  // Renderizado del resultado según respuesta del nodo
  function renderizarResultado(datos) {
    mostrarVista("resultado");

    const esReparado = datos.estado === "reparado";
    const esResuelto = datos.estado === "resuelto" || esReparado;
    const correcciones = Array.isArray(datos.correcciones) ? datos.correcciones : [];
    const corregidas = new Set(correcciones.map((c) => `${c.celda[0]},${c.celda[1]}`));
    const tieneJaulas = Array.isArray(datos.jaulas) && datos.jaulas.length > 0 && typeof datos.n === "number";

    tableroEnvoltura.innerHTML = "";
    avisosLista.innerHTML = "";
    avisosEnvoltura.classList.add("vista-oculta");
    mensajeEnvoltura.classList.add("vista-oculta");
    btnRevelarTodo.classList.add("vista-oculta");
    mensajeEnvoltura.querySelector(".lista-correcciones")?.remove();

    if (esResuelto) {
      resultadoTitulo.textContent = esReparado ? "Solución, con lectura corregida" : "Solución";
      resultadoMeta.textContent = formatearMetadatos(datos.ms);
      resultadoMeta.classList.remove("vista-oculta");

      dibujarTablero(datos.n, datos.jaulas, datos.solucion, modoActual, corregidas);

      if (esReparado) {
        // Honestidad de lectura: decir qué se corrigió y dónde.
        mensajeTexto.textContent = datos.mensaje || "";
        const lista = document.createElement("ul");
        lista.className = "lista-correcciones";
        correcciones.forEach((c) => {
          const li = document.createElement("li");
          const leido = `${c.leido.objetivo}${formatearOperador(c.leido.op)}`;
          const era = `${c.corregido.objetivo}${formatearOperador(c.corregido.op)}`;
          li.textContent = `Fila ${c.celda[0] + 1}, columna ${c.celda[1] + 1}: leí ${leido}, es ${era}`;
          lista.appendChild(li);
        });
        mensajeEnvoltura.appendChild(lista);
        mensajeEnvoltura.classList.remove("vista-oculta");
      }

      if (modoActual === "asistencia") {
        btnRevelarTodo.classList.remove("vista-oculta");
      }
    } else {
      resultadoTitulo.textContent = "No se pudo resolver";
      resultadoMeta.textContent = "";
      resultadoMeta.classList.add("vista-oculta");

      if (datos.mensaje) {
        mensajeTexto.textContent = datos.mensaje;
        mensajeEnvoltura.classList.remove("vista-oculta");
      }

      if (tieneJaulas) {
        dibujarTablero(datos.n, datos.jaulas, null, "rapido");
      }
    }

    if (Array.isArray(datos.avisos) && datos.avisos.length > 0) {
      datos.avisos.forEach((aviso) => {
        const li = document.createElement("li");
        li.textContent = aviso;
        avisosLista.appendChild(li);
      });
      avisosEnvoltura.classList.remove("vista-oculta");
    }
  }

  btnOtraFoto.addEventListener("click", () => {
    mostrarVista("captura");
  });

  // Verificación inicial de salud
  comprobarSalud();
});
