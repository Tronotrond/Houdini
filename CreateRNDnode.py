import hou

acceptedNodeTypes = ('null', 'output')
removePrefixes = ('ASSET_', 'GEO_', 'FX_')

nodes = hou.selectedNodes()
node = nodes[0]

def RemPrefix(text, prefixes):
    for pf in prefixes:
        if text.startswith(pf):
            return text[len(pf):]
    
    return text


def GetNodeByDialog():
    n = hou.ui.selectNode(title='Select Output or Null', node_type_filter=hou.nodeTypeFilter.Sop)
    node = hou.node(n)
    if node is None:
        return None
    if node.type() in acceptedNodeTypes:
        return node
        
    return None

if len(nodes) != 1:
    node = GetNodeByDialog()
else:
    t = nodes[0].type()
    if t.name() not in acceptedNodeTypes:
        node = GetNodeByDialog() 

        
if node is not None:
    root = node.parent()
    name = RemPrefix(root.name(), removePrefixes)
    name = 'RND_' + name
    
    root = root.parent() # Get to base level
    rnd = root.createNode('geo', name)
    rnd.setColor(hou.Color(1.0, 0.0, 0.0))
    
    om = rnd.createNode('object_merge')
    parm = om.parm('objpath1')
    parm.set(node.path())
else:
    hou.ui.displayMessage('No valid Output or NULL node selected!')
    
