"""
Contains prototype and specific classes for all types of equipable gear.
"""

import os
import pygame as pg

from .. import prepare, tools


class _Equipment(object):
    """A base prototype class for all equipment."""
    def __init__(self, stats, sheet_name, sheet_location, arrange="standard"):
        self.defense = stats[0]
        self.strength = stats[1]
        self.speed = stats[2]
        self.attack_images = "normal"
        sheet = prepare.GFX["equips"][sheet_name]
        if arrange == "attack":
            step = prepare.CELL_SIZE[0]*2
            start = (sheet_location[0]+prepare.CELL_SIZE[0], sheet_location[1])
            self.images = self.get_images(sheet, sheet_location, step)
            self.attack_images = self.get_images(sheet, start, step)
        elif arrange == "standard":
            self.images = self.get_images(sheet, sheet_location)
        else:
            self.get_images(sheet, sheet_location)

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
        _Equipment.__init__(self, stats, "heads", (0,0), "attack")
        self.title = "No headgear"
        self.description = "You should really find a helmet."
        self.vision_impair = None


class Helm(_Equipment):
    """A minor improvement on having no helmet."""
    def __init__(self):
        stats = (1, 0, 0)
        _Equipment.__init__(self, stats, "heads", (0,50), "attack")
        self.title = "Helmet"
        self.description = ("Average defense, average visibility. "
                            "Just pretty average.")
        self.vision_impair = None


class Sader(_Equipment):
    """Very high defense, but the vision impairment is a tough tradeoff."""
    def __init__(self):
        stats = (3, 0, 0)
        _Equipment.__init__(self, stats, "heads", (0,100), "attack")
        self.title = "Crusader Helm"
        self.description = ("Great for protection, but limited visibility... "
                            "seriously.")
        self.vision_impair = self.make_impair()

    def make_impair(self):
        pass


class Diver(_Equipment):
    """Impaired vision is the price one pays for underwater breathing."""
    def __init__(self):
        stats = (1, 0, 0)
        _Equipment.__init__(self, stats, "heads", (0,150), "attack")
        self.title = "Helm of the Mariner"
        self.description = ("Underwater breathing, and you can almost see "
                            "where you're going. Amazing.")
        self.vision_impair = self.make_impair()

    def make_impair(self):
        pass


class TopGoggles(_Equipment):
    """A novelty hat in which form seems to completely ignore function."""
    def __init__(self):
        stats = (1, 0, 0)
        _Equipment.__init__(self, stats, "heads", (0,200), "attack")
        self.title = "Begoggled Tophat"
        self.description = ("Wait, I don't get it.  Are there holes in the "
                            "tophat underneath the goggles?")
        self.vision_impair = self.make_impair()

    def make_impair(self):
        pass


#Specific types of body armor
class Cloth(_Equipment):
    """At least he doesn't start naked. Be thankful."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, stats, "bodies", (0,0))
        self.title = "Peasant Clothes"
        self.description = ("Leaves something to be desired "
                            "in the defense department.")


class ChainMail(_Equipment):
    """Higher defense at the cost of speed."""
    def __init__(self):
        stats = (3, 0, -50)
        _Equipment.__init__(self, stats, "bodies", (200,0))
        self.title = "Chainmail"
        self.description = ("What it has in defense it "
                            "lacks in freedom of movement.")


#Specific types of shields
class TinShield(_Equipment):
    """The first shield. Should only deflect basic projectiles."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, stats, "shields", (0,0), "attack")
        self.title = "Tin Shield"
        self.description = "Only slightly better than having no shield at all."
        self.deflect = 1


