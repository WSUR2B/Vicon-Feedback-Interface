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
    - ViconWorker: Dedicated QThread worker that polls the Vicon DataStream
      SDK at the hardware clock (~100 Hz in live mode) and pushes frame
      snapshots into a bounded "latest-wins" queue. In recording-playback
      mode the achieved rate is capped by the Nexus playback engine.
    - MainTask: GUI-thread coordinator that drains the worker queue and
      dispatches each snapshot to the visualization, export, streaming, and
      feedback subsystems.
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
from PySide6.QtCore import QTimer, Qt, QObject, QThread, Slot
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
import queue

frame_timing_vector = []
# Vicon streams at 100 Hz, so 6000 entries = 60 s of timing history
frame_timing_vector_max = 6000


class ViconWorker(QObject):
    """
    Dedicated worker for high-frequency Vicon data ingestion.

    Runs in its own QThread so the SDK ingestion stages (the S1..S10
    benchmarks recorded inside ViconWrapper.updateFrame) stay aligned with
    the Vicon hardware clock and are not pre-empted by GUI rendering.

    When Nexus is in live mode, GetFrame() blocks until the next 10 ms pulse,
    giving a steady ~100 Hz ingestion rate. When Nexus is in recording
    playback / replay mode, the SDK is rate-limited by the playback engine
    instead, so the achieved FPS in the GUI will be lower than 100 Hz - this
    is a Nexus-side limitation, not a problem with this worker.

    Frames are handed to the GUI thread via a bounded "latest-wins" queue
    (vicon_data_queue), drained by MainTask.drainQueue() on a QTimer. We
    intentionally do NOT use a Qt signal to deliver frames - the queue
    gives us deterministic drop-the-oldest backpressure, while a signal
    would buffer indefinitely behind a slow GUI.
    """

    def __init__(self, vicon_wrapper):
        super().__init__()
        self.vicon = vicon_wrapper
        # Cap at 5 frames. At 100 Hz that is 50 ms of lag; if the GUI thread
        # falls further behind than that we'd rather drop stale frames than
        # accumulate latency.
        self.vicon_data_queue = queue.Queue(maxsize=5)

        self._running = True

    @Slot()
    def run(self):
        while self._running:
            try:
                self._runOnce()
            except Exception as e:
                # Never let a transient SDK / network hiccup silently kill the
                # worker thread. Log and keep looping so the GUI keeps trying.
                print(f"[ViconWorker] frame iteration failed: {type(e).__name__}: {e}")
                # Tiny back-off so a persistent error doesn't pin a CPU core.
                QThread.msleep(10)

    def _runOnce(self):
        # In live mode this blocks until the next 10 ms pulse arrives.
        # In playback mode the SDK returns whenever Nexus produces the next
        # replayed frame, which may be slower than 100 Hz.
        self.vicon.updateFrame()

        # --- 1. BUILD DEVICE SNAPSHOT ---
        devices_snapshot = {}
        for dev_name, d_info in self.vicon.devices.items():
            devices_snapshot[dev_name] = {"Online": d_info["Online"], "Data": {}}
            for chan_name, c_info in d_info["Data"].items():
                devices_snapshot[dev_name]["Data"][chan_name] = {"Online": c_info.get("Online", False)}
                for comp_name, comp_val in c_info.items():
                    if comp_name != "Online":
                        current_val = comp_val['values']

                        # Match the steady-state shape ([list_of_samples]) even when the
                        # SDK has not produced data yet, so consumers can always do
                        # values[0][-1] without TypeError on an uninitialized channel.
                        if isinstance(current_val, int):
                            safe_val = [[0.0]]
                        else:
                            # The SDK is streaming, safely copy the list of floats
                            safe_val = [list(current_val[0])]

                        devices_snapshot[dev_name]["Data"][chan_name][comp_name] = {
                            'values': safe_val
                        }

        # --- 2. BUILD KINEMATICS SNAPSHOT ---
        subject_exists = self.vicon.subjectExists()
        angles_snap = {}
        flags_snap = {}
        if subject_exists:
            active_subj = self.vicon.getSubject(self.vicon.subjects[0].name)
            angles_snap = active_subj.kinematics.anglesDictionary.copy()
            flags_snap = active_subj.kinematics.angleFlags.copy()

        # --- 3. PACK ---
        data_packet = {
            'benchmarks': self.vicon.benchmarks.copy(),
            'frameNumber': self.vicon.frameNumber,
            'lastFrameNumber': self.vicon.lastFrameNumber,
            'subjectExists': subject_exists,
            'angles': angles_snap,
            'angleFlags': flags_snap,
            'devices': devices_snapshot
        }

        # --- 4. THE "LATEST-WINS" QUEUE LOGIC ---
        try:
            # Try to put the packet in. If there is room, it happens instantly.
            self.vicon_data_queue.put_nowait(data_packet)
        except queue.Full:
            # The GUI is busy/falling behind.
            try:
                # Remove the oldest frame (the "stale" one)
                self.vicon_data_queue.get_nowait()
                # Put the newest frame in its place
                self.vicon_data_queue.put_nowait(data_packet)
            except queue.Empty:
                # Rare race condition where the GUI emptied the queue
                # between our Full check and our Get check.
                pass

    def stop(self):
        self._running = False
        
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

    def updatePlotting(self, frameNumber, data_packet):
        """
        Update all plot series with data from the current frame.
        
        This method orchestrates the addition of both angle and device data to the chart.
        It checks if a subject exists before attempting to plot angle data.
        
        """
        if data_packet['subjectExists']:
            self.addAnglesToPlot(frameNumber, data_packet)
            
        # Add device data
        self.addDeviceDataToPlot(frameNumber, data_packet)
        
        # Finalize the frame update
        self.myChart.finalize()

    def addAnglesToPlot(self, frameNumber, data_packet):
        """
        Add angle data points to the chart series.
        
        Only adds data for angles that are selected (angleFlags = True) and have
        valid data available in the subject's kinematics dictionary.

        """
        angles_dict = data_packet['angles']
        angle_flags = data_packet['angleFlags']

        # Add first angle if selected and available
        if self.Angle1 != "":
            if self.Angle1[1:] in angle_flags and angle_flags[self.Angle1[1:]]:
                self.myChart.addData(1, frameNumber, angles_dict[self.Angle1])
        
        # Add second angle if selected and available
        if self.Angle2 != "":
            if self.Angle2[1:] in angle_flags and angle_flags[self.Angle2[1:]]:
                self.myChart.addData(2, frameNumber, angles_dict[self.Angle2])

    def addDeviceDataToPlot(self, frameNumber, data_packet):
        """
        Add device data points to the chart series.
        
        Applies filtering to device data before plotting. Handles multiple data points
        per frame (e.g., when device sampling rate exceeds mocap frame rate).

        """
        if self.deviceData == ['','',''] or self.deviceData == ['None', 'None', 'None'] or self.deviceData == []:
            return
        
        devices = data_packet['devices']
        
        if self.deviceData[0] not in devices:
            return
        if not devices[self.deviceData[0]]["Online"]:
            return
        
        data = devices[self.deviceData[0]]["Data"][self.deviceData[1]][self.deviceData[2]]['values'][0][-1]
        
        #is [-1] is removed, we allow subframes. for plotting, not optimal to have subframes
        # for i in range(len(data)):
        #     filtered_val = self.deviceFilter.filter(data[i])
        #     self.myChart.addData(3, frameNumber - 1 + i/len(data), filtered_val)
        filtered_val = self.deviceFilter.filter(data)
        self.myChart.addData(3, frameNumber, filtered_val)


