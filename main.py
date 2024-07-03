import sys
#sdfsdf

from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QTreeWidget, QHeaderView, QTableWidgetItem
from GUI.MainWindow_ui import Ui_MainWindow
from GUI.MyOpenGLCharting import MyCharting

import time

import threading
from ViconWrapper.ViconWrapper import ViconWrapper
# from WindowFilters import WindowFilter

import Kinematics.Calculation as calc
import Kinematics.Filters as filters

import numpy as np

from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer
from OpenGL.GL import *
from OpenGL.GLU import *
from PySide6.QtCore import Qt

import pandas as pd
import os
from tkinter import filedialog

import socket
import struct


class Plotting:
    def __init__(self, myChart):
        self.myChart = myChart
        self.myChart.setCustomXYAxis(0, 1000, -90, 90)
        self.myChart.series1.setName("Angle 1")
        self.myChart.series2.setName("Angle 2")
        self.myChart.series3.setName("Device Data")

        self.Angle1 = "" #name of the angle to draw
        self.Angle2 = "" #name of the angle to draw
        self.deviceData = [] #ex [device][channel][component]

    def clearAll(self):
        self.myChart.clearAllSeries()

    def updatePlotting(self, frameNumber, vicon):
        # print("Updating Plotting")
        # print(self.Angle1, self.Angle2, self.deviceData)
        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.addAnglesToPlot(frameNumber, activeSubject)
            
        self.addDeviceDataToPlot(frameNumber, vicon)
        self.myChart.finalize()

    def addAnglesToPlot(self, frameNumber, activeSubject):
        if self.Angle1 != "":
            if self.Angle1[1:] in activeSubject.kinematics.angleFlags and activeSubject.kinematics.angleFlags[self.Angle1[1:]]:
                self.myChart.addData(1, frameNumber, activeSubject.kinematics.anglesDictionary[self.Angle1])
        if self.Angle2 != "":
            if self.Angle2[1:] in activeSubject.kinematics.angleFlags and activeSubject.kinematics.angleFlags[self.Angle2[1:]]:
                self.myChart.addData(2, frameNumber, activeSubject.kinematics.anglesDictionary[self.Angle2])

    def addDeviceDataToPlot(self, frameNumber, vicon):
        if self.deviceData == ['','',''] or self.deviceData == ['None', 'None', 'None'] or self.deviceData == []:
            return
        
        #check if device exists
        if self.deviceData[0] not in vicon.devices:
            return
        
        #check that the device is online
        if not vicon.devices[self.deviceData[0]]["Online"]:
            return
        
        data = vicon.devices[self.deviceData[0]]["Data"][self.deviceData[1]][self.deviceData[2]]['values'][0]
        for i in range(len(data)):
            self.myChart.addData(3, frameNumber - 1 + i/len(data) ,data[i])

