"""
Vicon Data Interface - Real-time Motion Capture Data Processing and Visualization

This application provides a comprehensive interface for capturing, processing, visualizing,
and exporting real-time data from Vicon motion capture systems. It is designed for
biomechanics research and clinical applications.

Key Features:
    - Real-time data streaming from Vicon motion capture systems
    - Joint angle calculations for lower extremity kinematics
    - Data visualization with customizable plotting
    - Multiple data export modes (duration-based, manual, windowed)
    - UDP streaming for integration with external applications
    - Configurable signal filtering (bandpass, moving average, moving median, Kalman)
    - Real-time visual feedback for biofeedback applications

Architecture:
    - MainTask: Core processing loop coordinating all operations
    - Plotting: Real-time visualization of angles and device data
    - Exporting: Data recording and CSV export functionality
    - Streaming: UDP communication for external applications
    - Feedback: Visual biofeedback system for real-time monitoring

Dependencies:
    - PySide6: GUI framework
    - numpy: Numerical computations
    - pandas: Data management and export
    - vicon_dssdk: Vicon DataStream SDK
    - scipy: Signal processing

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

# Standard library imports
import sys
import time
import os
import socket
import struct
import threading

# Third-party imports
import numpy as np
import pandas as pd
from tkinter import filedialog

# PySide6 (Qt) imports
from PySide6.QtWidgets import (QApplication, QMainWindow, QTreeWidgetItem, 
                               QTreeWidget, QHeaderView, QTableWidgetItem, QWidget)
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtCore import QTimer, Qt
from OpenGL.GL import *
from OpenGL.GLU import *

# Local application imports
from GUI.MainWindow_ui import Ui_MainWindow
from GUI.FeedbackWindow_ui import Ui_Form
from GUI.FeedbackGraph import FeedbackGraph
from GUI.MyOpenGLCharting import MyCharting
from ViconWrapper.ViconWrapper import ViconWrapper
import Kinematics.Calculation as calc
import Filters as filters


# ============================================================================
# DATA VISUALIZATION CLASSES
# ============================================================================

class Plotting:
    """
    Manages real-time plotting of joint angles and device data.
    
    This class handles the visualization of up to two joint angles and one device
    data stream simultaneously. It supports real-time filtering of device data
    and integrates with the OpenGL-based charting system.
    
    Attributes:
        myChart (MyCharting): The OpenGL chart widget for rendering
        Angle1 (str): Name of the first angle to plot (e.g., 'LHip')
        Angle2 (str): Name of the second angle to plot (e.g., 'RKnee')
        deviceData (list): Device data specification [device, channel, component]
        deviceFilter (MyFilter): Filter applied to device data before plotting
        
    Methods:
        clearAll(): Clears all data series from the chart
        updateDeviceFilterType(): Configures the device data filter
        updatePlotting(): Updates all data series for the current frame
        addAnglesToPlot(): Adds angle data points to the chart
        addDeviceDataToPlot(): Adds device data points to the chart
    """
    
    def __init__(self, myChart):
        """
        Initialize the plotting system.
        
        Args:
            myChart (MyCharting): The OpenGL chart widget to use for rendering
        """
        self.myChart = myChart
        # Set initial chart range: X-axis (0-1000 frames), Y-axis (-90 to 90 degrees)
        self.myChart.setCustomXYAxis(0, 1000, -90, 90)
        self.myChart.series1.setName("Angle 1")
        self.myChart.series2.setName("Angle 2")
        self.myChart.series3.setName("Device Data")

        # Data stream selections
        self.Angle1 = ""  # Name of the first angle to draw (e.g., 'LHip')
        self.Angle2 = ""  # Name of the second angle to draw (e.g., 'RKnee')
        self.deviceData = []  # Format: [device, channel, component]
        
        # Initialize device data filter (default: no filtering)
        self.deviceFilter = filters.MyFilter(1, 1, "none")

    def clearAll(self):
        """Clear all data series from the chart."""
        self.myChart.clearAllSeries()

    def updateDeviceFilterType(self, windowSize, sampleRate, filterType, lowCut, highCut):
        """
        Update the filter configuration for device data.
        
        Args:
            windowSize (int): Number of samples in the filter window
            sampleRate (float): Sampling frequency in Hz
            filterType (str): Type of filter ('none', 'bandpass', 'moving_average', 'moving_median')
            lowCut (float): Lower cutoff frequency for bandpass filter (Hz)
            highCut (float): Upper cutoff frequency for bandpass filter (Hz)
        """
        self.deviceFilter = filters.MyFilter(windowSize, sampleRate, filterType, lowCut, highCut)

    def updatePlotting(self, frameNumber, vicon):
        """
        Update all plot series with data from the current frame.
        
        This method orchestrates the addition of both angle and device data to the chart.
        It checks if a subject exists before attempting to plot angle data.
        
        Args:
            frameNumber (int): Current frame number for X-axis positioning
            vicon (ViconWrapper): Vicon data source containing subject and device data
        """
        # Add angle data if a subject is present
        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.addAnglesToPlot(frameNumber, activeSubject)
            
        # Add device data
        self.addDeviceDataToPlot(frameNumber, vicon)
        
        # Finalize the frame update
        self.myChart.finalize()

    def addAnglesToPlot(self, frameNumber, activeSubject):
        """
        Add angle data points to the chart series.
        
        Only adds data for angles that are selected (angleFlags = True) and have
        valid data available in the subject's kinematics dictionary.
        
        Args:
            frameNumber (int): Current frame number for X-axis positioning
            activeSubject (Subject): Subject object containing kinematic data
        """
        # Add first angle if selected and available
        if self.Angle1 != "":
            # Check if angle is enabled and has valid data
            if self.Angle1[1:] in activeSubject.kinematics.angleFlags and activeSubject.kinematics.angleFlags[self.Angle1[1:]]:
                self.myChart.addData(1, frameNumber, activeSubject.kinematics.anglesDictionary[self.Angle1])
        
        # Add second angle if selected and available
        if self.Angle2 != "":
            if self.Angle2[1:] in activeSubject.kinematics.angleFlags and activeSubject.kinematics.angleFlags[self.Angle2[1:]]:
                self.myChart.addData(2, frameNumber, activeSubject.kinematics.anglesDictionary[self.Angle2])

    def addDeviceDataToPlot(self, frameNumber, vicon):
        """
        Add device data points to the chart series.
        
        Applies filtering to device data before plotting. Handles multiple data points
        per frame (e.g., when device sampling rate exceeds mocap frame rate).
        
        Args:
            frameNumber (int): Current frame number for X-axis positioning
            vicon (ViconWrapper): Vicon data source containing device data
        """
        # Validate device data selection
        if self.deviceData == ['','',''] or self.deviceData == ['None', 'None', 'None'] or self.deviceData == []:
            return
        
        # Check if device exists in the system
        if self.deviceData[0] not in vicon.devices:
            return
        
        # Check that the device is online and streaming
        if not vicon.devices[self.deviceData[0]]["Online"]:
            return
        
        # Get device data values for current frame
        data = vicon.devices[self.deviceData[0]]["Data"][self.deviceData[1]][self.deviceData[2]]['values'][0]
        
        # Apply filtering and add each data point to chart
        # Interpolate X-axis position for multiple samples per frame
        for i in range(len(data)):
            data[i] = self.deviceFilter.filter(data[i])
            self.myChart.addData(3, frameNumber - 1 + i/len(data), data[i])

# ============================================================================
# DATA EXPORT MANAGEMENT
# ============================================================================

class Exporting:
    """
    Manages data recording and CSV export functionality.
    
    This class handles three recording modes:
        1. Manual: User-controlled start/stop recording
        2. Duration: Timed recording for specified duration
        3. Window: Records data for the duration of the plot window
    
    Supports exporting both joint angle data and device channel data to separate
    CSV files with automatic file naming and indexing.
    
    Attributes:
        angleExportList (list): List of angle names to export (e.g., ['Hip', 'Knee'])
        angleExportFrame (DataFrame): Accumulated angle data for current recording
        deviceExportList (list): List of [device, channel] pairs to export
        deviceExportFrames (dict): Accumulated device data, keyed by "device:channel"
        isRecording (bool): Current recording state
        savingIndex (int): Manual file index for non-auto naming
        savingAutoIndex (bool): Enable automatic file index incrementing
        filename (str): Base filename for exported files
        saveAllDeviceData (bool): If True, export all samples; if False, export last sample only
        savePath (str): Directory path for exported files
        recordingStartTime (float): Timestamp when recording started (seconds)
        recordingDuration (float): Target duration for timed recording (seconds)
        
    Methods:
        startTimedRecording(): Begins a duration-based recording
        saveDataToCSV(): Exports accumulated data to CSV files
        updateExporting(): Processes current frame data during recording
        addAnglesToExport(): Adds angle data to export buffer
        addDeviceDataToExport(): Adds device data to export buffer
    """
    
    def __init__(self):
        """Initialize the data export system with default settings."""
        # Data collection buffers
        self.angleExportList = []  # List of angle names to export
        self.angleExportFrame = pd.DataFrame()  # Accumulated angle data

        self.deviceExportList = []  # List of [device, channel] pairs to export
        self.deviceExportFrames = {}  # Dict with keys "device:channel"

        # Recording control flags
        self.isRecording = False
        self.savingIndex = 0  # Manual file index
        self.savingAutoIndex = True  # Enable automatic index incrementing
        self.filename = "Recording"
        self.saveAllDeviceData = False  # Export all samples vs. last sample only
        
        # Default export path is the current directory
        self.savePath = os.path.dirname(os.path.realpath(__name__))

        # Timed recording parameters
        self.recordingStartTime = 0  # Start timestamp in seconds
        self.recordingDuration = 0  # Target duration in seconds

    def startTimedRecording(self, duration):
        """
        Start a timed recording session.
        
        Args:
            duration (float): Recording duration in seconds
        """
        self.isRecording = True
        self.recordingDuration = duration
        self.recordingStartTime = time.time()

    def saveDataToCSV(self):
        """
        Export accumulated data to CSV files.
        
        Creates separate CSV files for angle data and each device/channel combination.
        Implements automatic file indexing to prevent overwriting existing files.
        Files are named as: {filename}_angles[_index].csv and {filename}_{device}_{channel}[_index].csv
        
        The method clears all data buffers after successful export.
        """
        name = self.filename
        fullSavePath = ""
        
        # ---- Export angle data ----
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
        """
        Process current frame data during an active recording session.
        
        Checks if timed recording has completed, and if so, stops recording and saves data.
        Collects angle and device data from the current frame and adds to export buffers.
        
        Args:
            frameNumber (int): Current frame number
            vicon (ViconWrapper): Vicon data source containing subject and device data
        """
        # Check if timed recording duration has elapsed
        if time.time() - self.recordingStartTime >= self.recordingDuration and self.recordingDuration != 0:
            self.isRecording = False
            self.saveDataToCSV()
            addToLog("Recording Stopped")
            addToLog("Files Saved To: " + self.savePath)

        # Collect angle data if subject exists
        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.addAnglesToExport(frameNumber, activeSubject)
        
        # Collect device data
        self.addDeviceDataToExport(frameNumber, vicon)

    def addAnglesToExport(self, frameNumber, activeSubject):
        """
        Add current frame's angle data to the export buffer.
        
        Collects left and right side angles for all selected angles from the subject's
        kinematics dictionary and appends them to the angle export DataFrame.
        
        Args:
            frameNumber (int): Current frame number
            activeSubject (Subject): Subject object containing kinematic data
        """
        # Create new row with frame number
        new_row_dict = {'Frame': [frameNumber]}
        
        # Add left and right angles for each selected angle type
        for angle in self.angleExportList:
            new_row_dict['L'+angle] = [activeSubject.kinematics.anglesDictionary['L'+angle]]
            new_row_dict['R'+angle] = [activeSubject.kinematics.anglesDictionary['R'+angle]]

        # Append to DataFrame
        new_row = pd.DataFrame(new_row_dict)
        self.angleExportFrame = pd.concat([self.angleExportFrame, new_row], ignore_index=True)

    def addDeviceDataToExport(self, frameNumber, vicon):
        """
        Add current frame's device data to the export buffer.
        
        Handles two export modes:
            - saveAllDeviceData=True: Exports all samples in the frame (for high-rate devices)
            - saveAllDeviceData=False: Exports only the last sample per frame
        
        Args:
            frameNumber (int): Current frame number
            vicon (ViconWrapper): Vicon data source containing device data
        """
        for deviceName, channel in self.deviceExportList:
            # Get all component names for this device/channel
            listOfComponents = list(vicon.devices[deviceName]["Data"][channel].keys())
            listOfComponents.remove("Online")  # Remove the status flag

            # Initialize DataFrame for this device/channel if not exists
            if f"{deviceName}:{channel}" not in self.deviceExportFrames:
                self.deviceExportFrames[f"{deviceName}:{channel}"] = pd.DataFrame()

            # Export mode: Save all samples per frame (for high sampling rate devices)
            if self.saveAllDeviceData:
                # Iterate through all samples in current frame
                for i in range(len(vicon.devices[deviceName]["Data"][channel][listOfComponents[0]]['values'][0])):
                    # Interpolate frame number for sub-frame timing
                    new_dict_row = {'Frame': [frameNumber-1+i/len(vicon.devices[deviceName]["Data"][channel][listOfComponents[0]]['values'][0])]}
                    
                    # Add each component's value for this sample
                    for component in listOfComponents:
                        new_dict_row[component] = [vicon.devices[deviceName]["Data"][channel][component]['values'][0][i]]
                    
                    new_row = pd.DataFrame(new_dict_row)
                    self.deviceExportFrames[f"{deviceName}:{channel}"] = pd.concat([self.deviceExportFrames[f"{deviceName}:{channel}"], new_row], ignore_index=True)
            
            # Export mode: Save only the last sample per frame
            else:
                new_dict_row = {'Frame': [frameNumber]}
                
                # Add each component's last value
                for component in listOfComponents:
                    new_dict_row[component] = [vicon.devices[deviceName]["Data"][channel][component]['values'][0][-1]]
                
                new_row = pd.DataFrame(new_dict_row)
                self.deviceExportFrames[f"{deviceName}:{channel}"] = pd.concat([self.deviceExportFrames[f"{deviceName}:{channel}"], new_row], ignore_index=True)

# ============================================================================
# UDP STREAMING SYSTEM
# ============================================================================

class Streaming:
    """
    Manages UDP streaming of real-time data to external applications.
    
    Streams data packets over UDP containing joint angles and device measurements.
    Each data point is sent as a fixed-size packet with format:
        [Label (variable length) | Padding (spaces) | Value (fixed length) | '$' terminator]
    
    Supports optional filtering of device data before transmission.
    
    Attributes:
        sock (socket): UDP socket for data transmission
        UDPErrorCount (int): Consecutive transmission error counter
        IsStreamingUDP (bool): Current streaming state
        UDPHost (str): Target IP address
        UDPPort (int): Target port number
        packetSize (int): Total packet size in bytes (excluding terminator)
        valueSize (int): Size allocated for numerical value in packet
        deviceStreamList (list): List of [device, channel, component] to stream
        angleStreamList (list): List of angle names to stream (e.g., 'LHip', 'RKnee')
        deviceFilterList (dict): Filter objects keyed by "device:channel:component"
        filterType (str): Type of filter to apply to device data
        windowSize (int): Filter window size
        sampleRate (float): Data sampling rate in Hz
        lowCut (float): Low-frequency cutoff for bandpass filter
        highCut (float): High-frequency cutoff for bandpass filter
        
    Methods:
        updateDeviceFilterType(): Reconfigure device data filters
        updateStream(): Send current frame data over UDP
        sendAngleOverUDP(): Transmit angle data packets
        sendDeviceDataOverUDP(): Transmit device data packets
        sendOverUDP(): Low-level packet transmission
        startUDPStream(): Initialize UDP socket and begin streaming
        stopUDPStream(): Close socket and end streaming
    """
    
    def __init__(self, targetIP = "127.0.0.1", port = 5005):
        """
        Initialize the UDP streaming system.
        
        Args:
            targetIP (str): Target IP address (default: localhost)
            port (int): Target port number (default: 5005)
        """
        # UDP socket configuration
        self.sock = []  # Will hold socket object when streaming
        self.UDPErrorCount = 0
        self.IsStreamingUDP = False
        self.UDPHost = targetIP
        self.UDPPort = port

        # Packet format configuration
        self.packetSize = 50  # Total packet size excluding terminator
        self.valueSize = 10  # Size allocated for numerical value
        
        # Data selection for streaming
        self.deviceStreamList = []  # Format: [device, channel, component]
        self.angleStreamList = []  # Format: 'LHip', 'RKnee', etc.

        # Filter configuration for device data
        self.filterType = "none"
        self.windowSize = 101
        self.sampleRate = 100
        self.lowCut = .01
        self.highCut = 29

        # Filter instances for each device stream
        self.deviceFilterList = {}

    def updateDeviceFilterType(self, windowSize, sampleRate, filterType, lowCut, highCut):
        """
        Update filter configuration for all device streams.
        
        Reinitializes all device filters with new parameters. Existing filter states are reset.
        
        Args:
            windowSize (int): Number of samples in filter window
            sampleRate (float): Sampling frequency in Hz
            filterType (str): Type of filter ('none', 'bandpass', 'moving_average', 'moving_median')
            lowCut (float): Lower cutoff frequency for bandpass filter (Hz)
            highCut (float): Upper cutoff frequency for bandpass filter (Hz)
        """
        # Store filter parameters
        self.filterType = filterType
        self.windowSize = windowSize
        self.sampleRate = sampleRate
        self.lowCut = lowCut
        self.highCut = highCut

        # Reset and reinitialize all filters
        self.deviceFilterList = {}
        for deviceName, channel, component in self.deviceStreamList:
            deviceLabel = deviceName + ":" + channel + ":" + component
            self.deviceFilterList[deviceLabel] = filters.MyFilter(windowSize, sampleRate, filterType, lowCut, highCut)

    def updateStream(self, vicon):
        """
        Send current frame data over UDP.
        
        Transmits angle data if a subject is present, followed by device data.
        Only operates when streaming is active.
        
        Args:
            vicon (ViconWrapper): Vicon data source containing subject and device data
        """
        if not self.IsStreamingUDP:
            return
        
        # Send angle data if subject exists
        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.sendAngleOverUDP(activeSubject)
        
        # Send device data
        self.sendDeviceDataOverUDP(vicon)


    def sendAngleOverUDP(self, activeSubject):
        """
        Transmit angle data packets over UDP.
        
        Creates and sends one packet per angle. Packet format:
            [AngleName | Padding | AngleValue | '$']
        
        Args:
            activeSubject (Subject): Subject containing kinematic data
        """
        for angle in self.angleStreamList:
            angleName = angle
            angleNameSize = len(angleName)
            angleValue = activeSubject.kinematics.anglesDictionary[angle]
            
            # Convert angle value to fixed-length string
            angleValue = str(angleValue)
            angleValue = angleValue[:self.valueSize]
            
            # Pad with zeros if shorter than valueSize
            if len(angleValue) < self.valueSize:
                angleValue = angleValue + "0"*(self.valueSize-len(angleValue))

            # Create packet with spaces for padding
            packet = " "*self.packetSize

            # Insert angle name at beginning
            packet = angleName + packet[angleNameSize:]
            
            # Insert value at end of packet (before terminator)
            packet = packet[:self.packetSize-self.valueSize] + angleValue
            
            # Add terminator
            packet = packet + "$"

            # Send the packet
            self.sendOverUDP(packet)


              



    def sendDeviceDataOverUDP(self, vicon):
        """
        Transmit device data packets over UDP.
        
        Creates and sends one packet per device/channel/component. Packet format:
            [DeviceLabel | Padding | DataValue | '$']
        where DeviceLabel = "Device:Channel:Component"
        
        Args:
            vicon (ViconWrapper): Vicon data source containing device data
        """
        for deviceName, channel, component in self.deviceStreamList:
            # Create composite label for device data
            deviceLabel = deviceName + ":" + channel + ":" + component
            deviceLabelSize = len(deviceLabel)

            # Get the most recent data value
            deviceData = vicon.devices[deviceName]["Data"][channel][component]['values'][0][-1]
            
            # Convert to fixed-length string
            deviceData = str(deviceData)
            deviceData = deviceData[:self.valueSize]
            
            # Pad with zeros if shorter than valueSize
            if len(deviceData) < self.valueSize:
                deviceData = deviceData + "0"*(self.valueSize-len(deviceData))

            # Create packet with spaces for padding
            packet = " "*self.packetSize

            # Insert device label at beginning
            packet = deviceLabel + packet[deviceLabelSize:]
            
            # Insert value at end of packet (before terminator)
            packet = packet[:self.packetSize-self.valueSize] + deviceData

            # Add terminator
            packet = packet + "$"

            # Send the packet
            self.sendOverUDP(packet)

    def sendOverUDP(self, data):
        """
        Low-level UDP packet transmission.
        
        Handles error counting and automatic stream shutdown after 3 consecutive failures.
        
        Args:
            data (str): Packet string to transmit
        """
        try:
            # Convert string to bytes for transmission
            data = data.encode('utf-8')

            # Send via UDP socket
            self.sock.sendto(data, (self.UDPHost, self.UDPPort))
            self.UDPErrorCount = 0

        except:
            self.UDPErrorCount += 1
            addToLog(f"Error Sending Data Over UDP - attempt {self.UDPErrorCount}")

            # Stop streaming after 3 consecutive errors
            if self.UDPErrorCount >= 3:
                self.stopUDPStream()

    def startUDPStream(self):
        """
        Initialize UDP socket and begin streaming.
        
        Creates a new UDP socket and sets the streaming flag.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.IsStreamingUDP = True
        addToLog("UDP Streaming Started")

    def stopUDPStream(self):
        """
        Close UDP socket and end streaming.
        
        Closes the socket and clears the streaming flag.
        """
        self.IsStreamingUDP = False
        self.sock.close()
        addToLog("UDP Streaming Stopped")
    
