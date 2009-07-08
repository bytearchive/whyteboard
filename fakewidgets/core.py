#!/usr/bin/python

"""
Fake core wx module.
Overwrites wx namespace with fake classes/functions.

modified by Steven Sproat @ Thu 19 Mar 2009 03:58:33 GMT
- added scrollwindow, some attributes for a notebook

modified by Steven Sproat @ Fri 22 May 2009 08:20:10 GMT
- changed some more stuff

modified by Steven Sproat @ Fri 22 May 2009 08:20:10 GMT
- cleaned up the code, added more methods/static classes (i.e. The Clipboard)
"""

__version__ = "0.32"
__author__ = "Ryan Ginstrom / Steven Sproat"



# App/events

class PySimpleApp(object):
    def __init__(self, *args, **kwds):
        self.calls = []

    def MainLoop(self):
        pass

    def SetTopWindow(self, window):
        self.topwindow = window

    def IsDisplayAvailable(*args, **kwds):
        return True
    IsDisplayAvailable = staticmethod(IsDisplayAvailable)

class App(PySimpleApp):
    """Mocks wx.App

    This will allow us to step through our main startup code
    without actually invoking wx.App and the dreaded MainLoop!
    """

    def SetAppName(self, name):
        pass


class Event(object):
    def __init__(self, *args, **kwds):
        self.calls = []

    def Skip(self):
        pass

############
# Graphics
############

class EmptyIcon(object):
    def __init__(self, *args, **kwds):
        self.calls = []

    def LoadFile(self, path, type):
        self.path = path
        self.type = type
    def SetHandle(self, handle):
        self.handle = handle

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class EmptyBitmap(object):
    def __init__(self, *args, **kwds):
        self.calls = []

class Bitmap(object):
    def __init__(self, filename=None, flag=None):
        self.filename = filename
        self.flag = flag
        self.calls = []

    def SetMaskColour(self, color):
        self.mask_color = color

    def SetMask(self, mask):
        self.mask = mask

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class Image(object):
    def __init__(self, filename=None, type=None):
        self.calls = []

    def Resize(self, width, height):
        pass


    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None        
        
class Mask(object):
    def __init__(self, bmp, mask):
        self.bitmap = bmp
        self.mask = mask
        self.calls = []

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class Font(object):
    def __init__(self, *args, **kwds):
        self.__dict__.update(kwds)
        self.calls = []

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class Pen(object):
    def __init__(self, *args, **kwds):
        self.__dict__.update(kwds)
        self.calls = []

class Brush(object):
    def __init__(self, *args, **kwds):
        self.__dict__.update(kwds)
        self.calls = []

class StockCursor(object):
    def __init__(self, *args, **kwds):
        self.__dict__.update(kwds)
        self.calls = []

class ImageList(object):
    def __init__(self, width, height, *args):
        self.width = width
        self.height = height
        self.images = []
        self.calls = []

    def Add(self, image):
        """Stores image in list of images for unit testing"""

        self.images.append(image)

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class DC(object):
    def __init__(self, *args, **kwds):
        self.__dict__.update(kwds)
        self.calls = []
        
    def GetMultiLineTextExtent(self, *args, **kwds):
        return (0, 0)

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class BufferedDC(DC):
    pass

class PaintDC(DC):
    pass

class MemoryDC(DC):
    pass

class WindowDC(DC):
    pass

class ClientDC(DC):
    pass

def BitmapFromIcon(icon):
    return Bitmap()



############
# Windows
############

class Window(object):
    """The base of our fake widget classes.

    This class can contain operations common to all windows
    """

    def __init__(self, parent, *args, **kwds):
        self.parent = parent
        self.Enabled = True
        self.calls = []
        self.size = (0, 0)

    def GetClientSizeTuple(self):
        return (0, 0)    
    
    def Enable(self):
        self.Enabled=True

    def GetClassDefaultAttributes(self):
        return VisualAttributes()

    def Disable(self):
        self.Enabled=False

    def Show(self):
        pass

    def Refresh(self):
        pass
        
    def GetSize(self):
        return self.size
        
    def SetSize(self, size):
        self.size = size
                
    def RefreshRect(self):
        pass

    def Destroy(self):
        pass

    def Bind(self, *args, **kwds):
        pass

    def SetCursor(self, cursor):
        pass

    def SetToolTipString(self,tip):
        """Sets ToolTipString variable"""

        self.ToolTipString = tip

    def SetMinSize(self, size):
        """Sets MinSize variable.
        size should be a tuple of ints"""

        width, height = size
        assert int(width) == width, width
        assert int(height) == height, height

        self.MinSize = size

    def SetSizerProp(self, prop):
        pass
        
    def SetSizer(self, sizer):
        pass
        
    def GetSizer(self):
        return Sizer()

    def GetParent(self):
        return self.parent

    def SetBackgroundColour(self, *size):
        pass
    def SetBackgroundStyle(self, *size):
        pass    
    def ClearBackground(self):
        pass


