import wx
from molecule import Molecule
import moltempio
import molfetcher
from wx.lib.pubsub import Publisher as pub
from pymolinterface import PymolInterface
import threading
import time
import imageconvert
import Image
import customwidgets
import wx.animate

current_milli_time = lambda: int(round(time.time() * 1000))


class MoleculeDefWindow(wx.Frame):

    def __init__(self):
        """Constructor"""
        # Tab list
        self.potSelWindow = None
        self.current_molecule = Molecule()
        self.molfetch = molfetcher.MoleculeFetcher()
        w, h = wx.DisplaySize()
        wx.Frame.__init__(self, None, wx.ID_ANY, "Poly-MD", size=(w/3, h/3))
        panel = wx.Panel(self)
        self.mol_types = ["Atom", "Molecule", "Polymer", "Protein"]
        self.selected_pot_atom = None
        self.close_action = ""

        # Retrieve potential and molecule info
        self.potential = 'OPLSAA'
        self.available_potentials = moltempio.POTENTIALS.keys()
        #TODO: CHANGE! Use ATOM_TYPES[potential] instead, more general
        self.pot_atomtypes = moltempio.get_OPLS_atom_types(self.potential)
        # They are initially empty until a molecule is selected
        self.mol_atomtypes = None
        self.mol_tags = []
        self.pymol_loaded = False
        self.pymol_cmd = None
        self.setup_dialog = None

        ##WIDGETS##

        # Search and display
        self.mol_display =  MoleculeDisplay(panel, "generic_molecule.png")
        self.search_box = wx.Panel(panel, style=wx.BORDER_RAISED)
        self.bitmap_w = wx.StaticBitmap(self.search_box, -1,wx.Bitmap('./search_btn.png'), style=wx.BORDER_RAISED)
        self.m_box = MoleculeSearchBox(self.search_box, size=(200, -1))
        self.ln = wx.StaticLine(self.search_box, -1, style=wx.LI_VERTICAL)
        #self.databaseLabel = wx.StaticText(panel, -1, "Database:", style=wx.ALIGN_CENTRE)
        sizerxx = wx.BoxSizer(wx.HORIZONTAL)
        sizerxx.Add(self.bitmap_w, 0, wx.RIGHT, 2)
        sizerxx.Add(self.ln, 0, wx.LEFT| wx.EXPAND, 1)
        sizerxx.Add(self.m_box, 0, wx.LEFT|wx.EXPAND, 0)
        self.search_box.SetSizer(sizerxx)
        

        self.database_box = wx.ComboBox(panel, size=(100, -1), value="PubChem", choices=["PubChem"], style=wx.CB_READONLY)

        # Molecule info
        self.molnameBox = wx.TextCtrl(panel, -1, size=(150,-1))
        self.molnameLabel = wx.StaticText(panel, -1, "Name:", style=wx.ALIGN_CENTRE)
        self.chemFormBox = wx.TextCtrl(panel, -1, size=(150,-1))
        self.chemFormLabel = wx.StaticText(panel, -1, "Chemg. formula:", style=wx.ALIGN_CENTRE)
        self.typeBox = wx.ComboBox(panel, size=(150, -1), choices=self.mol_types)
        self.typeLabel = wx.StaticText(panel, -1, "Type:", style=wx.ALIGN_CENTRE)
        self.molweightBox = wx.TextCtrl(panel, -1, size=(150,-1) )
        self.molweightLabel = wx.StaticText(panel, -1, "Mol. weight:", style=wx.ALIGN_CENTRE)
        self.loadFileBtn = wx.Button(panel, -1, "...")

        # Buttons
        self.addBtn = wx.Button(panel, -1, "Add")
        self.closeBtn = wx.Button(panel, -1, "Close")
        self.optimizeBtn = wx.Button(panel, -1, "Optimize", size=(100,50))
        self.optimizeGlobalBtn = wx.Button(panel, -1, "Optimize Global", size=(100,50))
        self.applyBtn = wx.Button(panel, -1, "Apply")

        # Widget for the table
        self.list_ctrl = AtomListCtrl(panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN)

        #Selection mode widgets
        self.potential_label = wx.StaticText(panel, -1, "Potential:", style=wx.ALIGN_CENTRE)
        self.potential_box = wx.ComboBox(panel, size=(100,-1), style=wx.CB_READONLY, value=self.potential, choices=self.available_potentials)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.new_atom_label =  wx.StaticText(panel, -1, "[Potential atom]")
        self.targ_atom_label =  wx.StaticText(panel, -1, "[Molecule atom]")
        self.select_pot_atom_btn = wx.Button(panel, -1, label="Select...")
        font2 = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.select_pot_atom_label =  wx.StaticText(panel, -1)
        self.select_pot_atom_label.SetFont(font2)
        self.new_atom_label.SetFont(font)
        self.new_atom_label.SetFont(font)
        self.targ_atom_label.SetFont(font)
        self.radiobox_sel_expr = wx.RadioButton(panel, -1, label = 'Expression selection')
        self.radiobox_sel_mouse = wx.RadioButton(panel, -1, label = 'Mouse selection')
        self.mol_atomtype_label = wx.StaticText(panel, -1, "Atom: ")
        self.mol_atomtype_tbox = wx.ComboBox(panel, choices=[], size=(165,-1), style=wx.CB_READONLY)
        self.expr_atomtype_tbox = wx.SearchCtrl(panel, size=(200,-1))
        self.expr_atomtype_tbox.SetDescriptiveText("Expression...")
        self.expr_atomtype_tbox.ShowSearchButton(False)
        font = wx.Font(9, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_LIGHT)
        self.expr_atomtype_tbox.SetFont(font)
        self.mol_atomtype_tbox.SetFont(font)
        self.toggle_name_checkbox = wx.CheckBox(panel, id=wx.ID_ANY, label="Toggle names")


        # Separators 
        self.top_ln = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        self.bottom_ln = wx.StaticLine(panel, -1, style=wx.LI_HORIZONTAL)
        self.top_title = wx.StaticText(panel, -1, "Molecule data")
        self.bottom_title = wx.StaticText(panel, -1, "Potential configuration")
        font = wx.Font(12, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.top_title.SetFont(font)
        self.bottom_title.SetFont(font)

        self.enablePotentialConfig(False)
        ## SIZERS ##

         # Grid sizer for molecule info
        gridSizer = wx.FlexGridSizer(rows=2, cols=4, hgap=10, vgap=5)
        gridSizer.Add(self.molnameLabel, 0, wx.ALIGN_CENTER)
        gridSizer.Add(self.molnameBox, 0)
        gridSizer.Add(self.chemFormLabel, 0, wx.ALIGN_CENTER)
        gridSizer.Add(self.chemFormBox, 0)
        gridSizer.Add(self.typeLabel, 0, wx.ALIGN_CENTER)
        gridSizer.Add(self.typeBox, 0)
        gridSizer.Add(self.molweightLabel, 0, wx.ALIGN_CENTER)
        gridSizer.Add(self.molweightBox, 0)
        

        # Box sizer for display and searchbar	
        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(self.search_box, 0, wx.ALL, 5)
        searchSizer.Add(self.database_box , 0, wx.ALL, 5)
        searchSizer.Add(self.loadFileBtn, 0, wx.ALL, 5)
        topRightHalfSizer = wx.BoxSizer(wx.VERTICAL)
        topRightHalfSizer.Add(searchSizer, 0, wx.ALL | wx.ALIGN_TOP, 5)
        topRightHalfSizer.Add(gridSizer, 0, wx.ALL | wx.ALIGN_TOP | wx.ALIGN_LEFT, 5)
        topRightHalfSizer.AddStretchSpacer()
        topRightHalfSizer.Add(self.optimizeBtn, 0, wx.TOP | wx.ALIGN_BOTTOM, 5)
        topRightHalfSizer.Add(self.optimizeGlobalBtn, 0, wx.TOP | wx.ALIGN_BOTTOM, 5)
        topRightHalfSizer.Add(self.toggle_name_checkbox, 0, wx.TOP | wx.ALIGN_BOTTOM, 5)
        topRightHalfSizer.Add(self.toggle_name_checkbox, 0, wx.ALL, 5)
        topHalfSizer = wx.BoxSizer(wx.HORIZONTAL)
        topHalfSizer.Add(self.mol_display.bitmap_panel,0 , wx.ALL, 5)
        topHalfSizer.Add(topRightHalfSizer, 1, wx.ALL|wx.EXPAND, 5)



        # Box sizer for Selection widgets
        bottomLeftHalfSizer = wx.BoxSizer(wx.VERTICAL)
        bottomLeftHalfSizer.Add(self.potential_label, 0, wx.ALIGN_LEFT)
        bottomLeftHalfSizer.Add(self.potential_box, 0, wx.ALIGN_LEFT)

        bottomLeftHalfSizer.Add(self.targ_atom_label, 0, wx.ALIGN_LEFT |wx.TOP | wx.BOTTOM, 10)
        bottomLeftHalfSizer.Add(self.radiobox_sel_mouse , 0, wx.ALIGN_LEFT|wx.ALL,5) 
        bottomLeftHalfSizer.Add(self.radiobox_sel_expr , 0, wx.ALIGN_LEFT| wx.ALL, 5)

        mol_atomtype_sizer = wx.BoxSizer(wx.HORIZONTAL)
        mol_atomtype_sizer.Add(self.mol_atomtype_label, 0, wx.ALIGN_CENTER)
        mol_atomtype_sizer.Add(self.mol_atomtype_tbox, 0, wx.ALIGN_LEFT)
        bottomLeftHalfSizer.Add(mol_atomtype_sizer, 0, wx.ALIGN_LEFT| wx.LEFT, 20)

        bottomLeftHalfSizer.Add(wx.BoxSizer(wx.VERTICAL), 0, wx.TOP| wx.BOTTOM, 3)
        bottomLeftHalfSizer.Add(self.expr_atomtype_tbox, 0, wx.ALIGN_LEFT| wx.LEFT, 20)

        bottomLeftHalfSizer.Add(self.new_atom_label, 0, wx.ALIGN_LEFT|wx.TOP | wx.BOTTOM, 10)

        select_pot_atom_sizer = wx.BoxSizer(wx.HORIZONTAL)
        select_pot_atom_sizer.Add(self.select_pot_atom_btn, 0, wx.ALIGN_LEFT | wx.LEFT, 10)
        select_pot_atom_sizer.Add(self.select_pot_atom_label, 0, wx.ALIGN_CENTER | wx.LEFT, 20)
        bottomLeftHalfSizer.Add(select_pot_atom_sizer, 0, wx.ALIGN_LEFT)
        bottomLeftHalfSizer.Add(self.applyBtn, 1, wx.ALIGN_LEFT|wx.EXPAND|wx.ALL, 5)


        bottomHalfSizer = wx.BoxSizer(wx.HORIZONTAL)
        bottomHalfSizer.Add(bottomLeftHalfSizer, 0, wx.ALL, 5)
        bottomHalfSizer.Add(self.list_ctrl, 1, wx.EXPAND|wx.ALL, 5)
        
 

        # Top level vertical box sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.top_title, 0, wx.ALL, 5)
        sizer.Add(self.top_ln, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(topHalfSizer, 0, wx.ALL, 5)
        sizer.Add(self.bottom_title, 0, wx.ALL, 5)
        sizer.Add(self.bottom_ln, 0, wx.ALL|wx.EXPAND, 5)
        sizer.Add(bottomHalfSizer, 0, wx.ALL, 5)
        sizer.Add(self.addBtn, 0, wx.ALL, 5)
        sizer.Add(self.closeBtn, 0, wx.ALL, 5)
        panel.SetSizer(sizer)
        panel.SetAutoLayout(True)
        sizer.Fit(self)


        # Event binding
        self.loadFileBtn.Bind(wx.EVT_BUTTON, self.onLoadFile)
        self.addBtn.Bind(wx.EVT_BUTTON, self.on_add_button)
        self.optimizeBtn.Bind(wx.EVT_BUTTON, self.on_optimize_button)
        self.optimizeGlobalBtn.Bind(wx.EVT_BUTTON, self.on_optimize_global_button)
        self.applyBtn.Bind(wx.EVT_BUTTON, self._on_apply_button)
        self.radiobox_sel_expr.Bind(wx.EVT_RADIOBUTTON, self._onRadioButton) 
        self.radiobox_sel_mouse.Bind(wx.EVT_RADIOBUTTON, self._onRadioButton)
        self.select_pot_atom_btn.Bind(wx.EVT_BUTTON, self._onPotSelectionClick)
        self.potential_box.Bind(wx.EVT_COMBOBOX, self._onPotentialBox)
        self.typeBox.Bind(wx.EVT_COMBOBOX, self._onMolTypeBox)
        self.closeBtn.Bind(wx.EVT_BUTTON, self.onCloseBtn)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.toggle_name_checkbox.Bind(wx.EVT_CHECKBOX, self.onToggle)

        # Subscriptions to the publisher
        pub.subscribe(self._onMoleculeSelected, 'molecule.selected')
        pub.subscribe(self._change_current_molecule, 'molecule.changed')
        pub.subscribe(self._wait_animation, 'molecule.animate')
        pub.subscribe(self._loadPymol, 'pymol.load')
        pub.subscribe(self._closedPymol, 'pymol.close')

    def onToggle(self, event):
        if self.pymol_cmd is not None:
            if self.toggle_name_checkbox.IsChecked():
                self.pymol_cmd.toggle_name("elem")
            else:
                self.pymol_cmd.toggle_name("name")

    def onClose(self,e):
        if self.pymol_cmd is not None:
            self.close_action = "PYMOL_CLOSE"
            self.pymol_cmd.shutdown()
        else:
            self.Destroy()

    def onCloseBtn(self,e):
        self.Close()

    def onLoadFile(self, e):
        self.openFileDialog = wx.FileDialog(self, "Open", "", "",
                                       "*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        self.openFileDialog.ShowModal()
        print self.openFileDialog.GetPath()
        self.openFileDialog.Destroy()

    def _onPotSelectionClick(self, e):
        self.potSelWindow = PotentialSelectionWindow(self, self.pot_atomtypes, self.mol_tags)
        if self.potSelWindow.ShowModal() == wx.ID_OK:
            self.selected_pot_atom = self.potSelWindow.GetValue()
            self.select_pot_atom_label.SetLabel("%s (%s)"  % (self.selected_pot_atom[0], self.selected_pot_atom[1]))

    def _wait_animation(self, e):
        self.mol_display.set_animation(True)

    def _onMolTypeBox(self, e):
        mol_type_id = e.GetEventObject().GetSelection()
        self.current_molecule.mol_type = self.mol_types[mol_type_id]

    def _onPotentialBox(self, e):
        pot_id = e.GetEventObject().GetSelection()
        self.potential = self.available_potentials[pot_id]
        self.pot_atomtypes = moltempio.get_OPLS_atom_types(self.potential)
        print self.potential + " selected."

    def _onRadioButton(self, e):
        rb = e.GetEventObject()
        if ('Expression' in rb.GetLabel()):
            print "Selection mode by expression."
            self.mol_atomtype_tbox.Enable(True)
            self.expr_atomtype_tbox.Enable(True)
        else:
            print "Selection mode by mouse."
            self.mol_atomtype_tbox.Enable(False) 
            self.expr_atomtype_tbox.Enable(False) 

    def _onMoleculeSelected(self, message):
        molecule = message.data
        self.mol_display.set_animation(False)
        self.mol_display.set_mol_image(molecule.image)
        self.molnameBox.SetValue(molecule.name)
        self.molweightBox.SetValue(str(float(molecule.mol_weight)))
        self.chemFormBox.SetValue(molecule.chem_formula)
        self.current_molecule.loaded = True
        print "Selected " + molecule.name


    def _change_current_molecule(self, message):
        if self.current_molecule.loaded:
            self.setup_dialog = SetupDialogProgressDialog(self)
            self.current_molecule = message.data
            self.current_molecule.potential = self.potential
            mol_name = self.current_molecule.name
            def setup_molecule_task(mol_name):
                wx.CallAfter(pub.sendMessage, 'setupdialog.update', 20)
                self.molfetch.get_mol_SDF(mol_name)
                wx.CallAfter(pub.sendMessage, 'setupdialog.update', 60)
                self.mol_tags = self.molfetch.get_mol_tags(mol_name)
                wx.CallAfter(pub.sendMessage, 'setupdialog.update', 80)
                if self.pymol_cmd is not None:
                    self.close_action = "PYMOL_DESTROY"
                    self.pymol_cmd.shutdown()
                self.pymol_cmd = PymolInterface()
                self.pymol_cmd.load_molecule(self.current_molecule.name + '.sdf')
                wx.CallAfter(pub.sendMessage, 'setupdialog.update', 90)
                time.sleep(0.5)
                wx.CallAfter(pub.sendMessage, 'setupdialog.update', 100)
                wx.CallAfter(pub.sendMessage, 'pymol.load')

            thread = threading.Thread(target=setup_molecule_task, args=(mol_name,))
            thread.start()

    def _closedPymol(self, message):
        self.Destroy()

    def _loadPymol(self, message):
        def check_pymol_alive(pymol_process):
            pymol_process.join()
            if self.close_action != "PYMOL_DESTROY":
                self.close_action = "";
                wx.CallAfter(pub.sendMessage, 'pymol.close')
            self.close_action = "";

        thread = threading.Thread(target=check_pymol_alive, args=(self.pymol_cmd.cmd.pymol_process,))
        thread.start()
        self.mol_atomtypes = moltempio.get_model_atom_types(self.pymol_cmd.get_molecule_model())
        self.mol_atomtype_tbox.Clear()
        self.select_pot_atom_label.SetLabel("")
        self.expr_atomtype_tbox.SetDescriptiveText("Expression...")
        self.selected_pot_atom = None
        self.typeBox.SetValue("Molecule")
        self.mol_atomtype_tbox.AppendItems(self.mol_atomtypes)
        self.list_ctrl.fill_from_mol_model(self.pymol_cmd.get_molecule_model(), self.pot_atomtypes)
        self.pymol_loaded = True
        self.enablePotentialConfig(True)
     
    def on_add_button(self, event):
        if self.pymol_loaded: #TODO and potential assigned
            mol_writer = moltempio.MTMolWriter(self.potential, self.pymol_cmd)
            mol_writer.build_molecule_file()
            mol_writer.save()
            self.pymol_cmd.save_molecule(self.current_molecule.name + '.pdb')
            pub.sendMessage('molecule.added', self.current_molecule)
        else:
            print "There is no molecule loaded!"


    def on_optimize_button(self, event):
        def optimize():
            self.pymol_cmd.optimize_molecule_geometry(self.current_molecule.name)
            wx.CallAfter(pub.sendMessage,'execdialog.finish', None) 
        # Background task 
        self.diag = ExecDialog(self, "Optimizing", "Running...")
        self.thread = threading.Thread(target=optimize, args=())
    	self.thread.start()
        if self.diag.ShowModal() == wx.ID_CANCEL:
            print "CANCELADO" 
        else:
            print "OK"
        self.diag.Destroy()

    def on_optimize_global_button(self, event):
        #self.pymol_cmd._correct_H_bonding()
        self.pymol_cmd.conf_search(self.current_molecule.name)

    def enablePotentialConfig(self, enable):
        self.applyBtn.Enable(enable)
        self.list_ctrl.Enable(enable)
        self.potential_box.Enable(enable)
        self.select_pot_atom_btn.Enable(enable)
        self.radiobox_sel_expr.Enable(enable)
        self.radiobox_sel_mouse.Enable(enable)
        self.mol_atomtype_tbox.Enable(enable)
        self.expr_atomtype_tbox.Enable(enable)

    
    #TODO: Improve name saving - El(234) vs El and 234 separated
    def _on_apply_button(self, event):
        atom_name_out = ""
        atom_name_in = ""
        atoms_changed = 0

        #TODO: Change to dialog with yes/no - RETHINK THIS - First time it gets in should not know - RETHINK THIS - First time it gets in should not know
        """
        if self.potential_box.GetValue() != self.current_molecule.potential:
            print "Be carefull you are using a different potential for different atoms!"
            self.current_molecule.potential = self.potential
            return
        """

        if self.selected_pot_atom is not None:
            atom_name_out  = self.selected_pot_atom[0]
        else:
            print "Potential atom not selected!"
            return
        atomtype_id = self.selected_pot_atom[1]
        if self.radiobox_sel_mouse.GetValue():
            try:
                atoms_changed = self.pymol_cmd.change_atom_name_sel(atom_name_out, pot_atomtype_id=atomtype_id, color=self.pymol_cmd.get_random_color())
            except Exception as e:
                print e  
        else:

            if not self.mol_atomtype_tbox.GetValue():
                print "Select an atom from the molecule!"
                return 
            elem_id = self.mol_atomtype_tbox.GetCurrentSelection()
            atom_name_in = self.mol_atomtypes[elem_id]
            print "id:", atomtype_id, " name: ", atom_name_out, " namein: ", atom_name_in
            expression = self.expr_atomtype_tbox.GetValue()
            atoms_changed = self.pymol_cmd.change_atom_name_cond(atom_name_in, atom_name_out, expression, color=self.pymol_cmd.get_random_color())

        self.mol_atomtypes = moltempio.get_model_atom_types(self.pymol_cmd.get_molecule_model())
        self.mol_atomtype_tbox.Clear()
        self.mol_atomtype_tbox.AppendItems(self.mol_atomtypes)
        # Erase content
        self.mol_atomtype_tbox.SetValue("")
        self.mol_atomtype_tbox.SetSelection(-1)

        self.list_ctrl.fill_from_mol_model(self.pymol_cmd.get_molecule_model(), self.pot_atomtypes)


class AtomListCtrl(wx.ListCtrl):

    def  __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                  size=(500, 250), style=0):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        self.InsertColumn(0, 'No') 
        self.SetColumnWidth(0, 50)
        self.InsertColumn(1, 'Pot. index') 
        self.SetColumnWidth(1, 100)
        self.InsertColumn(2, 'Description')
        self.SetColumnWidth(2, 100)
        self.InsertColumn(3, 'Atom name')
        self.SetColumnWidth(3, 100)
        self.InsertColumn(4, 'x')
        self.SetColumnWidth(4, 50)
        self.InsertColumn(5, 'y')
        self.SetColumnWidth(5, 50)
        self.InsertColumn(6, 'z')
        self.SetColumnWidth(6, 50)

    def fill_from_mol_model(self, mol_model, pot_atomtypes):
        index = 0
        self.DeleteAllItems()
        for atom in mol_model.atom:
            pot_atom_idx = PymolInterface._index_from_name(atom.name)
            print "atomid:", pot_atom_idx
            self.InsertStringItem(index, str(atom.index))
            if (pot_atom_idx in pot_atomtypes.keys()):
                self.SetStringItem(index, 1, pot_atom_idx)
                self.SetStringItem(index, 2, pot_atomtypes[pot_atom_idx][1])
            else:
                self.SetStringItem(index, 1, 'None')
                self.SetStringItem(index, 2, 'None')
            self.SetStringItem(index, 3, atom.name) 
            self.SetStringItem(index, 4, str(atom.coord[0]))
            self.SetStringItem(index, 5, str(atom.coord[1]))
            self.SetStringItem(index, 6, str(atom.coord[2]))
            index += 1

class MoleculeDisplay:

    def __init__(self, parent, mol_fname, animation=False):
        self.ANIMATION_GIF = "waiting.gif"
        self.DEFAULT_MOLECULE = "generic_molecule.png"
        self.parent = parent
        self.mol_fname = mol_fname
        self.loading_animation = False
        self.mol_image = Image.open(self.mol_fname)
        imwx = imageconvert.WxImageFromPilImage(self.mol_image)
        self.mol_bitmap = wx.BitmapFromImage(imwx)
        self.bitmap_panel = wx.Panel(self.parent, style=wx.RAISED_BORDER)
        self.bitmap_widget = wx.StaticBitmap(self.bitmap_panel, -1, self.mol_bitmap)
        self.animCtrl = wx.animate.AnimationCtrl(self.bitmap_panel, wx.ID_ANY, wx.animate.NullAnimation, (-1 ,-1 ), ( -1,-1 ), wx.animate.AC_DEFAULT_STYLE )
        self.animCtrl.LoadFile(self.ANIMATION_GIF)
        self.set_animation(animation)

    def set_animation(self, enable):
        if enable:
            self.bitmap_widget.Enable(True)
            self.bitmap_widget.Hide()
            self.animCtrl.Show()
            self.animCtrl.Play()
        else:
            self.animCtrl.Hide()
            self.bitmap_widget.Show()
            if (self.mol_fname == self.DEFAULT_MOLECULE):
                self.bitmap_widget.Enable(False)

    def set_mol_image(self, mol_image):
        self.bitmap_widget.Enable(True)
        self.bitmap_widget.SetBitmap(wx.BitmapFromImage(mol_image))


class PotentialSelectionWindow(wx.Dialog):
    def __init__(self, parent, pot_atomtypes, suggestions=[]):
        """Constructor"""
        # Tab list
        w, h = wx.DisplaySize()
        self.parent = parent
        wx.Dialog.__init__(self, parent, wx.ID_ANY, "Poly-MD", size=(w, h))
        self.panel = wx.Panel(self)
        self.pot_atomtypes = pot_atomtypes
        self.list_ctrl = PotentialAtomsListCtrl(self.panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN|wx.LC_SINGLE_SEL)
        self.suggestions = suggestions
        self.list_ctrl.fill_from_pot_atomtypes(self.pot_atomtypes, self.suggestions)
        self.SetSizeHints(400+10,500,1200,1200)
        self.searchBox = wx.SearchCtrl(self.panel)
        self.closeBtn = wx.Button(self.panel, -1, "Close")
        self.selectBtn = wx.Button(self.panel, -1, "Select")
        self.selectBtn.Enable(False)

        sizer = wx.BoxSizer(wx.VERTICAL)
        searchBoxSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchBoxSizer.Add(self.searchBox, 0, wx.ALL, 5)
        sizer.Add(searchBoxSizer, 0, wx.ALL, 5)
        sizer.Add(self.list_ctrl, 1, wx.EXPAND|wx.ALL, 5)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonSizer.AddStretchSpacer()
        buttonSizer.Add(self.closeBtn, 0, wx.ALIGN_RIGHT)
        buttonSizer.Add(self.selectBtn, 0, wx.ALIGN_RIGHT)
        sizer.Add(buttonSizer, 0, wx.EXPAND|wx.ALL, 5)
        self.panel.SetSizer(sizer)
        sizer.Fit(self)
        self.panel.SetAutoLayout(True)

        self.searchBox.Bind(wx.EVT_TEXT, self.onKeyTyped)
        self.selectBtn.Bind(wx.EVT_BUTTON, self.onSelect)
        self.closeBtn.Bind(wx.EVT_BUTTON, self.onClose)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.onItemSelected)
        self.list_ctrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.onItemDeselected)

    def onItemSelected(self, event):
        self.selectBtn.Enable(True)

    def onItemDeselected(self, event):
        self.selectBtn.Enable(False)

    def onKeyTyped(self, event):
        search_txt = self.searchBox.GetValue().lower()
        selection = {k: v for k, v in self.pot_atomtypes.iteritems() if search_txt in v[1].lower()}
        self.list_ctrl.fill_from_pot_atomtypes(selection, self.suggestions)

    def onSelect(self, event):
        self.EndModal(wx.ID_OK)

    def GetValue(self):
        idx = self.list_ctrl.GetFirstSelected()
        atom_name = self.list_ctrl.GetItem(idx, 1).GetText()
        atom_idx = self.list_ctrl.GetItem(idx, 0).GetText()
        return (atom_name, atom_idx)

    def onClose(self, event):
        self.EndModal(wx.ID_CANCEL)


