from __future__ import division
from ij import IJ, ImagePlus, ImageStack, CompositeImage, ImageListener
from ij.io import DirectoryChooser
from ij.gui import WaitForUserDialog, GenericDialog
import os, sys
import random
import math
from loci.plugins import BF
from loci.plugins.in import ImporterOptions
from ij.gui import ImageWindow, ImageCanvas, Roi, PointRoi, Line, RoiListener
from ij.plugin.frame import RoiManager
from loci.plugins.util import LociPrefs
from ij import Prefs
from ij.plugin import ChannelSplitter, ZProjector
from ij.process import ImageStatistics
import math
from java.awt.event import KeyEvent, KeyAdapter, MouseWheelListener, WindowAdapter, ActionListener, MouseAdapter
from java.awt import Color, Insets, Rectangle, GridBagLayout, EventQueue, GridBagConstraints as GBC
from javax.swing import JFrame, ButtonGroup, JPanel, JCheckBox, JLabel, JButton, JTextField, JTextArea, BorderFactory, JOptionPane, JRadioButton, JComboBox
from java.lang import Thread
import csv

# This ensures ROIs appear on all Z-slices by default

Prefs.showAllSliceOnly = False
RoiManager.restoreCentered(False)
Prefs.useNamesAsLabels = False

def dist(point1, point2):
    return ((point2[0]-point1[0])**2 + (point2[1]-point1[1])**2)**0.5


class PointUpdateListener(MouseAdapter):
    def __init__(self, imp, textArea, rm):
        self.imp = imp
        self.canvas = imp.getCanvas()
        self.textArea = textArea
        
        listeners = self.canvas.getMouseListeners()
        for l in listeners:
            if "PointUpdateListener" in str(l):
                self.canvas.removeMouseListener(l)
        self.canvas.addMouseListener(self)

    def update_count(self):
        global cellDict
        global activeCounter
        global cellCoords
        global lineCoords
        global cellNames
        global TNTLabel
        
        roi = self.imp.getRoi()
        labels = [i.getText() for i in cellNames]
        print(labels)
        
        #roi.setPosition(0,0,0)
        
        rm = RoiManager.getRoiManager()
        if not rm:
            rm = RoiManager()

        rois_in_manager = rm.getRoisAsArray()
        index = -1 

        if roi and isinstance(roi, PointRoi):
            
            roi.setShowLabels(True)
            roi_name = "Cells"
            roi.setName(roi_name)

            for i, r in enumerate(rois_in_manager):
                if r.getName() == roi_name:
                    index = i
                    break

            if index != -1:
                rm.setRoi(roi, index) 
            else:
                rm.addRoi(roi)
            
            allPoints = list(zip(roi.getPolygon().xpoints, roi.getPolygon().ypoints))
            allTypes = list(roi.getCounters())
            print(list(zip(roi.getPolygon().xpoints, roi.getPolygon().ypoints, roi.getCounters())))
            
            cellDict = {}
            for i, point in enumerate(allPoints):
                cellDict[point] = [allTypes[i] % 256, str(labels[(allTypes[i] % 256)-1]), False, []]
            
            #lastPoint = list(zip(roi.getPolygon().xpoints, roi.getPolygon().ypoints))[-1]
            #cellDict[lastPoint] = [activeCounter[0], str(activeCounter[2].getText()), False, []]
            n_points = roi.getCount(int(activeCounter[0]))
            #print(n_points)
            
            
            activeCounter[1].setText(str(n_points))

            
        else:
            print("ERROR- NO ROI.")

        types = [roi.getType() for roi in rois_in_manager]
        xs = [list(r.getPolygon().xpoints) for r in rois_in_manager]
        ys = [list(r.getPolygon().ypoints) for r in rois_in_manager]
        
        
        lineCoords = [[list(zip(r.getPolygon().xpoints, r.getPolygon().ypoints)),r.getType()] for r in rois_in_manager]
        
        if (len(lineCoords)>1):
            for i in range(0, len(lineCoords)-1):
                if (lineCoords[i][1]!=5):
                    lineCoords.pop(i)
        else:
            try:
                if(lineCoords[0][1]!=5):
                    lineCoords.pop(0)
            except:
                pass
        for cell in cellDict.keys():
            cellDict[cell][3] = []
        for line in lineCoords:
            line[1] = []
            cellHolder = ()
            for point in line[0]:
                for cell in cellDict.keys():
                    if (dist(cell, point) < 30):
                        #print(point, cell, dist(cell,point))
                        # Add point type if point is <30 from line
                        line[1].append(cellDict[cell][0])
                        # Set point connection to true
                        cellDict[cell][2] = True
                        if(len(line[1])==2):
                            cellDict[cell][3].append(line[1])
                            cellDict[cellHolder][3].append(line[1])
                            print(line[1], "APPENDED TO CELLDICT.")
                            cellHolder = ()
                        elif(len(line[1])==1):
                            cellHolder = cell
                            print(line[1], "NOT APPENDED YET...")
            if len(line[1])<2:
                while len(line[1])<2:
                    line[1].append("ERR")
        print(lineCoords)
        print(cellDict)
        connectedCells = [i[2] for i in list(cellDict.values())].count(True)
        TNTLabel.setText(str(connectedCells))

            




    # FIXED: Ensure this is indented inside the class
    def mousePressed(self, event):
        EventQueue.invokeLater(lambda: self.update_count())
        
    # FIXED: Ensure this is indented inside the class
    def remove(self):
        self.canvas.removeMouseListener(self)
        #print("Listener removed.")

