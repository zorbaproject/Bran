#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pip

import sys
try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        print("Sto cercando di installare le librerie necessarie...")
        # TODO: check if root
        pip.main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        from PySide2.QtWidgets import QApplication
    except:
        sys.exit(1)
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMainWindow

from forms import regex_replace
from forms import url2corpus

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
        # TODO: importa da file zip: naviga un archivio come fosse una cartella
        # TODO: usa Apache openNLP

    def replaceCorpus(self):
        dialog = regex_replace.Form()
        dialog.exec()
        if dialog.result():
            print("Has been accepted")
            print(dialog.w.orig.text())
            print(dialog.w.dest.text())
        #fileName = QFileDialog.getOpenFileName(self)
        #if not fileName.isEmpty():
        #    print(fileName)

    def web2corpus(self):
        dialog = url2corpus.Form()
        dialog.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())



