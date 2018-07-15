#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#would be nice: https://github.com/yarolig/pyqtc


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
import json
import subprocess
from socket import timeout
import platform
import mmap

arch = platform.architecture()[0]
if arch != '64bit':
    from tkinter import messagebox
    messagebox.showinfo("Pericolo", "Sembra che tu stia utilizzando Python a 32bit. La maggioranza delle librerie moderne (come PySide2) utilizza codice a 64bit, per poter sfruttare appieno la RAM. Per favore, installa Python a 64bit.")
    sys.exit(1)

try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        from tkinter import messagebox
        thispkg = "le librerie grafiche"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        from PySide2.QtWidgets import QApplication
    except:
        try:
            from pip._internal import main
            main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
            from PySide2.QtWidgets import QApplication
        except:
            sys.exit(1)


from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtCore import QThread



from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor
from forms import tint
from forms import progress
from forms import sessione




class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/mainwindow.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader(self)
        self.w = loader.load(file)
        self.setCentralWidget(self.w)
        self.setWindowTitle("Bran")
        self.w.replace_in_corpus.clicked.connect(self.replaceCorpus)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.delselected.clicked.connect(self.delselected)
        self.w.actionScarica_corpus_da_sito_web.triggered.connect(self.web2corpus)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionEsporta_corpus_in_CSV_unico.triggered.connect(self.salvaCSV)
        self.w.actionDa_file_txt.triggered.connect(self.loadtxt)
        self.w.actionDa_file_JSON.triggered.connect(self.loadjson)
        self.w.actionDa_file_CSV.triggered.connect(self.loadCSV)
        self.w.actionConfigurazione_Tint.triggered.connect(self.loadConfig)
        self.w.actionSalva.triggered.connect(self.salvaProgetto)
        self.w.actionApri.triggered.connect(self.apriProgetto)
        self.w.actionEditor_di_testo.triggered.connect(self.texteditor)
        self.w.actionStatistiche_con_VdB.triggered.connect(self.statisticheconvdb)
        self.corpuscols = {
            'IDcorpus': 0,
            'Orig': 1,
            'Lemma': 2,
            'pos': 3,
            'ner': 4,
            'feat': 5,
            'IDword': 6
        }
        self.separator = "\t"
        self.enumeratecolumns(self.w.ccolumn)
        QApplication.processEvents()
        self.alreadyChecked = False
        self.ImportingFile = False
        self.sessionFile = ""
        self.sessionDir = "."
        self.loadSession()
        self.loadConfig()
        self.txtloadingstopped()

    def loadConfig(self):
        self.TintSetdialog = tint.Form(self)
        self.TintSetdialog.w.start.clicked.connect(self.runServer)
        self.TintSetdialog.w.check.clicked.connect(self.checkServer)
        self.TintSetdialog.exec()
        self.Java = self.TintSetdialog.w.java.text()
        self.TintDir = self.TintSetdialog.w.tintlib.text()
        self.TintPort = self.TintSetdialog.w.port.text()
        self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
        #self.Java -classpath $_CLASSPATH eu.fbk.dh.tint.runner.TintServer -p self.TintPort

    def loadSession(self):
        seSdialog = sessione.Form(self)
        seSdialog.exec()
        self.sessionFile = ""
        if seSdialog.result():
            self.sessionFile = seSdialog.filesessione
            if os.path.isfile(self.sessionFile):
                self.sessionDir = os.path.abspath(os.path.dirname(self.sessionFile))

    def apriProgetto(self):
        self.loadSession()
        self.txtloadingstopped()

    def replaceCorpus(self):
        repCdialog = regex_replace.Form(self)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.exec()
        if repCdialog.result():
            for row in range(self.w.corpus.rowCount()):
                for col in range(self.w.corpus.columnCount()):
                    if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                        origstr = self.w.corpus.item(row,col).text()
                        newstr = ""
                        if repCdialog.w.ignorecase.isChecked():
                            newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.IGNORECASE|re.DOTALL)
                        else:
                            newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.DOTALL)
                        self.setcelltocorpus(newstr, row, col)

    def contaoccorrenze(self):
        thisname = []
        for col in range(self.w.corpus.columnCount()):
            thisname.append(self.w.corpus.horizontalHeaderItem(col).text())
        column = QInputDialog.getItem(self, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(column[0], 0)
        TBdialog.addcolumn("Occorrenze", 1)
        for row in range(self.w.corpus.rowCount()):
            try:
                thistext = self.w.corpus.item(row,col).text()
            except:
                thistext = ""
            tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
            if len(tbitem)>0:
                tbrow = tbitem[0].row()
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        TBdialog.exec()

    def salvaProgetto(self):
        if self.sessionFile == "":
            fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
            if fileName != "":
                self.sessionFile = fileName
        if self.sessionFile != "":
            self.myprogress = progress.ProgressDialog(self.w)
            self.myprogress.start()
            self.CSVsaver(self.sessionFile, self.myprogress.Progrdialog, False)

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        self.CSVsaver(fileName, self.myprogress.Progrdialog, True)

    def CSVsaver(self, fileName, Progrdialog, addheader = False):
        if fileName != "":
            csv = ""
            if addheader:
                for col in range(self.w.corpus.columnCount()):
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.corpus.horizontalHeaderItem(col).text()
            totallines = self.w.corpus.rowCount()
            text_file = open(fileName, "w")
            text_file.write(csv)
            text_file.close()
            for row in range(self.w.corpus.rowCount()):
                csv = csv + "\n"
                Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                for col in range(self.w.corpus.columnCount()):
                    if Progrdialog.w.annulla.isChecked():
                        return
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.corpus.item(row,col).text()
                with open(fileName, "a") as myfile:
                    myfile.write(csv+"\n")
            Progrdialog.accept()

    def web2corpus(self):
        w2Cdialog = url2corpus.Form(self)
        w2Cdialog.exec()

    def delselected(self):
        for i in range(self.w.corpus.selectedItems()):
            row = self.w.corpus.selectedItems()[i].row()
        QMessageBox.warning(self, "Errore", "Funzione non ancora implementata.")

    def enumeratecolumns(self, combo):
        for col in range(self.w.corpus.columnCount()):
            thisname = self.w.corpus.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def dofiltra(self):
        for row in range(self.w.corpus.rowCount()):
            col = self.w.ccolumn.currentIndex()
            ctext = self.w.corpus.item(row,col).text()
            ftext = self.w.cfilter.text()
            if bool(re.match(ftext, ctext)):
                self.w.corpus.setRowHidden(row, False)
            else:
                self.w.corpus.setRowHidden(row, True)

    def cancelfiltro(self):
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.setRowHidden(row, False)

    def loadtxt(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
        self.TCThread = tint.TintCorpus(self.w, fileNames, self.corpuscols, self.TintAddr)
        self.TCThread.outputcsv = self.sessionFile
        if self.TCThread.outputcsv != "":
            csvheader = ""
            text_file = open(self.TCThread.outputcsv, "w")
            text_file.write(csvheader)
            text_file.close()
        self.TCThread.finished.connect(self.txtloadingstopped)
        self.TCThread.start()

    def loadjson(self):
        QMessageBox.information(self, "Attenzione", "Caricare un file JSON prodotto manualmente può essere pericoloso: se i singoli paragrafi sono troppo grandi, il programma può andare in crash. Utilizza questa funzione solo se sai esattamente cosa stai facendo.")
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file JSON", self.sessionDir, "Json files (*.txt *.json)")[0]
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    if self.w.corpus.rowCount() >0:
                        fileID = int(self.w.corpus.item(self.w.corpus.rowCount()-1,0).text().split("_")[0])
                    #QApplication.processEvents()
                    fileID = fileID+1
                    text_file = open(fileName, "r")
                    lines = text_file.read()
                    text_file.close()
                    IDcorpus = str(fileID)+"_"+os.path.basename(fileName)
                    try:
                        myarray = json.loads(lines)
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

    def loadCSV(self):
        if self.ImportingFile == False:
            fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "File CSV (*.txt *.csv)")[0]
            self.myprogress = progress.ProgressDialog(self.w)
            self.myprogress.start()
            self.ImportingFile = True
            self.CSVloader(fileNames, self.myprogress.Progrdialog)

    def CSVloader(self, fileNames, Progrdialog):
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    if not os.path.getsize(fileName) > 0:
                        #break
                        Progrdialog.reject()
                        self.ImportingFile = False
                        return
                    try:
                        totallines = self.linescount(fileName)
                    except:
                        Progrdialog.reject()
                        self.ImportingFile = False
                        return
                    text_file = open(fileName, "r")
                    lines = text_file.read()
                    text_file.close()
                    rowN = 0
                    for line in lines.split('\n'):
                        Progrdialog.w.testo.setText("Sto importando la riga numero "+str(rowN))
                        Progrdialog.w.progressBar.setValue(int((rowN/totallines)*100))
                        QApplication.processEvents()
                        colN = 0
                        for col in line.split(self.separator):
                            if Progrdialog.w.annulla.isChecked():
                                Progrdialog.reject()
                                self.ImportingFile = False
                                return
                            if colN == 0:
                                if col == "":
                                    break
                                rowN = self.addlinetocorpus(str(col), 0) #self.corpuscols["IDcorpus"]
                            self.setcelltocorpus(str(col), rowN, colN)
                            colN = colN + 1
        Progrdialog.accept()
        self.ImportingFile = False

    def linescount(self, filename):
        f = open(filename, "r+")
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    def txtloadingstopped(self):
        self.w.statusbar.clearMessage()
        if self.sessionFile != "" and self.ImportingFile == False:
            if os.path.isfile(self.sessionFile):
                if not os.path.getsize(self.sessionFile) > 1:
                    return
            try:
                self.myprogress = progress.ProgressDialog(self.w)
                self.myprogress.start()
                self.ImportingFile = True
                fileNames = ['']
                fileNames[0] = self.sessionFile
                self.CSVloader(fileNames, self.myprogress.Progrdialog)
            except:
                try:
                    self.myprogress.reject()
                    self.ImportingFile = False
                except:
                    return

    def runServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            self.w.statusbar.showMessage("ATTENDI: Devo avviare il server")
            self.TintThread = tint.TintRunner(self.TintSetdialog.w)
            self.TintThread.loadvariables(self.Java, self.TintDir, self.TintPort)
            self.TintThread.dataReceived.connect(lambda data: self.runServer(bool(data)))
            self.alreadyChecked = True
            self.TintThread.start()
        else:
            if platform.system() == "Windows":
                QMessageBox.information(self, "Come usare il server su Windows", "Sembra che tu stia usando Windows. Su questo sistema, per utilizzare il server Tint, devi chiudere l'interfaccia di Bran, lasciando aperto solo il terminale. Poi puoi aprire di nuovo Bran (caricherà un altro terminale e una nuova interfaccia grafica).")
            self.w.statusbar.showMessage("OK, il server è attivo")

    def checkServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            QApplication.processEvents()
            self.TestThread = tint.TintCorpus(self.w, [], self.corpuscols, self.TintAddr)
            self.TestThread.dataReceived.connect(lambda data: self.checkServer(bool(data)))
            self.alreadyChecked = True
            self.TestThread.start()
            #while self.TestThread.isRunning():
            #    time.sleep(10)
            self.TintSetdialog.w.loglist.addItem("Sto cercando il server")
        else:
            self.TintSetdialog.accept()

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

    def texteditor(self):
        te = texteditor.TextEditor()
        te.show()

    def statisticheconvdb(self):
        tbdialog = tableeditor.Form(self)
        tbdialog.setModal(False)
        tbdialog.exec()
        #usiamo la tabella per presentare i risultati, così è più facile esportarli

        #parole presenti in vdb1980 (occorrenze per ogni parola, percentuale su parole totali)
        #parole presenti in vdb2016 (occorrenze per ogni parola, percentuale su parole totali)
        #forestierismi presenti (occorrenze per ogni parola, percentuale su parole totali)
        if self.tbdialog.result():
            QMessageBox.warning(self, "Errore", "Funzione non ancora implementata.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())



