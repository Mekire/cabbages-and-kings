"""
Contains the class for our left hand control panel used during individual
map editing."""

import pygame as pg

from .. import map_prepare
from .map_gui_widgets import Selector,CheckBoxArray,NavSelector


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
        content = ("Standard","Specials","Events","Enemies","Items","NPCs")
        self.mode_select = Selector(content,(0,16),(0,20),(100,20),"Standard")
        content = ("Environment","Foreground","Solid/Fore",
                    "Solid","Water","BG Tiles","BG Colors")
        start = (20, map_prepare.SCREEN_RECT.bottom-20*len(content))
        self.layer_select = Selector(content,start,(0,20),(80,20),"BG Colors")
        self.check_boxes = CheckBoxArray(content,True,(0,start[1]),(0,20))
        content = ("<<",">>")
        self.pallet_nav = NavSelector(content,(10,start[1]-55),(40,0),(40,20))

    def update(self,surface,keys,current_time,time_delta):
        """Updates each toolbar widget to the screen."""
        self.current_time = current_time
        try:
            self.change_pallet()
        except KeyError:
            print("Not implemented yet")##
            self.pallet_nav.selected = None##
        surface.blit(self.image,(0,0))
        self.mode_select.update(surface)
        self.layer_select.update(surface)
        self.check_boxes.update(surface)
        self.pallet_nav.update(surface)

    def change_pallet(self):
        if self.pallet_nav.selected:
            mode = self.get_pallet_mode()
            length = len(PALLETS[mode])
            increment = NAVIGATION_DIRECTION[self.pallet_nav.selected]
            if mode in self.pallet:
                self.pallet[mode] = (self.pallet[mode]+increment)%length
            self.pallet_nav.selected = None
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
        self.mode_select.check_event(event)
        self.layer_select.check_event(event)
        self.check_boxes.check_event(event)
        self.pallet_nav.check_event(event)