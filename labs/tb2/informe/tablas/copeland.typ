#table(
  columns: (auto, 1fr, 1fr, 1fr, 1fr, auto),
  align: (left,) + (right,) * 5,
  stroke: none, inset: (x: 3pt, y: 2.6pt),
  table.hline(stroke: 0.6pt),
  table.header([*$a$ frente a $b$*], [*`AHO`*], [*`EXP`*], [*`CAR`*], [*`REP`*], [*Copeland*]),
  table.hline(stroke: 0.4pt),
  [`AHORRO`], [—], [25], [48], [41], [2,5],
  [`EXPANSION`], [25], [—], [40], [36], [2,5],
  [`CARRONA`], [2], [10], [—], [38], [1,0],
  [`REPLIEGUE`], [9], [14], [12], [—], [0,0],
  table.hline(stroke: 0.6pt),
)
