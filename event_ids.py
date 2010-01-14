#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2009, 2010 by Steven Sproat
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

import wx

"""
IDs used by the program for event binding
"""

ID_CHANGE_TOOL = wx.NewId()       # change tool hotkey
ID_CLEAR_ALL = wx.NewId()         # remove everything from current tab
ID_CLEAR_ALL_SHEETS = wx.NewId()  # remove everything from all tabs
ID_CLEAR_SHEETS = wx.NewId()      # remove all drawings from all tabs, keep imgs
ID_COLOUR_GRID = wx.NewId()       # toggle colour grid
ID_DESELECT = wx.NewId()          # deselect shape
ID_EXPORT = wx.NewId()            # export sheet to image file
ID_EXPORT_ALL = wx.NewId()        # export every sheet to numbered image files
ID_EXPORT_PDF = wx.NewId()        # export->PDF
ID_FEEDBACK = wx.NewId()          # help->feedback
ID_EXPORT_PREF = wx.NewId()       # export->preferences
ID_FULLSCREEN = wx.NewId()        # toggle fullscreen
ID_HISTORY = wx.NewId()           # history viewer
ID_IMPORT_IMAGE = wx.NewId()      # import->Image
ID_IMPORT_PDF = wx.NewId()        # import->PDF
ID_IMPORT_PREF = wx.NewId()       # import->Preferences
ID_IMPORT_PS = wx.NewId()         # import->PS
ID_MOVE_UP = wx.NewId()           # move shape up
ID_MOVE_DOWN = wx.NewId()         # move shape down
ID_MOVE_TO_TOP = wx.NewId()       # move shape to the top
ID_MOVE_TO_BOTTOM = wx.NewId()    # move shape to the bottom
ID_NEW = wx.NewId()               # new window
ID_NEXT = wx.NewId()              # next sheet
ID_PASTE_NEW = wx.NewId()         # paste as new selection
ID_PREV = wx.NewId()              # previous sheet
ID_RELOAD_PREF = wx.NewId()       # reload preferences
ID_RENAME = wx.NewId()            # rename sheet
ID_REPORT_BUG = wx.NewId()        # report a problem
ID_RESIZE = wx.NewId()            # resize dialog
ID_ROTATE = wx.NewId()            # rotate dialog for image 90/180/270
ID_SHAPE_VIEWER = wx.NewId()      # view/edit shapes
ID_STATUSBAR = wx.NewId()         # toggle statusbar
ID_TOOL_PREVIEW = wx.NewId()      # toggle preview of tool
ID_TOOLBAR = wx.NewId()           # toggle toolbar
ID_TRANSPARENT = wx.NewId()       # toggle shape transparency
ID_TRANSLATE = wx.NewId()         # open translation URL
ID_UNDO_SHEET = wx.NewId()        # undo close sheet
ID_UPDATE = wx.NewId()            # update self