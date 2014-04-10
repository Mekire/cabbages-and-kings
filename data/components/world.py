import os
import sys
import pygame as pg

from .. import prepare
from . import level


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


MAX_HISTORY = 3
OFFSCREEN_THRESHOLD = 30 #Amount player can be offscreen before map scrolls.
SCROLL_SPEED = 20.0


class WorldMap(object):
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

    def load(self, world_name):
        return {(5,5) : "desert.map",
                (5,4) : "desert.map",
                (5,6) : "desert.map",
                (4,5) : "desert.map",
                (6,5) : "desert.map"}
##        path = os.path.join(".", "resources", "map_data", world_name)
##        with open(path) as myfile:
##            return yaml.load(myfile)

    def update_history(self, next_map_name):
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
            self.level = self.update_history(next_map)
            self.scrolling = True

    def update(self, now):
        if self.scrolling:
            self.scroll()
        else:
            self.level.update(now)
            self.check_change_map()

    def scroll(self):
        if not self.screen_copy:
            self.player.rect.centerx %= prepare.PLAY_RECT.w
            self.player.rect.centery %= prepare.PLAY_RECT.h
            self.player.exact_position = list(self.player.rect.topleft)
            self.player.old_position = self.player.exact_position[:]
            self.screen_copy = pg.display.get_surface().copy()
            self.level.draw(self.next_screen, 0)
        for i in (0,1):
            self.offset[i] -= SCROLL_SPEED*self.scroll_vector[i]
            if abs(self.offset[i]) >= prepare.PLAY_RECT.size[i]:
                self.scrolling = False
                self.screen_copy = None
                self.offset = [0, 0]

    def draw(self, surface, interpolate):
        offset = self.offset[:]
        if self.scrolling and self.screen_copy:
            for i in (0,1):
                offset[i] -= SCROLL_SPEED*self.scroll_vector[i]*interpolate
                if abs(offset[i]) >= prepare.PLAY_RECT.size[i]:
                    offset = self.offset
                    break
            surface.blit(self.screen_copy, offset)
            pos = [0,0]
            pos[0] = offset[0]+prepare.PLAY_RECT.size[0]*self.scroll_vector[0]
            pos[1] = offset[1]+prepare.PLAY_RECT.size[1]*self.scroll_vector[1]
            surface.blit(self.next_screen, pos)
        else:
            self.level.draw(surface, interpolate)
