"""
Contains the class for our left hand control panel used during individual
map editing.
"""

import pygame as pg

from .. import map_prepare
from .map_gui_widgets import Selector, CheckBoxArray, Button


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
            "unclick" : True,
            "key_bindings" : [pg.K_a, pg.K_LEFT]}

NAV_RIGHT = {"name" : ">>",
             "rect" : (50, LAYER_SELECT_SETTINGS["start"][1]-55, 40, 20),
             "selected" : False,
             "unclick" : True,
             "key_bindings" : [pg.K_d, pg.K_RIGHT]}

SAVE_BUTTON = {"name": "Save",
               "rect" : (15,265,70,20),
               "selected" : False,
               "unclick" : True}

LOAD_BUTTON = {"name": "Load",
               "rect" : (15,305,70,20),
               "selected" : False,
               "unclick" : True}

#Used for pallet navigation buttons.
NAVIGATION_DIRECTION = {">>" : 1, "<<" : -1}


class ToolBar(object):
    """A class for our left hand control panel."""
    def __init__(self):
        """Initialize needed settings and create widgets."""
        self.image = map_prepare.GFX["misc"]["interface"]
        self.make_widgets()

    def make_widgets(self):
        """Create required GUI widgets."""
        self.mode_select = Selector(**MODE_SELECT_SETTINGS)
        self.layer_select = Selector(**LAYER_SELECT_SETTINGS)
        self.check_boxes = CheckBoxArray(**CHECK_ARRAY_SETTTINGS)
        self.navs = [Button(**NAV_LEFT), Button(**NAV_RIGHT)]
        self.save_button = Button(**SAVE_BUTTON)
        self.load_button = Button(**LOAD_BUTTON)
        self.widgets = [self.mode_select, self.layer_select, self.check_boxes,
                        self.navs[0], self.navs[1],
                        self.save_button, self.load_button]

    def get_event(self,event):
        """Recieve events from the Edit state and pass them to each widget."""
        for widget in self.widgets:
            widget.get_event(event)

    def update(self, keys, now):
        pass

    def draw(self, surface):
        """Draw main toolbar image and each individual widget."""
        surface.blit(self.image, (0,0))
        for widget in self.widgets:
            widget.draw(surface)
