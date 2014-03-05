"""
Contains the class for adding basic shadows to sprites.
"""

import pygame as pg


class Shadow(object):
    """A simple class for adding shadows to sprites."""
    def __init__(self, size, lock_rect, **kwargs):
        self.process_kwargs(kwargs)
        self.lock_rect = lock_rect
        self.image = pg.Surface(size).convert_alpha()
        self.image.fill((0,0,0,0))
        self.rect = self.image.get_rect()
        pg.draw.ellipse(self.image, self.color, self.rect.inflate(-1,-1))

    def process_kwargs(self, kwargs):
        """
        Custom values for the attribute of lock_rect to lock to,
        the color, and the offset from the center can be passed via keyword.
        """
        defaults = {"lock_attr"  : "midbottom",
                    "color" : (0, 0, 50, 150),
                    "offset" : (0, 0)}
        if any(kwarg not in defaults for kwarg in kwargs):
            raise AttributeError("Invalid keyword {}".format(kwarg))
        defaults.update(kwargs)
        self.__dict__.update(defaults)

    def draw(self, surface):
        """
        Draws the shadow to the surface.  Shadow will be centered on the
        self.lock_attr attribute of the self.lock_rect (usually midbottom).
        The self.offset attribute allows a shadow to blit offset from the
        chosen center point; most useful for flying monsters.
        """
        self.rect.center = getattr(self.lock_rect, self.lock_attr)
        self.rect.move_ip(self.offset)
        surface.blit(self.image, self.rect)
