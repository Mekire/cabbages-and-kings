import pygame as pg

from .. import tools, map_prepare
from .map_gui_widgets import Button, Selector


MIN_SCROLL = -302
MAX_SCROLL =  100
SCROLL_SPEED = 20.0

PULL_TAB = map_prepare.GFX["misc"]["pull"]
ARROWS = map_prepare.GFX["misc"]["arrows"]

CLEAR_BLUE = (50, 100, 255, 55)

FILL_BUTTON = {"name" : "Fill",
               "rect" : pg.Rect(150,200,100,50),
               "selected" : False,
               "unclick" : True,
               "key_bindings" : [pg.K_f]}

ITEM_TYPE = {"content" : ["Treasure Chest", "On Event"],
             "start" : (140, 400),
             "space" : (0,20),
             "size" : (100,20),
             "selected" : "Treasure Chest"}

SPECIAL_TYPE = {"content" : ["Portal", "Push", "Burnable", "Breakable"],
             "start" : (140, 50),
             "space" : (0,20),
             "size" : (100,20),
             "selected" : "Push"}


class Panel(object):
    """
    The panel from which the user selects tiles/enemies etc.  The visibility
    variables of all panel instances are shared.
    """
    rect = pg.Rect(-302, 48, 420, 604)
    scrolling = False
    visible = False
    scroll_direction = 1

    def __init__(self, map_state, pages):
        """
        The panel needs access to the map_state object.  The pages argument
        is a list of PanelPage (or subclass) instances.
        """
        self.map_state = map_state
        self.pages = pages
        self.index = 0
        self.image = self.make_panel()
        self.arrows = [ARROWS, pg.transform.flip(ARROWS, True, False)]

    @classmethod
    def do_scroll(cls):
        """Scroll panel in and out when Panel.scrolling is True."""
        cls.rect.x += SCROLL_SPEED*cls.scroll_direction
        cls.rect.x = min(max(cls.rect.x, MIN_SCROLL), MAX_SCROLL)
        if cls.rect.x == MIN_SCROLL:
            cls.visible = False
        if cls.rect.x in (MIN_SCROLL, MAX_SCROLL):
            cls.scrolling = False
            cls.scroll_direction *= -1

    @classmethod
    def retract(cls):
        """Set variables to trigger panel retract."""
        if cls.visible:
            cls.scrolling = True
            cls.scroll_direction = -1

    @classmethod
    def toggle_scroll(cls):
        """Flip the scrolling variables."""
        cls.scrolling = True
        cls.visible = True

    @property
    def pull_rect(self):
        """Conveniece for retrieving the position of the panel pull tab."""
        return PULL_TAB.get_rect(right=self.rect.right-2,
                                 centery=self.rect.centery)

    @property
    def arrow_rect(self):
        """Conveniece for retrieving the position of the pull tab arrows."""
        pull_rect = self.pull_rect
        return ARROWS.get_rect(centerx=pull_rect.centerx-1,
                               centery=pull_rect.centery)

    def is_ready(self):
        """Check if the panel is ready to send selection events to the page."""
        return self.visible and not self.scrolling

    def make_panel(self):
        """Create the base panel image."""
        image = pg.Surface(self.rect.size).convert_alpha()
        image.fill((0,0,0,0))
        image.fill(pg.Color("white"), (0,0,404,604))
        image.blit(PULL_TAB, (402, 152))
        return image

    def get_event(self, event):
        """
        Check for scroll trigger events (keyboard/mouse) and if the panel
        is currently ready, send event on to the current panel page.
        """
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_SPACE:
                self.toggle_scroll()
        elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.pull_rect.collidepoint(event.pos):
                self.toggle_scroll()
        if self.is_ready():
            self.pages[self.index].get_event(event)

    def update(self, keys, now):
        """Update scrolling if needed and update current panel page."""
        if self.visible and self.scrolling:
            self.do_scroll()
        self.pages[self.index].update(keys, now, self.rect, self.visible)

    def draw(self, surface, interpolate):
        """
        Draw panel elements including page.
        Location of the panel is interpolated between frames while scrolling.
        """
        scroll_direction = self.scroll_direction
        if self.visible and self.scrolling:
            pos = self.rect.copy()
            pos.x += SCROLL_SPEED*scroll_direction*interpolate
            pos.x = min(max(self.rect.x, MIN_SCROLL), MAX_SCROLL)
        else:
            pos = self.rect
        arrow = self.arrows[0] if scroll_direction>0 else self.arrows[1]
        self.pages[self.index].draw(self.image, interpolate)
        surface.blit(self.image, pos)
        surface.blit(arrow, self.arrow_rect)


