"""
MyOpenGLCharting Module - Hardware-Accelerated Real-Time Plotting

This module provides an OpenGL-accelerated line chart for displaying real-time
biomechanical data with minimal performance overhead.

Features:
    - OpenGL rendering for smooth, high-performance visualization
    - Support for up to 3 simultaneous data series
    - Automatic or custom axis scaling
    - Dark theme optimized for visibility
    - Real-time updates without performance degradation

Typical Use:
    - Plotting joint angles over time
    - Displaying device measurements (EMG, force, etc.)
    - Real-time data visualization during motion capture

Author: Daniil Grubich
Institution: Wayne State University - R2B Lab
"""

# ============================================================================
# IMPORTS
# ============================================================================

from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtGui import QKeyEvent, QPainter
from PySide6.QtWidgets import (QApplication, QDial, QFrame, QGraphicsView,
    QGridLayout, QHBoxLayout, QMainWindow, QMenuBar,
    QPlainTextEdit, QSizePolicy, QStatusBar, QVBoxLayout,
    QWidget)

import numpy as np

# ============================================================================
# CHARTING CLASS
# ============================================================================

class MyCharting():
    def __init__(self):
        """
        Initialize the OpenGL-accelerated chart widget.
        
        Creates a chart with three line series, all using OpenGL rendering
        for optimal performance with real-time data.
        """
        self.customeXYAxis = False  # Flag for custom axis range mode

        # Enable OpenGL acceleration for all series
        OPENGL = True
        
        # Create three data series
        self.series1 = QLineSeries()
        self.series1.setUseOpenGL(OPENGL)
        self.series1.setName("Line 1")

        self.series2 = QLineSeries()
        self.series2.setUseOpenGL(OPENGL)
        self.series2.setName("Line 2")

        self.series3 = QLineSeries()
        self.series3.setUseOpenGL(OPENGL)
        self.series3.setName("Line 3")

        # Create and configure the chart
        self.chart = QChart()
        self.chart.addSeries(self.series1)
        self.chart.addSeries(self.series2)
        self.chart.addSeries(self.series3)
        self.chart.legend().setVisible(True)
        self.chart.createDefaultAxes()
        self.chart.setTheme(QChart.ChartTheme.ChartThemeDark)

        # Create the chart view widget
        self.chartView = QChartView(self.chart)
        self.chartView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chartView.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, 
                                                 QSizePolicy.Policy.Minimum))

    def addData(self, axis, x, y):
        """
        Add a data point to a specific series.
        
        Args:
            axis (int): Series number (1, 2, or 3)
            x (float): X-coordinate (typically frame number or time)
            y (float): Y-coordinate (measurement value)
        """
        if axis == 1:
            self.series1.append(x, y)
        elif axis == 2:
            self.series2.append(x, y)
        elif axis == 3:
            self.series3.append(x, y)

        self.updateAxisRange()

    def clearSeries(self, axis):
        """
        Clear all data from a specific series.
        
        Args:
            axis (int): Series number (1, 2, or 3) to clear
        """
        if axis == 1:
            self.series1.clear()
        elif axis == 2:
            self.series2.clear()
        elif axis == 3:
            self.series3.clear()
        
        self.updateAxisRange()

    def clearAllSeries(self):
        """Clear all data from all three series."""
        self.series1.clear()
        self.series2.clear()
        self.series3.clear()
        self.updateAxisRange()

    def removeFirstAndShift(self, axis):
        """
        Remove the first data point from a series (for scrolling window effect).
        
        Args:
            axis (int): Series number (1, 2, or 3) to modify
        """
        if axis == 1:
            if self.series1.count() > 0:
                self.series1.remove(0)
        elif axis == 2:
            if self.series2.count() > 0:
                self.series2.remove(0)
        elif axis == 3:
            if self.series3.count() > 0:
                self.series3.remove(0)

        self.updateAxisRange()

    def setCustomXYAxis(self, xMin, xMax, yMin, yMax):
        """
        Set custom fixed axis ranges (disables auto-scaling).
        
        Args:
            xMin (float): Minimum X-axis value
            xMax (float): Maximum X-axis value
            yMin (float): Minimum Y-axis value
            yMax (float): Maximum Y-axis value
        """
        self.customeXYAxis = True
        self.chart.axisX().setRange(xMin, xMax)
        self.chart.axisY().setRange(yMin, yMax)

    def updateAxisRange(self):
        """
        Update axis ranges to fit all data (auto-scaling mode only).
        
        Automatically calculates and sets axis ranges based on all data
        points in all series. Skipped if custom axis mode is enabled.
        """
        if self.customeXYAxis:
            return
            
        # Extract all points from all series
        points = [self.series1.at(i) for i in range(self.series1.count())]
        points += [self.series2.at(i) for i in range(self.series2.count())]
        points += [self.series3.at(i) for i in range(self.series3.count())]

        # Calculate min/max for both axes
        xs = np.array([point.x() for point in points])
        ys = np.array([point.y() for point in points])

        # Update axis ranges if data exists
        if len(xs) > 0 and len(ys) > 0:
            self.chart.axisX().setRange(xs.min(), xs.max())
            self.chart.axisY().setRange(ys.min(), ys.max())

    def finalize(self):
        """
        Finalize the current frame update.
        
        Called after all data for the current frame has been added.
        Updates axis ranges and refreshes the chart display.
        """
        self.updateAxisRange()
        self.chart.update()

