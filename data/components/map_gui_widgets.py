import pygame as pg


class Selector(object):
    def __init__(self,content,start,space,size,selected=None):
        self.selected = selected
        self.buttons = self.create_buttons(content,start,space,size)

    def create_buttons(self,content,start,space,size):
        buttons = []
        for i,name in enumerate(content):
            rect = pg.Rect((start[0]+i*space[0],start[1]+i*space[1]),size)
            selected = (True if name==self.selected else False)
            buttons.append(Button(name,rect,self.get_result,selected))
        return buttons

    def get_result(self,name):
        self.selected = name
        for button in self.buttons:
            if button.name != name:
                button.clicked = False

    def check_event(self,event):
        for button in self.buttons:
            button.check_event(event)

    def update(self,surface):
        for button in self.buttons:
            button.update(surface)


class Button(object):
    def __init__(self,name,rect,function,selected=False):
        self.name = name
        self.rect = pg.Rect(rect)
        self.function = function
        self.color = (128,128,128)
        self.font = pg.font.SysFont("arial",12)
        self.text = self.font.render(name,False,pg.Color("white"))
        self.selected_text = self.font.render(name,False,pg.Color("black"))
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.clicked = selected

    def check_event(self,event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                self.function(self.name)

    def update(self,surface):
        if self.clicked:
            fill_color = pg.Color("white")
            text = self.selected_text
        elif self.rect.collidepoint(pg.mouse.get_pos()):
            fill_color = (198,226,255)
            text = self.selected_text
        else:
            fill_color = self.color
            text = self.text
        surface.fill(pg.Color("black"),self.rect)
        surface.fill(fill_color,self.rect.inflate(-2,-2))
        surface.blit(text,self.text_rect)


class CheckBoxArray(object):
    def __init__(self,content,initial,start,space):
        self.state = self.make_state(content,initial)
        self.checkboxes = self.create_checkboxes(content,start,space)

    def make_state(self,content,initial):
        if initial in (True,False):
            return {name:initial for name in content}
        else:
            return {name:state for (name,state) in zip(content,initial)}

    def create_checkboxes(self,content,start,space):
        boxes = []
        size = (20,20)
        for i,name in enumerate(content):
            rect = pg.Rect((start[0]+i*space[0],start[1]+i*space[1]),size)
            checked = self.state[name]
            boxes.append(CheckBox(name,rect,self.get_result,checked))
        return boxes

    def get_result(self,name):
        self.state[name] = not self.state[name]

    def check_event(self,event):
        for box in self.checkboxes:
            box.check_event(event)

    def update(self,surface):
        for box in self.checkboxes:
            box.update(surface)


class CheckBox(object):
    def __init__(self,name,rect,function,checked=False):
        self.name = name
        self.rect = pg.Rect(rect)
        self.function = function
        self.color = (128,128,128)
        self.select_rect = self.rect.inflate(-10,-10)
        self.checked = checked

    def check_event(self,event):
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                self.function(self.name)

    def update(self,surface):
        checked_color = (0,196,0) if self.checked else pg.Color("white")
        surface.fill(pg.Color("black"),self.rect)
        surface.fill(self.color,self.rect.inflate(-2,-2))
        surface.fill(pg.Color("white"),self.rect.inflate(-6,-6))
        surface.fill((205,205,205),self.rect.inflate(-8,-8))
        surface.fill(checked_color,self.select_rect)