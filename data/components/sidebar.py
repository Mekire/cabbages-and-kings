import pygame as pg

from .. import prepare, tools


SIDEBAR_SIZE = (200, 700)
HEAL_SIZE = (35, 35)
HEAL_OFFSET = 15, 50
HEAL_SPACER = 45


class SideBar(object):
    def __init__(self):
        self.image = pg.Surface(SIDEBAR_SIZE).convert()
        self.base = self.image.copy()
        self.base.blit(prepare.GFX["misc"]["sidebargfx"], (0,0))
        self.rect = self.image.get_rect(x=1000)
        self.cells = self.get_health_cells()

    def get_health_cells(self):
        cellsheet = prepare.GFX["misc"]["healthsheet"]
        cells = []
        for i in range(4):
            one_column = []
            for j in range(i+2):
                rect = pg.Rect((HEAL_SIZE[0]*i, HEAL_SIZE[1]*j), HEAL_SIZE)
                one_column.append(cellsheet.subsurface(rect))
            cells.append(one_column)
        return cells*2

    def render_health(self, player):
        count_health = 0
        for i,column in enumerate(self.cells):
            for cell in column[::-1]:
                if count_health != player.health:
                    if count_health < prepare.MAX_HEALTH//2:
                        pos_x = HEAL_OFFSET[0]+HEAL_SPACER*i
                        pos_y = HEAL_OFFSET[1]
                    else:
                        pos_x = HEAL_OFFSET[0]+HEAL_SPACER*(i-4)
                        pos_y = HEAL_OFFSET[1]+HEAL_SPACER
                    self.image.blit(cell, (pos_x,pos_y))
                    count_health += 1
                else:
                    return

    def update(self, player):
        self.image.blit(self.base, (0,0))
        self.render_health(player)

    def draw(self, surface):
        surface.blit(self.image, self.rect)
