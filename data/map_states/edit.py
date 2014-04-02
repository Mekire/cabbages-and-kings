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

STANDARD_LAYERS = LAYERS[1:6]


BASIC_PANELS = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
                "forest", "misc", "tatami")


class MapState(object):
    def __init__(self):
        self.map_dict = {layer:{} for layer in LAYERS}
        self.map_dict["BG Colors"]["fill"] = (0,0,0)
        self.selected = None
        self.select_image = None
        self.layer = "BG Colors"
        self.mode = "Standard"

    @property
    def mode_layer(self):
        return (self.mode, self.layer)


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
        self.map_state.selected = None
        self.map_state.layer = name

    def change_mode(self, name):
        self.map_state.selected = None
        self.map_state.mode = name

    def update(self, keys, now):
        """Updates the title screen."""
        self.now = now
        self.mode.update(keys, now)
        self.toolbar.update(keys, now)
        self.reset_cursor()

    def draw(self, surface, interpolate):
        surface.fill(BACKGROUND_COLOR)
        for layer in STANDARD_LAYERS:
            self.draw_normal_layer(surface, layer)
        self.mode.draw(surface, interpolate)
        self.toolbar.draw(surface)
        if self.map_state.selected:
            surface.blit(self.map_state.select_image, (25,185))

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        self.mode.get_event(event)
        self.toolbar.get_event(event)

    def draw_normal_layer(self, surface, layer):
        """Draw function for standard layers."""
        layer_dict = self.map_state.map_dict[layer]
        for coords in layer_dict:
            map_string, source_coords = layer_dict[coords][0:2]###
            sheet = map_prepare.GFX["mapsheets"][map_string]
            target = map_prepare.MAP_RECT.x+coords[0], 0+coords[1]
            surface.blit(sheet, target, pg.Rect(source_coords,
                                                map_prepare.CELL_SIZE))

    def reset_cursor(self):
        panel = self.mode.active_panel
        bg_edit = self.map_state.mode_layer == ("Standard", "BG Colors")
        on_panel = panel.rect.collidepoint(pg.mouse.get_pos())
        if not bg_edit or not (panel.is_ready() and on_panel):
            if pg.mouse.get_cursor() != map_prepare.DEFAULT_CURSOR:
                 pg.mouse.set_cursor(*map_prepare.DEFAULT_CURSOR)
