"""
Contains classes used for the player selection screen.
"""

import os
import sys
import pygame as pg

from .. import prepare, state_machine
from ..components import enemy_sprites, player


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)
SMALL_FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 32)

OPTIONS = ["SELECT/REGISTER", "DELETE", "CONTROLS"]
HIGHLIGHT_COLOR = (108, 148, 136)

#Placement and spacing constants.
OPTION_Y = 541
OPTION_SPACER = 59
SLOT_SPACER = 125
MAIN_TOPLEFT = (100, 40)
NAME_START = (320, 115)
PLAYER_START = (170, 95)
ITEM_IMAGES = (625, 95)
ITEM_START = (ITEM_IMAGES[0]+85, ITEM_IMAGES[1])
ITEM_SPACER = 60
STAT_START = (805, 128)
STAT_SPACER = 75
STAT_TEXT_SPACE = 45


class Select(state_machine._State):
    """
    This State is updated while our game shows the player select screen.
    This state is made up of four substates to organize updating;
    Options, SelectRegister, Delete, and Confirm.
    """
    def __init__(self):
        state_machine._State.__init__(self)
        self.next = "GAME"
        self.timeout = 15
        self.cabbages = pg.sprite.Group(MenuCabbage(25, 225, (25,525), 100),
                                      MenuCabbage(825, 1025, (1025,525), -100))
        self.state_machine = state_machine.StateMachine()

    def startup(self, now, persistant):
        """
        Recreate the substates and substate dict when this state starts up.
        """
        state_machine._State.startup(self, now, persistant)
        state_dict = {"OPTIONS" : Options(),
                      "SELECT/REGISTER" : SelectRegister(),
                      "DELETE" : Delete(),
                      "CONFIRM" : Confirm()}
        self.state_machine.setup_states(state_dict, "OPTIONS")
        self.state_machine.done = False

    def cleanup(self):
        """
        Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        """
        self.done = False
        regi = self.state_machine.state_dict["SELECT/REGISTER"]
        options = self.state_machine.state_dict["OPTIONS"]
        self.persist["save_slot"] = regi.index
        self.persist["player"] = options.players[regi.index]
        return self.persist

    def update(self, surface, keys, now, dt):
        """
        Updates the Cabbages; then the current substate; and finally
        checks to see if the game state or substate needs to change.
        """
        self.cabbages.update(now, dt)
        self.state_machine.update(surface, keys, now, dt)
        check_timeout = now-self.start_time > 1000.0*self.timeout
        if self.state_machine.state_name == "OPTIONS" and check_timeout:
            self.next = "TITLE"
            self.done = True
        elif self.state_machine.done:
            self.next = self.state_machine.state.next
            self.done = True
        self.render(surface)

    def render(self, surface):
        """
        Fill the screen; let the substates handle their own rendering;
        then draw the Cabbages.
        """
        surface.fill(prepare.BACKGROUND_COLOR)
        self.state_machine.state.draw(surface)
        self.cabbages.draw(surface)

    def get_event(self, event):
        """
        Get events from Control.
        """
        if event.type == pg.KEYDOWN:
            self.start_time = pg.time.get_ticks()
        self.state_machine.get_event(event)


