from PySide6.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QTreeWidget, QHeaderView, QTableWidgetItem, QWidget
from GUI.FeedbackWindow_ui import Ui_Form
from GUI.FeedbackGraph import FeedbackGraph
import sys

import pyqtgraph as pg
import numpy as np

import time

if __name__ == "__main__":
    app = QApplication(sys.argv)

    SideWindow = QWidget()
    ui = Ui_Form()
    ui.setupUi(SideWindow)

    feedbackGraph = FeedbackGraph()
    ui.panFeedbackPlot.addWidget(feedbackGraph.plotWidget)

    SideWindow.show()

    c = 0
    while True:
        app.processEvents()
        c+=.01
        a = 40
        feedbackGraph.setCurrentValue(np.sin(c)*a)

        time.sleep(1/60)

    sys.exit(app.exec_())

    