#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import sys
import os
import csv
import re
import mmap

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QDialog


from forms import regex_replace
from forms import progress
from forms import about

class TextEditor(QDialog):

    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/texteditor.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionRimuovi_frasi_ripetute.triggered.connect(self.rm_doublephrases)
        self.w.actionCerca_e_sostituisci.triggered.connect(self.searchreplace)
        self.w.actionNuovo.triggered.connect(self.nuovo)
        self.w.actionApri.triggered.connect(self.apri)
        self.w.actionSalva.triggered.connect(self.salva)
        self.w.actionSalva_come.triggered.connect(self.salvacome)
        self.w.actionBatch_mode.triggered.connect(self.batchmodeshift)
        self.w.actionPreview_mode.triggered.connect(self.previewmodeshift)
        self.w.actionElimina_invii_a_capo_multipli.triggered.connect(self.delmultiplecrlf)
        self.w.filelist.currentRowChanged.connect(self.switchfile)
        self.w.plainTextEdit.cursorPositionChanged.connect(self.showcurpos)
        self.currentFilename = ""
        self.batchmode = False
        self.donotshow = False
        self.previewlimit = 500000
        self.showpreview = False
        self.sessionDir = "."
        self.setWindowTitle("Bran Text Editor")

    def nuovo(self):
        self.currentFilename = ""
        self.w.plainTextEdit.setPlainText("")
        self.setWindowTitle("Bran Text Editor")

    def switchfile(self):
        fileName = self.w.filelist.item(self.w.filelist.currentRow()).text()
        self.setWindowTitle("Bran Text Editor - "+fileName)
        self.loadfile(fileName)
        self.currentFilename = fileName

    def showcurpos(self):
        row = self.w.plainTextEdit.textCursor().blockNumber()
        col = self.w.plainTextEdit.textCursor().positionInBlock()
        self.w.statusBar().showMessage("Riga: "+str(row)+" Colonna: "+str(col))

    def linescount(self, filename):
        f = open(filename, "r+", encoding='utf-8')
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    def salva(self, onlycurrent = ""):
        if self.currentFilename == "":
            self.salvacome()
            return
        fileName = self.currentFilename
        textlist = self.w.plainTextEdit.toPlainText().split("\n")
        text_file = open(fileName, "w", encoding='utf-8')
        text_file.write("")
        text_file.close()
        for line in textlist:
            with open(fileName, "a", encoding='utf-8') as myfile:
                myfile.write(line+"\n")

    def saveregexedit(self, orig, dest):
        fileNames = []
        if not self.batchmode:
            fileNames.append(self.currentFilename)
        else:
            for i in range(self.w.filelist.count()):
                fileNames.append(self.w.filelist.item(i).text())
        #for fileName in fileNames:
            #textlist = self.w.plainTextEdit.toPlainText().split("\n")
            #text_file = open(fileName, "w", encoding='utf-8')
            #text_file.write("")
            #text_file.close()
            #for line in textlist:
                #with open(fileName, "a", encoding='utf-8') as myfile:
                    #myfile.write(line+"\n")

    def salvacome(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file TXT", self.sessionDir, "Text files (*.txt)")[0]
        if fileName != "":
            if fileName[-4:] != ".txt":
                fileName = fileName + ".txt"
            self.currentFilename = fileName
            self.salva(fileName)

    def apri(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        aprilista(fileNames)

    def aprilista(self, fileNames):
        if len(fileNames)<1:
            return
        if len(fileNames)>1 and not self.batchmode:
            ret = QMessageBox.question(self,'Domanda', "Hai selezionato più di un file. Se attivi la modalità batch, le modifiche eseguite con gli strumenti di ricerca e sostituzione verranno applicate automaticamente a tutti i file, altrimenti saranno applicate solo al file attivo. Vuoi attivare la modalità batch?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.batchmode = True
                self.w.actionBatch_mode.setChecked(True)
        for fileName in fileNames:
            self.w.filelist.addItem(fileName)
        fileName = fileNames[-1]
        self.currentFilename = fileName
        self.w.filelist.setCurrentRow(self.w.filelist.count()-1)
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
                    if row>0:
                        lines = lines + "\n"
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
        self.do_searchreplace()

    def delmultiplecrlf(self):
        #ripeti finché non ce ne sono più
        self.do_searchreplace("\\n\\n","\\n", False)

    def do_searchreplace(self, searchstr = "", replstr = "", oneline = True):
        repCdialog = regex_replace.Form(self)
        repCdialog.setModal(False)
        repCdialog.w.lbl_in.hide()
        repCdialog.w.colcombo.hide()
        repCdialog.w.orig.setText(searchstr)
        repCdialog.w.dest.setText(replstr)
        repCdialog.w.colcheck.setText("Considera una riga alla volta")
        repCdialog.w.colcheck.setChecked(oneline)
        repCdialog.exec()
        if repCdialog.result():
            self.Progrdialog = progress.Form(self)
            self.Progrdialog.show()
            newtext = ""
            if repCdialog.w.colcheck.isChecked():
                textlist = self.w.plainTextEdit.toPlainText().split("\n")
                totallines = len(textlist)
                for row in range(totallines):
                    self.Progrdialog.w.testo.setText("Sto cercando nella riga numero "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    origstr = textlist[row]
                    newstr = ""
                    if repCdialog.w.ignorecase.isChecked():
                        newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.IGNORECASE|re.DOTALL)
                    else:
                        newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.DOTALL)
                    if row > 0:
                        newtext = newtext + "\n"
                    newtext = newtext + newstr
            else:
                origstr = self.w.plainTextEdit.toPlainText()
                newtext = ""
                if repCdialog.w.ignorecase.isChecked():
                    newtext = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.IGNORECASE|re.DOTALL)
                else:
                    newtext = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.DOTALL)
            self.w.plainTextEdit.setPlainText(newtext)
            self.Progrdialog.accept()

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

    def contaoccorrenze(self):
        #conta occorrenze: https://pastebin.com/0tPNVACe
        mycol = 1
        csvfile = ""
        mydelimiter = '\t'
        res = occ_count(csvfile, "", mycol, mydelimiter)

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


