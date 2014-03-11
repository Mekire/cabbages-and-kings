import random
import pygame as pg

from . import shadow, item_sprites
from .. import prepare, tools


ENEMY_SHEET = prepare.GFX["enemies"]["enemysheet"]

ENEMY_COORDS = {
    "cabbage" : [(0,0), (1,0), (2,0), (3,0), (4,0), (5,0), (6,0)],
    "snake" : [(0,5), (1,5), (2,5), (3,5), (4,5), (5,5), (6,5), (7,5), (8,5)],
    "zombie" : [(0,3), (1,3), (6,4), (7,4), (8,2), (9,2), (2,3), (3,3), (8,4),
                (9,4), (8,6), (9,6), (4,3), (5,3), (6,3), (7,3), (8,3), (9,3)]}

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
        return pg.sprite.spritecollideany(self.sprite, obstacles)


class LinearAI(BasicAI):
    """
    Another very basic AI.  Makes a sprite choose a new completely random
    direction, but will not select the completely opposite direction
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
        try:
            opposite = prepare.OPPOSITE_DICT[self.sprite.direction]
            directions = prepare.DIRECTIONS[:]
            directions.remove(opposite)
        except KeyError:
            directions = prepare.DIRECTIONS[:]
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
    def __init__(self, name, sheet, pos, speed, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        coords, size = ENEMY_COORDS[name], prepare.CELL_SIZE
        self.frames = tools.strip_coords_from_sheet(sheet, coords, size)
        self.rect = pg.Rect(pos, prepare.CELL_SIZE)
        self.mask = pg.Mask(prepare.CELL_SIZE)
        self.mask.fill()
        self.exact_position = list(self.rect.topleft)
        self.steps = [0, 0]
        self.ai = BasicAI(self)
        self.speed = speed
        self.direction = None
        self.anim_directions = prepare.DIRECTIONS[:]
        self.anim_direction = random.choice(self.anim_directions)
        self.shadow = shadow.Shadow((40,20), self.rect)
        self.image = None
        self.state = "walk"
        self.hit_state = False
        self.knock_state = False
        self.knock_dir = None
        self.knock_collide = None
        self.knock_clear = None
        self.drops = [None]

    def get_occupied_cell(self):
        """
        Return screen coordinates of the cell the sprite occupies with
        respect to the sprite's center point.
        """
        return tools.get_cell_coordinates(prepare.SCREEN_RECT,
                                          self.rect.center, prepare.CELL_SIZE)

    def collide_with_player(self, player):
        """Call the player's got_hit function doing damage, knocking, etc."""
        if self.state != "die":
            player.got_hit(self)

    def got_hit(self, player, obstacles, *item_groups):
        """
        Called from the level class if the player is attacking and the
        weapon rect collides with the sprite.
        """
        if not self.hit_state:
            self.health -= player.equipped["weapon"].strength
            if self.health > 0:
                self.state = "hit"
                self.hit_state = tools.Timer(300, 1)
                self.knock_state = True
                self.knock_dir = player.direction
                self.got_knocked_collision(obstacles)
            elif self.state != "die":
                self.drop_item(*item_groups)
                self.state = "die"

    def drop_item(self, *item_groups):
        """
        Drop a random item from self.drop.  If None is chosen then no
        item is dropped.
        """
        drop = random.choice(self.drops)
        if drop:
            item_sprites.ITEMS[drop](self.rect, 15, *item_groups)

    def got_knocked_collision(self, obstacles):
        """
        Check the next 3 cells for collisions and set knock_collide to
        the first one found.  If none are found set knock_clear to the 4th rect
        for a reference point.
        """
        self.knock_collide = None
        self.knock_clear = None
        index = self.knock_dir in ("front", "back")
        cell_size = prepare.CELL_SIZE[index]
        component = prepare.DIRECT_DICT[self.knock_dir][index]
        for knocked_distance in (1, 2, 3):
            move = component*cell_size*knocked_distance
            self.rect[index] += move
            collide = pg.sprite.spritecollideany(self, obstacles)
            self.rect[index] -= move
            if collide:
                self.knock_collide = collide.rect
                break
        else:
            self.knock_clear = self.rect.copy()
            self.knock_clear[index] += component*cell_size*(knocked_distance+1)

    def getting_knocked(self, dt):
        """
        Update exact position based on knock and check if sprite has reached
        the final rect (either knock_collide or knock_clear).
        """
        for i in (0,1):
            vec_component = prepare.DIRECT_DICT[self.knock_dir][i]
            self.exact_position[i] += vec_component*KNOCK_SPEED*dt
        test_rect = pg.Rect(self.exact_position, prepare.CELL_SIZE)
        if self.knock_clear:
            test_against = self.knock_clear
        else:
            test_against = self.knock_collide
        if test_rect.colliderect(test_against):
            index = self.knock_dir in ("front", "back")
            current = self.direction in ("front", "back")
            step_near_zero = [int(step) for step in self.steps] == [0, 0]
            self.adjust_on_collide(test_rect, test_against, index)
            self.exact_position = list(test_rect.topleft)
            if (index == current and self.knock_collide) or step_near_zero:
                #Makes update find a new direction next loop.
                self.steps = list(prepare.CELL_SIZE)
            self.knock_state = False

    def adjust_on_collide(self, rect_to_adjust, collide_rect, i):
        """
        Adjust sprites's position if colliding with a block while knocked.
        """
        if rect_to_adjust[i] < collide_rect[i]:
            rect_to_adjust[i] = collide_rect[i]-rect_to_adjust.size[i]
        else:
            rect_to_adjust[i] = collide_rect[i]+collide_rect.size[i]

    def update(self, now, dt, obstacles):
        """
        Update the sprite's exact position.  If this results in either of the
        values in _Enemy.steps exceeding the prepare.CELL_SIZE the sprite
        will be snapped to the cell and their AI will be queried for a new
        direction.  Finally, update the sprite's rect and animation.
        """
        if self.state not in ("hit", "die"):
            if self.direction:
                self.move(dt)
            else:
                self.change_direction(obstacles)
            if any(x >= prepare.CELL_SIZE[i] for i,x in enumerate(self.steps)):
                self.change_direction(obstacles)
        if self.hit_state:
            self.hit_state.check_tick(now)
            self.getting_knocked(dt)
            if self.hit_state.done and not self.knock_state:
                self.state = "walk"
                self.hit_state = False
        elif self.state == "die" and self.get_anim().done:
            self.kill()
        self.rect.topleft = self.exact_position
        self.image = self.get_anim().get_next_frame(now)

    def move(self, dt):
        """Move the sprites exact position and add to steps appropriately."""
        for i in (0,1):
            vec_component = prepare.DIRECT_DICT[self.direction][i]
            self.exact_position[i] += vec_component*self.speed*dt
            self.steps[i] += abs(vec_component*self.speed*dt)

    def change_direction(self, obstacles):
        """
        If either element of steps is greater than the corresponding
        element of CELL_SIZE, query AI for new direction.
        """
        self.snap_to_grid()
        self.direction = self.ai(obstacles)
        if self.direction in self.anim_directions:
            self.anim_direction = self.direction

    def snap_to_grid(self):
        """Reset steps and snap the sprite to its current cell."""
        self.steps = [0, 0]
        self.rect.topleft = self.get_occupied_cell()
        self.exact_position = list(self.rect.topleft)

    def get_anim(self):
        """Get the current frame from the appropriate animation."""
        try:
            anim = self.anims[self.state][self.anim_direction]
        except TypeError:
            anim = self.anims[self.state]
        return anim

    def draw(self, surface):
        """Generic draw function."""
        surface.blit(self.image, self.rect)


