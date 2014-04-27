"""
Contains simple gui elements for the mode and layer selection menus.
Not currently particularly flexible, but coded to suit my needs.
"""

import string
import pygame as pg


ACCEPTED = string.ascii_letters+string.digits+string.punctuation+" "


class _Widget(object):
    def bind(self, function):
        self.command = function

    def update(self, *args):
        pass


class TextBox(_Widget):
    def __init__(self, rect, **kwargs):
        self.rect = pg.Rect(rect)
        self.active = True
        self.buffer = []
        self.final = None
        self.rendered = None
        self.render_rect = None
        self.render_area = None
        self.blink = True
        self.blink_timer = 0.0
        self.process_kwargs(kwargs)

    def process_kwargs(self, kwargs):
        defaults = {"id" : None,
                    "command" : None,
                    "color" : pg.Color("white"),
                    "font_color" : pg.Color("black"),
                    "outline_color" : pg.Color("black"),
                    "outline_width" : 2,
                    "active_color" : (255,33,33),
                    "font" : pg.font.Font(None, self.rect.height+4),
                    "clear_on_enter" : False,
                    "inactive_on_enter" : True}
        for kwarg in kwargs:
            if kwarg in defaults:
                defaults[kwarg] = kwargs[kwarg]
            else:
                raise KeyError("InputBox accepts no keyword {}.".format(kwarg))
        self.__dict__.update(defaults)

    def get_event(self, event):
        if event.type == pg.KEYDOWN and self.active:
            if event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.execute()
            elif event.key == pg.K_BACKSPACE:
                if self.buffer:
                    self.buffer.pop()
            elif event.unicode in ACCEPTED:
                self.buffer.append(event.unicode)

    def execute(self):
        if self.command:
            self.command(self.id, self.final)
        self.active = not self.inactive_on_enter
        if self.clear_on_enter:
            self.buffer = []

    def update(self):
        new = "".join(self.buffer)
        if new != self.final:
            self.final = new
            self.rendered = self.font.render(self.final, True, self.font_color)
            self.render_rect = self.rendered.get_rect(x=self.rect.x+2,
                                                     centery=self.rect.centery)
            if self.render_rect.width > self.rect.width-6:
                offset = self.render_rect.width-(self.rect.width-6)
                self.render_area = pg.Rect(offset, 0, self.rect.width-6,
                                           self.render_rect.height)
            else:
                self.render_area = self.rendered.get_rect(topleft=(0,0))
        if pg.time.get_ticks()-self.blink_timer > 200:
            self.blink = not self.blink
            self.blink_timer = pg.time.get_ticks()

    def draw(self, surface):
        if self.active:
            outline_color = self.active_color
        else:
            outline_color = self.outline_color
        outline = self.rect.inflate(self.outline_width*2, self.outline_width*2)
        surface.fill(outline_color, outline)
        surface.fill(self.color, self.rect)
        if self.rendered:
            surface.blit(self.rendered, self.render_rect, self.render_area)
        if self.blink and self.active:
            curse = self.render_area.copy()
            curse.topleft = self.render_rect.topleft
            surface.fill(self.font_color, (curse.right+1,curse.y,2,curse.h))


class Selector(_Widget):
    """A selector menu including highlighting."""
    def __init__(self, content, start, space, size, selected=None):
        """
        The content argument is a list of strings that will be used both as
        the text appearing on the buttons, as well as the name referred to in
        the self.selected attribute. The arguments start, space, and size are
        all 2-tuples of the form (x,y). The start argument is the
        location on the target display surface of the first button; space is
        the distance between buttons; and size is the size of each individual
        button. The selected argument can be set to any element of content to
        have the Selector start with that option selected; or set to None to
        start with no options selected.
        """
        self.command = None
        self.selected = selected
        self.buttons = self.create_buttons(content, start, space, size)

    def create_buttons(self, content, start, space, size):
        """
        Create the buttons using the arguments detailed above in the init.
        """
        buttons = []
        for i,name in enumerate(content):
            rect = pg.Rect((start[0]+i*space[0],start[1]+i*space[1]), size)
            selected = (True if name == self.selected else False)
            buttons.append(Button(name, rect, clicked=selected,
                                  command=self.get_result,))
        return buttons

    def get_result(self, name):
        """
        This function is passed to each button on instantiazation. It is
        called by the button when it is clicked.
        """
        self.selected = name
        for button in self.buttons:
            button.clicked = button.name == name
        if self.command:
            self.command(name)

    def get_event(self, event, offset=(0,0)):
        """Pass events down to each button."""
        for button in self.buttons:
            button.get_event(event, offset)

    def draw(self, surface, offset=(0,0)):
        """Update and draw each button to the target surface."""
        for button in self.buttons:
            button.draw(surface, offset)


