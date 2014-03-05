import random
import pygame as pg

from .. import prepare, tools


ENEMY_SHEET = prepare.GFX["enemies"]["enemysheet"]

ENEMIES = {"cabbage" : [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0)],
           "snake" : [(0,5),(1,5),(2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5)],
           "zombie" : [(0,3),(1,3),(6,4),(7,4),(8,2),(9,2),(2,3),(3,3),(8,4),
                       (9,4),(8,6),(9,6),(4,3),(5,3),(6,3),(7,3),(8,3),(9,3)]}


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
        self.exact_position = list(self.rect.topleft)
        self.steps = [0, 0]
        self.ai = BasicAI(self)
        self.speed = speed
        self.direction = random.choice(prepare.DIRECTIONS)
        self.anim_direction = self.direction
        self.anim_directions = prepare.DIRECTIONS[:]
        self.image = None
        self.state = state

    def get_occupied_cell(self):
        """
        Return screen coordinates of the cell the sprite occupies with
        respect to the sprite's center point.
        """
        return tools.get_cell_coordinates(prepare.SCREEN_RECT,
                                          self.rect.center, prepare.CELL_SIZE)

    def update(self, now, dt, obstacles):
        """
        Update the sprite's exact position.  If this results in either of the
        values in _Enemy.steps exceeding the prepare.CELL_SIZE the sprite
        will be snapped to the cell and their AI will be queried for a new
        direction.  Finally, update the sprite's rect and animation.
        """
        change_dir = False
        #Update position and steps.
        for i in (0,1):
            vec_component = prepare.DIRECT_DICT[self.direction][i]
            self.exact_position[i] += vec_component*self.speed*dt
            self.steps[i] += abs(vec_component*self.speed*dt)
        #Snap to grid if steps exceeds prepare.CELL_SIZE.
        if any(val >= prepare.CELL_SIZE[i] for i,val in enumerate(self.steps)):
            self.steps = [0, 0]
            self.rect.topleft = self.get_occupied_cell()
            self.exact_position = list(self.rect.topleft)
            change_dir = True
        #Query AI for new direction
        if change_dir:
            self.direction = self.ai(obstacles)
            if self.direction in self.anim_directions:
                self.anim_direction = self.direction
        self.rect.topleft = self.exact_position
        #Select correct animation.
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
        self.anims = {"walk" : Anim(self.frames[:2], 7),
                      "hit" : Anim(self.frames[2:4], 20),
                      "die" : Anim(self.frames[4:], 7, 1)}

class Zombie(_Enemy):
    """The typical stock zombie. (4 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
        self.ai = LinearAI(self)
        self.frames = tools.strip_coords_from_sheet(ENEMY_SHEET,
                                          ENEMIES["zombie"], prepare.CELL_SIZE)
        walk = {"front" : Anim(self.frames[:2], 7),
                "back" : Anim(self.frames[2:4], 7),
                "left" : Anim([pg.transform.flip(self.frames[4], 1, 0),
                               pg.transform.flip(self.frames[5], 1, 0)], 7),
                "right" : Anim(self.frames[4:6], 7)}
        hit = {"front" : Anim(self.frames[6:8], 20),
                "back" : Anim(self.frames[8:10], 20),
                "left" : Anim([pg.transform.flip(self.frames[10], 1, 0),
                               pg.transform.flip(self.frames[11], 1, 0)], 20),
                "right" : Anim(self.frames[10:12], 20)}
        self.anims = {"walk" : walk,
                      "hit" : hit,
                      "die" : Anim(self.frames[12:]+self.frames[16:], 5, 1)}


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
        walk = {"left" : Anim(self.frames[:2], 7),
                "right" : Anim([pg.transform.flip(self.frames[0], 1, 0),
                                pg.transform.flip(self.frames[1], 1, 0)], 7)}
        hit = {"left" : Anim(self.frames[2:4], 20),
                "right" : Anim([pg.transform.flip(self.frames[2], 1, 0),
                                pg.transform.flip(self.frames[3], 1, 0)], 20)}
        self.anims = {"walk" : walk,
                      "hit" : hit,
                      "die" : Anim(self.frames[4:], 5, 1)}


class Anim(object):
    """A class to simplify the act of adding animations to sprites."""
    def __init__(self, frames, fps, loops=-1):
        """
        The argument frames is a list of frames in the correct order;
        fps is the frames per second of the animation;
        loops is the number of times the animation will loop (a value of -1
        will loop indefinitely).
        """
        self.frames = frames
        self.fps = fps
        self.frame = 0
        self.timer = None
        self.loops = loops
        self.loop_count = 0
        self.done = False

    def get_next_frame(self, now):
        """
        Advance the frame if enough time has elapsed and the animation has
        not finished looping.
        """
        if not self.timer:
            self.timer = now
        if not self.done and now-self.timer > 1000.0/self.fps:
            self.frame = (self.frame+1)%len(self.frames)
            if not self.frame:
                self.loop_count += 1
                if self.loops != -1 and self.loop_count >= self.loops:
                    self.done = True
                    self.frame -= 1
            self.timer = now
        return self.frames[self.frame]

    def reset(self):
        """Set frame, timer, and loop status back to the initialized state."""
        self.frame = 0
        self.timer = None
        self.loop_count = 0
        self.done = False
