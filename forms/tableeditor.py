#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QPushButton
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem

import re
import sys
import os


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/tableeditor.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.apricsv.clicked.connect(self.apriCSV)
        self.w.salvacsv.clicked.connect(self.salvaCSV)
        self.w.tableWidget.itemSelectionChanged.connect(self.selOps)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.filterGroup.clicked.connect(self.filtersh)
        self.w.tableWidget.horizontalHeader().sectionDoubleClicked.connect(self.sortbycolumn)
        self.w.apricsv.hide()
        self.setWindowTitle("Visualizzazione tabella")
        self.sessionDir = "."
        self.separator = "\t"
        self.w.filterWidget.hide()

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

    def addcolumn(self, text, column):
        cols = self.w.tableWidget.columnCount()
        self.w.tableWidget.setColumnCount(cols+1)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setHorizontalHeaderItem(cols, titem)
        self.enumeratecolumns(self.w.ccolumn)

    def addlinetotable(self, text, column):
        row = self.w.tableWidget.rowCount()
        self.w.tableWidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setItem(row, column, titem)
        self.w.tableWidget.setCurrentCell(row, column)
        return row

    def setcelltotable(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setItem(row, column, titem)

    def salvaCSV(self):
        checkfilter = False
        for row in range(self.w.tableWidget.rowCount()):
            if self.w.tableWidget.isRowHidden(row):
                msgBox = QMessageBox(self)
                msgBox.setWindowTitle("Domanda")
                msgBox.setText("Cosa vuoi salvare?")
                msgBox.addButton(QPushButton("Solo le righe filtrate", self.w), QMessageBox.YesRole)
                msgBox.addButton(QPushButton('Salva tutte le righe', self.w), QMessageBox.NoRole)
                msgBox.exec_()
                if msgBox.clickedButton().text() == "Solo le righe filtrate":
                    checkfilter = True
                break
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
        if fileName != "":
            if fileName[-4:] != ".csv":
                fileName = fileName + ".csv"
            csv = ""
            for col in range(self.w.tableWidget.columnCount()):
                if col > 0:
                    csv = csv + self.separator
                csv = csv + self.w.tableWidget.horizontalHeaderItem(col).text()
            for row in range(self.w.tableWidget.rowCount()):
                if self.w.tableWidget.isRowHidden(row) == False or checkfilter == False:
                    csv = csv + "\n"
                    for col in range(self.w.tableWidget.columnCount()):
                        if col > 0:
                            csv = csv + self.separator
                        try:
                            csv = csv + self.w.tableWidget.item(row,col).text()
                        except:
                            csv = csv + ""
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()

    def apriCSV(self):
        print("Niente")

    def selOps(self):
        somma = 0.0
        try:
            for i in range(len(self.w.tableWidget.selectedItems())):
                row = self.w.tableWidget.selectedItems()[i].row()
                col = self.w.tableWidget.selectedItems()[i].column()
                somma = somma + float(self.w.tableWidget.item(row,col).text())
            sommas = f'{somma:.3f}'
            self.w.statusbar.setText("Somma: " +str(sommas))
        except:
            if (self.w.statusbar.text() != ""):
                self.w.statusbar.setText("")


    def enumeratecolumns(self, combo):
        combo.clear()
        for col in range(self.w.tableWidget.columnCount()):
            thisname = self.w.tableWidget.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def dofiltra(self):
        tcount = 0
        for row in range(self.w.tableWidget.rowCount()):
            col = self.w.ccolumn.currentIndex()
            ctext = self.w.tableWidget.item(row,col).text()
            ftext = self.w.cfilter.text()
            if bool(re.match(ftext, ctext)):
                self.w.tableWidget.setRowHidden(row, False)
                tcount = tcount +1
            else:
                self.w.tableWidget.setRowHidden(row, True)
        self.w.statusbar.setText("Risultati totali: " +str(tcount))

    def cancelfiltro(self):
        for row in range(self.w.tableWidget.rowCount()):
            self.w.tableWidget.setRowHidden(row, False)

    def filtersh(self):
        if self.w.filterWidget.isVisible() == True:
            self.w.filterWidget.hide()
        else:
            self.w.filterWidget.show()

    def sortbycolumn(self, col):
        self.w.tableWidget.setSortingEnabled(False)
        for row in range(self.w.tableWidget.rowCount()):
            try:
                tbval = float(self.w.tableWidget.item(row,col).text()) #Se la cella contiene testo, questa riga provoca except
                titem = QTableNumberItem()
                titem.setText(self.w.tableWidget.item(row,col).text())
                self.w.tableWidget.setItem(row, col, titem)
            except:
                continue
        self.w.tableWidget.setSortingEnabled(True)
        self.w.tableWidget.sortItems(col)


class QTableNumberItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            myvalue = float(self.text())
            othervalue = float(other.text())
            return myvalue < othervalue
        except:
            return False
