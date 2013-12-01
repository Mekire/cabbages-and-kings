import pygame as pg

from .. import map_prepare,tools
from ..components.map_gui_widgets import Selector,CheckBoxArray


class Edit(tools._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.toolbar = map_prepare.GFX["misc"]["interface"]
        self.make_widgets()

    def make_widgets(self):
        content = ("Standard","Specials","Events","Enemies","Items","NPCs")
        self.mode_select = Selector(content,(0,16),(0,20),(100,20),"Standard")
        content = ("Environment","Foreground","Solid/Fore",
                    "Solid","Water","BG Tiles","BG Colors")
        start = 20, map_prepare.SCREEN_RECT.bottom-20*len(content)
        self.layer_select = Selector(content,start,(0,20),(80,20),"BG Colors")
        self.check_boxes = CheckBoxArray(content,True,(0,start[1]),(0,20))

    def render_font(self,font,size,msg,color=(255,255,255)):
        """Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given."""
        selected_font = pg.font.Font(map_prepare.FONTS[font],size)
        return selected_font.render(msg,1,color)

    def update(self,surface,keys,current_time,time_delta):
        """Updates the title screen."""
        self.current_time = current_time
        surface.blit(self.toolbar,(0,0))
        self.mode_select.update(surface)
        self.layer_select.update(surface)
        self.check_boxes.update(surface)

    def get_event(self,event):
        """Get events from Control."""
        self.mode_select.check_event(event)
        self.layer_select.check_event(event)
        self.check_boxes.check_event(event)