# ============================================================================
# VISUAL FEEDBACK SYSTEM
# ============================================================================

class Feedback:
    """
    Manages real-time visual feedback display for biofeedback applications.
    
    Displays a single data value on a visual feedback graph with configurable
    target ranges. Can display either a single angle or a single device measurement.
    
    Attributes:
        feedbackGraph (FeedbackGraph): Visual feedback widget
        currentValue (float): Current value being displayed
        deviceFeedbackList (list): List of [device, channel, component] for feedback
        angleFeedbackList (list): List of angle names for feedback (e.g., 'LHip')
        
    Methods:
        updateFeedback(): Update feedback display with current frame data
        updateAnglesFeedback(): Process angle data for feedback
        updateDeviceDataFeedback(): Process device data for feedback
        setCurrentValue(): Update the displayed value
    
    Note:
        Only one value (angle or device) should be selected at a time for feedback.
    """
    
    def __init__(self, feedbackGraph):
        """
        Initialize the feedback system.
        
        Args:
            feedbackGraph (FeedbackGraph): Visual feedback widget
        """
        self.feedbackGraph = feedbackGraph
        self.currentValue = 0
        self.negated = False

        # Data selections for feedback (should be mutually exclusive)
        self.deviceFeedbackList = []  # Format: [device, channel, component]
        self.angleFeedbackList = []  # Format: 'LHip', 'RKnee', etc.

    def updateFeedback(self, vicon):
        """
        Update feedback display with current frame data.
        
        Checks both angle and device lists and updates the display with
        the first available data source.
        
        Args:
            vicon (ViconWrapper): Vicon data source
        """
        # Skip if no feedback sources are selected
        if self.deviceFeedbackList == [] and self.angleFeedbackList == []:
            return
        
        # Update angle feedback if subject exists
        if vicon.subjectExists():
            activeSubject = vicon.getSubject(vicon.subjects[0].name)
            self.updateAnglesFeedback(activeSubject)
        
        # Update device feedback
        self.updateDeviceDataFeedback(vicon)

    def updateAnglesFeedback(self, activeSubject):
        """
        Update feedback display with angle data.
        
        Args:
            activeSubject (Subject): Subject containing kinematic data
        """
        for angle in self.angleFeedbackList:
            angleValue = activeSubject.kinematics.anglesDictionary[angle]
            self.setCurrentValue(angleValue)

    def updateDeviceDataFeedback(self, vicon):
        """
        Update feedback display with device data.
        
        Args:
            vicon (ViconWrapper): Vicon data source containing device data
        """
        for deviceName, channel, component in self.deviceFeedbackList:
            deviceData = vicon.devices[deviceName]["Data"][channel][component]['values'][0][-1]
            self.setCurrentValue(deviceData)

    def setCurrentValue(self, value):
        """
        Update the displayed value on the feedback graph.
        
        Args:
            value (float): New value to display
        """
        if self.negated:
            value = -value
        self.currentValue = value
        self.feedbackGraph.setCurrentValue(self.currentValue)

