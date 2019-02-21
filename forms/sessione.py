#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem

import re
import sys
import os


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/sessione.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.ok.clicked.connect(self.isaccepted)
        self.w.annulla.clicked.connect(self.isrejected)
        self.w.cancelrecenti.clicked.connect(self.clearh)
        self.w.rejected.connect(self.isrejected)
        self.w.selectapri.clicked.connect(self.selectapri)
        self.w.selectcrea.clicked.connect(self.selectcrea)
        self.setWindowTitle("Scegli una sessione di lavoro")
        #self.w.recenti.horizontalScrollBar().setValue(self.w.recenti.horizontalScrollBar().maximum())
        self.filesessione = ""

    def isaccepted(self):
        self.filesessione = ""
        if self.w.aprisessione.text() != "":
            #self.filesessione = self.w.aprisessione.text()
            lastchar = self.w.aprisessione.text()[len(self.w.aprisessione.text())-1]
            if lastchar == "/" or lastchar == "\\":
                self.w.aprisessione.setText(self.w.aprisessione.text()[0:-1])
            folder = os.path.basename(self.w.aprisessione.text())
            fileName = self.w.aprisessione.text() + "/" + folder + "-bran.tsv"
            #print(fileName)
            self.filesessione = self.filesessione + fileName
            if os.path.isfile(self.filesessione):
                self.accept()
            else:
                self.filesessione = ""
                QMessageBox.critical(self, "Errore", "Questa cartella non contiene un valido file di sessione. Il file deve essere chiamato "+fileName+".")
        elif self.w.creafolder.text() != "":
            lastchar = self.w.creasessione.text()[len(self.w.creasessione.text())-1]
            if lastchar == "/" or lastchar == "\\":
                self.w.creasessione.setText(self.w.creasessione.text()[0:-1])
            sname = self.w.creasessione.text()
            sname = sname.replace("/", "")
            sname = sname.replace("\\", "")
            folder = self.w.creafolder.text() + "/" + sname
            tempfile = folder + "/" + sname +"-bran.tsv"
            try:
                os.makedirs(folder)
                text_file = open(tempfile, "w")
                text_file.write("")
                text_file.close()
                self.filesessione = tempfile
                self.accept()
            except:
                QMessageBox.critical(self, "Errore", "Impossibile creare la cartella "+folder+" e il file " + tempfile + ": forse non hai il permesso di scrivere in questa posizione, oppure la cartella esiste già.")
        elif len(self.w.recenti.selectedItems())>0:
            self.filesessione = self.w.recenti.selectedItems()[0].text()
            self.accept()
        else:
            self.isrejected()

    def isrejected(self):
        self.filesessione = ""
        ret = QMessageBox.question(self,'Sicuro sicuro?', "Stai per avviare Bran senza un file per la sessione di lavoro: questo significa che tutte le modifiche resteranno nella RAM. Se usi file di grandi dimensioni, la memoria potrebbe non bastare, e il programma andrebbe in crash. Sei sicuro di voler procedere senza una sessione di lavoro su file?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            self.reject()

    def clearh(self):
        for i in range(self.w.recenti.count()):
            item = self.w.recenti.item(i)
            self.w.recenti.setItemSelected(item, False)

    def selectapri(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella in cui si trova la tua sessione di lavoro")
        if not fileName == "":
            if os.path.isdir(fileName):
                self.w.aprisessione.setText(fileName)

    def selectcrea(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella creare la tua sessione di lavoro")
        if not fileName == "":
            if os.path.isdir(fileName):
                self.w.creafolder.setText(fileName)

    def loadhistory(self, history):
        for olddir in history:
            if os.path.isfile(olddir):
                self.w.recenti.addItem(olddir)