#Specific arms and legs
class ArmsLegs(_Equipment):
    """Starting shoes.  No gloves."""
    def __init__(self):
        stats = (0, 0, 0)
        _Equipment.__init__(self, stats, "armslegs", (0,0), "other")
        self.title = "Basic Shoes"
        self.description = "Just your basic shoes... Nothing special."

    def get_images(self, sheet, sheet_location):
        """
        Slice images from the sheet with respect to a standard layout.
        Note that an exception must be made for right facing while holding a
        shield.
        """
        frames = tools.strip_from_sheet(sheet, sheet_location,
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
    def __init__(self,stats,sheet_location):
        _Equipment.__init__(self, stats, "weapons", sheet_location, "other")
        self.attack_images = None
        self.anims = None
        self.anim_rects = None
        self.anim_image = None
        self.attacking = False
        self.delay_timer = tools.Timer(300)

    def get_images(self, sheet, sheet_location):
        """Get the weapon images assuming a standard layout."""
        frames = tools.strip_from_sheet(sheet, sheet_location,
                                        prepare.CELL_SIZE, 8)
        self.images = {}
        for i,direction in enumerate(prepare.DIRECTIONS):
            self.images[direction] = frames[2*i:2*i+2]

    def start_attack(self):
        """
        Checks the time to see if the weapon's after attack delay has
        elapsed.
        """
        if self.delay_timer.check_tick(pg.time.get_ticks()):
            self.attacking = True
            return True

    def attack(self, player, now):
        """
        Called from the player's update method if the attacking flag
        is set.
        """
        self.anim = self.anims[player.direction]
        if self.anim.timer is None:
            self.sound.play()
        self.anim_image = self.anim.get_next_frame(now)
        if self.anim.done:
            self.reset_attack()
        if self.attacking:
            self.get_attack_position(player.rect, player.direction)

    def draw_attack(self, surface, direction):
        """Called from the player's draw method if the attacing flag is set."""
        rect = self.anim_rects[direction][self.anim.frame]
        surface.blit(self.anim_image, rect)

    def get_attack_position(self, player_rect, direction):
        """
        Find the location of the attack rect based on the player's location
        and direction.
        """
        set_direction = {"back"  : ("midbottom", player_rect.midtop),
                         "front" : ("midtop", player_rect.midbottom),
                         "right" : ("midleft", player_rect.midright),
                         "left"  : ("midright", player_rect.midleft)}
        rect = self.anim_rects[direction][self.anim.frame]
        attribute, value = set_direction[direction]
        setattr(rect, attribute, value)

    def reset_attack(self):
        """
        Reset the necessary variables to the pre-attack state.
        """
        self.attacking = False
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
        stats = (0, 1, 0)
        _Weapon.__init__(self, stats, (0,0))
        self.title = "Angry Mob Pitchfork"
        self.description = "Should vanquish all foes... Eventually."
        self.sound = prepare.SFX["boing"]
        self.anims, self.anim_rects = self.get_attack_info((0,0), (44,20), 2)


class Labrys(_Weapon):
    """
    A slightly more powerful weapon than the pitchfork. May gain the ability
    to chop down certain trees/obstacles.
    """
    def __init__(self):
        stats = (0, 2, 0)
        _Weapon.__init__(self, stats, (0,50))
        self.title = "Mini-Labrys"
        self.description = "Foliage beware !"
        self.sound = prepare.SFX["whoosh"]
        self.anims, self.anim_rects = self.get_attack_info((0,20), (30,50), 3)


#Organize all equips into a nested dictionary.
_HEADS = {"none" : NoHeadGear,
          "helm" : Helm,
          "diver" : Diver,
          "goggles" : TopGoggles,
          "sader" : Sader}

_BODIES = {"cloth" : Cloth,
           "chain" : ChainMail}

_SHIELDS = {"tin" : TinShield}

_ARMS_LEGS = {"normal" : ArmsLegs}

_WEAPONS = {"pitch" : PitchFork,
            "labrys" : Labrys}

EQUIP_DICT = {"head" : _HEADS,
              "body" : _BODIES,
              "shield" : _SHIELDS,
              "armleg" : _ARMS_LEGS,
              "weapon" : _WEAPONS}


def make_all_equips():
    """Return a dict with instances of all equips."""
    instances = {}
    for category in EQUIP_DICT:
        instances[category] = {}
        for part in EQUIP_DICT[category]:
            instances[category][part] = EQUIP_DICT[category][part]()
    return instances
