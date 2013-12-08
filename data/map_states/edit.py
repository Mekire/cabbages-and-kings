"""
The state for editing the individual maps.
"""

import pygame as pg

from .. import map_prepare,tools
from ..components import toolbar,editmap


class Edit(tools._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.toolbar = toolbar.ToolBar()
        self.edit_map = editmap.EditMap()
        self.adding = False
        self.deleting = False

    def render_font(self,font,size,msg,color=(255,255,255)):
        """Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given."""
        selected_font = pg.font.Font(map_prepare.FONTS[font],size)
        return selected_font.render(msg,1,color)

    def update(self,surface,keys,current_time,time_delta):
        """Updates the title screen."""
        self.current_time = current_time
        mouse_position = pg.mouse.get_pos()
        selected, layer = self.toolbar.selected,self.toolbar.layer
        if self.adding:
            self.edit_map.add_tile(selected,layer,mouse_position)
        elif self.deleting:
            self.edit_map.del_tile(layer,mouse_position)
        surface.fill((20,20,20))
        self.edit_map.draw_map(surface,self.toolbar.checkboxes)
        self.toolbar.update(surface,keys,current_time,time_delta)

    def get_event(self,event):
        """Get events from Control and pass them on to components."""
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if not self.toolbar.pallet_panel.visible:
                    if self.edit_map.rect.collidepoint(event.pos):
                        self.adding = True
            elif event.button == 3:
                if not self.toolbar.pallet_panel.visible:
                    if self.edit_map.rect.collidepoint(event.pos):
                        self.deleting = True
        elif event.type == pg.MOUSEBUTTONUP:
            self.adding = False
            self.deleting = False
        self.toolbar.check_event(event)