# ============================================================================
# MAIN PROCESSING LOOP
# ============================================================================

class MainTask:
    """
    Core processing loop coordinating all application subsystems.
    
    This class orchestrates the real-time data flow from Vicon through filtering,
    visualization, export, streaming, and feedback systems. Runs continuously at
    approximately 1000 Hz to minimize latency.
    
    Subsystems managed:
        - Plotting: Real-time visualization
        - Exporting: Data recording to CSV
        - Streaming: UDP transmission to external apps
        - Feedback: Visual biofeedback display
    
    Attributes:
        frame_count (int): Frame counter for FPS calculation
        start_time (float): Timestamp for FPS calculation
        activeSubject (Subject): Currently tracked subject
        filterType (str): Type of angle filter
        filterWindow (int): Angle filter window size
        filterLowCut (float): Angle filter low cutoff (Hz)
        filterHighCut (float): Angle filter high cutoff (Hz)
        filterSampleRate (float): Angle filter sample rate (Hz)
        setFilterFlag (bool): Flag to trigger filter reconfiguration
        plotting (Plotting): Visualization subsystem
        maxFrames (int): Plot window size in frames
        exporting (Exporting): Data export subsystem
        windowRecordingMode (bool): True when window recording is active
        pendingWindowData (bool): True when window recording is pending
        streaming (Streaming): UDP streaming subsystem
        feedback (Feedback): Visual feedback subsystem
        lastViconFrame (int): Previous Vicon frame number
        currentViconFrame (int): Current Vicon frame number
        
    Methods:
        runFrame(): Process one frame of data through all subsystems
        tickFPS(): Update FPS displays
        zeroSubjectAngles(): Zero the current joint angles
    """
    
    def __init__(self):
        """Initialize the main processing loop and all subsystems."""
        # FPS calculation
        self.frame_count = 0
        self.start_time = time.time()

        # Subject tracking
        self.activeSubject = None

        # Angle filter configuration
        self.filterType = "none"
        self.filterWindow = 101
        self.filterLowCut = .01
        self.filterHighCut = 29
        self.filterSampleRate = 100
        self.setFilterFlag = False  # Trigger for filter update

        # Initialize subsystems
        self.plotting = Plotting(myChart)
        self.maxFrames = 1000  # Plot window size

        self.exporting = Exporting()
        self.windowRecordingMode = False  # Window recording active
        self.pendingWindowData = False  # Window recording pending

        self.streaming = Streaming()

        self.feedback = Feedback(feedbackGraph)

        # Frame tracking for plot clearing
        self.lastViconFrame = 0
        self.currentViconFrame = 0

    def runFrame(self):
        """
        Process one frame of data through all subsystems.
        
        This method is called continuously by the Qt timer (~1000 Hz) and:
        1. Retrieves latest frame from Vicon
        2. Updates active subject and applies filters if needed
        3. Routes data to plotting, exporting, streaming, and feedback
        4. Manages window recording mode
        5. Updates FPS displays
        6. Processes Qt events
        
        The method handles frame rollover for continuous plotting and manages
        the window recording start/stop logic.
        """
        global vicon

        # Get latest frame from Vicon
        vicon.updateFrame()
        start_time = time.time()

        # Track frame numbers for plot clearing
        self.lastViconFrame = self.currentViconFrame
        self.currentViconFrame = vicon.frameNumber

        # Clear plot when frame counter rolls over
        if self.lastViconFrame%self.maxFrames > self.currentViconFrame%self.maxFrames:
            print("Clearing Plot")
            self.plotting.clearAll()

        # Handle window recording mode (triggered by frame rollover)
        if vicon.lastFrameNumber > vicon.frameNumber:
            # Stop window recording if active
            if self.exporting.isRecording and self.windowRecordingMode:
                self.windowRecordingMode = False
                self.exporting.isRecording = False
                self.exporting.saveDataToCSV()
                addToLog("Recording Stopped")
                addToLog("Files Saved To: " + self.exporting.savePath)

            # Start window recording if pending
            if self.windowRecordingMode and self.pendingWindowData:
                self.pendingWindowData = False
                self.exporting.isRecording = True
                addToLog("Recording Started")

        # Update active subject and apply filter changes
        if vicon.subjectExists():
            self.activeSubject = vicon.getSubject(vicon.subjects[0].name)

            # Apply new filter configuration if requested
            if self.setFilterFlag:
                self.setFilterFlag = False
                self.activeSubject.kinematics.setFilter(self.filterWindow, self.filterSampleRate, 
                                                       self.filterType, self.filterLowCut, self.filterHighCut)
        else:
            self.activeSubject = None

        # Update all subsystems with current frame data
        self.plotting.updatePlotting(vicon.frameNumber % self.maxFrames, vicon)
        
        if self.exporting.isRecording:
            self.exporting.updateExporting(vicon.frameNumber, vicon)
        
        if self.streaming.IsStreamingUDP:
            self.streaming.updateStream(vicon)

        if self.feedback.deviceFeedbackList != [] or self.feedback.angleFeedbackList != []:
            self.feedback.updateFeedback(vicon)

        # Calculate and update FPS
        dt = time.time() - start_time
        if dt == 0:
            dt = .001
        self.frame_count += 1
        if(self.frame_count >= 100):
            self.frame_count = 0
            self.tickFPS(dt)


        # Schedule next frame AFTER Qt processes all pending events (QTimer internally calls app.processEvents())
        QTimer.singleShot(0, self.runFrame)

    def tickFPS(self, dt):
        """
        Update FPS displays in the GUI.
        
        Args:
            dt (float): Time delta for FPS calculation
        """
        global vicon

        updateMainLoopFPS(int(1.0 / dt))
        updateViconStreamFPS(int(vicon.localFPS))

    def zeroSubjectAngles(self):
        """
        Zero all joint angles for the active subject.
        
        Records the current joint angles as the new zero reference.
        Useful for calibration or relative angle measurements.
        """
        if self.activeSubject != None:
            self.activeSubject.kinematics.recordZeroPosition()


