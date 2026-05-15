"""
Smart Irrigation AI  —  A* Pathfinding  (Enhanced Edition)
═══════════════════════════════════════════════════════════
NEW FEATURES
────────────
  • Crop priority  — high-priority (!) crops are irrigated first,
                     low-priority (v) crops last
  • Multi-source   — place extra water sources; A* picks the nearest
                     one for the first hop automatically
  • Explored nodes — toggle a blue wash showing every cell A* examined
  • Speed control  — five speeds from Slow → Instant
  • Efficiency grade A–F based on crops-per-step ratio
  • Save / Load    — persist your map to saved_grid.json

CONTROLS
────────
  [O]        Obstacle mode
  [C]        Normal crop mode
  [H]        High-priority crop mode  (irrigated first !)
  [L]        Low-priority crop mode   (irrigated last  v)
  [W]        Extra water-source mode
  [E]        Erase mode
  [A]        Run A* irrigation
  [R]        Reset grid
  [+] / [-]  Speed up / slow down animation
  [X]        Toggle explored-nodes display
  [S]        Save grid to file
  [F]        Load grid from file
  [ESC]      Clear / cancel mode
"""
from __future__ import annotations
import json
import os

import pygame

from config import *
from grid import (create_grid, draw_grid, get_all_crops,
                  get_all_water_sources, pixel_to_cell)
from algorithms import astar, astar_best_source, sort_crops_by_priority

# ── Save file ─────────────────────────────────────────────────────────────────
SAVE_FILE = "saved_grid.json"

# ── Mode display table ────────────────────────────────────────────────────────
MODE_LABELS = {
    MODE_NONE:      ("IDLE",        (80,  80,  80)),
    MODE_OBSTACLE:  ("OBSTACLE",    (180,  70,  20)),
    MODE_CROP:      ("CROP",        (30,  140,  50)),
    MODE_CROP_HIGH: ("CROP  HIGH!", (200,  80,  10)),
    MODE_CROP_LOW:  ("CROP  LOW v", (140, 130,  10)),
    MODE_WATER:     ("WATER SOURCE",(30,   80, 200)),
    MODE_ERASE:     ("ERASE",       (180,  30,  30)),
}

# ── Pygame init ───────────────────────────────────────────────────────────────
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Smart Irrigation AI — A* Pathfinding")
clock = pygame.time.Clock()

font_title = pygame.font.SysFont("consolas", 18, bold=True)
font_body  = pygame.font.SysFont("consolas", 15)
font_small = pygame.font.SysFont("consolas", 13)

# ── State ─────────────────────────────────────────────────────────────────────
grid:             list  = create_grid()
path:             list  = []
no_path_cells:    set   = set()
explored_cells:   set   = set()
efficiency_grade: tuple = ("—", (100, 100, 100))   # (label, color)

mode          = MODE_NONE
status_msg    = "Ready.  Press A to irrigate."
status_color  = (30, 100, 30)
is_running    = False

speed_idx     = DEFAULT_SPEED_IDX
show_explored = True


# ── Helper functions ──────────────────────────────────────────────────────────
def set_mode(new_mode: str):
    """Toggle a draw mode on/off."""
    global mode
    mode = new_mode if mode != new_mode else MODE_NONE


def compute_efficiency(crops_done: int, path_len: int):
    """
    Return (ratio, grade_label, grade_color).
    Grade is based on crops irrigated per 100 path steps.
    """
    if path_len == 0 or crops_done == 0:
        return 0.0, "—", (100, 100, 100)
    ratio = crops_done * 100 / path_len
    if ratio >= 35: return ratio, "A", (30,  160,  30)
    if ratio >= 22: return ratio, "B", (80,  160,  30)
    if ratio >= 12: return ratio, "C", (160, 160,  30)
    if ratio >=  6: return ratio, "D", (160, 100,  30)
    return ratio, "F", (160, 30, 30)


def save_grid_to_file() -> bool:
    try:
        with open(SAVE_FILE, "w") as f:
            json.dump(grid, f)
        return True
    except Exception:
        return False


def load_grid_from_file():
    """Load grid from JSON; return None if not found or invalid."""
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
        if (isinstance(data, list)
                and len(data) == GRID_SIZE
                and all(len(row) == GRID_SIZE for row in data)):
            return data
    except Exception:
        pass
    return None


def _refresh_display():
    """Blit current state without flipping — used inside animation."""
    screen.fill(BACKGROUND_COLOR)
    draw_grid(screen, grid, path, no_path_cells,
              explored_cells if show_explored else set(),
              show_explored, None, MODE_NONE, font_small)
    draw_panel()
    screen.blit(
        font_title.render("Smart Irrigation AI  —  A* Pathfinding",
                          True, (30, 60, 30)),
        (OFFSET_X, 18)
    )


