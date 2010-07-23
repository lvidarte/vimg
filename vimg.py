#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
    vimg - Simple GTK Image Viewer for shell lovers.

    Author:
        Leonardo Vidarte - http://blog.calcifer.com.ar

    Licence:
        http://www.gnu.org/licenses/gpl.html GNU General Public License

    Thanks to:
        * Marcelo Fidel Fernández - http://www.marcelofernandez.info
          (I took some code/ideas from him).

    TODO: 
        * Diferent levels of zoom
        * Copy actual image (:cp) @done
        * Copy images in memory (:mcp) @done
        * Move, Delete images in memory list.
        * No-verbose option.
        * Navigate mode for (only) saved images [op] @done
        * Simple save access (in the next available position) with key [m]. @done
        * Replace keys by gtk.keysyms @done
        * Replace environment variables by config file?
"""

import gtk
import os
import fnmatch
import sys
import glib
import shutil
from optparse import OptionParser

IMAGE_FORMATS = ('png', 'jpg', 'jpeg', 'gif', 'tif')

SCREEN = gtk.gdk.Screen()

DEFAULT_WIDTH = int(SCREEN.get_width() * 0.8) # 80% of screen width
DEFAULT_HEIGHT = int(SCREEN.get_height() * 0.8) # 80% of screen height
DEFAULT_MARGIN = 25
BG_COLOR = 6000

OFFSET_GRAL = 25
MOVE_KEYS = {
    gtk.keysyms.h: (-OFFSET_GRAL, 0),
    gtk.keysyms.j: (0,  OFFSET_GRAL),
    gtk.keysyms.k: (0, -OFFSET_GRAL),
    gtk.keysyms.l: (OFFSET_GRAL, 0),
}

NORMAL_WINDOW = 0
FULL_WINDOW = 1

# ============================================================================
# GTK STRUCTURE
# ============================================================================
# * Window
#  * VBox
#    * ScrolledWindow
#      * Viewport
#        * EventBox
#          * Image
#    * Entry
#    * Label
# ============================================================================

class Vimg:

    # {{{ __init__(self)
    def __init__(self):

        # 
        self.vimg_window_state = NORMAL_WINDOW
        self.img_paths = []
        self.img_cur_index = 0
        self.img_width = 0
        self.img_height = 0
        self.img_scaled_width = 0
        self.img_scaled_height = 0
        self.img_zoom = 0
        self.img_mem_indexes = []
        self.img_mem_cur_index = -1 # memory empty

        # ---------------
        # Parse arguments
        # ---------------
        (options, args) = self.parse_args()

        # ---------------
        # Get images list
        # ---------------
        self.img_paths = self.get_images_list(
            args[0], options.recursive, options.wildcard)
        if len(self.img_paths) == 0:
            print('No images found.')
            sys.exit(0)
        else:
            print("%d images found." % len(self.img_paths,))

        # ------------
        # Label (Info)
        # ------------
        self.label = gtk.Label()
        #self.label.show()

        # -----
        # Entry
        # -----
        self.entry = gtk.Entry()
        #self.entry.show()

        # -----
        # Image
        # -----
        self.image = gtk.Image()
        self.image.show()

        # --------
        # EventBox
        # --------
        self.event_box = gtk.EventBox()
        #self.event_box.connect('button_press_event', self.destroy)
        self.event_box.modify_bg(
            gtk.STATE_NORMAL, gtk.gdk.Color(BG_COLOR, BG_COLOR, BG_COLOR))
        self.event_box.add(self.image)
        self.event_box.show()

        # --------
        # Viewport
        # --------
        self.viewport = gtk.Viewport()
        self.viewport.connect('button-press-event', self.on_button_pressed)
        self.viewport.connect('button-release-event', self.on_button_released)
        self.viewport.connect('motion-notify-event', self.on_mouse_moved)
        self.viewport.add(self.event_box)
        self.viewport.show()

        # --------------
        # ScrolledWindow
        # --------------
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC,
                                        gtk.POLICY_AUTOMATIC)
        self.scrolled_window.add(self.viewport)
        self.scrolled_window.show()

        # ----
        # VBox
        # ----
        self.vbox = gtk.VBox()
        self.vbox.pack_start(self.scrolled_window)
        self.vbox.pack_end(self.label, expand=False, fill=True, padding=5)
        self.vbox.pack_end(self.entry, expand=False, fill=True, padding=5)
        self.vbox.show()

        # ------
        # Window
        # ------
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.connect("delete_event", lambda *args: gtk.main_quit())
        self.window.connect('key-press-event', self.on_key_press)
        self.window.add(self.vbox)
        self.window.show()

        # ----------------
        # Show first image
        # ----------------
        self.show_image(self.img_cur_index)
    # }}}
    # {{{ main(self)
    def main(self):
        gtk.main()
    # }}}
    # {{{ parse_args(self)
    def parse_args(self):

        # -------------------
        # Program description
        # -------------------
        self.parser = OptionParser(
            prog="vimg",
            description="Simple GTK Image Viewer for shell lovers.",
            usage="%prog [OPTIONS] FILEPATH",
            version="%prog 0.0.1"
        )

        # ----------------
        # Recursive option
        # ----------------
        self.parser.add_option("-r",
            dest="recursive", 
            action="store_true",
            help="Recursive"
        )

        # ----------------
        # Wildcards option
        # ----------------
        self.parser.add_option("--wildcard", "-w",
            type="string",
            dest="wildcard", 
            metavar="pattern",
            help="Unix shell-style wildcards: '*.png'"
        )

        (options, args) = self.parser.parse_args()

        if len(args) == 0:
            self.parser.print_help()
            sys.exit(1)

        return (options, args)
    # }}}
    # {{{ get_images_list(self, filepath, recursive=None, wildcard=None)
    def get_images_list(self, filepath, recursive=None, wildcard=None):

        images = []

        # -------------------
        # Path is a directory
        # -------------------
        if os.path.isdir(filepath):
            if recursive:
                for dirname, dirnames, filenames in os.walk(filepath):
                    for filename in filenames:
                        if self.check_filename(filename, wildcard):
                            images.append(os.path.join(dirname, filename))
            else:
                for filename in os.listdir(filepath):
                    if self.check_filename(filename, wildcard):
                        images.append(os.path.join(filepath, filename))
        # -------------------
        # Path is just a file
        # -------------------
        elif os.path.isfile(filepath) and self.check_filename(filepath, wildcard):
            images.append(filepath)

        return images
    # }}}
    # {{{ check_filename(self, filename, wildcard=None)
    def check_filename(self, filename, wildcard=None):

        if wildcard:
            return fnmatch.fnmatch(filename, wildcard)
        else:
            return filename.split('.')[-1] in IMAGE_FORMATS

    # }}}
    # {{{ show_image(self, index, adjust=True)
    def show_image(self, index, adjust=True):

        # ----------------------
        # Set actual image index
        # ----------------------
        if index >= 0 and index < len(self.img_paths):
            self.img_cur_index = index
        else:
            raise KeyError
            return

        # -----------------
        # Read actual image
        # -----------------
        try:
            self.pixbuf = gtk.gdk.pixbuf_new_from_file(self.img_paths[index])
            self.img_width = self.pixbuf.get_width()
            self.img_height = self.pixbuf.get_height()
        except glib.GError, e:
            print("%d. %s" % (self.img_cur_index, e.message))
            return

        # ----------------------------
        # Obtain size to display image
        # ----------------------------
        # no resize
        if self.vimg_window_state == FULL_WINDOW or not adjust or \
                (self.img_width <= DEFAULT_WIDTH
                and self.img_height <= DEFAULT_HEIGHT):
            self.image.set_from_pixbuf(self.pixbuf)
            self.img_scaled_width = self.img_width
            self.img_scaled_height = self.img_height
        # resize
        else:
            self.img_scaled_width = int(
                self.img_width * DEFAULT_HEIGHT / self.img_height)
            self.img_scaled_height = int(
                self.img_height * DEFAULT_WIDTH / self.img_width)

            if self.img_scaled_width > DEFAULT_WIDTH:
                self.img_scaled_width = DEFAULT_WIDTH
            elif self.img_scaled_height > DEFAULT_HEIGHT:
                self.img_scaled_height = DEFAULT_HEIGHT
            else:
                self.img_scaled_width = DEFAULT_WIDTH
                self.img_scaled_height = DEFAULT_HEIGHT

            scaled_buf = self.pixbuf.scale_simple(
                self.img_scaled_width, self.img_scaled_height,
                gtk.gdk.INTERP_BILINEAR)
            self.image.set_from_pixbuf(scaled_buf)

        # ----------------------------
        # Obtain actual zoom level (%)
        # ----------------------------
        self.img_zoom = round(
            float(self.img_scaled_width) / float(self.img_width) * 100, 1)

        # ----------------------------------
        # Adjust window size to actual image
        # ----------------------------------
        extra = 30 if self.label.flags() & gtk.VISIBLE else 0
        if self.vimg_window_state == NORMAL_WINDOW or adjust:
            self.window.resize(self.img_scaled_width + DEFAULT_MARGIN,
                self.img_scaled_height + DEFAULT_MARGIN + extra)

        # ---------------------------------------
        # Set window title, info and output shell
        # ---------------------------------------
        self.set_window_title()
        self.label.set_text(self.get_image_info())
        print(self.get_image_info())
    # }}}
    # {{{ get_image_info(self)
    def get_image_info(self):
        m = ' [M]' if self.img_cur_index in self.img_mem_indexes else ''
        info = "%d. %s (%sx%s)%s" % (
            self.img_cur_index, self.img_paths[self.img_cur_index],
            self.img_width, self.img_height, m)
        return info
    # }}}
    # {{{ set_window_title(self, title=None)
    def set_window_title(self, title=None):
        m = ' [M]' if self.img_cur_index in self.img_mem_indexes else ''
        if title == None:
            title = '%s x %s (%s%%)%s' % (
                self.img_width, self.img_height, self.img_zoom, m)
        self.window.set_title(title)
    # }}}
    # {{{ __move_image(self, h_offset, v_offset)
    def __move_image(self, h_offset, v_offset):
        # Horizontal
        h_adjust = self.viewport.props.hadjustment
        h_new = self.__get_adjust(h_adjust, h_offset)
        self.viewport.set_hadjustment(h_new)
        # Vertical
        v_adjust = self.viewport.props.vadjustment
        v_new = self.__get_adjust(v_adjust, v_offset)
        self.viewport.set_vadjustment(v_new)
    # }}}
    # {{{ __get_adjust(self, adjust, offset)
    def __get_adjust(self, adjust, offset):
        new = adjust.value + offset
        #print(new, adjust.value, adjust.upper,
        #            adjust.lower, adjust.page_size)
        if (new >= adjust.lower) and (
                new <= (adjust.upper - adjust.page_size)):
            adjust.value = new
        elif new > 0 and new > (adjust.upper - adjust.page_size):
            adjust.value = adjust.upper - adjust.page_size
        elif new < adjust.lower:
            adjust.value = adjust.lower

        return adjust
    # }}}
    # {{{ on_mouse_moved(self, widget, event)
    def on_mouse_moved(self, widget, event):
        # @see http://www.pygtk.org/pygtk2tutorial-es/sec-EventHandling.html
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            state = event.state
        x, y = event.x_root, event.y_root
        if state & gtk.gdk.BUTTON1_MASK:
            offset_x = self.prevmousex - x
            offset_y = self.prevmousey - y
            self.__move_image(offset_x, offset_y)
        self.prevmousex = x
        self.prevmousey = y
    # }}}
    # {{{ on_key_press(self, widget, event)
    def on_key_press(self, widget, event):
        #keycode = gtk.gdk.keyval_to_upper(event.keyval)
        #keycode = gtk.gdk.keyval_name(event.keyval)
        keycode = event.keyval
        #print keycode
        newx = newy = 0

        # =======
        # Command
        # =======
        if self.entry.flags() & gtk.VISIBLE:
            if keycode == gtk.keysyms.colon:
                self.entry.set_text('')
            if keycode == gtk.keysyms.Escape:
                self.entry.hide()
                #self.window.set_focus(self.window)
            if keycode == gtk.keysyms.Return:
                self.parse_entry()
        # ======
        # Normal
        # ======
        elif event.keyval == gtk.keysyms.colon:
            self.entry.show()
            self.window.set_focus(self.entry)
        else:
            # ===============
            # NEXT (space, j)
            # ===============
            if (keycode == gtk.keysyms.space) or (
                    self.vimg_window_state == NORMAL_WINDOW and \
                    keycode == gtk.keysyms.j):
                if self.img_cur_index < len(self.img_paths) -1:
                    self.show_image(self.img_cur_index + 1)
                else:
                    self.show_image(0)
            # =======================
            # PREVIOUS (backspace, k)
            # =======================
            elif (keycode == gtk.keysyms.BackSpace) or (
                    self.vimg_window_state == NORMAL_WINDOW and \
                    keycode == gtk.keysyms.k):
                if self.img_cur_index == 0:
                    self.show_image(len(self.img_paths) - 1)
                else:
                    self.show_image(self.img_cur_index - 1)
            # ======================
            # ENTER/EXIT FULL WINDOW
            # ======================
            elif keycode == gtk.keysyms.f:
                if self.vimg_window_state != FULL_WINDOW:
                    self.vimg_window_state = FULL_WINDOW
                    #self.window.maximize()
                    self.window.fullscreen()
                    self.show_image(self.img_cur_index, adjust=False)
                else:
                    self.vimg_window_state = NORMAL_WINDOW
                    #self.window.unmaximize()
                    self.window.unfullscreen()
                    self.show_image(self.img_cur_index, adjust=True)
            # =========
            # MOVE KEYS
            # =========
            elif keycode in MOVE_KEYS.keys():
                offset_x, offset_y = MOVE_KEYS[keycode]
                self.__move_image(offset_x, offset_y)
                return True
            # ======
            # MEMORY
            # ======
            elif keycode == gtk.keysyms.m:
                # Remove
                if self.img_cur_index in self.img_mem_indexes:
                    index = self.img_mem_indexes.index(self.img_cur_index)
                    del self.img_mem_indexes[index]
                    if index == 0:
                        self.img_mem_cur_index = len(self.img_mem_indexes) - 1
                    else:
                        self.img_mem_cur_index = index - 1
                    print("[M] Removed quick access for image %d." % (
                                                        self.img_cur_index))
                # Add
                else:
                    self.img_mem_indexes.append(self.img_cur_index)
                    self.img_mem_cur_index = len(self.img_mem_indexes) - 1
                    print("[M] Added quick access for image %d." % (
                                                        self.img_cur_index))
                #print(self.img_mem_cur_index)
                self.set_window_title()
                self.label.set_text(self.get_image_info())
            # ==============
            # MEMORY BROWSER
            # ==============
            elif keycode == gtk.keysyms.o and len(self.img_mem_indexes):
                if self.img_mem_cur_index < len(self.img_mem_indexes) -1:
                    self.img_mem_cur_index += 1
                    self.show_image(self.img_mem_indexes[self.img_mem_cur_index])
                else:
                    self.img_mem_cur_index = 0
                    self.show_image(self.img_mem_indexes[self.img_mem_cur_index])
                #print(self.img_mem_cur_index)
            elif keycode == gtk.keysyms.p and len(self.img_mem_indexes):
                if self.img_mem_cur_index == 0:
                    self.img_mem_cur_index = len(self.img_mem_indexes) - 1
                    self.show_image(self.img_mem_indexes[self.img_mem_cur_index])
                else:
                    self.img_mem_cur_index -= 1
                    self.show_image(self.img_mem_indexes[self.img_mem_cur_index])
                #print(self.img_mem_cur_index)
            # ====
            # INFO
            # ====
            elif keycode == gtk.keysyms.i:
                if self.label.flags() & gtk.VISIBLE:
                    self.label.hide()
                else:
                    self.label.show()
            # ======
            # EDITOR
            # ======
            elif keycode == gtk.keysyms.e:
                editor = os.getenv('VIMG_EDITOR')
                if editor:
                    from subprocess import call
                    #self.window.iconify() # don't work!
                    retcode = call([editor, self.img_paths[self.img_cur_index]])
                    if retcode == 0:
                        #self.window.deiconify() # don't work!
                        self.show_image(self.img_cur_index, adjust=True)
                else:
                    print('[!] Environment variable VIMG_EDITOR is not set.')
            # ========
            # QUIT (q)
            # ========
            elif keycode == gtk.keysyms.q:
                gtk.main_quit()
                sys.exit(0)
    # }}}
    # {{{ parse_entry(self)
    def parse_entry(self):
        entry = self.entry.get_text().split()

        # ====
        # Quit
        # ====
        if entry[0] == ':q':
            gtk.main_quit()
            sys.exit(0)
        # ====
        # Copy
        # ====
        if entry[0] == ':cp':
            if len(entry) != 2:
                self.entry.set_text('E02: Target directory or filepath required')
            else:
                try:
                    shutil.copy2(
                        os.path.abspath(self.img_paths[self.img_cur_index]),
                        os.path.abspath(entry[1]))
                except IOError as e:
                    self.entry.set_text(e.__str__())
                else:
                    self.entry.set_text('OK: File copied')
        # ========
        # Mem Copy
        # ========
        elif entry[0] == ':mcp':
            if len(self.img_mem_indexes) == 0:
                self.entry.set_text("E04: Memory is empty (Try `m' to add)")
            elif len(entry) != 2:
                self.entry.set_text('E03: Target directory required')
            elif not os.path.exists(entry[1]):
                self.entry.set_text('E05: Target directory do not exist')
            elif not os.path.isdir(entry[1]):
                self.entry.set_text('E06: Target must be a directory')
            else:
                filenames = []
                for index in self.img_mem_indexes:
                    filename = os.path.basename(self.img_paths[index])
                    if filename in filenames:
                        self.entry.set_text(
                            'E07: Files have same name: Abort copy')
                        return
                    else:
                        filenames.append(filename)
                for index in self.img_mem_indexes:
                    try:
                        shutil.copy2(
                            os.path.abspath(self.img_paths[index]),
                            os.path.join(os.path.abspath(entry[1]),
                                os.path.basename(self.img_paths[index])))
                    except IOError as e:
                        self.entry.set_text(e.__str__())
                        return
                    self.entry.set_text('OK: Files copied')
        # =======
        # Unknown
        # =======
        else:
            self.entry.set_text('E01: Command unknown')

    # }}}
    # {{{ on_button_pressed(self, widget, event)
    def on_button_pressed(self, widget, event):
        if event.button == 1:
            self.change_vport_cursor(gtk.gdk.Cursor(gtk.gdk.FLEUR))
            self.prevmousex = event.x_root
            self.prevmousey = event.y_root
        return True
    # }}}
    # {{{ on_button_released(self, widget, event)
    def on_button_released(self, widget, event):
        if event.button == 1:
            self.change_vport_cursor(None)
        return True
    # }}}
    # {{{ change_vport_cursor(self, type)
    def change_vport_cursor(self, type):
        self.viewport.window.set_cursor(type)
    # }}}

if __name__ == "__main__":
    vimg = Vimg()
    vimg.main()
