"""
Contains the class for our left hand control panel used during individual
map editing.
"""

import pygame as pg

from .. import map_prepare
from .map_gui_widgets import Selector,CheckBoxArray,Button


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
        self.image = map_prepare.GFX["misc"]["interface"]
        self.selected = None
        self.pallet = {"Tiles" : 0,
                       "Enemies" : 0,
                       "Items" : 0}
        self.make_widgets()

    def make_widgets(self):
        """Create required GUI elements."""
        self.mode_select = Selector(**MODE_SELECT_SETTINGS)
        self.layer_select = Selector(**LAYER_SELECT_SETTINGS)
        self.check_boxes = CheckBoxArray(**CHECK_ARRAY_SETTTINGS)
        nav_left = Button(self.change_pallet, **NAV_LEFT)
        nav_right = Button(self.change_pallet, **NAV_RIGHT)
        self.widgets = [self.mode_select,
                        self.layer_select,
                        self.check_boxes,
                        nav_left,
                        nav_right]

    def update(self,surface,keys,current_time,time_delta):
        """Updates each toolbar widget to the screen."""
        self.current_time = current_time
        surface.blit(self.image,(0,0))
        for widget in self.widgets:
            widget.update(surface)

    def change_pallet(self,name):
        """Changes the current pallet page to the next or previous. Called
        when pallet navigation buttons are clicked."""
        increment = NAVIGATION_DIRECTION[name]
        mode = self.get_pallet_mode()
        length = len(PALLETS[mode])
        if mode in self.pallet:
            self.pallet[mode] = (self.pallet[mode]+increment)%length
        print(self.get_pallet_name())

    def get_pallet_mode(self):
        """Returns the type of pallets used during a given mode and layer."""
        mode = self.mode_select.selected
        if mode == "Standard" :
            layer = self.layer_select.selected
            if layer in STANDARD_TILES:
                pallet_mode = "Tiles"
            else:
                pallet_mode = layer
        else:
            pallet_mode = mode
        return pallet_mode

    def get_pallet_name(self):
        """Get string name of pallet."""
        mode = self.get_pallet_mode()
        if mode in self.pallet:
            pallet_index = self.pallet[mode]
        else:
            pallet_index = 0
        return PALLETS[mode][pallet_index]

    def check_event(self,event):
        """Receive events from the Edit state and pass them to each widget."""
        for widget in self.widgets:
            widget.check_event(event)
