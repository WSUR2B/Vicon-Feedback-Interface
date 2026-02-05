"""
Forceplate Module - Force Plate Data Representation

This module defines the Forceplate class for accessing force plate data
from the Vicon system.

A Forceplate provides:
    - Force vectors (3D ground reaction forces)
    - Moment vectors (3D moments about force plate origin)
    - Center of Pressure (CoP) coordinates
    - Analog channel data

Note: This module is currently not fully integrated with the main application
but provides the foundation for future force plate support.

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# FORCEPLATE CLASS
# ============================================================================

class Forceplate:
    """
    Represents a force plate device in the Vicon system.
    
    Attributes:
        id (int): Force plate identifier
        forceVectorData (list): Force vector in plate coordinates
        momentVectorData (list): Moment vector in plate coordinates
        copData (list): Center of pressure in plate coordinates
        globalForceVectorData (list): Force vector in global coordinates
        globalMomentVectorData (list): Moment vector in global coordinates
        globalCopData (list): Center of pressure in global coordinates
        analogData (list): Raw analog channel voltages
    """
    
    def __init__(self, id):
        """
        Initialize a force plate object.
        
        Args:
            id (int): Force plate identifier
        """
        self.id = id

        # Plate coordinate system data
        self.forceVectorData = []
        self.momentVectorData = []
        self.copData = []
        
        # Global coordinate system data
        self.globalForceVectorData = []
        self.globalMomentVectorData = []
        self.globalCopData = []

        # Raw analog data
        self.analogData = []

    def update(self, client):
        """
        Update force plate data for the current frame.
        
        Args:
            client: Vicon DataStream client object
        """
        
        self.forceVectorData = []
        self.momentVectorData = []
        self.copData = []
        self.globalForceVectorData = []
        self.globalMomentVectorData = []
        self.globalCopData = []

        self.analogData = []
 


        self.forceVectorData = client.GetForceVector( self.id )
        self.momentVectorData = client.GetMomentVector( self.id )
        self.copData = client.GetCentreOfPressure( self.id )
        self.globalForceVectorData = client.GetGlobalForceVector( self.id )
        self.globalMomentVectorData = client.GetGlobalMomentVector( self.id )
        self.globalCopData = client.GetGlobalCentreOfPressure( self.id )

        try:
            self.analogData = client.GetAnalogChannelVoltage( self.id )
        except:
            pass