######################################################
##
##  Generate materials from shop_materialpath v1.0
##  Trond Hille 2023
##
##  FBX and external models often come in with material paths set, but recreating the materials is a manual process.
##  This scrips finds all unique material names create and reassign a new Houdini material for each one.
##
##  Currently defaults to creating a redshift vopnet (material builder) but can easily be changed to another type.
##
##
#####################################################


import hou
import re

materials = [] 

def CreateMaterial(matnet, matname, mattype='redshift_vopnet', skipexisting='True'):
    #Creates a new material at the given matnet. Defaults to Redshift Material Builder type.
    
    if skipexisting:
        matpath = matnet.path() + '/' + matname
        if hou.node(matpath) is not None:
            print(matname + ' already exists. Skipping Creation..')
            return hou.node(matpath)
    
    newmat = matnet.createNode(mattype, matname)
    return newmat

def remove_illegal_characters(string):
    # Define the pattern of illegal characters using regular expressions
    pattern = r'[#^!@]'

    cleaned_string = re.sub(pattern, '', string)
    cleaned_string = re.sub(' ', '_', cleaned_string)
    
    return cleaned_string

    
def CollectMaterialNames(node):
    #Loops through all primitives and collects all unquie materials.
    matlib = []
    geo = node.geometry()
    for prim in geo.prims():
        matname = prim.attribValue('shop_materialpath')
        if matname not in matlib:
            matlib.append(matname)
    return matlib
        


def GenerateMaterialsFromGeo(node):
    # Main script execution
    
    root = node.parent()
    materials = CollectMaterialNames(node)
    
    print('Found ' + str(len(materials)) + ' unique materials..')
    if len(materials) < 1:
        return

    # Create Matnet
    matpath = root.path() + '/materials'
    matnet = hou.node(matpath)
    if matnet == None:
        matnet = root.createNode('matnet', 'materials')
    
    newmats = []
    for mat in materials:
        matname = mat.rsplit('/', 1)[-1]
        matname = remove_illegal_characters(matname)
        
        newmat = CreateMaterial(matnet, matname)
            
        newmat.moveToGoodPosition()
        newmats.append(newmat)
     
    
    # Create Materials SOP
    '''
    # Should perhaps always create a new one, just in case...
    matsoppath = root.path() + 'update_material_assignments'
    matsop = hou.node(matsoppath)
    if matsop == None:
        matsop = root.createNode('material', 'update_material_assignments')
        matsop.setInput(0, node)
    '''
    matsop = root.createNode('material', 'update_material_assignments')
    matsop.setInput(0, node)
        
    pos = node.position()
    pos[1] -= 2
    matsop.setPosition(pos)
    matsop.moveToGoodPosition()
    
    # Update material SOP
    nummats = len(newmats)
    matsop.parm('num_materials').set(nummats)
    matsop.parm('num_materials').eval()
    
    for i in range(nummats):
        group = 'group' + str(i+1)
        path = 'shop_materialpath' + str(i+1)
        
        groupstring = '@shop_materialpath="' + materials[i] + '"'
        matstring = '../' + matnet.name() + '/' + newmats[i].name()

        matsop.parm(group).set(groupstring)
        matsop.parm(path).set(matstring)
    
      
    
# Run the script
if len(hou.selectedNodes()) != 1:
    print('Select one SOP node with shop_materialpath set')
else:
    node = hou.selectedNodes()[0]
    GenerateMaterialsFromGeo(node)
