# algorithms.py  —  A* pathfinding with explored-node tracking & multi-source support
import heapq
from config import CROP_PRIORITY
from utils import get_neighbors


def heuristic(a, b):
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar(grid, start, goal):
    """
    Run A* from start to goal.

    Returns
    -------
    path     : list[tuple]  — cells from start (exclusive) to goal (inclusive)
    explored : set[tuple]   — every cell popped from the open set during search
    """
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}
    g_score   = {start: 0}
    f_score   = {start: heuristic(start, goal)}
    explored  = set()

    while open_set:
        current = heapq.heappop(open_set)[1]
        explored.add(current)

        if current == goal:
            return _reconstruct(came_from, current), explored

        for neighbor in get_neighbors(current, grid):
            tentative_g = g_score[current] + 1
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor]   = tentative_g
                f_score[neighbor]   = tentative_g + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return [], explored   # no path found


def astar_best_source(grid, sources, goal):
    """
    Try A* from every water source to goal; return the shortest path found.

    Returns
    -------
    path        : list[tuple]
    explored    : set[tuple]  — union of all explored sets across every source tried
    best_source : tuple       — whichever source produced the shortest path
    """
    best_path   = None
    best_source = sources[0]
    all_explored: set = set()

    for src in sources:
        p, exp = astar(grid, src, goal)
        all_explored |= exp
        if p and (best_path is None or len(p) < len(best_path)):
            best_path   = p
            best_source = src

    return (best_path or []), all_explored, best_source


def sort_crops_by_priority(crops, grid):
    """
    Sort crop cells by CROP_PRIORITY (high first) then by grid position
    so the ordering is always deterministic.
    """
    return sorted(crops,
                  key=lambda rc: (CROP_PRIORITY.get(grid[rc[0]][rc[1]], 1), rc))


def _reconstruct(came_from, current):
    path = []
    while current in came_from:
        path.append(current)
        current = came_from[current]
    path.reverse()
    return path
