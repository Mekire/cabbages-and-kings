import random
import pygame as pg

from . import shadow
from .. import prepare, tools


ENEMY_SHEET = prepare.GFX["enemies"]["enemysheet"]

ENEMIES = {"cabbage" : [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0)],
           "snake" : [(0,5),(1,5),(2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5)],
           "zombie" : [(0,3),(1,3),(6,4),(7,4),(8,2),(9,2),(2,3),(3,3),(8,4),
                       (9,4),(8,6),(9,6),(4,3),(5,3),(6,3),(7,3),(8,3),(9,3)]}

KNOCK_SPEED = 750  #Pixels per second.


class BasicAI(object):
    """
    The most basic AI.  Makes a sprite choose a new completely random direction
    whenever they reach a new cell.  Gives enemies a very frenetic,
    unpredictable feel.
    """
    def __init__(self, sprite):
        self.sprite = sprite

    def __call__(self, obstacles):
        """Make AI classes callable."""
        return self.get_direction(obstacles)

    def get_direction(self, obstacles):
        """Return a new valid direction for the sprite."""
        new_dir = None
        while not new_dir:
            new_dir = random.choice(prepare.DIRECTIONS)
            move = (prepare.DIRECT_DICT[new_dir][0]*prepare.CELL_SIZE[0],
                    prepare.DIRECT_DICT[new_dir][1]*prepare.CELL_SIZE[1])
            self.sprite.rect.move_ip(*move)
            if self.check_collisions(obstacles):
                new_dir = None
            self.sprite.rect.move_ip(-move[0], -move[1])
        return new_dir

    def check_collisions(self, obstacles):
        """
        Check if the sprite attempts to leave the screen or move into a
        solid obstacle.
        """
        off_screen = not prepare.PLAY_RECT.contains(self.sprite.rect)
        return off_screen or pg.sprite.spritecollideany(self.sprite, obstacles)


class LinearAI(BasicAI):
    """
    Another very basic AI.  Makes a sprite choose a new completely random
    direction, but will not have select the completely opposite direction
    unless there are no other options available. Enemies still walk around
    completely randomly but appear much less chaotic than with the BasicAI.
    """
    def __init__(self, sprite):
        BasicAI.__init__(self, sprite)

    def get_direction(self, obstacles):
        """
        Try all other directions before attempting to go in the opposite
        direction.
        """
        opposite = prepare.OPPOSITE_DICT[self.sprite.direction]
        directions = prepare.DIRECTIONS[:]
        directions.remove(opposite)
        random.shuffle(directions)
        new_dir = None
        while directions and not new_dir:
            new_dir = directions.pop()
            move = (prepare.DIRECT_DICT[new_dir][0]*prepare.CELL_SIZE[0],
                    prepare.DIRECT_DICT[new_dir][1]*prepare.CELL_SIZE[1])
            self.sprite.rect.move_ip(*move)
            if self.check_collisions(obstacles):
                new_dir = None
            self.sprite.rect.move_ip(-move[0], -move[1])
        return new_dir if new_dir else opposite