# ============================================================================
# GLOBAL APPLICATION OBJECTS
# ============================================================================

# Core application objects (initialized in setupGUI)
app = None                  # Qt Application instance
Main = None                 # MainTask instance (core processing loop)
ui = None                   # Main window UI (Ui_MainWindow)
ui2 = None                  # Feedback window UI (Ui_Form)
vicon = None                # ViconWrapper instance (data source)

# Visualization widgets
myChart = None              # MyCharting instance (OpenGL plot widget)
feedbackGraph = None        # FeedbackGraph instance (visual feedback)

# Device filter parameters (separate from angle filters)
deviceFilterType = "none"
deviceFilterWindow = 101
deviceFilterLowCut = .01
deviceFilterHighCut = 29
deviceFilterSampleRate = 100
deviceSetFilterFlag = False

# ============================================================================
# DEVICE SELECTION FUNCTIONS
# ============================================================================

def updateViconDeviceTreeStatus(item):
    """
    Toggle device/channel online status when tree item is double-clicked.
    
    Handles both device-level and channel-level toggling:
    - Device toggle: Enables/disables all channels
    - Channel toggle: Enables/disables individual channel (and parent device if needed)
    
    Args:
        item (QTreeWidgetItem): The tree item that was double-clicked
    """
    global vicon, ui

    # Determine if this is a channel (child) or device (parent)
    isChild = item.childCount() == 0

    # Special case: Humac is treated as a device even if it has no children
    if item.text(0) == "Humac":
        isChild = False

    if isChild:
        # Toggle channel status
        vicon.devices[item.parent().text(0)]["Data"][item.text(0)]["Online"] = not vicon.devices[item.parent().text(0)]["Data"][item.text(0)]["Online"]
        
        # If channel is now online, ensure parent device is also online
        if vicon.devices[item.parent().text(0)]["Data"][item.text(0)]["Online"]:
            vicon.devices[item.parent().text(0)]["Online"] = True

    else:
        # Toggle device status
        vicon.devices[item.text(0)]["Online"] = not vicon.devices[item.text(0)]["Online"]
        
        # Update all channels to match device status
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