class SelectState(state_machine._State):
    """Base class for all Select state substates."""
    def __init__(self):
       state_machine._State.__init__(self)
       self.index = 0
       self.rendered = {}

    def get_event(self, event):
        """
        Generic event getter for scrolling through menus.
        """
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_DOWN:
                self.index = (self.index+1)%self.option_length
            elif event.key == pg.K_UP:
                self.index = (self.index-1)%self.option_length
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.pressed_enter()
            elif event.key in (pg.K_x, pg.K_ESCAPE):
                self.pressed_exit()

    def draw_player(self, surface, player_sprite, index, redraw=False):
        """
        Draw the player in slot index.  Setting the redraw flag allows for
        the player to be animated.
        """
        if player_sprite != "EMPTY":
            if player_sprite.image and not player_sprite.redraw:
                player_sprite.redraw = redraw
            player_sprite.adjust_frames(pg.time.get_ticks())
            expand = pg.transform.scale(player_sprite.image, (100,100))
            position = (PLAYER_START[0], PLAYER_START[1]+SLOT_SPACER*index)
            surface.blit(expand, position)
            self.draw_player_stats(surface, player_sprite, index)

    def draw_player_stats(self, surface, player_sprite, index):
        """Draw the player's key items and stats to their character slot."""
        items = prepare.GFX["misc"]["sidebargfx"].subsurface(20, 160, 80, 100)
        icons = prepare.GFX["misc"]["icons"]
        surface.blit(items, (ITEM_IMAGES[0],ITEM_IMAGES[1]+index*SLOT_SPACER))
        for i,stat in enumerate(["money", "keys"]):
            num = player_sprite.inventory[stat]
            pos_y = ITEM_START[1]+index*SLOT_SPACER+i*ITEM_SPACER
            surface.blit(self.get_rendered(str(num)), (ITEM_START[0], pos_y))
        defense = str(player_sprite.defense)
        strength = str(player_sprite.strength)
        speed = "{:.1f}".format(player_sprite.speed/20.0)
        for i,stat in enumerate((strength,defense,speed)):
            pos = STAT_START[0]+STAT_SPACER*i, STAT_START[1]+SLOT_SPACER*index
            surface.blit(icons, pos, (34*i,0,34,34))
            rendered = self.get_rendered(stat)
            surface.blit(rendered, (pos[0]+STAT_TEXT_SPACE,pos[1]))

    def get_rendered(self, to_render):
        """Simple cache to avoid rerendering text."""
        if to_render in self.rendered:
            image = self.rendered[to_render]
        else:
            image = SMALL_FONT.render(to_render, 0, pg.Color("white"))
            self.rendered[to_render] = image
        return image

    def make_options(self, font, choices, y_start, y_space):
        """
        Makes prerendered (text,rect) tuples for basic text menus.
        Both selected and non-selected versions are made of each.
        Used by both the Option and Confirm menus.
        """
        options = {}
        args = [font, choices, pg.Color("white"), y_start, y_space]
        options["unselected"] = make_text_list(*args)
        args = [font, choices, pg.Color("yellow"), y_start, y_space]
        options["selected"] = make_text_list(*args)
        return options

    def update(self, *args):
        pass

    def pressed_enter(self):
        pass

    def pressed_exit(self):
        pass


