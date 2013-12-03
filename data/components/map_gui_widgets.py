"""
Contains simple gui elements for the mode and layer selection menus.
Not currently particularly flexible, but coded to suit my needs.
"""

import pygame as pg


class Selector(object):
    """A selector menu including highlighting."""
    def __init__(self,content,start,space,size,selected=None):
        """The content argument is a list of strings that will be used both as
        the text appearing on the buttons, as well as the name referred to in
        the self.selected attribute. The arguments start, space, and size are
        all 2-tuples of the form (x,y). The start argument is the
        location on the target display surface of the first button; space is
        the distance between buttons; and size is the size of each individual
        button. The selected argument can be set to any element of content to
        have the Selector start with that option selected; or set to None to
        start with no options selected."""
        self.selected = selected
        self.buttons = self.create_buttons(content,start,space,size)

    def create_buttons(self,content,start,space,size):
        """Create the buttons using the arguments detailed above in the init."""
        buttons = []
        for i,name in enumerate(content):
            rect = pg.Rect((start[0]+i*space[0],start[1]+i*space[1]),size)
            selected = (True if name==self.selected else False)
            buttons.append(Button(self.get_result,name,rect,selected))
        return buttons

    def get_result(self,name):
        """This function is passed to each button on instantiazation. It is
        called by the button when it is clicked."""
        self.selected = name
        for button in self.buttons:
            if button.name != name:
                button.clicked = False

    def check_event(self,event):
        """Pass events down to each button."""
        for button in self.buttons:
            button.check_event(event)

    def update(self,surface):
        """Update and draw each button to the target surface."""
        for button in self.buttons:
            button.update(surface)


class Button(object):
    """A simple button class. Features such as colors, font and border
    width are currently hardcoded."""
    def __init__(self,function,name,rect,selected=False,unclick=False):
        """The argument name is a string used to refer to the button; rect is
        a pygame.Rect for the area of the button (inclusive of the border);
        function is the function that should be called when the button is
        clicked; selected is a boolean indicating whether or not the button
        is currently selected; unclick is a boolean indicating whether or not
        the self.clicked attribute will be set back to False on mouse up."""
        self.name = name
        self.rect = pg.Rect(rect)
        self.function = function
        self.color = (128,128,128)
        self.font = pg.font.SysFont("arial",12)
        self.text = self.font.render(name,False,pg.Color("white"))
        self.selected_text = self.font.render(name,False,pg.Color("black"))
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.clicked = selected
        self.unclick = unclick

    def check_event(self,event):
        """Check if the button has been clicked, and if so, set self.clicked to
        true and call self.function."""
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.clicked = True
                self.function(self.name)
        elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
            if self.unclick:
                self.clicked = False

    def update(self,surface):
        """Determine appearance based on whether the button is currently
        selected, hovered, or neither. Then draw the button to the target
        surface."""
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
    """A class to hold an array of CheckBox instances."""
    def __init__(self,content,initial,start,space):
        """The argument content is a list of strings used to refer to each box.
        The initial argument indicates the starting state of each CheckBox;
        pass True to start with all boxes check; False to start with no boxes
        checked; or a list of bools corresponding to the state of each member
        of content. The arguments start and space are 2-tuples of the form
        (x,y) and indicate the starting location of the first box and the space
        between each box, respectively."""
        self.state = self.make_state(content,initial)
        self.checkboxes = self.create_checkboxes(content,start,space)

    def make_state(self,content,initial):
        """Create the initial state dictionary. The details of the arguments
        can be found in the __init__ documentation."""
        if initial in (True,False):
            return {name:initial for name in content}
        else:
            return {name:state for (name,state) in zip(content,initial)}

    def create_checkboxes(self,content,start,space):
        """Create a list a CheckBox instances. The dimensions of the CheckBox
        are currently hardcoded. See __init__ for details on valid arguments."""
        boxes = []
        size = (20,20)
        for i,name in enumerate(content):
            rect = pg.Rect((start[0]+i*space[0],start[1]+i*space[1]),size)
            checked = self.state[name]
            boxes.append(CheckBox(name,rect,self.get_result,checked))
        return boxes

    def get_result(self,name):
        """This function is passed to each CheckBox and called when they are
        clicked."""
        self.state[name] = not self.state[name]

    def check_event(self,event):
        """Pass events down to each CheckBox."""
        for box in self.checkboxes:
            box.check_event(event)

    def update(self,surface):
        """Update and draw each CheckBox to the target surface."""
        for box in self.checkboxes:
            box.update(surface)


class CheckBox(object):
    """A simple checkbox class. Size and appearance are currently hardcoded."""
    def __init__(self,name,rect,function,checked=False):
        """The argument name is a string used to refer to the box; rect is
        a pygame.Rect for the area of the box (inclusive of the border);
        function is the function that should be called when the box is
        checked or unchecked; selected is a boolean indicating whether or not
        the button is currently checked."""
        self.name = name
        self.rect = pg.Rect(rect)
        self.function = function
        self.color = (128,128,128)
        self.select_rect = self.rect.inflate(-10,-10)
        self.checked = checked

    def check_event(self,event):
        """Check if the box has been clicked, and if so, flip self.clicked and
        call self.function."""
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked
                self.function(self.name)

    def update(self,surface):
        """Determine appearance based on whether the box is currently
        checked; then draw the box to the target surface."""
        checked_color = (0,196,0) if self.checked else pg.Color("white")
        surface.fill(pg.Color("black"),self.rect)
        surface.fill(self.color,self.rect.inflate(-2,-2))
        surface.fill(pg.Color("white"),self.rect.inflate(-6,-6))
        surface.fill((205,205,205),self.rect.inflate(-8,-8))
        surface.fill(checked_color,self.select_rect)
