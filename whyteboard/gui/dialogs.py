#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2009-2011 by Steven Sproat
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
This module contains classes extended from wx.Dialog used by the GUI.
"""

from __future__ import division
from __future__ import with_statement

import os
import sys
import logging
import time
import wx
import wx.lib.mixins.listctrl as listmix
from wx.lib.agw.hyperlink import HyperLinkCtrl

from urllib import urlopen, urlretrieve, urlencode

from whyteboard.lib import BaseErrorDialog, icon, pub
import whyteboard.tools as tools

from whyteboard.updater import Updater
from whyteboard.misc import meta
from whyteboard.misc import (get_home_dir, bitmap_button, fix_std_sizer_tab_order, 
                             format_bytes, get_image_path, create_bold_font, button,
                             spinctrl)

_ = wx.GetTranslation
logger = logging.getLogger("whyteboard.dialogs")

#----------------------------------------------------------------------

class History(wx.Dialog):
    """
    Creates a history replaying dialog and methods for its functionality
    """
    def __init__(self, gui):
        wx.Dialog.__init__(self, gui, title=_("History Player"), size=(225, 140))
        self.gui = gui
        self.looping = False
        self.paused = False

        self.playButton = bitmap_button(self, get_image_path(u"icons", u"play"), self.play, True, True)
        self.pauseButton = bitmap_button(self, get_image_path(u"icons", u"pause"), self.pause, True, True)
        self.stopButton = bitmap_button(self, get_image_path(u"icons", u"stop"), self.stop, True, True)
        closeButton = button(self, wx.ID_CANCEL, _("&Close"), self.on_close)
        closeButton.SetDefault()

        sizer = wx.BoxSizer(wx.VERTICAL)
        historySizer = wx.BoxSizer(wx.HORIZONTAL)
        historySizer.Add(self.playButton, 0, wx.ALL, 2)
        historySizer.Add(self.pauseButton, 0, wx.ALL, 2)
        historySizer.Add(self.stopButton, 0, wx.ALL, 2)

        sizer.Add(historySizer, 0, wx.ALIGN_CENTER_HORIZONTAL | wx.ALL, 13)
        sizer.Add((10, 5))
        sizer.Add(closeButton, 0, wx.ALIGN_CENTRE | wx.BOTTOM, 13)
        self.SetSizer(sizer)
        self.SetEscapeId(closeButton.GetId())
        self.SetFocus()
        self.toggle_buttons()

        self.Bind(wx.EVT_CLOSE, self.on_close)


    def play(self, event):
        """
        Starts the replay if it's not already started, unpauses if paused
        """
        if self.looping:
            self.paused = False
            self.toggle_buttons(True, False, False)
            return
        if self.paused:
            self.paused = False

        tmp_shapes = list(self.gui.canvas.shapes)
        shapes = []
        for shape in tmp_shapes:
            if not isinstance(shape, tools.Image):
                shapes.append(shape)

        if shapes:
            self.toggle_buttons(True, False, False)
            self.looping = True
            self.draw(shapes)


    def draw(self, shapes):
        """
        Replays the users' last-drawn pen strokes.
        The loop can be paused/unpaused by the user.
        """
        dc = wx.ClientDC(self.gui.canvas)
        dc.SetBackground(wx.WHITE_BRUSH)
        buff = self.gui.canvas.buffer
        bkgregion = wx.Region(0, 0, buff.GetWidth(), buff.GetHeight())

        dc.SetClippingRegionAsRegion(bkgregion)
        dc.Clear()
        self.gui.canvas.PrepareDC(dc)

        #  paint any images first
        for s in self.gui.canvas.shapes:
            if isinstance(s, tools.Image):
                s.draw(dc)

        for pen in shapes:
            # draw pen outline
            if isinstance(pen, tools.Pen):
                if isinstance(pen, tools.Highlighter):
                    gc = wx.GraphicsContext.Create(dc)
                    colour = (pen.colour[0], pen.colour[1], pen.colour[2], 50)
                    gc.SetPen(wx.Pen(colour, pen.thickness))
                    path = gc.CreatePath()
                else:
                    dc.SetPen(wx.Pen(pen.colour, pen.thickness))

                for x, p in enumerate(pen.points):
                    if self.looping and not self.paused:
                        try:
                            wx.MilliSleep((pen.time[x + 1] - pen.time[x]) * 950)
                            wx.Yield()
                        except IndexError:
                            pass

                        if isinstance(pen, tools.Highlighter):
                            path.MoveToPoint(p[0], p[1])
                            path.AddLineToPoint(p[2], p[3])
                            gc.DrawPath(path)
                        else:
                            dc.DrawLine(p[0], p[1], p[2], p[3])
                    else:  # loop is paused, wait for unpause/close/stop
                        while self.paused:
                            wx.MicroSleep(100)
                            wx.Yield()
            else:
                if self.looping and not self.paused:
                    wx.MilliSleep(350)
                    wx.Yield()
                    pen.draw(dc, True)

                else:  # loop is paused, wait for unpause/close/stop
                    while self.paused:
                        wx.MicroSleep(100)
                        wx.Yield()

        self.stop()  # restore other drawn items


    def pause(self, event=None):
        """Pauses/unpauses the replay."""
        if self.looping:
            self.paused = not self.paused
            self.toggle_buttons(not self.paused, self.paused, False)


    def stop(self, event=None):
        """Stops the replay."""
        if self.looping or self.paused:
            self.toggle_buttons(False, False, True)
            self.looping = False
            self.paused = False
            self.gui.canvas.Refresh()  # restore


    def on_close(self, event=None):
        """
        Called when the dialog is closed; stops the replay and ends the modal
        view, allowing the GUI to Destroy() the dialog.
        """
        self.stop()
        self.EndModal(1)


    def toggle_buttons(self, play=False, pause=False, stop=True):
        """
        Toggles the buttons on/off as indicated by the bool params
        """
        self.playButton.SetValue(play)
        self.pauseButton.SetValue(pause)
        self.stopButton.SetValue(stop)


#----------------------------------------------------------------------

class ProgressDialog(wx.Dialog):
    """
    Shows a Progres Gauge while an operation is taking place. May be cancellable
    which is possible when converting pdf/ps
    """
    def __init__(self, gui, title, cancellable=False):
        """Defines a gauge and a timer which updates the gauge."""
        wx.Dialog.__init__(self, gui, title=title, style=wx.CAPTION)
        self.gui = gui
        self.timer = wx.Timer(self)
        self.gauge = wx.Gauge(self, range=100, size=(180, 30))
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.gauge, 0, wx.ALL, 10)

        if cancellable:
            cancel = button(self, wx.ID_CANCEL, _("&Cancel"), self.on_cancel)
            cancel.SetDefault()
            btnSizer = wx.StdDialogButtonSizer()
            btnSizer.AddButton(cancel)
            btnSizer.Realize()
            sizer.Add(btnSizer, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetFocus()

        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(95)


    def on_timer(self, event):
        """Increases the gauge's progress."""
        self.gauge.Pulse()


    def on_cancel(self, event):
        """Cancels the conversion process"""
        self.SetTitle(_("Cancelling..."))
        self.FindWindowById(wx.ID_CANCEL).Disable()
        self.timer.Stop()
        self.gui.convert_cancelled = True
        if os.name == "nt":
            wx.Kill(self.gui.pid, wx.SIGKILL)
        else:
            wx.Kill(self.gui.pid)


