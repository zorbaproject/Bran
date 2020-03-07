#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import sys
import os
import csv
import re
import math

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import QDir
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtCore import QThread


from forms import progress
from forms import tableeditor

class Confronto(QMainWindow):

    def __init__(self, parent=None, mycfg=None, sessionDir = ""):
        super(Confronto, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/confronto.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        #layout = QVBoxLayout()
        #layout.addWidget(self.w)
        #self.setLayout(layout)
        self.setCentralWidget(self.w)
        self.mycfg = mycfg
        #self.w.accepted.connect(self.isaccepted)
        #self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("Confronta dati estratti dai corpora")
        self.w.do_occ.clicked.connect(self.do_occ)
        self.w.do_gen.clicked.connect(self.do_gen)
        self.w.do_multi.clicked.connect(self.do_multi)
        #self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.sessionDir = sessionDir
        self.w.addfile.clicked.connect(self.addfile)
        self.w.rmfile.clicked.connect(self.rmfile)
        self.w.altrofileselect.clicked.connect(self.altrofileselect)
        self.w.with_dict.currentIndexChanged.connect(self.dictselect)
        self.w.with_corpora.currentIndexChanged.connect(self.corporaselect)
        self.fillcombos()
        self.corpuscols = {}
        self.legendaPos = []
        self.ignoretext = ""
        self.dimList = []

    def addfile(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv *.txt)")[0]
        for fileName in fileNames:
            self.w.corpora.addItem(fileName)

    def rmfile(self):
        for i in self.w.corpora.selectedItems():
            self.w.corpora.takeItem(self.w.corpora.row(i))

    def altrofileselect(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv *.txt)")[0]
        for fileName in fileNames:
            self.w.altrofilename.setText(fileName)
            self.w.altrofile.setChecked(True)

    def dictselect(self):
        self.w.sel_dict.setChecked(True)

    def corporaselect(self):
        self.w.sel_corpora.setChecked(True)

    def readcsv(self, fileName, separator = "\t"):
        lines = self.opentextfile(fileName)
        mylist = lines.split("\n")
        for i in range(len(mylist)):
            mylist[i] = mylist[i].split(separator)
        return mylist

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

    def fillcombos(self):
        branroot = os.path.abspath(os.path.dirname(sys.argv[0]))
        self.dizionari = {
        "VdB 2016": branroot  + "/dizionario/vdb2016.txt",
        "VdB 1980": branroot  + "/dizionario/vdb1980.txt",
        "Dizionario De Mauro 2000": branroot + "/dizionario/De_Mauro-Dizionario_della_lingua_italiana/dizionario-de-mauro-pulito.txt",
        "Wikizionario": branroot + "/dizionario/wikitionary/wikitionary-it-pulito.txt"
        }
        self.corpora = {
        "Il barone rampante": branroot  + "/corpora/barone-rampante/barone-rampante",
        "Il fu Mattia Pascal": branroot  + "/corpora/",
        "Twitter Wilwoosh": branroot  + "/corpora/",
        "Lercio.it": branroot  + "/corpora/",
        "Wikipedia": branroot  + "/corpora/wikipedia/wiki-it"}
        for key in self.dizionari:
            self.w.with_dict.addItem(key)
        for key in self.corpora:
            self.w.with_corpora.addItem(key)
        self.w.sel_dict.setChecked(True)
        self.datatype = ['Occorrenze lemma', 'Occorrenze forma grafica','Occorrenze PoS', 'Statistiche VdB', 'Contaverbi', 'Densità lessicale', 'Segmenti ripetuti', 'Corpus intero']
        for key in self.datatype:
            self.w.datatype.addItem(key)
        self.w.datatype.setCurrentIndex(0)

    def getRiferimento(self, action):
        fileName = ""
        if self.w.sel_dict.isChecked():
            fileName = self.dizionari[self.w.with_dict.currentText()]
        if self.w.sel_corpora.isChecked():
            fileName = self.corpora[self.w.with_corpora.currentText()]
            if action == "Occorrenze lemma":
                fileName = fileName + "-occorrenze-lemma.tsv"
            if action == "Occorrenze PoS":
                fileName = fileName + "-occorrenze-pos.tsv"
            if action == "Occorrenze forma grafica":
                fileName = fileName + "-occorrenze-token.tsv"
            if action == "Statistiche VdB":
                fileName = fileName + "-vdb.tsv"
            if action == "Contaverbi":
                fileName = fileName + "-contaverbi.tsv"
            if action == "Densità lessicale":
                fileName = fileName + "-densita.tsv"
            if action == "Segmenti ripetuti":
                fileName = fileName + "-ngrams.tsv"
            if action == "Corpus intero":
                fileName = fileName + "-bran.tsv"
        if self.w.altrofile.isChecked():
            fileName = self.w.altrofilename.text()
        return fileName

    def do_occ(self):
        context = self.w.datatype.currentText()
        if context == "Corpus intero":
            self.filediff()
        else:
            self.do_confronta(context)

    def do_gen(self):
        context = "generico"
        self.do_confronta(context)

    def do_multi(self):
        context = "multicolonna"
        self.do_confronta(context)

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

    def filediff(self):
        #columns = range(self.corpusCol)
        columns = ""
        for colkey in self.corpuscols:
            coldata = self.corpuscols[colkey]
            columns = columns + str(coldata[0]) + ","
        columns = columns[0:-1]
        columnsRes = myencoding = QInputDialog.getText(self.w, "Scegli le colonne", "Indica le colonne da controllare separate da virgole", QLineEdit.Normal, columns)[0]
        columns = columnsRes.split(",")
        filterdifferent = False
        ret = QMessageBox.question(self.w,'Domanda', "Vuoi selezionare le righe diverse? Se scegli no, verranno estratte solo le righe uguali", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            filterdifferent = True
        riferimento = self.readcsv(self.w.altrofilename.text())
        corpus = self.readcsv(self.w.corpora.item(0).text())
        TBdialog = tableeditor.Form(self, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        for colkey in self.corpuscols:
            coldata = self.corpuscols[colkey]
            TBdialog.addcolumn(coldata[1], coldata[0])
        TBdialog.addcolumn("Riga", len(self.corpuscols))
        TBdialog.addcolumn("Differenza", len(self.corpuscols)+1)
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        totallines = len(corpus)
        print("Corpus lines:")
        print(len(corpus))
        print("Riferimento lines:")
        print(len(riferimento))
        rrow = 0
        crow = 0
        while crow < totallines:
            if crow<100 or crow%100==0:
                self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(crow))
                self.Progrdialog.w.progressBar.setValue(int((crow/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            mydiff = "="
            if len(corpus[crow])<len(self.corpuscols):
                crow = crow +1
                continue
            #else:
                #rrow = crow
            if rrow > len(riferimento)-1:
                rrow = len(riferimento)-1
            while len(riferimento[rrow])<len(self.corpuscols):
                rrow = rrow+1
                if rrow > len(riferimento)-1:
                    rrow = len(riferimento)-1
                    break
            for cl in columns:
                col = int(cl)
                if col > len(riferimento[rrow])-1 or col > len(corpus[crow])-1:
                    continue
                if bool(corpus[crow][col] != riferimento[rrow][col]):
                    tcrow = crow+1
                    try:
                        while bool(corpus[tcrow][col] != riferimento[rrow][col]) and tcrow<len(corpus):
                            tcrow = tcrow+1
                    except:
                        pass
                    trrow = rrow+1
                    try:
                        while bool(corpus[crow][col] != riferimento[trrow][col])and trrow<len(riferimento):
                            trrow = trrow+1
                    except:
                        pass
                    if (tcrow-crow) < (trrow-rrow) and tcrow < len(corpus)-1:
                        for r in range(crow,tcrow):
                            riga = corpus[r]
                            rigan = str(r)
                            mydiff = "-"
                            self.addcorpusline(TBdialog, riga, rigan, mydiff)
                        crow = tcrow
                    elif (tcrow-crow) > (trrow-rrow) and trrow < len(riferimento)-1:
                        for r in range(rrow,trrow):
                            riga = riferimento[r]
                            rigan = str(r)
                            mydiff = "+"
                            self.addcorpusline(TBdialog, riga, rigan, mydiff)
                        rrow = trrow
                    else:
                        riga = corpus[crow]
                        rigan = str(crow)
                        mydiff = "!"
                        print(corpus[crow][col]+":"+riferimento[rrow][col])
                        self.addcorpusline(TBdialog, riga, rigan, mydiff)
                    break
            if bool(not filterdifferent and mydiff == "="):
                self.addcorpusline(TBdialog, riga, rigan, mydiff)
            crow = crow +1
            rrow = rrow+1
        self.Progrdialog.accept()
        TBdialog.show()

    def addcorpusline(self, TBdialog, riga, el2 = "", el3 = ""):
        tbrow = TBdialog.addlinetotable(str(riga[0]), 0)
        for colkey in self.corpuscols:
            coldata = self.corpuscols[colkey]
            if coldata[0] == 0:
                continue
            TBdialog.setcelltotable(str(riga[coldata[0]]), tbrow, coldata[0])
        if el2 != "":
            TBdialog.setcelltotable(str(el2), tbrow, len(self.corpuscols))
        if el3 != "":
            TBdialog.setcelltotable(str(el3), tbrow, len(self.corpuscols)+1)

    def do_confronta(self, context):
        ignorethis = QInputDialog.getText(self.w, "Devo ignorare qualcosa?", "Se devo ignorare delle parole, scrivi qui l'espressione regolare. Altrimenti, lascia la casella vuota.", QLineEdit.Normal, self.ignoretext)[0]
        normalizzazionecorpus = 0
        if self.w.occ_ds.isChecked():
            normalizzazionecorpus = int(QInputDialog.getInt(self.w, "Normalizzazione", "Puoi indicare il numero di token in base al quale standardizzare i corpora. Se lasci questo valore a zero, Bran calcolerà automaticamente la dimensione adeguata per ciascun corpus.")[0])
        thisname = []
        if context != "generico" and context != "multicolonna":
            riferimentoName = self.getRiferimento(context)
        else:
            riferimentoName = self.w.altrofilename.text()
        riferimento = ""
        try:
            riferimento = self.readcsv(riferimentoName)
        except:
            print("Impossibile leggere la tabella di riferimento")
            if context == "multicolonna":
                try:
                    riferimento = self.readcsv(self.w.corpora.item(0).text())
                except:
                  return
            else:
                return
        TBdialog = tableeditor.Form(self, self.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(context, 0)
        self.Progrdialog = progress.Form(self)
        self.Progrdialog.show()
        thistext = ""
        thisvalue = ""
        indexes = 1 + self.w.corpora.count()
        multivalcols = []
        if context == "multicolonna":
            if self.w.multi_all.isChecked():
                if self.w.corpora.count() == 0:
                    multivalcols = list(range(len(riferimento[0])))
                else:
                    corpus = self.readcsv(self.w.corpora.item(0).text())
                    multivalcols = list(range(len(corpus[0])))
                multivalcols.remove(self.w.multiRifValue.value())
                multivalcols.remove(self.w.multiConfKey.value())
            else:
                multivalcols = self.w.multiConfValue.text().split(",")
            indexes = 1+ len(multivalcols)
        outputcol = 1
        for i in range(indexes):
            corpKeyCol = 0
            corpValueCol = 1
            if context == "generico":
                corpKeyCol = self.w.genConfKey.value()
                corpValueCol = self.w.genConfVal.value()
                if i == 0:
                    corpKeyCol = self.w.genRifKey.value()
                    corpValueCol = self.w.genRifVal.value()
                if self.w.gen_diff.isChecked():
                    self.w.occ_diff.setChecked(True)
                if self.w.gen_ds.isChecked():
                    self.w.occ_ds.setChecked(True)
                if self.w.gen_rms.isChecked():
                    self.w.occ_rms.setChecked(True)
                if self.w.gen_tfidf.isChecked():
                    self.w.tfidf.setChecked(True)
            startrow = 0
            if self.w.ignorefirstrow.isChecked():
                startrow = 1
            if i == 0:
                corpus = riferimento
                colname = os.path.basename(riferimentoName)
            elif context != "multicolonna":
                corpus = self.readcsv(self.w.corpora.item(i-1).text())
                colname = os.path.basename(self.w.corpora.item(i-1).text())
            if context == "multicolonna":
                if self.w.multi_diff.isChecked():
                    self.w.occ_diff.setChecked(True)
                if self.w.multi_ds.isChecked():
                    self.w.occ_ds.setChecked(True)
                if self.w.multi_rms.isChecked():
                    self.w.occ_rms.setChecked(True)
                if self.w.multi_tfidf.isChecked():
                    self.w.tfidf.setChecked(True)
                corpKeyCol = self.w.multiConfKey.value()
                if i == 0:
                    corpus = riferimento
                    corpValueCol = self.w.multiRifValue.value()
                else:
                    if self.w.corpora.count() == 0:
                        corpus = riferimento
                    else:
                        corpus = self.readcsv(self.w.corpora.item(0).text())
                    corpValueCol = int(multivalcols[i-1])
                tempcrp = []
                for row in range(len(corpus)):
                    try:
                        tempcrp.append([corpus[row][corpKeyCol], corpus[row][corpValueCol]])
                    except:
                        continue
                corpus = tempcrp
                corpKeyCol = 0
                corpValueCol = 1
                colname = str(i-1)
                if self.w.ignorefirstrow.isChecked():
                    colname = corpus[0][corpValueCol]
            TBdialog.addcolumn(colname, i+1)
            if self.w.occ_ds.isChecked():
                TBdialog.addcolumn(colname+" SCARTO", outputcol+1)
            if self.w.occ_rms.isChecked():
                TBdialog.addcolumn(colname+" RMS", outputcol+1)
            if self.w.tfidf.isChecked():
                TBdialog.addcolumn(colname+" TF-IDF", outputcol+1)
            totallines = len(corpus)
            for row in range(startrow, len(corpus)):
                if row<100 or row%100==0:
                    self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                try:
                    thistext = corpus[row][corpKeyCol]
                    if ignorethis != "":
                        thistext = re.sub(ignorethis, "", thistext)
                    if thistext == "":
                        continue
                    thisvalue = 0
                    if context == "Occorrenze PoS":
                        try:
                            thistext = self.legendaPos[corpus[row][corpKeyCol]][0]
                        except:
                            thistext = corpus[row][corpKeyCol]
                    try:
                        thisvalue = corpus[row][corpValueCol]
                    except:
                        thisvalue = "1"
                    tbrow = TBdialog.finditemincolumn(thistext, col=0, matchexactly = True, escape = True)
                    if tbrow>=0:
                        if self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked() or self.w.tfidf.isChecked():
                            tbcol = outputcol
                        else:
                            tbcol = i+1
                        try:
                            tbval = TBdialog.w.tableWidget.item(tbrow,tbcol).text() + thisvalue
                        except:
                            tbval = thisvalue
                        TBdialog.setcelltotable(str(tbval), tbrow, tbcol)
                    else:
                        TBdialog.addlinetotable(thistext, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        if bool(self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked() or self.w.tfidf.isChecked()) and i>0:
                            TBdialog.setcelltotable(str(thisvalue), tbrow, outputcol)
                            TBdialog.setcelltotable("0", tbrow, outputcol+1)
                        else:
                            TBdialog.setcelltotable(str(thisvalue), tbrow, i+1)
                        for itemp in range(1,i+1):
                            TBdialog.setcelltotable("0", tbrow, itemp)
                except:
                    thistext = ""
            if self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked() or self.w.tfidf.isChecked():
                outputcol = outputcol + 2
            else:
                outputcol = outputcol + 1
        totallines = TBdialog.w.tableWidget.rowCount()
        coltotal = []
        dimcorp = []
        if self.w.dopercent.isChecked() or self.w.occ_ds.isChecked() or self.w.tfidf.isChecked():
            for col in range(1,TBdialog.w.tableWidget.columnCount()):
                thistotal = 0.0
                for row in range(totallines):
                    if row<100 or row%100==0:
                        self.Progrdialog.w.testo.setText("Sto sommando la riga numero "+str(row))
                        self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                        QApplication.processEvents()
                    if self.Progrdialog.w.annulla.isChecked():
                        return
                    try:
                        teststring = TBdialog.w.tableWidget.item(row,col).text()
                        thistotal = thistotal + float(teststring)
                    except:
                        teststring = ""
                coltotal.append(thistotal)
                if normalizzazionecorpus == 0:
                    dimCorpus = self.getCorpusDim(thistotal)
                    normalizzazionecorpus = dimCorpus
                else:
                    dimCorpus = normalizzazionecorpus
                dimcorp.append(dimCorpus)
        col = 0
        while col < TBdialog.w.tableWidget.columnCount():
            for row in range(totallines):
                if row<100 or row%100==0:
                    self.Progrdialog.w.testo.setText("Sto controllando la riga numero "+str(row))
                    self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                    QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                try:
                    if col > 0:
                        try:
                            if float(TBdialog.w.tableWidget.item(row,col).text()) == 0:
                                TBdialog.setcelltotable("0", row, col)
                        except:
                            TBdialog.setcelltotable("0", row, col)
                        teststring = TBdialog.w.tableWidget.item(row,col).text()
                        if self.w.dopercent.isChecked():
                            thisvalue = str(float((float(teststring)/coltotal[col-1])*100.0))
                            TBdialog.setcelltotable(thisvalue, row, col)
                            teststring = thisvalue
                        if self.w.occ_ds.isChecked() and i>0:
                            try:
                                rifval = float(TBdialog.w.tableWidget.item(row,1).text())
                                if not self.w.dopercent.isChecked():
                                    teststring = str(float((float(teststring)/coltotal[col-1])*100.0))
                                    rifval = str(float((float(rifval)/coltotal[0])*100.0))
                                rifval = float(rifval)/100.0
                                myval = float(teststring)/100.0
                                tbval = float((float(myval*dimcorp[col-1])-(rifval*dimcorp[col-1]))/math.sqrt(rifval*dimcorp[col-1]))
                            except:
                                rifval = 0.0
                                tbval = 0.0
                            TBdialog.setcelltotable(str(tbval), row, col+1)
                            if row == 0:
                                tmpstr = TBdialog.w.tableWidget.horizontalHeaderItem(col+1).text()
                                TBdialog.w.tableWidget.horizontalHeaderItem(col+1).setText(tmpstr + " per " + str(dimcorp[col-1]) + " token")
                        if self.w.occ_rms.isChecked() and i>0:
                            N = 2
                            try:
                                rifval = float(TBdialog.w.tableWidget.item(row,1).text())
                            except:
                                rifval = 0.0
                            tbval = math.sqrt((math.pow(rifval,2)+ math.pow(float(teststring),2))/N)
                            TBdialog.setcelltotable(str(tbval), row, col+1)
                        if self.w.tfidf.isChecked() and i>0:
                            N = float(TBdialog.w.tableWidget.columnCount()-1)/2
                            if not self.w.dopercent.isChecked():
                                teststring = str(float((float(teststring)/coltotal[col-1])*100.0))
                            tfval = float(float(teststring)/100.0)
                            wINd = 0
                            wdcol = 1
                            while wdcol < TBdialog.w.tableWidget.columnCount():
                                try:
                                    tmptest = 1/float(TBdialog.w.tableWidget.item(row,wdcol).text()) #should fail if content of the cell is zero
                                    wINd = wINd +1
                                    wdcol = wdcol +2
                                except:
                                    wdcol = wdcol +2
                            try:
                                idfval = math.log10(N/float(wINd))
                            except:
                                idfval = 0.0
                            tfidfval = tfval * idfval
                            TBdialog.setcelltotable(str(tfidfval), row, col+1)
                except Exception as e:
                    print(str(e))
            if bool(self.w.occ_ds.isChecked() or self.w.occ_rms.isChecked() or self.w.tfidf.isChecked()) and col >0:
                col = col + 2
            else:
                col = col + 1
        self.Progrdialog.accept()
        TBdialog.show()
