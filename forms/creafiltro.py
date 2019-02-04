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

import re
import sys
import os


class Form(QDialog):
    def __init__(self, parent=None):
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
        self.w.andbtn.clicked.connect(self.andbtn)
        self.w.orbtn.clicked.connect(self.orbtn)
        self.w.delbtn.clicked.connect(self.delbtn)
        self.w.help.clicked.connect(self.help)
        self.setWindowTitle("Crea filtro multiplo")

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()
        self.w.filter.setText("")

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
        tbrow = self.addlinetotable("OR", 0)

    def delbtn(self):
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
