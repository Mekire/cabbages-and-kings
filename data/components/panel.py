import pygame as pg

from .. import tools, map_prepare
from .map_gui_widgets import Button


MIN_SCROLL = -302
MAX_SCROLL =  100
SCROLL_SPEED = 20.0

PULL_TAB = map_prepare.GFX["misc"]["pull"]
ARROWS = map_prepare.GFX["misc"]["arrows"]

CLEAR_BLUE = (50, 100, 255, 55)


class Panel(object):
    def __init__(self, map_state, pages):
        self.map_state = map_state
        self.pages = pages
        self.index = 0
        self.rect = self.map_state.panel_rect
        self.image = self.make_panel()
        self.arrows = [ARROWS, pg.transform.flip(ARROWS, True, False)]

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
        self.rect.x += SCROLL_SPEED*self.map_state.scroll_direction
        self.rect.x = min(max(self.rect.x, MIN_SCROLL), MAX_SCROLL)
        if self.rect.x == MIN_SCROLL:
            self.visible = False
        if self.rect.x in (MIN_SCROLL, MAX_SCROLL):
            self.map_state.scrolling = False
            self.map_state.scroll_direction *= -1

    def get_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.toggle_scroll()
        elif event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.pull_rect.collidepoint(event.pos):
                    self.toggle_scroll()

    def toggle_scroll(self):
        self.map_state.scrolling = True
        self.map_state.visible = True

    def update(self, keys, now):
        if self.map_state.visible and self.map_state.scrolling:
            self.do_scroll()
        self.pages[self.index].update(keys, now, self.rect)

    def draw(self, surface, interpolate):
        scroll_direction = self.map_state.scroll_direction
        if self.map_state.visible and self.map_state.scrolling:
            pos = self.rect.copy()
            pos.x += SCROLL_SPEED*scroll_direction*interpolate
            pos.x = min(max(self.rect.x, MIN_SCROLL), MAX_SCROLL)
        else:
            pos = self.rect
        arrow = self.arrows[0] if scroll_direction>0 else self.arrows[1]
        self.pages[self.index].draw(self.image, interpolate)
        surface.blit(self.image, pos)
        surface.blit(arrow, self.arrow_rect)


class PanelPage(object):
    def __init__(self, sheet_name, map_state):
        self.map_state = map_state
        self.sheet_name = sheet_name
        self.image = map_prepare.GFX["mapsheets"][sheet_name]
        self.rect = self.image.get_rect()
        self.cursor = self.make_selector_cursor()

    def update(self, keys, now, panel_rect):
        self.rect.topleft = panel_rect.move(2,2).topleft

    def draw(self, surface, interpolate):
        surface.fill((40,40,40), (2, 2, 400, 600))
        surface.blit(self.image, (2,2))
        self.draw_cursor(surface, self.image)

    def make_selector_cursor(self):
        """Creates the rectangular selector."""
        cursor = pg.Surface(map_prepare.CELL_SIZE).convert_alpha()
        cursor_rect = cursor.get_rect()
        cursor.fill(pg.Color("white"))
        cursor.fill(pg.Color("red"), cursor_rect.inflate(-2,-2))
        cursor.fill(pg.Color("white"), cursor_rect.inflate(-6,-6))
        cursor.fill(CLEAR_BLUE, cursor_rect.inflate(-8,-8))
        return cursor

    def draw_cursor(self, surface, pallet):
        """Draw rectangle cursor when required."""
        point = pg.mouse.get_pos()
        if self.rect.collidepoint(point):
            cell_size = map_prepare.CELL_SIZE
            on_sheet = tools.get_cell_coordinates(self.rect, point, cell_size)
            location = (on_sheet[0]+2, on_sheet[1]+2)
            surface.blit(self.cursor, location)


class BackGroundPage(PanelPage):
    def __init__(self, map_state):
        PanelPage.__init__(self, "background", map_state)
        self.fill_all = Button(name="Fill", rect=pg.Rect(0,0,100,50),
                               selected=False, unclick=True, active=False)

    def update(self, keys, now, panel_rect):
        point = pg.mouse.get_pos()
        if panel_rect.collidepoint(point):
            if pg.mouse.get_cursor() != map_prepare.DROPPER:
                pg.mouse.set_cursor((16,16), (0,15), *map_prepare.DROPPER)
        self.rect.topleft = panel_rect.move(2,2).topleft
        self.reset_cursor(panel_rect)

    def make_selector_cursor(self):
        if pg.mouse.get_cursor() != map_prepare.DROPPER:
            pg.mouse.set_cursor((16,16), (0,15), *map_prepare.DROPPER)

    def draw_cursor(self, *args):
        pass

    def reset_cursor(self, panel_rect):
        point = pg.mouse.get_pos()
        if not panel_rect.collidepoint(point):
            if pg.mouse.get_cursor() != map_prepare.DEFAULT_CURSOR:
                 pg.mouse.set_cursor(*map_prepare.DEFAULT_CURSOR)

