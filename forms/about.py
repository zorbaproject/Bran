#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt

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
        mytext = "<html>Bran è un programma per la linguistica dei corpora<br><br>"
        mytext = mytext + "Bran è stato sviluppato da Floriana Sciumbata(email) e Luca Tringali(TRINGALINVENT@libero.it)<br>"
        mytext = mytext + "Se utilizzi Bran per una pubblicazione accademica, ti chiediamo gentilmente di citarlo così:<br>"
        mytext = mytext + "<pre>{Bran, Floriana Sciumbata, Università di Trieste}</pre>"
        mytext = mytext + "<pre>{Italy goes to Stanford: a collection of CoreNLP modules for Italian},\n {{Palmero Aprosio}, A. and {Moretti}, G.,\n Fondazione Bruno Kessler Trento}</pre><br>"
        mytext = mytext + "Bran è basato su Tint, un fork italiano di StanfordCore NLP, e fornisce una interfaccia grafica<br>"
        mytext = mytext + "per l'analisi dei corpora. Utilizza anche il vocabolario di base di Tullio De Mauro.<br>"
        mytext = mytext + "Il nome \"bran\" in lingua inglese indica la crusca, ed è un riferimento all'Accademia della Crusca.<br><br>"
        mytext = mytext + "Bran è rilasciato come software libero con licenza GNU GPL, sei libero di modificarlo come preferisci.<br>"
        mytext = mytext + "Se vuoi collaborare allo sviluppo di Bran, controlla il repository GitHub <br><a href=\"https://github.com/zorbaproject/VdB-Hacking\">https://github.com/zorbaproject/VdB-Hacking</a></html>"
        self.w.label.setText(mytext)
        self.w.label.setTextInteractionFlags(Qt.TextSelectableByMouse)

    def setlogo(self):
        scene = QGraphicsScene()
        image = QPixmap(os.path.abspath(os.path.dirname(sys.argv[0]))+"/bran-logo.png").scaledToHeight(128)
        scene.addPixmap(image)
        self.w.logo.setScene(scene)
        self.w.logo.setFixedSize(image.width()+10, image.height()+10)
        #self.w.logo.fitInView(0, 0, image.width(), image.height(), Qt.KeepAspectRatio)
