"""
equipoX.py - faccion para el Trabajo Final de Topicos en CC (simulacion
multiagente en Marte).

El archivo esta ordenado en seis capas, una por sesion del curso:

  S1  Memoria espacial   cada unidad guarda SU mapa de hielo, restos y
                         tormentas, con olvido.
  S2  Utilidad y FSM     U(s,a) con cuatro pesos, una FSM por rol y A*
                         acotado contra tormentas.
  S3  Mensajes FIPA-ACL  un solo formato (performative, sender,
                         conversation_id, ontology, content) y filtros para
                         no gastar bateria en mensajes.
  S4  Contract Net       subastas CFP/PROPOSE/ACCEPT/REJECT para hielo,
                         restos y recargas, y subasta implicita (sin
                         mensajes) entre unidades que se ven.
  S5  Gobernanza         votacion Copeland entre cuatro politicas que
                         cambian pesos y umbrales.
  S6  Rendimiento        sin bloqueos, estructuras O(1), busquedas acotadas
                         y perfilado por turno.

Regla de integridad: lo que una unidad sabe de hielo, restos o rescates
fuera de su vision solo le llega por `api`. El equipo comparte sin costo
unicamente la politica vigente (un nombre) y las papeletas de la votacion,
que no llevan posiciones ni hallazgos.

El codigo no fija el tamano de la flota ni la esquina: funciona con
cualquier letra de equipo. Solo usa la libreria estandar y sintaxis
compatible con Python 3.8.
"""

from __future__ import annotations

import heapq
import math
import time
from typing import Any, Dict, List, Optional, Tuple

from equipo_base import (
    GRID_H,
    GRID_W,
    UMBRAL_BATERIA_BAJA,
    EquipoBase,
    Percepcion,
    UnidadVista,
)

Pos = Tuple[int, int]
Accion = Tuple[Any, ...]
Memoria = Dict[str, Any]
Tormenta = Tuple[
    float, float, float, int, float, float
]  # x, y, radio, tick, vx, vy

# -----------------------------------------------------------------------------
# Constantes del entorno (del enunciado y del simulador)
# -----------------------------------------------------------------------------
VISION = {"rover": 5, "dron_explorador": 9, "dron_recarga": 7}
RADIO_BASE = 6  # mas cerca que esto, la unidad se considera "en la base"
MARGEN_BATERIA = 4.0  # colchon sobre el 25 % al planificar un viaje

# Estados de las FSM (S2)
OCIOSO = "OCIOSO"
EXPLORANDO = "EXPLORANDO"
RECOLECTANDO = "RECOLECTANDO"
RETORNANDO = "RETORNANDO"
CONSUMIENDO_CARRONA = "CONSUMIENDO_CARRONA"
ESPERANDO_RECARGA = "ESPERANDO_RECARGA"
PATRULLANDO = "PATRULLANDO"
RETORNANDO_BASE = "RETORNANDO_BASE"
EN_ESPERA = "EN_ESPERA"
EN_RESCATE = "EN_RESCATE"

# Performativas FIPA-ACL (S3)
REQUEST = "REQUEST"
INFORM = "INFORM"
CFP = "CFP"
PROPOSE = "PROPOSE"
ACCEPT_PROPOSAL = "ACCEPT_PROPOSAL"
REJECT_PROPOSAL = "REJECT_PROPOSAL"
AGREE = "AGREE"
FAILURE = "FAILURE"

# Ontologias: de que trata el mensaje
ONT_HIELO = "hielo"
ONT_RESTOS = "restos"
ONT_RECARGA = "recarga"

# -----------------------------------------------------------------------------
# S5 - Politicas globales. La ganadora de la votacion fija estos parametros
# para todo el equipo.
#   w             pesos w1..w4 de U(s,a): hielo, desplazamiento, carrona,
#                 tormenta. Calibrados con un barrido (ver informe): frente a
#                 la primera version, w2 quedo a la mitad y w4 al triple.
#   umbral_u      utilidad de reserva: lo que vale "volver a base"; un objetivo
#                 debe superarla
#   radio_max     distancia maxima a la base a la que se trabaja o se patrulla
#   valor_min     hielo minimo de una zona para que valga un mensaje
#                 (umbral de S3)
#   enfriamiento  ticks antes de repetir un reporte sobre la misma zona
#                 (umbral de S3)
#   k_cnp         a cuantas unidades se invita a una subasta
#                 (umbral de S4)
#   exploradores  de cada 15 drones exploradores, cuantos estan de turno
#                 patrullando
#   cadencia      un explorador de turno avanza 1 de cada `cadencia` ticks
#   bat_pit       bateria bajo la cual un rover vacio pide recarga preventiva
#                 al pasar por base
# -----------------------------------------------------------------------------
POLITICAS = {
    "EXPANSION": {
        "w": (1.0, 0.4, 0.3, 3.0),
        "umbral_u": 0.02,
        "radio_max": 34,
        "valor_min": 3,
        "enfriamiento": 40,
        "k_cnp": 3,
        "exploradores": 3,
        "cadencia": 2,
        "bat_pit": 55.0,
    },
    "AHORRO": {
        "w": (1.0, 0.6, 0.3, 6.0),
        "umbral_u": 0.08,
        "radio_max": 26,
        "valor_min": 4,
        "enfriamiento": 90,
        "k_cnp": 2,
        "exploradores": 2,
        "cadencia": 3,
        "bat_pit": 50.0,
    },
    "CARRONA": {
        "w": (0.8, 0.5, 1.2, 4.5),
        "umbral_u": 0.05,
        "radio_max": 30,
        "valor_min": 4,
        "enfriamiento": 60,
        "k_cnp": 2,
        "exploradores": 2,
        "cadencia": 3,
        "bat_pit": 45.0,
    },
    "REPLIEGUE": {
        "w": (0.6, 0.8, 0.2, 9.0),
        "umbral_u": 0.25,
        "radio_max": 14,
        "valor_min": 8,
        "enfriamiento": 200,
        "k_cnp": 2,
        "exploradores": 1,
        "cadencia": 3,
        "bat_pit": 35.0,
    },
}
ORDEN_POLITICAS = (
    "AHORRO",
    "EXPANSION",
    "CARRONA",
    "REPLIEGUE",
)  # desempate final
POLITICA_INICIAL = "AHORRO"
# ventaja (fraccion de votantes) que la retadora debe sacar a la vigente
MARGEN_INERCIA = 0.10
PERIODO_VOTACION = 50  # ticks entre elecciones
# ticks sin ver ni conocer hielo para que una unidad vote por replegarse
TICKS_SIN_HIELO = 150

# S1 - memoria
# ticks para que la confianza en una veta no revisitada baje a la mitad
VIDA_MEDIA_HIELO = 250.0
OLVIDO_HIELO = (
    900  # ticks tras los cuales una veta o un resto no revisitado se borra
)
MEMORIA_TORMENTA = 14  # ticks que se recuerda una tormenta que ya no se ve
RASTRO_TORMENTAS = (
    12  # observaciones de tormenta que se conservan como trayectoria reciente
)

# S2 - navegacion y busqueda
MAX_NODOS_ASTAR = 90  # tope de expansiones por busqueda (S6)
MARGEN_ESQUIVE = (
    0.8  # una unidad quieta se aparta si una tormenta llega a radio + margen
)
MAX_ESPERA_TORMENTA = (
    10  # decisiones seguidas que una unidad espera a que pase una tormenta
)
TRAMOS_BUSQUEDA = (
    2  # tramos que recorre un rover ocioso en cada ronda de busqueda
)
RADIO_BUSQUEDA = (
    8  # radio del primer tramo; cada tramo siguiente suma PASO_BUSQUEDA
)
PASO_BUSQUEDA = 6
DESCANSO_BUSQUEDA = 300  # ticks entre dos rondas de busqueda de un mismo rover
BATERIA_BUSQUEDA = (
    65.0  # un rover ocioso solo sale a buscar con al menos esta bateria
)
BATERIA_VUELTA_OCIOSO = (
    42.0  # un rover ocioso lejos de la base vuelve a recargar bajo esto
)
MAX_CONSUMO = (
    8  # decisiones seguidas en "consumiendo" antes de soltar el resto
)
GAJOS = 5  # sectores en que se parte el abanico de patrulla
RADIO_PATRULLA = 22  # tope del radio de patrulla de los exploradores
TURNO_PATRULLA = 300  # ticks que dura el turno de patrulla antes del relevo

# S4 - subastas
FACTOR_SUBASTA = (
    1.8  # una zona se subasta si vale valor_min por este factor; si no, INFORM
)
PLAZO_SUBASTA = 5  # ticks que el iniciador espera propuestas de rovers
PLAZO_RECARGA = 2  # idem entre drones de recarga, que actuan todos los ticks

# Interruptores para los experimentos del informe: cada uno apaga una pieza
# para medir cuanto aporta. En la entrega van todos en True y EXP_PESOS en 1.
#   EXP_OLVIDO            S1: borrar las vetas que se ven agotadas
#   EXP_EVITAR_TORMENTAS  S2: esperar, rodear y esquivar tormentas
#   EXP_PESOS             S2: multiplicadores de w1..w4 para la calibracion
#   EXP_FILTROS_MENSAJES  S3: deduplicacion, enfriamiento y umbral de valor
#   EXP_SUBASTAS          S4: subasta implicita y CNP explicito
#   EXP_VOTACION          S5: eleccion periodica (en False queda la inicial)
EXP_OLVIDO = True
EXP_EVITAR_TORMENTAS = True
EXP_PESOS = (1.0, 1.0, 1.0, 1.0)
EXP_FILTROS_MENSAJES = True
EXP_SUBASTAS = True
EXP_VOTACION = True

