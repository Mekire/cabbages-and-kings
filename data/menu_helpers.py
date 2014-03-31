"""
Contains useful functionality for uni- and bi-directional menus.
"""

import pygame as pg

from . import prepare, state_machine


class BasicMenu(state_machine._State):
    """Base class for basic uni-directional menus."""
    def __init__(self, option_length):
        state_machine._State.__init__(self)
        self.option_length = option_length
        self.index = 0

    def get_event(self, event):
        """
        Generic event getter for scrolling through menus.
        """
        if event.type == pg.KEYDOWN:
            if event.key in (pg.K_DOWN, pg.K_RIGHT):
                prepare.SFX["dj-chronos__menu-nav-2"].play()
                self.index = (self.index+1)%self.option_length
            elif event.key in (pg.K_UP, pg.K_LEFT):
                prepare.SFX["dj-chronos__menu-nav-2"].play()
                self.index = (self.index-1)%self.option_length
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.pressed_enter()
            elif event.key in (pg.K_x, pg.K_ESCAPE):
                self.pressed_exit()

    def make_options(self, font, choices, y_start, y_space, center_x=None):
        """
        Makes prerendered (text,rect) tuples for basic text menus.
        Both selected and non-selected versions are made of each.
        Used by both the Option and Confirm menus.
        """
        options = {}
        args = [font, choices, pg.Color("white"), y_start, y_space, center_x]
        options["unselected"] = make_text_list(*args)
        args = [font, choices, pg.Color("yellow"), y_start, y_space, center_x]
        options["selected"] = make_text_list(*args)
        return options

    def update(self, keys, now):
        pass

    def pressed_enter(self):
        pass

    def pressed_exit(self):
        pass


class BidirectionalMenu(state_machine._State):
    """Base class for basic bi-directional menus."""
    def __init__(self, option_lengths):
        state_machine._State.__init__(self)
        self.option_lengths = option_lengths
        self.index = [0,0]

    def get_event(self, event):
        """
        Generic event getter for scrolling through menus.
        """
        if event.type == pg.KEYDOWN:
            if event.key in prepare.DEFAULT_CONTROLS:
                prepare.SFX["dj-chronos__menu-nav-2"].play()
                self.move_on_grid(event)
            elif event.key in (pg.K_RETURN, pg.K_KP_ENTER):
                self.pressed_enter()
            elif event.key in (pg.K_x, pg.K_ESCAPE):
                self.pressed_exit()

    def move_on_grid(self, event):
        """Called when user moves the selection cursor with the arrow keys."""
        direction = prepare.DEFAULT_CONTROLS[event.key]
        vector = prepare.DIRECT_DICT[direction]
        self.index[0] = (self.index[0]+vector[0])%self.option_lengths[0]
        self.index[1] = (self.index[1]+vector[1])%self.option_lengths[1]

    def update(self, keys, now):
        pass

    def pressed_enter(self):
        pass

    def pressed_exit(self):
        pass


def render_font(font, msg, color, center):
    """Return the rendered font surface and its rect centered on center."""
    msg = font.render(msg, 0, color)
    rect = msg.get_rect(center=center)
    return msg, rect


def make_text_list(font, strings, color, start_y, y_space, x_center=None):
    """
    Takes a list of strings and returns a list of
    (rendered_surface, rect) tuples. The rects are centered on the screen
    and their y coordinates begin at starty, with y_space pixels between
    each line.
    """
    x_center = x_center if x_center else prepare.SCREEN_RECT.centerx
    rendered_text = []
    for i,string in enumerate(strings):
        msg_center = (x_center, start_y+i*y_space)
        msg_data = render_font(font, string, color, msg_center)
        rendered_text.append(msg_data)
    return rendered_text
