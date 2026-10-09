/* Visualizaciones D3 de las diapositivas.
 *
 * Cada lienzo [data-viz] se dibuja la primera vez que su diapositiva aparece y avanza por
 * pasos. El paso es cuántos fragmentos de la diapositiva están visibles, así que la
 * narración (la lista .pasos) y el dibujo no se desincronizan, tampoco al retroceder.
 *
 * Los datos vienen de datos/datos.js (window.DATOS), que escribe
 * labs/tb1-kenken/scripts/datos_diapos.py: ninguna cifra de los gráficos está a mano,
 * salvo las del conjunto sintético, copiadas de la Tabla de tableros sintéticos del informe.
 */
(() => {
  "use strict";
  const D = window.DATOS;
  const KK = (window.KK = {});
  const VIZ = {};
  const T = 650; // duración de las transiciones (ms)
  const SVGNS = "http://www.w3.org/2000/svg";

  // ---------------------------------------------------------------- utilidades

  const tip = document.createElement("div");
  tip.className = "tooltip-viz";
  document.body.appendChild(tip);
  const verTip = (ev, html) => {
    tip.innerHTML = html;
    tip.style.opacity = 1;
    tip.style.left = `${ev.clientX + 14}px`;
    tip.style.top = `${ev.clientY + 14}px`;
  };
  const ocultarTip = () => (tip.style.opacity = 0);

  function lienzo(el, w, h) {
    const svg = d3.select(el).append("svg")
      .attr("class", "viz")
      .attr("viewBox", `0 0 ${w} ${h}`)
      .attr("role", "img")
      .attr("aria-label", el.dataset.label || "");
    if (!el.classList.contains("solo")) svg.attr("preserveAspectRatio", "none");
    return svg;
  }

  // Miles con espacio fino, como en el informe (5 883).
  const miles = (v) => d3.format(",")(v).replace(/,/g, " ");
  const pct = (v, d = 0) => `${(100 * v).toFixed(d)}%`;

  // Dibuja un trazo de punta a punta (stroke-dashoffset).
  function trazar(sel, delay = 0, dur = T) {
    sel.each(function () {
      const L = this.getTotalLength ? this.getTotalLength() : 0;
      d3.select(this)
        .attr("stroke-dasharray", `${L} ${L}`)
        .attr("stroke-dashoffset", L)
        .transition().delay(typeof delay === "function" ? delay.apply(this, arguments) : delay)
        .duration(dur).ease(d3.easeCubicOut)
        .attr("stroke-dashoffset", 0)
        .on("end", function () { d3.select(this).attr("stroke-dasharray", null); });
    });
  }

  // Bordes de un tablero: finos dentro de una jaula, gruesos entre jaulas y en el marco.
  // Coordenadas en celdas: [columna, fila].
  function segmentos(n, jaulas) {
    const id = Array.from({ length: n }, () => Array(n).fill(-1));
    jaulas.forEach((j, k) => j.celdas.forEach(([r, c]) => (id[r][c] = k)));
    const finos = [], gruesos = [];
    for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) {
      if (c < n - 1) (id[r][c] !== id[r][c + 1] ? gruesos : finos).push([[c + 1, r], [c + 1, r + 1]]);
      if (r < n - 1) (id[r][c] !== id[r + 1][c] ? gruesos : finos).push([[c, r + 1], [c + 1, r + 1]]);
    }
    gruesos.push([[0, 0], [n, 0]], [[n, 0], [n, n]], [[n, n], [0, n]], [[0, n], [0, 0]]);
    return { id, finos, gruesos };
  }
  const ancla = (j) => j.celdas.reduce((a, b) => (b[0] < a[0] || (b[0] === a[0] && b[1] < a[1]) ? b : a));
  const mismaCelda = (a, b) => a[0] === b[0] && a[1] === b[1];

  // Homografía de 4 pares de puntos (DLT con eliminación gaussiana).
  function homografia(src, dst) {
    const A = [], b = [];
    src.forEach(([x, y], i) => {
      const [u, v] = dst[i];
      A.push([x, y, 1, 0, 0, 0, -u * x, -u * y]); b.push(u);
      A.push([0, 0, 0, x, y, 1, -v * x, -v * y]); b.push(v);
    });
    const n = 8;
    for (let i = 0; i < n; i++) {
      let p = i;
      for (let k = i + 1; k < n; k++) if (Math.abs(A[k][i]) > Math.abs(A[p][i])) p = k;
      [A[i], A[p]] = [A[p], A[i]]; [b[i], b[p]] = [b[p], b[i]];
      for (let k = i + 1; k < n; k++) {
        const f = A[k][i] / A[i][i];
        for (let j = i; j < n; j++) A[k][j] -= f * A[i][j];
        b[k] -= f * b[i];
      }
    }
    const h = Array(n).fill(0);
    for (let i = n - 1; i >= 0; i--) {
      let s = b[i];
      for (let j = i + 1; j < n; j++) s -= A[i][j] * h[j];
      h[i] = s / A[i][i];
    }
    return ([x, y]) => {
      const w = h[6] * x + h[7] * y + 1;
      return [(h[0] * x + h[1] * y + h[2]) / w, (h[3] * x + h[4] * y + h[5]) / w];
    };
  }

  // Intervalo de Wilson al 95% para una proporción.
  function wilson(k, n, z = 1.96) {
    const p = k / n, d = 1 + (z * z) / n;
    const c = (p + (z * z) / (2 * n)) / d;
    const m = (z * Math.sqrt((p * (1 - p)) / n + (z * z) / (4 * n * n))) / d;
    return [Math.max(0, c - m), Math.min(1, c + m)];
  }

  // ------------------------------------------------- título: el tablero reparado

  VIZ.titulo = (el) => {
    const F = D.foto, n = F.n, S = 600, m = 10, c = (S - 2 * m) / n;
    const svg = d3.select(el).append("svg").attr("class", "viz").attr("viewBox", `0 0 ${S} ${S}`)
      .attr("width", "100%").attr("height", "100%").attr("aria-hidden", "true");
    const g = svg.append("g").attr("transform", `translate(${m},${m})`);
    const { finos, gruesos } = segmentos(n, F.jaulas);
    const corr = F.correcciones;
    let hecho = false;
    return () => {
      if (hecho) return;
      hecho = true;
      g.selectAll(".fino").data(finos).join("line").attr("class", "fino")
        .attr("x1", (d) => d[0][0] * c).attr("y1", (d) => d[0][1] * c)
        .attr("x2", (d) => d[1][0] * c).attr("y2", (d) => d[1][1] * c)
        .style("stroke", "rgba(237,235,245,0.22)").attr("stroke-width", 1.5)
        .call(trazar, (d, i) => 150 + i * 12, 500);
      g.selectAll(".grueso").data(gruesos).join("line").attr("class", "grueso")
        .attr("x1", (d) => d[0][0] * c).attr("y1", (d) => d[0][1] * c)
        .attr("x2", (d) => d[1][0] * c).attr("y2", (d) => d[1][1] * c)
        .style("stroke", "#EDEBF5").attr("stroke-width", 4.5).attr("stroke-linecap", "square")
        .call(trazar, (d, i) => 300 + i * 18, 450);
      g.selectAll(".etq").data(F.jaulas).join("text").attr("class", "etq mono")
        .attr("x", (j) => ancla(j)[1] * c + 9).attr("y", (j) => ancla(j)[0] * c + 22)
        .attr("font-size", 16).attr("font-weight", 600)
        .style("fill", (j) => (corr.some((k) => mismaCelda(k.celda, ancla(j))) ? "#F2A65A" : "#B9B8CC"))
        .text((j) => corr.find((k) => mismaCelda(k.celda, ancla(j)))?.corregido ?? j.etiqueta)
        .attr("opacity", 0).transition().delay(1200).duration(500).attr("opacity", 1);
      const celdas = F.solucion.flatMap((fila, r) => fila.map((v, cc) => ({ r, c: cc, v })));
      g.selectAll(".dig").data(celdas).join("text").attr("class", "dig")
        .attr("x", (d) => d.c * c + c / 2).attr("y", (d) => d.r * c + c * 0.68)
        .attr("text-anchor", "middle").attr("font-size", c * 0.42)
        .style("font-family", "'Space Grotesk', sans-serif").attr("font-weight", 600)
        .style("fill", "#857FEE").text((d) => d.v)
        .attr("opacity", 0)
        .transition().delay((d) => 1700 + (d.r + d.c) * 70).duration(400).attr("opacity", 1);
    };
  };

  // ------------------------------------- 97% por etiqueta es ~70% por tablero

  VIZ.compuesto = (el) => {
    const W = 780, H = 420, M = { l: 58, r: 26, t: 18, b: 50 };
    const svg = lienzo(el, W, H);
    const x = d3.scaleLinear([0, 85], [M.l, W - M.r]);
    const y = d3.scaleLinear([0, 1], [H - M.b, M.t]);
    const p = 0.9709, pSudoku = 0.99;

    svg.append("g").attr("class", "grid").selectAll("line").data([0, 0.25, 0.5, 0.75, 1]).join("line")
      .attr("x1", M.l).attr("x2", W - M.r).attr("y1", y).attr("y2", y);
    svg.append("g").attr("class", "eje").selectAll("text").data([0, 0.25, 0.5, 0.75, 1]).join("text")
      .attr("x", M.l - 10).attr("y", (d) => y(d) + 4).attr("text-anchor", "end").text((d) => pct(d));
    svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
      .call(d3.axisBottom(x).tickValues([0, 10, 20, 30, 40, 50, 60, 70, 81]).tickSize(5).tickPadding(6))
      .call((g) => g.select(".domain").remove());
    svg.append("text").attr("class", "rotulo-eje").attr("x", W - M.r).attr("y", H - 8)
      .attr("text-anchor", "end").text("etiquetas (o celdas) por tablero →");
    svg.append("text").attr("class", "rotulo-eje").attr("x", M.l).attr("y", M.t - 4)
      .text("tablero leído entero");

    const ks = d3.range(0, 85.01, 0.5);
    const linea = (q) => d3.line().x(x).y((k) => y(q ** k))(ks);
    const curva = svg.append("path").attr("d", linea(p)).attr("fill", "none")
      .style("stroke", "var(--indigo)").attr("stroke-width", 2.5).attr("stroke-linecap", "round").attr("opacity", 0);
    const etqCurva = svg.append("text").attr("class", "anot halo").attr("x", x(44)).attr("y", y(p ** 44) - 12)
      .text("p = 0.9709 por etiqueta").attr("opacity", 0);
    const curvaS = svg.append("path").attr("d", linea(pSudoku)).attr("fill", "none")
      .style("stroke", "var(--neutro)").attr("stroke-width", 2.5).attr("opacity", 0);

    const por = d3.groups(D.tableros, (t) => t.n).sort((a, b) => a[0] - b[0]).map(([n, ts]) => {
      const bien = ts.filter((t) => t.lectura === "bien").length;
      return { n, k: d3.mean(ts, (t) => t.etiquetas), bien, total: ts.length, ic: wilson(bien, ts.length) };
    });
    const obs = svg.append("g").attr("opacity", 0);
    obs.selectAll("line").data(por).join("line")
      .attr("x1", (d) => x(d.k)).attr("x2", (d) => x(d.k))
      .attr("y1", (d) => y(d.ic[0])).attr("y2", (d) => y(d.ic[1]))
      .style("stroke", "var(--indigo)").attr("stroke-width", 2).attr("opacity", 0.35).attr("stroke-linecap", "round");
    obs.selectAll("circle").data(por).join("circle")
      .attr("cx", (d) => x(d.k)).attr("cy", (d) => y(d.bien / d.total)).attr("r", 7)
      .style("fill", "var(--indigo)").style("stroke", "var(--papel)").attr("stroke-width", 2.5)
      .on("mousemove", (ev, d) => verTip(ev, `${d.n}×${d.n}: ${d.bien}/${d.total} leídos enteros<br>~${d.k.toFixed(1)} etiquetas por tablero<br>IC 95%: ${pct(d.ic[0])}–${pct(d.ic[1])}`))
      .on("mouseleave", ocultarTip);
    obs.selectAll("text").data(por).join("text").attr("class", "anot fuerte halo")
      .attr("x", (d) => x(d.k) + 14).attr("y", (d) => y(d.bien / d.total) + 5)
      .text((d) => `${d.n}×${d.n} · ${d.bien}/${d.total}`);

    const sud = svg.append("g").attr("opacity", 0);
    sud.append("circle").attr("cx", x(81)).attr("cy", y(pSudoku ** 81)).attr("r", 7)
      .style("fill", "var(--neutro)").style("stroke", "var(--papel)").attr("stroke-width", 2.5);
    sud.append("text").attr("class", "anot halo").attr("x", x(81)).attr("y", y(pSudoku ** 81) - 16)
      .attr("text-anchor", "end").text(`Sudoku 9×9: 81 celdas → ${pct(pSudoku ** 81)}`);

    let curvaHecha = false;
    return (s) => {
      if (s >= 1 && !curvaHecha) {
        curvaHecha = true;
        curva.attr("opacity", 1).call(trazar, 0, 1100);
        etqCurva.transition().delay(800).duration(400).attr("opacity", 1);
      } else if (s < 1) {
        curvaHecha = false;
        curva.interrupt().attr("opacity", 0);
        etqCurva.interrupt().attr("opacity", 0);
      }
      obs.transition().duration(T).attr("opacity", s >= 2 ? 1 : 0);
      curvaS.transition().duration(T).attr("opacity", s >= 3 ? 1 : 0);
      sud.transition().duration(T).attr("opacity", s >= 3 ? 1 : 0);
    };
  };

  // ------------------------------------------------------------ arquitectura

  VIZ.arquitectura = (el) => {
    const W = 1180, H = 330;
    const svg = lienzo(el, W, H);
    const defs = svg.append("defs");
    [["flecha", "var(--suave)"], ["flecha-n", "var(--naranja)"], ["flecha-i", "var(--indigo)"]].forEach(([id, col]) =>
      defs.append("marker").attr("id", id).attr("viewBox", "0 0 10 10").attr("refX", 9).attr("refY", 5)
        .attr("markerWidth", 7).attr("markerHeight", 7).attr("orient", "auto-start-reverse")
        .append("path").attr("d", "M0,0 L10,5 L0,10 z").style("fill", col));

    const nodos = {
      app:  { x: 0,   y: 24, w: 150, h: 78, t: "App móvil", s: "foto → JSON", paso: 1 },
      nodo: { x: 220, y: 24, w: 200, h: 78, t: "Nodo FastAPI", s: "POST /resolver · :8723", paso: 1 },
      f1:   { x: 490, y: 24, w: 190, h: 78, t: "Fase 1 · Visión", s: "sin aprendizaje", paso: 2 },
      inst: { x: 750, y: 24, w: 150, h: 78, t: "Instancia", s: "el contrato", paso: 3, clave: true },
      f2:   { x: 970, y: 24, w: 210, h: 78, t: "Fase 2 · CP-SAT", s: "resuelve y cuenta ≤ 2", paso: 4 },
      sol:  { x: 970, y: 186, w: 210, h: 70, t: "1 → solución", s: "se devuelve", paso: 5, acento: "var(--indigo)" },
      rep:  { x: 690, y: 186, w: 200, h: 70, t: "0 → reparación", s: "reificada · ¿única?", paso: 5, acento: "var(--naranja)" },
      rech: { x: 410, y: 186, w: 200, h: 70, t: "≥ 2 → rechazo", s: "mensaje en llano", paso: 5, acento: "var(--neutro)" },
    };
    const der = (k) => [nodos[k].x + nodos[k].w, nodos[k].y + nodos[k].h / 2];
    const izq = (k) => [nodos[k].x, nodos[k].y + nodos[k].h / 2];
    const abajo = (k, f = 0.5) => [nodos[k].x + nodos[k].w * f, nodos[k].y + nodos[k].h];
    const arriba = (k, f = 0.5) => [nodos[k].x + nodos[k].w * f, nodos[k].y];
    const curva = (a, b) => `M${a[0]},${a[1]} C${a[0]},${(a[1] + b[1]) / 2} ${b[0]},${(a[1] + b[1]) / 2} ${b[0]},${b[1]}`;
    const recta = (a, b) => `M${a[0]},${a[1]} L${b[0] - 2},${b[1]}`;

    const aristas = [
      { d: recta(der("app"), izq("nodo")), paso: 1, rot: "adb reverse · USB o Wi-Fi", rx: 185, ry: 14 },
      { d: recta(der("nodo"), izq("f1")), paso: 2 },
      { d: recta(der("f1"), izq("inst")), paso: 3 },
      { d: recta(der("inst"), izq("f2")), paso: 4 },
      { d: curva(abajo("f2", 0.6), arriba("sol", 0.6)), paso: 5 },
      { d: curva(abajo("f2", 0.3), arriba("rep", 0.5)), paso: 5 },
      { d: curva(abajo("f2", 0.12), arriba("rech", 0.5)), paso: 5 },
      { d: recta(der("rep"), izq("sol")), paso: 6, rep: true, rot: "única", rx: 930, ry: 210 },
      { d: recta(izq("rep"), der("rech")), paso: 6, rep: true, rot: "ambigua", rx: 650, ry: 210 },
      { d: `M${abajo("sol")[0]},${abajo("sol")[1]} V${H - 22} H${abajo("app")[0]} V${abajo("app")[1] + 2}`, paso: 7, vuelta: true,
        rot: "respuesta: estado · solución · correcciones · dónde cae cada celda en la foto", rx: 560, ry: H - 30 },
    ];

    const gA = svg.append("g");
    const rutas = gA.selectAll("path").data(aristas).join("path")
      .attr("d", (d) => d.d).attr("fill", "none")
      .style("stroke", (d) => (d.rep ? "var(--naranja)" : d.vuelta ? "var(--indigo)" : "var(--suave)"))
      .attr("stroke-width", (d) => (d.vuelta ? 2.2 : 1.8))
      .attr("stroke-dasharray", (d) => (d.rep ? "7 5" : null))
      .attr("marker-end", (d) => `url(#${d.rep ? "flecha-n" : d.vuelta ? "flecha-i" : "flecha"})`)
      .attr("opacity", 0);
    const rotulos = gA.selectAll("text").data(aristas.filter((a) => a.rot)).join("text")
      .attr("class", "anot mono halo").attr("font-size", 13)
      .attr("x", (d) => d.rx).attr("y", (d) => d.ry).attr("text-anchor", "middle")
      .text((d) => d.rot).attr("opacity", 0);

    const gN = svg.append("g").selectAll("g").data(Object.entries(nodos)).join("g")
      .attr("transform", ([, d]) => `translate(${d.x},${d.y})`).attr("opacity", 0.22);
    gN.append("rect").attr("width", ([, d]) => d.w).attr("height", ([, d]) => d.h).attr("rx", 12)
      .style("fill", ([, d]) => (d.clave ? "var(--indigo)" : "var(--tarjeta)"))
      .style("stroke", ([, d]) => (d.clave ? "var(--indigo)" : "var(--borde)"))
      .attr("stroke-dasharray", ([k]) => (k === "rep" ? "6 4" : null))
      .attr("stroke-width", 1.2);
    gN.filter(([, d]) => d.acento).append("rect").attr("width", ([, d]) => d.w).attr("height", 6).attr("rx", 3)
      .style("fill", ([, d]) => d.acento);
    gN.append("text").attr("x", 16).attr("y", ([, d]) => d.h / 2 - 3)
      .style("font-family", "'Space Grotesk', sans-serif").attr("font-weight", 600).attr("font-size", 19)
      .style("fill", ([, d]) => (d.clave ? "#fff" : "var(--tinta)")).text(([, d]) => d.t);
    gN.append("text").attr("class", "mono").attr("x", 16).attr("y", ([, d]) => d.h / 2 + 19).attr("font-size", 13)
      .style("fill", ([, d]) => (d.clave ? "rgba(255,255,255,0.8)" : "var(--nota)")).text(([, d]) => d.s);

    const ficha = svg.append("circle").attr("r", 7).style("fill", "var(--naranja)")
      .style("stroke", "var(--papel)").attr("stroke-width", 2.5).attr("opacity", 0);

    function viajar(nodosRuta) {
      const ultimo = nodosRuta[nodosRuta.length - 1];
      if (!ultimo) return ficha.attr("opacity", 0);
      const L = ultimo.getTotalLength();
      ficha.interrupt().attr("opacity", 1)
        .transition().duration(Math.min(1400, 500 + L * 1.3)).ease(d3.easeCubicInOut)
        .attrTween("transform", () => (t) => {
          const pt = ultimo.getPointAtLength(t * L);
          return `translate(${pt.x},${pt.y})`;
        })
        .transition().duration(300).attr("opacity", 0);
    }

    let anterior = 0;
    return (s) => {
      gN.transition().duration(T).attr("opacity", ([, d]) => (s >= d.paso ? 1 : 0.22));
      rutas.each(function (d) {
        const sel = d3.select(this);
        const on = s >= d.paso;
        if (on && sel.attr("opacity") === "0") {
          sel.attr("opacity", 1);
          if (!d.rep) sel.call(trazar, 0, 700);
        } else if (!on) sel.interrupt().attr("opacity", 0).attr("stroke-dasharray", d.rep ? "7 5" : null);
      });
      rotulos.transition().duration(T).attr("opacity", (d) => (s >= d.paso ? 1 : 0));
      if (s > anterior) viajar(rutas.filter((d) => d.paso === s && !d.rep).nodes());
      anterior = s;
    };
  };

  // ------------------------------------------------- Fase 1: foto → rectificada

  VIZ["fase1-foto"] = (el) => {
    const [izqEl, derEl] = el.querySelectorAll(".lienzo");
    const F = D.foto, PW = 900, PH = 1200;
    const svgI = lienzo(izqEl, PW, PH);
    const svgD = lienzo(derEl, 900, 900);
    const capaBin = izqEl.querySelector(".capa");
    const capaWarp = derEl.querySelector(".capa");
    const q = F.foto.esquinas.map(([u, v]) => [u * PW, v * PH]);
    const poli = svgI.append("polygon").attr("points", q.map((p) => p.join(",")).join(" "))
      .style("fill", "var(--indigo)").attr("fill-opacity", 0.08)
      .style("stroke", "var(--indigo)").attr("stroke-width", 9).attr("stroke-linejoin", "round").attr("opacity", 0);
    const esq = svgI.selectAll("circle").data(q).join("circle").attr("cx", (d) => d[0]).attr("cy", (d) => d[1])
      .attr("r", 20).style("fill", "var(--naranja)").style("stroke", "var(--papel)").attr("stroke-width", 6).attr("opacity", 0);

    const marco = svgD.append("g");
    marco.append("rect").attr("x", 2).attr("y", 2).attr("width", 896).attr("height", 896).attr("rx", 8)
      .style("fill", "none").style("stroke", "var(--borde)").attr("stroke-width", 3);
    marco.append("text").attr("class", "mono").attr("x", 450).attr("y", 460).attr("text-anchor", "middle")
      .attr("font-size", 38).style("fill", "var(--nota)").text("900 × 900");
    const lineas = svgD.append("g").attr("opacity", 0);
    lineas.selectAll(".v").data(F.xs).join("line").attr("class", "v")
      .attr("x1", (d) => d).attr("x2", (d) => d).attr("y1", 0).attr("y2", 900);
    lineas.selectAll(".h").data(F.ys).join("line").attr("class", "h")
      .attr("y1", (d) => d).attr("y2", (d) => d).attr("x1", 0).attr("x2", 900);
    lineas.selectAll("line").style("stroke", "var(--indigo)").attr("stroke-width", 6).attr("stroke-opacity", 0.75);
    const chip = svgD.append("g").attr("opacity", 0).attr("transform", "translate(640,820)");
    chip.append("rect").attr("width", 230).attr("height", 62).attr("rx", 31).style("fill", "var(--indigo)");
    chip.append("text").attr("x", 115).attr("y", 43).attr("text-anchor", "middle").attr("font-size", 36)
      .attr("font-weight", 600).style("fill", "#fff").attr("class", "mono").text(`n = ${F.n}`);

    let lineasHechas = false;
    return (s) => {
      capaBin.classList.toggle("visible", s >= 1 && s < 3);
      poli.transition().duration(T).attr("opacity", s >= 2 ? 1 : 0);
      esq.transition().delay((d, i) => (s >= 2 ? i * 120 : 0)).duration(400).attr("opacity", s >= 2 ? 1 : 0);
      capaWarp.classList.toggle("visible", s >= 3);
      marco.transition().duration(T).attr("opacity", s >= 3 ? 0 : 1);
      if (s >= 4 && !lineasHechas) {
        lineasHechas = true;
        lineas.attr("opacity", 1).selectAll("line").call(trazar, (d, i) => i * 60, 600);
      } else if (s < 4) { lineasHechas = false; lineas.attr("opacity", 0); }
      chip.transition().delay(s >= 4 ? 800 : 0).duration(400).attr("opacity", s >= 4 ? 1 : 0);
    };
  };

  // ------------------------------------- Fase 1: el tamaño por periodicidad

  VIZ["fase1-n"] = (el) => {
    const F = D.foto, LADO = F.lado, perfil = F.perfil.x, minimo = F.minimo_linea;
    const W = 780, H = 440, M = { l: 52, r: 18, t: 22, b: 120 };
    const svg = lienzo(el, W, H);
    const x = d3.scaleLinear([0, LADO], [M.l, W - M.r]);
    const y = d3.scaleLinear([0, 1], [H - M.b, M.t]);

    svg.append("g").attr("class", "grid").selectAll("line").data([0, 0.5, 1]).join("line")
      .attr("x1", M.l).attr("x2", W - M.r).attr("y1", y).attr("y2", y);
    svg.append("g").attr("class", "eje").selectAll("text").data([0, 0.5, 1]).join("text")
      .attr("x", M.l - 8).attr("y", (d) => y(d) + 4).attr("text-anchor", "end").text((d) => pct(d));
    svg.append("text").attr("class", "rotulo-eje").attr("x", M.l).attr("y", H - M.b + 20)
      .text("columna del tablero rectificado (px) →");
    svg.append("text").attr("class", "rotulo-eje").attr("x", M.l).attr("y", M.t - 8)
      .text("tinta de trazos verticales largos, por columna");

    const ventanas = svg.append("g");
    const area = d3.area().x((d, i) => x(i)).y0(y(0)).y1((d) => y(d)).curve(d3.curveStep);
    svg.append("path").datum(perfil).attr("d", area).style("fill", "var(--suave)").attr("fill-opacity", 0.18);
    svg.append("path").datum(perfil).attr("d", d3.line().x((d, i) => x(i)).y((d) => y(d)).curve(d3.curveStep))
      .attr("fill", "none").style("stroke", "var(--suave)").attr("stroke-width", 1.3);
    svg.append("line").attr("x1", M.l).attr("x2", W - M.r).attr("y1", y(minimo)).attr("y2", y(minimo))
      .style("stroke", "var(--naranja)").attr("stroke-width", 1.2);
    svg.append("text").attr("class", "anot mono halo").attr("font-size", 12).attr("x", W - M.r)
      .attr("y", y(minimo) - 6).attr("text-anchor", "end").text(`mínimo de una línea real: ${pct(minimo)}`);
    const marcas = svg.append("g");
    const leyendaN = svg.append("text").attr("class", "anot fuerte").attr("x", M.l).attr("y", H - M.b + 48).attr("opacity", 0);

    // Fila de candidatos: se pueden tocar.
    const puntajes = new Map(F.puntajes.map((p) => [p.n, Math.min(p.x, p.y)]));
    const ns = [...puntajes.keys()];
    const fila = svg.append("g").attr("transform", `translate(${M.l},${H - 52})`);
    const chipW = (W - M.l - M.r) / ns.length;
    const chips = fila.selectAll("g").data(ns).join("g")
      .attr("transform", (n, i) => `translate(${i * chipW},0)`).style("cursor", "pointer");
    chips.append("rect").attr("x", 3).attr("width", chipW - 6).attr("height", 40).attr("rx", 20)
      .style("fill", "var(--tarjeta)").style("stroke", "var(--borde)");
    chips.append("text").attr("class", "mono").attr("x", chipW / 2).attr("y", 26).attr("text-anchor", "middle")
      .attr("font-size", 15).attr("font-weight", 600).text((n) => `n=${n}`);
    const marcaChip = chips.append("text").attr("class", "mono").attr("x", chipW / 2).attr("y", 58)
      .attr("text-anchor", "middle").attr("font-size", 13).attr("opacity", 0)
      .style("fill", "var(--nota)")
      .text((n) => (puntajes.get(n) >= minimo ? (n === F.n ? "✓ elegido" : "✓") : "✕"));

    function mostrar(n, conVeredicto) {
      chips.select("rect").transition().duration(250)
        .style("fill", (k) => (k === n ? "var(--indigo)" : "var(--tarjeta)"))
        .style("stroke", (k) => (k === n ? "var(--indigo)" : "var(--borde)"));
      chips.select("text").style("fill", (k) => (k === n ? "#fff" : "var(--tinta)"));
      marcaChip.transition().duration(300).attr("opacity", conVeredicto ? 1 : 0);
      if (!n) {
        ventanas.selectAll("rect").remove(); marcas.selectAll("*").remove(); leyendaN.attr("opacity", 0);
        return;
      }
      const paso = LADO / n, half = Math.max(3, Math.floor(0.28 * paso));
      const datos = d3.range(n + 1).map((i) => {
        const centro = Math.round(i * paso), a = Math.max(0, centro - half), b = Math.min(LADO, centro + half + 1);
        let max = 0, arg = centro;
        for (let k = a; k < b; k++) if (perfil[k] > max) { max = perfil[k]; arg = k; }
        return { i, a, b, max, arg, ok: max >= minimo };
      });
      ventanas.selectAll("rect").data(datos, (d) => d.i).join(
        (en) => en.append("rect").attr("y", M.t).attr("height", y(0) - M.t).attr("opacity", 0),
        (up) => up, (ex) => ex.transition().duration(200).attr("opacity", 0).remove())
        .transition().duration(350)
        .attr("x", (d) => x(d.a)).attr("width", (d) => Math.max(2, x(d.b) - x(d.a)))
        .style("fill", (d) => (d.ok ? "var(--indigo-palido)" : "var(--naranja-palido)")).attr("opacity", 0.9);
      ventanas.lower();
      marcas.selectAll("*").remove();
      marcas.selectAll("circle").data(datos).join("circle")
        .attr("cx", (d) => x(d.arg)).attr("cy", (d) => y(d.max)).attr("r", 5.5)
        .style("fill", (d) => (d.ok ? "var(--indigo)" : "var(--naranja)"))
        .style("stroke", "var(--papel)").attr("stroke-width", 2);
      marcas.selectAll("text").data(datos.filter((d) => !d.ok)).join("text")
        .attr("x", (d) => x((d.a + d.b) / 2)).attr("y", y(0) - 10).attr("text-anchor", "middle")
        .attr("font-size", 18).attr("font-weight", 700).style("fill", "var(--naranja-texto)").text("✕");
      const peor = d3.least(datos, (d) => d.max);
      leyendaN.attr("opacity", 1)
        .text(`n = ${n}: ${n + 1} líneas predichas · la más débil tiene ${pct(peor.max)} de tinta → ${peor.ok ? "todas existen" : "falta una línea"}`);
    }
    chips.on("click", (ev, n) => mostrar(n, true));
    const guion = [null, 4, 6, 3, F.n];
    return (s) => mostrar(guion[Math.min(s, guion.length - 1)], s >= 3);
  };

  // ------------------------------------------ Fase 1: jaulas por grosor de arista

  VIZ["fase1-jaulas"] = (el) => {
    const F = D.foto, xs = F.xs, ys = F.ys, n = F.n;
    const svg = lienzo(el, 900, 900);
    const celdas = svg.append("g").attr("opacity", 0);
    const { id } = segmentos(n, F.jaulas);
    celdas.selectAll("rect").data(d3.cross(d3.range(n), d3.range(n))).join("rect")
      .attr("x", ([r, c]) => xs[c]).attr("y", ([r, c]) => ys[r])
      .attr("width", ([r, c]) => xs[c + 1] - xs[c]).attr("height", ([r, c]) => ys[r + 1] - ys[r])
      .style("fill", "var(--indigo-palido)").attr("fill-opacity", 0.7);
    const seg = (a) => {
      const [[r, c], [r2]] = [a.a, a.b];
      const pad = 10;
      return r === r2
        ? { x1: xs[c + 1], x2: xs[c + 1], y1: ys[r] + pad, y2: ys[r + 1] - pad }
        : { x1: xs[c] + pad, x2: xs[c + 1] - pad, y1: ys[r + 1], y2: ys[r + 1] };
    };
    const lineas = svg.append("g").selectAll("line").data(F.aristas).join("line")
      .each(function (a) { const s = seg(a); d3.select(this).attr("x1", s.x1).attr("x2", s.x2).attr("y1", s.y1).attr("y2", s.y2); })
      .attr("stroke-linecap", "round").attr("opacity", 0);
    let paso = 0;
    const estilo = (sel) => sel
      .style("stroke", (a) => (paso >= 2 ? (a.gruesa ? "var(--indigo)" : "var(--neutro)") : "var(--suave)"))
      .attr("stroke-width", (a) => (paso >= 2 ? (a.gruesa ? 14 : 7) : 9));
    KK.resaltarAristas = (pred) => {
      lineas.transition().duration(150)
        .attr("opacity", (a) => (paso < 1 ? 0 : !pred || pred(a) ? 1 : 0.12));
    };
    return (s) => {
      paso = s;
      lineas.transition().delay((a, i) => (s >= 1 ? i * 8 : 0)).duration(400).attr("opacity", s >= 1 ? 1 : 0).call(estilo);
      celdas.transition().duration(T).attr("opacity", s >= 3 ? 1 : 0);
    };
  };

  VIZ["fase1-grosor"] = (el) => {
    const F = D.foto;
    const W = 700, H = 270, M = { l: 40, r: 20, t: 62, b: 44 };
    const svg = lienzo(el, W, H);
    const x = d3.scaleLinear([3, 14], [M.l, W - M.r]);
    const cuenta = d3.rollups(F.aristas, (v) => v.length, (a) => a.grosor).map(([g, k]) => ({ g, k }));
    const y = d3.scaleLinear([0, d3.max(cuenta, (d) => d.k)], [H - M.b, M.t]);
    svg.append("g").attr("class", "eje").attr("transform", `translate(0,${H - M.b})`)
      .call(d3.axisBottom(x).ticks(11).tickSize(4).tickFormat((v) => `${v}`))
      .call((g) => g.select(".domain").style("stroke", "#C3C2B7"));
    svg.append("text").attr("class", "rotulo-eje").attr("x", W - M.r).attr("y", H - 6).attr("text-anchor", "end")
      .text("grosor de la arista (px) →");
    const bw = 22;
    const barras = svg.append("g").selectAll("path").data(cuenta).join("path")
      .attr("d", (d) => {
        const x0 = x(d.g) - bw / 2, y0 = y(0), y1 = y(d.k), r = Math.min(4, y0 - y1);
        return `M${x0},${y0} V${y1 + r} Q${x0},${y1} ${x0 + r},${y1} H${x0 + bw - r} Q${x0 + bw},${y1} ${x0 + bw},${y1 + r} V${y0} Z`;
      })
      .style("fill", "var(--suave)").attr("opacity", 0).style("cursor", "pointer")
      .on("mousemove", (ev, d) => { verTip(ev, `${d.k} aristas de ${d.g} px`); KK.resaltarAristas?.((a) => a.grosor === d.g); })
      .on("mouseleave", () => { ocultarTip(); KK.resaltarAristas?.(null); });
    const valores = svg.append("g").selectAll("text").data(cuenta).join("text").attr("class", "anot mono")
      .attr("font-size", 13).attr("x", (d) => x(d.g)).attr("y", (d) => y(d.k) - 7).attr("text-anchor", "middle")
      .text((d) => d.k).attr("opacity", 0);
    const corte = svg.append("g").attr("opacity", 0);
    corte.append("line").attr("x1", x(F.umbral)).attr("x2", x(F.umbral)).attr("y1", M.t - 10).attr("y2", H - M.b)
      .style("stroke", "var(--naranja)").attr("stroke-width", 2);
    corte.append("text").attr("class", "anot fuerte halo").attr("x", x(F.umbral) + 8).attr("y", M.t + 4)
      .text(`Otsu: ${F.umbral} px`);
    corte.append("line").attr("x1", x(F.marco)).attr("x2", x(F.marco)).attr("y1", H - M.b - 8).attr("y2", H - M.b)
      .style("stroke", "var(--suave)").attr("stroke-width", 2);
    corte.append("text").attr("class", "anot mono").attr("font-size", 12).attr("x", x(F.marco) - 4)
      .attr("y", H - M.b - 12).attr("text-anchor", "end").text(`marco ${F.marco}`);
    const finas = F.aristas.filter((a) => !a.gruesa).length, gruesas = F.aristas.length - finas;
    const rot = svg.append("g").attr("opacity", 0);
    rot.append("text").attr("class", "anot").attr("x", x(5.5)).attr("y", 18).attr("text-anchor", "middle").text(`${finas} finas: dentro de una jaula`);
    rot.append("text").attr("class", "anot").attr("x", x(11.5)).attr("y", 18).attr("text-anchor", "middle")
      .text(`${gruesas} gruesas: bordes de jaula`);
    return (s) => {
      barras.transition().duration(T).attr("opacity", s >= 1 ? 1 : 0)
        .style("fill", (d) => (s >= 2 ? (d.g > F.umbral ? "var(--indigo)" : "var(--neutro)") : "var(--suave)"));
      valores.transition().duration(T).attr("opacity", s >= 1 ? 1 : 0);
      corte.transition().duration(T).attr("opacity", s >= 2 ? 1 : 0);
      rot.transition().duration(T).attr("opacity", s >= 2 ? 1 : 0);
    };
  };

  // --------------------------------------------------- Fase 1: los recortes

  VIZ.recortes = (el) => (s) => el.classList.toggle("marcar", s >= 1);

  // ---------------------------------------------- la reparación sobre la foto

  VIZ["reparar-foto"] = (el) => {
    const F = D.foto, n = F.n, PW = 900, PH = 1200;
    const svg = lienzo(el, PW, PH);
    const q = F.foto.esquinas.map(([u, v]) => [u * PW, v * PH]);
    const H = homografia([[0, 0], [F.lado, 0], [F.lado, F.lado], [0, F.lado]], q);
    const P = (c, r) => H([F.xs[c], F.ys[r]]); // esquina de la rejilla en la foto
    const { finos, gruesos } = segmentos(n, F.jaulas);
    const linea = (d) => { const a = P(...d[0]), b = P(...d[1]); return `M${a[0]},${a[1]} L${b[0]},${b[1]}`; };
    const quad = (r, c) => [P(c, r), P(c + 1, r), P(c + 1, r + 1), P(c, r + 1)].map((p) => p.join(",")).join(" ");

    const malas = F.jaulas.filter((j) => F.correcciones.some((k) => mismaCelda(k.celda, ancla(j))));
    const gMal = svg.append("g").attr("opacity", 0);
    const celdasMal = gMal.selectAll("polygon").data(malas.flatMap((j) => j.celdas)).join("polygon")
      .attr("points", ([r, c]) => quad(r, c)).style("fill", "var(--naranja)").attr("fill-opacity", 0.32);

    const gRej = svg.append("g").attr("opacity", 0);
    gRej.selectAll(".f").data(finos).join("path").attr("class", "f").attr("d", linea)
      .style("stroke", "var(--indigo)").attr("stroke-width", 2.5).attr("stroke-opacity", 0.55);
    gRej.selectAll(".g").data(gruesos).join("path").attr("class", "g").attr("d", linea)
      .style("stroke", "var(--indigo)").attr("stroke-width", 7).attr("stroke-linecap", "round");

    const chips = svg.append("g").selectAll("g").data(malas).join("g").attr("opacity", 0)
      .attr("transform", (j) => { const [r, c] = ancla(j); const p = P(c, r); return `translate(${p[0] + 5},${p[1] + 6})`; });
    chips.append("rect").attr("width", 104).attr("height", 50).attr("rx", 25);
    chips.append("text").attr("class", "mono").attr("x", 52).attr("y", 35).attr("text-anchor", "middle")
      .attr("font-size", 29).attr("font-weight", 700).style("fill", "#fff");
    const pintarChips = (corregido) => {
      chips.select("rect").transition().duration(400).style("fill", corregido ? "var(--indigo)" : "var(--naranja)");
      chips.select("text").text((j) => (corregido ? F.correcciones.find((k) => mismaCelda(k.celda, ancla(j))).corregido : j.etiqueta));
    };

    const velo = svg.append("g").attr("opacity", 0);
    velo.append("polygon").attr("points", q.map((p) => p.join(",")).join(" ")).style("fill", "var(--papel)").attr("fill-opacity", 0.86);
    const cx = d3.mean(q, (p) => p[0]), cy = d3.mean(q, (p) => p[1]);
    velo.append("text").attr("x", cx).attr("y", cy).attr("text-anchor", "middle").attr("font-size", 120)
      .style("font-family", "'Space Grotesk', sans-serif").attr("font-weight", 700).style("fill", "var(--naranja-texto)").text("0");
    velo.append("text").attr("x", cx).attr("y", cy + 62).attr("text-anchor", "middle").attr("font-size", 40)
      .attr("font-weight", 600).text("soluciones");
    velo.append("text").attr("class", "mono").attr("x", cx).attr("y", cy + 112).attr("text-anchor", "middle").attr("font-size", 28)
      .style("fill", "var(--nota)").text(`CP-SAT lo demuestra en ${F.ms_resolver} ms`);

    const centros = F.foto.en_foto;
    const dig = svg.append("g").selectAll("text").data(F.solucion.flatMap((f, r) => f.map((v, c) => ({ v, r, c })))).join("text")
      .attr("x", (d) => centros[d.r][d.c][0] * PW).attr("y", (d) => centros[d.r][d.c][1] * PH + 22)
      .attr("text-anchor", "middle").attr("font-size", 64).attr("class", "halo")
      .style("font-family", "'Space Grotesk', sans-serif").attr("font-weight", 700)
      .style("fill", "var(--indigo)").style("stroke-width", "10px").text((d) => d.v).attr("opacity", 0);
    const pie = svg.append("text").attr("class", "mono halo").attr("x", PW / 2).attr("y", PH - 120)
      .attr("text-anchor", "middle").attr("font-size", 30).style("fill", "var(--suave)")
      .text(`reparar y resolver: ${F.ms_reparar} ms`).attr("opacity", 0);

    let rejHecha = false;
    return (s) => {
      if (s >= 1 && !rejHecha) {
        rejHecha = true;
        gRej.attr("opacity", 1).selectAll("path").call(trazar, (d, i) => i * 10, 500);
      } else if (s < 1) { rejHecha = false; gRej.attr("opacity", 0); }
      gRej.transition().duration(T).attr("opacity", s >= 1 ? (s >= 5 ? 0.35 : 1) : 0);
      gMal.transition().duration(T).attr("opacity", s >= 2 ? (s >= 5 ? 0.6 : 1) : 0);
      celdasMal.transition().duration(T).style("fill", s >= 4 ? "var(--indigo)" : "var(--naranja)");
      chips.transition().duration(T).attr("opacity", s >= 2 && s < 5 ? 1 : 0);
      pintarChips(s >= 4);
      velo.transition().duration(T).attr("opacity", s === 3 ? 1 : 0);
      dig.transition().delay((d) => (s >= 5 ? (d.r * 6 + d.c) * 35 : 0)).duration(350).attr("opacity", s >= 5 ? 1 : 0);
      pie.transition().delay(s >= 5 ? 1200 : 0).duration(400).attr("opacity", s >= 5 ? 1 : 0);
    };
  };

  VIZ.candidatas = (el) => {
    const F = D.foto;
    const malas = F.jaulas.filter((j) => F.correcciones.some((k) => mismaCelda(k.celda, ancla(j))));
    el.innerHTML = malas.map((j) => {
      const [r, c] = ancla(j);
      const elegida = F.correcciones.find((k) => mismaCelda(k.celda, [r, c])).corregido;
      return `<div class="fila"><span class="donde">jaula (${r + 1},${c + 1})</span>` +
        j.candidatas.map((k) => `<span class="cand ${k.peso === 0 ? "leido" : ""}" data-el="${k.etiqueta === elegida}">` +
          `${k.etiqueta}<small>${k.peso === 0 ? "leído" : `peso ${k.peso}`}</small></span>`).join("") + "</div>";
    }).join("") + `<div class="pie">Mínimo de cambios y, a igual número, la más plausible. Ninguna otra corrección con un cambio más da otro tablero.</div>`;
    let t;
    return (s) => {
      el.classList.toggle("visible", s >= 4);
      clearTimeout(t);
      el.querySelectorAll(".cand").forEach((c) => c.classList.remove("elegida"));
      if (s >= 4) t = setTimeout(() => el.querySelectorAll('.cand[data-el="true"]').forEach((c) => c.classList.add("elegida")), 700);
    };
  };

  // --------------------------------------------- el waffle de 895 etiquetas

  VIZ.waffle = (el) => {
    const E = D.etiquetas, W = 1180, H = 380, cols = 28, paso = 14.5, lado = 12;
    const svg = lienzo(el, W, H);
    const esCinco = (par) => { const [v, l] = par.split(" → "); return v.replace("5", "6") === l; };
    const bloques = [
      ["desarrollo", "Desarrollo · 6H, 9H", 0],
      ["no_usados", "No usados · 4E, 4H, 6E", 620],
    ];
    bloques.forEach(([clave, nombre, x0]) => {
      const g = E[clave], fallos = [];
      Object.entries(g.fallos).forEach(([par, k]) => d3.range(k).forEach(() => fallos.push({ par, tipo: esCinco(par) ? "cinco" : "otro" })));
      fallos.sort((a, b) => d3.ascending(a.tipo === "cinco", b.tipo === "cinco"));
      const items = d3.range(g.bien).map(() => ({ tipo: "bien" })).concat(fallos);
      const gb = svg.append("g").attr("transform", `translate(${x0},0)`);
      gb.append("text").attr("x", 0).attr("y", 22).style("font-family", "'Space Grotesk', sans-serif")
        .attr("font-weight", 600).attr("font-size", 22).text(nombre);
      const k = d3.sum(fallos, () => 1);
      gb.append("text").attr("class", "mono").attr("x", 0).attr("y", 46).attr("font-size", 15).style("fill", "var(--suave)")
        .text(`${g.n} etiquetas · ${pct(g.bien / g.n, 2)} · ${k} fallos`);
      gb.append("g").attr("transform", "translate(0,62)").selectAll("rect").data(items).join("rect")
        .attr("class", (d) => `w-${d.tipo}`)
        .attr("x", (d, i) => (i % cols) * paso).attr("y", (d, i) => Math.floor(i / cols) * paso)
        .attr("width", lado).attr("height", lado).attr("rx", 2.5).style("fill", "var(--borde)")
        .on("mousemove", (ev, d) => d.par && verTip(ev, d.par))
        .on("mouseleave", ocultarTip);
      if (clave === "no_usados") {
        const cinco = fallos.filter((f) => f.par === "5+ → 6+").length;
        gb.append("text").attr("class", "anot fuerte nota-cinco").attr("x", cols * paso - 3)
          .attr("y", 62 + (Math.floor((items.length - 1) / cols) + 1) * paso + 20).attr("text-anchor", "end")
          .text(`${cinco} de sus ${k} fallos: 5+ leído como 6+ ↑`).attr("opacity", 0);
      }
    });
    return (s) => {
      svg.selectAll(".w-otro, .w-cinco").transition().delay((d, i) => (s >= 1 ? i * 25 : 0)).duration(400)
        .style("fill", (d) => (s >= 2 && d.tipo === "cinco" ? "var(--naranja)" : s >= 1 ? "var(--suave)" : "var(--borde)"));
      svg.selectAll(".nota-cinco").transition().duration(T).attr("opacity", s >= 2 ? 1 : 0);
    };
  };

  // ------------------------------------------------ de punta a punta: 70 tableros

  VIZ.e2e = (el) => {
    const W = 790, H = 330, r = 8, p = 20;
    const svg = lienzo(el, W, H);
    const orden = { bien: 0, sin_solucion: 1, rechazado: 2 };
    const ts = D.tableros.map((t) => ({ ...t })).sort((a, b) =>
      d3.ascending(a.n, b.n) || d3.ascending(orden[a.lectura], orden[b.lectura]) || d3.ascending(a.reparacion ?? "", b.reparacion ?? "") || d3.ascending(a.id, b.id));

    // Disposición por tamaño de tablero.
    const filasN = { 4: 70, 6: 150, 9: 208 };
    const porN = d3.group(ts, (t) => t.n);
    porN.forEach((lista, n) => lista.forEach((t, i) => {
      t.pn = { x: 100 + (i % 24) * p, y: filasN[n] + Math.floor(i / 24) * p };
    }));
    const rotN = svg.append("g");
    rotN.selectAll("text").data([...porN]).join("text").attr("class", "anot mono")
      .attr("x", 0).attr("y", ([n]) => filasN[n] + 5).text(([n, l]) => `${n}×${n} · ${l.length}`);

    // Disposición por bloques: cada estado es una lista de bloques [clave, título, columnas, filtro].
    const grupo = (t) => (t.lectura === "sin_solucion" ? (t.reparacion === "bien" ? "reparado" : "abstiene") : t.lectura);
    const estados = {
      3: [["bien", "bien leídos", 8, (t) => t.lectura === "bien"],
          ["sin", "sin solución", 5, (t) => t.lectura === "sin_solucion"],
          ["rech", "rechazados", 3, (t) => t.lectura === "rechazado"]],
      4: [["bien", "bien leídos", 8, (t) => t.lectura === "bien"],
          ["rep", "reparados", 4, (t) => grupo(t) === "reparado"],
          ["abs", "se abstiene", 3, (t) => grupo(t) === "abstiene"],
          ["rech", "rechazados", 3, (t) => t.lectura === "rechazado"]],
      5: [["ok", "solución correcta", 8, (t) => t.lectura === "bien" || grupo(t) === "reparado"],
          ["sin", "sin respuesta", 3, (t) => grupo(t) === "abstiene" || t.lectura === "rechazado"],
          ["mal", "solución errónea", 3, () => false]],
    };
    function disponer(e) {
      const bloques = estados[e];
      let x = 6;
      return bloques.map(([clave, titulo, cols, f]) => {
        const miembros = ts.filter(f).sort((a, b) => d3.ascending(a.lectura !== "bien", b.lectura !== "bien"));
        const b = { clave, titulo, x, cols, k: miembros.length };
        miembros.forEach((t, i) => (t[`p${e}`] = { x: x + r + (i % cols) * p, y: 96 + Math.floor(i / cols) * p }));
        x += Math.max(cols * p, 120) + 46;
        return b;
      });
    }
    const bloques = { 3: disponer(3), 4: disponer(4), 5: disponer(5) };

    const cab = svg.append("g");
    const caja = svg.append("g").attr("opacity", 0);
    const bMal = bloques[5].find((b) => b.clave === "mal");
    caja.append("rect").attr("x", bMal.x).attr("y", 84).attr("width", 3 * p + 4).attr("height", 3 * p).attr("rx", 8)
      .style("fill", "none").style("stroke", "var(--critico)").attr("stroke-width", 1.5);
    caja.append("text").attr("x", bMal.x + 32).attr("y", 128).attr("text-anchor", "middle").attr("font-size", 26)
      .style("fill", "var(--critico)").text("✕");

    const puntos = svg.append("g").selectAll("circle").data(ts, (t) => t.id).join("circle")
      .attr("r", r).attr("cx", (t) => t.pn.x).attr("cy", (t) => t.pn.y).attr("opacity", 0)
      .on("mousemove", (ev, t) => verTip(ev, `${t.n}×${t.n} · ${t.cuadernillo.replace("INKY_", "")}<br>` +
        ({ bien: "bien leído", sin_solucion: "lectura sin solución", rechazado: "rechazado: etiqueta ilegible" })[t.lectura] +
        (t.reparacion ? ` → ${t.reparacion === "bien" ? "reparado" : "se abstiene"}` : "") +
        (t.verdad_erronea ? "<br>la verdad del PDF estaba mal; la lectura, bien" : "")))
      .on("mouseleave", ocultarTip);

    const color = (t, s) => {
      if (s < 2) return "none";
      if (t.lectura === "bien") return "var(--indigo)";
      if (s < 3) return "none";
      if (t.lectura === "rechazado") return "var(--neutro)";
      if (s < 4) return "var(--naranja)";
      return t.reparacion === "bien" ? "var(--indigo)" : "var(--neutro)";
    };
    const anillo = (t, s) => (s >= 4 && t.reparacion === "bien" ? "var(--naranja)" : s < 2 || (s < 3 && t.lectura !== "bien") ? "var(--suave)" : "var(--papel)");

    return (s) => {
      const pos = (t) => (s >= 5 ? t.p5 : s >= 4 ? t.p4 : s >= 3 ? t.p3 : t.pn);
      puntos.transition().delay((t, i) => (s >= 1 ? i * 6 : 0)).duration(T + 150).ease(d3.easeCubicInOut)
        .attr("opacity", s >= 1 ? 1 : 0)
        .attr("cx", (t) => pos(t).x).attr("cy", (t) => pos(t).y)
        .style("fill", (t) => color(t, s))
        .style("stroke", (t) => anillo(t, s))
        .attr("stroke-width", (t) => (s >= 4 && t.reparacion === "bien" ? 3.5 : 1.6));
      rotN.transition().duration(T).attr("opacity", s >= 1 && s < 3 ? 1 : 0);
      const bs = s >= 3 ? bloques[Math.min(s, 5)] : [];
      cab.selectAll("g").data(bs, (b) => b.clave + b.titulo).join(
        (en) => {
          const g = en.append("g").attr("opacity", 0);
          g.append("text").attr("class", "num").attr("y", 44).attr("font-size", 36).attr("font-weight", 700)
            .style("font-family", "'Space Grotesk', sans-serif");
          g.append("text").attr("class", "mono tit").attr("y", 68).attr("font-size", 14).style("fill", "var(--suave)");
          return g;
        },
        (up) => up,
        (ex) => ex.transition().duration(250).attr("opacity", 0).remove())
        .call((g) => g.select(".num").text((b) => b.k).style("fill", (b) => (b.clave === "mal" ? "var(--critico)" : "var(--tinta)")))
        .call((g) => g.select(".tit").text((b) => b.titulo))
        .transition().duration(T).attr("opacity", 1).attr("transform", (b) => `translate(${b.x},0)`);
      caja.transition().duration(T).attr("opacity", s >= 5 ? 1 : 0);
    };
  };

  // ------------------------------------------- formulaciones: ramas por tablero

  VIZ.formulaciones = (el) => {
    const W = 790, H = 400, M = { l: 62, r: 20, t: 30, b: 64 };
    const svg = lienzo(el, W, H);
    const ts = D.tableros.filter((t) => t.n > 4).sort((a, b) => d3.ascending(a.n, b.n) || d3.ascending(a.binaria.ramas, b.binaria.ramas));
    const dominio = ts.map((t) => t.id);
    dominio.splice(ts.findIndex((t) => t.n === 9), 0, "_");
    const x = d3.scaleBand(dominio, [M.l, W - M.r]).padding(0.25);
    const y = d3.scaleLinear([0, 6000], [H - M.b, M.t]);
    svg.append("g").attr("class", "grid").selectAll("line").data([2000, 4000, 6000]).join("line")
      .attr("x1", M.l).attr("x2", W - M.r).attr("y1", y).attr("y2", y);
    svg.append("g").attr("class", "eje").selectAll("text").data([0, 2000, 4000, 6000]).join("text")
      .attr("x", M.l - 8).attr("y", (d) => y(d) + 4).attr("text-anchor", "end").text(miles);
    svg.append("text").attr("class", "rotulo-eje").attr("x", M.l).attr("y", M.t - 12).text("ramas de búsqueda por tablero (1 hilo)");
    [[6, "6×6 · 16 tableros"], [9, "9×9 · 7 tableros"]].forEach(([n, t]) => {
      const de = ts.filter((d) => d.n === n);
      const a = x(de[0].id), b = x(de[de.length - 1].id) + x.bandwidth();
      svg.append("line").attr("x1", a).attr("x2", b).attr("y1", H - M.b + 14).attr("y2", H - M.b + 14).style("stroke", "#C3C2B7");
      svg.append("text").attr("class", "rotulo-eje").attr("x", (a + b) / 2).attr("y", H - M.b + 34).attr("text-anchor", "middle").text(t);
    });
    svg.append("text").attr("class", "rotulo-eje").attr("x", W - M.r).attr("y", H - 6).attr("text-anchor", "end")
      .text("4×4 · 47 tableros: 0 ramas con ambas");
    const bw = Math.min(24, x.bandwidth());
    const barras = svg.append("g").selectAll("rect").data(ts).join("rect")
      .attr("x", (t) => x(t.id) + (x.bandwidth() - bw) / 2).attr("width", bw).attr("y", y(0)).attr("height", 0)
      .attr("rx", 4).style("fill", "var(--suave)");
    const base = svg.append("g").attr("opacity", 0);
    base.append("line").attr("x1", M.l).attr("x2", W - M.r).attr("y1", y(0)).attr("y2", y(0))
      .style("stroke", "var(--indigo)").attr("stroke-width", 3);
    base.selectAll("circle").data(ts).join("circle").attr("cx", (t) => x(t.id) + x.bandwidth() / 2).attr("cy", y(0)).attr("r", 5)
      .style("fill", "var(--indigo)").style("stroke", "var(--papel)").attr("stroke-width", 2);
    base.append("text").attr("class", "anot fuerte halo").attr("x", M.l + 8).attr("y", y(0) - 12).text("AllDifferent: 0 ramas en todos");
    const max = d3.greatest(ts, (t) => t.binaria.ramas);
    const etqMax = svg.append("text").attr("class", "anot fuerte halo").attr("x", x(max.id) + x.bandwidth() / 2)
      .attr("y", y(max.binaria.ramas) - 10).attr("text-anchor", "end").text(`${miles(max.binaria.ramas)} ramas`).attr("opacity", 0);
    const zona = svg.append("g").selectAll("rect").data(ts).join("rect")
      .attr("x", (t) => x(t.id)).attr("width", x.bandwidth()).attr("y", M.t).attr("height", H - M.b - M.t)
      .style("fill", "transparent")
      .on("mousemove", (ev, t) => verTip(ev, `${t.n}×${t.n}<br>binaria: ${miles(t.binaria.ramas)} ramas · ${t.binaria.ms.toFixed(1)} ms<br>AllDifferent: ${t.global.ramas} ramas · ${t.global.ms.toFixed(1)} ms`))
      .on("mouseleave", ocultarTip);
    return (s) => {
      base.transition().duration(T).attr("opacity", s >= 1 ? 1 : 0);
      barras.transition().delay((t, i) => (s >= 2 ? i * 30 : 0)).duration(T)
        .attr("y", (t) => (s >= 2 ? y(t.binaria.ramas) : y(0))).attr("height", (t) => (s >= 2 ? y(0) - y(t.binaria.ramas) : 0));
      etqMax.transition().delay(s >= 2 ? 900 : 0).duration(400).attr("opacity", s >= 2 ? 1 : 0);
      base.raise();
      zona.raise();
    };
  };

  // ------------------------------------------- sintético frente a real

  VIZ.sintetico = (el) => {
    const W = 790, H = 330, l = 300, r = 70;
    const svg = lienzo(el, W, H);
    const bien = D.tableros.filter((t) => t.lectura === "bien").length, total = D.tableros.length;
    const filas = [
      { t: "Sintético · limpio · tipografía del banco", v: 0.978, real: false },
      { t: "Sintético · foto · tipografía del banco", v: 0.956, real: false },
      { t: "Sintético · limpio · fuera del banco", v: 0.914, real: false },
      { t: "Sintético · foto · fuera del banco", v: 0.714, real: false },
      { t: `Real · KrazyDad (${bien} de ${total})`, v: bien / total, real: true },
    ];
    const x = d3.scaleLinear([0, 1], [l, W - r]);
    const y = d3.scaleBand(filas.map((f) => f.t), [20, H - 40]).padding(0.45);
    svg.append("g").attr("class", "grid").selectAll("line").data([0, 0.25, 0.5, 0.75, 1]).join("line")
      .attr("x1", x).attr("x2", x).attr("y1", 10).attr("y2", H - 34);
    svg.append("g").attr("class", "eje").selectAll("text").data([0, 0.5, 1]).join("text")
      .attr("x", x).attr("y", H - 14).attr("text-anchor", "middle").text((d) => pct(d));
    svg.append("g").selectAll("text").data(filas).join("text").attr("x", l - 14).attr("y", (f) => y(f.t) + y.bandwidth() / 2 + 5)
      .attr("text-anchor", "end").attr("font-size", 15).attr("font-weight", (f) => (f.real ? 600 : 400))
      .style("fill", (f) => (f.real ? "var(--tinta)" : "var(--suave)")).text((f) => f.t);
    const bh = Math.min(24, y.bandwidth());
    const barras = svg.append("g").selectAll("path").data(filas).join("path")
      .style("fill", (f) => (f.real ? "var(--indigo)" : "var(--neutro)"));
    const camino = (f, v) => {
      const y0 = y(f.t) + (y.bandwidth() - bh) / 2, x1 = x(v), rr = Math.min(4, x1 - l);
      return `M${l},${y0} H${x1 - rr} Q${x1},${y0} ${x1},${y0 + rr} V${y0 + bh - rr} Q${x1},${y0 + bh} ${x1 - rr},${y0 + bh} H${l} Z`;
    };
    barras.attr("d", (f) => camino(f, 0));
    const valores = svg.append("g").selectAll("text").data(filas).join("text").attr("class", "mono")
      .attr("y", (f) => y(f.t) + y.bandwidth() / 2 + 5).attr("x", (f) => x(f.v) + 8).attr("font-size", 15)
      .attr("font-weight", (f) => (f.real ? 700 : 400)).text((f) => pct(f.v, 1)).attr("opacity", 0);
    return (s) => {
      barras.transition().delay((f, i) => i * 80).duration(T)
        .attr("d", (f) => camino(f, (f.real ? s >= 2 : s >= 1) ? f.v : 0));
      valores.transition().duration(T).attr("opacity", (f) => ((f.real ? s >= 2 : s >= 1) ? 1 : 0));
    };
  };

  // ----------------------------------- la regla del margen (la llama el OJS)

  KK.margen = (el, cambios, margen) => {
    const R = D.reparacion, res = R.resultados[`${cambios}-${margen}`];
    const W = 760, H = 250, r = 12, p = 30;
    if (!el._svg) {
      el._svg = lienzo(el, W, H);
      el._svg.append("g").attr("class", "cab");
      el._svg.append("g").attr("class", "pts");
      el._svg.append("text").attr("class", "anot mono pie").attr("x", 0).attr("y", H - 6).attr("font-size", 13);
    }
    const svg = el._svg;
    const grupos = [
      ["bien", "repara bien", "var(--indigo)"],
      ["abstiene", "se abstiene", "var(--neutro)"],
      ["error", "error silencioso", "var(--critico)"],
    ];
    const xs = { bien: 0, abstiene: 260, error: 470 };
    const datos = res.map((v, i) => ({ i, v, n: R.n[i] }));
    const idx = { bien: 0, abstiene: 0, error: 0 };
    datos.forEach((d) => { const k = idx[d.v]++; d.x = xs[d.v] + r + (k % 6) * p; d.y = 100 + Math.floor(k / 6) * p; });
    svg.select(".cab").selectAll("g").data(grupos).join((en) => {
      const g = en.append("g").attr("transform", ([k]) => `translate(${xs[k]},0)`);
      g.append("text").attr("class", "num").attr("y", 48).attr("font-size", 40).attr("font-weight", 700)
        .style("font-family", "'Space Grotesk', sans-serif");
      g.append("text").attr("class", "mono").attr("y", 72).attr("font-size", 14).style("fill", "var(--suave)").text(([, t]) => t);
      return g;
    }).select(".num").text(([k]) => `${idx[k]}${k === "error" && idx[k] > 0 ? " ✕" : ""}`)
      .style("fill", ([k]) => (k === "error" && idx[k] > 0 ? "var(--critico)" : "var(--tinta)"));
    const col = Object.fromEntries(grupos.map(([k, , c]) => [k, c]));
    svg.select(".pts").selectAll("circle").data(datos, (d) => d.i).join(
      (en) => en.append("circle").attr("r", r).attr("cx", (d) => d.x).attr("cy", (d) => d.y)
        .style("stroke", "var(--papel)").attr("stroke-width", 2.5),
      (up) => up)
      .on("mousemove", (ev, d) => verTip(ev, `${d.n}×${d.n} · lectura sin solución → ${({ bien: "repara bien", abstiene: "se abstiene", error: "solución ERRÓNEA" })[d.v]}`))
      .on("mouseleave", ocultarTip)
      .transition().duration(T).ease(d3.easeCubicInOut)
      .attr("cx", (d) => d.x).attr("cy", (d) => d.y).style("fill", (d) => col[d.v]);
    svg.select(".pie").text(cambios === 3 && margen === 1
      ? "Así está el nodo: 3 cambios como máximo y margen 1."
      : `cambios ≤ ${cambios} · margen ${margen}`);
  };

  // Sin servidor no corre el OJS (Quarto lo bloquea en file://): el HTML autónomo usa este
  // mismo control en JS puro. Ver el contenido condicional por perfil en index.qmd.
  function segmentado(rotulo, opciones, inicial, alCambiar) {
    const raiz = document.createElement("div");
    raiz.innerHTML = `<span class="control">${rotulo}</span><div class="segmentado"></div>`;
    const grupo = raiz.querySelector(".segmentado");
    opciones.forEach((op) => {
      const b = document.createElement("button");
      b.textContent = op;
      b.setAttribute("aria-pressed", op === inicial);
      b.onclick = () => {
        grupo.querySelectorAll("button").forEach((x) => x.setAttribute("aria-pressed", x === b));
        alCambiar(op);
      };
      grupo.append(b);
    });
    return raiz;
  }
  VIZ.margen = (el) => {
    let k = 3, m = 1;
    const lienzoM = document.createElement("div");
    lienzoM.className = "lienzo solo";
    el.append(segmentado("cambios máximos", [1, 2, 3], k, (v) => KK.margen(lienzoM, (k = v), m)),
              segmentado("margen", [0, 1], m, (v) => KK.margen(lienzoM, k, (m = v))), lienzoM);
    KK.margen(lienzoM, k, m);
  };

  // -------------------------------------------------------------- arranque

  const pasoDe = (slide) => slide.querySelectorAll(".fragment.visible").length;
  function actualizar(slide, forzado) {
    if (!slide) return;
    const lienzos = slide.matches("[data-viz]") ? [slide] : [];
    lienzos.push(...slide.querySelectorAll("[data-viz]"));
    lienzos.forEach((el) => {
      const crear = VIZ[el.dataset.viz];
      if (!crear) return;
      if (!el._paso) { el._paso = crear(el) || (() => {}); el._ultimo = -1; }
      const s = forzado ?? pasoDe(slide);
      if (s !== el._ultimo) { el._ultimo = s; el._paso(s); }
    });
  }

  function iniciar() {
    const titulo = document.querySelector(".reveal .slides > section.quarto-title-block") || document.getElementById("title-slide");
    if (titulo && !titulo.querySelector(".tablero-titulo")) {
      const d = document.createElement("div");
      d.className = "tablero-titulo";
      d.dataset.viz = "titulo";
      titulo.appendChild(d);
    }
    const actual = () => actualizar(Reveal.getCurrentSlide());
    Reveal.on("slidechanged", (e) => actualizar(e.currentSlide));
    Reveal.on("fragmentshown", actual);
    Reveal.on("fragmenthidden", actual);
    const imprimiendo = (Reveal.isPrintingPDF && Reveal.isPrintingPDF()) || (Reveal.isPrintView && Reveal.isPrintView());
    if (imprimiendo) document.querySelectorAll(".slides section").forEach((s) => actualizar(s, 99));
    else actual();
  }
  (function esperar() {
    if (window.Reveal && Reveal.isReady && Reveal.isReady()) iniciar();
    else setTimeout(esperar, 60);
  })();
})();
