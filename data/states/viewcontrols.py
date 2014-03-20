import pygame as pg

from .. import prepare, tools


FONT_BIG = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)


class ViewControls(tools._State):
    """This State is updated while our game shows the player select screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.next = "SELECT"
        self.timer = tools.Timer(300)
        self.blink = False
        msg_center = (prepare.SCREEN_RECT.centerx, 630)
        self.ne_key = self.render_font(FONT_BIG, "Press Any Key",
                                       pg.Color("white"), msg_center)

    def render_font(self, font, msg, color, center):
        """Return the rendered font surface and its rect centered on center."""
        msg = font.render(msg, 0, color)
        rect = msg.get_rect(center=center)
        return msg, rect

    def get_event(self, event):
        self.done = event.type == pg.KEYDOWN

    def update(self, surface, keys, now, dt):
        if self.timer.check_tick(now):
            self.blink = not self.blink
        surface.fill(prepare.BACKGROUND_COLOR)
        surface.blit(prepare.GFX["misc"]["keyboard"], (0,0))
        if self.blink:
            surface.blit(*self.ne_key)
