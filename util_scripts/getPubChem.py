import pubchempy as pcp
import json
#hex = pcp.request(11006, namespace='cid', domain='compound', operation='classification', output='JSON')
#text = json.loads(hex.read())
#print text["Hierarchies"]["Hierarchy"][1]["Node"][1]["Information"]["Name"]
 #print "AKI"
hex = pcp.get("meth", namespace='name', domain='compound', operation='cids', output='JSON', name_type='word', list_return='listkey')
hex = json.loads(hex)
listkey_name = hex['IdentifierList']['ListKey']
#print "AKI"
#hex = pcp.get(listkey_name, namespace='listkey', domain='compound', operation='cids', output='JSON', listkey_count=20)
hex = pcp.get_properties('MolecularWeight,MolecularFormula,IUPACName', listkey_name, namespace='listkey', listkey_count=200)
namelist = [c["IUPACName"] for c in hex if c["IUPACName"].startswith('meth')]
namelist.sort()
print namelist
#hex = json.loads(hex)
#compounds = [pcp.Compound(r) for r in hex['PC_Compounds']] if hex else []
#print len(compounds)
#print "AKI"
#print hex
#hex = pcp.get(297, namespace='cid', domain='compound', output='PNG')
#hex = pcp.get_cids('meth', 'name', name_type='word', listkey_start=0,listkey_count=2)
#print hex.molecular_formula
#print hex.to_dict(properties=["atoms","bonds"])
