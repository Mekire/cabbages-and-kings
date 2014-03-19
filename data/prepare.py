"""
This module initializes the display and creates dictionaries of resources.
Also contained are various constants used throughout the program.
"""

import os
import pygame as pg

from . import tools


SCREEN_SIZE = (1200, 700)
ORIGINAL_CAPTION = "The Cabbages"


#Initialization
pg.init()
_Y_OFFSET = (pg.display.Info().current_w-SCREEN_SIZE[0])//2
os.environ['SDL_VIDEO_WINDOW_POS'] = '{},{}'.format(_Y_OFFSET, 25)
pg.display.set_caption(ORIGINAL_CAPTION)
pg.display.set_mode(SCREEN_SIZE)


#General constants
COLOR_KEY = (255, 0, 255)
BACKGROUND_COLOR = (30, 40, 50)
SCREEN_RECT = pg.Rect((0,0), SCREEN_SIZE)
PLAY_RECT = pg.Rect(0, 0, 1000, 700)
CELL_SIZE = (50, 50)
MAX_HEALTH = 28
MAX_MONEY = 9999

DIRECTIONS = ["front", "back", "left", "right"]

DIRECT_DICT = {"front" : ( 0, 1),
               "back"  : ( 0,-1),
               "left"  : (-1, 0),
               "right" : ( 1, 0)}

OPPOSITE_DICT = {"front" : "back",
                 "back"  : "front",
                 "left"  : "right",
                 "right" : "left"}

DEFAULT_CONTROLS = {pg.K_DOWN  : "front",
                    pg.K_UP    : "back",
                    pg.K_LEFT  : "left",
                    pg.K_RIGHT : "right"}

DEFAULT_GEAR = {"head" : ["none"],
                "body" : ["cloth"],
                "shield" : ["none"],
                "armleg" : ["normal"],
                "weapon" : ["pitch"]}

DEFAULT_PLAYER = {"name" : None,
                  "money" : 0,
                  "keys" : 0,
                  "gear" : DEFAULT_GEAR,
                  "equipped" : {k:v[0] for k,v in DEFAULT_GEAR.items()}}

#Resource loading (Fonts and music just contain path names).
SAVE_PATH = os.path.join("resources", "save_data", "save_data.dat")
FONTS = tools.load_all_fonts(os.path.join("resources", "fonts"))
MUSIC = tools.load_all_music(os.path.join("resources", "music"))
SFX   = tools.load_all_sfx(os.path.join("resources", "sound"))


def graphics_from_directories(directories):
    """
    Calls the tools.load_all_graphics() function for all directories passed.
    """
    base_path = os.path.join("resources", "graphics")
    GFX = {}
    for directory in directories:
        path = os.path.join(base_path, directory)
        GFX[directory] = tools.load_all_gfx(path)
    return GFX


_SUB_DIRECTORIES = ["enemies", "equips", "mapsheets", "misc", "objects"]
GFX = graphics_from_directories(_SUB_DIRECTORIES)
