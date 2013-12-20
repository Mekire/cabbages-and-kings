"""
This is the launcher for the map editor. Dialogues from wxPython are used for
saving, and loading. YAML is also used (included).
This limits this version to python 2.7 for the time being.
"""

import sys
import pygame as pg

from data.map_main import main


if __name__ == '__main__':
    main()
    pg.quit()
    sys.exit()
