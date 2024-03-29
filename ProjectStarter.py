import hou, os, json
import sys
import re

try:
    import PySide2_External #hacky internal fix for missing PySide QtUiUTils in Houdini 
except:
    print('Hack fix: PySide2_External not found')
    
from PySide2 import QtCore, QtUiTools, QtWidgets, QtGui 
from PySide2.QtUiTools import QUiLoader
import tkinter as tk
from tkinter import filedialog
from tronoutils import main as utils

# default variables
_uiFile = r'Z:/_Assets/3D/0_SharedScripts/Houdini/py_scripts/projectstarter/ProjectStart.ui'
_configfile = r'Z:/_Assets/3D/0_SharedScripts/Houdini/py_scripts/projectstarter/FolderStructure.json'
_lastProjectFile = os.path.join(os.path.expanduser("~"), '.tronotools', 'lastprojects.json')
_maxProjectsToSave = 10
_prjRegEx = r"(?P<prjid>\d\d-\w{3,}-.*-\d{4,})(-|_)(?P<prjname>.*)"


def loadjson(file):
    #Create lastproject json file if not exists
    if not os.path.isfile(file):
        dir = os.path.dirname(os.path.abspath(file))
        if not os.path.exists(dir):
            os.mkdir(dir)
        with open(file, 'w') as file:
            print('Created user config file: ' + str(file))

    try:
        with open(file, 'r') as f:
            #print('loading json')
            data = json.load(f)
    except:
        #print('Some error loading json file: ' + file)
        data = []
        
    return data
    
        
def savejson(file, data):
    with open(file, 'w') as file:
        json.dump(data, file, indent=4)
        

