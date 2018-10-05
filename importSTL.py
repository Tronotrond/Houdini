# Batch import all STL files. Change folder location below and run

import glob, os
os.chdir("C:/MySTL-Directory/")

obj = hou.node("..")

if obj.node("file1") == None:
    for filename in glob.glob("*.stl"):
        file = obj.createNode("file")
        file.setParms({"file": filename})
else:
    print "nothing to load here" 
	
	
