import pygame as pg

from .. import tools, map_prepare
from . import panel, map_gui_widgets


BASIC = ("base", "exttemple", "inttemple1", "inttemple2", "dungeon1",
         "forest", "misc", "tatami", "water")

ITEM_SHEET_DICT = {(0,0) : "heart",
                   (50,0) : "diamond",
                   (100,0) : "key",
                   (150,0) : "potion",
                   (0,50) : ("head", "helm"),
                   (50,50) : ("head", "sader"),
                   (100,50) : ("head", "diver"),
                   (150,50) : ("head", "goggles"),
                   (0,100) : ("body", "chain"),
                   (50,100) : ("shield", "tin"),
                   (100,100) : ("weapon", "labrys"),
                   (150,100) : ("weapon", "pitch")}


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

    @property
    def item_type(self):
        return self.panel.pages[self.panel.index].selected

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
                prompt = 'Event id ("kill" for death of all enemies):'
                self.waiting = InputWindow(rect, prompt)
                self.active_panel.retract()

    def add_tile(self, *args):
        """Called in update if self.adding flag is set."""
        sheet, src = self.map_state.selected
        item = ITEM_SHEET_DICT[src]
        if self.waiting.done is not None:
            try:
                event_id = self.waiting.done
                if event_id == "":
                    raise ValueError
                map_rect = map_prepare.MAP_RECT
                size = map_prepare.CELL_SIZE
                coord = tools.get_cell_coordinates(map_rect, self.point, size)
                args = sheet, src, item, event_id
                if self.item_type == "Treasure Chest":
                    self.map_state.map_dict["Chests"][coord] = args
                elif self.item_type == "On Event":
                    self.map_state.map_dict["Items"][coord] = args
            except ValueError:
                print("Invalid input: Item not added.")
            self.reset_add_del()

    def del_tile(self, point):
        """Called in update if self.deleting flag is set."""
        map_rect = map_prepare.MAP_RECT
        if map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            coord = tools.get_cell_coordinates(map_rect, point, size)
            for item_type in ("Chests", "Items"):
                self.map_state.map_dict[item_type].pop(coord, None)        


