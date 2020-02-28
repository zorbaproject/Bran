#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pip
import sys
import os
import re
import urllib.request
import urllib.parse
import html
import datetime
import time
import json
from socket import timeout
import subprocess
import platform
import mmap
import random
import math

arch = platform.architecture()[0]

try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        from tkinter import messagebox
        thispkg = "le librerie grafiche"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "PySide2"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        from PySide2.QtWidgets import QApplication
    except:
        try:
            from pip._internal import main as pipmain
            from tkinter import messagebox
            pipmain(["install", "PySide2"])
            from PySide2.QtWidgets import QApplication
        except:
            sys.exit(1)

from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import QDir
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtWidgets import QTableWidgetSelectionRange
from PySide2.QtCore import QThread
from PySide2.QtCore import QObject
from PySide2.QtWidgets import QWidget

from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor
from forms import confronto
from forms import tint
from forms import progress
from forms import sessione
from forms import ripetizioni
from forms import about
from forms import creafiltro
from forms import alberofrasi



class BranCorpus(QObject):
    sizeChanged = Signal(int)
    progressUpdated = Signal(int)

    def __init__(self, corpcol, legPos, ignthis, dimlst, tablewidget=None, parent=None):
        #super(BranCorpus, self).__init__(parent)
        super(BranCorpus, self).__init__()
        #self.w = window
        self.corpuswidget = tablewidget
        self.corpus = []
        self.daToken = 0
        self.aToken = 100
        self.allToken = False
        self.corpuswidget.cellChanged.connect(self.corpusCellChanged)
        #self.setWindowTitle("Bran")
        self.corpuscols = corpcol
        self.legendaPos = legPos
        self.ignoretext = ignthis
        self.dimList = dimlst
        #self.ignorepos = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "altro"] # "punteggiatura - .?!"
        self.ignorepos = ["punteggiatura - .?!", "simboli", "altro"]
        self.separator = "\t"
        self.language = "it-IT"
        self.filtrimultiplienabled = 10 #"Filtro multiplo"
        self.filter = ""
        self.filterColumn = self.filtrimultiplienabled
        self.alreadyChecked = False
        self.ImportingFile = False
        self.OnlyVisibleRows = False
        self.sessionFile = ""
        self.sessionDir = "."
        self.mycfgfile = QDir.homePath() + "/.brancfg"
        self.mycfg = json.loads('{"javapath": "", "tintpath": "", "tintaddr": "", "tintport": "", "udpipe": "", "rscript": "", "sessions" : []}')
        self.loadPersonalCFG()
        #TODO: Should we specify the session in the constructor?
        #self.txtloadingstopped()

    def changeLang(self, lang):
        self.language = lang
        print("Set language "+self.language)

    def setOnlyVisible(self, value):
        self.OnlyVisibleRows = value

    def setStart(self, value):
        self.daToken = value
        #print("Set start: " +str(value))

    def setEnd(self, value):
        self.aToken = value
        #print("Set end: " +str(value))

    def setAllTokens(self, value):
        self.allToken = value
        self.setStart(0)
        self.setEnd(len(self.corpus))

    def setFilter(self, text):
        self.filter = text

    def loadPersonalCFG(self):
        try:
            text_file = open(self.mycfgfile, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
            self.mycfg = json.loads(lines.replace("\n", "").replace("\r", ""))
        except:
            try:
                text_file = open(self.mycfgfile, "r", encoding='ISO-8859-15')
                lines = text_file.read()
                text_file.close()
                self.mycfg = json.loads(lines.replace("\n", "").replace("\r", ""))
            except:
                print("Creo il file di configurazione")

    def savePersonalCFG(self):
        cfgtxt = json.dumps(self.mycfg)
        text_file = open(self.mycfgfile, "w", encoding='utf-8')
        text_file.write(cfgtxt)
        text_file.close()

    def chiudiProgetto(self):
        self.sessionFile = ""
        self.sessionDir = "."
        self.corpus = []
        for row in range(self.corpuswidget.rowCount()):
            self.corpuswidget.removeRow(0)
            if row<100 or row%100==0:
                QApplication.processEvents()
        #self.setWindowTitle("Bran")

    def loadFromTint(self, tintaddr = "localhost"):
        self.TintAddr = tintaddr
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        if self.language == "it-IT":
            self.TCThread = tint.TintCorpus(self.corpuswidget, fileNames, self.corpuscols, self.TintAddr)
            self.TCThread.outputcsv = self.sessionFile
            self.TCThread.finished.connect(self.txtloadingstopped)
            self.TCThread.start()
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadFromUDpipe(self):
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        if self.language != "it-IT" and self.language != "en-US":
            print("Language "+ self.language +" not supported")
            return
        udpipe = self.mycfg["udpipe"]
        model = self.mycfg["udpipemodels"][self.language]
        self.UDThread = UDCorpus(self.corpuswidget, fileNames, self.corpuscols, udpipe, model, self.language)
        self.UDThread.outputcsv = self.sessionFile
        self.UDThread.finished.connect(self.txtloadingstopped)
        self.UDThread.start()
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadTextFromCSV(self):
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv)")[0]
        if len(fileNames)<1:
            return
        if self.language == "it-IT":
            print("UDpipe still not supported")
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadjson(self):
        QMessageBox.information(self.corpuswidget, "Attenzione", "Caricare un file JSON non è più supportato.")

    def opentextfile(self, fileName):
        lines = ""
        try:
            text_file = open(fileName, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
        except:
            myencoding = "ISO-8859-15"
            #https://pypi.org/project/chardet/
            gotEncoding = False
            while gotEncoding == False:
                try:
                    myencoding = QInputDialog.getText(self.corpuswidget, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
                except:
                    print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
                    myencoding = [input()]
                try:
                    # TODO: prevediamo la codifica "FORCE", che permette di leggere il file come binario ignorando caratteri strani
                    text_file = open(fileName, "r", encoding=myencoding[0])
                    lines = text_file.read()
                    text_file.close()
                    gotEncoding = True
                except:
                    gotEncoding = False
        return lines

    def importfromTreeTagger(self):
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv *.txt)")[0]
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/treetagger-"+self.language+".json"
        try:
            text_file = open(filein, "r")
            myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
            text_file.close()
            legendaTT = json.loads(myjson)
        except:
            QMessageBox.warning(self.corpuswidget, "Errore", "Non riesco a leggere il dizionario di traduzione per TreeTagger.")
            return
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.ImportingFile = True
        for fileName in fileNames:
            totallines = 0
            try:
                if not os.path.getsize(fileName) > 0:
                    continue
                totallines = self.linescount(fileName)
            except:
                continue
            lines = self.opentextfile(fileName)
            trowN = 0
            for line in lines.split("\n"):
                if trowN<100 or trowN%100==0:
                    self.Progrdialog.w.testo.setText("Sto importando la riga numero "+str(trowN))
                    self.Progrdialog.w.progressBar.setValue(int((trowN/totallines)*100))
                    QApplication.processEvents()
                trowN = trowN + 1
                colN = 0
                if self.Progrdialog.w.annulla.isChecked():
                    self.Progrdialog.reject()
                    self.ImportingFile = False
                    return
                try:
                    cols = line.replace("\r", "").split("\t")
                    if cols[0] == "":
                        continue
                    tmpline = ['' for i in range(len(self.corpuscols))]  #Using list comprehension
                    tmpline[self.corpuscols["token"][0]] = str(cols[0])
                    tmpline[self.corpuscols["lemma"][0]] = str(cols[2])
                    try:
                        tmpline[self.corpuscols["pos"][0]] = legendaTT[str(cols[1])]
                    except:
                        tmpline[self.corpuscols["pos"][0]] = str(cols[1])
                    self.corpus.append(tmpline)
                except:
                    continue
        #self.updateCorpus(self.Progrdialog)
        self.Progrdialog.accept()
        self.sizeChanged.emit(len(self.corpus))
        self.updateCorpus()

    def loadCSV(self):
        if self.ImportingFile == False:
            fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file CSV", self.sessionDir, "File CSV (*.tsv *.txt *.csv)")[0]
            self.ImportingFile = True
            self.CSVloader(fileNames) #self.CSVloader(fileNames, self.Progrdialog)

    def CSVloader(self, fileNames):
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    print(fileName)
                    if not os.path.getsize(fileName) > 0:
                        #break
                        self.ImportingFile = False
                        continue
                    #print("Importing")
                    try:
                        totallines = self.linescount(fileName)
                        #print(totallines)
                    except Exception as ex:
                        print(ex)
                        self.ImportingFile = False
                        continue
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    linesA = lines.split('\n')
                    maximum = self.daToken+len(linesA)-1
                    #print("Maximum: "+str(maximum))
                    for line in linesA:
                        if line == "":
                            continue
                        newtoken = line.split(self.separator)
                        if len(newtoken) < len(self.corpuscols):
                            for i in range(len(newtoken),len(self.corpuscols)):
                                newtoken.append("")
                        elif len(newtoken) > len(self.corpuscols):
                            newtoken = newtoken[0:len(self.corpuscols)]
                        self.corpus.append(newtoken)
        #print("Updating view")
        self.sizeChanged.emit(len(self.corpus))
        self.updateCorpus()
        self.ImportingFile = False

    def linescount(self, filename):
        f = open(filename, "r+", encoding='utf-8')
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    def txtloadingstopped(self):
        print("Loading project")
        if self.sessionFile != "" and self.ImportingFile == False:
            if os.path.isfile(self.sessionFile):
                if not os.path.getsize(self.sessionFile) > 1:
                    return
            try:
                self.ImportingFile = True
                fileNames = ['']
                fileNames[0] = self.sessionFile
                self.corpuswidget.setRowCount(0)
                print("Reading CSV")
                self.CSVloader(fileNames)
            except Exception as ex:
                print(ex)
                try:
                    self.myprogress.reject()
                    self.ImportingFile = False
                except:
                    self.ImportingFile = False
                    return

    def salvaProgetto(self):
        if self.sessionFile == "":
            fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
            if fileName != "":
                self.sessionFile = fileName
        if self.sessionFile != "":
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            self.CSVsaver(self.sessionFile, self.Progrdialog, False)

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.CSVsaver(fileName, self.Progrdialog, True)

    def CSVsaver(self, fileName, Progrdialog, addheader = False, onlyrows = []):
        self.sanitizeTable(self.corpuswidget)
        self.sanitizeCorpus()
        if fileName != "":
            if fileName[-4:] != ".csv" and fileName[-4:] != ".tsv":
                fileName = fileName + ".tsv"
            csv = ""
            if addheader:
                col = 0
                for key in self.corpuscols:
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.corpuscols[key][1]
                    col = col +1
            totallines = len(self.corpus)
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()
            if len(onlyrows)==0:
                onlyrows = range(totallines)
            for row in onlyrows:
                #csv = csv + "\n"
                csv = ""
                Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                for col in range(len(self.corpuscols)):
                    if Progrdialog.w.annulla.isChecked():
                        return
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.corpus[row][col]
                with open(fileName, "a", encoding='utf-8') as myfile:
                    myfile.write(csv+"\n")
            Progrdialog.accept()

    def connluexport(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.corpus_to_connlu(fileName, self.Progrdialog, True)

    def corpus_to_connlu(self, fileName, Progrdialog, addcomments = False, onlyrows = []):
        self.sanitizeTable(self.corpuswidget)
        self.sanitizeCorpus()
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/isdt-ud.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        legendaISDTUD = json.loads(myjson)
        if fileName != "":
            if fileName[-4:] != ".csv" and fileName[-4:] != ".tsv":
                fileName = fileName + ".tsv"
            csv = ""
            if addcomments:
                try:
                    csv = "# newdoc id = " + self.corpus[0][self.corpuscols['TAGcorpus'][0]]
                except:
                    csv = "# newdoc id = Corpus esportato da Bran"
                csv = csv + "\n# newpar"
            totallines = len(self.corpus)
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()
            if len(onlyrows)==0:
                onlyrows = range(totallines)
            oldphrase = ""
            for row in onlyrows:
                csv = ""
                Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if Progrdialog.w.annulla.isChecked():
                    return
                Ucolumns = []
                Ucolumns.append(self.corpus[row][self.corpuscols['IDword'][0]])
                Ucolumns.append(self.corpus[row][self.corpuscols['token'][0]])
                if "[PUNCT]" in self.corpus[row][self.corpuscols['lemma'][0]]:
                    Ucolumns.append(self.corpus[row][self.corpuscols['token'][0]])
                else:
                    Ucolumns.append(self.corpus[row][self.corpuscols['lemma'][0]])
                mypos = self.corpus[row][self.corpuscols['pos'][0]]
                myposU = legendaISDTUD["pos"][mypos][0]
                Ucolumns.append(myposU)
                Ucolumns.append(mypos)
                myfeat = self.corpus[row][self.corpuscols['feat'][0]]
                myfeatU = ""
                for featpart in myfeat.split("/"):
                    tmpfeat = ""
                    for featel in featpart.split("+"):
                        try:
                            translated = legendaISDTUD["feat"][featel]
                        except:
                            #print("IGNORED: "+featel)
                            translated = ""
                        for trelem in translated.split("|"):
                            if not trelem in tmpfeat:
                                tmpfeat = tmpfeat + "|" + trelem
                    myfeatU = myfeatU + tmpfeat + "/"
                #add from pos
                myfeatU = re.sub("^\|*", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                myfeatU = re.sub("[^a-z]*$", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                tmpmorf = legendaISDTUD["pos"][mypos][1].split("/")
                myfeatUtotal = ""
                for tmppart in range(len(myfeatU.split("/"))):
                    myfeatUtotal = myfeatUtotal + myfeatU.split("/")[tmppart]
                    try:
                        for tmpelem in tmpmorf[tmppart].split("|"):
                            if not tmpelem in myfeatU.split("/")[tmppart]:
                                myfeatUtotal = myfeatUtotal + "|" + tmpelem
                    except:
                        continue
                    myfeatUtotal = myfeatUtotal + "/"
                myfeatU = myfeatUtotal
                #clean double chars
                while "||" in myfeatU or "/|" in myfeatU:
                    myfeatU = myfeatU.replace("||","|")
                    myfeatU = myfeatU.replace("/|","/")
                myfeatU = re.sub("^[\|]*", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                myfeatU = re.sub("[^a-z]*$", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                if myfeatU == "":
                    myfeatU = "_"
                Ucolumns.append(myfeatU)
                Ucolumns.append(self.corpus[row][self.corpuscols['governor'][0]])
                Ucolumns.append(self.corpus[row][self.corpuscols['dep'][0]])
                Ucolumns.append("_")
                Ucolumns.append("_")
                #Ucolumns.append(self.corpuswidget.item(row,self.corpuscols['ner'][0]).text())

                #ricostruzione della frase
                if self.corpus[row][self.corpuscols['IDphrase'][0]] != oldphrase and addcomments:
                    oldphrase = self.corpus[row][self.corpuscols['IDphrase'][0]]
                    csv = csv + "\n# sent_id = " + str(int(self.corpus[row][self.corpuscols['IDphrase'][0]])+1) + "\n"
                    endrow = row
                    while self.corpus[row][self.corpuscols['IDphrase'][0]] == self.corpus[endrow][self.corpuscols['IDphrase'][0]] and endrow<(len(self.corpus)-1):
                        endrow = endrow +1
                    myignore = []
                    phraseText = self.rebuildText(self.corpus, self.Progrdialog, self.corpuscols['token'][0], myignore, row, endrow)
                    phraseText = self.remUselessSpaces(phraseText)
                    if phraseText[-1] == " ":
                        phraseText = phraseText[:-1]
                    csv = csv + "# text = " + phraseText + "\n"
                for col in range(len(Ucolumns)):
                    if Ucolumns[col] == "":
                        Ucolumns[col] = "_"
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + Ucolumns[col]
                with open(fileName, "a", encoding='utf-8') as myfile:
                    myfile.write(csv+"\n")
            Progrdialog.accept()

    def convertiDaTint(self):
        fileName = QFileDialog.getOpenFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        if not fileName == "":
            newName = fileName
            fileName = fileName.replace(".tsv","")+"-old.tsv"
            os.rename(newName,fileName)
            TestThread = tint.TintCorpus(self.corpuswidget, [], self.corpuscols, "localhost")
            if os.path.isfile(fileName):
                if not os.path.getsize(fileName) > 0:
                    return
                try:
                    totallines = self.linescount(fileName)
                    print(totallines)
                except Exception as ex:
                    print(ex)
                    return
                text_file = open(fileName, "r", encoding='utf-8')
                lines = text_file.read()
                text_file.close()
                linesA = lines.split('\n')
                for line in linesA:
                    if line == "":
                        continue
                    fullline = TestThread.isdt_to_ud(line)
                    with open(newName, "a", encoding='utf-8') as myfile:
                        myfile.write(fullline+"\n")

    def esportavistaCSV(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        toselect = []
        for row in range(self.corpuswidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.corpuswidget.isRowHidden(row):
                toselect.append(row)
        self.CSVsaver(fileName, self.Progrdialog, True, toselect)

    def esportafiltroCSV(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        toselect = []
        totallines = len(self.corpus)
        startline = 0
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.applicaFiltro(row, self.filtrimultiplienabled, self.filter):
                continue
            toselect.append(row)
        self.Progrdialog.accept()
        self.CSVsaver(fileName, self.Progrdialog, True, toselect)

    def esportaCSVperID(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        IDs = []
        col = self.corpuscols['TAGcorpus'][0]
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.corpus[row][col] in IDs:
                IDs.append(self.corpus[row][col])
        for i in range(len(IDs)):
            toselect = []
            for row in range(startline, totallines):
                self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if IDs[i] == self.corpus[row][col]:
                    toselect.append(row)
                    QApplication.processEvents()
            fileNameT = fileName + str(i).zfill(6) + ".tsv"
            self.CSVsaver(fileNameT, self.Progrdialog, True, toselect)


    def replaceCorpus(self):
        repCdialog = regex_replace.Form(self.corpuswidget)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.w.changeCase.show()
        repCdialog.exec()
        if repCdialog.result():
            if repCdialog.w.ignorecase.isChecked():
                myflags=re.IGNORECASE|re.DOTALL
            else:
                myflags=re.DOTALL
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            totallines = len(self.corpus)
            startline = 0
            if self.OnlyVisibleRows:
                totallines = self.aToken
                startline = self.daToken
            for row in range(startline, totallines):
                self.Progrdialog.w.testo.setText("Sto cercando nella riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                        continue
                for col in range(len(self.corpus[row])):
                    if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                        origstr = self.corpus[row][col]
                        newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=myflags)
                        if repCdialog.w.dolower.isChecked():
                            indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                            for f in indexes:
                                newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                        if repCdialog.w.doupper.isChecked():
                            indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                            for f in indexes:
                                newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                        #self.setcelltocorpus(newstr, row, col)
                        self.corpus[row][col] = newstr
            self.Progrdialog.accept()
            self.updateCorpus()

    def replaceCells(self):
        repCdialog = regex_replace.Form(self.corpuswidget)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.w.changeCase.show()
        repCdialog.exec()
        if repCdialog.result():
            if repCdialog.w.ignorecase.isChecked():
                myflags=re.IGNORECASE|re.DOTALL
            else:
                myflags=re.DOTALL
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            startline = self.daToken
            totallines = len(self.corpuswidget.selectedItems())
            for i in range(len(self.corpuswidget.selectedItems())):
                row = self.corpuswidget.selectedItems()[i].row()
                col = self.corpuswidget.selectedItems()[i].column()
                self.Progrdialog.w.testo.setText("Sto cercando nella cella numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                    origstr = self.corpus[startline+row][col]
                    newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=myflags)
                    if repCdialog.w.dolower.isChecked():
                        indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                        for f in indexes:
                            newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                    if repCdialog.w.doupper.isChecked():
                        indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                        for f in indexes:
                            newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                    self.corpus[startline+row][col] = newstr
            self.Progrdialog.accept()
            self.updateCorpus()

    def selectVisibleCells(self):
        self.deselectAllCells()
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        for row in range(self.corpuswidget.rowCount()):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row):
                continue
            if row<100 or row%100==0:
                self.Progrdialog.w.testo.setText("Sto selezionando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisrow = QTableWidgetSelectionRange(row,0,row,self.corpuswidget.columnCount()-1)
            self.corpuswidget.setRangeSelected(thisrow, True)
        self.Progrdialog.accept()

    def deselectAllCells(self):
        self.corpuswidget.clearSelection()

    def contaoccorrenze(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(column[0], 0)
        TBdialog.addcolumn("Occorrenze", 1)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        self.progressUpdated.connect(self.Progrdialog.setValue)
        self.Progrdialog.setBasetext("Sto conteggiando la riga numero ")
        self.Progrdialog.setTotal(totallines)
        for row in range(startline, totallines):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                continue
            #self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            #self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            #QApplication.processEvents()
            self.progressUpdated.emit(row)
            if row<100 or row % 100 == 0:
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.corpus[row][col]
                try:
                    if col == self.corpuscols["pos"][0]:
                        thistext = self.legendaPos[thistext][0]
                except:
                    thistext = self.corpus[row][col]
            except:
                thistext = ""
            tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
            if tbrow>=0:
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        #TBdialog.exec()
        TBdialog.show()

    def contaoccorrenzefiltrate(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        QMessageBox.information(self.corpuswidget, "Filtro", "Ora devi impostare i filtri con cui dividere i risultati. I vari filtri devono essere separati da condizioni OR, per ciascuno di essi verrà creata una colonna a parte nella tabella dei risultati.")
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText("pos=A.*||pos=S.*")
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() == "":
            return
        allfilters = Fildialog.w.filter.text().split("||")
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(column[0], 0)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        for myfilter in allfilters:
            TBdialog.addcolumn(myfilter, 1)
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.corpus[row][col]
                try:
                    if col == self.corpuscols["pos"][0]:
                        thistext = self.legendaPos[thistext][0]
                except:
                    thistext = self.corpus[row][col]
            except:
                thistext = ""
            for ifilter in range(len(allfilters)):
                if self.applicaFiltro(row, fcol, allfilters[ifilter]):
                    tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        try:
                            tbval = int(TBdialog.w.tableWidget.item(tbrow,ifilter+1).text())+1
                        except:
                            tbval = 1
                        TBdialog.setcelltotable(str(tbval), tbrow, ifilter+1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable("1", tbrow, ifilter+1)
        self.Progrdialog.accept()
        TBdialog.show()

    def orderVerbMorf(self, text, ignoreperson = False):
        if not "VerbForm" in text:
            return text
        mytext = ""
        #Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin
        vform = ""
        mood = ""
        tense = ""
        pers = ""
        num = ""
        gender = ""
        for el in text.split("|"):
            if "VerbForm" in el:
                vform = re.sub(".*VerbForm\=(.*)","\g<1>",el)
            if "Mood" in el:
                mood = re.sub(".*Mood\=(.*)","\g<1>",el)
            if "Tense" in el:
                tense = re.sub(".*Tense\=(.*)","\g<1>",el)
            if "Person" in el:
                pers = re.sub(".*Person\=(.*)","\g<1>",el)
            if "Number" in el:
                num = re.sub(".*Number\=(.*)","\g<1>",el)
            if "Gender" in el:
                gender = re.sub(".*Gender\=(.*)","\g<1>",el)
        mytext = "VerbForm=" + vform
        if mood != "":
            mytext = mytext + "|Mood=" + mood
        if tense != "":
            mytext = mytext + "|Tense=" + tense
        if pers != "" and ignoreperson==False:
            mytext = mytext + "|Person=" + pers
        if num != "" and ignoreperson==False:
            mytext = mytext + "|Number=" + num
        if gender != "" and ignoreperson==False:
            mytext = mytext + "|Gender=" + gender
        return mytext

    def contaverbi(self):
        poscol = self.corpuscols["pos"][0] #thisname.index(column[0])
        morfcol = self.corpuscols["feat"][0]
        frasecol = self.corpuscols["IDphrase"][0]
        ignoreperson = False
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare persona, numero, genere, e caratteristica clitica dei verbi?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            ignoreperson = True
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Modo+Tempo", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        TBdialog.addcolumn("Percentuali", 1)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if row < startline:
                continue
            try:
                thispos = self.legendaPos[self.corpus[row][poscol]][0]
                thisphrase = self.corpus[row][frasecol]
            except:
                thispos = ""    
                thisphrase = "0"
            thistext = ""
            thistext2 = ""
            thistext3 = ""
            #Filtro per trovare i verbi a 3 come "è stato fatto": feat=.*VerbForm.*Part.*&&feat[1]=.*VerbForm.*Part.*||feat=.*VerbForm.*Part.*&&feat[-1]=.*VerbForm.*Part.*||feat=.*VerbForm.*&&feat[1]=.*VerbForm.*Part.*&&feat[2]=.*VerbForm.*Part.*
            if "verbo" in thispos:
                thistext = self.corpus[row][morfcol]
            if "ausiliare" in thispos:
                for ind in range(1,4):
                    try:
                        tmpos = self.legendaPos[self.corpus[row+ind][poscol]][0]
                        tmpphrase = self.corpus[row+ind][frasecol]
                    except:
                        tmpos = ""
                        tmpphrase = "0"
                    #i verbi consecutivi vanno bene finché sono nella stessa frase
                    if tmpphrase != thisphrase:
                        break
                    if "verbo" in tmpos:
                        thistext2 = thistext2 + self.corpus[row+ind][morfcol] + "+"
                    startline = row+ind+1
                if len(thistext2.split("+"))>1:
                    thistext3 = thistext2.split("+")[1]
                    thistext2 = thistext2.split("+")[0]
            if len(thistext) >= 3:
                thistext = self.orderVerbMorf(thistext, ignoreperson) + "+"
            if len(thistext2) >= 3:
                thistext2 = self.orderVerbMorf(thistext2, ignoreperson) + "+"
            if len(thistext3) >= 3:
                thistext3 = self.orderVerbMorf(thistext3, ignoreperson) #+ "+"
            if thistext != "":
                thistext = thistext + thistext2 + thistext3
                if ignoreperson:
                    thistext = thistext.replace("/Clitic=Yes", "")
            if thistext.endswith("+"):
                thistext = thistext[0:-1]
            if thistext != "":
                tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                if tbrow>=0:
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 1)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable("1", tbrow, 1)
        #calcolo le percentuali
        totallines = TBdialog.w.tableWidget.rowCount()
        verbitotali = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            verbitotali = verbitotali + int(TBdialog.w.tableWidget.item(row,1).text())
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto calcolando le percentuali su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            ratio = (float(TBdialog.w.tableWidget.item(row,1).text())/float(verbitotali)*100)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(ratios, row, 2)
        self.Progrdialog.accept()
        TBdialog.show()

    def trovaripetizioni(self):
        Repetdialog = ripetizioni.Form(self.corpuswidget)
        Repetdialog.loadipos(self.ignorepos)
        Repetdialog.loadallpos(self.legendaPos)
        self.enumeratecolumns(Repetdialog.w.colonna)
        Repetdialog.w.colonna.setCurrentIndex(self.corpuscols['token'][0])
        Repetdialog.exec()
        if Repetdialog.result():
            tokenda = Repetdialog.w.tokenda.value()
            tokena = Repetdialog.w.tokena.value()
            minoccur = Repetdialog.w.minoccurr.value()
            ignorecase = Repetdialog.w.ignorecase.isChecked()
            remspaces = bool(Repetdialog.w.remspaces.isChecked() and not Repetdialog.w.sigindex.isChecked())
            col = Repetdialog.w.colonna.currentIndex()
            ipunct = []
            for i in range(Repetdialog.w.ignorapos.count()):
                ipunct.append(Repetdialog.w.ignorapos.item(i).text())
            vuoteI = []
            if Repetdialog.w.ignoreI.isChecked():
                for i in range(Repetdialog.w.vuoteI.count()):
                    vuoteI.append(Repetdialog.w.vuoteI.item(i).text())
            vuoteF = []
            if Repetdialog.w.ignoreF.isChecked():
                for i in range(Repetdialog.w.vuoteF.count()):
                    vuoteF.append(Repetdialog.w.vuoteF.item(i).text())
            charNotWord = Repetdialog.w.charNotWord.isChecked()
            TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
            TBdialog.sessionDir = self.sessionDir
            TBdialog.addcolumn("nGram", 0)
            TBdialog.addcolumn("Occorrenze", 1)
            TBdialog.addcolumn("Parole piene", 2)
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            for tokens in range(tokenda, tokena+1):
                self.findngrams(tokens, minoccur, TBdialog, self.Progrdialog, ignorecase, remspaces, ipunct, col, vuoteI, vuoteF, charNotWord)
            if Repetdialog.w.sigindex.isChecked():
                TBdialog.addcolumn("Significatività assoluta", 3)
                TBdialog.addcolumn("Significatività relativa", 4)
                for row in range(TBdialog.w.tableWidget.rowCount()):
                    totallines = TBdialog.w.tableWidget.rowCount()
                    self.Progrdialog.w.testo.setText("Sto calcolando la significatività nella riga "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    sigass = 0.0
                    sigrel = 0.0
                    tmpstring = TBdialog.w.tableWidget.item(row,0).text()
                    Fseg = int(TBdialog.w.tableWidget.item(row,1).text())*1.0
                    sommatoria = 0.0
                    tmplist = tmpstring.split(" ")
                    for tmpword in tmplist:
                        # Controlliamo self.OnlyVisibleRows e facciamo un subset solo con le righe visibili?
                        crpitems = self.findItemsInColumn(self.corpus, tmpword, col)
                        lencrpitems = len(crpitems)
                        #lencrpitems = 0
                        #for crpitem in crpitems:
                        #    lencrpitems = lencrpitems +1
                        Fw = len(crpitems)*1.0
                        if Fw!=0:
                            sommatoria = sommatoria + (Fseg/Fw)
                    sigass = sommatoria * int(TBdialog.w.tableWidget.item(row,2).text())*1.0
                    ampiezza = len(tmplist) + 1
                    sigrel = (sigass*1.0)/(ampiezza*ampiezza)
                    TBdialog.setcelltotable(str(sigass), row, 3)
                    TBdialog.setcelltotable(str(sigrel), row, 4)
            if Repetdialog.w.remspaces.isChecked():
                for row in range(TBdialog.w.tableWidget.rowCount()):
                    totallines = TBdialog.w.tableWidget.rowCount()
                    self.Progrdialog.w.testo.setText("Sto pulendo gli spazi nella riga "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    tmpstring = TBdialog.w.tableWidget.item(row,0).text()
                    tmpstring = self.remUselessSpaces(tmpstring)
                    TBdialog.setcelltotable(tmpstring, row, 0)
            self.Progrdialog.accept()
            TBdialog.show()

    def ricostruisciTesto(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Su quale colonna devo ricostruire il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        mycorpus = self.rebuildText(self.corpus, self.Progrdialog, col)
        mycorpus = self.remUselessSpaces(mycorpus)
        self.Progrdialog.accept()
        te = texteditor.TextEditor(self.corpuswidget, self.mycfg)
        te.w.plainTextEdit.setPlainText(mycorpus)
        te.show()

    def rebuildText(self, table, Progrdialog, col = "", ipunct = [], startrow = 0, endrow = 0, filtercol = None):
        mycorpus = ""
        if col == "":
            col = self.corpuscols['token'][0]
        totallines = len(table)
        if endrow == 0:
            endrow = totallines
        for row in range(startrow, endrow):
            ftext = self.filter
            if filtercol != None:
                if self.OnlyVisibleRows and self.applicaFiltro(row, filtercol, ftext, table):
                    continue
            Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if Progrdialog.w.annulla.isChecked():
                return
            if row >= 0 and row < len(table):
                thispos = self.legendaPos[table[row][self.corpuscols['pos'][0]]][0]
                if not thispos in ipunct:
                    mycorpus = mycorpus + table[row][col] + " "
        return mycorpus

    def remUselessSpaces(self, tempstring):
        punt = " (["+re.escape(".,;!?)")+ "])"
        tmpstring = re.sub(punt, "\g<1>", tempstring, flags=re.IGNORECASE)
        punt = "(["+re.escape("'’(")+ "]) "
        tmpstring = re.sub(punt, "\g<1>", tmpstring, flags=re.IGNORECASE|re.DOTALL)
        return tmpstring

    def findngrams(self, tokens, minoccur, TBdialog, Progrdialog, ignorecase, remspaces, ipunct, col, vuoteI, vuoteF, charNotWord= False):
        mycorpus = self.rebuildText(self.corpus, Progrdialog, col, ipunct)
        if ignorecase:
            mycorpus = mycorpus.lower()
        searchthis = " "
        active = True
        pos = 0
        totallines = len(mycorpus)
        while active:
            wpos = pos
            npos = pos
            Progrdialog.w.testo.setText("Sto conteggiando il carattere numero "+str(pos))
            Progrdialog.w.progressBar.setValue(int((pos/totallines)*100))
            QApplication.processEvents()
            if Progrdialog.w.annulla.isChecked():
                return
            if not charNotWord:
                #read a specific number of words
                for i in range(tokens):
                    wpos = mycorpus.find(searchthis, npos+1)
                    if wpos > 0:
                        npos = wpos
            else:
                npos = pos+tokens
            #check if we reached someway the end of text
            if npos > len(mycorpus)-1:
                if pos > len(mycorpus)-1:
                    break
                else:
                    npos = len(mycorpus)-1
            #read this phrase
            tmpstring = mycorpus[pos:npos]
            parolai = re.sub(" .*", "", tmpstring, flags=re.IGNORECASE|re.DOTALL)
            parolaf = re.sub(".* ", "", tmpstring, flags=re.IGNORECASE|re.DOTALL)
            #look for all occurrences of this phrase
            if not charNotWord:
                wnIsRight = bool(tmpstring.count(searchthis)==tokens-1)
            else:
                wnIsRight = bool(len(tmpstring)==tokens)
            if tmpstring != "" and wnIsRight and bool(not parolai in vuoteI) and bool(not parolaf in vuoteF):
                tcount = mycorpus.count(tmpstring)
                if tcount >= minoccur:
                    tbrow = TBdialog.finditemincolumn(tmpstring, col=0, matchexactly = True, escape = True)
                    if tbrow<=0:
                        TBdialog.addlinetotable(tmpstring, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable(str(tcount), tbrow, 1)
                        ppcount = 0
                        tmplist = tmpstring.split(" ")
                        for tmpword in tmplist:
                            mycol = col
                            if ignorecase:
                                myfl = re.IGNORECASE|re.DOTALL
                            else:
                                myfl=re.DOTALL
                            tmprow = self.finditemincolumn(tmpword, col=mycol, matchexactly = True, escape = True, myflags=myfl)
                            if tmprow<0:
                                #print("Parola non riconosciuta: "+tmpword)
                                ppcount = ppcount + 1
                            else:
                                posword = self.corpus[tmprow][self.corpuscols['pos'][0]]
                                for key in self.legendaPos:
                                    if posword == self.legendaPos[key][0] or posword == key:
                                        if "piene" == self.legendaPos[key][2]:
                                            ppcount = ppcount + 1
                                            break
                                        if "vuote" == self.legendaPos[key][2]:
                                            break
                        TBdialog.setcelltotable(str(ppcount), tbrow, 2)
                #newtext = nth_replace(mycorpus, tmpstring, "", 2, "all right")
                #text = newtext
            if not charNotWord:
                pos = mycorpus.find(searchthis, pos+1)+1 #continue from next word
            else:
                pos = pos+1
            if pos <= 0:
                pos = len(mycorpus)


    def translatePos(self):
        col = self.corpuscols['pos'][0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto lavorando sulla riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.corpus[row][col]
            except:
                thistext = ""
            try:
                newtext = self.legendaPos[thistext][0]
            except:
                newtext = thistext
            self.corpus[row][col] = newtext
            #self.corpuswidget.item(row,col).setToolTip(newtext)
        self.Progrdialog.accept()
        self.updateCorpus()

    def densitalessico(self):
        col = self.corpuscols['pos'][0]
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Part of Speech", 0)
        TBdialog.addcolumn("Macrocategoria", 1)
        TBdialog.addcolumn("Occorrenze", 2)
        TBdialog.addcolumn("Percentuale", 3)
        #calcolo le occorrenze del pos
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        mytypes = {}
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistextO = self.corpus[row][col]
                thistext = self.legendaPos[thistextO][0]
                thisposc = self.legendaPos[self.corpus[row][self.corpuscols['pos'][0]]][1]
                try:
                    mytypes[thisposc] = mytypes[thisposc] +1
                except:
                    mytypes[thisposc] = 1
            except:
                thistext = ""
                thistextO = ""
            if thistext != "":
                tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                if tbrow>=0:
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,2).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 2)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable(self.legendaPos[thistextO][1], tbrow, 1)
                    TBdialog.setcelltotable("1", tbrow, 2)
        #calcolo le somme di parole piene e vuote
        totallines = TBdialog.w.tableWidget.rowCount()
        paroletotali = 0
        parolepiene = 0
        parolevuote = 0
        parolenone = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto sommando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            thistext = TBdialog.w.tableWidget.item(row,0).text()
            for key in self.legendaPos:
                if thistext == self.legendaPos[key][0]:
                    if "piene" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,2).text())
                        parolepiene = parolepiene + int(TBdialog.w.tableWidget.item(row,2).text())
                        break
                    if "vuote" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,2).text())
                        parolevuote = parolevuote + int(TBdialog.w.tableWidget.item(row,2).text())
                        break
                    if "none" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,2).text())
                        parolenone = parolenone + int(TBdialog.w.tableWidget.item(row,2).text())
                        break
        #presento le macrocategorie
        for key in mytypes:
            TBdialog.addlinetotable(key, 1)
            tbrow = TBdialog.w.tableWidget.rowCount()-1
            TBdialog.setcelltotable(str(mytypes[key]), tbrow, 2)
        TBdialog.addlinetotable("Parole totali", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(paroletotali), tbrow, 2)
        TBdialog.addlinetotable("Parole piene", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolepiene), tbrow, 2)
        TBdialog.addlinetotable("Parole vuote", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolevuote), tbrow, 2)
        TBdialog.addlinetotable("Altri tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolenone), tbrow, 2)
        #calcolo le percentuali
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto calcolando le percentuali su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            ratio = (float(TBdialog.w.tableWidget.item(row,2).text())/float(paroletotali)*100)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(ratios, row, 3)
        #mostro i risultati
        self.Progrdialog.accept()
        TBdialog.show()


    def delselected(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpuswidget.selectedItems())
        toselect = []
        for i in range(len(self.corpuswidget.selectedItems())):
            row = self.corpuswidget.selectedItems()[i].row()
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(i))
            self.Progrdialog.w.progressBar.setValue(int((i/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            toselect.append(row)
        totallines = len(toselect)
        startline = self.daToken
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.corpuswidget.removeRow(toselect[row-1])
            del self.corpus[startline+toselect[row-1]]

        self.Progrdialog.accept()
        self.sizeChanged.emit(len(self.corpus))

    def enumeratecolumns(self, combo):
        for col in range(self.corpuswidget.columnCount()):
            thisname = self.corpuswidget.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def finditemincolumn(self, mytext, col=0, matchexactly = True, escape = True, myflags=0):
        myregex = mytext
        if escape:
            myregex = re.escape(myregex)
        if matchexactly:
            myregex = "^" + myregex + "$"
        for row in range(len(self.corpus)):
            try:
                if bool(re.match(myregex, self.corpus[row][col], flags=myflags)):
                    return row
            except:
                continue
        return -1

    def findItemsInColumn(self, table, value, col):
        mylist = [row[col] for row in table if row[col]==value]
        return mylist

    def applicaFiltro(self, row, col, filtro, table = None):
        res = False
        if col != self.filtrimultiplienabled:
            try:
                if table == None:
                    ctext = self.corpus[row][col]
                else:
                    ctext = table[row][col]
            except:
                print("Unable to find row " +str(row) + " col "+ str(col))
                return False
            ftext = filtro
            if bool(re.match(ftext, ctext)):
                res = True
            else:
                res = False
        else:
            for option in filtro.split("||"):
                for andcond in option.split("&&"):
                    res = False
                    cellname = andcond.split("=", 1)[0]
                    try:
                        ftext = andcond.split("=", 1)[1]
                    except:
                        continue
                    colname = cellname.split("[")[0]
                    col = self.corpuscols[colname][0]
                    if "[" in cellname.replace("]",""):
                        rowlist = cellname.replace("]","").split("[")[1].split(",")
                    else:
                        rowlist = [0]
                    for rowp in rowlist:
                        tmprow = row + int(rowp)
                        try:
                            if table == None:
                                ctext = self.corpus[tmprow][col]
                            else:
                                ctext = table[tmprow][col]
                        except:
                            ctext = ""
                        try:
                            if bool(re.match(ftext, ctext)):
                                res = True
                                break
                        except:
                            print("Error in regex")
                            pass
                    if res == False:
                        break
                if res == True:
                    break
        return res

    def filtriMultipli(self):
        #fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(self.filter)
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()

    def actionNumero_dipendenze_per_frase(self):
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        col = self.corpuscols["dep"][0]
        Fildialog.filterColElements(self.corpuscols["IDphrase"][0])
        Fildialog.updateFilter()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        allfilters = Fildialog.w.filter.text().split("||")
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Dependency", 0)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        for myfilter in allfilters:
            TBdialog.addcolumn(myfilter, 1)
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.corpus[row][col]
                try:
                    if col == self.corpuscols["pos"][0]:
                        thistext = self.legendaPos[thistext][0]
                except:
                    thistext = self.corpus[row][col]
            except:
                thistext = ""
            for ifilter in range(len(allfilters)):
                if self.applicaFiltro(row, fcol, allfilters[ifilter]):
                    tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        try:
                            tbval = int(TBdialog.w.tableWidget.item(tbrow,ifilter+1).text())+1
                        except:
                            tbval = 1
                        TBdialog.setcelltotable(str(tbval), tbrow, ifilter+1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable("1", tbrow, ifilter+1)
        self.Progrdialog.accept()
        TBdialog.show()

    def addTagFromFilter(self):
        QMessageBox.information(self.corpuswidget, "Istruzioni", "Crea il filtro per selezionare gli elementi a cui vuoi aggiungere un tag.")
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        nuovotag = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag che vuoi aggiungere alle parole che rispettano il filtro:", QLineEdit.Normal, "")[0]
        repCdialog = regex_replace.Form(self.corpuswidget)
        repCdialog.setModal(False)
        repCdialog.w.orig.setText("(.*)")
        repCdialog.w.dest.setText("\g<1>, "+nuovotag)
        repCdialog.w.changeCase.show()
        repCdialog.w.colcheck.hide()
        repCdialog.w.colcombo.hide()
        repCdialog.w.lbl_in.hide()
        repCdialog.exec()
        if repCdialog.result():
            if repCdialog.w.ignorecase.isChecked():
                myflags=re.IGNORECASE|re.DOTALL
            else:
                myflags=re.DOTALL
        else:
            return
        col = self.corpuscols['TAGcorpus'][0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto modificando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if self.applicaFiltro(row, fcol, self.filter):
                origstr = self.corpus[row][col]
                newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=myflags)
                if repCdialog.w.dolower.isChecked():
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                    for f in indexes:
                        newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                if repCdialog.w.doupper.isChecked():
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                    for f in indexes:
                        newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                self.corpus[row][col] = newstr
        self.Progrdialog.accept()
        self.updateCorpus()

    def concordanze(self):
        parola = QInputDialog.getText(self.corpuswidget, "Scegli la parola", "Indica la parola che vuoi cercare:", QLineEdit.Normal, "")[0]
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "In quale colonna devo cercare il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        myrange = int(QInputDialog.getInt(self.corpuswidget, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        #myfilter = str(list(self.corpuscols)[col]) + "[" + rangestr + "]" +"="+parola
        myfilter = str(list(self.corpuscols)[col]) +"="+parola
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(myfilter) #"lemma=essere&&pos[1,-1]=SP||lemma[-1]=essere&&pos=S"
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        #self.dofiltra()
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = self.ignorepos
        else:
            myignore = []
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            if not self.applicaFiltro(row, self.filtrimultiplienabled, self.filter):
                continue
            thistext = self.rebuildText(self.corpus, self.Progrdialog, col, myignore, row-myrange, row+myrange+1)
            thistext = self.remUselessSpaces(thistext)
            tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
            if tbrow>=0:
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        TBdialog.show()

    def coOccorrenze(self):
        parola = QInputDialog.getText(self.corpuswidget, "Scegli la parola", "Indica la parola che vuoi cercare:", QLineEdit.Normal, "")[0]
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "In quale colonna devo cercare il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        myrange = int(QInputDialog.getInt(self.corpuswidget, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        myfilter = str(list(self.corpuscols)[col]) +"="+parola
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(myfilter) #"lemma=essere&&pos[1,-1]=SP||lemma[-1]=essere&&pos=S"
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        #self.dofiltra()
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = self.ignorepos
        else:
            myignore = []
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        concordanze = []
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            ftext = myfilter #self.filter
            if not self.applicaFiltro(row, fcol, ftext):
                continue
            thistext = self.rebuildText(self.corpus, self.Progrdialog, col, myignore, row-myrange, row+myrange+1)
            #thistext = self.remUselessSpaces(thistext)
            regex = re.escape('.?!')
            if bool(re.match(".*["+regex+"].*", thistext)):
                punctindex = [m.start(1) for m in re.finditer("(["+regex+"])", thistext, flags=re.DOTALL)]
                if punctindex[0] < thistext.index(parola):
                    thistext = thistext[punctindex[0]+1:]
                else:
                    thistext = thistext[0:punctindex[0]]
            if thistext != "":
                concordanze.append(thistext)
        totallines = len(concordanze)
        for row in range(totallines):
            self.Progrdialog.w.testo.setText("Sto controllando l'occorrenza numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisrow = concordanze[row].split(" ")
            for word in thisrow:
                thistext = ""
                if thisrow.index(word) < thisrow.index(parola):
                    thistext = str(word) + "..." + str(parola)
                if thisrow.index(word) > thisrow.index(parola):
                    thistext = str(parola) + "..." + str(word)
                if thistext != "":
                    tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                        TBdialog.setcelltotable(str(tbval), tbrow, 1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        TBdialog.show()

    def removevisiblerows(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        startline = self.daToken
        toselect = []
        for row in range(self.corpuswidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.corpuswidget.isRowHidden(row):
                toselect.append(row)
        totallines = len(toselect)
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.corpuswidget.removeRow(toselect[row-1])
            del self.corpus[startline+toselect[row-1]]
        self.Progrdialog.accept()
        self.sizeChanged.emit(len(self.corpus))

    def cancelfiltro(self):
        for row in range(self.corpuswidget.rowCount()):
            self.corpuswidget.setRowHidden(row, False)



    def corpusCellChanged(self, row, col):
        if self.ImportingFile:
            return
        try:
            startline = self.daToken
            self.corpus[row+startline][col] = self.corpuswidget.item(row,col).text()
        except:
            print("Error editing cell")
            self.updateCorpus()

    def updateCorpus(self):
        Progrdialog = progress.Form() #self.Progrdialog = progress.Form()
        Progrdialog.show() #self.Progrdialog.show()
        # Clear table before adding new lines
        self.corpuswidget.setRowCount(0)
        starting = self.daToken
        maximum = self.aToken
        #print(starting)
        #print(maximum)
        if self.allToken:
            starting = 0
            maximum = len(self.corpus)
        if maximum > len(self.corpus):
            maximum = len(self.corpus)
        if starting < 0:
            starting = 0
        totallines = maximum-starting
        print("Showing lines: "+str(totallines))
        if totallines < 0:
            print("daToken need to be smaller than aToken")
            return
        for rowN in range(starting,maximum):
            Progrdialog.w.testo.setText("Sto importando la riga numero "+str(rowN))
            Progrdialog.w.progressBar.setValue(int((rowN/totallines)*100))
            if rowN<100 or rowN%100==0:
                QApplication.processEvents()
            colN = 0
            line = self.corpus[rowN]
            for colN in range(len(line)):
                if Progrdialog.w.annulla.isChecked():
                    rowN = 0
                    Progrdialog.reject()
                    self.ImportingFile = False
                    return
                if colN == 0:
                    if line[colN] == "":
                        break
                    TBrow = self.addlinetocorpus(str(line[colN]), 0) #self.corpuscols["TAGcorpus"][0]
                self.setcelltocorpus(str(line[colN]), TBrow, colN)

    def visualizzafrasi(self):
        alberofrasidialog = alberofrasi.Form(self)
        alberofrasidialog.exec()

    def runServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self.corpuswidget, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            self.TintThread = tint.TintRunner(self.TintSetdialog.w)
            self.TintThread.loadvariables(self.Java, self.TintDir, self.TintPort)
            self.TintThread.dataReceived.connect(lambda data: self.runServer(bool(data)))
            self.alreadyChecked = True
            self.TintThread.start()
        else:
            if platform.system() == "Windows":
                QMessageBox.information(self.corpuswidget, "Come usare il server su Windows", "Sembra che tu stia usando Windows. Su questo sistema, per utilizzare il server Tint l'interfaccia di Bran verrà chiusa automaticamente: il terminale dovrà rimanere aperto. Dovrai aprire di nuovo Bran, così verrà caricata una nuova interfaccia grafica.")
                print("\nNON CHIUDERE QUESTA FINESTRA:  Tint è eseguito dentro questa finestra. Avvia di nuovo Bran.")
                print("\n\nNON CHIUDERE QUESTA FINESTRA")
                sys.exit(0)

    def checkServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self.corpuswidget, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            QApplication.processEvents()
            self.TestThread = tint.TintCorpus(self.corpuswidget, [], self.corpuscols, self.TintAddr)
            self.TestThread.dataReceived.connect(lambda data: self.checkServer(bool(data)))
            self.alreadyChecked = True
            self.TestThread.start()
            #while self.TestThread.isRunning():
            #    time.sleep(10)
            self.TintSetdialog.w.loglist.addItem("Sto cercando il server")
        else:
            self.TintSetdialog.accept()

    def addlinetocorpus(self, text, column):
        #self.corpuswidget.cellChanged.disconnect(self.corpusCellChanged)
        row = self.corpuswidget.rowCount()
        self.corpuswidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.corpuswidget.setItem(row, column, titem)
        self.corpuswidget.setCurrentCell(row, column)
        #self.corpuswidget.cellChanged.connect(self.corpusCellChanged)
        return row

    def setcelltocorpus(self, text, row, column):
        #self.corpuswidget.cellChanged.disconnect(self.corpusCellChanged)
        titem = QTableWidgetItem()
        titem.setText(text)
        if column == self.corpuscols["pos"][0]:
            try:
                newtext = self.legendaPos[text][0]
                titem.setToolTip(newtext)
            except:
                newtext = text
        self.corpuswidget.setItem(row, column, titem)
        #self.corpuswidget.cellChanged.connect(self.corpusCellChanged)

    def sanitizeTable(self, table):
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                if not table.item(row,col):
                    self.setcelltocorpus("", row, col)

    def sanitizeCorpus(self):
        for row in range(len(self.corpus)):
            for col in range(len(self.corpuscols)):
                try:
                    self.corpus[row][col] = str(self.corpus[row][col])
                except:
                    self.corpus[row][col] = ""

    def texteditor(self):
        te = texteditor.TextEditor(self.corpuswidget, self.mycfg)
        te.show()

    def confronto(self):
        cf = confronto.Confronto(self.corpuswidget, self.mycfg, self.sessionDir)
        cf.legendaPos = self.legendaPos
        cf.ignoretext = self.ignoretext
        cf.dimList = self.dimList
        cf.show()

    #def aboutbran(self):
    #    aw = about.Form(self.corpuswidget)
    #    aw.exec()

    def getCorpusDim(self, thistotal):
        dimCorpus = self.dimList[0]
        for i in range(len(self.dimList)-1):
            if self.dimList[i] <= thistotal and self.dimList[i+1] >= thistotal:
                lower = thistotal - self.dimList[i]
                upper = self.dimList[i+1] - thistotal
                if lower < upper:
                    dimCorpus = self.dimList[i]
                else:
                    dimCorpus = self.dimList[i+1]
        return dimCorpus

    def misure_lessicometriche(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Se vuoi estrarre il dizionario devi cercare nella colonna dei lemmi. Ma puoi anche scegliere di ottenere le statistiche su altre colonne, come la Forma grafica.",thisname,current=self.corpuscols['token'][0],editable=False)
        col = thisname.index(column[0])
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Token", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        #calcolo le occorrenze del pos
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totaltypes = 0
        mytypes = {}
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisposc = "False"
            try:
                thistext = self.corpus[row][col]
            except:
                thistext = ""
            if ret == QMessageBox.Yes:
                thistext = re.sub(self.ignoretext, "", thistext)
            if thistext != "":
                tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                if tbrow>=0:
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 1)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable("1", tbrow, 1)
                    totaltypes = totaltypes + 1
        hapax = 0
        classifrequenza = []
        occClassifrequenza = []
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto cercando gli hapax su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if int(TBdialog.w.tableWidget.item(row,1).text()) == 1:
                hapax = hapax + 1
            if TBdialog.w.tableWidget.item(row,1).text() in classifrequenza:
                ind = classifrequenza.index(TBdialog.w.tableWidget.item(row,1).text())
                occClassifrequenza[ind] = occClassifrequenza[ind] + 1
            else:
                classifrequenza.append(TBdialog.w.tableWidget.item(row,1).text())
                occClassifrequenza.append(1)
        totallines = TBdialog.w.tableWidget.rowCount()
        paroletotali = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto calcolando le somme su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,1).text())
        dimCorpus = self.getCorpusDim(paroletotali)
        TBdialog.addcolumn("Frequenza in " + str(dimCorpus) + " parole", 2)
        TBdialog.addcolumn("Ordine di grandezza (log10)", 3)
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto controllando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            thistext = TBdialog.w.tableWidget.item(row,0).text()
            ratio = (float(TBdialog.w.tableWidget.item(row,1).text())/float(paroletotali)*dimCorpus)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(str(ratios), row, 2)
            ratio = math.log10(float(TBdialog.w.tableWidget.item(row,1).text())/float(paroletotali))
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(str(ratios), row, 3)
        TBdialog.addlinetotable("Tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(paroletotali), tbrow, 1)
        TBdialog.addlinetotable("Types", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(totaltypes), tbrow, 1)
        TBdialog.addlinetotable("(Types/Tokens)*100", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(totaltypes)/float(paroletotali))*100.0
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Tokens/Types", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(paroletotali)/float(totaltypes))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Hapax", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(hapax), tbrow, 1)
        TBdialog.addlinetotable("(Hapax/Tokens)*100", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(hapax)/float(paroletotali))*100.0
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Types/sqrt(Tokens)", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = float(totaltypes)/float(math.sqrt(paroletotali))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("log(Types)/log(Tokens)", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(math.log10(totaltypes))/float(math.log10(paroletotali)))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        YuleSum = 0
        for cfi in range(len(classifrequenza)):
            YuleSum = YuleSum + ( math.pow(int(classifrequenza[cfi]),2) * occClassifrequenza[cfi] )
        TBdialog.addlinetotable("Caratteristica di Yule (K)", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = float(math.pow(10,4)) * ((float(YuleSum) - float(paroletotali))/ float(math.pow(paroletotali, 2)) )
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("W", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = math.pow(float(paroletotali), (1.0/math.pow(float(totaltypes), 0.172)))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("U", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio =  math.pow(float(math.log10(paroletotali)), 2.0)/(float(math.log10(paroletotali)) - float(math.log10(totaltypes)) )
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        #mostro i risultati
        self.Progrdialog.accept()
        TBdialog.show()

#
class UDCorpus(QThread):
    dataReceived = Signal(bool)
    updated = Signal(int)

    def __init__(self, widget, fnames, corpcol, udpipe, udpipemodel, lang):
        QThread.__init__(self)
        self.corpuswidget = widget
        self.fileNames = fnames
        self.corpuscols = corpcol
        self.udpipe = udpipe
        self.udpipemodel = udpipemodel
        self.language = lang
        self.outputcsv = ""
        self.csvIDcolumn = -1
        self.csvTextcolumn = -1
        self.loadvariables()
        self.setTerminationEnabled(True)
        self.iscli = False
        try:
            if self.corpuswidget == "cli":
                self.iscli = True
        except:
            self.iscli = False
        self.alwaysyes = False
        self.rowfilename = ""

    def loadvariables(self):
        self.useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

    def __del__(self):
        print("Shutting down thread")

    def run(self):
        self.loadtxt()
        return

    def loadtxt(self):
        fileID = 0
        self.Progrdialog = progress.Form()
        if not self.iscli:
            self.updated.connect(self.Progrdialog.setValue)
            self.Progrdialog.show()
        for fileName in self.fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    try:
                        if self.corpuswidget.rowCount() >0:
                            fileID = int(self.corpuswidget.item(self.corpuswidget.rowCount()-1,0).text().split("_")[0])
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
                        myencoding = "ISO-8859-15"
                        #https://pypi.org/project/chardet/
                        gotEncoding = False
                        while gotEncoding == False:
                            try:
                                myencoding = QInputDialog.getText(self.corpuswidget, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
                            except:
                                print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
                                myencoding = [input()]
                            try:
                                text_file = open(fileName, "r", encoding=myencoding[0])
                                lines = text_file.read()
                                text_file.close()
                                gotEncoding = True
                            except:
                                gotEncoding = False
                    self.rowfilename = fileName + ".tmp"
                    if self.iscli:
                        self.outputcsv = fileName + ".tsv"
                    print(fileName + " -> " + self.outputcsv)
                    if self.csvIDcolumn <0 or self.csvTextcolumn <0:
                        try:
                            corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:udpipe"
                            corpusID = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus:", QLineEdit.Normal, corpusID)[0]
                        except:
                            corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:udpipe"
                        self.text2corpusUD(lines, corpusID)
                    else:
                        try:
                            sep = QInputDialog.getText(self.corpuswidget, "Scegli il separatore", "Indica il carattere che separa le colonne (\\t è la tabulazione):", QLineEdit.Normal, "\\t")[0]
                            if sep == "\\t":
                                sep = "\t"
                            textID = QInputDialog.getInt(self.corpuswidget, "Scegli il testo", "Indica la colonna della tabella che contiene il testo di questo sottocorpus:")[0]
                            corpusIDtext = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus. Puoi usare [filename] per indicare il nome del file e [numeroColonna] per indicare la colonna da cui estrarre un tag.", QLineEdit.Normal, "[filename], [0]"+",tagger:udpipe")[0]
                            textID = int(textID)
                            for line in lines.split("\n"):
                                corpusID = corpusIDtext.replace("[filename]", os.path.basename(fileName))
                                indexes = [(m.start(0), m.end(0)) for m in re.finditer('\[[0-9]*\]', corpusID)]
                                for n in range(len(indexes)):
                                    start = indexes[n][0]
                                    end = indexes[n][1]
                                    try:
                                        strCol = corpusID[start:end]
                                        intCol = int(corpusID[start+1:end-1])
                                        corpusID = corpusID.replace(strCol, line.split(sep)[intCol])
                                    except:
                                        print("Impossibile trovare la colonna nel CSV")
                                print(corpusID)
                                self.text2corpusUD(line.split(sep)[textID], corpusID)
                        except:
                            try:
                                textID = int(self.csvTextcolumn)
                                colID = int(self.csvIDcolumn)
                                if textID != colID:
                                    for line in lines.split("\n"):
                                        corpusID = line.split("\t")[colID]+",lang:"+self.language+",tagger:udpipe"
                                        self.text2corpusUD(line.split("\t")[textID], corpusID)
                            except:
                                continue
        if self.fileNames == []:
            testline = "Il gatto è sopra al tetto."
            myres = self.getUDTable(testline)
            try:
                self.dataReceived.emit(True)
            except:
                self.dataReceived.emit(False)
        self.Progrdialog.accept()


    def addlinetocorpus(self, text, column):
        row = self.corpuswidget.rowCount()
        self.corpuswidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.corpuswidget.setItem(row, column, titem)
        self.corpuswidget.setCurrentCell(row, column)
        return row

    def setcelltocorpus(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.corpuswidget.setItem(row, column, titem)
        #self.corpuswidget.setCurrentCell(row, column)

    def text2corpusUD(self, text, TAGcorpus):
        itext = text.replace('.','. \n')
        itext = itext.replace('?','? \n')
        #merge phrases in paragraphs to optimize loading time for udpipe
        print("Lines before optimization: " + str(len(itext.split('\n'))))
        frasiInParagrafo = 50
        count = 0
        itext = itext.split('\n')
        ntext = []
        temp = ""
        for f in range(len(itext)):
            if count != frasiInParagrafo and f<(len(itext)-1):
                temp = temp + " " + itext[f]
                count = count + 1
            else:
                ntext.append(temp)
                count = 0
                temp = ""
        itext = ntext
        del ntext
        totallines = len(itext)
        print("Total lines: "+str(totallines))
        self.Progrdialog.setBasetext("Sto lavorando sul paragrafo numero ")
        self.Progrdialog.setTotal(totallines)
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
        #
        try:
            IDphrase = -1
            if self.outputcsv == "":
                for crow in range(self.corpuswidget.rowCount()):
                    if int(self.corpuswidget.item(crow, self.corpuscols["IDphrase"][0]).text()) > IDphrase:
                        IDphrase = int(self.corpuswidget.item(crow, self.corpuscols["IDphrase"][0]).text())
            else:
                with open(self.rowfilename, "r", encoding='utf-8') as ins:
                    for line in ins:
                        if int(line.split("\t")[self.corpuscols["IDphrase"][0]]) > IDphrase:
                            IDphrase = int(line.split("\t")[self.corpuscols["IDphrase"][0]])
        except:
            IDphrase = -1
        row = 0
        dct = {"ID" : 0, "FORM" : 1, "LEMMA" : 2, "UPOS" : 3, "XPOS" : 4, "FEATS" : 5 , "HEAD": 6, "DEPREL": 7, "DEPS": 8, "MISC": 9}
        for line in itext:
            row = row + 1
            if row > startatrow:
                #self.Progrdialog.w.testo.setText("Sto lavorando sulla frase numero "+str(row))
                #self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                self.updated.emit(row)
                if not self.iscli and row % 20 == 0:
                    QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                myres = []
                if line != "":
                    myres = self.getUDTable(line)
                for sentence in myres:
                    IDphrase = IDphrase +1
                    skipT = -1
                    for t in range(len(sentence)):
                        token = sentence[t]
                        fullline = ""
                        if "-" in str(token[dct["ID"]]):
                            fullline = str(TAGcorpus) + "\t"
                            fullline = fullline + str(sentence[t][dct["FORM"]]) + "\t"
                            lemma = ""
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                templemma = str(sentence[t+el+1][dct["LEMMA"]])
                                if len(templemma)>len(lemma):
                                    lemma = templemma
                            fullline = fullline + lemma + "\t"
                            pos = ""
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                if el > 0:
                                    pos = pos + "+"
                                pos = pos + str(sentence[t+el+1][dct["UPOS"]])
                            fullline = fullline + pos + "\t"
                            ner = "_"
                            fullline = fullline + str(ner) + "\t"
                            morf = ""
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                if el > 0:
                                    morf = morf + "/"
                                morf = morf + str(sentence[t+el+1][dct["FEATS"]])
                            fullline = fullline + str(morf) + "\t"
                            fullline = fullline + str(str(sentence[t][dct["ID"]]).split("-")[0]) + "\t"
                            fullline = fullline + str(IDphrase)
                            #for el in range(len(str(token[dct["ID"]]).split("-"))):
                            fullline = fullline + "\t" + str(sentence[t+1][dct["DEPREL"]]) + "\t"
                            governor = str(sentence[t+1][dct["HEAD"]])
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                tmpgov = str(sentence[t+el+1][dct["HEAD"]])
                                if not tmpgov in str(token[dct["ID"]]).split("-"):
                                    governor = tmpgov
                            fullline = fullline + governor
                            skipT = t + len(str(token[dct["ID"]]).split("-"))
                        elif t > skipT:
                            fullline = str(TAGcorpus) + "\t"
                            fullline = fullline + str(token[dct["FORM"]]) + "\t"
                            fullline = fullline + str(token[dct["LEMMA"]]) + "\t"
                            fullline = fullline + str(token[dct["UPOS"]]) + "\t"
                            ner = "O"
                            fullline = fullline + str(ner) + "\t"
                            morf = str(token[dct["FEATS"]])
                            fullline = fullline + str(morf) + "\t"
                            fullline = fullline + str(token[dct["ID"]]) + "\t"
                            fullline = fullline + str(IDphrase)
                            fullline = fullline + "\t" + str(token[dct["DEPREL"]]) + "\t"
                            fullline = fullline + str(token[dct["HEAD"]])
                        if fullline != "":
                            fdatefile = self.outputcsv
                            with open(fdatefile, "a", encoding='utf-8') as myfile:
                                myfile.write(fullline+"\n")
                if self.iscli:
                    with open(self.rowfilename, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
        if self.iscli:
            print("Done")

    def getUDTable(self, text):
        process = subprocess.Popen([self.udpipe, "--tokenize", "--tag", "--parse", self.udpipemodel], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        testobyte = text.encode(encoding='utf-8')
        outputbyte = process.communicate(testobyte)[0]
        process.stdin.close()
        stroutput = outputbyte.decode(encoding='utf-8')
        #print(stroutput)
        mytable = stroutput.split("\n")
        myres = []
        sentence = []
        sentid = 0
        for row in range(len(mytable)):
            if row == (len(mytable)-1) or bool("sent_id" in mytable[row] and row > 5):
                try:
                    newsentid = int(mytable[row].replace("# sent_id = ", ""))
                except:
                    newsentid = sentid +1
                myres.append(sentence)
                sentence = []
                sentid = newsentid
            if len(mytable[row].split("\t")) > 8:
                sentence.append(mytable[row].split("\t"))
        #print(myres)
        return myres
