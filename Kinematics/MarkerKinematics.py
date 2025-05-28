import Kinematics.Calculation as calc
from Filters import MyFilter
import numpy as np


"""
MarkerKinematics contains various classes for performing kinematics calculations with different marker sets and qualities.

"""

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

        #Filters For angles
        self.filters = {}
        for angle in self.anglesZeroDictionary:
            self.filters[angle] = MyFilter(1, 1, 'none')
        
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

    def updateWithSubject(self, markerDictionary):
        """
        Updates the marker dictionary and calculates joint positions and angles based on the provided marker dictionary.

        Args:
            markerDictionary (dict): A dictionary containing marker names as keys and marker positions as values.

        Returns:
            None
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
    





    def get_pelvis_position(self, LASI, RASI):
        """
        Calculates the position of the pelvis as the midpoint between the LASI and RASI markers.

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


        