#----------------------------------------------------------------------


class UpdateDialog(wx.Dialog):
    def __init__(self, gui):
        wx.Dialog.__init__(self, gui, title=_("Updates"), size=(250, 150))
        self.gui = gui
        self.updater = Updater()
        self.downloaded_byte_count = 0
        wx.CallAfter(self.check)  # show the dialog *then* check server

        self.text = wx.StaticText(self, label=_("Connecting to server..."), size=(-1, 80))
        cancel = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        self.btn = button(self, wx.ID_OK, _("Update"), self.update)
        self.btn.Enable(False)
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(cancel)
        btnSizer.AddButton(self.btn)
        btnSizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.text, 0, wx.LEFT | wx.TOP | wx.RIGHT, 10)
        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE)
        sizer.Add((1, 5))        
        self.SetSizer(sizer)
        
        self.SetFocus()


    def check(self):
        """
        Checks whether an update can be performed
        """
        download = self.updater.get_latest_version_info()

        if not download:
            self.text.SetLabel(_("Could not connect to server."))
            return

        if not self.updater.can_update():
            self.text.SetLabel(_("You are running the latest version."))
            return

        s = _("There is a new version available, %(version)s\nFile: %(filename)s\nSize: %(filesize)s"
             % {'version': download.version,
                'filename': download.filename(),
                'filesize': download.filesize()})
        self.text.SetLabel(s)
        self.btn.Enable(True)

    def update(self, event=None):
        """
        Downloads the latest file, extracts it and restarts the program
        """
        if not self.updater.download_file(self.progress_reporter):
            self.text.SetLabel(_("Could not connect to server."))
            self.btn.SetLabel(_("Retry"))
            return

        self.updater.extract()
        args = self.updater.restart_args(self.gui.util.filename)

        self.gui.prompt_for_save(os.execvp, wx.YES_NO, args)


    def progress_reporter(self, count, block, total):
        self.downloaded_byte_count += block

        self.text.SetLabel(_("Downloaded %s of %s") %
                            (format_bytes(self.downloaded_byte_count),
                             format_bytes(total)))

#----------------------------------------------------------------------


