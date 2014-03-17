import os
import sys
import copy
import pygame as pg

from .. import prepare, tools


if sys.version_info[0] < 3:
    import yaml
else:
    import yaml3 as yaml


FONT = pg.font.Font(prepare.FONTS["Fixedsys500c"], 60)
BACKGROUND_COLOR = (63, 54, 50)

MAX_LETTERS = 8

CURSOR = pg.Rect(292, 141, 41, 45)
CURSOR_SPACE = 82

HIGHLIGHT = pg.Rect(80, 270, 80, 85)
HIGHLIGHT_SPACE = (80, 75)
HIGHLIGHT_COLOR = pg.Color("darkslateblue")

ALPHAGRID = ["ABCDEFGHIJKLM",
             "NOPQRSTUVWXYZ",
             "abcdefghijklm",
             "nopqrstuvwxyz",
             "0123456789-"]

END_CELL = [12, 4]
BACKSPACE_CELL = [11, 4]


class Register(tools._State):
    """
    This State is updated while our game shows the name registration screen.
    """
    def __init__(self):
        tools._State.__init__(self)
        self.next = "SELECT"
        self.timer = tools.Timer(333)
        self.blink = True
        self.letter_images = {}

    def startup(self, now, persistant):
        tools._State.startup(self, now, persistant)
        pg.key.set_repeat(200,100)
        self.index = [0,0]
        self.name = []

    def save_new(self):
        path = os.path.join("resources", "save_data", "save_data.dat")
        player_data = copy.deepcopy(prepare.DEFAULT_PLAYER)
        player_data["name"] = "".join(self.name)
        try:
            with open(path) as my_file:
                players = yaml.load(my_file)
        except IOError:
            players = ["EMPTY", "EMPTY", "EMPTY"]
        save_slot = self.persist["save_slot"]
        players[save_slot] = player_data
        with open(path, 'w') as my_file:
            yaml.dump(players, my_file)

    def update(self, surface, keys, now, dt):
        if self.timer.check_tick(now):
            self.blink = not self.blink
        self.render(surface)

    def get_event(self, event):
        if event.type == pg.KEYDOWN:
            if event.key in prepare.DEFAULT_CONTROLS:
                direction = prepare.DEFAULT_CONTROLS[event.key]
                vector = prepare.DIRECT_DICT[direction]
                self.index[0] = (self.index[0]+vector[0])%len(ALPHAGRID[0])
                self.index[1] = (self.index[1]+vector[1])%len(ALPHAGRID)
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                if self.index == END_CELL and self.name:
                    self.save_new()
                    self.done = True
                    self.next = "SELECT"
                elif self.index == BACKSPACE_CELL:
                    if self.name:
                        self.name.pop()
                elif len(self.name) < MAX_LETTERS:
                    i, j = self.index
                    letter = ALPHAGRID[j][i]
                    self.name.append(ALPHAGRID[j][i])
                    self.render_letter(letter)

    def render_letter(self, letter):
        if letter not in self.letter_images:
            rendered = FONT.render(letter, 1, pg.Color("yellow"))
            self.letter_images[letter] = rendered

    def render(self, surface):
        surface.fill(BACKGROUND_COLOR)
        move = [HIGHLIGHT_SPACE[i]*self.index[i] for i in (0,1)]
        surface.fill(HIGHLIGHT_COLOR, HIGHLIGHT.move(*move))
        surface.blit(prepare.GFX["misc"]["register"], (0,0))
        pg.draw.rect(surface, pg.Color("yellow"), HIGHLIGHT.move(*move), 5)
        if self.blink and len(self.name) < MAX_LETTERS:
            rect = CURSOR.move(CURSOR_SPACE*len(self.name), 0)
            surface.fill(pg.Color("white"), rect)
        for i,letter in enumerate(self.name):
            rect = CURSOR.move(CURSOR_SPACE*i, 0)
            surface.fill(BACKGROUND_COLOR, rect)
            surface.blit(self.letter_images[letter], rect)
