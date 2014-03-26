"""
This module contains the logic for the camp menu screen.
"""

import pygame as pg

from operator import attrgetter
from .. import prepare, tools, state_machine, menu_helpers
from ..components import player, level, sidebar


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)
MEDIUM_FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 50) ###

HIGHLIGHT_COLOR = (108, 148, 200)

ARROWS = prepare.GFX["misc"]["menu_arrows"]
ARROW_SIZE = (86, 101)
ARROW_POS = [(62,520), (617,520)]

MAX_SCROLL = -prepare.PLAY_RECT.width
PLAYER_RECT = pg.Rect((32, 27), (400,400))

OPTIONS = ["EQUIP", "ABILITY", "ITEMS", "MAP"]
OPT_Y = 497
OPT_SPACER = 50
OPT_CENTER_X = 382

EQUIPPED_RECT = pg.Rect((473, 375), (258,50))

GEAR_BOX = prepare.GFX["misc"]["gear_box"]
GEAR_BOX_CENTER = (OPT_CENTER_X, 615)
GEAR_ORDER = ("head", "body", "armleg", "weapon", "shield")
GEAR_TITLE = ("Headgear", "Armor", "Gloves/Shoes", "Weapon", "Shield")

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
        """
        State machine, base images, and scrolling variables reset on startup.
        """
        state_machine._State.startup(self, now, persistant)
        state_dict = {"OPTIONS" : Options(),
                      "EQUIP" : EquipGeneral(),
                      "EQUIP_SPECIFIC" : EquipSpecific()}
        self.state_machine.setup_states(state_dict, "OPTIONS")
        self.player = self.persist["player"]
        self.state_machine.state.persist["player"] = self.player ###
        self.game_screen = pg.display.get_surface().copy()
        self.base = self.make_base_image()
        self.equipped = self.make_equipped_image()
        self.offset = 0
        self.is_scrolling = True

    def cleanup(self):
        """The state_machine.done variable must also be reset."""
        self.done = False
        self.state_machine.done = False
        return self.persist

    def make_base_image(self):
        """
        Build the main background image for the menu.
        """
        base = pg.Surface(prepare.PLAY_RECT.size).convert()
        base.fill(prepare.BACKGROUND_COLOR)
        base.blit(prepare.GFX["misc"]["campscreen"], (0,0))
        player = self.make_player_image()
        base.blit(player, PLAYER_RECT)
        return base

    def make_player_image(self):
        """Scale an image of the player up to approriate size."""
        size = PLAYER_RECT.size
        image = pg.Surface(size).convert()
        field = prepare.GFX["misc"]["charcreate"].subsurface(70, 55, 100, 100)#
        field = pg.transform.scale(field, size)##
##        image.fill(self.persist["bg_color"])
        image.blit(field, (0,0))
        player_anim = self.player.all_animations[0]["normal"]["front"]
        player_large = pg.transform.scale(player_anim.frames[0], size)
        image.blit(player_large, (0,0))
        return image

    def make_equipped_image(self):
        """Make image for player's currently equipped gear display."""
        image = pg.Surface(EQUIPPED_RECT.size).convert()
        image.fill(prepare.COLOR_KEY)
        image.set_colorkey(prepare.COLOR_KEY)
        for i,gear in enumerate(GEAR_ORDER):
            pos = (i*(prepare.CELL_SIZE[0]+2), 0)
            image.blit(self.player.equipped[gear].display, pos)
        return image

    def scroll(self, dt):
        """Offset the scrolling images until MAX_SCROLL is reached."""
        self.offset = max(self.offset-self.scroll_speed*dt, MAX_SCROLL)
        if self.offset == MAX_SCROLL:
            self.is_scrolling = False

    def update(self, surface, keys, now, dt):
        """
        Scroll if needed; update state machine; check if state_machine has
        quit; and draw everything.
        """
        if self.is_scrolling:
            self.scroll(dt)
        self.state_machine.update(surface, keys, now, dt)
        if self.state_machine.done:
            self.next = self.state_machine.state.next
            self.done = True
        if self.player.redraw:
            self.base.blit(self.make_player_image(), PLAYER_RECT)
            self.equipped = self.make_equipped_image()
            self.persist["sidebar"].update(self.player)
        self.draw(surface)

    def get_event(self, event):
        """
        The "S-key" immediately returns to game from all substates.
        All other events are passed down to the state machine.
        """
        if not self.is_scrolling:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_s:
                    self.done = True
            self.state_machine.get_event(event)

    def draw(self, surface):
        """
        Blit camp items to seperate surface; blit game_screen if still
        scrolling; finally draw sidebar.
        """
        self.image.blit(self.base, (0,0))
        self.state_machine.state.draw(self.image)
        self.image.blit(self.equipped, EQUIPPED_RECT)
        if self.is_scrolling:
            surface.blit(self.game_screen, (self.offset, 0))
        surface.blit(self.image, (prepare.SCREEN_RECT.w+self.offset,0))
        self.persist["sidebar"].draw(surface, self.offset)


class Options(menu_helpers.BasicMenu):
    """The root options in the camp menu."""
    def __init__(self):
        menu_helpers.BasicMenu.__init__(self, 4)
        self.options = self.make_options(MEDIUM_FONT, OPTIONS, OPT_Y,
                                         OPT_SPACER, OPT_CENTER_X)

    def draw(self, surface):
        """Draw menu options highlighting the currently selected one."""
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
        """Return to game."""
        self.quit = True
        self.next = "GAME"


