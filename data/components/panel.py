import pygame as pg


from .. import map_prepare,tools
from .map_gui_widgets import Button

MIN_SCROLL = -298
MAX_SCROLL =  102

CELL_SIZE = (50,50)

CLEAR_BLUE = (50,100,255,55)


class PalletPanel(object):
    def __init__(self,select_function,bg_function):
        self.select_function = select_function
        self.bg_function = bg_function
        self.rect = pg.Rect(-298,50,400,600)
        self.pull_image = map_prepare.GFX["misc"]["pull"]
        self.pull_rect = self.pull_image.get_rect(left=self.rect.right,y=200)
        self.right_arrows = map_prepare.GFX["misc"]["arrows"]
        self.left_arrows = pg.transform.flip(self.right_arrows,True,False)
        self.arrow_rect = self.right_arrows.get_rect()
        self.arrow_rect.topleft = self.pull_rect.move(3,121).topleft
        self.cursor = self.make_selector_cursor()
        self.visible = False
        self.scrolling = False
        self.scroll_speed = 800
        self.image = None
        self.bg_button = Button(self.change_background,
                              name="Background Fill",
                              rect=pg.Rect(0,0,100,50),
                              selected=False,
                              unclick=True,
                              active=False)

    def change_background(self,*args):
        """Change the background fill color. Currently messy callback hell."""
        self.bg_function()

    def make_selector_cursor(self):
        """Creates the rectangular selector."""
        cursor = pg.Surface(CELL_SIZE).convert_alpha()
        cursor_rect = cursor.get_rect()
        cursor.fill(pg.Color("white"))
        cursor.fill(pg.Color("red"),cursor_rect.inflate(-2,-2))
        cursor.fill(pg.Color("white"),cursor_rect.inflate(-6,-6))
        cursor.fill(CLEAR_BLUE,cursor_rect.inflate(-8,-8))
        return cursor

    def draw_cursor(self,surface,pallet):
        """Draw rectangle cursor when required."""
        point = pg.mouse.get_pos()
        if self.rect.collidepoint(point):
            if pallet == "background":
                pass ###
            else:
                on_sheet = tools.get_cell_coordinates(self.rect,point,CELL_SIZE)
                location = (on_sheet[0]+self.rect.x, on_sheet[1]+self.rect.y)
                surface.blit(self.cursor,location)

    def update(self,surface,pallet,dt):
        """Update panel if visible; scroll if needed."""
        self.image = map_prepare.GFX["mapsheets"][pallet]
        if self.visible:
            if self.scrolling:
                self.do_scroll(dt)
            surface.fill((255,255,255),self.rect.inflate(4,4))
            surface.fill((40,40,40),self.rect)
            surface.blit(self.image,self.rect)
            self.draw_cursor(surface,pallet)
            if pallet == "background":
                self.bg_button.rect.center = (self.rect.centerx,250)
                self.bg_button.text_rect.center = self.bg_button.rect.center
                self.bg_button.update(surface)
                self.bg_button.active = True
            else:
                self.bg_button.active = False
        surface.blit(self.pull_image, self.pull_rect)
        arrow = self.right_arrows if self.scroll_speed>0 else self.left_arrows
        surface.blit(arrow,self.arrow_rect)

    def check_event(self,event):
        """Handle events directed at the panel."""
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            point = event.pos
            if self.pull_rect.collidepoint(point):
                self.visible = True
                self.scrolling = True
            elif self.visible and self.rect.collidepoint(point):
                coords = tools.get_cell_coordinates(self.rect,point,CELL_SIZE)
                get_point = point[0]-self.rect.x,point[1]-self.rect.y
                try:
                    color = self.image.get_at(get_point)
                    self.select_function(coords,color)
                except IndexError:
                    print("Not on sheet.")
        if self.visible:
            self.bg_button.check_event(event)

    def do_scroll(self,dt):
        """Scroll panel in and out when handle is clicked."""
        self.rect.x += self.scroll_speed*dt
        self.rect.x = min(max(self.rect.x, MIN_SCROLL), MAX_SCROLL)
        if self.rect.x == MIN_SCROLL:
            self.visible = False
        if self.rect.x in (MIN_SCROLL,MAX_SCROLL):
            self.scrolling = False
            self.scroll_speed *= -1
        self.pull_rect.left = self.rect.right
        self.arrow_rect.topleft = self.pull_rect.move(3,121).topleft
