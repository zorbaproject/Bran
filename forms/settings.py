#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
from os import listdir
from os.path import isfile, join
import urllib.request
import urllib.parse
import html
import datetime
import json
import subprocess
from socket import timeout
import platform
import time

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtCore import QThread
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?



class Form(QDialog):
    def __init__(self, parent=None, mycfg=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/settings.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        if mycfg == None or mycfg["tintaddr"] == "":
            self.loadsettings()
        else:
            self.w.java.setText(mycfg["javapath"])
            self.w.tintlib.setText(mycfg["tintpath"])
            #self.w.address.setText(mycfg["tintaddr"])
            #self.w.port.setText(mycfg["tintport"])
        #self.w.quit.clicked.connect(self.quitme)
        self.w.loadjava.clicked.connect(self.loadjava)
        self.w.loadtint.clicked.connect(self.loadtint)
        self.setWindowTitle("Impostazioni di Bran")

    def quitme(self):
        self.notint = True
        self.accept()

    def loadsettings(self):
        if platform.system() == "Windows":
            jdir = "C:/Program Files/Java/"
            try:
                jfiles = os.listdir(jdir)
            except:
                jfiles = []
            jre = ""
            for fil in jfiles:
                if "jre" in fil:
                    jre = fil
            if jre == "":
                self.w.java.setText("")
            else:
                self.w.java.setText(jdir+jre+"/bin/java.exe")
        else:
            self.w.java.setText("/usr/bin/java")
        if platform.system() == "Windows":
            self.w.tintlib.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"\\tint\\lib")
        else:
            self.w.tintlib.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"/tint/lib")
        self.w.port.setText("8012")
        self.w.address.setText("localhost") #http://localhost:8012/tint

    def loadjava(self):
        QMessageBox.information(self, "Hai già Java?", "Se non hai Java puoi scaricarlo da qui per Windows: <a href=\"https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz\">https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz</a>. Devi solo estrarre il file con 7Zip, non servono privilegi di amministrazione. Poi, indica la posizione del file java.exe (di solito nella cartella bin).")
        fileName = QFileDialog.getOpenFileName(self, "Trova Java", ".", "Java (*.exe)")[0]
        if fileName != "":
            self.w.java.setText(fileName)

    def loadtint(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella di Tint")
        if fileName != "":
            self.w.tintlib.setText(fileName)
