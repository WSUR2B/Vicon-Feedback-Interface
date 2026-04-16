"""
ViconWrapper Module - High-Level Interface to Vicon DataStream SDK

This module provides a simplified, Pythonic wrapper around the Vicon DataStream SDK
for real-time motion capture data acquisition and processing.

Purpose:
    Abstracts the complexity of the Vicon DataStream SDK and provides an intuitive
    interface for accessing marker positions, device data (EMG, force plates, etc.),
    and subject kinematics from a Vicon motion capture system.

Key Features:
    - Real-time streaming of marker and device data
    - Automatic subject and device discovery
    - Configurable data streams (markers, devices, segments)
    - Frame-by-frame updates with FPS tracking
    - Support for multiple subjects and devices

Module Structure:
    - ViconWrapper: Main class for Vicon system connection and data streaming
    - Subject: Represents a tracked subject with markers and kinematics
    - Segment: Represents a subject body segment (when segment data is enabled)
    - Forceplate: Represents a force plate device (not yet implemented)

Usage Example:
    >>> from ViconWrapper import ViconWrapper
    >>> vicon = ViconWrapper("localhost:801")
    >>> vicon.startStream()
    >>> vicon.updateFrame()
    >>> if vicon.subjectExists():
    ...     subject = vicon.getSubject(vicon.subjects[0].name)
    ...     print(subject.kinematics.anglesDictionary['LHip'])

Intended Applications:
    - Biomechanics research
    - Real-time motion analysis
    - Clinical gait assessment
    - Sports performance analysis
    - Motion capture data integration

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

from vicon_dssdk import ViconDataStream
from ViconWrapper.Subject import Subject
from ViconWrapper.Forceplate import Forceplate
import time

# ============================================================================
# MAIN VICON WRAPPER CLASS
# ============================================================================


class ViconWrapper:
    def __init__(self, host = "localhost:801"):
        """
        Initializes a ViconWrapper object.

        Args:
            host (str): The host address to connect to.

        Attributes:
            client (ViconDataStream.Client): The ViconDataStream client object.
            markers (dict): A dictionary to store labeled markers.
            unlabeledMarkers (dict): A dictionary to store unlabeled markers.
            devices (dict): A dictionary to store devices.
            forcePlates (list): A list to store force plates.
            subjects (list): A list to store subjects.
            frameNumber (int): The current frame number.
            lastFrameNumber (int): The last frame number.
            labeledMarkerDataOn (bool): Flag to indicate if labeled marker data is enabled.
            unlabeledMarkerDataOn (bool): Flag to indicate if unlabeled marker data is enabled.
            forceplateDataOn (bool): Flag to indicate if force plate data is enabled.
            deviceDataOn (bool): Flag to indicate if device data is enabled.
            subjectDataOn (bool): Flag to indicate if subject data is enabled.
            segmentDataOn (bool): Flag to indicate if segment data is enabled.
            subjectLLegMM (int): The length of the left leg in millimeters.
            subjectRLegMM (int): The length of the right leg in millimeters.
            subjectMarkerRMM (int): The radius of the subject marker in millimeters.
            localFPS (int): The local frames per second.
            viconFPS (int): The Vicon system frames per second.
            running (bool): Flag to indicate if the ViconWrapper is running.
        """
        self.client = ViconDataStream.Client()
        self.client.Connect(host)
        self.client.SetBufferSize(1)
        # self.client.ConfigureWireless()

        self.markers = {}
        self.unlabeledMarkers = {}
        self.devices = {}
        self.forcePlates = []
        self.subjects = []
        self.frameNumber = -1
        self.lastFrameNumber = -1

        # Initialize all data streams to off except forceplateDataOn
        self.labeledMarkerDataOn = True
        self.unlabeledMarkerDataOn = True
        self.forceplateDataOn = False
        self.deviceDataOn = True
        self.subjectDataOn = True
        self.segmentDataOn = False

        self.configureIncomingData()
        self.printDataTypes()

        self.subjectLLegMM = 800
        self.subjectRLegMM = 800
        self.subjectLKneeWidth = 100
        self.subjectRKneeWidth = 100
        self.subjectLAnkleWidth = 80
        self.subjectRAnkleWidth = 80
        self.subjectMarkerRMM = 7

        self.viconFPS = 100
        self.localFPS = 0
        self.running = True

    # ========================================================================
    # CONFIGURATION METHODS
    # ========================================================================
    
    def configureIncomingData(self):
        """
        Configure incoming data streams based on current settings.

        Disables all data types by default, then selectively enables only the
        requested data streams. This minimizes bandwidth and processing overhead.
        """
        self.client.DisableMarkerData()
        self.client.DisableUnlabeledMarkerData()
        self.client.DisableMarkerRayData()
        self.client.DisableDeviceData()
        self.client.DisableCentroidData()
        self.client.EnableLightweightSegmentData()


        if self.labeledMarkerDataOn:
            self.client.EnableMarkerData()
        if self.unlabeledMarkerDataOn:
            self.client.EnableUnlabeledMarkerData()
        if self.deviceDataOn:
            self.client.EnableDeviceData()
        if self.segmentDataOn:
            self.client.EnableSegmentData()

    def printDataTypes(self):
        """
        Prints the enabled data types for Vicon streaming.

        This method prints the status of various data types such as segments, markers, unlabeled markers,
        marker rays, devices, and centroids. It uses the Vicon client object to check if each data type is enabled
        and prints the result.
        """
        print('Segments', self.client.IsSegmentDataEnabled())
        print('Markers', self.client.IsMarkerDataEnabled())
        print('Unlabeled Markers', self.client.IsUnlabeledMarkerDataEnabled())
        print('Marker Rays', self.client.IsMarkerRayDataEnabled())
        print('Devices', self.client.IsDeviceDataEnabled())
        print('Centroids', self.client.IsCentroidDataEnabled())

    # ========================================================================
    # DATA STREAM ENABLE/DISABLE METHODS
    # ========================================================================
    
    def enableSegmentData(self):
        """
        Enable streaming of segment data from the Vicon system.

        Segment data provides position and orientation of body segments as
        defined in the Vicon model.
        """
        self.segmentDataOn = True
        self.client.EnableSegmentData()

    def disableSegmentData(self):
        """
        Disables the streaming of segment data from the Vicon system.

        This method sets the `segmentDataOn` flag to False and calls the `DisableSegmentData` function of the Vicon client.

        """
        self.segmentDataOn = False
        self.client.DisableSegmentData()

    def enableLabeledMarkerData(self):
        """
        Enables the streaming of labeled marker data.

        This method sets the `labeledMarkerDataOn` attribute to True and enables the streaming of marker data
        using the `EnableMarkerData` method of the Vicon client.

        """
        self.labeledMarkerDataOn = True
        self.client.EnableMarkerData()

    def disableLabeledMarkerData(self):
        """
        Disables the streaming of labeled marker data.

        This method sets the `labeledMarkerDataOn` flag to False and calls the `DisableMarkerData` method of the client object.

        """
        self.labeledMarkerDataOn = False
        self.client.DisableMarkerData()

    def enableUnlabeledMarkerData(self):
        """
        Enables the streaming of unlabeled marker data from the Vicon system.

        This method sets the `unlabeledMarkerDataOn` attribute to True and calls the `EnableUnlabeledMarkerData` method of the client object.

        """
        self.unlabeledMarkerDataOn = True
        self.client.EnableUnlabeledMarkerData()

    def disableUnlabeledMarkerData(self):
        """
        Disables the streaming of unlabeled marker data.

        This method sets the `unlabeledMarkerDataOn` attribute to False and calls the `DisableUnlabeledMarkerData` method of the client.

        """
        self.unlabeledMarkerDataOn = False
        self.client.DisableUnlabeledMarkerData()

    def enableForceplateData(self):
        """
        Enables the forceplate data.

        This method sets the `forceplateDataOn` attribute to True and calls the `EnableForceplateData` method of the client.

        """
        self.forceplateDataOn = True
        self.client.EnableForceplateData()

    def disableForceplateData(self):
        """
        Disables the forceplate data streaming.

        This method sets the `forceplateDataOn` flag to False and calls the `DisableForceplateData` method of the client object.

        """
        self.forceplateDataOn = False
        self.client.DisableForceplateData()

    def enableDeviceData(self):
        """
        Enables device data streaming.

        This method sets the `deviceDataOn` flag to True and enables device data streaming
        using the `EnableDeviceData` method of the client.

        Note: Make sure the client is connected before calling this method.

        """
        self.deviceDataOn = True
        self.client.EnableDeviceData()

    def disableDeviceData(self):
        """
        Disables the device data streaming.

        This method sets the `deviceDataOn` flag to False and calls the `DisableDeviceData` method of the client object.

        """
        self.deviceDataOn = False
        self.client.DisableDeviceData()

    def enableSubjectData(self):
        """
        Enables the streaming of subject data.

        This method sets the `subjectDataOn` attribute to True and calls the `EnableSubjectData` method of the client object.
        """
        self.subjectDataOn = True
        self.client.EnableSubjectData()

    def disableSubjectData(self):
        """
        Disables the streaming of subject data.

        This method sets the `subjectDataOn` flag to False and calls the `DisableSubjectData` method of the client object.

        """
        self.subjectDataOn = False
        self.client.DisableSubjectData()

    # ========================================================================
    # SUBJECT MANAGEMENT METHODS
    # ========================================================================
    
    def getSubject(self, subjectName):
        """
        Retrieve a subject by name.

        Args:
            subjectName (str): The name of the subject to retrieve.

        Returns:
            Subject or None: The subject object, or None if not found.
        """
        return next((subject for subject in self.subjects if subject.name == subjectName), None)

    def updateSubjects(self):
        """
        Updates the list of subjects based on the current subject names received from the Vicon client.

        This method compares the current subject names with the existing subject names and performs the following actions:
        - Adds new subjects to the list of subjects.
        - Removes subjects that are no longer present.
        - Updates the existing subjects by updating their segments, markers, and kinematics.

        """

        
        currentSubjectNames = set(self.client.GetSubjectNames())
        existingSubjectNames = {subject.name for subject in self.subjects}

        newSubjects = currentSubjectNames - existingSubjectNames
        removedSubjects = existingSubjectNames - currentSubjectNames

        # Add new subjects
        for subjectName in newSubjects:
            print(f"New subject found: {subjectName}")
            subject = Subject(subjectName, self.subjectLLegMM, self.subjectRLegMM, self.subjectLKneeWidth, self.subjectRKneeWidth, self.subjectLAnkleWidth, self.subjectRAnkleWidth, self.subjectMarkerRMM)
            self.subjects.append(subject)

        # Remove subjects no longer present
        for subjectName in removedSubjects:
            print(f"Subject removed: {subjectName}")

        # Update existing subjects
        for subject in self.subjects:
            if self.segmentDataOn:
                subject.updateSegments(self.client)
            subject.updateMarkers(self.client)
            subject.updateKinematics()

    def updateMeasurmentsAndMarkerRadius(self, lLegMM, rLegMM, lKneeWidth, rKneeWidth, lAnkleWidth, rAnkleWidth, markerRMM):
        """
        Updates the lengths of the legs and markers for all subjects.

        This method updates the lengths of the left leg, right leg, and subject marker radius for all subjects
        in the Vicon system.

        Args:
        lLegMM (int): The length of the left leg in millimeters.
        rLegMM (int): The length of the right leg in millimeters.
        lKneeWidth (int): The width of the left knee in millimeters.
        rKneeWidth (int): The width of the right knee in millimeters.
        lAnkleWidth (int): The width of the left ankle in millimeters.
        rAnkleWidth (int): The width of the right ankle in millimeters.
        markerRMM (int): The radius of the subject marker in millimeters.

        """

        self.subjectLLegMM = lLegMM
        self.subjectRLegMM = rLegMM
        self.subjectLKneeWidth = lKneeWidth
        self.subjectRKneeWidth = rKneeWidth
        self.subjectLAnkleWidth = lAnkleWidth
        self.subjectRAnkleWidth = rAnkleWidth
        self.subjectMarkerRMM = markerRMM

        for subject in self.subjects:
            subject.updateMeasurmentsAndMarkerRadius(lLegMM, rLegMM, lKneeWidth, rKneeWidth, lAnkleWidth, rAnkleWidth, markerRMM)

    def subjectExists(self):
        """
        Checks if a subject exists in the Vicon system.

        This method checks if the subject exists in the Vicon system by comparing the current subject names
        with the existing subject names.

        Returns:
        bool: True if the subject exists, False otherwise.
        """

        return len(self.subjects) > 0

    # ========================================================================
    # DATA UPDATE METHODS
    # ========================================================================
    
    def updateLabeledMarkers(self):
        """
        Update labeled marker positions from the Vicon system.

        Retrieves all labeled markers for the current frame and updates the
        markers dictionary. Automatically removes markers that no longer exist.
        """
        labeledMarkers = self.client.GetLabeledMarkers()
        existingMarkerIDs = set(self.markers.keys())

        for markerPos, trajID in labeledMarkers:
            self.markers[trajID] = markerPos
            existingMarkerIDs.discard(trajID)

        # Remove markers that no longer exist
        for markerID in existingMarkerIDs:
            del self.markers[markerID]

    def updateUnlabeledMarkers(self):
        """
        Updates the positions of unlabeled markers based on the latest data from the Vicon system.

        This method retrieves the positions of unlabeled markers from the Vicon system and updates
        the `unlabeledMarkers` dictionary with the new positions. It also removes any markers that
        no longer exist.

        Note: This method assumes that the `client` attribute is already initialized and connected
        to the Vicon system.

        """
        unlabeledMarkers = self.client.GetUnlabeledMarkers()
        existingMarkerIDs = set(self.unlabeledMarkers.keys())

        for markerPos, trajID in unlabeledMarkers:
            self.unlabeledMarkers[trajID] = markerPos
            existingMarkerIDs.discard(trajID)

        # Remove markers that no longer exist
        for markerID in existingMarkerIDs:
            del self.unlabeledMarkers[markerID]

    def updateForceplates(self):
        """
        Updates the forceplates.

        This method should be implemented in further iterations to update the forceplates
        with the latest data.

        """
        pass # Implement this method in further iterations

    def updateDevices(self):
        """
        Updates the devices in the ViconWrapper object.

        This method retrieves the names of the devices from the Vicon client and updates the existing devices
        in the ViconWrapper object. It also creates and updates new devices if any are found.

        """
        deviceNames = self.client.GetDeviceNames()

        #Temporarily track names of existing devices to identify new ones
        deviceTrackingList = set(self.devices.keys())

        #trajID is treated as a marker name
        for deviceName, deviceType in deviceNames:
            if deviceName in self.devices:
                # print("Device found: ", deviceName, deviceType)
                # Update existing marker
                if self.devices[deviceName]["Online"] == False:
                    deviceTrackingList.remove(deviceName)
                    continue
                
                for outputName, componentName, unit in self.client.GetDeviceOutputDetails(deviceName):
                    if self.devices[deviceName]["Data"][outputName]['Online']:
                        self.devices[deviceName]["Data"][outputName][componentName]['values'] = self.client.GetDeviceOutputValues(deviceName, outputName, componentName)

                deviceTrackingList.remove(deviceName)
            else:
                print("New device found: ", deviceName, deviceType)

                # Create and update new device
                self.devices[deviceName] = {}
                self.devices[deviceName]["Online"] = False
                self.devices[deviceName]["Data"] = {}

                try:
                    for outputName, componentName, unit in self.client.GetDeviceOutputDetails(deviceName):
                        if outputName not in self.devices[deviceName]["Data"]:
                            self.devices[deviceName]["Data"][outputName] = {}
                            self.devices[deviceName]["Data"][outputName]['Online'] = False

                        if componentName not in self.devices[deviceName]["Data"][outputName]:
                            self.devices[deviceName]["Data"][outputName][componentName] = {
                                'values': 0,
                                'unit': unit
                            }
                except:
                    pass
                            

                # time.sleep(20)

        # remove markers that no longer exist
        for old_device_name in deviceTrackingList:
            print("Device removed: ", old_device_name)
            del self.devices[old_device_name]


    # ========================================================================
    # STREAMING CONTROL METHODS
    # ========================================================================
    
    def startStream(self):
        """
        Start streaming mode for the Vicon client.

        Sets the stream mode to ServerPush, which allows the Vicon system
        to push new frames to the client as they become available.
        """
        self.client.SetStreamMode(ViconDataStream.Client.StreamMode.EServerPush)

    def startStreamLoop(self):
        """
        Starts the stream loop and continuously updates the frame.

        This method runs in a loop until the `running` flag is set to False. It updates the frame,
        calculates the local FPS (frames per second) every 2 seconds, and prints it to the console.

        """
        counter = 0
        while self.running:
            self.updateFrame()
            
            # print(f"Vicon FPS: {self.localFPS}")

            # if counter >= 100:
            #     counter = 0
            #     print(f"Vicon FPS: {self.localFPS}")

    def updateFrame(self):
        """
        Updates the frame data from the Vicon system.

        This method retrieves the latest frame from the Vicon system and updates the frame number.
        It also updates the data streams if they are enabled, including device data, labeled marker data,
        unlabeled marker data, forceplate data, and subject data.
        """
        start_time = time.time()

        
        self.lastFrameNumber = self.frameNumber
        self.client.GetFrame()
        self.viconFPS = self.client.GetFrameRate()
        self.frameNumber = self.client.GetFrameNumber()

        # Update data streams if they are enabled
        if self.deviceDataOn:
            self.updateDevices()
        if self.labeledMarkerDataOn:
            self.updateLabeledMarkers()
        if self.unlabeledMarkerDataOn:
            self.updateUnlabeledMarkers()
        if self.forceplateDataOn:
            self.updateForeceplates()
        if self.subjectDataOn:
            self.updateSubjects()

        dt = (time.time() - start_time)
        if dt == 0:
            dt =.01
        self.localFPS =  1.0/dt

    def stopStream(self):
        """
        Stops the streaming and disconnects from the Vicon client.
        """
        self.running = False
        self.client.Disconnect()



