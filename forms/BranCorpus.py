#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pip
import sys
import os
import re
import urllib.request
import urllib.parse
import html
import datetime
import time
import json
from socket import timeout
import subprocess
import platform
import mmap
import random
import math
from shutil import copyfile

arch = platform.architecture()[0]

try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        from tkinter import messagebox
        thispkg = "le librerie grafiche"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "PySide2"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        from PySide2.QtWidgets import QApplication
    except:
        try:
            from pip._internal import main as pipmain
            from tkinter import messagebox
            pipmain(["install", "PySide2"])
            from PySide2.QtWidgets import QApplication
        except:
            sys.exit(1)

from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import QDir
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtWidgets import QTableWidgetSelectionRange
from PySide2.QtCore import QThread
from PySide2.QtCore import QObject
from PySide2.QtWidgets import QWidget

from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import textviewer
from forms import tableeditor
from forms import confronto
from forms import tint
from forms import progress
from forms import sessione
from forms import ripetizioni
from forms import about
from forms import creafiltro
from forms import alberofrasi



class BranCorpus(QObject):
    sizeChanged = Signal(int)
    progressUpdated = Signal(int)

    def __init__(self, corpcol, legPos, ignthis, dimlst, tablewidget=None, parent=None):
        #super(BranCorpus, self).__init__(parent)
        super(BranCorpus, self).__init__()
        #self.w = window
        self.corpuswidget = tablewidget
        self.corpus = []
        self.daToken = 0
        self.aToken = 100
        self.allToken = False
        try:
            self.corpuswidget.cellChanged.connect(self.corpusCellChanged)
        except:
            pass
        #self.setWindowTitle("Bran")
        self.corpuscols = corpcol
        self.legendaPos = legPos
        self.ignoretext = ignthis
        self.dimList = dimlst
        #self.ignorepos = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "altro"] # "punteggiatura - .?!"
        self.ignorepos = ["punteggiatura - .?!", "simboli", "altro"]
        self.separator = "\t"
        self.language = "ita"
        self.filtrimultiplienabled = 10 #"Filtro multiplo"
        self.filter = ""
        self.filterColumn = self.filtrimultiplienabled
        self.alreadyChecked = False
        self.ImportingFile = False
        self.OnlyVisibleRows = False
        self.core_killswitch = False
        self.sessionFile = ""
        self.sessionDir = "."
        self.Textracts_exts = "*.tsv *.csv *.doc *.docx *.eml *.epub *.gif *.jpg *.jpeg *.json *.html *.htm *.mp3 *.msg *.odt *.ogg *.pdf *.png via tesseract-ocr *.pptx *.ps *.rtf *.tiff *.tif *.txt *.wav *.xlsx *.xls"
        self.mycfgfile = QDir.homePath() + "/.brancfg"
        self.mycfg = json.loads('{"javapath": "", "tintpath": "", "tintaddr": "", "tintport": "", "udpipe": "", "rscript": "", "sessions" : []}')
        self.stupidwindows = False
        if platform.system() == "Windows":
            self.stupidwindows = True
        self.loadPersonalCFG()
        #TODO: Should we specify the session in the constructor?
        #self.txtloadingstopped()

    def changeLang(self, lang):
        self.language = lang
        print("Set language "+self.language)

    def setOnlyVisible(self, value):
        self.OnlyVisibleRows = value

    def setStart(self, value):
        self.daToken = value
        #print("Set start: " +str(value))

    def setEnd(self, value):
        self.aToken = value
        #print("Set end: " +str(value))

    def setAllTokens(self, value):
        self.allToken = value
        if value:
            self.setStart(0)
            self.setEnd(len(self.corpus))

    def setFilter(self, text):
        self.filter = text

    def loadPersonalCFG(self):
        try:
            text_file = open(self.mycfgfile, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
            self.mycfg = json.loads(lines.replace("\n", "").replace("\r", ""))
        except:
            try:
                text_file = open(self.mycfgfile, "r", encoding='ISO-8859-15')
                lines = text_file.read()
                text_file.close()
                self.mycfg = json.loads(lines.replace("\n", "").replace("\r", ""))
            except:
                print("Creo il file di configurazione")
        cfgtemplate = {'javapath': '', 'tintpath': '', 'tintaddr': '', '': '', 'sessions': [], 'udpipe': '', 'udpipemodels': {'ita': ''}, 'rscript': '', 'facebook': [], 'twitter': []}
        for key in cfgtemplate:
            if key not in self.mycfg:
                self.mycfg[key] = cfgtemplate[key]
                self.savePersonalCFG()

    def savePersonalCFG(self):
        cfgtxt = json.dumps(self.mycfg)
        text_file = open(self.mycfgfile, "w", encoding='utf-8')
        text_file.write(cfgtxt)
        text_file.close()

    def chiudiProgetto(self):
        self.sessionFile = ""
        self.sessionDir = "."
        self.corpus = []
        try:
            for row in range(self.corpuswidget.rowCount()):
                self.corpuswidget.removeRow(0)
                if row<100 or row%100==0:
                    QApplication.processEvents()
        except:
            print("Session closed")
        #self.setWindowTitle("Bran")

    def loadFromTint(self, tintaddr = "localhost"):
        self.TintAddr = tintaddr
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        if self.language == "ita":
            corpusID = "[ID]_[FILENAME],lang:ita,tagger:tint"
            corpusID = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus:", QLineEdit.Normal, corpusID)[0]
            self.copyOrigFiles(fileNames)

            # progrdialog
            recovery = self.sessionFile + "-TINT-importlog.tmp"
            totallines = 0
            self.core_killswitch = False
            self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
            self.Progrdialog.start()

            self.TCThread = tint.TintCorpus(self.corpuswidget, fileNames, self.corpuscols, self.TintAddr)
            self.TCThread.outputcsv = self.sessionFile
            self.TCThread.corpusIDpattern = corpusID
            self.TCThread.finished.connect(self.txtloadingstopped)
            self.TCThread.start()
        else:
            print("Tint funziona solo con la lingua italiana.")
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadFromUDpipe(self):
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        if self.language != "ita" and self.language != "eng":
            print("Language "+ self.language +" not supported")
            return

        udpipe = self.mycfg["udpipe"]
        model = self.mycfg["udpipemodels"][self.language]

        corpusID = "[ID]_[FILENAME],lang:ita,tagger:udpipe"
        corpusID = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus:", QLineEdit.Normal, corpusID)[0]
        self.copyOrigFiles(fileNames)

        # progrdialog
        recovery = self.sessionFile + "-UD-importlog.tmp"
        totallines = 0
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()

        # Run udpipe
        self.UDThread = UDCorpus(self.corpuswidget, fileNames, self.corpuscols, udpipe, model, self.language)
        self.UDThread.outputcsv = self.sessionFile
        self.UDThread.corpusIDpattern = corpusID
        self.UDThread.finished.connect(self.txtloadingstopped)
        self.UDThread.start()
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def core_paragraphscount(self, fileName):
        text_file = open(fileName, "r", encoding='utf-8')
        lines = text_file.read()
        text_file.close()
        itext = text.replace('.','. \n')
        itext = itext.replace('?','? \n')
        #merge phrases in paragraphs to optimize loading time for udpipe
        print("Lines before optimization: " + str(len(itext.split('\n'))))
        frasiInParagrafo = 50
        count = 0
        itext = itext.split('\n')
        ntext = []
        temp = ""
        for f in range(len(itext)):
            if count != frasiInParagrafo and f<(len(itext)-1):
                temp = temp + " " + itext[f]
                count = count + 1
            else:
                ntext.append(temp)
                count = 0
                temp = ""
        itext = ntext
        del ntext
        totallines = len(itext)
        return totallines

    def copyOrigFiles(self, fileNames):
        oldcount = 0
        mydir = os.path.dirname(self.sessionFile)
        if os.path.isdir(mydir):
            for tfile in os.listdir(mydir):
                print(tfile)
                if tfile.startswith(os.path.basename(self.sessionFile) + "-orig-"):
                    tmpcount = re.sub(".*\-orig\-(.*?)\-.*","\g<1>", tfile)
                    print(tmpcount)
                    try:
                        if int(tmpcount) > oldcount:
                            oldcount = int(tmpcount)
                    except:
                        continue
        oldcount = oldcount+1
        for fileName in fileNames:
            fileTitle = os.path.basename(fileName)
            dst = self.sessionFile + "-orig-" + str(oldcount) + "-" +re.sub("\..*?$","", fileTitle).replace("-","_") + ".txt"
            copyfile(fileName, dst)

    def loadTextFromCSV(self):
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv)")[0]
        if len(fileNames)<1:
            return
        return  #This function is not fully implemented
        sep = QInputDialog.getText(self.corpuswidget, "Scegli il separatore", "Indica il carattere che separa le colonne (\\t è la tabulazione):", QLineEdit.Normal, "\\t")[0]
        if sep == "\\t":
            sep = "\t"
        textID = QInputDialog.getInt(self.corpuswidget, "Scegli il testo", "Indica la colonna della tabella che contiene il testo di questo sottocorpus:")[0]
        corpusID = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus. Puoi usare [FILENAME] per indicare il nome del file e [COLONNA] per indicare la colonna da cui estrarre un tag.", QLineEdit.Normal, "[ID]_[FILENAME],[0],lang:ita,tagger:udpipe")[0]
        self.UDThread.corpusIDpattern = corpusID
        self.UDThread.csvTextcolumn = textID
        self.UDThread.csvSep = sep
        #if self.language == "ita":
        #    print("UDpipe still not supported")
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadjson(self):
        QMessageBox.information(self.corpuswidget, "Attenzione", "Caricare un file JSON non è più supportato.")

    def opentextfile(self, fileName):
        lines = ""
        try:
            text_file = open(fileName, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
        except:
            myencoding = "ISO-8859-15"
            #https://pypi.org/project/chardet/
            gotEncoding = False
            while gotEncoding == False:
                try:
                    myencoding = QInputDialog.getText(self.corpuswidget, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
                except:
                    print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
                    myencoding = [input()]
                try:
                    # TODO: prevediamo la codifica "FORCE", che permette di leggere il file come binario ignorando caratteri strani
                    text_file = open(fileName, "r", encoding=myencoding[0])
                    lines = text_file.read()
                    text_file.close()
                    gotEncoding = True
                except:
                    gotEncoding = False
        return lines

    def batch_textract(self, fileNames, append = False, lang = ""):
        try:
            import textract
        except:
            self.install_textract()
            import textract

        fulltext = ""
        for fileName in fileNames:
            try:
                mybytes = b''
                print("File: " + str(fileName))
                if ".gif" in fileName or ".jpg" in fileName or ".jpeg" in fileName or ".png" in fileName:
                    if lang == "":
                        print("Sembra che tu abbia selezionato un file immagine. Per estrarre il testo, verrà usato l'OCR: per favore, specifica la lingua del testo (es: ita, eng, deu)")
                        mylang = input()
                    else:
                        mylang = lang
                    mybytes = textract.process(fileName, language=mylang, method='tesseract', encoding='utf-8')
                else:
                    mybytes = textract.process(fileName, encoding='utf-8')
                mytext = mybytes.decode('utf-8')
                if append:
                    fulltext = fulltext + str(mytext)
                else:
                    text_file = open(str(fileName[0:fileName.rfind(".")])+".txt", "w", encoding='utf-8')
                    text_file.write(mytext)
                    text_file.close()
            except:
                print("Unable to extract file from "+str(fileName))
        if append:
            return fulltext

    def importfromTreeTagger(self):
        fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv *.txt)")[0]
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/treetagger-"+self.language+".json"
        try:
            text_file = open(filein, "r")
            myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
            text_file.close()
            legendaTT = json.loads(myjson)
        except:
            QMessageBox.warning(self.corpuswidget, "Errore", "Non riesco a leggere il dizionario di traduzione per TreeTagger.")
            return
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.ImportingFile = True
        for fileName in fileNames:
            totallines = 0
            try:
                if not os.path.getsize(fileName) > 0:
                    continue
                totallines = self.linescount(fileName)
            except:
                continue
            lines = self.opentextfile(fileName)
            trowN = 0
            for line in lines.split("\n"):
                if trowN<100 or trowN%100==0:
                    self.Progrdialog.w.testo.setText("Sto importando la riga numero "+str(trowN))
                    self.Progrdialog.w.progressBar.setValue(int((trowN/totallines)*100))
                    QApplication.processEvents()
                trowN = trowN + 1
                colN = 0
                if self.Progrdialog.w.annulla.isChecked():
                    self.Progrdialog.reject()
                    self.ImportingFile = False
                    return
                try:
                    cols = line.replace("\r", "").split("\t")
                    if cols[0] == "":
                        continue
                    tmpline = ['' for i in range(len(self.corpuscols))]  #Using list comprehension
                    tmpline[self.corpuscols["token"][0]] = str(cols[0])
                    tmpline[self.corpuscols["lemma"][0]] = str(cols[2])
                    try:
                        tmpline[self.corpuscols["pos"][0]] = legendaTT[str(cols[1])]
                    except:
                        tmpline[self.corpuscols["pos"][0]] = str(cols[1])
                    self.corpus.append(tmpline)
                except:
                    continue
        #self.updateCorpus(self.Progrdialog)
        self.Progrdialog.accept()
        self.sizeChanged.emit(len(self.corpus))
        self.updateCorpus()

    def loadCSV(self):
        if self.ImportingFile == False:
            fileNames = QFileDialog.getOpenFileNames(self.corpuswidget, "Apri file CSV", self.sessionDir, "File CSV (*.tsv *.txt *.csv)")[0]
            self.core_appendcorpus(fileNames)
            self.txtloadingstopped()

    def CSVloader(self, fileNames):
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    print(fileName)
                    if not os.path.getsize(fileName) > 0:
                        #break
                        self.ImportingFile = False
                        continue
                    #print("Importing")
                    try:
                        totallines = self.linescount(fileName)
                        #print(totallines)
                    except Exception as ex:
                        print(ex)
                        self.ImportingFile = False
                        continue
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    linesA = lines.split('\n')
                    maximum = self.daToken+len(linesA)-1
                    #print("Maximum: "+str(maximum))
                    for line in linesA:
                        if line == "":
                            continue
                        newtoken = line.split(self.separator)
                        if len(newtoken) < len(self.corpuscols):
                            for i in range(len(newtoken),len(self.corpuscols)):
                                newtoken.append("")
                        elif len(newtoken) > len(self.corpuscols):
                            newtoken = newtoken[0:len(self.corpuscols)]
                        self.corpus.append(newtoken)
        #print("Updating view")
        self.sizeChanged.emit(len(self.corpus))
        self.updateCorpus()
        self.ImportingFile = False

    def linescount(self, filename):
        f = open(filename, "r+", encoding='utf-8')
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    def txtloadingstopped(self):
        #Closing import progress dialog if it was running
        try:
            self.core_killswitch = False
            self.Progrdialog.cancelled = True
        except:
            pass
        print("Loading project")
        if self.sessionFile != "" and self.ImportingFile == False:
            if os.path.isfile(self.sessionFile):
                if not os.path.getsize(self.sessionFile) > 1:
                    return
            try:
                self.ImportingFile = True
                fileNames = ['']
                fileNames[0] = self.sessionFile
                self.corpus = []
                self.corpuswidget.setRowCount(0)
                print("Reading CSV")
                self.CSVloader(fileNames)
            except Exception as ex:
                print(ex)
                try:
                    self.myprogress.reject()
                    self.ImportingFile = False
                except:
                    self.ImportingFile = False
                    return

    def salvaProgetto(self):
        if self.sessionFile == "":
            fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
            if fileName != "":
                self.sessionFile = fileName
        if self.sessionFile != "":
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            self.CSVsaver(self.sessionFile, self.Progrdialog, False)

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.CSVsaver(fileName, self.Progrdialog, True)

    def CSVsaver(self, fileName, Progrdialog, addheader = False, onlyrows = []):
        self.sanitizeTable(self.corpuswidget)
        self.sanitizeCorpus()
        if fileName != "":
            if fileName[-4:] != ".csv" and fileName[-4:] != ".tsv":
                fileName = fileName + ".tsv"
            csv = ""
            if addheader:
                col = 0
                for key in self.corpuscols:
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.corpuscols[key][1]
                    col = col +1
                csv = csv + "\n"
            totallines = len(self.corpus)
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()
            if len(onlyrows)==0:
                onlyrows = range(totallines)
            for row in onlyrows:
                #csv = csv + "\n"
                csv = ""
                Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                for col in range(len(self.corpuscols)):
                    if Progrdialog.w.annulla.isChecked():
                        return
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.corpus[row][col]
                with open(fileName, "a", encoding='utf-8') as myfile:
                    myfile.write(csv+"\n")
            Progrdialog.accept()

    def connluexport(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.corpus_to_connlu(fileName, self.Progrdialog, True)

    def corpus_to_connlu(self, fileName, Progrdialog, addcomments = False, onlyrows = []):
        self.sanitizeTable(self.corpuswidget)
        self.sanitizeCorpus()
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/isdt-ud.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        legendaISDTUD = json.loads(myjson)
        if fileName != "":
            if fileName[-4:] != ".csv" and fileName[-4:] != ".tsv":
                fileName = fileName + ".tsv"
            csv = ""
            if addcomments:
                try:
                    csv = "# newdoc id = " + self.corpus[0][self.corpuscols['TAGcorpus'][0]]
                except:
                    csv = "# newdoc id = Corpus esportato da Bran"
                csv = csv + "\n# newpar"
            totallines = len(self.corpus)
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()
            if len(onlyrows)==0:
                onlyrows = range(totallines)
            oldphrase = ""
            for row in onlyrows:
                csv = ""
                Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if Progrdialog.w.annulla.isChecked():
                    return
                Ucolumns = []
                Ucolumns.append(self.corpus[row][self.corpuscols['IDword'][0]])
                Ucolumns.append(self.corpus[row][self.corpuscols['token'][0]])
                if "[PUNCT]" in self.corpus[row][self.corpuscols['lemma'][0]]:
                    Ucolumns.append(self.corpus[row][self.corpuscols['token'][0]])
                else:
                    Ucolumns.append(self.corpus[row][self.corpuscols['lemma'][0]])
                mypos = self.corpus[row][self.corpuscols['pos'][0]]
                myposU = legendaISDTUD["pos"][mypos][0]
                Ucolumns.append(myposU)
                Ucolumns.append(mypos)
                myfeat = self.corpus[row][self.corpuscols['feat'][0]]
                myfeatU = ""
                for featpart in myfeat.split("/"):
                    tmpfeat = ""
                    for featel in featpart.split("+"):
                        try:
                            translated = legendaISDTUD["feat"][featel]
                        except:
                            #print("IGNORED: "+featel)
                            translated = ""
                        for trelem in translated.split("|"):
                            if not trelem in tmpfeat:
                                tmpfeat = tmpfeat + "|" + trelem
                    myfeatU = myfeatU + tmpfeat + "/"
                #add from pos
                myfeatU = re.sub("^\|*", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                myfeatU = re.sub("[^a-z]*$", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                tmpmorf = legendaISDTUD["pos"][mypos][1].split("/")
                myfeatUtotal = ""
                for tmppart in range(len(myfeatU.split("/"))):
                    myfeatUtotal = myfeatUtotal + myfeatU.split("/")[tmppart]
                    try:
                        for tmpelem in tmpmorf[tmppart].split("|"):
                            if not tmpelem in myfeatU.split("/")[tmppart]:
                                myfeatUtotal = myfeatUtotal + "|" + tmpelem
                    except:
                        continue
                    myfeatUtotal = myfeatUtotal + "/"
                myfeatU = myfeatUtotal
                #clean double chars
                while "||" in myfeatU or "/|" in myfeatU:
                    myfeatU = myfeatU.replace("||","|")
                    myfeatU = myfeatU.replace("/|","/")
                myfeatU = re.sub("^[\|]*", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                myfeatU = re.sub("[^a-z]*$", "", myfeatU, flags=re.IGNORECASE|re.DOTALL)
                if myfeatU == "":
                    myfeatU = "_"
                Ucolumns.append(myfeatU)
                Ucolumns.append(self.corpus[row][self.corpuscols['head'][0]])
                Ucolumns.append(self.corpus[row][self.corpuscols['dep'][0]])
                Ucolumns.append("_")
                Ucolumns.append("_")
                #Ucolumns.append(self.corpuswidget.item(row,self.corpuscols['ner'][0]).text())

                #ricostruzione della frase
                if self.corpus[row][self.corpuscols['IDphrase'][0]] != oldphrase and addcomments:
                    oldphrase = self.corpus[row][self.corpuscols['IDphrase'][0]]
                    csv = csv + "\n# sent_id = " + str(int(self.corpus[row][self.corpuscols['IDphrase'][0]])+1) + "\n"
                    endrow = row
                    while self.corpus[row][self.corpuscols['IDphrase'][0]] == self.corpus[endrow][self.corpuscols['IDphrase'][0]] and endrow<(len(self.corpus)-1):
                        endrow = endrow +1
                    myignore = []
                    phraseText = self.rebuildText(self.corpus, self.Progrdialog, self.corpuscols['token'][0], myignore, row, endrow)
                    phraseText = self.remUselessSpaces(phraseText)
                    if phraseText[-1] == " ":
                        phraseText = phraseText[:-1]
                    csv = csv + "# text = " + phraseText + "\n"
                for col in range(len(Ucolumns)):
                    if Ucolumns[col] == "":
                        Ucolumns[col] = "_"
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + Ucolumns[col]
                with open(fileName, "a", encoding='utf-8') as myfile:
                    myfile.write(csv+"\n")
            Progrdialog.accept()

    def convertiDaTint(self):
        fileName = QFileDialog.getOpenFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        if not fileName == "":
            newName = fileName
            fileName = fileName.replace(".tsv","")+"-old.tsv"
            os.rename(newName,fileName)
            TestThread = tint.TintCorpus(self.corpuswidget, [], self.corpuscols, "localhost")
            if os.path.isfile(fileName):
                if not os.path.getsize(fileName) > 0:
                    return
                try:
                    totallines = self.linescount(fileName)
                    print(totallines)
                except Exception as ex:
                    print(ex)
                    return
                text_file = open(fileName, "r", encoding='utf-8')
                lines = text_file.read()
                text_file.close()
                linesA = lines.split('\n')
                for line in linesA:
                    if line == "":
                        continue
                    fullline = TestThread.isdt_to_ud(line)
                    with open(newName, "a", encoding='utf-8') as myfile:
                        myfile.write(fullline+"\n")

    def esportavistaCSV(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        toselect = []
        for row in range(self.corpuswidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.corpuswidget.isRowHidden(row):
                toselect.append(row)
        self.CSVsaver(fileName, self.Progrdialog, True, toselect)

    def esportafiltroCSV(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        toselect = []
        totallines = len(self.corpus)
        startline = 0
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.applicaFiltro(row, self.filtrimultiplienabled, self.filter):
                continue
            toselect.append(row)
        self.Progrdialog.accept()
        self.CSVsaver(fileName, self.Progrdialog, True, toselect)

    def esportaCSVperID(self):
        fileName = QFileDialog.getSaveFileName(self.corpuswidget, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        IDs = []
        col = self.corpuscols['TAGcorpus'][0]
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.corpus[row][col] in IDs:
                IDs.append(self.corpus[row][col])
        for i in range(len(IDs)):
            toselect = []
            for row in range(startline, totallines):
                self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if IDs[i] == self.corpus[row][col]:
                    toselect.append(row)
                    QApplication.processEvents()
            fileNameT = fileName + str(i).zfill(6) + ".tsv"
            self.CSVsaver(fileNameT, self.Progrdialog, True, toselect)


    def replaceCorpus(self):
        repCdialog = regex_replace.Form(self.corpuswidget)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.w.changeCase.show()
        repCdialog.exec()
        if repCdialog.result():
            if repCdialog.w.ignorecase.isChecked():
                myflags=re.IGNORECASE|re.DOTALL
            else:
                myflags=re.DOTALL
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            totallines = len(self.corpus)
            startline = 0
            if self.OnlyVisibleRows:
                totallines = self.aToken
                startline = self.daToken
            for row in range(startline, totallines):
                self.Progrdialog.w.testo.setText("Sto cercando nella riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row-startline):
                        continue
                for col in range(len(self.corpus[row])):
                    if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                        origstr = self.corpus[row][col]
                        newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=myflags)
                        if repCdialog.w.dolower.isChecked():
                            indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                            for f in indexes:
                                newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                        if repCdialog.w.doupper.isChecked():
                            indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                            for f in indexes:
                                newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                        #self.setcelltocorpus(newstr, row, col)
                        self.corpus[row][col] = newstr
            self.Progrdialog.accept()
            self.updateCorpus()

    def replaceCells(self):
        repCdialog = regex_replace.Form(self.corpuswidget)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.w.changeCase.show()
        repCdialog.exec()
        if repCdialog.result():
            if repCdialog.w.ignorecase.isChecked():
                myflags=re.IGNORECASE|re.DOTALL
            else:
                myflags=re.DOTALL
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            startline = self.daToken
            totallines = len(self.corpuswidget.selectedItems())
            for i in range(len(self.corpuswidget.selectedItems())):
                row = self.corpuswidget.selectedItems()[i].row()
                col = self.corpuswidget.selectedItems()[i].column()
                self.Progrdialog.w.testo.setText("Sto cercando nella cella numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                    origstr = self.corpus[startline+row][col]
                    newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=myflags)
                    if repCdialog.w.dolower.isChecked():
                        indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                        for f in indexes:
                            newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                    if repCdialog.w.doupper.isChecked():
                        indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                        for f in indexes:
                            newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                    self.corpus[startline+row][col] = newstr
            self.Progrdialog.accept()
            self.updateCorpus()

    def selectVisibleCells(self):
        self.deselectAllCells()
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        for row in range(self.corpuswidget.rowCount()):
            if self.OnlyVisibleRows and self.corpuswidget.isRowHidden(row):
                continue
            if row<100 or row%100==0:
                self.Progrdialog.w.testo.setText("Sto selezionando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisrow = QTableWidgetSelectionRange(row,0,row,self.corpuswidget.columnCount()-1)
            self.corpuswidget.setRangeSelected(thisrow, True)
        self.Progrdialog.accept()

    def deselectAllCells(self):
        self.corpuswidget.clearSelection()

    def showResults(self, output, fromProjectTree = False):
        #filemtime = int(os.path.getmtime(output))
        #now = int(datetime.datetime.now().timestamp())
        #if self.stupidwindows and 30>(now-filemtime) and not fromProjectTree:
        if self.stupidwindows and not fromProjectTree:
            print("Su Windows non puoi visualizzare una tabella subito dopo averla creata: devi aspettare un minuto per dare al sistema il tempo di finire di scrivere sul disco. Clicca su Visualizza/File del progetto e prova a aprire il file tra un minuto.")
            return
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        lineI = 0
        with open(output, "r", encoding='utf-8') as ins:
            for line in ins:
                colI = 0
                for col in line.replace("\n","").replace("\r","").split(self.separator):
                    if lineI == 0:
                        TBdialog.addcolumn(col, colI)
                    else:
                        if colI == 0:
                            TBdialog.addlinetotable(col, 0)
                        else:
                            TBdialog.setcelltotable(col, lineI-1, colI)
                    colI = colI +1
                lineI = lineI +1
        TBdialog.show()

    def contaoccorrenze(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        mycol = thisname.index(column[0])
        myrecovery = False
        hname = str(mycol)
        hkey = str(mycol)
        for key in self.corpuscols:
            if mycol == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        output = self.sessionFile + "-occorrenze-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_calcola_occorrenze(mycol, myrecovery)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def contaoccorrenzefiltrate(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        QMessageBox.information(self.corpuswidget, "Filtro", "Ora devi impostare i filtri con cui dividere i risultati. I vari filtri devono essere separati da condizioni OR, per ciascuno di essi verrà creata una colonna a parte nella tabella dei risultati.")
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText("pos=AD.*||pos=NOUN")
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() == "":
            return
        filtertext = Fildialog.w.filter.text()
        #allfilters = filtertext.split("||")
        mycol = thisname.index(column[0])
        myrecovery = False
        hname = str(mycol)
        hkey = str(mycol)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        cleanedfilter = re.sub("[^a-zA-Z0-9]", "", filtertext)
        fcol = self.filtrimultiplienabled
        output = self.sessionFile + "-occorrenze_filtrate-" + hkey + "-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_occorrenzeFiltrate(mycol, filtertext, myrecovery)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def contapersone(self):
        thisname = []
        #0 Tutto
        #1 solo persona numero e genere
        #2 solo persona e numero
        #3 solo numero genere e determinato
        #4 solo genere
        #5 solo numero
        thisname.append("Tutto")
        thisname.append("Persona, numero, e genere")
        thisname.append("Persona e numero")
        thisname.append("Numero, genere, e determinatezza")
        thisname.append("Genere")
        thisname.append("Numero")
        column = QInputDialog.getItem(self.corpuswidget, "Scegli il livello", "Che livello di dettaglio vuoi?",thisname,current=0,editable=False)
        level = thisname.index(column[0])
        myrecovery = False
        try:
            mylevel = int(level)
        except:
            mylevel = 2
        QMessageBox.information(self.corpuswidget, "Filtro", "Ora puoi indicare un filtro per selezionare cercare solo alcuni tipi di parole. Per esempio, con il filtro pos=DET&&feat=.*Definite=Def.* verranno selezionati solo gli articoli determinativi. Se lasci il filtro vuoto, verranno analizzate tutte le parole del corpus.")
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText("")
        #Definite=Def|Gender=Masc|Number=Plur|PronType=Art
        Fildialog.updateTable()
        Fildialog.exec()
        filtertext = Fildialog.w.filter.text()
        if filtertext == "":
            filtertext = "pos=.*"
        mycol = thisname.index(column[0])
        myrecovery = False
        cleanedfilter = re.sub("[^a-zA-Z0-9]", "", filtertext)
        fcol = self.filtrimultiplienabled
        output = self.sessionFile + "-contapersone-"+str(cleanedfilter)+"-"+str(mylevel)+".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_contapersone(filtertext, mylevel, myrecovery)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def coOccorrenze(self):
        parola = QInputDialog.getText(self.corpuswidget, "Scegli la parola", "Indica la parola che vuoi cercare:", QLineEdit.Normal, "")[0]
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "In quale colonna devo cercare il testo?",thisname,current=1,editable=False)
        mycol = thisname.index(column[0])
        myrange = int(QInputDialog.getInt(self.corpuswidget, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        myfilter = str(list(self.corpuscols)[mycol]) +"="+parola
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(myfilter) #"lemma=essere&&pos[1,-1]=SP||lemma[-1]=essere&&pos=S"
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = self.ignorepos
        else:
            myignore = []
        filtertext = Fildialog.w.filter.text()
        myrecovery = False
        hname = str(mycol)
        hkey = str(mycol)
        for key in self.corpuscols:
            if mycol == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        cleanedfilter = re.sub("[^a-zA-Z0-9]", "", filtertext)
        fcol = self.filtrimultiplienabled
        output = self.sessionFile + "-coOccorrenze-" + hkey + "-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_calcola_coOccorrenze(parola, mycol, myrange, True, myrecovery, filtertext)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def concordanze(self):
        parola = QInputDialog.getText(self.corpuswidget, "Scegli la parola", "Indica la parola che vuoi cercare:", QLineEdit.Normal, "")[0]
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "In quale colonna devo cercare il testo?",thisname,current=1,editable=False)
        mycol = thisname.index(column[0])
        myrange = int(QInputDialog.getInt(self.corpuswidget, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        myfilter = str(list(self.corpuscols)[mycol]) +"="+parola
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(myfilter) #"lemma=essere&&pos[1,-1]=SP||lemma[-1]=essere&&pos=S"
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = self.ignorepos
        else:
            myignore = []
        filtertext = Fildialog.w.filter.text()
        myrecovery = False
        hname = str(mycol)
        hkey = str(mycol)
        for key in self.corpuscols:
            if mycol == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        cleanedfilter = re.sub("[^a-zA-Z0-9]", "", filtertext)
        fcol = self.filtrimultiplienabled
        output = self.sessionFile + "-concordanze-" + hkey + "-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_calcola_concordanze(parola, mycol, myrange, True, myrecovery, filtertext)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def occorrenzenormalizzate(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Se vuoi estrarre il dizionario devi cercare nella colonna dei lemmi. Ma puoi anche scegliere di ottenere le statistiche su altre colonne, come la Forma grafica.",thisname,current=self.corpuscols['token'][0],editable=False)
        mycol = thisname.index(column[0])
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        doignorepunct = False
        if ret == QMessageBox.Yes:
            doignorepunct = True
        myrecovery = False
        hname = str(mycol)
        hkey = str(mycol)
        for key in self.corpuscols:
            if mycol == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        output = self.sessionFile + "-occorrenze_normalizzate-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_occorrenze_normalizzate(mycol, myrecovery, doignorepunct)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def orderVerbMorf(self, text, ignoreperson = False):
        if not "VerbForm" in text:
            return text
        mytext = ""
        #Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin
        vform = ""
        mood = ""
        tense = ""
        pers = ""
        num = ""
        gender = ""
        for el in text.split("|"):
            if "VerbForm" in el:
                vform = re.sub(".*VerbForm\=(.*)","\g<1>",el)
            if "Mood" in el:
                mood = re.sub(".*Mood\=(.*)","\g<1>",el)
            if "Tense" in el:
                tense = re.sub(".*Tense\=(.*)","\g<1>",el)
            if "Person" in el:
                pers = re.sub(".*Person\=(.*)","\g<1>",el)
            if "Number" in el:
                num = re.sub(".*Number\=(.*)","\g<1>",el)
            if "Gender" in el:
                gender = re.sub(".*Gender\=(.*)","\g<1>",el)
        mytext = "VerbForm=" + vform
        if mood != "":
            mytext = mytext + "|Mood=" + mood
        if tense != "":
            mytext = mytext + "|Tense=" + tense
        if pers != "" and ignoreperson==False:
            mytext = mytext + "|Person=" + pers
        if num != "" and ignoreperson==False:
            mytext = mytext + "|Number=" + num
        if gender != "" and ignoreperson==False:
            mytext = mytext + "|Gender=" + gender
        return mytext

    def contaverbi(self):
        ignoreperson = False
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare persona, numero, genere, e caratteristica clitica dei verbi?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            ignoreperson = True
        contigui = False
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi che i verbi composti siano sempre contigui (es: \"è anche stato\" non è contiguo)?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            contigui = True
        myrecovery = False
        output = self.sessionFile + "-contaverbi.tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_contaverbi(ignoreperson, contigui, myrecovery)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def trovaripetizioni(self):
        Repetdialog = ripetizioni.Form(self.corpuswidget)
        Repetdialog.loadipos(self.ignorepos)
        Repetdialog.loadallpos(self.legendaPos)
        self.enumeratecolumns(Repetdialog.w.colonna)
        Repetdialog.w.colonna.setCurrentIndex(self.corpuscols['token'][0])
        Repetdialog.exec()
        if Repetdialog.result():
            tokenda = Repetdialog.w.tokenda.value()
            tokena = Repetdialog.w.tokena.value()
            minoccur = Repetdialog.w.minoccurr.value()
            ignorecase = Repetdialog.w.ignorecase.isChecked()
            remspaces = bool(Repetdialog.w.remspaces.isChecked() and not Repetdialog.w.sigindex.isChecked())
            col = Repetdialog.w.colonna.currentIndex()
            ipunct = []
            for i in range(Repetdialog.w.ignorapos.count()):
                ipunct.append(Repetdialog.w.ignorapos.item(i).text())
            vuoteI = []
            if Repetdialog.w.ignoreI.isChecked():
                for i in range(Repetdialog.w.vuoteI.count()):
                    vuoteI.append(Repetdialog.w.vuoteI.item(i).text())
            vuoteF = []
            if Repetdialog.w.ignoreF.isChecked():
                for i in range(Repetdialog.w.vuoteF.count()):
                    vuoteF.append(Repetdialog.w.vuoteF.item(i).text())
            charNotWord = Repetdialog.w.charNotWord.isChecked()
            TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
            TBdialog.sessionDir = self.sessionDir
            TBdialog.addcolumn("nGram", 0)
            TBdialog.addcolumn("Occorrenze", 1)
            TBdialog.addcolumn("Parole piene", 2)
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            for tokens in range(tokenda, tokena+1):
                self.findngrams(tokens, minoccur, TBdialog, self.Progrdialog, ignorecase, remspaces, ipunct, col, vuoteI, vuoteF, charNotWord)
            if Repetdialog.w.sigindex.isChecked():
                TBdialog.addcolumn("Significatività assoluta", 3)
                TBdialog.addcolumn("Significatività relativa", 4)
                for row in range(TBdialog.w.tableWidget.rowCount()):
                    totallines = TBdialog.w.tableWidget.rowCount()
                    self.Progrdialog.w.testo.setText("Sto calcolando la significatività nella riga "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    sigass = 0.0
                    sigrel = 0.0
                    tmpstring = TBdialog.w.tableWidget.item(row,0).text()
                    Fseg = int(TBdialog.w.tableWidget.item(row,1).text())*1.0
                    sommatoria = 0.0
                    tmplist = tmpstring.split(" ")
                    for tmpword in tmplist:
                        # Controlliamo self.OnlyVisibleRows e facciamo un subset solo con le righe visibili?
                        crpitems = self.findItemsInColumn(self.corpus, tmpword, col)
                        lencrpitems = len(crpitems)
                        #lencrpitems = 0
                        #for crpitem in crpitems:
                        #    lencrpitems = lencrpitems +1
                        Fw = len(crpitems)*1.0
                        if Fw!=0:
                            sommatoria = sommatoria + (Fseg/Fw)
                    sigass = sommatoria * int(TBdialog.w.tableWidget.item(row,2).text())*1.0
                    ampiezza = len(tmplist) + 1
                    sigrel = (sigass*1.0)/(ampiezza*ampiezza)
                    TBdialog.setcelltotable(str(sigass), row, 3)
                    TBdialog.setcelltotable(str(sigrel), row, 4)
            if Repetdialog.w.remspaces.isChecked():
                for row in range(TBdialog.w.tableWidget.rowCount()):
                    totallines = TBdialog.w.tableWidget.rowCount()
                    self.Progrdialog.w.testo.setText("Sto pulendo gli spazi nella riga "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    tmpstring = TBdialog.w.tableWidget.item(row,0).text()
                    tmpstring = self.remUselessSpaces(tmpstring)
                    TBdialog.setcelltotable(tmpstring, row, 0)
            self.Progrdialog.accept()
            TBdialog.show()

    def ricostruisciTesto(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Su quale colonna devo ricostruire il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        #self.Progrdialog = progress.Form()
        #self.Progrdialog.show()
        #mycorpus = self.rebuildText(self.corpus, self.Progrdialog, col)
        #mycorpus = self.remUselessSpaces(mycorpus)
        #self.Progrdialog.accept()
        myfilter = ""
        usehtml = False
        ret = QMessageBox.question(self.corpuswidget,'Plain text o HTML', "Il testo può essere ricostruito come plain text oppure come html. Vuoi ricostruirlo come html?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            usehtml = True
        outfile = self.core_ricostruisci(self.corpus, col, [], 0, 0, myfilter, False, usehtml)
        te = textviewer.TextViewer(self.corpuswidget, self.mycfg)
        te.loadfile(outfile, usehtml)
        te.show()

    def rebuildText(self, table, Progrdialog, col = "", ipunct = [], startrow = 0, endrow = 0, filtercol = None):
        mycorpus = ""
        if col == "":
            col = self.corpuscols['token'][0]
        totallines = len(table)
        if endrow == 0:
            endrow = totallines
        for row in range(startrow, endrow):
            ftext = self.filter
            if filtercol != None:
                if self.OnlyVisibleRows and not self.applicaFiltro(row, filtercol, ftext, table):
                    continue
            Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if Progrdialog.w.annulla.isChecked():
                return
            if row >= 0 and row < len(table):
                thispos = self.legendaPos[table[row][self.corpuscols['pos'][0]]][0]
                if not thispos in ipunct:
                    mycorpus = mycorpus + table[row][col] + " "
        return mycorpus

    def remUselessSpaces(self, tempstring, usehtml = False):
        if usehtml:
            punt = " (<.*>["+re.escape(".,;!?)")+ "]<.*>)"
            tmpstring = re.sub(punt, "\g<1>", tempstring, flags=re.IGNORECASE)
            punt = "(<.*>["+re.escape("'’(")+ "]<.*>) "
            tmpstring = re.sub(punt, "\g<1>", tmpstring, flags=re.IGNORECASE|re.DOTALL)
        else:
            punt = " (["+re.escape(".,;!?)")+ "])"
            tmpstring = re.sub(punt, "\g<1>", tempstring, flags=re.IGNORECASE)
            punt = "(["+re.escape("'’(")+ "]) "
            tmpstring = re.sub(punt, "\g<1>", tmpstring, flags=re.IGNORECASE|re.DOTALL)
        return tmpstring

    def findngrams(self, tokens, minoccur, TBdialog, Progrdialog, ignorecase, remspaces, ipunct, col, vuoteI, vuoteF, charNotWord= False):
        mycorpus = self.rebuildText(self.corpus, Progrdialog, col, ipunct)
        if ignorecase:
            mycorpus = mycorpus.lower()
        searchthis = " "
        active = True
        pos = 0
        totallines = len(mycorpus)
        while active:
            wpos = pos
            npos = pos
            Progrdialog.w.testo.setText("Sto conteggiando il carattere numero "+str(pos))
            Progrdialog.w.progressBar.setValue(int((pos/totallines)*100))
            QApplication.processEvents()
            if Progrdialog.w.annulla.isChecked():
                return
            if not charNotWord:
                #read a specific number of words
                for i in range(tokens):
                    wpos = mycorpus.find(searchthis, npos+1)
                    if wpos > 0:
                        npos = wpos
            else:
                npos = pos+tokens
            #check if we reached someway the end of text
            if npos > len(mycorpus)-1:
                if pos > len(mycorpus)-1:
                    break
                else:
                    npos = len(mycorpus)-1
            #read this phrase
            tmpstring = mycorpus[pos:npos]
            parolai = re.sub(" .*", "", tmpstring, flags=re.IGNORECASE|re.DOTALL)
            parolaf = re.sub(".* ", "", tmpstring, flags=re.IGNORECASE|re.DOTALL)
            #look for all occurrences of this phrase
            if not charNotWord:
                wnIsRight = bool(tmpstring.count(searchthis)==tokens-1)
            else:
                wnIsRight = bool(len(tmpstring)==tokens)
            if tmpstring != "" and wnIsRight and bool(not parolai in vuoteI) and bool(not parolaf in vuoteF):
                tcount = mycorpus.count(tmpstring)
                if tcount >= minoccur:
                    tbrow = TBdialog.finditemincolumn(tmpstring, col=0, matchexactly = True, escape = True)
                    if tbrow<=0:
                        TBdialog.addlinetotable(tmpstring, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable(str(tcount), tbrow, 1)
                        ppcount = 0
                        tmplist = tmpstring.split(" ")
                        for tmpword in tmplist:
                            mycol = col
                            if ignorecase:
                                myfl = re.IGNORECASE|re.DOTALL
                            else:
                                myfl=re.DOTALL
                            tmprow = self.finditemincolumn(tmpword, col=mycol, matchexactly = True, escape = True, myflags=myfl)
                            if tmprow<0:
                                #print("Parola non riconosciuta: "+tmpword)
                                ppcount = ppcount + 1
                            else:
                                posword = self.corpus[tmprow][self.corpuscols['pos'][0]]
                                for key in self.legendaPos:
                                    if posword == self.legendaPos[key][0] or posword == key:
                                        if "piene" == self.legendaPos[key][2]:
                                            ppcount = ppcount + 1
                                            break
                                        if "vuote" == self.legendaPos[key][2]:
                                            break
                        TBdialog.setcelltotable(str(ppcount), tbrow, 2)
                #newtext = nth_replace(mycorpus, tmpstring, "", 2, "all right")
                #text = newtext
            if not charNotWord:
                pos = mycorpus.find(searchthis, pos+1)+1 #continue from next word
            else:
                pos = pos+1
            if pos <= 0:
                pos = len(mycorpus)


    def translatePos(self):
        col = self.corpuscols['pos'][0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto lavorando sulla riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.corpus[row][col]
            except:
                thistext = ""
            try:
                newtext = self.legendaPos[thistext][0]
            except:
                newtext = thistext
            self.corpus[row][col] = newtext
            #self.corpuswidget.item(row,col).setToolTip(newtext)
        self.Progrdialog.accept()
        self.updateCorpus()

    def densitalessico(self):
        col = self.corpuscols['pos'][0]
        thisname = []
        thisname.append("Dettagliato")
        thisname.append("Macrocategorie")
        thisname.append("Parole piene e vuote")
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Che livello di dettaglio vuoi?",thisname,current=2,editable=False)
        level = thisname.index(column[0])
        myrecovery = False
        try:
            mylevel = int(level)
        except:
            mylevel = 2
        output = self.sessionFile + "-densitalessicale-" + str(mylevel) + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_densitalessico(mylevel, myrecovery)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def delselected(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpuswidget.selectedItems())
        toselect = []
        for i in range(len(self.corpuswidget.selectedItems())):
            row = self.corpuswidget.selectedItems()[i].row()
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(i))
            self.Progrdialog.w.progressBar.setValue(int((i/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            toselect.append(row)
        totallines = len(toselect)
        startline = self.daToken
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.corpuswidget.removeRow(toselect[row-1])
            del self.corpus[startline+toselect[row-1]]

        self.Progrdialog.accept()
        self.sizeChanged.emit(len(self.corpus))

    def enumeratecolumns(self, combo):
        for col in range(self.corpuswidget.columnCount()):
            thisname = self.corpuswidget.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def finditemincolumn(self, mytext, col=0, matchexactly = True, escape = True, myflags=0):
        myregex = mytext
        if escape:
            myregex = re.escape(myregex)
        if matchexactly:
            myregex = "^" + myregex + "$"
        for row in range(len(self.corpus)):
            try:
                if bool(re.match(myregex, self.corpus[row][col], flags=myflags)):
                    return row
            except:
                continue
        return -1

    def findItemsInColumn(self, table, value, col):
        mylist = [row[col] for row in table if row[col]==value]
        return mylist

    def applicaFiltro(self, row, col, filtro, table = None):
        res = False
        if col != self.filtrimultiplienabled:
            try:
                if table == None:
                    ctext = self.corpus[row][col]
                else:
                    ctext = table[row][col]
            except:
                print("Unable to find row " +str(row) + " col "+ str(col))
                return False
            ftext = filtro
            if bool(re.match(ftext, ctext)):
                res = True
            else:
                res = False
        else:
            for option in filtro.split("||"):
                for andcond in option.split("&&"):
                    res = False
                    operators = [">=", "<=", "=", ">", "<"] #l'ordine è importante
                    for operator in operators:
                        if operator in andcond:
                            break
                    if operator != "=":
                        #Looking for number
                        cellname = andcond.split(operator, 1)[0]
                        try:
                            fnum = float(andcond.split(operator, 1)[1])
                        except:
                            continue
                        colname = cellname.split("[")[0]
                        col = self.corpuscols[colname][0]
                        rowlist = [0]
                        if "[" in cellname.replace("]",""):
                            tmprowliststr = cellname.replace("]","").split("[")[1]
                            if "," in tmprowliststr:
                                rowlist = tmprowliststr.split(",")
                            elif ":" in tmprowliststr:
                                rowlist = list(range(tmprowliststr.split(":")[0],tmprowliststr.split(":")[1]))
                                if len(rowlist)==0:
                                    rowlist = list(range(tmprowliststr.split(":")[0],tmprowliststr.split(":")[1], -1))
                            else:
                                rowlist = [int(tmprowliststr)]
                        if len(rowlist)==0:
                            rowlist = [0]
                        for rowp in rowlist:
                            tmprow = row + int(rowp)
                            try:
                                if table == None:
                                    ctext = self.corpus[tmprow][col]
                                else:
                                    ctext = table[tmprow][col]
                            except:
                                ctext = ""
                            try:
                                cnum = float(ctext)
                                #print(str(fnum)+"|"+str(cnum))
                            except:
                                continue
                            try:
                                if cnum >= fnum and operator == ">=":
                                    res = True
                                    break
                                elif cnum <= fnum and operator == "<=":
                                    res = True
                                    break
                                elif cnum > fnum and operator == ">":
                                    res = True
                                    break
                                elif cnum < fnum and operator == "<":
                                    res = True
                                    break
                                else:
                                    res = False
                                    break
                            except:
                                print("Error in numeric formula")
                                pass
                    else:
                        #Looking for regex
                        cellname = andcond.split(operator, 1)[0]
                        try:
                            ftext = andcond.split(operator, 1)[1]
                        except:
                            continue
                        colname = cellname.split("[")[0]
                        col = self.corpuscols[colname][0]
                        rowlist = [0]
                        if "[" in cellname.replace("]",""):
                            tmprowliststr = cellname.replace("]","").split("[")[1]
                            if "," in tmprowliststr:
                                rowlist = tmprowliststr.split(",")
                            elif ":" in tmprowliststr:
                                rowlist = list(range(tmprowliststr.split(":")[0],tmprowliststr.split(":")[1]))
                                if len(rowlist)==0:
                                    rowlist = list(range(tmprowliststr.split(":")[0],tmprowliststr.split(":")[1], -1))
                            elif "F" in tmprowliststr:              #Fino alla fine della frase
                                searchforphaseEnd = True
                                epCounter = 0
                                IDptextOLD = IDptext = self.corpus[row][self.corpuscols["IDphrase"][0]]
                                while searchforphaseEnd:
                                    epCounter = epCounter + 1
                                    try:
                                        if table == None:
                                            IDptext = self.corpus[row+epCounter][self.corpuscols["IDphrase"][0]]
                                        else:
                                            IDptext = table[row+epCounter][self.corpuscols["IDphrase"][0]]
                                        if IDptext != IDptextOLD:
                                            epCounter = epCounter + 1
                                            searchforphaseEnd = False
                                    except:
                                        searchforphaseEnd = False
                                    rowlist = list(range(0,epCounter))
                            elif "I" in tmprowliststr:     #Fino all'inizio della frase
                                searchforphaseEnd = True
                                epCounter = 0
                                IDptextOLD = IDptext = self.corpus[row][self.corpuscols["IDphrase"][0]]
                                while searchforphaseEnd:
                                    epCounter = epCounter - 1
                                    try:
                                        if table == None:
                                            IDptext = self.corpus[row+epCounter][self.corpuscols["IDphrase"][0]]
                                        else:
                                            IDptext = table[row+epCounter][self.corpuscols["IDphrase"][0]]
                                        if IDptext != IDptextOLD:
                                            epCounter = epCounter - 1
                                            searchforphaseEnd = False
                                    except:
                                        searchforphaseEnd = False
                                    rowlist = list(range(0,epCounter, -1))
                            else:
                                rowlist = [int(tmprowliststr)]
                        if len(rowlist)==0:
                            rowlist = [0]
                        for rowp in rowlist:
                            tmprow = row + int(rowp)
                            try:
                                if table == None:
                                    ctext = self.corpus[tmprow][col]
                                else:
                                    ctext = table[tmprow][col]
                            except:
                                ctext = ""
                            try:
                                if bool(re.match(ftext, ctext)):
                                    res = True
                                    break
                            except:
                                print("Error in regex")
                                pass
                    if res == False:
                        break
                if res == True:
                    break
            #if res:
            #    print(cnum)
        return res

    def filtriMultipli(self):
        #fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(self.filter)
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()

    def actionNumero_dipendenze_per_frase(self):
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        col = self.corpuscols["dep"][0]
        Fildialog.filterColElements(self.corpuscols["IDphrase"][0])
        Fildialog.updateFilter()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        allfilters = Fildialog.w.filter.text().split("||")
        TBdialog = tableeditor.Form(self.corpuswidget, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Dependency", 0)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        for myfilter in allfilters:
            TBdialog.addcolumn(myfilter, 1)
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.corpus[row][col]
                try:
                    if col == self.corpuscols["pos"][0]:
                        thistext = self.legendaPos[thistext][0]
                except:
                    thistext = self.corpus[row][col]
            except:
                thistext = ""
            for ifilter in range(len(allfilters)):
                if self.applicaFiltro(row, fcol, allfilters[ifilter]):
                    tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        try:
                            tbval = int(TBdialog.w.tableWidget.item(tbrow,ifilter+1).text())+1
                        except:
                            tbval = 1
                        TBdialog.setcelltotable(str(tbval), tbrow, ifilter+1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable("1", tbrow, ifilter+1)
        self.Progrdialog.accept()
        TBdialog.show()

    def addTagFromFilter(self):
        QMessageBox.information(self.corpuswidget, "Istruzioni", "Crea il filtro per selezionare gli elementi a cui vuoi aggiungere un tag.")
        fcol = self.filtrimultiplienabled
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.filter = Fildialog.w.filter.text()
        nuovotag = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag che vuoi aggiungere alle parole che rispettano il filtro:", QLineEdit.Normal, "")[0]
        repCdialog = regex_replace.Form(self.corpuswidget)
        repCdialog.setModal(False)
        repCdialog.w.orig.setText("(.*)")
        repCdialog.w.dest.setText("\g<1>, "+nuovotag)
        repCdialog.w.changeCase.show()
        repCdialog.w.colcheck.hide()
        repCdialog.w.colcombo.hide()
        repCdialog.w.lbl_in.hide()
        repCdialog.exec()
        if repCdialog.result():
            if repCdialog.w.ignorecase.isChecked():
                myflags=re.IGNORECASE|re.DOTALL
            else:
                myflags=re.DOTALL
        else:
            return
        col = self.corpuscols['TAGcorpus'][0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            startline = self.daToken
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto modificando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if self.applicaFiltro(row, fcol, self.filter):
                origstr = self.corpus[row][col]
                newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=myflags)
                if repCdialog.w.dolower.isChecked():
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                    for f in indexes:
                        newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].lower() + newstr[f[1]:]
                if repCdialog.w.doupper.isChecked():
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer(repCdialog.w.orig.text(), newstr, flags=myflags)]
                    for f in indexes:
                        newstr = newstr[0:f[0]] + newstr[f[0]:f[1]].upper() + newstr[f[1]:]
                self.corpus[row][col] = newstr
        self.Progrdialog.accept()
        self.updateCorpus()

    def removevisiblerows(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        startline = self.daToken
        toselect = []
        for row in range(self.corpuswidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.corpuswidget.isRowHidden(row):
                toselect.append(row)
        totallines = len(toselect)
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.corpuswidget.removeRow(toselect[row-1])
            del self.corpus[startline+toselect[row-1]]
        self.Progrdialog.accept()
        self.sizeChanged.emit(len(self.corpus))

    def cancelfiltro(self):
        for row in range(self.corpuswidget.rowCount()):
            self.corpuswidget.setRowHidden(row, False)



    def corpusCellChanged(self, row, col):
        if self.ImportingFile:
            return
        try:
            startline = self.daToken
            self.corpus[row+startline][col] = self.corpuswidget.item(row,col).text()
        except:
            print("Error editing cell")
            self.updateCorpus()

    def updateCorpus(self):
        try:
            tempccount = self.corpuswidget.columnCount()
        except:
            print("Running in cli, ignore table widget")
            return
        Progrdialog = progress.Form() #self.Progrdialog = progress.Form()
        Progrdialog.show() #self.Progrdialog.show()
        # Clear table before adding new lines
        self.corpuswidget.setRowCount(0)
        starting = self.daToken
        maximum = self.aToken
        #print(starting)
        #print(maximum)
        if self.allToken:
            starting = 0
            maximum = len(self.corpus)
        if maximum > len(self.corpus):
            maximum = len(self.corpus)
        if starting < 0:
            starting = 0
        totallines = maximum-starting
        print("Showing lines: "+str(totallines))
        if totallines < 0:
            print("daToken need to be smaller than aToken")
            return
        for rowN in range(starting,maximum):
            Progrdialog.w.testo.setText("Sto importando la riga numero "+str(rowN))
            Progrdialog.w.progressBar.setValue(int((rowN/totallines)*100))
            if rowN<100 or rowN%100==0:
                QApplication.processEvents()
            colN = 0
            line = self.corpus[rowN]
            for colN in range(len(line)):
                if Progrdialog.w.annulla.isChecked():
                    rowN = 0
                    Progrdialog.reject()
                    self.ImportingFile = False
                    return
                if colN == 0:
                    if line[colN] == "":
                        break
                    TBrow = self.addlinetocorpus(str(line[colN]), 0) #self.corpuscols["TAGcorpus"][0]
                self.setcelltocorpus(str(line[colN]), TBrow, colN)

    def visualizzafrasi(self):
        alberofrasidialog = alberofrasi.Form(self)
        alberofrasidialog.exec()

    def runServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self.corpuswidget, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            self.TintThread = tint.TintRunner(self.TintSetdialog.w)
            self.TintThread.loadvariables(self.Java, self.TintDir, self.TintPort)
            self.TintThread.dataReceived.connect(lambda data: self.runServer(bool(data)))
            self.alreadyChecked = True
            self.TintThread.start()
        else:
            if platform.system() == "Windows":
                QMessageBox.information(self.corpuswidget, "Come usare il server su Windows", "Sembra che tu stia usando Windows. Su questo sistema, per utilizzare il server Tint l'interfaccia di Bran verrà chiusa automaticamente: il terminale dovrà rimanere aperto. Dovrai aprire di nuovo Bran, così verrà caricata una nuova interfaccia grafica.")
                print("\nNON CHIUDERE QUESTA FINESTRA:  Tint è eseguito dentro questa finestra. Avvia di nuovo Bran.")
                print("\n\nNON CHIUDERE QUESTA FINESTRA")
                sys.exit(0)

    def checkServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self.corpuswidget, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            QApplication.processEvents()
            self.TestThread = tint.TintCorpus(self.corpuswidget, [], self.corpuscols, self.TintAddr)
            self.TestThread.dataReceived.connect(lambda data: self.checkServer(bool(data)))
            self.alreadyChecked = True
            self.TestThread.start()
            #while self.TestThread.isRunning():
            #    time.sleep(10)
            self.TintSetdialog.w.loglist.addItem("Sto cercando il server")
        else:
            self.TintSetdialog.accept()

    def addlinetocorpus(self, text, column):
        #self.corpuswidget.cellChanged.disconnect(self.corpusCellChanged)
        row = self.corpuswidget.rowCount()
        self.corpuswidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.corpuswidget.setItem(row, column, titem)
        self.corpuswidget.setCurrentCell(row, column)
        #self.corpuswidget.cellChanged.connect(self.corpusCellChanged)
        return row

    def setcelltocorpus(self, text, row, column):
        #self.corpuswidget.cellChanged.disconnect(self.corpusCellChanged)
        titem = QTableWidgetItem()
        titem.setText(text)
        if column == self.corpuscols["pos"][0]:
            try:
                newtext = self.legendaPos[text][0]
                titem.setToolTip(newtext)
            except:
                newtext = text
        self.corpuswidget.setItem(row, column, titem)
        #self.corpuswidget.cellChanged.connect(self.corpusCellChanged)

    def sanitizeTable(self, table):
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                if not table.item(row,col):
                    self.setcelltocorpus("", row, col)

    def sanitizeCorpus(self):
        for row in range(len(self.corpus)):
            for col in range(len(self.corpuscols)):
                try:
                    self.corpus[row][col] = str(self.corpus[row][col])
                except:
                    self.corpus[row][col] = ""

    def texteditor(self):
        te = texteditor.TextEditor(self.corpuswidget, self.mycfg)
        te.show()

    def confronto(self):
        cf = confronto.Confronto(self.corpuswidget, self.mycfg, self.sessionDir, self.corpuscols)
        cf.legendaPos = self.legendaPos
        cf.ignoretext = self.ignoretext
        cf.dimList = self.dimList
        cf.show()

    #def aboutbran(self):
    #    aw = about.Form(self.corpuswidget)
    #    aw.exec()

    def getCorpusDim(self, thistotal):
        dimCorpus = self.dimList[0]
        for i in range(len(self.dimList)-1):
            if self.dimList[i] <= thistotal and self.dimList[i+1] >= thistotal:
                lower = thistotal - self.dimList[i]
                upper = self.dimList[i+1] - thistotal
                if lower < upper:
                    dimCorpus = self.dimList[i]
                else:
                    dimCorpus = self.dimList[i+1]
        return dimCorpus

    def misure_lessicometriche(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self.corpuswidget, "Scegli la colonna", "Se vuoi estrarre il dizionario devi cercare nella colonna dei lemmi. Ma puoi anche scegliere di ottenere le statistiche su altre colonne, come la Forma grafica.",thisname,current=self.corpuscols['token'][0],editable=False)
        mycol = thisname.index(column[0])
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        doignorepunct = False
        if ret == QMessageBox.Yes:
            doignorepunct = True
        myrecovery = False
        hname = str(mycol)
        hkey = str(mycol)
        for key in self.corpuscols:
            if mycol == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        output = self.sessionFile + "-misure_lessicometriche-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_misure_lessicometriche(mycol, myrecovery, doignorepunct)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output

    def gulpease(self):
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self.corpuswidget)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText("IDphrase>0&&IDphrase<3")
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() == "":
            return
        myfilter = Fildialog.w.filter.text()
        print(myfilter)
        ret = QMessageBox.question(self.corpuswidget,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        doignorepunct = False
        if ret == QMessageBox.Yes:
            doignorepunct = True
        myrecovery = False
        hkey = re.sub("[^a-zA-Z0-9]", "_", myfilter)
        output = self.sessionFile + "-gulpease-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = self.core_linescount(self.sessionFile)
        self.core_killswitch = False
        self.Progrdialog = progress.ProgressDialog(self, recovery, totallines)
        self.Progrdialog.start()
        self.core_gulpease(myrecovery, myfilter, doignorepunct)
        self.Progrdialog.cancelled = True
        self.core_killswitch = False
        if not self.stupidwindows:
            self.showResults(output)
        return output


    ####################################################################################################################
    #CORE FUNCTIONS
    ####################################################################################################################




    def core_findintable(self, table, stringa, col=0):
        resrow = -1
        for row in range(len(table)):
            if table[row][col] == stringa:
                resrow = row
                break
        return resrow

    def core_finditemincolumn(self, table, mytext, col=0, matchexactly = True, escape = True, myflags=0):
        myregex = mytext
        if escape:
            myregex = re.escape(myregex)
        if matchexactly:
            myregex = "^" + myregex + "$"
        for row in range(len(table)):
            try:
                if bool(re.match(myregex, table[row][col], flags=myflags)):
                    return row
            except:
                continue
        return -1

    def core_linescount(self, filename):
        f = open(filename, "r+", encoding='utf-8')
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    def core_savetable(self, table, output):
        tabletext = ""
        for row in table:
            coln = 0
            for col in row:
                if coln > 0:
                    tabletext = tabletext + '\t'
                tabletext = tabletext + str(col)
                coln = coln + 1
            tabletext = tabletext + "\n"
        #safe writing
        permission = False
        first_run = True
        while not permission:
            try:
                file = open(output,"w", encoding='utf-8')
                file.write(tabletext)
                file.close()
                permission = True
            except:
                if first_run:
                    print("Waiting for permission to write file "+ output + "...")
                    first_run = False
                permission = False
        return permission

    def core_savetext(self, mytext, output):
        #safe writing
        permission = False
        first_run = True
        while not permission:
            try:
                file = open(output,"w", encoding='utf-8')
                file.write(mytext)
                file.close()
                permission = True
            except:
                if first_run:
                    print("Waiting for permission to write file "+ output + "...")
                    first_run = False
                permission = False
        return permission

    def core_fileappend(self, line, output):
        permission = False
        first_run = True
        while not permission:
            try:
                with open(output, "a", encoding='utf-8') as rowfile:
                    rowfile.write(line)
                permission = True
            except:
                if first_run:
                    print("Waiting for permission to write file "+ output + "...")
                    first_run = False
                permission = False
        return permission

    def core_calcola_occorrenze(self, mycol, myrecovery = False):
        fileName = self.sessionFile
        table = []
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        output = fileName + "-occorrenze-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append([hname,"Occorrenze"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                try:
                    thistext = self.corpus[row][col]
                except:
                    thistext = ""
                tbrow = self.core_findintable(table, thistext, 0)
                if tbrow>=0:
                    tbval = int(table[tbrow][1])+1
                    table[tbrow][1] = tbval
                else:
                    newrow = [thistext, "1"]
                    table.append(newrow)
                if row % 500 == 0:
                    self.core_savetable(table, output)
                    self.core_fileappend(str(row)+"\n", recovery)
                    #with open(recovery, "a", encoding='utf-8') as rowfile:
                    #    rowfile.write(str(row)+"\n")
            row = row + 1
        self.core_savetable(table, output)
        #with open(recovery, "a", encoding='utf-8') as rowfile:
        #    rowfile.write(str(row)+"\n")
        self.core_fileappend(str(row)+"\n", recovery)
        return output

    def core_occorrenzeFiltrate(self, mycol, filtertext = "", myrecovery = False):
        if filtertext=="":
            self.core_calcola_occorrenze(mycol, myrecovery)
            return
        allfilters = filtertext.split("||")
        fileName = self.sessionFile
        table = []
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", filtertext)
        fcol = self.filtrimultiplienabled
        output = fileName + "-occorrenze_filtrate-" + hkey + "-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            headerlist = [hname]
            for myfilter in allfilters:
                headerlist.append(myfilter)
            table.append(headerlist)
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                try:
                    thistext = self.corpus[row][col]
                    try:
                        if col == self.corpuscols["pos"][0]:
                            thistext = self.legendaPos[thistext][0]
                    except:
                        thistext = self.corpus[row][col]
                except:
                    thistext = ""
                for ifilter in range(len(allfilters)):
                    if self.applicaFiltro(row, fcol, allfilters[ifilter]):
                        tbrow = self.core_finditemincolumn(table, thistext, col=0, matchexactly = True, escape = True)
                        if tbrow>=0:
                            try:
                                tbval = int(table[tbrow][ifilter+1])+1
                            except:
                                tbval = 1
                            table[tbrow][ifilter+1] = tbval
                        else:
                            newrow = [thistext]
                            for emptyI in range(0,len(allfilters)):
                                newrow.append("")
                            newrow[ifilter+1] = "1"
                            table.append(newrow)
                if row % 500 == 0:
                    self.core_savetable(table, output)
                    self.core_fileappend(str(row)+"\n", recovery)
                    #with open(recovery, "a", encoding='utf-8') as rowfile:
                    #    rowfile.write(str(row)+"\n")
            row = row + 1
        self.core_savetable(table, output)
        #with open(recovery, "a", encoding='utf-8') as rowfile:
        #    rowfile.write(str(row)+"\n")
        self.core_fileappend(str(row)+"\n", recovery)
        return output

    def core_cercaConFiltro(self, mycol, filtertext, myrecovery = False):
        allfilters = filtertext.split("||")
        fileName = self.sessionFile
        table = []
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key

        max_lookahead = 0
        max_lookbehind = 0
        for m in re.finditer("\[\-([0-9]*)\]", filtertext):
            try:
                tmp_la = int(m.group(1))
            except:
                continue
            if tmp_la > max_lookbehind:
                max_lookbehind = tmp_la
        for m in re.finditer("\[([^\-][0-9]*)\]", filtertext):
            try:
                tmp_la = int(m.group(1))
            except:
                continue
            if tmp_la > max_lookahead:
                max_lookahead = tmp_la

        cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", filtertext)
        fcol = self.filtrimultiplienabled
        output = fileName + "-cerca-" + hkey + "-filtro-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            headerlist = [hname, "start", "end"]
            table.append(headerlist)
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                try:
                    thistext = self.corpus[row][col]
                    try:
                        if col == self.corpuscols["pos"][0]:
                            thistext = self.legendaPos[thistext][0]
                    except:
                        thistext = self.corpus[row][col]
                except:
                    thistext = ""
                for ifilter in range(len(allfilters)):
                    if self.applicaFiltro(row, fcol, allfilters[ifilter]):
                        tbrow = self.core_finditemincolumn(table, thistext, col=0, matchexactly = True, escape = True)
                        matchstart = row - max_lookbehind
                        matchend = row + max_lookahead
                        fullmatchtext = ""
                        for imatchr in range(matchstart,matchend+1):
                            try:
                                fullmatchtext += self.corpus[imatchr][col]
                                if col == self.corpuscols["pos"][0]:
                                    thistext = self.legendaPos[thistext][0]
                                fullmatchtext += " "
                            except:
                                pass
                        newrow = [fullmatchtext]
                        newrow.append(matchstart)
                        newrow.append(matchend)
                        table.append(newrow)
                if row % 500 == 0:
                    self.core_savetable(table, output)
                    self.core_fileappend(str(row)+"\n", recovery)
                    #with open(recovery, "a", encoding='utf-8') as rowfile:
                    #    rowfile.write(str(row)+"\n")
            row = row + 1
        self.core_savetable(table, output)
        #with open(recovery, "a", encoding='utf-8') as rowfile:
        #    rowfile.write(str(row)+"\n")
        self.core_fileappend(str(row)+"\n", recovery)
        return output

    def core_rebuildText(self, table, col = "", ipunct = [], startrow = 0, endrow = 0, filtercol = None, usehtml = False):
        mycorpus = ""
        if col == "":
            col = self.corpuscols['token'][0]
        totallines = len(table)
        if endrow == 0:
            endrow = totallines
        for row in range(startrow, endrow):
            ftext = self.filter
            if filtercol != None:
                if self.OnlyVisibleRows and not self.applicaFiltro(row, filtercol, ftext, table):
                    continue
            if row >= 0 and row < len(table):
                thispos = self.legendaPos[table[row][self.corpuscols['pos'][0]]][0]
                if not thispos in ipunct:
                    if usehtml:
                        wordid = table[row][self.corpuscols['IDphrase'][0]]+"-"+table[row][self.corpuscols['IDword'][0]]
                        mycorpus = mycorpus + '<span id="'+wordid+'" name="'+wordid+'" >' + table[row][col] +'</span> '
                    else:
                        mycorpus = mycorpus + table[row][col] + " "
        return mycorpus

    def core_ricostruisci(self, table, col = "", ipunct = [], startrow = 0, endrow = 0, myfilter = "", myrecovery = False, usehtml = False):
        self.filter = myfilter
        fileName = self.sessionFile
        oldvisrow = self.OnlyVisibleRows
        myfilcol = None
        if myfilter != "":
            myfilcol = self.filtrimultiplienabled
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", myfilter)
        output = fileName + "-ricostruito-" + hkey + "-"+ cleanedfilter
        if usehtml:
            output = output + ".html"
        else:
            output = output + ".txt"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        if endrow != 0:
            totallines = endrow
        startatrow = 0
        print(fileName + " -> " + output)
        fulltext = ""
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                primafrase = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        fulltext = fulltext + line
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            primafrase = 0
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        frasi = []
        frasecol = self.corpuscols["IDphrase"][0]
        for row in range(startatrow, totallines):
            phID = self.corpus[row][frasecol]
            if len(frasi)==0:
                frasi.append([phID,row,row+1])
                continue
            if phID != frasi[-1][0]:
                frasi[-1][2] = row
                frasi.append([phID,row,row])
        frasi[-1][2] = totallines
        if myfilter != "":
            myfilcol = self.filtrimultiplienabled
            self.OnlyVisibleRows = True
        for nFrase in range(primafrase, len(frasi)):
            startrow = frasi[nFrase][1]
            endrow = frasi[nFrase][2]
            if self.core_killswitch:
                break
            tmptext = self.core_rebuildText(self.corpus, col, ipunct, startrow, endrow, myfilcol, usehtml)
            tmptext = self.remUselessSpaces(tmptext, usehtml)
            if usehtml:
                phraseid = frasi[nFrase][0]
                fulltext = fulltext + '<span id="'+phraseid+'" name="'+phraseid+'" >' + tmptext +'</span> '
            else:
                fulltext = fulltext + tmptext
            if nFrase % 10 == 0:
                self.core_savetext(fulltext, output)
                self.core_fileappend(str(frasi[nFrase][0])+"\n", recovery)
        self.core_savetext(fulltext, output)
        self.core_fileappend(str(frasi[nFrase][0])+"\n", recovery)
        self.OnlyVisibleRows = oldvisrow
        return output

    def core_calcola_coOccorrenze(self, parola, mycol, myrange, ignorepunct, myrecovery = False, myfilter = ""):
        fileName = self.sessionFile
        table = []
        myignore = ""
        if ignorepunct:
            myignore = self.ignorepos
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        if myfilter == "":
            myfilter = str(list(self.corpuscols)[col]) +"="+parola
        cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", myfilter)
        fcol = self.filtrimultiplienabled
        output = fileName + "-coOccorrenze-" + hkey + "-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        concordanze = []
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                ftext = myfilter #self.filter
                if not self.applicaFiltro(row, fcol, ftext):
                    continue
                thistext = self.core_rebuildText(self.corpus, col, myignore, row-myrange, row+myrange+1)
                #thistext = self.remUselessSpaces(thistext)
                regex = re.escape('.?!')
                if bool(re.match(".*["+regex+"].*", thistext)):
                    punctindex = [m.start(1) for m in re.finditer("(["+regex+"])", thistext, flags=re.DOTALL)]
                    if punctindex[0] < thistext.index(parola):
                        thistext = thistext[punctindex[0]+1:]
                    else:
                        thistext = thistext[0:punctindex[0]]
                if thistext != "":
                    concordanze.append(thistext)
                    table.append([thistext])
                if row % 500 == 0:
                    self.core_savetable(table, output)
                self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        table = []
        table.append(["Segmento","Occorrenze"])
        totallines = len(concordanze)
        for row in range(totallines):
            if self.core_killswitch:
                break
            thisrow = concordanze[row].split(" ")
            for word in thisrow:
                thistext = ""
                if thisrow.index(word) < thisrow.index(parola):
                    thistext = str(word) + "..." + str(parola)
                if thisrow.index(word) > thisrow.index(parola):
                    thistext = str(parola) + "..." + str(word)
                if thistext != "":
                    tbrow = self.core_finditemincolumn(table, thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
        self.core_savetable(table, output)
        return output

    def core_calcola_concordanze(self, parola, mycol, myrange, ignorepunct, myrecovery = False, myfilter = ""):
        fileName = self.sessionFile
        table = []
        myignore = ""
        if ignorepunct:
            myignore = self.ignorepos
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        if myfilter == "":
            myfilter = str(list(self.corpuscols)[col]) +"="+parola
        cleanedfilter = re.sub("[^a-zA-Z0-9\[\]]", "", myfilter)
        fcol = self.filtrimultiplienabled
        output = fileName + "-concordanze-" + hkey + "-" + cleanedfilter + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append(["Segmento","Occorrenze"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                ftext = myfilter #self.filter
                if not self.applicaFiltro(row, fcol, ftext):
                    continue
                thistext = self.core_rebuildText(self.corpus, col, myignore, row-myrange, row+myrange+1)
                thistext = self.remUselessSpaces(thistext)
                if thistext != "":
                    tbrow = self.core_finditemincolumn(table, thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                if row % 500 == 0:
                    self.core_savetable(table, output)
                self.core_fileappend(str(row)+"\n", recovery)
        self.core_savetable(table, output)
        self.core_fileappend(str(row)+"\n", recovery)
        return output

    def core_orderVerbMorf(self, text, ignoreperson = False):
        if not "VerbForm" in text:
            return text
        mytext = ""
        #Mood=Ind|Number=Plur|Person=3|Tense=Pres|VerbForm=Fin
        vform = ""
        mood = ""
        tense = ""
        pers = ""
        num = ""
        gender = ""
        for el in text.split("|"):
            if "VerbForm" in el:
                vform = re.sub(".*VerbForm\=(.*)","\g<1>",el)
            if "Mood" in el:
                mood = re.sub(".*Mood\=(.*)","\g<1>",el)
            if "Tense" in el:
                tense = re.sub(".*Tense\=(.*)","\g<1>",el)
            if "Person" in el:
                pers = re.sub(".*Person\=(.*)","\g<1>",el)
            if "Number" in el:
                num = re.sub(".*Number\=(.*)","\g<1>",el)
            if "Gender" in el:
                gender = re.sub(".*Gender\=(.*)","\g<1>",el)
        mytext = "VerbForm=" + vform
        if mood != "":
            mytext = mytext + "|Mood=" + mood
        if tense != "":
            mytext = mytext + "|Tense=" + tense
        if pers != "" and ignoreperson==False:
            mytext = mytext + "|Person=" + pers
        if num != "" and ignoreperson==False:
            mytext = mytext + "|Number=" + num
        if gender != "" and ignoreperson==False:
            mytext = mytext + "|Gender=" + gender
        return mytext

    def core_contaverbi(self, ignoreperson = True, contigui = False, myrecovery = False):
        debug = False
        poscol = self.corpuscols["pos"][0] #thisname.index(column[0])
        morfcol = self.corpuscols["feat"][0]
        frasecol = self.corpuscols["IDphrase"][0]
        lemmacol = self.corpuscols["lemma"][0]
        fileName = self.sessionFile
        table = []
        output = fileName + "-contaverbi.tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append(["Modo+Tempo", "Occorrenze", "Percentuali"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                try:
                    thispos = self.legendaPos[self.corpus[row][poscol]][0]
                    thisphrase = self.corpus[row][frasecol]
                    thislemma = self.corpus[row][lemmacol]
                except:
                    thispos = ""
                    thisphrase = "0"
                    thislemma = ""
                thistext = ""
                thistext2 = ""
                thistext3 = ""
                #Filtro per trovare i verbi a 3 come "è stato fatto": feat=.*VerbForm.*Part.*&&feat[1]=.*VerbForm.*Part.*||feat=.*VerbForm.*Part.*&&feat[-1]=.*VerbForm.*Part.*||feat=.*VerbForm.*&&feat[1]=.*VerbForm.*Part.*&&feat[2]=.*VerbForm.*Part.*
                if "verbo" in thispos:
                    thistext = self.corpus[row][morfcol]
                try:
                    if (debug):
                        mydbg = self.corpus[row][1]
                except:
                    pass
                if "avere" in thislemma or "essere" in thislemma:
                    for ind in range(1,4): #range(1,3):
                        try:
                            tmpos = self.legendaPos[self.corpus[row+ind][poscol]][0]
                            tmpphrase = self.corpus[row+ind][frasecol]
                        except:
                            tmpos = ""
                            tmpphrase = "0"
                        #i verbi consecutivi vanno bene finché sono nella stessa frase
                        if tmpphrase != thisphrase:
                            break
                        if "verbo" in tmpos:
                            thistext2 = thistext2 + self.corpus[row+ind][morfcol] + "+"
                            try:
                                if (debug):
                                    mydbg = mydbg + " " + self.corpus[row+ind][1]
                            except:
                                pass
                            startline = row+ind+1
                        elif contigui=="y" or contigui=="Y":
                            break
                    if len(thistext2.split("+"))>1:
                        thistext3 = thistext2.split("+")[1]
                        thistext2 = thistext2.split("+")[0]
                if len(thistext) >= 3:
                    thistext = self.core_orderVerbMorf(thistext, ignoreperson) + "+"
                if len(thistext2) >= 3:
                    thistext2 = self.core_orderVerbMorf(thistext2, ignoreperson) + "+"
                if len(thistext3) >= 3:
                    thistext3 = self.core_orderVerbMorf(thistext3, ignoreperson) #+ "+"
                if thistext != "":
                    thistext = thistext + thistext2 + thistext3
                    if ignoreperson:
                        thistext = thistext.replace("/Clitic=Yes", "")
                if thistext.endswith("+"):
                    thistext = thistext[0:-1]
                if thistext != "":
                    tbrow = self.core_findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                        try:
                            if (debug):
                                print([thistext,mydbg])
                        except:
                            pass
            if row % 500 == 0 or row == len(self.corpus)-1:
                self.core_savetable(table, output)
                #with open(recovery, "a", encoding='utf-8') as rowfile:
                #    rowfile.write(str(row)+"\n")
                self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        #calcolo le percentuali
        totallines = len(table)
        verbitotali = 0
        for row in range(1,len(table)):
            try:
                tval = int(table[row][1])
            except:
                tval = 0
            verbitotali = verbitotali + tval
        for row in range(len(table)):
            try:
                ratio = (float(table[row][1])/float(verbitotali)*100)
                ratios = f'{ratio:.3f}'
            except:
                ratios = table[row][1]
            if len(table[row])>2:
                table[row][2] = ratios
            else:
                table[row].append(ratios)
        self.core_savetable(table, output)
        return output

    def core_contapersone(self, filter = "", level = 0, myrecovery = False):
        debug = False
        poscol = self.corpuscols["pos"][0] #thisname.index(column[0])
        morfcol = self.corpuscols["feat"][0]
        frasecol = self.corpuscols["IDphrase"][0]
        lemmacol = self.corpuscols["lemma"][0]
        fileName = self.sessionFile
        try:
            mylevel = int(level)
            if mylevel <0 or mylevel >6:
                mylevel = 0/0
        except:
            mylevel = 0
        if filter == "":
            myfilter = "pos=.*" #"pos=.*VERB.*||pos=.*AUX.*||pos=.*ADJ.*||pos=.*NOUN.*||pos=.*DET.*"
        else:
            myfilter = filter
        table = []
        cleanedfilter = re.sub("[^a-zA-Z0-9]", "", myfilter)
        output = fileName + "-contapersone-"+str(cleanedfilter)+"-"+str(mylevel)+".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append(["Modo+Tempo", "Occorrenze", "Percentuali"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                #TODO: sicuro che non dobbiamo considerare i verbi composti come "è stato fatto" come una unica entità?
                if not self.applicaFiltro(row, self.filtrimultiplienabled, myfilter):
                    continue
                thismorf = self.corpus[row][morfcol]
                try:
                    if (debug):
                        mydbg = self.corpus[row][1]
                except:
                    pass
                persona = ""
                numero = ""
                genere = ""
                determinato = ""
                clitico = ""
                for thispart in thismorf.split("/"):
                    for el in thispart.split("|"):
                        if "Person" in el:
                            persona = el
                        if "Number" in el:
                            numero = el
                        if "Gender" in el:
                            genere = el
                        if "Definite" in el:
                            determinato = el
                        if "Clitic" in el:
                            clitico = el
                #Livelli di dettaglio:
                #0 Tutto
                #1 solo persona numero e genere
                #2 solo persona e numero
                #3 solo numero genere e determinato
                #4 solo genere
                #5 solo numero
                thistext = ""
                if mylevel == 0 or mylevel == 1 or mylevel == 2:
                    thistext = persona
                if mylevel == 0 or mylevel == 1 or mylevel == 2 or mylevel == 3 or mylevel == 5:
                    if len(thistext) > 0 and numero != "":
                        thistext = thistext + "|"
                    thistext = thistext + numero
                if mylevel == 0 or mylevel == 1 or mylevel == 3 or mylevel == 4:
                    if len(thistext) > 0 and genere != "":
                        thistext = thistext + "|"
                    thistext = thistext + genere
                if mylevel == 0 or mylevel == 3:
                    if len(thistext) > 0 and determinato != "":
                        thistext = thistext + "|"
                    thistext = thistext + determinato
                if mylevel == 0:
                    if len(thistext) > 0 and clitico != "":
                        thistext = thistext + "|"
                    thistext = thistext + clitico
                #Gender=Masc|Number=Sing|Tense=Past|VerbForm=Part
                #Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin
                #Gender=Masc|Number=Plur
                #_/Definite=Def|Gender=Masc|Number=Plur|PronType=Art
                #Clitic=Yes|Person=3|PronType=Prs
                if thistext != "":
                    tbrow = self.core_findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                        try:
                            if (debug):
                                print([thistext,mydbg])
                        except:
                            pass
            if row % 500 == 0 or row == len(self.corpus)-1:
                self.core_savetable(table, output)
                #with open(recovery, "a", encoding='utf-8') as rowfile:
                #    rowfile.write(str(row)+"\n")
                self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        #calcolo le percentuali
        totallines = len(table)
        verbitotali = 0
        for row in range(1,len(table)):
            try:
                tval = int(table[row][1])
            except:
                tval = 0
            verbitotali = verbitotali + tval
        for row in range(len(table)):
            try:
                ratio = (float(table[row][1])/float(verbitotali)*100)
                ratios = f'{ratio:.3f}'
            except:
                ratios = table[row][1]
            if len(table[row])>2:
                table[row][2] = ratios
            else:
                table[row].append(ratios)
        self.core_savetable(table, output)
        return output

    def core_occorrenze_normalizzate(self, mycol, myrecovery, doignorepunct = True):
        fileName = self.sessionFile
        table = []
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        output = fileName + "-occorrenze_normalizzate-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append([hname,"Occorrenze", "Frequenza in parole", "Ordine (log10) della frequenza"]) #L'ordine di grandezza è log10(occorrenzeParola/occorrenzeTotali)
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        totaltypes = 0
        mytypes = {}
        #if startatrow >= (len(self.corpus)-1):
        #    return
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                thisposc = "False"
                try:
                    thistext = self.corpus[row][col]
                    if self.ignoretext != "" and doignorepunct:
                        thistext = re.sub(self.ignoretext, "", thistext)
                except:
                    thistext = ""
                if thistext != "":
                    tbrow = self.core_findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                        totaltypes = totaltypes + 1
                    if row % 500 == 0 or row == len(self.corpus)-1:
                        self.core_savetable(table, output)
                        #with open(recovery, "a", encoding='utf-8') as rowfile:
                        #    rowfile.write(str(row)+"\n")
                        self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        hapax = 0
        classifrequenza = []
        occClassifrequenza = []
        totallines = len(table)
        paroletotali = 0
        for row in range(len(table)):
            try:
                if int(table[row][1]) == 1:
                    hapax = hapax + 1
            except:
                continue
            if table[row][1] in classifrequenza:
                ind = classifrequenza.index(table[row][1])
                occClassifrequenza[ind] = occClassifrequenza[ind] + 1
            else:
                classifrequenza.append(table[row][1])
                occClassifrequenza.append(1)
            paroletotali = paroletotali + int(table[row][1])
        dimCorpus = self.dimList[0]
        for i in range(len(self.dimList)-1):
            if self.dimList[i] <= paroletotali and self.dimList[i+1] >= paroletotali:
                lower = paroletotali - self.dimList[i]
                upper = self.dimList[i+1] - paroletotali
                if lower < upper:
                    dimCorpus = self.dimList[i]
                else:
                    dimCorpus = self.dimList[i+1]
        for row in range(len(table)):
            thistext = table[row][0]
            try:
                ratio = (float(table[row][1])/float(paroletotali)*dimCorpus)
            except:
                continue
            ratios = f'{ratio:.3f}'
            table[row].append(str(ratios))
            ratio = math.log10(float(table[row][1])/float(paroletotali))
            ratios = f'{ratio:.3f}'
            table[row].append(str(ratios))
        table[0][2] = "Frequenza in " + str(dimCorpus) + " parole"
        self.core_savetable(table, output)
        return output

    def core_misure_lessicometriche(self, mycol, myrecovery, doignorepunct = True):
        fileName = self.sessionFile
        table = []
        try:
            col = int(mycol)
        except:
            col = 0
        hname = str(col)
        hkey = str(col)
        for key in self.corpuscols:
            if col == self.corpuscols[key][0]:
                hname = self.corpuscols[key][1]
                hkey = key
        output = fileName + "-misure_lessicometriche-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append([hname,"Occorrenze", "Frequenza in parole", "Ordine di grandezza (log10)"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        totaltypes = 0
        mytypes = {}
        #if startatrow >= (len(self.corpus)-1):
        #    return
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                thisposc = "False"
                try:
                    thistext = self.corpus[row][col]
                    if self.ignoretext != "" and doignorepunct:
                        thistext = re.sub(self.ignoretext, "", thistext)
                except:
                    thistext = ""
                if thistext != "":
                    tbrow = self.core_findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                        totaltypes = totaltypes + 1
                    if row % 500 == 0 or row == len(self.corpus)-1:
                        self.core_savetable(table, output)
                        #with open(recovery, "a", encoding='utf-8') as rowfile:
                        #    rowfile.write(str(row)+"\n")
                        self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        hapax = 0
        classifrequenza = []
        occClassifrequenza = []
        totallines = len(table)
        paroletotali = 0
        for row in range(len(table)):
            try:
                if int(table[row][1]) == 1:
                    hapax = hapax + 1
            except:
                continue
            if table[row][1] in classifrequenza:
                ind = classifrequenza.index(table[row][1])
                occClassifrequenza[ind] = occClassifrequenza[ind] + 1
            else:
                classifrequenza.append(table[row][1])
                occClassifrequenza.append(1)
            paroletotali = paroletotali + int(table[row][1])
        dimCorpus = self.dimList[0]
        for i in range(len(self.dimList)-1):
            if self.dimList[i] <= paroletotali and self.dimList[i+1] >= paroletotali:
                lower = paroletotali - self.dimList[i]
                upper = self.dimList[i+1] - paroletotali
                if lower < upper:
                    dimCorpus = self.dimList[i]
                else:
                    dimCorpus = self.dimList[i+1]
        for row in range(len(table)):
            thistext = table[row][0]
            try:
                ratio = (float(table[row][1])/float(paroletotali)*dimCorpus)
            except:
                continue
            ratios = f'{ratio:.3f}'
            table[row].append(str(ratios))
            ratio = math.log10(float(table[row][1])/float(paroletotali))
            ratios = f'{ratio:.3f}'
            table[row].append(str(ratios))
        table = []
        table.append(["Misura lessicometrica", "Valore"])
        table.append(["Tokens", str(paroletotali)])
        table.append(["Types", str(totaltypes)])
        ratio = (float(totaltypes)/float(paroletotali))*100.0
        ratios = f'{ratio:.3f}'
        table.append(["(Types/Tokens)*100", str(ratios)])
        ratio = (float(paroletotali)/float(totaltypes))
        ratios = f'{ratio:.3f}'
        table.append(["Tokens/Types", str(ratios)])
        table.append(["Hapax", str(hapax)])
        ratio = (float(hapax)/float(paroletotali))*100.0
        ratios = f'{ratio:.3f}'
        table.append(["(Hapax/Tokens)*100", str(ratios)])
        ratio = float(totaltypes)/float(math.sqrt(paroletotali))
        ratios = f'{ratio:.3f}'
        table.append(["Types/sqrt(Tokens)", str(ratios)])
        ratio = (float(math.log10(totaltypes))/float(math.log10(paroletotali)))
        ratios = f'{ratio:.3f}'
        table.append(["log(Types)/log(Tokens)", str(ratios)])
        YuleSum = 0
        for cfi in range(len(classifrequenza)):
            YuleSum = YuleSum + ( math.pow(int(classifrequenza[cfi]),2) * occClassifrequenza[cfi] )
        ratio = float(math.pow(10,4)) * ((float(YuleSum) - float(paroletotali))/ float(math.pow(paroletotali, 2)) )
        ratios = f'{ratio:.3f}'
        table.append(["Caratteristica di Yule (K)", str(ratios)])
        ratio = math.pow(float(paroletotali), (1.0/math.pow(float(totaltypes), 0.172)))
        ratios = f'{ratio:.3f}'
        table.append(["W", str(ratios)])
        ratio =  math.pow(float(math.log10(paroletotali)), 2.0)/(float(math.log10(paroletotali)) - float(math.log10(totaltypes)) )
        ratios = f'{ratio:.3f}'
        table.append(["U", str(ratios)])
        self.core_savetable(table, output)
        return output

    def core_densitalessico(self, level = 2, myrecovery = False):
        fileName = self.sessionFile
        col = self.corpuscols['pos'][0]
        table = []
        try:
            mylevel = int(level)
        except:
            mylevel = 2
        output = fileName + "-densitalessicale-" + str(mylevel) + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append(["Categoria", "Occorrenze", "Percentuale"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        totaltypes = 0
        mytypes = {}
        #if startatrow >= (len(self.corpus)-1):
        #    return
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                try:
                    thistextO = self.corpus[row][col]
                    thistext = self.legendaPos[thistextO][0]
                    thisposc = self.legendaPos[self.corpus[row][self.corpuscols['pos'][0]]][1]
                    try:
                        mytypes[thisposc] = mytypes[thisposc] +1
                    except:
                        mytypes[thisposc] = 1
                except:
                    thistext = ""
                    thistextO = ""
                if thistext != "":
                    tbrow = self.core_finditemincolumn(table, thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1", "0"]
                        table.append(newrow)
                    if row % 500 == 0 or row == len(self.corpus)-1:
                        self.core_savetable(table, output)
                        #with open(recovery, "a", encoding='utf-8') as rowfile:
                        #    rowfile.write(str(row)+"\n")
                        self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        paroletotali = 0
        parolepiene = 0
        parolevuote = 0
        parolenone = 0
        for row in range(len(table)):
            thistext = table[row][0]
            for key in self.legendaPos:
                if thistext == self.legendaPos[key][0]:
                    if "piene" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(table[row][1])
                        parolepiene = parolepiene + int(table[row][1])
                        break
                    if "vuote" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(table[row][1])
                        parolevuote = parolevuote + int(table[row][1])
                        break
                    if "none" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(table[row][1])
                        parolenone = parolenone + int(table[row][1])
                        break
        if mylevel == 2:
            table = [table[0]]
            table.append(["Parole totali", str(paroletotali), "1"])
            table.append(["Parole piene", str(parolepiene), "1"])
            table.append(["Parole vuote", str(parolevuote), "1"])
            table.append(["Altri token", str(parolenone), "1"])
        elif mylevel == 1:
            table = [table[0]]
            for key in mytypes:
                table.append([key,str(mytypes[key]), "1"])
        elif mylevel == 0:
            pass
        else:
            return ""
        #calcola percentuali
        for row in range(len(table)):
            thistext = table[row][0]
            try:
                ratio = (float(table[row][1])/float(paroletotali)*100)
                ratios = f'{ratio:.3f}'
            except:
                continue
            table[row][2] = str(ratios)
        self.core_savetable(table, output)
        return output

    def core_gulpease(self, myrecovery, filter = "", doignorepunct = True):
        fileName = self.sessionFile
        table = []
        col = self.corpuscols['pos'][0]
        hkey = re.sub("[^a-zA-Z0-9]", "_", filter)
        output = fileName + "-gulpease-" + hkey + ".tsv"
        recovery = output + ".tmp"
        totallines = len(self.corpus)
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1])
                startatrow = int(lastline)
                print("Carico la tabella")
                with open(output, "r", encoding='utf-8') as ins:
                    for line in ins:
                        table.append(line.replace("\n","").replace("\r","").split(separator))
                print("Comincio dalla riga " + str(startatrow))
            else:
                exception = 0/0
        except:
            startatrow = -1
            table.append(["Subcorpus", "Parole", "Frasi", "Caratteri", "Valore GULPEASE"])
        if self.OnlyVisibleRows:
            totallines = self.aToken
            if myrecovery and self.daToken > startatrow:
                startatrow = self.daToken
        #if startatrow >= (len(self.corpus)-1):
        #    return
        table = []
        table.append(["Subcorpus", "Parole", "Frasi", "Caratteri", "Valore GULPEASE"])
        if filter != "":
            table.append([filter, 0, 0, 0, 0])
        else:
            table.append(["Totale", 0, 0, 0, 0])
        lastphrasenum = ""
        for row in range(startatrow, totallines):
            if self.core_killswitch:
                break
            if row > startatrow:
                if filter != "":
                    if not self.applicaFiltro(row, self.filtrimultiplienabled, filter):
                        continue
                try:
                    thistext = self.corpus[row][self.corpuscols['lemma'][0]]
                    if self.ignoretext != "" and doignorepunct:
                        if self.corpus[row][self.corpuscols['pos'][0]] == "PUNCT":
                            thistext = ""
                            #Nota: ho visto che qualcuno tra i caratteri calcola anche la punteggiatura
                            #tbval = int(table[tbrow][3])+len(self.corpus[row][self.corpuscols['token'][0]])
                            #table[tbrow][3] = tbval
                        #thistext = re.sub(self.ignoretext, "", thistext) #Questo non dovrebbe servire, i numeri e altro testo speciale va contato comunque
                except:
                    thistext = ""
                if thistext != "":
                    filterClean = filter
                    if filter == "":
                        filterClean = "Totale"
                    tbrow = self.core_findintable(table, filterClean, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                        tbval = int(table[tbrow][3])+len(self.corpus[row][self.corpuscols['token'][0]])
                        table[tbrow][3] = tbval
                        if lastphrasenum != self.corpus[row][self.corpuscols['IDphrase'][0]]:
                            tbval = int(table[tbrow][2])+1
                            table[tbrow][2] = tbval
                            lastphrasenum = self.corpus[row][self.corpuscols['IDphrase'][0]]
                    else:
                        print("Non existent filter")
                    if row % 500 == 0 or row == len(self.corpus)-1:
                        self.core_savetable(table, output)
                        #with open(recovery, "a", encoding='utf-8') as rowfile:
                        #    rowfile.write(str(row)+"\n")
                        self.core_fileappend(str(row)+"\n", recovery)
        self.core_fileappend(str(row)+"\n", recovery)
        for row in range(len(table)):
            if row == 0:
                continue
            totalwords = int(table[row][1])
            totalphrases = int(table[row][2])
            totalchars = int(table[row][3])
            gulpease = 89+(((300*totalphrases)-(10*totalchars))/(totalwords))
            ratios = f'{gulpease:.3f}'
            table[row][4] = str(ratios)
            table[row][3] = str(totalchars)
            table[row][2] = str(totalphrases)
            table[row][1] = str(totalwords)
        self.core_savetable(table, output)
        return output



    def core_estrai_colonna(self, fileNames, mycol, myrecovery, separator = '\t'):
        try:
            col = int(mycol)
        except:
            col = 0
        for fileName in fileNames:
            row = 0
            output = fileName + "-colonna-" + str(col) + ".tsv"
            recovery = output + ".tmp"
            startatrow = -1
            try:
                if os.path.isfile(recovery) and myrecovery:
                    with open(recovery, "r", encoding='utf-8') as tempfile:
                       lastline = (list(tempfile)[-1])
                    startatrow = int(lastline)
                    print("Comincio dalla riga " + str(startatrow))
            except:
                startatrow = -1
            with open(fileName, "r", encoding='utf-8') as ins:
                for line in ins:
                    if row > startatrow:
                        try:
                            thistext = line.replace("\n","").replace("\r","").split(separator)[col]
                        except:
                            thistext = ""
                        #with open(output, "a", encoding='utf-8') as outfile:
                        #    outfile.write(thistext+"\n")
                        self.core_fileappend(thistext+"\n", output)
                        #with open(recovery, "a", encoding='utf-8') as rowfile:
                        #    rowfile.write(str(row)+"\n")
                        self.core_fileappend(str(row)+"\n", recovery)
                    row = row + 1
        return output

    def core_appendcorpus(self, fileNames):
        for fileName in fileNames:
            try:
                IDphrase = -1
                with open(self.sessionFile, "r", encoding='utf-8') as ins:
                    for line in ins:
                        try:
                            tmpphrase = int(line.split("\t")[self.corpuscols["IDphrase"][0]])
                        except:
                            continue
                        if tmpphrase > IDphrase:
                            IDphrase = tmpphrase
            except:
                IDphrase = -1
            IDphrase = IDphrase +1
            print("Appending " + fileName + " to " + self.sessionFile + " IDphrase: " + str(IDphrase))
            separator = '\t'
            with open(fileName, "r", encoding='utf-8') as ins:
                for line in ins:
                    myline = line.replace("\n","").replace("\r","").split(separator)
                    try:
                        tmpphrase = int(myline[self.corpuscols["IDphrase"][0]])
                        myline[self.corpuscols["IDphrase"][0]] = IDphrase + tmpphrase
                    except:
                        continue
                    coln = 0
                    fullline = ""
                    for col in myline:
                        if coln > 0:
                            fullline = fullline + '\t'
                        fullline = fullline + str(col)
                        coln = coln + 1
                    self.core_fileappend(fullline+"\n", self.sessionFile)

    def core_mergetables(self, mydir, mycol, opstr, headerlines, myrecovery):
        separator = '\t'
        fileNames = []
        try:
            if os.path.isdir(mydir):
                for tfile in os.listdir(mydir):
                    if bool(tfile[-4:] == ".tsv" or tfile[-4:] == ".tsv") and tfile[-11:] != "-merged.tsv" and tfile[-11:] != "-merged.csv":
                        fileNames.append(os.path.join(mydir,tfile))
            else:
                return
        except:
            try:
                if os.path.isfile(mydir[0]):
                    fileNames = mydir
            except:
                return
        dirName = os.path.basename(os.path.dirname(fileNames[0]))
        try:
            col = int(mycol)
        except:
            col = 0
        output = os.path.join(os.path.dirname(fileNames[0]),dirName + "-merged.tsv")
        with open(fileNames[0], "r", encoding='utf-8') as f:
            first_line = f.readline().replace("\n","").replace("\r","")
        try:
            opers = opstr.split(",")
        except:
            opers = ["sum"]
        try:
            startatrow = int(headerlines)-1
            useheader = True
        except:
            startatrow = -1
            useheader = False
        table = []
        firstfile = -1
        for fileName in fileNames:
            firstfile = firstfile + 1
            row = 0
            recovery = fileName + ".tmp"
            print(fileName + " -> " + output)
            totallines = self.core_linescount(fileName)
            ch = "N"
            try:
                if os.path.isfile(recovery) and myrecovery:
                        with open(recovery, "r", encoding='utf-8') as tempfile:
                           lastline = (list(tempfile)[-1])
                        startatrow = int(lastline)
                        print("Carico la tabella")
                        with open(output, "r", encoding='utf-8') as ins:
                            for line in ins:
                                table.append(line.replace("\n","").replace("\r","").split(separator))
                        print("Comincio dalla riga " + str(startatrow))
                        useheader = False
                else:
                    exc = 1/0
            except:
                if useheader:
                    table.append(first_line.split(separator))
                    useheader = False
            with open(fileName, "r", encoding='utf-8') as ins:
                for line in ins:
                    if row > startatrow:
                        try:
                            thislist = line.split(separator)
                            thistext = thislist[col].replace("\n","").replace("\r","")
                        except:
                            thislist = []
                            thistext = ""
                        thisvalues = []
                        for valcol in range(len(thislist)):
                            if valcol != col:
                                try:
                                    thisvalues.append(thislist[valcol].replace("\n", ""))
                                except:
                                    thisvalues.append("")
                        while len(thisvalues)<len(opers):
                            thisvalues.append("")
                        tbrow = self.core_findintable(table, thistext, 0)
                        if tbrow>=0:
                            for valind in range(len(opers)):
                                tbval = float(table[tbrow][valind+1])
                                if opers[valind] == "sum":
                                    tbval = float(tbval) + float(thisvalues[valind])
                                if opers[valind] == "mean":
                                    tbval = (float(tbval) + float(thisvalues[valind]))
                                if opers[valind] == "diff":
                                    tbval = float(tbval) - float(thisvalues[valind])
                                table[tbrow][valind+1] = tbval
                        else:
                            newrow = [thistext]
                            for valind in range(len(thisvalues)):
                                newrow.append(thisvalues[valind])
                            table.append(newrow)
                        if row % 500 == 0 or row == totallines:
                            self.core_savetable(table, output)
                            #with open(recovery, "a", encoding='utf-8') as rowfile:
                            #    rowfile.write(str(row)+"\n")
                            self.core_fileappend(str(row)+"\n", recovery)
                    row = row + 1
            self.core_fileappend(str(row)+"\n", recovery)
        if "mean" in opers and firstfile > 0 and row == totallines and startatrow < totallines:
            for mrow in range(len(table)):
                for valind in range(len(opers)):
                    if opers[valind] == "mean":
                        try:
                            table[mrow][valind+1] = float(table[mrow][valind+1])/len(fileNames)
                        except:
                            err = True
        self.core_savetable(table, output)
        return output


    def core_splitbigfile(self, myfile, mymaxrow, mysplit, myrecovery):
        separator = '\t'
        if os.path.isfile(myfile):
            fileName = myfile
            ext = fileName[-3:]
        try:
            maxrow = int(mymaxrow)
        except:
            maxrow = 20000
            if ext == "csv" or ext=="tsv":
                maxrow = 500000
        splitdot = False
        try:
            if mysplit == "." and ext == "txt":
                splitdot = True
        except:
            splitdot = False
        part = 0
        row = 0
        partrow = 0
        output = fileName + "-part" + str(part) + "." + ext
        recovery = output + ".tmp"
        startatrow = -1
        try:
            if os.path.isfile(recovery) and myrecovery:
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1].split(",")[0])
                startatrow = int(lastline)
                part = int(list(tempfile)[-1].split(",")[1])
                partrow = int(list(tempfile)[-1].split(",")[2])
                print("Comincio dalla riga " + str(startatrow))
        except:
            startatrow = -1
            part = 0
        oldoutput = ""
        with open(fileName, "r", encoding='utf-8') as ins:
            for line in ins:
                if row > startatrow:
                    try:
                        thistext = line
                        if ext == "txt" and splitdot:
                            partrow = partrow + len(line.split(".")) -1
                    except:
                        thistext = ""
                    if partrow > (maxrow-1):
                        partrow = 0
                        part = part + 1
                    output = fileName + "-part" + str(part) + "." + ext
                    if output != oldoutput:
                        print(output)
                        oldoutput = output
                    #with open(output, "a", encoding='utf-8') as outfile:
                    #    outfile.write(thistext)
                    self.core_fileappend(thistext, output)
                    #with open(recovery, "a", encoding='utf-8') as rowfile:
                    #    rowfile.write(str(row)+","+str(part)+","+str(partrow)+"\n")
                    self.core_fileappend(str(row)+","+str(part)+","+str(partrow)+"\n", recovery)
                    partrow = partrow + 1
                row = row + 1
        return output

    def core_samplebigfile(self, myfile, mymaxrow, mysplit, myrecovery = False):
        separator = '\t'
        if os.path.isfile(myfile):
            fileName = myfile
            ext = fileName[-3:]
        try:
            maxrow = int(mymaxrow)
        except:
            maxrow = 20000
            if ext == "csv":
                maxrow = 500000
        splitdot = False
        try:
            if mysplit == "." and ext == "txt":
                splitdot = True
        except:
            splitdot = False
        if splitdot == True:
            with open(fileName, "r", encoding='utf-8') as ins:
                for line in ins:
                    thistext = line.replace('.','.\n')
                    with open(fileName + "-splitondot.txt", "a", encoding='utf-8') as outfile:
                        outfile.write(thistext)
            fileName = fileName + "-splitondot.txt"
        row = 0
        output = fileName + "-estratto." + ext
        startatrow = -1
        totallines = self.core_linescount(fileName)
        print("Total Lines: " + str(totallines))
        #ripristino impossibile, è un sistema casuale
        chunkf = float(totallines)/float(maxrow)
        chunk = int(math.floor(chunkf))
        if chunk < 2:
            print("Non ci sono abbastanza righe nel file")
            return
        getrows = []
        start = 0
        print("Calcolo le righe da selezionare")
        for i in range(maxrow):
            end = start+chunk -1
            if start >= totallines-1:
                start = totallines -2
            if end >= totallines:
                end = totallines -1
            trow = random.randint(start, end)
            getrows.append(trow)
            start = end + 1
        print("Estraggo le righe in un nuovo file")
        ir = 0
        with open(fileName, "r", encoding='utf-8') as ins:
            for line in ins:
                if row == getrows[ir]:
                    try:
                        thistext = line
                    except:
                        thistext = ""
                    ir = ir + 1
                    if ir == len(getrows):
                        break
                    #with open(output, "a", encoding='utf-8') as outfile:
                    #    outfile.write(thistext)
                    self.core_fileappend(thistext, output)
                row = row + 1
        print(myfile +" -> "+ output)
        return output


########### UDPIPE INTEGRATION

class UDCorpus(QThread):
    dataReceived = Signal(bool)
    updated = Signal(int)

    def __init__(self, widget, fnames, corpcol, udpipe, udpipemodel, lang):
        QThread.__init__(self)
        self.corpuswidget = widget
        self.fileNames = fnames
        self.corpuscols = corpcol
        self.udpipe = udpipe
        self.udpipemodel = udpipemodel
        self.language = lang
        self.outputcsv = ""
        self.corpusIDpattern = "[ID]_[FILENAME],lang:ita,tagger:udpipe"
        self.csvIDcolumn = -1
        self.csvTextcolumn = -1
        self.csvSep = '\t'
        self.loadvariables()
        self.alwaysyes = False
        self.setTerminationEnabled(True)
        self.iscli = False
        try:
            if self.corpuswidget == "cli":
                self.iscli = True
        except:
            self.iscli = False
        self.alwaysyes = False
        self.core_killswitch = False
        self.rowfilename = ""
        self.logfile = ""

    def loadvariables(self):
        self.useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

    def __del__(self):
        print("Shutting down thread")

    def run(self):
        self.loadtxt()
        return

    def loadtxt(self):
        fileID = 0
        tagPattern = self.corpusIDpattern
        #if not self.iscli:
        #    self.Progrdialog = progress.Form()
        #    self.updated.connect(self.Progrdialog.setValue)
        #    self.Progrdialog.show()
        for fileName in self.fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    try:
                        if self.corpuswidget.rowCount() >0:
                            fileID = int(self.corpuswidget.item(self.corpuswidget.rowCount()-1,0).text().split("_")[0])
                    except:
                        fileID = 0
                    #QApplication.processEvents()
                    fileID = fileID+1
                    lines = ""
                    try:
                        text_file = open(fileName, "r", encoding='utf-8')
                        lines = text_file.read()
                        text_file.close()
                    except:
                        myencoding = "ISO-8859-15"
                        #https://pypi.org/project/chardet/
                        gotEncoding = False
                        encI = 0
                        encs = ["ISO-8859-15", "cp1252"]
                        while gotEncoding == False:
                            #try:
                                #self.Progrdialog.hide()
                                #myencoding = QInputDialog.getText(self.corpuswidget, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
                                #self.Progrdialog.show()
                            #except:
                            if encI > (len(encs)+1):
                                break
                            if encI > (len(encs)-1):
                                print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
                                myencoding = [input()]
                                encI = encI + 1
                            else:
                                myencoding = encs[encI]
                                encI = encI + 1
                            try:
                                text_file = open(fileName, "r", encoding=myencoding[0])
                                lines = text_file.read()
                                text_file.close()
                                gotEncoding = True
                            except:
                                gotEncoding = False
                    self.rowfilename = fileName + ".tmp"
                    self.logfile = fileName + ".log"
                    if self.iscli:
                        if self.outputcsv == "":
                            self.outputcsv = fileName + ".tsv"
                    print(fileName + " -> " + self.outputcsv)
                    if self.csvIDcolumn <0 or self.csvTextcolumn <0:
                        #try:
                        #    self.Progrdialog.hide()
                        #    corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:udpipe"
                        #    corpusID = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus:", QLineEdit.Normal, corpusID)[0]
                        #    self.Progrdialog.show()
                        #except:
                        #    corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:udpipe"
                        #corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:udpipe"
                        corpusID = tagPattern.replace("[ID]", str(fileID)).replace("[FILENAME]", os.path.basename(fileName))
                        self.text2corpusUD(lines, corpusID)
                    else:
                        try:
                            #sep = QInputDialog.getText(self.corpuswidget, "Scegli il separatore", "Indica il carattere che separa le colonne (\\t è la tabulazione):", QLineEdit.Normal, "\\t")[0]
                            sep = self.csvSep
                            if sep == "\\t":
                                sep = "\t"
                            #self.Progrdialog.hide()
                            #textID = QInputDialog.getInt(self.corpuswidget, "Scegli il testo", "Indica la colonna della tabella che contiene il testo di questo sottocorpus:")[0]
                            #corpusIDtext = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus. Puoi usare [FILENAME] per indicare il nome del file e [COLONNA] per indicare la colonna da cui estrarre un tag.", QLineEdit.Normal, "[filename], [0]"+",tagger:udpipe")[0]
                            textID = self.csvTextcolumn
                            corpusIDtext = tagPattern
                            #self.Progrdialog.show()
                            textID = int(textID)
                            for line in lines.split("\n"):
                                corpusID = corpusIDtext.replace("[FILENAME]", os.path.basename(fileName))
                                indexes = [(m.start(0), m.end(0)) for m in re.finditer('\[[0-9]*\]', corpusID)]
                                for n in range(len(indexes)):
                                    start = indexes[n][0]
                                    end = indexes[n][1]
                                    try:
                                        strCol = corpusID[start:end]
                                        intCol = int(corpusID[start+1:end-1])
                                        corpusID = corpusID.replace(strCol, line.split(sep)[intCol])
                                    except:
                                        print("Impossibile trovare la colonna nel CSV")
                                print(corpusID)
                                self.text2corpusUD(line.split(sep)[textID], corpusID)
                        except:
                            try:
                                textID = int(self.csvTextcolumn)
                                colID = int(self.csvIDcolumn)
                                if textID != colID:
                                    for line in lines.split("\n"):
                                        corpusID = line.split("\t")[colID]+",lang:"+self.language+",tagger:udpipe"
                                        self.text2corpusUD(line.split("\t")[textID], corpusID)
                            except:
                                if self.logfile != "":
                                    logline = "ERROR,"+fileName+","+ corpusID  + "," +"Errore in text2corpusUD"
                                    with open(self.logfile, "a", encoding='utf-8') as mylogfile:
                                        mylogfile.write(str(logline)+"\n")
                                continue
        if self.fileNames == []:
            testline = "Il gatto è sopra al tetto."
            myres = self.getUDTable(testline)
            try:
                self.dataReceived.emit(True)
            except:
                self.dataReceived.emit(False)
        #if not self.iscli:
        #    self.Progrdialog.accept()


    def addlinetocorpus(self, text, column):
        row = self.corpuswidget.rowCount()
        self.corpuswidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.corpuswidget.setItem(row, column, titem)
        self.corpuswidget.setCurrentCell(row, column)
        return row

    def setcelltocorpus(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.corpuswidget.setItem(row, column, titem)
        #self.corpuswidget.setCurrentCell(row, column)

    def text2corpusUD(self, text, TAGcorpus):
        itext = text.replace('.','. \n')
        itext = itext.replace('?','? \n')
        #merge phrases in paragraphs to optimize loading time for udpipe
        print("Lines before optimization: " + str(len(itext.split('\n'))))
        frasiInParagrafo = 50
        count = 0
        itext = itext.split('\n')
        ntext = []
        temp = ""
        for f in range(len(itext)):
            if count != frasiInParagrafo and f<(len(itext)-1):
                temp = temp + " " + itext[f]
                count = count + 1
            else:
                ntext.append(temp)
                count = 0
                temp = ""
        itext = ntext
        del ntext
        totallines = len(itext)
        print("Total lines: "+str(totallines))
        #if not self.iscli:
        #    self.Progrdialog.setBasetext("Sto lavorando sul paragrafo numero ")
        #    self.Progrdialog.setTotal(totallines)
        startatrow = -1
        try:
            if os.path.isfile(self.rowfilename):
                ch = "Y"
                if self.iscli:
                    if self.alwaysyes:
                        ch = "y"
                    else:
                        ch = "n"
                        print("Ho trovato un file di ripristino, lo devo usare? [Y/N]")
                        ch = input()
                    if ch == "Y" or ch == "y":
                        with open(self.rowfilename, "r", encoding='utf-8') as tempfile:
                           lastline = (list(tempfile)[-1])
                        startatrow = int(lastline)
                        print("Comincio dalla riga " + str(startatrow))
        except:
            startatrow = -1
        #
        try:
            IDphrase = -1
            if self.outputcsv == "":
                for crow in range(self.corpuswidget.rowCount()):
                    if int(self.corpuswidget.item(crow, self.corpuscols["IDphrase"][0]).text()) > IDphrase:
                        IDphrase = int(self.corpuswidget.item(crow, self.corpuscols["IDphrase"][0]).text())
            else:
                #with open(self.rowfilename, "r", encoding='utf-8') as ins:
                with open(self.outputcsv, "r", encoding='utf-8') as ins:
                    for line in ins:
                        try:
                            tmpphrase = int(line.split("\t")[self.corpuscols["IDphrase"][0]])
                        except:
                            continue
                        if tmpphrase > IDphrase:
                            IDphrase = tmpphrase
        except:
            IDphrase = -1
        #print("Starting from IDphrase " +str(IDphrase))
        row = 0
        dct = {"ID" : 0, "FORM" : 1, "LEMMA" : 2, "UPOS" : 3, "XPOS" : 4, "FEATS" : 5 , "HEAD": 6, "DEPREL": 7, "DEPS": 8, "MISC": 9}
        for line in itext:
            row = row + 1
            if row > startatrow:
                #self.Progrdialog.w.testo.setText("Sto lavorando sulla frase numero "+str(row))
                #self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                self.updated.emit(row)
                #if not self.iscli and row % 20 == 0:
                #    QApplication.processEvents()
                #if not self.iscli:
                #    if self.Progrdialog.w.annulla.isChecked():
                #        return
                if self.core_killswitch:
                    break
                myres = []
                if line != "":
                    myres = self.getUDTable(line)
                for sentence in myres:
                    IDphrase = IDphrase +1
                    skipT = -1
                    for t in range(len(sentence)):
                        token = sentence[t]
                        fullline = ""
                        if "-" in str(token[dct["ID"]]):
                            fullline = str(TAGcorpus) + "\t"
                            fullline = fullline + str(sentence[t][dct["FORM"]]) + "\t"
                            lemma = ""
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                templemma = str(sentence[t+el+1][dct["LEMMA"]])
                                if len(templemma)>len(lemma):
                                    lemma = templemma
                            fullline = fullline + lemma + "\t"
                            pos = ""
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                if el > 0:
                                    pos = pos + "+"
                                pos = pos + str(sentence[t+el+1][dct["UPOS"]])
                            fullline = fullline + pos + "\t"
                            ner = "_"
                            fullline = fullline + str(ner) + "\t"
                            morf = ""
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                if el > 0:
                                    morf = morf + "/"
                                morf = morf + str(sentence[t+el+1][dct["FEATS"]])
                            fullline = fullline + str(morf) + "\t"
                            fullline = fullline + str(str(sentence[t][dct["ID"]]).split("-")[0]) + "\t"
                            fullline = fullline + str(IDphrase)
                            #for el in range(len(str(token[dct["ID"]]).split("-"))):
                            fullline = fullline + "\t" + str(sentence[t+1][dct["DEPREL"]]) + "\t"
                            governor = str(sentence[t+1][dct["HEAD"]])
                            for el in range(len(str(token[dct["ID"]]).split("-"))):
                                tmpgov = str(sentence[t+el+1][dct["HEAD"]])
                                if not tmpgov in str(token[dct["ID"]]).split("-"):
                                    governor = tmpgov
                            fullline = fullline + governor
                            skipT = t + len(str(token[dct["ID"]]).split("-"))
                        elif t > skipT:
                            fullline = str(TAGcorpus) + "\t"
                            fullline = fullline + str(token[dct["FORM"]]) + "\t"
                            fullline = fullline + str(token[dct["LEMMA"]]) + "\t"
                            fullline = fullline + str(token[dct["UPOS"]]) + "\t"
                            ner = "O"
                            fullline = fullline + str(ner) + "\t"
                            morf = str(token[dct["FEATS"]])
                            fullline = fullline + str(morf) + "\t"
                            fullline = fullline + str(token[dct["ID"]]) + "\t"
                            fullline = fullline + str(IDphrase)
                            fullline = fullline + "\t" + str(token[dct["DEPREL"]]) + "\t"
                            fullline = fullline + str(token[dct["HEAD"]])
                        if fullline != "":
                            fdatefile = self.outputcsv
                            with open(fdatefile, "a", encoding='utf-8') as myfile:
                                myfile.write(fullline+"\n")
                        else:
                            if self.logfile != "" and t > skipT:
                                logline = "ERROR,"+self.outputcsv+",Frase:"+ str(IDphrase) +",Token:" + str(t) + "," +"Errore: riga vuota per il token "+str(token).replace("\n","")+" nella frase "+str(sentence).replace("\n","")
                                with open(self.logfile, "a", encoding='utf-8') as mylogfile:
                                    mylogfile.write(str(logline)+"\n")
                if self.iscli:
                    with open(self.rowfilename, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
                else:
                    with open(self.outputcsv+"-UD-importlog.tmp", "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+","+str(totallines)+"\n")
        if self.iscli:
            print("Done")

    def getUDTable(self, text):
        print("Running "+self.udpipe)
        process = subprocess.Popen([self.udpipe, "--tokenize", "--tag", "--parse", self.udpipemodel], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        testobyte = text.encode(encoding='utf-8')
        outputbyte = process.communicate(testobyte)[0]
        process.stdin.close()
        stroutput = outputbyte.decode(encoding='utf-8')
        #print(stroutput)
        mytable = stroutput.split("\n")
        myres = []
        sentence = []
        sentid = 0
        for row in range(len(mytable)):
            if row == (len(mytable)-1) or bool("sent_id" in mytable[row] and row > 5):
                try:
                    newsentid = int(mytable[row].replace("# sent_id = ", ""))
                except:
                    newsentid = sentid +1
                myres.append(sentence)
                sentence = []
                sentid = newsentid
            if len(mytable[row].split("\t")) > 8:
                sentence.append(mytable[row].split("\t"))
        #print(myres)
        return myres