# ============================================================================
# ANGLE SELECTION FUNCTIONS
# ============================================================================

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


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def addToLog(text):
    """
    Add a message to the application log display.
    
    Args:
        text (str): Message to log
    """
    global ui
    ui.plainTextEdit.appendPlainText(text)

def updateMainLoopFPS(fps):
    """
    Update the main loop FPS display.
    
    Args:
        fps (int): Frames per second value
    """
    global ui
    ui.lblFPS.setText(f'FPS {fps:10.2f}')

def updateViconStreamFPS(fps):
    """
    Update the Vicon stream FPS display.
    
    Args:
        fps (int): Frames per second value
    """
    global ui
    ui.lblViconFPS.setText(f'FPS {fps:10.2f}') 

# ============================================================================
# CHART CONTROL FUNCTIONS
# ============================================================================

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

# ============================================================================
# FILTER CONFIGURATION FUNCTIONS
# ============================================================================

def setFilterType(filterType):
    """
    Configure the angle data filter.
    
    Updates the filter configuration for joint angle data and displays
    the current filter settings in the UI.
    
    Args:
        filterType (str): Type of filter ('none', 'bandpass', 'moving_average', 'moving_median')
    """
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

def setDeviceFilterType(filterType):
    global deviceFilterType, deviceFilterWindow, deviceFilterLowCut, deviceFilterHighCut, deviceFilterSampleRate, deviceSetFilterFlag, ui
    global Main
    deviceFilterType = filterType
    deviceFilterWindow = ui.spinDeviceFilterSize.value()
    deviceFilterLowCut = ui.spinDeviceFilterLowcut.value()
    deviceFilterHighCut = ui.spinDeviceFilterHighcut.value()
    deviceFilterSampleRate = ui.spinDeviceFilterSampleRate.value()


    filterMessage = f"{deviceFilterType}"
    if filterType == "bandpass":
        filterMessage = f"{deviceFilterType} - [{deviceFilterLowCut},{deviceFilterHighCut}] Hz, Size {deviceFilterWindow}, Sample Rate {deviceFilterSampleRate}"
    elif filterType == "moving_average":
        filterMessage = f"{deviceFilterType} - Size {deviceFilterWindow}, Sample Rate {deviceFilterSampleRate}"
    elif filterType == "moving_median":
        filterMessage = f"{deviceFilterType} - Size {deviceFilterWindow}, Sample Rate {deviceFilterSampleRate}"

    ui.lblDeviceFilterIndec.setText(filterMessage)

    Main.plotting.updateDeviceFilterType(deviceFilterWindow, deviceFilterSampleRate, deviceFilterType, deviceFilterLowCut, deviceFilterHighCut)
    # Main.streaming.updateDeviceFilterType(deviceFilterWindow, deviceFilterSampleRate, deviceFilterType, deviceFilterLowCut, deviceFilterHighCut)

    deviceSetFilterFlag = True

