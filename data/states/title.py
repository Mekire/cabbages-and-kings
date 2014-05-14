"""
State for the Title scene.
"""

import random
import pygame as pg

from .. import prepare, state_machine, tools
from ..components import player, equips


SCROLL_SPEED = 2
DELAY_UNTIL_SCROLL = 10000 #Miliseconds.
SKY_COLOR = (66, 120, 150)
SKY_RECT = pg.Rect(0, 0, 1200, 514)
STAR_COLORS = [(74,156,173), (40, 40, 50), (250, 230, 250)]
NIGHT_SKY_COLOR = (0, 0, 30)


class Title(state_machine._State):
    """This State is updated while our game shows the title screen."""
    def __init__(self):
        state_machine._State.__init__(self)
        self.ground = prepare.GFX["misc"]["title_ground"]
        self.elements = self.make_elements()
        self.star_field = StarField()
        self.timer = None
        self.scrolling = False

    def startup(self, now, persistant):
        self.persist = persistant
        self.start_time = now
        self.timer = tools.Timer(DELAY_UNTIL_SCROLL, 1)
        self.timer.check_tick(now)
        self.scrolling = False
        self.elements = self.make_elements()
        self.star_field.reset()

    def make_elements(self):
        group = pg.sprite.LayeredUpdates()
        group.add(TitlePlayer(), AnyKey(), TitleImage(), layer=1)
        return group

    def update(self, keys, now):
        """Updates the title screen."""
        self.now = now
        self.elements.update(now, self.scrolling)
        if self.scrolling:
            self.star_field.update(now)
        elif self.timer.check_tick(now):
            self.scrolling = True

    def draw(self, surface, interpolate):
        surface.fill(SKY_COLOR, SKY_RECT)
        if self.scrolling:
            self.star_field.draw(surface)
        surface.blit(self.ground, SKY_RECT.bottomleft)
        self.elements.draw(surface)

    def get_event(self, event):
        """
        Get events from Control.  Currently changes to next state on any key
        press.
        """
        if event.type == pg.KEYDOWN:
            self.next = "SELECT"
            self.done = True


class TitleImage(tools._BaseSprite):
    def __init__(self, *groups):
        self.image = prepare.GFX["misc"]["titlewords"]
        tools._BaseSprite.__init__(self, (0,0), self.image.get_size(), *groups)
        self.needed_groups = groups

    def update(self, now, scrolling):
        if scrolling:
            self.exact_position[1] -= SCROLL_SPEED
        if not self.rect.colliderect(prepare.SCREEN_RECT):
            self.kill()
        self.rect.topleft = self.exact_position


class AnyKey(pg.sprite.Sprite):
    def __init__(self, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.raw_image = render_font("Fixedsys500c", 30,
                                 "[Press Any Key]", (255,255,0))
        self.null_image = pg.Surface((1,1)).convert_alpha()
        self.null_image.fill((0,0,0,0))
        self.image = self.raw_image
        center = (prepare.SCREEN_RECT.centerx, 650)
        self.rect = self.image.get_rect(center=center)
        self.blink = False
        self.timer = tools.Timer(200)

    def update(self, now, *args):
        if self.timer.check_tick(now):
            self.blink = not self.blink
        self.image = self.raw_image if self.blink else self.null_image


class TitlePlayer(player.Player):
    def __init__(self, *groups):
        player.Player.__init__(self, prepare.DEFAULT_PLAYER, *groups)
        self.inventory = equips.make_all_equips()
        self.speed = 3.5
        self.dancing = False
        self.done_dancing = False
        self.dance_timer = tools.Timer(1000, 1)
        self.prepare()

    def prepare(self):
        self.reset_position((-300,300))
        self.set_equips(prepare.DEFAULT_PLAYER["equipped"])
        self.direction = "right"
        self.direction_stack = [self.direction]

    def switch_direction(self):
        if not (-350 < self.rect.x < 1250):
            self.direction_stack[0] = prepare.OPPOSITE_DICT[self.direction]
            self.equipped = self.set_equips_random()
            self.all_animations = self.make_all_animations()
            self.done_dancing = False

    def update(self, now, *args):
        player.Player.update(self, now)
        self.switch_direction()
        self.dance(now)
        self.rect.y = 300
        if self.image.get_size() != (300,300):
            self.image = pg.transform.scale(self.image, (300,300))

    def dance(self, now):
        if not (self.done_dancing or self.dancing) and 100<self.rect.x<110:
            self.old_direction = self.direction
            self.dancing = True
            self.direction_stack[0] = "front"
            self.dance_timer.check_tick(now)
        if self.dancing and self.dance_timer.check_tick(now):
            self.dancing = False
            self.done_dancing = True
            self.dance_timer = tools.Timer(1000, 1)
            self.direction_stack[0] = self.old_direction


class Star(pg.sprite.Sprite):
    frames = []
    def __init__(self, pos, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        if not self.frames:
            sheet = prepare.GFX["objects"]["projectiles"]
            self.frames.extend(tools.strip_from_sheet(sheet,(300,0),(30,30),3))
            self.frames += [self.frames[1]]
        self.frame = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect(center=pos)
        self.blink_timer = tools.Timer(100)
        self.blink_timer.check_tick(pg.time.get_ticks())
        self.delay = random.randrange(200, 3000)
        self.delay_timer = 0.0
        self.animate = random.random() < 0.1

    def blink(self, now):
        if self.animate and now-self.delay_timer > self.delay:
            if self.blink_timer.check_tick(now):
                self.frame += 1
            if self.frame == len(self.frames):
                self.frame = 0
                self.delay_timer = now

    def update(self, now):
        self.blink(now)
        self.image = self.frames[self.frame]


class StarField(object):
    def __init__(self):
        self.alpha = 0
        self.alpha_speed = 2
        self.raw_stars = pg.Surface(SKY_RECT.size).convert()
        self.raw_stars.fill(NIGHT_SKY_COLOR)
        for i in range(1000):
            pos = [random.randrange(SKY_RECT.size[i]) for i in (0,1)]
            self.raw_stars.set_at(pos, random.choice(STAR_COLORS))
        self.stars = self.make_stars()

    def reset(self):
        self.alpha = 0

    def make_stars(self):
        min_distance_from_horizon = 10
        group = pg.sprite.Group()
        for i in range(50):
            pos = (random.randrange(SKY_RECT.w),
                   random.randrange(SKY_RECT.h-min_distance_from_horizon))
            Star(pos, group)
        return group

    def update(self, now):
        self.stars.update(now)
        self.alpha = min(self.alpha+self.alpha_speed, 255)

    def draw(self, surface):
        image = self.raw_stars.copy()
        self.stars.draw(image)
        image.set_alpha(self.alpha)
        surface.blit(image, SKY_RECT)


class ScrollObjects(object):
    def __init__(self):
        self.enemies = [("cabbage", "spider"),
                        ("frog", "snail"),
                        ("mushroom", "crab"),
                        ("skeleton", "zombie"),
                        ("snake", "scorpion"),
                        ("turtle", "tank"),
                        ("blue_oni", "red_oni"),
                        ("daruma", "lantern"),
                        ("evil_elf", "knight")]
        self.items = [("heart", "diamond"),
                      ("key", "potion")]


def render_font(font, size, msg, color=(255,255,255)):
        """
        Takes the name of a loaded font, the size, and the color and returns
        a rendered surface of the msg given.
        """
        selected_font = pg.font.Font(prepare.FONTS[font], size)
        return selected_font.render(msg, 1, color)
