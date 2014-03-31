"""
The state for editing the individual maps.
"""

import pygame as pg

from .. import map_prepare, state_machine
from ..components import toolbar, editmap


BACKGROUND_COLOR = (30, 40, 50)

LAYERS = ("BG Colors", "BG Tiles", "Water", "Solid",
          "Solid/Fore", "Foreground", "Environment",
          "Enemies", "Items")


class MapState(object):
    def __init__(self):
        self.map_dict = {layer:{} for layer in LAYERS}
        self.map_dict["BG Colors"]["fill"] = (0,0,0)


class Edit(state_machine._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.map_state = MapState()
        self.toolbar = toolbar.ToolBar()

    def update(self, surface, keys, now, dt):
        """Updates the title screen."""
        self.now = now
        self.toolbar.update(surface, keys, now, dt)
        self.draw(surface)

    def draw(self, surface):
        surface.fill(BACKGROUND_COLOR)
        self.toolbar.draw(surface)

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        self.toolbar.get_event(event)