class TextInput(wx.Dialog):
    """
    Shows a text input screen, updates the canvas' text as text is being input
    and has methods for
    """
    def __init__(self, gui, note=None, text=u""):
        """
        Standard constructor - sets text to supplied text variable, if present.
        """
        wx.Dialog.__init__(self, gui, title=_("Enter text"),
              style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.WANTS_CHARS, size=(350, 280))
        self.gui = gui
        self.note = None
        self.ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE, size=(300, 120))
        
        if not gui.util.font:
            gui.util.font = self.ctrl.GetFont()
        self.colour = gui.util.colour
        font = gui.util.font

        if note:
            self.note = note
            self.colour = note.colour
            text = note.text
            font = wx.FFont(1, wx.FONTFAMILY_DEFAULT)
            font.SetNativeFontInfoFromString(note.font_data)
            
        self.ctrl.SetFont(font)
        self.set_text_colour(text)        
        self.setup_gui()
        
        if text:
            self.update_canvas()
            self.gui.canvas.redraw_all(True)


    def setup_gui(self):        
        fontBtn = button(self, wx.NewId(), _("Select Font"), self.on_font)
        self.colourBtn = wx.ColourPickerCtrl(self)
        self.okButton = wx.Button(self, wx.ID_OK, _("&OK"))
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        self.colourBtn.SetColour(self.colour)

        font_colour_sizer = wx.BoxSizer(wx.HORIZONTAL)
        font_colour_sizer.Add(fontBtn, 0, wx.RIGHT, 5)
        font_colour_sizer.Add(self.colourBtn, 0)
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.okButton)
        btnSizer.AddButton(self.cancelButton)
        btnSizer.Realize()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.ctrl, 1, wx.LEFT | wx.TOP | wx.RIGHT | wx.EXPAND, 10)
        sizer.Add(font_colour_sizer, 0, wx.ALIGN_RIGHT | wx.RIGHT | wx.LEFT | wx.TOP, 10)
        sizer.Add((10, 10))  # Spacer.
        sizer.Add(btnSizer, 0, wx.BOTTOM | wx.ALIGN_CENTRE, 10)
        self.SetSizer(sizer)
        
        self.okButton.SetDefault()        
        fix_std_sizer_tab_order(btnSizer)
        self.set_focus()
        
        self.Bind(wx.EVT_COLOURPICKER_CHANGED, self.on_colour, self.colourBtn)
        self.Bind(wx.EVT_TEXT, self.update_canvas, self.ctrl)

        ac = [(wx.ACCEL_CTRL, wx.WXK_RETURN, self.okButton.GetId())]
        tbl = wx.AcceleratorTable(ac)
        self.SetAcceleratorTable(tbl)
        

    def on_font(self, evt):
        """
        Shows the font dialog, sets the input text's font and returns focus to
        the text input box, at the user's selected point.
        """
        data = wx.FontData()
        data.SetInitialFont(self.ctrl.GetFont())
        dlg = wx.FontDialog(self, data)

        if dlg.ShowModal() == wx.ID_OK:
            data = dlg.GetFontData()
            self.gui.util.font = data.GetChosenFont()
            self.ctrl.SetFont(self.gui.util.font)
            self.set_text_colour()
            self.update_canvas() # Update dialog with new text height
        dlg.Destroy()
        self.set_focus()


    def on_colour(self, event):
        """Change text colour to the chosen one"""
        self.colour = event.GetColour()
        self.set_text_colour()
        self.update_canvas()
        self.set_focus()

    def set_text_colour(self, text=None):
        """Updates (or forces...) the text colour"""
        if not text:
            text = self.ctrl.GetValue()
        self.ctrl.SetValue("")
        self.ctrl.SetForegroundColour(self.colour)
        self.ctrl.SetValue(text)

    def set_focus(self):
        """Gives the text focus, places the cursor at the end of the text"""
        self.ctrl.SetFocus()
        self.ctrl.SetInsertionPointEnd()


    def update_canvas(self, event=None):
        """Updates the canvas with the inputted text"""
        if self.note:
            shape = self.note
            canvas = shape.canvas
        else:
            canvas = self.gui.canvas
            shape = canvas.shape
        self.transfer_data(shape)

        shape.find_extent()
        canvas.redraw_all()  # stops overlapping text


    def transfer_data(self, text_obj):
        """Transfers the dialog's data to an object."""
        text_obj.text = self.ctrl.GetValue()
        text_obj.font = self.ctrl.GetFont()
        text_obj.colour = self.colour


#----------------------------------------------------------------------

class FindIM(wx.Dialog):
    """
    Asks a user for the location of ImageMagick (Windows-only)
    Method is called on the ok button (for preference use)
    """
    def __init__(self, parent, gui, method):
        wx.Dialog.__init__(self, gui, title=_("ImageMagick Notification"))
        self.gui = gui
        self.method = method
        self.path = u"C:/Program Files/"

        t = (_("Whyteboard uses ImageMagick to load PDF, SVG and PS files. \nPlease select its installed location."))
        text = wx.StaticText(self, label=t)
        btn = button(self, wx.NewId(), _("Find location..."), self.browse)
        gap = wx.LEFT | wx.TOP | wx.RIGHT

        self.okButton = button(self, wx.ID_OK, _("&OK"), self.ok)
        self.okButton.SetDefault()
        self.cancelButton = button(self, wx.ID_CANCEL, _("&Cancel"), self.cancel)
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(self.okButton)
        btnSizer.AddButton(self.cancelButton)
        btnSizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(text, 1, gap | wx.EXPAND, 10)
        sizer.Add(btn, 0, gap | wx.ALIGN_CENTRE, 20)
        sizer.Add((10, 20)) # Spacer.
        sizer.Add(btnSizer, 0, wx.BOTTOM | wx.ALIGN_CENTRE, 12)
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.SetFocus()


    def browse(self, event=None):
        dlg = wx.DirDialog(self, _("Choose a directory"), self.path, style=wx.DD_DIR_MUST_EXIST)

        if dlg.ShowModal() == wx.ID_OK:
            self.path = dlg.GetPath()
        else:
            dlg.Destroy()

    def ok(self, event=None):
        if self.method(self.path):
            self.Close()

    def cancel(self, event=None):
        self.Close()

#----------------------------------------------------------------------

