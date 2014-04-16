import os
import sys
import pygame as pg

from operator import attrgetter
from .. import prepare, tools
from . import enemy_sprites, item_sprites


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

LAYERS = ("BG Colors", "BG Tiles", "Water", "Solid",
          "Solid/Fore", "Foreground", "Environment",
          "Enemies", "Items", "Chests")


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
    def __init__(self, _a, _b, target, mask, fps=4, frames=2, src=None):
        """
        The frames argument is the number of frames in the animation, and
        fps is the desired framerate of the animation; src is the source
        location on the animation sheet (not the water sheet).
        _a and _b are dummy variables that are not actually needed.  They
        are in the list of args so that the interface to Tile and AnimatedTile
        are the same.
        """
        Tile.__init__(self, "animsheet", src, target, mask)
        size = prepare.CELL_SIZE
        frames = tools.strip_from_sheet(self.sheet, src, size, frames)
        self.anim = tools.Anim(frames, fps)

    def update(self, now, *args):
        """Check if the image should change frame."""
        self.image = self.anim.get_next_frame(now)


class HazardTile(Tile):
    """Basic hazard tiles (cacti, spikes, etc.)"""
    def __init__(self, sheet, source, target, mask, dmg=1):
         Tile.__init__(self, sheet, source, target, True)
         self.attack = dmg

    def collide_with_player(self, player):
        """
        Hit the player and reset the player's position to ensure that it
        is not possible to glitch through a hazard.
        """
        player.got_hit(self)
        player.collide_with_solid(False)


class AnimatedHazard(AnimatedTile):
    """Animated hazards including lava."""
    def __init__(self, _a, _b, target, mask, fps=4, frames=2, src=None, dmg=1):
        AnimatedTile.__init__(self, _a, _b, target, mask, fps, frames, src)
        self.attack = dmg

    def collide_with_player(self, player):
        """
        Deal damage to the player; then reset the player's position to avoid
        the possibility of glitching through the obstacle.
        """
        player.got_hit(self)
        player.collide_with_solid(False)


class TreasureChest(Tile):
    """A class for adding treasure chests to the map."""
    def __init__(self, sheet, source, target, mask, item, map_name, key):
        Tile.__init__(self, "chests", (0,0), target, True)
        self.item = item
        self.map_name, self.key = map_name, key
        self.open = False
        self.open_image = self.sheet.subsurface(((50,0), prepare.CELL_SIZE))
        self.open_mask = pg.mask.from_surface(self.open_image)
        self.add_to_map = False

    def check_opened(self, player):
        """
        If the chest is not yet set to open, check if the player has the
        identifier for the item inside.  If so, open it and switch image/mask.
        """
        if not self.open:
            ident = player.identifiers
            if self.map_name in ident and self.key in ident[self.map_name]:
                self.open = True
                self.image = self.open_image
                self.mask = self.open_mask

    def update(self, now, player, group_dict, *args):
        self.check_opened(player)
        if self.add_to_map:
            item_groups = (group_dict["items"], group_dict["main"],
                           group_dict["all"])
            item = item_sprites.ITEMS[self.item](self.rect, None, True,
                                    (self.map_name, self.key), *item_groups)
            item.get_item(player)
            self.add_to_map = False

    def interact_with(self, player):
        if not self.open and player.rect.centery > self.rect.top+10:
            self.add_to_map = True


