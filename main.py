#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#would be nice: https://github.com/yarolig/pyqtc
#Deploy as Docker container on Windows: https://robscode.onl/docker-run-gui-app-in-linux-container-on-windows-host/


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
import json
import subprocess
from socket import timeout
import platform
import mmap

arch = platform.architecture()[0]
if arch != '64bit':
    from tkinter import messagebox
    messagebox.showinfo("Pericolo", "Sembra che tu stia utilizzando Python a 32bit. La maggioranza delle librerie moderne (come PySide2) utilizza codice a 64bit, per poter sfruttare appieno la RAM. Per favore, installa Python a 64bit.")
    sys.exit(1)

try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        from tkinter import messagebox
        thispkg = "le librerie grafiche"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        from PySide2.QtWidgets import QApplication
    except:
        try:
            from pip._internal import main
            main(["install", "--index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/", "pyside2", "--trusted-host", "download.qt.io"])
            from PySide2.QtWidgets import QApplication
        except:
            sys.exit(1)


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



from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor
from forms import tint
from forms import progress
from forms import sessione
from forms import ripetizioni
from forms import about



class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/mainwindow.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader(self)
        self.w = loader.load(file)
        self.setCentralWidget(self.w)
        self.setWindowTitle("Bran")
        self.w.replace_in_corpus.clicked.connect(self.replaceCorpus)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.delselected.clicked.connect(self.delselected)
        self.w.actionScarica_corpus_da_sito_web.triggered.connect(self.web2corpus)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionEsporta_corpus_in_CSV_unico.triggered.connect(self.salvaCSV)
        self.w.actionCalcola_densit_lessicale.triggered.connect(self.densitalessico)
        self.w.actionDa_file_txt.triggered.connect(self.loadtxt)
        self.w.actionTraduci_i_tag_PoS_in_forma_leggibile.triggered.connect(self.translatePos)
        self.w.actionDa_file_JSON.triggered.connect(self.loadjson)
        self.w.actionDa_file_CSV.triggered.connect(self.loadCSV)
        self.w.actionConfigurazione_Tint.triggered.connect(self.loadConfig)
        self.w.actionSalva.triggered.connect(self.salvaProgetto)
        self.w.actionApri.triggered.connect(self.apriProgetto)
        self.w.actionEditor_di_testo.triggered.connect(self.texteditor)
        self.w.actionAbout_Bran.triggered.connect(self.aboutbran)
        self.w.actionStatistiche_con_VdB.triggered.connect(self.statisticheconvdb)
        self.w.actionTrova_ripetizioni.triggered.connect(self.trovaripetizioni)
        self.w.actionConta_verbi.triggered.connect(self.contaverbi)
        self.corpuscols = {
            'IDcorpus': 0,
            'Orig': 1,
            'Lemma': 2,
            'pos': 3,
            'ner': 4,
            'feat': 5,
            'IDword': 6
        }
        self.legendaPos = {"A":["aggettivo", "none"],"AP":["agg. Poss", "none"],"B":["avverbio", "none"],"B+PC":["avverbio+pron. clit. ", "none"],"BN":["avv, negazione", "none"],"CC":["cong. coord", "none"],"CS":["cong. Sub.", "none"],"DD":["det. dim.", "none"],"DE":["det. esclam. ", "none"],"DI":["det. indefinito", "none"],"DQ":["det. int.", "none"],"DR":["det. rel", "none"],"E":["preposizione", "none"],"E+RD":["prep. art. ", "none"],"FB":["punteggiatura - \"\" () «» - - ", "none"],"FC":["punteggiatura - : ;", "none"],"FF":["punteggiatura - ,", "none"],"FS":["punteggiatura - .?!", "none"],"I":["interiezione", "none"],"N":["numero", "none"],"NO":["numerale", "none"],"PC":["pron. clitico", "none"],"PC+PC":["pron. clitico+clitico", "none"],"PD":["pron. dimostrativo", "none"],"PE":["pron. pers. ", "none"],"PI":["pron. indef.", "none"],"PP":["pron. poss.", "none"],"PQ":["pron. interr.", "none"],"PR":["pron. rel.", "none"],"RD":["art. det.", "none"],"RI":["art. ind.", "none"],"S":["sost.", "none"],"SP":["nome proprio", "none"],"SW":["forestierismo", "none"],"T":["determinante (tutt*)", "none"],"V":["verbo", "none"],"V+PC":["verbo + pron. clitico", "none"],"V+PC+PC":["verbo + pron. clitico + pron clitico", "none"],"VA":["verbo ausiliare", "none"],"VA+PC":["verbo ausiliare + pron.clitico", "none"],"VM":["verbo mod", "none"],"VM+PC":["verbo mod + pron. clitico", "none"],"X":["altro", "none"]}
        self.ignorepos = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "punteggiatura - .?!", "altro"]
        self.separator = "\t"
        self.enumeratecolumns(self.w.ccolumn)
        QApplication.processEvents()
        self.alreadyChecked = False
        self.ImportingFile = False
        self.sessionFile = ""
        self.sessionDir = "."
        self.mycfgfile = QDir.homePath() + "/.brancfg"
        self.mycfg = json.loads('{"javapath": "", "tintpath": "", "tintaddr": "", "tintport": "", "sessions" : []}')
        self.loadPersonalCFG()
        self.loadSession()
        self.loadConfig()
        self.txtloadingstopped()

    def loadConfig(self):
        self.TintSetdialog = tint.Form(self, self.mycfg)
        self.TintSetdialog.w.start.clicked.connect(self.runServer)
        self.TintSetdialog.w.check.clicked.connect(self.checkServer)
        self.TintSetdialog.exec()
        self.Java = self.TintSetdialog.w.java.text()
        self.TintDir = self.TintSetdialog.w.tintlib.text()
        self.TintPort = self.TintSetdialog.w.port.text()
        self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
        #self.Java -classpath $_CLASSPATH eu.fbk.dh.tint.runner.TintServer -p self.TintPort
        if not self.TintSetdialog.notint:
            self.mycfg["javapath"] = self.TintSetdialog.w.java.text()
            self.mycfg["tintpath"] = self.TintSetdialog.w.tintlib.text()
            self.mycfg["tintaddr"] = self.TintSetdialog.w.address.text()
            self.mycfg["tintport"] = self.TintSetdialog.w.port.text()
            self.savePersonalCFG()

    def loadSession(self):
        seSdialog = sessione.Form(self)
        seSdialog.loadhistory(self.mycfg["sessions"])
        seSdialog.exec()
        self.sessionFile = ""
        if seSdialog.result():
            self.sessionFile = seSdialog.filesessione
            if os.path.isfile(self.sessionFile):
                self.setWindowTitle("Bran - "+self.sessionFile)
                self.sessionDir = os.path.abspath(os.path.dirname(self.sessionFile))
                tmpsess = [self.sessionFile]
                for i in range(len(self.mycfg["sessions"])-1):
                    it = len(self.mycfg["sessions"]) -i
                    try:
                        ind = tmpsess.index(self.mycfg["sessions"][it])
                    except:
                        tmpsess.append(self.mycfg["sessions"][it])
                    if i > 10:
                        break
                self.mycfg["sessions"] = tmpsess
                self.savePersonalCFG()


    def loadPersonalCFG(self):
        try:
            text_file = open(self.mycfgfile, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
            self.mycfg = json.loads(lines)
        except:
            print("Creo il file di configurazione")

    def savePersonalCFG(self):
        cfgtxt = json.dumps(self.mycfg)
        text_file = open(self.mycfgfile, "w", encoding='utf-8')
        text_file.write(cfgtxt)
        text_file.close()

    def apriProgetto(self):
        self.loadSession()
        self.txtloadingstopped()

    def replaceCorpus(self):
        repCdialog = regex_replace.Form(self)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.exec()
        if repCdialog.result():
            for row in range(self.w.corpus.rowCount()):
                for col in range(self.w.corpus.columnCount()):
                    if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                        origstr = self.w.corpus.item(row,col).text()
                        newstr = ""
                        if repCdialog.w.ignorecase.isChecked():
                            newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.IGNORECASE|re.DOTALL)
                        else:
                            newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.DOTALL)
                        self.setcelltocorpus(newstr, row, col)

    def contaoccorrenze(self):
        thisname = []
        for col in range(self.w.corpus.columnCount()):
            thisname.append(self.w.corpus.horizontalHeaderItem(col).text())
        column = QInputDialog.getItem(self, "Scegli la colonna", "Su quale colonna devo contare le occorrenze?",thisname,current=0,editable=False)
        col = thisname.index(column[0])
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn(column[0], 0)
        TBdialog.addcolumn("Occorrenze", 1)
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.myprogress.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.w.corpus.item(row,col).text()
            except:
                thistext = ""
            tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
            if len(tbitem)>0:
                tbrow = tbitem[0].row()
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        self.myprogress.Progrdialog.accept()
        TBdialog.exec()

    def contaverbi(self):
        poscol = self.corpuscols["pos"] #thisname.index(column[0])
        morfcol = self.corpuscols["feat"]
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Modo+Tempo", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.myprogress.Progrdialog.w.annulla.isChecked():
                return
            try:
                thispos = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][0]
            except:
                thispos = ""
            thistext = ""
            thistext2 = ""
            if thispos.split(" ")[0] == "verbo":
                for ind in range(1,4):
                    try:
                        tmpos = self.legendaPos[self.w.corpus.item(row-ind,self.corpuscols['pos']).text()][0]
                        thistext2 = self.w.corpus.item(row,morfcol).text()
                    except:
                        tmpos = ""
                    if tmpos == "verbo ausiliare":
                        thistext = thistext + self.w.corpus.item(row-ind,morfcol).text() + "/"
                        if bool(re.match('^v\+.*?$', thistext))==False:
                            thistext = ""
                        break
                if len(thistext.split("+")) >= 3:
                    tmptext = thistext.split("+")[0] + "+" +thistext.split("+")[1] + "+" +thistext.split("+")[2]
                    thistext = tmptext + "/"
                if len(thistext2.split("+")) >= 3:
                    tmptext = thistext2.split("+")[0] + "+" +thistext2.split("+")[1] + "+" +thistext2.split("+")[2]
                    thistext2 = tmptext
                if bool(re.match('^v\+.*?$', thistext2))==False:
                    thistext2 = ""
                thistext = thistext + thistext2
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
        self.myprogress.Progrdialog.accept()
        TBdialog.exec()

    def trovaripetizioni(self):
        ipunct = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "punteggiatura - .?!", "altro"]
        Repetdialog = ripetizioni.Form(self)
        Repetdialog.loadipos(ipunct)
        Repetdialog.loadallpos(self.legendaPos)
        Repetdialog.exec()
        if Repetdialog.result():
            tokenda = Repetdialog.w.tokenda.value()
            tokena = Repetdialog.w.tokena.value()
            minoccur = Repetdialog.w.minoccurr.value()
            ignorecase = Repetdialog.w.ignorecase.isChecked()
            remspaces = Repetdialog.w.remspaces.isChecked()
            ipunct = []
            for i in range(Repetdialog.w.ignorapos.count()):
                ipunct.append(Repetdialog.w.ignorapos.item(i).text())
            TBdialog = tableeditor.Form(self)
            TBdialog.sessionDir = self.sessionDir
            TBdialog.addcolumn("nGram", 0)
            TBdialog.addcolumn("Occorrenze", 1)
            self.myprogress = progress.ProgressDialog(self.w)
            self.myprogress.start()
            for tokens in range(tokenda, tokena+1):
                self.findngrams(tokens, minoccur, TBdialog, self.myprogress, ignorecase, remspaces, ipunct)
            self.myprogress.Progrdialog.accept()
            TBdialog.exec()

    def findngrams(self, tokens, minoccur, TBdialog, myprogress, ignorecase, remspaces, ipunct):
        mycorpus = ""
        col = self.corpuscols['Orig']
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            myprogress.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if myprogress.Progrdialog.w.annulla.isChecked():
                return
            thispos = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][0]
            if not thispos in ipunct:
                mycorpus = mycorpus + self.w.corpus.item(row,col).text() + " "
        if ignorecase:
            mycorpus = mycorpus.lower()
        searchthis = " "
        #if remspaces:
            #punt = re.escape(" (\.,;!\?)")
            #mycorpus = re.sub(punt, "\1", mycorpus, flags=re.IGNORECASE|re.DOTALL)
            #mycorpus = re.sub("' ", "'", mycorpus, flags=re.IGNORECASE|re.DOTALL)
            #searchthis = " " #we should take care about .,?!;:
        active = True
        pos = 0
        totallines = len(mycorpus)
        while active:
            wpos = pos
            npos = pos
            myprogress.Progrdialog.w.testo.setText("Sto conteggiando il carattere numero "+str(pos))
            myprogress.Progrdialog.w.progressBar.setValue(int((pos/totallines)*100))
            QApplication.processEvents()
            if myprogress.Progrdialog.w.annulla.isChecked():
                return
            #read a specific number of words
            for i in range(tokens):
                wpos = mycorpus.find(searchthis, npos+1)
                if wpos > 0:
                    npos = wpos
            #check if we reached someway the end of text
            if npos > len(mycorpus)-1:
                if pos > len(mycorpus)-1:
                    break
                else:
                    npos = len(mycorpus)-1
            #read this phrase
            tmpstring = mycorpus[pos:npos]
            #look for all occurrences of this phrase
            if tmpstring != "" and tmpstring.count(searchthis)==tokens-1:
                tcount = mycorpus.count(tmpstring)
                if tcount >= minoccur:
                    if remspaces:
                        punt = "( ["+re.escape(".,;!?")+ "])"
                        tmpstring = re.sub(punt, "\1", tmpstring, flags=re.IGNORECASE|re.DOTALL)
                        punt = "(["+re.escape("'’")+ "]) "
                        tmpstring = re.sub(punt, "\1", tmpstring, flags=re.IGNORECASE|re.DOTALL)
                    tbitem = TBdialog.w.tableWidget.findItems(tmpstring,Qt.MatchExactly)
                    if len(tbitem)<=0:
                        TBdialog.addlinetotable(tmpstring, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable(str(tcount), tbrow, 1)
                #newtext = nth_replace(mycorpus, tmpstring, "", 2, "all right")
                #text = newtext
            pos = mycorpus.find(searchthis, pos+1)+1 #continue from next word
            if pos <= 0:
                pos = len(mycorpus)


    def translatePos(self):
        col = self.corpuscols['pos']
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto lavorando sulla riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.myprogress.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.w.corpus.item(row,col).text()
            except:
                thistext = ""
            try:
                newtext = self.legendaPos[thistext][0]
            except:
                newtext = thistext
            self.setcelltocorpus(newtext, row, col)
        self.myprogress.Progrdialog.accept()

    def densitalessico(self):
        col = self.corpuscols['pos']
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Part of Speech", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        TBdialog.addcolumn("Percentuale", 2)
        #calcolo le occorrenze del pos
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.myprogress.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistextO = self.w.corpus.item(row,col).text()
                thistext = self.legendaPos[thistextO][0]
            except:
                thistext = ""
            tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
            if len(tbitem)>0:
                tbrow = tbitem[0].row()
                tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                TBdialog.setcelltotable(str(tbval), tbrow, 1)
            else:
                TBdialog.addlinetotable(thistext, 0)
                tbrow = TBdialog.w.tableWidget.rowCount()-1
                TBdialog.setcelltotable("1", tbrow, 1)
        #calcolo le somme di parole piene e vuote
        totallines = TBdialog.w.tableWidget.rowCount()
        paroletotali = 0
        parolepiene = 0
        parolevuote = 0
        parolenone = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto sommando la riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            thistext = TBdialog.w.tableWidget.item(row,0).text()
            for key in self.legendaPos:
                if thistext == self.legendaPos[key][0]:
                    if "piene" == self.legendaPos[key][1]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,1).text())
                        parolepiene = parolepiene + int(TBdialog.w.tableWidget.item(row,1).text())
                        break
                    if "vuote" == self.legendaPos[key][1]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,1).text())
                        parolevuote = parolevuote + int(TBdialog.w.tableWidget.item(row,1).text())
                        break
                    if "none" == self.legendaPos[key][1]:
                        paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,1).text())
                        parolenone = parolenone + int(TBdialog.w.tableWidget.item(row,1).text())
                        break
        TBdialog.addlinetotable("Parole totali", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(paroletotali), tbrow, 1)
        TBdialog.addlinetotable("Parole piene", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolepiene), tbrow, 1)
        TBdialog.addlinetotable("Parole vuote", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolevuote), tbrow, 1)
        TBdialog.addlinetotable("Altri tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(parolenone), tbrow, 1)
        #calcolo le percentuali
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto calcolando le percentuali su "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            ratio = (float(TBdialog.w.tableWidget.item(row,1).text())/float(paroletotali)*100)
            ratios = f'{ratio:.3f}'
            TBdialog.setcelltotable(ratios, row, 2)
        #mostro i risultati
        self.myprogress.Progrdialog.accept()
        TBdialog.exec()

    def salvaProgetto(self):
        if self.sessionFile == "":
            fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
            if fileName != "":
                self.sessionFile = fileName
        if self.sessionFile != "":
            self.myprogress = progress.ProgressDialog(self.w)
            self.myprogress.start()
            self.CSVsaver(self.sessionFile, self.myprogress.Progrdialog, False)

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        self.CSVsaver(fileName, self.myprogress.Progrdialog, True)

    def CSVsaver(self, fileName, Progrdialog, addheader = False):
        if fileName != "":
            csv = ""
            if addheader:
                for col in range(self.w.corpus.columnCount()):
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.corpus.horizontalHeaderItem(col).text()
            totallines = self.w.corpus.rowCount()
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()
            for row in range(self.w.corpus.rowCount()):
                csv = csv + "\n"
                Progrdialog.w.testo.setText("Sto salvando la riga numero "+str(row))
                Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                for col in range(self.w.corpus.columnCount()):
                    if Progrdialog.w.annulla.isChecked():
                        return
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.corpus.item(row,col).text()
                with open(fileName, "a", encoding='utf-8') as myfile:
                    myfile.write(csv+"\n")
            Progrdialog.accept()

    def web2corpus(self):
        w2Cdialog = url2corpus.Form(self)
        w2Cdialog.exec()

    def delselected(self):
        for i in range(self.w.corpus.selectedItems()):
            row = self.w.corpus.selectedItems()[i].row()
        QMessageBox.warning(self, "Errore", "Funzione non ancora implementata.")

    def enumeratecolumns(self, combo):
        for col in range(self.w.corpus.columnCount()):
            thisname = self.w.corpus.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def dofiltra(self):
        for row in range(self.w.corpus.rowCount()):
            col = self.w.ccolumn.currentIndex()
            ctext = self.w.corpus.item(row,col).text()
            ftext = self.w.cfilter.text()
            if bool(re.match(ftext, ctext)):
                self.w.corpus.setRowHidden(row, False)
            else:
                self.w.corpus.setRowHidden(row, True)

    def cancelfiltro(self):
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.setRowHidden(row, False)

    def loadtxt(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
        self.TCThread = tint.TintCorpus(self.w, fileNames, self.corpuscols, self.TintAddr)
        self.TCThread.outputcsv = self.sessionFile
        self.TCThread.finished.connect(self.txtloadingstopped)
        self.TCThread.start()

    def loadjson(self):
        QMessageBox.information(self, "Attenzione", "Caricare un file JSON prodotto manualmente può essere pericoloso: se i singoli paragrafi sono troppo grandi, il programma può andare in crash. Utilizza questa funzione solo se sai esattamente cosa stai facendo.")
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file JSON", self.sessionDir, "Json files (*.txt *.json)")[0]
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    if self.w.corpus.rowCount() >0:
                        fileID = int(self.w.corpus.item(self.w.corpus.rowCount()-1,0).text().split("_")[0])
                    #QApplication.processEvents()
                    fileID = fileID+1
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    IDcorpus = str(fileID)+"_"+os.path.basename(fileName)
                    try:
                        myarray = json.loads(lines)
                    except:
                        myarray = {'sentences': []}
                    for sentence in myarray["sentences"]:
                        for token in sentence["tokens"]:
                            rowN = self.addlinetocorpus(IDcorpus, self.corpuscols["IDcorpus"])
                            self.setcelltocorpus(str(token["index"]), rowN, self.corpuscols["IDword"])
                            self.setcelltocorpus(str(token["originalText"]), rowN, self.corpuscols["Orig"])
                            self.setcelltocorpus(str(token["lemma"]), rowN, self.corpuscols["Lemma"])
                            self.setcelltocorpus(str(token["pos"]), rowN, self.corpuscols["pos"])
                            self.setcelltocorpus(str(token["ner"]), rowN, self.corpuscols["ner"])
                            self.setcelltocorpus(str(token["full_morpho"]), rowN, self.corpuscols["feat"])

    def loadCSV(self):
        if self.ImportingFile == False:
            fileNames = QFileDialog.getOpenFileNames(self, "Apri file CSV", self.sessionDir, "File CSV (*.txt *.csv)")[0]
            self.myprogress = progress.ProgressDialog(self.w)
            self.myprogress.start()
            self.ImportingFile = True
            self.CSVloader(fileNames, self.myprogress.Progrdialog)

    def CSVloader(self, fileNames, Progrdialog):
        fileID = 0
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    if not os.path.getsize(fileName) > 0:
                        #break
                        Progrdialog.reject()
                        self.ImportingFile = False
                        return
                    try:
                        totallines = self.linescount(fileName)
                    except:
                        Progrdialog.reject()
                        self.ImportingFile = False
                        return
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    rowN = 0
                    for line in lines.split('\n'):
                        Progrdialog.w.testo.setText("Sto importando la riga numero "+str(rowN))
                        Progrdialog.w.progressBar.setValue(int((rowN/totallines)*100))
                        QApplication.processEvents()
                        colN = 0
                        for col in line.split(self.separator):
                            if Progrdialog.w.annulla.isChecked():
                                Progrdialog.reject()
                                self.ImportingFile = False
                                return
                            if colN == 0:
                                if col == "":
                                    break
                                rowN = self.addlinetocorpus(str(col), 0) #self.corpuscols["IDcorpus"]
                            self.setcelltocorpus(str(col), rowN, colN)
                            colN = colN + 1
        Progrdialog.accept()
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
                self.myprogress = progress.ProgressDialog(self.w)
                self.myprogress.start()
                self.ImportingFile = True
                fileNames = ['']
                fileNames[0] = self.sessionFile
                self.CSVloader(fileNames, self.myprogress.Progrdialog)
            except:
                try:
                    self.myprogress.reject()
                    self.ImportingFile = False
                except:
                    return

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
                QMessageBox.information(self, "Come usare il server su Windows", "Sembra che tu stia usando Windows. Su questo sistema, per utilizzare il server Tint, devi chiudere l'interfaccia di Bran, lasciando aperto solo il terminale. Poi puoi aprire di nuovo Bran (caricherà un altro terminale e una nuova interfaccia grafica).")
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
        row = self.w.corpus.rowCount()
        self.w.corpus.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.corpus.setItem(row, column, titem)
        self.w.corpus.setCurrentCell(row, column)
        return row

    def setcelltocorpus(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.corpus.setItem(row, column, titem)

    def texteditor(self):
        te = texteditor.TextEditor()
        te.show()

    def aboutbran(self):
        aw = about.Form(self)
        aw.exec()

    def statisticheconvdb(self):
        ret = QMessageBox.question(self,'Domanda', "Vuoi ignorare la punteggiatura?", QMessageBox.Yes | QMessageBox.No)
        #TODO: aggiungere forestierismi presenti (occorrenze per ogni parola, percentuale su parole totali)
        col = self.corpuscols['Lemma']
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Lemma", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        TBdialog.addcolumn("Presente in VdB 1980", 2)
        TBdialog.addcolumn("Presente in VdB 2016", 3)
        #calcolo le occorrenze del pos
        self.myprogress = progress.ProgressDialog(self.w)
        self.myprogress.start()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.myprogress.Progrdialog.w.annulla.isChecked():
                return
            thispos = "False"
            try:
                thistext = self.w.corpus.item(row,col).text()
                if ret == QMessageBox.Yes:
                    thispos = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][0]
            except:
                thistext = ""
            if not thispos in self.ignorepos and thistext != "":
                tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                if len(tbitem)>0:
                    tbrow = tbitem[0].row()
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 1)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable("1", tbrow, 1)
        #carico i vdb
        self.vdb2016 = []
        self.vdbfile16 = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/vdb2016.txt"
        if os.path.isfile(self.vdbfile16):
            self.vdb2016 = [line.rstrip('\n') for line in open(self.vdbfile16, "r", encoding='utf-8')]
        self.vdb1980 = []
        self.vdbfile80 = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/vdb1980.txt"
        if os.path.isfile(self.vdbfile80):
            self.vdb1980 = [line.rstrip('\n') for line in open(self.vdbfile80, "r", encoding='utf-8')]
        #controllo per ogni parola se appartiene a un VdB
        totallines = TBdialog.w.tableWidget.rowCount()
        paroletotali = 0
        parole2016 = 0
        parole1980 = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto controllando la riga numero "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            thistext = TBdialog.w.tableWidget.item(row,0).text()
            if thistext in self.vdb1980:
                TBdialog.setcelltotable("1", row, 2)
            else:
                TBdialog.setcelltotable("0", row, 2)
            if thistext in self.vdb2016:
                TBdialog.setcelltotable("1", row, 3)
            else:
                TBdialog.setcelltotable("0", row, 3)
        #calcolo le percentuali
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.myprogress.Progrdialog.w.testo.setText("Sto calcolando le somme su "+str(row))
            self.myprogress.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            paroletotali = paroletotali + int(TBdialog.w.tableWidget.item(row,1).text())
            parole1980 = parole1980 + int(TBdialog.w.tableWidget.item(row,2).text())*int(TBdialog.w.tableWidget.item(row,1).text())
            parole2016 = parole2016 + int(TBdialog.w.tableWidget.item(row,3).text())*int(TBdialog.w.tableWidget.item(row,1).text())
        TBdialog.addlinetotable("Totale", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(paroletotali), tbrow, 1)
        TBdialog.setcelltotable(str(parole1980), tbrow, 2)
        TBdialog.setcelltotable(str(parole2016), tbrow, 3)
        TBdialog.addlinetotable("Percentuale", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(paroletotali)/float(paroletotali)*100)
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        ratio = (float(parole1980)/float(paroletotali)*100)
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 2)
        ratio = (float(parole2016)/float(paroletotali)*100)
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 3)
        #mostro i risultati
        self.myprogress.Progrdialog.accept()
        TBdialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())