# ============================================================================
# DATA EXPORT MANAGEMENT
# ============================================================================

class Exporting:
    """
    Manages data recording and CSV export functionality.
    Optimized for real-time systems using in-memory list appending.
    """
    
    def __init__(self):
        """Initialize the data export system with default settings."""
        # Data collection buffers
        self.angleExportList = []  # List of angle names to export
        self.angleExportData = []  # Accumulated angle data

        self.deviceExportList = []  # List of [device, channel] pairs to export
        self.deviceExportData = {}  # Dict with keys "device:channel" <-- FIX 1

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
        self.isRecording = True
        self.recordingDuration = duration
        self.recordingStartTime = time.time()

    def saveDataToCSV(self):
        """
        Export accumulated data to CSV files.
        Converts lists to Pandas DataFrames only at the moment of saving.
        """
        name = self.filename
        
        # ---- Export angle data ----
        if self.angleExportData:
            if not self.savingAutoIndex:
                if self.savingIndex == 0:
                    fullSavePath = os.path.join(self.savePath, name + "_angles.csv")
                else:
                    fullSavePath = os.path.join(self.savePath, name + "_angles_" + str(self.savingIndex) + ".csv")
            else:
                savingIndex = 0

                if os.path.isfile(os.path.join(self.savePath, name + "_angles.csv")):
                    savingIndex += 1

                while os.path.isfile(os.path.join(self.savePath, name + "_angles_" + str(savingIndex) + ".csv")):
                    savingIndex += 1

                if savingIndex == 0:
                    fullSavePath = os.path.join(self.savePath, name + "_angles.csv")
                else:
                    fullSavePath = os.path.join(self.savePath, name + "_angles_" + str(savingIndex) + ".csv")
                                    
            pd.DataFrame(self.angleExportData).to_csv(fullSavePath, index=False)

        # ---- Export device data ---- <-- FIX 2
        for selectedDevice, data_list in self.deviceExportData.items():
            if not data_list:
                continue
                
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

            pd.DataFrame(data_list).to_csv(fullSavePath, index=False)

        # Clear buffers instantly to free RAM
        self.angleExportData = []
        self.deviceExportData = {}
        self.recordingStartTime = 0
        self.recordingDuration = 0

    def updateExporting(self, frameNumber, data_packet):
        if time.time() - self.recordingStartTime >= self.recordingDuration and self.recordingDuration != 0:
            self.isRecording = False
            self.saveDataToCSV()
            addToLog("Recording Stopped")
            addToLog("Files Saved To: " + self.savePath)

        if data_packet['subjectExists']:
            self.addAnglesToExport(frameNumber, data_packet['angles'])
        
        self.addDeviceDataToExport(frameNumber, data_packet['devices'])

    def addAnglesToExport(self, frameNumber, angles_dict):
        # <-- FIX 3: Removed brackets around values
        new_row = {'Frame': frameNumber} 
        
        for angle in self.angleExportList:
            new_row['L'+angle] = angles_dict['L'+angle]
            new_row['R'+angle] = angles_dict['R'+angle]

        self.angleExportData.append(new_row)

    def addDeviceDataToExport(self, frameNumber, devices_dict):
        for deviceName, channel in self.deviceExportList:
            key = f"{deviceName}:{channel}"
            
            if key not in self.deviceExportData:
                self.deviceExportData[key] = []
                
            listOfComponents = list(devices_dict[deviceName]["Data"][channel].keys())
            if "Online" in listOfComponents:
                listOfComponents.remove("Online") 

            if self.saveAllDeviceData:
                num_samples = len(devices_dict[deviceName]["Data"][channel][listOfComponents[0]]['values'][0])
                for i in range(num_samples):
                    new_row = {'Frame': frameNumber - 1 + i / num_samples}
                    for component in listOfComponents:
                        new_row[component] = devices_dict[deviceName]["Data"][channel][component]['values'][0][i]
                    self.deviceExportData[key].append(new_row)
            else:
                new_row = {'Frame': frameNumber}
                for component in listOfComponents:
                    new_row[component] = devices_dict[deviceName]["Data"][channel][component]['values'][0][-1]
                self.deviceExportData[key].append(new_row)
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

    def updateStream(self, data_packet):
        """
        Send current frame data over UDP.
        
        Transmits angle data if a subject is present, followed by device data.
        Only operates when streaming is active.

        """
        if not self.IsStreamingUDP:
            return
        
        if data_packet['subjectExists']:
            self.sendAngleOverUDP(data_packet['angles'])
        
        self.sendDeviceDataOverUDP(data_packet['devices'])


    def sendAngleOverUDP(self, angles_dict):
        """
        Transmit angle data packets over UDP.
        
        Creates and sends one packet per angle. Packet format:
            [AngleName | Padding | AngleValue | '$']

        """
        for angle in self.angleStreamList:
            # angleName = angle
            # angleNameSize = len(angleName)
            angleValue = angles_dict[angle]
            
            # angleValue = str(angleValue)[:self.valueSize]
            # if len(angleValue) < self.valueSize:
            #     angleValue = angleValue + "0"*(self.valueSize-len(angleValue))

            # packet = " "*self.packetSize
            # packet = angleName + packet[angleNameSize:]
            # packet = packet[:self.packetSize-self.valueSize] + angleValue
            # packet = packet + "$"


            # Fast string formatting using ljust
            val_str = str(angleValue)[:self.valueSize].ljust(self.valueSize, '0')
            left_part = angle.ljust(self.packetSize - self.valueSize, ' ')
            
            # Construct packet and append to batch
            packet = f"{left_part}{val_str}$"
            self.sendOverUDP(packet)


              



    def sendDeviceDataOverUDP(self, devices_dict):
        """
        Transmit device data packets over UDP.
        
        Creates and sends one packet per device/channel/component. Packet format:
            [DeviceLabel | Padding | DataValue | '$']
        where DeviceLabel = "Device:Channel:Component"
        
        """
        for deviceName, channel, component in self.deviceStreamList:
            # deviceLabel = deviceName + ":" + channel + ":" + component
            # deviceLabelSize = len(deviceLabel)

            # deviceData = devices_dict[deviceName]["Data"][channel][component]['values'][0][-1]
            
            # deviceData = str(deviceData)[:self.valueSize]
            # if len(deviceData) < self.valueSize:
            #     deviceData = deviceData + "0"*(self.valueSize-len(deviceData))

            # packet = " "*self.packetSize
            # packet = deviceLabel + packet[deviceLabelSize:]
            # packet = packet[:self.packetSize-self.valueSize] + deviceData
            # packet = packet + "$"

            deviceLabel = f"{deviceName}:{channel}:{component}"
            deviceData = devices_dict[deviceName]["Data"][channel][component]['values'][0][-1]
            
            # Fast string formatting using ljust
            val_str = str(deviceData)[:self.valueSize].ljust(self.valueSize, '0')
            left_part = deviceLabel.ljust(self.packetSize - self.valueSize, ' ')
            
            # Construct packet and append to batch
            packet = f"{left_part}{val_str}$"

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

        except BlockingIOError:
            # The network buffer is full. Drop the packet silently and treat it
            # as a successful no-op so we don't trip the 3-strike auto-stop.
            self.UDPErrorCount = 0

        except OSError as e:
            self.UDPErrorCount += 1
            addToLog(f"Error Sending Data Over UDP - attempt {self.UDPErrorCount} ({e})")

            # Stop streaming after 3 consecutive errors
            if self.UDPErrorCount >= 3:
                self.stopUDPStream()

    def startUDPStream(self):
        """
        Initialize UDP socket and begin streaming.
        
        Creates a new UDP socket and sets the streaming flag.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        if self.UDPHost.lower() == "localhost":
            self.UDPHost = "127.0.0.1"
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

    def updateFeedback(self, data_packet):
        """
        Update feedback display with current frame data.
        
        Checks both angle and device lists and updates the display with
        the first available data source.
        

        """
        if self.deviceFeedbackList == [] and self.angleFeedbackList == []:
            return
        
        if data_packet['subjectExists']:
            self.updateAnglesFeedback(data_packet['angles'])
        
        self.updateDeviceDataFeedback(data_packet['devices'])

    def updateAnglesFeedback(self, angles_dict):
        """
        Update feedback display with angle data.
        
        """
        for angle in self.angleFeedbackList:
            angleValue = angles_dict[angle]
            self.setCurrentValue(angleValue)

    def updateDeviceDataFeedback(self, devices_dict):
        """
        Update feedback display with device data.
        
        """
        for deviceName, channel, component in self.deviceFeedbackList:
            deviceData = devices_dict[deviceName]["Data"][channel][component]['values'][0][-1]
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

class MainTask(QObject): # Inherit QObject to receive signals
    """
    Core processing loop coordinating all application subsystems.

    This class orchestrates the real-time data flow from Vicon through filtering,
    visualization, export, streaming, and feedback systems. It runs on the GUI
    thread and consumes frame snapshots produced by ViconWorker on a dedicated
    thread, drained from a bounded "latest-wins" queue every few milliseconds.

    Effective throughput tracks the Vicon hardware clock (~100 Hz when Nexus is
    in live mode). Replaying a captured trial through Nexus is rate-limited by
    the playback engine, so the achieved FPS will be lower than 100 Hz until
    the system is switched back to live capture.

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
        queue_timer (QTimer): Polls the worker's data queue from the GUI thread

    Methods:
        drainQueue(): Pop all pending frame snapshots from the worker queue
        handleFrame(): Process one frame snapshot through all subsystems
        tickFPS(): Update FPS displays
        zeroSubjectAngles(): Zero the current joint angles
        setAngleFilter(): Defer-apply a new angle filter on the next frame
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

        # Poll the worker's frame queue on the GUI thread. 5 ms is half of the
        # 10 ms Vicon period, so we stay ahead of incoming frames without
        # spinning the CPU. drainQueue() handles bursty arrivals by emptying
        # the queue on each tick.
        self.queue_timer = QTimer()
        self.queue_timer.timeout.connect(self.drainQueue)
        self.queue_timer.start(5)

    @Slot()
    def drainQueue(self):
        global viconWorker
        # Guard for the brief window between MainTask construction and
        # ViconWorker assignment in setupGUI().
        if viconWorker is None:
            return
        # qsize() is documented as approximate and the worker can also pop
        # the oldest item when the queue is full. Drain by polling get_nowait()
        # until Empty so we never raise.
        while True:
            try:
                data = viconWorker.vicon_data_queue.get_nowait()
            except queue.Empty:
                break
            self.handleFrame(data)

    @Slot(dict)
    def handleFrame(self, data):
        """
        Process a single frame snapshot produced by ViconWorker.

        Runs on the GUI thread (invoked from drainQueue). Handles plot
        rollover, window-recording transitions, and dispatches the snapshot
        to the plotting, exporting, streaming, and feedback subsystems.
        Per-stage perf_counter timestamps are appended to frame_timing_vector
        so the timing-analysis tools can post-process them later.
        """
        global vicon
        global frame_timing_vector, frame_timing_vector_max
        frame_metrics = {}

        # Pull timing from the worker's ingestion
        frame_metrics = data['benchmarks']
        frame_metrics['frame number'] = data['frameNumber']

        self.lastViconFrame = self.currentViconFrame
        self.currentViconFrame = data['frameNumber']

        frame_metrics['11_plot_clean_saving_to_csv_get_active_subject_start'] = time.perf_counter()

        if vicon.subjectExists(): # GUI THREAD ACCESS
            self.activeSubject = vicon.getSubject(vicon.subjects[0].name) # GUI THREAD ACCESS

            # Apply pending angle-filter change now that a subject exists
            if self.setFilterFlag:
                self.setFilterFlag = False
                self.activeSubject.kinematics.setFilter(self.filterWindow, self.filterSampleRate,
                                                       self.filterType, self.filterLowCut, self.filterHighCut)
        else:
            self.activeSubject = None

        # Clear plot when frame counter rolls over
        if self.lastViconFrame%self.maxFrames > self.currentViconFrame%self.maxFrames:
            print("Clearing Plot")
            self.plotting.clearAll()

        # Handle window recording mode (triggered by frame rollover)
        if self.lastViconFrame > self.currentViconFrame:
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

        frame_metrics['12_plot_clean_saving_to_csv_get_active_subject_end'] = time.perf_counter()

        # Update all subsystems with current frame data
        frame_metrics['13_update_plotting_start'] = time.perf_counter()
        self.plotting.updatePlotting(self.currentViconFrame % self.maxFrames, data)
        frame_metrics['14_update_plotting_end'] = time.perf_counter()

        frame_metrics['15_update_exporting_start'] = time.perf_counter()
        if self.exporting.isRecording:
            self.exporting.updateExporting(self.currentViconFrame, data)
        frame_metrics['16_update_exporting_end'] = time.perf_counter()

        frame_metrics['17_update_streaming_start'] = time.perf_counter()
        if self.streaming.IsStreamingUDP:
            self.streaming.updateStream(data)
        frame_metrics['18_update_streaming_end'] = time.perf_counter()

        frame_metrics['19_update_feedback_start'] = time.perf_counter()
        if self.feedback.deviceFeedbackList != [] or self.feedback.angleFeedbackList != []:
            self.feedback.updateFeedback(data)
        frame_metrics['19_update_feedback_end'] = time.perf_counter()

        # Calculate and update FPS
        dt = time.perf_counter() - frame_metrics['1_sdk_update_loop_start']
        frame_metrics['total_time'] = dt
        
        # Store in your global vector for analysis
        frame_timing_vector.append(frame_metrics)
        if len(frame_timing_vector) > frame_timing_vector_max:
            frame_timing_vector.pop(0)

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

    def setAngleFilter(self):
        # Defer the actual filter setup until handleFrame() observes a subject.
        # Calling kinematics.setFilter() directly here would race with the worker
        # thread (which is computing kinematics) and crash if no subject exists.
        self.setFilterFlag = True
        

