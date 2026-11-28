#table(
  columns: (auto, 1fr, 1fr, 1fr, 1fr, auto),
  align: (left,) + (right,) * 5,
  stroke: none, inset: (x: 3pt, y: 2.6pt),
  table.hline(stroke: 0.6pt),
  table.header([*$a$ vence a $b$*], [*`AHO`*], [*`EXP`*], [*`CAR`*], [*`REP`*], [*Copeland*]),
  table.hline(stroke: 0.4pt),
  [`AHORRO`], [—], [33], [43], [50], [3,0],
  [`EXPANSION`], [17], [—], [43], [50], [2,0],
  [`CARRONA`], [7], [7], [—], [50], [1,0],
  [`REPLIEGUE`], [0], [0], [0], [—], [0,0],
  table.hline(stroke: 0.6pt),
)
