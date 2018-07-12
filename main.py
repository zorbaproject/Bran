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
        sys.exit(1)

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
        self.w.actionDa_file_txt.triggered.connect(self.loadtxt)
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
        self.enumeratecolumns(self.w.ccolumn)

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
            thistext = self.w.corpus.item(row,col).text()
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
        self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
        self.TCThread = tint.TintCorpus(self.w, fileNames, self.corpuscols)
        self.TCThread.finished.connect(self.txtloadingstopped)
        self.TCThread.start()

    def txtloadingstopped(self):
        #self.w.statusbar.showMessage("Importazione TXT Terminata", 10)
        self.w.statusbar.clearMessage()

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



