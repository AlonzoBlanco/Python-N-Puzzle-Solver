import pygame
from .constants import PANEL, BORDER, TILE, BLANK, ACCENT, WHITE, DIM, BTN, BTN_H, TILE_FONTS, F

def rrect(surf, color, rect, r=10, bw=0, bc=None):
    pygame.draw.rect(surf, color, rect, border_radius=r)
    if bw and bc:
        pygame.draw.rect(surf, bc, rect, bw, border_radius=r)

def txt(surf, text, font, color, pos, anchor="topleft"):
    img = font.render(text, True, color)
    surf.blit(img, img.get_rect(**{anchor: pos}))
    return img.get_rect(**{anchor: pos})

def draw_board(surf, state, size, cx, cy, tile_sz):
    """Draw puzzle board centred at (cx, cy)."""
    gap   = 5
    total = size * tile_sz + (size - 1) * gap
    ox    = cx - total // 2
    oy    = cy - total // 2
    pad   = 12
    rrect(surf, PANEL,
          (ox - pad, oy - pad, total + 2*pad, total + 2*pad),
          r=14, bw=2, bc=BORDER)
    tf = TILE_FONTS[size]
    for idx, tile in enumerate(state):
        row, col = divmod(idx, size)
        x = ox + col * (tile_sz + gap)
        y = oy + row * (tile_sz + gap)
        rect = pygame.Rect(x, y, tile_sz, tile_sz)
        if tile == 0:
            rrect(surf, BLANK, rect, r=9)
        else:
            rrect(surf, TILE, rect, r=9)
            lbl = tf.render(str(tile), True, WHITE)
            surf.blit(lbl, lbl.get_rect(center=rect.center))


class Button:
    def __init__(self, rect, label, c=BTN, ch=BTN_H, font=None, enabled=True):
        self.rect    = pygame.Rect(rect)
        self.label   = label
        self.c       = c
        self.ch      = ch
        self.font    = font or F["md"]
        self.enabled = enabled
        self._hov    = False

    def update(self, mpos):
        self._hov = self.rect.collidepoint(mpos) and self.enabled

    def clicked(self, ev):
        if not self.enabled:
            return False
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            return self.rect.collidepoint(ev.pos)
        return False

    def draw(self, surf):
        col = (self.ch if self._hov else self.c) if self.enabled else PANEL
        bc  = ACCENT if self.enabled else BORDER
        rrect(surf, col, self.rect, r=9, bw=1, bc=bc)
        tc = WHITE if self.enabled else DIM
        txt(surf, self.label, self.font, tc, self.rect.center, anchor="center")