#All map tiles that need to have specific behavior should be added here.
#Keys are (sheet, source_coordinates); Values are the type of tile and
#keyword arguments for initializing it.
SPECIAL_TILES = {
    # Water
    ("water", (0, 0)) : (AnimatedTile, {"src" : (0,0)}),
    ("water", (0, 50)) : (AnimatedTile, {"src" : (0,50)}),
    ("water", (50, 0)) : (AnimatedTile, {"src" : (200,0)}),
    ("water", (50, 50)) : (AnimatedTile, {"src" : (200,50)}),
    ("water", (100, 0)) : (AnimatedTile, {"src" : (100,0)}),
    ("water", (150, 0)) : (AnimatedTile, {"src" : (300,0)}),
    ("water", (150, 50)) : (AnimatedTile, {"src" : (300,50)}),
    ("water", (200, 0)) : (AnimatedTile, {"src" : (300,100)}),
    ("water", (200, 50)) : (AnimatedTile, {"src" : (300,150)}),
    # Lava
    ("water", (0,100)) : (AnimatedHazard, {"src" : (0,100), "dmg" : 5}),
    ("water", (0,150)) : (AnimatedHazard, {"src" : (0,150), "dmg" : 5}),
    ("water", (50,100)) : (AnimatedHazard, {"src" : (200,100), "dmg" : 5}),
    ("water", (50,150)) : (AnimatedHazard, {"src" : (200,150), "dmg" : 5}),
    ("water", (100,100)) : (AnimatedHazard, {"src" : (100,100), "dmg" : 5}),
    ("water", (150, 100)) : (AnimatedHazard, {"src" : (100,50), "dmg" : 5}),
    ("water", (150, 150)) : (AnimatedHazard, {"src" : (100,150), "dmg" : 5}),
    ("water", (200, 100)) : (AnimatedHazard, {"src" : (0,200), "dmg" : 5}),
    ("water", (200, 150)) : (AnimatedHazard, {"src" : (100,200), "dmg" : 5}),
    # Cacti
    ("base", (350, 400)) : (HazardTile, {"dmg" : 1}),
    ("base", (250, 450)) : (HazardTile, {"dmg" : 1}),
    ("base", (300, 450)) : (HazardTile, {"dmg" : 1})}


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
        self.interactables = pg.sprite.Group() ###
        self.group_dict = {"solid_border" : self.solid_border,
                           "projectiles" : None,
                           "items" : self.items,
                           "main" : self.main_sprites,
                           "all" : self.all_group}
        self.all_group.add(self.player)
        self.spawn()
        self.shadows = self.make_shadows()
        self.posted = set() # Set of map events that have been posted.
        self.make_chests() ###Temporary

    def make_chests(self):
        groups = (self.solid_border, self.solids, self.interactables)
        for target in self.map_dict["Chests"]:
            sheet, source, item, ident = self.map_dict["Chests"][target]
            args = (sheet, source, target, True, item, self.name, ident)
            chest = TreasureChest(*args)
            chest.add(groups)
            self.all_group.add(chest, layer=Z_ORDER["Solid"])
            chest.check_opened(self.player)

    def add_map_item(self, event):
        for target in self.map_dict["Items"]:
            item, keyword = self.map_dict["Items"][target][2:]
            if keyword == event:
                groups = (self.items, self.main_sprites, self.all_group)
                args = target, None, False, (self.name, keyword)
                args += groups
                item_sprites.ITEMS[item](*args)

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
        return pg.sprite.Group(shadows)

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
        map_dict = {layer:{} for layer in LAYERS}
        with open(path) as myfile:
            map_dict.update(yaml.load(myfile))
        return map_dict

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

    def post_map_event(self, event):
        """
        Intercept a map_event and make appropriate changes to map.
        If the change has persistence the player should add the event to
        his list of identifiers.
        """
        identifiers = self.player.identifiers.setdefault(self.name, set())
        if event not in self.posted:
            self.posted.add(event)
            if event not in identifiers:
                self.add_map_item(event)
                ### Check map changes here too.

    def update(self, now):
        """
        Update all sprites; check any collisions that may have occured;
        and finally sort the main_sprite group by y coordinate.
        """
        self.all_group.update(now, self.player, self.group_dict)
        if not self.enemies:
            self.post_map_event("kill")
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
            interpolated = (sprite.frame_speed[0]*interpolate,
                            sprite.frame_speed[1]*interpolate)
            sprite.rect.move_ip(*interpolated)
            self.all_group.change_layer(sprite, sprite.rect.centery)
        self.all_group.draw(surface)
