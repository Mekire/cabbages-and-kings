import pygame as pg

from .. import prepare,tools
from ..components import player


class Game(tools._State):
    """Core state for the actual gameplay."""
    def __init__(self):
        """Currently just creates a player."""
        tools._State.__init__(self)
        self.player = player.Player((0,0,50,50),190)
        self.player.exact_position = list(prepare.SCREEN_RECT.center)

    def get_event(self,event):
        """Process game state events. Add and pop directions from the player's
        direction stack as necessary."""
        if event.type == pg.KEYDOWN:
            self.player.add_direction(event.key)
            ##Temporary change to test attack images
            if event.key == pg.K_SPACE:
                flip = self.player.flags["attacking"]
                self.player.flags["attacking"] = not flip
        elif event.type == pg.KEYUP:
            self.player.pop_direction(event.key)

    def update(self,surface,keys,current_time,time_delta):
        """Update phase for the primary game state."""
        self.current_time = current_time
        self.player.update(prepare.SCREEN_RECT,time_delta)
        surface.fill((50,200,50))
        self.player.shadow.draw(self.player.rect.midbottom,surface)
        self.player.draw(surface)
