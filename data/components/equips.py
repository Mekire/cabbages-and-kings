"""
Contains prototype and specific classes for all types of equipable gear.
"""

import os
import pygame as pg

from .. import prepare, tools


DISPLAY_SHEET = prepare.GFX["equips"]["geardisplay"]


class _Equipment(object):
    """A base prototype class for all equipment."""
    def __init__(self, name, stats, sheet, sheet_pos, arrange="standard"):
        self.name = name
        self.stats = self.defense, self.strength, self.speed = stats
        self.sheet = sheet
        self.sort_stat = self.defense
        self.attack_images = "normal"
        sheet = prepare.GFX["equips"][sheet]
        if arrange == "attack":
            step = prepare.CELL_SIZE[0]*2
            start = (sheet_pos[0]+prepare.CELL_SIZE[0], sheet_pos[1])
            self.images = self.get_images(sheet, sheet_pos, step)
            self.attack_images = self.get_images(sheet, start, step)
        elif arrange == "standard":
            self.images = self.get_images(sheet, sheet_pos)
        else:
            self.get_images(sheet, sheet_pos)

    def get_images(self, sheet, coords, step=prepare.CELL_SIZE[0]):
        """Rip frames from sheet and place them in a dict by direction."""
        images = {}
        for i,direction in enumerate(["front","back","left","right"]):
            location = coords[0]+step*i, coords[1]
            images[direction] = sheet.subsurface(pg.Rect(location,
                                                         prepare.CELL_SIZE))
        return images


#Specific types of headgear
class NoHeadGear(_Equipment):
    """The initial headgearless player."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, "none", stats, "head", (0,0), "attack")
        self.title = "No Headgear"
        self.descript = ["You should really find a helmet."]
        self.vision_impair = None
        self.display = DISPLAY_SHEET.subsurface(0, 150, 50, 50)


class Helm(_Equipment):
    """A minor improvement on having no helmet."""
    def __init__(self):
        stats = (1, 0, 0)
        _Equipment.__init__(self, "helm", stats, "head", (0,50), "attack")
        self.title = "Helm"
        self.descript = ["Average defense, average visibility.",
                         "Just pretty average."]
        self.vision_impair = None
        self.display = DISPLAY_SHEET.subsurface(50, 150, 50, 50)


class Sader(_Equipment):
    """Very high defense, but the vision impairment is a tough tradeoff."""
    def __init__(self):
        stats = (3, 0, 0)
        _Equipment.__init__(self, "sader", stats, "head", (0,100), "attack")
        self.title = "Crusader Helm"
        self.descript = ["Great for protection,",
                         "but limited visibility... Seriously."]
        self.vision_impair = self.make_impair()
        self.display = DISPLAY_SHEET.subsurface(100, 150, 50, 50)

    def make_impair(self):
        pass


class Diver(_Equipment):
    """Impaired vision is the price one pays for underwater breathing."""
    def __init__(self):
        stats = (1, 0, 0)
        _Equipment.__init__(self, "diver", stats, "head", (0,150), "attack")
        self.title = "Helm of the Mariner"
        self.descript = ["Underwater breathing, and you can almost see",
                         "where you're going. Amazing."]
        self.vision_impair = self.make_impair()
        self.display = DISPLAY_SHEET.subsurface(150, 150, 50, 50)

    def make_impair(self):
        pass


class TopGoggles(_Equipment):
    """A novelty hat in which form seems to completely ignore function."""
    def __init__(self):
        stats = (1, 0, 0)
        _Equipment.__init__(self, "goggles", stats, "head", (0,200), "attack")
        self.title = "Begoggled Tophat"
        self.descript = ["Wait, I don't get it.  Are there holes in the",
                         "tophat underneath the goggles?"]
        self.vision_impair = self.make_impair()
        self.display = DISPLAY_SHEET.subsurface(200, 150, 50, 50)

    def make_impair(self):
        pass


#Specific types of body armor
class Cloth(_Equipment):
    """At least he doesn't start naked. Be thankful."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, "cloth", stats, "body", (0,0))
        self.title = "Peasant Clothes"
        self.descript = ["Leaves something to be desired",
                         "in the defense department."]
        self.display = DISPLAY_SHEET.subsurface(0, 300, 50, 50)


