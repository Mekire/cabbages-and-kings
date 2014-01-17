import os
import sys
import pygame as pg

from .. import prepare,tools

if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


CELL_SIZE = (50,50)

#Location on animsheet : number of frames in animation.
ANIMATED_TILES = {(0,0) : 2}



class Tile(pg.sprite.Sprite):
    """A basic tile. If the player can collide with it pass make_mask=True."""
    def __init__(self, sheet, source, target, make_mask=False):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(target, CELL_SIZE)
        self.sheet = prepare.GFX["mapsheets"][sheet]
        self.image = self.sheet.subsurface(pg.Rect(source, CELL_SIZE))
        if make_mask:
            self.mask = pg.mask.from_surface(self.image)


class Animated_Tile(Tile):
    """An animated tile. Animated tiles must be on the "animsheet" map sheet."""
    def __init__(self, source, target, frames, make_mask=False, fps=4.0):
        """The frames argument is the number of frames in the animation, and
        fps is the desired framerate of the animation.
        Currently only used for water."""
        Tile.__init__(self, "animsheet", source, target, make_mask)
        self.frame = 0
        self.frames = tools.strip_from_sheet(self.sheet, source,
                                             CELL_SIZE, frames)
        self.timer = 0.0
        self.fps = fps

    def update(self, current_time):
        """Check if the image should change frame."""
        if current_time-self.timer > 1000.0/self.fps:
            self.frame = (self.frame+1)%len(self.frames)
            self.image = self.frames[self.frame]
            self.timer = current_time


class Level(object):
    def __init__(self, player, map_name):
        self.player = player
        self.map_dict = self.load_map(map_name)
        self.background = self.make_background()
        self.layer_groups, self.solid_group = self.make_all_layer_groups()

    def load_map(self, map_name):
        path = os.path.join(".","resources","map_data",map_name)
        with open(path) as myfile:
            return yaml.load(myfile)

    def make_background(self):
        background = pg.Surface((1000,700)).convert()
        background.fill(self.map_dict["BG Colors"]["fill"])
        for target in self.map_dict["BG Colors"]:
            if target != "fill":
                color = self.map_dict["BG Colors"][target][1]
                background.fill(color,pg.Rect(target,CELL_SIZE))
        self.map_dict.pop("BG Colors")
        return background

    def make_all_layer_groups(self):
        layer_groups = {}
        solid_group = pg.sprite.Group()
        for layer in ("Foreground","BG Tiles"):
            layer_groups[layer] = self.make_tile_group(layer)
        for layer in ("Solid/Fore","Solid","Water"):
            layer_groups[layer] = self.make_tile_group(layer, True)
            solid_group.add(layer_groups[layer])
        return layer_groups, solid_group

    def make_tile_group(self, layer, make_mask=False):
        group = pg.sprite.Group()
        for target in self.map_dict[layer]:
            sheet, source = self.map_dict[layer][target]
            if sheet == "animsheet":
                frames = ANIMATED_TILES[source]
                group.add(Animated_Tile(source, target, frames, make_mask))
            else:
                group.add(Tile(sheet, source, target, make_mask))
        return group

    def update(self,current_time):
        for layer in self.layer_groups:
            self.layer_groups[layer].update(current_time)
        self.check_collisions()

    def check_collisions(self):
        collisions = pg.sprite.spritecollide(self.player,self.solid_group,False)
        collidable = pg.sprite.collide_mask
        if pg.sprite.spritecollideany(self.player,collisions,collidable):
            self.player.collide_with_solid()

    def draw(self,surface):
        surface.fill(pg.Color("black"),(1000,0,200,700))###
        surface.blit(self.background, (0,0))
        for layer in ("BG Tiles","Water"):
            self.layer_groups[layer].draw(surface)
        self.player.shadow.draw(self.player.rect.midbottom,surface)
        self.layer_groups["Solid"].draw(surface)
        self.player.draw(surface)
        for layer in ("Solid/Fore","Foreground"):
            self.layer_groups[layer].draw(surface)
