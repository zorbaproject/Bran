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

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?
from PySide2.QtCore import QThread


class TintRunner(QThread):
    dataReceived = Signal(bool)

    def __init__(self, widget,addr = ""):
        QThread.__init__(self)
        self.w = widget
        self.setTerminationEnabled(True)

    def loadvariables(self, javavar, tintdirvar, tintportvar):
        self.Java = javavar
        self.TintDir = tintdirvar
        self.TintPort = tintportvar

    def __del__(self):
        print("Shutting down thread")

    def run(self):
        self.runServer()
        return

    def runServer(self):
        print("Eseguo il server Tint")
        readystring = "TintServer - Pipeline loaded"  #"[HttpServer] Started"
        CLASSPATH = self.TintDir+"/*"
        args = [self.Java,"-classpath", CLASSPATH, "eu.fbk.dh.tint.runner.TintServer", "-p ",self.TintPort]
        print(self.Java)
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                lineb = p.stdout.readline()
                line = str(lineb)
                #print("++"+line+"++")
                self.w.loglist.addItem(line)
                self.w.loglist.setCurrentRow(self.w.loglist.count()-1)
                QApplication.processEvents()
                if readystring in line:
                    break
            self.dataReceived.emit(True)
            self.w.quit.clicked.emit()
        except:
            self.dataReceived.emit(False)



