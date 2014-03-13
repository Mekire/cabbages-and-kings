import pygame as pg

from .. import prepare, tools
from ..components import enemy_sprites


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)

OPTIONS = ["SELECT/REGISTER", "DELETE", "CONTROLS"]


class Select(tools._State):
    """This State is updated while our game shows the player select screen."""
    def __init__(self):
        tools._State.__init__(self)
        self.next = "GAME"
        self.timeout = 15
        self.base = pg.Surface((prepare.SCREEN_SIZE)).convert()
        self.base.blit(prepare.GFX["misc"]["charcreate"], (0,0))
        self.cabbages = pg.sprite.Group(MenuCabbage(25, 225, (25,525), 100),
                                      MenuCabbage(825, 1025, (1025,525), -100))
        self.image = None
        self.options = self.make_options()
        self.selected = 0

    def make_options(self):
        options = {}
        args = [FONT, OPTIONS, pg.Color("white"), 541, 59]
        options["unselected"] = self.make_text_list(*args)
        args = [FONT, OPTIONS, pg.Color("yellow"), 541, 59]
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
        surface.blit(self.base, (0,0))
        self.cabbages.draw(surface)
        for i,val in enumerate(OPTIONS):
            which = "selected" if i==self.selected else "unselected"
            msg, rect = self.options[which][i]
            surface.blit(msg, rect)

    def get_event(self, event):
        """
        Get events from Control. Currently changes to next state on any key
        press.
        """
        if event.type == pg.KEYDOWN:
            self.start_time = pg.time.get_ticks()
            if event.key == pg.K_RETURN:
                self.done = True
                self.next = "GAME"
            elif event.key == pg.K_DOWN:
                self.selected = (self.selected+1)%len(OPTIONS)
            elif event.key == pg.K_UP:
                self.selected = (self.selected-1)%len(OPTIONS)


class MenuCabbage(enemy_sprites.Cabbage):
    def __init__(self, min_x, max_x, pos, speed):
        enemy_sprites.Cabbage.__init__(self, pos, speed)
        self.min = min_x
        self.max = max_x
        self.anim = self.get_anim()
        self.image = None

    def update(self, now, dt):
        raw = self.anim.get_next_frame(now)
        self.image = pg.transform.scale(raw, (150,150))
        self.exact_position[0] += self.speed*dt
        self.rect.topleft = self.exact_position
        if not (self.min <= self.rect.x <= self.max):
            self.speed *= -1
            self.rect.x = min(max(self.rect.x, self.min), self.max)
            self.exact_position = list(self.rect.topleft)
