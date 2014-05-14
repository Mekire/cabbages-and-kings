import random
import pygame as pg

from . import shadow, item_sprites, projectiles
from .. import prepare, tools


KNOCK_SPEED = 12.5  #Pixels per frame.

ENEMY_SHEET = prepare.GFX["enemies"]["enemysheet"]
ENEMY_SHEET_2 = prepare.GFX["enemies"]["enemysheet1"]

ENEMY_COORDS = {
    "cabbage" : [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),(6,0)],
    "spider" : [(0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2)],
    "turtle" : [(0,4),(1,4),(2,4),(3,4),(4,4),(5,4)],
    "snake" : [(0,5),(1,5),(2,5),(3,5),(4,5),(5,5),(6,5),(7,5),(8,5)],
    "scorpion" : [(0,6),(1,6),(2,6),(3,6),(4,6),(5,6),(6,6),(7,6)],
    "skeleton" : [(0,1),(1,1),(2,1),(3,1),(4,1),(5,1),
                  (7,1),(7,0),(8,1),(8,0),(9,1),(9,0)],
    "tank" : [(0,7),(1,7),(2,7),(3,7),(4,7),(5,7),(6,7),(7,7),
              (8,6),(5,8),(6,8),(7,8),(8,7),(9,7),(8,8)],
    "frog" : [(0,10),(1,10),(0,11),(1,11),(2,11),(3,11),
              (2,10),(3,10),(4,11),(5,11),(6,11),(8,12),
              (4,10),(5,10),(6,10),(7,11),(8,11),(9,11),(9,12)],
    "crab" : [(4,9),(5,9),(6,9),(7,9),(8,9),(9,9),(7,10),(8,10),(9,10)],
    "zombie" : [(0,3),(1,3),(6,4),(7,4),(8,2),(9,2),(2,3),(3,3),(8,4),(9,4),
                (9,5),(9,6),(4,3),(5,3),(6,3),(7,3),(8,3),(9,3)],
    "snail" : [(0,8),(1,8),(2,8),(3,8),(4,8),(0,9),(1,9),(2,9),(3,9)],
    "mushroom" : [(0,0),(1,0),(2,0),(3,0),(4,0),(5,0),
                  (6,0),(7,0),(8,0),(9,0),(9,1)],
    "blue_oni" : [(0,1),(1,1),(4,1),(9,2),(7,1),(8,1),(2,1),(3,1),(5,1),(6,1),
                  (0,2),(1,2),(2,2),(3,2),(4,2),(5,2),(6,2),(7,2),(8,2)],
    "red_oni" : [(0,3),(1,3),(4,3),(5,3),(8,3),(9,3),(2,3),(3,3),(6,3),(7,3),
                 (0,4),(1,4),(2,4),(3,4),(4,4),(5,4),(6,2),(7,2),(8,2)],
    "daruma" : [(0,5),(1,5),(2,5),(3,5),(6,4),(7,4),(8,4),(9,4),(4,5),(5,5),
                (6,5),(7,5),(8,5),(9,5),(0,6),(1,6),(2,6),(3,6),(4,6),(5,6)],
    "lantern" : [(0,7),(1,7),(6,6),(7,6),(2,7),(3,7),(4,7),
                 (5,7),(6,7),(7,7),(8,7),(9,7),(9,6)],
    "evil_elf" : [(0,8),(1,8),(2,8),(3,8),(4,8),(5,8),(6,8),(7,8)],
    "knight" : [(0,11),(1,11),(2,11),(3,11),(4,11),(5,11),
                (6,11),(7,11),(0,12),(1,12),(2,12),(3,12)]}


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


class CrabWalk(BasicAI):
    """
    An AI that favors horizontal movement over vertical.
    Used for crabs and spiders.
    """
    def __init__(self, sprite):
        BasicAI.__init__(self, sprite)

    def __call__(self, obstacles):
        """Make AI classes callable."""
        return self.get_direction(obstacles)

    def get_direction(self, obstacles):
        """Sprite has a 3:4 chance of moving horizontally."""
        directions = ["front", "back"]+["left"]*3+["right"]*3
        random.shuffle(directions)
        new_dir = None
        while not new_dir:
            new_dir = directions.pop()
            move = (prepare.DIRECT_DICT[new_dir][0]*prepare.CELL_SIZE[0],
                    prepare.DIRECT_DICT[new_dir][1]*prepare.CELL_SIZE[1])
            self.sprite.rect.move_ip(*move)
            if self.check_collisions(obstacles):
                new_dir = None
            self.sprite.rect.move_ip(-move[0], -move[1])
        return new_dir


