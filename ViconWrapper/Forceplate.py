class Forceplate:
    def __init__(self, id):
        self.id = id

        self.forceVectorData = []
        self.momentVectorData = []
        self.copData = []
        self.globalForceVectorData = []
        self.globalMomentVectorData = []
        self.globalCopData = []

        self.analogData = []

    def update(self, client):
        
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