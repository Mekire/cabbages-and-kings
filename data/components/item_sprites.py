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
        self.frames = tools.strip_coords_from_sheet(ITEM_SHEET,
                                          ITEM_COORDS[name], prepare.CELL_SIZE)
        self.anim = tools.Anim(self.frames, 15)
        self.image = self.anim.get_next_frame(pg.time.get_ticks())
        #Subtract 1 from y axis to make item drop appear behind death anim.
        self.rect = pg.Rect((pos[0],pos[1]-1), prepare.CELL_SIZE)
        self.mask = pg.Mask(prepare.CELL_SIZE)
        self.mask.fill()
        self.exact_position = list(self.rect.topleft)
        self.timer = tools.Timer(duration*1000, 1) if duration else None

    def update(self, now, *args):
        if self.timer:
            self.timer.check_tick(now)
            if self.timer.done:
                self.kill()
        self.image = self.anim.get_next_frame(now)

    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Heart(_Item):
    def __init__(self, pos, duration, *groups):
        _Item.__init__(self, "heart", pos, duration, *groups)
        self.heal = 3

    def collide_with_player(self, player):
##        SFX["heart"].play()
        player.health = min(player.health+self.heal, prepare.MAX_HEALTH)
        self.kill()


ITEMS = {"heart" : Heart}
