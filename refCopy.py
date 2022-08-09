import hou

# Grab selected nodes and create a referenced copy
for n in hou.selectedNodes():
    newNode = n.parent().createNode(n.type().name(), '{0}_refcopy'.format(n.name()))
    newNode.setPosition(n.position())
    newNode.move((0.5, -0.5))
    newNode.setColor(hou.Color((0.35, 0.4, 0.5)))
    
    # Create source parms
    group = newNode.parmTemplateGroup()
    
    help_text = 'Select parent node for reference'
    
    source = hou.StringParmTemplate('ref_source', 'Reference Source', 1, string_type=hou.stringParmType.NodeReference, help=help_text)
    group.insertBefore((0,), source)
    
    newNode.setParmTemplateGroup(group)
    
    newNode.parm('ref_source').set(n.path())
    
    #Link parms
    for p in newNode.parms():
        #Skip if reference node parm of folders
        if p.name() == 'ref_source':
            continue
        if p.parmTemplate().type() == hou.parmTemplateType.Folder or p.parmTemplate().type() == hou.parmTemplateType.FolderSet:
            continue
            
        #Python
        p.setExpression("hou.node(hou.pwd().evalParm('ref_source')).evalParm('{0}')".format(p.name()), language=hou.exprLanguage.Python)
