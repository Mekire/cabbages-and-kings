"""
This module contains the primary class for the player.
"""

import random
import pygame as pg

from . import equips, shadow
from .. import prepare, tools


DRAW_ORDER = {"front" : ["body", "head", "weapon", "armleg", "shield"],
              "back"  : ["shield", "armleg", "weapon", "body", "head"],
              "left"  : ["shield", "body", "head", "weapon", "armleg"],
              "right" : ["weapon", "body", "head", "armleg", "shield"]}

DRAW_ATTACK_ORDER = {"front" : ["shield", "body", "head", "weapon", "armleg"],
                     "back"  : ["armleg", "weapon", "body", "head", "shield"],
                     "left"  : ["shield", "body", "head", "weapon", "armleg"],
                     "right" : ["weapon", "body", "head", "armleg", "shield"]}

STANDARD_ANIMATION_FPS = 7.0
HIT_ANIMATION_FPS = 20.0
BASE_SPEED = 3
KNOCK_SPEED = 12.5


class _ImageProcessing(object):
    """
    This is a mixin for use with the player class.  It pulls all the image
    loading and processing out of the main Player class to make things easier
    to work with.
    """
    def make_all_animations(self):
        """
        Returns a list of two dictionaries containing all animations.
        Index zero corresponds to normal frames; index one corresponds to
        frames for taking damage.
        """
        standard = {}
        standard["normal"] = self.make_images()
        standard["attack"] = self.make_images(True, DRAW_ATTACK_ORDER)
        strobing = {}
        strobing["normal"] = self.make_hit_images(standard["normal"])
        strobing["attack"] = self.make_hit_images(standard["attack"])
        return [standard, strobing]

    def make_death_animation(self):
        """Return a tools.Anim object with the player's death sequence."""
        sheet = prepare.GFX["enemies"]["enemysheet"]
        cell_coords = [(3,1), (4,1), (5,1), (6,1), (6,1)]
        args = (sheet, cell_coords, prepare.CELL_SIZE)
        death_cells = tools.strip_coords_from_sheet(*args)
        return tools.Anim(death_cells, 3, loops=1)

    def make_images(self, attack=False, order=DRAW_ORDER):
        """Create the player's animations any time he changes equipment."""
        base = pg.Surface(prepare.CELL_SIZE).convert()
        base.set_colorkey(prepare.COLOR_KEY)
        base.fill(prepare.COLOR_KEY)
        anims = {}
        for direction in prepare.DIRECTIONS:
            frames = []
            for frame in (0, 1):
                image = base.copy()
                for part in order[direction]:
                    if self.equipped[part]:
                        if attack:
                            get_part = self.get_attack_part_image
                        else:
                            get_part = self.get_part_image
                        blitting = get_part(direction, part, frame)
                        if blitting:
                            image.blit(blitting, (0,0))
                frames.append(image)
            anims[direction] = tools.Anim(frames, STANDARD_ANIMATION_FPS)
        return anims

    def make_hit_images(self, from_dict):
        """
        Create a dictionary of red and blue versions of the player's animations
        to use while getting hit.  Uses a messy 8-bit palette conversion.
        """
        anims = {}
        for direction in from_dict:
            frames = []
            for i,frame in enumerate(from_dict[direction].frames):
                image = pg.Surface(prepare.CELL_SIZE)
                image.fill((85,0,85))
                image.blit(frame, (0,0))
                image = image.convert(8)
                palette = image.get_palette()
                index, colorkey = (0, (235,0,85)) if i else (2, (85,0,235))
                for color in palette:
                    color[index] = min(color[index]+150, 255)
                image.set_palette(palette)
                image.set_colorkey(colorkey)
                frames.append(image)
            anims[direction] = tools.Anim(frames, HIT_ANIMATION_FPS)
        return anims

    def get_part_image(self, direction, part, frame):
        """Get the correct part image based on player direction and frame."""
        with_shield = not isinstance(self.equipped["shield"], equips.NoShield)
        if part=="armleg" and direction=="right" and with_shield:
            to_blit = self.equipped[part].images["right_with_shield"]
        elif self.equipped[part].images:
            to_blit = self.equipped[part].images[direction]
        else:
            return None
        try:
            return to_blit[frame]
        except TypeError:
            return to_blit

    def get_attack_part_image(self, direction, part, frame):
        """Get attack images if they exist."""
        if self.equipped[part].attack_images == "normal":
            piece = self.equipped[part].images
        elif self.equipped[part].attack_images:
            piece = self.equipped[part].attack_images
        else:
            return None
        to_blit = piece[direction]
        try:
            return to_blit[frame]
        except TypeError:
            return to_blit