class Exporting:
    def __init__(self):
        self.angleExportList = [] #ex [angle]
        self.angleExportFrame = pd.DataFrame()

        self.deviceExportList = [] #ex [device][channel]
        self.deviceExportFrames = {} #keys "device:channel"

        
        #exporting variables and flags
        self.isRecording = False
        self.savingIndex = 0
        self.savingAutoIndex = False
        self.filename = "Recording"
        self.saveAllDeviceData = True
        #default export path is the current directory of the main file
        self.savePath = os.path.dirname(os.path.realpath(__name__))

        self.recordingStartTime = 0 #in seconds
        self.recordingDuration = 0 # in seconds

    def startTimedRecording(self, duration):
        self.isRecording = True
        self.recordingDuration = duration
        self.recordingStartTime = time.time()


    def saveDataToCSV(self):
        name = self.filename
        fullSavePath = ""
        #saving angles
        if not self.savingAutoIndex:
            if self.savingIndex == 0:
                fullSavePath = os.path.join(self.savePath, name + "_angles.csv")
            else:
                fullSavePath = os.path.join(self.savePath, name + "_angles_" + str(self.savingIndex) + ".csv")
        else:
            savingIndex = 0

            if os.path.isfile(os.path.join(self.savePath, name + "_angles.csv")):
                savingIndex += 1

            #check if file exists, if it does, increment index
            while os.path.isfile(os.path.join(self.savePath, name + "_angles_" + str(savingIndex) + ".csv")):
                savingIndex += 1

            if savingIndex == 0:
                fullSavePath = os.path.join(self.savePath, name + "_angles.csv")
            else:
                fullSavePath = os.path.join(self.savePath, name + "_angles_" + str(savingIndex) + ".csv")
                                    
        self.angleExportFrame.to_csv(fullSavePath, index=False)

        #saving device data
        for selectedDevice in self.deviceExportFrames:
            deviceName, channel = selectedDevice.split(":")
            if not self.savingAutoIndex:
                if self.savingIndex == 0:
                    fullSavePath = os.path.join(self.savePath, name + f"_{deviceName}_{channel}.csv")
                else:
                    fullSavePath = os.path.join(self.savePath, name + f"_{deviceName}_{channel}_" + str(self.savingIndex) + ".csv")
            else:
                savingIndex = 0

                if os.path.isfile(os.path.join(self.savePath, name + f"_{deviceName}_{channel}.csv")):
                    savingIndex += 1


                while os.path.isfile(os.path.join(self.savePath, name + f"_{deviceName}_{channel}_" + str(savingIndex) + ".csv")):
                    savingIndex += 1
                
                if savingIndex == 0:
                    fullSavePath = os.path.join(self.savePath, name + f"_{deviceName}_{channel}.csv")
                else:
                    fullSavePath = os.path.join(self.savePath, name + f"_{deviceName}_{channel}_" + str(savingIndex) + ".csv")

            self.deviceExportFrames[selectedDevice].to_csv(fullSavePath, index=False)

        self.angleExportFrame = pd.DataFrame()
        self.deviceExportFrames = {}
        self.recordingStartTime = 0
        self.recordingDuration = 0

    def updateExporting(self, frameNumber, vicon):
        if time.time() - self.recordingStartTime >= self.recordingDuration and self.recordingDuration != 0:
            self.isRecording = False
            self.saveDataToCSV()
            addToLog("Recording Stopped")
            addToLog("Files Saved To: " + self.savePath)

        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.addAnglesToExport(frameNumber, activeSubject)
        
        self.addDeviceDataToExport(frameNumber, vicon)

    def addAnglesToExport(self, frameNumber, activeSubject):
        new_row_dict = {'Frame': [frameNumber]}
        for angle in self.angleExportList:
            new_row_dict['L'+angle] = [activeSubject.kinematics.anglesDictionary['L'+angle]]
            new_row_dict['R'+angle] = [activeSubject.kinematics.anglesDictionary['R'+angle]]

        new_row = pd.DataFrame(new_row_dict)
        self.angleExportFrame = pd.concat([self.angleExportFrame, new_row], ignore_index=True)

    def addDeviceDataToExport(self, frameNumber, vicon):
        for deviceName, channel in self.deviceExportList:
            listOfComponents = list(vicon.devices[deviceName]["Data"][channel].keys())
            listOfComponents.remove("Online")
            if f"{deviceName}:{channel}" not in self.deviceExportFrames:
                self.deviceExportFrames[f"{deviceName}:{channel}"] = pd.DataFrame()
            if self.saveAllDeviceData:
                for i in range(len(vicon.devices[deviceName]["Data"][channel][listOfComponents[0]]['values'][0])):
                    new_dict_row = {'Frame': [frameNumber-1+i/len(vicon.devices[deviceName]["Data"][channel][listOfComponents[0]]['values'][0])]}
                    for component in listOfComponents:
                        new_dict_row[component] = [vicon.devices[deviceName]["Data"][channel][component]['values'][0][i]]
                    new_row = pd.DataFrame(new_dict_row)
                    self.deviceExportFrames[f"{deviceName}:{channel}"] = pd.concat([self.deviceExportFrames[f"{deviceName}:{channel}"], new_row], ignore_index=True)
            else:
                new_dict_row = {'Frame': [frameNumber]}
                for component in listOfComponents:
                    new_dict_row[component] = [vicon.devices[deviceName]["Data"][channel][component]['values'][0][-1]]
                new_row = pd.DataFrame(new_dict_row)
                self.deviceExportFrames[f"{deviceName}:{channel}"] = pd.concat([self.deviceExportFrames[f"{deviceName}:{channel}"], new_row], ignore_index=True)

