"""
Segment Module - Body Segment Representation

This module defines the Segment class, which represents a body segment
(e.g., pelvis, femur, tibia) in the Vicon system.

A Segment contains:
    - Static properties (scale, initial pose)
    - Global pose (position and orientation in world space)
    - Local pose (position and orientation relative to parent)
    - Hierarchy information (parent and children)

Segments are used when working with the full Vicon skeletal model.
For marker-based kinematics only, segments are optional.

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# SEGMENT CLASS
# ============================================================================

class Segment:
    def __init__(self, subjectName, name):
        """
        Initializes a Segment object with the given subject name and segment name.

        Args:
            subjectName (str): The name of the subject to which the segment belongs.
            name (str): The name of the segment.

        Attributes:
            subjectName (str): The name of the subject to which the segment belongs.
            name (str): The name of the segment.
            childrenNames (list): A list of names of the segment's children.
            parentName (list): The name of the segment's parent.
            staticScale (list): The static scale of the segment.
            staticTranslation (list): The static translation of the segment.
            staticRotationHelical (list): The static helical rotation of the segment.
            staticRotationEulerXYZ (list): The static Euler XYZ rotation of the segment.
            staticRotationQuaternion (list): The static quaternion rotation of the segment.
            staticRotationMatrix (list): The static rotation matrix of the segment.
            globalTranslation (list): The global translation of the segment.
            globalRotationHelical (list): The global helical rotation of the segment.
            globalRotationEulerXYZ (list): The global Euler XYZ rotation of the segment.
            globalRotationQuaternion (list): The global quaternion rotation of the segment.
            globalRotationMatrix (list): The global rotation matrix of the segment.
            localTranslation (list): The local translation of the segment.
            localRotationHelical (list): The local helical rotation of the segment.
            localRotationEulerXYZ (list): The local Euler XYZ rotation of the segment.
            localRotationQuaternion (list): The local quaternion rotation of the segment.
            localRotationMatrix (list): The local rotation matrix of the segment.
            firstUpdate (bool): A flag indicating if it's the first update of the segment.
        """
        self.subjectName = subjectName
        self.name = name

        self.childrenNames = []
        self.parentName = []

        self.staticScale = []

        self.staticTranslation = []
        self.staticRotationHelical = []
        self.staticRotationEulerXYZ = []
        self.staticRotationQuaternion = []
        self.staticRotationMatrix = []

        self.globalTranslation = []
        self.globalRotationHelical = []
        self.globalRotationEulerXYZ = []
        self.globalRotationQuaternion = []
        self.globalRotationMatrix = []

        self.localTranslation = []
        self.localRotationHelical = []
        self.localRotationEulerXYZ = []
        self.localRotationQuaternion = []
        self.localRotationMatrix = []

        self.firstUpdate = True


    def setStaticProperties(self, client):
        """
        Sets the static properties of the segment.

        Args:
            client: The Vicon client object used to retrieve segment properties.

        Returns:
            None
        """
        try:
            self.childrenNames = client.GetSegmentChildren(self.subjectName, self.name)
        except:
            pass

        try:
            self.parentName = client.GetSegmentParent(self.subjectName, self.name)
        except:
            pass

        try:
            self.staticScale = client.GetSegmentStaticScale(self.subjectName, self.name)
        except:
            pass

        try:
            self.staticTranslation = client.GetSegmentStaticTranslation(self.subjectName, self.name)
        except:
            pass

        try:
            self.staticRotationHelical = client.GetSegmentStaticRotationHelical(self.subjectName, self.name)
            self.staticRotationEulerXYZ = client.GetSegmentStaticRotationEulerXYZ(self.subjectName, self.name)
            self.staticRotationQuaternion = client.GetSegmentStaticRotationQuaternion(self.subjectName, self.name)
            self.staticRotationMatrix = client.GetSegmentStaticRotationMatrix(self.subjectName, self.name)
        except:
            pass



    def update(self, client): 
        """
        Updates the segment's properties using the Vicon client.

        Args:
            client: The Vicon client object used to retrieve segment properties.

        Returns:
            None
        """
        if self.firstUpdate:
            self.setStaticProperties(client)
            self.firstUpdate = False
        try:
            self.globalTranslation = client.GetSegmentGlobalTranslation(self.subjectName, self.name)
            self.globalRoationHelical = client.GetSegmentGlobalRotationHelical(self.subjectName, self.name)
            self.globalRoationEulerXYZ = client.GetSegmentGlobalRotationEulerXYZ(self.subjectName, self.name)
            self.globalRotationQuaternion = client.GetSegmentGlobalRotationQuaternion(self.subjectName, self.name)
            self.globalRotationMatrix = client.GetSegmentGlobalRotationMatrix(self.subjectName, self.name)
        except:
            pass

