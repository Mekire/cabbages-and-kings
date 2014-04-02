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
    """
    An instance of this class maintains the primary state for the map
    dictionary and also keeps track of the current selected tile, layer,
    and mode. Most classes have complete access to this object.
    """
    def __init__(self):
        self.map_dict = {layer:{} for layer in LAYERS}
        self.map_dict["BG Colors"]["fill"] = (0,0,0)
        self.selected = None
        self.select_image = None
        self.layer = "BG Colors"
        self.mode = "Standard"

    @property
    def mode_layer(self):
        """A convenience for getting the mode and layer at the same time."""
        return (self.mode, self.layer)

    def change_layer(self, name):
        """Change the layer.  Callback for the toolbar layer_select widget."""
        self.selected = None
        self.layer = name

    def change_mode(self, name):
        """Change the mode.  Callback for the toolbar mode_select widget."""
        self.selected = None
        self.mode = name


class Edit(state_machine._State):
    """This is the state for individual map editing."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.map_state = MapState()
        self.toolbar = toolbar.ToolBar(self.map_state)
        self.set_toolbar_bindings()
        self.mode = modes.Standard(self.map_state)

    def set_toolbar_bindings(self):
        """Bind necessary callbacks to appropriate toolbar widgets."""
        self.toolbar.navs[0].bind(self.change_panel)
        self.toolbar.navs[1].bind(self.change_panel)
        self.toolbar.layer_select.bind(self.map_state.change_layer)
        self.toolbar.mode_select.bind(self.map_state.change_mode)

    def change_panel(self, name):
        """Callback function passed to the toolbar nav buttons."""
        increment = toolbar.NAVIGATION_DIRECTION[name]
        panel = self.mode.active_panel
        panel.index = (panel.index+increment)%len(panel.pages)

    def update(self, keys, now):
        """Update current mode and toolbar."""
        self.now = now
        self.mode.update(keys, now)
        self.toolbar.update(keys, now)
        self.reset_cursor()

    def draw(self, surface, interpolate):
        """Draw the entire map, panel, and toolbar to the surface."""
        visibility = self.toolbar.check_boxes.state
        surface.fill(BACKGROUND_COLOR)
        self.draw_color_layer(surface, visibility["BG Colors"])
        for layer in STANDARD_LAYERS:
            if visibility[layer]:
                self.draw_normal_layer(surface, layer)
        self.mode.draw(surface, interpolate)
        self.toolbar.draw(surface)
        if self.map_state.selected:
            surface.blit(self.map_state.select_image, (25,185))

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        self.mode.get_event(event)
        self.toolbar.get_event(event)

    def draw_color_layer(self, surface, visible):
        """The BG_Colors layer requires a unique draw function."""
        map_background_color = self.map_state.map_dict["BG Colors"]["fill"]
        surface.fill(map_background_color, map_prepare.MAP_RECT)
        if visible:
            for coords in self.map_state.map_dict["BG Colors"]:
                if coords != "fill":
                    color = self.map_state.map_dict["BG Colors"][coords][1]
                    target = map_prepare.MAP_RECT.x+coords[0], coords[1]
                    surface.fill(color, pg.Rect(target, map_prepare.CELL_SIZE))

    def draw_normal_layer(self, surface, layer):
        """Draw function for standard layers."""
        layer_dict = self.map_state.map_dict[layer]
        for coords in layer_dict:
            map_string, source = layer_dict[coords][0:2] ###
            sheet = map_prepare.GFX["mapsheets"][map_string]
            target = map_prepare.MAP_RECT.x+coords[0], coords[1]
            surface.blit(sheet, target, pg.Rect(source, map_prepare.CELL_SIZE))

    def reset_cursor(self):
        """When requirements satisfied, cursor reverts to default arrow."""
        panel = self.mode.active_panel
        bg_edit = self.map_state.mode_layer == ("Standard", "BG Colors")
        on_panel = panel.rect.collidepoint(pg.mouse.get_pos())
        if not bg_edit or not (panel.is_ready() and on_panel):
            if pg.mouse.get_cursor() != map_prepare.DEFAULT_CURSOR:
                 pg.mouse.set_cursor(*map_prepare.DEFAULT_CURSOR)
