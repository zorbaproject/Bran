#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import sys
import os
import csv
#import re

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QDialog

class Confronto(QDialog):

    def __init__(self, parent=None):
        super(Confronto, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/confronto.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        #self.w.accepted.connect(self.isaccepted)
        #self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("Confronta dati estratti dai corpora")
        #self.w.replace_in_corpus.clicked.connect(self.replaceCorpus)
        #self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
