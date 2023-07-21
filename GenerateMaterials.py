######################################################
##
##  Generate materials from shop_materialpath v1.11
##  Trond Hille 2023
##
##  FBX and external models often come in with material paths set, but recreating the materials is a manual process.
##  This scrips finds all unique material names create and reassign a new Houdini material for each one.
##
##  Currently defaults to creating a redshift vopnet (material builder) but can easily be changed to another type.
##
##  Changelog:
##  v1.0    initial release. Redshift Materials Only
##  v1.1    added support and choice for different render engines/material types 
##                Added support for Karma MaterialX and ease to add more later
##  v1.11   Enabled the output material flag to be enabled by default on new MtlX subnets
##
##
##
#####################################################


import hou
import re
from enum import Enum

materials = [] 


class ExtendedEnum(Enum):

    @classmethod
    def list(cls):
        return list(map(lambda c: c.name, cls))


class MatType(ExtendedEnum):
    Redshift = "redshift_vopnet"
    KarmaMtlX = "karmamtlx_vopnet"
    
    
    
# SHOW MAIN DIALOG    
def showDialog(node):
    # List of options for the dropdown list
    dropdown_options = MatType.list()

    
    # Create the custom dialog with the dropdown menu
    result = hou.ui.selectFromList(dropdown_options, exclusive=True, title='Select Material Type', message='Select Material Type', clear_on_cancel=True)
    if len(result) != 0:
        matclass = getattr(MatType, dropdown_options[result[0]])
        #print(matclass)
        GenerateMaterialsFromGeo(node, matclass)

        
        
        

def CreateKarmaMtlx(matnet, matname):
    matvopnet = matnet.createNode('subnet', matname)
    mtlx = matvopnet.createNode('mtlxstandard_surface', matname)
    
    # CLEANUP Default nodes
    tempPath = matvopnet.path() + '/suboutput1'
    defOutput = hou.node(tempPath)
    tempPath = matvopnet.path() + '/subinput1'
    defInput = hou.node(tempPath)
    defOutput.destroy()
    defInput.destroy()

    surfaceoutput = matvopnet.createNode('subnetconnector', 'surface_output')
        
    surfaceoutput.parm('connectorkind').set(1)
    surfaceoutput.parm('parmname').set('surface')
    surfaceoutput.parm('parmlabel').set('Surface')
    surfaceoutput.parm('parmtype').set(24) #Set to surface type
    surfaceoutput.parm('connectorkind').eval()
    surfaceoutput.setInput(0, mtlx)
    
    pos = mtlx.position()
    pos += hou.Vector2((4,0))
    surfaceoutput.setPosition(pos)
    pos += hou.Vector2((0,-4))
    
    displacementoutput = matvopnet.createNode('subnetconnector', 'displacement')
    displacementoutput.parm('connectorkind').set(1)
    displacementoutput.parm('parmname').set('displacement')
    displacementoutput.parm('parmlabel').set('Displacement')
    displacementoutput.parm('parmtype').set(25) #Set to displacement type
    displacementoutput.parm('connectorkind').eval()
    displacementoutput.setPosition(pos)
        
    matvopnet.setMaterialFlag(1)
    
    return matvopnet
    

def CreateMaterial(matnet, matname, mattype=MatType.Redshift, skipexisting='True'):
    #Creates a new material at the given matnet. Defaults to Redshift Material Builder type.
    
    if skipexisting:
        matpath = matnet.path() + '/' + matname
        if hou.node(matpath) is not None:
            print(matname + ' already exists. Skipping Creation..')
            return hou.node(matpath)
    newmat = None
    if mattype is MatType.KarmaMtlX:
        newmat = CreateKarmaMtlx(matnet, matname)
    else:
        newmat = matnet.createNode(mattype.value, matname)
        
    return newmat

def remove_illegal_characters(string):
    # Define the pattern of illegal characters using regular expressions
    pattern = r'[#^!@()*&%$]'

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
        


def GenerateMaterialsFromGeo(node, mattype=MatType.Redshift):
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
        
        newmat = CreateMaterial(matnet, matname, mattype)
            
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
    showDialog(node)
