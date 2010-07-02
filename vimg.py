#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
    vimg - Extremely simple GTK Image Viewer for shell lovers.

    Author:
        Leonardo Vidarte - http://blog.calcifer.com.ar

    Licence:
        http://www.gnu.org/licenses/gpl.html GNU General Public License

    Thanks to:
        * Marcelo Fidel Fernández - http://www.marcelofernandez.info
          (I took some code/ideas from him).

    TODO: 
        * Diferent levels of zoom
        * Navigate mode for (only) saved images [op]
        * Simple save access (in the next available position) with key [m].
        * Replace keys by gtk.keysyms
"""

import pygtk
pygtk.require('2.0')
import gtk
#import gtk.keysyms as keys
keys = gtk.keysyms

from optparse import OptionParser
import os
import fnmatch
import sys

import glib

IMAGE_FORMATS = ('png', 'jpg', 'jpeg', 'gif', 'tif')

DEFAULT_WIDTH = 800 
DEFAULT_HEIGHT = 600 
DEFAULT_MARGIN = 25
BG_COLOR = 6000

OFFSET_GRAL = 25
MOVE_KEYS = {
    keys.H: (-OFFSET_GRAL, 0),
    keys.J: (0,  OFFSET_GRAL),
    keys.K: (0, -OFFSET_GRAL),
    keys.L: (OFFSET_GRAL, 0),
}
MEMORY_KEYS = {
    keys._0: None,
    keys._1: None,
    keys._2: None,
    keys._3: None,
    keys._4: None,
    keys._5: None,
    keys._6: None,
    keys._7: None,
    keys._8: None,
    keys._9: None,
}

NORMAL_MODE = 0
FULL_MODE = 1

# ============================================================================
# GTK STRUCTURE
# ============================================================================
# 1. ONLY IMAGE
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# * Window
#   * ScrolledWindow
#     * Viewport
#       * EventBox
#         * Image
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# 2. IMAGE + INFO
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# * Window
#  * VBox
#    * ScrolledWindow
#      * Viewport
#        * EventBox
#          * Image
#    * Label
# ============================================================================

class Vimg:

    # {{{ __init__(self)
    def __init__(self):

        # 
        self.vimg_mode = NORMAL_MODE
        self.img_paths = []
        self.img_cur_index = 0
        self.img_width = 0
        self.img_height = 0
        self.img_scaled_width = 0
        self.img_scaled_height = 0
        self.img_zoom = 0
        self.img_mem_indexes = []

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
            sys.stderr.write('Error: No images found.\n')
            sys.exit(1)
        else:
            print "%d images found." % len(self.img_paths,)

        # ------
        # Window
        # ------
        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_position(gtk.WIN_POS_CENTER_ALWAYS)
        self.window.connect("delete_event", self.close_application)
        #self.window.connect("delete_event", lambda w,e: gtk.main_quit())
        self.window.connect('key-press-event', self.on_key_press)

        # --------------
        # ScrolledWindow
        # --------------
        self.scrolled_window = gtk.ScrolledWindow()
        self.scrolled_window.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.window.add(self.scrolled_window)

        # --------
        # Viewport
        # --------
        self.viewport = gtk.Viewport()
        self.viewport.connect('button-press-event', self.on_button_pressed)
        self.viewport.connect('button-release-event', self.on_button_released)
        self.viewport.connect('motion-notify-event', self.on_mouse_moved)
        self.scrolled_window.add(self.viewport)

        # --------
        # EventBox
        # --------
        self.event_box = gtk.EventBox()
        #self.event_box.connect('button_press_event', self.destroy)
        self.event_box.modify_bg(
            gtk.STATE_NORMAL, gtk.gdk.Color(BG_COLOR, BG_COLOR, BG_COLOR))
        self.viewport.add(self.event_box)

        # -----
        # Image
        # -----
        self.image = gtk.Image()
        self.event_box.add(self.image)

        # ------------
        # Label (Info)
        # ------------
        self.label = gtk.Label()

        # ----------------
        # Show first image
        # ----------------
        self.show_image(self.img_cur_index)
        self.window.show_all()
    # }}}
    # {{{ parse_args(self)
    def parse_args(self):

        # -------------------
        # Program description
        # -------------------
        self.parser = OptionParser(
            prog="vimg",
            description="Extremely simple GTK Image Viewer for shell lovers.",
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
            print "%d. %s" % (self.img_cur_index, e.message)
            return

        # ----------------------------
        # Obtain size to display image
        # ----------------------------
        # no resize
        if self.vimg_mode == FULL_MODE or not adjust or \
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
        if self.vimg_mode == NORMAL_MODE or adjust:
            self.window.resize(self.img_scaled_width + DEFAULT_MARGIN,
                self.img_scaled_height + DEFAULT_MARGIN)

        # ---------------------------------------
        # Set window title, info and output shell
        # ---------------------------------------
        self.set_window_title()
        self.label.set_text(self.get_image_info())
        print self.get_image_info()

        #self.image.show()
        #self.event_box.show()
    # }}}
    # {{{ get_image_info(self)
    def get_image_info(self):
        info = "%d. %s (%sx%s)" % (
            self.img_cur_index, self.img_paths[self.img_cur_index],
            self.img_width, self.img_height)
        if self.in_memory(self.img_cur_index):
            return "%s [M:%s]" % (info, self.get_memory_key(self.img_cur_index))
        else:
            return info
    # }}}
    # {{{ set_window_title(self, title=None)
    def set_window_title(self, title=None):
        if title == None:
            title = '%s x %s (%s%%)' % (
                self.img_width, self.img_height, self.img_zoom)
        if self.in_memory(self.img_cur_index):
            title = "%s [M:%s]" % (title, self.get_memory_key(self.img_cur_index))
        self.window.set_title(title)
    # }}}
    # {{{ _move_image(self, h_offset, v_offset)
    def _move_image(self, h_offset, v_offset):
        # Horizontal
        h_adjust = self.viewport.props.hadjustment
        h_new = self._get_adjust(h_adjust, h_offset)
        self.viewport.set_hadjustment(h_new)
        # Vertical
        v_adjust = self.viewport.props.vadjustment
        v_new = self._get_adjust(v_adjust, v_offset)
        self.viewport.set_vadjustment(v_new)
    # }}}
    # {{{ _get_adjust(self, adjust, offset)
    def _get_adjust(self, adjust, offset):
        new = adjust.value + offset
        #print new, adjust.value, adjust.upper, adjust.lower, adjust.page_size
        if (new >= adjust.lower) and (new <= (adjust.upper - adjust.page_size)):
            adjust.value = new
        elif new > 0 and new > (adjust.upper - adjust.page_size):
            adjust.value = adjust.upper - adjust.page_size
        elif new < adjust.lower:
            adjust.value = adjust.lower

        return adjust
    # }}}
    # {{{ _get_memory_key(self, keycode)
    def _get_memory_key(self, keycode):
        return '%s' % (keycode - 48) # 48 => decimal code to number cero (0)
    # }}}
    # {{{ in_memory(self, index)
    def in_memory(self, index):
        return self.img_cur_index in MEMORY_KEYS.values()
    # }}}
    # {{{ get_memory_key(self, index)
    def get_memory_key(self, index):
        for keycode, _index in MEMORY_KEYS.items():
            if _index == index:
                return self._get_memory_key(keycode) 
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
            self._move_image(offset_x, offset_y)
        self.prevmousex = x
        self.prevmousey = y
    # }}}
    # {{{ on_key_press(self, widget, event)
    def on_key_press(self, widget, event):
        keycode = gtk.gdk.keyval_to_upper(event.keyval)
        newx = newy = 0

        # ===============
        # NEXT (space, j)
        # ===============
        if (keycode == keys.space) or (self.vimg_mode == NORMAL_MODE
                                     and keycode == keys.J):
            if self.img_cur_index < len(self.img_paths) -1:
                self.show_image(self.img_cur_index + 1)
            else:
                self.show_image(0)
        # =======================
        # PREVIOUS (backspace, k)
        # =======================
        elif (keycode == keys.P) or (self.vimg_mode == NORMAL_MODE
                                   and keycode == keys.K):
            if self.img_cur_index == 0:
                self.show_image(len(self.img_paths) - 1)
            else:
                self.show_image(self.img_cur_index - 1)
        # =========
        # FULL MODE
        # =========
        elif keycode == keys.F:
            if self.vimg_mode != FULL_MODE:
                self.vimg_mode = FULL_MODE
                #self.window.maximize()
                self.window.fullscreen()
                self.show_image(self.img_cur_index, adjust=False)
            else:
                self.vimg_mode = NORMAL_MODE
                #self.window.unmaximize()
                self.window.unfullscreen()
                self.show_image(self.img_cur_index, adjust=True)
        # =========
        # MOVE KEYS
        # =========
        elif keycode in MOVE_KEYS.keys():
            offset_x, offset_y = MOVE_KEYS[keycode]
            self._move_image(offset_x, offset_y)
            return True
        # ===========
        # MEMORY KEYS
        # ===========
        elif keycode in MEMORY_KEYS.keys():
            # Set
            if MEMORY_KEYS[keycode] is None:
                if self.in_memory(self.img_cur_index):
                    print "[M] WARN the image is currently saved on key %s." % (
                        self.get_memory_key(self.img_cur_index)
                    )
                else:
                    MEMORY_KEYS[keycode] = self.img_cur_index
                    print "[M] quick access for %d was saved on key %s" % (
                        self.img_cur_index, self._get_memory_key(keycode))
            # Unset
            elif MEMORY_KEYS[keycode] == self.img_cur_index:
                MEMORY_KEYS[keycode] = None
                print "[M] quick access for %d was unset from key %s" % (
                    self.img_cur_index, self._get_memory_key(keycode))
            # Show previous set
            else:
                self.show_image(MEMORY_KEYS[keycode])

            # Update window title and info
            self.set_window_title()
            self.label.set_text(self.get_image_info())
        # ====
        # INFO
        # ====
        elif keycode == keys.I:
            child = self.window.get_child()
            # ---------------
            # Info is not set
            # ---------------
            if type(child) == gtk.ScrolledWindow:
                self.window.remove(child)
                vbox = gtk.VBox()
                vbox.pack_start(child)
                self.label.set_text(self.get_image_info())
                vbox.pack_end(self.label, expand=False, fill=True, padding=5)
                self.window.add(vbox)
                self.window.show_all()
            # -------------------
            # Info is already set
            # -------------------
            elif type(child) == gtk.VBox:
                self.window.remove(child)
                self.scrolled_window.reparent(self.window)
        # ======
        # EDITOR
        # ======
        elif keycode == keys.E:
            editor = os.getenv('VIMG_EDITOR')
            if editor:
                from subprocess import call
                #self.window.iconify() # don't work!
                retcode = call([IMAGE_EDITOR, self.img_paths[self.img_cur_index]])
                if retcode == 0:
                    #self.window.deiconify() # don't work!
                    self.show_image(self.img_cur_index, adjust=True)
            else:
                print '[!] Environment variable VIMG_EDITOR is not set.'
        # ========
        # QUIT (q)
        # ========
        elif keycode == keys.Q:
            gtk.main_quit()
            sys.exit(0)
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
    # {{{ close_application(self, widget, data=None):
    def close_application(self, widget, data=None):
        gtk.main_quit()
    # }}}
    # {{{ main(self)
    def main(self):
        gtk.main()
    # }}}

if __name__ == "__main__":
    vimg = Vimg()
    vimg.main()
