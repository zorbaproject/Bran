#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem

import re
import sys
import os


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/ripetizioni.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        #self.w.cancelrecenti.clicked.connect(self.clearh)
        self.w.rejected.connect(self.isrejected)
        #self.w.selectapri.clicked.connect(self.selectapri)
        #self.w.selectcrea.clicked.connect(self.selectcrea)
        self.setWindowTitle("Scegli come cercare le ripetizioni")
        #self.filesessione = ""
        self.w.remspaces.setChecked(False)
        self.w.ignorecase.setChecked(True)

    def isaccepted(self):
        self.accept()

    def isrejected(self):
        self.reject()

    def clearh(self):
        for i in range(self.w.recenti.count()):
            item = self.w.recenti.item(i)
            self.w.recenti.setItemSelected(item, False)

    def selectapri(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella in cui si trova la tua sessione di lavoro")
        if not fileName == "":
            if os.path.isdir(fileName):
                self.w.aprisessione.setText(fileName)

    def loadipos(self, history):
        for olddir in history:
            self.w.ignorapos.addItem(olddir)
