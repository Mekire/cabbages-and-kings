"""
This is currently a placeholder for the Title State of the game.
"""

import random
import pygame as pg

from .. import prepare, state_machine, tools
from ..components import player, equips


class Title(state_machine._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.background = pg.Surface(prepare.SCREEN_SIZE).convert()
        self.background.blit(prepare.GFX["misc"]["titlebg"], (0,0))
        self.ne_key = self.render_font("Fixedsys500c", 30,
                                       "[Press Any Key]", (255,255,0))
        ne_key_center = (prepare.SCREEN_RECT.centerx, 650)
        self.ne_key_rect = self.ne_key.get_rect(center=ne_key_center)
        self.blink = False
        self.player = TitlePlayer()
        self.timer = 0.0

    def render_font(self, font, size, msg, color=(255,255,255)):
        """
        Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given.
        """
        selected_font = pg.font.Font(prepare.FONTS[font], size)
        return selected_font.render(msg, 1, color)

    def update(self, keys, now):
        """Updates the title screen."""
        self.now = now
        self.player.update(now)
        if self.now-self.timer > 1000/5.0:
            self.blink = not self.blink
            self.timer = self.now

    def draw(self, surface, interpolate):
        surface.blit(self.background, (0,0))
        self.player.draw(surface)
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


class TitlePlayer(player.Player):
    def __init__(self):
        player.Player.__init__(self, prepare.DEFAULT_PLAYER)
        self.inventory = equips.make_all_equips()
        self.direction = "right"
        self.direction_stack = [self.direction]
        self.reset_position((-300,300))
        self.speed = 3.5
        self.dancing = False
        self.done_dancing = False
        self.dance_timer = tools.Timer(1000, 1)

    def switch_direction(self):
        if not (-350 < self.rect.x < 1250):
            self.direction_stack[0] = prepare.OPPOSITE_DICT[self.direction]
            self.equipped = self.set_equips_random()
            self.all_animations = self.make_all_animations()
            self.done_dancing = False

    def update(self, now):
        player.Player.update(self, now)
        self.switch_direction()
        self.dance(now)
        self.rect.y = 300

    def draw(self, surface):
        player_image = pg.transform.scale(self.image, (300,300))
        surface.blit(player_image, self.rect)

    def dance(self, now):
        if not (self.done_dancing or self.dancing) and 100<self.rect.x<110:
            self.old_direction = self.direction
            self.dancing = True
            self.direction_stack[0] = "front"
            self.dance_timer.check_tick(now)
        if self.dancing and self.dance_timer.check_tick(now):
            self.dancing = False
            self.done_dancing = True
            self.dance_timer = tools.Timer(1000, 1)
            self.direction_stack[0] = self.old_direction
