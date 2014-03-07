"""
This project represents an effort to completely recode one of my earliest
projects. The original project ran perfectly fine, but as it grew it became
more and more unmaintainable. This eventually led to it being abandoned.

-Mek, November 22, 2013.
"""

import sys
import pygame as pg

from data.main import main


if __name__ == '__main__':
    main()
    pg.quit()
    sys.exit()
