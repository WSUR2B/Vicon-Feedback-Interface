"""
Subject Module - Representation of Tracked Subjects

This module defines the Subject class, which represents a person or object
being tracked by the Vicon motion capture system.

A Subject contains:
    - Markers: 3D positions of reflective markers
    - Segments: Body segments with position/orientation (optional)
    - Kinematics: Calculated joint angles and positions

The Subject class automatically updates marker positions and calculates
kinematics on each frame update.

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

from ViconWrapper.Segment import Segment
from Kinematics.MarkerKinematics import MarkerKinematicsPlugInSetQ0

# ============================================================================
# SUBJECT CLASS
# ============================================================================

class Subject:
    def __init__(self, name, LLegMM, RLegMM, MarkerRMM):
        """
        Initializes a Subject object.

        Args:
            name (str): The name of the subject.
            LLegMM (float): Length of the left leg in millimeters.
            RLegMM (float): Length of the right leg in millimeters.
            MarkerRMM (float): Marker radius in millimeters.

        Attributes:
            name (str): The name of the subject.
            kinematics (MarkerKinematicsPlugInSetQ0): The kinematics plugin set with initial values.
            segments (list): List of segments.
            markers (dict): Dictionary of markers.

        Methods:
            updateSegments(self, client): Updates the segments of the subject using the provided Vicon client.
            updateMarkers(self, client): Update the markers of the subject based on the data received from the Vicon client.
            updateKinematics(self): Updates the kinematics of the subject using the provided markers.
            listSegments(self): Prints the names of all segments in the subject.
            listMarkers(self): Prints the names of all markers associated with the subject.

        """

        self.name = name
        self.kinematics = MarkerKinematicsPlugInSetQ0(LLegMM, RLegMM, MarkerRMM)
        self.segments = []
        self.markers = {}
    
    def updateLegAndMarkerLengths(self, LLegMM, RLegMM, MarkerRMM):
        """
        Updates the lengths of the legs and the marker radius.

        Args:
            LLegMM (float): Length of the left leg in millimeters.
            RLegMM (float): Length of the right leg in millimeters.
            MarkerRMM (float): Marker radius in millimeters.

        """
        self.kinematics.LegLengthL = LLegMM
        self.kinematics.LegLengthR = RLegMM
        self.kinematics.markerRadius = MarkerRMM
        
    
    def updateSegments(self, client):
        """
        Updates the segments of the subject using the provided Vicon client.

        Args:
            client: The Vicon client used to retrieve segment information.

        """
        segmentNames = client.GetSegmentNames(self.name)

        segmentExists = False
        for segmentName in segmentNames:
            for segment in self.segments:
                if segment.name == segmentName:
                    segment.update(client)
                    segmentExists = True

            if not segmentExists:
                segment = Segment(self.name, segmentName)
                segment.setStaticProperties(client)
                segment.update(client)

                self.segments.append(segment)

                

    def updateMarkers(self, client):
        """
        Update the markers of the subject based on the data received from the Vicon client.

        Args:
            client: The Vicon client object used to retrieve marker data.

        """
        markerNames = client.GetMarkerNames(self.name)
        existingMarkerNames = set(self.markers.keys())

        for markerName, parentSegment in markerNames:
            globalPosition = client.GetMarkerGlobalTranslation(self.name, markerName)
            self.markers[markerName] = globalPosition[0]
            existingMarkerNames.discard(markerName)

        # remove markers that no longer exist
        for old_marker_name in existingMarkerNames:
            del self.markers[old_marker_name]

    def updateKinematics(self):
        """
        Updates the kinematics of the subject using the provided markers.

        Parameters:
        - markers: A list of markers representing the subject's position.

        Returns:
        None
        """
        self.kinematics.updateWithSubject(self.markers)

    def listSegments(self):
        """
        Prints the names of all segments in the subject.
        """
        for segment in self.segments:
            print(segment.name)

    def listMarkers(self):
        """
        Prints the names of all markers associated with the subject.
        """
        for marker in self.markers:
            print(marker.name)
