#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pip
import sys
import os

try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        print("Sto cercando di installare le librerie necessarie...")
        pip.main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        from PySide2.QtWidgets import QApplication
    except:
        sys.exit(1)

try:
    from ufal.udpipe import Model, Pipeline, ProcessingError
except:
    try:
        print("Sto cercando di installare le librerie necessarie...")
        pip.main(["install", "ufal.udpipe"])
        from ufal.udpipe import Model, Pipeline, ProcessingError
    except:
        sys.exit(1)

from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?

from forms import regex_replace
from forms import url2corpus
from forms import texteditor

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        file = QFile("forms/mainwindow.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader(self)
        self.w = loader.load(file)
        self.setCentralWidget(self.w)
        self.w.replace_in_corpus.clicked.connect(self.replaceCorpus)
        self.w.actionScarica_corpus_da_sito_web.triggered.connect(self.web2corpus)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionDa_file_txt.triggered.connect(self.loadtxt)
        self.w.actionEditor_di_testo.triggered.connect(self.texteditor)
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
        self.poscorpuscol = 3

    def replaceCorpus(self):
        repCdialog = regex_replace.Form(self)
        repCdialog.setModal(False)
        repCdialog.exec()
        if self.repCdialog.result():
            print("Has been accepted")
            print(repCdialog.w.orig.text())
            print(repCdialog.w.dest.text())

    def web2corpus(self):
        w2Cdialog = url2corpus.Form(self)
        w2Cdialog.exec()

    def loadtxt(self):
        #TODO: supporta selezione multipla, ogni nuovo file ottiene un ID diverso
        fileName = QFileDialog.getOpenFileName(self, "Apri file TXT", ".", "Text files (*.txt *.md)")[0]
        if not fileName == "":
            if os.path.isfile(fileName):
                text_file = open(fileName, "r")
                lines = text_file.read() #.split('\n')
                text_file.close()
                self.text2corpus(lines, "1")


    def text2corpus(self, text, IDcorpus):
        #would be nice: https://github.com/yarolig/pyqtc
        #lines = text.split(' ')
        #text
        lines = "Il gatto è sul tetto"
        itext = ''.join(lines)
        # Process data
        processed = self.pipeline.process(itext, self.UDerror)
        if self.UDerror.occurred():
            print("An error occurred when running run_udpipe: ")
            print(self.UDerror.message)
        print(processed)
        processed = processed.split('\n')
        for rowtext in processed:
            if len(rowtext)>0 and rowtext[0]!="#":
                rowN = self.addlinetocorpus(IDcorpus, self.IDcorpuscol)
                rowlst = rowtext.split("\t")
                if len(rowlst)>1:
                    origcorpus = rowlst[1]
                    self.setcelltocorpus(origcorpus, rowN, self.origcorpuscol)
                if len(rowlst)>2:
                    lemmcorpus = rowlst[2]
                    self.setcelltocorpus(lemmcorpus, rowN, self.lemmcorpuscol)
                if len(rowlst)>3:
                    poscorpus = rowlst[3]
                    self.setcelltocorpus(poscorpus, rowN, self.poscorpuscol)

    def addlinetocorpus(self, text, column):
        row = self.w.corpus.rowCount()
        if len(self.w.corpus.selectedItems()) > 0:
            row = self.w.corpus.selectedItems()[0].row() + 1
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
        self.w.corpus.setCurrentCell(row, column)

    def contaoccorrenze(self):
        #conta occorrenze: https://pastebin.com/0tPNVACe
        print("nothing")

    def texteditor(self):
        te = texteditor.TextEditor()
        te.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())



