import pygame as pg

from .. import prepare, tools
from ..components import enemy_sprites


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)

OPTIONS = ["SELECT/REGISTER", "DELETE", "CONTROLS"]
OPTION_Y = 541
OPTION_SPACE = 59

BACKGROUND_COLOR = (63, 54, 50)
HIGHLIGHT_COLOR = (108, 148, 136)
HIGHLIGHT_SPACE = 125
MAIN_TOPLEFT = (100, 40)

NAME_START = (350, 115)
NAME_SPACE = 125


class Select(tools._State):
    """This State is updated while our game shows the player select screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.next = "GAME"
        self.timeout = 15
        self.cabbages = pg.sprite.Group(MenuCabbage(25, 225, (25,525), 100),
                                      MenuCabbage(825, 1025, (1025,525), -100))
        self.image = None
        self.highlight_rect = pg.Rect(129, 83, 942, 124)
        self.options = self.make_options()
        self.option_index = 0
        self.players = ["EMPTY", "EMPTY", "EMPTY"]
        self.player_index = 0
        self.names = self.make_player_names()
        self.state = "OPTIONS"

    def make_player_names(self):
        names = []
        for i,player in enumerate(self.players):
            try:
                args = FONT, player.name, pg.Color("white"), (0,0)
            except AttributeError:
                args = FONT, player, pg.Color("white"), (0,0)
            msg, rect = self.render_font(*args)
            rect.topleft = NAME_START[0], NAME_START[1]+NAME_SPACE*i
            names.append((msg, rect))
        return names

    def make_options(self):
        options = {}
        args = [FONT, OPTIONS, pg.Color("white"), OPTION_Y, OPTION_SPACE]
        options["unselected"] = self.make_text_list(*args)
        args = [FONT, OPTIONS, pg.Color("yellow"), OPTION_Y, OPTION_SPACE]
        options["selected"] = self.make_text_list(*args)
        return options

    def render_font(self, font, msg, color, center):
        """Return the rendered font surface and its rect centered on center."""
        msg = font.render(msg, 1, color)
        rect = msg.get_rect(center=center)
        return msg, rect

    def make_text_list(self, font, strings, color, start_y, y_space):
        """
        Takes a list of strings and returns a list of
        (rendered_surface, rect) tuples. The rects are centered on the screen
        and their y coordinates begin at starty, with y_space pixels between
        each line.
        """
        rendered_text = []
        for i,string in enumerate(strings):
            msg_center = (prepare.SCREEN_RECT.centerx, start_y+i*y_space)
            msg_data = self.render_font(font, string, color, msg_center)
            rendered_text.append(msg_data)
        return rendered_text

    def update(self, surface, keys, now, dt):
        """Updates the select screen."""
        self.cabbages.update(now, dt)
        if now-self.start_time > 1000.0*self.timeout:
            self.next = "TITLE"
            self.done = True
        self.render(surface)

    def render(self, surface):
        surface.fill(BACKGROUND_COLOR)
        if self.state in ("SELECT", "DELETE"):
            move = (0, HIGHLIGHT_SPACE*self.player_index)
            highlight = self.highlight_rect.move(*move)
            surface.fill(HIGHLIGHT_COLOR, highlight)
        surface.blit(prepare.GFX["misc"]["charcreate"], MAIN_TOPLEFT)
        for name_info in self.names:
            surface.blit(*name_info)
        self.cabbages.draw(surface)
        for i,val in enumerate(OPTIONS):
            which = "selected" if i==self.option_index else "unselected"
            msg, rect = self.options[which][i]
            surface.blit(msg, rect)

    def get_event(self, event):
        """
        Get events from Control.
        """
        if event.type == pg.KEYDOWN:
            self.start_time = pg.time.get_ticks()
            if event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.press_enter()
            elif event.key == pg.K_DOWN:
                if self.state == "OPTIONS":
                    self.option_index = (self.option_index+1)%len(OPTIONS)
                else:
                    self.player_index = (self.player_index+1)%len(self.players)
            elif event.key == pg.K_UP:
                if self.state == "OPTIONS":
                    self.option_index = (self.option_index-1)%len(OPTIONS)
                else:
                    self.player_index = (self.player_index-1)%len(self.players)
            elif event.key == pg.K_x:
                self.state = "OPTIONS"

    def press_enter(self):
        if self.state == "OPTIONS":
            if self.option_index == 0:
                self.state = "SELECT"
            elif self.option_index == 1:
                self.state = "DELETE"
            else:
                self.done = True
                self.next = "VIEW_CONTROLS"
        else:  ###
            self.done = True
            self.next = "GAME"


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
