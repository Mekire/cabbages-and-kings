"""
Contains a class for adding basic shadows to sprites.
"""

import pygame as pg


class Shadow(pg.sprite.Sprite):
    """A simple class for adding shadows to sprites."""
    def __init__(self, size, lock_rect, **kwargs):
        """
        Arguments are the size (width, height), and the rect that the shadow
        will lock to (the rect of the sprite with the shadow).
        See process_kwargs for detail on customizing via keyword.
        """
        pg.sprite.Sprite.__init__(self)
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
        for kwarg in kwargs:
            if kwarg  in defaults:
                defaults[kwarg] = kwargs[kwarg]
            else:
                raise AttributeError("Invalid keyword {}".format(kwarg))
        self.__dict__.update(defaults)

    def update(self, *args):
        """
        Shadow will be centered on the self.lock_attr attribute of the
        self.lock_rect (usually midbottom). The self.offset attribute allows a
        shadow to blit offset from the chosen center point; most useful for
        flying monsters.
        """
        self.rect.center = getattr(self.lock_rect, self.lock_attr)
        self.rect.move_ip(self.offset)
