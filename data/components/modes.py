import pygame as pg

from .. import tools, map_prepare
from . import panel


BASIC = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
         "forest", "misc", "tatami")


class Standard(object):
    def __init__(self, map_state):
        self.map_state = map_state
        self.make_panels()
        self.reset_add_del()

    def make_panels(self):
        normal_pages = [panel.PanelPage(s, self.map_state) for s in BASIC]
        self.panel = panel.Panel(self.map_state, normal_pages)
        background_page = [panel.BackGroundPage(self.map_state)]
        self.background_panel = panel.Panel(self.map_state, background_page)

    @property
    def active_panel(self):
        layer = self.map_state.layer
        if layer != "BG Colors":
            return self.panel
        else:
            return self.background_panel

    def update(self, keys, now):
        self.active_panel.update(keys, now)
        if self.adding:
            self.add_tile(pg.mouse.get_pos())
        elif self.deleting:
            self.del_tile(pg.mouse.get_pos())

    def get_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if map_prepare.MAP_RECT.collidepoint(event.pos):
                    self.set_adding(event.pos)
            elif event.button == 3:
                if map_prepare.MAP_RECT.collidepoint(event.pos):
                    self.deleting = True
        elif event.type == pg.MOUSEBUTTONUP:
            self.reset_add_del()
        self.active_panel.get_event(event)

    def set_adding(self, point):
        panel = self.active_panel
        if not panel.rect.collidepoint(point):
            self.adding = True
            panel.retract()

    def set_deleting(self, point):
        panel = self.active_panel
        if not panel.rect.collidepoint(point):
            self.adding = True
            panel.retract()

    def add_tile(self, point):
        """Called if self.adding flag is set."""
        selected = self.map_state.selected
        map_rect = map_prepare.MAP_RECT
        if selected:
            if map_rect.collidepoint(point):
                size = map_prepare.CELL_SIZE
                point = tools.get_cell_coordinates(map_rect, point, size)
                self.map_state.map_dict[self.map_state.layer][point] = selected

    def del_tile(self, point):
        selected = self.map_state.selected
        map_rect = map_prepare.MAP_RECT
        if map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            point = tools.get_cell_coordinates(map_rect, point, size)
            self.map_state.map_dict[self.map_state.layer].pop(point, None)

    def reset_add_del(self):
        """Flip both adding and deleting back to False."""
        self.adding = False
        self.deleting = False

    def draw(self, surface, interpolate):
        self.active_panel.draw(surface, interpolate)