class Feedback(wx.Dialog):
    """
    Sends feedback to myself by POSTing to a PHP script
    """
    def __init__(self, gui):
        wx.Dialog.__init__(self, gui, title=_("Send Feedback"))

        t_lbl = wx.StaticText(self, label=_("Your Feedback:"))
        email_label = wx.StaticText(self, label=_("E-mail Address"))
        self.feedback = wx.TextCtrl(self, size=(350, 250), style=wx.TE_MULTILINE)
        self.email = wx.TextCtrl(self)

        cancel_b = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
        send_b = button(self, wx.ID_OK, _("Send &Feedback"), self.submit)
        send_b.SetDefault()
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(send_b)
        btnSizer.AddButton(cancel_b)
        btnSizer.Realize()

        font = create_bold_font()
        t_lbl.SetFont(font)
        email_label.SetFont(font)

        vsizer = wx.BoxSizer(wx.VERTICAL)
        vsizer.Add((10, 10))
        vsizer.Add(t_lbl, 0, wx.LEFT | wx.RIGHT, 10)
        vsizer.Add(self.feedback, 0, wx.EXPAND | wx.ALL, 10)
        vsizer.Add((10, 10))
        vsizer.Add(email_label, 0, wx.ALL, 10)
        vsizer.Add(self.email, 0, wx.EXPAND | wx.LEFT | wx.RIGHT, 10)
        vsizer.Add((10, 10))
        vsizer.Add(btnSizer, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTRE, 15)

        self.SetSizerAndFit(vsizer)
        self.SetFocus()
        self.SetAutoLayout(True)


    def submit(self, event):
        """Submit feedback."""
        if not self.email.GetValue() or self.email.GetValue().find("@") == -1:
            wx.MessageBox(_("Please fill out your email address"), u"Whyteboard")
            return
        if len(self.feedback.GetValue()) < 10:
            wx.MessageBox(_("Please provide some feedback"), u"Whyteboard")
            return
        params = urlencode({'submitted': 'fgdg',
                            'feedback': self.feedback.GetValue(),
                            'email': self.email.GetValue()})
        f = urlopen(u"http://www.whyteboard.org/feedback_submit.php", params)
        wx.MessageBox(_("Your feedback has been sent, thank you."), _("Feedback Sent"))
        self.Destroy()

#----------------------------------------------------------------------


class PromptForSave(wx.Dialog):
    """
    Prompts the user to confirm quitting without saving. Style can be
    wx.YES_NO | wx.CANCEL or just wx.YES_NO. 2nd is used when prompting the user
    after updating the program.
    """
    def __init__(self, gui, name, method, style, args):
        wx.Dialog.__init__(self, gui, title=_("Save File?"))
        self.gui = gui
        self.method = method
        self.args = args
        logger.debug("Prompting for save, with method %s and arguments %s", method, args)

        warning = wx.ArtProvider.GetBitmap(wx.ART_WARNING, wx.ART_CMN_DIALOG)
        bmp = wx.StaticBitmap(self, bitmap=warning)
        btnSizer = wx.StdDialogButtonSizer()
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        iconSizer = wx.BoxSizer(wx.HORIZONTAL)
        textSizer = wx.BoxSizer(wx.VERTICAL)
        container = wx.BoxSizer(wx.HORIZONTAL)

        top_message = wx.StaticText(self, label=_('Save changes to "%s" before closing?') % name)
        bottom_message = wx.StaticText(self, label=self.get_time())

        font = create_bold_font()
        font.SetPointSize(font.GetPointSize() + 1)
        top_message.SetFont(font)

        if not self.gui.util.filename:
            saveButton = button(self, wx.ID_SAVE, _("Save &As..."), self.okay)
        else:
            saveButton = button(self, wx.ID_SAVE, _("&Save"), self.okay)

        if style == wx.YES_NO | wx.CANCEL:
            cancelButton = wx.Button(self, wx.ID_CANCEL, _("&Cancel"))
            btnSizer.AddButton(cancelButton)

        noButton = button(self, wx.ID_NO, _("&Don't Save"), self.no)
        saveButton.SetDefault()

        btnSizer.AddButton(noButton)
        btnSizer.AddButton(saveButton)
        btnSizer.Realize()
        iconSizer.Add(bmp, 0)

        textSizer.Add(top_message)
        textSizer.Add((10, 10))
        textSizer.Add(bottom_message)

        container.Add(iconSizer, 0, wx.LEFT, 15)
        container.Add((15, -1))
        container.Add(textSizer, 1, wx.RIGHT, 15)
        container.Layout()

        mainSizer.Add((10, 15))
        mainSizer.Add(container, wx.ALL, 30)
        mainSizer.Add((10, 10))
        mainSizer.Add(btnSizer, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTRE, 15)

        self.SetSizerAndFit(mainSizer)
        self.SetFocus()
        self.SetAutoLayout(True)
        fix_std_sizer_tab_order(btnSizer)


    def get_time(self):
        m, s = divmod(time.time() - self.gui.util.save_time, 60)
        h, m = divmod(m, 60)
        hours, mins, seconds = "", "", ""

        # ugly....
        if m > 0 and h < 1:
            mins = (u"%i " % m) + _("minutes")
        if m == 1 and h < 1:
            mins = _("minute")
        if h > 0:
            hours = (u"%i " % h) + _("hours")
        if h == 1:
            hours = _("hour")
        if s == 1 and m < 1:
            seconds = _("second")
        elif s > 1 and m < 1:
            seconds = (u"%i " % s) + _("seconds")

        ms = u"%s%s%s" % (hours, mins, seconds)

        return _("If you don't save, changes from the last\n%s will be permanently lost.") % ms


    def okay(self, event):
        self.gui.on_save()
        if self.gui.util.saved:
            self.Close()
        if self.gui.util.saved or self.method == os.execvp:
            logger.debug("Focing restart with params %s", self.args)
            self.method(*self.args)  # force restart, otherwise 'cancel'
                                     # returns to application

    def no(self, event):
        self.method(*self.args)
        self.Close()
        if self.method == self.gui.Destroy:
            logger.info("Program exiting.")
            #sys.exit()

    def cancel(self, event):
        logger.info("User cancelled out of save prompt")
        self.Close()


#----------------------------------------------------------------------

