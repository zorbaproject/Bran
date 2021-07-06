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
import time


class ProgressDialog(QThread):
    #dataReceived = Signal(bool)

    def __init__(self, corpus, rec = "", tl = -1):
        QThread.__init__(self)
        #self.w = widget
        self.Corpus = corpus
        self.Progrdialog = Form()
        self.cancelled = False
        self.recovery = rec
        self.totallines = tl
        print("Looking for recovery in "+self.recovery)
        self.stupidwindows = False
        if platform.system() == "Windows":
            self.stupidwindows = True

    def __del__(self):
        print("Done")

    def run(self):
        self.loadDialog()
        return

    def loadDialog(self):
        if self.recovery != "" and self.totallines > -1:
            self.autoUpdate()
            self.Progrdialog.isaccepted()
        else:
            if self.stupidwindows:
                self.Progrdialog.show()
            else:
                self.Progrdialog.exec()
            self.Progrdialog.isaccepted()

    def autoUpdate(self):
        self.Progrdialog.show()
        i = 0
        oldval = -1
        while self.cancelled == False and self.Corpus.core_killswitch == False:
            try:
                with open(self.recovery, "r", encoding='utf-8') as tempfile:
                    lastEl = list(tempfile)[-1]
                    if "," in lastEl:
                        lastline = int(lastEl.split(",")[0])
                        self.totallines = int(lastEl.split(",")[1])
                    else:
                        lastline = int(lastEl)
            except:
                lastline = 0
            if self.totallines > 0:
                tmpTotallines = self.totallines
            else:
                tmpTotallines = 1
            self.Progrdialog.w.testo.setText("Sto analizzando il paragrafo numero "+str(lastline))
            self.Progrdialog.w.progressBar.setValue(int((lastline/tmpTotallines)*100))
            if i%1==0 and lastline != oldval:
                QApplication.processEvents()
            time.sleep(1)
            oldval = lastline
            i = i +1
            if self.Progrdialog.w.annulla.isChecked():
                self.cancelled = True
                self.Corpus.core_killswitch = True


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
        self.basetext = ""
        self.totallines = 0
        self.currentValue = 0
        self.setWindowTitle("Operazione in corso")
        #https://stackoverflow.com/questions/11754865/how-to-show-an-infinite-floating-progressbar-in-qt-without-knowing-the-percent

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

    def setBasetext(self, basetext):
        self.basetext = basetext

    def setTotal(self, total):
        self.totallines = total

    def setValue(self, value):
        self.w.testo.setText(self.basetext+str(value))
        if self.currentValue != int((value/self.totallines)*100):
            self.currentValue = int((value/self.totallines)*100)
            self.w.progressBar.setValue(self.currentValue)