# ============================================================================
# GLOBAL APPLICATION OBJECTS
# ============================================================================

# Core application objects (initialized in setupGUI)
app = None                  # Qt Application instance
Main = None                 # MainTask instance (core processing loop)
ui = None                   # Main window UI (Ui_MainWindow)
ui2 = None                  # Feedback window UI (Ui_Form)
vicon = None                # ViconWrapper instance (data source)

viconWorker = None
viconThread = None


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
    global Main, ui, viconWorker

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
    lKneeWidth = ui.spinLeftKneeWidth.value()
    rKneeWidth = ui.spinRightKneeWidth.value()
    lAnkleWidth = ui.spinLeftAnkleWidth.value()
    rAnkleWidth = ui.spinRightAnkleWidth.value()
    markerR = ui.spinMarkerR.value()
    vicon.updateMeasurmentsAndMarkerRadius(lLegMM, rLegMM, lKneeWidth, rKneeWidth, lAnkleWidth, rAnkleWidth, markerR)


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

    
    Main.setAngleFilter()

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

def save_timing_data():
    """
    Converts the timing list to a CSV. 
    Using Pandas is fastest for list-of-dicts to CSV conversion.
    """
    global frame_timing_vector
    if not frame_timing_vector:
        print("No timing data to save.")
        return

    import pandas as pd
    import os

    df = pd.DataFrame(frame_timing_vector)

    # Always overwrite the same file so MATLAB analysis scripts can point at
    # a stable path. Swap to the timestamped variant if you want to keep
    # historical runs around.
    save_name = "timing_log.csv"
    # save_name = f"timing_log_{int(time.time())}.csv"
    save_path = save_name

    # index=False so MATLAB doesn't pick up the row index as a column
    df.to_csv(save_path, index=False)
    print(f"Timing data saved to: {save_path}")

