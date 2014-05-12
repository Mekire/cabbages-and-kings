"""
This module contains the fundamental Control class.
Also contained here are resource loading functions.
"""

import os
import pygame as pg

from . import state_machine


TIME_PER_UPDATE = 16.0  #Milliseconds


class Control(object):
    """
    Control class for entire project. Contains the game loop, and contains
    the event_loop which passes events to States as needed.
    """
    def __init__(self, caption):
        self.screen = pg.display.get_surface()
        self.caption = caption
        self.done = False
        self.clock = pg.time.Clock()
        self.fps = 60.0
        self.fps_visible = True
        self.now = 0.0
        self.keys = pg.key.get_pressed()
        self.state_machine = state_machine.StateMachine()

    def update(self):
        """
        Updates the currently active state.
        """
        self.now = pg.time.get_ticks()
        self.state_machine.update(self.keys, self.now)

    def draw(self, interpolate):
        if not self.state_machine.state.done:
            self.state_machine.draw(self.screen, interpolate)
            pg.display.update()
            self.show_fps()

    def event_loop(self):
        """
        Process all events and pass them down to the state_machine.
        The f5 key globally turns on/off the display of FPS in the caption
        """
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.done = True
            elif event.type == pg.KEYDOWN:
                self.keys = pg.key.get_pressed()
                self.toggle_show_fps(event.key)
            elif event.type == pg.KEYUP:
                self.keys = pg.key.get_pressed()
            self.state_machine.get_event(event)

    def toggle_show_fps(self, key):
        """Press f5 to turn on/off displaying the framerate in the caption."""
        if key == pg.K_F5:
            self.fps_visible = not self.fps_visible
            if not self.fps_visible:
                pg.display.set_caption(self.caption)

    def show_fps(self):
        """
        Display the current FPS in the window handle if fps_visible is True.
        """
        if self.fps_visible:
            fps = self.clock.get_fps()
            with_fps = "{} - {:.2f} FPS".format(self.caption, fps)
            pg.display.set_caption(with_fps)

    def main(self):
        """Main loop for entire program. Uses a constant timestep."""
        lag = 0.0
        while not self.done:
            lag += self.clock.tick(self.fps)
            self.event_loop()
            while lag >= TIME_PER_UPDATE:
                self.update()
                lag -= TIME_PER_UPDATE
            self.draw(lag/TIME_PER_UPDATE)


class Anim(object):
    """A class to simplify the act of adding animations to sprites."""
    def __init__(self, frames, fps, loops=-1):
        """
        The argument frames is a list of frames in the correct order;
        fps is the frames per second of the animation;
        loops is the number of times the animation will loop (a value of -1
        will loop indefinitely).
        """
        self.frames = frames
        self.fps = fps
        self.frame = 0
        self.timer = None
        self.loops = loops
        self.loop_count = 0
        self.done = False

    def get_next_frame(self, now):
        """
        Advance the frame if enough time has elapsed and the animation has
        not finished looping.
        """
        if not self.timer:
            self.timer = now
        if not self.done and now-self.timer > 1000.0/self.fps:
            self.frame = (self.frame+1)%len(self.frames)
            if not self.frame:
                self.loop_count += 1
                if self.loops != -1 and self.loop_count >= self.loops:
                    self.done = True
                    self.frame -= 1
            self.timer = now
        return self.frames[self.frame]

    def reset(self):
        """Set frame, timer, and loop status back to the initialized state."""
        self.frame = 0
        self.timer = None
        self.loop_count = 0
        self.done = False


class Timer(object):
    """
    A very simple timer for events that are not directly tied to animation.
    """
    def __init__(self, delay, ticks=-1):
        """
        The delay is given in milliseconds; ticks is the number of ticks the
        timer will make before flipping self.done to True.  Pass a value
        of -1 to bypass this.
        """
        self.delay = delay
        self.ticks = ticks
        self.tick_count = 0
        self.timer = None
        self.done = False

    def check_tick(self, now):
        """Returns true if a tick worth of time has passed."""
        if not self.timer:
            self.timer = now
            return True
        elif not self.done and now-self.timer > self.delay:
            self.tick_count += 1
            self.timer = now
            if self.ticks != -1 and self.tick_count >= self.ticks:
                self.done = True
            return True


class _BaseSprite(pg.sprite.Sprite):
    """
    A very basic base class that contains some commonly used functionality.
    """
    def __init__(self, pos, size, *groups):
        pg.sprite.Sprite.__init__(self, *groups)
        self.rect = pg.Rect(pos, size)
        self.exact_position = list(self.rect.topleft)
        self.old_position = self.exact_position[:]

    @property
    def frame_speed(self):
        """
        Returns the total displacement undergone in a frame. Used for the
        interpolation of the sprite's location in the draw phase.
        """
        return (self.exact_position[0]-self.old_position[0],
                self.exact_position[1]-self.old_position[1])

    def reset_position(self, value, attribute="topleft"):
        """
        Set the sprite's location variables to a new point.  The attribute
        argument can be specified to assign to a chosen attribute of the
        sprite's rect.
        """
        setattr(self.rect, attribute, value)
        self.exact_position = list(self.rect.topleft)
        self.old_position = self.exact_position[:]

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def on_map_change(self):
        pass