class Button(_Widget):
    """
    A simple button class. Features such as colors, font and border
    width are currently hardcoded.
    """
    def __init__(self, name, rect, **kwargs):
        """
        The argument name is a string used to refer to the button; rect is
        a pygame.Rect for the area of the button (inclusive of the border).
        See set_kwargs for details on optional keyword arguments.
        """
        self.name = name
        self.rect = pg.Rect(rect)
        self.color = (128, 128, 128)
        self.font = pg.font.SysFont("arial", 12)
        self.text = self.font.render(name, False, pg.Color("white"))
        self.selected_text = self.font.render(name, False, pg.Color("black"))
        self.text_rect = self.text.get_rect(center=self.rect.center)
        self.set_kwargs(kwargs)

    def set_kwargs(self, kwargs):
        """
        The following can be passed  as kwargs in the __init__ and give the
        button a measure of customizability.  The command argument is the
        function that is called when the button is clicked; unclick is a
        boolean indicating whether or not the self.clicked attribute will be
        set back to False on mouse up.  The button can also be bound to
        keys with the key_bindings argument.
        """
        accept = {"command" : None,
                  "clicked" : False,
                  "unclick" : False,
                  "active" : True,
                  "key_bindings" : []}
        for kwarg in kwargs:
            if kwarg in accept:
                accept[kwarg] = kwargs[kwarg]
        self.__dict__.update(accept)

    def get_event(self, event, offset=(0,0)):
        """
        Check if the button has been clicked, or bound keys pressed/released.
        """
        if self.active:
            if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                pos = event.pos[0]-offset[0], event.pos[1]-offset[1]
                if self.rect.collidepoint(pos):
                    self.press()
            elif event.type == pg.MOUSEBUTTONUP and event.button == 1:
                self.unpress()
            elif event.type == pg.KEYDOWN:
                self.press_bound_key(event)
            elif event.type == pg.KEYUP:
                self.release_bound_key(event)

    def bind_key(self, key):
        """Add passed key to the bindings for this button."""
        self.key_bindings.append(key)

    def press_bound_key(self, event):
        """Press button if bound key (or key+mod) combination is pressed."""
        if event.key in self.key_bindings:
            self.press()
        elif (event.key, pg.key.get_mods()) in self.key_bindings:
            self.press()

    def release_bound_key(self, event):
        """
        If key is released call unpress.  In the case of bindings that have
        mod keys, ignore the state of the mod key.
        """
        try:
            if event.key in [key[0] for key in self.key_bindings]:
                self.unpress()
        except TypeError:
            if event.key in self.key_bindings:
                self.unpress()

    def press(self):
        """Press the button and call its command callback if it exists."""
        self.clicked = True
        if self.command:
            self.command(self.name)

    def unpress(self):
        """Set button to unclicked state."""
        if self.unclick:
            self.clicked = False

    def draw(self, surface, offset=(0,0)):
        """
        Determine appearance based on whether the button is currently
        selected, hovered, or neither. Then draw the button to the target
        surface.
        """
        mouse = pg.mouse.get_pos()
        pos = mouse[0]-offset[0], mouse[1]-offset[1]
        if self.clicked:
            fill_color = pg.Color("white")
            text = self.selected_text
        elif self.rect.collidepoint(pos):
            fill_color = (198, 226, 255)
            text = self.selected_text
        else:
            fill_color = self.color
            text = self.text
        surface.fill(pg.Color("black"), self.rect)
        surface.fill(fill_color, self.rect.inflate(-2,-2))
        surface.blit(text, self.text_rect)


