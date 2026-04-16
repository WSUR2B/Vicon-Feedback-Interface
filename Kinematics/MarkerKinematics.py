"""
MarkerKinematics Module - Joint Angle Calculation from Motion Capture Markers

This module calculates lower extremity joint angles from motion capture marker
positions using biomechanical modeling techniques.

Implementation Details:
    Currently implements the Plug-in Gait marker set with Quality Level 1 (Q1),
    which calculates joint angles in the sagittal, frontal, and transverse planes
    for the hip, knee, and ankle joints.

Marker Set Requirements:
    - Pelvis: LASI, RASI, LPSI, RPSI
    - Lower extremity: LKNE, RKNE, LANK, RANK
    - Foot: LHEE, RHEE, LTOE, RTOE

Calculated Angles:
    - Hip flexion/extension (sagittal plane)
    - Hip adduction/abduction (frontal plane)  
    - Hip internal/external rotation (transverse plane)
    - Knee flexion/extension
    - Ankle dorsiflexion/plantarflexion
    - Subtalar angle (foot inversion/eversion)

Features:
    - Real-time filtering of angle data
    - Zero position calibration
    - Hip joint center calculation using regression equations
    - Pelvis coordinate system transformation

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

import Kinematics.Calculation as calc
from Filters import MyFilter
import numpy as np
import time

# ============================================================================
# MARKER KINEMATICS CLASSES
# ============================================================================

class MarkerKinematicsPlugInSetQ0:
    """
    Class for performing kinematics calculations with PlugInGait marker set and Quality of 0.

    Attributes:
    - markerDictionary: A dictionary containing the positions of markers.
    - jointDictionary: A dictionary containing the positions of joints.
    - anglesDictionary: A dictionary containing the angles of joints.
    - anglesZeroDictionary: A dictionary containing the zero angles of joints.
    - pendingZerowing: A boolean indicating if a zero position is pending.
    - LegLengthL: The length of the left leg.
    - LegLengthR: The length of the right leg.
    - markerRadius: The radius of the markers.
    - pelvisTransformation: The transformation matrix for the pelvis.
    - femurTransformation: The transformation matrix for the femur.
    - filters: A dictionary containing the filters for angles.

    Methods:
    - __init__(LegLengthL, LegLengthR, markerRadius): Initializes the MarkerKinematicsPlugInSetQ0 object.
    - recordZeroPosition(): Records the zero position of the angles.
    - setFilter(window_size, samplingRate, filter_type, lowcut, highcut): Sets the filter for the angles.
    - getFilterType(): Returns the filter type.
    - filterPassThrough(data, filterName): Filters the data using the specified filter.
    - updateWithSubject(markerDictionary): Updates the marker and joint positions with the given marker dictionary.
    - getHipAngles(): Calculates the hip angles.
    - getKneeAngles(): Calculates the knee angles.
    - getAnkleAngles(): Calculates the ankle angles.
    - getHipAdductionAngles(): Calculates the hip adduction angles.
    - getSubtalarAngles(): Calculates the subtalar angles.
    - getHipIversionAngles(): Calculates the hip inversion angles.
    - get_pelvis_position(LASI, RASI): Calculates the position of the pelvis.
    - get_pelvis_transformation(LASI, RASI, LPSI, RPSI): Calculates the transformation matrix for the pelvis.
    - get_hip_joint_center(LASI, RASI, LPSI, RPSI, LegLengthL, LegLengthR, markerRadius, inGlobal): Calculates the hip joint centers.
    
    """

    def __init__(self, LegLengthL, LegLengthR, markerRadius):
        """
        Initializes a MarkerKinematics object.

        Args:
            LegLengthL (float): The length of the left leg.
            LegLengthR (float): The length of the right leg.
            markerRadius (float): The radius of the markers.

        Attributes:
            markerDictionary (dict): A dictionary to store the positions of markers.
            jointDictionary (dict): A dictionary to store the positions of joints.
            anglesDictionary (dict): A dictionary to store the angles.
            anglesZeroDictionary (dict): A dictionary to store the zero angles.
            angleFlags (dict): A dictionary to store flags for angles.
            pendingZerowing (bool): A flag indicating if a zerowing is pending.
            LegLengthL (float): The length of the left leg.
            LegLengthR (float): The length of the right leg.
            markerRadius (float): The radius of the markers.
            pelvisTransformation (numpy.ndarray): The transformation matrix for the pelvis.
            femurTransformation (numpy.ndarray): The transformation matrix for the femur.
            filters (dict): A dictionary to store filters for angles.
        """
        #[markerName] position (global)
        self.markerDictionary = {}
        self.markerDictionary['LASI'] = [0,0,0]
        self.markerDictionary['RASI'] = [0,0,0]
        self.markerDictionary['LPSI'] = [0,0,0]
        self.markerDictionary['RPSI'] = [0,0,0]
        self.markerDictionary['LKNE'] = [0,0,0]
        self.markerDictionary['RKNE'] = [0,0,0]
        self.markerDictionary['LANK'] = [0,0,0]
        self.markerDictionary['RANK'] = [0,0,0]
        self.markerDictionary['LHEE'] = [0,0,0]
        self.markerDictionary['RHEE'] = [0,0,0]
        self.markerDictionary['LTOE'] = [0,0,0]
        self.markerDictionary['RTOE'] = [0,0,0]

        #[jointName] position (global)
        self.jointDictionary = {}
        #[AngleName] angle 
        self.anglesDictionary = {}
        #[AngleName] angle
        self.anglesZeroDictionary = {}
        self.anglesZeroDictionary['LHip'] = 0
        self.anglesZeroDictionary['RHip'] = 0
        self.anglesZeroDictionary['LKnee'] = 0
        self.anglesZeroDictionary['RKnee'] = 0
        self.anglesZeroDictionary['LAnkle'] = 0
        self.anglesZeroDictionary['RAnkle'] = 0
        self.anglesZeroDictionary['LHipAdduction'] = 0
        self.anglesZeroDictionary['RHipAdduction'] = 0
        self.anglesZeroDictionary['LSubtalar'] = 0
        self.anglesZeroDictionary['RSubtalar'] = 0
        self.anglesZeroDictionary['LHipInversion'] = 0
        self.anglesZeroDictionary['RHipInversion'] = 0

        self.angleFlags = {}
        for angle in self.anglesZeroDictionary:
            #remove first letter
            self.angleFlags[angle[1:]] = False

        self.pendingZerowing = False

        #subject measurements
        self.LegLengthL = LegLengthL
        self.LegLengthR = LegLengthR
        self.markerRadius = markerRadius
        
        #Pelvis vars
        self.pelvisTransformation = np.array([])

        # Filters for angle data
        self.filters = {}
        for angle in self.anglesZeroDictionary:
            self.filters[angle] = MyFilter(1, 1, 'none')
    
    # ========================================================================
    # CALIBRATION AND FILTER METHODS
    # ========================================================================
        
    def recordZeroPosition(self):
        """
        Records the zero position for the marker kinematics.

        This method sets a flag to indicate that the zero position is pending.
        The zero position is used as a reference point for calculating the marker kinematics.

        Parameters:
            None

        Returns:
            None
        """
        self.pendingZerowing = True
    
    def setFilter(self, window_size, samplingRate, filter_type, lowcut=.0001, highcut=0):
        """
        Sets the filter parameters for the marker kinematics.

        Args:
            window_size (int): The size of the filter window.
            samplingRate (float): The sampling rate of the data.
            filter_type (str): The type of filter to be applied.
            lowcut (float, optional): The low cutoff frequency. Defaults to .0001.
            highcut (float, optional): The high cutoff frequency. Defaults to (samplingRate)/2-1.

        Returns:
            None
        """
        highcut = (samplingRate)/2-1
        for filter in self.filters:
            self.filters[filter] = MyFilter(window_size, samplingRate, filter_type, lowcut, highcut)

    def getFilterType(self):
        """
        Returns the filter type of the filter.

        Returns:
            str: The filter type of the filter.
        """
        return self.filters['LHip'].filter_type

    def filterPassThrough(self, data, filterName):
        """
        Applies a specific filter to the given data.

        Parameters:
        - data: The data to be filtered.
        - filterName: The name of the filter to be applied.

        Returns:
        The filtered data.
        """
        return self.filters[filterName].filter(data)

    # ========================================================================
    # DATA UPDATE AND CALCULATION METHODS
    # ========================================================================
    
    def updateWithSubject(self, markerDictionary):
        """
        Update marker positions and calculate all joint angles.

        This is the main update method called each frame. It:
        1. Updates marker positions
        2. Calculates pelvis transformation
        3. Calculates hip joint centers
        4. Calculates all joint angles
        5. Applies filters
        6. Handles zero position calibration

        Args:
            markerDictionary (dict): Dictionary mapping marker names to 3D positions
        """
        requiredMarkers = set(self.markerDictionary.keys())
        #select field from markerDictionary
        # self.markerDictionary = markerDictionary

        #if marker is missing, dont update it position instead keep the old location
        for marker in markerDictionary:
            if not np.all(np.array(markerDictionary[marker]) == 0):
                self.markerDictionary[marker] = markerDictionary[marker]
            # else:
            #     print(f"Marker {marker} is missing")

        if requiredMarkers != set(self.markerDictionary.keys()):
            print("Marker dictionary does not contain all required markers")
            #Check if all markers are present
            for ReqMarker in requiredMarkers:
                if ReqMarker not in markerDictionary:
                    self.markerDictionary[ReqMarker] = (0,0,0)


        # Calculate the position of the pelvis as the midpoint between the PSIS markers
        self.pelvisLocation = self.get_pelvis_position(self.markerDictionary['LASI'], self.markerDictionary['RASI'])
    

        
        #Calculate the pelvis transformation matrix
        self.pelvisTransformation = self.get_pelvis_transformation(self.pelvisLocation, self.markerDictionary['LASI'], self.markerDictionary['RASI'],
                                                                    self.markerDictionary['LPSI'], self.markerDictionary['RPSI'])


        #Calculate the joint positions ***IN THE PELVIS COORDINATE SYSTEM***
        LHJC, RHJC = self.get_hip_joint_center(self.markerDictionary['LASI'], self.markerDictionary['RASI'],
                                                self.markerDictionary['LPSI'], self.markerDictionary['RPSI'], 
                                                self.LegLengthL, self.LegLengthR, self.markerRadius)
        
        
        if not np.all(LHJC == 0):
            self.jointDictionary['LHJC'] = LHJC #in pelvis coordinate system
        elif not 'LHJC' in self.jointDictionary:
            self.jointDictionary['LHJC'] = np.array([[0,0,0]])

        if not np.all(RHJC == 0):
            self.jointDictionary['RHJC'] = RHJC #in pelvis coordinate system
        elif not 'RHJC' in self.jointDictionary:
            self.jointDictionary['RHJC'] = np.array([[0,0,0]])

        #Calculate the knee joint centers (assume knee joint center is knee marker)
        self.jointDictionary['LKJC'] = self.markerDictionary['LKNE']
        self.jointDictionary['RKJC'] = self.markerDictionary['RKNE']

        #Calculate the ankle joint centers (assume ankle joint center is ankle marker)
        self.jointDictionary['LAKJC'] = self.markerDictionary['LANK']
        self.jointDictionary['RAKJC'] = self.markerDictionary['RANK']

        #Get angles
        LHipAngle, RHipAngle = self.getHipAngles()
        self.anglesDictionary['LHip'] = self.filterPassThrough(LHipAngle - self.anglesZeroDictionary['LHip'], 'LHip')
        self.anglesDictionary['RHip'] = self.filterPassThrough(RHipAngle - self.anglesZeroDictionary['RHip'], 'RHip')
            

        LKneeAngle, RKneeAngle = self.getKneeAngles()
        self.anglesDictionary['LKnee'] = self.filterPassThrough(LKneeAngle - self.anglesZeroDictionary['LKnee'], 'LKnee')
        self.anglesDictionary['RKnee'] = self.filterPassThrough(RKneeAngle - self.anglesZeroDictionary['RKnee'], 'RKnee')

        LAnkleAngle, RAnkleAngle = self.getAnkleAngles()
        self.anglesDictionary['LAnkle'] = self.filterPassThrough(LAnkleAngle - self.anglesZeroDictionary['LAnkle'], 'LAnkle')
        self.anglesDictionary['RAnkle'] = self.filterPassThrough(RAnkleAngle - self.anglesZeroDictionary['RAnkle'], 'RAnkle')

        LHipAdductionAngle, RHipAdductionAngle = self.getHipAdductionAngles()
        self.anglesDictionary['LHipAdduction'] = self.filterPassThrough(LHipAdductionAngle - self.anglesZeroDictionary['LHipAdduction'], 'LHipAdduction')
        self.anglesDictionary['RHipAdduction'] = self.filterPassThrough(RHipAdductionAngle - self.anglesZeroDictionary['RHipAdduction'], 'RHipAdduction')

        LSubtalarAngle, RSubtalarAngle = self.getSubtalarAngles()
        self.anglesDictionary['LSubtalar'] = self.filterPassThrough(LSubtalarAngle - self.anglesZeroDictionary['LSubtalar'], 'LSubtalar')
        self.anglesDictionary['RSubtalar'] = self.filterPassThrough(RSubtalarAngle - self.anglesZeroDictionary['RSubtalar'], 'RSubtalar')

        LHipInversionAngle, RHipInversionAngle = self.getHipIversionAngles()
        self.anglesDictionary['LHipInversion'] = self.filterPassThrough(LHipInversionAngle - self.anglesZeroDictionary['LHipInversion'], 'LHipInversion')
        self.anglesDictionary['RHipInversion'] = self.filterPassThrough(RHipInversionAngle - self.anglesZeroDictionary['RHipInversion'], 'RHipInversion')

        if self.pendingZerowing:
            self.pendingZerowing = False
            for angle in self.anglesDictionary:
                self.anglesZeroDictionary[angle] = self.anglesDictionary[angle]+self.anglesZeroDictionary[angle]
    
    # ========================================================================
    # JOINT ANGLE CALCULATION METHODS
    # ========================================================================
        
    def getHipAngles(self):
        """
        Calculate the hip angles.

        Args:
        None

        Returns:
        - LAngle: The left hip angle.
        - RAngle: The right hip angle.
        """
        v2 = [0,0,-1]

        # compute in pelvis coordinate system
        v1 = calc.compute_segment_vector((self.jointDictionary['LHJC']),
                                        self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']))[0]
        LAngle = -calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        
        v1 = calc.compute_segment_vector((self.jointDictionary['RHJC']),
                                        self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']))[0]
        RAngle = -calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        return LAngle, RAngle
    
    def getKneeAngles(self):
        """
        Calculate the knee angles.

        Args:
        None

        Returns:
        - LAngle: The left knee angle.
        - RAngle: The right knee angle.
        """
        #compute in pelvis coordinate system
        v1 = calc.compute_segment_vector((self.jointDictionary['LHJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']))[0]
        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']))

        LAngle = -calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        v1 = calc.compute_segment_vector((self.jointDictionary['RHJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']))[0]
        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']))
        RAngle = -calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        return LAngle, RAngle
        
    def getAnkleAngles(self):
        """
        Calculate the ankle angles.

        Args:
        None

        Returns:
        - LAngle: The left ankle angle.
        - RAngle: The right ankle angle.
        """
        #compute in pelvis coordinate system
        v1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']))
        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LHEE']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LTOE']))
        LAngle = calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        v1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']))
        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RHEE']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RTOE']))
        RAngle = calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        return LAngle, RAngle

    
    def getHipAdductionAngles(self):
        """
        Calculates the hip adduction angles for the left and right hip joints.

        Returns:
            Tuple[float, float]: A tuple containing the left and right hip adduction angles in degrees.
        """
        v1 = [0, 0, -1]
        v2 = calc.compute_segment_vector((self.jointDictionary['LHJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']))[0]
        
        LAngle = -calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        v2 = calc.compute_segment_vector((self.jointDictionary['RHJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']))[0]
        RAngle = calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        return LAngle, RAngle
    

    def getSubtalarAngles(self):
        """
        Calculates the subtalar angles for the left and right foot.

        Returns:
            tuple: A tuple containing the subtalar angle for the left foot and the subtalar angle for the right foot.
        """
        v1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']))

        v2_1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LHEE']))
        v2_2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LTOE']))
        v2 = np.cross(v2_1, v2_2)
        LAngle = calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        v1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']))
        
        v2_1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RHEE']))
        v2_2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RTOE']))
        v2 = np.cross(v2_1, v2_2)
        RAngle = calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        return LAngle, RAngle
    
    def getHipIversionAngles(self):
        """
        Calculates the hip inversion angles for the left and right legs.

        Returns:
            Tuple[float, float]: A tuple containing the left and right hip inversion angles in degrees.
        """
        v1 = [1, 0, 0]
        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LHEE']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LTOE']))
        LAngle = calc.calculate_2d_angle([v1[0], v1[1]], [v2[0], v2[1]])

        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RHEE']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RTOE']))
        
        RAngle = calc.calculate_2d_angle([v1[0], v1[1]], [v2[0], v2[1]])

        return LAngle, RAngle
    





    # ========================================================================
    # BIOMECHANICAL MODEL CALCULATIONS
    # ========================================================================
    
    def get_pelvis_position(self, LASI, RASI):
        """
        Calculate the pelvis origin as the midpoint between LASI and RASI markers.

        Parameters:
        LASI (numpy.ndarray): The position of the LASI marker.
        RASI (numpy.ndarray): The position of the RASI marker.

        Returns:
        numpy.ndarray: The position of the pelvis.

        """
        # Ensure that points are in numpy array
        LASI = np.array(LASI)
        RASI = np.array(RASI)

        # Calculate the position of the pelvis as the midpoint between the LASI and RASI markers
        pelvis_position = (LASI + RASI) / 2
        return pelvis_position

    def get_pelvis_transformation(self, pelvis_position, LASI, RASI, LPSI, RPSI):
        """
        Calculates the transformation matrix for the pelvis based on the given marker positions.

        Parameters:
        LASI (numpy.ndarray): Position of the left anterior superior iliac spine marker.
        RASI (numpy.ndarray): Position of the right anterior superior iliac spine marker.
        LPSI (numpy.ndarray): Position of the left posterior superior iliac spine marker.
        RPSI (numpy.ndarray): Position of the right posterior superior iliac spine marker.

        Returns:
        numpy.ndarray: Transformation matrix for the pelvis.

        """
        #ensure that points are in numpy array
        LASI = np.array(LASI)
        RASI = np.array(RASI)
        LPSI = np.array(LPSI)
        RPSI = np.array(RPSI)

        #The dominant axis, taken as the Y axis, is the direction from the right asis marker to the left asis marker    ###Y
        pelvis_direction = LASI - RASI
        pelvis_direction = pelvis_direction / np.linalg.norm(pelvis_direction)

        # The secondary direction is taken as the direction from the sacrum marker to the right asis marker
        if not np.all(LPSI == 0) and not np.all(RPSI == 0):        
            sacral = (LPSI + RPSI) / 2
            pelvis_right_vector = RASI - sacral
        elif not np.all(LPSI == 0):
            pelvis_right_vector = RASI - LPSI
        elif not np.all(RPSI == 0):
            pelvis_right_vector = RASI - RPSI
        else:
            sacral = (LPSI + RPSI) / 2
            pelvis_right_vector = RASI - sacral
        pelvis_right_vector = pelvis_right_vector / np.linalg.norm(pelvis_right_vector)

        #The Z direction is generally upwards, perpendicular to this plane
        pelvis_up_vector = np.cross(pelvis_right_vector, pelvis_direction)
        pelvis_up_vector = pelvis_up_vector / np.linalg.norm(pelvis_up_vector)

        # Complete the orthonormal basis
        pelvis_right_vector = np.cross(pelvis_direction, pelvis_up_vector)
        pelvis_right_vector = pelvis_right_vector / np.linalg.norm(pelvis_right_vector)

        # Create the transformation
        pelvis_transformation = np.array([pelvis_right_vector, pelvis_direction, pelvis_up_vector]).T

        #Add position giving transformation matrix
        pelvis_transformation = np.hstack([pelvis_transformation, pelvis_position.reshape(3,1)])
        pelvis_transformation = np.vstack([pelvis_transformation, [0, 0, 0, 1]])

        return pelvis_transformation

    def get_hip_joint_center(self, LASI, RASI, LPSI, RPSI, LegLengthL, LegLengthR, markerRadius):
        """
        Calculates the coordinates of the hip joint center based on the given markers and parameters.

        Parameters:
        LASI (list): The coordinates of the left anterior superior iliac spine marker.
        RASI (list): The coordinates of the right anterior superior iliac spine marker.
        LPSI (list): The coordinates of the left posterior superior iliac spine marker.
        RPSI (list): The coordinates of the right posterior superior iliac spine marker.
        LegLengthL (float): The length of the left leg.
        LegLengthR (float): The length of the right leg.
        markerRadius (float): The radius of the marker.

        Returns:
        tuple: A tuple containing the coordinates of the left hip joint center and the right hip joint center.

        """
        #ensure that points are in numpy array
        LASI = np.array(LASI)
        RASI = np.array(RASI)
        LPSI = np.array(LPSI)
        RPSI = np.array(RPSI)

        #check if markers are present
        if np.all(LASI == 0) or np.all(RASI == 0):
            return np.array([[0,0,0]]), np.array([[0,0,0]])
        

        AsisTrocDistL = .1288 * LegLengthL - 48.56
        AsisTrocDistR = .1288 * LegLengthR - 48.56
        MeanLegLength = (LegLengthL + LegLengthR) / 2

        interAsisDistance = calc.calculate_distance(LASI, RASI)
        C = MeanLegLength*.115 - 15.3

        theta = .5
        beta = .314

        #Calculate Left Side 
        if not np.all(LPSI == 0):
            X = C*np.cos(theta)*np.sin(beta) - (AsisTrocDistL + markerRadius) * np.cos(beta)
            Y = -(C*np.sin(theta) - interAsisDistance/2)
            Z = -C*np.cos(theta)*np.cos(beta) - (AsisTrocDistL + markerRadius) * np.sin(beta)
            hip_joint_centerL = np.array([[X, Y, Z]])
        else:
            hip_joint_centerL = np.array([[0,0,0]])

        #Calculate Right Side
        if not np.all(RPSI == 0):
            X = C*np.cos(theta)*np.sin(beta) - (AsisTrocDistR + markerRadius) * np.cos(beta)
            Y = (C*np.sin(theta) - interAsisDistance/2)
            Z = -C*np.cos(theta)*np.cos(beta) - (AsisTrocDistR + markerRadius) * np.sin(beta)
            hip_joint_centerR = np.array([[X, Y, Z]])
        else:
            hip_joint_centerR = np.array([[0,0,0]])

        
        return hip_joint_centerL, hip_joint_centerR

    def globalToPelvisFrame(self, pelvis_transformation, point):
        """
        Transforms a point from the global coordinate frame to the pelvis coordinate frame.

        Args:
            pelvis_transformation (numpy.ndarray): The transformation matrix representing the pelvis frame.
            point (numpy.ndarray): The point to be transformed.

        Returns:
            numpy.ndarray: The transformed point in the pelvis coordinate frame.
        """
        # Ensure that points are in numpy array
        point = np.array(point)

        # Default transformation matrix is pelvis to global, inverse it to get global to pelvis
        pelvis_transformation = np.linalg.inv(pelvis_transformation)

        point = np.reshape(point, (3, 1)).T
        # Apply the pelvis transformation to the point
        point = calc.transform_using_transformation_matrix(pelvis_transformation, point)[0]

        return point

class MarkerKinematicsPlugInSetQ1:
    """
    Class for performing kinematics calculations with PlugInGait marker set and Quality of 1.

    Attributes:
    - markerDictionary: A dictionary containing the positions of markers.
    - jointDictionary: A dictionary containing the positions of joints.
    - anglesDictionary: A dictionary containing the angles of joints.
    - anglesZeroDictionary: A dictionary containing the zero angles of joints.
    - pendingZerowing: A boolean indicating if a zero position is pending.
    - LegLengthL: The length of the left leg.
    - LegLengthR: The length of the right leg.
    - markerRadius: The radius of the markers.
    - pelvisTransformation: The transformation matrix for the pelvis.
    - femurTransformation: The transformation matrix for the femur.
    - filters: A dictionary containing the filters for angles.

    Methods:
    - __init__(LegLengthL, LegLengthR, markerRadius): Initializes the MarkerKinematicsPlugInSetQ0 object.
    - recordZeroPosition(): Records the zero position of the angles.
    - setFilter(window_size, samplingRate, filter_type, lowcut, highcut): Sets the filter for the angles.
    - getFilterType(): Returns the filter type.
    - filterPassThrough(data, filterName): Filters the data using the specified filter.
    - updateWithSubject(markerDictionary): Updates the marker and joint positions with the given marker dictionary.
    - getHipAngles(): Calculates the hip angles.
    - getKneeAngles(): Calculates the knee angles.
    - getAnkleAngles(): Calculates the ankle angles.
    - getHipAdductionAngles(): Calculates the hip adduction angles.
    - getSubtalarAngles(): Calculates the subtalar angles.
    - getHipIversionAngles(): Calculates the hip inversion angles.
    - get_pelvis_position(LASI, RASI): Calculates the position of the pelvis.
    - get_pelvis_transformation(LASI, RASI, LPSI, RPSI): Calculates the transformation matrix for the pelvis.
    - get_hip_joint_center(LASI, RASI, LPSI, RPSI, LegLengthL, LegLengthR, markerRadius, inGlobal): Calculates the hip joint centers.
    
    """

    def __init__(self, LegLengthL, LegLengthR, LKneeWidth, RKneeWidth, LAnkleWidth, RAnkleWidth, markerRadius):
        """
        Initializes a MarkerKinematics object.

        Args:
            LegLengthL (float): The length of the left leg.
            LegLengthR (float): The length of the right leg.
            LKneeWidth (float): The width of the left knee.
            RKneeWidth (float): The width of the right knee.
            LAnkleWidth (float): The width of the left ankle.
            RAnkleWidth (float): The width of the right ankle.
            markerRadius (float): The radius of the markers.

        Attributes:
            markerDictionary (dict): A dictionary to store the positions of markers.
            jointDictionary (dict): A dictionary to store the positions of joints.
            anglesDictionary (dict): A dictionary to store the angles.
            anglesZeroDictionary (dict): A dictionary to store the zero angles.
            angleFlags (dict): A dictionary to store flags for angles.
            pendingZerowing (bool): A flag indicating if a zerowing is pending.
            LegLengthL (float): The length of the left leg.
            LegLengthR (float): The length of the right leg.
            LKneeWidth (float): The width of the left knee.
            RKneeWidth (float): The width of the right knee.
            LAnkleWidth (float): The width of the left ankle.
            RAnkleWidth (float): The width of the right ankle.
            markerRadius (float): The radius of the markers.
            pelvisTransformation (numpy.ndarray): The transformation matrix for the pelvis.
            femurTransformation (numpy.ndarray): The transformation matrix for the femur.
            filters (dict): A dictionary to store filters for angles.
        """
        #[markerName] position (global)
        self.markerDictionary = {}
        self.markerDictionary['LASI'] = [0,0,0]
        self.markerDictionary['RASI'] = [0,0,0]
        self.markerDictionary['LPSI'] = [0,0,0]
        self.markerDictionary['RPSI'] = [0,0,0]
        self.markerDictionary['LTHI'] = [0,0,0]
        self.markerDictionary['RTHI'] = [0,0,0]
        self.markerDictionary['LKNE'] = [0,0,0]
        self.markerDictionary['RKNE'] = [0,0,0]
        self.markerDictionary['LTIB'] = [0,0,0]
        self.markerDictionary['RTIB'] = [0,0,0]
        self.markerDictionary['LANK'] = [0,0,0]
        self.markerDictionary['RANK'] = [0,0,0]
        self.markerDictionary['LHEE'] = [0,0,0]
        self.markerDictionary['RHEE'] = [0,0,0]
        self.markerDictionary['LTOE'] = [0,0,0]
        self.markerDictionary['RTOE'] = [0,0,0]

        #[jointName] position (global)
        self.jointDictionary = {}
        #[AngleName] angle 
        self.anglesDictionary = {}
        #[AngleName] angle
        self.anglesZeroDictionary = {}
        self.anglesZeroDictionary['LHip'] = 0
        self.anglesZeroDictionary['RHip'] = 0
        self.anglesZeroDictionary['LKnee'] = 0
        self.anglesZeroDictionary['RKnee'] = 0
        self.anglesZeroDictionary['LAnkle'] = 0
        self.anglesZeroDictionary['RAnkle'] = 0
        self.anglesZeroDictionary['LHipAdduction'] = 0
        self.anglesZeroDictionary['RHipAdduction'] = 0
        self.anglesZeroDictionary['LSubtalar'] = 0
        self.anglesZeroDictionary['RSubtalar'] = 0
        self.anglesZeroDictionary['LHipInversion'] = 0
        self.anglesZeroDictionary['RHipInversion'] = 0

        self.angleFlags = {}
        for angle in self.anglesZeroDictionary:
            #remove first letter
            self.angleFlags[angle[1:]] = False

        self.pendingZerowing = False

        #subject measurements
        self.LegLengthL = LegLengthL
        self.LegLengthR = LegLengthR
        self.LKneeWidth = LKneeWidth
        self.RKneeWidth = RKneeWidth
        self.LAnkleWidth = LAnkleWidth
        self.RAnkleWidth = RAnkleWidth
        self.markerRadius = markerRadius
        
        #Pelvis vars
        self.pelvisTransformation = np.array([])

        # Filters for angle data
        self.filters = {}
        for angle in self.anglesZeroDictionary:
            self.filters[angle] = MyFilter(1, 1, 'none')
    
    # ========================================================================
    # CALIBRATION AND FILTER METHODS
    # ========================================================================
        
    def recordZeroPosition(self):
        """
        Records the zero position for the marker kinematics.

        This method sets a flag to indicate that the zero position is pending.
        The zero position is used as a reference point for calculating the marker kinematics.

        Parameters:
            None

        Returns:
            None
        """
        self.pendingZerowing = True
    
    def setFilter(self, window_size, samplingRate, filter_type, lowcut=.0001, highcut=0):
        """
        Sets the filter parameters for the marker kinematics.

        Args:
            window_size (int): The size of the filter window.
            samplingRate (float): The sampling rate of the data.
            filter_type (str): The type of filter to be applied.
            lowcut (float, optional): The low cutoff frequency. Defaults to .0001.
            highcut (float, optional): The high cutoff frequency. Defaults to (samplingRate)/2-1.

        Returns:
            None
        """
        highcut = (samplingRate)/2-1
        for filter in self.filters:
            self.filters[filter] = MyFilter(window_size, samplingRate, filter_type, lowcut, highcut)

    def getFilterType(self):
        """
        Returns the filter type of the filter.

        Returns:
            str: The filter type of the filter.
        """
        return self.filters['LHip'].filter_type

    def filterPassThrough(self, data, filterName):
        """
        Applies a specific filter to the given data.

        Parameters:
        - data: The data to be filtered.
        - filterName: The name of the filter to be applied.

        Returns:
        The filtered data.
        """
        return self.filters[filterName].filter(data)

    # ========================================================================
    # DATA UPDATE AND CALCULATION METHODS
    # ========================================================================
    
    def updateWithSubject(self, markerDictionary):
        """
        Update marker positions and calculate all joint angles.

        This is the main update method called each frame. It:
        1. Updates marker positions
        2. Calculates pelvis transformation
        3. Calculates hip joint centers
        4. Calculates all joint angles
        5. Applies filters
        6. Handles zero position calibration

        Args:
            markerDictionary (dict): Dictionary mapping marker names to 3D positions
        """
        requiredMarkers = set(self.markerDictionary.keys())
        #select field from markerDictionary
        # self.markerDictionary = markerDictionary

        #if marker is missing, dont update it position instead keep the old location
        for marker in markerDictionary:
            if not np.all(np.array(markerDictionary[marker]) == 0):
                self.markerDictionary[marker] = markerDictionary[marker]
            # else:
            #     print(f"Marker {marker} is missing")

        if requiredMarkers != set(self.markerDictionary.keys()):
            print("Marker dictionary does not contain all required markers")
            #Check if all markers are present
            for ReqMarker in requiredMarkers:
                if ReqMarker not in markerDictionary:
                    self.markerDictionary[ReqMarker] = (0,0,0)


        # Calculate the position of the pelvis as the midpoint between the PSIS markers
        self.pelvisLocation = self.get_pelvis_position(self.markerDictionary['LASI'], self.markerDictionary['RASI'])
    

        
        #Calculate the pelvis transformation matrix
        self.pelvisTransformation = self.get_pelvis_transformation(self.pelvisLocation, self.markerDictionary['LASI'], self.markerDictionary['RASI'],
                                                                    self.markerDictionary['LPSI'], self.markerDictionary['RPSI'])


        #Calculate the joint positions ***IN THE PELVIS COORDINATE SYSTEM***
        LHJC, RHJC = self.get_hip_joint_center(self.markerDictionary['LASI'], self.markerDictionary['RASI'],
                                                self.markerDictionary['LPSI'], self.markerDictionary['RPSI'], 
                                                self.LegLengthL, self.LegLengthR, self.markerRadius)
        #***NOW IN GLOBAL COORDINATE SYSTEM***
        LHJC = self.pelvisToGlobalFrame(self.pelvisTransformation, LHJC)
        RHJC = self.pelvisToGlobalFrame(self.pelvisTransformation, RHJC)

        
        if not np.all(LHJC == 0):
            self.jointDictionary['LHJC'] = LHJC #in global coordinate system
        elif not 'LHJC' in self.jointDictionary:
            self.jointDictionary['LHJC'] = np.array([[0,0,0]])

        if not np.all(RHJC == 0):
            self.jointDictionary['RHJC'] = RHJC #in global coordinate system
        elif not 'RHJC' in self.jointDictionary:
            self.jointDictionary['RHJC'] = np.array([[0,0,0]])

        startTime = time.time()
        LKJC, RKJC, leftKneePlaneNormal, rightKneePlaneNormal = self.get_knee_joint_center(
            LHJC, self.markerDictionary['LTHI'], self.markerDictionary['LKNE'], 
            RHJC, self.markerDictionary['RTHI'], self.markerDictionary['RKNE'], 
            self.LKneeWidth, self.RKneeWidth
        )
        self.jointDictionary['LKJC'] = LKJC
        self.jointDictionary['RKJC'] = RKJC
        endTime = time.time()
        # print(f"Time taken to get knee joint centers: {endTime - startTime} seconds")
        # print(f"LKJC: {LKJC}, RKJC: {RKJC}")
        LAKJC, RAKJC, leftAnklePlaneNormal, rightAnklePlaneNormal = self.get_ankle_joint_center(
            LKJC, self.markerDictionary['LTIB'], self.markerDictionary['LANK'],
            RKJC, self.markerDictionary['RTIB'], self.markerDictionary['RANK'],
            self.LAnkleWidth, self.RAnkleWidth
        )
        self.jointDictionary['LAKJC'] = LAKJC
        self.jointDictionary['RAKJC'] = RAKJC

        #Get angles
        timeStart = time.time()
        LHipAngle, RHipAngle = self.getHipAngles()
        self.anglesDictionary['LHip'] = self.filterPassThrough(LHipAngle - self.anglesZeroDictionary['LHip'], 'LHip')
        self.anglesDictionary['RHip'] = self.filterPassThrough(RHipAngle - self.anglesZeroDictionary['RHip'], 'RHip')
        timeEnd = time.time()
        # print(f"Time taken to get hip angles: {timeEnd - timeStart} seconds")
        # print(f"LHipAngle: {LHipAngle}, RHipAngle: {RHipAngle}")

        timeStart = time.time()
        LKneeAngle, RKneeAngle = self.getKneeAngles(leftKneePlaneNormal, rightKneePlaneNormal)
        self.anglesDictionary['LKnee'] = self.filterPassThrough(LKneeAngle - self.anglesZeroDictionary['LKnee'], 'LKnee')
        self.anglesDictionary['RKnee'] = self.filterPassThrough(RKneeAngle - self.anglesZeroDictionary['RKnee'], 'RKnee')
        timeEnd = time.time()
        # print(f"Time taken to get knee angles: {timeEnd - timeStart} seconds")
        # print(f"LKneeAngle: {LKneeAngle}, RKneeAngle: {RKneeAngle}")

        timeStart = time.time()
        LAnkleAngle, RAnkleAngle = self.getAnkleAngles(leftAnklePlaneNormal, rightAnklePlaneNormal)
        self.anglesDictionary['LAnkle'] = self.filterPassThrough(LAnkleAngle - self.anglesZeroDictionary['LAnkle'], 'LAnkle')
        self.anglesDictionary['RAnkle'] = self.filterPassThrough(RAnkleAngle - self.anglesZeroDictionary['RAnkle'], 'RAnkle')
        timeEnd = time.time()
        # print(f"Time taken to get ankle angles: {timeEnd - timeStart} seconds")
        # print(f"LAnkleAngle: {LAnkleAngle}, RAnkleAngle: {RAnkleAngle}")

        timeStart = time.time()
        LHipAdductionAngle, RHipAdductionAngle = self.getHipAdductionAngles()
        self.anglesDictionary['LHipAdduction'] = self.filterPassThrough(LHipAdductionAngle - self.anglesZeroDictionary['LHipAdduction'], 'LHipAdduction')
        self.anglesDictionary['RHipAdduction'] = self.filterPassThrough(RHipAdductionAngle - self.anglesZeroDictionary['RHipAdduction'], 'RHipAdduction')
        timeEnd = time.time()
        # print(f"Time taken to get hip adduction angles: {timeEnd - timeStart} seconds")
        # print(f"LHipAdductionAngle: {LHipAdductionAngle}, RHipAdductionAngle: {RHipAdductionAngle}")

        timeStart = time.time()
        LSubtalarAngle, RSubtalarAngle = self.getSubtalarAngles()
        self.anglesDictionary['LSubtalar'] = self.filterPassThrough(LSubtalarAngle - self.anglesZeroDictionary['LSubtalar'], 'LSubtalar')
        self.anglesDictionary['RSubtalar'] = self.filterPassThrough(RSubtalarAngle - self.anglesZeroDictionary['RSubtalar'], 'RSubtalar')
        timeEnd = time.time()
        # print(f"Time taken to get subtalar angles: {timeEnd - timeStart} seconds")
        # print(f"LSubtalarAngle: {LSubtalarAngle}, RSubtalarAngle: {RSubtalarAngle}")

        timeStart = time.time()
        LHipInversionAngle, RHipInversionAngle = self.getHipIversionAngles()
        self.anglesDictionary['LHipInversion'] = self.filterPassThrough(LHipInversionAngle - self.anglesZeroDictionary['LHipInversion'], 'LHipInversion')
        self.anglesDictionary['RHipInversion'] = self.filterPassThrough(RHipInversionAngle - self.anglesZeroDictionary['RHipInversion'], 'RHipInversion')
        timeEnd = time.time()
        # print(f"Time taken to get hip inversion angles: {timeEnd - timeStart} seconds")
        # print(f"LHipInversionAngle: {LHipInversionAngle}, RHipInversionAngle: {RHipInversionAngle}")

        if self.pendingZerowing:
            self.pendingZerowing = False
            for angle in self.anglesDictionary:
                self.anglesZeroDictionary[angle] = self.anglesDictionary[angle]+self.anglesZeroDictionary[angle]
    
    # ========================================================================
    # JOINT ANGLE CALCULATION METHODS
    # ========================================================================
        
    def getHipAngles(self):
        """
        Calculate the hip angles.

        Args:
        None

        Returns:
        - LAngle: The left hip angle.
        - RAngle: The right hip angle.
        """
        v2 = [0, 0, -1]

        LHJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LHJC'])
        LKJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC'])

        v1 = calc.compute_segment_vector(LHJC_pelvis, LKJC_pelvis)
        LAngle = -calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        RHJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RHJC'])
        RKJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC'])

        v1 = calc.compute_segment_vector(RHJC_pelvis, RKJC_pelvis)
        RAngle = -calc.calculate_2d_angle([v1[0], v1[2]], [v2[0], v2[2]])

        return LAngle, RAngle
    
    def getKneeAngles(self, leftKneePlaneNormal, rightKneePlaneNormal):
        """
        Calculate the knee angles.

        Args:
        None

        Returns:
        - LAngle: The left knee angle.
        - RAngle: The right knee angle.
        """
        # --- Left Knee ---
        leftThighAxis = np.array(self.jointDictionary['LKJC']) - np.array(self.jointDictionary['LHJC'])
        leftShankAxis = np.array(self.jointDictionary['LAKJC']) - np.array(self.jointDictionary['LKJC'])

        s1_hat = leftKneePlaneNormal / np.linalg.norm(leftKneePlaneNormal)
        leftThighAxis_hat = leftThighAxis / np.linalg.norm(leftThighAxis)

        # Medio-lateral axis: perpendicular to both the plane normal and thigh axis
        v_left = np.cross(s1_hat, leftThighAxis_hat)
        v_left_hat = v_left / np.linalg.norm(v_left)

        # Project shank into the sagittal plane (remove medio-lateral component)
        leftShankAxis_proj = leftShankAxis - np.dot(leftShankAxis, v_left_hat) * v_left_hat
        leftShankAxis_hat = leftShankAxis_proj / np.linalg.norm(leftShankAxis_proj)

        cross_vec = np.cross(leftThighAxis_hat, leftShankAxis_hat)
        sin_component = np.dot(cross_vec, v_left_hat)
        cos_component = np.dot(leftThighAxis_hat, leftShankAxis_hat)
        LAngle = -np.degrees(np.arctan2(sin_component, cos_component))



        # --- Right Knee ---
        rightThighAxis = np.array(self.jointDictionary['RKJC']) - np.array(self.jointDictionary['RHJC'])
        rightShankAxis = np.array(self.jointDictionary['RAKJC']) - np.array(self.jointDictionary['RKJC'])

        s1_right_hat = rightKneePlaneNormal / np.linalg.norm(rightKneePlaneNormal)
        rightThighAxis_hat = rightThighAxis / np.linalg.norm(rightThighAxis)

        v_right = np.cross(s1_right_hat, rightThighAxis_hat)
        v_right_hat = v_right / np.linalg.norm(v_right)

        rightShankAxis_proj = rightShankAxis - np.dot(rightShankAxis, v_right_hat) * v_right_hat
        rightShankAxis_hat = rightShankAxis_proj / np.linalg.norm(rightShankAxis_proj)

        cross_vec = np.cross(rightThighAxis_hat, rightShankAxis_hat)
        sin_component = np.dot(cross_vec, v_right_hat)
        cos_component = np.dot(rightThighAxis_hat, rightShankAxis_hat)
        RAngle = np.degrees(np.arctan2(sin_component, cos_component))

        return LAngle, RAngle
        
    def getAnkleAngles(self, leftAnklePlaneNormal, rightAnklePlaneNormal):
        """
        Calculate the ankle angles (dorsiflexion/plantarflexion).
        """
        # --- Left ankle ---
        leftShankAxis = np.array(self.jointDictionary['LAKJC']) - np.array(self.jointDictionary['LKJC'])
        leftFootAxis = np.array(self.markerDictionary['LTOE']) - np.array(self.markerDictionary['LHEE'])

        s1_hat = leftAnklePlaneNormal / np.linalg.norm(leftAnklePlaneNormal)
        leftShankAxis_hat = leftShankAxis / np.linalg.norm(leftShankAxis)

        v_left = np.cross(s1_hat, leftShankAxis_hat)
        v_left_hat = v_left / np.linalg.norm(v_left)

        leftFootAxis_proj = leftFootAxis - np.dot(leftFootAxis, v_left_hat) * v_left_hat
        leftFootAxis_hat = leftFootAxis_proj / np.linalg.norm(leftFootAxis_proj)

        cross_vec = np.cross(leftShankAxis_hat, leftFootAxis_hat)
        sin_component = np.dot(cross_vec, v_left_hat)
        cos_component = np.dot(leftShankAxis_hat, leftFootAxis_hat)
        LAngle = np.degrees(np.arctan2(sin_component, cos_component))

        # --- Right ankle ---
        rightShankAxis = np.array(self.jointDictionary['RAKJC']) - np.array(self.jointDictionary['RKJC'])
        rightFootAxis = np.array(self.markerDictionary['RTOE']) - np.array(self.markerDictionary['RHEE'])

        s1_right_hat = rightAnklePlaneNormal / np.linalg.norm(rightAnklePlaneNormal)
        rightShankAxis_hat = rightShankAxis / np.linalg.norm(rightShankAxis)

        v_right = np.cross(s1_right_hat, rightShankAxis_hat)
        v_right_hat = v_right / np.linalg.norm(v_right)

        rightFootAxis_proj = rightFootAxis - np.dot(rightFootAxis, v_right_hat) * v_right_hat
        rightFootAxis_hat = rightFootAxis_proj / np.linalg.norm(rightFootAxis_proj)

        cross_vec = np.cross(rightShankAxis_hat, rightFootAxis_hat)
        sin_component = np.dot(cross_vec, v_right_hat)
        cos_component = np.dot(rightShankAxis_hat, rightFootAxis_hat)
        RAngle = np.degrees(np.arctan2(sin_component, cos_component))

        LAngle = LAngle - 90
        RAngle = -RAngle - 90

        return LAngle, RAngle

    
    def getHipAdductionAngles(self):
        """
        Calculates the hip adduction angles for the left and right hip joints.

        Returns:
            Tuple[float, float]: A tuple containing the left and right hip adduction angles in degrees.
        """
        v1 = [0, 0, -1]

        LHJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LHJC'])
        LKJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC'])
        v2 = calc.compute_segment_vector(LHJC_pelvis, LKJC_pelvis)
        
        LAngle = -calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        RHJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RHJC'])
        RKJC_pelvis = self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC'])
        v2 = calc.compute_segment_vector(RHJC_pelvis, RKJC_pelvis)
        RAngle = calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        return LAngle, RAngle
    

    def getSubtalarAngles(self):
        """
        Calculates the subtalar angles for the left and right foot.

        Returns:
            tuple: A tuple containing the subtalar angle for the left foot and the subtalar angle for the right foot.
        """
        v1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']))

        v2_1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LHEE']))
        v2_2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['LAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LTOE']))
        v2 = np.cross(v2_1, v2_2)
        LAngle = calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        v1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RKJC']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']))
        
        v2_1 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RHEE']))
        v2_2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.jointDictionary['RAKJC']),
                                           self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RTOE']))
        v2 = np.cross(v2_1, v2_2)
        RAngle = calc.calculate_2d_angle([v1[1], v1[2]], [v2[1], v2[2]])

        return LAngle, RAngle
    
    def getHipIversionAngles(self):
        """
        Calculates the hip inversion angles for the left and right legs.

        Returns:
            Tuple[float, float]: A tuple containing the left and right hip inversion angles in degrees.
        """
        v1 = [1, 0, 0]
        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LHEE']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['LTOE']))
        LAngle = calc.calculate_2d_angle([v1[0], v1[1]], [v2[0], v2[1]])

        v2 = calc.compute_segment_vector(self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RHEE']),
                                         self.globalToPelvisFrame(self.pelvisTransformation, self.markerDictionary['RTOE']))
        
        RAngle = calc.calculate_2d_angle([v1[0], v1[1]], [v2[0], v2[1]])

        return LAngle, RAngle
    





    # ========================================================================
    # BIOMECHANICAL MODEL CALCULATIONS
    # ========================================================================
    
    def get_pelvis_position(self, LASI, RASI):
        """
        Calculate the pelvis origin as the midpoint between LASI and RASI markers.

        Parameters:
        LASI (numpy.ndarray): The position of the LASI marker.
        RASI (numpy.ndarray): The position of the RASI marker.

        Returns:
        numpy.ndarray: The position of the pelvis.

        """
        # Ensure that points are in numpy array
        LASI = np.array(LASI)
        RASI = np.array(RASI)

        # Calculate the position of the pelvis as the midpoint between the LASI and RASI markers
        pelvis_position = (LASI + RASI) / 2
        return pelvis_position

    def get_pelvis_transformation(self, pelvis_position, LASI, RASI, LPSI, RPSI):
        """
        Calculates the transformation matrix for the pelvis based on the given marker positions.

        Parameters:
        LASI (numpy.ndarray): Position of the left anterior superior iliac spine marker.
        RASI (numpy.ndarray): Position of the right anterior superior iliac spine marker.
        LPSI (numpy.ndarray): Position of the left posterior superior iliac spine marker.
        RPSI (numpy.ndarray): Position of the right posterior superior iliac spine marker.

        Returns:
        numpy.ndarray: Transformation matrix for the pelvis.

        """
        #ensure that points are in numpy array
        LASI = np.array(LASI)
        RASI = np.array(RASI)
        LPSI = np.array(LPSI)
        RPSI = np.array(RPSI)

        #The dominant axis, taken as the Y axis, is the direction from the right asis marker to the left asis marker    ###Y
        pelvis_direction = LASI - RASI
        pelvis_direction = pelvis_direction / np.linalg.norm(pelvis_direction)

        # The secondary direction is taken as the direction from the sacrum marker to the right asis marker
        if not np.all(LPSI == 0) and not np.all(RPSI == 0):        
            sacral = (LPSI + RPSI) / 2
            pelvis_right_vector = RASI - sacral
        elif not np.all(LPSI == 0):
            pelvis_right_vector = RASI - LPSI
        elif not np.all(RPSI == 0):
            pelvis_right_vector = RASI - RPSI
        else:
            sacral = (LPSI + RPSI) / 2
            pelvis_right_vector = RASI - sacral
        pelvis_right_vector = pelvis_right_vector / np.linalg.norm(pelvis_right_vector)

        #The Z direction is generally upwards, perpendicular to this plane
        pelvis_up_vector = np.cross(pelvis_right_vector, pelvis_direction)
        pelvis_up_vector = pelvis_up_vector / np.linalg.norm(pelvis_up_vector)

        # Complete the orthonormal basis
        pelvis_right_vector = np.cross(pelvis_direction, pelvis_up_vector)
        pelvis_right_vector = pelvis_right_vector / np.linalg.norm(pelvis_right_vector)

        # Create the transformation
        pelvis_transformation = np.array([pelvis_right_vector, pelvis_direction, pelvis_up_vector]).T

        #Add position giving transformation matrix
        pelvis_transformation = np.hstack([pelvis_transformation, pelvis_position.reshape(3,1)])
        pelvis_transformation = np.vstack([pelvis_transformation, [0, 0, 0, 1]])

        return pelvis_transformation

    def get_hip_joint_center(self, LASI, RASI, LPSI, RPSI, LegLengthL, LegLengthR, markerRadius):
        """
        Calculates the coordinates of the hip joint center based on the given markers and parameters.

        Parameters:
        LASI (list): The coordinates of the left anterior superior iliac spine marker.
        RASI (list): The coordinates of the right anterior superior iliac spine marker.
        LPSI (list): The coordinates of the left posterior superior iliac spine marker.
        RPSI (list): The coordinates of the right posterior superior iliac spine marker.
        LegLengthL (float): The length of the left leg.
        LegLengthR (float): The length of the right leg.
        markerRadius (float): The radius of the marker.

        Returns:
        tuple: A tuple containing the coordinates of the left hip joint center and the right hip joint center.

        """
        #ensure that points are in numpy array
        LASI = np.array(LASI)
        RASI = np.array(RASI)
        LPSI = np.array(LPSI)
        RPSI = np.array(RPSI)

        #check if markers are present
        if np.all(LASI == 0) or np.all(RASI == 0):
            return np.array([[0,0,0]]), np.array([[0,0,0]])
        

        AsisTrocDistL = .1288 * LegLengthL - 48.56
        AsisTrocDistR = .1288 * LegLengthR - 48.56
        MeanLegLength = (LegLengthL + LegLengthR) / 2

        interAsisDistance = calc.calculate_distance(LASI, RASI)
        C = MeanLegLength*.115 - 15.3

        theta = .5
        beta = .314

        #Calculate Left Side 
        if not np.all(LPSI == 0):
            X = C*np.cos(theta)*np.sin(beta) - (AsisTrocDistL + markerRadius) * np.cos(beta)
            Y = -(C*np.sin(theta) - interAsisDistance/2)
            Z = -C*np.cos(theta)*np.cos(beta) - (AsisTrocDistL + markerRadius) * np.sin(beta)
            hip_joint_centerL = np.array([[X, Y, Z]])
        else:
            hip_joint_centerL = np.array([[0,0,0]])

        #Calculate Right Side
        if not np.all(RPSI == 0):
            X = C*np.cos(theta)*np.sin(beta) - (AsisTrocDistR + markerRadius) * np.cos(beta)
            Y = (C*np.sin(theta) - interAsisDistance/2)
            Z = -C*np.cos(theta)*np.cos(beta) - (AsisTrocDistR + markerRadius) * np.sin(beta)
            hip_joint_centerR = np.array([[X, Y, Z]])
        else:
            hip_joint_centerR = np.array([[0,0,0]])

        
        return hip_joint_centerL, hip_joint_centerR

    def get_knee_joint_center(self, LHJC, LTHI, LKNE, RHJC, RTHI, RKNE, LKneeWidth, RKneeWidth):
        """
        Calculates the coordinates of the knee joint center based on the given markers and parameters.
        """
        #ensure that points are in numpy array
        LHJC = np.array(LHJC)
        LTHI = np.array(LTHI)
        LKNE = np.array(LKNE)
        RHJC = np.array(RHJC)
        RTHI = np.array(RTHI)
        RKNE = np.array(RKNE)

        #Firt compute the left side of the knee joint center
        left_plane_origin, left_plane_normal = calc.define_plane(LTHI, LKNE, LHJC)

        #compute left knee joint center
        r = LKneeWidth / 2
        d_vec = LKNE - LHJC
        D = np.linalg.norm(d_vec)
        e = d_vec / D  # unit vector from LHJC toward LKNE

        # In-plane direction perpendicular to e
        perp = np.cross(left_plane_normal, e)
        perp = perp / np.linalg.norm(perp)

        # Components of LKJC relative to LKNE
        t = -(r ** 2) / D                    # along e (toward LHJC)
        s = r * np.sqrt(D ** 2 - r ** 2) / D # perpendicular to e (medial offset)
        left_knee_joint_center = LKNE + t * e + s * perp

        #compute right knee joint center
        right_plane_origin, right_plane_normal = calc.define_plane(RTHI, RKNE, RHJC)

        r = RKneeWidth / 2
        d_vec = RKNE - RHJC
        D = np.linalg.norm(d_vec)
        e = d_vec / D  # unit vector from RHJC toward RKNE

        perp = np.cross(right_plane_normal, e)
        perp = perp / np.linalg.norm(perp)
        t = -(r ** 2) / D                    # along e (toward RHJC)
        s = r * np.sqrt(D ** 2 - r ** 2) / D # perpendicular to e (medial offset)
        right_knee_joint_center = RKNE + t * e + s * perp

        return left_knee_joint_center, right_knee_joint_center, left_plane_normal, right_plane_normal

    def get_ankle_joint_center(self, LKJC, LTIB, LANK, RKJC, RTIB, RANK, LAnkleWidth, RAnkleWidth):
        """
        Calculates the coordinates of the ankle joint center using the chord function.
        """
        LKJC = np.array(LKJC)
        LTIB = np.array(LTIB)
        LANK = np.array(LANK)
        RKJC = np.array(RKJC)
        RTIB = np.array(RTIB)
        RANK = np.array(RANK)

        # --- Left ankle ---
        left_plane_origin, left_plane_normal = calc.define_plane(LTIB, LANK, LKJC)

        r = LAnkleWidth / 2
        d_vec = LANK - LKJC
        D = np.linalg.norm(d_vec)
        e = d_vec / D

        perp = np.cross(left_plane_normal, e)
        perp = perp / np.linalg.norm(perp)

        t = -(r ** 2) / D
        s = r * np.sqrt(D ** 2 - r ** 2) / D
        left_ankle_joint_center = LANK + t * e + s * perp

        # --- Right ankle ---
        right_plane_origin, right_plane_normal = calc.define_plane(RTIB, RANK, RKJC)

        r = RAnkleWidth / 2
        d_vec = RANK - RKJC
        D = np.linalg.norm(d_vec)
        e = d_vec / D

        perp = np.cross(right_plane_normal, e)
        perp = perp / np.linalg.norm(perp)

        t = -(r ** 2) / D
        s = r * np.sqrt(D ** 2 - r ** 2) / D
        right_ankle_joint_center = RANK + t * e + s * perp

        return left_ankle_joint_center, right_ankle_joint_center, left_plane_normal, right_plane_normal


    def globalToPelvisFrame(self, pelvis_transformation, point):
        """
        Transforms a point from the global coordinate frame to the pelvis coordinate frame.

        Args:
            pelvis_transformation (numpy.ndarray): The transformation matrix representing the pelvis frame.
            point (numpy.ndarray): The point to be transformed.

        Returns:
            numpy.ndarray: The transformed point in the pelvis coordinate frame.
        """
        # Ensure that points are in numpy array
        point = np.array(point)

        # Default transformation matrix is pelvis to global, inverse it to get global to pelvis
        pelvis_transformation = np.linalg.inv(pelvis_transformation)

        point = np.reshape(point, (3, 1)).T
        # Apply the pelvis transformation to the point
        point = calc.transform_using_transformation_matrix(pelvis_transformation, point)[0]

        return point


    def pelvisToGlobalFrame(self, pelvis_transformation, point):
        """
        Transforms a point from the pelvis coordinate frame to the global coordinate frame.
        Args:
            pelvis_transformation (numpy.ndarray): The transformation matrix representing the pelvis frame.
            point (numpy.ndarray): The point to be transformed.

        Returns:
            numpy.ndarray: The transformed point in the global coordinate frame.
        """
        # Ensure that points are in numpy array
        point = np.array(point)

        point = np.reshape(point, (3, 1)).T
        # Apply the pelvis transformation to the point
        point = calc.transform_using_transformation_matrix(pelvis_transformation, point)[0]

        return point
        