class Player(tools._BaseSprite, _ImageProcessing):
    """A class to represent our main protagonist."""
    def __init__(self, data, *groups):
        """
        Most member variables are initialized within set_player_data and reset.
        """
        tools._BaseSprite.__init__(self, (0,0), prepare.CELL_SIZE, *groups)
        self.controls = prepare.DEFAULT_CONTROLS
        self.set_player_data(data)
        self.mask = self.make_mask()
        self.all_animations = self.make_all_animations()
        self.death_anim = self.make_death_animation()
        self.image = None
        self.reset()

    def reset(self):
        """
        Reset all necessary variables for a fresh player.
        Called on character creation as well as a continued game.
        """
        self.health = prepare.MAX_HEALTH
        self.direction = self.start_direction
        self.direction_stack = [] #Held keys in the order they were pressed.
        pos = (self.start_coord[0]*prepare.CELL_SIZE[0],
               self.start_coord[1]*prepare.CELL_SIZE[1])
        self.reset_position(pos)
        self.action_state = "normal"
        self.hit_state = False  #When true hit_state is a tools.Timer instance.
        self.knock_state = False #(direction, tools.Timer()) tuple when true.
        self.death_anim.reset()
        self.shadow = shadow.Shadow((40,20), self.rect)
        self.redraw = True

    def set_player_data(self, data):
        """Set required stats based on player data."""
        for key in data:
            if key not in ("identifiers", "gear", "equipped", "money", "keys"):
                setattr(self, key, data[key])
        self.identifiers = data["identifiers"].copy() #Persistant event flags.
        self.inventory = equips.make_equips(data["gear"])
        self.inventory["money"] = data["money"]
        self.inventory["keys"] = data["keys"]
        self.equipped = self.set_equips(data["equipped"])
        self.defense,self.strength,self.speed = self.calc_stats(self.equipped)

    def get_player_data(self):
        """Return a dictionary of the data that needs to be saved."""
        data = {}
        for key in prepare.DEFAULT_PLAYER:
            if key not in ("gear", "equipped", "money", "keys"):
                data[key] = getattr(self, key)
        data["money"] = self.inventory["money"]
        data["keys"] = self.inventory["keys"]
        gears = prepare.DEFAULT_GEAR.keys()
        data["gear"] = {gear:list(self.inventory[gear]) for gear in gears}
        data["equipped"] = {gear:self.equipped[gear].name for gear in gears}
        return data

    def set_equips(self, equip_data):
        """
        Set the equips the player is wearing.  Currently hardcoded.
        Eventually it will load from player data or revert to defaults.
        """
        equipped = {}
        for part,gear in equip_data.items():
            equipped[part] = self.inventory[part][gear]
        return equipped

    def set_equips_random(self):
        """
        Equip the player with random gear chosen from the items in their
        inventory.
        """
        equipped = {}
        for part in equips.EQUIP_DICT:
            parts = list(self.inventory[part].values())
            equipped[part] = random.choice(parts)
        return equipped

    def change_equip(self, gear_type, gear):
        """
        Called if the player switches out one gear for another.
        All animations are reconstructed and stats recalced.
        Do not call at performance critical times.
        """
        self.equipped[gear_type] = gear
        self.all_animations = self.make_all_animations()
        self.defense,self.strength,self.speed = self.calc_stats(self.equipped)
        self.redraw = True

    def calc_stats(self, gear):
        """Calculate stats based on current gear."""
        stat_mods = zip(*[g.stats for g in gear.values()])
        defense, attack, speed_mod = [sum(stats) for stats in stat_mods]
        return (defense, attack, BASE_SPEED+speed_mod)

    def make_mask(self):
        """Create a collision mask for the player."""
        temp = pg.Surface((prepare.CELL_SIZE)).convert_alpha()
        temp.fill((0,0,0,0))
        temp.fill(pg.Color("white"), (10,20,30,30))
        return pg.mask.from_surface(temp)

    def add_direction(self, key):
        """Add a pressed direction key on the direction stack."""
        if key in self.controls:
            direction = self.controls[key]
            if direction in self.direction_stack:
                self.direction_stack.remove(direction)
            self.direction_stack.append(direction)

    def pop_direction(self, key):
        """Pop a released key from the direction stack."""
        if key in self.controls:
            direction = self.controls[key]
            if direction in self.direction_stack:
                self.direction_stack.remove(direction)

    def collide_with_solid(self, cancel_knock=True):
        """Called from level when the player walks into a solid tile."""
        self.exact_position = self.old_position[:]
        self.rect.topleft = self.exact_position
        if cancel_knock:
            self.knock_state = False

    def got_hit(self, enemy):
        """Called on collision with enemy."""
        if not self.hit_state:
            damage = max(enemy.attack-self.defense, 1)
            self.health = max(self.health-damage, 0)
            self.hit_state = tools.Timer(50, 10)
            knock_dir = self.get_collision_direction(enemy)
            self.knock_state = (knock_dir, tools.Timer(100, 1))

    def check_death(self):
        """
        If player's health has dropped to zero set action_state to "death" and
        reset weapon attack if necessary.
        """
        if self.health == 0:
            self.action_state = "dead"
            self.equipped["weapon"].sprite.reset_attack()

    def get_collision_direction(self, other_sprite):
        """
        Find the direction the player will be knocked after colliding
        with an enemy.
        """
        dx = self.get_finite_difference(other_sprite, 0)
        dy = self.get_finite_difference(other_sprite, 1)
        abs_x, abs_y = abs(dx), abs(dy)
        if abs_x > abs_y:
            return "right" if dx > 0 else "left"
        else:
            return "front" if dy > 0 else "back"

    def get_finite_difference(self, other_sprite, index, delta=1):
        """
        Find the finite difference in area of mask collision with the
        rects position incremented and decremented in axis index by delta.
        """
        base_offset = [other_sprite.rect.x-self.rect.x,
                       other_sprite.rect.y-self.rect.y]
        offset_high = base_offset[:]
        offset_low = base_offset[:]
        offset_high[index] += delta
        offset_low[index] -= delta
        first_term = self.mask.overlap_area(other_sprite.mask, offset_high)
        second_term = self.mask.overlap_area(other_sprite.mask, offset_low)
        return first_term-second_term

    def attack(self):
        """
        Change attack flag to True if weapon is ready and add weapon.
        attack sprite to player sprite groups.
        """
        if self.action_state != "attack":
            weapon = self.equipped["weapon"].sprite
            if weapon.start_attack(self):
                self.action_state = "attack"
                weapon.add(self.groups())
                self.redraw = True

    def interact(self, interactables):
        """
        Check if the player is facing and close enough to an object that
        can be interacted with via the left-shift key.
        If so call that object's interact_with method.
        """
        vec = prepare.DIRECT_DICT[self.direction]
        move = vec[0]*5, vec[1]*5  #Currently hardcoded 5 pixel range.
        self.rect.move_ip(*move)
        for item in interactables:
            if pg.sprite.collide_mask(self, item):
                item.interact_with(self)
                break
        self.rect.move_ip(-move[0], -move[1])

    def check_states(self, now):
        """Change states when required."""
        attacking = self.action_state == "attack"
        if attacking and not self.equipped["weapon"].sprite.attacking:
            self.action_state = "normal"
            self.redraw = True
        if self.hit_state:
            self.hit_state.check_tick(now)
            if self.hit_state.done:
                self.hit_state = False
            self.redraw = True
        if self.knock_state:
            knock_timer = self.knock_state[1]
            knock_timer.check_tick(now)
            if knock_timer.done:
                self.knock_state = False

    def move(self):
        """Move the player if not attacking (or interupted some other way)."""
        if self.action_state != "attack" and self.direction_stack:
            self.direction = self.direction_stack[-1]
            vector = prepare.DIRECT_DICT[self.direction]
            self.exact_position[0] += self.speed*vector[0]
            self.exact_position[1] += self.speed*vector[1]
        if self.knock_state:
            vector = prepare.DIRECT_DICT[self.knock_state[0]]
            self.exact_position[0] += KNOCK_SPEED*vector[0]
            self.exact_position[1] += KNOCK_SPEED*vector[1]

    def adjust_frames(self, now):
        """Update the sprite's animation as needed."""
        if self.action_state != "dead":
            animation_dict = self.all_animations[bool(self.hit_state)]
            animation = animation_dict[self.action_state][self.direction]
        else:
            animation = self.death_anim
            self.redraw = True
        if self.direction_stack or self.hit_state or self.redraw:
            self.image = animation.get_next_frame(now)
        self.redraw = False

    def update(self, now, *args):
        """Updates our player appropriately every frame."""
        self.old_position = self.exact_position[:]
        self.check_death()
        if self.action_state != "dead":
            self.check_states(now)
            self.move()
        self.adjust_frames(now)
        self.rect.topleft = self.exact_position