class PanelPage(object):
    """Base class for panel pages."""
    def __init__(self, sheet_name, map_state):
        """
        Argument sheet_name is the string name for the sheet corresponding
        to the map_prepare.GFX["mapsheets"] dictionary.  The page must also
        have access to the map_state object.
        """
        self.map_state = map_state
        self.sheet_name = sheet_name
        if sheet_name:
            self.image = map_prepare.GFX["mapsheets"][sheet_name]
        else:
            self.image = pg.Surface((0,0)).convert()
        self.rect = self.image.get_rect()
        self.cursor = self.make_selector_cursor()

    def update(self, keys, now, panel_rect, visible):
        """
        Set the position of the pages rect based on the location of the
        panel's rect.
        """
        self.rect.topleft = panel_rect.move(2,2).topleft

    def get_event(self, event):
        """If the page is clicked on run the set_select method."""
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.set_select(event.pos)

    def draw(self, surface, interpolate):
        """Draw the page to the surface, followed by the cursor if needed."""
        surface.fill((40,40,40), (2, 2, 400, 600))
        surface.blit(self.image, (2,2))
        self.draw_cursor(surface, self.image)

    def make_selector_cursor(self):
        """Creates the rectangular selector."""
        cursor = pg.Surface(map_prepare.CELL_SIZE).convert_alpha()
        cursor_rect = cursor.get_rect()
        cursor.fill(pg.Color("white"))
        cursor.fill(pg.Color("red"), cursor_rect.inflate(-2,-2))
        cursor.fill(pg.Color("white"), cursor_rect.inflate(-6,-6))
        cursor.fill(CLEAR_BLUE, cursor_rect.inflate(-8,-8))
        return cursor

    def draw_cursor(self, surface, pallet):
        """Draw rectangle cursor when required."""
        point = pg.mouse.get_pos()
        if self.rect.collidepoint(point):
            cell_size = map_prepare.CELL_SIZE
            on_sheet = tools.get_cell_coordinates(self.rect, point, cell_size)
            location = (on_sheet[0]+2, on_sheet[1]+2)
            surface.blit(self.cursor, location)

    def set_select(self, point):
        """Set the selected item and corresponding image."""
        cell_size = map_prepare.CELL_SIZE
        coords = tools.get_cell_coordinates(self.rect, point, cell_size)
        self.map_state.selected = (self.sheet_name, coords)
        image = self.image.subsurface((coords, cell_size))
        self.map_state.select_image = image


class BackGroundPage(PanelPage):
    """
    The background page has slightly different behavior than the standard
    pages and requires its own class.
    """
    def __init__(self, map_state):
        """Create the fill button and bind it to appropriate method."""
        PanelPage.__init__(self, "background", map_state)
        self.fill_button = Button(**FILL_BUTTON)
        self.fill_button.bind(self.fill_all)

    def fill_all(self, name):
        """
        Set the background fill color if a color is currently selected and
        the fill button is clicked.
        """
        selected = self.map_state.selected
        if selected:
            self.map_state.map_dict["BG Colors"]["fill"] = selected[1]

    def update(self, keys, now, panel_rect, visible):
        """
        If the mouse is over the background page and it is visible,
        set the cursor to the dropper.
        """
        point = pg.mouse.get_pos()
        if panel_rect.collidepoint(point) and visible:
            if pg.mouse.get_cursor() != map_prepare.DROPPER:
                pg.mouse.set_cursor(*map_prepare.DROPPER)
        self.rect.topleft = panel_rect.move(2,2).topleft

    def get_event(self, event):
        """
        Run the standard PanelPage get_event method but also send the event
        to the fill button.
        """
        PanelPage.get_event(self, event)
        self.fill_button.get_event(event, self.rect.topleft)

    def draw(self, surface, interpolate):
        """Draw page and fill button."""
        PanelPage.draw(self, surface, interpolate)
        self.fill_button.draw(surface, self.rect.topleft)

    def set_select(self, point):
        """
        Set the selected to the color tuple at point rather than to
        coordinates on the map sheet.
        """
        cell_size = map_prepare.CELL_SIZE
        coords = tools.get_cell_coordinates(self.rect, point, cell_size)
        get_point = point[0]-self.rect.x, point[1]-self.rect.y
        try:
            color = self.image.get_at(get_point)
            if color.a != 255:
                raise IndexError
        except IndexError:
            print("Not on sheet.")
        self.map_state.selected = (self.sheet_name, tuple(color))
        image = pg.Surface(cell_size).convert()
        image.fill(color)
        self.map_state.select_image = image

    def make_selector_cursor(self):
        """Not needed for this page."""
        pass

    def draw_cursor(self, *args):
        """Not needed for this page."""
        pass


class ItemPage(PanelPage):
    """
    Page for item placement.  Contains the selctable item images as well
    as a selector menu to choose if the item comes from a treasure chest or
    is spawned after a particular map event.
    """
    def __init__(self, map_state):
        """Create the selector menu and bind it to appropriate callback."""
        PanelPage.__init__(self, "item_place", map_state)
        self.selector = Selector(**ITEM_TYPE)
        self.selector.bind(self.set_type)
        self.selected = "Treasure Chest"

    def set_type(self, name):
        """Call back for the selector menu."""
        self.selected = name

    def get_event(self, event):
        """
        Run the standard PanelPage get_event method but also send the event
        to the selector.
        """
        PanelPage.get_event(self, event)
        self.selector.get_event(event, self.rect.topleft)

    def draw(self, surface, interpolate):
        """Draw page and selector menu."""
        PanelPage.draw(self, surface, interpolate)
        self.selector.draw(surface, self.rect.topleft)


class SpecialPage(ItemPage):
    """
    Page for portals, push, break, and burn blocks.
    Similar functionality to item page.
    """
    def __init__(self, map_state):
        PanelPage.__init__(self, None, map_state)
        self.selector = Selector(**SPECIAL_TYPE)
        self.selector.bind(self.set_type)
        self.selected = "Push"
