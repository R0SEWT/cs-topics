"""TSP con CP-SAT — TP5 (materials/week-05/TP5.pdf).

Tres formas de evitar subtours sobre las mismas variables x[i, j]:
  Tarea 1  add_circuit: la restricción global se encarga del ciclo.
  Tarea 2  MTZ reificado: grados + orden u[i] con only_enforce_if, sin add_circuit.
  Tarea 3  híbrido: add_circuit para el ciclo y u solo para medir el orden.

Contrato común: devuelven (costo, ruta), con la ruta saliendo y volviendo a 0
(p. ej. [0, 3, 1, 2, 0]), o None si el solver no encuentra solución. Aceptan
un `solver` ya configurado (límite de tiempo, workers) para poder leer sus
estadísticas después; si no se pasa, crean uno.

El enunciado usa la API en CamelCase (NewBoolVar, AddCircuit, OnlyEnforceIf);
aquí va la snake_case, como en nqueens.py. Es la misma API.
"""

from ortools.sat.python import cp_model

Ruta = list[int]
Arcos = dict[tuple[int, int], cp_model.IntVar]


def extraer_ruta(solver: cp_model.CpSolver, x: Arcos, n: int) -> Ruta:
    """Tarea 1, paso 4: la ruta secuencial a partir de los arcos activos."""
    # COMPLETAR AQUI: empieza en el nodo 0, busca el arco activo (True) que
    # sale de él, avanza, y repite hasta volver al nodo 0.
    raise NotImplementedError("Tarea 1, paso 4: extraer la ruta")


def solve_tsp_circuit_basic(
    dist_matrix: list[list[int]], solver: cp_model.CpSolver | None = None
) -> tuple[int, Ruta] | None:
    """Tarea 1: add_circuit básico."""
    n = len(dist_matrix)
    model = cp_model.CpModel()
    x = {}
    arcs = []  # tuplas (origen, destino, var_booleana)
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.new_bool_var(f"x_{i}_{j}")
                # 1. COMPLETAR AQUI: agrega la tupla correspondiente a `arcs`

    # 2. COMPLETAR AQUI: la restricción global de circuito

    # 3. Función objetivo
    model.minimize(sum(x[i, j] * dist_matrix[i][j] for i, j in x))

    solver = solver if solver is not None else cp_model.CpSolver()
    if solver.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return int(solver.objective_value), extraer_ruta(solver, x, n)


def solve_tsp_mtz_cp(
    dist_matrix: list[list[int]], solver: cp_model.CpSolver | None = None
) -> tuple[int, Ruta] | None:
    """Tarea 2: MTZ "manual" con reificación, sin add_circuit."""
    n = len(dist_matrix)
    model = cp_model.CpModel()
    x = {(i, j): model.new_bool_var(f"x_{i}_{j}") for i in range(n) for j in range(n) if i != j}
    u = {i: model.new_int_var(1, n - 1, f"u_{i}") for i in range(1, n)}

    # 1. Restricciones de grado: un arco sale y un arco entra en cada nodo
    for i in range(n):
        model.add_exactly_one(x[i, j] for j in range(n) if i != j)
        model.add_exactly_one(x[j, i] for j in range(n) if i != j)

    # 2. Restricción MTZ (reificación)
    for i in range(1, n):
        for j in range(1, n):
            if i != j:
                # COMPLETAR AQUI: si x[i, j] es True, entonces u[j] >= u[i] + 1
                pass

    model.minimize(sum(x[i, j] * dist_matrix[i][j] for i, j in x))

    solver = solver if solver is not None else cp_model.CpSolver()
    if solver.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return int(solver.objective_value), extraer_ruta(solver, x, n)


def solve_tsp_precedence(
    dist_matrix: list[list[int]],
    antes: int = 2,
    despues: int = 4,
    solver: cp_model.CpSolver | None = None,
) -> tuple[int, Ruta] | None:
    """Tarea 3: circuito + precedencia (`antes` se visita antes que `despues`)."""
    n = len(dist_matrix)
    model = cp_model.CpModel()
    x = {}
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.new_bool_var(f"x_{i}_{j}")
                # COMPLETAR AQUI (como en la Tarea 1): la tupla del arco

    # COMPLETAR AQUI (como en la Tarea 1): la restricción de circuito

    # COMPLETAR AQUI: las variables de orden u (el enunciado las da por definidas)
    u = {}

    # Vinculamos la variable de tiempo u con la ruta x (dado por el enunciado)
    for i in range(n):
        for j in range(n):
            if i != j and i != 0:
                model.add(u[j] == u[i] + 1).only_enforce_if(x[i, j])

    # COMPLETAR AQUI: el nodo `antes` va antes que el nodo `despues`

    model.minimize(sum(x[i, j] * dist_matrix[i][j] for i, j in x))

    solver = solver if solver is not None else cp_model.CpSolver()
    if solver.solve(model) not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return None
    return int(solver.objective_value), extraer_ruta(solver, x, n)


if __name__ == "__main__":
    # Asimétrica: en simétrica, invertir el ciclo sale gratis y la precedencia
    # de la Tarea 3 nunca cambiaría el costo.
    ejemplo = [
        [0, 5, 19, 3, 9],
        [4, 0, 16, 15, 16],
        [13, 7, 0, 4, 16],
        [1, 13, 14, 0, 20],
        [1, 15, 9, 8, 0],
    ]
    for nombre, solve in [
        ("Tarea 1 · circuit", solve_tsp_circuit_basic),
        ("Tarea 2 · MTZ", solve_tsp_mtz_cp),
        ("Tarea 3 · 2 antes que 4", solve_tsp_precedence),
    ]:
        total, ruta = solve(ejemplo)
        print(f"{nombre}: costo {total}, ruta {' -> '.join(map(str, ruta))}")
