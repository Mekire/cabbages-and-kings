"""
This module contains the logic for the camp menu screen.
"""

import pygame as pg

from operator import attrgetter
from .. import prepare, tools, state_machine, menu_helpers
from ..components import player, level, sidebar


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)
MEDIUM_FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 50) ###

ARROWS = prepare.GFX["misc"]["menu_arrows"]
ARROW_SIZE = (86, 101)
ARROW_POS = [(62,520), (617,520)]

MAX_SCROLL = -prepare.PLAY_RECT.width
PLAYER_POSITION = (32, 27)
PLAYER_SIZE = (400, 400)

GEAR_BOX = prepare.GFX["misc"]["gear_box"]
GEAR_ORDER = ("head", "body", "armleg", "weapon", "shield")
GEAR_TITLE = ("Headgear", "Armor", "Gloves/Shoes", "Weapon", "Shield")
GEAR_POSITION = (473, 375)

OPTIONS = ["EQUIP", "ABILITY", "ITEMS", "MAP"]
OPT_Y = 497
OPT_SPACER = 50
OPT_CENTER_X = 382

NOT_IMPLEMENTED = ["ABILITY", "ITEMS", "MAP"]  ###


class Camp(state_machine._State):
    """State for changing gear, selecting items, etc."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.scroll_speed = 1200
        self.next = "GAME"
        self.state_machine = state_machine.StateMachine()
        self.image = pg.Surface(prepare.PLAY_RECT.size).convert()

    def startup(self, now, persistant):
        state_machine._State.startup(self, now, persistant)
        state_dict = {"OPTIONS" : Options(),
                      "EQUIP" : EquipGeneral()}
        self.state_machine.setup_states(state_dict, "OPTIONS")
        self.player = self.persist["player"]
        self.state_machine.state.persist["player"] = self.player ###
        self.game_screen = pg.display.get_surface().copy()
        self.base = self.make_base_image()
        self.gear = self.make_gear_image()
        self.offset = 0
        self.is_scrolling = True

    def cleanup(self):
        self.done = False
        self.state_machine.done = False
        return self.persist

    def make_base_image(self):
        base = pg.Surface(prepare.PLAY_RECT.size).convert()
        base.fill(prepare.BACKGROUND_COLOR)
        base.blit(prepare.GFX["misc"]["campscreen"], (0,0))
        player = self.make_player_image()
        base.blit(player, PLAYER_POSITION)
        return base

    def make_player_image(self):
        image = pg.Surface(PLAYER_SIZE).convert()
        field = prepare.GFX["misc"]["charcreate"].subsurface(70, 55, 100, 100)#
        field = pg.transform.scale(field, (400,400))##
##        image.fill(self.persist["bg_color"])
        image.blit(field, (0,0))
        player_anim = self.player.all_animations[0]["normal"]["front"]
        player_large = pg.transform.scale(player_anim.frames[0], PLAYER_SIZE)
        image.blit(player_large, (0,0))
        return image

    def make_gear_image(self):
        image = pg.Surface((258,50)).convert()
        image.fill(prepare.COLOR_KEY)
        image.set_colorkey(prepare.COLOR_KEY)
        for i,gear in enumerate(GEAR_ORDER):
            pos = (i*(prepare.CELL_SIZE[0]+2), 0)
            image.blit(self.player.equipped[gear].display, pos)
        return image

    def scroll(self, dt):
        self.offset = max(self.offset-self.scroll_speed*dt, MAX_SCROLL)
        if self.offset == MAX_SCROLL:
            self.is_scrolling = False

    def update(self, surface, keys, now, dt):
        if self.is_scrolling:
            self.scroll(dt)
        self.state_machine.update(surface, keys, now, dt)
        if self.state_machine.done:
            self.next = self.state_machine.state.next
            self.done = True
        self.draw(surface)

    def get_event(self, event):
        if not self.is_scrolling:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.done = True
            self.state_machine.get_event(event)

    def draw(self, surface):
        self.image.blit(self.base, (0,0))
        self.state_machine.state.draw(self.image)
        self.image.blit(self.gear, GEAR_POSITION)
        if self.is_scrolling:
            surface.blit(self.game_screen, (self.offset, 0))
        surface.blit(self.image, (prepare.SCREEN_RECT.w+self.offset,0))
        self.persist["sidebar"].draw(surface, self.offset)


class Options(menu_helpers.BasicMenu):
    def __init__(self):
        menu_helpers.BasicMenu.__init__(self, 4)
        self.options = self.make_options(MEDIUM_FONT, OPTIONS, OPT_Y,
                                         OPT_SPACER, OPT_CENTER_X)

    def draw(self, surface):
        for i,val in enumerate(OPTIONS):
            which = "selected" if i==self.index else "unselected"
            msg, rect = self.options[which][i]
            surface.blit(msg, rect)

    def pressed_enter(self):
        """Enter next substate or view the controls screen on enter."""
        self.next = OPTIONS[self.index]
        if self.next not in NOT_IMPLEMENTED:
            self.done = True

    def pressed_exit(self):
        self.quit = True
        self.next = "GAME"


class EquipGeneral(menu_helpers.BasicMenu):
    def __init__(self):
        menu_helpers.BasicMenu.__init__(self, 5)
        self.arrows = tools.strip_from_sheet(ARROWS, (0,0), ARROW_SIZE, 2)
        self.rendered = {}

    def startup(self, now, persistant):
        self.persist = persistant
        self.player = persistant["player"]
        self.gear_box, self.gear_box_rect = self.make_gear_box()
        self.start_time = now

    def make_gear_box(self):
        gear_box = pg.Surface(GEAR_BOX.get_size()).convert()
        gear_box.fill(prepare.COLOR_KEY)
        gear_box.set_colorkey(prepare.COLOR_KEY)
        gear_type = GEAR_ORDER[self.index]
        relevant = list(self.player.inventory[gear_type].values())
        sorted_relevant = sorted(relevant, key=attrgetter("sort_stat"))
        for i,item in enumerate(sorted_relevant):
            y,x = divmod(i, 5)
            pos = (2+x*(prepare.CELL_SIZE[0]+2), 2+y*(prepare.CELL_SIZE[0]+2))
##            item = self.player.inventory[gear_type][item]
            gear_box.blit(item.display, pos)
        return gear_box, gear_box.get_rect(center=(OPT_CENTER_X,615))

    def get_event(self, event):
        menu_helpers.BasicMenu.get_event(self, event)
        if event.type == pg.KEYDOWN and event.key in prepare.DEFAULT_CONTROLS:
            self.gear_box, self.gear_box_rect = self.make_gear_box()

    def draw(self, surface):
        rect = pg.Rect(GEAR_POSITION, prepare.CELL_SIZE)
        rect.move_ip(52*self.index,0)
        surface.fill(pg.Color("yellow"), rect.inflate(4,4))
        surface.fill((108, 148, 200), rect)
        title = GEAR_TITLE[self.index]
        rend_it = (FONT, title, pg.Color("white"), self.rendered)
        rended = tools.get_rendered(*rend_it)
        rend_rect = rended.get_rect(center=(OPT_CENTER_X,OPT_Y))
        surface.blit(rended, rend_rect)
        for i,arrow in enumerate(self.arrows):
            surface.blit(arrow, ARROW_POS[i])
        surface.blit(GEAR_BOX, self.gear_box_rect)
        surface.blit(self.gear_box, self.gear_box_rect)

    def pressed_exit(self):
        self.done = True
        self.next = "OPTIONS"
