import wx
from customwidgets import ToolBookTab
from molecule import MoleculeDb, Molecule
import moltempio
import wx.lib.mixins.listctrl as listmixins

class ConfigTab(ToolBookTab):
    def __init__(self, parent, image_fname, label=""):
        ToolBookTab.__init__(self, parent, image_fname, label)
        topSizer = wx.BoxSizer(wx.VERTICAL)
        self.moldb = MoleculeDb("molecules.db")
        self.moldb.load_all()

        ##WIDGETS##

        # Box definition widgets
        self.box_x_text = wx.TextCtrl(self)
        self.xLabel = wx.StaticText(self, -1, "x: ", style=wx.ALIGN_CENTRE)
        self.box_x_text.SetValue("0.0")
        self.box_y_text = wx.TextCtrl(self)
        self.yLabel = wx.StaticText(self, -1, "y: ", style=wx.ALIGN_CENTRE)
        self.box_y_text.SetValue("0.0")
        self.box_z_text = wx.TextCtrl(self)
        self.zLabel = wx.StaticText(self, -1, "z: ", style=wx.ALIGN_CENTRE)
        self.box_z_text.SetValue("0.0")
        self.densityLabel = wx.StaticText(self, -1, "Density:", style=wx.ALIGN_CENTRE)
        self.densityText = wx.StaticText(self, -1, "0.0", style=wx.ALIGN_CENTRE)
        self.boxTitleLabel = wx.StaticText(self, -1, "Box dimensions", style=wx.ALIGN_CENTRE)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.boxTitleLabel.SetFont(font)

        # Molecules list widgets
        self.mol_list_ctrl = MoleculesDbListCtrl(self, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.mol_list_ctrl.add_molecules(self.moldb.molecules.values())
        self.list_ctrl = MoleculesConfigListCtrl(self, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
        self.selectionTitleLabel = wx.StaticText(self, -1, "Molecule selection", style=wx.ALIGN_CENTRE)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.selectionTitleLabel.SetFont(font)

        # Buttons
        bmp_add = wx.Image("add_btn.png", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        bmp_del = wx.Image("delete_btn.ico", wx.BITMAP_TYPE_ICO).ConvertToBitmap()
        self.del_btn = wx.BitmapButton(self, -1, bmp_del)
        self.add_btn = wx.BitmapButton(self, -1, bmp_add)
        self.gen_btn = wx.Button(self, -1, "Generate", size=(-1, 44))


        ##SIZERS##
        
        gridSizer = wx.FlexGridSizer(rows=3, cols=2, hgap=5, vgap=5)
        gridSizer.Add(self.xLabel, 0)
        gridSizer.Add(self.box_x_text, 0)
        gridSizer.Add(self.yLabel, 0)
        gridSizer.Add(self.box_y_text, 0)
        gridSizer.Add(self.zLabel, 0)
        gridSizer.Add(self.box_z_text, 0)

        densitySizer = wx.BoxSizer(wx.HORIZONTAL)
        densitySizer.Add(self.densityLabel, 0, wx.TOP, 0)
        densitySizer.Add(self.densityText, 0, wx.LEFT, 3)

        boxInfoSizer = wx.BoxSizer(wx.VERTICAL)
        boxInfoSizer.Add(self.boxTitleLabel, 0, wx.BOTTOM|wx.TOP, 10)
        boxInfoSizer.Add(gridSizer, 0, wx.ALL, 5)
        boxInfoSizer.Add(densitySizer, 0, wx.ALL, 5)

        self.ln = wx.StaticLine(self, -1, style=wx.LI_VERTICAL)

        buttonsSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonsSizer.Add(self.gen_btn, 0, wx.TOP|wx.ALIGN_LEFT, 5)
        buttonsSizer.AddStretchSpacer()
        buttonsSizer.Add(self.del_btn, 0, wx.TOP|wx.ALIGN_RIGHT, 5)
        buttonsSizer.Add(self.add_btn, 0, wx.TOP|wx.ALIGN_RIGHT, 5)

        listAndButtonSizer = wx.BoxSizer(wx.VERTICAL)
        listAndButtonSizer.Add(self.list_ctrl, 0, wx.ALL, 0)
        listAndButtonSizer.Add(buttonsSizer, 1, wx.ALL|wx.EXPAND, 0)

        molSelectionSizer = wx.BoxSizer(wx.HORIZONTAL)
        molSelectionSizer.Add(listAndButtonSizer, 0, wx.ALL, 5)
        molSelectionSizer.Add(self.mol_list_ctrl, 1, wx.ALL|wx.EXPAND, 5)

        selectionTitleSizer = wx.BoxSizer(wx.VERTICAL)
        selectionTitleSizer.Add(self.selectionTitleLabel, 0, wx.ALL, 10)
        selectionTitleSizer.Add(molSelectionSizer, 1, wx.ALL|wx.EXPAND, 5)

        topSizer = wx.BoxSizer(wx.HORIZONTAL)
        topSizer.Add(boxInfoSizer, 0, wx.ALL|wx.EXPAND, 5)
        topSizer.Add(self.ln, 0, wx.ALL| wx.EXPAND, 5)
        topSizer.Add(selectionTitleSizer, 0, wx.ALL|wx.EXPAND, 5)

        self.SetSizer(topSizer)
        self.SetAutoLayout(True)
        topSizer.Fit(self)
        
        # Event binding
        self.del_btn.Bind(wx.EVT_BUTTON, self.onDelButton)
        self.add_btn.Bind(wx.EVT_BUTTON, self.onAddButton)
        self.gen_btn.Bind(wx.EVT_BUTTON, self.onGenerateConfig)
        self.Bind(wx.EVT_NOTEBOOK_PAGE_CHANGED, self.onTabChanged)

    def onTabChanged(self, event):
        print "CAMBIO"

    def onDelButton(self, event):
        self.list_ctrl._fix_cursor()
        items = self.list_ctrl.get_selected_items()
        mol_names =  [self.list_ctrl.GetItemText(i).lower() for i in items]
        for mol_name in mol_names:
            item = self.list_ctrl.FindItem(-1, mol_name.lower())
            self.list_ctrl.DeleteItem(item)


    def onAddButton(self, event):
        item = -1
        while 1:
            item = self.mol_list_ctrl.GetNextItem(item,
                            wx.LIST_NEXT_ALL,
                            wx.LIST_STATE_SELECTED)

            if item == -1:
                break
            mol_name =  self.mol_list_ctrl.GetItemText(item).lower()
            molecule = self.moldb.get_molecule(mol_name)
            self.list_ctrl.add_molecules(molecule)
            
    def onGenerateConfig(self, event):
        item = -1
        molecules = []
        try:
            lx = float(self.box_x_text.GetValue())
            ly = float(self.box_y_text.GetValue())
            lz = float(self.box_z_text.GetValue())
        except:
            print "Box length values are not well formated!"
            return

        if (lx == 0.0 or ly == 0.0 or lz == 0.0):
            print "Box dimensions have to be greater than 0.0!"
            return

        if self.list_ctrl.GetItemCount() > 0:
            while 1:
                item = self.list_ctrl.GetNextItem(item,
                                wx.LIST_NEXT_ALL,
                                wx.LIST_STATE_DONTCARE)

                if item == -1:
                    break

                mol_name =  self.list_ctrl.GetItemText(item).lower()
                mol_number = self.list_ctrl.GetItem(item, 2).GetText()
                if int(mol_number) == 0:
                    print "Specify the number of %s molecules." % mol_name
                    return
                molecule = self.moldb.get_molecule(mol_name)
                molecules.append((molecule, int(mol_number)))

            box_dims =  [(0.0, lx ), (0.0, ly), (0.0, lz)]
            conf_writer = moltempio.MTSystemWriter(box_dims, molecules)
            conf_writer.build_system_file()
            conf_writer.save()
            sys_writer_packmol = moltempio.PackmolSystemWriter(box_dims, molecules)
            sys_writer_packmol.build_system_file()
            sys_writer_packmol.save()
            print "System files generated!"
        else:
            print "Molecule list empty! -- Add some molecules."



class MoleculesConfigListCtrl(wx.ListCtrl, listmixins.TextEditMixin):
    def  __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                  size=(300,250), style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        listmixins.TextEditMixin.__init__(self)
        self.InsertColumn(0, 'Molecule') 
        self.SetColumnWidth(0, 100)
        self.InsertColumn(1, 'Potential') 
        self.SetColumnWidth(1, 100)
        self.InsertColumn(2, '# of molecules')
        self.SetColumnWidth(2, 100)
        self.index = 0

        self.Bind(wx.EVT_LIST_BEGIN_LABEL_EDIT, self.OnBeginLabelEdit)
        self.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.OnItemDeselected)

    def _fix_cursor(self):
        self.curRow = -1

    def add_molecules(self, molecules):
        mol_list = []
        if isinstance(molecules, Molecule):
            mol_list = [molecules]
        else:
            mol_list = molecules

        for molecule in mol_list:
            self.InsertStringItem(self.index, molecule.name.title())
            self.SetStringItem(self.index, 1, molecule.potential)
            self.SetStringItem(self.index, 2, "0")
        self._fix_cursor()

    def OnItemDeselected(self, event):
        self._fix_cursor()
        event.Skip()

    def get_selected_items(self):
        items = []
        item = -1
        while 1:
            item = self.GetNextItem(item,
                            wx.LIST_NEXT_ALL,
                            wx.LIST_STATE_SELECTED)

            if item == -1:
                break
            items.append(item)
        return items

    def OnBeginLabelEdit(self, event):
        #self._fix_cursor()
        if event.m_col != 2:
            event.Veto()
        else:
            event.Skip()



class MoleculesDbListCtrl(wx.ListCtrl): 

    def  __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                  size=(500,250), style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        self.InsertColumn(0, 'Name') 
        self.SetColumnWidth(0, 100)
        self.InsertColumn(1, 'Chem. formula') 
        self.SetColumnWidth(1, 100)
        self.InsertColumn(2, 'Type') 
        self.SetColumnWidth(2, 100)
        self.InsertColumn(3, 'Potentials')
        self.SetColumnWidth(3, 100)
        self.InsertColumn(4, 'Mol. weight')
        self.SetColumnWidth(4, 100)
        self.index = 0

    def add_molecules(self, molecules):
        if isinstance(molecules, Molecule):
            molecules = [molecules]
        if molecules:
            for molecule in molecules:
                self.InsertStringItem(self.index, molecule.name.title())
                self.SetStringItem(self.index, 1, molecule.chem_formula)
                self.SetStringItem(self.index, 2, molecule.mol_type)
                self.SetStringItem(self.index, 3, molecule.potential)
                self.SetStringItem(self.index, 4, str(molecule.mol_weight))
            self.index += 1

    def get_selected_items(self):
        items = []
        item = -1
        while 1:
            item = self.GetNextItem(item,
                            wx.LIST_NEXT_ALL,
                            wx.LIST_STATE_SELECTED)

            if item == -1:
                break
            items.append(item)
        return items
 
