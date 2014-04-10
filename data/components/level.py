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


Z_ORDER = {"BG Tiles" : -4,
           "Water" : -3,
           "Shadows" : -2,
           "Solid" : -1,
           "Solid/Fore" : 750,
           "Foreground" : 800}


class CollisionRect(pg.sprite.Sprite):
    """A rect that can be used as a sprite for collision purposes."""
    def __init__(self, rect, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.rect = rect


class Tile(pg.sprite.Sprite):
    """A basic tile."""
    def __init__(self, sheet, source, target, mask):
        """If the player can collide with it pass mask=True."""
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(target, prepare.CELL_SIZE)
        self.sheet = prepare.GFX["mapsheets"][sheet]
        self.image = self.sheet.subsurface(pg.Rect(source, prepare.CELL_SIZE))
        if mask:
            self.mask = pg.mask.from_surface(self.image)

    def collide_with_player(self, player):
        """
        Any sprite that will need to find collision with the player must
        have this method.
        """
        player.collide_with_solid()


class AnimatedTile(Tile):
    """
    An animated tile. Animated tiles must be on the "animsheet" map sheet.
    """
    def __init__(self, sheet, source, target, mask, fps=4, frames=2):
        """
        The frames argument is the number of frames in the animation, and
        fps is the desired framerate of the animation.
        Currently only used for water.
        """
        Tile.__init__(self, "animsheet", source, target, mask)
        size = prepare.CELL_SIZE
        frames = tools.strip_from_sheet(self.sheet, source, size, frames)
        self.anim = tools.Anim(frames, fps)

    def update(self, now, *args):
        """Check if the image should change frame."""
        self.image = self.anim.get_next_frame(now)


class HazardTile(Tile):
    """Basic hazard tiles (cacti, spikes, etc.)"""
    def __init__(self, sheet, source, target, mask, damage=1):
         Tile.__init__(self, sheet, source, target, True)
         self.attack = damage

    def collide_with_player(self, player):
        """
        Hit the player and reset the player's position to ensure that it
        is not possible to glitch through a hazard.
        """
        player.got_hit(self)
        player.collide_with_solid(False)


class AnimatedHazard(AnimatedTile):
    """Animated hazards including lava."""
    def __init__(self, sheet, source, target, mask, fps=4, frames=2, damage=1):
        AnimatedTile.__init__(self, sheet, source, target, mask, fps, frames)
        self.attack = damage

    def collide_with_player(self, player):
        player.got_hit(self)
        player.collide_with_solid(False)


#All map tiles that need to have specific behavior should be added here.
#Keys are (sheet, source_coordinates); Values are the type of tile and
#keyword arguments for initializing it.
SPECIAL_TILES = {("animsheet", (0, 0)) : (AnimatedTile, {"frames" : 2}),
                 ("animsheet", (0, 50)) : (AnimatedHazard, {"frames" : 2,
                                                            "damage" : 5}),
                 ("base", (350, 400)) : (HazardTile, {"damage" : 1}),
                 ("base", (250, 450)) : (HazardTile, {"damage" : 1}),
                 ("base", (300, 450)) : (HazardTile, {"damage" : 1})}


class Level(object):
    """Class representing an individual map."""
    def __init__(self, player, map_name):
        self.player = player
        self.name = map_name
        self.map_dict = self.load_map(map_name)
        self.background = self.make_background()
        self.enemies = pg.sprite.Group()
        self.items = pg.sprite.Group()
        self.main_sprites = pg.sprite.Group(self.player)
        self.all_group, self.solids = self.make_all_layer_groups()
        self.solid_border = pg.sprite.Group(self.solids, self.make_borders())
        self.all_group.add(self.player)
        self.spawn()
        self.make_shadows()

    def spawn(self):
        """Create enemies, adding them to the required groups."""
        groups = (self.enemies, self.main_sprites, self.all_group)
        for target in self.map_dict["Enemies"]:
            sheet, source, speed = self.map_dict["Enemies"][target]
            enemy_sprites.ENEMY_DICT[source](target, speed, *groups)

    def make_shadows(self):
        """Create shadows for the player and all enemies."""
        shadows = [enemy.shadow for enemy in self.enemies]+[self.player.shadow]
        self.all_group.add(shadows, layer=Z_ORDER["Shadows"])

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
        self.background_color = self.map_dict["BG Colors"]["fill"]
        background.fill(self.background_color)
        for target in self.map_dict["BG Colors"]:
            if target != "fill":
                color = self.map_dict["BG Colors"][target][1]
                background.fill(color, pg.Rect(target, prepare.CELL_SIZE))
        return background

    def make_all_layer_groups(self):
        """Create sprite groups for all layers."""
        all_group = pg.sprite.LayeredUpdates()
        solid_group = pg.sprite.Group()
        for layer in ("Foreground", "BG Tiles"):
            all_group.add(self.make_tile_group(layer), layer=Z_ORDER[layer])
        for layer in ("Solid/Fore", "Solid", "Water"):
            solids = self.make_tile_group(layer, True)
            all_group.add(solids, layer=Z_ORDER[layer])
            solid_group.add(solids)
        return all_group, solid_group

    def make_tile_group(self, layer, mask=False):
        """
        Create a single sprite group for the selected layer.
        Pass mask=True to create collision masks for the tiles.
        If the sheet and source coordinates are found in the SPECIAL_TILES
        dict, a tile of that type will be made instead of the default.
        """
        group = pg.sprite.Group()
        for target in self.map_dict[layer]:
            sheet, source = self.map_dict[layer][target]
            if (sheet, source) in SPECIAL_TILES:
                TileType, kwargs = SPECIAL_TILES[(sheet,source)]
                group.add(TileType(sheet, source, target, mask, **kwargs))
            else:
                group.add(Tile(sheet, source, target, mask))
        return group

    def update(self, now):
        """
        Update all sprites; check any collisions that may have occured;
        and finally sort the main_sprite group by y coordinate.
        """
        self.all_group.update(now, self.solid_border)
        self.check_collisions()

    def check_collisions(self):
        """
        Check collisions and call the appropriate functions of the affected
        sprites.
        """
        call_mask = pg.sprite.collide_mask
        collide_group = pg.sprite.Group(self.solids, self.enemies, self.items)
        hit = pg.sprite.spritecollide(self.player, collide_group, False)
        mask_hits = pg.sprite.spritecollide(self.player, hit, False, call_mask)
        for hit in mask_hits:
            hit.collide_with_player(self.player)
        self.process_attacks()

    def process_attacks(self):
        """Check if player is attacking, and if so, check enemy collisions."""
        weapon = self.player.equipped["weapon"].sprite
        if weapon.attacking:
            for enemy in pg.sprite.spritecollide(weapon, self.enemies, False):
                enemy.got_hit(self.player, self.solid_border, self.items,
                              self.main_sprites, self.all_group)

    def draw(self, surface, interpolate):
        """Draw all sprites and layers to the surface."""
        surface.blit(self.background, (0,0))
        for sprite in self.main_sprites:
            speed = [interpolate*sprite.frame_speed[i] for i in (0,1)]
            sprite.rect.move_ip(*speed)
            self.all_group.change_layer(sprite, sprite.rect.centery)
        self.all_group.draw(surface)
