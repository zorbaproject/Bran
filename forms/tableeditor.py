#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
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
        #self.w.apri.clicked.connect(self.doaiuto)
        #self.w.salva.clicked.connect(self.dotest)
        self.setWindowTitle("Visualizzazione tabella")

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

    def addcolumn(self, text, column):
        cols = self.w.tableWidget.columnCount()
        self.w.tableWidget.setColumnCount(cols+1)
        #self.w.tableWidget.horizontalHeaderItem(cols).setText(text)

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
