import os
import sys
import pygame as pg

from .. import prepare, tools
from . import level


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


MAX_HISTORY = 3
OFFSCREEN_THRESHOLD = 25 #Amount player can be offscreen before map scrolls.
SCROLL_SPEED = 20.0


class MapError(Exception):
    """Exception thrown if the map fails to rectify a collision issue."""
    pass


class WorldMap(object):
    """
    Class for functionality of a series of connected maps.  Each area of the
    game is implemented as a WorldMap (overworld, dungeons, houses, etc.).
    """
    def __init__(self, player):
        self.player = player
        self.name = self.player.world
        self.world_dict = self.load(self.name)
        self.history = []
        self.scrolling = False
        self.screen_copy = None
        self.next_screen = pg.Surface(prepare.PLAY_RECT.size).convert()
        self.scroll_vector = None
        start_coords = self.player.save_world_coords
        self.level = self.update_history(self.world_dict[start_coords])
        self.current_coords = list(start_coords)
        self.offset = [0, 0]
        self.drawn_this_frame = False #Disallow multiple updates per frame.

    def load(self, world_name):
        """Load world given a world_name."""
        return {(5,5) : "desert.map",
                (5,4) : "desert_north.map",
                (4,4) : "desert_northwest.map",
                (6,4) : "desert_northeast.map",
                (4,6) : "desert_southwest.map",
                (4,5) : "desert_west.map",
                (6,5) : "desert_east.map",
                (6,6) : "desert_southeast.map",
                (5,6) : "desert_south.map"}
##        path = os.path.join(".", "resources", "map_data", world_name)
##        with open(path) as myfile:
##            return yaml.load(myfile)

    def update_history(self, next_map_name):
        """
        Check to see if the current map is saved in history.  If it is
        found, use the old map (don't respawn monsters etc.).  If not, create a
        new map and place it in history.  Remove older maps if MAX_HISTORY is
        exceeded."""
        try:
            index = [mapp.name for mapp in self.history].index(next_map_name)
            next_map = self.history.pop(index)
        except ValueError:
            next_map = level.Level(self.player, next_map_name)
        if len(self.history) == MAX_HISTORY:
            del self.history[-1]
        self.history.insert(0, next_map)
        return self.history[0]

    def check_change_map(self):
        """
        Check if player has exited an edge of the map.  If he has, update
        the current map coordinates, change the level, and set scrolling to
        True.
        """
        direction = None
        if self.player.rect.left < -OFFSCREEN_THRESHOLD:
            direction = "left"
        elif self.player.rect.right > prepare.PLAY_RECT.w+OFFSCREEN_THRESHOLD:
            direction = "right"
        elif self.player.rect.top < -OFFSCREEN_THRESHOLD:
            direction = "back"
        elif self.player.rect.bottom > prepare.PLAY_RECT.h+OFFSCREEN_THRESHOLD:
            direction = "front"
        if direction:
            self.scroll_vector = prepare.DIRECT_DICT[direction]
            self.current_coords[0] += self.scroll_vector[0]
            self.current_coords[1] += self.scroll_vector[1]
            next_map = self.world_dict[tuple(self.current_coords)]
            self.level.on_map_change()
            self.level = self.update_history(next_map)
            self.scrolling = True

    def update(self, now):
        """
        If scrolling, update the scroll offset; else update the current level
        and check if the player has left the map.
        """
        if self.scrolling:
            self.scroll()
        else:
            self.level.update(now)
            self.check_change_map()

    def prepare_scroll(self):
        """
        Set the player's location for the next map; copy the current screen;
        and create an image for the next screen.
        """
        centerx, centery = self.player.rect.center
        new_center = centerx%prepare.PLAY_RECT.w, centery%prepare.PLAY_RECT.h
        self.player.reset_position(new_center, "center")
        #Fixes the "stuck in attack pose after scroll" glitch hopefully.
        self.player.equipped["weapon"].sprite.reset_attack()
        self.screen_copy = pg.display.get_surface().copy()
        self.level.shadows.update()
        self.level.draw(self.next_screen, 0)

    def scroll(self):
        """
        If the current screen hasn't been copied yet, call prepare_scroll.
        Update the offset of the scrolling and if it has exceeded the size of
        the screen, reset scrolling variables.
        """
        if not self.screen_copy:
            self.prepare_scroll()
        elif self.drawn_this_frame:
            for i in (0,1):
                self.offset[i] -= SCROLL_SPEED*self.scroll_vector[i]
                if abs(self.offset[i]) >= prepare.PLAY_RECT.size[i]:
                    self.scrolling = False
                    self.screen_copy = None
                    self.offset = [0, 0]
                    self.after_scroll_safety_check()
            self.drawn_this_frame = False

    def after_scroll_safety_check(self):
        """
        This method performs an initial collision check with the new map.
        If the player is found to be overlapping a tile, a minor adjustment is
        attempted (player will not be adjusted more than max_adjust pixels).
        If the collision can not be avoided a MapError is thrown and the map
        should be revised.
        """
        max_adjust = 15 #More than 15 pixels would probably be too noticeable.
        callback = tools.rect_then_mask
        collision_args = (self.player, self.level.solids, False, callback)
        adjust = self.scroll_vector[::-1] #Adjusts perpendicular to scroll.
        for count in range(max_adjust):
            for direction in (1, -1):
                move = direction*count*adjust[0], direction*count*adjust[1]
                self.player.rect.move_ip(*move)
                if not any(pg.sprite.spritecollide(*collision_args)):
                    #Executes and returns if player confirmed clear.
                    self.player.reset_position(self.player.rect.topleft)
                    return
                self.player.rect.move_ip(-move[0], -move[1])
        raise MapError("Map collision after scroll. Please report this map.")

    def draw_scroll(self, surface, interpolate):
        """
        Interpolate the scroll offset and blit the previous map and the
        new map in their scrolled positions.
        """
        offset = self.offset[:]
        surface.blit(self.screen_copy, offset)
        pos = [0,0]
        pos[0] = offset[0]+prepare.PLAY_RECT.size[0]*self.scroll_vector[0]
        pos[1] = offset[1]+prepare.PLAY_RECT.size[1]*self.scroll_vector[1]
        surface.blit(self.next_screen, pos)

    def draw(self, surface, interpolate):
        """
        Draw the scrolling map when appropriate;
        else, draw the level as normal.
        """
        if self.scrolling and self.screen_copy:
            self.draw_scroll(surface, interpolate)
        elif not self.scrolling:
            self.level.draw(surface, interpolate)
        self.drawn_this_frame = True