class TintCorpus(QThread):
    dataReceived = Signal(bool)

    def __init__(self, widget, fnames, corpcol, myTintAddr):
        QThread.__init__(self)
        self.w = widget
        self.fileNames = fnames
        self.corpuscols = corpcol
        self.Tintaddr = myTintAddr
        self.loadvariables()
        self.setTerminationEnabled(True)

    def loadvariables(self):
        #http://localhost:8012/tint?text=Barack%20Obama%20era%20il%20presidente%20degli%20Stati%20Uniti%20d%27America.
        self.TintTimeout = 300
        self.useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

    def __del__(self):
        print("Shutting down thread")

    def run(self):
        self.loadtxt()
        return

    def loadtxt(self):
        fileID = 0
        for fileName in self.fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    if self.w.corpus.rowCount() >0:
                        fileID = int(self.w.corpus.item(self.w.corpus.rowCount()-1,0).text().split("_")[0])
                    #QApplication.processEvents()
                    fileID = fileID+1
                    text_file = open(fileName, "r")
                    lines = text_file.read()
                    text_file.close()
                    #self.w.statusbar.showMessage("ATTENDI: sto lavorando su "+fileName)
                    self.text2corpusTINT(lines, str(fileID)+"_"+os.path.basename(fileName))
        #self.w.statusbar.clearMessage()
        if self.fileNames == []:
            testline = "Il gatto è sopra al tetto."
            myres = self.getJson(testline)
            try:
                myarray = json.loads(myres)
                self.dataReceived.emit(True)
            except:
                self.dataReceived.emit(False)


    def addlinetocorpus(self, text, column):
        row = self.w.corpus.rowCount()
        self.w.corpus.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.corpus.setItem(row, column, titem)
        self.w.corpus.setCurrentCell(row, column)
        return row

    def setcelltocorpus(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.corpus.setItem(row, column, titem)
        #self.w.corpus.setCurrentCell(row, column)

    def text2corpusTINT(self, text, IDcorpus):
        #process
        itext = text.split('\n')
        for line in itext:
            myres = ""
            if line != "":
                myres = self.getJson(line)
            try:
                myarray = json.loads(myres)
            except:
                myarray = {'sentences': []}
            for sentence in myarray["sentences"]:
                for token in sentence["tokens"]:
                    rowN = self.addlinetocorpus(IDcorpus, self.corpuscols["IDcorpus"])
                    self.setcelltocorpus(str(token["index"]), rowN, self.corpuscols["IDword"])
                    self.setcelltocorpus(str(token["originalText"]), rowN, self.corpuscols["Orig"])
                    self.setcelltocorpus(str(token["lemma"]), rowN, self.corpuscols["Lemma"])
                    self.setcelltocorpus(str(token["pos"]), rowN, self.corpuscols["pos"])
                    self.setcelltocorpus(str(token["ner"]), rowN, self.corpuscols["ner"])
                    self.setcelltocorpus(str(token["full_morpho"]), rowN, self.corpuscols["feat"])

    #def runServer(self):
    #    self.TThread = TintRunner(self.w, "")
    #    #self.TThread.finished.connect(self.threadstopped)
    #    self.TThread.start()

    def getJson(self, text):
        #http://localhost:8012/tint?text=Barack%20Obama%20era%20il%20presidente%20degli%20Stati%20Uniti%20d%27America.
        urltext = urllib.parse.quote(text)
        thisurl = self.Tintaddr+"?text=" + urltext
        if thisurl == '':
            return ''
        req = urllib.request.Request(
            thisurl,
            data=None,
            headers={
                'User-Agent': self.useragent
            }
        )

        thishtml = ""
        try:
            f = urllib.request.urlopen(req,timeout=self.TintTimeout)
            ft = f.read() #we should stop if this is taking too long
        except:
            ft = ""
        try:
            thishtml = ft.decode('utf-8', 'backslashreplace')
        except:
            thishtml = str(ft)
        return thishtml


    def text2corpusUDPIPE(self, text, IDcorpus):
        self.istdmodel = os.path.abspath(os.path.dirname(sys.argv[0]))+"/udpipe/UD_Italian-ISDT/nob.udpipe"
        self.model = Model.load(self.istdmodel)
        if not self.model:
            QMessageBox.warning(self, "Errore", "Non ho trovato il modello italiano in "+self.istdmodel)
        self.pipeline = Pipeline(self.model, "tokenize", Pipeline.DEFAULT, Pipeline.DEFAULT, "conllu")
        #sys.stderr.write('Usage: %s input_format(tokenize|conllu|horizontal|vertical) output_format(conllu) model_file\n' % sys.argv[0])
        self.UDerror = ProcessingError()
        self.IDcorpuscol = 0
        self.origcorpuscol = 1
        self.lemmcorpuscol = 2
        self.uposcorpuscol = 3
        self.xposcorpuscol = 4
        self.featcorpuscol = 5
        self.headcorpuscol = 6
        self.deprelcorpuscol = 7
        self.depscorpuscol = 8
        self.misccorpuscol = 9
        self.idwordcorpuscol = 10
        itext = ''.join(text)
        processed = self.pipeline.process(itext, self.UDerror)
        if self.UDerror.occurred():
            print(self.UDerror.message)
        #print(processed)
        processed = processed.split('\n')
        oldorig = ""
        origempty = 0
        for rowtext in processed:
            if len(rowtext)>0 and rowtext[0]!="#" and rowtext[0]!="_":
                QApplication.processEvents()
                rowN = -1
                rowlst = rowtext.split("\t")
                if len(rowlst)>0:
                    wID = rowlst[0]
                    if "-" in wID:
                        if len(rowlst)>1:
                            oldorig = rowlst[1]
                        rowlst = ""
                        origempty = int(wID.split("-")[1]) - int(wID.split("-")[0])
                    else:
                        rowN = self.addlinetocorpus(IDcorpus, self.IDcorpuscol)
                if len(rowlst)>0:
                    idwordcorpus = rowlst[0]
                    self.setcelltocorpus(idwordcorpus, rowN, self.idwordcorpuscol)
                if len(rowlst)>1:
                    origcorpus = rowlst[1]
                    if oldorig != "":
                        origcorpus = oldorig
                        oldorig = ""
                    elif origempty > 0:
                        origcorpus = ""
                        origempty = origempty-1
                    self.setcelltocorpus(origcorpus, rowN, self.origcorpuscol)
                if len(rowlst)>2:
                    lemmcorpus = rowlst[2]
                    self.setcelltocorpus(lemmcorpus, rowN, self.lemmcorpuscol)
                if len(rowlst)>3:
                    uposcorpus = rowlst[3]
                    self.setcelltocorpus(uposcorpus, rowN, self.uposcorpuscol)
                if len(rowlst)>4:
                    xposcorpus = rowlst[4]
                    self.setcelltocorpus(xposcorpus, rowN, self.xposcorpuscol)
                if  len(rowlst)>5:
                    featcorpus = rowlst[5]
                    self.setcelltocorpus(featcorpus, rowN, self.featcorpuscol)
                if len(rowlst)>6:
                    headcorpus = rowlst[6]
                    self.setcelltocorpus(headcorpus, rowN, self.headcorpuscol)
                if len(rowlst)>7:
                    deprelcorpus = rowlst[7]
                    self.setcelltocorpus(deprelcorpus, rowN, self.deprelcorpuscol)
                if len(rowlst)>8:
                    depscorpus = rowlst[8]
                    self.setcelltocorpus(depscorpus, rowN, self.depscorpuscol)
                if len(rowlst)>9:
                    misccorpus = rowlst[9]
                    self.setcelltocorpus(misccorpus, rowN, self.misccorpuscol)


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile("forms/tint.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.loadsettings()
        self.w.quit.clicked.connect(self.accept)
        self.w.loadjava.clicked.connect(self.loadjava)
        self.w.loadtint.clicked.connect(self.loadtint)
        self.setWindowTitle("Impostazioni di Tint")

    def loadsettings(self):
        if platform.system() == "Windows":
            jdir = "C:/Program Files/Java/"
            jfiles = os.listdir(jdir)
            jre = "jre"
            for fil in jfiles:
                if "jre" in fil:
                    jre = fil
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
        QMessageBox.information(self, "Attenzione", "Per qualche motivo, Tint non funziona con Java di Oracle, ma solo con OpenJDK. Puoi scaricarlo da qui per Windows: <a href=\"https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz\">https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz</a>. Devi solo estrarre il file con 7Zip, non servono privilegi di amministrazione.")
        fileName = QFileDialog.getOpenFileName(self, "Trova Java", ".", "Java (*.exe)")[0]
        if fileName != "":
            self.w.java.setText(fileName)

    def loadtint(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella di Tint")
        if fileName != "":
            self.w.tintlib.setText(fileName)
