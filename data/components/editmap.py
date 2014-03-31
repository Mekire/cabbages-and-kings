import pygame as pg

from .. import map_prepare, tools
from ..components import map_gui_widgets


STANDARD_LAYERS = ("BG Colors", "BG Tiles", "Water", "Solid",
          "Solid/Fore", "Foreground", "Environment")

OTHER_LAYERS = ("Enemies", "Items")


class EditMap(object):
    """A class to contain the actual map data."""
    def __init__(self, map_dict):
        self.map_dict = map_dict
        self.rect = pg.Rect(120, 0, 1000, 700)
        self.adding = False
        self.deleting = False
        self.waiting = False

    def add_tile(self, selected, layer, point):
        """Called if self.adding flag is set."""
        if layer == "Enemies":
            self.add_enemy(selected, layer, point)

        elif selected and self.rect.collidepoint(point):
            point = tools.get_cell_coordinates(self.rect, point,
                                               map_prepare.CELL_SIZE)
            self.map_dict[layer][point] = selected

    def add_enemy(self, selected, layer, point):
        if not self.waiting:
            self.waiting = map_gui_widgets.TextBox((600,100,100,50))
        self.waiting.update()
        if not self.waiting.active:
            try:
                speed = int(self.waiting.final)
                if speed < 0:
                    raise ValueError
                sheet, source = selected
                self.map_dict["Enemies"][point] = sheet, source, speed
                self.adding = False
                self.waiting = False
            except ValueError:
                self.waiting.active = True

    def del_tile(self, layer, point):
        """Called if self.deleting flag is set."""
        point = tools.get_cell_coordinates(self.rect, point,
                                           map_prepare.CELL_SIZE)
        if point in self.map_dict[layer]:
            self.map_dict[layer].pop(point)

    def draw_map(self, surface, visibility):
        """
        Draws the map layers in the correct order.  The toolbar.checkboxes
        are checked to see if the layer's visibility is on/off.
        """
        surface.fill(self.map_dict["BG Colors"]["fill"], self.rect)
        for layer in STANDARD_LAYERS:
            if visibility[layer]:
                if layer == "BG Colors":
                    self.draw_color_layer(surface, layer)
                else:
                    self.draw_normal_layer(surface, layer)
        for layer in OTHER_LAYERS:
            self.draw_normal_layer(surface, layer)

    def draw_color_layer(self, surface, layer):
        """The BG_Colors layer requires a unique draw function."""
        for coords in self.map_dict[layer]:
            if not coords == "fill":
                color = self.map_dict[layer][coords][1]
                target = pg.Rect((120+coords[0],0+coords[1]),
                                 map_prepare.CELL_SIZE)
                surface.fill(color, target)

    def draw_normal_layer(self, surface, layer):
        """Draw function for standard layers."""
        for coords in self.map_dict[layer]:
            map_string, source_coords = self.map_dict[layer][coords][0:2]###
            sheet = map_prepare.GFX["mapsheets"][map_string]
            target = 120+coords[0], 0+coords[1]
            surface.blit(sheet, target, pg.Rect(source_coords,
                                                map_prepare.CELL_SIZE))

    def reset_add_del(self):
        """Flip both adding and deleting back to False."""
        self.adding = False
        self.deleting = False

    def check_event(self,event):
        """Set adding and deleting flags based on mouse clicks."""
        if not self.waiting:
            if event.type == pg.MOUSEBUTTONDOWN:
                if event.button == 1:
                    if self.rect.collidepoint(event.pos):
                        self.adding = True
                elif event.button == 3:
                    if self.rect.collidepoint(event.pos):
                        self.deleting = True
            elif event.type == pg.MOUSEBUTTONUP:
                self.reset_add_del()
        else:
            self.waiting.get_event(event)

    def update(self, selected, layer):
        """Add and delete tiles according to current flags."""
        mouse_position = pg.mouse.get_pos()
        if self.adding:
            self.add_tile(selected, layer, mouse_position)
        elif self.deleting:
            self.del_tile(layer, mouse_position)
