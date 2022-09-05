import hou

acceptedNodeTypes = ('null', 'output')
removePrefixes = ('ASSET_', 'GEO_', 'FX_', 'ANIM_', 'OUT_', 'RND_')


def RemPrefix(text, prefixes):
    # Remove prefix from given string
    for pf in prefixes:
        if text.startswith(pf):
            return text[len(pf):]
    
    return text
    

def GetNodeByDialog():
    # Opens a dialog box for user to select node
    n = hou.ui.selectNode(title='Select Output or Null', node_type_filter=hou.nodeTypeFilter.Sop)
    node = hou.node(n)
    if node is None:
        return None
    if node.type().name() in acceptedNodeTypes:
        return node
        
    return None

    
def AskForName(initial_name=''):
    input = hou.ui.readInput('Render node name', initial_contents=initial_name, close_choice=1, buttons=('OK', 'Cancel'))
    #print(input)
    if(input == None or input[0] != 0):
        return None
        
    return input[1]
    
    
def CreateRenderNode(node):
            
    root = node.parent()
    name = 'RND_'
    # Get name of root object - used before
    #name = RemPrefix(root.name(), removePrefixes)
    
    # If user selected ouput/null, get name and use this node for object merge
    # if not, create a null and name it correctly
    if node.type().name() in acceptedNodeTypes:
        orgname = node.name()
        name += RemPrefix(node.name(), removePrefixes)
        name = AskForName(name)
        
        # Check if user cancelled input
        if(name == None): 
            return
    else:
        name = AskForName(name)
        # Check if user cancelled input
        if(name == None): 
            return
        
        # Create new NULL
        nullname = 'OUT_' + RemPrefix(name, removePrefixes)
        nullnode = root.createNode('null', node_name=nullname)
        nullnode.setInput(0, node)
        nullnode.moveToGoodPosition()
        node = nullnode
    
    # Create the render GEO node
    root = root.parent() # Get to base level
    rnd = root.createNode('geo', name, force_valid_node_name=1)
    rnd.setColor(hou.Color(1.0, 0.0, 0.0))
    rnd.moveToGoodPosition()
    
    om = rnd.createNode('object_merge')
    parm = om.parm('objpath1')
    parm.set(node.path())

        
nodes = hou.selectedNodes()
if len(nodes) == 1:
    if nodes[0].type().category() == hou.sopNodeTypeCategory():
        CreateRenderNode(nodes[0])
    else:
        print('Tool only work on SOP level nodes')
else:
    print('Select single node...')