class selectType(ActionListener):
    def __init__(self, stype, textField, cellField, rm,imp):
        self.stype = stype
        self.textField = textField
        self.cellField = cellField
        self.rm = rm
        self.imp = imp

    def actionPerformed(self, event):
        
        rois = self.rm.getRoisAsArray() 
        roiNames = [roi.getName() for roi in rois]
            
        if self.stype > 0:
            if ("Cells") in roiNames:
                currentZ = self.imp.getSlice()
                self.rm.select(roiNames.index("Cells"))
                self.imp.setSlice(currentZ)
            else:
                currentZ = self.imp.getSlice()
                IJ.run("Add to Manager")
                self.imp.setSlice(currentZ)
            self.imp.setSlice(currentZ)
        
            
            
            print(self.stype, " SELECTED")
            IJ.setTool("multipoint")
            IJ.run("Point Tool...", "counter=" + str(self.stype) + " label show size=Large type=Dot stroke=black")
            #self.textField.setText(str(int(self.textField.getText())+1))
            global activeCounter
            activeCounter = [self.stype, self.textField, self.cellField]
        else:
            activeCounter = [self.stype, self.textField, self.cellField]
            IJ.run(self.imp, "Select None", "")
            IJ.setTool("line")
        

class submit(ActionListener):
    def __init__(self, textfield, checkBox, frame):
        self.checkBox = checkBox
        self.textfield = textfield
        self.frame = frame
        self.result = None
        self.ZProj = None

    def actionPerformed(self, event):
        try:
            self.result = self.textfield.getText()
            self.ZProj = self.checkBox.getSelectedItem()
            print("PROJECTION? ",self.ZProj)
            self.frame.dispose()
            return [self.result, self.ZProj]
            
        except Exception as e:
            IJ.log(e, "NOT AN INT")
            self.textfield.setBackground(Color.red)
            return ["",""]

class lutsListen(ActionListener):
    def __init__(self, imp):
        self.imp = imp
    
    def actionPerformed(self, event):
        global fixLUTs
        fixLUTs = []
        # Apply same range to all channels
        for c in range(1, self.imp.getNChannels() + 1):
            self.imp.setC(c)
            fixLUTs.append(self.imp.getChannelLut(c))
            
        IJ.log("Fixed LUTs!");
            




