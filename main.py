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
        from pip._internal import main
        main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
        from PySide2.QtWidgets import QApplication

#try:
#    from ufal.udpipe import Model, Pipeline, ProcessingError
#except:
#    try:
#        from tkinter import messagebox
#        thispkg = "UDPipe"
#        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
#        pip.main(["install", "ufal.udpipe"])
#        from ufal.udpipe import Model, Pipeline, ProcessingError
#    except:
#        sys.exit(1)


from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?
from PySide2.QtCore import QThread



from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor
from forms import tint





class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        file = QFile("forms/mainwindow.ui")
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
        self.w.actionEditor_di_testo.triggered.connect(self.texteditor)
        self.w.actionStatistiche_con_VdB.triggered.connect(self.statisticheconvdb)
        # TODO: importa da file zip: naviga un archivio come fosse una cartella
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
        self.loadConfig()

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

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", ".", "Text files (*.csv *.txt)")[0]
        if fileName != "":
            csv = ""
            for col in range(self.w.corpus.columnCount()):
                if col > 0:
                    csv = csv + self.separator
                csv = csv + self.w.corpus.horizontalHeaderItem(col).text()
            for row in range(self.w.corpus.rowCount()):
                csv = csv + "\n"
                for col in range(self.w.corpus.columnCount()):
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.corpus.item(row,col).text()
            text_file = open(fileName, "w")
            text_file.write(csv)
            text_file.close()

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
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", ".", "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
        self.TCThread = tint.TintCorpus(self.w, fileNames, self.corpuscols, self.TintAddr)
        QMessageBox.information(self, "Attenzione", "Per evitare di finire la memoria RAM a disposizione, è una buona idea salvare il corpus in un file CSV e importarlo successivamente. Ti verrà proposto di scegliere il nome del file su cui salvare il corpus, se vuoi comunque provare a importarlo direttamente in Bran non selezionare alcun file.")
        self.TCThread.outputcsv = QFileDialog.getSaveFileName(self, "Salva come CSV", ".", "CSV files (*.txt *.csv)")[0]
        if self.TCThread.outputcsv != "":
            csvheader = ""
            text_file = open(self.TCThread.outputcsv, "w")
            text_file.write(csvheader)
            text_file.close()
        self.TCThread.finished.connect(self.txtloadingstopped)
        self.TCThread.start()

    def loadjson(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file JSON", ".", "Json files (*.txt *.json)")[0]
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
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", ".", "Json files (*.txt *.csv)")[0]
        fileID = 0
        rowN = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    text_file = open(fileName, "r")
                    lines = text_file.read()
                    text_file.close()
                    for line in lines.split('\n'):
                        self.w.statusbar.showMessage("ATTENDI: Sto importando la riga numero "+str(rowN))
                        QApplication.processEvents()
                        #print(rowN)
                        colN = 0
                        for col in line.split('\t'):
                            if colN == 0:
                                if col == "":
                                    break
                                rowN = self.addlinetocorpus(col, self.corpuscols["IDcorpus"])
                            self.setcelltocorpus(str(col), rowN, colN)
                            colN = colN + 1

    def txtloadingstopped(self):
        self.w.statusbar.clearMessage()

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
            self.w.statusbar.showMessage("ATTENDI: sto controllando se il server sia attivo")
            QApplication.processEvents()
            self.TestThread = tint.TintCorpus(self.w, [], self.corpuscols, self.TintAddr)
            self.TestThread.finished.connect(self.txtloadingstopped)
            self.TestThread.dataReceived.connect(lambda data: self.checkServer(bool(data)))
            self.alreadyChecked = True
            self.TestThread.start()
            while self.TestThread.isRunning():
                time.sleep(10)
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



