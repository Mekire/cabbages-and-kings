"""
The state for editing the individual maps.
"""

import pygame as pg

from .. import map_prepare, state_machine
from ..components import toolbar, panel, modes


BACKGROUND_COLOR = (30, 40, 50)

LAYERS = ("BG Colors", "BG Tiles", "Water", "Solid",
          "Solid/Fore", "Foreground", "Environment",
          "Enemies", "Items")


BASIC_PANELS = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
                "forest", "misc", "tatami")


class MapState(object):
    def __init__(self):
        self.map_dict = {layer:{} for layer in LAYERS}
        self.map_dict["BG Colors"]["fill"] = (0,0,0)
        self.selected = None
        self.layer = "BG Colors"
        self.mode = "Standard"
        self.panel_rect = pg.Rect(-302, 48, 420, 604)
        self.scrolling = False
        self.visible = False
        self.scroll_direction = 1


class Edit(state_machine._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.map_state = MapState()
        self.toolbar = toolbar.ToolBar()
        self.set_toolbar_bindings()
        self.mode = modes.Standard(self.map_state)

    def set_toolbar_bindings(self):
        self.toolbar.navs[0].bind(self.change_panel)
        self.toolbar.navs[1].bind(self.change_panel)
        self.toolbar.layer_select.bind(self.change_layer)
        self.toolbar.mode_select.bind(self.change_mode)

    def change_panel(self, name):
        increment = toolbar.NAVIGATION_DIRECTION[name]
        panel = self.mode.active_panel
        panel.index = (panel.index+increment)%len(panel.pages)

    def change_layer(self, name):
        self.map_state.layer = name

    def change_mode(self, name):
        self.map_state.mode = name

    def update(self, keys, now):
        """Updates the title screen."""
        self.now = now
        self.mode.update(keys, now)
        self.toolbar.update(keys, now)

    def draw(self, surface, interpolate):
        surface.fill(BACKGROUND_COLOR)
        self.mode.draw(surface, interpolate)
        self.toolbar.draw(surface)

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        self.mode.get_event(event)
        self.toolbar.get_event(event)
