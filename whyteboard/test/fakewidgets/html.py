#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Fake wx.html module.

"""

from core import Control, Window

class HtmlWindow(Window):
    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)

    def LoadUrl(self, url):
        pass
    def SetPage(self, page):
        self.page = page

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class HtmlHelpController(object):
    def AddBook(self, book):
        pass

import wx.html
wx.html.__dict__.update(locals())
assert wx.html.HtmlWindow == HtmlWindow