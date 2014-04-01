import pygame as pg

from .. import map_prepare


MIN_SCROLL = -302
MAX_SCROLL =  100
SCROLL_SPEED = 20.0

PULL_TAB = map_prepare.GFX["misc"]["pull"]
ARROWS = map_prepare.GFX["misc"]["arrows"]


class Panel(object):
    def __init__(self, map_state, pages):
        self.map_state = map_state
        self.pages = pages
        self.index = 0
        self.rect = pg.Rect(-302, 48, 420, 604)
        self.image = self.make_panel()
        self.arrows = [ARROWS, pg.transform.flip(ARROWS, True, False)]
        self.scrolling = False
        self.visible = False
        self.scroll_direction = 1

    @property
    def pull_rect(self):
        return PULL_TAB.get_rect(right=self.rect.right-2,
                                 centery=self.rect.centery)

    @property
    def arrow_rect(self):
        pull_rect = self.pull_rect
        return ARROWS.get_rect(centerx=pull_rect.centerx-1,
                               centery=pull_rect.centery)

    def make_panel(self):
        image = pg.Surface(self.rect.size).convert_alpha()
        image.fill((0,0,0,0))
        image.fill(pg.Color("white"), (0,0,404,604))
        image.blit(PULL_TAB, (402, 152))
        return image

    def do_scroll(self):
        """Scroll panel in and out when handle is clicked."""
        self.rect.x += SCROLL_SPEED*self.scroll_direction
        self.rect.x = min(max(self.rect.x, MIN_SCROLL), MAX_SCROLL)
        if self.rect.x == MIN_SCROLL:
            self.visible = False
        if self.rect.x in (MIN_SCROLL, MAX_SCROLL):
            self.scrolling = False
            self.scroll_direction *= -1

    def get_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.toggle_scroll()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.pull_rect.collidepoint(event.pos):
                    self.toggle_scroll()

    def toggle_scroll(self):
        self.scrolling = True
        self.visible = True

    def update(self, keys, now):
        if self.visible and self.scrolling:
            self.do_scroll()

    def draw(self, surface, interpolate):
        if self.visible and self.scrolling:
            pos = self.rect.copy()
            pos.x += SCROLL_SPEED*self.scroll_direction*interpolate
            pos.x = min(max(self.rect.x, MIN_SCROLL), MAX_SCROLL)
        else:
            pos = self.rect
        arrow = self.arrows[0] if self.scroll_direction>0 else self.arrows[1]
        self.pages[self.index].draw(self.image, interpolate)
        surface.blit(self.image, pos)
        surface.blit(arrow, self.arrow_rect)


class PanelPage(object):
    def __init__(self, sheet_name):
        self.sheet_name = sheet_name
        self.image = map_prepare.GFX["mapsheets"][sheet_name]

    def update(self, keys, now):
        pass

    def draw(self, surface, interpolate):
        surface.fill((40,40,40), (2, 2, 400, 600))
        surface.blit(self.image, (2,2))