class ChainMail(_Equipment):
    """Higher defense at the cost of speed."""
    def __init__(self):
        stats = (3, 0, -0.7)
        _Equipment.__init__(self, "chain", stats, "body", (200,0))
        self.title = "Chainmail"
        self.descript = ["What it has in defense,",
                         "it lacks in freedom of movement."]
        self.display = DISPLAY_SHEET.subsurface(50, 300, 50, 50)


#Specific types of shields
class NoShield(_Equipment):
    def __init__(self):
        self.name = "none"
        self.title = "No Shield"
        self.descript = ["Those arrows aren't going to block themselves."]
        self.stats = self.defense, self.strength, self.speed = (0, 0, 0)
        self.images = None
        self.attack_images = None
        self.deflect = 0
        self.display = DISPLAY_SHEET.subsurface(350, 450, 50, 50)
        self.sort_stat = self.deflect


class TinShield(_Equipment):
    """The first shield. Should only deflect basic projectiles."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, "tin", stats, "shield", (0,0), "attack")
        self.title = "Tin Shield"
        self.descript = ["Only slightly better than",
                         "having no shield at all."]
        self.deflect = 1
        self.display = DISPLAY_SHEET.subsurface(0, 450, 50, 50)
        self.sort_stat = self.deflect


#Specific arms and legs
class ArmsLegs(_Equipment):
    """Starting shoes.  No gloves."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, "normal", stats, "armleg", (0,0), "other")
        self.title = "Basic Shoes"
        self.descript = ["Just your basic shoes... Nothing special."]
        self.display = DISPLAY_SHEET.subsurface(0, 600, 50, 50)

    def get_images(self, sheet, sheet_pos):
        """
        Slice images from the sheet with respect to a standard layout.
        Note that an exception must be made for right facing while holding a
        shield.
        """
        frames = tools.strip_from_sheet(sheet, sheet_pos,
                                        prepare.CELL_SIZE, 18)
        self.images = {}
        self.attack_images = {}
        for i,direction in enumerate(prepare.DIRECTIONS):
            self.images[direction] = frames[4*i:4*i+2]
            self.attack_images[direction] = frames[4*i+2:4*i+4]
        self.images["right_with_shield"] = frames[16:]


#Weapons follow.
class _Weapon(_Equipment):
    """Prototype class for weapons."""
    def __init__(self, name, stats, sheet_pos):
        _Equipment.__init__(self, name, stats, "weapon", sheet_pos, "other")
        self.attack_images = None
        self.sort_stat = self.strength
        self.sprite = None

    def get_images(self, sheet, sheet_pos):
        """Get the weapon images assuming a standard layout."""
        frames = tools.strip_from_sheet(sheet, sheet_pos, prepare.CELL_SIZE, 8)
        self.images = {}
        for i,direction in enumerate(prepare.DIRECTIONS):
            self.images[direction] = frames[2*i:2*i+2]