class EquipGeneral(menu_helpers.BasicMenu):
    """Substate for player to select the type of gear to equip."""
    def __init__(self):
        menu_helpers.BasicMenu.__init__(self, 5)
        self.arrows = tools.strip_from_sheet(ARROWS, (0,0), ARROW_SIZE, 2)
        self.rendered = {}

    def startup(self, now, persistant):
        """Remake the gear display image on startup."""
        self.persist = persistant
        self.player = persistant["player"]
        self.gear_box, self.gear_box_rect = self.make_gear_box()
        self.start_time = now

    def cleanup(self):
        """Preserve gear display for next state."""
        self.done = False
        self.persist["gear_display"] = (self.gear_box, self.gear_box_rect)
        return self.persist

    def make_gear_box(self):
        """
        Create display image for all gear of a specific type.
        Display order is determined by the sort stat attribute of the items.
        """
        gear_box = pg.Surface(GEAR_BOX.get_size()).convert()
        gear_box.fill(prepare.COLOR_KEY)
        gear_box.set_colorkey(prepare.COLOR_KEY)
        gear_type = GEAR_ORDER[self.index]
        gear = list(self.player.inventory[gear_type].values())
        sorted_gear = sorted(gear, key=attrgetter("sort_stat"))
        self.persist["sorted_gear"] = sorted_gear
        for i,item in enumerate(sorted_gear):
            y,x = divmod(i, 5) #2 rows of 5 columns.
            if item is self.player.equipped[gear_type]: #Save current gear ind.
                self.persist["equipped"] = (gear_type, [x,y])
            pos = (2+x*(prepare.CELL_SIZE[0]+2), 2+y*(prepare.CELL_SIZE[0]+2))
            gear_box.blit(item.display, pos)
        return gear_box, gear_box.get_rect(center=GEAR_BOX_CENTER)

    def get_event(self, event):
        """
        Process events as any other menu, but remake the gear box display if
        the menu index changes.
        """
        menu_helpers.BasicMenu.get_event(self, event)
        if event.type == pg.KEYDOWN and event.key in prepare.DEFAULT_CONTROLS:
            self.gear_box, self.gear_box_rect = self.make_gear_box()

    def draw(self, surface):
        """Draw equipped highlight; title; arrows; and gear box."""
        highlight = pg.Rect(EQUIPPED_RECT.topleft, prepare.CELL_SIZE)
        highlight.move_ip((prepare.CELL_SIZE[0]+2)*self.index, 0)
        surface.fill(pg.Color("yellow"), highlight.inflate(4,4))
        surface.fill(HIGHLIGHT_COLOR, highlight)
        title = GEAR_TITLE[self.index]
        rend_it = (FONT, title, pg.Color("white"), self.rendered)
        rended = tools.get_rendered(*rend_it)
        rend_rect = rended.get_rect(center=(OPT_CENTER_X,OPT_Y))
        surface.blit(rended, rend_rect)
        for i,arrow in enumerate(self.arrows):
            surface.blit(arrow, ARROW_POS[i])
        surface.blit(GEAR_BOX, self.gear_box_rect)
        surface.blit(self.gear_box, self.gear_box_rect)

    def pressed_enter(self):
        """Enter substate to choose specific item."""
        self.done = True
        self.next = "EQUIP_SPECIFIC"

    def pressed_exit(self):
        """Return to main camp options if a cancel key is pressed."""
        self.done = True
        self.next = "OPTIONS"


class EquipSpecific(menu_helpers.BidirectionalMenu):
    """Substate for player to select the specific gear to equip."""
    def __init__(self):
        menu_helpers.BidirectionalMenu.__init__(self, (5,2))
        self.rendered = {}

    def startup(self, now, persistant):
        """Get player and player-gear related variables from persist."""
        self.persist = persistant
        self.player = persistant["player"]
        self.gear_image, self.gear_rect = self.persist["gear_display"]
        self.gear_type, self.index = self.persist["equipped"]
        self.sorted_gear = self.persist["sorted_gear"]
        self.start_time = now

    def get_event(self, event):
        """
        Run standard BiDirectional get_event, but don't let the player move
        cursor to an unoccupied cell.
        """
        old_index = self.index[:]
        menu_helpers.BidirectionalMenu.get_event(self, event)
        un_divmod = self.index[1]*self.option_lengths[1]+self.index[0]
        try:
            self.sorted_gear[un_divmod]
        except IndexError:
            self.index = old_index

    def draw(self, surface):
        self.draw_text(surface)
        surface.blit(GEAR_BOX, self.gear_rect)
        self.draw_highlight(surface)
        surface.blit(self.gear_image, self.gear_rect)

    def draw_text(self, surface):
        un_divmod = self.index[1]*self.option_lengths[1]+self.index[0]
        title = self.sorted_gear[un_divmod].title
        rend_it = (MEDIUM_FONT, title, pg.Color("white"), self.rendered)
        rended = tools.get_rendered(*rend_it)
        rend_rect = rended.get_rect(center=(OPT_CENTER_X,OPT_Y))
        surface.blit(rended, rend_rect)

    def draw_highlight(self, surface):
        """Draw the specific gear selection cursor to the screen."""
        highlight_pos = self.gear_rect.x+2, self.gear_rect.y+2
        highlight = pg.Rect(highlight_pos, prepare.CELL_SIZE)
        spacer = prepare.CELL_SIZE[0]+2
        x,y = self.index
        highlight.move_ip(spacer*x, spacer*y)
        surface.fill(pg.Color("yellow"), highlight.inflate(4,4))
        surface.fill(HIGHLIGHT_COLOR, highlight)

    def pressed_enter(self):
        """
        Change the player's selected equipment;
        the return to equip type select.
        """
        un_divmod = self.index[1]*self.option_lengths[1]+self.index[0]
        self.player.change_equip(self.gear_type, self.sorted_gear[un_divmod])
        self.pressed_exit()

    def pressed_exit(self):
        """Return to equip type select if a cancel key is pressed."""
        self.done = True
        self.next = "EQUIP"
