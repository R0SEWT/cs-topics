#table(
  columns: (auto, 1fr, auto),
  align: (right, left, left),
  stroke: none, inset: (x: 3pt, y: 2.6pt),
  table.hline(stroke: 0.6pt),
  table.header([*$n$*], [*Estado local del votante*], [*Papeleta*]),
  table.hline(stroke: 0.4pt),
  [18], [en base, batería llena, tormenta a la vista], [`AHO` ≻ `EXP` ≻ `CAR` ≻ `REP`],
  [12], [en campo, sin tormenta, 4 vetas ricas en memoria], [`EXP` ≻ `AHO` ≻ `CAR` ≻ `REP`],
  [8], [en campo, tormenta a la vista, 2 vetas ricas], [`AHO` ≻ `EXP` ≻ `CAR` ≻ `REP`],
  [7], [batería bajo 50 %, 2 restos en memoria], [`CAR` ≻ `AHO` ≻ `EXP` ≻ `REP`],
  [5], [en base, sin tormenta ni hallazgos], [`EXP` ≻ `AHO` ≻ `CAR` ≻ `REP`],
  table.hline(stroke: 0.6pt),
)
