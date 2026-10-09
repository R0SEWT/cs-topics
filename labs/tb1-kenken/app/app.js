/**
 * Cliente móvil KenKen (TB1) — Diseño Centrado en las Personas (HCD).
 * Implementa guía en tiempo real, Heurística 9 de Nielsen, Modo Rápido (Diego)
 * y andamiaje cognitivo progresivo (Marta), conectado a datos reales del nodo.
 */

document.addEventListener("DOMContentLoaded", () => {
  // Constantes de persistencia y configuración
  const CLAVE_MODO = "kenken_modo";
  const CLAVE_URL_NODO = "kenken_url_nodo";
  const URL_POR_DEFECTO = "http://localhost:8723";

  // Estado reactivo de la aplicación
  let modoActual = localStorage.getItem(CLAVE_MODO) || "asistencia";
  let nodoConectado = false;
  let nodoNombre = "";
  let ultimaFoto = null;
  let ultimoResultado = null;
  let controladorActual = null;

  // Estado del Modo Asistencia (Marta)
  const celdasReveladas = new Set();
  const anotacionesMarta = new Map(); // "r,c" -> número
  let modoAnotacionActivo = false;
  let celdaSeleccionadaAnotar = null; // { r, c }
  let celdaConflictoActual = null; // { r, c }
  let jaulaConflictoIdx = -1;

  // Estado de la cámara y visor
  let camaraStream = null;
  let facingModeActual = "environment";
  let intervaloMuestreoLuminancia = null;
  let canvasLuminancia = null;
  let ctxLuminancia = null;
  let bajaLuminancia = false;
  let ultimoHapticoListo = 0;

  // Elementos del DOM: Barra superior
  const btnModoAsistencia = document.getElementById("btn-modo-asistencia");
  const btnModoRapido = document.getElementById("btn-modo-rapido");
  const puntoEstado = document.getElementById("punto-estado");
  const textoEstado = document.getElementById("texto-estado");
  const btnAjustes = document.getElementById("btn-ajustes");

  // Vistas
  const vistaCamara = document.getElementById("vista-camara");
  const vistaLeyendo = document.getElementById("vista-leyendo");
  const vistaRapido = document.getElementById("vista-rapido");
  const vistaAsistencia = document.getElementById("vista-asistencia");
  const vistaInvalido = document.getElementById("vista-invalido");

  // Elementos de la cámara
  const videoStream = document.getElementById("video-stream");
  const reticulaCaja = document.getElementById("reticula-caja");
  const pildoraGuia = document.getElementById("pildora-guia");
  const iconoGuia = document.getElementById("icono-guia");
  const textoGuia = document.getElementById("texto-guia");
  const fallbackCamara = document.getElementById("fallback-camara");
  const btnFallbackFoto = document.getElementById("btn-fallback-foto");
  const btnFallbackGaleria = document.getElementById("btn-fallback-galeria");
  const rotuloAccionObturador = document.getElementById("rotulo-accion-obturador");
  const btnDisparador = document.getElementById("btn-disparador");
  const btnGaleriaCamara = document.getElementById("btn-galeria-camara");
  const btnCambiarCamara = document.getElementById("btn-cambiar-camara");

  // Elementos de pantalla Leyendo
  const miniaturaFoto = document.getElementById("miniatura-foto");
  const btnCancelarLectura = document.getElementById("btn-cancelar-lectura");

  // Elementos de Modo Rápido (Diego)
  const btnVolverRapido = document.getElementById("btn-volver-rapido");
  const btnPerspFoto = document.getElementById("btn-persp-foto");
  const btnPerspLimpio = document.getElementById("btn-persp-limpio");
  const envolturaProyeccionFoto = document.getElementById("envoltura-proyeccion-foto");
  const imgFotoCapturada = document.getElementById("img-foto-capturada");
  const svgProyeccionNumeros = document.getElementById("svg-proyeccion-numeros");
  const tableroEnvolturaRapido = document.getElementById("tablero-envoltura-rapido");
  const chipLatenciaRapido = document.getElementById("chip-latencia-rapido");
  const chipConfianzaRapido = document.getElementById("chip-confianza-rapido");
  const avisosRapido = document.getElementById("avisos-rapido");
  const listaAvisosRapido = document.getElementById("lista-avisos-rapido");
  const reparacionesRapido = document.getElementById("reparaciones-rapido");
  const listaReparacionesRapido = document.getElementById("lista-reparaciones-rapido");
  const btnOtraFotoRapido = document.getElementById("btn-otra-foto-rapido");

  // Elementos de Modo Asistencia (Marta)
  const btnVolverAsistencia = document.getElementById("btn-volver-asistencia");
  const tableroEnvolturaAsistencia = document.getElementById("tablero-envoltura-asistencia");
  const btnToggleAnotar = document.getElementById("btn-toggle-anotar");
  const textoBtnAnotar = document.getElementById("texto-btn-anotar");
  const guiaToqueCasilla = document.getElementById("guia-toque-casilla");
  const btnVoyBien = document.getElementById("btn-voy-bien");
  const scaffoldNivel1 = document.getElementById("scaffold-nivel-1");
  const tituloAndamiaje1 = document.getElementById("titulo-andamiaje-1");
  const descAndamiaje1 = document.getElementById("desc-andamiaje-1");
  const scaffoldNivel2 = document.getElementById("scaffold-nivel-2");
  const alertaTituloL2 = document.getElementById("alerta-titulo-l2");
  const alertaDescL2 = document.getElementById("alerta-desc-l2");
  const btnSenalarJaula = document.getElementById("btn-senalar-jaula");
  const scaffoldNivel3 = document.getElementById("scaffold-nivel-3");
  const alertaDescL3 = document.getElementById("alerta-desc-l3");
  const btnExplicarRegla = document.getElementById("btn-explicar-regla");
  const scaffoldNivel4 = document.getElementById("scaffold-nivel-4");
  const textoReglaLogica = document.getElementById("texto-regla-logica");
  const btnRevelarJaula = document.getElementById("btn-revelar-jaula");
  const avisosAsistencia = document.getElementById("avisos-asistencia");
  const listaAvisosAsistencia = document.getElementById("lista-avisos-asistencia");
  const reparacionesAsistencia = document.getElementById("reparaciones-asistencia");
  const listaReparacionesAsistencia = document.getElementById("lista-reparaciones-asistencia");
  const btnMartaRevelarTodo = document.getElementById("btn-marta-revelar-todo");
  const btnOtraFotoAsistencia = document.getElementById("btn-otra-foto-asistencia");

  // Elementos de vista Inválido (sin_solucion / varias)
  const btnVolverInvalido = document.getElementById("btn-volver-invalido");
  const invalidoTitulo = document.getElementById("invalido-titulo");
  const invalidoMensaje = document.getElementById("invalido-mensaje");
  const tableroEnvolturaInvalido = document.getElementById("tablero-envoltura-invalido");
  const btnOtraFotoInvalido = document.getElementById("btn-otra-foto-invalido");

  // Diálogos modales
  const dialogoErrorAccionable = document.getElementById("dialogo-error-accionable");
  const modalErrorIcono = document.getElementById("modal-error-icono");
  const modalErrorTitulo = document.getElementById("modal-error-titulo");
  const modalErrorDesc = document.getElementById("modal-error-desc");
  const modalErrorConsejo = document.getElementById("modal-error-consejo");
  const modalErrorAcciones = document.getElementById("modal-error-acciones");
  const btnModalErrorEntendido = document.getElementById("btn-modal-error-entendido");

  const dialogoConfirmarSpoiler = document.getElementById("dialogo-confirmar-spoiler");
  const btnCancelarSpoiler = document.getElementById("btn-cancelar-spoiler");
  const btnConfirmarSpoiler = document.getElementById("btn-confirmar-spoiler");

  const dialogoAjustes = document.getElementById("dialogo-ajustes");
  const btnCerrarAjustes = document.getElementById("btn-cerrar-ajustes");
  const btnCancelarAjustes = document.getElementById("btn-cancelar-ajustes");
  const formAjustes = document.getElementById("form-ajustes");
  const inputUrlNodo = document.getElementById("input-url-nodo");
  const resultadoPrueba = document.getElementById("resultado-prueba");

  const dialogoTecladoAnotar = document.getElementById("dialogo-teclado-anotar");
  const tituloTecladoAnotar = document.getElementById("titulo-teclado-anotar");
  const rejillaTeclado = document.getElementById("rejilla-teclado");
  const btnBorrarAnotacion = document.getElementById("btn-borrar-anotacion");
  const btnCancelarTeclado = document.getElementById("btn-cancelar-teclado");
  const btnCerrarTeclado = document.getElementById("btn-cerrar-teclado");

  // Entradas de archivo ocultas para fallback
  const inputCamaraArchivo = document.getElementById("input-camara-archivo");
  const inputGaleriaArchivo = document.getElementById("input-galeria-archivo");

  // ========================================================
  // UTILIDADES: HÁPTICA Y DIÁLOGOS
  // ========================================================
  function triggerHaptic(patron = 20) {
    if (typeof navigator.vibrate === "function") {
      try {
        navigator.vibrate(patron);
      } catch (_) {
        // Ignorar si el navegador bloquea vibración sin gesto previo
      }
    }
  }

  function abrirDialogo(d) {
    if (typeof d.showModal === "function") {
      try {
        if (!d.open) d.showModal();
      } catch (_) {
        d.setAttribute("open", "");
      }
    } else {
      d.setAttribute("open", "");
    }
  }

  function cerrarDialogo(d) {
    if (typeof d.close === "function") {
      try {
        if (d.open) d.close();
      } catch (_) {
        d.removeAttribute("open");
      }
    } else {
      d.removeAttribute("open");
    }
  }

  // ========================================================
  // NAVEGACIÓN ENTRE VISTAS
  // ========================================================
  function mostrarVista(nombre) {
    vistaCamara.classList.toggle("vista-oculta", nombre !== "camara");
    vistaLeyendo.classList.toggle("vista-oculta", nombre !== "leyendo");
    vistaRapido.classList.toggle("vista-oculta", nombre !== "rapido");
    vistaAsistencia.classList.toggle("vista-oculta", nombre !== "asistencia");
    vistaInvalido.classList.toggle("vista-oculta", nombre !== "invalido");

    if (nombre === "camara") {
      iniciarCamara();
    } else {
      detenerMuestreoLuminancia();
    }
  }

  // ========================================================
  // CONEXIÓN Y ESTADO DEL NODO (GET /salud)
  // ========================================================
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
          nodoConectado = true;
          nodoNombre = datos.nodo;
          puntoEstado.className = "punto-estado conectado";
          textoEstado.textContent = `Nodo: ${datos.nodo}`;
          actualizarGuiaCamara();
          return { ok: true, nodo: datos.nodo };
        }
      }
    } catch (_) {
      // Error de red o tiempo de espera
    }

    nodoConectado = false;
    nodoNombre = "";
    puntoEstado.className = "punto-estado desconectado";
    textoEstado.textContent = "Buscando nodo…";
    actualizarGuiaCamara();
    return { ok: false };
  }

  // ========================================================
  // SELECTOR DE MODO (ASISTENCIA / RÁPIDO)
  // ========================================================
  function establecerModo(modo, conHaptico = true) {
    modoActual = modo;
    localStorage.setItem(CLAVE_MODO, modo);

    const esAsistencia = modo === "asistencia";
    btnModoAsistencia.classList.toggle("activo", esAsistencia);
    btnModoAsistencia.setAttribute("aria-checked", esAsistencia ? "true" : "false");

    btnModoRapido.classList.toggle("activo", !esAsistencia);
    btnModoRapido.setAttribute("aria-checked", !esAsistencia ? "true" : "false");

    rotuloAccionObturador.textContent = esAsistencia
      ? "Verificar mi avance a lápiz (¿Voy bien?)"
      : "Resolver todo el tablero (Modo Rápido)";

    if (conHaptico) {
      triggerHaptic(20);
    }
  }

  btnModoAsistencia.addEventListener("click", () => establecerModo("asistencia"));
  btnModoRapido.addEventListener("click", () => establecerModo("rapido"));
  establecerModo(modoActual, false);

  // ========================================================
  // 1. VISOR DE CÁMARA EN VIVO Y LUMINANCIA REAL
  // ========================================================
  async function iniciarCamara() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      mostrarFallbackCamara();
      return;
    }

    try {
      if (camaraStream) {
        camaraStream.getTracks().forEach((t) => t.stop());
      }

      camaraStream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: { ideal: facingModeActual },
          width: { ideal: 1920 },
          height: { ideal: 1080 },
        },
        audio: false,
      });

      videoStream.srcObject = camaraStream;
      videoStream.classList.remove("vista-oculta");
      fallbackCamara.classList.add("vista-oculta");

      videoStream.onloadedmetadata = () => {
        videoStream.play().catch(() => {});
        iniciarMuestreoLuminancia();
      };
    } catch (err) {
      console.warn("No se pudo iniciar la cámara web en vivo:", err);
      mostrarFallbackCamara();
    }
  }

  function mostrarFallbackCamara() {
    videoStream.classList.add("vista-oculta");
    fallbackCamara.classList.remove("vista-oculta");
    detenerMuestreoLuminancia();
    actualizarGuiaCamara();
  }

  function detenerMuestreoLuminancia() {
    if (intervaloMuestreoLuminancia) {
      clearInterval(intervaloMuestreoLuminancia);
      intervaloMuestreoLuminancia = null;
    }
  }

  function iniciarMuestreoLuminancia() {
    if (!canvasLuminancia) {
      canvasLuminancia = document.createElement("canvas");
      canvasLuminancia.width = 32;
      canvasLuminancia.height = 32;
      ctxLuminancia = canvasLuminancia.getContext("2d", { willReadFrequently: true });
    }
    detenerMuestreoLuminancia();
    intervaloMuestreoLuminancia = setInterval(verificarLuminanciaVideo, 500);
  }

  function verificarLuminanciaVideo() {
    if (!camaraStream || !videoStream || videoStream.readyState < 2) return;
    try {
      ctxLuminancia.drawImage(videoStream, 0, 0, 32, 32);
      const imgData = ctxLuminancia.getImageData(0, 0, 32, 32);
      const data = imgData.data;
      let suma = 0;
      const total = 32 * 32;
      for (let i = 0; i < data.length; i += 4) {
        suma += 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
      }
      const media = suma / total;
      bajaLuminancia = media < 45;
      actualizarGuiaCamara();
    } catch (_) {}
  }

  function actualizarGuiaCamara() {
    if (!nodoConectado) {
      // 1. Sin conexión con el nodo: disparador deshabilitado
      reticulaCaja.className = "reticula reticulo-error";
      pildoraGuia.className = "pildora-guia guia-error";
      textoGuia.textContent = "Sin conexión con el nodo";
      iconoGuia.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="1" y1="1" x2="23" y2="23"/>
          <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
          <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
          <path d="M10.71 5.05A16 16 0 0 1 22.58 9"/>
          <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
          <line x1="12" y1="20" x2="12.01" y2="20"/>
        </svg>
      `;
      btnDisparador.disabled = true;
      return;
    }

    if (bajaLuminancia) {
      // 2. Poca luz real medida en el video
      reticulaCaja.className = "reticula reticulo-aviso";
      pildoraGuia.className = "pildora-guia guia-aviso";
      textoGuia.textContent = "Poca luz · acércate a una ventana o enciende una lámpara";
      iconoGuia.innerHTML = `
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
      `;
      btnDisparador.disabled = false;
      return;
    }

    // 3. Todo bien: listo para capturar
    reticulaCaja.className = "reticula reticulo-listo";
    pildoraGuia.className = "pildora-guia guia-listo";
    textoGuia.textContent = "Listo para capturar";
    iconoGuia.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="20 6 9 17 4 12"/>
      </svg>
    `;
    btnDisparador.disabled = false;

    const ahora = Date.now();
    if (ahora - ultimoHapticoListo > 4000) {
      triggerHaptic(15);
      ultimoHapticoListo = ahora;
    }
  }

  // Cambiar orientación de cámara (delantera / trasera)
  btnCambiarCamara.addEventListener("click", () => {
    facingModeActual = facingModeActual === "environment" ? "user" : "environment";
    iniciarCamara();
  });

  // ========================================================
  // CAPTURA Y OBTURACIÓN (DESDE VIDEO O NATIVO)
  // ========================================================
  async function capturarDesdeVideo() {
    if (!nodoConectado) {
      triggerHaptic([40, 60, 40]);
      mostrarErrorAccionable({
        tipo: "red",
        titulo: "Sin conexión con el nodo",
        desc: "No podemos resolver el KenKen porque la app no tiene contacto con la PC del nodo de cómputo.",
        tip: "Verifica que ambos dispositivos estén en la misma red Wi-Fi o revisa la dirección en Ajustes.",
      });
      return;
    }

    if (videoStream && !videoStream.classList.contains("vista-oculta") && videoStream.videoWidth > 0) {
      triggerHaptic(30);

      const maxLado = 2000;
      let w = videoStream.videoWidth;
      let h = videoStream.videoHeight;
      if (w > maxLado || h > maxLado) {
        if (w > h) {
          h = Math.round((h * maxLado) / w);
          w = maxLado;
        } else {
          w = Math.round((w * maxLado) / h);
          h = maxLado;
        }
      }

      const canvas = document.createElement("canvas");
      canvas.width = w;
      canvas.height = h;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(videoStream, 0, 0, w, h);
      const dataUrl = canvas.toDataURL("image/jpeg", 0.85);

      procesarFoto(dataUrl);
    } else {
      // Si la cámara en vivo no está activa, usamos el selector de foto
      iniciarCapturaDispositivo("camera");
    }
  }

  btnDisparador.addEventListener("click", capturarDesdeVideo);

  // Fallbacks: Capacitor o input file
  async function iniciarCapturaDispositivo(origen) {
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
        console.warn("Captura en dispositivo cancelada:", err);
      }
    } else {
      if (origen === "camera") {
        inputCamaraArchivo.click();
      } else {
        inputGaleriaArchivo.click();
      }
    }
  }

  btnGaleriaCamara.addEventListener("click", () => iniciarCapturaDispositivo("photos"));
  btnFallbackFoto.addEventListener("click", () => iniciarCapturaDispositivo("camera"));
  btnFallbackGaleria.addEventListener("click", () => iniciarCapturaDispositivo("photos"));

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

  inputCamaraArchivo.addEventListener("change", leerArchivoSeleccionado);
  inputGaleriaArchivo.addEventListener("change", leerArchivoSeleccionado);

  // ========================================================
  // ENVÍO AL NODO (POST /resolver)
  // ========================================================
  async function procesarFoto(dataUrl) {
    ultimaFoto = dataUrl;
    celdasReveladas.clear();
    anotacionesMarta.clear();
    celdaConflictoActual = null;
    jaulaConflictoIdx = -1;
    modoAnotacionActivo = false;
    actualizarEstadoBotonAnotar();

    miniaturaFoto.src = dataUrl;
    mostrarVista("leyendo");

    controladorActual = new AbortController();
    const timeoutId = setTimeout(() => controladorActual.abort(), 30000);

    try {
      const res = await fetch(`${obtenerUrlNodo()}/resolver`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imagen: dataUrl }),
        signal: controladorActual.signal,
      });
      clearTimeout(timeoutId);

      if (!res.ok) {
        let detalle = "";
        try {
          const errJson = await res.json();
          detalle = errJson.detail || errJson.mensaje || JSON.stringify(errJson);
        } catch (_) {
          detalle = await res.text();
        }
        triggerHaptic([40, 60, 40]);
        mostrarErrorAccionable({
          tipo: "red",
          titulo: "Error en el nodo de cómputo",
          desc: detalle || `El servidor respondió con código ${res.status}.`,
          tip: "Revisa los registros en la terminal de tu PC.",
        });
        return;
      }

      const datos = await res.json();
      ultimoResultado = datos;
      enrutarRespuestaNodo(datos);
    } catch (err) {
      clearTimeout(timeoutId);
      triggerHaptic([40, 60, 40]);
      if (err.name === "AbortError") {
        mostrarErrorAccionable({
          tipo: "red",
          titulo: "Tiempo de espera agotado",
          desc: "El nodo de cómputo tardó más de 30 segundos en procesar la imagen.",
          tip: "Comprueba que la PC no esté sobrecargada o procesando un tablero muy grande.",
        });
      } else {
        mostrarErrorAccionable({
          tipo: "red",
          titulo: "No encuentro el nodo",
          desc: "No pudimos comunicar con la API en el nodo de cómputo.",
          tip: "Revisa que la PC esté encendida y en la misma red Wi-Fi, o reconecta la depuración USB.",
        });
      }
    }
  }

  btnCancelarLectura.addEventListener("click", () => {
    if (controladorActual) {
      controladorActual.abort();
    }
    mostrarVista("camara");
  });

  // ========================================================
  // ENRUTADOR SEGÚN CONTRATO DEL NODO (Heurística 9)
  // ========================================================
  function enrutarRespuestaNodo(datos) {
    const estado = datos.estado;

    if (estado === "sin_tablero") {
      triggerHaptic([40, 60, 40]);
      mostrarErrorAccionable({
        tipo: "sin_tablero",
        titulo: "No encuentro el tablero",
        desc: "No encuentro el tablero: aléjate un poco para que entre el borde exterior completo.",
        tip: "Mantén el teléfono paralelo a la mesa y asegúrate de que las 4 esquinas del recuadro queden dentro de la foto.",
        onAccion: () => mostrarVista("camara"),
      });
      return;
    }

    if (estado === "ilegible") {
      triggerHaptic([40, 60, 40]);
      mostrarErrorAccionable({
        tipo: "ilegible",
        titulo: "No pude leer una etiqueta",
        desc: "No pude leer una etiqueta: acércate y evita sombras sobre el papel.",
        tip: "Comprueba que la tinta esté nítida, haya buena luz y el teléfono enfoque correctamente las esquinas superiores de las jaulas.",
        onAccion: () => mostrarVista("camara"),
      });
      return;
    }

    if (estado === "sin_solucion" || estado === "varias") {
      triggerHaptic([40, 60, 40]);
      if (datos.jaulas && datos.jaulas.length > 0 && typeof datos.n === "number") {
        // Honestidad de lectura: dibujar el tablero leído sin valores para que la persona vea lo que se detectó
        mostrarVista("invalido");
        invalidoTitulo.textContent = estado === "varias" ? "Múltiples soluciones posibles" : "Sin solución única";
        invalidoMensaje.textContent = datos.mensaje || "Leí algo mal: con las etiquetas detectadas el tablero no tiene solución.";
        dibujarTablero({
          n: datos.n,
          jaulas: datos.jaulas,
          solucion: null,
          modo: "invalido",
          contenedor: tableroEnvolturaInvalido,
        });
      } else {
        mostrarErrorAccionable({
          tipo: "sin_solucion",
          titulo: estado === "varias" ? "Múltiples soluciones" : "Sin solución",
          desc: datos.mensaje || "Leí algo mal: el tablero no tiene solución única.",
          tip: "Toma otra foto más de frente y asegurando que ninguna jaula se corte.",
          onAccion: () => mostrarVista("camara"),
        });
      }
      return;
    }

    // Estados resuelto y reparado
    triggerHaptic([25, 40, 25]);
    if (modoActual === "rapido") {
      mostrarVista("rapido");
      configurarModoRapido(datos);
    } else {
      mostrarVista("asistencia");
      configurarModoAsistencia(datos);
    }
  }

  // ========================================================
  // 3. MODO RÁPIDO (DIEGO - PROYECCIÓN Y TABLERO LIMPIO)
  // ========================================================
  function configurarModoRapido(datos) {
    const correcciones = Array.isArray(datos.correcciones) ? datos.correcciones : [];
    const corregidas = new Set(correcciones.map((c) => `${c.celda[0]},${c.celda[1]}`));

    // Renderizar tablero limpio
    dibujarTablero({
      n: datos.n,
      jaulas: datos.jaulas,
      solucion: datos.solucion,
      modo: "rapido",
      corregidas,
      contenedor: tableroEnvolturaRapido,
    });

    // Proyección sobre la foto capturada con centros de homografía
    renderizarProyeccionFoto(datos.en_foto, datos.solucion, ultimaFoto);

    // Chips con datos reales
    if (datos.ms && typeof datos.ms.vision === "number" && typeof datos.ms.solver === "number") {
      const msTotal = Math.round(datos.ms.vision + datos.ms.solver);
      chipLatenciaRapido.textContent = `Resuelto en ${msTotal} ms`;
      chipLatenciaRapido.classList.remove("vista-oculta");
    } else {
      chipLatenciaRapido.classList.add("vista-oculta");
    }

    if (datos.n && datos.confianza !== null && datos.confianza !== undefined) {
      chipConfianzaRapido.textContent = `Tablero ${datos.n}×${datos.n} · confianza ${Math.round(datos.confianza * 100)}%`;
      chipConfianzaRapido.classList.remove("vista-oculta");
    } else if (datos.n) {
      chipConfianzaRapido.textContent = `Tablero ${datos.n}×${datos.n}`;
      chipConfianzaRapido.classList.remove("vista-oculta");
    } else {
      chipConfianzaRapido.classList.add("vista-oculta");
    }

    // Manejo de reparado: correcciones reportadas honestamente
    listaReparacionesRapido.innerHTML = "";
    if (correcciones.length > 0) {
      correcciones.forEach((c) => {
        const li = document.createElement("li");
        const leido = `${c.leido.objetivo}${formatearOperador(c.leido.op)}`;
        const es = `${c.corregido.objetivo}${formatearOperador(c.corregido.op)}`;
        li.textContent = `Fila ${c.celda[0] + 1}, columna ${c.celda[1] + 1}: leí ${leido}, es ${es}`;
        listaReparacionesRapido.appendChild(li);
      });
      reparacionesRapido.classList.remove("vista-oculta");
    } else {
      reparacionesRapido.classList.add("vista-oculta");
    }

    // Avisos generales
    listaAvisosRapido.innerHTML = "";
    if (Array.isArray(datos.avisos) && datos.avisos.length > 0) {
      datos.avisos.forEach((a) => {
        const li = document.createElement("li");
        li.textContent = a;
        listaAvisosRapido.appendChild(li);
      });
      avisosRapido.classList.remove("vista-oculta");
    } else {
      avisosRapido.classList.add("vista-oculta");
    }

    // Por defecto, intentar mostrar sobre la foto si hay centros
    if (datos.en_foto && datos.en_foto.centros) {
      activarPerspectivaRapido("foto");
    } else {
      activarPerspectivaRapido("limpio");
    }
  }

  function renderizarProyeccionFoto(enFoto, solucion, urlFoto) {
    svgProyeccionNumeros.innerHTML = "";
    imgFotoCapturada.src = urlFoto || "";

    if (!enFoto || !Array.isArray(enFoto.centros) || !solucion) {
      btnPerspFoto.disabled = true;
      btnPerspFoto.classList.add("vista-oculta");
      activarPerspectivaRapido("limpio");
      return;
    }

    btnPerspFoto.disabled = false;
    btnPerspFoto.classList.remove("vista-oculta");

    const centros = enFoto.centros;
    const n = centros.length;

    const trazarNumeros = () => {
      const W = imgFotoCapturada.naturalWidth || 1000;
      const H = imgFotoCapturada.naturalHeight || 1000;
      svgProyeccionNumeros.setAttribute("viewBox", `0 0 ${W} ${H}`);

      // Distancia euclídea media entre celdas vecinas para fijar tamaño de fuente proporcional
      let sumaDist = 0;
      let countDist = 0;

      for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
          if (c + 1 < n) {
            const dx = (centros[r][c + 1][0] - centros[r][c][0]) * W;
            const dy = (centros[r][c + 1][1] - centros[r][c][1]) * H;
            sumaDist += Math.hypot(dx, dy);
            countDist++;
          }
          if (r + 1 < n) {
            const dx = (centros[r + 1][c][0] - centros[r][c][0]) * W;
            const dy = (centros[r + 1][c][1] - centros[r][c][1]) * H;
            sumaDist += Math.hypot(dx, dy);
            countDist++;
          }
        }
      }

      const distMedia = countDist > 0 ? sumaDist / countDist : 60;
      const tamFuente = Math.max(16, Math.round(distMedia * 0.55));
      const contornoGrosor = Math.max(2, Math.round(tamFuente * 0.12));

      for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
          const cx = centros[r][c][0] * W;
          const cy = centros[r][c][1] * H;
          const val = solucion[r][c];

          const textEl = document.createElementNS("http://www.w3.org/2000/svg", "text");
          textEl.setAttribute("x", cx);
          textEl.setAttribute("y", cy);
          textEl.setAttribute("font-size", tamFuente);
          textEl.setAttribute("text-anchor", "middle");
          textEl.setAttribute("dominant-baseline", "central");
          textEl.setAttribute("class", "numero-proyectado");
          textEl.style.strokeWidth = `${contornoGrosor}px`;
          textEl.textContent = val;
          svgProyeccionNumeros.appendChild(textEl);
        }
      }
    };

    if (imgFotoCapturada.complete && imgFotoCapturada.naturalWidth > 0) {
      trazarNumeros();
    } else {
      imgFotoCapturada.onload = trazarNumeros;
    }
  }

  function activarPerspectivaRapido(tipo) {
    const esFoto = tipo === "foto";
    btnPerspFoto.classList.toggle("activo", esFoto);
    btnPerspFoto.setAttribute("aria-checked", esFoto ? "true" : "false");

    btnPerspLimpio.classList.toggle("activo", !esFoto);
    btnPerspLimpio.setAttribute("aria-checked", !esFoto ? "true" : "false");

    envolturaProyeccionFoto.classList.toggle("vista-oculta", !esFoto);
    tableroEnvolturaRapido.classList.toggle("vista-oculta", esFoto);
  }

  btnPerspFoto.addEventListener("click", () => activarPerspectivaRapido("foto"));
  btnPerspLimpio.addEventListener("click", () => activarPerspectivaRapido("limpio"));
  btnVolverRapido.addEventListener("click", () => mostrarVista("camara"));
  btnOtraFotoRapido.addEventListener("click", () => mostrarVista("camara"));

  // ========================================================
  // 4. MODO ASISTENCIA (MARTA - ANDAMIAJE COGNITIVO)
  // ========================================================
  function configurarModoAsistencia(datos) {
    celdasReveladas.clear();
    anotacionesMarta.clear();
    celdaConflictoActual = null;
    jaulaConflictoIdx = -1;

    resetearAndamiajeMarta();
    renderizarTableroMarta();

    // Reparaciones
    const correcciones = Array.isArray(datos.correcciones) ? datos.correcciones : [];
    listaReparacionesAsistencia.innerHTML = "";
    if (correcciones.length > 0) {
      correcciones.forEach((c) => {
        const li = document.createElement("li");
        const leido = `${c.leido.objetivo}${formatearOperador(c.leido.op)}`;
        const es = `${c.corregido.objetivo}${formatearOperador(c.corregido.op)}`;
        li.textContent = `Fila ${c.celda[0] + 1}, columna ${c.celda[1] + 1}: leí ${leido}, es ${es}`;
        listaReparacionesAsistencia.appendChild(li);
      });
      reparacionesAsistencia.classList.remove("vista-oculta");
    } else {
      reparacionesAsistencia.classList.add("vista-oculta");
    }

    // Avisos
    listaAvisosAsistencia.innerHTML = "";
    if (Array.isArray(datos.avisos) && datos.avisos.length > 0) {
      datos.avisos.forEach((a) => {
        const li = document.createElement("li");
        li.textContent = a;
        listaAvisosAsistencia.appendChild(li);
      });
      avisosAsistencia.classList.remove("vista-oculta");
    } else {
      avisosAsistencia.classList.add("vista-oculta");
    }
  }

  function resetearAndamiajeMarta() {
    scaffoldNivel1.classList.remove("vista-oculta");
    tituloAndamiaje1.textContent = "Verificación de tus números";
    descAndamiaje1.textContent = "Anota lo que tienes a lápiz y pulsa '¿Voy bien?' para comprobar tu avance.";
    scaffoldNivel2.classList.add("vista-oculta");
    scaffoldNivel3.classList.add("vista-oculta");
    scaffoldNivel4.classList.add("vista-oculta");
    jaulaConflictoIdx = -1;
  }

  function renderizarTableroMarta() {
    if (!ultimoResultado) return;
    const correcciones = Array.isArray(ultimoResultado.correcciones) ? ultimoResultado.correcciones : [];
    const corregidas = new Set(correcciones.map((c) => `${c.celda[0]},${c.celda[1]}`));

    dibujarTablero({
      n: ultimoResultado.n,
      jaulas: ultimoResultado.jaulas,
      solucion: ultimoResultado.solucion,
      modo: "asistencia",
      celdasReveladas,
      anotaciones: anotacionesMarta,
      jaulaResaltada: jaulaConflictoIdx,
      corregidas,
      onCeldaClick: manejarToqueCeldaMarta,
      contenedor: tableroEnvolturaAsistencia,
    });
  }

  function actualizarEstadoBotonAnotar() {
    btnToggleAnotar.classList.toggle("activo", modoAnotacionActivo);
    btnToggleAnotar.setAttribute("aria-pressed", modoAnotacionActivo ? "true" : "false");
    textoBtnAnotar.textContent = modoAnotacionActivo
      ? "Anotando a lápiz (toca una casilla)"
      : "Anotar lo que llevo";
    guiaToqueCasilla.textContent = modoAnotacionActivo
      ? "Toca una casilla para ingresar o cambiar tu número a lápiz"
      : "Toca una casilla vacía para revelar su número";
  }

  btnToggleAnotar.addEventListener("click", () => {
    modoAnotacionActivo = !modoAnotacionActivo;
    triggerHaptic(15);
    actualizarEstadoBotonAnotar();
  });

  function manejarToqueCeldaMarta(r, c) {
    if (!ultimoResultado || !ultimoResultado.solucion) return;

    if (modoAnotacionActivo) {
      // Abrir teclado táctil para anotar número a lápiz
      celdaSeleccionadaAnotar = { r, c };
      abrirTecladoAnotacion(r, c, ultimoResultado.n);
    } else {
      // Tocar celda vacía revela directamente su número (asistencia individual)
      const clave = `${r},${c}`;
      if (!celdasReveladas.has(clave)) {
        celdasReveladas.add(clave);
        anotacionesMarta.delete(clave);
        triggerHaptic(25);
        renderizarTableroMarta();
      }
    }
  }

  // Teclado numérico grande para Marta (1..n)
  function abrirTecladoAnotacion(r, c, n) {
    tituloTecladoAnotar.textContent = `Anotar en fila ${r + 1}, columna ${c + 1}`;
    rejillaTeclado.innerHTML = "";

    const valorActual = anotacionesMarta.get(`${r},${c}`);

    for (let num = 1; num <= n; num++) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn-tecla-numero";
      btn.textContent = num;
      if (valorActual === num) {
        btn.style.borderColor = "var(--acento)";
      }
      btn.addEventListener("click", () => {
        anotacionesMarta.set(`${r},${c}`, num);
        triggerHaptic(20);
        cerrarDialogo(dialogoTecladoAnotar);
        renderizarTableroMarta();
      });
      rejillaTeclado.appendChild(btn);
    }

    abrirDialogo(dialogoTecladoAnotar);
  }

  btnBorrarAnotacion.addEventListener("click", () => {
    if (celdaSeleccionadaAnotar) {
      anotacionesMarta.delete(`${celdaSeleccionadaAnotar.r},${celdaSeleccionadaAnotar.c}`);
      triggerHaptic(20);
      renderizarTableroMarta();
    }
    cerrarDialogo(dialogoTecladoAnotar);
  });

  btnCancelarTeclado.addEventListener("click", () => cerrarDialogo(dialogoTecladoAnotar));
  btnCerrarTeclado.addEventListener("click", () => cerrarDialogo(dialogoTecladoAnotar));

  // NIVEL 1: "¿Voy bien?"
  btnVoyBien.addEventListener("click", () => {
    if (!ultimoResultado || !ultimoResultado.solucion) return;

    if (anotacionesMarta.size === 0) {
      triggerHaptic(20);
      descAndamiaje1.textContent = "Aún no has anotado números. Toca 'Anotar lo que llevo' para ingresar lo que tienes a lápiz en el papel.";
      return;
    }

    let correctos = 0;
    const fallos = [];

    anotacionesMarta.forEach((valorAnotado, clave) => {
      const [r, c] = clave.split(",").map(Number);
      const valorReal = ultimoResultado.solucion[r][c];
      if (valorAnotado === valorReal) {
        correctos++;
      } else {
        fallos.push({ r, c, anotado: valorAnotado, real: valorReal });
      }
    });

    if (fallos.length === 0) {
      triggerHaptic(30);
      tituloAndamiaje1.textContent = "¡Vas excelente!";
      descAndamiaje1.textContent = `Vas bien: ${correctos === 1 ? "tu 1 número cuadra" : `tus ${correctos} números cuadran`} perfectamente con las reglas.`;
      scaffoldNivel2.classList.add("vista-oculta");
      scaffoldNivel3.classList.add("vista-oculta");
      scaffoldNivel4.classList.add("vista-oculta");
      jaulaConflictoIdx = -1;
      renderizarTableroMarta();
    } else {
      triggerHaptic([40, 60, 40]);
      const m = fallos.length;
      tituloAndamiaje1.textContent = "Verificación";
      descAndamiaje1.textContent = `Hay ${m === 1 ? "1 número que no cuadra" : `${m} números que no cuadran`}. El resto de tus casillas va bien.`;

      celdaConflictoActual = fallos[0];
      alertaTituloL2.textContent = `Hay ${m === 1 ? "1 número que no cuadra" : `${m} números que no cuadran`}`;
      alertaDescL2.textContent = "Puedes señalar en el tablero cuál es la jaula que tiene el conflicto.";
      scaffoldNivel2.classList.remove("vista-oculta");
      scaffoldNivel3.classList.add("vista-oculta");
      scaffoldNivel4.classList.add("vista-oculta");
    }
  });

  // NIVEL 2: "Señalar la jaula con el error"
  btnSenalarJaula.addEventListener("click", () => {
    if (!ultimoResultado || !celdaConflictoActual) return;
    triggerHaptic(25);

    // Encontrar índice de jaula que contiene celdaConflictoActual
    const { r, c } = celdaConflictoActual;
    jaulaConflictoIdx = ultimoResultado.jaulas.findIndex((j) =>
      j.celdas.some(([cr, cc]) => cr === r && cc === c)
    );

    if (jaulaConflictoIdx !== -1) {
      renderizarTableroMarta();
      const jaula = ultimoResultado.jaulas[jaulaConflictoIdx];
      const etiqueta = `${jaula.objetivo}${formatearOperador(jaula.op)}`;
      alertaDescL3.textContent = `Conflicto en la jaula destacada con borde ámbar (etiqueta ${etiqueta}).`;
      scaffoldNivel3.classList.remove("vista-oculta");
    }
  });

  // NIVEL 3: "Explicar la regla"
  btnExplicarRegla.addEventListener("click", () => {
    if (!ultimoResultado || jaulaConflictoIdx === -1) return;
    triggerHaptic(25);

    const jaula = ultimoResultado.jaulas[jaulaConflictoIdx];
    const k = jaula.celdas.length;
    const op = jaula.op;
    const obj = jaula.objetivo;

    let explicacion = "";
    if (op === "+") {
      explicacion = `En esta jaula los ${k} números deben sumar ${obj}.`;
    } else if (op === "*") {
      explicacion = `En esta jaula los ${k} números deben multiplicar ${obj}.`;
    } else if (op === "-") {
      explicacion = `En esta jaula los 2 números deben restar ${obj} (el mayor menos el menor).`;
    } else if (op === "/") {
      explicacion = `En esta jaula los 2 números deben dividir ${obj} (el mayor entre el menor).`;
    } else if (op === "=") {
      explicacion = `En esta jaula el número debe ser ${obj}.`;
    } else {
      explicacion = `En esta jaula el objetivo es ${obj}${formatearOperador(op)}.`;
    }

    // Listar qué números anotó el usuario en esa jaula
    const anotadosEnJaula = [];
    jaula.celdas.forEach(([cr, cc]) => {
      const v = anotacionesMarta.get(`${cr},${cc}`);
      if (v !== undefined) anotadosEnJaula.push(v);
    });

    if (anotadosEnJaula.length > 0) {
      explicacion += ` Actualmente tienes anotado: ${anotadosEnJaula.join(", ")}.`;
    }

    textoReglaLogica.textContent = explicacion;
    scaffoldNivel4.classList.remove("vista-oculta");
    btnRevelarJaula.disabled = false;
    btnRevelarJaula.textContent = "Revelar esta jaula";
  });

  // NIVEL 4: "Revelar esta jaula"
  btnRevelarJaula.addEventListener("click", () => {
    if (!ultimoResultado || jaulaConflictoIdx === -1) return;
    triggerHaptic(30);

    const jaula = ultimoResultado.jaulas[jaulaConflictoIdx];
    jaula.celdas.forEach(([r, c]) => {
      celdasReveladas.add(`${r},${c}`);
      anotacionesMarta.delete(`${r},${c}`);
    });

    jaulaConflictoIdx = -1;
    renderizarTableroMarta();

    btnRevelarJaula.textContent = "Jaula revelada con éxito";
    btnRevelarJaula.disabled = true;
  });

  // Revelar toda la solución con diálogo anti-spoilers
  btnMartaRevelarTodo.addEventListener("click", () => {
    abrirDialogo(dialogoConfirmarSpoiler);
  });

  btnCancelarSpoiler.addEventListener("click", () => {
    cerrarDialogo(dialogoConfirmarSpoiler);
  });

  btnConfirmarSpoiler.addEventListener("click", () => {
    cerrarDialogo(dialogoConfirmarSpoiler);
    if (!ultimoResultado || !ultimoResultado.solucion) return;
    triggerHaptic(35);

    const n = ultimoResultado.n;
    for (let r = 0; r < n; r++) {
      for (let c = 0; c < n; c++) {
        celdasReveladas.add(`${r},${c}`);
        anotacionesMarta.delete(`${r},${c}`);
      }
    }
    jaulaConflictoIdx = -1;
    renderizarTableroMarta();
    btnMartaRevelarTodo.classList.add("vista-oculta");
  });

  btnVolverAsistencia.addEventListener("click", () => mostrarVista("camara"));
  btnOtraFotoAsistencia.addEventListener("click", () => mostrarVista("camara"));
  btnVolverInvalido.addEventListener("click", () => mostrarVista("camara"));
  btnOtraFotoInvalido.addEventListener("click", () => mostrarVista("camara"));

  // ========================================================
  // DIBUJADO DE TABLERO KENKEN VECTORIAL (SVG)
  // ========================================================
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

  function dibujarTablero({
    n,
    jaulas,
    solucion,
    modo,
    celdasReveladas = new Set(),
    anotaciones = new Map(),
    jaulaResaltada = -1,
    corregidas = new Set(),
    onCeldaClick = null,
    contenedor,
  }) {
    contenedor.innerHTML = "";
    if (!n || !Array.isArray(jaulas)) return;

    const S = 60;
    const W = n * S;
    const H = n * S;
    const grosorBorde = 3.5;
    const margenExterior = grosorBorde / 2;

    // Mapa celda -> índice de jaula
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
        const idxJaula = mapaJaula[r][c];
        const enJaulaResaltada = jaulaResaltada !== -1 && idxJaula === jaulaResaltada;

        const valorSol = solucion ? solucion[r][c] : null;
        const esRevelada = modo === "rapido" || celdasReveladas.has(`${r},${c}`);
        const anotacion = anotaciones.get(`${r},${c}`);

        let clases = "celda";
        if (esRevelada) clases += " revelada";
        if (enJaulaResaltada) clases += " jaula-conflicto";

        gCelda.setAttribute("class", clases);
        gCelda.setAttribute("data-r", r);
        gCelda.setAttribute("data-c", c);
        gCelda.setAttribute("role", "gridcell");
        gCelda.setAttribute("tabindex", "0");

        let ariaText = `Fila ${r + 1}, columna ${c + 1}`;
        if (esRevelada && valorSol !== null) {
          ariaText += `, número ${valorSol}`;
        } else if (anotacion) {
          ariaText += `, número anotado ${anotacion}`;
        } else {
          ariaText += `, casilla vacía`;
        }
        gCelda.setAttribute("aria-label", ariaText);

        const fondo = document.createElementNS("http://www.w3.org/2000/svg", "rect");
        fondo.setAttribute("x", c * S);
        fondo.setAttribute("y", r * S);
        fondo.setAttribute("width", S);
        fondo.setAttribute("height", S);
        fondo.setAttribute("class", "fondo-celda");
        gCelda.appendChild(fondo);

        if (esRevelada && valorSol !== null) {
          const textoVal = document.createElementNS("http://www.w3.org/2000/svg", "text");
          textoVal.setAttribute("x", c * S + S / 2);
          textoVal.setAttribute("y", r * S + S / 2 + 1);
          textoVal.setAttribute("font-size", tamNumero);
          textoVal.setAttribute("text-anchor", "middle");
          textoVal.setAttribute("dominant-baseline", "central");
          textoVal.setAttribute("class", "valor-celda valor-solucion");
          textoVal.textContent = valorSol;
          gCelda.appendChild(textoVal);
        } else if (anotacion) {
          const textoVal = document.createElementNS("http://www.w3.org/2000/svg", "text");
          textoVal.setAttribute("x", c * S + S / 2);
          textoVal.setAttribute("y", r * S + S / 2 + 1);
          textoVal.setAttribute("font-size", tamNumero);
          textoVal.setAttribute("text-anchor", "middle");
          textoVal.setAttribute("dominant-baseline", "central");
          textoVal.setAttribute("class", "valor-celda valor-anotado");
          textoVal.textContent = anotacion;
          gCelda.appendChild(textoVal);
        } else if (solucion && modo === "asistencia") {
          const punto = document.createElementNS("http://www.w3.org/2000/svg", "circle");
          punto.setAttribute("cx", c * S + S / 2);
          punto.setAttribute("cy", r * S + S / 2);
          punto.setAttribute("r", "3");
          punto.setAttribute("class", "punto-oculto");
          gCelda.appendChild(punto);
        }

        if (onCeldaClick) {
          const accion = () => onCeldaClick(r, c);
          gCelda.addEventListener("click", accion);
          gCelda.addEventListener("keydown", (evt) => {
            if (evt.key === "Enter" || evt.key === " ") {
              evt.preventDefault();
              accion();
            }
          });
        }

        capaCeldas.appendChild(gCelda);
      }
    }
    svg.appendChild(capaCeldas);

    // 2. Capa de líneas
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

    // Borde exterior
    const contorno = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    contorno.setAttribute("x", margenExterior);
    contorno.setAttribute("y", margenExterior);
    contorno.setAttribute("width", W - grosorBorde);
    contorno.setAttribute("height", H - grosorBorde);
    contorno.setAttribute("class", "borde-exterior");
    capaLineas.appendChild(contorno);

    svg.appendChild(capaLineas);

    // 3. Capa de etiquetas de jaulas
    const capaEtiquetas = document.createElementNS("http://www.w3.org/2000/svg", "g");
    capaEtiquetas.setAttribute("class", "capa-etiquetas");
    capaEtiquetas.style.pointerEvents = "none";

    const tamEtiqueta = Math.max(10, Math.round(S * 0.20));

    jaulas.forEach((jaula) => {
      if (!Array.isArray(jaula.celdas) || jaula.celdas.length === 0) return;
      const ordenadas = [...jaula.celdas].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
      const [anclaR, anclaC] = ordenadas[0];

      const texto = `${jaula.objetivo ?? ""}${formatearOperador(jaula.op)}`;
      if (!texto) return;

      const textoEt = document.createElementNS("http://www.w3.org/2000/svg", "text");
      textoEt.setAttribute("x", anclaC * S + 4);
      textoEt.setAttribute("y", anclaR * S + tamEtiqueta + 3);
      textoEt.setAttribute("font-size", tamEtiqueta);
      const corregida = corregidas.has(`${anclaR},${anclaC}`);
      textoEt.setAttribute("class", corregida ? "etiqueta-jaula etiqueta-corregida" : "etiqueta-jaula");
      textoEt.textContent = texto;
      capaEtiquetas.appendChild(textoEt);
    });

    svg.appendChild(capaEtiquetas);
    contenedor.appendChild(svg);
  }

  // ========================================================
  // DIÁLOGOS: ERRORES ACCIONABLES (HEURÍSTICA 9)
  // ========================================================
  function mostrarErrorAccionable({ tipo, titulo, desc, tip, onAccion }) {
    let svgIcono = "";
    if (tipo === "sin_tablero") {
      svgIcono = `
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 2v4M18 2v4M2 6h4M18 6h4M2 18h4M18 18h4M6 22v-4M18 22v-4"/>
        </svg>
      `;
    } else if (tipo === "ilegible") {
      svgIcono = `
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      `;
    } else {
      svgIcono = `
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <line x1="1" y1="1" x2="23" y2="23"/>
          <path d="M16.72 11.06A10.94 10.94 0 0 1 19 12.55"/>
          <path d="M5 12.55a10.94 10.94 0 0 1 5.17-2.39"/>
          <path d="M10.71 5.05A16 16 0 0 1 22.58 9"/>
          <path d="M1.42 9a15.91 15.91 0 0 1 4.7-2.88"/>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"/>
          <line x1="12" y1="20" x2="12.01" y2="20"/>
        </svg>
      `;
    }

    modalErrorIcono.innerHTML = svgIcono;
    modalErrorTitulo.textContent = titulo;
    modalErrorDesc.textContent = desc;
    modalErrorConsejo.innerHTML = tip ? `<strong>Consejo:</strong> ${tip}` : "";
    modalErrorConsejo.classList.toggle("vista-oculta", !tip);

    modalErrorAcciones.innerHTML = "";

    const btnOk = document.createElement("button");
    btnOk.type = "button";
    btnOk.className = "btn-primario btn-accion";
    btnOk.textContent = "Entendido, volver a intentar";
    btnOk.addEventListener("click", () => {
      cerrarDialogo(dialogoErrorAccionable);
      if (onAccion) onAccion();
      else mostrarVista("camara");
    });
    modalErrorAcciones.appendChild(btnOk);

    if (tipo === "red") {
      const btnIrAjustes = document.createElement("button");
      btnIrAjustes.type = "button";
      btnIrAjustes.className = "btn-secundario btn-accion";
      btnIrAjustes.textContent = "Ajustes de conexión";
      btnIrAjustes.addEventListener("click", () => {
        cerrarDialogo(dialogoErrorAccionable);
        btnAjustes.click();
      });
      modalErrorAcciones.appendChild(btnIrAjustes);
    }

    abrirDialogo(dialogoErrorAccionable);
  }

  btnModalErrorEntendido.addEventListener("click", () => {
    cerrarDialogo(dialogoErrorAccionable);
    mostrarVista("camara");
  });

  // ========================================================
  // AJUSTES DE CONEXIÓN
  // ========================================================
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

    const resSalud = await comprobarSalud();
    if (resSalud.ok) {
      resultadoPrueba.textContent = `Conectado a ${resSalud.nodo}`;
      resultadoPrueba.className = "resultado-prueba exito";
      triggerHaptic(20);
      setTimeout(() => {
        cerrarDialogo(dialogoAjustes);
      }, 500);
    } else {
      resultadoPrueba.textContent = "Sin conexión con el nodo en esa dirección.";
      resultadoPrueba.className = "resultado-prueba fallo";
      triggerHaptic([40, 60, 40]);
    }
  });

  // Comprobar salud periódicamente y al recuperar foco
  window.addEventListener("focus", comprobarSalud);
  setInterval(comprobarSalud, 12000);

  // Inicialización
  comprobarSalud();
  mostrarVista("camara");
});
