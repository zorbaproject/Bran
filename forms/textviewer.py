#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import sys
import os
import subprocess
import platform
import csv
import re
import mmap
import json

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QDialog
from PySide2.QtCore import Qt
from PySide2.QtGui import QTextCursor


from forms import regex_replace
from forms import progress
from forms import about
from forms import tableeditor
from forms import alberofrasi

class TextViewer(QMainWindow):

    def __init__(self, parent=None, mycfg=None):
        super(TextViewer, self).__init__(parent.corpuswidget)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/textviewer.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        #layout = QVBoxLayout()
        #layout.addWidget(self.w)
        #self.setLayout(layout)
        self.setCentralWidget(self.w)
        self.mycfg = mycfg
        self.w.actionNuovo.triggered.connect(self.nuovo)
        self.w.actionChiudi.triggered.connect(self.chiudi)
        self.w.actionApri.triggered.connect(self.apri)
        self.w.actionSalva.triggered.connect(self.salva)
        self.w.actionSalva_come.triggered.connect(self.salvacome)
        self.w.actionCopia.triggered.connect(self.copia)
        #self.w.actionIncolla.triggered.connect(self.incolla)
        self.w.gotoButton.clicked.connect(self.goto)
        self.w.gotoLoadFromFile.clicked.connect(self.gotoLoadFile)
        self.w.gotoList.itemDoubleClicked.connect(self.gotoFromList)
        self.w.findprev.clicked.connect(self.findprev)
        self.w.findnext.clicked.connect(self.findnext)
        self.w.visualizzaalbero.clicked.connect(self.alberofrase)
        self.w.textEdit.selectionChanged.connect(self.textselected)
        #self.w.textEdit.cursorPositionChanged.connect(self.showcurpos)
        #self.w.textEdit.textChanged.connect(self.textchanged)
        self.currentFilename = ""
        self.donotshow = False
        self.previewlimit = 500000
        self.showpreview = False
        self.sessionDir = "."
        self.separator = "\t"
        self.setWindowTitle("Bran RichText Viewer")
        self.orightml = ""
        self.gotofile = []
        self.corpuswidget = parent.corpuswidget
        self.Corpus = parent


    def nuovo(self):
        self.currentFilename = ""
        self.w.textEdit.setPlainText("")
        self.setWindowTitle("Bran RichText Viewer")
        self.modified = -1
        self.w.textEdit.document().clearUndoRedoStacks()

    def chiudi(self):
        for i in self.w.filelist.selectedItems():
            self.w.filelist.takeItem(self.w.filelist.row(i))
        for i in range(self.w.filelist.count()):
            item = self.w.filelist.item(i)
            self.w.filelist.setItemSelected(item, False)
        self.nuovo()

    def copia(self):
        self.w.textEdit.copy()

    def incolla(self):
        self.w.textEdit.paste()

    def taglia(self):
        self.w.textEdit.cut()

    def goto(self):
        try:
            phID = str(self.w.gotophrase.text())
        except:
            phID = ""
        try:
            tkID = str(self.w.gototoken.text())
        except:
            tkID = ""
        if not phID.startswith("P"):
            phID = "P"+str(phID)
        if not tkID.startswith("T"):
            tkID = "T"+str(tkID)
        self.highlight([phID],[tkID])


    def gotoFromList(self, myitem):
        phIDs = []
        #TODO: find out how to get phrase id
        tkIDs = []
        try:
            i = self.w.gotoList.row(myitem)
            for t in range(int(self.gotofile[i][1]), int(self.gotofile[i][2])+1):
                tkIDs.append("T"+str(t))
        except:
            pass
        self.highlight(phIDs,tkIDs)

    def highlight(self, phraseIDs = [], tokenIDs = []):
        gotoName = ""
        gotocss = ""
        try:
            phraseID = phraseIDs[0]
        except:
            phraseID = "-1"
        try:
            tokenID = tokenIDs[0]
        except:
            tokenID = "-1"
        gotoName = phraseID
        if tokenID != "" and tokenID != "T":
            gotoName = tokenID
        #gotocss = gotocss +"body {\nbackground: yellow;\n}\n"
        for frase in phraseIDs:
            if frase == "":
                continue
            gotocss = gotocss +"." + str(frase) + " {\nbackground: yellow;\n}\n"
        for token in tokenIDs:
            if token == "":
                continue
            gotocss = gotocss + "." + str(token) + " {\ncolor: blue;\n}\n"
        document = self.w.textEdit.document()
        document.setDefaultStyleSheet(gotocss)
        #print(gotocss)
        document.setHtml(self.orightml)
        self.w.textEdit.setDocument(document)
        if gotoName != "":
            print("scrolling to "+gotoName)
            self.w.textEdit.scrollToAnchor(gotoName);
            #Select text
            #self.textselected()

    def gotoLoadFile(self):
        self.gotofile = []
        fileNames = QFileDialog.getOpenFileNames(self.w, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv)")[0]
        self.do_gotoloadfile(fileNames)

    def do_gotoloadfile(self, fileNames):
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    print(fileName)
                    if not os.path.getsize(fileName) > 0:
                        continue
                    try:
                        totallines = self.linescount(fileName)
                    except Exception as ex:
                        print(ex)
                        continue
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    linesA = lines.split('\n')
                    row = 0
                    firstrow = True
                    for line in linesA:
                        if line == "":
                            continue
                        if firstrow:
                            firstrow = False
                            continue
                        newtoken = line.split(self.separator)
                        self.gotofile.append(newtoken)
                        self.w.gotoList.addItem(str(newtoken[0]))

    def showcurpos(self):
        row = self.w.textEdit.textCursor().blockNumber()
        col = self.w.textEdit.textCursor().positionInBlock()
        self.w.statusBar().showMessage("Riga: "+str(row)+" Colonna: "+str(col))

    def linescount(self, filename):
        lines = 0
        try:
            f = open(filename, "r+", encoding='utf-8')
            buf = mmap.mmap(f.fileno(), 0)
            readline = buf.readline
            while readline():
                lines += 1
        except:
            lines = 0
        return lines

    def alberofrase(self):
        alberofrasidialog = alberofrasi.Form(self.Corpus)
        alberofrasidialog.openphrase(self.w.gotophrase.text())
        alberofrasidialog.exec()

    def salva(self, onlycurrent = ""):
        if self.currentFilename == "":
            self.salvacome()
            return
        if self.showpreview:
            QMessageBox.information(self, "Attenzione", "È abilitata la modalità di anteprima: significa che il testo attualmente visualizzato potrebbe non essere il completo contenuto del file originale. Per evitare sovrascritture, ti verrà chiesto di salvare su un nuovo file.")
            self.salvacome()
            return
        fileName = self.currentFilename
        textlist = self.w.textEdit.toPlainText().split("\n")
        text_file = open(fileName, "w", encoding='utf-8')
        text_file.write("")
        text_file.close()
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        row = 0
        totallines = len(textlist)
        for line in textlist:
            self.Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            with open(fileName, "a", encoding='utf-8') as myfile:
                myfile.write(line+"\n")
            row = row + 1
        self.modified = 0
        self.Progrdialog.accept()

    def salvacome(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file TXT", self.sessionDir, "Text files (*.txt)")[0]
        if fileName != "":
            if fileName[-4:] != ".txt":
                fileName = fileName + ".txt"
            self.currentFilename = fileName
            self.salva(fileName)

    def apri(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        self.aprilista(fileNames)

    def aprilista(self, fileNames):
        if len(fileNames)<1:
            return
        for fileName in fileNames:
            if len(self.w.filelist.findItems(fileName, Qt.MatchExactly))==0:
                self.w.filelist.addItem(fileName)
        fileName = fileNames[-1]
        self.currentFilename = fileName
        self.w.filelist.setCurrentRow(self.w.filelist.count()-1)
        if self.w.filelist.count()>1 and not self.batchmode:
            ret = QMessageBox.question(self,'Domanda', "Hai selezionato più di un file. Se attivi la modalità batch, le modifiche eseguite con gli strumenti di ricerca e sostituzione verranno applicate automaticamente a tutti i file, altrimenti saranno applicate solo al file attivo. Vuoi attivare la modalità batch?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.batchmode = True
                self.w.actionBatch_mode.setChecked(True)
        self.loadfile(fileName)

    def loadfile(self, fileName = "", showhtml = False):
        if fileName == "":
            fileName = self.currentFilename
        totallines = self.linescount(fileName)
        if totallines > self.previewlimit and not self.showpreview:
            ret = QMessageBox.question(self,'Domanda', "Il file selezionato è molto grande, caricarlo del tutto richiederà tempo e risorse: se non hai abbastanza RAM, il computer potrebbe bloccarsi. Vuoi caricare solo una anteprima?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.showpreview = True
                self.w.actionPreview_mode.setChecked(True)
                totallines = self.previewlimit
        self.nuovo()
        self.sessionDir = os.path.dirname(fileName)
        lines = self.openwithencoding(fileName, 'utf-8', totallines, showhtml)
        if lines == "ERRORE BRAN: Codifica errata":
            predefEncode = "ISO-8859-15"
            #https://pypi.org/project/chardet/
            myencoding = QInputDialog.getText(self, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, predefEncode)
            self.nuovo()
            lines = self.openwithencoding(fileName, myencoding[0], totallines, showhtml)
            if lines == "ERRORE BRAN: Codifica errata":
                self.loadfile(fileName)
                return
        self.orightml = lines
        self.setWindowTitle("Bran RichText Viewer - "+fileName)
        self.currentFilename = fileName

    def openwithencoding(self, fileName, myencoding = 'utf-8', totallines = -1, showhtml = False):
        if totallines < 0:
            totallines = self.linescount(fileName)
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        row = 0
        lines = ""
        try:
            self.w.textEdit.setText("")
            with open(fileName, "r", encoding=myencoding) as ins:
                for line in ins:
                    if row%500 == 0:
                        self.Progrdialog.w.testo.setText("Sto caricando la riga numero "+str(row))
                        self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                        QApplication.processEvents()
                        if self.Progrdialog.w.annulla.isChecked():
                            return
                    lines = lines + line
                    if showhtml:
                        self.w.textEdit.insertHtml(line.replace('\n',''))
                    else:
                        self.w.textEdit.insertPlainText(line.replace('\n',''))
                    #if row%2==0:
                    #    fmt= QTextBlockFormat()
                    #    fmt.setBackground(self.errorColor)
                    #    self.w.textEdit.textCursor().setBlockFormat(fmt)
                    row = row + 1
                    if row > self.previewlimit and self.showpreview:
                        break
        except:
            lines = "ERRORE BRAN: Codifica errata"
        self.Progrdialog.accept()
        self.modified = 0
        self.w.textEdit.document().clearUndoRedoStacks()
        return lines

    def previewmodeshift(self):
        if showpreview:
            showpreview = False
            self.w.actionPreview_mode.setChecked(False)
        else:
            showpreview = True
            self.w.actionPreview_mode.setChecked(True)

    def searchreplace(self):
        self.do_searchreplace(self.w.textEdit.toPlainText())


    def findnext(self):
        self.findgeneric(1)

    def findprev(self):
        self.findgeneric(-1)

    def findgeneric(self, dir = 0):
        mytext = self.w.textEdit.toPlainText()
        escape = bool(self.w.findregex.isChecked() == False)
        myregex = self.w.findtext.text()
        mypos = self.w.textEdit.textCursor().position()
        if escape:
            myregex = re.escape(myregex)
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(myregex, mytext)]
        if dir > 0:
            n = 0
        else:
            n = len(indexes)-1
        while n > -1 and n < len(indexes):
            start = indexes[n][0]
            end = indexes[n][1]
            if bool(dir > 0 and start > mypos) or bool(dir < 0 and end < mypos):
                cursor = QTextCursor(self.w.textEdit.textCursor())
                cursor.setPosition(start, QTextCursor.MoveAnchor)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                self.w.textEdit.setTextCursor(cursor)
                self.textselected()
                break
            if dir > 0:
                n = n + 1
            else:
                n = n - 1

    def textselected(self):
        selhtml = self.w.textEdit.textCursor().selection().toHtml()
        #print(selhtml)
        tokenname = re.sub('.*'+re.escape('<a name="T')+'([0-9]*)".*','\g<1>',selhtml.replace("\n",""))
        phrasename = re.sub('.*'+re.escape('<a name="P')+'([0-9]*)".*','\g<1>',selhtml.replace("\n",""))
        if phrasename.isnumeric() and tokenname.isnumeric() == False:
            s = self.orightml.find('name="T', self.orightml.find('name="P'+phrasename+'"'))
            e = self.orightml.find('"', s+7)
            tokenname = self.orightml[s+7:e]
        if tokenname.isnumeric() and phrasename.isnumeric() == False:
            s = self.orightml.rfind('name="P', 0, self.orightml.find('name="T'+tokenname+'"'))
            e = self.orightml.find('"', s+7)
            phrasename = self.orightml[s+7:e]
        try:
            self.w.gototoken.setText(str(int(tokenname)))
        except:
            self.w.gototoken.setText("")
        try:
            self.w.gotophrase.setText(str(int(phrasename)))
        except:
            self.w.gotophrase.setText("")

    def findIndexinCol(arr, string, col):
        for i in range(len(arr)):
            if (arr[i][col]) == string:
                return i
        return -1

