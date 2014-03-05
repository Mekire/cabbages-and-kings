"""
This module contains the primary class for the player.
"""

import os
import pygame as pg

from . import equips,shadow
from .. import prepare


COLOR_KEY = (255,0,255)

PLAYER_SIZE = (50,50)

DIRECTIONS = ["front", "back", "left", "right"]

DIRECT_DICT = {"front" : ( 0, 1),
               "back"  : ( 0,-1),
               "left"  : (-1, 0),
               "right" : ( 1, 0)}

DRAW_ORDER = {"front" : ["body", "head", "weapon", "armleg", "shield"],
              "back"  : ["shield", "armleg", "weapon", "body", "head"],
              "left"  : ["shield", "body", "head", "weapon", "armleg"],
              "right" : ["weapon", "body", "head", "armleg", "shield"]}

DRAW_ATTACK_ORDER = {"front" : ["shield", "body", "head", "weapon", "armleg"],
                     "back"  : ["armleg", "weapon", "body", "head", "shield"],
                     "left"  : ["shield", "body", "head", "weapon", "armleg"],
                     "right" : ["weapon", "body", "head", "armleg", "shield"]}


class Player(pg.sprite.Sprite):
    """A class to represent our main protagonist."""
    def __init__(self, rect, speed, direction="back"):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(rect)
        self.exact_position = list(self.rect.topleft)
        self.old_position = self.exact_position[:]
        self.speed = speed
        self.direction = direction
        self.old_direction = None #The Players previous direction every frame.
        self.direction_stack = [] #Held keys in the order they were pressed.
        self.redraw = False #Force redraw if needed.
        self.controls = self.set_controls()
        self.inventory = equips.make_all_equips()
        self.equipped = self.set_equips()
        self.image_dict = self.make_images()
        self.attack_image_dict = self.make_images(True, DRAW_ATTACK_ORDER)
        self.frame  = 0
        self.animate_timer = 0.0
        self.animate_fps = 7.0
        self.image = None
        self.mask = self.make_mask()
        self.attack_image = None
        self.walk_frames = self.image_dict[self.direction]
        self.attack_frames = self.attack_image_dict[self.direction]
        self.adjust_images()
        self.flags = self.initialize_flags()
        self.shadow = shadow.Shadow((40,20))

    def make_mask(self):
        """Create a collision mask for the player."""
        temp = pg.Surface((PLAYER_SIZE)).convert_alpha()
        temp.fill((0,0,0,0))
        temp.fill(pg.Color("white"), (10,20,30,30))
        return pg.mask.from_surface(temp)

    def initialize_flags(self):
        """Sets flags to the default state of the player."""
        flags = {"attacking" : False,
                 "knocked" : False,
                 "pushing" : False,
                 "invincible" : False}
        return flags

    def set_controls(self):
        """A class for linking directions to controls. Currently hardcoded.
        will possibly go elsewhere eventually if controls are made
        customizable."""
        controls = {pg.K_DOWN  : "front",
                    pg.K_UP    : "back",
                    pg.K_LEFT  : "left",
                    pg.K_RIGHT : "right"}
        return controls

    def set_equips(self):
        """Set the equips the player is wearing.  Currently hardcoded.
        Eventually it will load from player data or revert to defaults."""
        equips = {}
        equips = {"head" : self.inventory["head"]["none"],
                  "body" : self.inventory["body"]["chain"],
                  "shield" : self.inventory["shield"]["tin"],
##                  "shield" : None,
                  "armleg" : self.inventory["armleg"]["normal"],
                  "weapon" : self.inventory["weapon"]["pitch"]}
        return equips

    def make_images(self,attack=False,order=DRAW_ORDER):
        """Create the player's images any time he changes equipment."""
        base = pg.Surface(PLAYER_SIZE).convert()
        base.set_colorkey(COLOR_KEY)
        base.fill(COLOR_KEY)
        images = {}
        for direction in DIRECTIONS:
            frames = []
            for frame in (0,1):
                image = base.copy()
                for part in order[direction]:
                    if self.equipped[part]:
                        if attack:
                            get_part = self.get_attack_part_image
                        else:
                            get_part = self.get_part_image
                        blitting = get_part(direction,part,frame)
                        if blitting:
                            image.blit(blitting,(0,0))
                frames.append(image)
            images[direction] = frames
        return images

    def get_part_image(self,direction,part,frame):
        """Get the correct part image based on player direction and frame."""
        if part=="armleg" and direction=="right" and self.equipped["shield"]:
            to_blit = self.equipped[part].images["right_with_shield"]
        else:
            to_blit = self.equipped[part].images[direction]
        try:
            return to_blit[frame]
        except TypeError:
            return to_blit

    def get_attack_part_image(self,direction,part,frame):
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

    def adjust_images(self):
        """Update the sprites walk_frames as the sprite's direction changes."""
        if self.direction_stack:
            self.direction = self.direction_stack[-1]
        if self.direction != self.old_direction:
            self.walk_frames = self.image_dict[self.direction]
            self.attack_frames = self.attack_image_dict[self.direction]
            self.old_direction = self.direction
            self.redraw = True
        self.change_frame()

    def change_frame(self):
        """Update the sprite's animation as needed."""
        time_now = pg.time.get_ticks()
        if self.redraw or time_now-self.animate_timer > 1000.0/self.animate_fps:
            if self.direction_stack:
                self.frame = (self.frame+1)%len(self.walk_frames)
                self.image = self.walk_frames[self.frame]
                self.attack_image = self.attack_frames[self.frame]
            self.animate_timer = time_now
        if not self.image:
            self.image = self.walk_frames[self.frame]
            self.attack_image = self.attack_frames[self.frame]
        self.redraw = False

    def add_direction(self,key):
        """Add a pressed direction key on the direction stack."""
        if key in self.controls:
            direction = self.controls[key]
            if direction in self.direction_stack:
                self.direction_stack.remove(direction)
            self.direction_stack.append(direction)

    def pop_direction(self,key):
        """Pop a released key from the direction stack."""
        if key in self.controls:
            direction = self.controls[key]
            if direction in self.direction_stack:
                self.direction_stack.remove(direction)

    def attack(self):
        """Change attack flag to True if weapon is ready."""
        if not self.flags["attacking"] and self.equipped["weapon"]:
            self.flags["attacking"] = self.equipped["weapon"].start_attack()

    def update(self,now,dt):
        """Updates our player appropriately every frame."""
        if not self.flags["attacking"]:
            self.move(dt)
        else:
            self.equipped["weapon"].attack(self,now)
        self.rect.topleft = self.exact_position

    def move(self,dt):
        """Move the player if not attacking (or interupted some other way)."""
        self.adjust_images()
        self.old_position = self.exact_position[:]
        if self.direction_stack:
            vector = DIRECT_DICT[self.direction_stack[-1]]
            self.exact_position[0] += self.speed*vector[0]*dt
            self.exact_position[1] += self.speed*vector[1]*dt

    def draw(self,surface):
        """Draw the appropriate frames to the target surface."""
        if self.flags["attacking"]:
            surface.blit(self.attack_image,self.rect)
            draw_attack = self.equipped["weapon"].draw_attack
            draw_attack(surface,self.direction)
        else:
            surface.blit(self.image,self.rect)

    def collide_with_solid(self):
        """Called from level when the player walks into a solid tile."""
        self.exact_position = self.old_position
        self.rect.topleft = self.exact_position