class SetupDialogProgressDialog(wx.ProgressDialog):

    def __init__(self, parent):
        wx.ProgressDialog.__init__(self, "Setup Molecule", "Loading molecule...", maximum=100, parent=parent,
                               style=wx.PD_APP_MODAL|wx.PD_AUTO_HIDE)
        pub.subscribe(self._onUpdate, 'setupdialog.update')

    def _onUpdate(self, message):
            print message.data
            self.Update(message.data)

class ExecDialog(wx.Dialog):
    def __init__(self, parent, caption, msg):
        wx.Dialog.__init__(self, parent, -1, caption, size=(300, 100))
        self.bitmap_panel = wx.Panel(self, style=wx.RAISED_BORDER)
        self.ANIMATION_GIF = "loading.gif"
        self.cancelButton = wx.Button(self, wx.ID_CANCEL, "Cancel")
        self.animCtrl = wx.animate.AnimationCtrl(self.bitmap_panel, wx.ID_ANY, wx.animate.NullAnimation, (-1 ,-1 ), ( -1,-1 ), wx.animate.AC_DEFAULT_STYLE )
        self.animCtrl.LoadFile(self.ANIMATION_GIF)
        pub.subscribe(self.onFinish, 'execdialog.finish')
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.bitmap_panel, 0, wx.NO_BORDER, 1)
        sizer.Add(self.cancelButton, 0, wx.NO_BORDER|wx.EXPAND, 1)
        self.animCtrl.Play()
        self.SetSizer(sizer)
        sizer.Fit(self)
        self.cancelButton.Bind(wx.EVT_BUTTON, self.onClose)

    def onClose(self, event):
        self.EndModal(wx.ID_CANCEL)
        
    def onFinish(self, message):
        self.EndModal(wx.ID_OK)
    

