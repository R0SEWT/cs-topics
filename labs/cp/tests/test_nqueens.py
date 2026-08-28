from models.nqueens import solve_nqueens


def test_ocho_reinas_no_se_atacan():
    sol = solve_nqueens(8)
    assert sol is not None
    assert len(set(sol)) == 8, "dos reinas comparten fila"
    assert len({r + c for c, r in enumerate(sol)}) == 8, "diagonal ↘ repetida"
    assert len({r - c for c, r in enumerate(sol)}) == 8, "diagonal ↙ repetida"


def test_tres_reinas_no_tiene_solucion():
    assert solve_nqueens(3) is None
