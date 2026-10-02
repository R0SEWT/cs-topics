"""Modelo CP-SAT de KenKen.

Implementación de la Fase 2 del solver.
"""

from __future__ import annotations

from ortools.sat.python import cp_model
from kenken_cv.schema import Instance

# Una rejilla resuelta: `rejilla[fila][columna]` es el valor de esa celda.
Rejilla = tuple[tuple[int, ...], ...]


def _construir_modelo(instancia: Instance) -> tuple[cp_model.CpModel, list[list[cp_model.IntVar]]]:
    n = instancia.size
    model = cp_model.CpModel()
    
    # 1. Variables enteras por celda con dominio 1..n
    x = [[model.NewIntVar(1, n, f"x_{r}_{c}") for c in range(n)] for r in range(n)]
    
    # 2. Cuadrado latino: AllDifferent por cada fila y por cada columna
    for i in range(n):
        model.AddAllDifferent(x[i])
        model.AddAllDifferent([x[j][i] for j in range(n)])
        
    # 3. Restricciones por jaula
    for idx, cage in enumerate(instancia.cages):
        celdas = [x[r][c] for r, c in cage.cells]
        target = cage.target
        op = cage.op
        
        if op == "=":
            model.Add(celdas[0] == target)
        elif op == "+":
            model.Add(sum(celdas) == target)
        elif op == "*":
            model.AddMultiplicationEquality(target, celdas)
        elif op == "-":
            a, b = celdas[0], celdas[1]
            max_var = model.NewIntVar(1, n, f"max_{idx}")
            min_var = model.NewIntVar(1, n, f"min_{idx}")
            model.AddMaxEquality(max_var, [a, b])
            model.AddMinEquality(min_var, [a, b])
            model.Add(max_var - min_var == target)
        elif op == "/":
            a, b = celdas[0], celdas[1]
            max_var = model.NewIntVar(1, n, f"max_{idx}")
            min_var = model.NewIntVar(1, n, f"min_{idx}")
            model.AddMaxEquality(max_var, [a, b])
            model.AddMinEquality(min_var, [a, b])
            # max_var / min_var == target AND max_var % min_var == 0
            # -> max_var == target * min_var
            model.Add(max_var == target * min_var)
            
    return model, x


def resolver(instancia: Instance) -> Rejilla | None:
    """Resuelve el tablero. Devuelve la rejilla, o None si no tiene solución."""
    model, x = _construir_modelo(instancia)
    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        n = instancia.size
        return tuple(tuple(solver.Value(x[r][c]) for c in range(n)) for r in range(n))
    return None


class SolutionCounter(cp_model.CpSolverSolutionCallback):
    def __init__(self, limit: int):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.solution_count = 0
        self.limit = limit

    def on_solution_callback(self):
        self.solution_count += 1
        if self.solution_count >= self.limit:
            self.StopSearch()


def contar_soluciones(instancia: Instance, tope: int = 2) -> int:
    """Cuántas soluciones tiene, dejando de contar al llegar a `tope`."""
    model, _ = _construir_modelo(instancia)
    solver = cp_model.CpSolver()
    counter = SolutionCounter(tope)
    
    # Encontrar todas las soluciones hasta el límite
    solver.parameters.enumerate_all_solutions = True
    solver.Solve(model, counter)
    
    return counter.solution_count
