#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import sys
import os
import csv
import re
import math

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import QDir
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


from forms import progress
from forms import tableeditor

class Confronto(QDialog):

    def __init__(self, sessionDir, parent=None):
        super(Confronto, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/confronto.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        #self.w.accepted.connect(self.isaccepted)
        #self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("Confronta dati estratti dai corpora")
        self.w.do_occ.clicked.connect(self.do_occ)
        #self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.sessionDir = sessionDir
        self.w.addfile.clicked.connect(self.addfile)
        self.w.rmfile.clicked.connect(self.rmfile)

    def addfile(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.csv *.txt)")[0]
        for fileName in fileNames:
            self.w.corpora.addItem(fileName)

    def rmfile(self):
        for i in self.w.corpora.selectedItems():
            self.w.corpora.takeItem(self.w.corpora.row(i))

    def readcsv(self, fileName, separator = "\t"):
        text_file = open(fileName, "r", encoding='utf-8')
        lines = text_file.read()
        text_file.close()
        mylist = lines.split("\n")
        for i in range(len(mylist)):
            mylist[i] = mylist[i].split(separator)
        return mylist

    def getRiferimento(self, action):
        fileName = ""
        if self.w.vdb2016.isChecked:
            fileName = os.path.abspath(os.path.dirname(sys.argv[0])) + "/dizionario/vdb2016.txt"
        if action == "do_occ" and not bool(self.w.vdb2016.isChecked or self.w.vdb1980.isChecked):
            fileName = fileName + "-lemmi.txt"
        return fileName

    def do_occ(self):
        thisname = []
        riferimentoName = self.getRiferimento("do_occ")
        riferimento = self.readcsv(riferimentoName)
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Lemma", 0)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        if 1==1:
            if 1==1: #try:
                thistext = ""
                thisvalue = ""
                indexes = 1 + self.w.corpora.count()
                for i in range(indexes):
                    if i == 0:
                        corpus = riferimento
                        colname = riferimentoName
                    else:
                        corpus = self.readcsv(self.w.corpora.item(i-1).text())
                        colname = os.path.basename(self.w.corpora.item(i-1).text())
                    TBdialog.addcolumn(colname, i+1)
                    totallines = len(corpus)
                    for row in range(len(corpus)):
                        self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
                        self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                        QApplication.processEvents()
                        if self.Progrdialog.w.annulla.isChecked():
                            return
                        thistext = corpus[row][0]
                        if self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked():
                            try:
                                thisvalue = corpus[row][1]
                            except:
                                thisvalue = "1"
                        if self.w.occ_diff.isChecked():
                            thisvalue = "1"
                        tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                        if len(tbitem)>0:
                            tbrow = tbitem[0].row()
                            tbval = thisvalue
                            if self.w.occ_ds.isChecked and i>1:
                                rifval = int(TBdialog.w.tableWidget.item(tbrow,1).text())
                                tbval = rifval-int(thisvalue)
                            if self.w.occ_rms.isChecked and i>1:
                                rifval = int(TBdialog.w.tableWidget.item(tbrow,1).text())
                                tbval = math.sqrt(((rifval*rifval)+(int(thisvalue)*int(thisvalue)))/2)
                            TBdialog.setcelltotable(str(tbval), tbrow, i+1)
                        else:
                            TBdialog.addlinetotable(thistext, 0)
                            tbrow = TBdialog.w.tableWidget.rowCount()-1
                            TBdialog.setcelltotable(thisvalue, tbrow, i+1)
                            for itemp in range(1,i+1):
                                TBdialog.setcelltotable("0", tbrow, itemp)
            #except:
            #    thistext = ""
        self.Progrdialog.accept()
        TBdialog.exec()