class fixBC(ActionListener):
    def __init__(self, imp):
        self.imp = imp
    
    def actionPerformed(self, event):
        global fixRange
        fixRange = []
        # Apply same range to all channels
        IJ.log("Fixed B&C!")
        
        for c in range(1, self.imp.getNChannels() + 1):
            self.imp.setC(c)
            fixRange.append([self.imp.getDisplayRangeMin(), self.imp.getDisplayRangeMax()])
            IJ.log("Channel "+str(c)+" set to "+str(fixRange[-1]));


class continueProcessing(ActionListener):
    def __init__(self, frame, cont, cellNum, rm, imp, globalCount, analyzedList, files, folder, cellNames, cellDict):
        self.frame = frame
        self.cont = cont
        self.cellNum = cellNum
        self.rm = rm
        self.imp = imp
        self.count = globalCount
        self.analyzed = analyzedList
        self.files = files
        self.folder = folder
        self.cellNames = cellNames
        self.cellDict = cellDict

    
    def actionPerformed(self, event):
        global lineCoords
        global cellDict
        
        self.count = self.count + 1
        self.frame.dispose()
        
        
        # CREATE CELL MATRIX
        
        cellLabels = [i.getText() for i in self.cellNames]
        cellLabels.insert(0, 0)
        
        cellMatrix = [[0 for i in cellLabels] for i in cellLabels]

        for i in range(0, len(cellMatrix)):
            cellMatrix[0][i] = str(cellLabels[i])
            cellMatrix[i][0] = str(cellLabels[i])
        
        connections = [i[1] for i in lineCoords]

        
        for i in connections:
            try:
                cellMatrix[int(i[0])][int(i[1])] += 1
                if (not i[0]==i[1]):
                    cellMatrix[int(i[1])][int(i[0])] += 1
            except:
                pass
        
        for i in range(len(cellMatrix)):
            for j in range(len(cellMatrix[i])):
                cellMatrix[i][j] = str(cellMatrix[i][j])
        
        printMatrix = "\n".join(["\t".join(i) for i in cellMatrix])
        
        # SAVE TO CSV HERE
        #def saveToCSV(directory, current_file, results):
        #Images	Cells (Total)	TNT-Connected Cells	Cells Types	Connected Cell Subtypes	Connection Matrix
        
        connectedCells = [i[2] for i in list(cellDict.values())].count(True)
        print(connectedCells)
        
        cT = [i[1] for i in list(cellDict.values())]

        cellTypes = {}
        connectedTypes = {}
        
        cellLabels.pop(0)
        
        for j in set(cellLabels):
            cellTypes[str(j)] = cT.count(j)
           
        connCells = []

        for cell in list(cellDict.values()):
            if cell[2]:
                connCells.append(cell[1])
        for j in set(cT):
            connectedTypes[str(j)] = connCells.count(j)
        

        #Images,	Cells (Total),	TNT-Connected Cells,	Cells Types	Connected Cell Subtypes	Connection Matrix
        results = [currentFile, len(cellDict.keys()), connectedCells, float(int(connectedCells)/len(cellDict.keys())), cellTypes, connectedTypes, printMatrix, cellDict, lineCoords]
        saveToCSV(self.folder, currentFile, results, self.cellNum)
        
        
        if (self.cont == True):
            self.rm.reset()
            self.imp.close()
            openImage(self.files, self.count, len(self.files), self.cellNum, self.analyzed, self.folder)
        else:
            self.rm.reset()
            self.imp.close()

def openImage(fileList, counter, total, cellTypes, analyzed, folder):
    global cellDict
    cellDict = {}
    proc = processFile(fileList[counter], counter, total, cellTypes, analyzed, fileList, folder)

    analyzed.append(fileList[globalCount])
    return proc

