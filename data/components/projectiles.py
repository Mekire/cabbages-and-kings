import random
import pygame as pg

from .. import prepare, tools


SHOOT_SHEET = prepare.GFX["objects"]["projectiles"]


ROTATE_DICT = {"right" : 0,
               "back" : 90,
               "left" : 180,
               "front" : 270}

LOCK_DICT = {"right" : ("midright", "midleft"),
             "left" : ("midleft", "midright"),
             "back" : ("midtop", "midbottom"),
             "front" : ("midbottom", "midtop")}


class Web(tools._BaseSprite):
    def __init__(self, owner, *groups):
        self.owner = owner
        direction = owner.previous_direction
        self.base = SHOOT_SHEET.subsurface(pg.Rect(51,0,21,50))
        if direction in ("front","back"):
            self.axis = 0
            size = (50, 21)
        elif direction in ("left","right"):
            self.axis = 1
            size = (21,50)
        self.vec = prepare.DIRECT_DICT[direction]
        self.image = pg.transform.rotate(self.base, ROTATE_DICT[direction])
        self.mask = pg.mask.from_surface(self.image)
        get_from, set_to = LOCK_DICT[direction]
        kwarg = {set_to : getattr(owner.rect, get_from)}
        rect = self.image.get_rect(**kwarg)
        tools._BaseSprite.__init__(self, rect.topleft, size, *groups)
        self.range = 150
        self.distance = 0
        self.speed = 3
        self.attack = 5
        self.go_back = False
        self.done = False

    def update(self, now, player, group_dicts):
        self.old_position = self.exact_position[:]
        self.exact_position[self.axis] = self.owner.exact_position[self.axis]
        move = self.speed*self.vec[not self.axis]
        self.exact_position[not self.axis] += move
        self.distance += abs(move)
        if not self.go_back:
            collide = pg.sprite.spritecollide(self, group_dicts["borders"], 0)
            if self.distance >= self.range or collide:
                self.go_back = True
                self.speed *= -1
        if self.go_back and pg.sprite.collide_rect(self, self.owner):
            self.kill()
            self.done = True
        self.rect.topleft = self.exact_position

    def collide_with_player(self, player):
        """Call the player's got_hit function doing damage, knocking, etc."""
        player.got_hit(self)
        if not self.go_back:
            self.go_back = True
            self.speed *= -1


class WebLine(pg.sprite.Sprite):
    null_surface = pg.Surface((1000,700)).convert()
    def __init__(self, owner, web):
        pg.sprite.Sprite.__init__(self)
        self.owner = owner
        self.web = web
        self.point_anchors = LOCK_DICT[owner.previous_direction]
        self.rect = pg.Rect(0,0,0,0)
        self.image = pg.Surface((0,0)).convert()

    def update(self, now, player, group_dicts):
        start = getattr(self.owner.rect, self.point_anchors[0])
        end = getattr(self.web.rect, self.point_anchors[1])
        self.rect = pg.draw.line(self.null_surface, (0,0,0), start, end, 2)
        self.image = pg.Surface(self.rect.size).convert()
        self.image.fill(pg.Color("white"))
        if self.web.done:
            self.kill()
