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

CHECK_ARRAY_SETTINGS = {"content" : LAYERS,
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
               "unclick" : True,
               "key_bindings" : [(pg.K_s, pg.KMOD_LCTRL)]}

LOAD_BUTTON = {"name": "Load",
               "rect" : (15,305,70,20),
               "selected" : False,
               "unclick" : True,
               "key_bindings" : [(pg.K_o, pg.KMOD_LCTRL)]}

NEW_BUTTON = {"name": "New",
              "rect" : (15,345,70,20),
              "selected" : False,
              "unclick" : True,
              "key_bindings" : [(pg.K_n, pg.KMOD_LCTRL)]}

#Used for pallet navigation buttons.
NAVIGATION_DIRECTION = {">>" : 1, "<<" : -1}


class ToolBar(object):
    """A class for our left hand control panel."""
    def __init__(self, map_state):
        """Initialize needed settings and create widgets."""
        self.map_state = map_state
        self.image = map_prepare.GFX["misc"]["interface"]
        self.make_widgets()

    def make_widgets(self):
        """Create required GUI widgets."""
        self.mode_select = Selector(**MODE_SELECT_SETTINGS)
        self.bind_keys_to_modes()
        self.layer_select = Selector(**LAYER_SELECT_SETTINGS)
        self.check_boxes = CheckBoxArray(**CHECK_ARRAY_SETTINGS)
        self.check_boxes.bind_key(pg.K_v, self.toggle_layer_visibility)
        self.navs = [Button(**NAV_LEFT), Button(**NAV_RIGHT)]
        self.save_button = Button(**SAVE_BUTTON)
        self.load_button = Button(**LOAD_BUTTON)
        self.new_button = Button(**NEW_BUTTON)
        self.widgets = [self.mode_select, self.layer_select, self.check_boxes,
                        self.navs[0], self.navs[1],
                        self.save_button, self.load_button, self.new_button]

    def bind_keys_to_modes(self):
        """Bind each mode button to the keys 1-6."""
        for i,button in enumerate(self.mode_select.buttons, 1):
            key = getattr(pg, "K_{}".format(i))
            button.bind_key(key)

    def toggle_layer_visibility(self, check_box_array):
        """
        Toggle the visibility of the currently selected layer via 'v-key'.
        """
        for check_box in check_box_array.checkboxes:
            if self.map_state.layer == check_box.name:
                check_box.toggle()

    def change_layer_with_keys(self, event):
        """Move up and down layers with w/up and s/down keys."""
        if event.key in (pg.K_w, pg.K_UP):
            index = (LAYERS.index(self.map_state.layer)-1)%len(LAYERS)
            self.layer_select.buttons[index].press()
        elif event.key in (pg.K_s, pg.K_DOWN):
            index = (LAYERS.index(self.map_state.layer)+1)%len(LAYERS)
            self.layer_select.buttons[index].press()

    def get_event(self,event):
        """Recieve events from the Edit state and pass them to each widget."""
        if event.type == pg.KEYDOWN:
            self.change_layer_with_keys(event)
        for widget in self.widgets:
            widget.get_event(event)

    def update(self, keys, now):
        pass

    def draw(self, surface):
        """Draw main toolbar image and each individual widget."""
        surface.blit(self.image, (0,0))
        for widget in self.widgets:
            widget.draw(surface)
