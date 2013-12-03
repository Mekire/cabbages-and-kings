"""
Contains the class for our left hand control panel used during individual
map editing.
"""

import pygame as pg

from .. import map_prepare
from .panel import PalletPanel
from .map_gui_widgets import Selector,CheckBoxArray,Button


CELL_SIZE = (50,50)

#Available modes and layers.
MODES = ("Standard","Specials","Events","Enemies","Items","NPCs")

LAYERS = ("Environment","Foreground","Solid/Fore",
          "Solid","Water","BG Tiles","BG Colors")

#Settings for widgets, passed via **kwarg syntax.
MODE_SELECT_SETTINGS = {"content" : MODES,
                        "start" : (0,16),
                        "space" : (0,20),
                        "size" : (100,20),
                        "selected" : "Standard"}

LAYER_SELECT_SETTINGS = {"content" : LAYERS,
                         "start" : (20, map_prepare.SCREEN_RECT.bottom-140),
                         "space" : (0,20),
                         "size" : (80,20),
                         "selected" : "BG Colors"}

CHECK_ARRAY_SETTTINGS = {"content" : LAYERS,
                         "initial" : True,
                         "start" : (0, LAYER_SELECT_SETTINGS["start"][1]),
                         "space" : (0,20)}

NAV_LEFT = {"name" : "<<",
            "rect" : (10, LAYER_SELECT_SETTINGS["start"][1]-55, 40, 20),
            "selected" : False,
            "unclick" : True}

NAV_RIGHT = {"name" : ">>",
             "rect" : (50, LAYER_SELECT_SETTINGS["start"][1]-55, 40, 20),
             "selected" : False,
             "unclick" : True}


#Dictionary of pallet modes to pallet lists.
_TILE_PALLETS = ["base","exttemple","inttemple1","inttemple2",
                 "misc","forest","tatami"]

_BACKGROUND_PALLETS = ["background"]

_ENEMIES = ["enemyplace1","enemyplace2","bossplace1"]

_ITEMS = ["itemplace1","gearplace1"]

PALLETS = {"Tiles" : _TILE_PALLETS,
           "BG Colors" : _BACKGROUND_PALLETS,
           "Enemies" : _ENEMIES,
           "Items" : _ITEMS}

#Use standard tiles if mode is standard and selected layer is in the following.
STANDARD_TILES = ["Foreground","Solid/Fore","Solid","Water","BG Tiles"]

#Used for pallet navigation buttons.
NAVIGATION_DIRECTION = {">>" : 1, "<<" : -1}


class ToolBar(object):
    """A class for our left hand control panel."""
    def __init__(self):
        """Initialize needed settings and create widgets."""
        self.image = map_prepare.GFX["misc"]["interface"]
        self.selected = None
        self.mode = None
        self.layer = None
        self.checkboxes = None
        self.pallet = {"Tiles" : 0,
                       "Enemies" : 0,
                       "Items" : 0}
        self.pallet_panel = PalletPanel(self.change_selected)
        self.make_widgets()

    def make_widgets(self):
        """Create required GUI elements."""
        self.mode_select = Selector(self.change_mode, **MODE_SELECT_SETTINGS)
        self.layer_select = Selector(self.change_layer, **LAYER_SELECT_SETTINGS)
        check_boxes = CheckBoxArray(self.set_checkboxes,**CHECK_ARRAY_SETTTINGS)
        nav_left = Button(self.change_pallet, **NAV_LEFT)
        nav_right = Button(self.change_pallet, **NAV_RIGHT)
        self.widgets = [self.mode_select,
                        self.layer_select,
                        check_boxes,
                        nav_left,
                        nav_right]

    def change_mode(self,name):
        """Called from the selector when mode buttons are clicked."""
        self.mode = name

    def change_layer(self,name):
        """Called from the selector when layer buttons are clicked."""
        self.layer = name

    def set_checkboxes(self,state):
        """Called from the checkbox array when the user changes any checkbox."""
        self.checkboxes = state

    def change_selected(self,coordinates):
        """Called from the panel when a tile is selected."""
        pallet_name = self.get_pallet_name()
        self.selected = (pallet_name, coordinates)

    def draw_selected(self,surface):
        """Draw the currently selected tile onto the control bar."""
        if self.selected:
            sheet = map_prepare.GFX["mapsheets"][self.selected[0]]
            surface.blit(sheet,(25,185),pg.Rect(self.selected[1],CELL_SIZE))

    def change_pallet(self,name):
        """Changes the current pallet page to the next or previous. Called
        when pallet navigation buttons are clicked."""
        increment = NAVIGATION_DIRECTION[name]
        mode = self.get_pallet_mode()
        length = len(PALLETS[mode])
        if mode in self.pallet:
            self.pallet[mode] = (self.pallet[mode]+increment)%length

    def get_pallet_mode(self):
        """Returns the type of pallets used during a given mode and layer."""
        if self.mode == "Standard" :
            if self.layer in STANDARD_TILES:
                pallet_mode = "Tiles"
            else:
                pallet_mode = self.layer
        else:
            pallet_mode = self.mode
        return pallet_mode

    def get_pallet_name(self):
        """Get string name of pallet."""
        pallet_mode = self.get_pallet_mode()
        if pallet_mode in self.pallet:
            pallet_index = self.pallet[pallet_mode]
        else:
            pallet_index = 0
        return PALLETS[pallet_mode][pallet_index]

    def update(self,surface,keys,current_time,time_delta):
        """Updates each toolbar widget to the screen."""
        self.current_time = current_time

        try:##
            pallet = self.get_pallet_name()
        except KeyError:
            print("Not implemented yet")##
            self.mode_select.get_result("Standard")
            self.layer_select.get_result("BG Colors")
            pallet = self.get_pallet_name()

        self.pallet_panel.update(surface,pallet,time_delta)
        surface.blit(self.image,(0,0))
        self.draw_selected(surface)
        for widget in self.widgets:
            widget.update(surface)

    def check_event(self,event):
        """Receive events from the Edit state and pass them to each widget."""
        for widget in self.widgets:
            widget.check_event(event)
        self.pallet_panel.check_event(event)