class ProjectStarter(QtWidgets.QWidget):
    data = None
    _projectDir = None
    _cacheDir = None
    _assetDir = None
    _hdaDir = None
    _hdaGlobalDir = None
    _scriptDir = None
    _jobVariable = None
    _qBoxActivated = 0
    _lastProjectsList = []
    # FPS Controls to be implemented
    _FPS = hou.fps()

    def __init__(self):
        super(ProjectStarter, self).__init__()
        if self.startupChecks() == -1:
            return
            
        self.ui = QUiLoader().load(_uiFile, parentWidget=self)
        self.setParent(hou.ui.mainQtWindow(), QtCore.Qt.Window)

        self.data = loadjson(_configfile)
        self._projectDir = self.data['projectroot']
        self._cacheDir = self.data['cachedir']
        self._assetDir = self.data['assetdir']
        self._hdaDir = self.data['hdadir']
        self._scriptDir = self.data['scriptdir']
        self._hdaGlobalDir = self.data['hdaglobaldir']

        # initialize ui
        self.ui.linePrjId.textChanged.connect(self.projectNameChanged)
        self.ui.linePrjName.textChanged.connect(self.projectNameChanged)
        self.ui.linePrjDir.textChanged.connect(self.projectNameChanged)
        self.ui.lastProjects.currentIndexChanged.connect(self.lastProjectChanged)
             

        if hou.hscriptExpression("isvariable(PRJ)") == 1:
            prjName = hou.hscriptExpression("$PRJ")
        else:
            prjName = ""
    
        
        # check if a job varaible is already set and use it to fill the UI      
        if hou.hscriptExpression("isvariable(JOB)") == 1:
            jobVar = hou.hscriptExpression("$JOB")
            jobArray = jobVar.split("/")
            prjName = jobArray[len(jobArray)-1]
            head, tail = os.path.split(jobVar)
            projectDir = head
        if hou.hscriptExpression("isvariable(PRJID)") == 1 and hou.hscriptExpression("isvariable(PRJNAME)") == 1:
            id = hou.hscriptExpression("$PRJID")
            prjName = hou.hscriptExpression("$PRJNAME") 
            if id != 'replaceme':
                self.ui.linePrjId.setText(id)
                
        #Append to and adjust table
        self.ui.tableVariables.setColumnWidth(1, 500)
        rowPosition = self.ui.tableVariables.rowCount()
        self.ui.tableVariables.insertRow(rowPosition)
        self.ui.tableVariables.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem('HDA'))
        rowPosition += 1
        self.ui.tableVariables.insertRow(rowPosition)
        self.ui.tableVariables.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem('SCRIPTS'))
        
        # Fill UI input fields
        self.ui.linePrjName.setText(prjName)
        self.ui.linePrjDir.setText(projectDir)
        self.updateVariableTable()
        self.ui.linePrjName.setText(prjName)
                
        # Setup "Create Project" button
        self.ui.btnCreateProject.clicked.connect(self.createProject)
        self.ui.btnBrowse.clicked.connect(self.browseDirs)
        self.ui.btnSetupVariables.clicked.connect(self.setupVariables)
    
        #Load last projects list
        self.loadPrjList()

    
    #Create Project functions
    def startupChecks(self):
        if not os.path.exists(_uiFile):
            print('UI File does not exist:\n' + _uiFile)
            return -1
        if not os.path.exists(_configfile):
            print('Config File does not exist:\n' + _configfile)
            return -1
            
        return 1
    
    def createProject(self):
        prjId = self.ui.linePrjId.text()
        prjName = self.ui.linePrjName.text()
        dir = self.ui.linePrjDir.text()
        
        if prjId != '':
            prjName = prjId + '-' + prjName
        
        dir = utils.fixpath(dir)
        
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
        data = loadjson(_configfile)
        
        #create the array of folders
        for item in data['folders']:
            folders.append(item)            
        
        #create the folders
        winpath = utils.fixpath(prjPath, new_sep='\\')
        print ('Creating folder structure at ' + winpath)

        for folder in folders:
            os.makedirs(prjPath + folder)
            #print prjPath + folder
        #setup the variables
        self.setupVariables()
        
        self._lastProjectsList = loadjson(_lastProjectFile)
        
        #Save project to last projects list
        prj_data = {
            
                'prjId': self.ui.linePrjId.text(),
                'prjName': self.ui.linePrjName.text(),
                'prjPath': dir,
                'outPath': self.ui.tableVariables.item(2,1).text(),
                'cachePath': self.ui.tableVariables.item(3,1).text(),
                'hdaPath': self.ui.tableVariables.item(4,1).text(),
                'scriptPath': self.ui.tableVariables.item(5,1).text(),
            }
        prj_name = prj_data['prjId'] + '-' + prj_data['prjName']
        newprj = []
        newprj.append(prj_name)
        newprj.append(prj_data)
        self._lastProjectsList.insert(0, newprj)
        
        #Save project list
        savejson(_lastProjectFile, self._lastProjectsList[:_maxProjectsToSave])
        #Refresh dropdown list
        self.loadPrjList()
        
        print ('done!')
        
        if hou.ui.displayMessage('Project created!', buttons=('OK', 'Open in Explorer')) == 1:
            os.startfile(winpath)
        
        
    #keep things updated as project name is changed
    def projectNameChanged(self):
        dir = self.ui.linePrjDir.text()
        prjId = self.ui.linePrjId.text()
        prjName = self.ui.linePrjName.text()
        
        # Remove spaces and backslashes and update UI
        dir = utils.fixpath(dir)
        prjId = utils.fixpath(prjId)
        prjName = utils.fixpath(prjName)
        
        

        self.ui.linePrjDir.setText(dir)
        self.ui.linePrjId.setText(prjId)
        self.ui.linePrjName.setText(prjName)
        
        if prjId != '':
            prjName = prjId + '-' + prjName
        
        _jobVariable = dir + "/" + prjName
        self.ui.tableVariables.setItem(0,1, QtWidgets.QTableWidgetItem(_jobVariable))
        self.ui.tableVariables.setItem(1,1, QtWidgets.QTableWidgetItem(prjName))
        self.ui.tableVariables.setItem(2,1, QtWidgets.QTableWidgetItem(dir + "/" + prjName + "/_Frames/0_RAW/"))
        self.ui.tableVariables.setItem(3,1, QtWidgets.QTableWidgetItem(self._cacheDir + "/" + prjName + "/"))
        self.ui.tableVariables.setItem(4,1, QtWidgets.QTableWidgetItem(dir + "/" + prjName + "/" + self._hdaDir))
        self.ui.tableVariables.setItem(5,1, QtWidgets.QTableWidgetItem(dir + "/" + prjName + "/" + self._scriptDir))
        
        
        self.checkVariables()
        
    #browse directories button
    def browseDirs(self):
        #print 'browse dirs pressed'
        root = tk.Tk()
        root.withdraw()

        file_path = filedialog.askdirectory()
        
        #REGEX path and break down according to set regex variable
        path = os.path.normpath(file_path)
        last_directory = os.path.basename(path)
        directories_up_to_last = path.replace(last_directory, '', 1)
        #patharray = [directories_up_to_last, last_directory]
        
        match = re.match(_prjRegEx, last_directory)
        if match:
            self.ui.linePrjDir.setText(directories_up_to_last)
            self.ui.linePrjId.setText(match.group('prjid'))
            self.ui.linePrjName.setText(match.group('prjname'))
        else:
            self.ui.linePrjDir.setText(directories_up_to_last)
            self.ui.linePrjId.setText('')
            self.ui.linePrjName.setText(last_directory)
        
    def updateVariableTable(self):
        #print self.ui.tableVariables.item(0,0).text()
        jobVar = hou.hscriptExpression('$JOB')
        self.ui.tableVariables.setItem(0,1, QtWidgets.QTableWidgetItem(jobVar))
        
    def setupVariables(self):
        name = self.ui.linePrjName.text()
        id = self.ui.linePrjId.text()
        jobVarUI = self.ui.tableVariables.item(0,1).text()
        prjVarUI = self.ui.tableVariables.item(1,1).text()
        outVarUI = self.ui.tableVariables.item(2,1).text()
        cacheVarUI = self.ui.tableVariables.item(3,1).text()
        hdaVarUI = self.ui.tableVariables.item(4,1).text()
        scriptVarUI = self.ui.tableVariables.item(5,1).text()
        
        #CREATE THE VARIABLES FIRST TO BE ABLE TO WRITE THEM AND SEE THEM IN THE VARIABLE PANEL
        hou.hscript('setenv JOB = replaceme')
        hou.hscript('setenv PRJID = replaceme')
        hou.hscript('setenv PRJNAME = replaceme')
        hou.hscript('setenv PRJ = replaceme')
        hou.hscript('setenv OUT = replaceme')
        hou.hscript('setenv CACHE = replaceme')
        hou.hscript('setenv PRJHDA = replaceme')
        hou.hscript('setenv PRJSCRIPT = replaceme')
            
        hou.putenv('JOB', jobVarUI)
        hou.putenv('PRJID', id)
        hou.putenv('PRJNAME', name)
        hou.putenv('PRJ', prjVarUI)
        hou.putenv('OUT', outVarUI)
        hou.putenv('CACHE', cacheVarUI)
        hou.putenv('PRJHDA', hdaVarUI)
        hou.putenv('PRJSCRIPT', scriptVarUI)
        
        # Update houdini internal search paths
        # Append project script directory (TODO: Remove when changing projects)
        sys.path.append(self._scriptDir)
        
        # Build HDA search path
        hda_paths = [
            '$HH/otls',
            hdaVarUI,
            self._hdaGlobalDir,
        ]
        
        hou.putenv('HOUDINI_OTLSCAN_PATH', ';'.join(hda_paths)) 
        
        
        hou.hda.reloadAllFiles()
        
        self._lastProjectsList = loadjson(_lastProjectFile)
        
        #Save project to last projects list
        prj_data = {
            
                'prjId': self.ui.linePrjId.text(),
                'prjName': self.ui.linePrjName.text(),
                'prjPath': self.ui.linePrjDir.text(),
                'outPath': self.ui.tableVariables.item(2,1).text(),
                'cachePath': self.ui.tableVariables.item(3,1).text(),
                'hdaPath': self.ui.tableVariables.item(4,1).text(),
                'scriptPath': self.ui.tableVariables.item(5,1).text(),
            }
        prj_name = prj_data['prjId'] + '-' + prj_data['prjName']
        newprj = []
        newprj.append(prj_name)
        newprj.append(prj_data)
        self._lastProjectsList.insert(0, newprj)
        
        #Save project list
        savejson(_lastProjectFile, self._lastProjectsList[:_maxProjectsToSave])
        #Refresh dropdown list
        self.loadPrjList()
        
               
        
        self.checkVariables()
       
    def loadPrjList(self):
        self._lastProjectsList = loadjson(_lastProjectFile)
        
        names = []
        for item in self._lastProjectsList:
            names.append(item[0])
            
        # Clear old items and add project names to dropbox
        self.ui.lastProjects.clear()
        self.ui.lastProjects.addItems(names)
        
    def lastProjectChanged(self, s):
        #Function triggers as list populates. Avoid running the code on first run
        if self._qBoxActivated == 0:
            self._qBoxActivated = 1
            return
            
        prjdata = self._lastProjectsList[s][1]
        self.ui.linePrjId.setText(prjdata['prjId'])
        self.ui.linePrjName.setText(prjdata['prjName'])
        self.ui.linePrjDir.setText(prjdata['prjPath'])
        self.ui.tableVariables.setItem(0,1, QtWidgets.QTableWidgetItem(prjdata['prjPath'] + '/' + prjdata['prjId'] + '-' + prjdata['prjName']))
        self.ui.tableVariables.setItem(1,1, QtWidgets.QTableWidgetItem(prjdata['prjId'] + '-' + prjdata['prjName']))
        self.ui.tableVariables.setItem(2,1, QtWidgets.QTableWidgetItem(prjdata['outPath']))
        self.ui.tableVariables.setItem(3,1, QtWidgets.QTableWidgetItem(prjdata['cachePath']))
        
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
        if hou.hscriptExpression("isvariable(PRJID)") == 1:
            idVar = hou.hscriptExpression("$PRJID")
        else:
            idVar = ""
        if hou.hscriptExpression("isvariable(PRJNAME)") == 1:
            nameVar = hou.hscriptExpression("$PRJNAME")
        else:
            nameVar = ""
        if hou.hscriptExpression("isvariable(OUT)") == 1:
            outVar = hou.hscriptExpression("$OUT")
        else:
            outVar = ""
        if hou.hscriptExpression("isvariable(CACHE)") == 1:
            cacheVar = hou.hscriptExpression("$CACHE")
        else:
            cacheVar = ""
        if hou.hscriptExpression("isvariable(PRJHDA)") == 1:
            hdaVar = hou.hscriptExpression("$PRJHDA")
        else:
            hdaVar = ""
        if hou.hscriptExpression("isvariable(PRJSCRIPT)") == 1:
            scriptVar = hou.hscriptExpression("$PRJSCRIPT")
        else:
           scriptVar = ""
        
        jobVarUI = self.ui.tableVariables.item(0,1).text()
        prjVarUI = self.ui.tableVariables.item(1,1).text()
        outVarUI = self.ui.tableVariables.item(2,1).text()
        cacheVarUI = self.ui.tableVariables.item(3,1).text()
        hdaVarUI = self.ui.tableVariables.item(4,1).text()
        scriptVarUI = self.ui.tableVariables.item(5,1).text()
        
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
            
        if hdaVar == hdaVarUI:        
            self.ui.tableVariables.item(4,1).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.ui.tableVariables.item(4,1).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))
            
        if scriptVar == scriptVarUI:        
            self.ui.tableVariables.item(5,1).setForeground(QtGui.QBrush(QtGui.QColor(0, 255, 0)))
        else:
            self.ui.tableVariables.item(5,1).setForeground(QtGui.QBrush(QtGui.QColor(255, 0, 0)))

win = ProjectStarter()
win.show()
