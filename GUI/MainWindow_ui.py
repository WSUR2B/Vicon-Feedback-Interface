# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.6.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QGridLayout, QHBoxLayout, QHeaderView,
    QLabel, QLayout, QLineEdit, QMainWindow,
    QMenuBar, QPlainTextEdit, QPushButton, QSizePolicy,
    QSlider, QSpacerItem, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QToolButton, QTreeWidget,
    QTreeWidgetItem, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1173, 680)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout_4 = QGridLayout(self.centralwidget)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout_5 = QVBoxLayout()
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.plainTextEdit = QPlainTextEdit(self.centralwidget)
        self.plainTextEdit.setObjectName(u"plainTextEdit")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plainTextEdit.sizePolicy().hasHeightForWidth())
        self.plainTextEdit.setSizePolicy(sizePolicy)
        self.plainTextEdit.setReadOnly(True)

        self.verticalLayout_5.addWidget(self.plainTextEdit)

        self.frame_2 = QFrame(self.centralwidget)
        self.frame_2.setObjectName(u"frame_2")
        sizePolicy1 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Maximum)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.frame_2.sizePolicy().hasHeightForWidth())
        self.frame_2.setSizePolicy(sizePolicy1)
        self.frame_2.setFrameShape(QFrame.StyledPanel)
        self.frame_2.setFrameShadow(QFrame.Raised)
        self.gridLayout_5 = QGridLayout(self.frame_2)
        self.gridLayout_5.setSpacing(0)
        self.gridLayout_5.setObjectName(u"gridLayout_5")
        self.gridLayout_5.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_20 = QHBoxLayout()
        self.horizontalLayout_20.setObjectName(u"horizontalLayout_20")
        self.horizontalLayout_19 = QHBoxLayout()
        self.horizontalLayout_19.setObjectName(u"horizontalLayout_19")
        self.label_5 = QLabel(self.frame_2)
        self.label_5.setObjectName(u"label_5")
        sizePolicy2 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.label_5.sizePolicy().hasHeightForWidth())
        self.label_5.setSizePolicy(sizePolicy2)

        self.horizontalLayout_19.addWidget(self.label_5)

        self.lblAngleFilterIndec = QLabel(self.frame_2)
        self.lblAngleFilterIndec.setObjectName(u"lblAngleFilterIndec")
        sizePolicy3 = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        sizePolicy3.setHorizontalStretch(0)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.lblAngleFilterIndec.sizePolicy().hasHeightForWidth())
        self.lblAngleFilterIndec.setSizePolicy(sizePolicy3)
        font = QFont()
        font.setPointSize(8)
        self.lblAngleFilterIndec.setFont(font)

        self.horizontalLayout_19.addWidget(self.lblAngleFilterIndec)


        self.horizontalLayout_20.addLayout(self.horizontalLayout_19)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_20.addItem(self.horizontalSpacer_2)

        self.btnTest = QPushButton(self.frame_2)
        self.btnTest.setObjectName(u"btnTest")

        self.horizontalLayout_20.addWidget(self.btnTest)

        self.label_23 = QLabel(self.frame_2)
        self.label_23.setObjectName(u"label_23")
        self.label_23.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_20.addWidget(self.label_23)

        self.lblViconFPS = QLabel(self.frame_2)
        self.lblViconFPS.setObjectName(u"lblViconFPS")
        self.lblViconFPS.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout_20.addWidget(self.lblViconFPS)

        self.label_22 = QLabel(self.frame_2)
        self.label_22.setObjectName(u"label_22")
        self.label_22.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_20.addWidget(self.label_22)

        self.lblFPS = QLabel(self.frame_2)
        self.lblFPS.setObjectName(u"lblFPS")
        self.lblFPS.setLayoutDirection(Qt.LeftToRight)
        self.lblFPS.setAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignVCenter)

        self.horizontalLayout_20.addWidget(self.lblFPS)


        self.gridLayout_5.addLayout(self.horizontalLayout_20, 0, 0, 1, 1)


        self.verticalLayout_5.addWidget(self.frame_2)


        self.gridLayout.addLayout(self.verticalLayout_5, 2, 0, 1, 3)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setSizeConstraint(QLayout.SetMinimumSize)

        self.gridLayout.addLayout(self.horizontalLayout, 0, 1, 1, 1)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setFrameShape(QFrame.StyledPanel)
        self.frame.setFrameShadow(QFrame.Raised)
        self.gridLayout_2 = QGridLayout(self.frame)
        self.gridLayout_2.setSpacing(0)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.tabWidget = QTabWidget(self.frame)
        self.tabWidget.setObjectName(u"tabWidget")
        sizePolicy.setHeightForWidth(self.tabWidget.sizePolicy().hasHeightForWidth())
        self.tabWidget.setSizePolicy(sizePolicy)
        self.tab_2 = QWidget()
        self.tab_2.setObjectName(u"tab_2")
        sizePolicy.setHeightForWidth(self.tab_2.sizePolicy().hasHeightForWidth())
        self.tab_2.setSizePolicy(sizePolicy)
        self.verticalLayout_2 = QVBoxLayout(self.tab_2)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.deviceTree = QTreeWidget(self.tab_2)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"1");
        self.deviceTree.setHeaderItem(__qtreewidgetitem)
        self.deviceTree.setObjectName(u"deviceTree")
        self.deviceTree.setExpandsOnDoubleClick(False)

        self.verticalLayout_2.addWidget(self.deviceTree)

        self.tabWidget.addTab(self.tab_2, "")
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.verticalLayout_7 = QVBoxLayout(self.tab_3)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.angleTree = QTreeWidget(self.tab_3)
        __qtreewidgetitem1 = QTreeWidgetItem()
        __qtreewidgetitem1.setText(0, u"1");
        self.angleTree.setHeaderItem(__qtreewidgetitem1)
        self.angleTree.setObjectName(u"angleTree")
        self.angleTree.setExpandsOnDoubleClick(False)

        self.verticalLayout_7.addWidget(self.angleTree)

        self.btnZerAngles_1 = QPushButton(self.tab_3)
        self.btnZerAngles_1.setObjectName(u"btnZerAngles_1")
        sizePolicy4 = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.btnZerAngles_1.sizePolicy().hasHeightForWidth())
        self.btnZerAngles_1.setSizePolicy(sizePolicy4)

        self.verticalLayout_7.addWidget(self.btnZerAngles_1)

        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.label_24 = QLabel(self.tab_3)
        self.label_24.setObjectName(u"label_24")

        self.horizontalLayout_5.addWidget(self.label_24)

        self.spinLeftLeg = QSpinBox(self.tab_3)
        self.spinLeftLeg.setObjectName(u"spinLeftLeg")
        self.spinLeftLeg.setMinimum(100)
        self.spinLeftLeg.setMaximum(9999)
        self.spinLeftLeg.setValue(800)

        self.horizontalLayout_5.addWidget(self.spinLeftLeg)

        self.label_28 = QLabel(self.tab_3)
        self.label_28.setObjectName(u"label_28")

        self.horizontalLayout_5.addWidget(self.label_28)

        self.spinRightLeg = QSpinBox(self.tab_3)
        self.spinRightLeg.setObjectName(u"spinRightLeg")
        self.spinRightLeg.setMinimum(100)
        self.spinRightLeg.setMaximum(9999)
        self.spinRightLeg.setValue(800)

        self.horizontalLayout_5.addWidget(self.spinRightLeg)

        self.label_27 = QLabel(self.tab_3)
        self.label_27.setObjectName(u"label_27")

        self.horizontalLayout_5.addWidget(self.label_27)

        self.spinMarkerR = QSpinBox(self.tab_3)
        self.spinMarkerR.setObjectName(u"spinMarkerR")
        self.spinMarkerR.setMinimum(1)
        self.spinMarkerR.setValue(5)

        self.horizontalLayout_5.addWidget(self.spinMarkerR)


        self.verticalLayout_8.addLayout(self.horizontalLayout_5)

        self.line = QFrame(self.tab_3)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_8.addWidget(self.line)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.label_9 = QLabel(self.tab_3)
        self.label_9.setObjectName(u"label_9")

        self.horizontalLayout_9.addWidget(self.label_9)

        self.comboFilter = QComboBox(self.tab_3)
        self.comboFilter.setObjectName(u"comboFilter")

        self.horizontalLayout_9.addWidget(self.comboFilter)


        self.verticalLayout_8.addLayout(self.horizontalLayout_9)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.label_10 = QLabel(self.tab_3)
        self.label_10.setObjectName(u"label_10")

        self.horizontalLayout_13.addWidget(self.label_10)

        self.spinSize = QSpinBox(self.tab_3)
        self.spinSize.setObjectName(u"spinSize")
        self.spinSize.setMinimum(1)
        self.spinSize.setMaximum(300)
        self.spinSize.setValue(100)

        self.horizontalLayout_13.addWidget(self.spinSize)

        self.label_13 = QLabel(self.tab_3)
        self.label_13.setObjectName(u"label_13")

        self.horizontalLayout_13.addWidget(self.label_13)

        self.spinSampleRate = QSpinBox(self.tab_3)
        self.spinSampleRate.setObjectName(u"spinSampleRate")
        self.spinSampleRate.setMaximum(9999)
        self.spinSampleRate.setValue(100)

        self.horizontalLayout_13.addWidget(self.spinSampleRate)


        self.verticalLayout_8.addLayout(self.horizontalLayout_13)

        self.horizontalLayout_15 = QHBoxLayout()
        self.horizontalLayout_15.setObjectName(u"horizontalLayout_15")
        self.label_11 = QLabel(self.tab_3)
        self.label_11.setObjectName(u"label_11")

        self.horizontalLayout_15.addWidget(self.label_11)

        self.spinLowcut = QDoubleSpinBox(self.tab_3)
        self.spinLowcut.setObjectName(u"spinLowcut")
        self.spinLowcut.setMaximum(9999.000000000000000)
        self.spinLowcut.setValue(0.010000000000000)

        self.horizontalLayout_15.addWidget(self.spinLowcut)

        self.label_12 = QLabel(self.tab_3)
        self.label_12.setObjectName(u"label_12")

        self.horizontalLayout_15.addWidget(self.label_12)

        self.spinHighcut = QDoubleSpinBox(self.tab_3)
        self.spinHighcut.setObjectName(u"spinHighcut")
        self.spinHighcut.setMaximum(9999.000000000000000)
        self.spinHighcut.setValue(29.000000000000000)

        self.horizontalLayout_15.addWidget(self.spinHighcut)


        self.verticalLayout_8.addLayout(self.horizontalLayout_15)


        self.verticalLayout_7.addLayout(self.verticalLayout_8)

        self.tabWidget.addTab(self.tab_3, "")
        self.tab = QWidget()
        self.tab.setObjectName(u"tab")
        sizePolicy.setHeightForWidth(self.tab.sizePolicy().hasHeightForWidth())
        self.tab.setSizePolicy(sizePolicy)
        self.verticalLayout = QVBoxLayout(self.tab)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout_6 = QVBoxLayout()
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.btnZerAngles = QPushButton(self.tab)
        self.btnZerAngles.setObjectName(u"btnZerAngles")
        sizePolicy4.setHeightForWidth(self.btnZerAngles.sizePolicy().hasHeightForWidth())
        self.btnZerAngles.setSizePolicy(sizePolicy4)

        self.verticalLayout_6.addWidget(self.btnZerAngles)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setSizeConstraint(QLayout.SetMinimumSize)
        self.label = QLabel(self.tab)
        self.label.setObjectName(u"label")
        self.label.setLayoutDirection(Qt.LeftToRight)
        self.label.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_4.addWidget(self.label)

        self.angleComboBox = QComboBox(self.tab)
        self.angleComboBox.setObjectName(u"angleComboBox")

        self.horizontalLayout_4.addWidget(self.angleComboBox)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.checkBoxLeft = QCheckBox(self.tab)
        self.checkBoxLeft.setObjectName(u"checkBoxLeft")
        self.checkBoxLeft.setChecked(True)
        self.checkBoxLeft.setTristate(False)

        self.horizontalLayout_3.addWidget(self.checkBoxLeft)

        self.checkBoxRight = QCheckBox(self.tab)
        self.checkBoxRight.setObjectName(u"checkBoxRight")

        self.horizontalLayout_3.addWidget(self.checkBoxRight)


        self.horizontalLayout_4.addLayout(self.horizontalLayout_3)


        self.verticalLayout_6.addLayout(self.horizontalLayout_4)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setSizeConstraint(QLayout.SetMinimumSize)
        self.label_14 = QLabel(self.tab)
        self.label_14.setObjectName(u"label_14")
        self.label_14.setLayoutDirection(Qt.LeftToRight)
        self.label_14.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_10.addWidget(self.label_14)

        self.angleComboBox_2 = QComboBox(self.tab)
        self.angleComboBox_2.setObjectName(u"angleComboBox_2")

        self.horizontalLayout_10.addWidget(self.angleComboBox_2)

        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.checkBoxLeft_2 = QCheckBox(self.tab)
        self.checkBoxLeft_2.setObjectName(u"checkBoxLeft_2")

        self.horizontalLayout_11.addWidget(self.checkBoxLeft_2)

        self.checkBoxRight_2 = QCheckBox(self.tab)
        self.checkBoxRight_2.setObjectName(u"checkBoxRight_2")
        self.checkBoxRight_2.setChecked(True)

        self.horizontalLayout_11.addWidget(self.checkBoxRight_2)


        self.horizontalLayout_10.addLayout(self.horizontalLayout_11)


        self.verticalLayout_6.addLayout(self.horizontalLayout_10)


        self.verticalLayout.addLayout(self.verticalLayout_6)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.label_7 = QLabel(self.tab)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setLayoutDirection(Qt.LeftToRight)
        self.label_7.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_2.addWidget(self.label_7)

        self.comboBoxDevice = QComboBox(self.tab)
        self.comboBoxDevice.setObjectName(u"comboBoxDevice")

        self.horizontalLayout_2.addWidget(self.comboBoxDevice)

        self.comboBoxChannel = QComboBox(self.tab)
        self.comboBoxChannel.setObjectName(u"comboBoxChannel")

        self.horizontalLayout_2.addWidget(self.comboBoxChannel)

        self.comboBoxComponent = QComboBox(self.tab)
        self.comboBoxComponent.setObjectName(u"comboBoxComponent")

        self.horizontalLayout_2.addWidget(self.comboBoxComponent)

        self.btnAddRemoveDeviceFromStream = QPushButton(self.tab)
        self.btnAddRemoveDeviceFromStream.setObjectName(u"btnAddRemoveDeviceFromStream")

        self.horizontalLayout_2.addWidget(self.btnAddRemoveDeviceFromStream)


        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout.addItem(self.verticalSpacer)

        self.tabWidget.addTab(self.tab, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.verticalLayout_4 = QVBoxLayout(self.tab_4)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.label_15 = QLabel(self.tab_4)
        self.label_15.setObjectName(u"label_15")

        self.horizontalLayout_12.addWidget(self.label_15)

        self.txtFilename = QLineEdit(self.tab_4)
        self.txtFilename.setObjectName(u"txtFilename")

        self.horizontalLayout_12.addWidget(self.txtFilename)

        self.label_16 = QLabel(self.tab_4)
        self.label_16.setObjectName(u"label_16")

        self.horizontalLayout_12.addWidget(self.label_16)

        self.spinSavingIndex = QSpinBox(self.tab_4)
        self.spinSavingIndex.setObjectName(u"spinSavingIndex")
        self.spinSavingIndex.setValue(0)

        self.horizontalLayout_12.addWidget(self.spinSavingIndex)

        self.checkSavingAutoIndex = QCheckBox(self.tab_4)
        self.checkSavingAutoIndex.setObjectName(u"checkSavingAutoIndex")

        self.horizontalLayout_12.addWidget(self.checkSavingAutoIndex)


        self.verticalLayout_4.addLayout(self.horizontalLayout_12)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.label_8 = QLabel(self.tab_4)
        self.label_8.setObjectName(u"label_8")

        self.horizontalLayout_8.addWidget(self.label_8)

        self.txtSavePath = QLineEdit(self.tab_4)
        self.txtSavePath.setObjectName(u"txtSavePath")

        self.horizontalLayout_8.addWidget(self.txtSavePath)

        self.btnSetPath = QToolButton(self.tab_4)
        self.btnSetPath.setObjectName(u"btnSetPath")

        self.horizontalLayout_8.addWidget(self.btnSetPath)


        self.verticalLayout_4.addLayout(self.horizontalLayout_8)

        self.label_19 = QLabel(self.tab_4)
        self.label_19.setObjectName(u"label_19")
        self.label_19.setAlignment(Qt.AlignCenter)

        self.verticalLayout_4.addWidget(self.label_19)

        self.tableExport = QTableWidget(self.tab_4)
        self.tableExport.setObjectName(u"tableExport")

        self.verticalLayout_4.addWidget(self.tableExport)

        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.checkSaveAllDeviceData = QCheckBox(self.tab_4)
        self.checkSaveAllDeviceData.setObjectName(u"checkSaveAllDeviceData")

        self.horizontalLayout_7.addWidget(self.checkSaveAllDeviceData)


        self.verticalLayout_4.addLayout(self.horizontalLayout_7)

        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_4.addItem(self.verticalSpacer_3)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.horizontalLayout_14 = QHBoxLayout()
        self.horizontalLayout_14.setObjectName(u"horizontalLayout_14")
        self.label_2 = QLabel(self.tab_4)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setAlignment(Qt.AlignRight|Qt.AlignTrailing|Qt.AlignVCenter)

        self.horizontalLayout_14.addWidget(self.label_2)

        self.spinInterval = QSpinBox(self.tab_4)
        self.spinInterval.setObjectName(u"spinInterval")

        self.horizontalLayout_14.addWidget(self.spinInterval)

        self.btnRecordDuration = QPushButton(self.tab_4)
        self.btnRecordDuration.setObjectName(u"btnRecordDuration")

        self.horizontalLayout_14.addWidget(self.btnRecordDuration)


        self.verticalLayout_9.addLayout(self.horizontalLayout_14)

        self.btnRecordStopSaveToCSV = QPushButton(self.tab_4)
        self.btnRecordStopSaveToCSV.setObjectName(u"btnRecordStopSaveToCSV")

        self.verticalLayout_9.addWidget(self.btnRecordStopSaveToCSV)

        self.btnSaveWindowToCSV = QPushButton(self.tab_4)
        self.btnSaveWindowToCSV.setObjectName(u"btnSaveWindowToCSV")

        self.verticalLayout_9.addWidget(self.btnSaveWindowToCSV)


        self.verticalLayout_4.addLayout(self.verticalLayout_9)

        self.tabWidget.addTab(self.tab_4, "")
        self.tab_5 = QWidget()
        self.tab_5.setObjectName(u"tab_5")
        self.verticalLayout_3 = QVBoxLayout(self.tab_5)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.horizontalLayout_16 = QHBoxLayout()
        self.horizontalLayout_16.setObjectName(u"horizontalLayout_16")
        self.label_3 = QLabel(self.tab_5)
        self.label_3.setObjectName(u"label_3")

        self.horizontalLayout_16.addWidget(self.label_3)

        self.txtTargetMachineIP = QLineEdit(self.tab_5)
        self.txtTargetMachineIP.setObjectName(u"txtTargetMachineIP")

        self.horizontalLayout_16.addWidget(self.txtTargetMachineIP)

        self.label_4 = QLabel(self.tab_5)
        self.label_4.setObjectName(u"label_4")

        self.horizontalLayout_16.addWidget(self.label_4)

        self.txtStreamPort = QLineEdit(self.tab_5)
        self.txtStreamPort.setObjectName(u"txtStreamPort")
        sizePolicy5 = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.txtStreamPort.sizePolicy().hasHeightForWidth())
        self.txtStreamPort.setSizePolicy(sizePolicy5)

        self.horizontalLayout_16.addWidget(self.txtStreamPort)


        self.verticalLayout_3.addLayout(self.horizontalLayout_16)

        self.horizontalLayout_17 = QHBoxLayout()
        self.horizontalLayout_17.setObjectName(u"horizontalLayout_17")
        self.label_20 = QLabel(self.tab_5)
        self.label_20.setObjectName(u"label_20")

        self.horizontalLayout_17.addWidget(self.label_20)

        self.spinPacketSize = QSpinBox(self.tab_5)
        self.spinPacketSize.setObjectName(u"spinPacketSize")
        self.spinPacketSize.setMinimum(10)
        self.spinPacketSize.setValue(50)

        self.horizontalLayout_17.addWidget(self.spinPacketSize)

        self.label_21 = QLabel(self.tab_5)
        self.label_21.setObjectName(u"label_21")

        self.horizontalLayout_17.addWidget(self.label_21)

        self.spinValueSize = QSpinBox(self.tab_5)
        self.spinValueSize.setObjectName(u"spinValueSize")
        self.spinValueSize.setMinimum(10)

        self.horizontalLayout_17.addWidget(self.spinValueSize)


        self.verticalLayout_3.addLayout(self.horizontalLayout_17)

        self.label_17 = QLabel(self.tab_5)
        self.label_17.setObjectName(u"label_17")
        self.label_17.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_17)

        self.tableStream = QTableWidget(self.tab_5)
        self.tableStream.setObjectName(u"tableStream")

        self.verticalLayout_3.addWidget(self.tableStream)

        self.label_18 = QLabel(self.tab_5)
        self.label_18.setObjectName(u"label_18")
        self.label_18.setAlignment(Qt.AlignCenter)

        self.verticalLayout_3.addWidget(self.label_18)

        self.plainTextOrderOfPackets = QPlainTextEdit(self.tab_5)
        self.plainTextOrderOfPackets.setObjectName(u"plainTextOrderOfPackets")
        font1 = QFont()
        font1.setFamilies([u"Courier New"])
        self.plainTextOrderOfPackets.setFont(font1)

        self.verticalLayout_3.addWidget(self.plainTextOrderOfPackets)

        self.verticalSpacer_4 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_3.addItem(self.verticalSpacer_4)

        self.btnStartEndStream = QPushButton(self.tab_5)
        self.btnStartEndStream.setObjectName(u"btnStartEndStream")

        self.verticalLayout_3.addWidget(self.btnStartEndStream)

        self.tabWidget.addTab(self.tab_5, "")

        self.gridLayout_2.addWidget(self.tabWidget, 1, 0, 2, 2)


        self.gridLayout.addWidget(self.frame, 0, 3, 3, 1)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_6.addItem(self.horizontalSpacer)

        self.label_6 = QLabel(self.centralwidget)
        self.label_6.setObjectName(u"label_6")
        sizePolicy2.setHeightForWidth(self.label_6.sizePolicy().hasHeightForWidth())
        self.label_6.setSizePolicy(sizePolicy2)

        self.horizontalLayout_6.addWidget(self.label_6)

        self.spinNFrames = QSpinBox(self.centralwidget)
        self.spinNFrames.setObjectName(u"spinNFrames")
        sizePolicy6 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.spinNFrames.sizePolicy().hasHeightForWidth())
        self.spinNFrames.setSizePolicy(sizePolicy6)
        self.spinNFrames.setMinimum(1)
        self.spinNFrames.setMaximum(10000)
        self.spinNFrames.setSingleStep(100)
        self.spinNFrames.setValue(1000)

        self.horizontalLayout_6.addWidget(self.spinNFrames)


        self.gridLayout.addLayout(self.horizontalLayout_6, 1, 1, 1, 1)

        self.gridLayout_3 = QGridLayout()
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.spinYmin = QDoubleSpinBox(self.centralwidget)
        self.spinYmin.setObjectName(u"spinYmin")
        sizePolicy7 = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy7.setHorizontalStretch(0)
        sizePolicy7.setVerticalStretch(0)
        sizePolicy7.setHeightForWidth(self.spinYmin.sizePolicy().hasHeightForWidth())
        self.spinYmin.setSizePolicy(sizePolicy7)
        self.spinYmin.setDecimals(5)
        self.spinYmin.setMinimum(-99999.000000000000000)
        self.spinYmin.setMaximum(99999.000000000000000)
        self.spinYmin.setSingleStep(100.000000000000000)
        self.spinYmin.setValue(-1000.000000000000000)

        self.gridLayout_3.addWidget(self.spinYmin, 2, 0, 1, 2)

        self.sliderYrange2 = QSlider(self.centralwidget)
        self.sliderYrange2.setObjectName(u"sliderYrange2")
        sizePolicy8 = QSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Minimum)
        sizePolicy8.setHorizontalStretch(0)
        sizePolicy8.setVerticalStretch(0)
        sizePolicy8.setHeightForWidth(self.sliderYrange2.sizePolicy().hasHeightForWidth())
        self.sliderYrange2.setSizePolicy(sizePolicy8)
        self.sliderYrange2.setMaximum(10000)
        self.sliderYrange2.setOrientation(Qt.Vertical)

        self.gridLayout_3.addWidget(self.sliderYrange2, 1, 1, 1, 1)

        self.sliderYrange1 = QSlider(self.centralwidget)
        self.sliderYrange1.setObjectName(u"sliderYrange1")
        sizePolicy8.setHeightForWidth(self.sliderYrange1.sizePolicy().hasHeightForWidth())
        self.sliderYrange1.setSizePolicy(sizePolicy8)
        self.sliderYrange1.setMaximum(10000)
        self.sliderYrange1.setSingleStep(0)
        self.sliderYrange1.setValue(10000)
        self.sliderYrange1.setOrientation(Qt.Vertical)
        self.sliderYrange1.setTickPosition(QSlider.NoTicks)

        self.gridLayout_3.addWidget(self.sliderYrange1, 1, 0, 1, 1)

        self.spinYmax = QDoubleSpinBox(self.centralwidget)
        self.spinYmax.setObjectName(u"spinYmax")
        sizePolicy7.setHeightForWidth(self.spinYmax.sizePolicy().hasHeightForWidth())
        self.spinYmax.setSizePolicy(sizePolicy7)
        self.spinYmax.setFrame(True)
        self.spinYmax.setAccelerated(False)
        self.spinYmax.setDecimals(5)
        self.spinYmax.setMinimum(-99999.000000000000000)
        self.spinYmax.setMaximum(99999.000000000000000)
        self.spinYmax.setSingleStep(100.000000000000000)
        self.spinYmax.setValue(1000.000000000000000)

        self.gridLayout_3.addWidget(self.spinYmax, 0, 0, 1, 2)


        self.gridLayout.addLayout(self.gridLayout_3, 0, 0, 2, 1)


        self.gridLayout_4.addLayout(self.gridLayout, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1173, 22))
        MainWindow.setMenuBar(self.menubar)

        self.retranslateUi(MainWindow)

        self.tabWidget.setCurrentIndex(1)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.plainTextEdit.setPlainText(QCoreApplication.translate("MainWindow", u"Hello Data Outputas", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Angle Filter: ", None))
        self.lblAngleFilterIndec.setText(QCoreApplication.translate("MainWindow", u"none", None))
        self.btnTest.setText(QCoreApplication.translate("MainWindow", u"test", None))
        self.label_23.setText(QCoreApplication.translate("MainWindow", u"Vicon Processing ", None))
        self.lblViconFPS.setText(QCoreApplication.translate("MainWindow", u"lblFPS", None))
        self.label_22.setText(QCoreApplication.translate("MainWindow", u"  Main ", None))
        self.lblFPS.setText(QCoreApplication.translate("MainWindow", u"lblFPS", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), QCoreApplication.translate("MainWindow", u"Device Selection", None))
        self.btnZerAngles_1.setText(QCoreApplication.translate("MainWindow", u"Zero Angles", None))
        self.label_24.setText(QCoreApplication.translate("MainWindow", u"Left Leg (mm):", None))
        self.label_28.setText(QCoreApplication.translate("MainWindow", u"Right Leg (mm):", None))
        self.label_27.setText(QCoreApplication.translate("MainWindow", u"Marker R (mm):", None))
        self.label_9.setText(QCoreApplication.translate("MainWindow", u"Angle Filter: ", None))
        self.label_10.setText(QCoreApplication.translate("MainWindow", u"Size:", None))
        self.label_13.setText(QCoreApplication.translate("MainWindow", u"Sample Rate:", None))
        self.label_11.setText(QCoreApplication.translate("MainWindow", u"Lowcut:", None))
        self.label_12.setText(QCoreApplication.translate("MainWindow", u"Highcut: ", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Angle Selection", None))
        self.btnZerAngles.setText(QCoreApplication.translate("MainWindow", u"Zero Angles", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Angle 1:", None))
        self.checkBoxLeft.setText(QCoreApplication.translate("MainWindow", u"Left", None))
        self.checkBoxRight.setText(QCoreApplication.translate("MainWindow", u"Right", None))
        self.label_14.setText(QCoreApplication.translate("MainWindow", u"Angle 2:", None))
        self.checkBoxLeft_2.setText(QCoreApplication.translate("MainWindow", u"Left", None))
        self.checkBoxRight_2.setText(QCoreApplication.translate("MainWindow", u"Right", None))
        self.label_7.setText(QCoreApplication.translate("MainWindow", u"Plot Device Data", None))
        self.btnAddRemoveDeviceFromStream.setText(QCoreApplication.translate("MainWindow", u"Set", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), QCoreApplication.translate("MainWindow", u"Plotting", None))
        self.label_15.setText(QCoreApplication.translate("MainWindow", u"Filename", None))
        self.txtFilename.setText(QCoreApplication.translate("MainWindow", u"Recording", None))
        self.label_16.setText(QCoreApplication.translate("MainWindow", u"Index:", None))
        self.checkSavingAutoIndex.setText(QCoreApplication.translate("MainWindow", u"Auto Index", None))
        self.label_8.setText(QCoreApplication.translate("MainWindow", u"Save Path:", None))
        self.btnSetPath.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.label_19.setText(QCoreApplication.translate("MainWindow", u"Data To Export", None))
        self.checkSaveAllDeviceData.setText(QCoreApplication.translate("MainWindow", u"Save All Device Data", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Duration(s):", None))
        self.btnRecordDuration.setText(QCoreApplication.translate("MainWindow", u"Record Duration", None))
        self.btnRecordStopSaveToCSV.setText(QCoreApplication.translate("MainWindow", u"Start Recording", None))
        self.btnSaveWindowToCSV.setText(QCoreApplication.translate("MainWindow", u"Record And Save Single Window to CSV", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Exporting", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Client Machine IP", None))
        self.txtTargetMachineIP.setText(QCoreApplication.translate("MainWindow", u"127.0.0.1", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"UDP Port", None))
        self.txtStreamPort.setText(QCoreApplication.translate("MainWindow", u"5005", None))
        self.label_20.setText(QCoreApplication.translate("MainWindow", u"Packet Size", None))
        self.label_21.setText(QCoreApplication.translate("MainWindow", u"Value Size", None))
        self.label_17.setText(QCoreApplication.translate("MainWindow", u"Select Data To Stream", None))
        self.label_18.setText(QCoreApplication.translate("MainWindow", u"Order of Packets", None))
        self.btnStartEndStream.setText(QCoreApplication.translate("MainWindow", u"Start Stream", None))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_5), QCoreApplication.translate("MainWindow", u"Streaming", None))
        self.label_6.setText(QCoreApplication.translate("MainWindow", u"N Frames", None))
        self.spinYmax.setPrefix("")
        self.spinYmax.setSuffix("")
    # retranslateUi