class _Enemy(tools._BaseSprite):
    """
    The base class for all enemies.
    """
    def __init__(self, name, sheet, pos, speed, *groups):
        coords, size = ENEMY_COORDS[name], prepare.CELL_SIZE
        tools._BaseSprite.__init__(self, pos, size, *groups)
        self.frames = tools.strip_coords_from_sheet(sheet, coords, size)
        self.mask = pg.Mask(prepare.CELL_SIZE)
        self.mask.fill()
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
        self.busy = False
        self.act_mid_step = False
        self.drops = [None]

    def check_action(self, player, group_dict):
        pass

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
        if not self.hit_state and self.state != "spawn":
            self.health -= player.strength
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
            item_sprites.ITEMS[drop](self.rect, 15, False, None, *item_groups)

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

    def getting_knocked(self):
        """
        Update exact position based on knock and check if sprite has reached
        the final rect (either knock_collide or knock_clear).
        """
        for i in (0,1):
            vec_component = prepare.DIRECT_DICT[self.knock_dir][i]
            self.exact_position[i] += vec_component*KNOCK_SPEED
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

    def update(self, now, player, group_dict):
        """
        Update the sprite's exact position.  If this results in either of the
        values in _Enemy.steps exceeding the prepare.CELL_SIZE the sprite
        will be snapped to the cell and their AI will be queried for a new
        direction.  Finally, update the sprite's rect and animation.
        """
        obstacles = group_dict["solid_border"]
        self.old_position = self.exact_position[:]
        if self.state not in ("hit", "die", "spawn"):
            if self.act_mid_step and not self.busy:
                self.busy = self.check_action(player, group_dict)
            if self.direction and not self.busy:
                self.move()
            else:
                self.change_direction(obstacles)
            if any(x >= prepare.CELL_SIZE[i] for i,x in enumerate(self.steps)):
                if not self.act_mid_step and not self.busy:
                    self.busy = self.check_action(player, group_dict)
                self.change_direction(obstacles)
        if self.hit_state:
            self.hit_state.check_tick(now)
            self.getting_knocked()
            if self.hit_state.done and not self.knock_state:
                self.state = "walk"
                self.hit_state = False
        elif self.state == "die" and self.get_anim().done:
            self.kill()
            self.shadow.kill()
        elif self.state == "spawn" and self.get_anim().done:
            self.state = "walk"
        self.rect.topleft = self.exact_position
        self.image = self.get_anim().get_next_frame(now)

    def move(self):
        """Move the sprites exact position and add to steps appropriately."""
        for i in (0,1):
            vec_component = prepare.DIRECT_DICT[self.direction][i]
            self.exact_position[i] += vec_component*self.speed
            self.steps[i] += abs(vec_component*self.speed)

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

    def on_map_change(self):
        self.busy = False


class _BasicFrontFrames(_Enemy):
    """
    Used for enemy sprites that only have frames in 1 direction.
    Include: Cabbage, Spider, Turtle, Crab.
    """
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
        self.anims = {"walk" : tools.Anim(self.frames[:2], 7),
                      "hit" : tools.Anim(self.frames[2:4], 20),
                      "die" : None} #Set die in specific class declaration.
        self.image = self.get_anim().get_next_frame(pg.time.get_ticks())