# ============================================================================
# EXPORT MANAGEMENT FUNCTIONS
# ============================================================================

def updateExportTable():
    """
    Refresh the export table with current device and angle selections.
    
    Populates the export table UI with all currently enabled devices and angles.
    This table shows what data will be recorded when exporting starts.
    """
    global ui, Main, vicon

    # Reset export lists
    Main.exporting.deviceExportList = []  # Format: [device, channel]
    Main.exporting.angleExportList = []  # Format: [angle]


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

def updateFeedbackTable():
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


    ui.tableFeedback.clear()
    ui.tableFeedback.setRowCount(max(len(rawAngleStreamList), len(rawDeviceStreamList)))
    ui.tableFeedback.setColumnCount(2)
    #stretch the columns
    ui.tableFeedback.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
    ui.tableFeedback.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    #name the columns
    ui.tableFeedback.setHorizontalHeaderLabels(["Angles", "Devices"])
    
    #fill the table
    for i in range(max(len(rawAngleStreamList), len(rawDeviceStreamList))):
        if i < len(rawAngleStreamList):
            ui.tableFeedback.setItem(i, 0, QTableWidgetItem(rawAngleStreamList[i]))
        if i < len(rawDeviceStreamList):
            ui.tableFeedback.setItem(i, 1, QTableWidgetItem(f"{rawDeviceStreamList[i][0]}:{rawDeviceStreamList[i][1]}:{rawDeviceStreamList[i][2]}"))

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
    elif tabName == "Feedback":
        updateFeedbackTable()

