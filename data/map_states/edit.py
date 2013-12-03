"""
The state for editing the individual maps.
"""

import pygame as pg

from .. import map_prepare,tools
from ..components import toolbar


class Edit(tools._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.toolbar = toolbar.ToolBar()

    def render_font(self,font,size,msg,color=(255,255,255)):
        """Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given."""
        selected_font = pg.font.Font(map_prepare.FONTS[font],size)
        return selected_font.render(msg,1,color)

    def update(self,surface,keys,current_time,time_delta):
        """Updates the title screen."""
        self.current_time = current_time
        self.toolbar.update(surface,keys,current_time,time_delta)
        surface.fill((255,255,255),(102,48,402,604))
        surface.fill((40,40,40),(102,50,400,600))
        try:##
            pallet = self.toolbar.get_pallet_name()
            pallet_image = map_prepare.GFX["mapsheets"][pallet]
            surface.blit(pallet_image,(102,50))
        except KeyError:
            print("Not implemented yet")##
            self.toolbar.mode_select.get_result("Standard")
            self.toolbar.layer_select.get_result("BG Colors")

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        self.toolbar.check_event(event)