class ScrolledWindow(Window):
    def SetVirtualSize(self, *size):
        pass

    def SetVirtualSizeHints(self, *size):
        pass
        
    def Scroll(self, width, height):
        pass

    def SetScrollRate(self, *size):
        pass

    def SetVirtualSize(self, *size):
        pass

    def GetBestVirtualSize(self, *size):
        pass
        
class Panel(Window):
    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class ScrolledPanel(Panel):
    def SetVirtualSize(self, *size):
        pass

    def SetVirtualSizeHints(self, *size):
        pass

    def SetScrollRate(self, *size):
        pass

    def SetVirtualSize(self, *size):
        pass

############
# Controls
############

class Control(Window):
    """Generic control class that our concrete
    controls inherit from
    """

    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)

    def SetFont(self, font):
        """Sets the Font variable"""
        self.Font = font

class Button(Control):

    def __init__(self, parent, id=-1, label="", **kwds):
        Control.__init__(self, parent, **kwds)
        self.Label = label
        self.IsDefault = False

    def SetDefault(self):
        """Makes this button the default
        IsDefault -> True"""

        self.IsDefault = True

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class ToggleButton(Button):

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None
        
class BitmapButton(ToggleButton):
    pass
                    
class StaticBox(Window):
    def __init__(self, parent, id=-1, label="", **kwds):
        Window.__init__(self, parent, **kwds)
        self.Label = label


class StaticLine(Window):
    def __init__(self, parent, id=-1, label="", **kwds):
        Window.__init__(self, parent, **kwds)
        self.Label = label

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class TextCtrl(Control):

    def __init__(self, parent=None, id=None, value=None, size=None, style=None):
        Control.__init__(self,parent)
        self.Id = id
        self.Value = value
        self.Size = size
        self.Style = style

    def SetValue(self, value):
        """Sets the Value variable"""
        self.Value = value

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

        
class ComboBox(Control):
    def __init__(self, parent=None, choices=None, size=None, style=None):
        Control.__init__(self,parent)
        self.choices = choices
        self.Size = size
        self.Style = style
        self.selection = 0

    def SetSelection(self, value):
        self.selection = value

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None
        
        
class TreeItemData(object):
    #  holds a Python object referenced to a tree node
    def __init__(self, data):
        self.data = data
        
    def SetData(self, data):
        self.data = data
        
    def	GetData(self):
        return self.data                      


class TreeItemId(object):
    #  holds a Python object referenced to a tree node
    ids = []
    def __init__(self):
        self.ids.append(self)
        
    
                
class TreeCtrl(Control):
    def __init__(self, parent=None, size=None, style=None):
        Control.__init__(self, parent)
        self.Size = size
        self.Style = style
                
    def GetFirstChild(self, item):
        return (None, None)
        
    def GetNextChild(self, item, cookie):
        return ("item", cookie)
        
        
    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None
        
                        
class ListCtrl(Control):
    """Mocks wx.ListCtrl"""

    def __init__(self,parent=None,id=None,value=None,size=None,style=None):
        Control.__init__(self,parent)
        self.Id = id
        self.Value = value
        self.Size = size
        self.Style = style
        self.ItemData = []
        self.columns = {}
        self.ImageList = {}
        self.selected = []

    def DeleteAllItems(self):
        self.ItemData = []
        self.selected = []

    def InsertStringItem(self, index, text, image_id = None):
        self.ItemData.append(text)
        if not self.selected:
            self.selected = [len(self.ItemData)-1]

    def SetItemData(self, item, index):
        pass

    def SetStringItem(self, row, col, data):
        pass

    def SetColumnWidth(self, column, style):
        self.columns[column] = style

    def InsertColumn(self, index, label):
        self.columns[index] = label

    def SetImageList(self, img_list, type):
        self.ImageList[type] = img_list

    def GetFirstSelected(self):
        if not self.ItemData:
            return -1
        return self.selected[0]

    def GetItemText(self, index):
        return self.ItemData[index]

    def DeleteItem(self, index):
        del self.ItemData[index]
        self.selected = [item for item in self.selected if item != index]

    def GetItemCount(self):
        return len(self.ItemData)

    def Select(self, index):
        self.selected = [index]

    def GetSelectedItemCount(self):
        return len(self.selected)

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class CheckBox(Control):

    def __init__(self,parent=None,Value=None, *args, **kwds):
        Control.__init__(self, parent, *args, **kwds)
        self.Value = Value

    def SetValue(self, value):
        self.Value = value

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class StaticText(Control):

    def __init__(self,parent=None,id=None,label=None,size=None):
        Control.__init__(self,parent)
        self.Id = id
        self.Label = label
        self.Size = size

    def GetLabel(self):
        return self.Label

    def SetLabel(self, label):
        self.Label = label

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