VECINOS = [
    (-1, -1),
    (0, -1),
    (1, -1),
    (-1, 0),
    (1, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
]


def cheb(a: Pos, b: Pos) -> int:
    """Distancia Chebyshev: los pasos reales, porque la diagonal cuesta lo
    mismo.
    """
    dx = a[0] - b[0]
    dy = a[1] - b[1]
    return max(dx if dx >= 0 else -dx, dy if dy >= 0 else -dy)


def indice_de(uid: str) -> int:
    """Numero al final del id ('A_rover_17' -> 17)."""
    try:
        return int(uid.rsplit("_", 1)[-1])
    except ValueError:
        return sum(ord(c) for c in uid) % 30


def a_pos(valor: Any) -> Pos:
    """Convierte una posicion recibida por mensaje en una tupla de enteros."""
    return (int(valor[0]), int(valor[1]))


class EquipoPermafrost(EquipoBase):
    """Rovers, exploradores y recargadores coordinados por utilidad, CNP y
    votacion.
    """

    nombre = "Equipo - Permafrost"

    # =========================================================================
    # Arranque
    # =========================================================================
    def inicializar(
        self, letra: str, base_pos: Pos, grid_size: Pos = (GRID_W, GRID_H)
    ) -> None:
        """Prepara el estado del equipo al iniciar (o reiniciar) una partida.
        """
        super().inicializar(letra, base_pos, grid_size)
        self.nombre = "Equipo %s - Permafrost" % letra
        self.w, self.h = grid_size
        # Sentido "hacia adentro" del mapa desde nuestra esquina
        self.sx = 1 if base_pos[0] < self.w // 2 else -1
        self.sy = 1 if base_pos[1] < self.h // 2 else -1
        # S5: politica vigente y urna (no transportan posiciones ni hallazgos)
        self.politica = POLITICA_INICIAL
        self.urna: Dict[str, Tuple[str, ...]] = {}
        self.ultima_eleccion = 0
        self.historial_votos: List[Dict[str, Any]] = []
        self.ticks_politica: Dict[str, int] = {}
        # S6: perfilado
        self._tick = -1
        self._ms_tick = 0.0
        self.ms_por_tick: List[float] = []
        self.contadores: Dict[str, int] = {}
        self._conv = 0
        self._cache_centros: Tuple[Any, int, Any] = (None, -1, [])

    def _cuenta(self, clave: str, n: int = 1) -> None:
        """Suma a un contador de diagnostico (para los experimentos y el
        informe).
        """
        self.contadores[clave] = self.contadores.get(clave, 0) + n

    # =========================================================================
    # S6 - Punto de entrada: perfilado y red de seguridad
    # =========================================================================
    def decidir_unidad(
        self, unidad: UnidadVista, percepcion: Percepcion, api: Any
    ) -> Accion:
        """Decide la accion de una unidad; mide el turno y nunca deja escapar
        un error.
        """
        t0 = time.perf_counter()
        if percepcion.tick != self._tick:
            if self._tick >= 0:
                self.ms_por_tick.append(self._ms_tick)
            self._tick = percepcion.tick
            self._ms_tick = 0.0
            self.ticks_politica[self.politica] = (
                self.ticks_politica.get(self.politica, 0) + 1
            )
            self._votar_si_toca(percepcion.tick)
        try:
            accion = self._decidir(unidad, percepcion, api)
        except Exception:  # una excepcion aqui tumbaria el simulador entero
            self._cuenta("errores")
            accion = self._accion_segura(unidad)
        self._ms_tick += (time.perf_counter() - t0) * 1000.0
        return accion

    def _accion_segura(self, u: UnidadVista) -> Accion:
        """Lo minimo que respeta las mecanicas obligatorias si la logica falla.
        """
        if (
            u.tipo == "rover"
            and u.bateria <= UMBRAL_BATERIA_BAJA
            and u.estado == "activo"
        ):
            return ("solicitar_recarga",)
        return ("esperar",)

    def estadisticas(self) -> Dict[str, Any]:
        """Resumen para el arnes de pruebas y el informe. El simulador no lo
        usa.
        """
        orden = sorted(self.ms_por_tick + [self._ms_tick])
        n = len(orden)

        def pct(p: float) -> float:
            """Percentil p de los tiempos por turno."""
            return round(orden[min(n - 1, int(p * n))], 3)

        return {
            "contadores": dict(self.contadores),
            "politica_final": self.politica,
            "elecciones": len(self.historial_votos),
            "desempates": {
                metodo: sum(
                    1 for v in self.historial_votos if v["desempate"] == metodo
                )
                for metodo in ("copeland", "borda", "orden_fijo", "inercia")
            },
            "ticks_por_politica": dict(self.ticks_politica),
            "votos": self.historial_votos[:40],
            "cambios_de_politica": [
                (v["tick"], v["ganadora"])
                for v in self.historial_votos
                if v["cambio"]
            ],
            "ms": {
                "media": round(sum(orden) / n, 3),
                "p95": pct(0.95),
                "p99": pct(0.99),
                "max": pct(1.0),
            },
        }

    def _decidir(self, u: UnidadVista, p: Percepcion, api: Any) -> Accion:
        """Ciclo de una unidad: percibir, leer mensajes, opinar y actuar segun
        su rol.
        """
        if u.estado == "muerto":
            return ("esperar",)
        m = self._memoria_de(u)
        self._percibir(u, p, m)
        self._leer_mensajes(u, p, api, m)
        self._depositar_papeleta(u, p, m)
        if u.tipo == "rover":
            return self._rover(u, p, api, m)
        if u.tipo == "dron_explorador":
            return self._explorador(u, p, api, m)
        return self._recargador(u, p, api, m)

    # =========================================================================
    # S1 - Percepcion y memoria espacial (una por unidad)
    # =========================================================================
    def _memoria_de(self, u: UnidadVista) -> Memoria:
        """Devuelve la memoria privada de la unidad, creandola la primera vez.
        """
        m = self.memoria.get(u.id)
        if m is None:
            idx = indice_de(u.id)
            inicial = {
                "rover": OCIOSO,
                "dron_explorador": RETORNANDO_BASE,
            }.get(u.tipo, EN_ESPERA)
            m = {
                "estado": inicial,
                "idx": idx,
                # (x, y) -> (cantidad, tick de ultima observacion)
                "hielo": {},
                "restos": {},  # id -> (pos, combustible, tick)
                # [(x, y, radio, tick, vx, vy)] vistas hace poco
                "tormentas": [],
                # [(tick, x, y)] trayectoria reciente de tormentas
                "rastro": [],
                "ultimo_hielo": 0,  # ultimo tick en que vio o supo de hielo
                "objetivo": None,  # ("hielo", pos) | ("restos", id, pos)
                "revisar": 0,  # tick en que se vuelve a evaluar el objetivo
                # tarea adjudicada por CNP (ver _aceptar_contrato)
                "contrato": None,
                # (conversation_id, vence): propuesta enviada sin respuesta
                "oferta": None,
                # conversation_id -> subasta abierta por esta unidad
                "subastas": {},
                # conversation_id -> (ontologia, tarea, tick) ya adjudicada
                "adjudicadas": {},
                # clave de zona -> tick del ultimo reporte (S3)
                "reportes": {},
                # restos que esta unidad ya no intentara consumir
                "vetados": set(),
                # decisiones seguidas esperando a que pase una tormenta
                "paciencia": 0,
                # rover
                "tramo": 0,  # tramo actual de la ronda de busqueda
                "busca_desde": (idx % 6)
                * 8,  # tick desde el que puede salir a buscar
                "consumo": 0,  # decisiones seguidas en estado "consumiendo"
                "baja": False,  # ya entro a la mecanica de bateria baja
                "ping": -999,  # tick del ultimo REQUEST de recarga
                # pedidos de recarga seguidos sin haber sido recargado
                "pings": 0,
                "agree": -999,  # tick del ultimo AGREE recibido
                # explorador
                "ruta": [],  # puntos de patrulla pendientes
                "salidas": 0,  # gajos patrullados
                "a_base": False,  # volviendo a recargar
                # recargador
                "rescate": None,  # {"rover", "pos", "desde", "conv"}
            }
            self.memoria[u.id] = m
        return m

    def _percibir(self, u: UnidadVista, p: Percepcion, m: Memoria) -> None:
        """Actualiza las creencias con lo visible y olvida lo que ya no es
        cierto.
        """
        tick = p.tick
        radio = VISION.get(u.tipo, 5)
        ux, uy = u.pos

        # Hielo: indexado por coordenada, con cantidad y tick de observacion.
        hielo = m["hielo"]
        visibles = set()
        for hx, hy, cant in p.hielo_visible:
            hielo[(hx, hy)] = (cant, tick)
            visibles.add((hx, hy))
        if visibles:
            m["ultimo_hielo"] = tick
        # Olvido por revisita: una celda recordada, dentro de la vision y sin
        # hielo, esta agotada.
        # Olvido por tiempo: lo no revisitado hace mucho se borra (su confianza
        # ya habia decaido).
        caducas = [
            c
            for c, (_, visto) in hielo.items()
            if (
                EXP_OLVIDO
                and c not in visibles
                and abs(c[0] - ux) <= radio
                and abs(c[1] - uy) <= radio
            )
            or tick - visto > OLVIDO_HIELO
        ]
        for c in caducas:
            del hielo[c]
        if u.pos in hielo and u.pos not in visibles:
            # Parado encima y sin hielo: agotada, diga lo que diga EXP_OLVIDO.
            del hielo[u.pos]

        # Restos: por id, con su coordenada y combustible. Mismo olvido que el
        # hielo.
        restos = m["restos"]
        ids_visibles = set()
        for r in p.restos_visible:
            restos[r["id"]] = (
                a_pos(r["pos"]),
                int(r.get("combustible", 10)),
                tick,
            )
            ids_visibles.add(r["id"])
        idos = [
            rid
            for rid, (pos, _, visto) in restos.items()
            if (
                rid not in ids_visibles
                and abs(pos[0] - ux) <= radio
                and abs(pos[1] - uy) <= radio
            )
            or tick - visto > OLVIDO_HIELO
        ]
        for rid in idos:
            del restos[rid]

        self._percibir_tormentas(p, m)

    def _percibir_tormentas(self, p: Percepcion, m: Memoria) -> None:
        """Guarda cada tormenta visible con su velocidad estimada y recuerda
        las recientes.

        La velocidad sale de comparar con la observacion anterior mas cercana.
        Las tormentas que dejan de verse se conservan MEMORIA_TORMENTA ticks,
        proyectadas con esa velocidad.
        """
        tick = p.tick
        previas: List[Tormenta] = m["tormentas"]
        nuevas: List[Tormenta] = []
        usadas = set()
        for tx, ty, radio in p.tormentas_visible:
            vx = vy = 0.0
            mejor = None
            for i, t in enumerate(previas):
                d = math.hypot(tx - t[0], ty - t[1])
                if (
                    i not in usadas
                    and d <= 4.0
                    and (mejor is None or d < mejor[0])
                ):
                    mejor = (d, i)
            if mejor is not None:
                t = previas[mejor[1]]
                usadas.add(mejor[1])
                dt = tick - t[3]
                if dt > 0:
                    vx, vy = (tx - t[0]) / dt, (ty - t[1]) / dt
                else:
                    vx, vy = t[4], t[5]
            nuevas.append((tx, ty, radio, tick, vx, vy))
            m["rastro"].append((tick, round(tx, 1), round(ty, 1)))
        for i, t in enumerate(previas):
            if i not in usadas and tick - t[3] <= MEMORIA_TORMENTA:
                nuevas.append(t)
        m["tormentas"] = nuevas
        if len(m["rastro"]) > RASTRO_TORMENTAS:
            del m["rastro"][:-RASTRO_TORMENTAS]

    def _confianza(self, tick: int, visto: int) -> float:
        """Decaimiento exponencial: una veta vista hace VIDA_MEDIA_HIELO ticks
        vale la mitad.
        """
        return 0.5 ** ((tick - visto) / VIDA_MEDIA_HIELO)

    # =========================================================================
    # S2 - Navegacion: paso directo, espera y A* acotado sobre el riesgo de
    # tormentas
    # =========================================================================
    def _centros(
        self, tormentas: List[Tormenta]
    ) -> List[Tuple[float, float, float]]:
        """Posicion estimada de cada tormenta un tick adelante, segun su
        velocidad.

        Es el campo de riesgo de la unidad: se calcula una sola vez por
        decision y lo reutilizan el paso, el A*, el esquive y la utilidad de
        ese mismo turno.
        """
        cache = self._cache_centros
        if cache[0] is tormentas and cache[1] == self._tick:
            return cache[2]  # ya calculado para esta unidad en este turno
        salida = []
        for tx, ty, radio, visto, vx, vy in tormentas:
            dt = self._tick - visto + 1
            salida.append((tx + vx * dt, ty + vy * dt, radio))
        self._cache_centros = (tormentas, self._tick, salida)
        return salida

    def _riesgo(
        self, celda: Pos, centros: List[Tuple[float, float, float]]
    ) -> float:
        """0 fuera de toda tormenta; crece hacia el centro. El margen cubre el
        error de estima.
        """
        peor = 0.0
        for tx, ty, radio in centros:
            d = math.hypot(celda[0] - tx, celda[1] - ty)
            limite = radio + 1.5
            if d <= limite:
                peor = max(peor, 1.0 + (limite - d) / limite)
        return peor

    def _paso_directo(self, origen: Pos, destino: Pos) -> Pos:
        """Paso en linea recta (diagonal incluida) hacia el destino."""
        dx = (destino[0] > origen[0]) - (destino[0] < origen[0])
        dy = (destino[1] > origen[1]) - (destino[1] < origen[1])
        return (dx, dy)

    def _astar(
        self,
        origen: Pos,
        destino: Pos,
        centros: List[Tuple[float, float, float]],
    ) -> Optional[Pos]:
        """A* con tope de expansiones; devuelve el primer paso del mejor camino
        hallado.

        Pisar tormenta cuesta 5 (como en el simulador) mas la exposicion. Si el
        tope se agota antes de llegar, se toma el camino al nodo mas cercano al
        destino.
        """
        abiertos: List[Tuple[float, int, Pos]] = [
            (float(cheb(origen, destino)), 0, origen)
        ]
        costo = {origen: 0.0}
        primer_paso: Dict[Pos, Pos] = {}
        mejor, mejor_h, mejor_g = origen, cheb(origen, destino), 0.0
        expandidos = 0
        orden = 0
        while abiertos and expandidos < MAX_NODOS_ASTAR:
            _, _, actual = heapq.heappop(abiertos)
            expandidos += 1
            h_actual = cheb(actual, destino)
            if h_actual < mejor_h or (
                h_actual == mejor_h and costo[actual] < mejor_g
            ):
                mejor, mejor_h, mejor_g = actual, h_actual, costo[actual]
            if actual == destino:
                break
            for dx, dy in VECINOS:
                nx, ny = actual[0] + dx, actual[1] + dy
                if not (0 <= nx < self.w and 0 <= ny < self.h):
                    continue
                vecino = (nx, ny)
                riesgo = self._riesgo(vecino, centros)
                g = (
                    costo[actual]
                    + 1.0
                    + (4.0 + 3.0 * riesgo if riesgo > 0.0 else 0.0)
                )
                if g < costo.get(vecino, 1e9):
                    costo[vecino] = g
                    primer_paso[vecino] = (
                        (dx, dy) if actual == origen else primer_paso[actual]
                    )
                    orden += 1
                    heapq.heappush(
                        abiertos, (g + cheb(vecino, destino), orden, vecino)
                    )
        return primer_paso.get(mejor)

    def _mover(self, u: UnidadVista, destino: Pos, m: Memoria) -> Accion:
        """Un paso hacia el destino.

        Dentro o al borde de una tormenta conviene esperar: un paso ahi cuesta
        5 %, y la tormenta pasa (o empuja a la unidad hacia afuera) en pocos
        ticks. Solo si la espera se agota se busca un rodeo con A*. Asi la
        busqueda, que es lo caro, corre pocas veces por turno (S6).
        """
        if u.pos == destino:
            return ("esperar",)
        dx, dy = self._paso_directo(u.pos, destino)
        if m["tormentas"] and EXP_EVITAR_TORMENTAS:
            centros = self._centros(m["tormentas"])
            siguiente = (u.pos[0] + dx, u.pos[1] + dy)
            if u.en_tormenta or self._riesgo(siguiente, centros) > 0.0:
                if m["paciencia"] < MAX_ESPERA_TORMENTA:
                    m["paciencia"] += 1
                    self._cuenta("esperas_por_tormenta")
                    return ("esperar",)
                self._cuenta("astar")
                dx, dy = self._astar(u.pos, destino, centros) or (dx, dy)
            else:
                m["paciencia"] = 0
        else:
            m["paciencia"] = 0
        self._cuenta("pasos_" + m["estado"])
        return ("mover", dx, dy)

    def _riesgo_de_ruta(self, origen: Pos, destino: Pos, m: Memoria) -> float:
        """Fraccion de la recta origen->destino que cruza tormentas
        (muestreada, sin A*).
        """
        if not m["tormentas"] or not EXP_EVITAR_TORMENTAS:
            return 0.0
        centros = self._centros(m["tormentas"])
        muestras = min(max(1, cheb(origen, destino)), 8)
        dentro = 0
        for i in range(1, muestras + 1):
            f = i / muestras
            celda = (
                int(round(origen[0] + (destino[0] - origen[0]) * f)),
                int(round(origen[1] + (destino[1] - origen[1]) * f)),
            )
            if self._riesgo(celda, centros) > 0.0:
                dentro += 1
        return dentro / muestras

    def _esquivar(self, u: UnidadVista, m: Memoria) -> Optional[Accion]:
        """Para quien esta quieto: apartarse de una tormenta que se le viene
        encima.

        Un paso lateral (1 %) sale mas barato que el pulso (3 % y empuje). Ya
        adentro no se mueve: cada paso costaria 5 %.
        """
        if u.en_tormenta or not m["tormentas"] or not EXP_EVITAR_TORMENTAS:
            return None
        ux, uy = u.pos
        cerca = None
        for tx, ty, radio in self._centros(m["tormentas"]):
            d = math.hypot(ux - tx, uy - ty)
            if d <= radio + MARGEN_ESQUIVE and (cerca is None or d < cerca[0]):
                cerca = (d, tx, ty)
        if cerca is None:
            return None
        mejor, mejor_d = None, cerca[0]
        for dx, dy in VECINOS:
            nx, ny = ux + dx, uy + dy
            if 0 <= nx < self.w and 0 <= ny < self.h:
                d = math.hypot(nx - cerca[1], ny - cerca[2])
                if d > mejor_d:
                    mejor, mejor_d = (dx, dy), d
        if mejor is None:
            return None
        self._cuenta("esquives")
        return ("mover", mejor[0], mejor[1])

    def _quieto(self, u: UnidadVista, m: Memoria) -> Accion:
        """Esperar sin gastar, salvo que haya que esquivar una tormenta."""
        return self._esquivar(u, m) or ("esperar",)

    def _punto(self, angulo: float, radio: float) -> Pos:
        """Celda a `radio` de la base en la direccion `angulo` del abanico
        hacia adentro.
        """
        x = self.base_pos[0] + self.sx * math.cos(angulo) * radio
        y = self.base_pos[1] + self.sy * math.sin(angulo) * radio
        return (
            int(min(self.w - 2, max(1, x))),
            int(min(self.h - 2, max(1, y))),
        )

    # =========================================================================
    # S2 - Utilidad multi-atributo  U(s,a) = w1*g - w2*c + w3*o - w4*r
    # =========================================================================
    def _utilidad(
        self, pol: Dict[str, Any], g: float, c: float, o: float, r: float
    ) -> float:
        """U(s,a) con los pesos de la politica vigente. Todos los atributos van
        en [0, 1].

        g: hielo que se ganaria / 5. c: pasos extra / 40. o: combustible
        aprovechable / 20. r: fraccion de la ruta bajo tormenta.
        """
        w1, w2, w3, w4 = [w * k for w, k in zip(pol["w"], EXP_PESOS)]
        return w1 * g - w2 * c + w3 * o - w4 * r

    def _utilidad_hielo(
        self,
        u: UnidadVista,
        celda: Pos,
        cantidad: float,
        visto: int,
        m: Memoria,
        pol: Dict[str, Any],
    ) -> float:
        """Utilidad de ir a extraer a `celda`: ganancia descontada por
        antiguedad del dato.
        """
        libre = u.capacidad - u.carga
        g = min(libre, cantidad) * self._confianza(self._tick, visto) / 5.0
        # Costo marginal: cuanto alarga el viaje de vuelta a base pasar por la
        # celda.
        extra = (
            cheb(u.pos, celda)
            + cheb(celda, self.base_pos)
            - cheb(u.pos, self.base_pos)
        )
        return self._utilidad(
            pol, g, extra / 40.0, 0.0, self._riesgo_de_ruta(u.pos, celda, m)
        )

    def _utilidad_restos(
        self,
        u: UnidadVista,
        pos: Pos,
        combustible: int,
        m: Memoria,
        pol: Dict[str, Any],
        hay_critico: bool,
    ) -> float:
        """Utilidad de ir a consumir un resto: lo que recargaria (a si mismo o
        a un aliado).
        """
        aprovechable = (
            combustible if hay_critico else min(combustible, 100.0 - u.bateria)
        )
        c = 2.0 * cheb(u.pos, pos) / 40.0
        return self._utilidad(
            pol,
            0.0,
            c,
            aprovechable / 20.0,
            self._riesgo_de_ruta(u.pos, pos, m),
        )

    def _alcanza_bateria(self, u: UnidadVista, destino: Pos) -> bool:
        """Dice si la unidad llega al destino y vuelve a la base sin caer al 25
        %.
        """
        pasos = cheb(u.pos, destino) + cheb(destino, self.base_pos)
        return u.bateria - 1.15 * pasos >= UMBRAL_BATERIA_BAJA + MARGEN_BATERIA

    def _gana_subasta_implicita(
        self, u: UnidadVista, destino: Pos, p: Percepcion
    ) -> bool:
        """S4 sin mensajes: entre los rovers que se ven, la tarea es del mas
        cercano.

        Cada rover compara su distancia a la tarea con la de los aliados que ve
        (empate: menor id) y cede si alguno esta mas cerca, sin gastar bateria.
        No se cede a un aliado detenido ni a uno con bateria baja, que no
        podria ir. Limite conocido: el aliado mas cercano puede no conocer la
        veta o ir lleno, y entonces nadie la toma en esa ronda.
        """
        if not EXP_SUBASTAS:
            return True
        mia = (cheb(u.pos, destino), u.id)
        for a in p.aliados_visible:
            if (
                a["tipo"] != "rover"
                or a["id"] == u.id
                or a["estado"] != "activo"
            ):
                continue
            if a["bateria"] <= UMBRAL_BATERIA_BAJA + 10.0:
                continue
            if (cheb(a_pos(a["pos"]), destino), a["id"]) < mia:
                return False
        return True

    def _aliado_critico(self, u: UnidadVista, p: Percepcion) -> Optional[str]:
        """Un rover aliado visible detenido por bateria: candidato a recibir el
        combustible.
        """
        for a in p.aliados_visible:
            if (
                a["id"] != u.id
                and a["tipo"] == "rover"
                and a["estado"] == "esperando_recarga"
            ):
                return a["id"]
        return None

    def _elegir_objetivo(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> Optional[Tuple[Any, ...]]:
        """Evalua U(s,a) sobre las vetas y restos que esta unidad conoce y
        devuelve el mejor.

        La alternativa "retornar a base" vale la utilidad de reserva de la
        politica (`umbral_u`): un objetivo solo se elige si la supera. Un
        contrato ganado por CNP tiene prioridad mientras siga siendo cumplible.
        """
        pol = POLITICAS[self.politica]
        por_contrato = self._objetivo_de_contrato(u, p, api, m)
        if por_contrato is not None:
            return por_contrato

        mejor = None
        mejor_u = pol["umbral_u"]
        if u.carga < u.capacidad:
            cercanas = sorted(
                m["hielo"].items(), key=lambda kv: cheb(u.pos, kv[0])
            )[:14]
            for celda, (cant, visto) in cercanas:
                if cheb(celda, self.base_pos) > pol["radio_max"]:
                    continue
                # Una veta vale por ella y por lo que tiene al lado.
                grupo = cant + 0.5 * sum(
                    c2
                    for otra, (c2, _) in cercanas
                    if otra != celda and cheb(otra, celda) <= 2
                )
                # Si un solo rover la vacia, va el que gana la subasta
                # implicita.
                if grupo <= u.capacidad and not self._gana_subasta_implicita(
                    u, celda, p
                ):
                    self._cuenta("cedidas_sin_mensaje")
                    continue
                if not self._alcanza_bateria(u, celda):
                    continue
                valor = self._utilidad_hielo(u, celda, grupo, visto, m, pol)
                if valor > mejor_u:
                    mejor_u, mejor = valor, ("hielo", celda)

        if u.carga == 0 and m["restos"]:
            hay_critico = self._aliado_critico(u, p) is not None
            for rid, (pos, combustible, _) in m["restos"].items():
                if rid in m["vetados"] or not self._alcanza_bateria(u, pos):
                    continue
                if not self._gana_subasta_implicita(u, pos, p):
                    continue  # un resto lo consume un solo rover
                valor = self._utilidad_restos(
                    u, pos, combustible, m, pol, hay_critico
                )
                if valor > mejor_u:
                    mejor_u, mejor = valor, ("restos", rid, pos)
        return mejor

    # =========================================================================
    # S2 - FSM del rover
    #   OCIOSO -> EXPLORANDO -> RECOLECTANDO -> RETORNANDO -> OCIOSO
    # cualquiera -> ESPERANDO_RECARGA (bateria <= 25 %) -> OCIOSO al ser
    # recargado
    #   OCIOSO/EXPLORANDO -> CONSUMIENDO_CARRONA -> OCIOSO
    # =========================================================================
    def _rover(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> Accion:
        """Un turno de rover: bateria baja, carrona en curso, retorno,
        extraccion u objetivo.
        """
        pol = POLITICAS[self.politica]
        tick = p.tick

        # --- ESPERANDO_RECARGA: mecanica obligatoria con bateria <= 25 % ---
        if u.estado == "esperando_recarga" or u.bateria <= UMBRAL_BATERIA_BAJA:
            if not m["baja"]:
                m["baja"] = True
                m["ping"], m["pings"] = (
                    -999,
                    0,
                )  # el pedido urgente sale ya, sin retroceso
            m["estado"] = ESPERANDO_RECARGA
            m["objetivo"] = None
            self._pedir_recarga(u, p, api, m, urgente=True)
            return (
                ("solicitar_recarga",)
                if u.estado != "esperando_recarga"
                else ("esperar",)
            )
        m["baja"] = False
        if u.bateria >= 90.0:
            m["pings"] = 0

        # --- CONSUMIENDO_CARRONA en curso ---
        if u.estado == "consumiendo":
            m["estado"] = CONSUMIENDO_CARRONA
            m["consumo"] += 1
            if m["consumo"] <= MAX_CONSUMO:
                return ("esperar",)
            # El consumo no avanza (el simulador lo pausa en ciertos casos):
            # soltar el resto.
            m["vetados"].update(m["restos"].keys())
            m["objetivo"] = None
            self._cuenta("consumos_abandonados")
            dx, dy = self._paso_directo(u.pos, self.base_pos)
            return (
                ("mover", dx, dy)
                if (dx, dy) != (0, 0)
                else ("mover", self.sx, self.sy)
            )
        m["consumo"] = 0

        # --- Recarga preventiva en la base (pedido ya hecho): sigue en
        # ESPERANDO_RECARGA ---
        if m["estado"] == ESPERANDO_RECARGA:
            if (
                u.bateria >= 90.0
                or tick - m["ping"] > 40
                or not p.base_aliada_cerca
            ):
                m["estado"] = OCIOSO
            else:
                return self._quieto(u, m)

        # --- RETORNANDO: lleno, o ultimos 30 s con carga ---
        if u.carga >= u.capacidad or (p.fase_final and u.carga > 0):
            return self._retornar(u, p, api, m)
        if p.fase_final:
            # Ya no queda hielo en el mapa: moverse solo gasta bateria.
            m["estado"] = OCIOSO
            return self._quieto(u, m)

        # --- RECOLECTANDO: extraer si esta sobre hielo ---
        if u.pos in m["hielo"]:
            m["estado"] = RECOLECTANDO
            if m["objetivo"] is not None and m["objetivo"][0] == "hielo":
                m["objetivo"] = None  # llego: ya no es un viaje pendiente
            self._cuenta("extracciones")
            return ("extraer",)

        # --- Elegir o mantener objetivo segun U(s,a) ---
        objetivo = m["objetivo"]
        if objetivo is not None:
            vigente = (
                objetivo[0] == "hielo" and objetivo[1] in m["hielo"]
            ) or (objetivo[0] == "restos" and objetivo[1] in m["restos"])
            if not vigente and objetivo[0] == "hielo":
                self._cuenta(
                    "viajes_en_vano"
                )  # la veta se agoto antes de llegar
            if not vigente or tick >= m["revisar"]:
                objetivo = None
        if objetivo is None:
            objetivo = self._elegir_objetivo(u, p, api, m)
            m["objetivo"] = objetivo
            # Desfase por indice: los rovers no reevaluan todos en el mismo
            # turno (S6).
            m["revisar"] = tick + 6 + 2 * (m["idx"] % 4)

        if objetivo is not None and objetivo[0] == "hielo":
            m["estado"] = RECOLECTANDO
            return self._mover(u, objetivo[1], m)
        if objetivo is not None and objetivo[0] == "restos":
            return self._ir_a_restos(u, p, m, objetivo[1], objetivo[2])

        # --- Sin objetivo que supere la utilidad de reserva ---
        if u.carga > 0:
            return self._retornar(u, p, api, m)
        # Recarga preventiva: en la base, vacio y con bateria bajo el umbral de
        # la politica.
        if p.base_aliada_cerca and u.bateria < pol["bat_pit"]:
            if self._pedir_recarga(u, p, api, m, urgente=False):
                m["estado"] = ESPERANDO_RECARGA
                return self._quieto(u, m)
        return self._buscar_o_esperar(u, p, m, pol)

    def _ir_a_restos(
        self, u: UnidadVista, p: Percepcion, m: Memoria, rid: str, pos: Pos
    ) -> Accion:
        """CONSUMIENDO_CARRONA: acercarse al resto y consumirlo, para si o para
        un aliado.
        """
        m["estado"] = CONSUMIENDO_CARRONA
        if cheb(u.pos, pos) > 1:
            return self._mover(u, pos, m)
        m["objetivo"] = None
        if m["contrato"] is not None and m["contrato"]["ont"] == ONT_RESTOS:
            m["contrato"] = None
        self._cuenta("carronas")
        # Transferir si a esta unidad le sobra bateria y hay un aliado detenido
        # a la vista;
        # si no, el combustible es para ella.
        critico = self._aliado_critico(u, p)
        if critico is not None and u.bateria >= 70.0:
            self._cuenta("carronas_transferidas")
            return ("consumir_restos", rid, ("transferir", critico))
        return ("consumir_restos", rid, "propia")

    def _retornar(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> Accion:
        """RETORNANDO: volver a la base y depositar. Al salir lleno avisa del
        hielo que deja.
        """
        if (
            m["estado"] != RETORNANDO
            and u.carga >= u.capacidad
            and not p.fase_final
        ):
            self._avisar_sobrante(u, p, api, m)
        m["estado"] = RETORNANDO
        m["objetivo"] = None
        if p.base_aliada_cerca:
            self._cuenta("depositos")
            self._cuenta("hielo_depositado", u.carga)
            return ("depositar",)
        return self._mover(u, self.base_pos, m)

    def _buscar_o_esperar(
        self, u: UnidadVista, p: Percepcion, m: Memoria, pol: Dict[str, Any]
    ) -> Accion:
        """EXPLORANDO: el rover ocioso busca hielo en rondas; entre rondas
        queda OCIOSO.

        Una ronda son TRAMOS_BUSQUEDA tramos en abanico, cada uno mas lejos y
        en otra direccion (segun el indice del rover, para que no vayan todos
        al mismo sitio). Si encuentra hielo o le llega un aviso, deja de buscar
        y recolecta. Tras la ronda descansa DESCANSO_BUSQUEDA ticks, porque
        repetir el mismo recorrido no descubre nada nuevo.
        """
        tick = p.tick
        if u.bateria >= BATERIA_BUSQUEDA and tick >= m["busca_desde"]:
            angulo = ((m["idx"] * 0.6180339887 + m["tramo"] * 0.29) % 1.0) * (
                math.pi / 2.0
            )
            radio = min(
                pol["radio_max"], RADIO_BUSQUEDA + PASO_BUSQUEDA * m["tramo"]
            )
            destino = self._punto(angulo, radio)
            if cheb(u.pos, destino) > 2 and self._alcanza_bateria(u, destino):
                m["estado"] = EXPLORANDO
                return self._mover(u, destino, m)
            m["tramo"] += 1
            if m["tramo"] >= TRAMOS_BUSQUEDA or not self._alcanza_bateria(
                u, destino
            ):
                m["tramo"] = 0
                m["busca_desde"] = tick + DESCANSO_BUSQUEDA
                self._cuenta("rondas_de_busqueda")
        m["estado"] = OCIOSO
        # Lejos de la base y con poca bateria: volver para la recarga
        # preventiva.
        if u.bateria < BATERIA_VUELTA_OCIOSO and not p.base_aliada_cerca:
            return self._mover(u, self.base_pos, m)
        return self._quieto(u, m)

    # =========================================================================
    # S3 - Mensajeria FIPA-ACL con control de costo
    # =========================================================================
    def _acl(
        self,
        performative: str,
        sender: str,
        conversation_id: str,
        ontology: str,
        content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Arma un mensaje con los cinco campos FIPA-ACL que usa el equipo."""
        return {
            "performative": performative,
            "sender": sender,
            "conversation_id": conversation_id,
            "ontology": ontology,
            "content": content,
        }

    def _nueva_conversacion(self, uid: str, tick: int) -> str:
        """Identificador unico de conversacion: emisor, tick y un contador."""
        self._conv += 1
        return "%s-%d-%d" % (uid, tick, self._conv)

    def _enviar(self, api: Any, destino: str, msg: Dict[str, Any]) -> bool:
        """Envia un mensaje ACL a una unidad concreta (unicast) y lo
        contabiliza.
        """
        ok = bool(api.enviar_mensaje(destino, msg["performative"], msg))
        if ok:
            self._cuenta("msg_" + msg["performative"])
            self._cuenta("msg_ont_" + msg["ontology"])
        return ok

    def _informar_a_rover_ocioso(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        ontologia: str,
        contenido: Dict[str, Any],
        pos: Pos,
    ) -> bool:
        """INFORM dirigido al rover ocioso mas cercano a `pos` (lo elige el
        simulador).
        """
        msg = self._acl(
            INFORM,
            u.id,
            self._nueva_conversacion(u.id, p.tick),
            ontologia,
            contenido,
        )
        if api.enviar_a_rover_ocioso_cercano(INFORM, msg, pos_ref=pos) is None:
            return False
        self._cuenta("msg_" + INFORM)
        self._cuenta("msg_ont_" + ontologia)
        return True

    def _puede_reportar(
        self, m: Memoria, clave: Any, tick: int, cooldown: int = 35
    ) -> bool:
        """Deduplicacion: una zona no se vuelve a reportar hasta que pase el
        enfriamiento.
        """
        if not EXP_FILTROS_MENSAJES:
            return True
        ultimo = m["reportes"].get(clave, -(10**6))
        if tick - ultimo >= cooldown:
            m["reportes"][clave] = tick
            return True
        self._cuenta("reportes_filtrados")
        return False

    def _cede_reporte(self, u: UnidadVista, p: Percepcion, pos: Pos) -> bool:
        """Deduplicacion entre drones: si otro dron en vuelo tambien ve `pos`,
        reporta uno solo.

        Reporta el de menor id; los demas callan. Los drones estacionados en la
        base no reportan (ver `_reportar_hallazgos`), asi que no cuentan.
        """
        if not EXP_FILTROS_MENSAJES:
            return False
        for a in p.aliados_visible:
            if a["tipo"] == "rover" or a["id"] >= u.id:
                continue
            otro = a_pos(a["pos"])
            if cheb(otro, self.base_pos) > 2 and cheb(otro, pos) <= VISION.get(
                a["tipo"], 7
            ):
                return True
        return False

    def _avisar_sobrante(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> None:
        """Un rover que se va lleno y deja hielo a la vista avisa a UN rover
        ocioso (INFORM).
        """
        pol = POLITICAS[self.politica]
        celdas = [
            (hx, hy, c)
            for hx, hy, c in p.hielo_visible
            if cheb((hx, hy), u.pos) <= 3
        ]
        if sum(c for _, _, c in celdas) < pol["valor_min"]:
            return
        otros = sum(
            1
            for a in p.aliados_visible
            if a["tipo"] == "rover"
            and a["id"] != u.id
            and a["estado"] == "activo"
        )
        clave = ("sobrante", u.pos[0] // 5, u.pos[1] // 5)
        if otros >= 2 or not self._puede_reportar(
            m, clave, p.tick, pol["enfriamiento"]
        ):
            return
        mejor = max(celdas, key=lambda c: c[2])
        pos = (mejor[0], mejor[1])
        if self._informar_a_rover_ocioso(
            u, p, api, ONT_HIELO, {"pos": pos, "cantidad": mejor[2]}, pos
        ):
            self._cuenta("avisos_de_sobrante")

    def _pedir_recarga(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        urgente: bool,
    ) -> bool:
        """REQUEST de recarga al recargador disponible mas cercano.

        El primer pedido sale de inmediato. Insistir cuesta 1 % por intento
        entre emisor y receptor, asi que tras n pedidos sin respuesta la espera
        es min(320, 20 * 2^n) ticks: 40, 80, 160... Un AGREE la fija en 60 y un
        FAILURE la devuelve a 40.
        """
        tick = p.tick
        espera = (
            60 if tick - m["agree"] < 60 else min(320, 20 * (2 ** m["pings"]))
        )
        if tick - m["ping"] < espera:
            return True
        contenido = {
            "rover": u.id,
            "pos": u.pos,
            "bateria": round(u.bateria, 1),
            "urgente": urgente,
        }
        msg = self._acl(
            REQUEST,
            u.id,
            self._nueva_conversacion(u.id, tick),
            ONT_RECARGA,
            contenido,
        )
        if api.enviar_a_recargador_cercano(REQUEST, msg) is None:
            return False
        m["ping"] = tick
        m["pings"] += 1
        self._cuenta("msg_" + REQUEST)
        self._cuenta("msg_ont_" + ONT_RECARGA)
        return True

    def _leer_mensajes(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> None:
        """Procesa la bandeja. Un mensaje mal formado se descarta sin afectar a
        los demas.
        """
        for sobre in p.mensajes:
            self._cuenta("recibidos")
            try:
                msg = sobre.get("datos")
                if isinstance(msg, dict) and isinstance(
                    msg.get("content"), dict
                ):
                    self._procesar_mensaje(
                        u, p, api, m, msg, sobre.get("emisor_id")
                    )
                else:
                    self._cuenta("mensajes_descartados")
            except Exception:
                # Un contenido inesperado no debe costar el resto de la
                # bandeja.
                self._cuenta("mensajes_descartados")

    def _procesar_mensaje(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        msg: Dict[str, Any],
        emisor_real: Any,
    ) -> None:
        """Despacha un mensaje ACL segun su performativa y su ontologia."""
        perf = msg.get("performative")
        ont = msg.get("ontology")
        conv = msg.get("conversation_id")
        contenido = msg["content"]
        emisor = msg.get("sender") or emisor_real
        tick = p.tick

        if perf == INFORM and ont == ONT_HIELO:
            pos = a_pos(contenido["pos"])
            if contenido.get("agotado"):
                m["hielo"].pop(
                    pos, None
                )  # un aliado confirma que la veta se agoto
            else:
                m["hielo"][pos] = (int(contenido.get("cantidad", 1)), tick)
                m["ultimo_hielo"] = tick
        elif perf == INFORM and ont == ONT_RESTOS:
            m["restos"][contenido["id"]] = (
                a_pos(contenido["pos"]),
                int(contenido.get("combustible", 10)),
                tick,
            )
        elif perf == CFP:
            self._responder_cfp(u, p, api, m, emisor, conv, ont, contenido)
        elif perf == PROPOSE:
            if conv in m["subastas"]:
                m["subastas"][conv]["propuestas"].append(
                    (float(contenido.get("puja", 1e9)), emisor)
                )
        elif perf == ACCEPT_PROPOSAL:
            self._aceptar_contrato(u, p, api, m, emisor, conv, ont, contenido)
        elif perf == REJECT_PROPOSAL:
            if m["oferta"] is not None and m["oferta"][0] == conv:
                m["oferta"] = None
        elif (
            perf == REQUEST and ont == ONT_RECARGA and u.tipo == "dron_recarga"
        ):
            self._atender_request(u, p, api, m, conv, contenido)
        elif perf == AGREE and ont == ONT_RECARGA:
            m["agree"] = tick
        elif perf == FAILURE and ont == ONT_RECARGA:
            # Nadie puede venir ahora: se anula el AGREE y el retroceso vuelve
            # a su primer
            # escalon, para reintentar en ~40 ticks con el dron que este libre.
            m["agree"] = -999
            m["pings"] = min(m["pings"], 1)
        elif perf == FAILURE:
            # El adjudicatario declina: la tarea se reasigna por la via sin
            # subasta.
            self._cuenta("contratos_fallidos")
            adjudicada = m["adjudicadas"].pop(conv, None)
            if adjudicada is not None and tick - adjudicada[2] <= 30:
                self._subasta_desierta(
                    u, p, api, adjudicada[0], conv, adjudicada[1]
                )
                self._cuenta("contratos_reasignados")

    # =========================================================================
    # S4 - Contract Net Protocol (hielo, restos y recargas)
    #   iniciador --CFP--> k candidatos preseleccionados
    # candidato --PROPOSE(puja)--> iniciador      (no pujar = rechazar sin
    # gastar un mensaje)
    # iniciador --ACCEPT_PROPOSAL--> menor puja ;  --REJECT_PROPOSAL--> el
    # resto
    # =========================================================================
    def _abrir_subasta(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        ontologia: str,
        contenido: Dict[str, Any],
        candidatos: List[str],
        plazo: int,
        puja_propia: Optional[float] = None,
    ) -> bool:
        """Manda el CFP a los candidatos y deja la subasta abierta hasta
        `plazo` ticks.
        """
        conv = self._nueva_conversacion(u.id, p.tick)
        tarea = dict(contenido)
        tarea["vence"] = p.tick + plazo
        cfp = self._acl(CFP, u.id, conv, ontologia, tarea)
        invitados = [c for c in candidatos if self._enviar(api, c, cfp)]
        if not invitados:
            return False
        propuestas = [(puja_propia, u.id)] if puja_propia is not None else []
        m["subastas"][conv] = {
            "ont": ontologia,
            "contenido": tarea,
            "vence": tarea["vence"],
            "propuestas": propuestas,
        }
        self._cuenta("subastas_abiertas")
        self._cuenta("subastas_" + ontologia)
        return True

    def _puja_rover(
        self, u: UnidadVista, ontologia: str, pos: Pos, m: Memoria
    ) -> float:
        """Puja de un rover (menor es mejor).

        Hielo: pasos de ida y vuelta, bateria que falta, carga ocupada y
        exposicion a tormentas. Restos: pasos de ida y vuelta y cuanta bateria
        tiene (quien menos tiene, mas lo necesita).
        """
        riesgo = 25.0 * self._riesgo_de_ruta(u.pos, pos, m)
        if ontologia == ONT_RESTOS:
            return 2.0 * cheb(u.pos, pos) + 0.3 * u.bateria + riesgo
        pasos = cheb(u.pos, pos) + cheb(pos, self.base_pos)
        return pasos + 0.25 * (100.0 - u.bateria) + 4.0 * u.carga + riesgo

    def _puja_recargador(
        self, u: UnidadVista, pos: Pos, m: Memoria
    ) -> Optional[float]:
        """Puja de un dron de recarga por un rescate, o None si no puede
        tomarlo.
        """
        distancia = cheb(u.pos, pos)
        libre = (
            m["rescate"] is None
            and u.carga_recarga > 0
            and not self._oferta_viva(m)
        )
        if (
            not libre
            or u.bateria - 2.3 * distancia
            < UMBRAL_BATERIA_BAJA + MARGEN_BATERIA
        ):
            return None
        return (
            2.0 * distancia
            + 0.2 * (100.0 - u.bateria)
            + 25.0 * self._riesgo_de_ruta(u.pos, pos, m)
        )

    def _oferta_viva(self, m: Memoria) -> bool:
        """Dice si la unidad tiene una propuesta enviada que aun no vence (la
        compromete).
        """
        if m["oferta"] is not None and self._tick > m["oferta"][1]:
            m["oferta"] = None  # la propuesta expiro sin respuesta
        return m["oferta"] is not None

    def _responder_cfp(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        emisor: str,
        conv: str,
        ontologia: str,
        contenido: Dict[str, Any],
    ) -> None:
        """El candidato puja solo si puede cumplir y no esta comprometido con
        otra subasta.
        """
        pos = a_pos(contenido["pos"])
        puja = None
        if u.tipo == "dron_recarga" and ontologia == ONT_RECARGA:
            puja = self._puja_recargador(u, pos, m)
        elif u.tipo == "rover" and ontologia in (ONT_HIELO, ONT_RESTOS):
            libre = (
                u.estado == "activo"
                and m["contrato"] is None
                and not self._oferta_viva(m)
                and not p.fase_final
                and (
                    u.carga == 0
                    if ontologia == ONT_RESTOS
                    else u.carga < u.capacidad
                )
            )
            if libre and self._alcanza_bateria(u, pos):
                puja = self._puja_rover(u, ontologia, pos, m)
        if puja is None:
            self._cuenta("cfp_sin_puja")
            return
        propuesta = self._acl(
            PROPOSE, u.id, conv, ontologia, {"puja": round(puja, 2)}
        )
        if self._enviar(api, emisor, propuesta):
            m["oferta"] = (
                conv,
                int(contenido.get("vence", p.tick + PLAZO_SUBASTA)) + 2,
            )

    def _cerrar_subastas(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> None:
        """Al vencer el plazo: ACCEPT a la menor puja (empate: menor id) y
        REJECT al resto.
        """
        vencidas = [
            c for c, s in m["subastas"].items() if p.tick >= s["vence"]
        ]
        for conv in vencidas:
            s = m["subastas"].pop(conv)
            ont, tarea = s["ont"], s["contenido"]
            orden = sorted(s["propuestas"])
            if not orden:
                self._cuenta("subastas_desiertas")
                self._subasta_desierta(u, p, api, ont, conv, tarea)
                continue
            ganador = orden[0][1]
            self._cuenta("subastas_adjudicadas")
            if ganador == u.id:
                self._tomar_rescate(u, p, api, m, conv, tarea)
            else:
                acepta = self._acl(ACCEPT_PROPOSAL, u.id, conv, ont, tarea)
                m["adjudicadas"][conv] = (ont, tarea, p.tick)
                if not self._enviar(api, ganador, acepta):
                    # El ganador ya no existe: se cae a la via sin subasta.
                    self._subasta_desierta(u, p, api, ont, conv, tarea)
            for _, perdedor in orden[1:]:
                if perdedor != u.id:
                    self._enviar(
                        api,
                        perdedor,
                        self._acl(REJECT_PROPOSAL, u.id, conv, ont, {}),
                    )

    def _subasta_desierta(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        ontologia: str,
        conv: str,
        tarea: Dict[str, Any],
    ) -> None:
        """Sin adjudicatario: se avisa por la via barata (INFORM) o se informa
        el fallo.
        """
        if ontologia == ONT_RECARGA:
            conv = tarea.get("pedido", conv)
            fallo = self._acl(
                FAILURE,
                u.id,
                conv,
                ONT_RECARGA,
                {"motivo": "sin_disponibilidad"},
            )
            self._enviar(api, tarea["rover"], fallo)
        elif not p.fase_final:
            self._informar_a_rover_ocioso(
                u, p, api, ontologia, tarea, a_pos(tarea["pos"])
            )

    def _aceptar_contrato(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        emisor: str,
        conv: str,
        ontologia: str,
        contenido: Dict[str, Any],
    ) -> None:
        """El ganador recibe ACCEPT_PROPOSAL y queda obligado a la tarea."""
        if m["oferta"] is not None and m["oferta"][0] == conv:
            m["oferta"] = None
        pos = a_pos(contenido["pos"])
        if u.tipo == "dron_recarga" and ontologia == ONT_RECARGA:
            if m["rescate"] is None and u.carga_recarga > 0:
                self._tomar_rescate(u, p, api, m, conv, contenido)
            else:
                fallo = self._acl(
                    FAILURE, u.id, conv, ONT_RECARGA, {"motivo": "ocupado"}
                )
                self._enviar(api, contenido["rover"], fallo)
            return
        if u.tipo != "rover":
            return
        if m["contrato"] is not None:
            # Ya comprometido con otra adjudicacion: se declina con FAILURE y
            # el iniciador
            # reasigna la tarea (ver _procesar_mensaje).
            fallo = self._acl(
                FAILURE, u.id, conv, ontologia, {"motivo": "ocupado"}
            )
            self._enviar(api, emisor, fallo)
            return
        m["contrato"] = {
            "ont": ontologia,
            "conv": conv,
            "pos": pos,
            "iniciador": emisor,
            "id": contenido.get("id"),
        }
        if ontologia == ONT_HIELO:
            m["hielo"][pos] = (int(contenido.get("cantidad", 1)), p.tick)
            m["ultimo_hielo"] = p.tick
        else:
            m["restos"][contenido["id"]] = (
                pos,
                int(contenido.get("combustible", 10)),
                p.tick,
            )
        m["objetivo"] = None
        self._cuenta("contratos_ganados")

    def _objetivo_de_contrato(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> Optional[Tuple[Any, ...]]:
        """Convierte el contrato vigente en objetivo, o lo cierra si ya no se
        puede cumplir.
        """
        contrato = m["contrato"]
        if contrato is None:
            return None
        pos = contrato["pos"]
        if (
            contrato["ont"] == ONT_HIELO
            and pos in m["hielo"]
            and self._alcanza_bateria(u, pos)
        ):
            return ("hielo", pos)
        if (
            contrato["ont"] == ONT_RESTOS
            and contrato["id"] in m["restos"]
            and u.carga == 0
            and self._alcanza_bateria(u, pos)
        ):
            return ("restos", contrato["id"], pos)
        m["contrato"] = None
        # Si llego y la veta ya no esta, confirma el agotamiento a quien se la
        # adjudico,
        # para que la borre de su mapa y no la vuelva a anunciar.
        if (
            contrato["ont"] == ONT_HIELO
            and cheb(u.pos, pos) <= VISION["rover"]
        ):
            aviso = self._acl(
                INFORM,
                u.id,
                contrato["conv"],
                ONT_HIELO,
                {"pos": pos, "agotado": True},
            )
            if self._enviar(api, contrato["iniciador"], aviso):
                self._cuenta("avisos_de_agotamiento")
        return None

    def _reportar_hallazgos(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> None:
        """Un dron en vuelo avisa de hielo o restos, con un mensaje (o subasta)
        por turno.

        Filtros anti-saturacion: los drones estacionados en la base no
        reportan; si varios drones ven lo mismo reporta uno; una zona no se
        repite hasta su enfriamiento; solo se avisa de lo que supera el valor
        minimo y que ningun rover tiene ya a la vista.
        """
        if p.fase_final or u.bateria <= UMBRAL_BATERIA_BAJA + 5:
            return
        if EXP_FILTROS_MENSAJES and cheb(u.pos, self.base_pos) <= 2:
            return
        rovers = [
            (a["id"], a_pos(a["pos"]))
            for a in p.aliados_visible
            if a["tipo"] == "rover" and a["estado"] == "activo"
        ]
        primero_restos = self.politica == "CARRONA"
        orden = (self._reportar_restos, self._reportar_hielo)
        for reportar in orden if primero_restos else orden[::-1]:
            if reportar(u, p, api, m, rovers):
                return

    def _reportar_hielo(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        rovers: List[Tuple[str, Pos]],
    ) -> bool:
        """Avisa de la zona de hielo mas rica que pase los filtros. True si
        envio algo.
        """
        pol = POLITICAS[self.politica]
        zonas: Dict[Pos, List[Tuple[int, int, int]]] = {}
        for hx, hy, cant in p.hielo_visible:
            zonas.setdefault((hx // 5, hy // 5), []).append((hx, hy, cant))
        valor_min = pol["valor_min"] if EXP_FILTROS_MENSAJES else 1
        candidatas = sorted(
            zonas.items(), key=lambda kv: -sum(c for _, _, c in kv[1])
        )
        for clave, celdas in candidatas:
            total = sum(c for _, _, c in celdas)
            if total < valor_min:
                break
            mejor = max(celdas, key=lambda c: c[2])
            pos = (mejor[0], mejor[1])
            if cheb(pos, self.base_pos) > pol[
                "radio_max"
            ] or self._cede_reporte(u, p, pos):
                continue
            # Si un rover ya la tiene a la vista, la vera solo.
            if EXP_FILTROS_MENSAJES and any(
                cheb(rp, pos) <= VISION["rover"] for _, rp in rovers
            ):
                continue
            if not self._puede_reportar(
                m, (ONT_HIELO, clave), p.tick, pol["enfriamiento"]
            ):
                continue
            contenido = {"pos": pos, "cantidad": mejor[2], "total": total}
            # La subasta cuesta unos 6 mensajes: solo si la zona es grande y
            # hay a quien elegir.
            cercanos = [
                rid
                for rid, rp in sorted(rovers, key=lambda r: cheb(r[1], pos))
            ]
            cercanos = cercanos[: pol["k_cnp"]]
            if (
                EXP_SUBASTAS
                and len(cercanos) >= 2
                and total >= pol["valor_min"] * FACTOR_SUBASTA
            ):
                if self._abrir_subasta(
                    u, p, api, m, ONT_HIELO, contenido, cercanos, PLAZO_SUBASTA
                ):
                    return True
            return self._informar_a_rover_ocioso(
                u, p, api, ONT_HIELO, contenido, pos
            )
        return False

    def _reportar_restos(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        rovers: List[Tuple[str, Pos]],
    ) -> bool:
        """Avisa de un resto caido que ningun rover tiene a la vista. True si
        envio algo.
        """
        pol = POLITICAS[self.politica]
        for r in sorted(
            p.restos_visible, key=lambda r: -int(r.get("combustible", 10))
        ):
            pos = a_pos(r["pos"])
            if cheb(pos, self.base_pos) > pol[
                "radio_max"
            ] or self._cede_reporte(u, p, pos):
                continue
            if EXP_FILTROS_MENSAJES and any(
                cheb(rp, pos) <= VISION["rover"] for _, rp in rovers
            ):
                continue
            if not self._puede_reportar(
                m, (ONT_RESTOS, r["id"]), p.tick, 4 * pol["enfriamiento"]
            ):
                continue
            contenido = {
                "id": r["id"],
                "pos": pos,
                "combustible": int(r.get("combustible", 10)),
            }
            cercanos = [
                rid
                for rid, rp in sorted(rovers, key=lambda x: cheb(x[1], pos))
            ]
            cercanos = cercanos[: pol["k_cnp"]]
            if EXP_SUBASTAS and len(cercanos) >= 2:
                if self._abrir_subasta(
                    u,
                    p,
                    api,
                    m,
                    ONT_RESTOS,
                    contenido,
                    cercanos,
                    PLAZO_SUBASTA,
                ):
                    return True
            return self._informar_a_rover_ocioso(
                u, p, api, ONT_RESTOS, contenido, pos
            )
        return False

    # =========================================================================
    # S2 - FSM del dron explorador:  PATRULLANDO <-> RETORNANDO_BASE
    # =========================================================================
    def _de_turno(self, m: Memoria, tick: int, pol: Dict[str, Any]) -> bool:
        """Relevo de patrulla: de cada 15 exploradores, `exploradores` estan de
        turno.

        El 15 es el tamano del grupo de relevo, no el de la flota: con 30
        exploradores habria dos por turno de cada grupo, es decir, la misma
        proporcion.

        El turno rota cada TURNO_PATRULLA ticks, de modo que todos los drones
        patrullan a lo largo de la partida y siempre hay cobertura en el aire.
        Los demas esperan en la base, donde ademas se recargan gratis.
        """
        return (m["idx"] - tick // TURNO_PATRULLA) % 15 < pol["exploradores"]

    def _ruta_de_patrulla(
        self, pos: Pos, m: Memoria, pol: Dict[str, Any]
    ) -> List[Pos]:
        """Dos puntos del gajo que toca: cada salida toma el gajo siguiente.

        El abanico de 90 grados hacia adentro se parte en GAJOS sectores. Como
        cada dron empieza en un gajo distinto (por su indice), los que estan de
        turno no repiten franja.
        """
        gajo = (m["idx"] + m["salidas"]) % GAJOS
        m["salidas"] += 1
        angulo = (gajo + 0.5) / GAJOS * (math.pi / 2.0)
        tope = min(pol["radio_max"], RADIO_PATRULLA)
        puntos = [
            self._punto(angulo, tope * 0.6),
            self._punto(angulo, float(tope)),
        ]
        if cheb(pos, puntos[1]) < cheb(pos, puntos[0]):
            puntos.reverse()  # si ya esta lejos, empieza por el extremo
        return puntos

    def _explorador(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> Accion:
        """Un turno de explorador: cerrar subastas, reportar, y patrullar o
        volver a base.
        """
        pol = POLITICAS[self.politica]
        tick = p.tick
        self._cerrar_subastas(u, p, api, m)
        self._reportar_hallazgos(u, p, api, m)

        # Bateria baja: obligatorio a <= 25 %; se adelanta lo justo para llegar
        # sin morir.
        vuelta = cheb(u.pos, self.base_pos) * 1.2 + UMBRAL_BATERIA_BAJA + 3.0
        if u.bateria <= max(UMBRAL_BATERIA_BAJA, vuelta):
            m["a_base"] = True
        de_turno = self._de_turno(m, tick, pol) and not p.fase_final

        if m["a_base"] or not de_turno:
            # RETORNANDO_BASE: sin bateria, fuera de turno o en los ultimos 30
            # s.
            m["estado"] = RETORNANDO_BASE
            m["ruta"] = []
            if not p.base_aliada_cerca:
                return self._mover(u, self.base_pos, m)
            if u.bateria < 99.0:
                return ("recargar_en_base",)
            m["a_base"] = False
            if not de_turno:
                return self._quieto(u, m)

        # PATRULLANDO: recorre gajo tras gajo sin pausa; la politica fija la
        # cadencia.
        m["estado"] = PATRULLANDO
        if (tick + m["idx"]) % pol["cadencia"] != 0:
            return self._quieto(u, m)
        if not m["ruta"]:
            m["ruta"] = self._ruta_de_patrulla(u.pos, m, pol)
            self._cuenta("patrullas")
        if cheb(u.pos, m["ruta"][0]) <= 2:
            m["ruta"].pop(0)
            if not m["ruta"]:
                m["ruta"] = self._ruta_de_patrulla(u.pos, m, pol)
                self._cuenta("patrullas")
        return self._mover(u, m["ruta"][0], m)

    # =========================================================================
    # S2 - FSM del dron de recarga:  EN_ESPERA -> EN_RESCATE -> RETORNANDO_BASE
    # -> EN_ESPERA
    # =========================================================================
    def _atender_request(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        conv: str,
        contenido: Dict[str, Any],
    ) -> None:
        """El recargador que recibe un REQUEST lo toma o lo subasta entre los
        demas (CNP).

        Evaluacion perezosa: si esta libre y el rover esta al lado (recarga
        preventiva en la base) lo toma sin mas. Si no, abre una subasta entre
        los recargadores que ve, en la que el tambien puja; asi varios pedidos
        simultaneos se reparten sin duplicar viajes. Si nadie puede, responde
        FAILURE y el rover reintenta.
        """
        rover = contenido["rover"]
        pos = a_pos(contenido["pos"])
        if m["rescate"] is not None and m["rescate"]["rover"] == rover:
            return  # pedido repetido de un rescate ya en curso
        tarea = {
            "rover": rover,
            "pos": pos,
            "urgente": bool(contenido.get("urgente")),
            "pedido": contenido.get("pedido", conv),
        }
        mi_puja = self._puja_recargador(u, pos, m)
        otros = [
            a["id"]
            for a in p.aliados_visible
            if a["tipo"] == "dron_recarga"
            and a["id"] != u.id
            and a["bateria"] > 40.0
        ]
        otros = otros[: POLITICAS[self.politica]["k_cnp"]]
        if mi_puja is not None and (
            cheb(u.pos, pos) <= 3 or not otros or not EXP_SUBASTAS
        ):
            self._tomar_rescate(u, p, api, m, conv, tarea)
            return
        if (
            otros
            and EXP_SUBASTAS
            and self._abrir_subasta(
                u, p, api, m, ONT_RECARGA, tarea, otros, PLAZO_RECARGA, mi_puja
            )
        ):
            return
        self._subasta_desierta(u, p, api, ONT_RECARGA, conv, tarea)

    def _tomar_rescate(
        self,
        u: UnidadVista,
        p: Percepcion,
        api: Any,
        m: Memoria,
        conv: str,
        tarea: Dict[str, Any],
    ) -> None:
        """Compromete al dron con el rescate y lo confirma al rover con AGREE.

        El AGREE se omite solo en la recarga preventiva con el rover a la vista
        del dron, donde el rover ya ve venir la ayuda y el mensaje seria
        bateria gastada.
        """
        pos = a_pos(tarea["pos"])
        m["rescate"] = {
            "rover": tarea["rover"],
            "pos": pos,
            "desde": p.tick,
            "conv": conv,
        }
        m["estado"] = EN_RESCATE
        self._cuenta("rescates_aceptados")
        conv = tarea.get(
            "pedido", conv
        )  # se responde en la conversacion del REQUEST original
        m["rescate"]["conv"] = conv
        if tarea.get("urgente") or cheb(u.pos, pos) > 3:
            acuerdo = self._acl(
                AGREE, u.id, conv, ONT_RECARGA, {"eta": cheb(u.pos, pos)}
            )
            self._enviar(api, tarea["rover"], acuerdo)

    def _recargador(
        self, u: UnidadVista, p: Percepcion, api: Any, m: Memoria
    ) -> Accion:
        """Un turno de recargador: espera en base, va al rescate y vuelve."""
        self._cerrar_subastas(u, p, api, m)
        if m["estado"] != EN_ESPERA:
            self._reportar_hallazgos(
                u, p, api, m
            )  # en transito tambien avisa de lo que ve
        rescate = m["rescate"]

        if u.bateria <= UMBRAL_BATERIA_BAJA or u.carga_recarga <= 0:
            # Obligatorio: sin bateria o sin carga, a la base.
            if rescate is not None and u.carga_recarga > 0:
                fallo = self._acl(
                    FAILURE,
                    u.id,
                    rescate["conv"],
                    ONT_RECARGA,
                    {"motivo": "bateria"},
                )
                self._enviar(api, rescate["rover"], fallo)
            m["rescate"] = None
            m["estado"] = RETORNANDO_BASE
        elif rescate is not None:
            m["estado"] = EN_RESCATE
            objetivo = rescate["pos"]
            visto = next(
                (a for a in p.aliados_visible if a["id"] == rescate["rover"]),
                None,
            )
            if visto is not None:
                objetivo = a_pos(visto["pos"])
                rescate["pos"] = objetivo
                if visto["bateria"] >= 95.0:
                    m["rescate"] = None  # otro ya lo recargo
            elif cheb(u.pos, objetivo) <= 3 or p.tick - rescate["desde"] > 160:
                m["rescate"] = None  # no esta donde dijo: murio o se fue
            if m["rescate"] is None:
                m["estado"] = RETORNANDO_BASE
            elif cheb(u.pos, objetivo) <= 1:
                m["rescate"] = None
                m["estado"] = RETORNANDO_BASE
                self._cuenta("recargas")
                return ("recargar_aliado", rescate["rover"])
            else:
                return self._mover(u, objetivo, m)

        if not p.base_aliada_cerca:
            m["estado"] = RETORNANDO_BASE
            return self._mover(u, self.base_pos, m)
        # EN_ESPERA: en la base, con bateria y carga completas.
        m["estado"] = EN_ESPERA
        if u.bateria < 99.0 or u.carga_recarga <= 0:
            return ("recargar_en_base",)
        return ("esperar",)

    # =========================================================================
    # S5 - Eleccion social: Copeland por comparacion de pares
    # =========================================================================
    def _depositar_papeleta(
        self, u: UnidadVista, p: Percepcion, m: Memoria
    ) -> None:
        """Cada unidad ordena las cuatro politicas segun su estado LOCAL.

        La papeleta es solo un orden de preferencias: no lleva posiciones ni
        hallazgos. Evaluacion perezosa: solo se opina cuando la eleccion esta
        cerca.
        """
        if p.tick - self.ultima_eleccion < PERIODO_VOTACION - 4:
            return
        bateria = u.bateria / 100.0
        tormenta = 1.0 if (u.en_tormenta or m["tormentas"]) else 0.0
        ricas = sum(1 for cant, _ in m["hielo"].values() if cant >= 4)
        # Escasez: solo cuenta la opinion de quien esta en el campo y no
        # encuentra nada. Una
        # unidad estacionada en la base no ve hielo porque no esta mirando, no
        # porque no haya.
        escasez = (
            not m["hielo"]
            and p.tick - m["ultimo_hielo"] > TICKS_SIN_HIELO
            and cheb(u.pos, self.base_pos) > RADIO_BASE
        )
        puntaje = {
            "EXPANSION": 0.45 * bateria
            + 0.55 * min(1.0, ricas / 4.0)
            - 0.4 * tormenta,
            "AHORRO": 0.35 + 0.45 * tormenta + 0.2 * (1.0 - bateria),
            "CARRONA": (
                0.6 * min(1.0, len(m["restos"]) / 2.0)
                + (0.35 if u.bateria < 50.0 else 0.0)
            ),
            "REPLIEGUE": 1.5 if p.fase_final else (0.75 if escasez else 0.0),
        }
        self.urna[u.id] = tuple(
            sorted(ORDEN_POLITICAS, key=lambda k: -puntaje[k])
        )

    def _votar_si_toca(self, tick: int) -> None:
        """Cada PERIODO_VOTACION ticks cuenta las papeletas y fija la politica
        del equipo.
        """
        if (
            not EXP_VOTACION
            or tick - self.ultima_eleccion < PERIODO_VOTACION
            or not self.urna
        ):
            return
        self.ultima_eleccion = tick
        papeletas = list(self.urna.values())
        self.urna = {}
        ganadora, matriz, copeland, metodo = self._copeland(papeletas)
        # Inercia: para desplazar a la politica vigente, la retadora debe
        # ganarle el duelo
        # directo por mas del 10 % de los votantes. Evita cambiar de postura en
        # cada eleccion.
        # REPLIEGUE no espera: responde a la fase final o a la escasez.
        if ganadora != self.politica and ganadora != "REPLIEGUE":
            ventaja = (
                matriz[ganadora][self.politica]
                - matriz[self.politica][ganadora]
            )
            if ventaja <= MARGEN_INERCIA * len(papeletas):
                ganadora, metodo = self.politica, "inercia"
        self.historial_votos.append(
            {
                "tick": tick,
                "votantes": len(papeletas),
                "matriz": matriz,
                "copeland": copeland,
                "ganadora": ganadora,
                "desempate": metodo,
                "cambio": ganadora != self.politica,
            }
        )
        self.politica = ganadora
        self._cuenta("elecciones")

    def _copeland(
        self, papeletas: List[Tuple[str, ...]]
    ) -> Tuple[str, Dict[str, Dict[str, int]], Dict[str, float], str]:
        """Metodo de Copeland: gana quien vence mas duelos por pares (medio
        punto por empate).

        Si hay empate en el puntaje de Copeland -lo que incluye los ciclos de
        Condorcet- se desempata por conteo de Borda y, si persiste, por el
        orden fijo ORDEN_POLITICAS. Devuelve la ganadora, la matriz de pares,
        los puntajes y el metodo que decidio.
        """
        cands = ORDEN_POLITICAS
        matriz = {a: {b: 0 for b in cands if b != a} for a in cands}
        borda = {a: 0 for a in cands}
        for orden in papeletas:
            puesto = {c: i for i, c in enumerate(orden)}
            for a in cands:
                borda[a] += len(cands) - 1 - puesto[a]
                for b in cands:
                    if a != b and puesto[a] < puesto[b]:
                        matriz[a][b] += 1
        copeland = {a: 0.0 for a in cands}
        for i, a in enumerate(cands):
            for b in cands[i + 1 :]:
                if matriz[a][b] > matriz[b][a]:
                    copeland[a] += 1.0
                elif matriz[a][b] < matriz[b][a]:
                    copeland[b] += 1.0
                else:
                    copeland[a] += 0.5
                    copeland[b] += 0.5
        tope = max(copeland.values())
        finalistas = [a for a in cands if copeland[a] == tope]
        if len(finalistas) == 1:
            return finalistas[0], matriz, copeland, "copeland"
        mejor_borda = max(borda[a] for a in finalistas)
        finalistas = [a for a in finalistas if borda[a] == mejor_borda]
        return (
            finalistas[0],
            matriz,
            copeland,
            ("borda" if len(finalistas) == 1 else "orden_fijo"),
        )
