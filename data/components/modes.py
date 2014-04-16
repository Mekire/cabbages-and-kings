import pygame as pg

from .. import tools, map_prepare
from ..components import map_gui_widgets
from . import panel


BASIC = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
         "forest", "misc", "tatami", "water")


class _Mode(object):
    """Base class for modes."""
    def __init__(self, map_state):
        self.map_state = map_state
        self.make_panels()
        self.reset_add_del()

    @property
    def active_panel(self):
        """Get the currently active panel (generally based on layer)."""
        return self.panel

    def update(self, keys, now):
        """Update panel and add/delete tiles from map editing window."""
        self.active_panel.update(keys, now)
        if self.adding:
            self.add_tile(pg.mouse.get_pos())
        elif self.deleting:
            self.del_tile(pg.mouse.get_pos())
        if self.waiting:
            self.waiting.update()

    def get_event(self, event):
        """
        Handle mouse events on map editing window and pass event on to the
        panel window.  If the mode is currently waiting on an input pass the
        event down to waiting instead.
        """
        if not self.waiting:
            if event.type == pg.MOUSEBUTTONDOWN:
                if map_prepare.MAP_RECT.collidepoint(event.pos):
                    if event.button == 1:
                        self.set_add_del(event.pos, "adding")
                    elif event.button == 3:
                        self.set_add_del(event.pos, "deleting")
            elif event.type == pg.MOUSEBUTTONUP:
                self.reset_add_del()
            self.active_panel.get_event(event)
        else:
            self.waiting.get_event(event)

    def draw(self, surface, interpolate):
        """Draw the currently active panel to the surface."""
        self.active_panel.draw(surface, interpolate)
        if self.waiting:
            self.waiting.draw(surface)

    def reset_add_del(self):
        """Flip both adding and deleting back to False."""
        self.adding = False
        self.deleting = False
        self.waiting = None


class Standard(_Mode):
    """Standard mode in the primary map editor."""
    def make_panels(self):
        """Create necessary panels and their pages."""
        pages = [panel.PanelPage(sheet, self.map_state) for sheet in BASIC]
        self.panel = panel.Panel(self.map_state, pages)
        background_page = [panel.BackGroundPage(self.map_state)]
        self.background_panel = panel.Panel(self.map_state, background_page)

    @property
    def active_panel(self):
        """Get the currently active panel (generally based on layer)."""
        if self.map_state.layer != "BG Colors":
            return self.panel
        else:
            return self.background_panel

    def set_add_del(self, point, attribute):
        """Set adding or deleting attributes and retract panel."""
        if not self.active_panel.rect.collidepoint(point):
            setattr(self, attribute, True)
            self.active_panel.retract()

    def add_tile(self, point):
        """Called in update if self.adding flag is set."""
        selected = self.map_state.selected
        map_rect = map_prepare.MAP_RECT
        if selected and map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            point = tools.get_cell_coordinates(map_rect, point, size)
            self.map_state.map_dict[self.map_state.layer][point] = selected

    def del_tile(self, point):
        """Called in update if self.deleting flag is set."""
        map_rect = map_prepare.MAP_RECT
        if map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            point = tools.get_cell_coordinates(map_rect, point, size)
            self.map_state.map_dict[self.map_state.layer].pop(point, None)


class Enemies(_Mode):
    def make_panels(self):
        """Create necessary panels and their pages."""
        pages = [panel.PanelPage("enemy_place", self.map_state)]
        self.panel = panel.Panel(self.map_state, pages)

    def add_tile(self, *args):
        """Called in update if self.adding flag is set."""
        sheet, source = self.map_state.selected
        if self.waiting.done != None:
            try:
                speed = float(self.waiting.done)
                if speed < 0:
                    raise ValueError
                selected = sheet, source, speed
                map_rect = map_prepare.MAP_RECT
                size = map_prepare.CELL_SIZE
                coord = tools.get_cell_coordinates(map_rect, self.point, size)
                self.map_state.map_dict["Enemies"][coord] = selected
            except ValueError:
                print("Invalid input: Enemy not added.")
            self.reset_add_del()

    def del_tile(self, point):
        """Called in update if self.deleting flag is set."""
        map_rect = map_prepare.MAP_RECT
        if map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            coord = tools.get_cell_coordinates(map_rect, point, size)
            self.map_state.map_dict["Enemies"].pop(coord, None)

    def set_add_del(self, point, attribute):
        """Set adding or deleting attributes and retract panel."""
        if not self.active_panel.rect.collidepoint(point):
            if attribute == "deleting" and not self.adding:
                self.deleting = True
                self.active_panel.retract()
            elif not self.waiting and self.map_state.selected:
                self.point = point
                rect = map_prepare.MAP_RECT.inflate(-500, -600)
                self.adding = True
                self.waiting = InputWindow(rect, "Enter Speed (pixels/frame):")
                self.active_panel.retract()


class Items(_Mode):
    def make_panels(self):
        """Create necessary panels and their pages."""
        pages = [panel.ItemPage(self.map_state)]
        self.panel = panel.Panel(self.map_state, pages)

    def add_tile(self, *args):
        """Called in update if self.adding flag is set."""
        pass

    def del_tile(self, point):
        """Called in update if self.deleting flag is set."""
        pass

    def set_add_del(self, point, attribute):
        """Set adding or deleting attributes and retract panel."""
        pass


class InputWindow(object):
    def __init__(self, rect, prompt):
        self.rect = pg.Rect(rect)
        zeroed = pg.Rect((0,0), self.rect.size)
        self.font = pg.font.Font(None, 35)
        self.prompt = self.font.render(prompt, 1, pg.Color("white"))
        self.prompt_rect = self.prompt.get_rect(centerx=zeroed.centerx, y=10)
        self.image = pg.Surface(self.rect.size).convert()
        self.image.fill(pg.Color("white"))
        self.image.fill((40,40,40), zeroed.inflate(-4,-4))
        text_rect = zeroed.inflate(-self.rect.w//3, -3*self.rect.h//4)
        text_rect.centery = 3*self.rect.h//5
        self.textbox = map_gui_widgets.TextBox(text_rect)
        self.done = None

    def update(self):
        self.textbox.update()
        if not self.textbox.active:
            self.done = self.textbox.final

    def get_event(self, event):
        self.textbox.get_event(event)

    def draw(self, surface):
        self.textbox.draw(self.image)
        self.image.blit(self.prompt, self.prompt_rect)
        surface.blit(self.image, self.rect)
