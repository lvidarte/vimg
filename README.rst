===============================================
vimg: Simple GTK Image Viewer for shell lovers.
===============================================

Common use:
-----------

  vimg image.png              # view just image.png
  vimg ~/Images               # view all images in ~/Images
  vimg -r ~/Images            # view recursively all images in ~/Images
  vimg -w '*.png' ~/Images    # view all png images in ~/Images
  vimg -rw '*.png' ~/Images   # view recursively all png images in ~/Images

Shortcuts:
----------

**Normal Mode:**

::

  j,space        next image
  k,backspace    previous image
  f              enter/exit fullscreen
  i              show/hide info
  m              add/remove image from memory list
  o              next image in memory list
  p              previous image in memory list
  q              quit
  :              enter to command mode

  Only in fullscreen:

  j              scroll down
  k              scroll up
  h              scroll left
  l              scroll right

**Command Mode:**

::

  :cp  <target>  copy actual image to directory or filename
  :mcp <target>  copy all images in memory to directory
  :q             quit
  Esc            return to normal mode

