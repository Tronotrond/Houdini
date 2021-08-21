import hou
import os

"""
TODO:
- UI and preferences
    - Set destination drive/folder
- Grab cached sequences
- Find File Caches and disable nodes above
    - Store in array and restore to previous state after submission
- Update paths to destination
- Copy files
- Create log file
- Export job / submit to Deadline

DONE:
- Get reference files
- Expand variables to full paths
- Filter duplicates
- Filter out ROPs and unnecessary files 

"""

frameRange = [560, 600]
# SETTINGS: ignore bypassed sops, ignore proxies, ignore non-displayed, enable file filtering, filter extension list
settings = [1,1,1,0,""]


toCopy = []
toCopyMisc = [] # for non-HIP/JOB files to sort out



def CollectSceneAssets(settings):
    IGNORE_BYPASSED = settings[0]
    IGNORE_PROXY = settings[1]
    IGNORE_NONDISPLAY = settings[2]
    FILTER_FILETYPES = settings[3]
    FILETYPES = settings[4]
    
    SceneAssets = []

    #Set to frame 0 and update to manual
    hou.setUpdateMode(hou.updateMode.Manual)        
    hou.setFrame(hou.playbar.playbackRange()[0])    
    #hou.hipFile.save()
    
    #collect all file references
    refs = hou.fileReferences():  
    
    # Find file caches and remove file references above in the same network   
    # We'll end up looping through twice for this
    for file_parm, file in refs:
        #IF file parameter is None, it's an HDA or something we shouldn't need to include
        if file_parm is None: 
            continue;
        if isinstance(file_parm.node(), hou.SopNode):
            if file_parm.name() == "file":
                p = file_parm.path().split("/")
                #SKIP IF WRITE OUT NODE - TWO FILES NODES EXISTS IN EACH FILE CACHE
                if "file_mode" in p:
                    continue;
                if file_parm
        
    
    string = "----\n\n"
    for file_parm, file in refs:
        #IF file parameter is None, it's an HDA or something we do not need to include
        if file_parm is None: 
            continue;
        
        #Remove ROP file references
        if type(file_parm.node()) == hou.RopNode:        
            continue;
        
        # Finding and ignoring referenced SOPs and not displayed
        # Hacky way, iterate 10 times; Returns the referenced parameter. If no parameter is referenced, returns this parameter.
        for i in xrange(10): 
            file_parm = file_parm.getReferencedParm()
            
        # Check and skip if node is disabled
        if IGNORE_BYPASSED and file_parm.isDisabled():
            continue;
        #Check if bypassed
        if IGNORE_BYPASSED and file_parm.node().isGenericFlagSet(hou.nodeFlag.Bypass):
            continue;
            
        # Testing for display flag. 
        # DOES NOT WORK because of assets objs are hidden
        """
        disp = True
        if isinstance(file_parm.node(), hou.SopNode):
            top = getObjParent(file_parm.node())
            if top:
                disp = top.isGenericFlagSet(hou.nodeFlag.Display)
        if IGNORE_NONDISPLAY and not disp:
            continue;
        """
        
        # GET FILE CACHE SOPS AND FILE RANGES
        if isinstance(file_parm.node(), hou.SopNode):
            if file_parm.name() == "file":
                p = file_parm.path().split("/")
                #SKIP IF WRITE OUT NODE - TWO FILES NODES EXISTS IN EACH FILE CACHE
                if "file_mode" in p:
                    continue;
                startFr = file_parm.node().parm("f1").eval()
                endFr = file_parm.node().parm("f2").eval()
                # Adjust frame ranges from which is smallest. Render or file cache range.
                if frameRange[0] > startFr:
                    startFr = frameRange[0]
                if frameRange[1] < endFr:
                    endFr = frameRange[1]
                files = CollectFrameRange(file_parm, startFr, endFr)
                for file in files:
                    SceneAssets.append(file)
                    continue;
        
        
        #Evaluate variables and expressions to the complete path
        expandedFile = file_parm.eval()
            
        #string += str(file_parm)
        #string += " :: " + expandedFile + "\n"
        
        SceneAssets.append(expandedFile)
        
    
    #Filter list and delete duplicates
    FilteredAssets = []
    for i in SceneAssets:
        if i not in FilteredAssets:
            FilteredAssets.append(i)
    
    return FilteredAssets

def getObjParent(node):
    if isinstance(node, hou.ObjNode):
        return node
    parent = node.parent()
    if not parent:
        return None
    return getObjParent(parent)
    

def CollectFrameRange(fileparm, startFr, endFr):
    files = []
    for i in range(int(startFr), int(endFr)):
        filename = fileparm.evalAtFrame(i)
        files.append(filename)
        
    return files
    
    
AssetsToCopy = CollectSceneAssets(settings)
print "\n\nASSETS TO COPY:\n\n"
for asset in AssetsToCopy:
    print asset


    