class PotentialAtomsListCtrl(wx.ListCtrl): 

    def  __init__(self, parent, ID=wx.ID_ANY, pos=wx.DefaultPosition,
                  size=(400,250), style=None):
        wx.ListCtrl.__init__(self, parent, ID, pos, size, style)
        self.InsertColumn(0, 'Pot. Index') 
        self.SetColumnWidth(0, 100)
        self.InsertColumn(1, 'Atom') 
        self.SetColumnWidth(1, 100)
        self.InsertColumn(2, 'Description') 
        self.SetColumnWidth(2, 200)

    def fill_from_pot_atomtypes(self, pot_atomtypes, suggestions=[]):
        self.DeleteAllItems()
        colourify = False
        for atom_type_id in pot_atomtypes.keys():
            atom_info = pot_atomtypes[atom_type_id][1]
            atom_name = pot_atomtypes[atom_type_id][0]
            index = self.GetItemCount()
            for s in suggestions:
                if s in atom_info.lower(): 
                    index = 0
                    colourify = True

                    #self.SetItemBackgroundColour(index, (102, 179, 255))
            self.InsertStringItem(index, str(atom_type_id))
            self.SetStringItem(index, 1, atom_name) 
            self.SetStringItem(index, 2, atom_info)

            if colourify:
                self.SetItemTextColour(index, (0, 172, 230))
                colourify = False



