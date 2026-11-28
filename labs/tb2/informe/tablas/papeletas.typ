#table(
  columns: (1fr, auto),
  align: (left, left),
  stroke: none, inset: (x: 3pt, y: 2.6pt),
  table.hline(stroke: 0.6pt),
  table.header([*Estado local del votante*], [*Papeleta que produce*]),
  table.hline(stroke: 0.4pt),
  [en base, batería llena, tormenta a la vista], [`AHO` ≻ `EXP` ≻ `CAR` ≻ `REP`],
  [en campo, sin tormenta, 4 vetas ricas en memoria], [`EXP` ≻ `AHO` ≻ `CAR` ≻ `REP`],
  [en campo, tormenta a la vista, 2 vetas ricas], [`AHO` ≻ `EXP` ≻ `CAR` ≻ `REP`],
  [batería bajo 50 %, 2 restos en memoria], [`CAR` ≻ `AHO` ≻ `EXP` ≻ `REP`],
  [en base, sin tormenta ni hallazgos], [`EXP` ≻ `AHO` ≻ `CAR` ≻ `REP`],
  table.hline(stroke: 0.6pt),
)