# ── Panel drawing ─────────────────────────────────────────────────────────────
def draw_panel():
    px = MAP_WIDTH
    pygame.draw.rect(screen, PANEL_COLOR,  (px, 0, PANEL_WIDTH, HEIGHT))
    pygame.draw.line(screen, PANEL_BORDER, (px, 0), (px, HEIGHT), 3)

    def txt(text, x, y, f=font_small, color=(30, 30, 30)):
        screen.blit(f.render(text, True, color), (x, y))

    def div(y):
        pygame.draw.line(screen, PANEL_BORDER,
                         (px + 10, y), (px + PANEL_WIDTH - 10, y), 1)

    y = 12

    # ── Title ────────────────────────────────────────────────────────────────
    txt("SMART IRRIGATION AI",   px + 14, y, font_body, (30, 90, 30)); y += 20
    txt("A* Pathfinding System", px + 14, y, color=(80, 100, 80));      y += 18
    div(y); y += 8

    # ── Farm stats ───────────────────────────────────────────────────────────
    crops_h   = sum(row.count(CROP_HIGH) for row in grid)
    crops_n   = sum(row.count(CROP)      for row in grid)
    crops_l   = sum(row.count(CROP_LOW)  for row in grid)
    obstacles = sum(row.count(OBSTACLE)  for row in grid)
    waters    = sum(row.count(WATER)     for row in grid)

    txt("── FARM STATS ──", px + 14, y, color=(60, 90, 60));            y += 16
    txt(f"  Water sources : {waters}",    px + 14, y, color=(30, 80, 200));  y += 16
    txt(f"  High crops  ! : {crops_h}",   px + 14, y, color=(200, 80, 10));  y += 16
    txt(f"  Normal crops  : {crops_n}",   px + 14, y, color=(40, 140, 40));  y += 16
    txt(f"  Low crops   v : {crops_l}",   px + 14, y, color=(130, 120, 10)); y += 16
    txt(f"  Obstacles     : {obstacles}", px + 14, y, color=(140, 70, 20));  y += 16
    txt(f"  Path length   : {len(path)}", px + 14, y, color=(30, 80, 180));  y += 16

    # Efficiency grade (label printed in its own colour)
    grade_lbl, grade_col = efficiency_grade
    txt("  Efficiency    : ", px + 14, y, color=(60, 60, 60))
    txt(grade_lbl, px + 148, y, font_body, grade_col)
    y += 20; div(y); y += 6

    # ── Draw mode indicator ───────────────────────────────────────────────────
    txt("── DRAW MODE ──", px + 14, y, color=(60, 90, 60)); y += 16
    label, col = MODE_LABELS[mode]
    pygame.draw.rect(screen, col,
                     (px + 14, y, PANEL_WIDTH - 28, 24), border_radius=4)
    pygame.draw.rect(screen, (255, 255, 255),
                     (px + 14, y, PANEL_WIDTH - 28, 24), 2, border_radius=4)
    lbl_s = font_small.render(label, True, (255, 255, 255))
    screen.blit(lbl_s, lbl_s.get_rect(center=(px + PANEL_WIDTH // 2, y + 12)))
    y += 30; div(y); y += 6

    # ── Speed indicator ───────────────────────────────────────────────────────
    txt("── ANIMATION SPEED ──", px + 14, y, color=(60, 90, 60)); y += 16
    for i in range(5):
        bc = (30, 140, 30) if i <= speed_idx else (180, 180, 180)
        pygame.draw.rect(screen, bc, (px + 14 + i * 18, y, 14, 8), border_radius=2)
    txt(f"  {SPEED_LABELS[speed_idx]}  [+/-]", px + 110, y - 2, color=(60, 60, 60))
    y += 18; div(y); y += 6

    # ── Controls ─────────────────────────────────────────────────────────────
    txt("── CONTROLS ──", px + 14, y, color=(60, 90, 60)); y += 16
    controls = [
        ("[O] Obstacle   [E] Erase",        (130,  60,  20)),
        ("[C] Crop  [H] High  [L] Low",      (30,  130,  40)),
        ("[W] Extra water source",           (30,   70, 180)),
        ("[A] Run A*  irrigation",           (30,   70, 180)),
        ("[X] Explored: " + ("ON " if show_explored else "OFF"),
                                             (80,   80, 150)),
        ("[S] Save      [F] Load",           (80,   80,  80)),
        ("[R] Reset   [ESC] Idle",           (80,   80,  80)),
    ]
    for line, col in controls:
        txt(line, px + 14, y, color=col); y += 18
    div(y); y += 6

    # ── Legend ───────────────────────────────────────────────────────────────
    txt("── LEGEND ──", px + 14, y, color=(60, 90, 60)); y += 16
    legend = [
        ((40,  120, 255), "Water source"),
        ((200,  80,  10), "High crop  (!)"),
        ((35,  155,  55), "Normal crop"),
        ((140, 130,  10), "Low crop   (v)"),
        ((110,  65,  25), "Obstacle"),
        ((100, 170, 255), "A* Path"),
        ((80,  140, 255), "Explored cells"),
        ((255,  60,  60), "No path!"),
    ]
    for col, lbl in legend:
        pygame.draw.rect(screen, col, (px + 14, y + 2, 12, 12), border_radius=2)
        txt(lbl, px + 32, y, color=(40, 40, 40))
        y += 16
    div(y); y += 6

    # ── Status ───────────────────────────────────────────────────────────────
    txt("── STATUS ──", px + 14, y, color=(60, 90, 60)); y += 16
    words = status_msg.split()
    line_str, lines_out = "", []
    for w in words:
        test = (line_str + " " + w).strip()
        if font_small.size(test)[0] < PANEL_WIDTH - 28:
            line_str = test
        else:
            lines_out.append(line_str)
            line_str = w
    lines_out.append(line_str)
    for ln in lines_out[:4]:
        txt(ln, px + 14, y, color=status_color); y += 16


# ── A* animation ─────────────────────────────────────────────────────────────
def run_astar_animation():
    global path, no_path_cells, explored_cells
    global efficiency_grade, status_msg, status_color, is_running

    is_running       = True
    path             = []
    no_path_cells    = set()
    explored_cells   = set()
    efficiency_grade = ("—", (100, 100, 100))

    # ── Validate prerequisites ────────────────────────────────────────────────
    sources = get_all_water_sources(grid)
    if not sources:
        status_msg   = "No water source found!"
        status_color = (200, 30, 30)
        is_running   = False
        return

    crops = get_all_crops(grid)
    if not crops:
        status_msg   = "No crops to irrigate!"
        status_color = (200, 30, 30)
        is_running   = False
        return

    # Sort by priority: high ! → normal → low v
    crops = sort_crops_by_priority(crops, grid)

    # ── Phase 1: compute all A* paths ─────────────────────────────────────────
    status_msg   = f"Computing A* for {len(crops)} crops…"
    status_color = (30, 80, 180)
    _refresh_display()
    pygame.display.flip()

    segments: list  = []
    failed:   int   = 0
    current:  tuple | None = None

    for crop in crops:
        if current is None:
            # First segment: pick the closest water source automatically
            seg, exp, _ = astar_best_source(grid, sources, crop)
        else:
            # Subsequent segments: continue from last irrigated crop
            seg, exp = astar(grid, current, crop)

        explored_cells |= exp

        if seg:
            segments.append(seg)
            current = crop
        else:
            no_path_cells.add(crop)
            failed += 1

    # ── Phase 2: animate paths step-by-step ──────────────────────────────────
    delay      = SPEED_LEVELS[speed_idx]
    total_path: list = []

    for seg in segments:
        for step in seg:
            total_path.append(step)
            path = list(total_path)   # keep global in sync for panel stats

            if delay > 0:
                _refresh_display()

                # Moving robot dot on current cell
                r2, c2 = step
                cx = c2 * CELL_SIZE + OFFSET_X + CELL_SIZE // 2
                cy = r2 * CELL_SIZE + OFFSET_Y + CELL_SIZE // 2
                pygame.draw.circle(screen, (0, 200, 255), (cx, cy), 10)
                pygame.draw.circle(screen, (255, 255, 255), (cx, cy), 4)

                pygame.display.update()
                pygame.time.delay(delay)

                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit(); exit()

    path = total_path

    # ── Compute final efficiency grade ────────────────────────────────────────
    crops_done = len(crops) - failed
    _, grade_lbl, grade_col = compute_efficiency(crops_done, len(path))
    efficiency_grade = (grade_lbl, grade_col)

    if failed == 0:
        status_msg   = (f"Done! {len(crops)} crops irrigated. "
                        f"Path: {len(path)} steps.  Grade: {grade_lbl}")
        status_color = (20, 130, 20)
    else:
        status_msg   = (f"Irrigated {crops_done}/{len(crops)} crops. "
                        f"{failed} unreachable.  Grade: {grade_lbl}")
        status_color = (180, 100, 10)

    is_running = False


# ── Main loop ─────────────────────────────────────────────────────────────────
running    = True
mouse_down = False
hover_cell = None

while running:
    clock.tick(60)

    mx, my     = pygame.mouse.get_pos()
    hover_cell = pixel_to_cell(mx, my) if mx < MAP_WIDTH else None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # ── Keyboard ──────────────────────────────────────────────────────────
        if event.type == pygame.KEYDOWN and not is_running:
            k = event.key

            if k == pygame.K_ESCAPE:
                mode         = MODE_NONE
                status_msg   = "Mode cleared."
                status_color = (60, 60, 60)

            elif k == pygame.K_o:
                set_mode(MODE_OBSTACLE)
                status_msg   = "Obstacle mode. Click to place rocks."
                status_color = (160, 60, 10)

            elif k == pygame.K_c:
                set_mode(MODE_CROP)
                status_msg   = "Normal crop mode."
                status_color = (20, 120, 30)

            elif k == pygame.K_h:
                set_mode(MODE_CROP_HIGH)
                status_msg   = "High-priority crop (!) — irrigated first."
                status_color = (180, 70, 10)

            elif k == pygame.K_l:
                set_mode(MODE_CROP_LOW)
                status_msg   = "Low-priority crop (v) — irrigated last."
                status_color = (120, 115, 10)

            elif k == pygame.K_w:
                set_mode(MODE_WATER)
                status_msg   = "Water source mode. Add extra sources!"
                status_color = (20, 60, 180)

            elif k == pygame.K_e:
                set_mode(MODE_ERASE)
                status_msg   = "Erase mode. Click cells to remove."
                status_color = (160, 20, 20)

            elif k == pygame.K_r:
                grid             = create_grid()
                path             = []
                no_path_cells    = set()
                explored_cells   = set()
                efficiency_grade = ("—", (100, 100, 100))
                mode             = MODE_NONE
                status_msg       = "Grid reset."
                status_color     = (30, 100, 30)

            elif k == pygame.K_x:
                show_explored = not show_explored
                status_msg    = f"Explored nodes: {'ON' if show_explored else 'OFF'}."
                status_color  = (60, 60, 130)

            # Speed up  (+  or  =  or numpad +)
            elif k in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                speed_idx    = min(speed_idx + 1, len(SPEED_LEVELS) - 1)
                status_msg   = f"Speed: {SPEED_LABELS[speed_idx]}."
                status_color = (60, 60, 60)

            # Slow down  (-  or numpad -)
            elif k in (pygame.K_MINUS, pygame.K_KP_MINUS):
                speed_idx    = max(speed_idx - 1, 0)
                status_msg   = f"Speed: {SPEED_LABELS[speed_idx]}."
                status_color = (60, 60, 60)

            elif k == pygame.K_s:
                ok           = save_grid_to_file()
                status_msg   = "Grid saved!" if ok else "Save failed!"
                status_color = (30, 100, 30) if ok else (180, 30, 30)

            elif k == pygame.K_f:
                loaded = load_grid_from_file()
                if loaded:
                    grid             = loaded
                    path             = []
                    no_path_cells    = set()
                    explored_cells   = set()
                    efficiency_grade = ("—", (100, 100, 100))
                    status_msg       = "Grid loaded from file!"
                    status_color     = (30, 100, 30)
                else:
                    status_msg       = "No save file found."
                    status_color     = (180, 30, 30)

            elif k == pygame.K_a:
                run_astar_animation()

        # ── Mouse button tracking ─────────────────────────────────────────────
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_down = True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            mouse_down = False

    # ── Continuous painting while mouse held ──────────────────────────────────
    if mouse_down and not is_running and hover_cell:
        r, c    = hover_cell
        changed = False

        if mode == MODE_OBSTACLE and grid[r][c] not in (WATER,):
            grid[r][c] = OBSTACLE;  changed = True

        elif mode == MODE_CROP and grid[r][c] == EMPTY:
            grid[r][c] = CROP;      changed = True

        elif mode == MODE_CROP_HIGH and grid[r][c] == EMPTY:
            grid[r][c] = CROP_HIGH; changed = True

        elif mode == MODE_CROP_LOW and grid[r][c] == EMPTY:
            grid[r][c] = CROP_LOW;  changed = True

        elif mode == MODE_WATER and grid[r][c] == EMPTY:
            grid[r][c] = WATER;     changed = True

        elif mode == MODE_ERASE:
            sources = get_all_water_sources(grid)
            if grid[r][c] != WATER:
                grid[r][c] = EMPTY; changed = True
            elif len(sources) > 1:          # allow removing extra water sources
                grid[r][c] = EMPTY; changed = True

        if changed:
            path             = []
            no_path_cells    = set()
            explored_cells   = set()
            efficiency_grade = ("—", (100, 100, 100))

    # ── Render ────────────────────────────────────────────────────────────────
    screen.fill(BACKGROUND_COLOR)
    draw_grid(screen, grid, path, no_path_cells,
              explored_cells if show_explored else set(),
              show_explored, hover_cell, mode, font_small)
    draw_panel()
    screen.blit(
        font_title.render("Smart Irrigation AI  —  A* Pathfinding",
                          True, (30, 60, 30)),
        (OFFSET_X, 18)
    )
    pygame.display.flip()

pygame.quit()
