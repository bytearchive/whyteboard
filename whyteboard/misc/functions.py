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


"""
Contains generic functions for the program that are not dependent on any other
classes, only Python and wx functionality.
"""

import os
import subprocess
import sys
import random
import tarfile
import urllib
import webbrowser

import wx
from wx.lib.buttons import GenBitmapButton, GenBitmapToggleButton

from distutils.dir_util import copy_tree, remove_tree

from whyteboard.lib import pub

_ = wx.GetTranslation
path = os.path.split(os.path.abspath(sys.argv[0]))

#----------------------------------------------------------------------

def get_home_dir(extra_path=None):
    """
    Returns the home directory for Whyteboard in a cross-platform way
    If the extra path is supplied, it is appended to the home directory.
    The directory is verified to see if it exists: if doesn't, it is created.
    """
    std_paths = wx.StandardPaths.Get()
    path = wx.StandardPaths.GetUserLocalDataDir(std_paths)
    if extra_path:
        path = os.path.join(path, extra_path, "")   # "" forces slash at end

    if not os.path.isdir(path):
        os.makedirs(path)
    return path


def get_time(seconds):
    """Returns an (h:)m:s time from a seconds value - hour not shown if < 0"""
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)

    if h > 0:
        h = u"%d:" % h
    else:
        h = u""
    return h + u"%02d:%02d" % (m, s)


def file_dialog(gui, title, style, wildcard, defaultDir="", defaultFile=""):
    """
    Returns the result of a file dialog
    """
    dlg = wx.FileDialog(gui, title, style=style, wildcard=wildcard,
                        defaultDir=defaultDir, defaultFile=defaultFile)
    if dlg.ShowModal() == wx.ID_OK:
        return dlg.GetPath()
    return False


def load_image(path, canvas, image_class):
    """
    Loads an image into the given Whyteboard tab. bitmap is the path to an
    image file to create a bitmap from.
    image_class = tools.Image *CLASS ITSELF*
    """
    image = wx.Bitmap(path)
    shape = image_class(canvas, image, path)
    shape.left_down(0, 0)  # renders, updates scrollbars
    pub.sendMessage('thumbs.update_current')


def create_colour_bitmap(colour):
    """
    Draws a small coloured bitmap for a colour grid button. Can take a name,
    RGB tupple or RGB-packed int.
    """
    bmp = wx.EmptyBitmap(20, 20)
    dc = wx.MemoryDC()
    dc.SelectObject(bmp)
    dc.SetBackground(wx.Brush(colour))
    dc.Clear()
    dc.SelectObject(wx.NullBitmap)
    return bmp


def bitmap_button(parent, path, border=True, toggle=False):
    """
    Creates a platform-dependent bitmap button that's toggleable or not.
    """
    _type = GenBitmapToggleButton
    if not toggle:
        _type = GenBitmapButton
        if os.name == "posix":
            _type = wx.BitmapButton

    style = 0
    if not border:
        style = wx.NO_BORDER

    return _type(parent, bitmap=wx.Bitmap(path), style=style)


def get_wx_image_type(filename):
    """
    Returns the wx.BITMAP_TYPE_X for a given filename
    """
    _name = os.path.splitext(filename)[1].replace(".", "").lower()

    types = {"png": wx.BITMAP_TYPE_PNG, "jpg": wx.BITMAP_TYPE_JPEG,
             "jpeg": wx.BITMAP_TYPE_JPEG, "bmp": wx.BITMAP_TYPE_BMP,
             "tiff": wx.BITMAP_TYPE_TIF, "pcx": wx.BITMAP_TYPE_PCX }

    return types[_name]  # grab the right image type from dict. above


def convert_quality(quality, im_location, _file, path):
    """Returns a string for controlling the convert quality"""
    density = 200
    resample = 88

    if quality == 'highest':
        density = 300
        resample = 120
    if quality == 'high':
        density = 250
        resample = 100
    cmd = (u'"%s" -density %i "%s" -resample %i -unsharp 0x.5 -trim +repage -bordercolor white -border 20 "%s"'
           % (im_location, density, _file, resample, path))
    return cmd


def make_filename():
    """
    Create a random filename using letters, numbers and other characters
    """
    alphabet = (u"abcdefghijklmnopqrstuvwxyz1234567890-+!^&()=[]@$%_ ABCDEFGHIJKLMNOPQRSTUVWXYZ")
    _list = []
    for x in random.sample(alphabet, random.randint(8, 20)):
        _list.append(x)

    string = u"".join(_list)
    return string + u"-temp-%s" % (random.randrange(0, 999999))


def get_clipboard():
    """
    Gets the clipboard's contents, or False for any valid image/text data
    """
    bmp = wx.BitmapDataObject()
    wx.TheClipboard.Open()
    success = wx.TheClipboard.GetData(bmp)
    wx.TheClipboard.Close()
    if success:
        return bmp
    text = wx.TextDataObject()
    wx.TheClipboard.Open()
    success = wx.TheClipboard.GetData(text)
    wx.TheClipboard.Close()
    if success:
        return text
    return False


