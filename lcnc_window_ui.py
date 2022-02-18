# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'lcnc_window.ui'
#
# Created by: PyQt5 UI code generator 5.14.1
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_lcnc_test_window(object):
    def setupUi(self, lcnc_test_window):
        lcnc_test_window.setObjectName("lcnc_test_window")
        lcnc_test_window.resize(150, 650)
        self.centralwidget = QtWidgets.QWidget(lcnc_test_window)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.examplelayout = QtWidgets.QHBoxLayout()
        self.examplelayout.setObjectName("examplelayout")
        self.HeaderStatus = QtWidgets.QLabel(self.centralwidget)
        self.HeaderStatus.setObjectName("HeaderStatus")
        self.examplelayout.addWidget(self.HeaderStatus)
        self.HeadeHumanReadable = QtWidgets.QLabel(self.centralwidget)
        self.HeadeHumanReadable.setObjectName("HeadeHumanReadable")
        self.examplelayout.addWidget(self.HeadeHumanReadable)
        self.verticalLayout.addLayout(self.examplelayout)
        lcnc_test_window.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(lcnc_test_window)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 150, 26))
        self.menubar.setObjectName("menubar")
        lcnc_test_window.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(lcnc_test_window)
        self.statusbar.setObjectName("statusbar")
        lcnc_test_window.setStatusBar(self.statusbar)

        self.retranslateUi(lcnc_test_window)
        QtCore.QMetaObject.connectSlotsByName(lcnc_test_window)

    def retranslateUi(self, lcnc_test_window):
        _translate = QtCore.QCoreApplication.translate
        lcnc_test_window.setWindowTitle(_translate("lcnc_test_window", "Linuxcnc Test Window"))
        self.HeaderStatus.setText(_translate("lcnc_test_window", "Status"))
        self.HeadeHumanReadable.setText(_translate("lcnc_test_window", "Translation"))
