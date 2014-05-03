"""
This module initializes the display and creates dictionaries of resources.
"""

import os
import pygame as pg

from . import tools


SCREEN_SIZE = (1120, 700)
ORIGINAL_CAPTION = "The Cabbages: Map Editor"


#Initialization
pg.init()
_Y_OFFSET = (pg.display.Info().current_w-SCREEN_SIZE[0])//2
os.environ['SDL_VIDEO_WINDOW_POS'] = '{},{}'.format(_Y_OFFSET, 25)
pg.display.set_caption(ORIGINAL_CAPTION)
SCREEN = pg.display.set_mode(SCREEN_SIZE)
SCREEN_RECT = SCREEN.get_rect()

#General constants
CELL_SIZE = (50, 50)
MAP_RECT = pg.Rect(120, 0, 1000, 700)

#Resource loading (Fonts and music just contain path names).
FONTS = tools.load_all_fonts(os.path.join("resources", "fonts"))


def graphics_from_directories(directories):
    base_path = os.path.join("resources", "graphics")
    GFX = {}
    for directory in directories:
        path = os.path.join(base_path, directory)
        GFX[directory] = tools.load_all_gfx(path)
    return GFX


_SUB_DIRECTORIES = ["enemies", "equips", "mapsheets", "misc", "objects"]
GFX = graphics_from_directories(_SUB_DIRECTORIES)

DROPPER = tools.cursor_from_image(GFX["misc"]["dropper"], 16, (0,15))
DEFAULT_CURSOR = pg.mouse.get_cursor()