def askCells():
    panel = JPanel()
    panel.setBorder(BorderFactory.createEmptyBorder(10,10,10,10))
    gb = GridBagLayout()
    panel.setLayout(gb)
    gc = GBC()
    
    gc.gridx = 0
    gc.gridy = 0
    gc.anchor = GBC.EAST
    label = JLabel("How many cell types are you counting?")
    gb.setConstraints(label, gc)
    panel.add(label)
    
    gc.gridx = 2
    gc.anchor = GBC.WEST
    textfield = JTextField("1", 10)
    gb.setConstraints(textfield, gc)
    panel.add(textfield)
    textValue = textfield.getText()
    
    gc.gridx = 0
    gc.gridy = 2
    gc.anchor = GBC.EAST
    label = JLabel("Z-Projection?	")
    gb.setConstraints(label, gc)
    panel.add(label)
    
    
    gc.gridx = 2
    gc.gridy = 2
    gc.anchor = GBC.WEST
    checkBox = JComboBox(["None","Average Intensity","Max Intensity","Min Intensity","Sum Slices","Standard Deviation","Median"])
    gb.setConstraints(checkBox, gc)
    panel.add(checkBox)
    #checkboxVal = checkBox.get()
    
    gc.gridy = 4
    button = JButton("Submit")
    gb.setConstraints(button, gc)
    panel.add(button)
    
    
    
    frame = JFrame("Cell type selection", visible = True)
    listener = submit(textfield, checkBox, frame)
    button.addActionListener(listener)
    
    frame.getContentPane().add(panel)  
    frame.pack() # make UI elements render to their preferred dimensions  
    frame.setLocationRelativeTo(None) # center in the screen  
    frame.setVisible(True)
    
    # Wait for user to submit the form
    while listener.result is None:
        Thread.sleep(100)
    
    return [listener.result,listener.ZProj]