class Cabbage(_Enemy):
    """The eponymous Cabbage monster. (1 direction)"""
    def __init__(self, *args):
        _Enemy.__init__(self, "cabbage", ENEMY_SHEET, *args)
        self.anims = {"walk" : tools.Anim(self.frames[:2], 7),
                      "hit" : tools.Anim(self.frames[2:4], 20),
                      "die" : tools.Anim(self.frames[4:], 5, 1)}
        self.health = 3
        self.attack = 4
        self.drops = ["heart"]


class Zombie(_Enemy):
    """The typical stock zombie. (4 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self,  "zombie", ENEMY_SHEET, *args)
        self.ai = LinearAI(self)
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
        self.drops = ["key"]


class Snake(_Enemy):
    """An annoying snake. (2 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self, "snake", ENEMY_SHEET, *args)
        self.anim_directions = ["left", "right"]
        self.anim_direction = random.choice(self.anim_directions)
        self.direction = self.anim_direction
        self.ai = LinearAI(self)
        walk = {"left" : tools.Anim(self.frames[:2], 7),
                "right" : tools.Anim([pg.transform.flip(self.frames[0], 1, 0),
                                pg.transform.flip(self.frames[1], 1, 0)], 7)}
        hit = {"left" : tools.Anim(self.frames[2:4], 20),
               "right" : tools.Anim([pg.transform.flip(self.frames[2], 1, 0),
                                pg.transform.flip(self.frames[3], 1, 0)], 20)}
        flipped_die = [pg.transform.flip(f, 1, 0) for f in self.frames[4:]]
        die = {"left" : tools.Anim(self.frames[4:], 5, 1),
               "right" : tools.Anim(flipped_die, 5, 1)}
        self.anims = {"walk" : walk,
                      "hit" : hit,
                      "die" : die}
        self.health = 6
        self.attack = 6
        self.drops = ["diamond", "potion"]
