from vicon_dssdk import ViconDataStream
from ViconWrapper.Subject import Subject
from ViconWrapper.Forceplate import Forceplate
import time
""" 
ViconWrapper is a Python module that provides a wrapper around the Vicon DataStream SDK to simplify the process of
retrieving and processing data from a Vicon motion capture system. It provides a high-level interface to the Vicon
DataStream SDK and allows users to easily enable and disable different data streams, such as labeled markers, unlabeled
markers, force plates, devices, and subjects. The module also provides classes to represent subjects, segments, markers,
and force plates, making it easier to work with the data coming from the Vicon system.

This module is intended to be used in research projects, motion capture applications, and other projects that require
real-time motion capture data from a Vicon system. It provides a simple and flexible API that allows users to configure
the data streams, retrieve the latest data from the Vicon system, and process the data in real-time.

The ViconWrapper module consists of the following classes:

1. ViconWrapper: A class that represents a wrapper around the Vicon DataStream SDK and provides methods to enable and
disable different data streams, update the frame data, and retrieve data from the Vicon system.

2. Subject: A class that represents a subject in the Vicon system and provides methods to update the segments, markers,
and kinematics of the subject.

3. Segment: A class that represents a segment of a subject in the Vicon system and provides methods to update the markers
and kinematics of the segment.

5. Forceplate: A class that represents a force plate in the Vicon system and provides methods to update the force and
moment data of the force plate.                                 NOT IMPLEMENTED 

The ViconWrapper module is designed to be easy to use and extensible, allowing users to customize the behavior of the
module to suit their specific needs. It provides a high-level interface to the Vicon DataStream SDK and abstracts away
the complexity of working with the Vicon system, making it easier to integrate motion capture data into Python
applications.

"""


class ViconWrapper:
    def __init__(self, host):
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
        self.client.ConfigureWireless()

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
        self.subjectMarkerRMM = 7

        self.viconFPS = 100
        self.localFPS = 0
        self.running = True

    def configureIncomingData(self):
        """
        Configures the incoming data for the Vicon client.

        This method enables or disables different types of data based on the current configuration settings.
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

    def enableSegmentData(self):
        """
        Enables the streaming of segment data from the Vicon system.

        This method sets the `segmentDataOn` attribute to True and calls the `EnableSegmentData` method of the client object.
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

    def getSubject(self, subjectName):
        """
        Returns the subject object with the given name.

        Parameters:
        subjectName (str): The name of the subject to retrieve.

        Returns:
        Subject or None: The subject object with the given name, or None if not found.
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
            subject = Subject(subjectName, self.subjectLLegMM, self.subjectRLegMM, self.subjectMarkerRMM)
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

    def updateLegAndMarkerLengths(self, lLegMM, rLegMM, markerRMM):
        """
        Updates the lengths of the legs and markers for all subjects.

        This method updates the lengths of the left leg, right leg, and subject marker radius for all subjects
        in the Vicon system.

        Args:
        lLegMM (int): The length of the left leg in millimeters.
        rLegMM (int): The length of the right leg in millimeters.
        markerRMM (int): The radius of the subject marker in millimeters.

        """

        self.subjectLLegMM = lLegMM
        self.subjectRLegMM = rLegMM
        self.subjectMarkerRMM = markerRMM

        for subject in self.subjects:
            subject.updateLegAndMarkerLengths(lLegMM, rLegMM, markerRMM)

    def subjectExists(self):
        """
        Checks if a subject exists in the Vicon system.

        This method checks if the subject exists in the Vicon system by comparing the current subject names
        with the existing subject names.

        Returns:
        bool: True if the subject exists, False otherwise.
        """

        return len(self.subjects) > 0

    def updateLabeledMarkers(self):
        """
        Updates the labeled markers by retrieving the latest marker positions from the Vicon system.

        This method retrieves the labeled markers from the Vicon system using the `GetLabeledMarkers` function
        and updates the `markers` dictionary with the latest marker positions. It also removes any markers
        that no longer exist.

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


    def startStream(self):
        """
        Starts the streaming mode for the Vicon client.

        This method sets the stream mode of the Vicon client to EServerPush,
        which allows the Vicon system to push data to the client.

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