def updateSavingParameters():
    global Main, ui
    Main.exporting.filename = ui.txtFilename.text()
    Main.exporting.savingIndex = ui.spinSavingIndex.value()
    Main.exporting.savingAutoIndex = ui.checkSavingAutoIndex.isChecked()
    Main.exporting.saveAllDeviceData = ui.checkSaveAllDeviceData.isChecked()

    print(Main.exporting.filename, Main.exporting.savingIndex, Main.exporting.savingAutoIndex, Main.exporting.saveAllDeviceData)

# ============================================================================
# UDP STREAMING FUNCTIONS
# ============================================================================

def startEndStream():
    """
    Toggle UDP streaming on/off.
    
    Starts or stops UDP streaming based on current state. When starting,
    validates and applies packet configuration from UI.
    """
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
    Main.streaming.deviceFilterList = {} #ex "itemName"
    Main.streaming.angleStreamList = [] #ex [Side]+[angle] LHip
    for item in selectedItems:
        if item.column() == 0:
            Main.streaming.angleStreamList.append(item.text())
        elif item.column() == 1:
            device, channel, component = item.text().split(":")
            Main.streaming.deviceStreamList.append([device, channel, component])
            Main.streaming.deviceFilterList[f"{device}:{channel}:{component}"] = filters.MyFilter(Main.streaming.windowSize, Main.streaming.sampleRate, Main.streaming.filterType, Main.streaming.lowCut, Main.streaming.highCut)

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

# ============================================================================
# FEEDBACK CONFIGURATION FUNCTIONS
# ============================================================================

def feedbackTableSelectionChanged():
    """
    Handle changes to feedback data selection.
    
    Updates the feedback system with newly selected angles or device data
    from the feedback table.
    """
    global ui, Main
    
    selectedItems = ui.tableFeedback.selectedItems()
    print(selectedItems)

    # Update feedback data selections
    Main.feedback.deviceFeedbackList = [] #ex [device][channel][component]
    Main.feedback.angleFeedbackList = [] #ex [Side]+[angle] LHip
    for item in selectedItems:
        if item.column() == 0:
            Main.feedback.angleFeedbackList.append(item.text())
        elif item.column() == 1:
            device, channel, component = item.text().split(":")
            Main.feedback.deviceFeedbackList.append([device, channel, component])

    print(Main.feedback.angleFeedbackList)
    print(Main.feedback.deviceFeedbackList)

    feedbackGraph.toggleVisible(len(Main.feedback.angleFeedbackList) > 0 or len(Main.feedback.deviceFeedbackList) > 0)