class Options(SelectState):
    """
    Essentially the main menu state of the whole game.
    """
    def __init__(self):
       SelectState.__init__(self)
       self.option_length = 3
       self.players = self.load_players()
       self.names = self.make_player_names()
       self.options = self.make_options(FONT, OPTIONS, OPTION_Y, OPTION_SPACER)
       self.image = pg.Surface(prepare.SCREEN_SIZE).convert()
       self.image.set_colorkey(prepare.COLOR_KEY)
       self.image.fill(prepare.COLOR_KEY)

    def startup(self, now, persistant):
        """Reload all players and rerender their names on startup."""
        state_machine._State.startup(self, now, persistant)
        self.image.fill(prepare.COLOR_KEY)
        self.players = self.load_players()
        self.names = self.make_player_names()

    def load_players(self):
        """
        Load player data.  If no data is find create three empty slots.
        """
        players = ["EMPTY", "EMPTY", "EMPTY"]
        try:
            with open(prepare.SAVE_PATH) as my_file:
                data = yaml.load(my_file)
            for i,play_data in enumerate(data):
                if play_data != "EMPTY":
                    players[i] = player.Player((0,0,50,50), "front", play_data)
        except IOError:
            pass
        return players

    def make_player_names(self):
        """
        Return a list of (name,rect) tuples for each player in self.players.
        """
        names = []
        for i,player in enumerate(self.players):
            try:
                args = FONT, player.name, pg.Color("white"), (0,0)
            except AttributeError:
                args = FONT, player, pg.Color("white"), (0,0)
            msg, rect = render_font(*args)
            rect.topleft = NAME_START[0], NAME_START[1]+SLOT_SPACER*i
            names.append((msg, rect))
        return names

    def cleanup(self):
        """
        Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        """
        self.done = False
        self.persist["options_bg"] = self.image
        self.persist["players"] = self.players
        return self.persist

    def pressed_enter(self):
        """Enter next substate or view the controls screen on enter."""
        self.next = OPTIONS[self.index]
        if self.next == "DELETE":
            if not all(player=="EMPTY" for player in self.players):
                self.done = True
        elif self.next == "CONTROLS":
            self.quit = True
        else:
            self.done = True

    def draw(self, surface):
        """
        Blit the base image and options to a seperate surface for later use.
        Then blit that surface and the players to the screen.
        """
        self.image.blit(prepare.GFX["misc"]["charcreate"], MAIN_TOPLEFT)
        for name_info in self.names:
            self.image.blit(*name_info)
        for i,val in enumerate(OPTIONS):
            which = "selected" if i==self.index else "unselected"
            msg, rect = self.options[which][i]
            self.image.blit(msg, rect)
        surface.blit(self.image, (0,0))
        for i,player_sprite in enumerate(self.players):
            self.draw_player(surface, player_sprite, i)


class CharHighlighter(SelectState):
    """
    Both substates SelectRegister and Delete inherit from this class.
    Contains the logic for drawing the player selection highlight cursor.
    """
    def __init__(self):
       SelectState.__init__(self)
       self.option_length = 3
       self.highlight_rect = pg.Rect(129, 83, 942, 124)

    def draw(self, surface):
        """
        Draw the highlight first; then the base screen image; finally draw
        the players, animating the currently selected player.
        """
        highlight = self.highlight_rect.move(0, SLOT_SPACER*self.index)
        surface.fill(HIGHLIGHT_COLOR, highlight)
        surface.blit(self.persist["options_bg"], (0,0))
        for i,player_sprite in enumerate(self.persist["players"]):
            redraw = i == self.index
            self.draw_player(surface, player_sprite, i, redraw)

    def pressed_exit(self):
        """Return to options menu."""
        self.done = True
        self.next = "OPTIONS"


class SelectRegister(CharHighlighter):
    """State for selecting (or creating a new) character."""
    def __init__(self):
        CharHighlighter.__init__(self)

    def pressed_enter(self):
        """
        If a already created player is selected, enter game with that player;
        Else enter the "register a new player" state.
        """
        if self.persist["players"][self.index] != "EMPTY":
            self.quit = True
            self.next = "GAME"
        else:
            self.quit = True
            self.next = "REGISTER"


class Delete(CharHighlighter):
    """
    Substate updates when the Delete option is selected from the option menu.
    """
    def __init__(self):
        CharHighlighter.__init__(self)

    def pressed_enter(self):
        """
        If there is a player at the selected index, enter confirm substate.
        """
        if self.persist["players"][self.index] != "EMPTY":
            self.done = True
            self.next = "CONFIRM"

    def cleanup(self):
        """
        Add the index of the potentially deleted player to the persist dict
        so that we can access it as needed from the Confirm substate.
        """
        self.done = False
        self.persist["del_index"] = self.index
        return self.persist


