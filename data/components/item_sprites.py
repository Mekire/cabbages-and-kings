import pygame as pg

from .. import tools, prepare


ITEM_SHEET = prepare.GFX["objects"]["items"]

ITEM_COORDS = {"heart" : [(0,0), (1,0)],
               "diamond" : [(0,1), (1,1)],
               "potion" : [(0,2), (1,2)],
               "key" : [(0,3), (1,3)]}


class _Item(pg.sprite.Sprite):
    def __init__(self, name, pos, duration, *groups):
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

    @property
    def frame_speed(self):
        return (self.exact_position[0]-self.old_position[0],
                self.exact_position[1]-self.old_position[1])

    def update(self, now, *args):
        self.old_position = self.exact_position[:]
        if self.timer:
            self.timer.check_tick(now)
            if self.timer.done:
                self.kill()
        self.image = self.anim.get_next_frame(now)

    def draw(self, surface, interpolate):
        surface.blit(self.image, self.rect)


class Heart(_Item):
    def __init__(self, pos, duration, *groups):
        _Item.__init__(self, "heart", pos, duration, *groups)
        self.heal = 3

    def collide_with_player(self, player):
##        SFX["heart"].play()
        player.health = min(player.health+self.heal, prepare.MAX_HEALTH)
        self.kill()


class Diamond(_Item):
    def __init__(self, pos, duration, *groups):
        _Item.__init__(self, "diamond", pos, duration, *groups)
        self.value = 5

    def collide_with_player(self, player):
##        SFX["money"].play()
        money = player.inventory["money"]
        player.inventory["money"] = min(money+self.value, prepare.MAX_MONEY)
        self.kill()


class Potion(_Item):
    def __init__(self, pos, duration, *groups):
        _Item.__init__(self, "potion", pos, duration, *groups)

    def collide_with_player(self, player):
##        SFX["get_item"].play()
        #Insert effect here.
        self.kill()


class Key(_Item):
    def __init__(self, pos, duration, *groups):
        _Item.__init__(self, "key", pos, duration, *groups)

    def collide_with_player(self, player):
##        SFX["get_item"].play()
        player.inventory["keys"] += 1
        self.kill()


ITEMS = {"heart" : Heart,
         "diamond" : Diamond,
         "potion" : Potion,
         "key" : Key}