def feedbackRangesChanged():
    global ui, Main, feedbackGraph

    feedbackGraph.setTotalRange(ui.spinFeedbackMin.value(), ui.spinFeedbackMax.value())
    feedbackGraph.setRegionRange(ui.spinFeedbackRegionMin.value(), ui.spinFeedbackRegionMax.value())

def feedbackNegateChanged():
    global ui, Main, feedbackGraph
    Main.feedback.negated = ui.btnPushReverseFeedbackSignal.isChecked()
    print(Main.feedback.negated)
# ============================================================================
# APPLICATION LIFECYCLE FUNCTIONS
# ============================================================================

def closingEvent():
    """
    Handle application shutdown.
    
    Ensures clean shutdown of Vicon stream and UDP streaming before exit.
    """
    global vicon, Main
    print("Closing Event")
    vicon.stopStream()
    Main.streaming.stopUDPStream()
    

def setupGUI():
    """
    Initialize and configure the GUI and all application components.
    
    This function:
    1. Creates the Qt application and windows
    2. Initializes visualization widgets (chart, feedback)
    3. Creates the MainTask processing loop
    4. Configures all UI connections and event handlers
    5. Starts the main processing timer
    6. Launches the application event loop
    
    The function does not return until the application is closed.
    """
    global myChart, Main, vicon, ui, feedbackGraph, app

    # Initialize Qt application
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Vicon Data Viewer")
    app.setApplicationDisplayName("Vicon Data Viewer")
    app.setApplicationVersion("1.0")

    


    MainWindow = QMainWindow()
    MainWindow.setWindowTitle("Vicon Data Viewer")
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()

    SideWindow = QWidget(None, Qt.WindowType.Window)
    # Make window non-resizable, minimizable, but not closable
    SideWindow.setWindowFlags(Qt.WindowType.Window | 
                              Qt.WindowType.CustomizeWindowHint | 
                              Qt.WindowType.WindowTitleHint | 
                              Qt.WindowType.WindowMinimizeButtonHint | 
                              Qt.WindowType.WindowMaximizeButtonHint )
    ui2 = Ui_Form()
    ui2.setupUi(SideWindow)
    SideWindow.show()

    


    feedbackMax = 100
    feedbackRegionMax = 50
    feedbackValue = 0
    feedbackRegionMin = -50
    feedbackMin = -100

    feedbackGraph = FeedbackGraph(feedbackMax, feedbackRegionMax, feedbackValue, feedbackRegionMin, feedbackMin)
    ui2.panFeedbackPlot.addWidget(feedbackGraph.plotWidget)
    ui.spinFeedbackMax.setValue(feedbackMax)
    ui.spinFeedbackRegionMax.setValue(feedbackRegionMax)
    ui.spinFeedbackRegionMin.setValue(feedbackRegionMin)
    ui.spinFeedbackMin.setValue(feedbackMin)

    
    myChart = MyCharting()
    ui.horizontalLayout.addWidget(myChart.chartView)

    Main = MainTask()

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


    for filter in filters.FilterTypes:
        ui.comboDeviceFilterType.addItem(filter)
    ui.comboDeviceFilterType.currentIndexChanged.connect(lambda: setDeviceFilterType(ui.comboDeviceFilterType.currentText()))
    ui.spinDeviceFilterSize.valueChanged.connect(lambda: setDeviceFilterType(ui.comboDeviceFilterType.currentText()))
    ui.spinDeviceFilterLowcut.valueChanged.connect(lambda: setDeviceFilterType(ui.comboDeviceFilterType.currentText()))
    ui.spinDeviceFilterHighcut.valueChanged.connect(lambda: setDeviceFilterType(ui.comboDeviceFilterType.currentText()))
    ui.spinDeviceFilterSampleRate.valueChanged.connect(lambda: setDeviceFilterType(ui.comboDeviceFilterType.currentText()))





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

    ui.spinFeedbackMax.valueChanged.connect(lambda: feedbackRangesChanged())
    ui.spinFeedbackRegionMax.valueChanged.connect(lambda: feedbackRangesChanged())
    ui.spinFeedbackRegionMin.valueChanged.connect(lambda: feedbackRangesChanged())
    ui.spinFeedbackMin.valueChanged.connect(lambda: feedbackRangesChanged())

    ui.tableFeedback.itemSelectionChanged.connect(lambda: feedbackTableSelectionChanged())
    ui.btnPushReverseFeedbackSignal.clicked.connect(lambda: feedbackNegateChanged())

    #add closing event
    app.aboutToQuit.connect(lambda: closingEvent())


    QTimer.singleShot(0, Main.runFrame)
    sys.exit(app.exec())




# ============================================================================
# APPLICATION ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    """
    Application entry point.
    
    Initializes the Vicon connection and launches the GUI.
    Configure the Vicon host address before running.
    """
    # Vicon system configuration
    # Update this IP:port to match your Vicon system
    host = "141.217.165.179:801"
    
    # Initialize Vicon connection
    vicon = ViconWrapper(host)
    vicon.startStream()
 
    # Launch GUI (blocks until application closes)
    setupGUI()


# ============================================================================
# ALTERNATIVE THREADING IMPLEMENTATION (COMMENTED OUT)
# ============================================================================
# The following code demonstrates an alternative approach using a separate
# thread for Vicon streaming. This is not currently used.
#
# def ViconThreadingFunction():
#     global vicon
#     host = "141.217.165.179:801"
#     vicon = ViconWrapper(host)
#     vicon.startStream()
#     vicon.startStreamLoop()
#    
# viconThread = threading.Thread(target=ViconThreadingFunction)
# viconThread.start()
#
# while True:
#     try:
#         print(vicon.localFPS)
#     except:
#         continue
