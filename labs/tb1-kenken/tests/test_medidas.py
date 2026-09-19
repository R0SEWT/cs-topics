"""Tests de las dos defensas que solo se notan en fotos reales.

Ambas sobrevivían a la mutación con los tableros sintéticos: en ellos la
morfología ya deja la imagen limpia, así que hay que provocar la situación a
mano sobre máscaras construidas para el caso.
"""

import numpy as np

from kenken_cv.cages import _grosor_en
from kenken_cv.grid import _elegir_n, _perfil, _posiciones


def test_el_grosor_ignora_lo_que_toca_la_linea_solo_en_un_tramo():
    """Un dígito pegado a la arista engorda la medida en unas pocas filas.

    Con la mediana el resultado sigue siendo el grosor real; con la media se
    contamina, y una arista fina pasaría por gruesa (jaulas partidas de más).
    """
    alto, ancho, centro = 100, 60, 30
    mascara = np.zeros((alto, ancho), dtype=np.uint8)
    mascara[:, centro - 1 : centro + 2] = 255           # línea fina de 3 px
    mascara[10:25, centro - 12 : centro + 13] = 255     # mancha: un glifo al lado

    assert _grosor_en(mascara, centro, range(0, alto), vertical=True) == 3.0


def test_el_grosor_mide_el_tramo_contiguo_al_centro_no_toda_la_franja():
    """Otra línea cercana dentro del radio de muestreo no debe sumarse."""
    alto, ancho, centro = 60, 60, 30
    mascara = np.zeros((alto, ancho), dtype=np.uint8)
    mascara[:, centro - 3 : centro + 4] = 255   # la línea que nos interesa: 7 px
    mascara[:, centro + 9 : centro + 12] = 255  # vecina, separada por blanco

    assert _grosor_en(mascara, centro, range(0, alto), vertical=True) == 7.0


def _mascara_con_lineas(lado: int, n: int, huecos: dict[int, tuple[int, int]] | None = None):
    """Rejilla de n celdas; `huecos` borra un tramo de la línea i-ésima."""
    m = np.zeros((lado, lado), dtype=np.uint8)
    paso = lado / n
    for i in range(n + 1):
        x = min(lado - 3, int(round(i * paso)))
        m[:, max(0, x - 1) : x + 2] = 255
        if huecos and i in huecos:
            a, b = huecos[i]
            m[a:b, max(0, x - 1) : x + 2] = 0
    return m


def test_deduce_el_tamano_aunque_las_lineas_lleguen_partidas():
    """El caso que los tableros sintéticos nunca produjeron y los reales sí.

    En un KenKen impreso la línea fina se interrumpe allí donde una jaula la
    atraviesa, y un sesgo mínimo la trocea en tramos a alturas distintas.
    Exigir que cada línea cruce el tablero entero descartaba esos tramos y el
    tamaño salía mal; la periodicidad sobrevive a los huecos.
    """
    lado, n = 900, 6
    huecos = {1: (0, 600), 2: (200, 800), 4: (0, 450)}  # más de la mitad borrada
    perfil = _perfil(_mascara_con_lineas(lado, n, huecos), eje=0)
    assert _elegir_n((perfil,), lado) == n


def test_ante_un_divisor_gana_el_tamano_mayor():
    """Una rejilla de 3 cae sobre líneas reales de un tablero de 6 y puntúa
    igual de bien. Sin preferir el n mayor, el tablero saldría a la mitad."""
    lado, n = 900, 6
    perfil = _perfil(_mascara_con_lineas(lado, n), eje=0)
    assert _elegir_n((perfil,), lado) == n


def test_las_posiciones_caen_sobre_las_lineas_reales():
    lado, n = 900, 5
    perfil = _perfil(_mascara_con_lineas(lado, n), eje=0)
    for i, x in enumerate(_posiciones(perfil, n, lado)):
        assert abs(x - i * lado / n) <= 3


def test_los_dos_ejes_deciden_juntos_el_tamano():
    """Si un eje sale limpio y el otro maltrecho, el limpio no debe imponer un
    tamaño que el otro no soporta: se puntúa por el peor de los dos.

    El hueco es del 65%, no del 98%: medido sobre los tableros de KrazyDad, la
    línea más comida de un tablero correcto conserva ~29% del ancho. Pedirle al
    detector que sobreviva a una línea prácticamente borrada sería pedirle que
    no distinga una línea ausente de una presente, que es justo lo que decide
    el tamaño.
    """
    lado = 900
    bueno = _perfil(_mascara_con_lineas(lado, 6), eje=0)
    malo = _perfil(_mascara_con_lineas(lado, 6, {3: (0, 585)}), eje=0)
    assert _elegir_n((bueno, malo), lado) == 6


def test_una_linea_que_no_existe_descarta_ese_tamano():
    """El criterio en una frase: si el n propuesto predice una línea que no
    está, ese n queda fuera aunque las demás encajen perfectas."""
    lado = 900
    completo = _perfil(_mascara_con_lineas(lado, 6), eje=0)
    assert _elegir_n((completo,), lado) == 6

    # Se borra una línea que solo pertenece a la rejilla de 6 (las de índice
    # par las comparte con la de 3, y borrar una de esas no dejaría ningún n en
    # pie). Sin ella, la explicación más fina que sobrevive es la de 3.
    sin_una = _mascara_con_lineas(lado, 6)
    x = int(round(1 * lado / 6))
    sin_una[:, x - 1 : x + 2] = 0
    assert _elegir_n((_perfil(sin_una, eje=0),), lado) == 3
