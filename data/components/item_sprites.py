import pygame as pg

from .. import tools, prepare
from . import equips


ITEM_SHEET = prepare.GFX["objects"]["items"]

ITEM_COORDS = {"heart" : [(0,0), (1,0)],
               "diamond" : [(0,1), (1,1)],
               "potion" : [(0,2), (1,2)],
               "key" : [(0,3), (1,3)]}

RISE_SPEED = 1.5
MAX_RISE = 50


class _Item(pg.sprite.Sprite):
    """Base class for specific items."""
    def __init__(self, name, pos, duration, chest=False, ident=None, *groups):
        """
        The argument name is the type of item corresponding to the ITEMS dict;
        pos is the location on the map the item is located; if the item is in
        a treasure chest, pass chest=True; if the player can only get this item
        once, pass a unique (to the map) ident string to be stored in the
        player's identifiers attribute.
        """
        pg.sprite.Sprite.__init__(self, *groups)
        coords, size = ITEM_COORDS[name], prepare.CELL_SIZE
        self.frames = tools.strip_coords_from_sheet(ITEM_SHEET, coords, size)
        self.anim = tools.Anim(self.frames, 7)
        self.image = self.anim.get_next_frame(pg.time.get_ticks())
        #Subtract 1 from y axis to make item drop appear behind death anim.
        self.rect = pg.Rect((pos[0],pos[1]-1), prepare.CELL_SIZE)
        self.exact_position = list(self.rect.topleft)
        self.old_position = self.exact_position[:]
        self.mask = pg.Mask(prepare.CELL_SIZE)
        self.mask.fill()
        self.timer = tools.Timer(duration*1000, 1) if duration else None
        self.from_chest = chest
        self.identifier = ident  #Used to stop respawning of unique items.
        self.height = 0  #Used when item rises from chest.
        self.sound_effect = None

    @property
    def frame_speed(self):
        """Get the total amount the object has been displaced this frame."""
        return (self.exact_position[0]-self.old_position[0],
                self.exact_position[1]-self.old_position[1])

    def collide_with_player(self, player):
        """
        Objects that aren't inside treasure chests bestow their effects and
        disappear on collision with the player.
        """
        if not self.from_chest:
            self.get_item(player)
            self.kill()

    def get_item(self, player):
        """
        Play sound effect; bestow effect of item; add unique identifier to
        player's identifiers if applicable.
        """
        if self.sound_effect:
            self.sound_effect.play()
        self.process_result(player)
        if self.identifier:
            identifiers = player.identifiers
            map_name, key = self.identifier
            identifiers.setdefault(map_name, set())
            identifiers[map_name].add(key)

    def update(self, now, *args):
        """
        If the object has a duration check to see if it has expired;
        If the item came from a chest animate it rising appropriately;
        Get next frame of animation.
        """
        self.old_position = self.exact_position[:]
        if self.timer:
            self.timer.check_tick(now)
            if self.timer.done:
                self.kill()
        if self.from_chest:
            self.height += RISE_SPEED
            self.exact_position[1] -= RISE_SPEED
            if self.height >= MAX_RISE:
                self.kill()
        self.rect.topleft = self.exact_position
        if hasattr(self, "anim"):
            self.image = self.anim.get_next_frame(now)

    def draw(self, surface, interpolate):
        """Basic draw function."""
        surface.blit(self.image, self.rect)


class Heart(_Item):
    """Fundamental healing item."""
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "heart", pos, duration, chest, ident, *groups)
        self.heal = 3

    def process_result(self, player):
        """Restore self.heal amount of health up to the player's max."""
        player.health = min(player.health+self.heal, prepare.MAX_HEALTH)


class Diamond(_Item):
    """A currency item worth 5 units."""
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "diamond", pos, duration, chest, ident, *groups)
        self.value = 5

    def process_result(self, player):
        """
        Add self.value to the player's inventory["money"] up to MAX_MONEY.
        """
        money = player.inventory["money"]
        player.inventory["money"] = min(money+self.value, prepare.MAX_MONEY)


class Potion(_Item):
    """Cure poison effect. (not implemented)."""
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "potion", pos, duration, chest, ident, *groups)

    def process_result(self, player):
        """Not implemented."""
        pass
        #Insert effect here.


class Key(_Item):
    """Basic key for generic doors."""
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "key", pos, duration, chest, ident, *groups)

    def process_result(self, player):
        """Add 1 to player's inventory["keys"]."""
        player.inventory["keys"] += 1


def make_equip_drop(GearClass):
    """Given an equipment class, return a corresponding drop item class."""
    class EquipDrop(_Item):
        """This class works for creating drops for all equipment."""
        def __init__(self, pos, dur, chest=False, ident=None, *groups):
            pg.sprite.Sprite.__init__(self, *groups)
            self.item = GearClass()
            self.image = self.item.display
            self.rect = pg.Rect((pos[0],pos[1]-1), prepare.CELL_SIZE)
            self.exact_position = list(self.rect.topleft)
            self.old_position = self.exact_position[:]
            self.mask = pg.Mask(prepare.CELL_SIZE)
            self.mask.fill()
            self.timer = None
            self.from_chest = chest
            self.identifier = ident  #Used to stop respawning of unique items.
            self.height = 0  #Used when item rises from chest.
            self.sound_effect = None

        def process_result(self, player):
            """Add the gear item to the player's inventory."""
            gear, name = self.item.sheet, self.item.name
            player.inventory[gear][name] = self.item
    return EquipDrop #Return the class, not an instance.


ITEMS = {"heart" : Heart,
         "diamond" : Diamond,
         "potion" : Potion,
         "key" : Key,
         ("head", "helm") : make_equip_drop(equips.Helm),
         ("head", "sader") : make_equip_drop(equips.Sader),
         ("head", "diver") : make_equip_drop(equips.Diver),
         ("head", "goggles") : make_equip_drop(equips.TopGoggles),
         ("body", "chain") : make_equip_drop(equips.ChainMail),
         ("shield", "tin") : make_equip_drop(equips.TinShield),
         ("weapon", "labrys") : make_equip_drop(equips.Labrys),
         ("weapon", "pitch") : make_equip_drop(equips.PitchFork)}