class _SideFramesOnly(_Enemy):
    """
    Used for enemy sprites that only have frames for the right and left sides.
    The right frames are flipped versions of the left.
    Include: Snake, Scorpion, Snail.
    """
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
        self.anim_directions = ["left", "right"]
        self.anim_direction = random.choice(self.anim_directions)
        self.ai = LinearAI(self)
        walk = {"left" : tools.Anim(self.frames[:2], 7),
                "right" : tools.Anim([pg.transform.flip(self.frames[0], 1, 0),
                                pg.transform.flip(self.frames[1], 1, 0)], 7)}
        hit = {"left" : tools.Anim(self.frames[2:4], 20),
               "right" : tools.Anim([pg.transform.flip(self.frames[2], 1, 0),
                                pg.transform.flip(self.frames[3], 1, 0)], 20)}
        die_frames = self.frames[4:]+[self.frames[-1]]
        flipped_die = [pg.transform.flip(frame, 1, 0) for frame in die_frames]
        die = {"left" : tools.Anim(self.frames[4:], 5, 1),
               "right" : tools.Anim(flipped_die, 5, 1)}
        self.anims = {"walk" : walk, "hit" : hit, "die" : die}
        self.image = self.get_anim().get_next_frame(pg.time.get_ticks())


class _FourDirFrames(_Enemy):
    """
    Used for four direction enemies.
    The left frames are flipped versions of the right.
    """
    def __init__(self, *args):
        _Enemy.__init__(self, *args)
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
        self.anims = {"walk" : walk, "hit" : hit, "die" : None}
        self.image = self.get_anim().get_next_frame(pg.time.get_ticks())


class Cabbage(_BasicFrontFrames):
    """The eponymous Cabbage monster. (1 direction)"""
    def __init__(self, *args):
        _BasicFrontFrames.__init__(self, "cabbage", ENEMY_SHEET, *args)
        die_frames = self.frames[4:]+[self.frames[-1]]
        self.anims["die"] = tools.Anim(die_frames, 5, 1)
        self.health = 3
        self.attack = 4
        self.drops = ["heart"]


class Spider(_BasicFrontFrames):
    """Spider like monster; shoots webs (1 direction)."""
    def __init__(self, *args):
        _BasicFrontFrames.__init__(self, "spider", ENEMY_SHEET, *args)
        die_frames = self.frames[4:6]+self.frames[6:]*2
        self.anims["die"] = tools.Anim(die_frames, 5, 1)
        self.ai = CrabWalk(self)
        self.health = 6
        self.attack = 6
        self.drops = ["diamond", None]
        self.shooting = pg.sprite.Group()

    def check_action(self, player, group_dict):
        """
        Every time the spider finishes moving a cell it has a chance to
        shoot a web.
        """
        if not self.shooting and random.random() <= 0.25:
            self.shooting.add(projectiles.Web(self, group_dict))


class Crab(_BasicFrontFrames):
    """Irritated crab. Shoots bubbles (not implemented) (1 direction)."""
    def __init__(self, *args):
        _BasicFrontFrames.__init__(self, "crab", ENEMY_SHEET, *args)
        die_frames = self.frames[4:7]+self.frames[7:]*2
        self.anims["die"] = tools.Anim(die_frames, 5, 1)
        self.ai = CrabWalk(self)
        self.health = 6
        self.attack = 6
        self.drops = [None, None, "diamond"]


class Turtle(_BasicFrontFrames):
    """Spinning tornado turtle (1 direction)."""
    def __init__(self, *args):
        _BasicFrontFrames.__init__(self, "turtle", ENEMY_SHEET, *args)
        die_frames = self.frames[2:5]+[self.frames[5]]*2
        self.anims["die"] = tools.Anim(die_frames, 5, 1)
        self.health = 12
        self.attack = 6
        self.drops = [None]


class Snake(_SideFramesOnly):
    """An annoying snake. (2 directions)"""
    def __init__(self, *args):
        _SideFramesOnly.__init__(self, "snake", ENEMY_SHEET, *args)
        self.health = 6
        self.attack = 6
        self.drops = ["diamond", "potion", None, None]


class Scorpion(_SideFramesOnly):
    """A high damage scorpion. (2 directions)"""
    def __init__(self, *args):
        _SideFramesOnly.__init__(self, "scorpion", ENEMY_SHEET, *args)
        self.health = 6
        self.attack = 10
        self.drops = ["heart", None]


class Snail(_SideFramesOnly):
    """A toxic trail leaving snail (not implemented). (2 directions)"""
    def __init__(self, *args):
        _SideFramesOnly.__init__(self, "snail", ENEMY_SHEET, *args)
        self.health = 10
        self.attack = 8
        self.drops = ["diamond", "heart", None, None]