class CheckBoxArray(_Widget):
    """A class to hold an array of CheckBox instances."""
    def __init__(self, content, initial, start, space, key_bindings=None):
        """
        The argument content is a list of strings used to refer to each box.
        The initial argument indicates the starting state of each CheckBox;
        pass True to start with all boxes check; False to start with no boxes
        checked; or a list of bools corresponding to the state of each member
        of content. The arguments start and space are 2-tuples of the form
        (x,y) and indicate the starting location of the first box and the space
        between each box, respectively.  An optional dictionary of key to
        callback bindings can be passed with the key_bindings argument.
        """
        self.command = None
        self.state = self.make_state(content, initial)
        self.checkboxes = self.create_checkboxes(content, start, space)
        self.key_bindings = {}
        if key_bindings:
            for binding in key_bindings.items():
                self.bind_key(*binding)

    def make_state(self, content, initial):
        """
        Create the initial state dictionary. The details of the arguments
        can be found in the __init__ documentation.
        """
        if initial in (True, False):
            return {name:initial for name in content}
        else:
            return {name:state for (name,state) in zip(content, initial)}

    def bind_key(self, key, command):
        """Bind a key to a function and place it in the key_binding dict."""
        self.key_bindings[key] = command

    def create_checkboxes(self, content, start, space):
        """
        Create a list a CheckBox instances. The dimensions of the CheckBox
        are currently hardcoded. See __init__ for details on valid arguments.
        """
        boxes = []
        size = (20, 20)
        for i,name in enumerate(content):
            rect = pg.Rect((start[0]+i*space[0],start[1]+i*space[1]), size)
            checked = self.state[name]
            boxes.append(CheckBox(name, rect, checked, self.get_result))
        return boxes

    def get_result(self, name):
        """
        This function is passed to each checkbox and called when they are
        clicked.
        """
        self.state[name] = not self.state[name]
        if self.command:
            self.command(self.state)

    def get_event(self, event):
        """Pass events down to each checkbox."""
        for box in self.checkboxes:
            box.get_event(event)
        if event.type == pg.KEYDOWN and event.key in self.key_bindings:
            self.key_bindings[event.key](self)

    def draw(self, surface):
        """Update and draw each checjbox to the target surface."""
        for box in self.checkboxes:
            box.draw(surface)


class CheckBox(_Widget):
    """A simple checkbox class. Size and appearance are currently hardcoded."""
    def __init__(self, name, rect, checked=False, command=None):
        """
        The argument name is a string used to refer to the box; rect is
        a pygame.Rect for the area of the box (inclusive of the border);
        checked is a boolean indicating whether or not the button is currently
        checked; command is the function that is called when the box is
        checked or unchecked.
        """
        self.name = name
        self.rect = pg.Rect(rect)
        self.command = command
        self.color = (128, 128, 128)
        self.select_rect = self.rect.inflate(-10, -10)
        self.checked = checked

    def get_event(self, event):
        """Check if the box has been clicked, and if so, toggle it."""
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.toggle()

    def toggle(self):
        """Flip self.checked and call self.command."""
        self.checked = not self.checked
        if self.command:
            self.command(self.name)

    def draw(self, surface):
        """
        Determine appearance based on whether the box is currently
        checked; then draw the box to the target surface.
        """
        checked_color = (0, 196, 0) if self.checked else pg.Color("white")
        surface.fill(pg.Color("black"), self.rect)
        surface.fill(self.color, self.rect.inflate(-2,-2))
        surface.fill(pg.Color("white"), self.rect.inflate(-6,-6))
        surface.fill((205,205,205), self.rect.inflate(-8,-8))
        surface.fill(checked_color, self.select_rect)
