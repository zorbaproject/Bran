# -*- coding: utf-8 -*-

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile

import re

class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        #QMessageBox.warning(self, self.tr("My Application"), self.tr("The document has been modified.\nDo you want to save your changes?"))
        file = QFile("forms/regex_replace.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.aiutowid.hide()
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.aiutocb.clicked.connect(self.doaiuto)
        self.w.dotest.clicked.connect(self.dotest)
        self.w.cheat.clicked.connect(self.docheat)
        self.setWindowTitle("Sostituisci con RegEx")

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

    def doaiuto(self):
        if self.w.aiutocb.isChecked():
            self.w.aiutowid.show()
            self.w.setMinimumWidth(500)
        else:
            self.w.aiutowid.hide()

    def dotest(self):
        origstr = self.w.test.toPlainText()
        newstr = ""
        if self.w.ignorecase.isChecked():
            newstr = re.sub(self.w.orig.text(), self.w.dest.text(), origstr, flags=re.IGNORECASE|re.DOTALL)
        else:
            newstr = re.sub(self.w.orig.text(), self.w.dest.text(), origstr, flags=re.DOTALL)
        self.w.test.document().setPlainText(newstr)

    def docheat(self):
        QMessageBox.information(self, "RegEx cheatsheet", "^ = inizio della stringa\n$ = fine della stringa\n( ) = gruppo\n\\1 = primo gruppo da sinistra (nella destinazione)")
