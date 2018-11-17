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
        self.w.altrofileselect.clicked.connect(self.altrofileselect)
        self.w.with_dict.currentIndexChanged.connect(self.dictselect)
        self.w.with_corpora.currentIndexChanged.connect(self.corporaselect)
        self.fillcombos()
        self.legendaPos = []

    def addfile(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.csv *.txt)")[0]
        for fileName in fileNames:
            self.w.corpora.addItem(fileName)

    def rmfile(self):
        for i in self.w.corpora.selectedItems():
            self.w.corpora.takeItem(self.w.corpora.row(i))

    def altrofileselect(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.csv *.txt)")[0]
        for fileName in fileNames:
            self.w.altrofilename.setText(fileName)
            self.w.altrofile.setChecked(True)

    def dictselect(self):
        self.w.sel_dict.setChecked(True)

    def corporaselect(self):
        self.w.sel_corpora.setChecked(True)

    def readcsv(self, fileName, separator = "\t"):
        text_file = open(fileName, "r", encoding='utf-8')
        lines = text_file.read()
        text_file.close()
        mylist = lines.split("\n")
        for i in range(len(mylist)):
            mylist[i] = mylist[i].split(separator)
        return mylist

    def fillcombos(self):
        branroot = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.dizionari = {
        "VdB 2016": branroot  + "/dizionario/vdb2016.txt",
        "VdB 1980": branroot  + "/dizionario/vdb1980.txt",
        "Dizionario De Mauro 2000": branroot + "/dizionario/De_Mauro-Dizionario_della_lingua_italiana/dizionario-de-mauro-pulito.txt",
        "Wikizionario": branroot + "/dizionario/wikitionary/wikitionary-it-pulito.txt"
        }
        self.corpora = {
        "Il barone rampante": branroot  + "/corpora/barone-rampante/barone-rampante",
        "Il fu Mattia Pascal": branroot  + "/corpora/",
        "Twitter Wilwoosh": branroot  + "/corpora/",
        "Lercio.it": branroot  + "/corpora/",
        "Wikipedia": branroot  + "/corpora/"}
        for key in self.dizionari:
            self.w.with_dict.addItem(key)
        for key in self.corpora:
            self.w.with_corpora.addItem(key)
        self.w.sel_dict.setChecked(True)
        self.datatype = ['Occorrenze Lemma','Occorrenze PoS', 'Statistiche VdB', 'Contaverbi', 'Densità lessicale', 'Segmenti ripetuti']
        for key in self.datatype:
            self.w.datatype.addItem(key)
        self.w.datatype.setCurrentIndex(0)

    def getRiferimento(self, action):
        fileName = ""
        if self.w.sel_dict.isChecked():
            fileName = self.dizionari[self.w.with_dict.currentText()]
        if self.w.sel_corpora.isChecked():
            fileName = self.corpora[self.w.with_corpora.currentText()]
            if action == "Occorrenze Lemma":
                fileName = fileName + "-occorrenze-lemma.csv"
            if action == "Occorrenze PoS":
                fileName = fileName + "-occorrenze-pos.csv"
            if action == "Statistiche VdB":
                fileName = fileName + "-vdb.csv"
            if action == "Contaverbi":
                fileName = fileName + "-contaverbi.csv"
            if action == "Densità lessicale":
                fileName = fileName + "-densita.csv"
            if action == "Segmenti ripetuti":
                fileName = fileName + "-ngrams.csv"
        if self.w.altrofile.isChecked():
            fileName = self.w.altrofilename.text()
        return fileName

    def do_occ(self):
        context = self.w.datatype.currentText()
        self.do_confronta(context)

    def do_confronta(self, context):
        thisname = []
        riferimentoName = self.getRiferimento(context)
        riferimento = self.readcsv(riferimentoName)
        corpKeyCol = 0
        corpValueCol = 1
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(context, 0)
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        if 1==1: #try:
            thistext = ""
            thisvalue = ""
            indexes = 1 + self.w.corpora.count()
            outputcol = 1;
            for i in range(indexes):
                if i == 0:
                    corpus = riferimento
                    colname = os.path.basename(riferimentoName)
                else:
                    corpus = self.readcsv(self.w.corpora.item(i-1).text())
                    colname = os.path.basename(self.w.corpora.item(i-1).text())
                TBdialog.addcolumn(colname, i+1)
                if self.w.occ_ds.isChecked():
                    TBdialog.addcolumn(colname+" DS", outputcol+1)
                if self.w.occ_rms.isChecked():
                    TBdialog.addcolumn(colname+" RMS", outputcol+1)
                totallines = len(corpus)
                colincrease = 0
                startrow = 0
                if self.w.ignorefirstrow.isChecked():
                    startrow = 1
                for row in range(startrow, len(corpus)):
                    self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    thistext = corpus[row][corpKeyCol]
                    if context == "Occorrenze PoS":
                        try:
                            thistext = self.legendaPos[corpus[row][corpKeyCol]][0]
                        except:
                            thistext = corpus[row][corpKeyCol]
                    if self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked():
                        try:
                            thisvalue = corpus[row][corpValueCol]
                        except:
                            thisvalue = "1"
                    if self.w.occ_diff.isChecked():
                        thisvalue = "1"
                    tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                    if len(tbitem)>0:
                        tbrow = tbitem[0].row()
                        tbval = thisvalue
                        if self.w.occ_ds.isChecked() and i>0:
                            N = 2
                            try:
                                rifval = int(TBdialog.w.tableWidget.item(tbrow,1).text())
                            except:
                                rifval = 0
                            mean = (rifval+float(thisvalue))/N
                            tbval = math.sqrt((math.pow(rifval-mean,2)+ math.pow(float(thisvalue)-mean,2))/N)
                        if self.w.occ_rms.isChecked() and i>0:
                            N = 2
                            try:
                                rifval = int(TBdialog.w.tableWidget.item(tbrow,1).text())
                            except:
                                rifval = 0
                            tbval = math.sqrt((math.pow(rifval,2)+ math.pow(float(thisvalue),2))/N)
                        if self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked():
                            TBdialog.setcelltotable(str(thisvalue), tbrow, outputcol)
                            TBdialog.setcelltotable(str(tbval), tbrow, outputcol+1)
                        else:
                            TBdialog.setcelltotable(str(tbval), tbrow, i+1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        #TBdialog.setcelltotable(thisvalue, tbrow, i+1)
                        if bool(self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked()) and i>0:
                            TBdialog.setcelltotable(str(thisvalue), tbrow, outputcol)
                            TBdialog.setcelltotable("0", tbrow, outputcol+1)
                        else:
                            TBdialog.setcelltotable(str(thisvalue), tbrow, i+1)
                        for itemp in range(1,i+1):
                            TBdialog.setcelltotable("0", tbrow, itemp)
                if self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked():
                    outputcol = outputcol + 2
                else:
                    outputcol = outputcol + 1
        #except:
        #    thistext = ""
        totallines = TBdialog.w.tableWidget.rowCount()
        for col in range(TBdialog.w.tableWidget.columnCount()):
            for row in range(totallines):
                self.Progrdialog.w.testo.setText("Sto controllando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                try:
                    teststring = TBdialog.w.tableWidget.item(row,col).text()
                    if col > 0 and float(teststring) == 0:
                        TBdialog.setcelltotable("0", row, col)
                except:
                    TBdialog.setcelltotable("0", row, col)
        self.Progrdialog.accept()
        TBdialog.exec()