class AttackSprite(pg.sprite.Sprite):
    def __init__(self, sound, *attack_info):
        pg.sprite.Sprite.__init__(self)
        self.sound = sound
        self.anims, self.anim_rects = self.get_attack_info(*attack_info)
        self.anim = None
        self.image = None
        self.rect = None
        self.player = None
        self.attacking = False
        self.delay_timer = tools.Timer(300)
        self.frame_speed = [0, 0]

    def start_attack(self, player):
        """
        Checks the time to see if the weapon's after attack delay has
        elapsed.
        """
        if self.delay_timer.check_tick(pg.time.get_ticks()):
            self.attacking = True
            self.player = player
            return True

    def update(self, now, *args):
        """Updated in the Level objects update phase."""
        self.frame_speed = self.player.frame_speed
        self.anim = self.anims[self.player.direction]
        if self.anim.timer is None:
            self.sound.play()
        self.image = self.anim.get_next_frame(now)
        self.get_attack_position(self.player.rect, self.player.direction)
        if self.anim.done:
            self.reset_attack()

    def get_attack_position(self, player_rect, direction):
        """
        Find the location of the attack rect based on the player's location
        and direction.
        """
        set_direction = {"back"  : ("midbottom", player_rect.midtop),
                         "front" : ("midtop", player_rect.midbottom),
                         "right" : ("midleft", player_rect.midright),
                         "left"  : ("midright", player_rect.midleft)}
        self.rect = self.anim_rects[direction][self.anim.frame]
        attribute, value = set_direction[direction]
        setattr(self.rect, attribute, value)

    def reset_attack(self):
        """
        Reset the necessary variables to the pre-attack state.
        """
        self.attacking = False
        self.kill()
        if self.anim:
            self.anim.reset()

    def get_attack_info(self, start, size, columns, fps=15.0):
        """Get attack frames from the attack sheet."""
        sheet = prepare.GFX["equips"]["attacks1"]
        raw_frames = tools.strip_from_sheet(sheet, start, size, columns)
        anims = {}
        rects = {}
        for i,direct in enumerate(["right", "back", "left", "front"]):
            frames = [pg.transform.rotate(pic, i*90) for pic in raw_frames]
            anims[direct] = tools.Anim(frames, fps, 1)
            rects[direct] = [pic.get_rect() for pic in frames]
        return anims, rects


class PitchFork(_Weapon):
    """The first weapon our player will use. Very unimpressive."""
    def __init__(self):
        stats = (0, 2, 0)
        _Weapon.__init__(self, "pitch", stats, (0,0))
        self.title = "Angry Mob Pitchfork"
        self.descript = ["Should vanquish all foes... Eventually."]
        self.display = DISPLAY_SHEET.subsurface((50,0,50,50))
        self.sprite = AttackSprite(prepare.SFX["boing"], (0,0), (44,20), 2)


class Labrys(_Weapon):
    """
    A slightly more powerful weapon than the pitchfork. May gain the ability
    to chop down certain trees/obstacles.
    """
    def __init__(self):
        stats = (0, 3, 0)
        _Weapon.__init__(self, "labrys", stats, (0,50))
        self.title = "Mini-Labrys"
        self.descript = ["Foliage beware !"]
        self.display = DISPLAY_SHEET.subsurface(((0,0), prepare.CELL_SIZE))
        self.sprite = AttackSprite(prepare.SFX["whoosh"], (0,20), (30,50), 3)
        #Left frames need to be vertically flipped.
        left_frames = self.sprite.anims["left"].frames
        lefts = [pg.transform.flip(frame,0,1) for frame in left_frames]
        self.sprite.anims["left"] = tools.Anim(lefts, 15.0, 1)


#Organize all equips into a nested dictionary.
_HEADS = {"none" : NoHeadGear,
          "helm" : Helm,
          "diver" : Diver,
          "goggles" : TopGoggles,
          "sader" : Sader}

_BODIES = {"cloth" : Cloth,
           "chain" : ChainMail}

_SHIELDS = {"none" : NoShield,
            "tin" : TinShield}

_ARMS_LEGS = {"normal" : ArmsLegs}

_WEAPONS = {"pitch" : PitchFork,
            "labrys" : Labrys}

EQUIP_DICT = {"head" : _HEADS,
              "body" : _BODIES,
              "shield" : _SHIELDS,
              "armleg" : _ARMS_LEGS,
              "weapon" : _WEAPONS}


def make_equips(equips):
    """
    Creates instances of all equips passed in.
    """
    instances = {}
    for category in EQUIP_DICT:
        instances[category] = {}
        for part in equips[category]:
            instances[category][part] = EQUIP_DICT[category][part]()
    return instances


def make_all_equips():
    return make_equips(EQUIP_DICT)
