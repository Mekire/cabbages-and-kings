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
        self.alpha = 0
        self.alpha_speed  = 125  #Alpha change per second
        self.image = prepare.GFX["misc"]['splash1'].copy().convert()
        self.image.set_alpha(self.alpha)
        self.rect = self.image.get_rect(center=prepare.SCREEN_RECT.center)

    def update(self, surface, keys, now, dt):
        """Updates the splash screen."""
        self.now = now
        surface.fill(prepare.BACKGROUND_COLOR)
        surface.blit(self.image, self.rect)
        self.alpha = min(self.alpha+self.alpha_speed*dt, 255)
        self.image.set_alpha(self.alpha)
        if self.now-self.start_time > 1000.0*self.timeout:
            self.done = True

    def get_event(self, event):
        """
        Get events from Control. Changes to next state on any key press.
        """
        self.done = event.type == pg.KEYDOWN
