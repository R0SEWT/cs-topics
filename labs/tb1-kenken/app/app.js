/**
 * Lógica interactiva del Prototipo HCD KenKen (Diego & Marta).
 * Implementa las heurísticas de Nielsen, la guía de visor en tiempo real
 * y el andamiaje cognitivo progresivo (Scaffolding).
 */

document.addEventListener("DOMContentLoaded", () => {
  // Estado de la app (HCD: Asistencia por defecto para respetar el juego, Modo Rápido como acelerador)
  let currentMode = localStorage.getItem("kenken_mode") || "assist";
  let currentCondition = "ideal"; // "ideal" | "tilted" | "dark" | "cutoff" | "fused" | "offline"
  let lastReadyHaptic = 0;

  // Feedback háptico accesible (vibración física en Android)
  function triggerHaptic(pattern = 30) {
    if (navigator.vibrate) {
      try {
        navigator.vibrate(pattern);
      } catch (e) {
        // Ignorar si el navegador bloquea vibración sin interacción previa
      }
    }
  }

  // Elementos principales
  const screenCamera = document.getElementById("screen-camera");
  const screenDiego = document.getElementById("screen-diego");
  const screenMarta = document.getElementById("screen-marta");

  // Barra de selección de Modo y estado
  const btnModeAssist = document.getElementById("btn-mode-assist");
  const btnModeFast = document.getElementById("btn-mode-fast");
  const shutterActionLabel = document.getElementById("shutter-action-label");
  const statusIndicator = document.getElementById("status-indicator");
  const statusText = document.getElementById("status-text");

  // Capa de escaneo láser
  const scanningOverlay = document.getElementById("scanning-overlay");
  const scanningText = document.getElementById("scanning-text");

  // Visor y guía
  const cameraStream = document.getElementById("camera-stream");
  const simulatedCamera = document.getElementById("simulated-camera");
  const btnToggleCamera = document.getElementById("btn-toggle-camera");
  const reticleBox = document.getElementById("reticle-box");
  const cameraGuidance = document.getElementById("camera-guidance");
  const guidanceIcon = document.getElementById("guidance-icon");
  const guidanceMsg = document.getElementById("guidance-msg");
  const conditionChips = document.querySelectorAll(".btn-chip");
  const btnShutter = document.getElementById("btn-shutter");

  let currentFacingMode = "environment";

  async function initCamera() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: currentFacingMode } },
        audio: false
      });
      cameraStream.srcObject = stream;
      cameraStream.classList.remove("hidden");
      simulatedCamera.classList.add("hidden");
    } catch (err) {
      console.log("Cámara no iniciada o rechazada, usando tablero simulado:", err);
      cameraStream.classList.add("hidden");
      simulatedCamera.classList.remove("hidden");
    }
  }

  btnToggleCamera.addEventListener("click", async () => {
    currentFacingMode = currentFacingMode === "environment" ? "user" : "environment";
    if (cameraStream.srcObject) {
      cameraStream.srcObject.getTracks().forEach(t => t.stop());
    }
    await initCamera();
  });

  initCamera();

  // Diego controls
  const btnBackDiego = document.getElementById("btn-back-diego");
  const togglePhotoDiego = document.getElementById("toggle-photo-diego");
  const toggleCleanDiego = document.getElementById("toggle-clean-diego");
  const photoProjDiego = document.getElementById("photo-projection-diego");
  const cleanBoardDiego = document.getElementById("clean-board-diego");
  const btnAgainDiego = document.getElementById("btn-again-diego");

  // Marta controls
  const btnBackMarta = document.getElementById("btn-back-marta");
  const toggleCleanMarta = document.getElementById("toggle-clean-marta");
  const btnShowConflict = document.getElementById("btn-show-conflict-cage");
  const btnExplainRule = document.getElementById("btn-explain-rule");
  const btnRevealCageSol = document.getElementById("btn-reveal-cage-sol");
  const btnMartaRevealAll = document.getElementById("btn-marta-reveal-all");

  const scaffoldL1 = document.getElementById("scaffold-l1");
  const scaffoldL2 = document.getElementById("scaffold-l2");
  const scaffoldL3 = document.getElementById("scaffold-l3");
  const conflictCells = [
    document.getElementById("cell-conflict-1"),
    document.getElementById("cell-conflict-2"),
    document.getElementById("cell-conflict-3"),
  ];

  // Modales
  const modalActionable = document.getElementById("modal-actionable-error");
  const modalTitle = document.getElementById("modal-title");
  const modalDesc = document.getElementById("modal-desc");
  const modalIcon = document.getElementById("modal-icon");
  const modalTip = document.getElementById("modal-tip");
  const btnModalDismiss = document.getElementById("btn-modal-dismiss");

  const modalConfirmSpoiler = document.getElementById("modal-confirm-spoiler");
  const btnCancelSpoiler = document.getElementById("btn-cancel-spoiler");
  const btnConfirmSpoiler = document.getElementById("btn-confirm-spoiler");

  // -------------------------------------------------------------
  // 1. Selector de Modo (Asistencia por defecto vs Modo Rápido)
  // -------------------------------------------------------------
  function setMode(mode, save = true) {
    currentMode = mode;
    if (save) {
      try {
        localStorage.setItem("kenken_mode", mode);
      } catch (e) {
        // En caso de restricciones de almacenamiento local
      }
    }
    triggerHaptic(15);
    if (mode === "assist") {
      btnModeAssist.classList.add("active");
      btnModeAssist.setAttribute("aria-pressed", "true");
      btnModeFast.classList.remove("active");
      btnModeFast.setAttribute("aria-pressed", "false");
      shutterActionLabel.textContent = "🔍 Verificar mi avance a lápiz (¿Voy bien?)";
    } else {
      btnModeFast.classList.add("active");
      btnModeFast.setAttribute("aria-pressed", "true");
      btnModeAssist.classList.remove("active");
      btnModeAssist.setAttribute("aria-pressed", "false");
      shutterActionLabel.textContent = "⚡ Resolver todo el tablero (Modo Rápido)";
    }
  }

  btnModeAssist.addEventListener("click", () => setMode("assist"));
  btnModeFast.addEventListener("click", () => setMode("fast"));
  setMode(currentMode, false); // Inicializar con preferencia recordada

  // -------------------------------------------------------------
  // 2. Simulador de condiciones del visor (Active Viewfinder)
  // -------------------------------------------------------------
  const CONDITION_CONFIG = {
    ideal: {
      reticleClass: "reticle-ready",
      guidanceClass: "ready",
      icon: "✓",
      msg: "Tablero centrado · Listo para capturar",
      canCapture: true,
    },
    tilted: {
      reticleClass: "reticle-warning",
      guidanceClass: "warning",
      icon: "⚠️",
      msg: "Muy inclinada · Ponte más de frente al papel",
      canCapture: false,
      modal: {
        icon: "📐",
        title: "La foto está muy inclinada",
        desc: "Las líneas de la rejilla se deforman y el detector de perspectiva no logra cuadrarlas.",
        tip: "💡 <strong>Consejo:</strong> Mantén el teléfono paralelo a la mesa.",
      },
    },
    dark: {
      reticleClass: "reticle-warning",
      guidanceClass: "warning",
      icon: "💡",
      msg: "Poca luz · Enciende la lámpara o evita tu sombra",
      canCapture: false,
      modal: {
        icon: "💡",
        title: "Hay poca luz o mucho reflejo",
        desc: "El contraste entre la tinta del periódico y el papel es insuficiente para leer los números con seguridad.",
        tip: "💡 <strong>Consejo:</strong> Acércate a una ventana o enciende la luz de apoyo ⚡.",
      },
    },
    cutoff: {
      reticleClass: "reticle-error",
      guidanceClass: "error",
      icon: "⛔",
      msg: "Falta una parte · Aléjate para ver las 4 esquinas",
      canCapture: false,
      modal: {
        icon: "✂️",
        title: "Falta un borde del tablero",
        desc: "Una de las esquinas del KenKen quedó cortada por el borde de la cámara.",
        tip: "💡 <strong>Consejo:</strong> Aléjate unos 10 cm para que el recuadro negro exterior entre completo.",
      },
    },
    fused: {
      reticleClass: "reticle-warning",
      guidanceClass: "warning",
      icon: "🧩",
      msg: "Jaula dudosa · Trazo fino discontinuo detectado",
      canCapture: true,
      modal: {
        icon: "🧩",
        title: "Aviso de jaula dudosa (cst-90g)",
        desc: "El detector encontró dos jaulas que podrían estar unidas en una sola debido a un trazo fino discontinuo.",
        tip: "💡 <strong>Honestidad de lectura:</strong> La app señalará la jaula dudosa para que la confirmes en vez de inventar números erróneos.",
      },
    },
    offline: {
      reticleClass: "reticle-error",
      guidanceClass: "error",
      icon: "📡",
      msg: "Sin conexión con el nodo de cómputo",
      canCapture: false,
      modal: {
        icon: "📡",
        title: "No encuentro el nodo en la red Wi-Fi",
        desc: "No pudimos comunicar con la API en tu PC (192.168.1.45).",
        tip: "💡 <strong>Plan B:</strong> Verifica que ambos estén en la misma Wi-Fi o conecta tu PC al punto de acceso del teléfono.",
      },
    },
  };

  function updateCondition(cond) {
    currentCondition = cond;
    conditionChips.forEach((chip) => {
      chip.classList.toggle("active", chip.dataset.condition === cond);
    });

    const cfg = CONDITION_CONFIG[cond];
    reticleBox.className = `reticle ${cfg.reticleClass}`;
    cameraGuidance.className = `camera-guidance-pill ${cfg.guidanceClass}`;
    guidanceIcon.textContent = cfg.icon;
    guidanceMsg.textContent = cfg.msg;

    if (cond === "offline") {
      statusIndicator.className = "status-indicator";
      statusText.textContent = "Buscando nodo Wi-Fi... (Desconectado)";
    } else {
      statusIndicator.className = "status-indicator online";
      statusText.textContent = "Nodo Wi-Fi conectado: 192.168.1.45";
    }

    if (cond === "ideal") {
      const now = Date.now();
      if (now - lastReadyHaptic > 1800) {
        triggerHaptic(20);
        lastReadyHaptic = now;
      }
    }
  }

  conditionChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      updateCondition(chip.dataset.condition);
    });
  });

  // -------------------------------------------------------------
  // 3. Obturador (Shutter Button)
  // -------------------------------------------------------------
  btnShutter.addEventListener("click", () => {
    const cfg = CONDITION_CONFIG[currentCondition];
    if (!cfg.canCapture) {
      triggerHaptic([40, 50, 40]);
      modalIcon.textContent = cfg.modal.icon;
      modalTitle.textContent = cfg.modal.title;
      modalDesc.textContent = cfg.modal.desc;
      modalTip.innerHTML = cfg.modal.tip;
      modalActionable.classList.remove("hidden");
      return;
    }

    btnShutter.style.transform = "scale(0.85)";
    triggerHaptic(30);

    // Si la cámara real está transmitiendo, capturamos el cuadro
    if (cameraStream.srcObject && cameraStream.videoWidth) {
      try {
        const canvas = document.createElement("canvas");
        canvas.width = cameraStream.videoWidth;
        canvas.height = cameraStream.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(cameraStream, 0, 0, canvas.width, canvas.height);
        const snapshotUrl = canvas.toDataURL("image/jpeg", 0.85);
        photoProjDiego.style.backgroundImage = `url(${snapshotUrl})`;
        photoProjDiego.style.backgroundSize = "cover";
        photoProjDiego.style.backgroundPosition = "center";
      } catch (e) {
        console.log("No se pudo capturar snapshot de canvas:", e);
      }
    }

    // Activar capa de escaneo láser (percepción de latencia)
    scanningOverlay.classList.remove("hidden");
    scanningText.textContent = "Extrayendo rejilla y etiquetas...";

    setTimeout(() => {
      scanningText.textContent = "Resolviendo con OR-Tools CP-SAT...";
    }, 180);

    setTimeout(() => {
      btnShutter.style.transform = "scale(1)";
      scanningOverlay.classList.add("hidden");
      screenCamera.classList.remove("active");
      triggerHaptic([30, 40, 30]);

      if (currentCondition === "fused") {
        // Honestidad de lectura (cst-90g): avisar sobre jaula dudosa
        modalIcon.textContent = cfg.modal.icon;
        modalTitle.textContent = cfg.modal.title;
        modalDesc.textContent = cfg.modal.desc;
        modalTip.innerHTML = cfg.modal.tip;
        modalActionable.classList.remove("hidden");
      }

      if (currentMode === "fast") {
        screenDiego.classList.add("active");
      } else {
        resetMartaScaffolding();
        screenMarta.classList.add("active");
      }
    }, 420);
  });

  btnModalDismiss.addEventListener("click", () => {
    modalActionable.classList.add("hidden");
  });

  // -------------------------------------------------------------
  // 4. Flujo de Diego (Solución Inmediata)
  // -------------------------------------------------------------
  btnBackDiego.addEventListener("click", () => {
    screenDiego.classList.remove("active");
    screenCamera.classList.add("active");
  });

  btnAgainDiego.addEventListener("click", () => {
    screenDiego.classList.remove("active");
    screenCamera.classList.add("active");
  });

  togglePhotoDiego.addEventListener("click", () => {
    togglePhotoDiego.classList.add("active");
    toggleCleanDiego.classList.remove("active");
    photoProjDiego.classList.remove("hidden");
    cleanBoardDiego.classList.add("hidden");
  });

  toggleCleanDiego.addEventListener("click", () => {
    toggleCleanDiego.classList.add("active");
    togglePhotoDiego.classList.remove("active");
    cleanBoardDiego.classList.remove("hidden");
    photoProjDiego.classList.add("hidden");
  });

  // -------------------------------------------------------------
  // 5. Flujo de Marta (Andamiaje Cognitivo Graduado)
  // -------------------------------------------------------------
  function resetMartaScaffolding() {
    scaffoldL1.classList.remove("hidden");
    scaffoldL2.classList.add("hidden");
    scaffoldL3.classList.add("hidden");
    conflictCells.forEach((c) => c.classList.remove("conflict-cage-highlight"));
    // Restaurar valores erróneos de Marta para la prueba
    const errorCandidates = document.querySelectorAll(".error-candidate");
    if (errorCandidates.length >= 3) {
      errorCandidates[0].textContent = "3";
      errorCandidates[1].textContent = "1";
      errorCandidates[2].textContent = "3";
      errorCandidates.forEach((el) => (el.style.color = "var(--pencil-lead)"));
    }
  }

  btnBackMarta.addEventListener("click", () => {
    screenMarta.classList.remove("active");
    screenCamera.classList.add("active");
  });

  // Nivel 1 -> Nivel 2: Señalar espacialmente la jaula
  btnShowConflict.addEventListener("click", () => {
    scaffoldL1.classList.add("hidden");
    scaffoldL2.classList.remove("hidden");
    conflictCells.forEach((c) => c.classList.add("conflict-cage-highlight"));
  });

  // Nivel 2 -> Nivel 3: Explicar la regla lógica rota
  btnExplainRule.addEventListener("click", () => {
    scaffoldL2.classList.add("hidden");
    scaffoldL3.classList.remove("hidden");
  });

  // Nivel 3 -> Revelar solo esta jaula (4, 1, 5 o similar según tablero)
  btnRevealCageSol.addEventListener("click", () => {
    const errorCandidates = document.querySelectorAll(".error-candidate");
    if (errorCandidates.length >= 3) {
      errorCandidates[0].textContent = "4";
      errorCandidates[1].textContent = "1";
      errorCandidates[2].textContent = "5";
      errorCandidates.forEach((el) => {
        el.style.color = "var(--ink-pen)";
        el.style.fontWeight = "bold";
      });
    }
    conflictCells.forEach((c) => c.classList.remove("conflict-cage-highlight"));
    btnRevealCageSol.textContent = "✓ Jaula resuelta con éxito";
    btnRevealCageSol.disabled = true;
  });

  // Prevención de spoilers: Revelar todo el tablero
  btnMartaRevealAll.addEventListener("click", () => {
    modalConfirmSpoiler.classList.remove("hidden");
  });

  btnCancelSpoiler.addEventListener("click", () => {
    modalConfirmSpoiler.classList.add("hidden");
  });

  btnConfirmSpoiler.addEventListener("click", () => {
    modalConfirmSpoiler.classList.add("hidden");
    // Pasar a la vista limpia de solución completa
    screenMarta.classList.remove("active");
    screenDiego.classList.add("active");
  });
});
