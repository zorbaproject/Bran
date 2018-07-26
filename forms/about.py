#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile

import re
import sys
import os


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        #QMessageBox.warning(self, self.tr("My Application"), self.tr("The document has been modified.\nDo you want to save your changes?"))
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/about.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("A proposito di Bran")
        self.setlabel()
        self.setlogo()

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

    def setlabel(self):
        mytext = "Bran è un programma per la linguistica dei corpora\n\n"
        mytext = mytext + "Bran è stato sviluppato da Floriana Sciumbata(email) e Luca Tringali(TRINGALINVENT@libero.it)\n"
        mytext = mytext + "Se utilizzi Bran per una ricerca accademica, ti chiediamo gentilmente di citarlo così:\n"
        mytext = mytext + "{Bran, Floriana Sciumbata, Università di Udine}\n"
        mytext = mytext + "Bran è basato su Tint, un fork italiano di StanfordCore NLP, e fornisce una interfaccia grafica\n"
        mytext = mytext + "per l'analisi dei corpora. Utilizza anche il vocabolario di base di Tullio De Mauro.\n"
        mytext = mytext + "Il nome \"bran\" in lingua inglese indica la crusca, ed è un riferimento all'Accademia della Crusca."
        self.w.label.setText(mytext)

    def setlogo(self):
        scene = QGraphicsScene()
        scene.addText("Hello, world!")
        self.w.logo.setScene(scene)
