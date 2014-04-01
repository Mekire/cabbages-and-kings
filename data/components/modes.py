import pygame as pg

from .. import tools, map_prepare
from . import panel


BASIC = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
         "forest", "misc", "tatami")


class Standard(object):
    def __init__(self, map_state):
        self.map_state = map_state
        self.make_panels()

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

    def get_event(self, event):
        self.active_panel.get_event(event)

    def draw(self, surface, interpolate):
        self.active_panel.draw(surface, interpolate)
