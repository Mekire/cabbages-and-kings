import math
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

class _Particle(tools._BaseSprite):
    def on_map_change(self):
        self.done = True
        self.kill()


class Web(_Particle):
    def __init__(self, owner, group_dict):#*groups):
        self.owner = owner
        self.base = SHOOT_SHEET.subsurface(pg.Rect(51,0,21,50))
        self.direction = random.choice(prepare.DIRECTIONS)
        if self.direction in ("front","back"):
            self.axis = 0
            size = (50, 21)
        elif self.direction in ("left","right"):
            self.axis = 1
            size = (21,50)
        self.vec = prepare.DIRECT_DICT[self.direction]
        self.image = pg.transform.rotate(self.base,ROTATE_DICT[self.direction])
        self.mask = pg.mask.from_surface(self.image)
        get_from, set_to = LOCK_DICT[self.direction]
        kwarg = {set_to : getattr(owner.rect, get_from)}
        rect = self.image.get_rect(**kwarg)
        #Add to all needed groups and create a WebLine.
        _Particle.__init__(self, rect.topleft, size)
        self.add(group_dict["projectiles"], group_dict["moving"])
        self.webline = _WebLine(self.owner, self)
        z_level = prepare.Z_ORDER["Projectiles"]
        group_dict["all"].add(self, layer=z_level)
        group_dict["all"].add(self.webline, layer=z_level)

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

    def on_map_change(self):
        _Particle.on_map_change(self)
        self.webline.kill()


class _WebLine(tools._BaseSprite):
    null_surface = pg.Surface((1000,700)).convert()
    def __init__(self, owner, web):
        tools._BaseSprite.__init__(self, (0,0), (0,0))
        self.owner = owner
        self.web = web
        self.point_anchors = LOCK_DICT[web.direction]
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


class FireBall(_Particle):
    def __init__(self, owner, *groups):
        size = prepare.CELL_SIZE
        _Particle.__init__(self, owner.rect.topleft, size, *groups)
        self.owner = owner
        self.vec = None
        self.speed = 5
        self.attack = 5
        self.frames = tools.strip_from_sheet(SHOOT_SHEET, (100,250), size, 2)
        self.anim = tools.Anim(self.frames, 12)
        self.image = self.anim.get_next_frame(pg.time.get_ticks())
        self.mask = pg.mask.from_surface(self.image)

    def get_vector(self, player):
        x = player.rect.centerx-self.owner.rect.centerx
        y = player.rect.centery-self.owner.rect.centery
        mag = math.hypot(x,y)
        vec_x = self.speed*(x/mag)
        vec_y = self.speed*(y/mag)
        return (vec_x, vec_y)

    def update(self, now, player, group_dict):
        self.old_position = self.exact_position[:]
        self.image = self.anim.get_next_frame(now)
        if not self.vec:
            self.vec = self.get_vector(player)
        self.exact_position[0] += self.vec[0]
        self.exact_position[1] += self.vec[1]
        self.rect.topleft = self.exact_position
        if not self.rect.colliderect(prepare.SCREEN_RECT):
            self.kill()

    def collide_with_player(self, player):
        """Call the player's got_hit function doing damage, knocking, etc."""
        player.got_hit(self)
        self.kill()
