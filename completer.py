#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" 
    vimg - Simple GTK Image Viewer for shell lovers.

    This file is part of vimg.
    
    vimg is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License version 3
    as published by the Free Software Foundation.
    
    vimg is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with vimg. If not, see <http://www.gnu.org/licenses/>.

    Author: Leonardo Vidarte - http://calcifer.com.ar

""" 

import gtk
import os

COMMANDS = {
    ':cp'   : True,
    ':mcp'  : True,
    #':mv'   : True,
    #':mmv'  : True,
    #':rm'   : False,
    #':mrm'  : False,
    ':q'    : False,
    #'pyar'  : False,
    #'python': False,
}

class Main:

    def __init__(self):
        self.entry = gtk.Entry()

        self.window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.connect('key-press-event', self.on_key_press)
        self.window.connect('delete-event', gtk.main_quit)
        self.window.add(self.entry)
        self.window.show_all()

        self.completer = Completer(tabkey=gtk.keysyms.Tab,
                            commands=COMMANDS, dotfiles=False)

    def on_key_press(self, widget, event):
        # Unica forma que encontre para posicionar
        # el cursor al final del texto
        self.entry.select_region(
            len(self.entry.get_text()),
            len(self.entry.get_text())+1)

        # Esc: salir
        if event.keyval == gtk.keysyms.Escape:
            gtk.main_quit()
        # Tab: autocompletar
        elif event.keyval == gtk.keysyms.Tab:
            self.entry.set_text(
                self.completer.complete(self.entry.get_text()))

        # Completer necesita saber si la ultima tecla fue Tab o no.
        self.completer.set_lastkey(event.keyval)

    def show(self):
        gtk.main()

class Completer:
    '''Clase para autocompletado de texto mediante Tab,
    similar al modo menu-complete usado por GNU readline.'''

    def __init__(self, tabkey, commands, dotfiles=True):
        '''tabkey es un entero con el valor de la tecla Tab (gtk.keysyms.Tab).

        commands es un diccionario con el listado de palabras/comandos,
        indicando en cada caso si se admite o no el parametro path:

            commands = {
                ':cp': True,        <- comando + path
                ':rm': False,       <- comando sin path
            }

        dotfiles hace que se listen o no los archivos ocultos cuando se
        ejecuta /algun_dir/<Tab>.
        En cualquier caso /algun_dir/.<Tab> funciona como es de esperarse.

        '''
        self.tabkey = tabkey
        self.commands = commands
        self.dotfiles = dotfiles
        self.lastkey = None
        self.basedir = None
        self.matches = []
        self.index = -1

    def complete(self, text):
        '''complete(text) -> string'''
        if not text.strip():
            return ''

        tokens = text.strip().split(' ', 1)

        # Command
        if len(tokens) == 1:
            if self.lastkey != self.tabkey:
                self.complete_word(tokens[0])
            tokens[0] = self.get_next_completion()
        # Path
        elif self.commands[tokens[0]]:
            if self.lastkey != self.tabkey or len(self.matches) == 2:
                self.complete_path(tokens[1])
            tokens[1] = os.path.join(self.basedir, self.get_next_completion())

        return ' '.join(tokens)

    def get_next_completion(self):
        '''get_next_completion() -> string'''
        if len(self.matches):
            if self.index == len(self.matches) - 1:
                self.index = 0
            else:
                self.index += 1
            return self.matches[self.index]

    def complete_word(self, token):
        '''complete_word(token) -> list'''
        self.matches = [token]
        self.index = 0
        for cmd in self.commands.keys():
            if cmd[0:len(token)] == token:
                self.matches.append(cmd)
        if len(self.matches) > 2:
            self.matches = sorted(self.matches)
        return self.matches

    def complete_path(self, token):
        '''complete_path(token) -> list'''
        if token[0:2] == '~/':
            token = os.path.expanduser(token)
        elif token[0] != '/':
            token = os.path.realpath(token)
        self.basedir = token[0:token.rfind('/')+1]
        q = token[len(self.basedir):]
        self.matches = [q]
        self.index = 0
        if os.path.isdir(self.basedir):
            try:
                listdir = os.listdir(self.basedir)
            except (OSError,):
                pass
            else:
                for entry in listdir:
                    if entry[0:len(q)] == q and not (q == '' and
                            entry[0] == '.' and not self.dotfiles):
                        if os.path.isdir(
                                os.path.join(self.basedir, entry)):
                            entry += '/'
                        self.matches.append(entry)
                if len(self.matches) > 2:
                    self.matches = sorted(self.matches)
        return self.matches

    def set_lastkey(self, lastkey):
        '''Completer necesita saber si la ultima tecla fue Tab o no,
        por eso el metodo que captura el evento key-press-event
        debe pasarle al final el valor de la tecla pulsada:

            def on_key_press(self, widget, event):
                if event.keyval == gtk.keysyms.Tab:
                    self.entry.set_text(
                        self.completer.complete(self.entry.get_text()))

                self.completer.set_lastkey(event.keyval)

        '''
        self.lastkey = lastkey

if __name__ == '__main__':
    main = Main()
    main.show()