class Special(_Mode):
    @property
    def special_type(self):
        return self.panel.pages[self.panel.index].selected
    
    def make_panels(self):
        """Create necessary panels and their pages."""
        pages = [panel.SpecialPage(self.map_state)]
        self.panel = panel.Panel(self.map_state, pages)
        self.coord = None

        self.start_waiting_mode = {"Push" : "DIRECTION",
            "Portal" : "WORLD"}
        self.waiting_mode = None
        self.args = []
        
        self.prompts_push = {"DIRECTION" : "Enter pushable directions ('1111'='NESW'): ",
            "STACKED" : "Number Stacked: ",
            "ID" : "Identifier key: "}
        self.checks_push = {"DIRECTION" : self.check_direction_input,
            "STACKED" : self.check_stack,
            "ID" : self.check_non_empty}
        self.nexts_push = {"DIRECTION" : "STACKED",
            "STACKED" : "ID",
            "ID" : "DONE"}

        self.prompts_portal = {"WORLD" : ("Enter world map name: "),
            "MAP_COORDS" : "Enter map coordinates: ",
            "START_COORDS" : "Enter start position within map: "}
        self.checks_portal = {"WORLD" : self.check_non_empty,
                              "MAP_COORDS" : self.check_coords,
                              "START_COORDS" : self.check_coords}
        self.nexts_portal = {"WORLD" : "MAP_COORDS",
            "MAP_COORDS" : "START_COORDS",
            "START_COORDS" : "DONE"}
            
    def set_add_del(self, point, attribute):
        if self.special_type == "Push":
            if not self.active_panel.rect.collidepoint(point):
                if attribute == "deleting" and not self.adding:
                    self.deleting = True
                    self.active_panel.retract()
                elif not self.waiting:
                    map_rect = map_prepare.MAP_RECT
                    self.coord = tools.get_cell_coordinates(map_rect,point,(50,50))
                    if self.coord in self.map_state.map_dict["Solid"]:
                        self.waiting_mode = self.start_waiting_mode["Push"]
                        self.adding = True
                        self.point = point
                        rect = map_prepare.MAP_RECT.inflate(-500, -600)
                        prompt = self.prompts_push[self.waiting_mode]
                        self.waiting = InputWindow(rect, prompt)
                    else:
                        print("Push blocks must be placed on solid tiles.")
                    self.active_panel.retract()
        elif self.special_type == "Portal":
            if not self.active_panel.rect.collidepoint(point):
                if attribute == "deleting" and not self.adding:
                    self.deleting = True
                    self.active_panel.retract()
                elif not self.waiting:
                    self.waiting_mode = self.start_waiting_mode["Portal"]
                    map_rect = map_prepare.MAP_RECT
                    self.coord = tools.get_cell_coordinates(map_rect,point,(50,50))
                    self.adding = True
                    self.point = point
                    rect = map_prepare.MAP_RECT.inflate(-500, -600)
                    prompt = self.prompts_portal[self.waiting_mode]
                    self.waiting = InputWindow(rect, prompt)
                    self.active_panel.retract()

    def add_tile(self, *args):
        """Called in update if self.adding flag is set."""
        if self.special_type == "Push":
            if self.waiting.done is not None:
                try:
                    user_input = self.checks_push[self.waiting_mode]()
                    self.args.append(user_input)
                    if self.nexts_push[self.waiting_mode] == "DONE":
                        self.make_final_changes()
                    else:
                        self.waiting_mode = self.nexts_push[self.waiting_mode]
                        rect = map_prepare.MAP_RECT.inflate(-500, -600)
                        prompt = self.prompts_push[self.waiting_mode]
                        self.waiting = InputWindow(rect, prompt)
                except ValueError:
                    print("Invalid input: PushBlock not added.")
                    self.reset()
        elif self.special_type == "Portal":
            if self.waiting.done is not None:
                try:
                    user_input = self.checks_portal[self.waiting_mode]()
                    self.args.append(user_input)
                    if self.nexts_portal[self.waiting_mode] == "DONE":
                        self.make_final_changes()
                    else:
                        self.waiting_mode = self.nexts_portal[self.waiting_mode]
                        rect = map_prepare.MAP_RECT.inflate(-500, -600)
                        prompt = self.prompts_portal[self.waiting_mode]
                        self.waiting = InputWindow(rect, prompt)
                except ValueError:
                    print("Invalid input: Portal not added.")
                    self.reset()

    def make_final_changes(self):
        """
        If all input fields have been satisfied with valid results, remove the
        target block from the solid layer and place corresponding block in the
        Push layer.
        """
        if self.special_type == "Push":
            sheet, source = self.map_state.map_dict["Solid"][self.coord][:2]
            self.map_state.map_dict["Solid"].pop(self.coord)
            self.map_state.map_dict["Push"][self.coord] = [sheet, source] + self.args
        elif self.special_type == "Portal":
            self.map_state.map_dict["Portal"][self.coord] = self.args
            print("Added portal: {}".format(self.args))
        self.reset()

    def reset(self):
        """Reset needed variables for adding a new block."""
        self.reset_add_del()
        self.args = []
        if self.special_type == "Push":
            self.waiting_mode = "DIRECTION"
        elif self.special_type == "Portal":
            self.waiting_mode = "WORLD"
            
    def check_direction_input(self):
        """
        Check if binary direction string is valid.  Must have a length of 4
        and contain only 0s and 1s.
        """
        directions = self.waiting.done
        if len(directions) != 4 or any(c not in "01" for c in directions):
            raise ValueError
        return directions

    def check_stack(self):
        """Check stacked value is valid.  Must be a non-negative integer."""
        stacked = int(self.waiting.done)
        if stacked < 0:
            raise ValueError
        return stacked

    def check_non_empty(self):
        """Confirm input is valid.  All non empty strings pass."""
        if not self.waiting.done:
            raise ValueError
        return self.waiting.done

    def check_coords(self):
        """Confirm input is valid.  Accepts len 2 tuples of integers."""
        coords = self.waiting.done.split(",")
        coords = tuple(int(c) for c in coords)
        if len(coords) != 2:
            raise ValueError
        return coords

    def del_tile(self, point):
        """Called in update if self.deleting flag is set."""
        map_rect = map_prepare.MAP_RECT
        if map_rect.collidepoint(point):
            size = map_prepare.CELL_SIZE
            coord = tools.get_cell_coordinates(map_rect, point, size)
            self.map_state.map_dict[self.special_type].pop(coord, None)


class InputWindow(object):
    """A box for text input used to prompt for custom arguments."""
    def __init__(self, rect, prompt):
        """
        The argument rect is the total size of the window.
        Prompt is the text shown to the player indicating what is needed.
        """
        self.rect = pg.Rect(rect)
        zeroed = pg.Rect((0,0), self.rect.size)
        self.font = pg.font.SysFont("arial", 25)
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
        """
        Update the text box widget and set done to True if the text box
        loses focus.
        """
        self.textbox.update()
        if not self.textbox.active:
            self.done = self.textbox.final

    def get_event(self, event):
        """Pass the event on to the actual text box widget."""
        self.textbox.get_event(event)

    def draw(self, surface):
        """
        Draw the text box to the image and then draw the image to the
        target surface.
        """
        self.textbox.draw(self.image)
        self.image.blit(self.prompt, self.prompt_rect)
        surface.blit(self.image, self.rect)