class _Enemy(pg.sprite.Sprite):
    """
    The base class for all enemies.
    """
    def __init__(self, pos, speed, state, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.rect = pg.Rect(pos, prepare.CELL_SIZE)
        self.mask = pg.Mask(prepare.CELL_SIZE)
        self.mask.fill()
        self.exact_position = list(self.rect.topleft)
        self.steps = [0, 0]
        self.ai = BasicAI(self)
        self.speed = speed
        self.direction = random.choice(prepare.DIRECTIONS)
        self.anim_direction = self.direction
        self.anim_directions = prepare.DIRECTIONS[:]
        self.shadow = shadow.Shadow((40,20), self.rect)
        self.image = None
        self.state = state
        self.hit_state = False
        self.knock_dir = None

    def get_occupied_cell(self):
        """
        Return screen coordinates of the cell the sprite occupies with
        respect to the sprite's center point.
        """
        return tools.get_cell_coordinates(prepare.SCREEN_RECT,
                                          self.rect.center, prepare.CELL_SIZE)

    def collide_with_player(self, player):
        """Call the player's got_hit function doing damage, knocking, etc."""
        player.got_hit(self)

    def got_hit(self, player):
        if not self.hit_state:
            self.state = "hit"
            self.hit_state = tools.Timer(200, 1)
            self.knock_dir = player.direction
            print("knocked")

    def update(self, now, dt, obstacles):
        """
        Update the sprite's exact position.  If this results in either of the
        values in _Enemy.steps exceeding the prepare.CELL_SIZE the sprite
        will be snapped to the cell and their AI will be queried for a new
        direction.  Finally, update the sprite's rect and animation.
        """
        change_dir = False
        self.move(dt)
        if any(val >= prepare.CELL_SIZE[i] for i,val in enumerate(self.steps)):
            self.snap_to_grid()
            change_dir = True
        if change_dir:
            self.direction = self.ai(obstacles)
            if self.direction in self.anim_directions:
                self.anim_direction = self.direction
        if self.hit_state:
            self.hit_state.check_tick(now)
            if self.hit_state.done:
                self.state = "walk"
                self.hit_state = False
        self.rect.topleft = self.exact_position
        self.adjust_image(now)

    def move(self, dt):
        for i in (0,1):
            vec_component = prepare.DIRECT_DICT[self.direction][i]
            self.exact_position[i] += vec_component*self.speed*dt
            self.steps[i] += abs(vec_component*self.speed*dt)

    def snap_to_grid(self):
        self.steps = [0, 0]
        self.rect.topleft = self.get_occupied_cell()
        self.exact_position = list(self.rect.topleft)

    def adjust_image(self, now):
        try:
            anim = self.anims[self.state][self.anim_direction]
        except TypeError:
            anim = self.anims[self.state]
        self.image = anim.get_next_frame(now)

    def draw(self, surface):
        """Generic draw function."""
        surface.blit(self.image, self.rect)


class Cabbage(_Enemy):
    """The eponymous Cabbage monster. (1 direction)"""
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
        self.frames = tools.strip_coords_from_sheet(ENEMY_SHEET,
                                         ENEMIES["cabbage"], prepare.CELL_SIZE)
        self.anims = {"walk" : tools.Anim(self.frames[:2], 7),
                      "hit" : tools.Anim(self.frames[2:4], 20),
                      "die" : tools.Anim(self.frames[4:], 7, 1)}
        self.health = 3
        self.attack = 4


class Zombie(_Enemy):
    """The typical stock zombie. (4 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
        self.ai = LinearAI(self)
        self.frames = tools.strip_coords_from_sheet(ENEMY_SHEET,
                                          ENEMIES["zombie"], prepare.CELL_SIZE)
        walk = {"front" : tools.Anim(self.frames[:2], 7),
                "back" : tools.Anim(self.frames[2:4], 7),
                "left" : tools.Anim([pg.transform.flip(self.frames[4], 1, 0),
                               pg.transform.flip(self.frames[5], 1, 0)], 7),
                "right" : tools.Anim(self.frames[4:6], 7)}
        hit = {"front" : tools.Anim(self.frames[6:8], 20),
                "back" : tools.Anim(self.frames[8:10], 20),
                "left" : tools.Anim([pg.transform.flip(self.frames[10], 1, 0),
                               pg.transform.flip(self.frames[11], 1, 0)], 20),
                "right" : tools.Anim(self.frames[10:12], 20)}
        die_frames = self.frames[12:]+self.frames[16:]
        self.anims = {"walk" : walk,
                      "hit" : hit,
                      "die" : tools.Anim(die_frames, 5, 1)}
        self.health = 10
        self.attack = 8


class Snake(_Enemy):
    """An annoying snake. (2 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
        self.anim_directions = ["left", "right"]
        self.anim_direction = random.choice(self.anim_directions)
        self.direction = self.anim_direction
        self.ai = LinearAI(self)
        self.frames = tools.strip_coords_from_sheet(ENEMY_SHEET,
                                           ENEMIES["snake"], prepare.CELL_SIZE)
        walk = {"left" : tools.Anim(self.frames[:2], 7),
                "right" : tools.Anim([pg.transform.flip(self.frames[0], 1, 0),
                                pg.transform.flip(self.frames[1], 1, 0)], 7)}
        hit = {"left" : tools.Anim(self.frames[2:4], 20),
               "right" : tools.Anim([pg.transform.flip(self.frames[2], 1, 0),
                                pg.transform.flip(self.frames[3], 1, 0)], 20)}
        self.anims = {"walk" : walk,
                      "hit" : hit,
                      "die" : tools.Anim(self.frames[4:], 5, 1)}
        self.health = 6
        self.attack = 6
