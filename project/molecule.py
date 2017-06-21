import shelve

FORMATS = ["CUSTOM", "PUBCHEM"]
class Molecule():
    def __init__(self, name=None, args=None, image=None, mol_type=None,
            format="CUSTOM", from_db=False, attr_dict=None, potential=None):
        
        if from_db:
            for k,v in attr_dict.items():
                setattr(self, k, v)
        else:
            self.format = format
            self.potential = potential
            self.image = image
            if  mol_type is None:
                self.mol_type = 'UNKNOWN'
            else:
                self.mol_type = mol_type
            self.name = name
            self.chem_formula = None
            self.mol_weight = None
            self.id = None
            self.tags  = None
            if format in FORMATS:
                if format == "PUBCHEM":
                    self._init_pubchem(args)
                if format == "CUSTOM":
                    self._init_custom(args)
        self.loaded = False


    def _init_pubchem(self, args):     
        self.chem_formula = args['MolecularFormula']
        self.mol_weight = args['MolecularWeight']
        self.id = args['CID']

    def _init_custom(self, args):     
        pass

    def _save_image(path='./molecules-db/mol-images'):
        pass


class MoleculeDb:

    def __init__(self, dbname):
        self.db = shelve.open(dbname)
        self.molecules = {}

    def load_all(self):
        for mol_name in self.db.keys():
            attr_dict = self.db[mol_name]
            attr_dict['name'] = mol_name
            molecule = Molecule(from_db=True, attr_dict=attr_dict)
            self.molecules[mol_name] = molecule
            #self.list_ctrl.add_molecule(molecule)
            print "Added " + molecule.name

    # TODO: Overload []
    def get_molecule(self, mol_name):
        try:
            return self.molecules[mol_name]
        except :
            print "Molecule " + mol_name + " not found!"


    def add_molecule(self, molecule):
        d = molecule.__dict__
        # Save every attribute except the image. It can be get by a
        # predefined path.
        name = molecule.name.encode('ascii', 'ignore')
        attr_dict = dict((i, d[i]) for i in d if i != 'image')
        if self.db.has_key(name):
            raise Exception("Molecule already in the database.")
        else:
            self.db[name] = attr_dict
            self.db.sync()

    def del_molecule(self, mol_name):
        del self.db[mol_name.encode('ascii', 'ignore')]
        self.db.sync()