def countingUI(cellNum, rm, imp, globCount, analyzedList, files, contFolder):
    global cellNames
    global TNTLabel
    global cellDict
    global lineCoords
    
    panel = JPanel()
    panel.setBorder(BorderFactory.createEmptyBorder(10,10,10,10))
    gb = GridBagLayout()
    panel.setLayout(gb)
    gc = GBC()
    
    gc.gridx = 0 
    gc.gridy = 0
    gc.fill = GBC.HORIZONTAL
    
    group = ButtonGroup()

    
    gc.gridx = 1
    TNT = JLabel("  TNT-connected cells")
    gb.setConstraints(TNT, gc)
    panel.add(TNT)
    
    gc.gridx = 2
    label = "0"
    countField = JTextArea()
    countField.setText(label)
    countField.setEditable(False)
    TNTLabel = countField
    gb.setConstraints(countField, gc)
    panel.add(countField)
    
    gc.gridx = 0
    gc.insets = Insets(2, 0, 0, 0)
    button = JRadioButton("")
    gb.setConstraints(button, gc)
    panel.add(button)
    cellListener = selectType(0, countField, TNT, rm,imp)
    button.addActionListener(cellListener)
    group.add(button)
    

    '''roiListener = TextFieldUpdater(countField)
    Roi.addRoiListener(roiListener)'''
    
    
    gc.gridy = 2
    
    try:
    	if len(cellNames) != 0:
    		currLabels = [i.getText() for i in cellNames]
    		print(currLabels, "CURRLABELS")
    		cellNames = []
    	    
    except Exception as e:
    	print(e)
    	cellNames = []
    	currLabels = [str("Cell type "+str(i+1)) for i in range(int(cellNum))]
    
    for i in range(0, int(cellNum)):
        gc.gridx = 1
        label = "".join(currLabels[i])
        cellField = JTextField(label, 10)
        gb.setConstraints(cellField, gc)
        panel.add(cellField)
        cellNames.append(cellField)
        
        gc.gridx = 2
        label = "0"
        countField = JTextArea()
        countField.setText(label)
        countField.setEditable(False)
        gb.setConstraints(countField, gc)
        panel.add(countField)
        listener = PointUpdateListener(imp, countField, rm)
        
        gc.gridx = 0
        gc.anchor = GBC.EAST
        button = JRadioButton("")
        group.add(button)
        cellListener = selectType(i+1, countField, cellField, rm,imp)
        button.addActionListener(cellListener)
        gb.setConstraints(button, gc)
        panel.add(button)
            
        gc.fill = GBC.HORIZONTAL
        

        
        gc.gridy += 2


                
    frame = JFrame("Measure", visible = True)
    
    gc.anchor = GBC.WEST
    gc.gridy += 2	
    gc.insets = Insets(20, 0, 0, 0)
    gc.gridx = 1
    fixButton = JButton("Fix B&C")
    fixButton.setBackground(Color(3, 111, 252))
    fixButton.foreground = Color.black
    fixListener = fixBC(imp)
    fixButton.addActionListener(fixListener)
    gb.setConstraints(fixButton, gc)
    panel.add(fixButton)
    
    gc.anchor = GBC.WEST	
    gc.insets = Insets(20, 0, 0, 0)
    gc.gridx = 2
    lutsButton = JButton("Fix LUTs")
    lutsButton.setBackground(Color(207, 205, 87))
    lutsButton.foreground = Color.black
    lutsListener = lutsListen(imp)
    lutsButton.addActionListener(lutsListener)
    gb.setConstraints(lutsButton, gc)
    panel.add(lutsButton)
    
    gc.anchor = GBC.WEST
    gc.gridy += 2	
    gc.insets = Insets(20, 0, 0, 0)
    gc.gridx = 1
    contButton = JButton("Continue")
    contButton.setBackground(Color(120, 227, 179))
    contButton.foreground = Color.black
    contListener = continueProcessing(frame, True, cellNum, rm, imp, globCount, analyzedList, files, contFolder, cellNames, cellDict)
    contButton.addActionListener(contListener)
    gb.setConstraints(contButton, gc)
    panel.add(contButton)
    
    gc.gridx = 2
    exitButton = JButton("Exit")
    exitButton.setBackground(Color(245, 154, 180))
    exitButton.foreground = Color.black
    exitListener = continueProcessing(frame, False, cellNum, rm, imp, globCount, analyzedList, files, contFolder, cellNames, cellDict)
    exitButton.addActionListener(exitListener)
    gb.setConstraints(exitButton, gc)
    panel.add(exitButton)
    

    frame.getContentPane().add(panel)  
    frame.pack() # make UI elements render to their preferred dimensions  
    frame.setLocationRelativeTo(None) # center in the screen  
    frame.setVisible(True) 
    

def countingCells(cells, lines):
    #print(cells)
    xylines = []

    # Cycle through lines, keep endpoints
    for points in lines:
        xylines.append([points[0][0], points[0][1]])
        xylines.append([points[1][0], points[1][1]])

    connected = []

    # Identify distances of all points to all line endpoints
    # 30px as max distance from cell mark to line
    print(cells)
    print(xylines)

    for point in cells:
        for coord in xylines:
            dist = math.hypot(point[0] - coord[0], point[1] - coord[1])
            if dist < 30:
                if not point in connected:
                    connected.append(point)

    connectedCells = len(connected)
    return [connectedCells, cells, xylines, connected]

