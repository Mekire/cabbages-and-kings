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
    """
    This State is updated while our game shows the player select screen.
    This state is made up of four substates to organize updating.
    """
    def __init__(self):
        tools._State.__init__(self)
        self.next = "GAME"
        self.timeout = 15
        self.cabbages = pg.sprite.Group(MenuCabbage(25, 225, (25,525), 100),
                                      MenuCabbage(825, 1025, (1025,525), -100))

    def startup(self, now, persistant):
        tools._State.startup(self, now, persistant)
        self.state_name = "OPTIONS"
        self.state_dict = {"OPTIONS" : Options(),
                           "SELECT/REGISTER" : SelectRegister(),
                           "DELETE" : Delete()}
        self.state = self.state_dict[self.state_name]

    def cleanup(self):
        """
        Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        """
        self.done = False
        self.persist["save_slot"] = self.state_dict["SELECT/REGISTER"].index
        return self.persist

    def update(self, surface, keys, now, dt):
        """Updates the select screen."""
        self.cabbages.update(now, dt)
        self.state.update()
        if now-self.start_time > 1000.0*self.timeout:
            self.next = "TITLE"
            self.done = True
        elif self.state.quit:
            self.next = self.state.next
            self.done = True
        elif self.state.done:
            self.flip_state()
        self.render(surface)

    def flip_state(self):
        """
        When a State changes to done necessary startup and cleanup functions
        are called and the current State is changed.
        """
        previous, self.state_name = self.state_name, self.state.next
        persist = self.state.cleanup()
        self.state = self.state_dict[self.state_name]
        self.state.startup(self.now, persist)
        self.state.previous = previous

    def render(self, surface):
        surface.fill(BACKGROUND_COLOR)
        self.state.draw(surface)
        self.cabbages.draw(surface)

    def get_event(self, event):
        """
        Get events from Control.
        """
        if event.type == pg.KEYDOWN:
            self.start_time = pg.time.get_ticks()
        self.state.get_event(event)


class SelectState(tools._State):
    def __init__(self):
       tools._State.__init__(self)
       self.index = 0
       self.options = self.make_options()

    def get_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_DOWN:
                self.index = (self.index+1)%self.option_length
            elif event.key == pg.K_UP:
                self.index = (self.index-1)%self.option_length
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.pressed_enter()
            elif event.key == pg.K_x:
                self.pressed_exit()

    def update(self, *args):
        pass

    def make_options(self):
        pass

    def pressed_enter(self):
        pass

    def pressed_exit(self):
        pass


class Options(SelectState):
    def __init__(self):
       SelectState.__init__(self)
       self.option_length = 3
       self.players = ["EMPTY", "EMPTY", "EMPTY"]
       self.names = self.make_player_names()
       self.image = pg.Surface(prepare.SCREEN_SIZE, pg.SRCALPHA)

    def make_options(self):
        options = {}
        args = [FONT, OPTIONS, pg.Color("white"), OPTION_Y, OPTION_SPACE]
        options["unselected"] = make_text_list(*args)
        args = [FONT, OPTIONS, pg.Color("yellow"), OPTION_Y, OPTION_SPACE]
        options["selected"] = make_text_list(*args)
        return options

    def make_player_names(self):
        names = []
        for i,player in enumerate(self.players):
            try:
                args = FONT, player.name, pg.Color("white"), (0,0)
            except AttributeError:
                args = FONT, player, pg.Color("white"), (0,0)
            msg, rect = render_font(*args)
            rect.topleft = NAME_START[0], NAME_START[1]+NAME_SPACE*i
            names.append((msg, rect))
        return names

    def cleanup(self):
        """
        Add variables that should persist to the self.persist dictionary.
        Then reset State.done to False.
        """
        self.done = False
        self.persist["options_bg"] = self.image
        self.persist["players"] = self.players  ####
        return self.persist

    def pressed_enter(self):
        self.done = True
        self.next = OPTIONS[self.index]
        if self.next == "CONTROLS":
            self.quit = True

    def draw(self, surface):
        self.image.blit(prepare.GFX["misc"]["charcreate"], MAIN_TOPLEFT)
        for name_info in self.names:
            self.image.blit(*name_info)
        for i,val in enumerate(OPTIONS):
            which = "selected" if i==self.index else "unselected"
            msg, rect = self.options[which][i]
            self.image.blit(msg, rect)
        surface.blit(self.image, (0,0))


class CharHighlighter(SelectState):
    def __init__(self):
       SelectState.__init__(self)
       self.option_length = 3
       self.highlight_rect = pg.Rect(129, 83, 942, 124)

    def draw(self, surface):
        move = (0, HIGHLIGHT_SPACE*self.index)
        highlight = self.highlight_rect.move(*move)
        surface.fill(HIGHLIGHT_COLOR, highlight)
        surface.blit(self.persist["options_bg"], (0,0))

    def pressed_exit(self):
        self.done = True
        self.next = "OPTIONS"


class SelectRegister(CharHighlighter):
    def __init__(self):
        CharHighlighter.__init__(self)

    def pressed_enter(self):
        if self.persist["players"][self.index] != "EMPTY":
            self.quit = True
            self.next = "GAME"
        else:
            self.quit = True
            self.next = "REGISTER"


class Delete(CharHighlighter):
    def __init__(self):
        CharHighlighter.__init__(self)

    def pressed_enter(self):
        pass


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
    msg = font.render(msg, 1, color)
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
