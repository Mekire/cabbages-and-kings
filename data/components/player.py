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
KNOCK_SPEED = 750  #Pixels per second.


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


class Player(pg.sprite.Sprite, _ImageProcessing):
    """A class to represent our main protagonist."""
    def __init__(self, rect, direction="front", data=prepare.DEFAULT_PLAYER):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(rect)
        self.exact_position = list(self.rect.topleft)
        self.old_position = self.exact_position[:]
        self.speed = 190  ##Calculate from gear later.
        self.direction = direction
        self.direction_stack = [] #Held keys in the order they were pressed.
        self.controls = prepare.DEFAULT_CONTROLS
        self.set_player_data(data)###
        self.mask = self.make_mask()
        self.all_animations = self.make_all_animations()
        self.image = None
        self.action_state = "normal"
        self.hit_state = False  #When true hit_state is a tools.Timer instance.
        self.knock_state = False #(direction, tools.Timer()) tuple when true.
        self.redraw = True
        self.shadow = shadow.Shadow((40,20), self.rect)
        self.health = prepare.MAX_HEALTH

    def set_player_data(self, player_data):
        """Set required stats based on player data."""
        self.name = player_data["name"]
##        self.inventory = equips.make_equips(player_data["gear"])
        self.inventory = equips.make_all_equips() ###
        self.inventory["money"] = player_data["money"]
        self.inventory["keys"] = player_data["keys"]
##        self.equipped = self.set_equips(player_data["equipped"])
        self.equipped = self.set_equips_random() ###

    def set_equips(self, equipped):
        """
        Set the equips the player is wearing.  Currently hardcoded.
        Eventually it will load from player data or revert to defaults.
        """
        equipped = {}
        for part,gear in equipped.items():
            equipped[part] = self.inventory[part][gear]
        return equipped

    def set_equips_random(self):
        equipped = {}
        for part in equips.EQUIP_DICT:
            equipped[part] = random.choice(self.inventory[part].values())
        return equipped

    def make_mask(self):
        """Create a collision mask for the player."""
        temp = pg.Surface((prepare.CELL_SIZE)).convert_alpha()
        temp.fill((0,0,0,0))
        temp.fill(pg.Color("white"), (10,20,30,30))
        return pg.mask.from_surface(temp)

    def adjust_frames(self, now):
        """Update the sprite's animation as needed."""
        animation_dict = self.all_animations[bool(self.hit_state)]
        animation = animation_dict[self.action_state][self.direction]
        if self.direction_stack or self.hit_state or self.redraw:
            self.image = animation.get_next_frame(now)
        self.redraw = False

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

    def collide_with_solid(self):
        """Called from level when the player walks into a solid tile."""
        self.exact_position = self.old_position
        self.rect.topleft = self.exact_position
        self.knock_state = False

    def got_hit(self, enemy):
        """Called on collision with enemy."""
        if not self.hit_state:
            self.health = max(self.health-enemy.attack, 0)
            self.hit_state = tools.Timer(50, 10)
            knock_dir = self.get_collision_direction(enemy)
            self.knock_state = (knock_dir, tools.Timer(100, 1))

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
        """Change attack flag to True if weapon is ready."""
        if self.action_state != "attack":
            if self.equipped["weapon"].start_attack():
                self.action_state = "attack"
                self.redraw = True

    def check_states(self, now):
        """Change states when required."""
        attacking = self.action_state == "attack"
        if attacking and not self.equipped["weapon"].attacking:
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

    def update(self, now, dt):
        """Updates our player appropriately every frame."""
        self.check_states(now)
        self.move(dt)
        self.adjust_frames(now)
        if self.action_state == "attack":
            self.equipped["weapon"].attack(self, now)
        self.rect.topleft = self.exact_position

    def move(self, dt):
        """Move the player if not attacking (or interupted some other way)."""
        self.old_position = self.exact_position[:]
        if self.action_state != "attack" and self.direction_stack:
            self.direction = self.direction_stack[-1]
            vector = prepare.DIRECT_DICT[self.direction]
            self.exact_position[0] += self.speed*vector[0]*dt
            self.exact_position[1] += self.speed*vector[1]*dt
        if self.knock_state:
            vector = prepare.DIRECT_DICT[self.knock_state[0]]
            self.exact_position[0] += KNOCK_SPEED*vector[0]*dt
            self.exact_position[1] += KNOCK_SPEED*vector[1]*dt

    def draw(self, surface):
        """Draw the appropriate frames to the target surface."""
        if self.action_state == "attack":
            self.equipped["weapon"].draw_attack(surface, self.direction)
        surface.blit(self.image, self.rect)