class Lantern(_SideFramesOnly):
    """A haunted lantern. (2 directions)"""
    def __init__(self, *args):
        _SideFramesOnly.__init__(self, "lantern", ENEMY_SHEET_2, *args)
        self.ai = BasicAI(self)
        self.health = 6
        self.attack = 6
        self.drops = ["heart", None, None]


class Zombie(_FourDirFrames):
    """The typical stock zombie. (4 directions)"""
    def __init__(self, *args):
        _FourDirFrames.__init__(self,  "zombie", ENEMY_SHEET, *args)
        self.ai = LinearAI(self)
        die_frames = self.frames[12:]+self.frames[16:]
        self.anims["die"] = tools.Anim(die_frames, 5, 1)
        self.health = 10
        self.attack = 8
        self.drops = ["key"]


class Frog(_FourDirFrames):
    """Your standard hoppy frog (4 directions)"""
    def __init__(self, *args):
        _FourDirFrames.__init__(self,  "frog", ENEMY_SHEET, *args)
        die_frames = self.frames[12:]
        self.anims["die"] = tools.Anim(die_frames, 5, 1)
        self.health = 6
        self.attack = 6
        self.drops = ["heart", None, None]


class AoOni(_FourDirFrames):
    """Let's go to Onigashima."""
    def __init__(self, *args):
        _FourDirFrames.__init__(self,  "blue_oni", ENEMY_SHEET_2, *args)
        die_frames = self.frames[12:]
        self.anims["die"] = tools.Anim(die_frames, 10, 1)
        self.health = 15
        self.attack = 8
        self.drops = ["heart", None, None]


class AkaOni(_FourDirFrames):
    """Let's go to Onigashima."""
    def __init__(self, *args):
        _FourDirFrames.__init__(self,  "red_oni", ENEMY_SHEET_2, *args)
        die_frames = self.frames[12:]
        self.anims["die"] = tools.Anim(die_frames, 10, 1)
        self.health = 10
        self.attack = 15
        self.drops = ["diamond", None, None]