def saveToCSV(directory, current_file, results, numCells):
    #results = [len(cellDict.keys()), connectedCells, cellTypes, connectedTypes, printMatrix, cellDict, lineCoords]
    #saveToCSV(self.folder, currentFile, results
    #Image, Cells (total), TNT-Connected Cells, Cell Types, Connected Cell Subtypes, Connection Matrix, Cell Dict, Line List \n"
    global filei
    
    filepath = str(directory) + "results-" + str(filei) + ".csv"
    with open(filepath, 'a') as file:
        writer = csv.writer(
            file,
            quoting=csv.QUOTE_ALL,
            lineterminator='\n'
        )
        writer.writerow(results)
    
    
    ''''[[cells, cellCoords], TNTinfo, True]
    # [roi.getName(), roi.getLength(), line]
    # Unpack results
    numCells = str(results[0][0])
    print(numCells)
    cellCoords = ";".join([str(i) for i in results[0][1]]).replace(",", " ")
    connectedCells = str(results[0][2][0])
    print(connectedCells)
    lineCoords = ";".join([str(i[2]) for i in results[1]]).replace(",", " ")
    ROIids = ";".join([str(i[0]) for i in results[1]])
    ROIlengths = ";".join([str(i[1]) for i in results[1]])

    filepath = str(directory) + "results.csv"
    with open(filepath, 'a') as file:
        if (len(ROIids.split(";")) - 1) > 0:
            ratio = str(round(float(connectedCells) / float(numCells), 4))
            print("rat", ratio)
        else:
            ratio = "0"

        # Image file, total cells, connected cells, ratio, ROI names, ROI lengths, cell coordinates, line coordinates
        writeline = current_file + ', ' + numCells + ', ' + connectedCells + ', ' + ratio + ', ' + ROIids + ', ' + ROIlengths + ', ' + cellCoords + ', ' + lineCoords + ' \n'
        print(writeline)
        file.write(writeline)'''

# Auto-set brightness (works poorly, lol)
def auto_brightness_relative(imp):
    # Split channels
    channels = ChannelSplitter.split(imp)

    global_min = float("inf")
    global_max = float("-inf")

    # Find global min/max across all channels
    for ch in channels:
        stats = ch.getStatistics()
        global_min = min(global_min, stats.min)
        global_max = max(global_max, stats.max)

    # Apply same range to all channels
    for c in range(1, imp.getNChannels() + 1):
        imp.setC(c)
        imp.setDisplayRange(global_min, global_max)

    imp.updateAndDraw()


def processFile(cfile, globCount, n, cellnum, analyzedList, files, contFolder):
    global currentFile
    global cellCoords
    global lineCoords
    global fixRange
    
    cellCoords = []
    lineCoords = []
    currentFile = cfile
    
    ImageWindow.centerNextImage()
    options = ImporterOptions()
    Prefs.set("roi.manager.associate", False)
    Prefs.showAllPoints = True
    ImageWindow.centerNextImage()
    options.setId(cfile)
    options.setSplitChannels(False)
    options.setVirtual(True)
    options.setColorMode(ImporterOptions.COLOR_MODE_COMPOSITE)
    imps = BF.openImagePlus(options)

    for imp in imps:
        auto_brightness_relative(imp)

        if imp.getNChannels() > 1:
            imp = CompositeImage(imp, CompositeImage.COMPOSITE)

        zProjDict = {"None":None, "Average intensity":"avg", "Max Intensity":"max", "Min Intensity":"min", "Sum Slices":"sum", "Standard Deviation":"sd","Median":"median"}
        zProj = zProjDict[num_cells_res[1]]
        print(zProj, "ZPROJ")
        if (zProj):
            imp = ZProjector.run(imp,zProj)
            
        imp.show()
        imp.setTitle(str(globCount) + " out of " + str(n))
        IJ.run(imp, "Set Label...", " ")
        colors = ['Blue', 'Green', 'Red', 'Magenta', 'Yellow', 'Cyan', 'Fire']
        count = 0
        
        # SET UP CHANNELS AND COLORS
        for c in range(1, imp.getNChannels() + 1):
            count += 1
            label = imp.getProp("Name #" + str(c + 1))
            if not label:
                label = imp.getProp("WaveName" + str(c + 1))
                print(label)

                if not label:
                    #print("No label")
                    label = ""
                    imp.setC(count)
                    IJ.run(imp, colors[count], "")

                if "561" in label.lower():
                    imp.setC(c)
                    IJ.run(imp, "Blue", "")
                    colors.remove("Blue")
                elif "405" in label.lower():
                    imp.setC(c)
                    IJ.run(imp, "Green", "")
                    colors.remove("Green")
                elif "642" in label.lower():
                    imp.setC(c)
                    IJ.run(imp, "Red", "")
                    colors.remove("Red")
                elif ("488") in label.lower():
                    imp.setC(c)
                    IJ.run(imp, "Magenta", "")

            if "dapi" in label.lower():
                imp.setC(c)
                IJ.run(imp, "Blue", "")
            elif "phal" in label.lower():
                imp.setC(c)
                IJ.run(imp, "Green", "")
            elif "gfp" in label.lower():
                imp.setC(c)
                IJ.run(imp, "Green", "")
            elif ("cy5") in label.lower():
                imp.setC(c)
                IJ.run(imp, "Red", "")

            try:
                #print(fixLUTs[c-1], "Current LUT")
                imp.setChannelLut(fixLUTs[c-1], c)
                imp.updateAndDraw()
            except:
                pass

            try:
                imp.setC(c)
                #print(fixRange[c-1], " Fixrange ", c)
                imp.setDisplayRange(fixRange[c-1][0], fixRange[c-1][1])
                imp.updateAndDraw()
            except:
                #print("No set range...")
                pass
                
                

                

            

        try:
            imp.setC(1)
            imp.setDisplayRange(fixRange[0][0], fixRange[0][1])
            imp.updateAndDraw()
        except:
            imp.setC(1)
            pass
        
        rm = RoiManager.getInstance()
        if not rm:
            rm = RoiManager()
        
        countingUI(cellnum, rm, imp, globCount, analyzedList, files, contFolder)
        
        
        rm.setVisible(True)
        rm.runCommand("Show All")
    
    # "Image, Cells (total), Cell subtypes (n), TNT-Connected Cells, Cell Dict, Line List"
    
    # cellConnectionMatrix
    
