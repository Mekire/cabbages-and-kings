import pygame as pg

from .. import map_prepare,tools


LAYERS = ("BG Colors","BG Tiles","Water","Solid",
          "Solid/Fore","Foreground","Environment")

CELL_SIZE = (50,50)


class EditMap(object):
    """A class to contain the actual map data."""
    def __init__(self):
        self.rect = pg.Rect(120,0,1200,700)
        self.map_dict = {layer:{} for layer in LAYERS}
        self.adding = False
        self.deleting = False

    def add_tile(self,selected,layer,point):
        """Called if self.adding flag is set."""
        if selected and self.rect.collidepoint(point):
            point = tools.get_cell_coordinates(self.rect,point,CELL_SIZE)
            self.map_dict[layer][point] = selected

    def del_tile(self,layer,point):
        """Called if self.deleting flag is set."""
        point = tools.get_cell_coordinates(self.rect,point,CELL_SIZE)
        if point in self.map_dict[layer]:
            self.map_dict[layer].pop(point)

    def draw_map(self,surface,visibility):
        """Draws the map layers in the correct order.  The toolbar.checkboxes
        are checked to see if the layer's visibility is on/off."""
        for layer in LAYERS:
            if visibility[layer]:
                for coords in self.map_dict[layer]:
                    map_string, source_coords = self.map_dict[layer][coords]
                    sheet = map_prepare.GFX["mapsheets"][map_string]
                    target = 120+coords[0], 0+coords[1]
                    surface.blit(sheet,target,pg.Rect(source_coords,CELL_SIZE))

    def check_event(self,event):
        """Set adding and deleting flags based on mouse clicks."""
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.adding = True
            elif event.button == 3:
                if self.edit_map.rect.collidepoint(event.pos):
                    self.deleting = True
        elif event.type == pg.MOUSEBUTTONUP:
            self.adding = False
            self.deleting = False

    def update(self,selected,layer):
        """Add and delete tiles according to current flags."""
        mouse_position = pg.mouse.get_pos()
        if self.adding:
            self.add_tile(selected,layer,mouse_position)
        elif self.deleting:
            self.del_tile(layer,mouse_position)