class MoleculeSearchBox(customwidgets.SearchCtrlAutoComplete):
    def __init__(self, *args, **kwargs):
        self.molecule_choices =  [""]
        self.enter_pressed = False
        self.new_search = True
        self.current_molecule = Molecule()
        self.searched = True 

        self.molfetch = molfetcher.MoleculeFetcher()
        kwargs["choices"] = self.molecule_choices
        kwargs["selectCallback"] =  self.selectCallback
	kwargs["style"] = wx.NO_BORDER
        self.parent = args[0]
        self.type_timer = wx.Timer(self.parent)
        self.parent.Bind(wx.EVT_TIMER, self.type_timer_cb)
        customwidgets.SearchCtrlAutoComplete.__init__(self, *args, **kwargs) 
         # Custom widget
        self.SetEntryCallback(self.setDynamicChoices)
        self.typing_evt_time = 0.0 
        self.dropdownlistbox.Bind(wx.EVT_LIST_ITEM_SELECTED, self.OnItemSelect)
        self.Bind(wx.EVT_TEXT_ENTER, self.on_enter_press)

    def on_enter_press(self, event):
        wx.CallAfter(pub.sendMessage, 'molecule.changed', self.current_molecule)
        self.enter_pressed = True
        self.new_search = False

    
    def OnItemSelect(self, event):
        mol_name = event.GetItem().GetText()
        pub.sendMessage('molecule.animate')

        ##TODO Add a call to molecule.loaded in parent

        def get_molecule_info_task(mol_name):
            ## TRY
            mol_data = self.molfetch.get_mol_data(mol_name)
            mol_thumbnail = self.molfetch.get_mol_thumbnail(mol_name)
            ## EXCEPT
            self.current_molecule = Molecule(mol_name.lower(), mol_data, 
                                             image=mol_thumbnail, format='PUBCHEM')
            wx.CallAfter(pub.sendMessage,'molecule.selected', self.current_molecule) 
        # Background task 
        thread = threading.Thread(target=get_molecule_info_task, args=(mol_name,))
    	thread.start()

    def setDynamicChoices(self, event=None):
        # Get molecules from internet
        text = self.GetValue().lower()
        if (self._DecideToSearch(text)):
            self.molecule_choices = self.molfetch.search_molecules(text)
            text = text.title()
            self.molecule_choices = [choice.lower().title() for choice in self.molecule_choices]
            choices = [choice for choice in self.molecule_choices if choice.startswith(text)]
            restof_choices = sorted([choice for choice in self.molecule_choices if (choice not in choices)])
            self.molecule_choices = choices + restof_choices
            self.SetChoices(self.molecule_choices)
             

    def _DecideToSearch(self, string):
        self.type_timer.Stop()
        current_evt_time = current_milli_time()
        search = False
        if not self.enter_pressed:
            if len(string) > 1:
                print "Milis:",  abs(current_evt_time - self.typing_evt_time)
                print "searched: " , self.searched
                if not self.searched and abs(current_evt_time - self.typing_evt_time) > 500:
                    print "Search", current_evt_time
                    search =  True
                    self.searched = True
                else:
                    print "No Search"
                    self.searched = False
                    self.type_timer.Start(500)
            else:
                self.searched = True
                self.molecule_choices = [""]
                self.SetChoices(self.molecule_choices)
            self.typing_evt_time = current_evt_time

        if not self.new_search:
            self.enter_pressed = False
        return search

    def type_timer_cb(self, event):
        evt = wx.CommandEvent(wx.wxEVT_COMMAND_TEXT_UPDATED)
        evt.SetEventObject(self) 
        evt.SetId(self.GetId()) 
        self.GetEventHandler().ProcessEvent(evt) 

    def selectCallback(self, values):
        print "Values ", values 


