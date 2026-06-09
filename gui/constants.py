import pygame

pygame.init()

W, H = 940, 700

PUZZLE_NAMES = {3: "8-Puzzle (3×3)", 4: "15-Puzzle (4×4)", 5: "24-Puzzle (5×5)"}
PUZZLE_DESC  = {
    3: "classic · up to 31 optimal moves · A*",
    4: "moderate · ~80 optimal moves · A*",
    5: "hard · 100+ moves · IDA*",
}
DIFFICULTY_SHUFFLES = {
    "Easy":   {3: 15, 4:  25, 5:  35},
    "Medium": {3: 35, 4:  60, 5:  80},
    "Hard":   {3: 80, 4: 120, 5: 160},
}
DIFFICULTY_WARNINGS_24 = {
    "Easy":   "usually < 5 s",
    "Medium": "may take 10–60 s",
    "Hard":   "may take several minutes",
}
TIME_LIMIT = 600.0   # 10-minute hard cap for 24-puzzle

def _font(size, bold=False):
    for name in ("Segoe UI", "Arial", "DejaVu Sans"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size + 6)

def _mono(size):
    for name in ("Consolas", "Courier New", "DejaVu Sans Mono"):
        try:
            return pygame.font.SysFont(name, size)
        except Exception:
            pass
    return pygame.font.Font(None, size + 6)

F = {
    "hdr":    _font(40, bold=True),
    "lg":     _font(28, bold=True),
    "md":     _font(22),
    "md_b":   _font(22, bold=True),
    "sm":     _font(18),
    "sm_b":   _font(18, bold=True),
    "xs":     _font(15),
    "mono":   _mono(20),
    "t3":     _font(50, bold=True),
    "t4":     _font(38, bold=True),
    "t5":     _font(28, bold=True),
}
TILE_FONTS = {3: F["t3"], 4: F["t4"], 5: F["t5"]}

BG       = ( 11,  17,  34)
PANEL    = ( 21,  29,  52)
BORDER   = ( 44,  64, 100)
TILE     = ( 44,  94, 184)
BLANK    = ( 17,  24,  44)
ACCENT   = ( 68, 194, 234)
WHITE    = (234, 244, 255)
GREEN    = ( 52, 204, 108)
YELLOW   = (255, 204,  52)
RED      = (234,  64,  64)
DIM      = ( 88, 110, 144)
BTN      = ( 36,  70, 144)
BTN_H    = ( 56, 106, 196)
BTN_G    = ( 40, 152,  72)
BTN_G_H  = ( 56, 188,  96)
BTN_R    = (148,  36,  36)
BTN_R_H  = (192,  56,  56)

MAIN      = "main"
PUZ_MENU  = "puz_menu"
DIFF      = "diff"
CUSTOM    = "custom"
PREVIEW   = "preview"
SOLVING   = "solving"
RESULT    = "result"
PLAY_ALL  = "play_all"
PLAY_FL   = "play_fl"
STATS     = "stats"