def check_clipboard():
    """
    Checks whether supported data is on the clipboard
    """
    if not wx.TheClipboard.IsOpened():
        wx.TheClipboard.Open()
        success = wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_BITMAP))
        success2 = wx.TheClipboard.IsSupported(wx.DataFormat(wx.DF_TEXT))
        wx.TheClipboard.Close()
        return success or success2
    return False


def set_clipboard(bitmap):
    """
    Sets the clipboard with bitmap image data
    """
    bmp = wx.BitmapDataObject()
    bmp.SetBitmap(bitmap)

    wx.TheClipboard.Open()
    wx.TheClipboard.SetData(bmp)
    wx.TheClipboard.Close()


def transparent_supported():
    """
    Does this wxPython build support transparency?
    """
    try:
        dc = wx.MemoryDC()
        dc.SelectObject(wx.EmptyBitmap(10, 10))
        x = wx.GCDC(dc)
        return True
    except NotImplementedError:
        return False


def is_exe():
    """
    Determine if Whyteboard is being run as an exe
    """
    return hasattr(sys, u"frozen")


def is_save_file(name):
    return name.lower().endswith(u".wtbd")

def show_dialog(_class, modal=True):
    if modal:
        _class.ShowModal()
    else:
        _class.Show()


def open_url(url):
    wx.BeginBusyCursor()
    webbrowser.open_new_tab(url)
    wx.CallAfter(wx.EndBusyCursor)


def new_instance():
    program = (u'python', os.path.abspath(sys.argv[0]))
    if is_exe():
        program = os.path.abspath(sys.argv[0])

    subprocess.Popen(program)


def fix_std_sizer_tab_order(sizer):
    """
    Fixes wx.StdDialogButtonSizer's tab ordering
    """
    buttons = []
    for child in sizer.GetChildren():
        win = child.GetWindow()
        if win is not None:
            buttons.append(win)
    if len(buttons) >= 1:
        buttons[1].MoveAfterInTabOrder(buttons[0])


def format_bytes(total):
    """
    Turn an amount of byte into readable KB/MB format
    http://www.5dollarwhitebox.org/drupal/node/84
    """
    _bytes = float(total)
    if _bytes >= 1048576:
        megabytes = _bytes / 1048576
        size = u'%.2fMB' % megabytes
    elif _bytes >= 1024:
        kilobytes = _bytes / 1024
        size = u'%.2fKB' % kilobytes
    else:
        size = u'%.2fb' % _bytes
    return size


def get_version_int(version):
    """
    Turns a version string like 0.40.2 into [0, 40, 2]
    """
    num = [int(x) for x in version.split(u".")]
    if len(num) == 2:
        num.append(0)
    return num


def version_is_greater(version1, version2):
    """
    Checks whether the first version is greater than the 2nd
    """
    a = get_version_int(version1)
    b = get_version_int(version2)

    return b[1] < a[1] or (b[1] == a[1] and b[2] < a[2])


def download_help_files(path):
    """
    Downloads the help files to the user's directory and shows them
    """
    _file = os.path.join(path, u"whyteboard-help.tar.gz")
    url = u"http://whyteboard.googlecode.com/files/help-files.tar.gz"
    tmp = None
    try:
        tmp = urllib.urlretrieve(url, _file)
    except IOError:
        wx.MessageBox(_("Could not connect to server.\n Check your Internet connection and firewall settings"), u"Whyteboard")
        raise IOError

    if os.name == "posix":
        os.system(u"tar -xf " + tmp[0])
    else:
        tar = tarfile.open(tmp[0])
        tar.extractall(path)
        tar.close()
    os.remove(tmp[0])


def extract_tar(path, _file, version, backup_extension):
    """
    Extract a .tar.gz source file on Windows, without needing to use the
    'tar' command, and with no other downloads!
    """
    tar = tarfile.open(_file)
    tar.extractall(path)
    tar.close()
    # remove 2 folders that will be updated, may not exist
    src = os.path.join(path, u"whyteboard-" + version)

    # rename all relevant files - ignore any dirs
    for f in os.listdir(path):
        location = os.path.join(path, f)
        if not os.path.isdir(location):
            _type = os.path.splitext(f)

            if _type[1] in [u".py", u".txt"]:
                new_file = os.path.join(path, _type[0]) + backup_extension
                os.rename(location, new_file)

    # move extracted file to current dir, remove tar, remove extracted dir
    copy_tree(src, path)
    remove_tree(src)


def help_file_path():
    return os.path.join(get_path(), u'whyteboard-help', u'whyteboard.hhp')

def get_path():
    """
    Root directory from wherever the application is installed to. We must follow
    through any symlinks to find the actual install directory for Unix.
    """
    _file = os.path.abspath(sys.argv[0])
    path = os.path.dirname(_file)
    if os.path.islink(_file):
        path = os.path.dirname(os.path.join(os.path.dirname(_file), os.readlink(_file)))
    return path.decode("utf-8")


def get_image_path(directory, filename):
    """
    Fetch an image from the correct directory
    """
    return os.path.join(get_path(), u"images", directory, u"%s.png" % filename)