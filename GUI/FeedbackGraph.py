"""
FeedbackGraph Module - Visual Biofeedback Display

This module provides a vertical bar graph widget for real-time biofeedback applications.
The display shows:
    - Total range (gray bar): Full measurement range
    - Target region (colored bar): Desired target zone for the user
    - Current value (red line): Real-time measurement indicator

The visual feedback helps users maintain a measurement (e.g., joint angle, force)
within a target range during exercise or rehabilitation tasks.

Usage Example:
    >>> feedback = FeedbackGraph(maxVal=100, regionMax=50, 
    ...                          currentVal=0, regionMin=-50, minVal=-100)
    >>> feedback.setCurrentValue(25)  # Update displayed value

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

import pyqtgraph as pg
from pyqtgraph import QtCore, QtGui
import numpy as np

# ============================================================================
# FEEDBACK GRAPH CLASS
# ============================================================================

class FeedbackGraph():
    def __init__(self, maxVal = 100, regionMax = 50, currentVal = 0, regionMin = -50, minVal = -100):
        """
        Initialize the feedback graph widget.
        
        Creates a vertical bar display with a total range (gray), target region (colored),
        and current value indicator (red line).
        
        Args:
            maxVal (float): Maximum value of total range
            regionMax (float): Maximum value of target region
            currentVal (float): Initial current value
            regionMin (float): Minimum value of target region
            minVal (float): Minimum value of total range
        """
        self.maxVal = maxVal
        self.regionMax = regionMax
        self.currentVal = currentVal
        self.regionMin = regionMin
        self.minVal = minVal

        # Create the plot widget
        self.plotWidget = pg.PlotWidget()
        self.plotWidget.useOpenGL(True)
        self.plotWidget.hideAxis('bottom')  # Hide X-axis (not used)
        self.plotWidget.hideAxis('left')  # Hide Y-axis (not used)

        # Set the display range
        self.plotWidget.setXRange(-3, 3)
        self.plotWidget.setYRange(self.minVal, self.maxVal)

        # Create the total range bar (gray background)
        self.bar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.minVal, 
                                   height=[self.maxVal - self.minVal], brush='grey')
        self.plotWidget.addItem(self.bar)

        # Create the target region bar (colored foreground)
        self.regionBar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.regionMin, 
                                        height=[self.regionMax - self.regionMin], brush='g')
        self.plotWidget.addItem(self.regionBar)

        # Create the current value indicator (red horizontal line)
        self.horizontalLine = pg.InfiniteLine(span=(0.25, .75))
        self.horizontalLine.setAngle(0)
        self.horizontalLine.setPos(0)
        pen = pg.mkPen('r', width=5)
        self.horizontalLine.setPen(pen)
        self.horizontalLine.setZValue(10)  # Draw on top
        self.plotWidget.addItem(self.horizontalLine)


        #turn off interactive mode
        self.plotWidget.setInteractive(False)

    def setTotalRange(self, minVal, maxVal):
        """
        Update the total range (gray bar) of the feedback display.
        
        Args:
            minVal (float): New minimum value
            maxVal (float): New maximum value
        """
        self.minVal = minVal
        self.maxVal = maxVal
        

        if self.minVal > self.regionMin:
            newRegionMin = self.minVal
            self.setRegionRange(newRegionMin, self.regionMax)
        if self.maxVal < self.regionMax:
            newRegionMax = self.maxVal
            self.setRegionRange(self.regionMin, newRegionMax)

        

        # Recreate the total range bar with new dimensions
        self.plotWidget.removeItem(self.bar)
        self.bar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.minVal, 
                                   height=[self.maxVal - self.minVal], brush='grey')



        self.plotWidget.addItem(self.bar)
        #rescale the plot so that the total range is visible
        self.plotWidget.setYRange(self.minVal, self.maxVal)
        self.plotWidget.update()

    def setRegionRange(self, regionMin, regionMax):
        """
        Update the target region (colored bar) of the feedback display.
        
        Args:
            regionMin (float): New minimum of target region
            regionMax (float): New maximum of target region
        """
        self.regionMin = regionMin
        self.regionMax = regionMax
        
        # Recreate the target region bar with new dimensions
        self.plotWidget.removeItem(self.regionBar)
        self.regionBar = pg.BarGraphItem(x0=-1, x1 = 1,y0 = self.regionMin, 
                                        height=[self.regionMax - self.regionMin], brush='g')
        
        self.plotWidget.addItem(self.regionBar)
        self.plotWidget.update()

    def setCurrentValue(self, currentVal):
        """
        Update the current value indicator (red line) position.
        
        Args:
            currentVal (float): New current value to display
        """
        self.currentVal = currentVal
        self.horizontalLine.setPos(self.currentVal) 
        self.plotWidget.update()

    def toggleVisible(self, visible):
        """
        Toggle the visibility of the feedback graph.
        
        Args:
            visible (bool): New visibility state
        """
        self.plotWidget.setVisible(visible)
        self.plotWidget.update()




