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
from PySide2.QtCore import QThread
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?

from forms import progress


class TintRunner(QThread):
    dataReceived = Signal(bool)

    def __init__(self, widget,addr = ""):
        QThread.__init__(self)
        self.w = widget
        self.iscli = False
        try:
            if self.w == "cli":
                self.iscli = True
        except:
            self.iscli = False
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
                if self.iscli:
                    print("++"+line+"++")
                else:
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
        self.outputcsv = ""
        self.loadvariables()
        self.setTerminationEnabled(True)
        self.iscli = False
        try:
            if self.w == "cli":
                self.iscli = True
        except:
            self.iscli = False
        self.alwaysyes = False
        self.rowfilename = ""

    def loadvariables(self):
        #http://localhost:8012/tint?text=Barack%20Obama%20era%20il%20presidente%20degli%20Stati%20Uniti%20d%27America.
        self.TintTimeout = 60 #300
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
                    try:
                        if self.w.corpus.rowCount() >0:
                            fileID = int(self.w.corpus.item(self.w.corpus.rowCount()-1,0).text().split("_")[0])
                    except:
                        fileID = 0
                    #QApplication.processEvents()
                    fileID = fileID+1
                    lines = ""
                    try:
                        text_file = open(fileName, "r", encoding='utf-8')
                        lines = text_file.read()
                        text_file.close()
                    except:
                        predefEncode = "ISO-8859-15"
                        #https://pypi.org/project/chardet/
                        try:
                            myencoding = QInputDialog.getText(self.w, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, predefEncode)
                        except:
                            print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
                            myencoding = [input()]
                        try:
                            text_file = open(fileName, "r", encoding=myencoding[0])
                            lines = text_file.read()
                            text_file.close()
                        except:
                           return
                    self.rowfilename = fileName + ".tmp"
                    if self.iscli:
                        self.outputcsv = fileName + ".csv"
                    print(fileName + " -> " + self.outputcsv)
                    self.text2corpusTINT(lines, str(fileID)+"_"+os.path.basename(fileName))
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
        itext = text.replace('.','.\n')
        itext = itext.replace('?','?\n')
        itext = itext.split('\n')
        #itext = re.split('[\n\.\?]', text)
        self.Progrdialog = progress.Form()
        if not self.iscli:
            self.Progrdialog.show()
        totallines = len(itext)
        print("Total lines: "+str(totallines))
        startatrow = -1
        try:
            if os.path.isfile(self.rowfilename):
                ch = "Y"
                if self.iscli:
                    if self.alwaysyes:
                        ch = "y"
                    else:
                        print("Ho trovato un file di ripristino, lo devo usare? [Y/N]")
                        ch = input()
                    if ch == "Y" or ch == "y":
                        with open(self.rowfilename, "r", encoding='utf-8') as tempfile:
                           lastline = (list(tempfile)[-1])
                        startatrow = int(lastline)
                        print("Comincio dalla riga " + str(startatrow))
        except:
            startatrow = -1
        row = 0
        for line in itext:
            row = row + 1
            if row > startatrow:
                self.Progrdialog.w.testo.setText("Sto lavorando sulla frase numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                if not self.iscli and row % 20 == 0:
                    QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                myres = ""
                if line != "":
                    myres = self.getJson(line)
                try:
                    myarray = json.loads(myres)
                except:
                    #print("Errore nella lettura:")
                    #print(line)
                    myarray = {'sentences': []}
                oldtokens = ["A", "A", "A"]
                indoltk = 0
                legenda = {'A': ['adj'], 'AP': ['adj'], 'B': ['adv','prep'], 'BN': ['adv'], 'I': ['adv'], 'S': ['n'], 'T': ['pron'], 'RI': ['art'], 'RD': ['art','pron'], 'V': ['v'], 'E': ['prep'], 'VA': ['v'], 'CC': ['conj'], 'PC': ['art','pron'], 'PR': ['conj', 'pron'], 'VM': ['v'], 'CS': ['conj'], 'PE': ['pron'], 'DD': ['adj'], 'DI': ['pron', 'adj'], 'PI': ['pron'], 'SW': ['n']}
                for sentence in myarray["sentences"]:
                    for token in sentence["tokens"]:
                        morfL = str(token["full_morpho"]).split(' ')
                        posL = str(token["pos"]).split('+')
                        oldtokens[indoltk%3] = posL[0]
                        indoltk = indoltk +1
                        morf = ""
                        try:
                            posN = 0
                            for pos in posL:
                                posML = legenda[pos]
                                ind = 0
                                c = False
                                for morfT in morfL:
                                    #c = False
                                    if ind == 0 and pos=="V" and "VA" in oldtokens:
                                        oldtokens = ["A", "A", "A"]
                                        #se preceduto da ausiliare, è un participio
                                        indo2 = 0
                                        for morfT in morfL:
                                            if "v+part+" in morfT:
                                                ind = indo2
                                                c = True
                                                break
                                            indo2 = indo2 +1
                                    stupidoimperativo = True
                                    for posM in posML:
                                        if bool(re.match('.*?\+'+posM+'([\+/].*?|$)', morfT)):
                                            if "v+imp+pres+" in morfT:
                                                if stupidoimperativo == False:
                                                    if "+2+plur" in morfT or "+2+sing" in morfT:
                                                        if 'I' in oldtokens:
                                                            c = True #il modo imperativo è legittimo solo per seconda persona e solo se c'è una interiezione
                                                            break
                                            else:
                                                c = True
                                                break
                                    if c:
                                        break
                                    ind = ind + 1
                                txt = morfL[ind]
                                if posN > 0:
                                    stind = txt.index('/')+1
                                    stind = txt.index('~',stind)+1
                                    stind = txt.index('+',stind)+1
                                    txt = txt[stind:]
                                else:
                                    stind = txt.index('+')+1
                                    if '/' in txt:
                                        enind = txt.index('/')+1
                                    else:
                                        enind = len(txt)
                                    txt = txt[stind:enind]
                                morf = morf + txt
                                posN = posN +1
                        except:
                            morf = str(token["full_morpho"]) #.split(" ")[0]
                            #print(posL)
                            #print(str(token["full_morpho"]))
                        if self.outputcsv == "":
                            rowN = self.addlinetocorpus(IDcorpus, self.corpuscols["IDcorpus"])
                            self.setcelltocorpus(str(token["index"]), rowN, self.corpuscols["IDword"])
                            self.setcelltocorpus(str(token["originalText"]), rowN, self.corpuscols["Orig"])
                            self.setcelltocorpus(str(token["lemma"]), rowN, self.corpuscols["Lemma"])
                            self.setcelltocorpus(str(token["pos"]), rowN, self.corpuscols["pos"])
                            self.setcelltocorpus(str(token["ner"]), rowN, self.corpuscols["ner"])
                            self.setcelltocorpus(morf, rowN, self.corpuscols["feat"])
                        else:
                            fullline = IDcorpus + "\t" + str(token["originalText"]) + "\t" + str(token["lemma"]) + "\t" + str(token["pos"]) + "\t" + str(token["ner"]) + "\t" + morf + "\t" + str(token["index"])
                            fdatefile = self.outputcsv
                            with open(fdatefile, "a", encoding='utf-8') as myfile:
                                myfile.write(fullline+"\n")
                if self.iscli:
                    with open(self.rowfilename, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
        self.Progrdialog.accept()
        if self.iscli:
            print("Done")

    def getJson(self, text):
        #http://localhost:8012/tint?text=Barack%20Obama%20era%20il%20presidente%20degli%20Stati%20Uniti%20d%27America.
        urltext = urllib.parse.quote(text)
        #print(urltext)
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
            msg = "ERRORE: Tint non risponde. Prova a chiudere il processo \"java\" e riavviare."
            if self.iscli:
                print(msg)
                sys.exit(1)
            else:
                ret = QMessageBox.question(self.w,'Errore', msg + " Vuoi chiudere Bran?", QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.Yes:
                    sys.exit(1)
        try:
            thishtml = ft.decode('utf-8', 'backslashreplace')
        except:
            thishtml = str(ft)
        return thishtml



class Form(QDialog):
    def __init__(self, parent=None, mycfg=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/tint.ui")
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
            self.w.address.setText(mycfg["tintaddr"])
            self.w.port.setText(mycfg["tintport"])
        self.w.quit.clicked.connect(self.quitme)
        self.w.loadjava.clicked.connect(self.loadjava)
        self.w.loadtint.clicked.connect(self.loadtint)
        self.setWindowTitle("Impostazioni di Tint")
        self.notint = False

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
