"""
This module contains the logic for the camp menu screen.
"""

import pygame as pg

from .. import prepare, tools
from ..components import player, level, sidebar


MAX_SCROLL = -prepare.PLAY_RECT.width
PLAYER_SIZE = 400, 400


class Camp(tools._State):
    """State for changing gear, selecting items, etc."""
    def __init__(self):
        tools._State.__init__(self)
        self.scroll_speed = 1200
        self.next = "GAME"

    def startup(self, now, persistant):
        tools._State.startup(self, now, persistant)
        self.game_screen = pg.display.get_surface().copy()
        self.base = self.make_base_image()
        self.offset = 0
        self.is_scrolling = True

    def make_base_image(self):
        base = pg.Surface(prepare.PLAY_RECT.size).convert()
        base.fill(prepare.BACKGROUND_COLOR)
        base.blit(prepare.GFX["misc"]["campscreen"], (0,0))
        player = self.make_player_image()
        base.blit(player, (30,50))
        return base

    def make_player_image(self):
        image = pg.Surface(PLAYER_SIZE).convert()
        image.fill(self.persist["bg_color"])
        player = self.persist["player"]
        player_image = player.all_animations[0]["normal"]["front"].frames[0]
        player_large = pg.transform.scale(player_image, PLAYER_SIZE)
        image.blit(player_large, (0,0))
        return image

    def scroll(self, dt):
        self.offset = max(self.offset-self.scroll_speed*dt, MAX_SCROLL)
        if self.offset == MAX_SCROLL:
            self.is_scrolling = False

    def update(self, surface, keys, now, dt):
        if self.is_scrolling:
            self.scroll(dt)
        self.draw(surface)

    def  get_event(self, event):
        if not self.is_scrolling:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.done = True

    def draw(self, surface):
        if self.is_scrolling:
            surface.blit(self.game_screen, (self.offset, 0))
        surface.blit(self.base, (prepare.SCREEN_RECT.w+self.offset, 0))
        self.persist["sidebar"].draw(surface, self.offset)

