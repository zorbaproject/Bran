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

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile("forms/tableeditor.ui")
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
        self.setWindowTitle("Visualizzazione tabella")
        self.separator = "\t"

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
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", ".", "Text files (*.csv *.txt)")[0]
        if fileName != "":
            csv = ""
            for col in range(self.w.tableWidget.columnCount()):
                if col > 0:
                    csv = csv + self.separator
                csv = csv + self.w.tableWidget.horizontalHeaderItem(col).text()
            for row in range(self.w.tableWidget.rowCount()):
                csv = csv + "\n"
                for col in range(self.w.tableWidget.columnCount()):
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.tableWidget.item(row,col).text()
            text_file = open(fileName, "w")
            text_file.write(csv)
            text_file.close()

    def apriCSV(self):
        print("Niente")