class Confirm(SelectState):
    """
    Select substate that updates when the user is asked to confirm the
    deletion of a character.
    """
    def __init__(self):
       self.box_image = prepare.GFX["misc"]["delete"]
       centerx = prepare.SCREEN_RECT.centerx
       top = MAIN_TOPLEFT[1]+130
       self.rect = self.box_image.get_rect(centerx=centerx, top=top)
       SelectState.__init__(self)
       self.option_length = 2
       self.options = self.make_options(SMALL_FONT, ["Confirm", "Cancel"],
                                        self.rect.y+130, 35)
       self.player = None

    def startup(self, now, persistant):
        """
        Make options default to Cancel to be polite.
        Set the currently selected player's hit_state so they damage strobe.
        """
        state_machine._State.startup(self, now, persistant)
        del_index = self.persist["del_index"]
        self.player = self.persist["players"][del_index]
        self.player.hit_state = True
        self.index = 1

    def draw(self, surface):
        """
        Draw the background, players, delete window and options.
        """
        surface.blit(self.persist["options_bg"], (0,0))
        for i,player_sprite in enumerate(self.persist["players"]):
            redraw = i == self.persist["del_index"]
            self.draw_player(surface, player_sprite, i, redraw)
        surface.blit(self.box_image, self.rect)
        for i in (0,1):
            which = "selected" if i==self.index else "unselected"
            msg, rect = self.options[which][i]
            surface.blit(msg, rect)

    def save_change(self):
        """
        Overwrite the save data of the player with
        the string EMPTY.
        """
        with open(prepare.SAVE_PATH) as my_file:
            data = yaml.load(my_file)
        del_index = self.persist["del_index"]
        data[del_index] = "EMPTY"
        with open(prepare.SAVE_PATH, 'w') as my_file:
            yaml.dump(data, my_file)

    def pressed_enter(self):
        """
        Return to menu on 'Cancel'; set player to 'dead' on 'Confirm'.
        """
        if not self.index:
            self.player.action_state = "dead"
        else:
            self.pressed_exit()

    def update(self, *args):
        """
        If a player deletion has been confirmed and death animation completed,
        return to menu.
        """
        if self.player.death_anim.done:
            self.save_change()
            self.pressed_exit()

    def get_event(self, event):
        """Don't process events if a player deletion has been confirmed."""
        if self.player.action_state != "dead":
            SelectState.get_event(self, event)

    def pressed_exit(self):
        """Return to options menu."""
        self.done = True
        self.next = "OPTIONS"


class MenuCabbage(enemy_sprites.Cabbage):
    """A class for the cabbages that animate on the selector menu."""
    def __init__(self, min_x, max_x, pos, speed):
        """
        Pass minimum and maximum x value to walk back and forth between.
        The pos argument is the start position and speed is the walk speed in
        pixels per second.
        """
        enemy_sprites.Cabbage.__init__(self, pos, speed)
        self.min = min_x
        self.max = max_x
        self.anim = self.get_anim()
        self.image = None

    def update(self, now, dt):
        """
        Scale up the current image of the animation and reverse direction
        if a minimum or maximum point is reached.
        """
        raw = self.anim.get_next_frame(now)
        self.image = pg.transform.scale(raw, (150,150))
        self.exact_position[0] += self.speed*dt
        self.rect.topleft = self.exact_position
        if not (self.min <= self.rect.x <= self.max):
            self.speed *= -1
            self.rect.x = min(max(self.rect.x, self.min), self.max)
            self.exact_position = list(self.rect.topleft)


def render_font(font, msg, color, center):
    """Return the rendered font surface and its rect centered on center."""
    msg = font.render(msg, 0, color)
    rect = msg.get_rect(center=center)
    return msg, rect


def make_text_list(font, strings, color, start_y, y_space):
    """
    Takes a list of strings and returns a list of
    (rendered_surface, rect) tuples. The rects are centered on the screen
    and their y coordinates begin at starty, with y_space pixels between
    each line.
    """
    rendered_text = []
    for i,string in enumerate(strings):
        msg_center = (prepare.SCREEN_RECT.centerx, start_y+i*y_space)
        msg_data = render_font(font, string, color, msg_center)
        rendered_text.append(msg_data)
    return rendered_text
