#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtCore import QThread
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem

import re
import sys
import os
import platform


class ProgressDialog(QThread):
    dataReceived = Signal(bool)

    def __init__(self, widget):
        QThread.__init__(self)
        self.w = widget
        self.Progrdialog = Form()
        self.cancelled = False
        self.stupidwindows = 0
        if platform.system() == "Windows":
            self.stupidwindows = 1

    def __del__(self):
        print("Done")

    def run(self):
        self.loadDialog()
        return

    def loadDialog(self):
        if self.stupidwindows == 1:
            self.Progrdialog.show()
        else:
            self.Progrdialog.exec()
        #self.Progrdialog.isaccepted()




class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/progress.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.annulla.clicked.connect(self.isrejected)
        self.setWindowTitle("Operazione in corso")

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()