#################
# Other widgets
#################

class VisualAttributes(object):
    def __init__(self, *args, **kwds):
        self.font = Font()
    

class StatusBar(Window):
    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)
        self.fields = {}

    def SetStatusWidths(self, widths):
        self.widths = widths

    def SetStatusText(self, field, i):
        self.fields[i] = field

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None


class CollapsiblePane(Window):
    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)

    def Collapse(self):
        pass
        
    def Expand(self):
        pass
        
    def GetPane(self):
        return self.parent
                
    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None
        
        
class Notebook(Window):
    def __init__(self, parent, *args, **kwds):
        Window.__init__(self,parent, *args, **kwds)
        self.pages = []
        self.texts = [] 
        self.parent = parent
        self.selection = 0

    def AddPage(self, page, text):
        self.pages.append(page)
        self.texts.append(text)
        
    def RemovePage(self, page):
        del self.texts[page - 1]
        del self.pages[page - 1]
        
    def DeletePage(self, page):
        del self.texts[page - 1]
        del self.pages[page - 1]
        
    def GetPage(self, n):
        return self.pages[n]
        
    def GetCurrentPage(self):
        #print self.selection  
        #print self.pages  
        return self.pages[self.selection]
                
    def GetPageText(self):
        return self.selection
        
    def SetPageText(self, sel):
        self.selection = sel
                
    def GetSelection(self):
        return self.selection - 1
        
    def SetSelection(self, sel):
        self.selection = sel
        
    def GetParent(self):
        return self.parent

###########
# Toolbars
###########

class ToolBar(Window):
    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)

    def SetToolBitmapSize(self, tsize):
        self.tsize = tsize

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

###########
# Menus
###########

class MenuBar(object):
    def __init__(self, *args, **kwds):
        self.menus = []
        self.calls = []

    def Append(self, menu, title, kind=None):
        self.menus.append((menu, title))

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class Menu(object):
    def __init__(self, *args, **kwds):
        self.items = []
        self.calls = []

    def Append(self, id, label, tip="", kind=None):
        self.items.append((label,tip))
        return self.items[-1]

    def AppendItem(self, item):
        self.items.append(item)
        return self.items[-1]

    def AppendSeparator(self):
        self.items.append("---")
        return self.items[-1]

    def AppendMenu(self, id, menu, title, *args, **kwds):
        self.items.append((menu, title))
        return self.items[-1]

    def AppendSubMenu(self, menu, title):
        self.items.append((menu, title))
        return self.items[-1]

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class MenuItem(Window):
    def __init__(self, *args, **kwds):
        self.calls = []

    def SetBitmap(self, bmp):
        self.bitmap = bmp

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

###############
# Main windows
###############

class TopWindow(Window):
    """Generic top-level window"""

    def __init__(self, *args, **kwds):
        Window.__init__(self, *args, **kwds)

    def SetSizer(self, sizer):
        self.sizer = sizer

    def SetTitle(self, title):
        self.Title = title

    def SetIcon(self, icon):
        self.icon = icon

    def Fit(self):
        pass

    def Layout(self):
        pass

class Frame(TopWindow):
    """Mocks wx.Frame"""

    def __init__(self,
                 parent,
                 id=-1,
                 title=u"Frame",
                 pos=None,
                 size=(0,0),
                 style=None,
                 **kwds):

        TopWindow.__init__(self,parent)
        self.Title = title
        self.Size = size
        self.Pos = pos
        self.Style = style

    def CenterOnScreen(self):
        self.calls.append("CenterOnScreen")

    def Show(self):
        self.calls.append("Show")

    def CreateStatusBar(self, *args, **kwds):
        return StatusBar(self, *args, **kwds)

    def CreateToolBar(self, *args, **kwds):
        return ToolBar(self, *args, **kwds)
        
    def SetMenuBar(self, mb):
        self.MenuBar = mb

    def SetToolBar(self, tb):
        self.ToolBar = tb

    def SetAutoLayout(self, flag):
        self.AutoLayout = flag

    def GetTextExtent(self, text):
        return (0, 0)

    def Centre(self):
        pass

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

################
# Dialogs
################

