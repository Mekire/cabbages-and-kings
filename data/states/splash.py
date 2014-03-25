"""
The splash screen of the game. The first thing the user sees.
"""

import pygame as pg

from .. import prepare, state_machine


class Splash(state_machine._State):
    """This State is updated while our game shows the splash screen."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.next = "TITLE"
        self.timeout = 5
        self.cover = pg.Surface((prepare.SCREEN_SIZE)).convert()
        self.cover.fill(pg.Color("black"))
        self.cover_alpha = 256
        self.alpha_step  = 2
        self.image = prepare.GFX["misc"]['splash1']
        self.rect = self.image.get_rect(center=prepare.SCREEN_RECT.center)

    def make_text_list(self, font, size, strings, color, start_y, y_space):
        """
        Takes a list of strings and returns a list of (rendered_surface, rect)
        tuples. The rects are centered on the screen and their y coordinates
        begin at starty, with y_space pixels between each line.
        """
        rendered_text = []
        for i,string in enumerate(strings):
            msg = self.render_font(font, size, string, color)
            msg_center = (prepare.SCREEN_RECT.centerx, start_y+i*y_space)
            rect = msg.get_rect(center=msg_center)
            rendered_text.append((msg, rect))
        return rendered_text

    def render_font(self, font, size, msg, color=(255,255,255)):
        """
        Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given.
        """
        selected_font = pg.font.Font(prepare.FONTS[font], size)
        return selected_font.render(msg, 1, color)

    def update(self, surface, keys, current_time, time_delta):
        """Updates the splash screen."""
        self.current_time = current_time
        surface.blit(self.image, self.rect)
        self.cover.set_alpha(self.cover_alpha)
        self.cover_alpha = max(self.cover_alpha-self.alpha_step, 0)
        surface.blit(self.cover, (0,0))
        if self.current_time-self.start_time > 1000.0*self.timeout:
            self.done = True

    def get_event(self, event):
        """
        Get events from Control. Currently changes to next state on any key
        press.
        """
        self.done = event.type == pg.KEYDOWN
