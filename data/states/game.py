"""
This module contains the primary gameplay state.
"""

import math
import pygame as pg

from .. import prepare, state_machine
from ..components import player, level, sidebar


IRIS_MIN_RADIUS = 30
IRIS_TRANSPARENCY = (0, 0, 0, 175)
IRIS_STRIP_RECT = pg.Rect(prepare.PLAY_RECT.w-5, 0, 5, prepare.PLAY_RECT.h)


class Game(state_machine._State):
    """Core state for the actual gameplay."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.map_scrolling = False
        self.level = None

    def startup(self, now, persistant):
        state_machine._State.startup(self, now, persistant)
        if not self.level:
            self.player = self.persist["player"]
            self.player.exact_position = list(prepare.SCREEN_RECT.center) ###
            self.level = level.Level(self.player, "central.map") ###
            self.sidebar = sidebar.SideBar()
            self.iris = None

    def cleanup(self):
        self.done = False
        self.persist["bg_color"] = self.level.background_color
        self.persist["sidebar"] = self.sidebar
        return self.persist

    def get_event(self, event):
        """
        Process game state events. Add and pop directions from the player's
        direction stack as necessary.
        """
        if self.player.action_state != "dead":
            if event.type == pg.KEYDOWN:
                self.player.add_direction(event.key)
                if not self.map_scrolling:
                    if event.key == pg.K_SPACE:
                        self.player.attack()
                    elif event.key == pg.K_s:
                        self.done = True
                        self.next = "CAMP"
                        self.player.direction_stack = []
            elif event.type == pg.KEYUP:
                self.player.pop_direction(event.key)

    def update(self, surface, keys, now, dt):
        """Update phase for the primary game state."""
        self.now = now
        self.player.update(now, dt)
        self.level.update(now, dt)
        self.sidebar.update(self.player)
        self.level.draw(surface)
        self.sidebar.draw(surface)
        if self.player.action_state == "dead":
            self.update_on_death(surface, keys, now, dt)

    def update_on_death(self, surface, keys, now, dt):
        """
        If the player has been killed this method will be called during the
        update phase.  Handles the iris in effect and the "play again" prompt.
        Iris is created after the player's death animation completes, and
        "play again" prompt is not displayed until iris finishes.
        """
        if self.player.death_anim.done:
            if not self.iris:
                x,y = self.player.rect.center
                self.iris = IrisIn((x,y+10))
            self.iris.update(now, dt)
            self.iris.draw(surface)


class IrisIn(object):
    """
    Class for displaying and updating an iris that closes on the player
    upon death.
    """
    def __init__(self, center, rect=prepare.PLAY_RECT):
        self.center = center
        self.rect = pg.Rect(rect)
        self.image = pg.Surface(self.rect.size).convert_alpha()
        self.rad = self.get_start_radius()
        self.speed = 240 #Rate radius shrinks in pixels per second.
        self.done = False

    def get_start_radius(self):
        """
        Find the required max radius of the circle based on center distance
        from each corner.
        """
        max_radius = 0
        for attribute in ("topleft", "topright", "bottomleft", "bottomright"):
            x, y = getattr(self.rect, attribute)
            vec = self.center[0]-x, self.center[1]-y
            distance_to_corner = math.hypot(*vec)
            if distance_to_corner > max_radius:
                max_radius = distance_to_corner
        return max_radius

    def update(self, now, dt):
        """
        Decrease the radius size appropriately; set done to True if radius has
        reached IRIS_MIN_RADIUS; recreate image.
        """
        self.rad = max(self.rad-self.speed*dt, IRIS_MIN_RADIUS)
        if self.rad == IRIS_MIN_RADIUS:
            self.done = True
        self.image.fill(IRIS_TRANSPARENCY)
        self.image.fill(pg.Color("yellow"), IRIS_STRIP_RECT)
        pg.draw.circle(self.image, (0,0,0,0), self.center, int(self.rad))

    def draw(self, surface):
        """Standard draw method."""
        surface.blit(self.image, self.rect)
