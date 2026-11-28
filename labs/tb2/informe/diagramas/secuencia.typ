// Diagramas de secuencia y de arquitectura dibujados con primitivas de Typst.
// secuencia(actores, pasos): cada paso es (de, a, txt[, raya]) | (nota, sobre) | (sep,).

#let secuencia(actores, pasos, ancho: 230pt, paso: 15pt, tam: 6.9pt) = {
  let n = actores.len()
  let col = ancho / n
  let x(i) = col * (i + 0.5)
  let cab = 22pt
  // Altura acumulada: una nota de dos líneas ocupa 1,6 pasos.
  let peso(p) = if "nota" in p { p.at("h", default: 1.15) } else if "sep" in p { 0.85 } else { 1 }
  let total = pasos.map(peso).sum()
  let alto = cab + paso * (total + 0.6)
  set text(size: tam)
  set par(leading: 0.35em, justify: false)
  box(width: ancho, height: alto, {
    for (i, a) in actores.enumerate() {
      place(dx: x(i), dy: cab - 3pt, line(angle: 90deg, length: alto - cab + 3pt,
        stroke: (thickness: 0.4pt, dash: "dashed", paint: luma(130))))
      place(dx: x(i) - col / 2 + 3pt, dy: 0pt, box(width: col - 6pt, height: cab - 4pt, stroke: 0.5pt + luma(70),
        radius: 2pt, fill: luma(244), align(center + horizon, strong(a))))
    }
    let acum = 0
    for p in pasos {
      let h = peso(p)
      let y = cab + paso * (acum + h)
      acum += h
      if "nota" in p {
        let w = p.at("w", default: col * 0.94)
        let izq = calc.max(0pt, calc.min(ancho - w, x(p.sobre) - w / 2))
        place(dx: izq, dy: y - paso * h + 3pt, box(width: w, height: paso * h - 4pt, fill: rgb("#fff6dc"), stroke: 0.3pt + luma(120),
          inset: (x: 2pt, y: 1pt), radius: 1pt, align(center + horizon, p.nota)))
      } else if "sep" in p {
        place(dx: 0pt, dy: y - 9pt, line(length: ancho, stroke: (thickness: 0.4pt, paint: luma(110), dash: "dotted")))
        place(dx: 1pt, dy: y - 7.5pt, box(fill: white, inset: (x: 1.5pt, y: 0.5pt), emph(p.sep)))
      } else {
        let x0 = x(p.de)
        let x1 = x(p.a)
        let d = if x1 > x0 { 1 } else { -1 }
        let izq = calc.min(x0, x1)
        let largo = calc.abs(x1 - x0)
        place(dx: izq, dy: y, line(length: largo, stroke: (thickness: 0.6pt,
          dash: if p.at("raya", default: false) { "dashed" } else { "solid" })))
        place(dx: 0pt, dy: 0pt, polygon(fill: black, (x1, y), (x1 - d * 4pt, y - 1.8pt), (x1 - d * 4pt, y + 1.8pt)))
        let medio = (x0 + x1) / 2
        let w = calc.min(ancho, 2 * calc.min(medio, ancho - medio))
        place(dx: medio - w / 2, dy: y - 9pt, box(width: w, align(center, box(fill: white, inset: (x: 1.5pt, y: 0.6pt), p.txt))))
      }
    }
  })
}

// Arquitectura por capas: la tubería de decidir_unidad y los dos almacenes de estado.
#let capa(titulo, cuerpo, relleno: luma(246)) = box(width: 100%, height: 100%, fill: relleno, stroke: 0.5pt + luma(90),
  radius: 3pt, inset: 4pt, align(center + horizon, [#strong(titulo) \ #cuerpo]))
#let flecha = align(center + horizon, text(size: 9pt, sym.arrow.r))

#let arquitectura() = {
  set text(size: 7.2pt)
  set par(leading: 0.4em)
  let ext = rgb("#ffffff")
  block(width: 100%, stroke: (thickness: 0.5pt, paint: luma(120), dash: "dashed"), radius: 4pt, inset: 5pt, {
    align(left, text(size: 7.4pt)[*S6 · Optimización* — `decidir_unidad`: `time.perf_counter()` por turno, red de seguridad `try/except`, búsquedas acotadas, evaluación perezosa])
    v(-3pt)
    grid(columns: (1.05fr, 9pt, 1fr, 9pt, 1.05fr, 9pt, 1.1fr, 9pt, 1.25fr, 9pt, 1.2fr, 9pt, 0.7fr), rows: 56pt,
      capa([Simulador], [`unidad`, `percepcion`, `api`], relleno: ext), flecha,
      capa([S1 · Percepción y memoria], [`_percibir` \ `_percibir_tormentas` \ `_confianza`]), flecha,
      capa([S3 · FIPA-ACL], [`_leer_mensajes` \ `_procesar_mensaje` \ `_acl`, `_puede_reportar`]), flecha,
      capa([S5 · Gobernanza], [`_depositar_papeleta` \ `_votar_si_toca` \ `_copeland`]), flecha,
      capa([S2 · Utilidad y FSM], [`_rover`, `_explorador`, `_recargador` \ `_elegir_objetivo`, `_utilidad`, `_mover`, `_astar`]), flecha,
      capa([S4 · Contract Net], [`_reportar_hallazgos` \ `_abrir_subasta`, `_responder_cfp` \ `_cerrar_subastas`]), flecha,
      capa([Acción], [tupla], relleno: ext),
    )
    v(-3pt)
    grid(columns: (1fr, 1fr), column-gutter: 6pt, rows: 30pt,
      capa([Memoria privada de cada unidad (`self.memoria[id]`)], [hielo, restos, tormentas, objetivo, contrato, subastas, reportes · escriben S1, S3 y S4; lee S2], relleno: rgb("#eaf2fb")),
      capa([Estado de equipo, sin posiciones ni hallazgos], [política vigente, urna, tabla `POLITICAS` · escribe S5; S2 lee los pesos, S3 y S4 los umbrales], relleno: rgb("#fdf1e3")),
    )
  })
}
