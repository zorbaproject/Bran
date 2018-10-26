#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#would be nice: https://github.com/yarolig/pyqtc

#Lavorare con R: https://www.tidytextmining.com/twitter.html

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

try:
    from pyquery import PyQuery as pqtest
    from lxml import etree
except:
    try:
        from tkinter import messagebox
        thispkg = "le librerie per scaricare i tweet"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "pyquery"])
        pip.main(["install", "lxml"])
        messagebox.showinfo("Prendi nota", "Probabilmente dovrai installare i pacchetti di sviluppo, su Ubuntu basta questo comando: sudo apt-get install libxml2-dev libxslt1-dev python-dev")
    except:
        try:
            from pip._internal import main as pipmain
            from tkinter import messagebox
            pipmain(["install", "pyquery"])
            pipmain(["install", "lxml"])
            messagebox.showinfo("Prendi nota", "Probabilmente dovrai installare i pacchetti di sviluppo, su Ubuntu basta questo comando: sudo apt-get install libxml2-dev libxslt1-dev python-dev")
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
from forms import confronto
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
        self.w.actionSostituisci_nel_corpus_con_RegEx.triggered.connect(self.replaceCorpus)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.delselected.clicked.connect(self.delselected)
        self.w.actionRimuovi_righe_selezionate.triggered.connect(self.delselected)
        self.w.actionScarica_corpus_da_sito_web.triggered.connect(self.web2corpus)
        self.w.actionEsporta_corpus_in_un_CSV_per_ogni_ID.triggered.connect(self.esportaCSVperID)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionEsporta_corpus_in_CSV_unico.triggered.connect(self.salvaCSV)
        self.w.actionEsporta_vista_attuale_in_CSV.triggered.connect(self.esportavistaCSV)
        self.w.actionRimuovi_vista_attuale_dal_corpus.triggered.connect(self.removevisiblerows)
        self.w.actionCalcola_densit_lessicale.triggered.connect(self.densitalessico)
        self.w.actionDa_file_txt.triggered.connect(self.loadtxt)
        #self.w.actionTraduci_i_tag_PoS_in_forma_leggibile.triggered.connect(self.translatePos)
        self.w.actionDa_file_JSON.triggered.connect(self.loadjson)
        self.w.actionDa_file_CSV.triggered.connect(self.loadCSV)
        self.w.actionConfigurazione_Tint.triggered.connect(self.loadConfig)
        self.w.actionSalva.triggered.connect(self.salvaProgetto)
        self.w.actionApri.triggered.connect(self.apriProgetto)
        self.w.actionChiudi.triggered.connect(self.chiudiProgetto)
        self.w.actionEditor_di_testo.triggered.connect(self.texteditor)
        self.w.actionConfronta_corpora.triggered.connect(self.confronto)
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
        self.legendaPos = {"A":["aggettivo", "aggettivi", "piene"],"AP":["agg. poss", "aggettivi", "piene"],"B":["avverbio", "avverbi", "piene"],"B+PC":["avverbio+pron. clit. ", "avverbi", "piene"],"BN":["avv, negazione", "avverbi", "piene"],"CC":["cong. coord", "congiunzioni", "vuote"],"CS":["cong. sub.", "congiunzioni", "vuote"],"DD":["det. dim.", "aggettivi", "piene"],"DE":["det. esclam.", "aggettivi", "piene"],"DI":["det. indefinito", "aggettivi", "piene"],"DQ":["det. interr.", "aggettivi", "piene"],"DR":["det. Rel", "aggettivi", "piene"],"E":["preposizione", "preposizioni", "vuote"],"E+RD":["prep. art. ", "preposizioni", "vuote"],"FB":["punteggiatura - \"\" () «» - - ", "punteggiatura", "none"],"FC":["punteggiatura - : ;", "punteggiatura", "none"],"FF":["punteggiatura - ,", "punteggiatura", "none"],"FS":["punteggiatura - .?!", "punteggiatura", "none"],"I":["interiezione", "interiezioni", "vuote"],"N":["numero", "altro", "none"],"NO":["numerale", "aggettivi", "piene"],"PC":["pron. Clitico", "pronomi", "vuote"],"PC+PC":["pron. clitico+clitico", "pronomi", "vuote"],"PD":["pron. dimostrativo", "pronomi","vuote"],"PE":["pron. pers. ", "pronomi", "vuote"],"PI":["pron. indef.", "pronomi", "vuote"],"PP":["pron. poss.", "pronomi", "vuote"],"PQ":["pron. interr.", "pronomi", "vuote"],"PR":["pron. rel.", "pronomi", "vuote"],"RD":["art. Det.", "articoli", "vuote"],"RI":["art. ind.", "articoli", "vuote"],"S":["sost.", "sostantivi", "piene"],"SP":["nome proprio", "sostantivi", "piene"],"SW":["forestierismo", "altro", "none"],"T":["det. coll.)", "aggettivi", "piene"],"V":["verbo", "verbi", "piene"],"V+PC":["verbo + pron. clitico", "verbi", "piene"],"V+PC+PC":["verbo + pron. clitico + pron clitico", "verbi", "piene"],"VA":["verbo ausiliare", "verbi", "piene"],"VA+PC":["verbo ausiliare + pron.clitico", "verbi", "piene"],"VM":["verbo mod", "verbi", "piene"],"VM+PC":["verbo mod + pron. clitico", "verbi", "piene"],"X":["altro", "altro", "none"]}
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
                for i in range(len(self.mycfg["sessions"])-1,-1,-1):
                    if not self.mycfg["sessions"][i] in tmpsess:
                        tmpsess.append(self.mycfg["sessions"][i])
                    if i > 10:
                        break
                self.mycfg["sessions"] = tmpsess
                #print(tmpsess)
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

    def chiudiProgetto(self):
        self.sessionFile = ""
        self.sessionDir = "."
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.removeRow(0)
            if row<100 or row%100==0:
                QApplication.processEvents()
        self.setWindowTitle("Bran")

    def replaceCorpus(self):
        repCdialog = regex_replace.Form(self)
        repCdialog.setModal(False)
        self.enumeratecolumns(repCdialog.w.colcombo)
        repCdialog.exec()
        if repCdialog.result():
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            totallines = self.w.corpus.rowCount()
            for row in range(self.w.corpus.rowCount()):
                self.Progrdialog.w.testo.setText("Sto cercando nella riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                for col in range(self.w.corpus.columnCount()):
                    if repCdialog.w.colcheck.isChecked() or (not repCdialog.w.colcheck.isChecked() and col == repCdialog.w.colcombo.currentIndex()):
                        origstr = self.w.corpus.item(row,col).text()
                        newstr = ""
                        if repCdialog.w.ignorecase.isChecked():
                            newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.IGNORECASE|re.DOTALL)
                        else:
                            newstr = re.sub(repCdialog.w.orig.text(), repCdialog.w.dest.text(), origstr, flags=re.DOTALL)
                        self.setcelltocorpus(newstr, row, col)
            self.Progrdialog.accept()

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
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistext = self.w.corpus.item(row,col).text()
                if col == self.corpuscols["pos"]:
                    thistext = self.legendaPos[thistext][0]
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
        self.Progrdialog.accept()
        TBdialog.exec()

    def contaverbi(self):
        poscol = self.corpuscols["pos"] #thisname.index(column[0])
        morfcol = self.corpuscols["feat"]
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Modo+Tempo", 0)
        TBdialog.addcolumn("Occorrenze", 1)
        TBdialog.addcolumn("Percentuali", 1)
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thispos = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][0]
            except:
                thispos = ""
            thistext = ""
            thistext2 = ""
            if thispos.split(" ")[0] == "verbo":
                thistext = self.w.corpus.item(row,morfcol).text()
            if "ausiliare" in thispos:
                for ind in range(1,4):
                    try:
                        tmpos = self.legendaPos[self.w.corpus.item(row+ind,self.corpuscols['pos']).text()][0]
                    except:
                        tmpos = ""
                    if "verbo" in tmpos:
                        thistext = ""
                        break
            elif thispos.split(" ")[0] == "verbo":
                for ind in range(1,4):
                    try:
                        tmpos = self.legendaPos[self.w.corpus.item(row-ind,self.corpuscols['pos']).text()][0]
                    except:
                        tmpos = ""
                    if "ausiliare" in tmpos and "v+part+pass" in thistext:
                        thistext2 = thistext2 + "/" + self.w.corpus.item(row-ind,morfcol).text()
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
                tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                if len(tbitem)>0:
                    tbrow = tbitem[0].row()
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
        ipunct = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "punteggiatura - .?!", "altro"]
        Repetdialog = ripetizioni.Form(self)
        Repetdialog.loadipos(ipunct)
        Repetdialog.loadallpos(self.legendaPos)
        self.enumeratecolumns(Repetdialog.w.colonna)
        Repetdialog.w.colonna.setCurrentIndex(self.corpuscols['Orig'])
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
            TBdialog = tableeditor.Form(self)
            TBdialog.sessionDir = self.sessionDir
            TBdialog.addcolumn("nGram", 0)
            TBdialog.addcolumn("Occorrenze", 1)
            TBdialog.addcolumn("Parole piene", 2)
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            for tokens in range(tokenda, tokena+1):
                self.findngrams(tokens, minoccur, TBdialog, self.Progrdialog, ignorecase, remspaces, ipunct, col, vuoteI, vuoteF)
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
                        crpitems = self.w.corpus.findItems(tmpword,Qt.MatchFixedString)
                        Fw = len(crpitems)*1.0
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
                    punt = "( ["+re.escape(".,;!?")+ "])"
                    tmpstring = re.sub(punt, "\1", tmpstring, flags=re.IGNORECASE|re.DOTALL)
                    punt = "(["+re.escape("'’")+ "]) "
                    tmpstring = re.sub(punt, "\1", tmpstring, flags=re.IGNORECASE|re.DOTALL)
                    TBdialog.setcelltotable(tmpstring, row, 0)
            self.Progrdialog.accept()
            TBdialog.exec()

    def findngrams(self, tokens, minoccur, TBdialog, Progrdialog, ignorecase, remspaces, ipunct, col, vuoteI, vuoteF):
        mycorpus = ""
        if col == "":
            col = self.corpuscols['Orig']
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if Progrdialog.w.annulla.isChecked():
                return
            thispos = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][0]
            if not thispos in ipunct:
                mycorpus = mycorpus + self.w.corpus.item(row,col).text() + " "
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
            parolai = re.sub(" .*", "", tmpstring, flags=re.IGNORECASE|re.DOTALL)
            parolaf = re.sub(".* ", "", tmpstring, flags=re.IGNORECASE|re.DOTALL)
            #look for all occurrences of this phrase
            if tmpstring != "" and tmpstring.count(searchthis)==tokens-1 and bool(not parolai in vuoteI) and bool(not parolaf in vuoteF):
                tcount = mycorpus.count(tmpstring)
                if tcount >= minoccur:
                    #if remspaces:
                    #    punt = "( ["+re.escape(".,;!?")+ "])"
                    #    tmpstring = re.sub(punt, "\1", tmpstring, flags=re.IGNORECASE|re.DOTALL)
                    #    punt = "(["+re.escape("'’")+ "]) "
                    #    tmpstring = re.sub(punt, "\1", tmpstring, flags=re.IGNORECASE|re.DOTALL)
                    tbitem = TBdialog.w.tableWidget.findItems(tmpstring,Qt.MatchExactly)
                    if len(tbitem)<=0:
                        TBdialog.addlinetotable(tmpstring, 0)
                        tbrow = TBdialog.w.tableWidget.rowCount()-1
                        TBdialog.setcelltotable(str(tcount), tbrow, 1)
                        ppcount = 0
                        tmplist = tmpstring.split(" ")
                        for tmpword in tmplist:
                            if ignorecase:
                                crpitem = self.w.corpus.findItems(tmpword,Qt.MatchFixedString)
                            else:
                                crpitem = self.w.corpus.findItems(tmpword,Qt.MatchExactly)
                            if len(crpitem)<=0:
                                print("Parola non riconosciuta: "+tmpword)
                                ppcount = ppcount + 1
                            else:
                                tmprow = crpitem[0].row()
                                posword = self.w.corpus.item(tmprow,self.corpuscols['pos']).text()
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
            pos = mycorpus.find(searchthis, pos+1)+1 #continue from next word
            if pos <= 0:
                pos = len(mycorpus)


    def translatePos(self):
        col = self.corpuscols['pos']
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto lavorando sulla riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
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
        self.Progrdialog.accept()

    def densitalessico(self):
        col = self.corpuscols['pos']
        TBdialog = tableeditor.Form(self)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.addcolumn("Part of Speech", 0)
        TBdialog.addcolumn("Macrocategoria", 1)
        TBdialog.addcolumn("Occorrenze", 2)
        TBdialog.addcolumn("Percentuale", 3)
        #calcolo le occorrenze del pos
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        mytypes = {}
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            try:
                thistextO = self.w.corpus.item(row,col).text()
                thistext = self.legendaPos[thistextO][0]
                thisposc = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][1]
                try:
                    mytypes[thisposc] = mytypes[thisposc] +1
                except:
                    mytypes[thisposc] = 1
            except:
                thistext = ""
                thistextO = ""
            if thistext != "":
                tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                if len(tbitem)>0:
                    tbrow = tbitem[0].row()
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

    def salvaProgetto(self):
        if self.sessionFile == "":
            fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
            if fileName != "":
                self.sessionFile = fileName
        if self.sessionFile != "":
            self.Progrdialog = progress.Form()
            self.Progrdialog.show()
            self.CSVsaver(self.sessionFile, self.Progrdialog, False)

    def salvaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.CSVsaver(fileName, self.Progrdialog, True)

    def CSVsaver(self, fileName, Progrdialog, addheader = False, onlyrows = []):
        if fileName != "":
            if fileName[-4:] != ".csv":
                fileName = fileName + ".csv"
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
            if len(onlyrows)==0:
                onlyrows = range(self.w.corpus.rowCount())
            for row in onlyrows:
                #csv = csv + "\n"
                csv = ""
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

    def esportavistaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        toselect = []
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.w.corpus.isRowHidden(row):
                toselect.append(row)
        self.CSVsaver(fileName, self.Progrdialog, True, toselect)

    def esportaCSVperID(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.csv *.txt)")[0]
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        IDs = []
        col = self.corpuscols['IDcorpus']
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.w.corpus.item(row,col).text() in IDs:
                IDs.append(self.w.corpus.item(row,col).text())
        for i in range(len(IDs)):
            toselect = []
            for row in range(self.w.corpus.rowCount()):
                self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                if self.Progrdialog.w.annulla.isChecked():
                    return
                if IDs[i] == self.w.corpus.item(row,col).text():
                    toselect.append(row)
                    QApplication.processEvents()
            fileNameT = fileName + str(i).zfill(6) + ".csv"
            self.CSVsaver(fileNameT, self.Progrdialog, True, toselect)

    def web2corpus(self):
        w2Cdialog = url2corpus.Form(self)
        w2Cdialog.setmycfgfile(self.mycfgfile)
        w2Cdialog.exec()

    def delselected(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = len(self.w.corpus.selectedItems())
        toselect = []
        for i in range(len(self.w.corpus.selectedItems())):
            row = self.w.corpus.selectedItems()[i].row()
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(i))
            self.Progrdialog.w.progressBar.setValue(int((i/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            toselect.append(row)
        totallines = len(toselect)
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.w.corpus.removeRow(toselect[row-1])
        self.Progrdialog.accept()

    def enumeratecolumns(self, combo):
        for col in range(self.w.corpus.columnCount()):
            thisname = self.w.corpus.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def dofiltra(self):
        tcount = 0
        for row in range(self.w.corpus.rowCount()):
            col = self.w.ccolumn.currentIndex()
            ctext = self.w.corpus.item(row,col).text()
            ftext = self.w.cfilter.text()
            if bool(re.match(ftext, ctext)):
                self.w.corpus.setRowHidden(row, False)
                tcount = tcount +1
            else:
                self.w.corpus.setRowHidden(row, True)
        self.w.statusbar.showMessage("Risultati totali: " +str(tcount))

    def dofiltra2(self):
        tcount = 0
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto filtrando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            if row<100 or row%100==0:
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            col = self.w.ccolumn.currentIndex()
            ctext = self.w.corpus.item(row,col).text()
            ftext = self.w.cfilter.text()
            if bool(re.match(ftext, ctext)):
                self.w.corpus.setRowHidden(row, False)
                tcount = tcount +1
            else:
                self.w.corpus.setRowHidden(row, True)
        self.w.statusbar.showMessage("Risultati totali: " +str(tcount))
        self.Progrdialog.accept()

    def removevisiblerows(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        toselect = []
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            if not self.w.corpus.isRowHidden(row):
                toselect.append(row)
        totallines = len(toselect)
        for row in range(len(toselect),0,-1):
            self.Progrdialog.w.testo.setText("Sto eliminando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int(((len(toselect)-row)/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            self.w.corpus.removeRow(toselect[row-1])
        self.Progrdialog.accept()

    def cancelfiltro(self):
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.setRowHidden(row, False)

    def loadtxt(self):
        fileNames = QFileDialog.getOpenFileNames(self, "Apri file TXT", self.sessionDir, "Text files (*.txt *.md)")[0]
        if len(fileNames)<1:
            return
        #self.w.statusbar.showMessage("ATTENDI: Sto importando i file txt nel corpus...")
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
            self.Progrdialog = progress.Form() #self.Progrdialog = progress.Form()
            self.Progrdialog.show() #self.Progrdialog.show()
            self.ImportingFile = True
            self.CSVloader(fileNames, self.Progrdialog) #self.CSVloader(fileNames, self.Progrdialog)

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
                        if rowN<100 or rowN%100==0:
                            QApplication.processEvents()
                        colN = 0
                        for col in line.split(self.separator):
                            if Progrdialog.w.annulla.isChecked():
                                rowN = 0
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
                self.Progrdialog = progress.Form()
                self.Progrdialog.show()
                self.ImportingFile = True
                fileNames = ['']
                fileNames[0] = self.sessionFile
                self.CSVloader(fileNames, self.Progrdialog)
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
        te.exec()

    def confronto(self):
        cf = confronto.Confronto(self.sessionDir)
        cf.exec()

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
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        totaltypes = 0
        mytypes = {}
        for row in range(self.w.corpus.rowCount()):
            self.Progrdialog.w.testo.setText("Sto conteggiando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisposc = "False"
            myignore = []
            try:
                thistext = self.w.corpus.item(row,col).text()
                thisposc = self.legendaPos[self.w.corpus.item(row,self.corpuscols['pos']).text()][1]
                if ret == QMessageBox.Yes:
                    myignore = ["punteggiatura"]
                try:
                    mytypes[thisposc] = mytypes[thisposc] +1
                except:
                    mytypes[thisposc] = 1
            except:
                thistext = ""
            if not thisposc in myignore and thistext != "":
                tbitem = TBdialog.w.tableWidget.findItems(thistext,Qt.MatchExactly)
                if len(tbitem)>0:
                    tbrow = tbitem[0].row()
                    tbval = int(TBdialog.w.tableWidget.item(tbrow,1).text())+1
                    TBdialog.setcelltotable(str(tbval), tbrow, 1)
                else:
                    TBdialog.addlinetotable(thistext, 0)
                    tbrow = TBdialog.w.tableWidget.rowCount()-1
                    TBdialog.setcelltotable("1", tbrow, 1)
                    totaltypes = totaltypes + 1
        hapax = 0
        for row in range(TBdialog.w.tableWidget.rowCount()):
            self.Progrdialog.w.testo.setText("Sto cercando gli hapax su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
            QApplication.processEvents()
            if int(TBdialog.w.tableWidget.item(row,1).text()) == 1:
                hapax = hapax + 1
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
            self.Progrdialog.w.testo.setText("Sto controllando la riga numero "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
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
            self.Progrdialog.w.testo.setText("Sto calcolando le somme su "+str(row))
            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
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
        #presento le macrocategorie
        #for key in mytypes:
        #    if not key in myignore:
        #        TBdialog.addlinetotable(key, 0)
        #        tbrow = TBdialog.w.tableWidget.rowCount()-1
        #        TBdialog.setcelltotable(str(mytypes[key]), tbrow, 1)
        TBdialog.addlinetotable("Types", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(totaltypes), tbrow, 1)
        TBdialog.addlinetotable("Types/Tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(totaltypes)/float(paroletotali))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        TBdialog.addlinetotable("Hapax", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        TBdialog.setcelltotable(str(hapax), tbrow, 1)
        TBdialog.addlinetotable("Hapax/Tokens", 0)
        tbrow = TBdialog.w.tableWidget.rowCount()-1
        ratio = (float(hapax)/float(paroletotali))
        ratios = f'{ratio:.3f}'
        TBdialog.setcelltotable(str(ratios), tbrow, 1)
        #mostro i risultati
        self.Progrdialog.accept()
        TBdialog.exec()

def findintable(table, stringa, col=0):
    resrow = -1
    for row in range(len(table)):
        if table[row][col] == stringa:
            resrow = row
            break
    return resrow

def linescount(filename):
    f = open(filename, "r+", encoding='utf-8')
    buf = mmap.mmap(f.fileno(), 0)
    lines = 0
    readline = buf.readline
    while readline():
        lines += 1
    return lines

def savetable(table, output):
    tabletext = ""
    for row in table:
        coln = 0
        for col in row:
            if coln > 0:
                tabletext = tabletext + '\t'
            tabletext = tabletext + str(col)
            coln = coln + 1
        tabletext = tabletext + "\n"
    file = open(output,"w", encoding='utf-8')
    file.write(tabletext)
    file.close()

def calcola_occorrenze():
    separator = '\t'
    fileNames = []
    if os.path.isfile(sys.argv[2]):
        fileNames = [sys.argv[2]]
    if os.path.isdir(sys.argv[2]):
        for tfile in os.listdir(sys.argv[2]):
            fileNames.append(os.path.join(sys.argv[2],tfile))
    try:
        col = int(sys.argv[3])
    except:
        col = 0
    for fileName in fileNames:
        table = []
        table.append([os.path.basename(fileName)+"-"+str(col),"Occorrenze"])
        row = 0
        output = fileName + "-occorrenze-" + str(col) + ".csv"
        recovery = output + ".tmp"
        startatrow = -1
        try:
            if os.path.isfile(recovery):
                ch = "Y"
                print("Ho trovato un file di ripristino, lo devo usare? [Y/N]")
                ch = input()
                if ch == "Y" or ch == "y":
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
                        thistext = line.split(separator)[col]
                    except:
                        thistext = ""
                    tbrow = findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                    savetable(table, output)
                    with open(recovery, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
                row = row + 1


def estrai_colonna():
    separator = '\t'
    fileNames = []
    if os.path.isfile(sys.argv[2]):
        fileNames = [sys.argv[2]]
    if os.path.isdir(sys.argv[2]):
        for tfile in os.listdir(sys.argv[2]):
            fileNames.append(os.path.join(sys.argv[2],tfile))
    try:
        col = int(sys.argv[3])
    except:
        col = 0
    for fileName in fileNames:
        row = 0
        output = fileName + "-colonna-" + str(col) + ".csv"
        recovery = output + ".tmp"
        startatrow = -1
        try:
            if os.path.isfile(recovery):
                ch = "Y"
                print("Ho trovato un file di ripristino, lo devo usare? [Y/N]")
                ch = input()
                if ch == "Y" or ch == "y":
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
                        thistext = line.split(separator)[col]
                    except:
                        thistext = ""
                    with open(output, "a", encoding='utf-8') as outfile:
                        outfile.write(thistext+"\n")
                    with open(recovery, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
                row = row + 1

def splitbigfile():
    separator = '\t'
    if os.path.isfile(sys.argv[2]):
        fileName = sys.argv[2]
        ext = fileName[-3:]
    try:
        maxrow = int(sys.argv[3])
    except:
        maxrow = 20000
        if ext == "csv":
            maxrow = 500000
    splitdot = False
    try:
        if sys.argv[3] == "." and ext == "txt":
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
        if os.path.isfile(recovery):
            ch = "Y"
            print("Ho trovato un file di ripristino, lo devo usare? [Y/N]")
            ch = input()
            if ch == "Y" or ch == "y":
                with open(recovery, "r", encoding='utf-8') as tempfile:
                   lastline = (list(tempfile)[-1].split(",")[0])
                startatrow = int(lastline)
                part = int(list(tempfile)[-1].split(",")[1])
                partrow = int(list(tempfile)[-1].split(",")[2])
                print("Comincio dalla riga " + str(startatrow))
    except:
        startatrow = -1
        part = 0
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
                with open(output, "a", encoding='utf-8') as outfile:
                    outfile.write(thistext)
                with open(recovery, "a", encoding='utf-8') as rowfile:
                    rowfile.write(str(row)+","+str(part)+","+str(partrow)+"\n")
                partrow = partrow + 1
            row = row + 1

def samplebigfile():
    separator = '\t'
    if os.path.isfile(sys.argv[2]):
        fileName = sys.argv[2]
        ext = fileName[-3:]
    try:
        maxrow = int(sys.argv[3])
    except:
        maxrow = 20000
        if ext == "csv":
            maxrow = 500000
    splitdot = False
    try:
        if sys.argv[3] == "." and ext == "txt":
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
    totallines = linescount(fileName)
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
        end = start+chunk
        if end >= totallines:
            end = totallines -1
        trow = random.randint(start, end)
        getrows.append(trow)
    print("Estraggo le righe in un nuovo file")
    with open(fileName, "r", encoding='utf-8') as ins:
        for line in ins:
            if row in getrows:
                try:
                    thistext = line
                except:
                    thistext = ""
                with open(output, "a", encoding='utf-8') as outfile:
                    outfile.write(thistext)
            row = row + 1

if __name__ == "__main__":
    if len(sys.argv)>1:
        corpuscols = {
                    'IDcorpus': 0,
                    'Orig': 1,
                    'Lemma': 2,
                    'pos': 3,
                    'ner': 4,
                    'feat': 5,
                    'IDword': 6
        }
        w = "cli"
        app = QApplication(sys.argv)
        if sys.argv[1] == "help" or sys.argv[1] == "aiuto":
            print("Elenco dei comandi:\n")
            print("python3 main.py tintstart [javapath]\n")
            print("python3 main.py txt2corpus file.txt|cartella [indirizzoServerTint]\n")
            print("python3 main.py splitbigfile file.txt [maxnumberoflines] [.]\n")
            print("* python3 main.py samplebigfile file.txt [maxnumberoflines] [.]\n")
            print("python3 main.py occorrenze file.csv|cartella [colonna]\n")
            print("python3 main.py extractcolumn file.csv|cartella colonna\n")
            print("* python3 main.py mergetables cartella colonnaChiave [sum|mean|diff]\n")
            print("Gli argomenti tra parentesi [] sono facoltativi.")
            print("\nI comandi preceduti da * sono sperimentali o non ancora implementati.")
        if sys.argv[1] == "txt2corpus":
            fileNames = []
            if os.path.isfile(sys.argv[2]):
                fileNames = [sys.argv[2]]
            if os.path.isdir(sys.argv[2]):
                for tfile in os.listdir(sys.argv[2]):
                    fileNames.append(os.path.join(sys.argv[2],tfile))
            try:
                tmpurl = sys.argv[3]
            except:
                tmpurl = "localhost"
            tinturl = "http://" + tmpurl + ":8012/tint"
            TCThread = tint.TintCorpus(w, fileNames, corpuscols, tinturl)
            TCThread.outputcsv = fileNames[0] + ".csv"
            TCThread.finished.connect(sys.exit)
            TCThread.start()
            while True:
                time.sleep(10)
        if sys.argv[1] == "tintstart":
            TintThread = tint.TintRunner(w)
            Java = "/usr/bin/java"
            TintPort = "8012"
            TintDir = os.path.abspath(os.path.dirname(sys.argv[0]))+"/tint/lib"
            TintThread.loadvariables(Java, TintDir, TintPort)
            TintThread.start()
            while True:
                time.sleep(10)
        if sys.argv[1] == "occorrenze":
            calcola_occorrenze()
        if sys.argv[1] == "extractcolumn":
            estrai_colonna()
        if sys.argv[1] == "splitbigfile":
            splitbigfile()
        if sys.argv[1] == "samplebigfile":
            samplebigfile()
    else:
        app = QApplication(sys.argv)
        w = MainWindow()
        w.show()
        sys.exit(app.exec_())



