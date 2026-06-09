import math
import heapq
import time
import random
import sys
from dataclasses import dataclass

@dataclass
class SolverStats:
    algorithm: str
    size: str
    heuristic: str
    solution_length: int
    nodes_expanded: int
    nodes_generated: int
    time_ms: float
    max_frontier_or_depth: int
    memory_usage_est_bytes: int
    status: str
    path: list

sys.setrecursionlimit(50_000)   # IDA* on 24-puzzle may go 150+ calls deep

class NPuzzle:
    def __init__(self, size: int):
        assert size in (3, 4, 5)
        self.size = size
        self.n    = size * size
        self.goal = tuple(range(1, self.n)) + (0,)
        self._build_tables()
        self.nodes_expanded = 0

    def _build_tables(self):
        s = self.size
        self.goal_pos = {tile: (i // s, i % s)
                         for i, tile in enumerate(self.goal)}
        self.neighbors = tuple(
            tuple(
                nb for nb in (i - s, i + s, i - 1, i + 1)
                if 0 <= nb < self.n
                and not (i % s == 0     and nb == i - 1)
                and not (i % s == s - 1 and nb == i + 1)
            )
            for i in range(self.n)
        )

    def generate(self, shuffle_moves: int) -> tuple:
        state      = list(self.goal)
        blank      = self.n - 1
        prev_blank = -1
        for _ in range(shuffle_moves):
            candidates = [nb for nb in self.neighbors[blank] if nb != prev_blank]
            nb = random.choice(candidates)
            state[blank], state[nb] = state[nb], state[blank]
            prev_blank = blank
            blank      = nb
        return tuple(state)

    def is_solvable(self, state: tuple) -> bool:
        s          = self.size
        tiles      = [t for t in state if t != 0]
        inversions = sum(1 for i in range(len(tiles))
                           for j in range(i + 1, len(tiles))
                           if tiles[i] > tiles[j])
        if s % 2 == 1:
            return inversions % 2 == 0
        blank_row_from_bottom = s - state.index(0) // s
        return (inversions + blank_row_from_bottom) % 2 == 1

    def heuristic(self, state: tuple) -> int:
        s    = self.size
        gpos = self.goal_pos
        dist = 0
        for idx, tile in enumerate(state):
            if tile == 0:
                continue
            gr, gc = gpos[tile]
            dist  += abs(idx // s - gr) + abs(idx % s - gc)
        for row in range(s):
            row_tiles = []
            for col in range(s):
                tile = state[row * s + col]
                if tile != 0 and gpos[tile][0] == row:
                    row_tiles.append((gpos[tile][1], col))
            for i in range(len(row_tiles)):
                for j in range(i + 1, len(row_tiles)):
                    if row_tiles[i][0] > row_tiles[j][0]:
                        dist += 2
        for col in range(s):
            col_tiles = []
            for row in range(s):
                tile = state[row * s + col]
                if tile != 0 and gpos[tile][1] == col:
                    col_tiles.append((gpos[tile][0], row))
            for i in range(len(col_tiles)):
                for j in range(i + 1, len(col_tiles)):
                    if col_tiles[i][0] > col_tiles[j][0]:
                        dist += 2
        return dist

    def _solve_astar(self, initial: tuple):
        goal      = self.goal
        neighbors = self.neighbors
        h         = self.heuristic
        blank0    = initial.index(0)
        heap      = [(h(initial), 0, initial, blank0)]
        came_from = {initial: None}
        g_score   = {initial: 0}
        nodes     = 0
        nodes_gen = 1
        max_frontier = 1
        INF       = 10**9
        
        t_start   = time.perf_counter()
        
        while heap:
            if len(heap) > max_frontier:
                max_frontier = len(heap)
            
            f, g, state, blank = heapq.heappop(heap)
            if state == goal:
                path, cur = [], state
                while cur is not None:
                    path.append(cur)
                    cur = came_from[cur]
                path.reverse()
                self.nodes_expanded = nodes
                
                t_end = time.perf_counter()
                time_ms = (t_end - t_start) * 1000.0
                mem_est = (len(came_from) + len(heap)) * 150
                
                return SolverStats(
                    algorithm="A*",
                    size=f"{self.size}x{self.size}",
                    heuristic="Manhattan + Linear Conflict",
                    solution_length=len(path)-1,
                    nodes_expanded=nodes,
                    nodes_generated=nodes_gen,
                    time_ms=time_ms,
                    max_frontier_or_depth=max_frontier,
                    memory_usage_est_bytes=mem_est,
                    status="Success",
                    path=path
                )
                
            if g > g_score.get(state, INF):
                continue
            nodes += 1
            for nb in neighbors[blank]:
                lst         = list(state)
                lst[blank], lst[nb] = lst[nb], lst[blank]
                ns          = tuple(lst)
                new_g       = g + 1
                if new_g < g_score.get(ns, INF):
                    if ns not in g_score:
                        nodes_gen += 1
                    g_score[ns]   = new_g
                    came_from[ns] = state
                    heapq.heappush(heap, (new_g + h(ns), new_g, ns, nb))
                    
        t_end = time.perf_counter()
        return SolverStats("A*", f"{self.size}x{self.size}", "Manhattan + LC", 0, nodes, nodes_gen, (t_end-t_start)*1000, max_frontier, (len(came_from)+len(heap))*150, "No Solution", [])

    def _solve_idastar(self, initial: tuple, time_limit: float = 120.0):
        goal      = self.goal
        neighbors = self.neighbors
        h         = self.heuristic
        nodes     = [0]
        nodes_gen = [1]
        max_depth = [0]
        t_start   = time.perf_counter()
        FOUND     = object()
        path      = [initial]
        blanks    = [initial.index(0)]

        def search(g: int, bound: int):
            if g > max_depth[0]:
                max_depth[0] = g
                
            state = path[-1]
            blank = blanks[-1]
            f     = g + h(state)
            if f > bound:
                return f
            if state == goal:
                return FOUND
            if time.perf_counter() - t_start > time_limit:
                raise TimeoutError()
            nodes[0] += 1
            prev  = path[-2] if len(path) > 1 else None
            min_t = float("inf")
            for nb in neighbors[blank]:
                lst         = list(state)
                lst[blank], lst[nb] = lst[nb], lst[blank]
                ns          = tuple(lst)
                if ns == prev:
                    continue
                nodes_gen[0] += 1
                path.append(ns)
                blanks.append(nb)
                t = search(g + 1, bound)
                if t is FOUND:
                    return FOUND
                if isinstance(t, (int, float)) and t < min_t:
                    min_t = t
                path.pop()
                blanks.pop()
            return min_t

        bound = h(initial)
        while True:
            try:
                t = search(0, bound)
            except TimeoutError:
                t_end = time.perf_counter()
                return SolverStats("IDA*", f"{self.size}x{self.size}", "Manhattan + LC", 0, nodes[0], nodes_gen[0], (t_end-t_start)*1000, max_depth[0], max_depth[0]*100, "Timeout", [])
                
            if t is FOUND:
                self.nodes_expanded = nodes[0]
                t_end = time.perf_counter()
                return SolverStats(
                    algorithm="IDA*",
                    size=f"{self.size}x{self.size}",
                    heuristic="Manhattan + Linear Conflict",
                    solution_length=len(path)-1,
                    nodes_expanded=nodes[0],
                    nodes_generated=nodes_gen[0],
                    time_ms=(t_end-t_start)*1000.0,
                    max_frontier_or_depth=max_depth[0],
                    memory_usage_est_bytes=max_depth[0]*100,
                    status="Success",
                    path=list(path)
                )
            if t == float("inf"):
                t_end = time.perf_counter()
                return SolverStats("IDA*", f"{self.size}x{self.size}", "Manhattan + LC", 0, nodes[0], nodes_gen[0], (t_end-t_start)*1000, max_depth[0], max_depth[0]*100, "No Solution", [])
            bound = t

    def solve(self, initial: tuple, algorithm: str = "A*", time_limit: float = 120.0):
        self.nodes_expanded = 0
        if not self.is_solvable(initial):
            return None
        
        # If it's already solved, we can still return a SolverStats object
        if initial == self.goal:
            return SolverStats(
                algorithm=algorithm,
                size=f"{self.size}x{self.size}",
                heuristic="Manhattan + Linear Conflict",
                solution_length=0,
                nodes_expanded=0,
                nodes_generated=1,
                time_ms=0.0,
                max_frontier_or_depth=1,
                memory_usage_est_bytes=100,
                status="Success",
                path=[initial]
            )
            
        if algorithm == "A*":
            return self._solve_astar(initial)
        else:
            return self._solve_idastar(initial, time_limit=time_limit)
