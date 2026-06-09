import sys
import math
import time
import threading
import pygame
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from models.puzzle import NPuzzle
from .constants import (
    W, H, F, TILE_FONTS, BG, PANEL, BORDER, ACCENT, WHITE, GREEN, YELLOW, RED, DIM,
    PUZZLE_NAMES, PUZZLE_DESC, DIFFICULTY_SHUFFLES, DIFFICULTY_WARNINGS_24, TIME_LIMIT,
    MAIN, PUZ_MENU, DIFF, CUSTOM, PREVIEW, SOLVING, RESULT, PLAY_ALL, PLAY_FL, STATS,
    BTN_G, BTN_G_H, BTN_R, BTN_R_H, BTN, BTN_H
)
from .components import Button, rrect, txt, draw_board

screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("N-Puzzle Solver")
clock = pygame.time.Clock()

class App:
    def __init__(self):
        self.screen  = MAIN
        self.size    = 3
        self.puzzle  = None
        self.state   = None          # initial puzzle state
        self.path    = None          # solution path
        self.elapsed = 0.0
        self.nodes   = 0

        # playback
        self.step      = 0
        self.autoplay  = False
        self.ap_last   = 0.0
        self.ap_delay  = 0.5         # seconds per step in auto mode

        # solve thread
        self._result   = None        # "pending" | list | "timeout" | "nosol" | "err:…"
        self._thread   = None
        self._t0       = 0.0
        self._algo_mode = "A*"       # "A*", "IDA*", "Compare Both"
        self._stats_a    = None
        self._stats_ida  = None
        self._stats_plot = None      # cached pygame Surface for the plot

        # custom-input
        self.ctext  = ""
        self.cerr   = ""

        # notifications on board-preview screen
        self.note   = ""
        self.note_c = WHITE

        self._make_buttons()

    # ── button factory ────────────────────────────────────────────────────────

    def _make_buttons(self):
        cx   = W // 2
        bw   = 460
        bh   = 52
        bx   = cx - bw // 2

        # MAIN MENU
        ys = [210, 272, 334, 414]
        self.b_main = [
            Button((bx, ys[0], bw, bh),
                   "8-Puzzle (3x3)"),
            Button((bx, ys[1], bw, bh),
                   "15-Puzzle (4x4)"),
            Button((bx, ys[2], bw, bh),
                   "24-Puzzle (5x5)"),
            Button((bx, ys[3], bw, bh),
                   "Quit", c=BTN_R, ch=BTN_R_H),
        ]

        # PUZZLE MENU
        bw2 = 380
        bx2 = cx - bw2 // 2
        self.b_puz = [
            Button((bx2, 260, bw2, bh), "Generate a Random Puzzle",
                   c=BTN_G, ch=BTN_G_H),
            Button((bx2, 322, bw2, bh), "Enter a Custom Puzzle"),
            Button((bx2, 400, bw2, bh), "← Back to Main Menu",
                   c=BTN_R, ch=BTN_R_H),
        ]

        # DIFFICULTY MENU
        diffs = list(DIFFICULTY_SHUFFLES.keys())
        self.b_diff = []
        for i, d in enumerate(diffs):
            y   = 230 + i * 68
            col = BTN
            colh = BTN_H
            self.b_diff.append(Button((bx2, y, bw2, bh), d, c=col, ch=colh))
        self.b_diff.append(Button((bx2, 230 + len(diffs)*68 + 14, bw2, bh),
                                  "← Back", c=BTN_R, ch=BTN_R_H))

        # CUSTOM INPUT
        self.b_cok    = Button((cx - 200, 540, 188, bh), "[OK] Confirm",
                               c=BTN_G, ch=BTN_G_H)
        self.b_cback  = Button((cx +  12, 540, 188, bh), "<- Back",
                               c=BTN_R, ch=BTN_R_H)
        self.b_cclear = Button((cx - 200, 488, 400, 42), "[X] Clear Input")

        # BOARD PREVIEW
        self.b_solve_a = Button((cx - 310, 578, 180, bh), "Solve (A*)",
                                c=BTN_G, ch=BTN_G_H)
        self.b_solve_i = Button((cx - 110, 578, 180, bh), "Solve (IDA*)",
                                c=BTN_G, ch=BTN_G_H)
        self.b_solve_c = Button((cx + 90, 578, 180, bh), "Compare Both",
                                c=BTN, ch=BTN_H)
        self.b_pback   = Button((cx - 100, 640, 200, bh), "<- Back",
                                c=BTN_R, ch=BTN_R_H)

        # RESULT (5 buttons -> 4 buttons)
        rw, rh = 420, 46
        rx = cx - rw // 2
        self.b_res = [
            Button((rx, 348, rw, rh), "Play All Steps"),
            Button((rx, 402, rw, rh), "|<->| First & Last Only"),
            Button((rx, 456, rw, rh), "Show Statistics"),
            Button((rx - 5, 526, rw // 2 - 4, rh), "<- Try Another Puzzle",
                   c=BTN, ch=BTN_H),
            Button((rx + rw // 2 + 9, 526, rw // 2 - 4, rh), "Home",
                   c=BTN_R, ch=BTN_R_H),
        ]

        # STATS screen buttons
        self.b_stats_back = Button((cx - 100, 630, 200, bh), "<- Back to Results")

        # PLAY-ALL controls
        pw  = 130
        gap = 12
        tw  = 4 * pw + 3 * gap
        px0 = cx - tw // 2
        yp  = 608
        self.b_play = [
            Button((px0,                yp, pw, bh), "<- Prev"),
            Button((px0 + pw + gap,     yp, pw, bh), "Next ->"),
            Button((px0 + 2*(pw+gap),   yp, pw, bh), ">> Auto",
                   c=BTN_G, ch=BTN_G_H),
            Button((px0 + 3*(pw+gap),   yp, pw, bh), "[X] Done",
                   c=BTN_R, ch=BTN_R_H),
        ]

        # FIRST/LAST
        self.b_fl_back = Button((cx - 100, 618, 200, bh), "<- Back",
                                c=BTN_R, ch=BTN_R_H)

    # ── active buttons for current screen ─────────────────────────────────────

    def _active_btns(self):
        return {
            MAIN:     self.b_main,
            PUZ_MENU: self.b_puz,
            DIFF:     self.b_diff,
            CUSTOM:   [self.b_cok, self.b_cback, self.b_cclear],
            PREVIEW:  [self.b_solve_a, self.b_solve_i, self.b_solve_c, self.b_pback],
            SOLVING:  [],
            RESULT:   self.b_res,
            STATS:    [self.b_stats_back],
            PLAY_ALL: self.b_play,
            PLAY_FL:  [self.b_fl_back],
        }.get(self.screen, [])

    # ── helpers ───────────────────────────────────────────────────────────────

    def _go(self, s, **kw):
        self.screen = s
        for k, v in kw.items():
            setattr(self, k, v)

    def _notify(self, msg, color=WHITE):
        self.note   = msg
        self.note_c = color

    def _format_time(self, ms_val):
        if ms_val >= 1000:
            return f"{ms_val / 1000.0:.2f} s"
        return f"{ms_val:.1f} ms"

    def _format_mem(self, bytes_val):
        if bytes_val >= 1024**3:
            return f"{bytes_val / (1024**3):.2f} GB"
        elif bytes_val >= 1024**2:
            return f"{bytes_val / (1024**2):.2f} MB"
        elif bytes_val >= 1024:
            return f"{bytes_val / 1024:.2f} KB"
        return f"{bytes_val:,} bytes"

    # ── solve thread ──────────────────────────────────────────────────────────

    def _start_solve(self, mode):
        self._algo_mode = mode
        self._result = "pending"
        self._stats_a = None
        self._stats_ida = None
        self._stats_plot = None
        self.puzzle  = NPuzzle(self.size)

        def worker():
            try:
                t0 = time.perf_counter()
                if mode == "A*":
                    res = self.puzzle.solve(self.state, algorithm="A*", time_limit=TIME_LIMIT)
                    self._stats_a = res
                    self._result = res if res and res.status != "No Solution" else "nosol"
                elif mode == "IDA*":
                    res = self.puzzle.solve(self.state, algorithm="IDA*", time_limit=TIME_LIMIT)
                    self._stats_ida = res
                    self._result = res if res and res.status != "No Solution" else "nosol"
                elif mode == "Compare Both":
                    res_a = self.puzzle.solve(self.state, algorithm="A*", time_limit=TIME_LIMIT)
                    self._stats_a = res_a
                    res_ida = self.puzzle.solve(self.state, algorithm="IDA*", time_limit=TIME_LIMIT)
                    self._stats_ida = res_ida
                    
                    if res_ida and res_ida.status != "No Solution":
                        self._result = res_ida
                    elif res_a and res_a.status != "No Solution":
                        self._result = res_a
                    else:
                        self._result = "nosol"
            except TimeoutError:
                self._result = "timeout"
            except Exception as e:
                self._result = f"err:{e}"

        self._t0          = time.perf_counter()
        self._thread      = threading.Thread(target=worker, daemon=True)
        self._thread.start()
        self._go(SOLVING)

    def _poll_solve(self):
        if self.screen != SOLVING or self._result == "pending":
            return
        r = self._result
        if r == "timeout":
            self._notify(
                f"[!] Time limit ({int(TIME_LIMIT)} s) reached. Try an easier difficulty.",
                YELLOW)
            self._go(PREVIEW)
        elif r == "nosol":
            self._notify("[!] No solution found (puzzle was reported solvable — this is a bug).", RED)
            self._go(PREVIEW)
        elif isinstance(r, str) and r.startswith("err:"):
            self._notify(f"[!] Error: {r[4:]}", RED)
            self._go(PREVIEW)
        else:
            self.path    = r.path
            self.elapsed = r.time_ms / 1000.0
            self.nodes   = r.nodes_expanded
            self._go(RESULT)

    # ── event handling ────────────────────────────────────────────────────────

    def handle(self, ev):
        s = self.screen

        # ── MAIN ────────────────────────────────────────────────────────────
        if s == MAIN:
            sizes = [3, 4, 5]
            for i, b in enumerate(self.b_main[:3]):
                if b.clicked(ev):
                    self.size = sizes[i]
                    self.note = ""
                    self._go(PUZ_MENU)
                    return
            if self.b_main[3].clicked(ev):
                pygame.quit(); sys.exit()

        # ── PUZZLE MENU ──────────────────────────────────────────────────────
        elif s == PUZ_MENU:
            if self.b_puz[0].clicked(ev):
                self._go(DIFF)
            elif self.b_puz[1].clicked(ev):
                self.ctext = ""; self.cerr = ""
                self._go(CUSTOM)
            elif self.b_puz[2].clicked(ev):
                self._go(MAIN)

        # ── DIFFICULTY ───────────────────────────────────────────────────────
        elif s == DIFF:
            diffs = list(DIFFICULTY_SHUFFLES.keys())
            for i, b in enumerate(self.b_diff[:-1]):
                if b.clicked(ev):
                    diff  = diffs[i]
                    nshu  = DIFFICULTY_SHUFFLES[diff][self.size]
                    p     = NPuzzle(self.size)
                    self.state = p.generate(nshu)
                    self.note  = (f"Generated with {nshu} random shuffles  ({diff})")
                    self.note_c = DIM
                    self._go(PREVIEW)
                    return
            if self.b_diff[-1].clicked(ev):
                self._go(PUZ_MENU)

        # ── CUSTOM INPUT ─────────────────────────────────────────────────────
        elif s == CUSTOM:
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_BACKSPACE:
                    self.ctext = self.ctext[:-1]
                elif ev.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._confirm_custom()
                elif ev.unicode and (ev.unicode.isdigit() or ev.unicode in " ,"):
                    self.ctext += ev.unicode
            if self.b_cok.clicked(ev):
                self._confirm_custom()
            elif self.b_cback.clicked(ev):
                self._go(PUZ_MENU)
            elif self.b_cclear.clicked(ev):
                self.ctext = ""; self.cerr = ""

        # ── BOARD PREVIEW ────────────────────────────────────────────────────
        elif s == PREVIEW:
            if self.b_solve_a.clicked(ev):
                if not NPuzzle(self.size).is_solvable(self.state):
                    self._notify("This configuration is unsolvable.", RED)
                    return
                self.note = ""
                self._start_solve("A*")
            elif self.b_solve_i.clicked(ev):
                if not NPuzzle(self.size).is_solvable(self.state):
                    self._notify("This configuration is unsolvable.", RED)
                    return
                self.note = ""
                self._start_solve("IDA*")
            elif self.b_solve_c.clicked(ev):
                if not NPuzzle(self.size).is_solvable(self.state):
                    self._notify("This configuration is unsolvable.", RED)
                    return
                self.note = ""
                self._start_solve("Compare Both")
            elif self.b_pback.clicked(ev):
                self._go(PUZ_MENU)

        # ── RESULT ───────────────────────────────────────────────────────────
        elif s == RESULT:
            total = len(self.path) - 1
            if self.b_res[0].clicked(ev):           # all steps
                if total > 0:
                    self.step = 0; self.autoplay = False
                    self._go(PLAY_ALL)
            elif self.b_res[1].clicked(ev):         # first+last
                if total > 0:
                    self._go(PLAY_FL)
            elif self.b_res[2].clicked(ev):         # show statistics
                self._go(STATS)
            elif self.b_res[3].clicked(ev):         # try another
                self._go(PUZ_MENU)
            elif self.b_res[4].clicked(ev):         # main menu
                self._go(MAIN)
                
        # ── STATS ────────────────────────────────────────────────────────────
        elif s == STATS:
            if self.b_stats_back.clicked(ev):
                self._go(RESULT)

        # ── PLAY ALL ─────────────────────────────────────────────────────────
        elif s == PLAY_ALL:
            total = len(self.path) - 1
            if self.b_play[0].clicked(ev):
                self.step = max(0, self.step - 1); self.autoplay = False
            elif self.b_play[1].clicked(ev):
                self.step = min(total, self.step + 1); self.autoplay = False
            elif self.b_play[2].clicked(ev):
                self.autoplay = not self.autoplay
                self.ap_last  = time.perf_counter()
            elif self.b_play[3].clicked(ev):
                self.autoplay = False; self._go(RESULT)
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_RIGHT, pygame.K_SPACE):
                    self.step = min(total, self.step + 1)
                elif ev.key == pygame.K_LEFT:
                    self.step = max(0, self.step - 1)
                elif ev.key == pygame.K_HOME:
                    self.step = 0
                elif ev.key == pygame.K_END:
                    self.step = total
                elif ev.key == pygame.K_ESCAPE:
                    self.autoplay = False; self._go(RESULT)

        # ── PLAY FIRST/LAST ───────────────────────────────────────────────────
        elif s == PLAY_FL:
            if self.b_fl_back.clicked(ev):
                self._go(RESULT)
            elif ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                self._go(RESULT)

    def _confirm_custom(self):
        n   = self.size * self.size
        raw = self.ctext.replace(",", " ").split()
        try:
            tiles = [int(x) for x in raw]
        except ValueError:
            self.cerr = "Non-integer value found — use only digits."; return
        if len(tiles) != n:
            self.cerr = f"Need exactly {n} numbers, got {len(tiles)}."; return
        if sorted(tiles) != list(range(n)):
            self.cerr = f"Must use each of 0–{n-1} exactly once."; return
        state = tuple(tiles)
        if not NPuzzle(self.size).is_solvable(state):
            self.cerr = "This configuration is unsolvable."; return
        self.state = state
        self.cerr  = ""
        self.note  = "Custom puzzle loaded."
        self.note_c = DIM
        self._go(PREVIEW)

    # ── auto-play ticker ──────────────────────────────────────────────────────

    def _tick_autoplay(self):
        if self.screen != PLAY_ALL or not self.autoplay:
            return
        now   = time.perf_counter()
        total = len(self.path) - 1
        if now - self.ap_last >= self.ap_delay:
            self.ap_last = now
            if self.step < total:
                self.step += 1
            else:
                self.autoplay = False

    # =========================================================================
    #  Drawing
    # =========================================================================

    def draw(self):
        screen.fill(BG)
        {
            MAIN:     self._d_main,
            PUZ_MENU: self._d_puz_menu,
            DIFF:     self._d_diff,
            CUSTOM:   self._d_custom,
            PREVIEW:  self._d_preview,
            SOLVING:  self._d_solving,
            RESULT:   self._d_result,
            STATS:    self._d_stats,
            PLAY_ALL: self._d_play_all,
            PLAY_FL:  self._d_play_fl,
        }.get(self.screen, lambda: None)()

    # ── shared header ─────────────────────────────────────────────────────────

    def _header(self, title, sub=""):
        txt(screen, title, F["hdr"], ACCENT, (W//2, 48), anchor="center")
        if sub:
            txt(screen, sub, F["sm"],  DIM,    (W//2, 96), anchor="center")
        pygame.draw.line(screen, BORDER, (60, 118), (W - 60, 118), 1)

    # ── MAIN ──────────────────────────────────────────────────────────────────

    def _d_main(self):
        self._header("N-Puzzle Solver",
                     "Sliding tile puzzles  ·  A* and IDA*  ·  Manhattan + Linear Conflict")
        txt(screen, "Select Puzzle Type", F["md_b"], WHITE, (W//2, 174), anchor="center")
        for b in self.b_main:
            b.draw(screen)

    # ── PUZZLE MENU ───────────────────────────────────────────────────────────

    def _d_puz_menu(self):
        name = PUZZLE_NAMES[self.size]
        desc = PUZZLE_DESC[self.size]
        self._header(name, desc)
        for b in self.b_puz:
            b.draw(screen)
        if self.size == 5:
            rrect(screen, (60, 50, 10), (W//2 - 300, 450, 600, 44), r=8, bw=1, bc=(100, 80, 20))
            txt(screen,
                "[!] IDA* may take a while on complex 24-puzzle configurations.",
                F["sm"], YELLOW, (W//2, 472), anchor="center")

    # ── DIFFICULTY ────────────────────────────────────────────────────────────

    def _d_diff(self):
        self._header(PUZZLE_NAMES[self.size], "Difficulty controls how many random shuffles are applied")
        diffs = list(DIFFICULTY_SHUFFLES.keys())
        for i, b in enumerate(self.b_diff[:-1]):
            b.draw(screen)
            d    = diffs[i]
            nshu = DIFFICULTY_SHUFFLES[d][self.size]
            note = DIFFICULTY_WARNINGS_24[d] if self.size == 5 else f"{nshu} shuffle steps"
            txt(screen, note, F["xs"], DIM,
                (b.rect.right + 16, b.rect.centery), anchor="midleft")
        self.b_diff[-1].draw(screen)

    # ── CUSTOM INPUT ──────────────────────────────────────────────────────────

    def _d_custom(self):
        n = self.size * self.size
        self._header(f"Custom  {PUZZLE_NAMES[self.size]}",
                     f"Enter {n} integers (0 = blank) — space- or comma-separated")

        txt(screen,
            f"Must include each number from 0 to {n - 1} exactly once.",
            F["sm"], DIM, (W//2, 145), anchor="center")

        # Input box
        box = pygame.Rect(W//2 - 340, 168, 680, 52)
        rrect(screen, PANEL, box, r=9, bw=2, bc=ACCENT)
        raw = self.ctext
        if not raw:
            txt(screen, "e.g.  1 2 3 4 5 6 7 8 0",
                F["mono"], DIM, (box.x + 14, box.centery), anchor="midleft")
        else:
            tw  = F["mono"].size(raw)[0]
            max_w = box.width - 28
            img = F["mono"].render(raw, True, WHITE)
            if tw > max_w:
                clip = pygame.Surface((max_w, img.get_height()), pygame.SRCALPHA)
                clip.blit(img, (max_w - tw, 0))
                screen.blit(clip, (box.x + 14, box.centery - clip.get_height()//2))
            else:
                txt(screen, raw, F["mono"], WHITE, (box.x + 14, box.centery), anchor="midleft")
        # cursor blink
        if int(time.perf_counter() * 2) % 2 == 0:
            cw = min(F["mono"].size(raw)[0], box.width - 28)
            cx_, cy_ = box.x + 14 + cw, box.centery
            pygame.draw.line(screen, ACCENT, (cx_, cy_ - 14), (cx_, cy_ + 14), 2)

        # Live count + mini-preview
        valid = []
        for x in raw.replace(",", " ").split():
            try:
                valid.append(int(x))
            except ValueError:
                break

        y_info = 238
        if valid:
            col_c = GREEN if len(valid) == n else DIM
            txt(screen, f"Tiles entered:  {len(valid)} / {n}",
                F["sm"], col_c, (W//2, y_info), anchor="center")

        # Mini board preview when complete
        if len(valid) == n and sorted(valid) == list(range(n)):
            ts_mini = {3: 52, 4: 40, 5: 32}[self.size]
            draw_board(screen, tuple(valid), self.size, W//2, 355, ts_mini)

        # Error / hint
        if self.cerr:
            txt(screen, f"[!] {self.cerr}", F["sm"], RED, (W//2, 460), anchor="center")

        self.b_cclear.draw(screen)
        self.b_cok.draw(screen)
        self.b_cback.draw(screen)

    # ── BOARD PREVIEW ─────────────────────────────────────────────────────────

    def _d_preview(self):
        name = PUZZLE_NAMES[self.size]
        self._header(f"Initial State  —  {name}")

        ts = {3: 115, 4: 88, 5: 70}[self.size]
        draw_board(screen, self.state, self.size, W//2, 330, ts)

        is_sol = NPuzzle(self.size).is_solvable(self.state)
        if is_sol:
            txt(screen, "[OK] Puzzle is solvable",   F["sm_b"], GREEN, (W//2, 533), anchor="center")
        else:
            txt(screen, "[X] Puzzle is unsolvable", F["sm_b"], RED,   (W//2, 533), anchor="center")

        self.b_solve_a.enabled = is_sol and self.size != 5
        self.b_solve_i.enabled = is_sol
        self.b_solve_c.enabled = is_sol and self.size != 5

        if self.note:
            txt(screen, self.note, F["xs"], self.note_c, (W//2, 550), anchor="center")

        if self.size == 5 and is_sol:
            txt(screen,
                f"IDA* search aborts after {int(TIME_LIMIT)} s if no solution. (A* disabled)",
                F["xs"], YELLOW, (W//2, 566), anchor="center")

        self.b_solve_a.draw(screen)
        self.b_solve_i.draw(screen)
        self.b_solve_c.draw(screen)
        self.b_pback.draw(screen)

    # ── SOLVING ───────────────────────────────────────────────────────────────

    def _d_solving(self):
        self._header("Solving…")
        elapsed = time.perf_counter() - self._t0
        dots    = "·" * (int(elapsed * 2) % 4 + 1)

        txt(screen, f"Running solver  {dots}", F["lg"],  ACCENT, (W//2, 245), anchor="center")
        txt(screen, PUZZLE_NAMES[self.size],   F["md"],  DIM,    (W//2, 295), anchor="center")
        algo = "A*" if self.size <= 4 else "IDA*"
        txt(screen,
            f"Algorithm: {algo}   ·   Heuristic: Manhattan Distance + Linear Conflict",
            F["sm"], DIM, (W//2, 335), anchor="center")
        txt(screen, f"Elapsed: {elapsed:.1f} s", F["sm"], DIM, (W//2, 365), anchor="center")

        if self.size == 5:
            txt(screen, f"Time limit: {int(TIME_LIMIT)} s   (IDA* may take a while)",
                F["sm"], YELLOW, (W//2, 400), anchor="center")

        # Spinner
        cx_, cy_ = W//2, 476
        pygame.draw.circle(screen, BORDER, (cx_, cy_), 34, 4)
        angle = (elapsed * 200) % 360
        ax = cx_ + 30 * math.cos(math.radians(angle))
        ay = cy_ + 30 * math.sin(math.radians(angle))
        pygame.draw.line(screen, ACCENT, (cx_, cy_), (int(ax), int(ay)), 4)

        txt(screen, "Please wait — this may take a moment for harder puzzles.",
            F["xs"], DIM, (W//2, 528), anchor="center")

    # ── RESULT ────────────────────────────────────────────────────────────────

    def _d_result(self):
        moves = len(self.path) - 1
        self._header("Solved! [OK]", PUZZLE_NAMES[self.size])

        # Stats card
        card = pygame.Rect(W//2 - 240, 130, 480, 190)
        rrect(screen, PANEL, card, r=14, bw=1, bc=BORDER)

        if moves == 0:
            txt(screen, "The puzzle was already in the goal state.",
                F["md"], DIM, (W//2, 224), anchor="center")
        else:
            rows = [
                ("Moves",           f"{moves}",                  ACCENT),
                ("Nodes Expanded",  f"{self.nodes:,}",           WHITE),
                ("Time",            self._format_time(self.elapsed * 1000), WHITE),
            ]
            for i, (label, val, vc) in enumerate(rows):
                y0 = 160 + i * 50
                txt(screen, label + ":",  F["sm"],   DIM,  (W//2 - 90, y0), anchor="midright")
                txt(screen, val,          F["md_b"], vc,   (W//2 - 80, y0), anchor="midleft")

        # Step display options label
        txt(screen, "Show solution steps?", F["md_b"], WHITE, (W//2, 325), anchor="center")

        # Disable step buttons if already solved
        for b in self.b_res[:2]:
            b.enabled = moves > 0

        for b in self.b_res:
            b.draw(screen)

    # ── STATS ─────────────────────────────────────────────────────────────────

    def _d_stats(self):
        self._header("Statistics", "Algorithm Performance & Resource Usage")
        
        if self._algo_mode != "Compare Both":
            stats = self._stats_a if self._algo_mode == "A*" else self._stats_ida
            if not stats:
                txt(screen, "No stats available.", F["md"], DIM, (W//2, 300), anchor="center")
                self.b_stats_back.draw(screen)
                return
            
            card = pygame.Rect(W//2 - 240, 160, 480, 360)
            rrect(screen, PANEL, card, r=14, bw=1, bc=BORDER)
            txt(screen, f"Algorithm: {stats.algorithm}", F["md_b"], ACCENT, (W//2, 190), anchor="center")
            
            rows = [
                ("Puzzle Size", stats.size),
                ("Heuristic", stats.heuristic),
                ("Solution Length", f"{stats.solution_length} moves"),
                ("Nodes Expanded", f"{stats.nodes_expanded:,}"),
                ("Nodes Generated", f"{stats.nodes_generated:,}"),
                ("Execution Time", self._format_time(stats.time_ms)),
                ("Max Frontier/Depth", f"{stats.max_frontier_or_depth:,}"),
                ("Est. Memory", self._format_mem(stats.memory_usage_est_bytes)),
                ("Status", stats.status)
            ]
            for i, (label, val) in enumerate(rows):
                y = 230 + i * 30
                txt(screen, label + ":", F["sm"], DIM, (W//2 - 20, y), anchor="midright")
                vc = GREEN if label == "Status" and val == "Success" else WHITE
                if label == "Status" and val != "Success":
                    vc = RED
                txt(screen, val, F["sm_b"], vc, (W//2 + 20, y), anchor="midleft")
                
        else:
            sa = self._stats_a
            si = self._stats_ida
            if not sa or not si:
                txt(screen, "Comparison data incomplete.", F["md"], DIM, (W//2, 300), anchor="center")
                self.b_stats_back.draw(screen)
                return
            
            if self._stats_plot is None:
                fig, axs = plt.subplots(2, 2, figsize=(7.5, 4.5), facecolor='#0B1122')
                fig.subplots_adjust(hspace=0.5, wspace=0.3)
                
                labels = ['A*', 'IDA*']
                colors = ['#44C2EA', '#34CC6C']
                
                def plot_bar(ax, title, v1, v2):
                    ax.bar(labels, [v1, v2], color=colors)
                    ax.set_title(title, color='white', fontsize=10)
                    ax.tick_params(colors='white', labelsize=8)
                    ax.set_facecolor('#151D34')
                    for spine in ax.spines.values():
                        spine.set_edgecolor('#2C4064')
                
                mem_max = max(sa.memory_usage_est_bytes, si.memory_usage_est_bytes)
                if mem_max >= 1024**3:
                    mem_unit = "GB"
                    mem_div = 1024**3
                elif mem_max >= 1024**2:
                    mem_unit = "MB"
                    mem_div = 1024**2
                elif mem_max >= 1024:
                    mem_unit = "KB"
                    mem_div = 1024
                else:
                    mem_unit = "bytes"
                    mem_div = 1
                
                time_max = max(sa.time_ms, si.time_ms)
                if time_max >= 1000:
                    time_unit = "s"
                    time_div = 1000.0
                else:
                    time_unit = "ms"
                    time_div = 1.0
                
                plot_bar(axs[0, 0], f'Execution Time ({time_unit})', sa.time_ms / time_div, si.time_ms / time_div)
                plot_bar(axs[0, 1], 'Nodes Expanded', sa.nodes_expanded, si.nodes_expanded)
                plot_bar(axs[1, 0], 'Nodes Generated', sa.nodes_generated, si.nodes_generated)
                plot_bar(axs[1, 1], f'Est. Memory ({mem_unit})', sa.memory_usage_est_bytes / mem_div, si.memory_usage_est_bytes / mem_div)
                
                fig.canvas.draw()
                raw_data = fig.canvas.buffer_rgba()
                size = fig.canvas.get_width_height()
                self._stats_plot = pygame.image.frombuffer(raw_data, size, "RGBA")
                plt.close(fig)
            
            screen.blit(self._stats_plot, (W//2 - self._stats_plot.get_width()//2, 120))
            
            if sa.time_ms < si.time_ms and sa.memory_usage_est_bytes > si.memory_usage_est_bytes:
                conc = "Conclusion: A* was faster but used more memory."
            elif sa.time_ms > si.time_ms and sa.memory_usage_est_bytes < si.memory_usage_est_bytes:
                conc = "Conclusion: IDA* was faster but A* used less memory."
            elif sa.time_ms < si.time_ms and sa.memory_usage_est_bytes < si.memory_usage_est_bytes:
                conc = "Conclusion: A* was faster and used less memory."
            else:
                conc = "Conclusion: IDA* was faster and used less memory."
            txt(screen, conc, F["sm_b"], ACCENT, (W//2, 590), anchor="center")

        self.b_stats_back.draw(screen)

    # ── PLAY ALL ──────────────────────────────────────────────────────────────

    def _d_play_all(self):
        total = len(self.path) - 1
        cur   = self.step

        lbl = "Goal [OK]" if cur == total else f"Move {cur}"
        self._header(f"Step-by-Step  —  {lbl}",
                     f"{PUZZLE_NAMES[self.size]}   ·   {total} total move{'s' if total!=1 else ''}")

        ts = {3: 110, 4: 86, 5: 68}[self.size]
        draw_board(screen, self.path[cur], self.size, W//2, 325, ts)

        # Progress bar
        bw = 520
        bx = W//2 - bw//2
        by = 542
        rrect(screen, BORDER, (bx, by, bw, 9), r=5)
        if total > 0:
            fill = int(bw * cur / total)
            if fill > 0:
                rrect(screen, ACCENT, (bx, by, fill, 9), r=5)
        txt(screen, "Start", F["xs"], DIM, (bx,      by + 14), anchor="topleft")
        txt(screen, "Goal",  F["xs"], DIM, (bx + bw, by + 14), anchor="topright")
        txt(screen, f"{cur} / {total}", F["sm_b"], ACCENT,
            (W//2, by + 14), anchor="center")

        # Auto-play label / keyboard hint
        if self.autoplay:
            txt(screen, ">>  Auto-playing...  press Auto again to pause",
                F["xs"], GREEN, (W//2, 584), anchor="center")
        else:
            txt(screen, "<- -> arrows  ·  Space = next  ·  Home / End  ·  Esc = back",
                F["xs"], DIM, (W//2, 584), anchor="center")

        self.b_play[2].label = "Pause" if self.autoplay else ">> Auto"
        for b in self.b_play:
            b.draw(screen)

    # ── PLAY FIRST / LAST ─────────────────────────────────────────────────────

    def _d_play_fl(self):
        total = len(self.path) - 1
        self._header("First & Last",
                     f"{PUZZLE_NAMES[self.size]}   ·   {total} move{'s' if total!=1 else ''} total")

        # Two boards side-by-side
        if self.size == 5:
            ts = 52
            offx = 232
        else:
            ts   = {3: 82, 4: 64}[self.size]
            offx = 228

        cx_L = W//2 - offx
        cx_R = W//2 + offx

        txt(screen, "Initial State  (Move 0)", F["sm"], DIM, (cx_L, 148), anchor="center")
        draw_board(screen, self.path[0], self.size, cx_L, 330, ts)

        txt(screen, f"Goal State  (Move {total})", F["sm"], DIM, (cx_R, 148), anchor="center")
        draw_board(screen, self.path[-1], self.size, cx_R, 330, ts)

        # Middle annotation
        mid_moves = total - 1
        if mid_moves > 0:
            lbl = f"<->  {mid_moves} intermediate move{'s' if mid_moves != 1 else ''}"
            txt(screen, lbl, F["md_b"], DIM, (W//2, 520), anchor="center")

        self.b_fl_back.draw(screen)

    # =========================================================================
    #  Main loop
    # =========================================================================

    def run(self):
        while True:
            clock.tick(60)
            mpos = pygame.mouse.get_pos()
            for b in self._active_btns():
                b.update(mpos)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                self.handle(ev)

            self._poll_solve()
            self._tick_autoplay()
            self.draw()
            pygame.display.flip()
