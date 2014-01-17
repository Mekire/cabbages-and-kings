import os
import sys
import pygame as pg

from .. import prepare

if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


CELL_SIZE = (50,50)


LAYERS = ("Environment","Foreground","Solid/Fore",
          "Solid","Water","BG Tiles","BG Colors")


class Tile(pg.sprite.Sprite):
    def __init__(self, sheet_name, source, target, make_mask=False):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(target, CELL_SIZE)
        sheet = prepare.GFX["mapsheets"][sheet_name]
        self.image = sheet.subsurface(pg.Rect(source, CELL_SIZE))
        if make_mask:
            self.mask = pg.mask.from_surface(self.image)

    def on_collision(self,other):
        return "SOLID"


class Level(object):
    def __init__(self, player, map_name):
        self.player = player
        self.map_dict = self.load_map(map_name)
        self.background = self.make_background()
        self.make_all_tiles()

    def load_map(self,map_name):
        path = os.path.join(".","resources","map_data",map_name)
        with open(path) as myfile:
            return yaml.load(myfile)

    def make_all_tiles(self):
        self.solid_group = pg.sprite.Group()
        for layer in ("Foreground","BG Tiles"):
            self.make_tile_group(layer)
        for layer in ("Solid/Fore","Solid","Water"):
            self.make_tile_group(layer, True)

    def make_background(self):
        background = pg.Surface((1000,700)).convert()
        background.fill(self.map_dict["BG Colors"]["fill"])
        for target in self.map_dict["BG Colors"]:
            if target != "fill":
                color = self.map_dict["BG Colors"][target][1]
                background.fill(color,pg.Rect(target,CELL_SIZE))
        return background

    def make_tile_group(self, layer, make_mask=False):
        group = pg.sprite.Group()
        for target in self.map_dict[layer]:
            sheet_name, source = self.map_dict[layer][target]
            group.add(Tile(sheet_name, source, target, make_mask))
        self.map_dict[layer] = group
        if make_mask:
            self.solid_group.add(group)

    def update(self):
        collisions = pg.sprite.spritecollide(self.player,self.solid_group,False)
        collidable = pg.sprite.collide_mask
        if pg.sprite.spritecollideany(self.player,collisions,collidable):
            self.player.exact_position = self.player.old_position
            self.player.rect.topleft = self.player.exact_position

    def draw(self,surface):
        surface.fill(0)###
        surface.blit(self.background, (0,0))
        for layer in ("BG Tiles","Water","Solid"):
            self.map_dict[layer].draw(surface)
        self.player.shadow.draw(self.player.rect.midbottom,surface)
        self.player.draw(surface)
        for layer in ("Solid/Fore","Foreground"):
            self.map_dict[layer].draw(surface)