class Resize(wx.Dialog):
    """
    Allows the user to resize a sheet's canvas
    """
    def __init__(self, gui):
        """
        Two spinctrls are used to set the width/height. Canvas updates as the
        values change
        """
        wx.Dialog.__init__(self, gui, title=_("Resize Canvas"))

        self.gui = gui
        gap = wx.LEFT | wx.TOP | wx.RIGHT
        width, height = self.gui.canvas.buffer.GetSize()
        self.size = (width, height)

        self.wctrl = spinctrl(self, 12000, width, self.resize)
        self.hctrl = spinctrl(self, 12000, height, self.resize)

        csizer = wx.GridSizer(cols=2, hgap=1, vgap=2)
        csizer.Add(wx.StaticText(self, label=_("Width:")), 0, wx.TOP |
                                                            wx.ALIGN_RIGHT, 10)
        csizer.Add(self.wctrl, 1, gap, 7)
        csizer.Add(wx.StaticText(self, label=_("Height:")), 0, wx.TOP |
                                                             wx.ALIGN_RIGHT, 7)
        csizer.Add(self.hctrl, 1, gap, 7)

        okButton = button(self, wx.ID_OK, _("&OK"), self.ok)
        okButton.SetDefault()
        cancelButton = button(self, wx.ID_CANCEL, _("&Cancel"), self.cancel)
        applyButton = button(self, wx.ID_APPLY, _("&Apply"), self.apply)

        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.AddButton(applyButton)
        btnSizer.Realize()
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(csizer, 0, gap, 7)
        sizer.Add((10, 15))
        sizer.Add(btnSizer, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        sizer.Add((15, 5))
        self.SetSizer(sizer)
        self.SetFocus()
        self.SetEscapeId(cancelButton.GetId())
        self.Fit()

        fix_std_sizer_tab_order(sizer)


    def apply(self, event):
        x, y, = self.gui.canvas.buffer.GetSize()
        self.size = (x, y) 

    def ok(self, event):
        self.resize()
        self.Close()

    def resize(self, event=None):
        value = (self.wctrl.GetValue(), self.hctrl.GetValue())
        self.gui.canvas.resize(value)

    def cancel(self, event):
        self.gui.canvas.resize(self.size)
        self.Close()

#----------------------------------------------------------------------


class ErrorDialog(BaseErrorDialog):
    def __init__(self, msg):
        BaseErrorDialog.__init__(self, None, title=_("Error Report"), message=msg)
        self.SetDescriptionLabel(_("An error has occured - please report it"))
        self.gui = wx.GetTopLevelWindows()[0]

    def Abort(self):
        if isinstance(self.gui, ErrorDialog):
            self.Destroy()
            sys.exit()
        self.gui.prompt_for_save(self.gui.Destroy)

    def GetEnvironmentInfo(self):
        """
        Need to stick in extra information: preferences, helps with debugging
        """
        info = super(ErrorDialog, self).GetEnvironmentInfo()

        path = os.path.join(get_home_dir(), u"user.pref")
        if os.path.exists(path):
            info.append(u"#---- Preferences ----#")
            with open(path) as f:
                for preference in f:
                    preference = preference.rstrip()
                    info.append(unicode(preference, "utf-8"))
            info.append(u"")
            info.append(u"")
        return os.linesep.join(info)

    def GetProgramName(self):
        return u"Whyteboard %s" % meta.version


    def Send(self):
        """Send the error report. PHP script calls isset($_POST['submitted'])"""
        params = urlencode({'submitted': 'fgdg',
                            'message': self._panel.err_msg,
                            'desc': self._panel.action.GetValue(),
                            'email': self._panel.email.GetValue()})
        f = urlopen(u"http://www.whyteboard.org/bug_submit.php", params)

        self.gui.prompt_for_save(self.Close)


 #----------------------------------------------------------------------

def ExceptionHook(exctype, value, trace):
    """
    Handler for all unhandled exceptions
    """
    ftrace = ErrorDialog.FormatTrace(exctype, value, trace)
    print ftrace  # show in console
    logger.critical(ftrace)

    if ErrorDialog.ABORT:
        os._exit(1)
    if not ErrorDialog.REPORTER_ACTIVE and not ErrorDialog.ABORT:
        dlg = ErrorDialog(ftrace)
        dlg.ShowModal()
        dlg.Destroy()

#----------------------------------------------------------------------


class WhyteboardList(wx.ListCtrl, listmix.ListCtrlAutoWidthMixin, listmix.ListRowHighlighter):

    def __init__(self, parent):
        wx.ListCtrl.__init__(self, parent, style=wx.DEFAULT_CONTROL_BORDER |
                             wx.LC_REPORT | wx.LC_SINGLE_SEL | wx.LC_HRULES)
        listmix.ListRowHighlighter.__init__(self, (206, 218, 255))
        listmix.ListCtrlAutoWidthMixin.__init__(self)


#----------------------------------------------------------------------


class ShapeViewer(wx.Dialog):
    """
    Presents a list of the current sheet's shapes, in accordance to their
    position in the list, which is the order that the shapes are drawn in.
    Allows the user to move shapes up/down/to top/to bottom, as well as info
    about the shape such as its colour/thickness
    """
    def __init__(self, gui):
        """
        Initialise and populate the listbox
        """
        wx.Dialog.__init__(self, gui, title=_("Shape Viewer"), size=(550, 400),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.MINIMIZE_BOX |
                           wx.MAXIMIZE_BOX | wx.RESIZE_BORDER | wx.WANTS_CHARS)
        self.gui = gui
        self.count = 0
        self.shapes = list(self.gui.canvas.shapes)
        self.SetSizeHints(550, 400)

        label = wx.StaticText(self, label=_("Shapes at the top of the list are drawn over shapes at the bottom"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)
        nextprevsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.moveUp = self.make_button(u"move-up", _("Move Shape Up"), self.on_up)
        self.moveTop = self.make_button(u"move-top", _("Move Shape To Top"), self.on_top)
        self.moveDown = self.make_button(u"move-down", _("Move Shape Down"), self.on_down)
        self.moveBottom = self.make_button(u"move-bottom", _("Move Shape To Bottom"), self.on_bottom)
        self.deleteBtn = self.make_button(u"delete", _("Delete Shape"), self.on_delete)
        self.prev = self.make_button(u"prev_sheet", _("Previous Sheet"), self.on_prev)
        self.next = self.make_button(u"next_sheet", _("Next Sheet"), self.on_next)

        self.pages = wx.ComboBox(self, size=(125, 25), style=wx.CB_READONLY)
        self.list = WhyteboardList(self)
        self.list.InsertColumn(0, _("Position"))
        self.list.InsertColumn(1, _("Type"))
        self.list.InsertColumn(2, _("Thickness"))
        self.list.InsertColumn(3, _("Color"))
        self.list.InsertColumn(4, _("Properties"))

        bsizer.AddMany([(self.moveTop, 0, wx.RIGHT, 5), (self.moveUp, 0, wx.RIGHT, 5), 
                        (self.moveDown, 0, wx.RIGHT, 5), (self.moveBottom, 0, wx.RIGHT, 5),
                        (self.deleteBtn, 0, wx.RIGHT, 5)])
        nextprevsizer.Add(self.prev, 0, wx.RIGHT, 5)
        nextprevsizer.Add(self.next)

        bsizer.Add((1, 1), 1, wx.EXPAND)  # align to the right
        bsizer.Add(nextprevsizer, 0, wx.RIGHT, 10)
        bsizer.Add(self.pages, 0, wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)

        okButton = button(self, wx.ID_OK, _("&OK"), self.ok)
        okButton.SetDefault()
        cancelButton = button(self, wx.ID_CANCEL, _("&Cancel"), self.cancel)
        applyButton = button(self, wx.ID_APPLY, _("&Apply"), self.apply)
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.AddButton(applyButton)
        btnSizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.ALL, 15)
        sizer.Add((10, 5))
        sizer.Add(bsizer, 0, wx.LEFT | wx.EXPAND, 10)
        sizer.Add((10, 15))
        sizer.Add(self.list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        sizer.Add((10, 5))
        sizer.Add(btnSizer, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTRE, 15)
        self.SetSizer(sizer)
        self.populate()
        self.Fit()
        self.SetFocus()
        self.SetEscapeId(cancelButton.GetId())

        self.pages.Bind(wx.EVT_COMBOBOX, self.on_change_sheet)
        self.Bind(wx.EVT_CLOSE, self.on_close)

        ac = [(wx.ACCEL_NORMAL, wx.WXK_DELETE, self.deleteBtn.GetId())]
        tbl = wx.AcceleratorTable(ac)
        self.list.SetAcceleratorTable(tbl)
        self.Bind(wx.EVT_CHAR_HOOK, self.delete_key)

        pub.subscribe(self.sheet_rename, 'sheet.rename')
        pub.subscribe(self.update, 'update_shape_viewer')

        ids = [self.moveUp.GetId(), self.moveTop.GetId(), self.moveDown.GetId(),
               self.moveBottom.GetId(), self.deleteBtn.GetId(), self.prev.GetId(), self.next.GetId()]

        [self.Bind(wx.EVT_UPDATE_UI, self.update_buttons, id=x) for x in ids]


    def make_button(self, filename, tooltip, event_handler):
        btn = bitmap_button(self, get_image_path(u"icons", filename), event_handler, False)
        btn.SetToolTipString(tooltip)
        return btn


    def sheet_rename(self, _id, text):
        self.populate()

    def update(self):
        logger.debug("Updating shape viewer.")
        self.shapes = list(self.gui.canvas.shapes)
        self.populate()

    def populate(self):
        """
        Creates all columns and populates with the current sheets' data
        """
        self.pages.SetItems(self.gui.get_tab_names())
        self.pages.SetSelection(self.gui.current_tab)
        selection = self.list.GetFirstSelected()
        self.list.DeleteAllItems()

        if not self.shapes:
            index = self.list.InsertStringItem(sys.maxint, "")
            self.list.SetStringItem(index, 3, _("No shapes drawn"))
        else:
            for x, shape in enumerate(reversed(self.shapes)):
                index = self.list.InsertStringItem(sys.maxint, str(x + 1))
                self.list.SetStringItem(index, 0, str(x + 1))
                self.list.SetStringItem(index, 1, _(shape.name))
                self.list.SetStringItem(index, 2, str(shape.thickness))
                self.list.SetStringItem(index, 3, str(shape.colour))
                self.list.SetStringItem(index, 4, shape.properties())
            self.list.Select(selection)
            self.list.EnsureVisible(selection)



    def update_buttons(self, event):
        _id = event.GetId()
        do = False

        if _id == self.next.GetId() and self.gui.current_tab + 1 < self.gui.tab_count:
            do = True
        elif _id == self.prev.GetId() and self.gui.current_tab > 0:
            do = True
        elif _id == self.deleteBtn.GetId() and self.shapes and self.list.GetFirstSelected() >= 0:
            do = True
        elif _id in [self.moveUp.GetId(), self.moveTop.GetId()] and self.list.GetFirstSelected() > 0:
            do = True
        elif _id in [self.moveDown.GetId(), self.moveBottom.GetId()] and self.is_not_last_item():
            do = True
        event.Enable(do)
        for x in [self.moveBottom, self.moveDown, self.moveUp, self.moveTop, self.deleteBtn, self.prev, self.next]:
            x.Refresh()

    def is_not_last_item(self):
        return (self.list.GetFirstSelected() != len(self.shapes) - 1  and self.shapes
            and self.list.GetFirstSelected() >= 0)


    def find_shape(self):
        """Find the selected shape's index and actual object"""
        count = 0
        for x in reversed(self.shapes):
            if count == self.list.GetFirstSelected():
                return (self.shapes.index(x), x)
            count += 1

    def move_shape(fn):
        """
        Passes the selected shape and its index to the decorated function, which
        handles moving the shape. function returns the list index to select
        """
        def wrapper(self, event, index=None, item=None):
            index, item = self.find_shape()
            self.shapes.pop(index)
            x = fn(self, event, index, item)

            self.populate()
            self.list.Select(x)
        return wrapper

    @move_shape
    def on_top(self, event, index=None, item=None):
        self.shapes.append(item)
        return 0

    @move_shape
    def on_bottom(self, event, index=None, item=None):
        self.shapes.insert(0, item)
        return len(self.shapes) - 1

    @move_shape
    def on_up(self, event, index=None, item=None):
        self.shapes.insert(index + 1, item)
        return self.list.GetFirstSelected() - 1

    @move_shape
    def on_down(self, event, index=None, item=None):
        self.shapes.insert(index - 1, item)
        return self.list.GetFirstSelected() + 1

    @move_shape
    def on_delete(self, event, index=None, item=None):
        if self.list.GetFirstSelected() - 1 <= 0:
            return 0
        return self.list.GetFirstSelected() - 1

    def delete_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE and self.shapes:
            self.on_delete(None)
        event.Skip()


    def change(self, selection):
        """Change the sheet, repopulate"""
        self.gui.tabs.SetSelection(selection)
        self.pages.SetSelection(selection)
        self.gui.on_change_tab()
        self.update()


    def on_change_sheet(self, event):
        self.change(self.pages.GetSelection())

    def on_next(self, event):
        self.change(self.gui.current_tab + 1)

    def on_prev(self, event):
        self.change(self.gui.current_tab - 1)

    def ok(self, event):
        self.apply()
        self.Close()

    def cancel(self, event=None):
        self.Close()

    def on_close(self, event):
        self.gui.shape_viewer_open = False
        event.Skip()

    def apply(self, event=None):
        self.gui.canvas.add_undo()
        self.gui.canvas.shapes = self.shapes
        self.gui.canvas.redraw_all(True)


#----------------------------------------------------------------------

class PDFCacheDialog(wx.Dialog):
    """
    Views a list of all cached PDFs - showing the amount of pages, location,
    conversion quality and date saved. Has options to remove items to re-convert
    """
    def __init__(self, gui, cache):
        wx.Dialog.__init__(self, gui, title=_("PDF Cache Viewer"), size=(650, 300),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.cache = cache
        self.files = cache.entries()
        self.original_files = dict(cache.entries())
        self.list = WhyteboardList(self)
        self.SetSizeHints(450, 300)

        label = wx.StaticText(self, label=_("Whyteboard will load these files from its cache instead of re-converting them"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        bsizer = wx.BoxSizer(wx.HORIZONTAL)

        self.deleteBtn = bitmap_button(self, get_image_path(u"icons", u"delete"), self.on_remove, False)
        self.deleteBtn.SetToolTipString(_("Remove cached item"))
        bsizer.Add(self.deleteBtn, 0, wx.RIGHT, 5)

        okButton = button(self, wx.ID_OK, _("&OK"), self.ok)
        cancelButton = button(self, wx.ID_CANCEL, _("&Cancel"), lambda x: self.Close())
        cancelButton.SetDefault()
        btnSizer = wx.StdDialogButtonSizer()
        btnSizer.AddButton(okButton)
        btnSizer.AddButton(cancelButton)
        btnSizer.Realize()

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(label, 0, wx.ALL, 15)
        sizer.Add((10, 5))
        sizer.Add(bsizer, 0, wx.LEFT | wx.EXPAND, 10)
        sizer.Add((10, 5))
        sizer.Add(self.list, 1, wx.LEFT | wx.RIGHT | wx.EXPAND, 10)
        sizer.Add((10, 5))
        sizer.Add(btnSizer, 0, wx.TOP | wx.BOTTOM | wx.ALIGN_CENTRE, 15)
        self.SetSizer(sizer)
        self.populate()
        self.check_buttons()
        self.SetEscapeId(cancelButton.GetId())
        self.SetFocus()

        self.Bind(wx.EVT_LIST_ITEM_SELECTED, lambda x: self.check_buttons())
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, lambda x: self.check_buttons())

        ac = [(wx.ACCEL_NORMAL, wx.WXK_DELETE, self.deleteBtn.GetId())]
        tbl = wx.AcceleratorTable(ac)
        self.list.SetAcceleratorTable(tbl)
        self.Bind(wx.EVT_CHAR_HOOK, self.delete_key)


    def populate(self):
        """
        Creates all columns and populates them with the PDF cache list
        """
        self.list.ClearAll()
        self.list.InsertColumn(0, _("File Location"))
        self.list.InsertColumn(1, _("Quality"))
        self.list.InsertColumn(2, _("Pages"))
        self.list.InsertColumn(3, _("Date Cached"))

        if not self.files:
            index = self.list.InsertStringItem(sys.maxint, "")
            self.list.SetStringItem(index, 0, _("There are no cached items to display"))
        else:
            for x, key in self.files.items():
                f = self.files[x]
                index = self.list.InsertStringItem(sys.maxint, str(x + 1))

                self.list.SetStringItem(index, 0, f['file'])
                self.list.SetStringItem(index, 1, f['quality'].capitalize())
                self.list.SetStringItem(index, 2, u"%s" % len(f['images']))
                self.list.SetStringItem(index, 3, f.get('date', _("No Date Saved")))

        self.list.SetColumnWidth(0, wx.LIST_AUTOSIZE)
        self.list.SetColumnWidth(1, 70)
        self.list.SetColumnWidth(2, 60)
        self.list.SetColumnWidth(3, wx.LIST_AUTOSIZE)


    def check_buttons(self):
        """ Enable / Disable the appropriate buttons """
        if not self.list.GetItemCount() or self.list.GetFirstSelected() == -1:
            self.deleteBtn.Disable()
        else:
            self.deleteBtn.Enable()


    def ok(self, event):
        self.cache.write_dict(self.files)
        self.Close()


    def delete_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE and self.files.items():
            self.on_remove(None)
        event.Skip()


    def on_remove(self, event):
        """Remove the dictionary item that matches the selected item's path"""
        item = self.list.GetFirstSelected()
        if item == -1:
            return

        quality = self.list.GetItem(item, 1).GetText()
        text = self.list.GetItemText(item)
        files = dict(self.files)

        for x, key in self.files.items():
            if (self.files[x]['file'] == text and
                self.files[x]['quality'].capitalize() == quality):
                del files[x]

        self.files = files
        self.populate()


#----------------------------------------------------------------------

class AboutDialog(wx.Dialog):
    """
    A replacement About Dialog for Windows, as it uses a generic frame that
    well...sucks.
    """
    def __init__(self, parent, info):
        wx.Dialog.__init__(self, parent, title=_("About Whyteboard"))

        image = wx.StaticBitmap(self, bitmap=icon.GetBitmap())
        name = wx.StaticText(self, label="%s %s" % (info.Name, info.Version))
        description = wx.StaticText(self, label=info.Description)
        copyright = wx.StaticText(self, label=info.Copyright)
        url = HyperLinkCtrl(self, label=info.WebSite[0], URL=info.WebSite[1])

        font = create_bold_font()
        font.SetPointSize(18)
        name.SetFont(font)

        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttons = {_("C&redits"): (wx.ID_ABOUT, wx.LEFT | wx.RIGHT,
                                   lambda evt: CreditsDialog(self, info)),
                  _("&License"): (wx.ID_ANY, wx.RIGHT,
                                   lambda evt: LicenseDialog(self, info.License)),
                  _("&Close"): (wx.ID_CANCEL, wx.RIGHT,
                                   lambda evt: self.Destroy())}

        for label, values in buttons.items():
            btn = button(self, values[0], label, values[2])
            btnSizer.Add(btn, flag=wx.CENTER | values[1], border=5)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(image, flag=wx.CENTER | wx.TOP | wx.BOTTOM, border=5)
        sizer.Add(name, flag=wx.CENTER | wx.BOTTOM, border=10)
        sizer.Add(description, flag=wx.CENTER | wx.BOTTOM, border=10)
        sizer.Add(copyright, flag=wx.CENTER | wx.BOTTOM, border=10)
        sizer.Add(url, flag=wx.CENTER | wx.BOTTOM, border=15)
        sizer.Add(btnSizer, flag=wx.CENTER | wx.BOTTOM, border=5)

        container = wx.BoxSizer(wx.VERTICAL)
        container.Add(sizer, flag=wx.ALL, border=10)
        self.SetSizerAndFit(container)
        self.Centre()
        self.Show(True)


#----------------------------------------------------------------------

class CreditsDialog(wx.Dialog):
    def __init__(self, parent, info):
        wx.Dialog.__init__(self, parent, title=_("Credits"), size=(475, 320),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetIcon(icon.GetIcon())
        self.SetMinSize((300, 200))
        notebook = wx.Notebook(self)
        close = button(self, wx.ID_CANCEL, _("&Close"), lambda evt: self.Destroy())
        close.SetDefault()

        labels = [_("Written by"), _("Translated by")]
        texts = [info.Developers, info.Translators]

        for label, text in zip(labels, texts):
            btn = wx.TextCtrl(notebook, style=wx.TE_READONLY | wx.TE_MULTILINE)
            btn.SetValue(u"\n".join(text))
            notebook.AddPage(btn, text=label)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(notebook, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(close, flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()


#----------------------------------------------------------------------

class LicenseDialog(wx.Dialog):
    def __init__(self, parent, license):
        wx.Dialog.__init__(self, parent, title=_("License"), size=(500, 400),
                           style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.SetMinSize((400, 300))
        self.SetIcon(icon.GetIcon())
        close = button(self, wx.ID_CANCEL, _("&Close"), lambda evt: self.Destroy())

        ctrl = wx.TextCtrl(self, style=wx.TE_READONLY | wx.TE_MULTILINE)
        ctrl.SetValue(license)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(ctrl, 1, wx.EXPAND | wx.ALL, 10)
        sizer.Add(close, flag=wx.ALIGN_RIGHT | wx.RIGHT | wx.BOTTOM, border=10)
        self.SetSizer(sizer)
        self.Layout()
        self.Show()

#----------------------------------------------------------------------