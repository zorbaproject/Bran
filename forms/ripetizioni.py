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
        self.w.rejected.connect(self.isrejected)
        self.w.aggiungi.clicked.connect(self.selectaggiungi)
        self.w.rimuovi.clicked.connect(self.rimuovi)
        self.setWindowTitle("Scegli come cercare le ripetizioni")
        self.w.remspaces.setChecked(False)
        self.w.ignorecase.setChecked(True)
        self.allPos = []

    def isaccepted(self):
        self.accept()

    def isrejected(self):
        self.reject()

    def rimuovi(self):
        for i in self.w.ignorapos.selectedItems():
            self.w.ignorapos.takeItem(self.w.ignorapos.row(i))

    def selectaggiungi(self):
        mypos = QInputDialog.getItem(self, "Scegli la categoria", "Scegli la categoria PoS da aggiungere alla lista di PoS da ignorare",self.allPos,current=0,editable=False)
        self.w.ignorapos.addItem(mypos[0])

    def loadallpos(self, legenda):
        for item in legenda:
            self.allPos.append(legenda[item][0])

    def loadipos(self, history):
        for olddir in history:
            self.w.ignorapos.addItem(olddir)
