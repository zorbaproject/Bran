#!/usr/bin/env python
# -*- coding: utf-8 -*-

from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor
from forms import confronto
from forms import tint
from forms import progress
from forms import sessione
from forms import ripetizioni
from forms import about
from forms import creafiltro
from forms import alberofrasi



class BranCorpus():

    def __init__(self, corpcol, legPos, ignthis, dimlst, tablewidget=None, window=None, parent=None):
        #super(MainWindow, self).__init__(parent)
        self.w = window
        self.corpuswidget = tablewidget
        self.setCentralWidget(self.w)
        self.setWindowTitle("Bran")
        self.corpuscols = corpcol
        self.legendaPos = legPos
        self.ignoretext = ignthis
        self.dimList = dimlst
        self.ignorepos = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "altro"] # "punteggiatura - .?!"
        self.separator = "\t"
        self.language = "it-IT"
        self.corpus = []
        self.filtrimultiplienabled = "Filtro multiplo"
        self.alreadyChecked = False
        self.ImportingFile = False
        self.sessionFile = ""
        self.sessionDir = "."
        #self.w.cfilter.setMaxLength(sys.maxsize-1)
        self.w.cfilter.setMaxLength(2147483647)
        self.mycfgfile = QDir.homePath() + "/.brancfg"
        self.mycfg = json.loads('{"javapath": "", "tintpath": "", "tintaddr": "", "tintport": "", "sessions" : []}')
        self.loadPersonalCFG()
        self.loadSession()
        self.loadConfig()
        self.txtloadingstopped()

    def changeLang(self, lang):
        self.language = lang
        print("Set language "+self.language)

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

    def savePersonalCFG(self):
        cfgtxt = json.dumps(self.mycfg)
        text_file = open(self.mycfgfile, "w", encoding='utf-8')
        text_file.write(cfgtxt)
        text_file.close()

    def chiudiProgetto(self):
        self.sessionFile = ""
        self.sessionDir = "."
        self.corpus = []
        for row in range(self.corpuswidget.rowCount()):
            self.corpuswidget.removeRow(0)
            if row<100 or row%100==0:
                QApplication.processEvents()
        #self.setWindowTitle("Bran")

    def loadtxt(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        #self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
        if self.language == "it-IT":
            self.TCThread = tint.TintCorpus(self.w, fileNames, self.corpuscols, self.TintAddr)
            self.TCThread.outputcsv = self.sessionFile
            self.TCThread.finished.connect(self.txtloadingstopped)
            self.TCThread.start()
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadTextFromCSV(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv)")[0]
        if len(fileNames)<1:
            return
        #self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
        if self.language == "it-IT":
            self.TCThread = tint.TintCorpus(self.w, fileNames, self.corpuscols, self.TintAddr)
            self.TCThread.outputcsv = self.sessionFile
            self.TCThread.csvIDcolumn = 0
            self.TCThread.csvTextcolumn = 0
            self.TCThread.finished.connect(self.txtloadingstopped)
            self.TCThread.start()
        #else if self.language == "en-US":
        #https://www.datacamp.com/community/tutorials/stemming-lemmatization-python

    def loadjson(self):
        QMessageBox.information(self, "Attenzione", "Caricare un file JSON non è più supportato.")

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
                    myencoding = QInputDialog.getText(self.w, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
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

    def importfromTreeTagger(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv *.txt)")[0]
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/treetagger-"+self.language+".json"
        try:
            text_file = open(filein, "r")
            myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
            text_file.close()
            legendaTT = json.loads(myjson)
        except:
            QMessageBox.warning(self, "Errore", "Non riesco a leggere il dizionario di traduzione per TreeTagger.")
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
                    tmpline[self.corpuscols["Orig"][0]] = str(cols[0])
                    tmpline[self.corpuscols["Lemma"][0]] = str(cols[2])
                    try:
                        tmpline[self.corpuscols["pos"][0]] = legendaTT[str(cols[1])]
                    except:
                        tmpline[self.corpuscols["pos"][0]] = str(cols[1])
                    self.corpus.append(tmpline)
                except:
                    continue
        self.updateCorpus(self.Progrdialog)
        self.Progrdialog.accept()

    def loadCSV(self):
        if self.ImportingFile == False:
            fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "File CSV (*.tsv *.txt *.csv)")[0]
            self.ImportingFile = True
            self.CSVloader(fileNames) #self.CSVloader(fileNames, self.Progrdialog)

    def CSVloader(self, fileNames):
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    if not os.path.getsize(fileName) > 0:
                        #break
                        self.ImportingFile = False
                        return
                    try:
                        totallines = self.linescount(fileName)
                    except:
                        self.ImportingFile = False
                        return
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    linesA = lines.split('\n')
                    maximum = self.w.daToken.value()+len(linesA)-1
                    self.w.daToken.setMaximum(maximum)
                    self.w.aToken.setMaximum(maximum)
                    for line in linesA:
                        newtoken = line.split(self.separator)
                        if len(newtoken) == len(self.corpuscols):
                            self.corpus.append(newtoken)
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
        self.w.statusbar.clearMessage()
        if self.sessionFile != "" and self.ImportingFile == False:
            if os.path.isfile(self.sessionFile):
                if not os.path.getsize(self.sessionFile) > 1:
                    return
            try:
                self.ImportingFile = True
                fileNames = ['']
                fileNames[0] = self.sessionFile
                self.corpuswidget.setRowCount(0)
                self.CSVloader(fileNames)
            except:
                try:
                    self.myprogress.reject()
                    self.ImportingFile = False
                except:
                    return

    def salvaProgetto(self):
        if self.sessionFile == "":
            fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
            if fileName != "":
                self.sessionFile = fileName
        if self.sessionFile != "":
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            self.CSVsaver(self.sessionFile, self.Progrdialog, False)

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
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
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
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
                    csv = "# newdoc id = " + self.corpus[0][self.corpuscols['IDcorpus'][0]]
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
                Ucolumns.append(self.corpus[row][self.corpuscols['Orig'][0]])
                if "[PUNCT]" in self.corpus[row][self.corpuscols['Lemma'][0]]:
                    Ucolumns.append(self.corpus[row][self.corpuscols['Orig'][0]])
                else:
                    Ucolumns.append(self.corpus[row][self.corpuscols['Lemma'][0]])
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
                Ucolumns.append(self.corpus[row][self.corpuscols['governor'][0]])
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
                    phraseText = self.rebuildText(self.corpus, self.Progrdialog, self.corpuscols['Orig'][0], myignore, row, endrow, False)
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

    def esportavistaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
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

    def esportaCSVperID(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        IDs = []
        col = self.corpuscols['IDcorpus'][0]
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
        repCdialog = regex_replace.Form(self)
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
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
                totallines = self.w.aToken.value()
                startline = self.w.daToken.value()
            for row in range(startline, totallines):
                self.Progrdialog.w.testo.setText("Sto cercando nella riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row-startline):
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
        repCdialog = regex_replace.Form(self)
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
            startline = self.w.daToken.value()
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
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row):
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

    def contaoccorrenze(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(column[0], 0)
        TBdialog.addcolumn("Occorrenze", 1)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row-startline):
                continue
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
            tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
            if tbrow>=0:
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        TBdialog.exec()

    def contaoccorrenzefiltrate(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        QMessageBox.information(self, "Filtro", "Ora devi impostare i filtri con cui dividere i risultati. I vari filtri devono essere separati da condizioni OR, per ciascuno di essi verrà creata una colonna a parte nella tabella dei risultati.")
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText("pos=A.*||pos=S.*")
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() == "":
            return
        allfilters = Fildialog.w.filter.text().split("||")
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(column[0], 0)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        for myfilter in allfilters:
            TBdialog.addcolumn(myfilter, 1)
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row-startline):
                continue
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
                if self.applicaFiltro(self.corpus, row, col, allfilters[ifilter]):
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
        TBdialog.exec()

    def contaverbi(self):
        poscol = self.corpuscols["pos"][0] #thisname.index(column[0])
        morfcol = self.corpuscols["feat"][0]
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Modo+Tempo", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        TBdialog.addcolumn("Percentuali", 1)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thispos = self.legendaPos[self.corpus[row][self.corpuscols['pos'][0]]][0]
            except:
                thispos = ""
            thistext = ""
            thistext2 = ""
            if thispos.split(" ")[0] == "verbo":
                thistext = self.corpus[row][morfcol]
            if "ausiliare" in thispos:
                for ind in range(1,4):
                    try:
                        tmpos = self.legendaPos[self.corpus[row+ind][self.corpuscols['pos'][0]]][0]
                    except:
                        tmpos = ""
                    if "verbo" in tmpos:
                        thistext = ""
                        break
            elif thispos.split(" ")[0] == "verbo":
                for ind in range(1,4):
                    try:
                        tmpos = self.legendaPos[self.corpus[row-ind][self.corpuscols['pos'][0]]][0]
                    except:
                        tmpos = ""
                    if "ausiliare" in tmpos and "v+part+pass" in thistext:
                        thistext2 = thistext2 + "/" + self.corpus[row-ind][morfcol]
                    if "verbo" in tmpos and not "ausiliare" in tmpos:
                        break
            if len(thistext2)>0:
                if thistext2[0]=="/":
                    thistext2=thistext2[1:]
            if bool(re.match('^v\+.*?$', thistext))==False:
                thistext = ""
            if bool(re.match('^v\+.*?$', thistext2))==False:
                thistext2 = ""
            if len(thistext.split("+")) >= 3:
                tmptext = thistext.split("+")[0] + "+" +thistext.split("+")[1] + "+" +thistext.split("+")[2]
                thistext = tmptext
            thistext3 = ""
            if len(thistext2.split("/"))>1:
                thistext3 = thistext2.split("/")[1]
                thistext2 = thistext2.split("/")[0]
            if bool(re.match('^v\+.*?$', thistext3))==False:
                thistext3 = ""
            if len(thistext2.split("+")) >= 3:
                tmptext = thistext2.split("+")[0] + "+" +thistext2.split("+")[1] + "+" +thistext2.split("+")[2]
                thistext2 = tmptext + "/"
            if len(thistext3.split("+")) >= 3:
                tmptext = thistext3.split("+")[0] + "+" +thistext3.split("+")[1] + "+" +thistext3.split("+")[2]
                thistext3 = tmptext + "/"
            if thistext != "":
                thistext = thistext3 + thistext2 + thistext
            if thistext != "":
                tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                if tbrow>=0:
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 1)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable("1", tbrow, 1)
        #calcolo le percentuali
        totallines = TBdialog.w.tableWidget.rowCount()
        verbitotali = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            verbitotali = verbitotali + int(TBdialog.w.tableWidget.item(row,1).text())
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto calcolando le percentuali su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            ratio = (float(TBdialog.w.tableWidget.item(row,1).text())/float(verbitotali)*100)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(ratios, row, 2)
        self.Progrdialog.accept()
        TBdialog.exec()

    def trovaripetizioni(self):
        Repetdialog = ripetizioni.Form(self)
        Repetdialog.loadipos(self.ignorepos)
        Repetdialog.loadallpos(self.legendaPos)
        self.enumeratecolumns(Repetdialog.w.colonna)
        Repetdialog.w.colonna.setCurrentIndex(self.corpuscols['Orig'][0])
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
            TBdialog = tableeditor.Form(self)
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
                        # Controlliamo self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() e facciamo un subset solo con le righe visibili?
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
            TBdialog.exec()

    def ricostruisciTesto(self):
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self, "Scegli la colonna", "Su quale colonna devo ricostruire il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        mycorpus = self.rebuildText(self.corpus, self.Progrdialog, col)
        mycorpus = self.remUselessSpaces(mycorpus)
        self.Progrdialog.accept()
        te = texteditor.TextEditor()
        te.w.plainTextEdit.setPlainText(mycorpus)
        te.exec()

    def rebuildText(self, table, Progrdialog, col = "", ipunct = [], startrow = 0, endrow = 0, usefilter = True):
        mycorpus = ""
        if col == "":
            col = self.corpuscols['Orig'][0]
        totallines = len(table)
        if endrow == 0:
            endrow = totallines
        for row in range(startrow, endrow):
            ftext = self.w.cfilter.text()
            fcol = self.w.ccolumn.currentIndex()
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.applicaFiltro(table, row, fcol, ftext) and usefilter:
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

    def remUselessSpaces(self, tempstring):
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
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Part of Speech", 0)
        TBdialog.addcolumn("Macrocategoria", 1)
        TBdialog.addcolumn("Occorrenze", 2)
        TBdialog.addcolumn("Percentuale", 3)
        #calcolo le occorrenze del pos
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        mytypes = {}
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
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
                tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                if tbrow>=0:
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,2).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 2)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable(self.legendaPos[thistextO][1], tbrow, 1)
                    TBdialog.setcelltotable("1", tbrow, 2)
        #calcolo le somme di parole piene e vuote
        totallines = TBdialog.w.tableWidget.rowCount()
        paroletotali = 0
        parolepiene = 0
        parolevuote = 0
        parolenone = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto sommando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            thistext = TBdialog.w.tableWidget.item(row,0).text()
            for key in self.legendaPos:
                if thistext == self.legendaPos[key][0]:
                    if "piene" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,2).text())
                        parolepiene = parolepiene + int(TBdialog.w.tableWidget.item(row,2).text())
                        break
                    if "vuote" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,2).text())
                        parolevuote = parolevuote + int(TBdialog.w.tableWidget.item(row,2).text())
                        break
                    if "none" == self.legendaPos[key][2]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,2).text())
                        parolenone = parolenone + int(TBdialog.w.tableWidget.item(row,2).text())
                        break
        #presento le macrocategorie
        for key in mytypes:
            TBdialog.addlinetotable(key, 1)
            tbrow = TBdialog.w.tableWidget.rowCount()-1
            TBdialog.setcelltotable(str(mytypes[key]), tbrow, 2)
        TBdialog.addlinetotable("Parole totali", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(paroletotali), tbrow, 2)
        TBdialog.addlinetotable("Parole piene", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolepiene), tbrow, 2)
        TBdialog.addlinetotable("Parole vuote", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolevuote), tbrow, 2)
        TBdialog.addlinetotable("Altri tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolenone), tbrow, 2)
        #calcolo le percentuali
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto calcolando le percentuali su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            ratio = (float(TBdialog.w.tableWidget.item(row,2).text())/float(paroletotali)*100)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(ratios, row, 3)
        #mostro i risultati
        self.Progrdialog.accept()
        TBdialog.exec()


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
        startline = self.w.daToken.value()
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.corpuswidget.removeRow(toselect[row-1])
            del self.corpus[startline+toselect[row-1]]

        self.Progrdialog.accept()

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

    def dofiltra(self):
        if self.w.ccolumn.currentText() == self.filtrimultiplienabled and len(self.w.cfilter.text().split("||"))>10:
            ret = QMessageBox.question(self,'Domanda', "Sembra che tu voglia applicare un filtro multiplo, l'operazione può essere lenta. Vuoi vedere la percentuale di progresso?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                self.dofiltra2()
                return
        tcount = 0
        totallines = self.w.aToken.value()
        startline = self.w.daToken.value()
        for row in range(startline, totallines):
            fcol = self.w.ccolumn.currentIndex()
            #ctext = self.corpuswidget.item(row,col).text()
            ftext = self.w.cfilter.text()
            if self.applicaFiltro(self.corpus, row, fcol, ftext): #if bool(re.match(ftext, ctext)):
                self.corpuswidget.setRowHidden(row-startline, False)
                tcount = tcount +1
            else:
                self.corpuswidget.setRowHidden(row-startline, True)
        self.w.statusbar.showMessage("Risultati totali: " +str(tcount))
        #self.Progrdialog.accept()

    def dofiltra2(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        tcount = 0
        totallines = self.corpuswidget.rowCount()
        for row in range(self.corpuswidget.rowCount()):
            if row<100 or row%200==0:
                self.Progrdialog.w.testo.setText("Sto filtrando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            col = self.w.ccolumn.currentIndex()
            #ctext = self.corpuswidget.item(row,col).text()
            ftext = self.w.cfilter.text()
            if self.applicaFiltro(self.corpuswidget, row, col, ftext): #if bool(re.match(ftext, ctext)):
                self.corpuswidget.setRowHidden(row, False)
                tcount = tcount +1
            else:
                self.corpuswidget.setRowHidden(row, True)
        self.w.statusbar.showMessage("Risultati totali: " +str(tcount))
        self.Progrdialog.accept()

    def findNext(self):
        irow = 0
        if len(self.corpuswidget.selectedItems())>0:
            irow = self.corpuswidget.selectedItems()[len(self.corpuswidget.selectedItems())-1].row()+1
        if irow < self.corpuswidget.rowCount():
            col = self.w.ccolumn.currentIndex()
            for row in range(irow, self.corpuswidget.rowCount()):
                if self.corpuswidget.isRowHidden(row):
                    continue
                ftext = self.w.cfilter.text()
                if self.applicaFiltro(self.corpuswidget, row, col, ftext):
                    self.corpuswidget.setCurrentCell(row,0)
                    break

    def applicaFiltro(self, table, row, col, filtro):
        res = False
        if self.w.ccolumn.currentText() != self.filtrimultiplienabled:
            try:
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
                    cellname = andcond.split("=")[0]
                    try:
                        ftext = andcond.split("=")[1]
                    except:
                        continue
                    colname = cellname.split("[")[0]
                    col = self.corpuscols[colname][0]
                    if "[" in cellname.replace("]",""):
                        rowlist = cellname.replace("]","").split("[")[1].split(",")
                    else:
                        rowlist = [0]
                    for rowp in rowlist:
                        tmprow = row + int(rowp)
                        try:
                            ctext = table[tmprow][col]
                        except:
                            ctext = ""
                        if bool(re.match(ftext, ctext)):
                            res = True
                            break
                    if res == False:
                        break
                if res == True:
                    break
        return res

    def filtriMultipli(self):
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(self.w.cfilter.text())
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.w.cfilter.setText(Fildialog.w.filter.text())

    def actionNumero_dipendenze_per_frase(self):
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self)
        Fildialog.sessionDir = self.sessionDir
        col = self.corpuscols["dep"][0]
        Fildialog.filterColElements(self.corpuscols["IDphrase"][0])
        Fildialog.updateFilter()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.w.cfilter.setText(Fildialog.w.filter.text())
        allfilters = Fildialog.w.filter.text().split("||")
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Dependency", 0)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        for myfilter in allfilters:
            TBdialog.addcolumn(myfilter, 1)
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
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
                if self.applicaFiltro(self.corpus, row, col, allfilters[ifilter]):
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
        TBdialog.exec()

    def addTagFromFilter(self):
        QMessageBox.information(self, "Istruzioni", "Crea il filtro per selezionare gli elementi a cui vuoi aggiungere un tag.")
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.w.cfilter.setText(Fildialog.w.filter.text())
        nuovotag = QInputDialog.getText(self.w, "Scegli il tag", "Indica il tag che vuoi aggiungere alle parole che rispettano il filtro:", QLineEdit.Normal, "")[0]
        repCdialog = regex_replace.Form(self)
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
        col = self.corpuscols['IDcorpus'][0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            self.Progrdialog.w.testo.setText("Sto modificando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if self.applicaFiltro(self.corpus, row, col, self.w.cfilter.text()):
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

    def concordanze(self):
        parola = QInputDialog.getText(self.w, "Scegli la parola", "Indica la parola che vuoi cercare:", QLineEdit.Normal, "")[0]
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self, "Scegli la colonna", "In quale colonna devo cercare il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        myrange = int(QInputDialog.getInt(self.w, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        #myfilter = str(list(self.corpuscols)[col]) + "[" + rangestr + "]" +"="+parola
        myfilter = str(list(self.corpuscols)[col]) +"="+parola
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(myfilter) #"Lemma=essere&&pos[1,-1]=SP||Lemma[-1]=essere&&pos=S"
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.w.cfilter.setText(Fildialog.w.filter.text())
        #self.dofiltra()
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = self.ignorepos
        else:
            myignore = []
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if not self.applicaFiltro(self.corpus, row, self.filtrimultiplienabled, self.w.cfilter.text()):
                continue
            thistext = self.rebuildText(self.corpus, self.Progrdialog, col, myignore, row-myrange, row+myrange+1, False)
            thistext = self.remUselessSpaces(thistext)
            tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
            if tbrow>=0:
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        TBdialog.exec()

    def coOccorrenze(self):
        parola = QInputDialog.getText(self.w, "Scegli la parola", "Indica la parola che vuoi cercare:", QLineEdit.Normal, "")[0]
        thisname = []
        for col in self.corpuscols:
            thisname.append(self.corpuscols[col][1])
        column = QInputDialog.getItem(self, "Scegli la colonna", "In quale colonna devo cercare il testo?",thisname,current=1,editable=False)
        col = thisname.index(column[0])
        myrange = int(QInputDialog.getInt(self.w, "Indica il range", "Quante parole, prima e dopo, vuoi leggere?")[0])
        rangestr = str(myrange)
        myfilter = str(list(self.corpuscols)[col]) +"="+parola
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        Fildialog = creafiltro.Form(self.corpus, self.corpuscols, self)
        Fildialog.sessionDir = self.sessionDir
        Fildialog.w.filter.setText(myfilter) #"Lemma=essere&&pos[1,-1]=SP||Lemma[-1]=essere&&pos=S"
        Fildialog.updateTable()
        Fildialog.exec()
        if Fildialog.w.filter.text() != "":
            self.w.cfilter.setText(Fildialog.w.filter.text())
        #self.dofiltra()
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Segmento", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        ret = QMessageBox.question(self,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            myignore = self.ignorepos
        else:
            myignore = []
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        concordanze = []
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            ftext = myfilter #self.w.cfilter.text()
            fcol = self.w.ccolumn.currentIndex()
            if not self.applicaFiltro(self.corpus, row, fcol, ftext):
                continue
            thistext = self.rebuildText(self.corpus, self.Progrdialog, col, myignore, row-myrange, row+myrange+1, False)
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
        totallines = len(concordanze)
        for row in range(totallines):
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
                    tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                        TBdialog.setcelltotable(str(tbval), tbrow, 1)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable("1", tbrow, 1)
        self.Progrdialog.accept()
        TBdialog.exec()

    def removevisiblerows(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.corpuswidget.rowCount()
        startline = self.w.daToken.value()
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

    def cancelfiltro(self):
        for row in range(self.corpuswidget.rowCount()):
            self.corpuswidget.setRowHidden(row, False)



    def corpusCellChanged(self, row, col):
        try:
            startline = self.w.daToken.value()
            self.corpus[row+startline][col] = self.corpuswidget.item(row,col).text()
        except:
            print("Error editing cell")
            self.updateCorpus()

    def updateCorpus(self):
        if self.w.allToken.isChecked():
            self.w.daToken.setValue(0)
            self.w.aToken.setValue(self.w.aToken.maximum())
        Progrdialog = progress.Form() #self.Progrdialog = progress.Form()
        Progrdialog.show() #self.Progrdialog.show()
        # Clear table before adding new lines
        self.corpuswidget.setRowCount(0)
        maximum = self.w.aToken.value()
        if maximum > len(self.corpus):
            maximum = len(self.corpus)
        totallines = maximum-self.w.daToken.value()
        if totallines < 0:
            print("daToken need to be smaller than aToken")
            return
        for rowN in range(self.w.daToken.value(),maximum):
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
                        continue
                    TBrow = self.addlinetocorpus(str(line[colN]), 0) #self.corpuscols["IDcorpus"][0]
                self.setcelltocorpus(str(line[colN]), TBrow, colN)

    def runServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            self.w.statusbar.showMessage("ATTENDI: Devo avviare il server")
            self.TintThread = tint.TintRunner(self.TintSetdialog.w)
            self.TintThread.loadvariables(self.Java, self.TintDir, self.TintPort)
            self.TintThread.dataReceived.connect(lambda data: self.runServer(bool(data)))
            self.alreadyChecked = True
            self.TintThread.start()
        else:
            if platform.system() == "Windows":
                QMessageBox.information(self, "Come usare il server su Windows", "Sembra che tu stia usando Windows. Su questo sistema, per utilizzare il server Tint l'interfaccia di Bran verrà chiusa automaticamente: il terminale dovrà rimanere aperto. Dovrai aprire di nuovo Bran, così verrà caricata una nuova interfaccia grafica.")
                print("\nNON CHIUDERE QUESTA FINESTRA:  Tint è eseguito dentro questa finestra. Avvia di nuovo Bran.")
                print("\n\nNON CHIUDERE QUESTA FINESTRA")
                sys.exit(0)
            self.w.statusbar.showMessage("OK, il server è attivo")

    def checkServer(self, ok = False):
        if not ok:
            if self.alreadyChecked:
                QMessageBox.warning(self, "Errore", "Non ho trovato il server Tint.")
                self.alreadyChecked = False
                return
            self.Java = self.TintSetdialog.w.java.text()
            self.TintDir = self.TintSetdialog.w.tintlib.text()
            self.TintPort = self.TintSetdialog.w.port.text()
            self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
            QApplication.processEvents()
            self.TestThread = tint.TintCorpus(self.w, [], self.corpuscols, self.TintAddr)
            self.TestThread.dataReceived.connect(lambda data: self.checkServer(bool(data)))
            self.alreadyChecked = True
            self.TestThread.start()
            #while self.TestThread.isRunning():
            #    time.sleep(10)
            self.TintSetdialog.w.loglist.addItem("Sto cercando il server")
        else:
            self.TintSetdialog.accept()

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
        if column == self.corpuscols["pos"][0]:
            try:
                newtext = self.legendaPos[text][0]
                titem.setToolTip(newtext)
            except:
                newtext = text
        self.corpuswidget.setItem(row, column, titem)

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
        te = texteditor.TextEditor()
        te.exec()

    def confronto(self):
        cf = confronto.Confronto(self.sessionDir)
        cf.legendaPos = self.legendaPos
        cf.ignoretext = self.ignoretext
        cf.dimList = self.dimList
        cf.exec()

    def aboutbran(self):
        aw = about.Form(self)
        aw.exec()

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
        column = QInputDialog.getItem(self, "Scegli la colonna", "Se vuoi estrarre il dizionario devi cercare nella colonna dei lemmi. Ma puoi anche scegliere di ottenere le statistiche su altre colonne, come la Forma grafica.",thisname,current=self.corpuscols['Orig'][0],editable=False)
        col = thisname.index(column[0])
        ret = QMessageBox.question(self,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Token", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        #calcolo le occorrenze del pos
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totaltypes = 0
        mytypes = {}
        totallines = len(self.corpus)
        startline = 0
        if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked():
            totallines = self.w.aToken.value()
            startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.corpuswidget.isRowHidden(row-startline):
                continue
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisposc = "False"
            try:
                thistext = self.corpus[row][col]
            except:
                thistext = ""
            if ret == QMessageBox.Yes:
                thistext = re.sub(self.ignoretext, "", thistext)
            if thistext != "":
                tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                if tbrow>=0:
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 1)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable("1", tbrow, 1)
                    totaltypes = totaltypes + 1
        hapax = 0
        classifrequenza = []
        occClassifrequenza = []
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto cercando gli hapax su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if int(TBdialog.w.tableWidget.item(row,1).text()) == 1:
                hapax = hapax + 1
            if TBdialog.w.tableWidget.item(row,1).text() in classifrequenza:
                ind = classifrequenza.index(TBdialog.w.tableWidget.item(row,1).text())
                occClassifrequenza[ind] = occClassifrequenza[ind] + 1
            else:
                classifrequenza.append(TBdialog.w.tableWidget.item(row,1).text())
                occClassifrequenza.append(1)
        totallines = TBdialog.w.tableWidget.rowCount()
        paroletotali = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto calcolando le somme su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,1).text())
        dimCorpus = self.getCorpusDim(paroletotali)
        TBdialog.addcolumn("Frequenza in " + str(dimCorpus) + " parole", 2)
        TBdialog.addcolumn("Ordine di grandezza (log10)", 3)
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto controllando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            thistext = TBdialog.w.tableWidget.item(row,0).text()
            ratio = (float(TBdialog.w.tableWidget.item(row,1).text())/float(paroletotali)*dimCorpus)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(str(ratios), row, 2)
            ratio = math.log10(float(TBdialog.w.tableWidget.item(row,1).text())/float(paroletotali))
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(str(ratios), row, 3)
        TBdialog.addlinetotable("Tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(paroletotali), tbrow, 1)
        TBdialog.addlinetotable("Types", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(totaltypes), tbrow, 1)
        TBdialog.addlinetotable("(Types/Tokens)*100", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(totaltypes)/float(paroletotali))*100.0
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Tokens/Types", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(paroletotali)/float(totaltypes))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Hapax", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(hapax), tbrow, 1)
        TBdialog.addlinetotable("(Hapax/Tokens)*100", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(hapax)/float(paroletotali))*100.0
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Types/sqrt(Tokens)", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = float(totaltypes)/float(math.sqrt(paroletotali))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("log(Types)/log(Tokens)", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(math.log10(totaltypes))/float(math.log10(paroletotali)))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        YuleSum = 0
        for cfi in range(len(classifrequenza)):
            YuleSum = YuleSum + ( math.pow(int(classifrequenza[cfi]),2) * occClassifrequenza[cfi] )
        TBdialog.addlinetotable("Caratteristica di Yule (K)", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = float(math.pow(10,4)) * ((float(YuleSum) - float(paroletotali))/ float(math.pow(paroletotali, 2)) )
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("W", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = math.pow(float(paroletotali), (1.0/math.pow(float(totaltypes), 0.172)))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("U", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio =  math.pow(float(math.log10(paroletotali)), 2.0)/(float(math.log10(paroletotali)) - float(math.log10(totaltypes)) )
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        #mostro i risultati
        self.Progrdialog.accept()
        TBdialog.exec()
