import pygame as pg

from .. import tools, map_prepare
from . import panel


BASIC = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
         "forest", "misc", "tatami")


class Standard(object):
    """Standard mode in the primary map editor."""
    def __init__(self, map_state):
        self.map_state = map_state
        self.make_panels()
        self.reset_add_del()

    def make_panels(self):
        """Create necessary panels and their pages."""
        pages = [panel.PanelPage(sheet, self.map_state) for sheet in BASIC]
        self.panel = panel.Panel(self.map_state, pages)
        background_page = [panel.BackGroundPage(self.map_state)]
        self.background_panel = panel.Panel(self.map_state, background_page)

    @property
    def active_panel(self):
        """Get the currently active panel (generally based on layer)."""
        if self.map_state.layer != "BG Colors":
            return self.panel
        else:
            return self.background_panel

    def update(self, keys, now):
        """Update panel and add/delete tiles from map editing window."""
        self.active_panel.update(keys, now)
        if self.adding:
            self.add_tile(pg.mouse.get_pos())
        elif self.deleting:
            self.del_tile(pg.mouse.get_pos())

    def get_event(self, event):
        """
        Handle mouse events on map editing window and pass event on to the
        panel window.
        """
        if event.type == pg.MOUSEBUTTONDOWN:
            if map_prepare.MAP_RECT.collidepoint(event.pos):
                if event.button == 1:
                    self.set_add_del(event.pos, "adding")
                elif event.button == 3:
                    self.set_add_del(event.pos, "deleting")
        elif event.type == pg.MOUSEBUTTONUP:
            self.reset_add_del()
        self.active_panel.get_event(event)

    def set_add_del(self, point, attribute):
        """Set adding or deleting attributes and retract panel."""
        if not self.active_panel.rect.collidepoint(point):
            setattr(self, attribute, True)
            self.active_panel.retract()

    def reset_add_del(self):
        """Flip both adding and deleting back to False."""
        self.adding = False
        self.deleting = False

    def add_tile(self, point):
        """Called in update if self.adding flag is set."""
        selected = self.map_state.selected
        map_rect = map_prepare.MAP_RECT
        if selected:
            if map_rect.collidepoint(point):
                size = map_prepare.CELL_SIZE
                point = tools.get_cell_coordinates(map_rect, point, size)
                self.map_state.map_dict[self.map_state.layer][point] = selected

    def del_tile(self, point):
        """Called in update if self.deleting flag is set."""
        selected = self.map_state.selected
        map_rect = map_prepare.MAP_RECT
        if map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            point = tools.get_cell_coordinates(map_rect, point, size)
            self.map_state.map_dict[self.map_state.layer].pop(point, None)

    def draw(self, surface, interpolate):
        """Draw the currently active panell to the surface."""
        self.active_panel.draw(surface, interpolate)