class Streaming:
    def __init__(self, targetIP = "127.0.0.1", port = 5005):
        #UDP Streaming
        self.sock = []
        self.UDPErrorCount = 0
        self.UDPStream = False
        self.UDPHost = targetIP
        self.UDPPort = port

        self.packetSize = 50
        self.valueSize = 10
        self.deviceStreamList = [] #ex [device][channel][component]
        self.angleStreamList = [] #ex [Side]+[angle] LHip

    def updateStream(self, vicon):
        if not self.UDPStream:
            return
        
        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.sendAngleOverUDP(activeSubject)
        
        self.sendDeviceDataOverUDP(vicon)


    def sendAngleOverUDP(self, activeSubject):
        for angle in self.angleStreamList:
            angleName = angle
            angleNameSize = len(angleName)
            angleValue = activeSubject.kinematics.anglesDictionary[angle]
            #convert angle to string with set length
            angleValue = str(angleValue)
            angleValue = angleValue[:self.valueSize]
            if len(angleValue) < self.valueSize:
                angleValue = angleValue + "0"*(self.valueSize-len(angleValue))

            #create a packet to store character data
            packet = " "*self.packetSize

            #add angle name at the beginning of the packet
            packet = angleName + packet[angleNameSize:]
            packet = packet[:self.packetSize-self.valueSize] + angleValue
            
            #add $ to the end of the packet
            packet = packet + "$"

            # print(packet)
            self.sendOverUDP(packet)


              



    def sendDeviceDataOverUDP(self, vicon):
        for deviceName, channel, component in self.deviceStreamList:
            deviceLabel = deviceName + ":" + channel + ":" + component
            deviceLabelSize = len(deviceLabel)


            deviceData = vicon.devices[deviceName]["Data"][channel][component]['values'][0][-1]
            deviceData = str(deviceData)
            deviceData = deviceData[:self.valueSize]
            if len(deviceData) < self.valueSize: #add 0s to the end of the string
                deviceData = deviceData + "0"*(self.valueSize-len(deviceData))

            packet = " "*self.packetSize

            packet = deviceLabel + packet[deviceLabelSize:]
            packet = packet[:self.packetSize-self.valueSize] + deviceData

            #add $ to the end of the packet
            packet = packet + "$"

            # print(packet)
            self.sendOverUDP(packet)

    def sendOverUDP(self, data):
        try:
            #data is a string, convert to bytes
            data = data.encode('utf-8')
            packed_data = struct.pack(f"{len(data)}s", data)

            # Send the packed data via UDP
            self.sock.sendto(packed_data, (self.UDPHost, self.UDPPort))
            self.UDPErrorCount = 0

        except:
            self.UDPErrorCount += 1
            addToLog(f"Error Sending Data Over UDP - attempt {self.UDPErrorCount}")

            if self.UDPErrorCount >= 3:
                self.stopUDPStream()

    def startUDPStream(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.UDPStream = True
        addToLog("UDP Streaming Started")

    def stopUDPStream(self):
        self.UDPStream = False
        self.sock.close()
        addToLog("UDP Streaming Stopped")
    
#Like OpenGL main loop, but witough OpenGLRenderering
class MainTask:
    
    def __init__(self):
        self.frame_count = 0
        self.start_time = time.time()

        
        self.activeSubject = None

        self.filterType = "none"
        self.filterWindow = 101
        self.filterLowCut = .01
        self.filterHighCut = 29
        self.filterSampleRate = 100
        self.setFilterFlag = False

        self.plotting = Plotting(myChart)
        self.maxFrames = 1000

        self.exporting = Exporting()
        self.windowRecordingMode = False
        self.pendingWindowData = False

        self.streaming = Streaming()

        self.lastViconFrame = 0
        self.currentViconFrame = 0

    def runFrame(self):
        global vicon

        self.lastViconFrame = self.currentViconFrame    #used for clearning the plot 
        self.currentViconFrame = vicon.frameNumber      #used for clearning the plot

        if self.lastViconFrame%self.maxFrames > self.currentViconFrame%self.maxFrames:
            print("Clearing Plot")
            self.plotting.clearAll()

        if vicon.lastFrameNumber > vicon.frameNumber:
            
            if self.exporting.isRecording and self.windowRecordingMode:
                self.windowRecordingMode = False
                self.exporting.isRecording = False
                self.exporting.saveDataToCSV()
                addToLog("Recording Stopped")
                addToLog("Files Saved To: " + self.exporting.savePath)

            if self.windowRecordingMode and self.pendingWindowData:
                self.pendingWindowData = False
                self.exporting.isRecording = True
                addToLog("Recording Started")


                

        
        if vicon.subjectExists():
            self.activeSubject = vicon.getSubject(vicon.subjects[0].name)

            if self.setFilterFlag:
                self.setFilterFlag = False
                self.activeSubject.kinematics.setFilter(self.filterWindow, self.filterSampleRate, self.filterType, self.filterLowCut, self.filterHighCut)
        else:
            self.activeSubject = None



        # if not (self.plotting.Angle1 == "" or self.plotting.Angle2 == "" or self.plotting.deviceData == ['','','']):
        self.plotting.updatePlotting(vicon.frameNumber % self.maxFrames, vicon)
        if self.exporting.isRecording:
            self.exporting.updateExporting(vicon.frameNumber, vicon)
        if self.streaming.UDPStream:
            self.streaming.updateStream(vicon)

        self.tickFPS()
        

    def tickFPS(self):
        global vicon
        self.frame_count += 1
        if time.time() - self.start_time >= 1.0:  # Every second, print the FPS
                updateMainLoopFPS(self.frame_count / (time.time() - self.start_time))
                updateViconStreamFPS(vicon.localFPS)

                self.frame_count = 0
                self.start_time = time.time()

    def zeroSubjectAngles(self):
        if self.activeSubject != None:
            self.activeSubject.kinematics.recordZeroPosition()



Main = None         #Main Task
ui = None           #UI elements
vicon = None        #Vicon Wrapper

############################ DEVICE SELECTION FUNCTIONS ############################

def updateViconDeviceTreeStatus(item):
    global vicon, ui

    isChild = item.childCount() == 0

    if item.text(0) == "Humac":
        isChild = False

    if isChild:
        vicon.devices[item.parent().text(0)]["Data"][item.text(0)]["Online"] = not vicon.devices[item.parent().text(0)]["Data"][item.text(0)]["Online"]
        if vicon.devices[item.parent().text(0)]["Data"][item.text(0)]["Online"]:
            vicon.devices[item.parent().text(0)]["Online"] = True


    else:
        vicon.devices[item.text(0)]["Online"] = not vicon.devices[item.text(0)]["Online"]
        for channel in vicon.devices[item.text(0)]["Data"]:
            vicon.devices[item.text(0)]["Data"][channel]["Online"] = vicon.devices[item.text(0)]["Online"]




    ui.deviceTree.clear()
    ui.comboBoxDevice.clear()
    treeItems = []
    #fill device tree with devices from vicon
    for device in vicon.devices:
        deviceIsOnline = vicon.devices[device]["Online"]

        item = QTreeWidgetItem([device, "✅" if deviceIsOnline else "❌"])

        if deviceIsOnline:
            ui.comboBoxDevice.addItem(device)

        for channel in vicon.devices[device]["Data"]:
            item.addChild(QTreeWidgetItem([channel, "✅" if vicon.devices[device]["Data"][channel]["Online"] else "❌"]))
        treeItems.append(item)
    ui.deviceTree.addTopLevelItems(treeItems)

def updateDeviceTree():
    global vicon, ui
    


    ui.deviceTree.clear()
    treeItems = []
    #fill device tree with devices from vicon
    for device in vicon.devices:
        deviceIsOnline = vicon.devices[device]["Online"]

        item = QTreeWidgetItem([device, "✅" if deviceIsOnline else "❌"])

        if deviceIsOnline:
            ui.comboBoxDevice.addItem(device)

        for channel in vicon.devices[device]["Data"]:
            item.addChild(QTreeWidgetItem([channel, "✅" if vicon.devices[device]["Data"][channel]["Online"] else "❌"]))
        treeItems.append(item)
    ui.deviceTree.addTopLevelItems(treeItems)

def comboBoxDeviceChanged():
    global ui, vicon
    device = ui.comboBoxDevice.currentText()

    if device == "":
        return
    
    ui.comboBoxChannel.clear()
    for channel in vicon.devices[device]["Data"]:
        if vicon.devices[device]["Data"][channel]["Online"]:
            ui.comboBoxChannel.addItem(channel)

def comboBoxChannelChanged():
    global ui, vicon
    device = ui.comboBoxDevice.currentText()
    channel = ui.comboBoxChannel.currentText()

    if device == "" or channel == "":
        return
    
    ui.comboBoxComponent.clear()
    for component in vicon.devices[device]["Data"][channel]:
        if component == "Online":
            continue
        ui.comboBoxComponent.addItem(component)

def buttonClickedSetDeviceData():
    global Main, ui
    Main.plotting.deviceData = [ui.comboBoxDevice.currentText(), ui.comboBoxChannel.currentText(), ui.comboBoxComponent.currentText()]
    print(Main.plotting.deviceData)   

############################ ANGLE SELECTION FUNCTIONS ############################

def updateAngleTreeStatus(item):
    global Main, ui

    Main.activeSubject.kinematics.angleFlags[item.text(0)] = not Main.activeSubject.kinematics.angleFlags[item.text(0)]
    ui.angleComboBox.clear()
    ui.angleComboBox_2.clear()
    for angle in Main.activeSubject.kinematics.angleFlags:
        if Main.activeSubject.kinematics.angleFlags[angle]:
            ui.angleComboBox.addItem(angle)
            ui.angleComboBox_2.addItem(angle)

    updateAngleTree()

def updateAngleTree():
    global Main, ui

    if Main.activeSubject == None:
        return

    ui.angleTree.clear()
    treeItems = []
    #fill device tree with angles from subject
    for angle in Main.activeSubject.kinematics.angleFlags:
        item = QTreeWidgetItem([angle, "✅" if Main.activeSubject.kinematics.angleFlags[angle] else "❌"])
        treeItems.append(item)

    ui.angleTree.addTopLevelItems(treeItems)

def setDrawingAngle1(angle):
    global Main, ui
    Main.plotting.clearAll()

    Main.plotting.Angle1 = ""

    if ui.checkBoxLeft.isChecked():
        Main.plotting.Angle1 = 'L'+angle
    elif ui.checkBoxRight.isChecked():
        Main.plotting.Angle1 = 'R'+angle

    print("setDrawingAngle1", Main.plotting.Angle1)

def setDrawingAngle2(angle):
    global Main, ui
    Main.plotting.clearAll()

    Main.plotting.Angle2 = ""

    if ui.checkBoxLeft_2.isChecked():
        Main.plotting.Angle2 = 'L'+angle
    if ui.checkBoxRight_2.isChecked():
        Main.plotting.Angle2 = 'R'+angle

    print("setDrawingAngle2", Main.plotting.Angle2)

def updateLegsandMarkreDimentions():
    global vicon, ui
    lLegMM = ui.spinLeftLeg.value()
    rLegMM = ui.spinRightLeg.value()
    markerR = ui.spinMarkerR.value()
    vicon.updateLegAndMarkerLengths(lLegMM, rLegMM, markerR)


def addToLog(text):
    global ui
    ui.plainTextEdit.appendPlainText(text)

def updateMainLoopFPS(fps):
    global ui
    ui.lblFPS.setText(f'FPS {fps:.2f}')

def updateViconStreamFPS(fps):
    global ui
    ui.lblViconFPS.setText(f'FPS {fps:.2f}') 

def adjestChartRange():
    global Main, ui
    ##y axis
    absoluteMax = ui.spinYmax.value()
    absoluteMin = ui.spinYmin.value()

    val1 = ui.sliderYrange1.value()
    val2 = ui.sliderYrange2.value()

    var1Normalized = val1/ui.sliderYrange1.maximum()
    var2Normalized = val2/ui.sliderYrange2.maximum()

    minNormalized = min(var1Normalized, var2Normalized)
    maxNormalized = max(var1Normalized, var2Normalized)

    var1 = minNormalized * (absoluteMax - absoluteMin) + absoluteMin
    var2 = maxNormalized * (absoluteMax - absoluteMin) + absoluteMin

    Main.maxFrames = ui.spinNFrames.value()
    Main.plotting.myChart.setCustomXYAxis(0, ui.spinNFrames.value(), var1, var2)
                       
def buttonClickedSaveWindowToCSV():
    global Main, ui
    addToLog("Pending Window Data Export")
    Main.windowRecordingMode = True
    Main.pendingWindowData = True

def startFinishAbsoluteRecording():
    global Main, ui

    if ui.btnRecordStopSaveToCSV.text() == "Start Recording":
        ui.btnSaveWindowToCSV.setEnabled(False)
        ui.btnRecordDuration.setEnabled(False)
        addToLog("Recording Started")
        ui.btnRecordStopSaveToCSV.setText("Stop Recording")

        Main.exporting.isRecording = True
    else:
        ui.btnRecordStopSaveToCSV.setText("Start Recording")
        Main.exporting.isRecording = False
        Main.exporting.saveDataToCSV()

        addToLog("Recording Stopped")
        addToLog("Files Saved To: " + Main.exporting.savePath)


        ui.btnRecordDuration.setEnabled(True)
        ui.btnSaveWindowToCSV.setEnabled(True)

def startTimeRecording():
    global Main, ui
    Main.exporting.startTimedRecording(ui.spinInterval.value())
    addToLog("Timed Recording Started")

def setPath():
    global Main, ui
    path = filedialog.askdirectory()
    if path != "":
        Main.exporting.savePath = path
    
    ui.txtSavePath.setText(Main.exporting.savePath)

def setFilterType(filterType):
    global Main, ui
    Main.filterType = filterType
    Main.filterWindow = ui.spinSize.value()
    Main.filterLowCut = ui.spinLowcut.value()
    Main.filterHighCut = ui.spinHighcut.value()
    Main.filterSampleRate = ui.spinSampleRate.value()
    
    filterMessage = f"{Main.filterType}"
    if filterType == "bandpass":
        filterMessage = f"{Main.filterType} - [{Main.filterLowCut},{Main.filterHighCut}] Hz, Size {Main.filterWindow}, Sample Rate {Main.filterSampleRate}"
    elif filterType == "moving_average":
        filterMessage = f"{Main.filterType} - Size {Main.filterWindow}, Sample Rate {Main.filterSampleRate}"
    elif filterType == "moving_median":
        filterMessage = f"{Main.filterType} - Size {Main.filterWindow}, Sample Rate {Main.filterSampleRate}"

    ui.lblAngleFilterIndec.setText(filterMessage)

    
    Main.setFilterFlag = True

def updateExportTable():
    global ui, Main, vicon

    Main.exporting.deviceExportList = [] #ex [device][channel]
    Main.exporting.angleExportList = [] #ex [angle]


    for device in vicon.devices:
        for channel in vicon.devices[device]["Data"]:
            if vicon.devices[device]["Data"][channel]["Online"]:
                Main.exporting.deviceExportList.append([device, channel])

    if Main.activeSubject != None:
        for angle in Main.activeSubject.kinematics.angleFlags:
            if Main.activeSubject.kinematics.angleFlags[angle]:
                Main.exporting.angleExportList.append(angle)

    ui.tableExport.clear()
    ui.tableExport.setRowCount(max(len(Main.exporting.angleExportList), len(Main.exporting.deviceExportList)))
    ui.tableExport.setColumnCount(2)
    #stretch the columns
    ui.tableExport.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    ui.tableExport.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    #name the columns
    ui.tableExport.setHorizontalHeaderLabels(["Angles To Export", "Devices To Export"])
    
    #fill the table
    for i in range(max(len(Main.exporting.angleExportList), len(Main.exporting.deviceExportList))):
        if i < len(Main.exporting.angleExportList):
            ui.tableExport.setItem(i, 0, QTableWidgetItem(Main.exporting.angleExportList[i]))
        if i < len(Main.exporting.deviceExportList):
            ui.tableExport.setItem(i, 1, QTableWidgetItem(f"{Main.exporting.deviceExportList[i][0]}:{Main.exporting.deviceExportList[i][1]}"))

def updateStreamTable():
    global ui, Main, vicon

    rawDeviceStreamList = [] #ex [device][channel][component]
    rawAngleStreamList = [] #ex [Side]+[angle] LHip


    for device in vicon.devices:
        for channel in vicon.devices[device]["Data"]:
            if vicon.devices[device]["Data"][channel]["Online"]:
                for component in vicon.devices[device]["Data"][channel]:
                    if component != "Online":
                        rawDeviceStreamList.append([device, channel, component])

    if Main.activeSubject != None:
        for angle in Main.activeSubject.kinematics.angleFlags:
            if Main.activeSubject.kinematics.angleFlags[angle]:
                rawAngleStreamList.append('L'+angle)
                rawAngleStreamList.append('R'+angle)


    ui.tableStream.clear()
    ui.tableStream.setRowCount(max(len(rawAngleStreamList), len(rawDeviceStreamList)))
    ui.tableStream.setColumnCount(2)
    #stretch the columns
    ui.tableStream.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    ui.tableStream.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    #name the columns
    ui.tableStream.setHorizontalHeaderLabels(["Angles To Export", "Devices To Export"])
    
    #fill the table
    for i in range(max(len(rawAngleStreamList), len(rawDeviceStreamList))):
        if i < len(rawAngleStreamList):
            ui.tableStream.setItem(i, 0, QTableWidgetItem(rawAngleStreamList[i]))
        if i < len(rawDeviceStreamList):
            ui.tableStream.setItem(i, 1, QTableWidgetItem(f"{rawDeviceStreamList[i][0]}:{rawDeviceStreamList[i][1]}:{rawDeviceStreamList[i][2]}"))

def tabSelected(tabName):
    global ui

    print(tabName)
    if tabName == "Exporting":
        updateExportTable()
    elif tabName == "Streaming":
        updateStreamTable()
    elif tabName == "Angle Selection":
        updateAngleTree()
    elif tabName == "Device Selection":
        updateDeviceTree()    

def updateSavingParameters():
    global Main, ui
    Main.exporting.filename = ui.txtFilename.text()
    Main.exporting.savingIndex = ui.spinSavingIndex.value()
    Main.exporting.savingAutoIndex = ui.checkSavingAutoIndex.isChecked()
    Main.exporting.saveAllDeviceData = ui.checkSaveAllDeviceData.isChecked()

    print(Main.exporting.filename, Main.exporting.savingIndex, Main.exporting.savingAutoIndex, Main.exporting.saveAllDeviceData)

def startEndStream():
    global Main, ui
    if ui.btnStartEndStream.text() == "Start Stream":
        Main.streaming.UDPHost = ui.txtTargetMachineIP.text()
        Main.streaming.UDPPort = int(ui.txtStreamPort.text())
        Main.streaming.packetSize = ui.spinPacketSize.value()
        Main.streaming.valueSize = ui.spinValueSize.value()
        if Main.streaming.valueSize > Main.streaming.packetSize:
            Main.streaming.packetSize = Main.streaming.valueSize
            ui.spinPacketSize.setValue(Main.streaming.packetSize)

        Main.streaming.startUDPStream()
        ui.btnStartEndStream.setText("End Stream")
    else:
        Main.streaming.stopUDPStream()
        ui.btnStartEndStream.setText("Start Stream")

def streamingTableSelectionChanged():
    global ui, Main
    
    selectedItems = ui.tableStream.selectedItems()
    print(selectedItems)

    #set values to stream
    Main.streaming.deviceStreamList = [] #ex [device][channel][component]
    Main.streaming.angleStreamList = [] #ex [Side]+[angle] LHip
    for item in selectedItems:
        if item.column() == 0:
            Main.streaming.angleStreamList.append(item.text())
        elif item.column() == 1:
            device, channel, component = item.text().split(":")
            Main.streaming.deviceStreamList.append([device, channel, component])

    print(Main.streaming.angleStreamList)
    print(Main.streaming.deviceStreamList)

    #set text to packet otder planetext

    ui.plainTextOrderOfPackets.clear()

    #angles first 
    #devices second
    packetSize = ui.spinPacketSize.value()
    valueSize = ui.spinValueSize.value()
    if valueSize > packetSize:
        packetSize = valueSize
        ui.spinPacketSize.setValue(packetSize)

    for angle in Main.streaming.angleStreamList:
        angleNameSize = len(angle)
        angleValue = "X"*valueSize
        
        packet = " "*packetSize
        #add angle name at the beginning of the packet
        packet = angle + packet[angleNameSize:]
        packet = packet[:packetSize-valueSize] + angleValue
        
        #add $ to the end of the packet
        packet = packet + "$"

        ui.plainTextOrderOfPackets.appendPlainText(packet)

    for deviceName, channelName, componentName in Main.streaming.deviceStreamList:
        deviceLabel = deviceName + ":" + channelName + ":" + componentName
        deviceLabelSize = len(deviceLabel)

        deviceData = "X"*valueSize
        packet = " "*packetSize

        packet = deviceLabel + packet[deviceLabelSize:]
        packet = packet[:packetSize-valueSize] + deviceData

        #add $ to the end of the packet
        packet = packet + "$"

        ui.plainTextOrderOfPackets.appendPlainText(packet)







def closingEvent():
    global vicon, Main
    print("Closing Event")
    vicon.stopStream()
    Main.streaming.stopUDPStream()

    
def test():
    global vicon, ui
    text = f"Devices: {vicon.devices}\n"
    ui.plainTextEdit.appendPlainText(text)


def setupGUI():
    global myChart, Main, vicon, ui

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Vicon Data Viewer")
    app.setApplicationDisplayName("Vicon Data Viewer")
    app.setApplicationVersion("1.0")


    MainWindow = QMainWindow()
    #make full screen
    # MainWindow.showMaximized()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    
    myChart = MyCharting()
    ui.horizontalLayout.addWidget(myChart.chartView)

    Main = MainTask()
    # ui.OpenGLLayout.addWidget(Main)

    ui.deviceTree.setColumnCount(2)
    ui.deviceTree.setHeaderLabels(["Device", "Online"])
    updateDeviceTree()
    ui.deviceTree.itemDoubleClicked.connect(lambda: updateViconDeviceTreeStatus(ui.deviceTree.currentItem()))


    ui.angleTree.setColumnCount(2)
    ui.angleTree.setHeaderLabels(["Angle", "Selected"])
    ui.angleTree.itemDoubleClicked.connect(lambda: updateAngleTreeStatus(ui.angleTree.currentItem()))


    
    ui.comboBoxDevice.currentIndexChanged.connect(lambda: comboBoxDeviceChanged())
    ui.comboBoxChannel.currentIndexChanged.connect(lambda: comboBoxChannelChanged())
    ui.btnAddRemoveDeviceFromStream.clicked.connect(lambda: buttonClickedSetDeviceData())

    ui.spinYmax.valueChanged.connect(lambda: adjestChartRange())
    ui.spinYmin.valueChanged.connect(lambda: adjestChartRange())
    ui.sliderYrange1.valueChanged.connect(lambda: adjestChartRange())
    ui.sliderYrange2.valueChanged.connect(lambda: adjestChartRange())
    ui.spinNFrames.valueChanged.connect(lambda: adjestChartRange())


    ui.angleComboBox.currentIndexChanged.connect(lambda: setDrawingAngle1(ui.angleComboBox.currentText()))
    ui.checkBoxLeft.stateChanged.connect(lambda: setDrawingAngle1(ui.angleComboBox.currentText()))
    ui.checkBoxRight.stateChanged.connect(lambda: setDrawingAngle1(ui.angleComboBox.currentText()))

    ui.angleComboBox_2.currentIndexChanged.connect(lambda: setDrawingAngle2(ui.angleComboBox_2.currentText()))
    ui.checkBoxLeft_2.stateChanged.connect(lambda: setDrawingAngle2(ui.angleComboBox_2.currentText()))
    ui.checkBoxRight_2.stateChanged.connect(lambda: setDrawingAngle2(ui.angleComboBox_2.currentText()))

    ui.btnZerAngles.clicked.connect(lambda: Main.zeroSubjectAngles())
    ui.btnZerAngles_1.clicked.connect(lambda: Main.zeroSubjectAngles())
    ui.btnSaveWindowToCSV.clicked.connect(lambda: buttonClickedSaveWindowToCSV())
    ui.btnRecordStopSaveToCSV.clicked.connect(lambda: startFinishAbsoluteRecording())

    ui.txtSavePath.setText(Main.exporting.savePath)
    ui.btnSetPath.clicked.connect(lambda: setPath())

    #fill filter combo box
    for filter in filters.FilterTypes:
        ui.comboFilter.addItem(filter)
    ui.comboFilter.currentIndexChanged.connect(lambda: setFilterType(ui.comboFilter.currentText()))
    ui.spinSize.valueChanged.connect(lambda: setFilterType(ui.comboFilter.currentText()))
    ui.spinLowcut.valueChanged.connect(lambda: setFilterType(ui.comboFilter.currentText()))
    ui.spinHighcut.valueChanged.connect(lambda: setFilterType(ui.comboFilter.currentText()))
    ui.spinSampleRate.valueChanged.connect(lambda: setFilterType(ui.comboFilter.currentText()))

    ui.tabWidget.currentChanged.connect(lambda: tabSelected(ui.tabWidget.tabText(ui.tabWidget.currentIndex())))

    ui.txtFilename.setText(Main.exporting.filename)
    ui.spinSavingIndex.setValue(Main.exporting.savingIndex)
    ui.checkSavingAutoIndex.setChecked(Main.exporting.savingAutoIndex)
    ui.checkSaveAllDeviceData.setChecked(Main.exporting.saveAllDeviceData)
    ui.txtFilename.textChanged.connect(lambda: updateSavingParameters())
    ui.spinSavingIndex.valueChanged.connect(lambda: updateSavingParameters())
    ui.spinInterval.valueChanged.connect(lambda: updateSavingParameters())
    ui.checkSavingAutoIndex.stateChanged.connect(lambda: updateSavingParameters())
    ui.checkSaveAllDeviceData.stateChanged.connect(lambda: updateSavingParameters())

    ui.btnRecordDuration.clicked.connect(lambda: startTimeRecording())
    ui.btnStartEndStream.clicked.connect(lambda: startEndStream())

    ui.tableStream.itemSelectionChanged.connect(lambda: streamingTableSelectionChanged())


    ui.spinLeftLeg.valueChanged.connect(lambda: updateLegsandMarkreDimentions())
    ui.spinRightLeg.valueChanged.connect(lambda: updateLegsandMarkreDimentions())
    ui.spinMarkerR.valueChanged.connect(lambda: updateLegsandMarkreDimentions())

    ui.btnTest.clicked.connect(lambda: test())

    #add closing event
    app.aboutToQuit.connect(lambda: closingEvent())

    timer = QTimer(MainWindow)
    timer.timeout.connect(Main.runFrame)
    timer.start(1)  # ~60 frames per second



    sys.exit(app.exec())



def ViconThreadingFunction():
    global vicon
    host = "35.16.69.139:801"
    vicon = ViconWrapper(host)
    vicon.startStream()
    vicon.startStreamLoop()

if __name__ == "__main__":

    viconThread = threading.Thread(target=ViconThreadingFunction)
    viconThread.start()

 
    setupGUI()




   

 

