===============================================
vimg: Simple GTK Image Viewer for shell lovers.
===============================================

Common use:
-----------

::

  vimg                    # view all images in current dir
  vimg image.png          # view just image.png
  vimg dir/*.png          # view all png images in dir
  vimg dir                # view all images in dir
  vimg -r dir             # view recursively all images in dir

Shortcuts:
----------

**Normal Mode:**

::

  Space,j        next image
  Backspace,k    previous image
  i              show/hide info
  m              add/remove image from memory list
  o              next image in memory list
  p              previous image in memory list
  e              edit current image with external editor (see below)
  q              quit
  f              enter/exit fullscreen mode
  :              enter to command mode

**Fullscreen Mode:**

::

  j              scroll down
  k              scroll up
  h              scroll left
  l              scroll right

**Command Mode:**

::

  :cp  <target>  copy current image to directory or filename
  :mcp <target>  copy all images in memory to directory
  :q             quit
  Esc            return to normal mode

**Setting external editor:**

vimg uses the environment variable ``VIMG_EDITOR`` to set the external editor:

::

  export VIMG_EDITOR=/usr/bin/gimp
