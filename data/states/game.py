"""
This module contains the primary gameplay state.
"""

import pygame as pg

from .. import prepare,tools
from ..components import player,level


class Game(tools._State):
    """Core state for the actual gameplay."""
    def __init__(self):
        """Currently just creates a player."""
        tools._State.__init__(self)
        self.player = player.Player((0,0,50,50),190)
        self.player.exact_position = list(prepare.SCREEN_RECT.center)
        self.level = level.Level(self.player, "central.map")

    def get_event(self,event):
        """Process game state events. Add and pop directions from the player's
        direction stack as necessary."""
        if event.type == pg.KEYDOWN:
            self.player.add_direction(event.key)
            if event.key == pg.K_SPACE:
                self.player.attack()
        elif event.type == pg.KEYUP:
            self.player.pop_direction(event.key)

    def update(self,surface,keys,current_time,time_delta):
        """Update phase for the primary game state."""
        self.current_time = current_time
        self.player.update(current_time,time_delta)
        self.level.update(current_time)
        self.level.draw(surface)
