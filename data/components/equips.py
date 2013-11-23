import os
import pygame as pg

from .. import prepare,tools


CELL_SIZE = (50,50)


class _Equipment(object):
    """A base prototype class for all equipment."""
    def __init__(self,stats,sheet_name,sheet_location,arrange="standard"):
        self.defense = stats[0]
        self.strength = stats[1]
        self.speed = stats[2]
        self.attack_images = "normal"
        sheet = prepare.GFX["equips"][sheet_name]
        if arrange == "attack":
            step = CELL_SIZE[0]*2
            start = (sheet_location[0]+CELL_SIZE[0],sheet_location[1])
            self.images = self.get_images(sheet,sheet_location,step)
            self.attack_images = self.get_images(sheet,start,step)
        elif arrange == "standard":
            self.images = self.get_images(sheet,sheet_location)
        else:
            self.get_images(sheet,sheet_location)

    def get_images(self,sheet,coords,step=CELL_SIZE[0]):
        """Rip frames from sheet and place them in a dict by direction."""
        images = {}
        for i,direction in enumerate(["front","back","left","right"]):
            location = coords[0]+step*i,coords[1]
            images[direction] = sheet.subsurface(pg.Rect(location,CELL_SIZE))
        return images


#Specific types of headgear
class NoHeadGear(_Equipment):
    def __init__(self):
        stats = (0,0,0)
        _Equipment.__init__(self,stats,"heads",(0,0),"attack")
        self.title = "No headgear"
        self.description = "You should really find a helmet."
        self.vision_impair = None


class Helm(_Equipment):
    def __init__(self):
        stats = (1,0,0)
        _Equipment.__init__(self,stats,"heads",(0,50),"attack")
        self.title = "Helmet"
        self.description = ("Average defense, average visibility. "
                            "Just pretty average.")
        self.vision_impair = None


class Sader(_Equipment):
    def __init__(self):
        stats = (3,0,0)
        _Equipment.__init__(self,stats,"heads",(0,100),"attack")
        self.title = "Crusader Helm"
        self.description = ("Great for protection, but limited visibility... "
                            "seriously.")
        self.vision_impair = self.make_impair()

    def make_impair(self):
        pass


class Diver(_Equipment):
    def __init__(self):
        stats = (1,0,0)
        _Equipment.__init__(self,stats,"heads",(0,150),"attack")
        self.title = "Helm of the Mariner"
        self.description = ("Underwater breathing, and you can almost see "
                            "where you're going. Amazing.")
        self.vision_impair = self.make_impair()

    def make_impair(self):
        pass


class TopGoggles(_Equipment):
    def __init__(self):
        stats = (1,0,0)
        _Equipment.__init__(self,stats,"heads",(0,200),"attack")
        self.title = "Begoggled Tophat"
        self.description = ("Wait, I don't get it.  Are there holes in the "
                            "tophat underneath the goggles?")
        self.vision_impair = self.make_impair()

    def make_impair(self):
        pass


#Specific types of body armor
class Cloth(_Equipment):
    def __init__(self):
        stats = (0,0,0)
        _Equipment.__init__(self,stats,"bodies",(0,0))
        self.title = "Peasant Clothes"
        self.description = ("Leaves something to be desired "
                            "in the defense department.")


class ChainMail(_Equipment):
    def __init__(self):
        stats = (3,0,-50)
        _Equipment.__init__(self,stats,"bodies",(200,0))
        self.title = "Chainmail"
        self.description = ("What it has in defense it "
                            "lacks in freedom of movement.")


#Specific types of shields
class TinShield(_Equipment):
    def __init__(self):
        stats = (0,0,0)
        _Equipment.__init__(self,stats,"shields",(0,0),"attack")
        self.title = "Tin Shield"
        self.description = "Only slightly better than having no shield at all."
        self.deflect = 1


#Specific arms and legs
class ArmsLegs(_Equipment):
    def __init__(self):
        stats = (0,0,0)
        _Equipment.__init__(self,stats,"armslegs",(0,0),"other")
        self.title = "Basic Shoes"
        self.description = "Just your basic shoes... Nothing special."

    def get_images(self,sheet,sheet_location):
        frames = tools.strip_from_sheet(sheet,sheet_location,CELL_SIZE,18)
        self.images = {}
        self.attack_images = {}
        self.images["front"] = frames[:2]
        self.attack_images["front"] = frames[2:4]
        self.images["back"] = frames[4:6]
        self.attack_images["back"] = frames[6:8]
        self.images["left"] = frames[8:10]
        self.attack_images["left"] = frames[10:12]
        self.images["right"] = frames[12:14]
        self.attack_images["right"] = frames[14:16]
        self.images["right_with_shield"] = frames[16:]


#Weapons follow.
class _Weapon(_Equipment):
    """Prototype class for weapons."""
    def __init__(self,stats,sheet_location):
        _Equipment.__init__(self,stats,"weapons",sheet_location,"other")
        self.attack_images = None

    def get_images(self,sheet,sheet_location):
        frames = tools.strip_from_sheet(sheet,sheet_location,CELL_SIZE,8)
        self.images = {}
        self.images["front"] = frames[:2]
        self.images["back"] = frames[2:4]
        self.images["left"] = frames[4:6]
        self.images["right"] = frames[6:]


class PitchFork(_Weapon):
    def __init__(self):
        stats = (0,1,0)
        _Weapon.__init__(self,stats,(0,0))
        self.title = "Angry Mob Pitchfork"
        self.description = "Should vanquish all foes... Eventually."


class Labrys(_Weapon):
    def __init__(self):
        stats = (0,2,0)
        _Weapon.__init__(self,stats,(0,50))
        self.title = "Mini-Labrys"
        self.description = "Foliage beware !"


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


