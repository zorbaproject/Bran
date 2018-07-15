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
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/sessione.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("Scegli una sessione di lavoro")

    def isaccepted(self):
        self.filesessione = ""
        if self.w.aprisessione.text() != "":
            self.filesessione = self.w.aprisessione.text()
            fileName = "-bran.csv" #nome della cartella
            self.filesessione = self.filesessione + fileName
            if os.path.isfile(self.filesessione):
                self.accept()
            else:
                QMessageBox.errore(self, "Errore", "Questa cartella non contiene un valido file di sessione. Il file deve essere chiamato "+fileName+".")
        if self.w.creafolder.text() != "":
            self.filesessione = self.w.aprisessione.text()
            self.accept()

    def isrejected(self):
        self.filesessione = ""
        QMessageBox.warning(self, "Sicuro sicuro?", "Stai per avviare Bran senza un file per la sessione di lavoro: questo significa che tutte le modifiche resteranno nella RAM. Se usi file di grandi dimensioni, la memoria potrebbe non bastare, e il programma andrebbe in crash. Sei sicuro di voler procedere senza una sessione di lavoro su file?")
        self.reject()

    def selectapri(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella in cui si trova la tua sessione di lavoro")
        if not fileName == "":
            if os.path.isdir(fileName):
                self.w.aprisessione.setText(fileName)

    def selectcrea(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella creare la tua sessione di lavoro")
        if not fileName == "":
            if os.path.isdir(fileName):
                self.w.creafolder.setText(fileName)