class Dialog(TopWindow):
    """Generic mock dialog.

    Set Dialog.retval to the simulated modal return value
    """
    retval = 'ok'

    def __init__(self, parent, *args, **kwds):
        TopWindow.__init__(self, parent)
        self.modal_return = Dialog.retval
        self.is_modal = True

    def ShowModal(self):
        return self.modal_return

    def Create(self, parent, id, pos, size, style, name):
        pass

    def CreateSeparatedButtonSizer(self, flags):
        return Sizer()

    def CreateStdDialogButtonSizer(self, flags):
        return Sizer()

    def CreateTextSizer(self, message):
        return Sizer()

    def EndModal(self, retCode):
        pass

    def GetAffirmativeId(self):
        pass

    def GetClassDefaultAttributes(variant):
        return variant

    def GetEscapeId(self):
        return -1

    def GetReturnCode(self):
        return self.modal_return

    def IsModal(self):
        return self.is_modal

    def SetAffirmativeId(self, affirmativeId):
        pass

    def SetEscapeId(self, escapeId):
        pass

    def SetReturnCode(self, returnCode):
        self.modal_return = returnCode

class ProgressDialog(Window):
    """Handled slightly differently than the other
    dialogs"""

    def __init__(self,
                 title="",
                 message="",
                 maximum=0,
                 parent=None,
                 style=None,
                 **kwds):
        Window.__init__(self, parent, **kwds)
        self.title = title
        self.message = message
        self.maximum = maximum
        self.style = style
        self.calls = []

    def Update(self, current=0, message=''):
        self.current = current
        self.message = message

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None


class DirDialog(Dialog):
    """Mocks the dir dialog. Set the class-level path
    variable to simulate user directory selection.

    Set Dialog.retval to the modal return value"""

    path = ""

    def __init__(self, parent, caption="", style=None):
        Dialog.__init__(self,parent)
        self.caption = caption
        self.style = style

    def GetPath(self):
        return DirDialog.path

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class FileDialog(Dialog):
    """Mocks the file dialog. Set the class-level paths
    variable to simulate user file selection.

    Set Dialog.retval to the modal return value"""

    paths = []

    def __init__(self, parent, message="", style=None, wildcard="", defaultFile=""):
        Dialog.__init__(self,parent)
        self.message = message
        self.style = style
        self.paths = FileDialog.paths
        self.wildcard = wildcard
        self.defaultFile = defaultFile

    def GetPaths(self):
        print "Getting paths:", self.paths
        return self.paths

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class ColourPickerCtrl(Dialog):
    paths = []

    def __init__(self, parent):
        Dialog.__init__(self,parent)


    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None        
        
###########
# Sizers
###########

class Sizer(object):

    def __init__(self,orientation=None, **kwds):
        self.orientation = orientation
        self.items = []
        self.calls = []

    def Add(self, item, *args, **kwds):
        self.items.append(item)

    def SetSizeHints(self, window):
        pass

    def Fit(self, window):
        pass

class BoxSizer(Sizer):
    def __init__(self, *args, **kwds):
        Sizer.__init__(self, *args, **kwds)

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None

class StaticBoxSizer(Sizer):
    def __init__(self, *args, **kwds):
        Sizer.__init__(self, None, **kwds)
        
class GridSizer(StaticBoxSizer):
    pass       

class FlexGridSizer(Sizer):
    def __init__(self, rows, cols, vgap, hgap):
        Sizer.__init__(self)

        self.rows = rows
        self.cols = cols
        self.vgap = vgap
        self.hgap = hgap

        self.growable_cols = []
        self.growable_rows = []

    def SetFlexibleDirection(self, orientation):
        self.orientation = orientation

    def AddGrowableCol(self, col):
        self.growable_cols.append(col)
    def AddGrowableRow(self, row):
        self.growable_rows.append(row)

    def __getattr__(self, attr):
        """Just fake any other methods"""
        self.calls.append(attr)
        return lambda *args, **kwds: None
     
  

#############
# Functions
#############

def MessageBox(msg, title="MessageBox", flags=None):
    pass

def ImageFromBitmap(*args):
    return Image()

def BitmapFromImage(*args):
    pass

def CursorFromImage(*args):
    pass

def FFont(*args):
    return Font(*args)
    
    
#
# This is a static class which needs to be emulated
#    
    
class TheClipboard(object):       
    def Open():        
        pass
    Open = staticmethod(Open)
    
    def GetData(data):        
        pass
    GetData = staticmethod(GetData) 

    def SetData(data):        
        pass
    SetData = staticmethod(GetData)       

    def Close():        
        pass
    Close = staticmethod(Close)  

class ArtProvider(object):       
    def GetBitmap(bmp, id):        
        pass
    GetBitmap = staticmethod(GetBitmap)
 
    
class lib(object):       
    class scrolledpanel():        
        pass

    
            
# Overwrite the wx namespace with the fake classes declared above
import wx
wx.__dict__.update(locals())