dc = DirectoryChooser("Choose a folder")
folder = dc.getDirectory()


num_cells_res = askCells()
num_cells = num_cells_res[0]
global zProj
global fixRange
global fixLUTs
global cellNames
global TNTLabel


zProj = num_cells_res[1]


if folder is None:
    error = GenericDialog("No folder selected.")
    error.showDialog()
                
else:
    # FOLDER PICKED
    fileslist = []

    # OBTAIN ALL FILES, SHUFFLED
    for (root, dirs, files) in os.walk(folder):
        for file in files:
            if file.endswith(".nd") or file.endswith(".nd2"):
                fileslist.append(str(root + "/" + file))

    random.shuffle(fileslist)
    
    global filei
    filei = 0

    while True:
        filei += 1  
        filepath = str(folder) + "results-"+str(filei)+".csv"
        print("CHECKING FILE ... ", filepath)
        
        with open(filepath, 'a+') as file:
            
            reader = csv.reader(file, quoting = csv.QUOTE_ALL)
            
            file.seek(0)
            lines = list(reader)
            
            if len(lines) == 0:
                print(" FILEREAD0NO")
                header = "Image, Cells (total), TNT-Connected Cells, % of Total Connected, Cell Types, Connected Cell Subtypes, Connection Matrix, Cell Dict, Line List \n"
                file.write(header)
                print(header)
                imagesAnalyzed = []
                break
            else:
                lines.pop(0)
                fileCellTypes = lines[0][3].count(":")
                if(int(fileCellTypes) == int(num_cells)):

                    imagesAnalyzed = [i[0].split(",")[0] for i in lines]
                    print(filepath, " ANALYSIS FILE")
                    print(imagesAnalyzed, " IMAGES ANALYZED")
                    break
                    

    filesToDo = [i.split("/")[-1] for i in fileslist]
    
    # REMOVE IMAGES ALREADY ANALYZED 
    for i in fileslist:
        if i in imagesAnalyzed:
            fileslist.remove(i)
    
    globalCount = 0
    
    # LOAD FIRST IMAGE
    openImage(fileslist, globalCount, len(fileslist), num_cells, imagesAnalyzed, folder)
    
    

