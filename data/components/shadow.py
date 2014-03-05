"""
Contains the class for adding basic shadows to sprites.
"""

import pygame as pg


class Shadow(object):
    """A simple class for adding shadows to sprites."""
    def __init__(self, size, color=(0,0,50,150), offset=(0,0)):
        self.image = pg.Surface(size).convert_alpha()
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect()
        pg.draw.ellipse(self.image, color, self.rect.inflate(-1,-1))
        self.offset = offset

    def draw(self, center, surface):
        """
        Draws the shadow to the surface.  Center is the location that the
        shadow will be cenetered on, and should be an attribute of the shadow's
        corresponding sprite (usually midbottom).  The self.offset attribute
        allows a shadow to blit offset from the chosen center point; most
        useful for flying monsters.
        """
        self.rect.center = (center[0]+self.offset[0], center[1]+self.offset[1])
        surface.blit(self.image, self.rect)