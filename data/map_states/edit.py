"""
The state for editing the individual maps.
"""

import os
import sys
import wx
import pygame as pg

from .. import map_prepare, state_machine
from ..map_components import toolbar, panel, modes

if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


BACKGROUND_COLOR = (30, 40, 50)

LAYERS = ("BG Colors", "BG Tiles", "Water", "Solid",
          "Solid/Fore", "Foreground", "Environment",
          "Enemies", "Items", "Chests", "Push", "Portal")

STANDARDS = LAYERS[1:6]
OTHERS = ("Enemies", "Items", "Chests", "Push")


class MapState(object):
    """
    An instance of this class maintains the primary state for the map
    dictionary and also keeps track of the current selected tile, layer,
    and mode. Most classes have complete access to this object.
    """
    def __init__(self):
        self.new_map()
        self.selected = None
        self.select_image = None
        self.layer = "BG Colors"
        self.mode = "Standard"

    @property
    def mode_layer(self):
        """A convenience for getting the mode and layer at the same time."""
        return (self.mode, self.layer)

    def new_map(self, name=None):
        """Clears the map_dict so the user can edit a blank map."""
        self.map_dict = {layer:{} for layer in LAYERS}
        self.map_dict["BG Colors"]["fill"] = (0,0,0)

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
        self.mode_dict = {"Standard" : modes.Standard(self.map_state),
                          "Enemies" : modes.Enemies(self.map_state),
                          "Items" : modes.Items(self.map_state),
                          "Specials" : modes.Special(self.map_state)}
        self.mode = self.mode_dict[self.map_state.mode]

    def set_toolbar_bindings(self):
        """Bind necessary callbacks to appropriate toolbar widgets."""
        for nav in self.toolbar.navs:
            nav.bind(self.change_panel)
        self.toolbar.layer_select.bind(self.map_state.change_layer)
        self.toolbar.mode_select.bind(self.map_state.change_mode)
        self.toolbar.save_button.bind(self.save_map)
        self.toolbar.load_button.bind(self.load_map)
        self.toolbar.new_button.bind(self.map_state.new_map)

    def save_map(self, name):
        """Save current map dict using a wx FileDialog."""
        directory = os.path.join(".", "resources", "map_data")
        wx_app = wx.App(False)
        ask = wx.FileDialog(None, "Save As",directory, "",
                            "Map files (*.map)|*.map",
                            wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT|wx.STAY_ON_TOP)
        ask.ShowModal()
        path = ask.GetPath()
        if path:
            try:
                with open(path,"w") as myfile:
                    yaml.dump(self.map_state.map_dict, myfile)
                    print("Map saved.")
            except IOError:
                print("Invalid filename.")
        else:
            print("File name not entered. Data not saved.")
        self.toolbar.save_button.unpress()

    def load_map(self, name):
        """Load map from file using a wx FileDialog."""
        directory = os.path.join(".", "resources", "map_data")
        wx_app = wx.App(False)
        ask = wx.FileDialog(None, "Open", directory, "",
                            "Map files (*.map)|*.map",
                            wx.FD_OPEN|wx.FD_FILE_MUST_EXIST|wx.STAY_ON_TOP)
        ask.ShowModal()
        path = ask.GetPath()
        if path:
            try:
                with open(path) as myfile:
                    self.map_state.map_dict.update(yaml.load(myfile))
                    print("Map loaded.\n")
            except IOError:
                print("File not found.")
        else:
            print("Filename not entered.  Cannot load data.")
        self.toolbar.load_button.unpress()

    def change_panel(self, name):
        """Callback function passed to the toolbar nav buttons."""
        increment = toolbar.NAVIGATION_DIRECTION[name]
        panel = self.mode.active_panel
        panel.index = (panel.index+increment)%len(panel.pages)

    def update(self, keys, now):
        """Update current mode and toolbar."""
        self.now = now
        try:
            self.mode = self.mode_dict[self.map_state.mode]
        except KeyError:
            self.map_state.change_mode("Standard")
            self.mode = self.mode_dict[self.map_state.mode]
        self.mode.update(keys, now)
        if not self.mode.waiting:
            self.toolbar.update(keys, now)
            self.reset_cursor()

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        self.mode.get_event(event)
        if not self.mode.waiting:
            self.toolbar.get_event(event)

    def draw(self, surface, interpolate):
        """Draw the entire map, panel, and toolbar to the surface."""
        visibility = self.toolbar.check_boxes.state
        surface.fill(BACKGROUND_COLOR)
        self.draw_color_layer(surface, visibility["BG Colors"])
        for layer in LAYERS:
            if (layer in STANDARDS and visibility[layer]) or layer in OTHERS:
                self.draw_normal_layer(surface, layer)
        self.mode.draw(surface, interpolate)
        self.toolbar.draw(surface)
        if self.map_state.selected:
            surface.blit(self.map_state.select_image, (25,185))

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
            map_string, source = layer_dict[coords][0:2]
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
