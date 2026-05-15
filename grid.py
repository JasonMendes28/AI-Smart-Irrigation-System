# grid.py
import pygame
import random
from config import *


# ── Asset loading ─────────────────────────────────────────────────────────────
def _load(path, size):
    img = pygame.image.load(path)
    return pygame.transform.scale(img, size)

def load_assets():
    s = CELL_SIZE
    return {
        "water":   _load("assets/water.png",      (s-10, s-10)),
        "crop":    _load("assets/crop.png",        (s-10, s-10)),
        "crop_hi": _load("assets/beans.png",        (s-4,  s-4)),
        "crop_high_hi": _load("assets/beans.png",        (s-4,  s-4)),
        "crop_low": _load("assets/corn.png",    (s-4,  s-4)),
        "crop_low_hi": _load("assets/corn.png",    (s-4,  s-4)),
        "rock":    _load("assets/rock.png",        (s-4,  s-4)),
        "grass":   _load("assets/grass_tile.png",  (s,    s)),
    }

ASSETS = None

def get_assets():
    global ASSETS
    if ASSETS is None:
        ASSETS = load_assets()
    return ASSETS


# ── Grid creation ─────────────────────────────────────────────────────────────
def _place_cluster(grid, size, crop_type):
    r = random.randint(1, GRID_SIZE - size - 1)
    c = random.randint(1, GRID_SIZE - size - 1)
    for i in range(size):
        for j in range(size):
            if grid[r+i][c+j] == EMPTY:
                grid[r+i][c+j] = crop_type

def create_grid():
    grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
    grid[0][0] = WATER                          # default water source top-left

    # Two clusters each of high / normal / low priority crops
    _place_cluster(grid, 2, CROP_HIGH)
    _place_cluster(grid, 2, CROP_HIGH)
    _place_cluster(grid, 2, CROP)
    _place_cluster(grid, 2, CROP)
    _place_cluster(grid, 2, CROP_LOW)
    _place_cluster(grid, 2, CROP_LOW)

    # Random obstacles
    for _ in range(18):
        r = random.randint(0, GRID_SIZE - 1)
        c = random.randint(0, GRID_SIZE - 1)
        if grid[r][c] == EMPTY:
            grid[r][c] = OBSTACLE

    return grid


# ── Grid queries ──────────────────────────────────────────────────────────────
def get_all_crops(grid):
    return [(r, c) for r in range(GRID_SIZE)
                   for c in range(GRID_SIZE) if grid[r][c] in ALL_CROPS]

def get_all_water_sources(grid):
    return [(r, c) for r in range(GRID_SIZE)
                   for c in range(GRID_SIZE) if grid[r][c] == WATER]

def cell_rect(r, c):
    x = c * CELL_SIZE + OFFSET_X
    y = r * CELL_SIZE + OFFSET_Y
    return pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)

def pixel_to_cell(mx, my):
    c = (mx - OFFSET_X) // CELL_SIZE
    r = (my - OFFSET_Y) // CELL_SIZE
    if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE:
        return (r, c)
    return None


# ── Drawing ───────────────────────────────────────────────────────────────────
# Background tint per crop priority
_CROP_BG = {
    CROP:      (185, 255, 185),   # soft green  (normal)
    CROP_HIGH: (255, 200, 130),   # warm orange (high)
    CROP_LOW:  (240, 240, 110),   # pale yellow (low)
}

# Hover preview colours per mode
_HOVER_COLORS = {
    MODE_OBSTACLE:  (200,  80,  30, 100),
    MODE_CROP:      ( 50, 200,  80, 100),
    MODE_CROP_HIGH: (255, 140,  50, 100),
    MODE_CROP_LOW:  (220, 220,  50, 100),
    MODE_WATER:     ( 50, 120, 255, 100),
    MODE_ERASE:     (255,  50,  50,  80),
}


def draw_grid(screen, grid, path=None, no_path_cells=None,
              explored=None, show_explored=True,
              hover_cell=None, mode=MODE_NONE, font_small=None):
    """Render the full grid with all overlays."""

    a = get_assets()
    path_set      = set(path)          if path          else set()
    no_path_cells = set(no_path_cells) if no_path_cells else set()
    explored      = explored           if explored       else set()

    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            rect = cell_rect(r, c)
            val  = grid[r][c]

            # 1 ── Grass base
            screen.blit(a["grass"], rect)

            # 2 ── Explored-node wash (faint blue; EMPTY cells only)
            if show_explored and (r, c) in explored and val == EMPTY:
                ov = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                ov.fill((80, 140, 255, 55))
                screen.blit(ov, rect)

            # 3 ── Cell content
            if val == OBSTACLE:
                screen.blit(a["rock"], a["rock"].get_rect(center=rect.center))

            elif val == WATER:
                screen.blit(a["water"], a["water"].get_rect(center=rect.center))
                # Pulsing ring
                pygame.draw.circle(screen, (100, 180, 255),
                                   rect.center, CELL_SIZE // 2 - 4, 2)

            elif val in ALL_CROPS:
                # Priority-tinted background
                pygame.draw.rect(screen, _CROP_BG.get(val, (185, 255, 185)), rect)
                
                if val == CROP_HIGH:
                 img = a["crop_hi"] if (r,c) in path_set else a["crop"]
                elif val == CROP_LOW:
                    img = a["crop_low_hi"] if (r,c) in path_set else a["crop_low"]
                else:
                    img = a["crop_hi"] if (r,c) in path_set else a["crop"]    

                screen.blit(img, img.get_rect(center=rect.center))
                # Small priority badge in top-right corner
                if font_small:
                    if val == CROP_HIGH:
                        badge = font_small.render("!", True, (180, 40, 0))
                        screen.blit(badge, (rect.right - 14, rect.top + 2))
                    elif val == CROP_LOW:
                        badge = font_small.render("v", True, (110, 100, 0))
                        screen.blit(badge, (rect.right - 14, rect.top + 2))

            # 4 ── A* path highlight
            if (r, c) in path_set and val not in (WATER, OBSTACLE):
                ov = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                ov.fill((100, 170, 255, 130))
                screen.blit(ov, rect)

            # 5 ── No-path warning
            if (r, c) in no_path_cells:
                ov = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                ov.fill((255, 60, 60, 110))
                screen.blit(ov, rect)

            # 6 ── Hover preview (empty cells only)
            if (r, c) == hover_cell and val == EMPTY:
                col = _HOVER_COLORS.get(mode)
                if col:
                    ov = pygame.Surface((CELL_SIZE, CELL_SIZE), pygame.SRCALPHA)
                    ov.fill(col)
                    screen.blit(ov, rect)

            # 7 ── Grid lines
            pygame.draw.rect(screen, GRID_LINE_COLOR, rect, 1)
