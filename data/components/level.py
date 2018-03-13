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


LAYERS = ("BG Colors", "BG Tiles", "Water", "Solid",
          "Solid/Fore", "Foreground", "Environment",
          "Enemies", "Items", "Chests", "Push", "Portal")


class CollisionRect(pg.sprite.Sprite):
    """A rect that can be used as a sprite for collision purposes."""
    def __init__(self, rect, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.rect = rect


class Tile(tools._BaseSprite):
    """A basic tile."""
    def __init__(self, sheet, source, target, mask):
        """If the player can collide with it pass mask=True."""
        tools._BaseSprite.__init__(self, target, prepare.CELL_SIZE)
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

    def update(self, *args):
        self.rect.topleft = self.exact_position


class PushBlock(Tile):
    """
    A class for blocks that the player can push on the map to trigger
    various events.
    """
    def __init__(self, sheet, source, target, mask, post_event,
                 pushable="1111", stack_height=2, event_key=None):
        """
        The argument post_event is a callback function (generally
        Level.post_map_event); it is used to trigger changes by posting
        the event_key to the level map.  Pushable is a 4 digit binary string;
        each bit corresponds to the directions NESW (for example the string
        '1110' would mean the block could be pushed in all directions except
        for West).
        """
        Tile.__init__(self, sheet, source, target, True)
        self.pushable = self.set_pushable_directions(pushable)
        self.stack_height = stack_height
        self.linked = None
        self.post_event = post_event
        self.mask.fill() #Solid block masks for pushblocks avoid problems.
        self.event_key = event_key
        self.start_rect = self.rect.copy()
        self.offset = [0,0]
        self.pushed = False
        self.is_pushing = False
        self.pushed_for_frames = 0
        self.push_direction = None
        self.speed = 1.5

    def set_pushable_directions(self, binary):
        """
        Return a set of the pushable direction strings from the binary
        representation.
        """
        directions = ["back", "right", "front", "left"]
        return {directions[i] for i,num in enumerate(binary) if num == "1"}

    def collide_with_player(self, player):
        """
        The player's position will initially be reset as with any solid
        block collision; then it is checked if the player would collide with
        the block if they took another step in their current direction
        (if they are currently walking).  If this returns True, set the
        push_direction to the player's direction.
        """
        player.collide_with_solid()
        if player.direction_stack and not (self.pushed or self.is_pushing):
            direction = player.direction_stack[-1]
            vector = prepare.DIRECT_DICT[player.direction]
            player.exact_position[0] += player.speed*vector[0]
            player.exact_position[1] += player.speed*vector[1]
            player.rect.topleft = player.exact_position
            if pg.sprite.collide_mask(self, player):
                self.push_direction = player.direction
            player.exact_position[0] -= player.speed*vector[0]
            player.exact_position[1] -= player.speed*vector[1]
            player.rect.topleft = player.exact_position

    def get_stacked_tiles(self, groups):
        """
        Find the tiles that are stacked on the pushblock via collision with the
        foreground group.
        """
        rect = pg.Rect(0, 0, 50, 50*self.stack_height)
        rect.bottomleft = self.rect.topleft
        test = CollisionRect(rect)
        return pg.sprite.spritecollide(test, groups["foreground"], False)

    def update(self, now, player, groups):
        """
        If the block has not yet been moved, check if the player is currently
        pushing the block.  If the block is currently moving, update its
        position.
        """
        if self.stack_height and not self.linked:
            self.linked = self.get_stacked_tiles(groups)
        if not (self.pushed or self.is_pushing):
            self.check_if_pushing(groups)
        elif self.is_pushing and not self.pushed:
            self.pushing()

    def check_if_pushing(self, groups):
        """
        If the player is pushing the block in a pushable direction, increment
        pushed_for_frames.  If the block has been being pushed for 15 frames,
        and the function check_if_clear has confirmed there are no enemies in
        the way, set is_pushing to True.  If the player is ever not pushing,
        reset pushed_for_frames back to zero.
        """
        if self.push_direction and self.push_direction in self.pushable:
            self.pushed_for_frames += 1
            if self.pushed_for_frames >= 15 and self.check_if_clear(groups):
                self.is_pushing = True
            else:
                self.push_direction = None
        else:
            self.pushed_for_frames = 0

    def check_if_clear(self, groups):
        """
        Check if there is an enemy that would be collided with in the final
        position of the block.
        """
        enemies = groups["enemies"]
        unit_vec = prepare.DIRECT_DICT[self.push_direction]
        final = unit_vec[0]*50, unit_vec[1]*50
        test_sprite = CollisionRect(self.start_rect.move(*final))
        return not pg.sprite.spritecollideany(test_sprite, enemies)

    def push_stack(self):
        if self.linked:
            ordered = sorted(self.linked, key=attrgetter('rect.y'), reverse=1)
            current = self.rect
            for sprite in ordered:
                sprite.rect.bottomleft = current.topleft
                sprite.exact_position = list(sprite.rect.topleft)
                current = sprite.rect

    def pushing(self):
        """
        Animate the movement of the block.  If the block has moved a full cell,
        post the event_key using the callback post_event (if applicable).
        """
        unit_vec = prepare.DIRECT_DICT[self.push_direction]
        vec = unit_vec[0]*self.speed, unit_vec[1]*self.speed
        self.offset = [self.offset[0]+vec[0], self.offset[1]+vec[1]]
        if any(abs(component) >= 50 for component in self.offset):
            self.pushed = True
            final = unit_vec[0]*50, unit_vec[1]*50
            self.rect.topleft = self.start_rect.move(*final).topleft
            if self.event_key:
                self.post_event(self.event_key)
        else:
            self.rect.topleft = self.start_rect.move(*self.offset).topleft
        self.push_stack()


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
        """
        Check if the chest is open.  Then check if the add_to_map variable
        has been set; if it has, add the new item to the appropriate sprite
        groups.  The actual item is instantly added to the player's inventory
        to avoid issues associated with leaving a map during the animation.
        """
        self.check_opened(player)
        if self.add_to_map:
            item_groups = (group_dict["items"], group_dict["main"],
                           group_dict["all"])
            item = item_sprites.ITEMS[self.item](self.rect, None, True,
                                    (self.map_name, self.key), *item_groups)
            item.get_item(player)
            self.add_to_map = False

    def interact_with(self, player):
        """
        Open chest when player presses the action key.  Chest can not be
        opened from above for both practical (collision mask changes) and
        aesthetic purposes.
        """
        if not self.open and player.rect.centery > self.rect.top+10:
            self.add_to_map = True


class PortalTile(pg.sprite.Sprite):
    def __init__(self, target, world, map_coords, start_coords, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.rect = pg.Rect(target, (50, 50))
        self.mask = pg.mask.Mask((50,50))
        self.mask.fill()
        self.world = world
        self.map_coords = map_coords
        self.start_coords = start_coords

    def collide_with_player(self, player):
        offset = player.rect.x - self.rect.x, player.rect.y - self.rect.y
        overlap = self.mask.overlap_area(player.mask, offset)
        if overlap > 800: # Magic Number (volume of player pixels)
            player.on_world_change(self.world, self.map_coords, self.start_coords)
        

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
        self.moving = pg.sprite.Group(self.player)
        self.all_group, self.solids, foreground = self.make_all_layer_groups()
        self.borders = self.make_borders()
        self.solid_border = pg.sprite.Group(self.solids, self.borders)
        self.interactables = pg.sprite.Group() ###
        self.projectiles = pg.sprite.Group()
        self.portals = pg.sprite.Group()
        self.group_dict = {"borders" : self.borders,
                           "solid_border" : self.solid_border,
                           "foreground" : foreground,
                           "projectiles" : self.projectiles,
                           "enemies" : self.enemies,
                           "items" : self.items,
                           "portals" : self.portals,
                           "main" : self.main_sprites,
                           "moving" : self.moving,
                           "all" : self.all_group}
        self.all_group.add(self.player)
        self.spawn()
        self.shadows = self.make_shadows()
        self.posted = set() # Set of map events that have been posted.
        self.make_chests()
        self.make_push()
        self.make_portal()

    def make_push(self):
        """Create all push blocks."""
        for target in self.map_dict["Push"]:
            data = self.map_dict["Push"][target]
            sheet, source = data[:2]
            args = [sheet, source, target, True, self.post_map_event]+data[2:]
            push = PushBlock(*args)
            self.all_group.add(push, layer=prepare.Z_ORDER["Solid"])
            groups = (self.solids, self.solid_border, self.moving)
            push.add(*groups)
            
    def make_portal(self):
        """Create all portals."""
        for target in self.map_dict["Portal"]:
            data = self.map_dict["Portal"][target]
            args = [target] + data
            portal = PortalTile(*args)
            groups = (self.portals,)
            portal.add(*groups)

    def make_chests(self):
        """
        Create any treasure chests on the screen.  Chests are both solid
        and interactable.
        """
        groups = (self.solid_border, self.solids, self.interactables)
        for target in self.map_dict["Chests"]:
            sheet, source, item, ident = self.map_dict["Chests"][target]
            args = (sheet, source, target, True, item, self.name, ident)
            chest = TreasureChest(*args)
            chest.add(groups)
            self.all_group.add(chest, layer=prepare.Z_ORDER["Solid"])
            chest.check_opened(self.player)

    def add_map_item(self, event):
        """
        If a map event is posted that the player doesn't already have,
        check if there is an item with that event ID and add it to the map.
        """
        for target in self.map_dict["Items"]:
            item, keyword = self.map_dict["Items"][target][2:]
            if keyword == event:
                groups = (self.items, self.main_sprites, self.all_group)
                args = target, None, False, (self.name, keyword)
                args += groups
                item_sprites.ITEMS[item](*args)

    def spawn(self):
        """Create enemies, adding them to the required groups."""
        groups = (self.enemies, self.main_sprites, self.moving, self.all_group)
        for target in self.map_dict["Enemies"]:
            sheet, source, speed = self.map_dict["Enemies"][target]
            enemy_sprites.ENEMY_DICT[source](target, speed, *groups)

    def make_shadows(self):
        """Create shadows for the player and all enemies."""
        shadows = [e.shadow for e in self.enemies if hasattr(e, "shadow")]
        shadows += [self.player.shadow]
        self.all_group.add(shadows, layer=prepare.Z_ORDER["Shadows"])
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
        layer = "BG Tiles"
        all_group.add(self.make_tile_group(layer), layer=prepare.Z_ORDER[layer])
        foreground = self.make_tile_group("Foreground")
        all_group.add(foreground, layer=prepare.Z_ORDER["Foreground"])
        for layer in ("Solid/Fore", "Solid", "Water"):
            solids = self.make_tile_group(layer, True)
            all_group.add(solids, layer=prepare.Z_ORDER[layer])
            solid_group.add(solids)
        return all_group, solid_group, foreground

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
        callback = tools.rect_then_mask
        groups = pg.sprite.Group(self.solids, self.enemies,
                                 self.items, self.projectiles, self.portals)
        hits = pg.sprite.spritecollide(self.player, groups, False, callback)
        for hit in hits:
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
        for sprite in self.moving:
            interpolated = (sprite.frame_speed[0]*interpolate,
                            sprite.frame_speed[1]*interpolate)
            sprite.rect.move_ip(*interpolated)
        for sprite in self.main_sprites:
            self.all_group.change_layer(sprite, sprite.rect.centery)
        self.all_group.draw(surface)

    def on_map_change(self):
        groups = pg.sprite.Group(self.group_dict["projectiles"],
                                 self.group_dict["enemies"])
        for sprite in groups:
            sprite.on_map_change()
