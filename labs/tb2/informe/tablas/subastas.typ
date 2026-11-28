#table(
  columns: (1fr, auto, auto, auto, auto, auto, auto),
  align: (left,) + (right,) * 6,
  stroke: none, inset: (x: 3pt, y: 2.6pt),
  table.hline(stroke: 0.6pt),
  table.header([], [*Viajes en vano*], [*Bat. en pasos*], [*Hielo*], [*Hielo / 100 bat.*], [*Mensajes*], [*Ratio ± desv.*]),
  table.hline(stroke: 0.4pt),
  [Con subastas (entrega)], [51,0], [2808], [133], [3,67], [188], [0,0378 ± 0,0075],
  [Sin subastas], [276,7], [4809], [171], [2,89], [175], [0,0332 ± 0,0098],
  table.hline(stroke: 0.6pt),
)
