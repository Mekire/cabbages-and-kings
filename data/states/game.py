"""
This module contains the primary gameplay state.
"""

import sys
import math
import pygame as pg

from .. import prepare, state_machine, menu_helpers
from ..components import player, world, sidebar, enemy_sprites


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


SMALL_FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 32) ###

PLAY_AGAIN = prepare.GFX["misc"]["retry"]
PLAY_AGAIN_OPTIONS = ["Continue", "Save and Quit"]
PLAY_AGAIN_NEXT = ["GAME", "SELECT"]
PLAY_AGAIN_CENTERS = [(prepare.PLAY_RECT.centerx, 175),
                      (prepare.PLAY_RECT.centerx, 525)]
IRIS_MIN_RADIUS = 30
IRIS_TRANSPARENCY = (0, 0, 0, 175)
IRIS_STRIP_RECT = pg.Rect(prepare.PLAY_RECT.w-5, 0, 5, prepare.PLAY_RECT.h)
IRIS_STRIP_COLOR = (255, 73, 73)


class Game(state_machine._State):
    """Core state for the actual gameplay."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.world = None
        self.reset_map = True

    def startup(self, now, persistant):
        """
        Call the parent class' startup method.
        If reset_map has been set (after player death etc.) recreate the world
        map and reset relevant variables.
        """
        state_machine._State.startup(self, now, persistant)
        if self.reset_map:
            self.player = self.persist["player"]
            self.world = world.WorldMap(self.player)
            self.sidebar = sidebar.SideBar()
            self.iris = None
            self.play_again = None
            self.reset_map = False

    def cleanup(self):
        """Store background color and sidebar for use in camp menu."""
        self.done = False
        self.persist["bg_color"] = self.world.level.background_color
        self.persist["sidebar"] = self.sidebar
        return self.persist

    def save_player(self):
        """
        Retrieve needed data and save it in the player's save slot using YAML.
        """
        data = self.player.get_player_data()
        try:
            with open(prepare.SAVE_PATH) as my_file:
                players = yaml.load(my_file)
        except IOError:
            print("Problem loading data. Exiting.")
            raise
        save_slot = self.persist["save_slot"]
        players[save_slot] = data
        with open(prepare.SAVE_PATH, 'w') as my_file:
            yaml.dump(players, my_file)

    def get_event(self, event):
        """
        Process game state events. Add and pop directions from the player's
        direction stack as necessary.
        """
        if self.player.action_state != "dead":
            if event.type == pg.KEYDOWN:
                self.player.add_direction(event.key)
                if not self.world.scrolling:
                    if event.key == pg.K_SPACE:
                        self.player.attack()
                    elif event.key == pg.K_s:
                        self.change_to_camp()
                    elif event.key == pg.K_LSHIFT:
                        self.player.interact(self.world.level.interactables)
            elif event.type == pg.KEYUP:
                self.player.pop_direction(event.key)
        elif self.iris and self.iris.done:
            self.play_again.get_event(event)

    def change_to_camp(self):
        """
        Change the state to the camp screen.  The player's direction stack,
        attack, and action_state are reset to avoid unnecessary results when
        returning to the game state.
        """
        self.done = True
        self.next = "CAMP"
        self.player.direction_stack = []
        self.player.equipped["weapon"].sprite.reset_attack()
        self.player.action_state = "normal"

    def update(self, keys, now):
        """Update phase for the primary game state."""
        self.now = now
        if self.player.world_change:
            self.change_world()
        self.world.update(now)
        self.sidebar.update(self.player)
        if self.player.action_state == "dead":
            self.update_on_death(keys, now)

    def change_world(self):
        self.world = world.WorldMap(self.player)
        pos = (self.player.start_coord[0]*prepare.CELL_SIZE[0],
            self.player.start_coord[1]*prepare.CELL_SIZE[1])
        self.player.reset_position(pos)
        self.player.world_change = False

    def draw(self, surface, interpolate):
        """Draw level and sidebar; if player is dead draw death sequence."""
        self.world.draw(surface, interpolate)
        self.sidebar.draw(surface, interpolate)
        if self.player.action_state == "dead" and self.iris:
            self.iris.draw(surface)
            if self.iris.done:
                self.play_again.draw(surface, interpolate)

    def update_on_death(self, keys, now):
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
                center = self.player.rect.centery < prepare.PLAY_RECT.centery
                self.play_again = PlayAgain(PLAY_AGAIN_CENTERS[center])
            self.iris.update(now)
            if self.iris.done:
                self.play_again.update(keys, now)
                if self.play_again.done:
                    self.done = True
                    self.next = self.play_again.next
                    self.player.reset()
                    self.reset_map = True
                    self.save_player() ###


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
        self.speed = 4.0 #Rate radius shrinks in pixels per frame.
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

    def update(self, now):
        """
        Decrease the radius size appropriately; set done to True if radius has
        reached IRIS_MIN_RADIUS; recreate image.
        """
        self.rad = max(self.rad-self.speed, IRIS_MIN_RADIUS)
        if self.rad == IRIS_MIN_RADIUS:
            self.done = True
        self.image.fill(IRIS_TRANSPARENCY)
        self.image.fill(IRIS_STRIP_COLOR, IRIS_STRIP_RECT)
        pg.draw.circle(self.image, (0,0,0,0), self.center, int(self.rad))

    def draw(self, surface):
        """Standard draw method."""
        surface.blit(self.image, self.rect)


class PlayAgain(menu_helpers.BasicMenu):
    """A class for the simple menu that runs on game over."""
    def __init__(self, center):
        menu_helpers.BasicMenu.__init__(self, 2)
        self.rect = PLAY_AGAIN.get_rect(center=center)
        self.options = self.make_options(SMALL_FONT, PLAY_AGAIN_OPTIONS,
                                         self.rect.y+130, 35,
                                         prepare.PLAY_RECT.centerx)
        skel_pos = [(self.rect.x+100, self.rect.y+100),
                   (self.rect.right-100, self.rect.y+100)]
        self.skeletons = pg.sprite.Group(RetrySkeleton(p) for p in skel_pos)

    def update(self, keys, now):
        """Update the animated skeletons."""
        self.skeletons.update(now)

    def draw(self, surface, interpolate):
        """Draw window options and skeletons to the screen."""
        surface.blit(PLAY_AGAIN, self.rect)
        for i,val in enumerate(PLAY_AGAIN_OPTIONS):
            which = "selected" if i==self.index else "unselected"
            msg, rect = self.options[which][i]
            surface.blit(msg, rect)
        self.skeletons.draw(surface)

    def pressed_enter(self):
        """Set next to the selected item."""
        self.done = True
        self.next = PLAY_AGAIN_NEXT[self.index]


class RetrySkeleton(enemy_sprites.Skeleton):
    """A class for the skeletons that animate on game over."""
    def __init__(self, pos):
        enemy_sprites.Skeleton.__init__(self, pos, 0)
        self.rect = pg.Rect(0, 0, 100, 100)
        self.rect.center = pos
        self.anim_direction = "front"
        self.state = "walk"
        self.anim = self.get_anim()
        self.image = None

    def update(self, now):
        """Scale up the current image."""
        raw = self.anim.get_next_frame(now)
        self.image = pg.transform.scale(raw, self.rect.size)
