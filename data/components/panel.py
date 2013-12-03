import pygame as pg

from .. import map_prepare


DIRECTION = {"RIGHT" : 1,
             "LEFT" : -1}

class PalletPanel(object):
    def __init__(self):#select_function,scroll_function):
        self.rect = pg.Rect(-298,50,400,600)
        self.pull_image = map_prepare.GFX["misc"]["pull"]
        self.pull_rect = self.pull_image.get_rect(left=self.rect.right,y=200)
        self.right_arrows = map_prepare.GFX["misc"]["arrows"]
        self.left_arrows = pg.transform.flip(self.right_arrows,True,False)
        self.arrow_rect = self.right_arrows.get_rect()
        self.arrow_rect.topleft = self.pull_rect.move(3,121).topleft
        self.visible = False
        self.scrolling = False
        self.scroll_direction = "RIGHT"
        self.scroll_speed = 800

    def update(self,surface,pallet,dt):
        image = map_prepare.GFX["mapsheets"][pallet]
        if self.visible:
            if self.scrolling:
                self.do_scroll(dt)
            surface.fill((255,255,255),self.rect.inflate(4,4))
            surface.fill((40,40,40),self.rect)
            surface.blit(image,self.rect)
        surface.blit(self.pull_image, self.pull_rect)
        if self.scroll_direction == "RIGHT":
            surface.blit(self.right_arrows,self.arrow_rect)
        else:
            surface.blit(self.left_arrows,self.arrow_rect)

    def check_event(self,event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.pull_rect.collidepoint(event.pos):
                self.visible = True
                self.scrolling = True

    def do_scroll(self,dt):
        direction = DIRECTION[self.scroll_direction]
        self.rect.x += direction*self.scroll_speed*dt
        if self.rect.x <= -298:
            self.rect.x = -298
            self.visible = False
            self.scrolling = False
            if self.scroll_direction == "RIGHT":
                self.scroll_direction = "LEFT"
            else:
                self.scroll_direction = "RIGHT"
        elif self.rect.x >= 102:
            self.rect.x = 102
            self.scrolling = False
            if self.scroll_direction == "RIGHT":
                self.scroll_direction = "LEFT"
            else:
                self.scroll_direction = "RIGHT"
        self.pull_rect.left = self.rect.right
        self.arrow_rect.topleft = self.pull_rect.move(3,121).topleft
