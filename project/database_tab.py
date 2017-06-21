import wx
from customwidgets import Toolbook, ToolBookTab
from molecule import MoleculeDb
from wx.lib.pubsub import Publisher as pub
from config_tab import MoleculesDbListCtrl
from molecule_window import MoleculeDefWindow

class DatabaseTab(ToolBookTab):
    def __init__(self, parent, image_fname, label=""):
        ToolBookTab.__init__(self, parent, image_fname, label)
        self.tabs = [(MoleculesDbTab, "mol32.png", "Molecules"),
                (ToolBookTab, "pot32.png", "Potentials"),
                     (ToolBookTab, "mol32.png", "Configs"),
                     ]
        self.notebook = Toolbook(self, self.tabs, position=wx.BK_BOTTOM)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.notebook, 1, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)
        self.Show()


class MoleculesDbTab(ToolBookTab):
    def __init__(self, parent, image_fname, label=""):
        ToolBookTab.__init__(self, parent, image_fname, label)
        # List control definition
        self.list_ctrl = MoleculesDbListCtrl(self, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.moldb = MoleculeDb("molecules.db")
        self.moldb.load_all()
        self.list_ctrl.add_molecules(self.moldb.molecules.values())
        
        bmp_add = wx.Image("add_btn.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bmp_del = wx.Image("delete_btn.ico", wx.BITMAP_TYPE_ICO).ConvertToBitmap()
        self.delButton = wx.BitmapButton(self, -1, bmp_del)
        self.addButton = wx.BitmapButton(self, -1, bmp_add)

        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer()
        buttonSizer.Add(self.delButton, 0, wx.ALL|wx.ALIGN_RIGHT)
        buttonSizer.Add(self.addButton, 0, wx.ALL|wx.ALIGN_RIGHT)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.list_ctrl, 1, wx.ALL|wx.EXPAND, 5)
        sizer.Add(buttonSizer, 0, wx.ALL|wx.EXPAND, 5)
        self.SetSizer(sizer)

        self.addButton.Bind(wx.EVT_BUTTON, self.onAddButton)
        self.delButton.Bind(wx.EVT_BUTTON, self.onDelButton)
        # Publisher
        pub.subscribe(self._onMoleculeAdded, 'molecule.added')

    def _onMoleculeAdded(self, message):
        molecule = message.data
        molecule_added = True
        if molecule is not None:
            try:
                self.moldb.add_molecule(molecule)
            except Exception as e:
                print e
                molecule_added = False
       
        if not molecule_added:
            diag_message = "Molecule '%s' already exists. Do you want to overwrite it?" % molecule.name
            ok_dialog = wx.MessageDialog(None,  diag_message, caption="Save molecule",
                style=wx.YES_NO|wx.STAY_ON_TOP|wx.NO_DEFAULT|wx.ICON_EXCLAMATION)
            if ok_dialog.ShowModal() == wx.ID_YES:
                self.moldb.del_molecule(molecule.name)
                self.moldb.add_molecule(molecule)
                item = self.list_ctrl.FindItem(-1, molecule.name.lower())
                self.list_ctrl.DeleteItem(item)
                self.list_ctrl.add_molecules(molecule)
                self.molDefWindow.Close()
            ok_dialog.Destroy()
        else:
            self.list_ctrl.add_molecules(molecule)
            self.molDefWindow.Close()

 
    def onAddButton(self, event):
        self.molDefWindow = MoleculeDefWindow()
        self.molDefWindow.Show()

    def onDelButton(self, event):
        items = self.list_ctrl.get_selected_items()
        mol_names =  [self.list_ctrl.GetItemText(i).lower() for i in items]
        ok_dialog = wx.MessageDialog(None, "Do you want to delete '" + "', '".join(mol_names) + "'?", caption="Delete molecule", style=wx.YES_NO|wx.STAY_ON_TOP|wx.NO_DEFAULT|wx.ICON_EXCLAMATION)
        if ok_dialog.ShowModal() == wx.ID_YES:
            for mol_name  in mol_names:
                try:
                    self.moldb.del_molecule(mol_name)
                    print mol_name.title() + " deleted!"
                except:
                    pass
                item = self.list_ctrl.FindItem(-1, mol_name.lower())
                self.list_ctrl.DeleteItem(item)
        ok_dialog.Destroy()
