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
        self.w.addI.clicked.connect(self.addI)
        self.w.remI.clicked.connect(self.remI)
        self.w.addF.clicked.connect(self.addF)
        self.w.remF.clicked.connect(self.remF)
        self.setWindowTitle("Scegli come cercare le ripetizioni")
        self.w.remspaces.setChecked(False)
        self.w.ignorecase.setChecked(True)
        self.allPos = []
        self.loadvuote()

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

    def addI(self):
        words = QInputDialog.getText(self.w, "Scegli la codifica", "Scrivi le parole che vuoi aggiungere separate da spazi:")
        wordsL = words[0].split(" ")
        for myword in wordsL:
            self.w.vuoteI.addItem(myword)

    def addF(self):
        words = QInputDialog.getText(self.w, "Scegli la codifica", "Scrivi le parole che vuoi aggiungere separate da spazi:")
        wordsL = words[0].split(" ")
        for myword in wordsL:
            self.w.vuoteF.addItem(myword)

    def remI(self):
        for i in self.w.vuoteI.selectedItems():
            self.w.vuoteI.takeItem(self.w.vuoteI.row(i))

    def remF(self):
        for i in self.w.vuoteF.selectedItems():
            self.w.vuoteF.takeItem(self.w.vuoteF.row(i))

    def loadallpos(self, legenda):
        for item in legenda:
            self.allPos.append(legenda[item][0])

    def loadipos(self, history):
        for olddir in history:
            self.w.ignorapos.addItem(olddir)

    def loadvuote(self):
        vuoteifile = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/VuoteI.txt"
        vuoteffile = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/VuoteF.txt"
        if os.path.isfile(vuoteifile):
            vuotei = [line.rstrip('\n') for line in open(vuoteifile, encoding='utf-8')]
            for vuota in vuotei:
                self.w.vuoteI.addItem(vuota)
        if os.path.isfile(vuoteffile):
            vuotef = [line.rstrip('\n') for line in open(vuoteffile, encoding='utf-8')]
            for vuota in vuotef:
                self.w.vuoteF.addItem(vuota)
