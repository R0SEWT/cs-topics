"""N-reinas con CP-SAT — ejemplo de referencia para las unidades 2-4.

Sirve de plantilla: modelo -> restricciones -> solver -> solución.
"""

from ortools.sat.python import cp_model


def solve_nqueens(n: int) -> list[int] | None:
    """Devuelve la fila de cada reina por columna, o None si no hay solución."""
    model = cp_model.CpModel()
    queens = [model.new_int_var(0, n - 1, f"q{i}") for i in range(n)]

    model.add_all_different(queens)
    model.add_all_different(queens[i] + i for i in range(n))
    model.add_all_different(queens[i] - i for i in range(n))

    solver = cp_model.CpSolver()
    if solver.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return [solver.value(q) for q in queens]


if __name__ == "__main__":
    for size in (8, 12):
        print(f"n={size}: {solve_nqueens(size)}")
