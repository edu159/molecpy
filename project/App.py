import wx
from customwidgets import Toolbook, ToolBookTab
from config_tab import ConfigTab
from database_tab import DatabaseTab

class Splash(wx.SplashScreen):

    def __init__(self, parent=None, id=-1):

        image = "waiting.gif"
        aBitmap = wx.Image(name =image).ConvertToBitmap()
        splashStyle = wx.SPLASH_CENTRE_ON_PARENT
        splashDuration = 0 # milliseconds
        wx.SplashScreen.__init__(self, aBitmap, splashStyle,
                                 splashDuration, parent)

        gif = wx.animate.GIFAnimationCtrl(self, id, "load2.gif")
        self.gif.Play()
        self.Show()
        self.gif = gif

    def Run(self,):
        pass

#######################################################################
class MainFrame(wx.Frame):
    """
    Frame that holds all other widgets
    """
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        # Tab list
        w, h = wx.DisplaySize()
        wx.Frame.__init__(self, None, wx.ID_ANY,
                          "Poly-MD",
                   #       size=(w, h)
                          )
        panel = wx.Panel(self)

        self.Bind(wx.EVT_KILL_FOCUS, self.onFocus, self)
        self.tabs = [(ConfigTab, "config_tab.png", "Configuration"),
                (DatabaseTab, "db_tab.png", "Database"),
                     (ToolBookTab, "jobs_tab.png", "Jobs"),
                     ]
        self.notebook = Toolbook(panel, self.tabs)
        self.logConsole = wx.TextCtrl(panel)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.notebook, 5, wx.ALL|wx.EXPAND, 5)
        sizer.Add(self.logConsole, 1, wx.ALL|wx.EXPAND, 5)
        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        sizer.Fit(self)
        self.Show()

    def onFocus(self, event):
        event.Skip()
 

if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MainFrame()
    app.MainLoop()
