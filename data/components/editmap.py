import pygame as pg

from .. import map_prepare,tools


LAYERS = ("BG Colors","BG Tiles","Water","Solid",
          "Solid/Fore","Foreground","Environment")

CELL_SIZE = (50,50)


class EditMap(object):
    def __init__(self):
        self.rect = pg.Rect(120,0,1200,700)
        self.map_dict = {layer:{} for layer in LAYERS}

    def add_tile(self,selected,layer,point):
        if selected and self.rect.collidepoint(point):
            point = tools.get_cell_coordinates(self.rect,point,CELL_SIZE)
            self.map_dict[layer][point] = selected

    def del_tile(self,layer,point):
        point = tools.get_cell_coordinates(self.rect,point,CELL_SIZE)
        if point in self.map_dict[layer]:
            self.map_dict[layer].pop(point)

    def draw_map(self,surface,visibility):
        for layer in LAYERS:
            if visibility[layer]:
                for coords in self.map_dict[layer]:
                    map_string, source_coords = self.map_dict[layer][coords]
                    sheet = map_prepare.GFX["mapsheets"][map_string]
                    target = 120+coords[0], 0+coords[1]
                    surface.blit(sheet,target,pg.Rect(source_coords,CELL_SIZE))
