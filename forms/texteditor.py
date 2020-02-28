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

class TextEditor(QMainWindow):

    def __init__(self, parent=None, mycfg=None):
        super(TextEditor, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/texteditor.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        #layout = QVBoxLayout()
        #layout.addWidget(self.w)
        #self.setLayout(layout)
        self.setCentralWidget(self.w)
        self.mycfg = mycfg
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionRimuovi_frasi_ripetute.triggered.connect(self.rm_doublephrases)
        self.w.actionCerca_e_sostituisci.triggered.connect(self.searchreplace)
        self.w.actionNuovo.triggered.connect(self.nuovo)
        self.w.actionChiudi.triggered.connect(self.chiudi)
        self.w.actionApri.triggered.connect(self.apri)
        self.w.actionSalva.triggered.connect(self.salva)
        self.w.actionSalva_come.triggered.connect(self.salvacome)
        self.w.actionCopia.triggered.connect(self.copia)
        self.w.actionTaglia.triggered.connect(self.taglia)
        self.w.actionIncolla.triggered.connect(self.incolla)
        self.w.actionBatch_mode.triggered.connect(self.batchmodeshift)
        self.w.actionPreview_mode.triggered.connect(self.previewmodeshift)
        self.w.actionIniziali_sempre_minuscole.triggered.connect(self.normalizzainiziali)
        self.w.actionTutto_maiuscolo.triggered.connect(self.tuttomaiuscolo)
        self.w.actionTutto_minuscolo.triggered.connect(self.tuttominuscolo)
        self.w.actionElimina_invii_a_capo_multipli.triggered.connect(self.delmultiplecrlf)
        self.w.actionNormalizza_parole_note.triggered.connect(self.normalizza_parolenote)
        self.w.actionTrova_co_occorrenze.triggered.connect(self.coOccorrenze)
        self.w.actionEstrai_testo_da_file_PDF.triggered.connect(self.do_textract)
        self.w.findprev.clicked.connect(self.findprev)
        self.w.findnext.clicked.connect(self.findnext)
        self.w.filelist.currentRowChanged.connect(self.switchfile)
        self.w.plainTextEdit.cursorPositionChanged.connect(self.showcurpos)
        self.w.plainTextEdit.textChanged.connect(self.textchanged)
        self.currentFilename = ""
        self.batchmode = False
        self.donotshow = False
        self.previewlimit = 500000
        self.showpreview = False
        self.sessionDir = "."
        self.modified = -1
        self.setWindowTitle("Bran Text Editor")

    def nuovo(self):
        self.currentFilename = ""
        self.w.plainTextEdit.setPlainText("")
        self.setWindowTitle("Bran Text Editor")
        self.modified = -1
        self.w.plainTextEdit.document().clearUndoRedoStacks()

    def switchfile(self):
        if self.modified == 1:
            ret = QMessageBox.question(self,'Domanda', "Il file attuale è stato modificato, se passi a un altro file le modifiche verranno perse. Vuoi salvare il file attuale?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.salva()
        fileName = self.w.filelist.item(self.w.filelist.currentRow()).text()
        self.setWindowTitle("Bran Text Editor - "+fileName)
        self.loadfile(fileName)
        self.currentFilename = fileName

    def textchanged(self):
        if self.w.plainTextEdit.toPlainText() != "":
            self.modified = 1

    def chiudi(self):
        for i in self.w.filelist.selectedItems():
            self.w.filelist.takeItem(self.w.filelist.row(i))
        for i in range(self.w.filelist.count()):
            item = self.w.filelist.item(i)
            self.w.filelist.setItemSelected(item, False)
        self.nuovo()

    def copia(self):
        self.w.plainTextEdit.copy()

    def incolla(self):
        self.w.plainTextEdit.paste()

    def taglia(self):
        self.w.plainTextEdit.cut()

    def showcurpos(self):
        row = self.w.plainTextEdit.textCursor().blockNumber()
        col = self.w.plainTextEdit.textCursor().positionInBlock()
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

    def coOccorrenze(self):
        parola = QInputDialog.getText(self.w, "Scegli la parola", "Indica la parola che vuoi cercare (come RegEx):", QLineEdit.Normal, "")[0]
        myrange = int(QInputDialog.getInt(self.w, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        TBdialog = tableeditor.Form(self, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = "[" + re.escape(",;:-'\"^°`") + "]"
        else:
            myignore = ""
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        concordanze = []
        tmptxt = self.w.plainTextEdit.toPlainText().replace("'", "' ")
        corpus = tmptxt.split(" ")
        for row in range(len(corpus)):
            if bool(re.match(parola, corpus[row]))==False:
                continue
            thistext = ""
            for i in range(row-myrange, row+myrange+1):
                thistext = thistext + corpus[i] + " "
            punt = " (["+re.escape(".,;!?)")+ "])"
            thistext = re.sub(punt, "\g<1>", thistext, flags=re.IGNORECASE)
            punt = "(["+re.escape("'’(")+ "]) "
            thistext = re.sub(punt, "\g<1>", thistext, flags=re.IGNORECASE|re.DOTALL)
            thistext = re.sub(myignore, "", thistext)
            regex = re.escape('.?!')
            if bool(re.match(".*["+regex+"].*", thistext)):
                punctindex = [m.start(1) for m in re.finditer("(["+regex+"])", thistext, flags=re.DOTALL)]
                if punctindex[0] < thistext.index(parola):
                    thistext = thistext[punctindex[0]+1:]
                else:
                    thistext = thistext[0:punctindex[0]]
            concordanze.append(thistext)
        totallines = len(concordanze)
        for row in range(len(concordanze)):
            self.Progrdialog.w.testo.setText("Sto controllando l'occorrenza numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisrow = concordanze[row].split(" ")
            for word in thisrow:
                thistext = ""
                if thisrow.index(word) < thisrow.index(parola):
                    thistext = str(word) + "..." + str(parola)
                if thisrow.index(word) > thisrow.index(parola):
                    thistext = str(parola) + "..." + str(word)
                if thistext != "":
                    tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                    if len(tbitem)>0:
                        tbrow = tbitem[0].row()
                        tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                        TBdialog.setcelltotable(str(tbval), tbrow, 1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        TBdialog.show()

    def salva(self, onlycurrent = ""):
        if self.currentFilename == "":
            self.salvacome()
            return
        if self.showpreview:
            QMessageBox.information(self, "Attenzione", "È abilitata la modalità di anteprima: significa che il testo attualmente visualizzato potrebbe non essere il completo contenuto del file originale. Per evitare sovrascritture, ti verrà chiesto di salvare su un nuovo file.")
            self.salvacome()
            return
        fileName = self.currentFilename
        textlist = self.w.plainTextEdit.toPlainText().split("\n")
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

    def loadfile(self, fileName = ""):
        if fileName == "":
            fileName = self.currentFilename
        totallines = self.linescount(fileName)
        if totallines > self.previewlimit and not self.showpreview:
            ret = QMessageBox.question(self,'Domanda', "Il file selezionato è molto grande, caricarlo del tutto richiederà tempo e risorse: se non hai abbastanza RAM, il computer potrebbe bloccarsi. Vuoi caricare solo una anteprima?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.showpreview = True
                self.w.actionPreview_mode.setChecked(True)
        self.nuovo()
        lines = self.openwithencoding(fileName, 'utf-8')
        if lines == "ERRORE BRAN: Codifica errata":
            predefEncode = "ISO-8859-15"
            #https://pypi.org/project/chardet/
            myencoding = QInputDialog.getText(self, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, predefEncode)
            self.nuovo()
            lines = self.openwithencoding(fileName, myencoding[0])
            if lines == "ERRORE BRAN: Codifica errata":
                self.loadfile(fileName)
                return
        self.setWindowTitle("Bran Text Editor - "+fileName)
        self.currentFilename = fileName

    def openwithencoding(self, fileName, myencoding = 'utf-8', totallines = -1):
        if totallines < 0:
            totallines = self.linescount(fileName)
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        row = 0
        lines = ""
        try:
            with open(fileName, "r", encoding=myencoding) as ins:
                for line in ins:
                    if row%500 == 0:
                        self.Progrdialog.w.testo.setText("Sto caricando la riga numero "+str(row))
                        self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                        QApplication.processEvents()
                        if self.Progrdialog.w.annulla.isChecked():
                            return
                    self.w.plainTextEdit.appendPlainText(line.replace('\n',''))
                    #if row%2==0:
                    #    fmt= QTextBlockFormat()
                    #    fmt.setBackground(self.errorColor)
                    #    self.w.plainTextEdit.textCursor().setBlockFormat(fmt)
                    row = row + 1
                    if row > self.previewlimit and self.showpreview:
                        break
        except:
            lines = "ERRORE BRAN: Codifica errata"
        self.Progrdialog.accept()
        self.modified = 0
        self.w.plainTextEdit.document().clearUndoRedoStacks()
        return lines

    def batchopenwithencoding(self, fileName, myencoding = 'utf-8', totallines = -1):
        if totallines < 0:
            totallines = self.linescount(fileName)
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        row = 0
        lines = ""
        try:
            with open(fileName, "r", encoding=myencoding) as ins:
                for line in ins:
                    if row%500 == 0:
                        self.Progrdialog.w.testo.setText("Sto caricando la riga numero "+str(row))
                        self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                        QApplication.processEvents()
                        if self.Progrdialog.w.annulla.isChecked():
                            return
                    lines = lines + line
                    row = row + 1
        except:
            lines = "ERRORE BRAN: Codifica errata"
        self.Progrdialog.accept()
        return lines

    def batchmodeshift(self):
        if self.batchmode:
            self.batchmode = False
            self.w.actionBatch_mode.setChecked(False)
        else:
            self.batchmode = True
            self.w.actionBatch_mode.setChecked(True)

    def previewmodeshift(self):
        if showpreview:
            showpreview = False
            self.w.actionPreview_mode.setChecked(False)
        else:
            showpreview = True
            self.w.actionPreview_mode.setChecked(True)

    def searchreplace(self):
        self.do_searchreplace(self.w.plainTextEdit.toPlainText())

    def delmultiplecrlf(self):
        #ripeti finché non ce ne sono più
        self.do_searchreplace(self.w.plainTextEdit.toPlainText(), "\\n\\n","\\n", False)

    def findnext(self):
        self.findgeneric(1)

    def findprev(self):
        self.findgeneric(-1)

    def findgeneric(self, dir = 0):
        mytext = self.w.plainTextEdit.toPlainText()
        escape = bool(self.w.findregex.isChecked() == False)
        myregex = self.w.findtext.text()
        mypos = self.w.plainTextEdit.textCursor().position()
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
                cursor = QTextCursor(self.w.plainTextEdit.textCursor())
                cursor.setPosition(start, QTextCursor.MoveAnchor)
                cursor.setPosition(end, QTextCursor.KeepAnchor)
                self.w.plainTextEdit.setTextCursor(cursor)
                break
            if dir > 0:
                n = n + 1
            else:
                n = n - 1

    def normalizza_parolenote(self):
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/normalizzazione.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        normalizzazione = json.loads(myjson)
        Progrdialog = progress.Form(self)
        Progrdialog.show()
        totallines = len(normalizzazione)
        row = 0
        mytext = self.w.plainTextEdit.toPlainText()
        newtext = ""
        for regola in normalizzazione:
            if row <51 or row % 500 == 0:
                Progrdialog.w.testo.setText("Sto cercando la regola numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if Progrdialog.w.annulla.isChecked():
                    return
            searchstr = regola["search"]
            replstr = regola["replace"]
            escape = False
            if not regola["regex"]:
                #escape = True
                #searchstr = " " + searchstr + " "
                #replstr = " " + replstr + " "
                searchstr = "([^a-zA-Z0-9òàùèéì])" + re.escape(searchstr) + "([^a-zA-Z0-9òàùèéì])"
                replstr = "\g<1>" + replstr + "\g<2>"
            ignorecase = regola["caseinsensitive"]
            dolower = regola["lower"]
            doupper = regola["upper"]
            mytext = self.perform_searchreplace(mytext, searchstr, replstr, escape, False, dolower, doupper, ignorecase, False)
            if mytext != "":
                newtext = mytext
            row = row + 1
        self.w.plainTextEdit.setPlainText(newtext)
        Progrdialog.accept()

    def do_searchreplace(self, mytext, searchstr = "", replstr = "", oneline = True, dolower = False, doupper = False):
        repCdialog = regex_replace.Form(self)
        repCdialog.setModal(False)
        repCdialog.w.lbl_in.hide()
        repCdialog.w.colcombo.hide()
        repCdialog.w.changeCase.show()
        repCdialog.w.dolower.setChecked(dolower)
        repCdialog.w.doupper.setChecked(doupper)
        repCdialog.w.orig.setText(searchstr)
        repCdialog.w.dest.setText(replstr)
        repCdialog.w.colcheck.setText("Considera una riga alla volta")
        repCdialog.w.colcheck.setChecked(oneline)
        repCdialog.exec()
        if repCdialog.result():
            self.perform_searchreplace(mytext, repCdialog.w.orig.text(), repCdialog.w.dest.text(), False, repCdialog.w.colcheck.isChecked(), repCdialog.w.dolower.isChecked(), repCdialog.w.doupper.isChecked(), repCdialog.w.ignorecase.isChecked())

    def perform_searchreplace(self, mytext, searchstr = "", replstr = "", escape = False, oneline = True, dolower = False, doupper = False, ignorecase = True, showprogress = True):
        if ignorecase:
            myflags=re.IGNORECASE|re.DOTALL
        else:
            myflags=re.DOTALL
        newtext = ""
        fileNames = []
        if self.batchmode:
            for i in range(self.w.filelist.count()):
                fileNames.append(self.w.filelist.item(i).text())
        else:
            fileNames.append("")
        totfiles = len(fileNames)
        filen = 0
        if showprogress:
            Progrdialog = progress.Form(self)
            Progrdialog.show()
        for fileName in fileNames:
            if fileName != "" and os.path.isfile(fileName) and self.batchmode:
                mytext = self.batchopenwithencoding(fileName, 'utf-8')
                if mytext == "ERRORE BRAN: Codifica errata":
                    predefEncode = "ISO-8859-15"
                    #https://pypi.org/project/chardet/
                    myencoding = QInputDialog.getText(self, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, predefEncode)
                    self.nuovo()
                    mytext = self.openwithencoding(fileName, myencoding[0])
                    if mytext == "ERRORE BRAN: Codifica errata":
                       return ""
            else:
                if showprogress:
                    self.w.plainTextEdit.setPlainText("")
            if oneline:
                textlist = mytext.split("\n")
                totallines = len(textlist)
                for row in range(totallines):
                    if showprogress:
                        Progrdialog.w.testo.setText("Sto cercando nella riga numero "+str(row))
                        Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                        QApplication.processEvents()
                        if Progrdialog.w.annulla.isChecked():
                            return ""
                    origstr = textlist[row]
                    try:
                        if escape:
                            #searchstr = re.escape(searchstr)
                            newstr = origstr.replace(searchstr, replstr)
                        else:
                            newstr = re.sub(searchstr, replstr, origstr, flags=myflags)
                    except:
                        self.w.plainTextEdit.setPlainText(mytext)
                        if showprogress:
                            Progrdialog.accept()
                        QMessageBox.critical(self, "Attenzione", "Sembra ci sia un errore nell'espressione regolare" + searchstr + " -> " + replstr + " \nControlla la sintassi.")
                        return
                    if dolower:
                        indexes = [(m.start(0), m.end(0)) for m in re.finditer(searchstr, newstr, flags=myflags)]
                        for f in indexes:
                            newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                    if doupper:
                        indexes = [(m.start(0), m.end(0)) for m in re.finditer(searchstr, newstr, flags=myflags)]
                        for f in indexes:
                            newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                    newtext = newstr
                    if not self.batchmode:
                        self.w.plainTextEdit.appendPlainText(newtext)
                    else:
                        if row == 0:
                            text_file = open(fileName, "w", encoding='utf-8')
                            text_file.write("")
                            text_file.close()
                        with open(fileName, "a", encoding='utf-8') as myfile:
                            if row > 0:
                                newtext = "\n" + newtext
                            myfile.write(newtext)
            else:
                if showprogress:
                    Progrdialog.w.testo.setText("Sto cercando nel file numero "+str(filen))
                    Progrdialog.w.progressBar.setValue(int((filen/totfiles)*100))
                    QApplication.processEvents()
                    if Progrdialog.w.annulla.isChecked():
                        return ""
                try:
                    if escape:
                        #searchstr = re.escape(searchstr)
                        newtext = mytext.replace(searchstr, replstr)
                    else:
                        newtext = re.sub(searchstr, replstr, mytext, flags=myflags)
                except:
                    self.w.plainTextEdit.setPlainText(mytext)
                    if showprogress:
                        Progrdialog.accept()
                    QMessageBox.critical(self, "Attenzione", "Sembra ci sia un errore nell'espressione regolare. Controlla la sintassi.")
                    return ""
                if dolower:
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer(searchstr, newtext, flags=myflags)]
                    for f in indexes:
                        newtext = newtext[0:f[0]] + newtext[f[0]:f[1]].lower() + newtext[f[1]:]
                if doupper:
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer(searchstr, newtext, flags=myflags)]
                    for f in indexes:
                        newtext = newtext[0:f[0]] + newtext[f[0]:f[1]].upper() + newtext[f[1]:]
                if fileName != "":
                    text_file = open(fileName, "w", encoding='utf-8')
                    text_file.write(newtext)
                    text_file.close()
                else:
                    if showprogress:
                        self.w.plainTextEdit.setPlainText(newtext)
                    else:
                        return newtext
                filen = filen + 1
        if showprogress:
            Progrdialog.accept()
        if self.batchmode:
            self.switchfile()
        return ""

    def rm_doublephrases(self):
        #dele phrases repeated: https://pastebin.com/7Krbii0d
        wnumber = 10
        searchthis = " " #this is the separator: if " " you look for words, if "." you look for phrases
        filein = ""
        fileout = ""
        text = ""

        #if len(sys.argv) > 1:
        #    filein = sys.argv[1]
        #if filein == "-h":
        #    print("Usage:\n delete-phrases-repetition.py \"fileinput.txt\" 10 \"fileoutput.txt\" \" \"\n delete-phrases-repetition.py \"fileinput.txt\" 1 \"fileoutput.txt\" \".\"\nNOTE: The number represents occurrences of the separator to get a phrase. If you use \".\" as separator, the number should be 1.")
        #    sys.exit()

        #if len(sys.argv) > 2:
        #   wnumber = int(sys.argv[2])

        #if len(sys.argv) > 3:
        #    fileout = sys.argv[3]

        #if len(sys.argv) > 4:
        #    searchthis = sys.argv[4]

        if filein != "" and os.path.isfile(filein):
            text_file = open(filein , "r")
            #text = text_file.read().replace("\n", "")
            text = text_file.read()
            text_file.close()
        else:
            return

        if wnumber < 0:
            wnumber = 10


        active = 1
        pos = 0
        while active:
            wpos = pos
            npos = pos
            #read a specific number of words
            for i in range(wnumber):
                wpos = text.find(searchthis, npos+1)
                if wpos > 0:
                    npos = wpos
            #check if we reached someway the end of text
            if npos > len(text)-1:
                if pos > len(text)-1:
                    break
                else:
                    npos = len(text)-1
            #read this phrase
            tmpstring = text[pos:npos]
            #replace all occurrences of the phrase, after the first one, with nothing
            if tmpstring != "":
                newtext = nth_replace(text, tmpstring, "", 2, "all right")
                text = newtext
            pos = text.find(searchthis, pos+1)+1 #continue from next word
            if pos <= 0:
                pos = len(text)

        #delete double spaces
        newtext = newtext.replace("  ", " ")

        if fileout:
            text_file = open(fileout, "w")
            text_file.write(newtext)
            text_file.close()
        else:
            self.w.plainTextEdit.document().setPlainText(newtext)

    def findIndexinCol(arr, string, col):
        for i in range(len(arr)):
            if (arr[i][col]) == string:
                return i
        return -1

    def normalizzainiziali(self):
        self.do_searchreplace(self.w.plainTextEdit.toPlainText(), "([" + re.escape(".?!") + "]) *([A-ZÈÉÀÒÌÙ])","\\g<1> \\g<2>", False, True, False)

    def tuttominuscolo(self):
        self.do_searchreplace(self.w.plainTextEdit.toPlainText(), "(.*)","\\g<1>", False, True, False)

    def tuttomaiuscolo(self):
        self.do_searchreplace(self.w.plainTextEdit.toPlainText(), "(.*)","\\g<1>", False, False, True)

    def contaoccorrenze(self):
        #conta occorrenze: https://pastebin.com/0tPNVACe
        mycol = 1
        csvfile = ""
        mydelimiter = '\t'
        res = self.occ_count(csvfile, "", mycol, mydelimiter)

    def occ_count(self, csvfile = "", outputfile = "", mycol = 1, mydelimiter = '\t'):
        mycsv = []
        #mycol = 1
        #csvfile = ""
        #mydelimiter = '\t'
        words = []
        #outputfile = ""

        #if len(sys.argv) < 2:
        #        print("python3 conta-occorrenze.py FILEINPUT FILEOUTPUT COLONNA DELIMITATORE\n ES:\n \"C:\\Programs\\Python 3.6\\Python 3.6 (32-bit).lnk\" \"C:\\conta-occorrenze.py\" \"C:\\ETR Tagged.txt\" \"C:\\occorrenze.csv\" 1 '\\t'")
        #if len(sys.argv) > 1:
        #        csvfile = sys.argv[1]
        #if len(sys.argv) > 2:
        #        outputfile = sys.argv[2]
        #if len(sys.argv) > 3:
        #        mycol = int(sys.argv[3])
        #if len(sys.argv) > 4:
        #        mydelimiter = sys.argv[4]

        if (len(mydelimiter) != 1):
                mydelimiter = '\t'

        if csvfile == "":
                return

        csvfile = os.path.abspath(csvfile)
        origdict = list(csv.reader(open(csvfile), delimiter=mydelimiter)) #this is [row][column]
        for i in range(len(origdict)):
                if (len(origdict[i]) > mycol):
                        mycsv.append(origdict[i][mycol])

        for word in mycsv:
                value_index = findIndexinCol(words,word,0)
                if value_index > -1:
                        thiscount = words[value_index][1]
                        words[value_index][1] = thiscount + 1
                else:
                        value_index = len(words)
                        words.append([word,1])

        csvoutput = ""
        for i in range(len(words)):
                csvoutput += words[i][0] + ";" + str(words[i][1]) + "\n"

        #if (outputfile != ""):
        #        text_file = open(outputfile, "w")
        #        text_file.write(csvoutput)
        #        text_file.close()
        return csvoutput

    def nth_replace(string, old, new, n=1, option='only nth'):
        """
       This function replaces occurrences of string 'old' with string 'new'.
       There are three types of replacement of string 'old':
       1) 'only nth' replaces only nth occurrence (default).
       2) 'all left' replaces nth occurrence and all occurrences to the left.
       3) 'all right' replaces nth occurrence and all occurrences to the right.
       """
        if option == 'only nth':
            left_join = old
            right_join = old
        elif option == 'all left':
            left_join = new
            right_join = old
        elif option == 'all right':
            left_join = old
            right_join = new
        else:
            print("Invalid option. Please choose from: 'only nth' (default), 'all left' or 'all right'")
            return None
        groups = string.split(old)
        nth_split = [left_join.join(groups[:n]), right_join.join(groups[n:])]
        return new.join(nth_split)

    def install_textract(self):
        try:
            import pip
            import sys
            import os
            debcmd = "sudo apt-get install python-dev libxml2-dev libxslt1-dev antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-dev swig libpulse-dev"
            rpmcmd = "sudo yum install python-devel libxml2-devel libxslt1-devel antiword unrtf poppler-utils pstotext tesseract-ocr flac ffmpeg lame libmad0 libsox-fmt-mp3 sox libjpeg-devel swig libpulse-devel"
            try:
                import textract
            except:
                pkgname = "textract"
                if platform.system() == "Linux":
                    if os.path.isfile("/usr/bin/apt-get"):
                        os.system("xterm -e "+debcmd)
                    else:
                         os.system("xterm -e "+rpmcmd)
                elif platform.system() == "Windows":
                    #http://prdownloads.sourceforge.net/swig/swigwin-3.0.12.zip 
                    QMessageBox.information(self, "Attenzione", "Prima di installare Textract devi installare SWIG, seguendo le istruzioni della pagina https://stackoverflow.com/questions/44504899/installing-pocketsphinx-python-module-command-swig-exe-failed")
                    pkgname = "https://github.com/deanmalmgren/textract/archive/master.zip"
                elif platform.system() == "OS X":
                    maccmd = "brew install caskroom/cask/brew-cask \nbrew cask install xquartz \nbrew install poppler antiword unrtf tesseract swig"
                    QMessageBox.information(self, "Ottimo", "Ricordati che sarà necessario installare una serie di pacchetti affinché Textract possa funzionare. Su un sistema di tipo MacOSX dovrai dare un comando di questo tipo: "+maccmd)
                try:
                    pip.main(["install", pkgname])
                except:
                    from pip._internal import main as pipmain
                    pipmain(["install", pkgname])
        except:
            QMessageBox.critical(self, "Peccato...", "Non sono riuscito a installare Textract. Potrebbe essere un problema temporaneo, riprova tra qualche giorno. Altrimenti, consulta la pagina https://textract.readthedocs.io/en/latest/installation.html")
            return

    def do_textract(self):
        if platform.system() == "Windows":
            QMessageBox.warning(self, "Peccato...", "L'utilizzo della libreria Textract su Windows è sperimentale: puoi provare a installarlo, ma molti tipi di file potrebbero non essere supportati. Se vuoi essere sicuro che funzioni tutto, prova a usare Bran da GNU/Linux o MacOSX.")
        try:
            import textract
        except:
            ret = QMessageBox.question(self,'Suggerimento', "Pare che la libreria Textract non sia installata sul tuo sistema. Vuoi provare a installarla adesso?\nSe la procedura si interrompe, basta ripeterla più volte fino al corretto completamento.", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.install_textract()
            return
        oldcurfile = self.currentFilename
        if self.modified == 1:
            ret = QMessageBox.question(self,'Domanda', "Il file attuale è stato modificato, se passi a un altro file le modifiche verranno perse. Vuoi salvare il file attuale?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.salva()
        try:
            exts = "*.tsv *.csv *.doc *.docx *.eml *.epub *.gif *.jpg *.jpeg *.json *.html *.htm *.mp3 *.msg *.odt *.ogg *.pdf *.png via tesseract-ocr *.pptx *.ps *.rtf *.tiff *.tif *.txt *.wav *.xlsx *.xls"
            fileNames = QFileDialog.getOpenFileNames(self, "Apri file", self.sessionDir, "Text files ("+exts+")")[0]
            if len(fileNames)>0:
                self.nuovo()
            for fileName in fileNames:
                mybytes = b''
                if ".gif" in fileName or ".jpg" in fileName or ".jpeg" in fileName or ".png" in fileName:
                    predefLang = "ita"
                    mylang = QInputDialog.getText(self.w, "Scegli la lingua", "Sembra che tu abbia selezionato un file immagine. Per estrarre il testo, verrà usato l'OCR: per favore, specifica la lingua del testo (es: ita, eng, deu)", QLineEdit.Normal, predefLang)[0]
                    mybytes = textract.process(fileName, language=mylang, method='tesseract', encoding='utf-8')
                else:
                    mybytes = textract.process(fileName, encoding='utf-8')
                mytext = mybytes.decode('utf-8')
                self.w.plainTextEdit.appendPlainText(str(mytext))
        except:
            fileName = oldcurfile
            self.setWindowTitle("Bran Text Editor - "+fileName)
            if fileName != "" and os.path.isfile(fileName):
                self.loadfile(fileName)
                self.currentFilename = fileName
