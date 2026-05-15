# utils.py
from config import OBSTACLE

def get_neighbors(pos, grid):
    """Return all non-obstacle orthogonal neighbours of pos."""
    rows = len(grid)
    cols = len(grid[0])
    r, c = pos
    neighbors = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < rows and 0 <= nc < cols:
            if grid[nr][nc] != OBSTACLE:
                neighbors.append((nr, nc))
    return neighbors
