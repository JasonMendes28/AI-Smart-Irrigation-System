# config.py

GRID_SIZE = 12
CELL_SIZE = 52

OFFSET_X = 16
OFFSET_Y = 70

MAP_WIDTH   = GRID_SIZE * CELL_SIZE + OFFSET_X * 2
PANEL_WIDTH = 290
WIDTH  = MAP_WIDTH + PANEL_WIDTH
HEIGHT = GRID_SIZE * CELL_SIZE + OFFSET_Y + 40

# ── Cell type constants ───────────────────────────────────────────────────────
EMPTY     = 0
OBSTACLE  = 1
WATER     = 2
CROP      = 3   # normal  priority  (green)
CROP_HIGH = 4   # high    priority  (orange) — irrigated first
CROP_LOW  = 5   # low     priority  (yellow) — irrigated last

ALL_CROPS     = (CROP, CROP_HIGH, CROP_LOW)
CROP_PRIORITY = {CROP_HIGH: 0, CROP: 1, CROP_LOW: 2}   # lower = earlier

# ── Colors ────────────────────────────────────────────────────────────────────
GRID_LINE_COLOR  = (80,  80,  80)
BACKGROUND_COLOR = (240, 245, 240)
PANEL_COLOR      = (230, 235, 228)
PANEL_BORDER     = (100, 130,  90)

# ── UI Mode constants ─────────────────────────────────────────────────────────
MODE_NONE      = "none"
MODE_OBSTACLE  = "obstacle"
MODE_CROP      = "crop"
MODE_CROP_HIGH = "crop_high"
MODE_CROP_LOW  = "crop_low"
MODE_WATER     = "water"
MODE_ERASE     = "erase"

# ── Animation speeds (ms delay per step) ─────────────────────────────────────
SPEED_LEVELS      = [200, 80, 25, 5, 0]
SPEED_LABELS      = ["Slow", "Normal", "Fast", "Turbo", "Instant"]
DEFAULT_SPEED_IDX = 1
