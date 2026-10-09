"""Reparación guiada por el solver.

Cuando lo que la visión leyó no tiene solución, casi siempre es porque confundió un glifo:
un ÷ cuyos puntos se fundieron con la barra se lee +, un 5 se lee 6. En vez de rendirse,
el modelo considera para cada jaula su lectura y las alternativas plausibles, cada una con
un literal reificado (ℓ ⇒ restricción de la jaula), exige exactamente una por jaula y
minimiza cuántas lecturas cambia. La corrección se acepta solo si:
  * cambia como mucho `max_cambios` jaulas,
  * ninguna otra corrección con los mismos cambios o uno más lleva a una solución distinta
    (si dos lecturas casi igual de plausibles dan tableros distintos, no hay base para
    elegir: pasó en un 4x4 real con dos 5+ leídos como 6+, donde arreglar uno solo ya
    dejaba un tablero válido, pero equivocado),
  * y deja el tablero con solución única.
Si algo de eso falla, no se repara: mejor rechazar que inventar.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from ortools.sat.python import cp_model

from kenken_cp.solver import Rejilla, contar_soluciones, resolver
from kenken_cv.schema import Cage, Instance

# Confusiones de operador observadas: los puntos del ÷ se funden con la barra (+), y el ×
# girado se parece al +.
OPERADORES = {"+": ("/", "*"), "/": ("+",), "*": ("+",), "-": ("+",)}
# Confusiones de dígito observadas en 895 etiquetas reales (5->6 domina) y sus vecinas.
DIGITOS = {"5": "6", "6": "58", "8": "693", "3": "8", "9": "8", "1": "7", "7": "1"}


@dataclass(frozen=True)
class Correccion:
    celda: tuple[int, int]  # celda ancla de la jaula
    leido: tuple[str, int]
    corregido: tuple[str, int]


@dataclass(frozen=True)
class Reparacion:
    instancia: Instance
    solucion: Rejilla
    correcciones: tuple[Correccion, ...]


def _admisible(op: str, objetivo: int, celdas: int, n: int) -> bool:
    if objetivo < 1:
        return False
    if op == "=":
        return celdas == 1 and objetivo <= n
    if op in "-/":
        return celdas == 2 and objetivo < n
    return celdas >= 2


def _peso(leido: tuple[str, int], alternativa: tuple[str, int]) -> int:
    """Cuán poco plausible es una corrección, según lo observado en tableros reales:
    el 5 leído como 6 domina (21 de 26 fallos), luego el ÷ leído como + (fotos)."""
    (op, t), (op2, t2) = leido, alternativa
    if op != op2:
        return 2 if (op, op2) == ("+", "/") else 4
    if (str(t).count("6") > str(t2).count("6")) and "5" in str(t2):
        return 1
    return 3


def candidatas(jaula: Cage, n: int) -> list[tuple[str, int, int]]:
    """(op, objetivo, peso): la lectura original (peso 0) y las alternativas a un solo
    cambio de glifo, de la más a la menos plausible."""
    op, t = jaula.op, jaula.target
    alternativas = [(op2, t) for op2 in OPERADORES.get(op, ())]
    s = str(t)
    for i, d in enumerate(s):
        for d2 in DIGITOS.get(d, ""):
            if i == 0 and d2 == "0":
                continue
            alternativas.append((op, int(s[:i] + d2 + s[i + 1:])))
    vistas, salida = set(), []
    for c in alternativas:
        if c not in vistas and c != (op, t) and _admisible(*c, len(jaula.cells), n):
            vistas.add(c)
            salida.append((*c, _peso((op, t), c)))
    return [(op, t, 0)] + sorted(salida, key=lambda c: c[2])


def _modelo(instancia: Instance, opciones: list[list[tuple[str, int]]]):
    n = instancia.size
    m = cp_model.CpModel()
    x = [[m.NewIntVar(1, n, f"x_{r}_{c}") for c in range(n)] for r in range(n)]
    for i in range(n):
        m.AddAllDifferent(x[i])
        m.AddAllDifferent([x[j][i] for j in range(n)])
    literales, cambios, peso = [], [], []
    for k, (jaula, cands) in enumerate(zip(instancia.cages, opciones)):
        v = [x[r][c] for r, c in jaula.cells]
        # Variables definidas sin condición; la restricción sobre ellas es la que se reifica.
        suma = sum(v)
        prod = None
        if any(op == "*" for op, _, _ in cands):
            prod = m.NewIntVar(1, n ** len(v), f"p_{k}")
            m.AddMultiplicationEquality(prod, v)
        if len(v) == 2:
            M, mi = m.NewIntVar(1, n, f"M_{k}"), m.NewIntVar(1, n, f"m_{k}")
            m.AddMaxEquality(M, v)
            m.AddMinEquality(mi, v)
        lits = []
        for j, (op, t, w) in enumerate(cands):
            ell = m.NewBoolVar(f"l_{k}_{j}")
            if op == "=":
                m.Add(v[0] == t).OnlyEnforceIf(ell)
            elif op == "+":
                m.Add(suma == t).OnlyEnforceIf(ell)
            elif op == "*":
                m.Add(prod == t).OnlyEnforceIf(ell)
            elif op == "-":
                m.Add(M - mi == t).OnlyEnforceIf(ell)
            elif op == "/":
                m.Add(M == t * mi).OnlyEnforceIf(ell)
            lits.append(ell)
            if j > 0:
                cambios.append(ell)
                # Primero se minimizan los cambios; entre correcciones con igual número
                # de cambios, gana la más plausible según lo observado.
                peso.append((100 + w) * ell)
        m.AddExactlyOne(lits)
        literales.append(lits)
    return m, x, literales, cambios, peso


def _resolver_modelo(m: cp_model.CpModel) -> cp_model.CpSolver | None:
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = 3.0
    s.parameters.num_workers = 8
    return s if s.Solve(m) == cp_model.OPTIMAL else None


def reparar(instancia: Instance, max_cambios: int = 3, margen: int = 1) -> Reparacion | None:
    """Corrección mínima y sin ambigüedad de una lectura sin solución, o None."""
    if resolver(instancia) is not None:
        return None  # ya tiene solución: no hay nada que reparar
    n = instancia.size
    opciones = [candidatas(j, n) for j in instancia.cages]
    m, x, literales, cambios, peso = _modelo(instancia, opciones)
    m.Add(sum(cambios) <= max_cambios)
    m.Minimize(sum(peso))
    s = _resolver_modelo(m)
    if s is None:
        return None
    elegidas = [next(j for j, ell in enumerate(lits) if s.Value(ell)) for lits in literales]
    k_cambios = sum(e > 0 for e in elegidas)
    rejilla = [[s.Value(v) for v in fila] for fila in x]

    # ¿Otra corrección con los mismos cambios, o `margen` más, da un tablero distinto?
    # Entonces es ambigua.
    m2, x2, _, cambios2, _ = _modelo(instancia, opciones)
    m2.Add(sum(cambios2) <= k_cambios + margen)
    distinta = []
    for r, fila in enumerate(x2):
        for c, v in enumerate(fila):
            b = m2.NewBoolVar(f"d_{r}_{c}")
            m2.Add(v != rejilla[r][c]).OnlyEnforceIf(b)
            distinta.append(b)
    m2.AddBoolOr(distinta)
    s2 = cp_model.CpSolver()
    s2.parameters.max_time_in_seconds = 3.0
    s2.parameters.num_workers = 8
    if s2.Solve(m2) != cp_model.INFEASIBLE:
        return None  # ambigua, o no se pudo descartar en el tiempo dado

    jaulas, correcciones = [], []
    for jaula, cands, e in zip(instancia.cages, opciones, elegidas):
        op, t, _ = cands[e]
        if e > 0:
            correcciones.append(Correccion(min(jaula.cells), (jaula.op, jaula.target), (op, t)))
        jaulas.append(replace(jaula, op=op, target=t))
    corregida = Instance(size=n, cages=tuple(jaulas))
    if contar_soluciones(corregida, tope=2) != 1:
        return None
    return Reparacion(corregida, resolver(corregida), tuple(correcciones))
