import hou, os, json
from PySide2 import QtCore, QtUiTools, QtWidgets, QtGui
import tkinter as tk
from tkinter import filedialog

#default variables
_projectDir = 'S:/Projects/2021/'
_cacheDir = 'S:/Sim/'
_uiFile = 'S:/Assets/_Tronotools/Houdini/ParticleFX-PM/ProjectStart.ui'
_folderStructure = 'S:/Assets/_Tronotools/Houdini/ParticleFX-PM/FolderStructure.json'
_jobVariable = ""

class ProjectStarter(QtWidgets.QWidget):
    def __init__(self):
        super(ProjectStarter,self).__init__()
        self.ui = QtUiTools.QUiLoader().load(_uiFile, parentWidget=self)
        self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)
        
        # initialize ui
        self.ui.linePrjName.textChanged.connect(self.projectNameChanged)
        self.ui.linePrjDir.textChanged.connect(self.projectNameChanged)
        
        
        
         
        if hou.hscriptExpression("isvariable(PRJ)") == 1:
            prjVar = hou.hscriptExpression("$PRJ")
        else:
            prjVar = ""
        
        
        # check if a job varaible is already set and use it to fill the UI
        if hou.hscriptExpression("isvariable(JOB)") == 1:
            jobVar = hou.hscriptExpression("$JOB")
            jobArray = jobVar.split("/")
            prjVar = jobArray[len(jobArray)-1]
            head, tail = os.path.split(jobVar)
            _projectDir = head


        
        # Fill UI input fields
        self.ui.linePrjDir.setText(_projectDir)
        self.updateVariableTable()
        self.ui.linePrjName.setText(prjVar)
                
        # Setup "Create Project" button
        self.ui.btnCreateProject.clicked.connect(self.createProject)
        self.ui.btnBrowse.clicked.connect(self.browseDirs)
        self.ui.btnSetupVariables.clicked.connect(self.setupVariables)
    
        
        
    #Create Project functions
    def createProject(self):
        prjName = self.ui.linePrjName.text()
        dir = self.ui.linePrjDir.text()
        if len(prjName) < 1:
            hou.ui.displayMessage('Please enter a project name!')
            return
         
        #create full path to project directory
        prjPath = dir + "/" + prjName

        if os.path.exists(prjPath):
            hou.ui.displayMessage('Project Directory already exists!')
            return
        
        folders = []
        
        #load the json with folder structure
        with open(_folderStructure) as f:
            data = json.load(f)
        
        #create the array of folders
        for item in data['folders']:
            folders.append(item)            
        
        #create the folders
        print 'Creating folder structure at ' + prjPath

        for folder in folders:
            os.makedirs(prjPath + folder)
            #print prjPath + folder
        #setup the variables
        self.setupVariables()
        print 'done!'
        
    #keep things updated as project name is changed
    def projectNameChanged(self):
        dir = self.ui.linePrjDir.text()
        prjName = self.ui.linePrjName.text()
        _jobVariable = dir + "/" + prjName
        self.ui.tableVariables.setItem(0,1, QtWidgets.QTableWidgetItem(_jobVariable))
        self.ui.tableVariables.setItem(1,1, QtWidgets.QTableWidgetItem(prjName))
        self.ui.tableVariables.setItem(2,1, QtWidgets.QTableWidgetItem(dir + "/" + prjName + "/_Frames/0_RAW/"))
        self.ui.tableVariables.setItem(3,1, QtWidgets.QTableWidgetItem(_cacheDir + prjName + "/"))
        
        
        self.checkVariables()
        
    #browse directories button
    def browseDirs(self):
        #print 'browse dirs pressed'
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askdirectory()
        self.ui.linePrjDir.setText(file_path)
        
    def updateVariableTable(self):
        #print self.ui.tableVariables.item(0,0).text()
        jobVar = hou.hscriptExpression("$JOB")
        self.ui.tableVariables.setItem(0,1, QtWidgets.QTableWidgetItem(jobVar))
        
    def setupVariables(self):
        jobVarUI = self.ui.tableVariables.item(0,1).text()
        prjVarUI = self.ui.tableVariables.item(1,1).text()
        outVarUI = self.ui.tableVariables.item(2,1).text()
        cacheVarUI = self.ui.tableVariables.item(3,1).text()
        
        #CREATE THE VARIABLES FIRST TO BE ABLE TO WRITE THEM AND SEE THEM IN THE VARIABLE PANEL
        hou.hscript("setenv JOB = replaceme")
        hou.hscript("setenv PRJ = replaceme")
        hou.hscript("setenv OUT = replaceme")
        hou.hscript("setenv CACHE = replaceme")
            
        hou.putenv('JOB', jobVarUI)
        hou.putenv('PRJ', prjVarUI)
        hou.putenv('OUT', outVarUI)
        hou.putenv('CACHE', cacheVarUI)
        self.checkVariables()
        
    
    def checkVariables(self):
        #Have to check if variables exists, to avoid undefined error
        if hou.hscriptExpression("isvariable(JOB)") == 1:
            jobVar = hou.hscriptExpression("$JOB")
        else:
            jobVar = ""
        if hou.hscriptExpression("isvariable(PRJ)") == 1:
            prjVar = hou.hscriptExpression("$PRJ")
        else:
            prjVar = ""
        if hou.hscriptExpression("isvariable(OUT)") == 1:
            outVar = hou.hscriptExpression("$OUT")
        else:
            outVar = ""
        if hou.hscriptExpression("isvariable(CACHE)") == 1:
            cacheVar = hou.hscriptExpression("$CACHE")
        else:
            cacheVar = ""
        jobVarUI = self.ui.tableVariables.item(0,1).text()
        prjVarUI = self.ui.tableVariables.item(1,1).text()
        outVarUI = self.ui.tableVariables.item(2,1).text()
        cacheVarUI = self.ui.tableVariables.item(3,1).text()
        
        if jobVar == jobVarUI:        
            self.ui.tableVariables.item(0,1).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.ui.tableVariables.item(0,1).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            
        if prjVar == prjVarUI:        
            self.ui.tableVariables.item(1,1).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.ui.tableVariables.item(1,1).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            
        if outVar == outVarUI:        
            self.ui.tableVariables.item(2,1).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.ui.tableVariables.item(2,1).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            
        if cacheVar == cacheVarUI:        
            self.ui.tableVariables.item(3,1).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.ui.tableVariables.item(3,1).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

win = ProjectStarter()
win.show()