### Resource loading functions.
def load_all_gfx(directory,colorkey=(255,0,255),accept=(".png",".jpg",".bmp")):
    """
    Load all graphics with extensions in the accept argument.  If alpha
    transparency is found in the image the image will be converted using
    convert_alpha().  If no alpha transparency is detected image will be
    converted using convert() and colorkey will be set to colorkey.
    """
    graphics = {}
    for pic in os.listdir(directory):
        name,ext = os.path.splitext(pic)
        if ext.lower() in accept:
            img = pg.image.load(os.path.join(directory,pic))
            if img.get_alpha():
                img = img.convert_alpha()
            else:
                img = img.convert()
                img.set_colorkey(colorkey)
            graphics[name]=img
    return graphics


def load_all_music(directory, accept=(".wav",".mp3",".ogg",".mdi")):
    """
    Create a dictionary of paths to music files in given directory
    if their extensions are in accept.
    """
    songs = {}
    for song in os.listdir(directory):
        name,ext = os.path.splitext(song)
        if ext.lower() in accept:
            songs[name] = os.path.join(directory,song)
    return songs


def load_all_fonts(directory, accept=(".ttf",)):
    """
    Create a dictionary of paths to font files in given directory
    if their extensions are in accept.
    """
    return load_all_music(directory,accept)


def load_all_sfx(directory, accept=(".wav",".mp3",".ogg",".mdi")):
    """
    Load all sfx of extensions found in accept.  Unfortunately it is
    common to need to set sfx volume on a one-by-one basis.  This must be done
    manually if necessary.
    """
    effects = {}
    for fx in os.listdir(directory):
        name,ext = os.path.splitext(fx)
        if ext.lower() in accept:
            effects[name] = pg.mixer.Sound(os.path.join(directory,fx))
    return effects


def strip_from_sheet(sheet, start, size, columns, rows=1):
    """
    Strips individual frames from a sprite sheet given a start location,
    sprite size, and number of columns and rows.
    """
    frames = []
    for j in range(rows):
        for i in range(columns):
            location = (start[0]+size[0]*i, start[1]+size[1]*j)
            frames.append(sheet.subsurface(pg.Rect(location,size)))
    return frames


def strip_coords_from_sheet(sheet, coords, size):
    """Strip specific coordinates from a sprite sheet."""
    frames = []
    for coord in coords:
        location = (coord[0]*size[0], coord[1]*size[1])
        frames.append(sheet.subsurface(pg.Rect(location,size)))
    return frames


def get_cell_coordinates(rect, point, size):
    """Find the cell of size, within rect, that point occupies."""
    cell = [None, None]
    point = (point[0]-rect.x, point[1]-rect.y)
    cell[0] = (point[0]//size[0])*size[0]
    cell[1] = (point[1]//size[1])*size[1]
    return tuple(cell)


def cursor_from_image(image,size,hotspot,location=(0,0),flip=False):
    """
    This function's return value is of the form accepted by
    pg.mouse.set_cursor() (passed using the *args syntax). The argument image
    is an already loaded image surface containing your desired cursor; size is
    a single integer corresponding to the width of the cursor (must be a
    multiple of 8); hotspot is a 2-tuple representing the exact point in your
    cursor that will represent the mouse position; location is a 2-tuple for
    where your cursor is located on the passed in image. Setting flip to True
    will create the cursor with colors opposite to the source image.

    Color in image to color in cursor defaults:
        Black (  0,   0,   0) ---> Black
        White (255, 255, 255) ---> White
        Cyan  (  0, 255, 255) ---> Xor (only available on certain systems)
        Any Other Color ---------> Transparent
    """
    if size%8:
        raise ValueError("Size must be a multiple of 8.")
    compile_args = (".", "X", "o") if flip else ("X", ".", "o")
    colors = {(  0,  0,  0,255) : ".",
              (255,255,255,255) : "X",
              (  0,255,255,255) : "o"}
    cursor_string = []
    for j in range(size):
        this_row = []
        for i in range(size):
            where = (i+location[0], j+location[1])
            pixel = tuple(image.get_at(where))
            this_row.append(colors.get(pixel, " "))
        cursor_string.append("".join(this_row))
    xors,ands = pg.cursors.compile(cursor_string, *compile_args)
    size = size, size
    return size, hotspot, xors, ands


def get_rendered(font, text, color, cache):
    """Simple font renderer that caches render."""
    if text in cache:
        image = cache[text]
    else:
        image = font.render(text, 0, color)
        cache[text] = image
    return image


def rect_then_mask(one, two):
    """
    This is a callback function to be used with sprite group collision methods.
    It initially checks if two sprites have overlapping rectangles. If this is
    True, it will check if their masks collide and return the result.  If the
    rectangles were not colliding, the mask check is not performed.
    """
    return pg.sprite.collide_rect(one,two) and pg.sprite.collide_mask(one,two)
