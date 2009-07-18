#!/usr/bin/python

# Copyright (c) 2009 by Steven Sproat
#
# GNU General Public Licence (GPL)
#
# Whyteboard is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.
# Whyteboard is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# You should have received a copy of the GNU General Public License along with
# Whyteboard; if not, write to the Free Software Foundation, Inc., 59 Temple
# Place, Suite 330, Boston, MA  02111-1307  USA


"""
This module contains the Whyteboard class, a window that can be drawn upon. Each
Whyteboard panel gets added to a tab in the GUI, and each Whyteboard maintains
a list of undo/redo actions for itself; thus each Whyteboard tab on the GUI has
its own undo/redo.
"""

import wx
import wx.lib.dragscroller
import copy

from tools import Image, Text, Note, Select, OverlayShape

#----------------------------------------------------------------------

class Whyteboard(wx.ScrolledWindow):
    """
    The drawing frame of the application.
    """
    def __init__(self, tab, gui):
        """
        Initalise the window, class variables and bind mouse/paint events
        """
        wx.ScrolledWindow.__init__(self, tab, style=wx.NO_FULL_REPAINT_ON_RESIZE
                                                        | wx.CLIP_CHILDREN )
        self.canvas_size = (1000, 1000)
        self.area = (1000, 1000)
        self.SetVirtualSizeHints(2, 2)
        self.SetVirtualSize(self.canvas_size)
        self.SetScrollRate(3, 3)

        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)  # no flicking on Windows!
        self.SetBackgroundColour("White")
        self.ClearBackground()
        self.scroller = wx.lib.dragscroller.DragScroller(self)
        self.overlay = wx.Overlay()

        self.gui = gui
        self.tab = tab
        self.shapes = []  # list of shapes for re-drawing/saving
        self.shape = None  # currently selected shape to draw with
        self.selected = None  # selected shape with Select tool
        self.text  = None  # current Text object for redraw all
        self.copy = None  # BitmapSelect instance
        self.undo_list = []
        self.redo_list = []
        self.drawing = False
        self.select_tool()
        self.buffer = wx.EmptyBitmap(*self.area)

        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_LEFT_DOWN, self.left_down)
        self.Bind(wx.EVT_LEFT_UP, self.left_up)
        self.Bind(wx.EVT_LEFT_DCLICK, self.left_double)
        self.Bind(wx.EVT_MIDDLE_DOWN, self.middle_down)
        self.Bind(wx.EVT_MIDDLE_UP, self.middle_up)
        self.Bind(wx.EVT_MOTION, self.left_motion)
        self.Bind(wx.EVT_PAINT, self.on_paint)


    def left_down(self, event):
        """Starts drawing, removes bitmap selection"""
        x, y = self.convert_coords(event)
        self.shape.button_down(x, y)
        self.drawing = True

    def left_motion(self, event):
        """Updates the shape. Indicate shape may be moved using Select tool"""
        x, y = self.convert_coords(event)

        #  Crashes without the Text check
        if self.drawing and not isinstance(self.shape, Text):
            self.shape.motion(x, y)
            self.draw_shape(self.shape)
        elif isinstance(self.shape, Select):

            for shape in (reversed(self.shapes)):
                if shape.handle_hit_test(x, y):
                    self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))
                    break
                if shape.hit_test(x, y):
                    self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
                    break
            else:
                self.change_cursor()

    def left_up(self, event):
        """
        Called when the left mouse button is released.
        """
        x, y = self.convert_coords(event)

        if self.drawing:
            before = len(self.shapes)
            self.shape.button_up(x, y)

            if len(self.shapes) - before:
                self.select_tool()
                self.update_thumb()
            self.drawing = False

    def left_double(self, event):
        """Double click for the Select tool - edit text"""
        x, y = self.convert_coords(event)
        if isinstance(self.shape, Select):
            self.shape.double_click(x, y)

    def redraw_dirty(self, dc):
        """
        Figure out what part of the window to refresh.
        """
        x1, y1, x2, y2 = dc.GetBoundingBox()
        x1, y1 = self.CalcScrolledPosition(x1, y1)
        x2, y2 = self.CalcScrolledPosition(x2, y2)

        rect = wx.Rect()
        rect.SetTopLeft((x1, y1))
        rect.SetBottomRight((x2, y2))
        rect.Inflate(2, 2)
        self.RefreshRect(rect)

    def redraw_all(self, update_thumb=False):
        """
        Redraws all shapes that have been drawn. self.text is used to show text
        characters as they're being typed, as new Text/Note objects have not
        been added to self.shapes at this point.
        """
        dc = wx.BufferedDC(None, self.buffer)
        dc.Clear()

        for s in self.shapes:
            s.draw(dc, True)
        if self.text:
            self.text.draw(dc, True)
        if self.copy:
            self.copy.draw(dc, True)
        self.Refresh()
        if update_thumb:
            self.update_thumb()


    def select_tool(self, new=None):
        """
        Changes the users' tool (and cursor) they are drawing with. new is an
        int, corresponding to new - 1 = Tool ID in Utility.items
        Can be called with no new ID to reset itself with the current tool
        """
        if not new:
            new = self.gui.util.tool
        else:
            self.gui.util.tool = new

        items = self.gui.util.items
        colour = self.gui.util.colour
        thickness = self.gui.util.thickness
        params = [self, colour, thickness]  # Object constructor parameters
        self.shape = None
        self.shape = items[new - 1](*params)  # create new Tool object
        self.change_cursor()
        self.gui.control.preview.Refresh()

    def change_cursor(self):
        if isinstance(self.shape.cursor, wx.Cursor):
            self.SetCursor(self.shape.cursor)
        else:
            self.SetCursor(wx.StockCursor(self.shape.cursor) )


    def add_shape(self, shape):
        """ Adds a shape to the "to-draw" list. """
        self.add_undo(shape)
        self.shapes.append(shape)

        if self.selected:
            self.deselect()
            self.redraw_all()
        if self.text:
            self.text = None
        if self.copy:
            self.copy = None
            self.redraw_all()


    def add_undo(self, shape=None):
        """ Creates an undo point """
        l = [copy.copy(x) for x in self.shapes]
        self.undo_list.append(l)

        if self.redo_list:
            self.redo_list = []
        if self.gui.util.saved:
            self.gui.util.saved = False

    def undo(self):
        """
        Undoes an action, and adds it to the redo list. Re-add any cleared shape
        one-by-one because each shape is then undoable
        """
        if not self.undo_list:
            return
        shapes = self.undo_list.pop()
        self.redo_list.append(list(self.shapes))
        self.gui.notes.tree.DeleteChildren(self.gui.notes.tabs[self.gui.tabs.GetSelection()])

        for x in shapes:
            if isinstance(x, Note):
                self.gui.notes.add_note(x)

        self.shapes = shapes
        self.deselect()
        self.redraw_all(True)


    def redo(self):
        """ Redoes an action, and adds it to the undo list. """
        if not self.redo_list:
            return
        shapes = self.redo_list.pop()
        self.undo_list.append(list(self.shapes))
        self.gui.notes.tree.DeleteChildren(self.gui.notes.tabs[self.gui.tabs.GetSelection()])

        for x in shapes:
            if isinstance(x, Note):
                self.gui.notes.add_note(x)

        self.shapes = shapes
        self.deselect()
        self.redraw_all(True)


    def clear(self, keep_images=False):
        """ Removes all shapes from the 'to-draw' list. """
        self.add_undo()
        images = []
        if keep_images:
            for x in self.shapes:
                if isinstance(x, Image):
                    images.append(x)

        self.shapes = images
        self.redraw_all(update_thumb=True)


    def convert_coords(self, event):
        """ Translate mouse x/y coords to virtual scroll ones. """
        return self.CalcUnscrolledPosition(event.GetX(), event.GetY())


    def middle_down(self, event):
        """ Begin dragging the scroller to move around the panel """
        self.SetCursor(wx.StockCursor(wx.CURSOR_SIZENESW))
        self.scroller.Start(event.GetPosition())

    def middle_up(self, event):
        """ Stop dragging the scroller. """
        self.scroller.Stop()
        self.change_cursor()  # bugfix with custom cursor

    def on_paint(self, event=None):
        """ Called when the window is exposed. """
        wx.BufferedPaintDC(self, self.buffer, wx.BUFFER_VIRTUAL_AREA)

    def deselect(self):
        for x in self.shapes:
            if isinstance(x, OverlayShape):
                x.selected = False
        if self.selected:
            self.draw_shape(self.selected, True)
            self.selected = None

    def get_dc(self):
        cdc = wx.ClientDC(self)
        self.PrepareDC(cdc)
        return wx.BufferedDC(cdc, self.buffer, wx.BUFFER_VIRTUAL_AREA)

    def draw_shape(self, shape, replay=False):
        """Redraws a single shape"""
        dc = self.get_dc()
        if replay:
            shape.draw(dc, replay)
        else:
            shape.draw(dc)
        self.redraw_dirty(dc)

    def get_tab(self):
        """ Returns the current tab number of this Whyteboard instance. """
        return self.tab.GetSelection()

    def update_thumb(self):
        """ Updates this tab's thumb """
        self.gui.thumbs.update(self.get_tab())

    def on_size(self, event):
        """ Updates the scrollbars when the window is resized. """
        size = self.GetClientSize()
        self.update_scrollbars(size)
        self.redraw_all()


    def update_scrollbars(self, new_size, ignore_min=False):
        """
        Updates the Whyteboard's scrollbars if the loaded image/text string
        is bigger than the scrollbar's current size.
        Ignore_min is used when the user is resizing the canvas manually
        """
        width, height = new_size
        x, y = width, height
        update = True
        if not ignore_min:
            if width > self.canvas_size[0]:
                x = width
            else:
                x = self.canvas_size[0]

            if height > self.canvas_size[1]:
                y = height
            else:
                y =  self.canvas_size[1]

            update = False
            #  update the scrollbars and the board's buffer size
            if x > self.canvas_size[0]:
                update = True
            elif y > self.canvas_size[1]:
                update = True

        if update:
            self.canvas_size = (x, y)
            self.buffer = wx.EmptyBitmap(*(x, y))
            self.SetVirtualSize((x, y))
            self.redraw_all()
        else:
            return False

#----------------------------------------------------------------------

if __name__ == '__main__':
    from gui import WhyteboardApp
    app = WhyteboardApp(False)
    app.MainLoop()
