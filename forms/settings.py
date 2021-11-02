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
from PySide2.QtCore import QTemporaryDir
from PySide2.QtGui import QDesktopServices


class Form(QDialog):
    def __init__(self, parent=None, corpus=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/settings.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.Corpus = corpus
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.loadjava.clicked.connect(self.loadjava)
        self.w.loadtint.clicked.connect(self.loadtint)
        self.w.loadrscript.clicked.connect(self.loadrscript)
        self.w.loadTempDir.clicked.connect(self.loadTempDir)
        self.w.loadudpipe.clicked.connect(self.loadudpipe)
        self.w.loadudpipemodels.clicked.connect(self.loadudpipemodels)
        self.w.removeudpipemodels.clicked.connect(self.delselected)
        self.w.downloadudpipemodels.clicked.connect(self.downloadUD)
        self.w.clearsessions.clicked.connect(self.clearsessions)
        self.w.resetport.clicked.connect(self.resetport)
        self.w.resetaddress.clicked.connect(self.resetaddress)
        self.w.resettwitter.clicked.connect(self.resettwitter)
        self.w.resetfacebook.clicked.connect(self.resetfacebook)
        self.w.configfile.setText(self.Corpus.mycfgfile)
        self.w.disableProgress.stateChanged.connect(self.showprogress)
        self.setWindowTitle("Impostazioni di Bran")
        self.accepted = False
        self.langLegenda = {"afr": "Afrikaans" , "grc": "AncientGreek" , "ara": "Arabic" , "hye": "Armenian" , "eus": "Basque" , "bel": "Belarusian" , "bul": "Bulgarian" , "cat": "Catalan" , "zho": "Chinese" , "chu": "ChurchSlavic" , "cop": "Coptic" , "hrv": "Croatian" , "ces": "Czech" , "dan": "Danish" , "nld": "Dutch" , "eng": "English" , "est": "Estonian" , "fin": "Finnish" , "fra": "French" , "glg": "Galician" , "wof": "GambianWolof" , "deu": "German" , "got": "Gothic" , "heb": "Hebrew" , "hin": "Hindi" , "hun": "Hungarian" , "ind": "Indonesian" , "gle": "Irish" , "ita": "Italian" , "jpn": "Japanese" , "kaz": "Kazakh" , "kor": "Korean" , "lat": "Latin" , "lav": "Latvian" , "lzh": "LiteraryChinese" , "lit": "Lithuanian" , "mlt": "Maltese" , "mar": "Marathi" , "ell": "Modern Greek" , "sme": "Northern Sami" , "nob": "NorwegianBokmål" , "nno": "Norwegian Nynorsk" , "fro": "OldFrench" , "orv": "OldRussian" , "fas": "Persian" , "pol": "Polish" , "por": "Portuguese" , "ron": "Romanian" , "rus": "Russian" , "san": "Sanskrit" , "gla": "ScottishGaelic" , "srp": "Serbian" , "slk": "Slovak" , "slv": "Slovenian" , "spa": "Spanish" , "swe": "Swedish" , "tam": "Tamil" , "tel": "Telugu" , "tur": "Turkish" , "uig": "Uighur" , "ukr": "Ukrainian" , "urd": "Urdu" , "vie": "Vietnamese" , "wol": "Wolof" }
        self.loadsettings()

    def loadsettings(self):
        try:
            self.w.java.setText(self.Corpus.mycfg["javapath"])
            if self.Corpus.mycfg["javapath"] == "":
                0/0
        except:
            self.Corpus.mycfg["javapath"] = ""
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
            print("Error reading Bran config")
        try:
            self.w.tintlib.setText(self.Corpus.mycfg["tintpath"])
            if self.Corpus.mycfg["tintpath"] == "":
                0/0
        except:
            print("Error reading Bran config")
            self.Corpus.mycfg["tintpath"] = ""
            if platform.system() == "Windows":
                self.w.tintlib.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"\\tint\\lib")
            else:
                self.w.tintlib.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"/tint/lib")
        try:
            self.w.tempDir.setText(self.Corpus.mycfg["tempDir"])
            if self.Corpus.mycfg["tempDir"] == "":
                0/0
        except:
            print("Error reading Bran config")
            self.Corpus.mycfg["tempDir"] = ""
            if platform.system() == "Windows":
                tdir = QTemporaryDir()
                foldername = tdir.path().replace("-","_")
                self.w.tempDir.setText(os.path.abspath(os.path.dirname(foldername)))
            else:
                self.w.tempDir.setText("/tmp/")
        try:
            self.w.udpipe.setText(self.Corpus.mycfg["udpipe"])
            if self.Corpus.mycfg["udpipe"] == "":
                0/0
        except:
            self.Corpus.mycfg["udpipe"] = ""
            print("Error reading Bran config")
            if platform.system() == "Windows":
                self.w.udpipe.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"\\udpipe\\bin-win64\\udpipe.exe")
            else:
                if platform.architecture()[0] == '32bit':
                    self.w.udpipe.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"/udpipe/bin-linux32/udpipe")
                else:
                    self.w.udpipe.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"/udpipe/bin-linux64/udpipe")
        try:
            print("mycfg")
            print(self.Corpus.mycfg)
            udmodelsDict = self.Corpus.mycfg["udpipemodels"] #json.loads(self.Corpus.mycfg["udpipemodels"])
            print(udmodelsDict)
            self.setUDmodels(udmodelsDict)
            #self.w.udpipemodels.setText(self.Corpus.mycfg["udpipemodels"])
            if self.Corpus.mycfg["udpipemodels"] == "":
                0/0
        except:
            self.Corpus.mycfg["udpipemodels"] = ""
            print("Error reading Bran config")
            if platform.system() == "Windows":
                udmodels = { "it-IT" : os.path.abspath(os.path.dirname(sys.argv[0]))+"\\udpipe\\modelli\\italian-isdt-ud-2.4-190531.udpipe" }
                #self.w.udpipemodels.setText(json.dumps(udmodels))
                self.setUDmodels(udmodels)
            else:
                udmodels = { "it-IT" : os.path.abspath(os.path.dirname(sys.argv[0]))+"/udpipe/modelli/italian-isdt-ud-2.4-190531.udpipe" }
                #self.w.udpipemodels.setText(json.dumps(udmodels))
                self.setUDmodels(udmodels)
        try:
            self.w.disableProgress.setChecked(self.Corpus.mycfg["disableProgress"])
        except:
            self.Corpus.mycfg["disableProgress"] = False
            print("Error reading Bran config")
            if platform.system() == "Windows":
                self.Corpus.mycfg["disableProgress"] = True
                self.w.disableProgress.setChecked(True)
        try:
            self.w.rscript.setText(self.Corpus.mycfg["rscript"])
            if self.Corpus.mycfg["rscript"] == "":
                0/0
        except:
            self.Corpus.mycfg["rscript"] = ""
            print("Error reading Bran config")
            if platform.system() == "Windows":
                rdir = "C:/Program Files/R/"
                try:
                    rfiles = os.listdir(rdir)
                except:
                    rfiles = []
                rs = ""
                for fil in rfiles:
                    if "R-" in fil:
                        rs = fil
                if rs == "":
                    self.w.rscript.setText("C:\\Program Files\\R\\Rscript.exe")
                else:
                    self.w.rscript.setText(rdir+rs+"/bin/Rscript.exe")
            else:
                self.w.rscript.setText("/usr/bin/Rscript")
        try:
            self.w.address.setText(self.Corpus.mycfg["tintaddr"])
            print(self.Corpus.mycfg["tintaddr"])
            if self.Corpus.mycfg["tintaddr"] == "":
                0/0
        except:
            self.Corpus.mycfg["tintaddr"] = ""
            print("Error reading Bran config")
            self.w.address.setText("localhost") #http://localhost:8012/tint
        try:
            self.w.port.setText(self.Corpus.mycfg["tintport"])
            print(self.Corpus.mycfg["tintport"])
            if self.Corpus.mycfg["tintport"] == "":
                0/0
        except:
            self.Corpus.mycfg["tintport"] = ""
            print("Error reading Bran config")
            self.w.port.setText("8012")
        try:
            self.w.sessions.setText(json.dumps(self.Corpus.mycfg["sessions"]))
            if self.Corpus.mycfg["sessions"] == "":
                0/0
        except:
            self.Corpus.mycfg["sessions"] = []
            print("Error reading Bran config")
            self.w.sessions.setText("[]")
        try:
            self.w.facebook.setText(json.dumps(self.Corpus.mycfg["facebook"]))
            if self.Corpus.mycfg["facebook"] == "":
                0/0
        except:
            self.Corpus.mycfg["facebook"] = []
            print("Error reading Bran config")
            self.w.facebook.setText("[]")
        try:
            self.w.twitter.setText(json.dumps(self.Corpus.mycfg["twitter"]))
            if self.Corpus.mycfg["twitter"] == "":
                0/0
        except:
            self.Corpus.mycfg["twitter"] = []
            print("Error reading Bran config")
            self.w.twitter.setText("[]")

    def setUDmodels(self, udmodelsDict):
        self.w.udpipemodelsTable.setRowCount(0)
        for key in udmodelsDict:
            myrow = self.addlinetotable(key, 0)
            self.setcelltotable(udmodelsDict[key], myrow, 1)
        self.Corpus.mycfg["udpipemodels"] = udmodelsDict

    def addlinetotable(self, text, column):
        row = self.w.udpipemodelsTable.rowCount()
        self.w.udpipemodelsTable.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.udpipemodelsTable.setItem(row, column, titem)
        self.w.udpipemodelsTable.setCurrentCell(row, column)
        return row

    def setcelltotable(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.udpipemodelsTable.setItem(row, column, titem)

    def udmodelsTable2Dict(self):
        temp = {}
        for row in range(self.w.udpipemodelsTable.rowCount()):
            try:
                key = self.w.udpipemodelsTable.item(row,0).text()
            except:
                continue
            try:
                value = self.w.udpipemodelsTable.item(row,1).text()
            except:
                continue
            temp[key] = value
        #temp = json.loads(self.w.udpipemodels.text())
        return temp

    def delselected(self):
        toselect = []
        for i in range(len(self.w.udpipemodelsTable.selectedItems())):
            row = self.w.udpipemodelsTable.selectedItems()[i].row()
            toselect.append(row)
        totallines = len(toselect)
        for row in range(len(toselect),0,-1):
            self.w.udpipemodelsTable.removeRow(toselect[row-1])

    def downloadUD(self):
        udurl="https://lindat.mff.cuni.cz/repository/xmlui/handle/11234/1-3131"
        QDesktopServices.openUrl(udurl)

    def isaccepted(self):
        self.accepted = True
        temp = self.udmodelsTable2Dict()
        self.Corpus.mycfg["udpipemodels"] = temp
        self.accept()

    def isrejected(self):
        self.reject()

    def loadjava(self):
        QMessageBox.information(self, "Hai già Java?", "Se non hai Java puoi scaricarlo da qui per Windows: <a href=\"https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz\">https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz</a>. Devi solo estrarre il file con 7Zip, non servono privilegi di amministrazione. Poi, indica la posizione del file java.exe (di solito nella cartella bin).")
        filter = ""
        if platform.system() == "Windows":
            filter = "Java (*.exe)"
        fileName = QFileDialog.getOpenFileName(self, "Trova Java", ".", filter)[0]
        if fileName != "":
            self.w.java.setText(fileName)

    def loadtint(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella di Tint")
        if fileName != "":
            self.w.tintlib.setText(fileName)


    def loadTempDir(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella dei file temporanei")
        if fileName != "":
            self.w.tempDir.setText(fileName)

    def loadrscript(self):
        QMessageBox.information(self, "Hai già RScript?", "Se non hai Rscript puoi scaricarlo da qui per Windows: <a href=\"https://cran.r-project.org/bin/windows/base/\">https://cran.r-project.org/bin/windows/base/</a>. Scarica il file di setup e installalo. Poi, indica la posizione del file RScript.exe (di solito nella cartella bin). Dovranno essere installati anche i pacchetti ggplot2 e gridSVG. Puoi farlo automaticamente eseguendo lo script creato da Bran come amministratore, oppure manualmente con il gestore pacchetti di R.")
        filter = ""
        if platform.system() == "Windows":
            filter = "RScript (*.exe)"
        fileName = QFileDialog.getOpenFileName(self, "Trova RScript", ".", filter)[0]
        if fileName != "":
            self.w.rscript.setText(fileName)

    def loadudpipe(self):
        filter = ""
        if platform.system() == "Windows":
            filter = "UDpipe (*.exe)"
        fileName = QFileDialog.getOpenFileName(self, "Trova UDpipe", ".", filter)[0]
        if fileName != "":
            self.w.udpipe.setText(fileName)

    def loadudpipemodels(self):
        #Got standard code from https://iso639-3.sil.org/code_tables/639/data
        thisname = []
        #thisname.append("it-IT")
        #thisname.append("en-US")
        for key in self.langLegenda:
            thisname.append(key)
        lang = QInputDialog.getItem(self.w, "Scegli la lingua", "Per quale lingua (ISO639-3) stai scegliendo il modello di UDpipe?",thisname,current=0,editable=False)[0]
        filter = ""
        if platform.system() == "Windows":
            filter = "UDpipe Models (*.udpipe)"
        fileName = QFileDialog.getOpenFileName(self, "Trova modelli UDpipe", ".", filter)[0]
        if fileName != "":
            temp = self.udmodelsTable2Dict() #json.loads(self.w.udpipemodels.text())
            temp[lang] = fileName
            #self.w.udpipemodels.setText(json.dumps(temp))
            self.setUDmodels(temp)

    def clearsessions(self):
        self.w.sessions.setText("[]")

    def resettwitter(self):
        self.w.twitter.setText("[]")

    def resetfacebook(self):
        self.w.facebook.setText("[]")

    def resetport(self):
        self.w.port.setText("8012")

    def resetaddress(self):
        self.w.address.setText("localhost")

    def showprogress(self, state):
        self.Corpus.mycfg["disableProgress"] = self.w.disableProgress.isChecked()
