import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui
import numpy as np



class FeedbackGraph():
    def __init__(self, maxVal = 100, regionMax = 50, currentVal = 0, regionMin = -50, minVal = -100):
        self.maxVal = maxVal
        self.regionMax = regionMax
        self.currentVal = currentVal
        self.regionMin = regionMin
        self.minVal = minVal

        self.plotWidget = pg.PlotWidget()
        #hide the axis
        self.plotWidget.hideAxis('bottom')
        # self.plotWidget.hideAxis('left')

        #set the range of the plot
        self.plotWidget.setXRange(-2, 2)
        self.plotWidget.setYRange(self.minVal, self.maxVal)

        #create graphics objects
        self.bar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.minVal, height=[self.maxVal - self.minVal], brush='gray', )
        self.plotWidget.addItem(self.bar)

        self.regionBar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.regionMin, height=[self.regionMax - self.regionMin], brush='y', )
        self.plotWidget.addItem(self.regionBar)

        #create a marker that would show current value 
        self.horizontalLine = pg.InfiniteLine(span=(0.25, .75))
        self.horizontalLine.setAngle(0)
        self.horizontalLine.setPos(0)
        pen = pg.mkPen('r', width=5)
        self.horizontalLine.setPen(pen)
        self.horizontalLine.setZValue(10)
        self.plotWidget.addItem(self.horizontalLine)




        # self.horizontalLine.setMovable(True)


    def setTotalRange(self, minVal, maxVal):
        self.minVal = minVal
        self.maxVal = maxVal
        
        self.plotWidget.removeItem(self.bar)
        self.bar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.minVal, height=[self.maxVal - self.minVal], brush='b', )
        
        self.plotWidget.addItem(self.bar)
        self.plotWidget.repaint()
        self.plotWidget.update()


    def setRegionRange(self, regionMin, regionMax):
        self.regionMin = regionMin
        self.regionMax = regionMax
        
        self.plotWidget.removeItem(self.regionBar)
        self.regionBar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.regionMin, height=[self.regionMax - self.regionMin], brush='g', )
        
        self.plotWidget.addItem(self.regionBar)
        self.plotWidget.repaint()
        self.plotWidget.update()


    def setCurrentValue(self, currentVal):
        self.currentVal = currentVal
        self.horizontalLine.setPos(self.currentVal) 
        self.plotWidget.repaint()
        self.plotWidget.update()





