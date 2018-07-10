#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#would be nice: https://github.com/yarolig/pyqtc

import pip
import sys
import os
import re

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

try:
    from ufal.udpipe import Model, Pipeline, ProcessingError
except:
    try:
        from tkinter import messagebox
        thispkg = "UDPipe"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "ufal.udpipe"])
        from ufal.udpipe import Model, Pipeline, ProcessingError
    except:
        sys.exit(1)


from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?

from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        file = QFile("forms/mainwindow.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader(self)
        self.w = loader.load(file)
        self.setCentralWidget(self.w)
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
        #conta occorrenze: https://pastebin.com/0tPNVACe
        thisname = []
        for col in range(self.w.corpus.columnCount()):
            thisname.append(self.w.corpus.horizontalHeaderItem(col).text())
        column = QInputDialog.getItem(self, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.item(row,col).text()

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
        fileID = 0
        if self.w.corpus.rowCount() >0:
            fileID = int(self.w.corpus.item(self.w.corpus.rowCount()-1,0).text().split("_")[0])
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    QApplication.processEvents()
                    fileID = fileID+1
                    text_file = open(fileName, "r")
                    lines = text_file.read() #.split('\n')
                    text_file.close()
                    self.w.statusbar.showMessage("ATTENDI: sto lavorando su "+fileName)
                    self.text2corpus(lines, str(fileID)+"_"+os.path.basename(fileName))
        self.w.statusbar.clearMessage()


    def text2corpus(self, text, IDcorpus):
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



