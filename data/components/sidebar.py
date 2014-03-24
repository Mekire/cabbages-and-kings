import pygame as pg

from .. import prepare, tools


SIDEBAR_SIZE = (200, 700)
HEAL_SIZE = (35, 35)
HEAL_OFFSET = 15, 50
HEAL_SPACER = 45
PRIMARY_EQUIP = pg.Rect(20, 405, 64, 64)
SECONDARY_EQUIP = pg.Rect(115, 405, 64, 64)


STAT_LOCATIONS = {"money" : (110, 160),
                  "keys"  : (110, 220)}

SMALL_FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 34)



class SideBar(object):
    """
    A class for the HUD which is displayed on the right of the screen.
    """
    def __init__(self):
        self.image = pg.Surface(SIDEBAR_SIZE).convert()
        self.rect = self.image.get_rect(x=1000)
        self.cells = self.get_health_cells()
        self.stats = {"money" : (None,None), "keys" : (None,None)}

    def get_health_cells(self):
        """
        Strip cells from health sheet.
        """
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
        """Draw the players current health to the HUD."""
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

    def render_numbers(self, player):
        """
        Draw current stat numbers (money, keys, etc.) to the HUD.
        Number is only rerendered if it has changed.
        """
        for stat,value in self.stats.items():
            number, image = value
            current = player.inventory[stat]
            if current != number:
                image = SMALL_FONT.render(str(current), 0, pg.Color("white"))
                self.stats[stat] = (current, image)
            self.image.blit(image, STAT_LOCATIONS[stat])

    def render_gear(self, player):
        """Draw player's primary and secondary equips to sidebar."""
        display_image = player.equipped["weapon"].display
        primary = display_image.get_rect(center=PRIMARY_EQUIP.center)
        self.image.blit(display_image, primary)

    def update(self, player):
        """Update and redraw all elements to the image."""
        self.image.fill(prepare.BACKGROUND_COLOR)
        self.image.blit(prepare.GFX["misc"]["sidebargfx"], (0,0))
        self.render_health(player)
        self.render_numbers(player)
        self.render_gear(player)

    def draw(self, surface, offset=0):
        """Standard draw function."""
        surface.blit(self.image, (self.rect.x+offset, self.rect.y))