def closingEvent():
    """
    Handle application shutdown.

    Stops the ViconWorker loop, waits for the dedicated worker thread to
    exit, disconnects the Vicon SDK, dumps the timing log, and closes the
    UDP stream. Connected to QApplication.aboutToQuit so it runs whether
    the user closes the main window or quits via Qt.
    """
    global vicon, Main
    global viconWorker
    global viconThread

    print("Closing Event")

    viconWorker.stop()      # Breaks the while loop
    viconThread.quit()      # Tells Qt to stop the thread
    viconThread.wait()      # Blocks until the thread is fully dead
    print("Worker thread stopped.")
    
    vicon.stopStream()
    print("Vicon SDK disconnected.")

    save_timing_data()

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
    global viconWorker
    global viconThread

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

    
    def on_main_window_close(event):
        # This forces the entire application to shut down when the main UI is closed
        QApplication.quit()
        event.accept()

    MainWindow.closeEvent = on_main_window_close


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

    viconThread = QThread()
    viconWorker = ViconWorker(vicon)
    viconWorker.moveToThread(viconThread)

    # Thread starts -> Worker begins its run loop. Frames flow through
    # viconWorker.vicon_data_queue and are drained by Main.drainQueue() on a QTimer.
    viconThread.started.connect(viconWorker.run)
    viconThread.start()
    viconThread.setPriority(QThread.Priority.TimeCriticalPriority)

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
    ui.spinRightKneeWidth.valueChanged.connect(lambda: updateLegsandMarkreDimentions())
    ui.spinLeftKneeWidth.valueChanged.connect(lambda: updateLegsandMarkreDimentions())
    ui.spinLeftAnkleWidth.valueChanged.connect(lambda: updateLegsandMarkreDimentions())
    ui.spinRightAnkleWidth.valueChanged.connect(lambda: updateLegsandMarkreDimentions())
    ui.spinMarkerR.valueChanged.connect(lambda: updateLegsandMarkreDimentions())

    ui.spinFeedbackMax.valueChanged.connect(lambda: feedbackRangesChanged())
    ui.spinFeedbackRegionMax.valueChanged.connect(lambda: feedbackRangesChanged())
    ui.spinFeedbackRegionMin.valueChanged.connect(lambda: feedbackRangesChanged())
    ui.spinFeedbackMin.valueChanged.connect(lambda: feedbackRangesChanged())

    ui.tableFeedback.itemSelectionChanged.connect(lambda: feedbackTableSelectionChanged())
    ui.btnPushReverseFeedbackSignal.clicked.connect(lambda: feedbackNegateChanged())

    #add closing event
    app.aboutToQuit.connect(lambda: closingEvent())

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
    host = "localhost:801"
    
    # Initialize Vicon connection
    vicon = ViconWrapper(host)
    vicon.startStream()
 
    # Launch GUI (blocks until application closes)
    setupGUI()
