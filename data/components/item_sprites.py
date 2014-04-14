import pygame as pg

from .. import tools, prepare


ITEM_SHEET = prepare.GFX["objects"]["items"]

ITEM_COORDS = {"heart" : [(0,0), (1,0)],
               "diamond" : [(0,1), (1,1)],
               "potion" : [(0,2), (1,2)],
               "key" : [(0,3), (1,3)]}

RISE_SPEED = 1.5
MAX_RISE = 50


class _Item(pg.sprite.Sprite):
    def __init__(self, name, pos, duration, chest=False, ident=None, *groups):
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
        self.exact_position = list(self.rect.topleft)
        self.timer = tools.Timer(duration*1000, 1) if duration else None
        self.from_chest = chest
        self.identifier = ident  #Used to stop respawning of unique items.
        self.height = 0  #Used when item rises from chest.
        self.sound_effect = None

    @property
    def frame_speed(self):
        return (self.exact_position[0]-self.old_position[0],
                self.exact_position[1]-self.old_position[1])

    def collide_with_player(self, player):
        if not self.from_chest:
            self.get_item(player)
            self.kill()

    def get_item(self, player):
        if self.sound_effect:
            self.sound_effect.play()
        self.process_result(player)
        if self.identifier:
            flags = player.flags
            map_name, key = self.identifier
            flags.setdefault(map_name,set())
            flags[map_name].add(key)

    def update(self, now, *args):
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
        self.image = self.anim.get_next_frame(now)

    def draw(self, surface, interpolate):
        surface.blit(self.image, self.rect)


class Heart(_Item):
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "heart", pos, duration, chest, ident, *groups)
        self.heal = 3

    def process_result(self, player):
        player.health = min(player.health+self.heal, prepare.MAX_HEALTH)


class Diamond(_Item):
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "diamond", pos, duration, chest, ident, *groups)
        self.value = 5

    def process_result(self, player):
        money = player.inventory["money"]
        player.inventory["money"] = min(money+self.value, prepare.MAX_MONEY)


class Potion(_Item):
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "potion", pos, duration, chest, ident, *groups)

    def process_result(self, player):
        pass
        #Insert effect here.


class Key(_Item):
    def __init__(self, pos, duration, chest=False, ident=None, *groups):
        _Item.__init__(self, "key", pos, duration, chest, ident, *groups)

    def process_result(self, player):
        player.inventory["keys"] += 1


ITEMS = {"heart" : Heart,
         "diamond" : Diamond,
         "potion" : Potion,
         "key" : Key}
