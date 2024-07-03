from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtGui import QKeyEvent, QPainter
from PySide6.QtWidgets import (QApplication, QDial, QFrame, QGraphicsView,
    QGridLayout, QHBoxLayout, QMainWindow, QMenuBar,
    QPlainTextEdit, QSizePolicy, QStatusBar, QVBoxLayout,
    QWidget)

import numpy as np

class MyCharting():
    def __init__(self):
        
        self.customeXYAxis = False

        OPENGL = True
        self.series1 = QLineSeries()
        self.series1.setUseOpenGL(OPENGL)
        self.series1.setName("Line 1")

        self.series2 = QLineSeries()
        self.series2.setUseOpenGL(OPENGL)
        self.series2.setName("Line 2")

        self.series3 = QLineSeries()
        self.series3.setUseOpenGL(OPENGL)
        self.series3.setName("Line 3")



        self.chart = QChart()
        self.chart.addSeries(self.series1)
        self.chart.addSeries(self.series2)
        self.chart.addSeries(self.series3)
        self.chart.legend().setVisible(True)
        # self.chart.setTitle("Simple Line Chart Example")

        self.chart.createDefaultAxes()
        self.chart.setTheme(QChart.ChartTheme.ChartThemeDark)

        self.chartView = QChartView(self.chart)
        self.chartView.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.chartView.setSizePolicy(QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum))



    def addData(self, axis, x, y):
        if axis == 1:
            self.series1.append(x, y)
        elif axis == 2:
            self.series2.append(x, y)
        elif axis == 3:
            self.series3.append(x, y)

        self.updateAxisRange()


    def clearSeries(self, axis):
        if axis == 1:
            self.series1.clear()
        elif axis == 2:
            self.series2.clear()
        elif axis == 3:
            self.series3.clear()
        
        self.updateAxisRange()

    def clearAllSeries(self):
        self.series1.clear()
        self.series2.clear()
        self.series3.clear()
        self.updateAxisRange()

    def removeFirstAndShift(self, axis):

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
        self.customeXYAxis = True
        self.chart.axisX().setRange(xMin, xMax)
        self.chart.axisY().setRange(yMin, yMax)

    def updateAxisRange(self):
        if self.customeXYAxis:
            return
        # Extract all points from the series
        points = [self.series1.at(i) for i in range(self.series1.count())]
        points += [self.series2.at(i) for i in range(self.series2.count())]
        points += [self.series3.at(i) for i in range(self.series3.count())]

        xs = np.array([point.x() for point in points])
        ys = np.array([point.y() for point in points])

        # Update axis range
        if len(xs) > 0 and len(ys) > 0:
            self.chart.axisX().setRange(xs.min(), xs.max())
            self.chart.axisY().setRange(ys.min(), ys.max())


    def finalize(self):
        self.updateAxisRange()
        self.chart.update()

