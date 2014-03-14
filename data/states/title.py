"""
This is currently a placeholder for the Title State of the game.
"""

import pygame as pg

from .. import prepare, tools


class Title(tools._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.background = pg.Surface(prepare.SCREEN_SIZE).convert()
        self.background.blit(prepare.GFX["misc"]["titlebg"], (0,0))
        self.ne_key = self.render_font("Fixedsys500c", 20,
                                       "[Press Any Key]", (255,255,0))
        ne_key_center = (prepare.SCREEN_RECT.centerx, 500)
        self.ne_key_rect = self.ne_key.get_rect(center=ne_key_center)
        self.blink = False
        self.timer = 0.0

    def render_font(self, font, size, msg, color=(255,255,255)):
        """
        Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given.
        """
        selected_font = pg.font.Font(prepare.FONTS[font], size)
        return selected_font.render(msg, 1, color)

    def update(self, surface, keys, now, dt):
        """Updates the title screen."""
        self.now = now
        surface.blit(self.background, (0,0))
        if self.now-self.timer > 1000/5.0:
            self.blink = not self.blink
            self.timer = self.now
        if self.blink:
            surface.blit(self.ne_key, self.ne_key_rect)

    def get_event(self, event):
        """
        Get events from Control.  Currently changes to next state on any key
        press.
        """
        if event.type == pg.KEYDOWN:
            self.next = "SELECT"
            self.done = True