class Skeleton(_Enemy):
    """The classic skeleton. (4 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self,  "skeleton", ENEMY_SHEET, *args)
        self.ai = LinearAI(self)
        self.state = "spawn"
        walk = {"front" : tools.Anim([self.frames[3],
                               pg.transform.flip(self.frames[3], 1, 0)], 7),
                "back" : tools.Anim([self.frames[2],
                               pg.transform.flip(self.frames[2], 1, 0)], 7),
                "left" : tools.Anim(self.frames[:2], 7),
                "right" : tools.Anim([pg.transform.flip(self.frames[0], 1, 0),
                               pg.transform.flip(self.frames[1], 1, 0)], 7)}
        hit = {"front" : tools.Anim(self.frames[10:], 20),
               "back" : tools.Anim(self.frames[8:10], 20),
               "left" : tools.Anim(self.frames[6:8], 20),
               "right" : tools.Anim([pg.transform.flip(self.frames[6], 1, 0),
                               pg.transform.flip(self.frames[7], 1, 0)], 20)}
        die_frames = self.frames[3:5]+[self.frames[5]]*2
        self.anims = {"walk" : walk,
                      "hit" : hit,
                      "die" : tools.Anim(die_frames, 5, 1),
                      "spawn" : tools.Anim(die_frames[::-1], 3, 1)}
        self.image = self.get_anim().get_next_frame(pg.time.get_ticks())
        self.health = 6
        self.attack = 6
        self.drops = ["heart", None]


class Daruma(_Enemy):
    """A bouncy Daruma with a typical lack of depth perception."""
    def __init__(self, *args):
        _Enemy.__init__(self,  "daruma", ENEMY_SHEET_2, *args)
        self.anim_directions = ["front", "back"]
        self.anim_direction = random.choice(self.anim_directions)
        self.ai = BasicAI(self)
        walk = {"front" : tools.Anim(self.frames[:2], 7),
                "back" : tools.Anim(self.frames[4:6], 7)}
        hit = {"front" : tools.Anim(self.frames[2:4], 20),
               "back" : tools.Anim(self.frames[6:8], 20)}
        die = tools.Anim(self.frames[8:], 10, 1)
        self.anims = {"walk" : walk, "hit" : hit, "die" : die}
        self.image = self.get_anim().get_next_frame(pg.time.get_ticks())
        self.health = 6
        self.attack = 6
        self.drops = ["heart", None]


class EvilElf(_Enemy):
    """Elf that shoots arrows (not implemented) (4 directions)"""
    def __init__(self, *args):
        _Enemy.__init__(self,  "evil_elf", ENEMY_SHEET_2, *args)
        self.ai = LinearAI(self)
        walk = {"front" : tools.Anim(self.frames[:2], 7),
                "back" : tools.Anim(self.frames[6:8], 7),
                "left" : tools.Anim(self.frames[2:4], 7),
                "right" : tools.Anim(self.frames[4:6], 7)}
        hit = {"front" : tools.Anim(self.frames[:2], 20),
                "back" : tools.Anim(self.frames[6:8], 20),
                "left" : tools.Anim(self.frames[2:4], 20),
                "right" : tools.Anim(self.frames[4:6], 20)}
        death_args = (ENEMY_SHEET, (150,50), prepare.CELL_SIZE, 3)
        death_frames = tools.strip_from_sheet(*death_args)
        die = tools.Anim(death_frames, 3, loops=1)
        self.anims = {"walk" : walk, "hit" : hit, "die" : die}
        self.image = self.get_anim().get_next_frame(pg.time.get_ticks())
        self.health = 6
        self.attack = 6
        self.drops = ["heart", None]


class FireBallGenerator(_Enemy):
    """Creates fireballs at a specified interval."""
    def __init__(self, target, speed, *groups):
        tools._BaseSprite.__init__(self, target, prepare.CELL_SIZE, *groups)
        self.image = pg.Surface((1,1)).convert_alpha() #Required by interface.
        self.image.fill((0,0,0,0))
        self.speed = speed*100 #Miliseconds between shots.
        self.shot_delay = random.random()*self.speed/2
        self.timer = None

    def reset_timer(self):
        """
        This timer is reset every time the player leaves the screen to
        prevent projectiles from syncronizing.
        """
        self.timer = tools.Timer(self.speed)
        self.timer.check_tick(pg.time.get_ticks())

    def collide_with_player(self, player):
        """The generator itself can not hit or be hit."""
        pass

    def got_hit(self, player, obstacles, *item_groups):
        """The generator itself can not hit or be hit."""
        pass

    def update(self, now, player, group_dict):
        """
        If the timer isn't setup, reset it.  Check timer tick and
        add a new fireball if ready.
        """
        if not self.timer:
            self.reset_timer()
        if self.timer.check_tick(now-self.shot_delay):
            groups = group_dict["projectiles"], group_dict["moving"]
            fire = projectiles.FireBall(self, *groups)
            group_dict["all"].add(fire, layer=prepare.Z_ORDER["Projectiles"])

    def on_map_change(self):
        """
        The timer must be reset to None on map change to avoid syncronization.
        """
        _Enemy.on_map_change(self)
        self.timer = None


ENEMY_DICT = {(0, 0) : Cabbage,
              (50, 0) : Spider,
              (100, 0) : Frog,
              (150, 0) : None, #Mushroom,
              (200, 0) : Snail,
              (250, 0) : Crab,
              (300, 0) : Skeleton,
              (350, 0) : Zombie,
              (0, 50) : Snake,
              (50, 50) : Scorpion,
              (100, 50) : Turtle,
              (150, 50) : AoOni,
              (200, 50) : AkaOni,
              (250, 50) : Lantern,
              (300, 50) : Daruma,
              (350, 50) : FireBallGenerator,
              (0, 100) : None, #Knight,
              (50, 100) : EvilElf,
              (100, 100) : None, #Tank,
              (150, 100) : None} #Turret}


ENEMY_NAME = {"cabbage" : Cabbage,
              "spider" : Spider,
              "turtle" : Turtle,
              "snake" : Snake,
              "scorpion" : Scorpion,
              "skeleton" : Skeleton,
              "tank" : None, #Tank,
              "frog" : Frog,
              "crab" : Crab,
              "zombie" : Zombie,
              "snail" : Snail,
              "mushroom" : None, #Mushroom,
              "blue_oni" : AoOni,
              "red_oni" : AkaOni,
              "daruma" : Daruma,
              "lantern" : Lantern,
              "evil_elf" : EvilElf,
              "knight" : None} #Knight}
