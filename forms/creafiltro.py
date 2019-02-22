#!/usr/bin/env python
# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QGraphicsScene
from PySide2.QtGui import QPixmap
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QFileDialog

import re
import sys
import os

from forms import progress


class Form(QDialog):
    def __init__(self, corpus, cpcols, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/creafiltro.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.updateFilter.clicked.connect(self.updateFilter)
        self.w.filtroautomatico.clicked.connect(self.filtroautomatico)
        self.w.andbtn.clicked.connect(self.andbtn)
        self.w.orbtn.clicked.connect(self.orbtn)
        self.w.delbtn.clicked.connect(self.delbtn)
        self.w.help.clicked.connect(self.help)
        self.setWindowTitle("Crea filtro multiplo")
        self.mycorpus = corpus
        self.corpuscols = cpcols
        self.fillautocombo()
        self.sessionDir = "."
        #self.w.filter.setMaxLength(sys.maxsize-1)
        self.w.filter.setMaxLength(2147483647)

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()
        self.w.filter.setText("")

    def fillautocombo(self):
        self.w.autofiltercombo.addItem(" ")
        self.w.autofiltercombo.addItem("Ogni elemento di una colonna")
        self.w.autofiltercombo.addItem("Su un dizionario")

    def updateFilter(self):
        self.sanitizeTable()
        myfilter = ""
        iand = 0
        for tbrow in range(self.w.tableWidget.rowCount()):
            if iand >0:
                if self.w.tableWidget.item(tbrow,0).text() == "OR":
                    myfilter = myfilter + "||"
                    iand = 0
                    continue
                else:
                    myfilter = myfilter + "&&"
            myfilter = myfilter + self.w.tableWidget.item(tbrow,0).text()
            if self.w.tableWidget.item(tbrow,1).text() != "":
                myfilter = myfilter + "[" + self.w.tableWidget.item(tbrow,1).text()+ "]"
            myfilter = myfilter + "=" + self.w.tableWidget.item(tbrow,2).text()
            iand = iand+1
        self.w.filter.setText(myfilter)

    def updateTable(self):
        iopt = 0
        try:
            for option in self.w.filter.text().split("||"):
                if iopt >0:
                    self.addlinetotable("OR", 0)
                for andcond in option.split("&&"):
                    tmpcol = ""
                    tmprows = ""
                    tmpregex = ""
                    cellname = andcond.split("=")[0]
                    tmpregex = andcond.split("=")[1]
                    tmpcol = cellname.split("[")[0]
                    if "[" in cellname.replace("]",""):
                        tmprows = cellname.replace("]","").split("[")[1]
                    else:
                        tmprows = ""
                    tbrow = self.addlinetotable(tmpcol, 0)
                    self.setcelltocorpus(tmprows, tbrow, 1)
                    self.setcelltocorpus(tmpregex, tbrow, 2)
                iopt = iopt +1
        except:
            print("Filtro non valido")

    def filterColElements(self, col):
        self.Progrdialog = progress.Form(self.w)
        self.Progrdialog.show()
        totallines = self.mycorpus.rowCount()
        myvalues = []
        for row in range(self.mycorpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.mycorpus.item(row,col).text()
                if not thistext in myvalues:
                    myvalues.append(thistext)
            except:
                thistext = ""
        mycol = ""
        for key in self.corpuscols:
            if self.corpuscols[key] == col:
                mycol = key
        totallines = len(myvalues)
        for row in range(len(myvalues)):
            self.Progrdialog.w.testo.setText("Sto aggiungendo la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.orbtn()
            tbrow = self.addlinetotable(mycol, 0)
            self.setcelltocorpus("0", tbrow, 2)
            self.setcelltocorpus("^"+re.escape(myvalues[row])+"$", tbrow, 2)
        self.Progrdialog.accept()

    def filterDizionario(self, col, fileName, dizcol = 0):
        self.Progrdialog = progress.Form(self.w)
        self.Progrdialog.show()

        try:
            text_file = open(fileName, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
        except:
            myencoding = "ISO-8859-15"
            #https://pypi.org/project/chardet/
            gotEncoding = False
            while gotEncoding:
                try:
                    myencoding = QInputDialog.getText(self.w, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
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

        totallines = len(lines.split("\n"))
        myvalues = []
        row = 0
        for line in lines.split("\n"):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = line.split("\t")[dizcol]
                if bool(not thistext in myvalues) and thistext != "":
                    myvalues.append(thistext)
            except:
                thistext = ""
            row = row + 1
        mycol = ""
        for key in self.corpuscols:
            if self.corpuscols[key] == col:
                mycol = key
        totallines = len(myvalues)
        for row in range(len(myvalues)):
            self.Progrdialog.w.testo.setText("Sto aggiungendo la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.orbtn()
            tbrow = self.addlinetotable(mycol, 0)
            self.setcelltocorpus("0", tbrow, 2)
            self.setcelltocorpus("^"+re.escape(myvalues[row])+"$", tbrow, 2)
        self.Progrdialog.accept()

    def filtroautomatico(self):
        if self.w.autofiltercombo.currentIndex() == 1:
            thisname = []
            for col in range(self.mycorpus.columnCount()):
                thisname.append(self.mycorpus.horizontalHeaderItem(col).text())
            column = QInputDialog.getItem(self, "Scegli la colonna", "Da quale colonna del corpus devo estrarre i valori del filtro?",thisname,current=self.corpuscols['pos'],editable=False)
            col = thisname.index(column[0])
            self.filterColElements(col)
        if self.w.autofiltercombo.currentIndex() == 2:
            fileName = QFileDialog.getOpenFileName(self, "Apri file del dizionario", self.sessionDir, "TXT files (*.tsv *.csv *.txt)")[0]
            if len(fileName)<1:
                return
            istable = False
            with open(fileName, "r", encoding='utf-8') as ins:
                for line in ins:
                    if bool(re.match(".*[A-Za-z0-9].*", line))==True:
                        if len(line.split("\t"))>1:
                            istable = True
                        break
            dizcol = 0
            if istable:
                dizcol = int(QInputDialog.getInt(self.w, "Indica la colonna del dizionario", "Sembra che il dizionario che hai scelto sia una tabella. Indica la colonna da cui estrarre le parole:")[0])
            thisname = []
            for col in range(self.mycorpus.columnCount()):
                thisname.append(self.mycorpus.horizontalHeaderItem(col).text())
            column = QInputDialog.getItem(self, "Scegli la colonna", "In quale colonna del corpus devo cercare i valori del dizionario?",thisname,current=self.corpuscols['Lemma'],editable=False)
            col = thisname.index(column[0])
            self.filterDizionario(col, fileName, dizcol)
        self.updateFilter()

    def addlinetotable(self, text, column):
        row = self.w.tableWidget.rowCount()
        self.w.tableWidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setItem(row, column, titem)
        self.w.tableWidget.setCurrentCell(row, column)
        return row

    def setcelltocorpus(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setItem(row, column, titem)

    def andbtn(self):
        tbrow = self.addlinetotable("", 0)

    def orbtn(self):
        if self.w.tableWidget.rowCount() > 0:
            tbrow = self.addlinetotable("OR", 0)

    def delbtn(self):
        self.sanitizeTable()
        totallines = len(self.w.tableWidget.selectedItems())
        toselect = []
        for i in range(len(self.w.tableWidget.selectedItems())):
            row = self.w.tableWidget.selectedItems()[i].row()
            toselect.append(row)
        totallines = len(toselect)
        for row in range(len(toselect),0,-1):
            self.w.tableWidget.removeRow(toselect[row-1])

    def sanitizeTable(self):
        for row in range(self.w.tableWidget.rowCount()):
            for col in range(self.w.tableWidget.columnCount()):
                if not self.w.tableWidget.item(row,col):
                    self.setcelltocorpus("", row, col)
    def help(self):
        QMessageBox.information(self, "Suggerimento", "Puoi indicare le parole rpecedenti e successive con il loro numero. Per esempio, -1 è la parola precedente a quella trovata, 1 è la parola successiva.")
