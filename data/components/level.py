import os
import sys
import pygame as pg

from operator import attrgetter
from .. import prepare, tools
from . import enemy_sprites


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


#Location on animsheet : number of frames in animation.
ANIMATED_TILES = {(0, 0) : 2,
                  (0, 50) : 2}


class CollisionRect(pg.sprite.Sprite):
    """A rect that can be used as a sprite for collision purposes."""
    def __init__(self, rect, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.rect = rect


class Tile(pg.sprite.Sprite):
    """A basic tile."""
    def __init__(self, sheet, source, target, make_mask=False):
        """If the player can collide with it pass make_mask=True."""
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(target, prepare.CELL_SIZE)
        self.sheet = prepare.GFX["mapsheets"][sheet]
        self.image = self.sheet.subsurface(pg.Rect(source, prepare.CELL_SIZE))
        if make_mask:
            self.mask = pg.mask.from_surface(self.image)

    def collide_with_player(self, player):
        player.collide_with_solid()


class Animated_Tile(Tile):
    """
    An animated tile. Animated tiles must be on the "animsheet" map sheet.
    """
    def __init__(self, source, target, frames, make_mask=False, fps=4.0):
        """
        The frames argument is the number of frames in the animation, and
        fps is the desired framerate of the animation.
        Currently only used for water.
        """
        Tile.__init__(self, "animsheet", source, target, make_mask)
        frames = tools.strip_from_sheet(self.sheet, source,
                                        prepare.CELL_SIZE, frames)
        self.anim = tools.Anim(frames, fps)

    def update(self, now):
        """Check if the image should change frame."""
        self.image = self.anim.get_next_frame(now)


class Level(object):
    """Class representing an individual map."""
    def __init__(self, player, map_name):
        self.player = player
        self.enemies = pg.sprite.Group()
        self.items = pg.sprite.Group()
        self.main_sprites = pg.sprite.Group(self.player)
        enemy_sprites.Zombie((400,500), 40, self.enemies, self.main_sprites)
        enemy_sprites.Snake((50,300), 50, self.enemies, self.main_sprites)
        enemy_sprites.Cabbage((850,300), 60, self.enemies, self.main_sprites)

        self.map_dict = self.load_map(map_name)
        self.background = self.make_background()
        self.layer_groups, self.solid_group = self.make_all_layer_groups()
        self.borders = self.make_borders()
        self.solids_borders = pg.sprite.Group(self.solid_group, self.borders)

    def make_borders(self):
        """
        Creates a sprite group of rectangles that border the screen.
        These are used to easily prevent enemies from leaving or being knocked
        off the map.
        """
        borders = pg.sprite.Group()
        right = pg.Rect(prepare.PLAY_RECT.w, 0, 50, prepare.PLAY_RECT.h)
        left = pg.Rect(-50, 0, 50, prepare.PLAY_RECT.h)
        top = pg.Rect(0, -50, prepare.PLAY_RECT.w, 50)
        bottom = pg.Rect(0, prepare.PLAY_RECT.h, prepare.PLAY_RECT.w, 50)
        for rect in (right, left, top, bottom):
            CollisionRect(rect, borders)
        return borders

    def load_map(self, map_name):
        """Load the map data from a resource file."""
        path = os.path.join(".", "resources", "map_data", map_name)
        with open(path) as myfile:
            return yaml.load(myfile)

    def make_background(self):
        """Create the background as one big surface."""
        background = pg.Surface((1000,700)).convert()
        background.fill(self.map_dict["BG Colors"]["fill"])
        for target in self.map_dict["BG Colors"]:
            if target != "fill":
                color = self.map_dict["BG Colors"][target][1]
                background.fill(color, pg.Rect(target, prepare.CELL_SIZE))
        self.map_dict.pop("BG Colors")
        return background

    def make_all_layer_groups(self):
        """Create sprite groups for all layers."""
        layer_groups = {}
        solid_group = pg.sprite.Group()
        for layer in ("Foreground", "BG Tiles"):
            layer_groups[layer] = self.make_tile_group(layer)
        for layer in ("Solid/Fore", "Solid", "Water"):
            layer_groups[layer] = self.make_tile_group(layer, True)
            solid_group.add(layer_groups[layer])
        return layer_groups, solid_group

    def make_tile_group(self, layer, make_mask=False):
        """
        Create a single sprite group for the selected layer.  Pass
        make_mask=True to create collision masks for the tiles.
        """
        group = pg.sprite.Group()
        for target in self.map_dict[layer]:
            sheet, source = self.map_dict[layer][target]
            if sheet == "animsheet":
                frames = ANIMATED_TILES[source]
                group.add(Animated_Tile(source, target, frames, make_mask))
            else:
                group.add(Tile(sheet, source, target, make_mask))
        return group

    def update(self, now, dt):
        """
        Update all tiles (currently only affects animated water).
        Then check any collisions that may have occured.
        """
        for layer in self.layer_groups:
            self.layer_groups[layer].update(now)
        self.enemies.update(now, dt, self.solids_borders)
        self.items.update(now)
        self.check_collisions()

    def check_collisions(self):
        """
        Check collisions and call the appropriate functions of the affected
        sprites.
        """
        call_mask = pg.sprite.collide_mask
        collide_group = pg.sprite.Group(self.solid_group, self.enemies,
                                        self.items)
        hit = pg.sprite.spritecollide(self.player, collide_group, False)
        mask_hits = pg.sprite.spritecollide(self.player, hit, False, call_mask)
        for hit in mask_hits:
            hit.collide_with_player(self.player)
        self.process_attacks()

    def process_attacks(self):
        """
        Check if the player is attacking, and is so, check if the attack rect
        is hitting any enemies.
        """
        weap = self.player.equipped["weapon"]
        if weap.attacking:
            rect = weap.anim_rects[self.player.direction][weap.anim.frame]
            for badguy in self.enemies:
                if rect.colliderect(badguy.rect):
                    badguy.got_hit(self.player, self.solids_borders,
                                   self.items, self.main_sprites)

    def draw(self,surface):
        """
        Draw all sprites and layers to the surface.  This may be greatly
        simplified if I implement layered sprite groups.
        """
        surface.blit(self.background, (0,0))
        for layer in ("BG Tiles", "Water"):
            self.layer_groups[layer].draw(surface)
        for sprite in self.main_sprites:
            if hasattr(sprite, "shadow"):
                sprite.shadow.draw(surface)
        self.layer_groups["Solid"].draw(surface)
        for sprite in sorted(self.main_sprites, key=attrgetter("rect.y")):
            sprite.draw(surface)
        for layer in ("Solid/Fore", "Foreground"):
            self.layer_groups[layer].draw(surface)
