"""
Contains the class for our left hand control panel used during individual
map editing."""

import pygame as pg

from .. import map_prepare
from .map_gui_widgets import Selector,CheckBoxArray


class ToolBar(object):
    """A class for our left hand control panel."""
    def __init__(self):
        self.image = map_prepare.GFX["misc"]["interface"]
        self.selected = None
        self.make_widgets()

    def make_widgets(self):
        """Create required GUI elements."""
        content = ("Standard","Specials","Events","Enemies","Items","NPCs")
        self.mode_select = Selector(content,(0,16),(0,20),(100,20),"Standard")
        content = ("Environment","Foreground","Solid/Fore",
                    "Solid","Water","BG Tiles","BG Colors")
        start = 20, map_prepare.SCREEN_RECT.bottom-20*len(content)
        self.layer_select = Selector(content,start,(0,20),(80,20),"BG Colors")
        self.check_boxes = CheckBoxArray(content,True,(0,start[1]),(0,20))

    def update(self,surface,keys,current_time,time_delta):
        """Updates each toolbar widget to the screen."""
        self.current_time = current_time
        surface.blit(self.image,(0,0))
        self.mode_select.update(surface)
        self.layer_select.update(surface)
        self.check_boxes.update(surface)

    def check_event(self,event):
        """Receive events from the Edit state and pass them to each widget."""
        self.mode_select.check_event(event)
        self.layer_select.check_event(event)
        self.check_boxes.check_event(event)