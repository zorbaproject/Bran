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


from PySide2.QtWidgets import QApplication


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
from PySide2.QtWidgets import QTreeWidget
from PySide2.QtWidgets import QTreeWidgetItem
from PySide2.QtWidgets import QTreeWidgetItemIterator
from PySide2.QtWidgets import QSizePolicy
from PySide2.QtCore import QThread


from forms import BranCorpus
from forms import regex_replace
from forms import url2corpus
from forms import texteditor
from forms import tableeditor
from forms import confronto
from forms import tint
from forms import settings
from forms import progress
from forms import sessione
from forms import ripetizioni
from forms import about
from forms import creafiltro
from forms import alberofrasi



class MainWindow(QMainWindow):

    def __init__(self, corpcol, legPos, ignthis, dimlst, parent=None):
        super(MainWindow, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/branwindow.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader(self)
        self.w = loader.load(file)
        self.setCentralWidget(self.w)
        self.setWindowTitle("Bran")
        self.corpuscols = corpcol
        self.legendaPos = legPos
        self.ignoretext = ignthis
        self.dimList = dimlst
        self.w.replace_in_corpus.clicked.connect(self.replaceCorpus)
        self.w.replace_in_cells.clicked.connect(self.replaceCells)
        self.w.actionSostituisci_nel_corpus_con_RegEx.triggered.connect(self.replaceCorpus)
        self.w.actionSostituisci_solo_nelle_celle_selezionate.triggered.connect(self.replaceCells)
        self.w.actionSeleziona_tutte_le_celle_visibili.triggered.connect(self.selectVisibleCells)
        self.w.actionDeseleziona_tutte_le_celle.triggered.connect(self.deselectAllCells)
        self.w.actionAggiornamenti.triggered.connect(self.aggiornamenti)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.findNext.clicked.connect(self.findNext)
        self.w.filtriMultipli.clicked.connect(self.filtriMultipli)
        self.w.actionFiltri_multipli.triggered.connect(self.filtriMultipli)
        self.w.delselected.clicked.connect(self.delselected)
        self.w.updateCorpus.clicked.connect(self.updateCorpus)
        self.w.updateProject.clicked.connect(self.updateProject)
        self.w.projectfilter.textChanged.connect(self.filterProject)
        self.w.progetto.itemDoubleClicked.connect(self.openprjfile)
        self.w.actionRimuovi_righe_selezionate.triggered.connect(self.delselected)
        self.w.actionScarica_corpus_da_sito_web.triggered.connect(self.web2corpus)
        self.w.actionConverti_vecchio_corpus.triggered.connect(self.convertiDaTint)
        self.w.actionEsporta_corpus_in_un_CSV_per_ogni_ID.triggered.connect(self.esportaCSVperID)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionConta_persone.triggered.connect(self.contapersone)
        self.w.actionConta_occorrenze_normalizzate.triggered.connect(self.occorrenzenormalizzate)
        self.w.actionConta_occorrenze_filtrate.triggered.connect(self.contaoccorrenzefiltrate)
        self.w.actionEsporta_corpus_in_CSV_unico.triggered.connect(self.salvaCSV)
        self.w.actionEsporta_vista_attuale_in_CSV.triggered.connect(self.esportavistaCSV)
        self.w.actionEsporta_subcorpus_in_base_a_filtro.triggered.connect(self.esportafiltroCSV)
        self.w.actionEsporta_in_formato_CoNNL_U.triggered.connect(self.connluexport)
        self.w.actionAggiungi_tag_in_corpus_in_base_a_RegEx.triggered.connect(self.addTagFromFilter)
        self.w.actionRimuovi_vista_attuale_dal_corpus.triggered.connect(self.removevisiblerows)
        self.w.actionCalcola_densit_lessicale.triggered.connect(self.densitalessico)
        self.w.actionNumero_dipendenze_per_frase.triggered.connect(self.actionNumero_dipendenze_per_frase)
        self.w.actionFile_del_progetto.triggered.connect(self.showProjectFiles)
        self.w.actionVisualizza_frasi.triggered.connect(self.visualizzafrasi)
        self.w.actionRicostruisci_testo.triggered.connect(self.ricostruisciTesto)
        self.w.actionConcordanze.triggered.connect(self.concordanze)
        self.w.actionCo_occorrenze.triggered.connect(self.coOccorrenze)
        self.w.actionDa_file_di_testo_con_Tint.triggered.connect(self.loadFromTint)
        self.w.actionDa_file_di_testo_con_UDpipe.triggered.connect(self.loadFromUDpipe)
        #self.w.actionTraduci_i_tag_PoS_in_forma_leggibile.triggered.connect(self.translatePos)
        #self.w.actionDa_file_JSON.triggered.connect(self.loadjson)
        self.w.actionEstrai_testo_da_CSV.triggered.connect(self.loadTextFromCSV)
        self.w.actionDa_file_CSV.triggered.connect(self.loadCSV)
        self.w.actionDa_file_di_TreeTagger.triggered.connect(self.importfromTreeTagger)
        self.w.actionConfigurazione_Tint.triggered.connect(self.loadTintConfig)
        self.w.actionSalva.triggered.connect(self.salvaProgetto)
        self.w.actionApri.triggered.connect(self.apriProgetto)
        self.w.actionChiudi.triggered.connect(self.chiudiProgetto)
        self.w.actionEditor_di_testo.triggered.connect(self.texteditor)
        self.w.actionEditor_tabelle.triggered.connect(self.tableeditor)
        self.w.actionConfigurazione_di_Bran.triggered.connect(self.showbranconfig)
        self.w.actionConfronta_corpora.triggered.connect(self.confronto)
        self.w.actionAbout_Bran.triggered.connect(self.aboutbran)
        self.w.actionEstrai_dizionario.triggered.connect(self.misure_lessicometriche)
        self.w.actionGulpEASE.triggered.connect(self.gulpease)
        self.w.actionTrova_ripetizioni.triggered.connect(self.trovaripetizioni)
        self.w.actionConta_verbi.triggered.connect(self.contaverbi)
        self.w.actionTutti_i_token.triggered.connect(self.menualltoken)
        self.w.actionItaliano.triggered.connect(lambda: self.changeLang("it-IT"))
        self.ignorepos = ["punteggiatura - \"\" () «» - - ", "punteggiatura - : ;", "punteggiatura - ,", "altro"] # "punteggiatura - .?!"
        self.separator = "\t"
        self.language = "it-IT"
        self.Corpus = BranCorpus.BranCorpus(self.corpuscols, self.legendaPos, self.ignoretext, self.dimList, tablewidget=self.w.corpus)
        self.Corpus.sizeChanged.connect(self.corpusSizeChanged)
        self.w.allToken.toggled.connect(self.setalltokens)
        self.w.actionEsegui_calcoli_solo_su_righe_visibili.toggled.connect(lambda: self.Corpus.setOnlyVisible(self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked()))
        self.w.cfilter.textChanged.connect(lambda text: self.Corpus.setFilter(text))
        self.w.daToken.valueChanged.connect(self.Corpus.setStart)
        self.w.aToken.valueChanged.connect(self.Corpus.setEnd)
        self.enumeratecolumns(self.w.ccolumn)
        self.filtrimultiplienabled = "Filtro multiplo"
        self.w.ccolumn.addItem(self.filtrimultiplienabled)
        QApplication.processEvents()
        self.alreadyChecked = False
        self.ImportingFile = False
        self.Corpus.sessionFile = ""
        self.sessionDir = "."
        #self.w.cfilter.setMaxLength(sys.maxsize-1)
        self.w.cfilter.setMaxLength(2147483647)
        #self.Corpus.mycfgfile = QDir.homePath() + "/.brancfg"
        self.loadSession()
        self.TintAddr = ""
        self.Corpus.txtloadingstopped()
        self.setcss()
        self.showProjectFiles()
        self.w.corpusandproject.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.w.groupBox_progetto.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        self.w.groupBox_filter.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.w.updatetokens_group.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self.w.groupBox_filter.setStyleSheet("QGroupBox{padding-top:1em; margin-top:-1em}")
        self.w.groupBox_progetto.setStyleSheet("QGroupBox{padding-top:1em; margin-top:-1em}")
        self.tableeditor("init")

    def corpusSizeChanged(self, newsize):
        #maximum = len(self.Corpus.corpus)
        d = self.w.daToken.value()
        a = self.w.aToken.value()
        if a == 0 or a < d:
            a = 100
        if a < d:
            d = 0
        self.w.daToken.setMaximum(newsize)
        self.w.aToken.setMaximum(newsize)
        if newsize > d:
            self.w.daToken.setValue(d)
        else:
            self.w.daToken.setValue(newsize)
        if newsize > a:
            self.w.aToken.setValue(a)
        else:
            self.w.aToken.setValue(newsize)

    def changeLang(self, lang):
        self.language = lang
        print("Set language "+self.language)

    def loadTintConfig(self):
        self.TintSetdialog = tint.Form(self, self.Corpus.mycfg)
        self.TintSetdialog.w.start.clicked.connect(self.runServer)
        self.TintSetdialog.w.check.clicked.connect(self.checkServer)
        self.TintSetdialog.exec()
        self.Java = self.TintSetdialog.w.java.text()
        self.TintDir = self.TintSetdialog.w.tintlib.text()
        self.TintPort = self.TintSetdialog.w.port.text()
        self.TintAddr = "http://" + self.TintSetdialog.w.address.text() + ":" +self.TintPort +"/tint"
        #self.Java -classpath $_CLASSPATH eu.fbk.dh.tint.runner.TintServer -p self.TintPort
        if not self.TintSetdialog.notint:
            self.Corpus.mycfg["javapath"] = self.TintSetdialog.w.java.text()
            self.Corpus.mycfg["tintpath"] = self.TintSetdialog.w.tintlib.text()
            self.Corpus.mycfg["tintaddr"] = self.TintSetdialog.w.address.text()
            self.Corpus.mycfg["tintport"] = self.TintSetdialog.w.port.text()
            self.Corpus.savePersonalCFG()

    def loadSession(self):
        seSdialog = sessione.Form(self)
        seSdialog.loadhistory(self.Corpus.mycfg["sessions"])
        seSdialog.baseTempDir = self.Corpus.mycfg["tempDir"]
        seSdialog.exec()
        self.Corpus.sessionFile = seSdialog.filesessione
        self.setWindowTitle("Bran - "+self.Corpus.sessionFile)
        self.sessionDir = os.path.abspath(os.path.dirname(self.Corpus.sessionFile))
        if seSdialog.result():
            if os.path.isfile(self.Corpus.sessionFile):
                tmpsess = [self.Corpus.sessionFile]
                for i in range(len(self.Corpus.mycfg["sessions"])-1,-1,-1):
                    if not self.Corpus.mycfg["sessions"][i] in tmpsess:
                        tmpsess.append(self.Corpus.mycfg["sessions"][i])
                    if i > 10:
                        break
                self.Corpus.mycfg["sessions"] = tmpsess
                #print(tmpsess)
                self.Corpus.savePersonalCFG()
        else:
            print("Temporary folder")
        if self.Corpus.sessionFile == "":
            print("Session file does not exist")
            sys.exit(0)

    def filterProject(self):
        myfilter = ".*"+self.w.projectfilter.text()+".*"
        for it in QTreeWidgetItemIterator(self.w.progetto):
            it.value().setHidden(False)
        for it in QTreeWidgetItemIterator(self.w.progetto):
            filetitle = it.value().text(0)
            filename = os.path.basename(it.value().text(1))
            if it.value().childCount() >0:
                continue
            if bool(re.match(myfilter, filetitle, flags=re.IGNORECASE|re.DOTALL)) or bool(re.match(myfilter, filename, flags=re.IGNORECASE|re.DOTALL)):
            #if myfilter.lower() in filetitle.lower() or myfilter.lower() in filename.lower():
                it.value().setHidden(False)
            else:
                it.value().setHidden(True)

    def openprjfile(self, myitem, col):
        filepath = myitem.text(1)
        if filepath[-4:]==".tsv" or filepath[-4:]==".csv":
            self.Corpus.showResults(filepath, True)
        else:
            te = texteditor.TextEditor(self.Corpus.corpuswidget, self.Corpus.mycfg)
            te.aprilista([filepath])
            te.show()

    def updateProject(self):
        self.w.progetto.clear()
        if self.Corpus.sessionFile == "" or self.sessionDir == ".":
            return
        origitem = QTreeWidgetItem(self.w.progetto)
        origitem.setText(0,"Corpus")
        resitem = QTreeWidgetItem(self.w.progetto)
        resitem.setText(0,"Risultati di Bran")
        otheritem = QTreeWidgetItem(self.w.progetto)
        otheritem.setText(0,"Altri file")
        fileNames = []
        sessionname = os.path.basename(self.Corpus.sessionFile)
        if os.path.isdir(self.sessionDir):
            for tfile in os.listdir(self.sessionDir):
                fileNames.append(os.path.join(self.sessionDir,tfile))
        for fileName in fileNames:
            fileTitle = os.path.basename(fileName)
            rootelem = otheritem
            if fileName[-4:] == ".tmp":
                continue
            if fileTitle.startswith(sessionname):
                if fileTitle == sessionname:
                    rootelem = origitem
                    fileTitle = "Progetto di Bran"
                #Prevediamo la possibilità di avere più versioni del corpus
                fingerprint = sessionname+"-ricostruito-"
                if fileTitle.startswith(fingerprint):
                    rootelem = origitem
                    myregex = re.escape(fingerprint) + "(.*?)\-" + "(.*?)" + re.escape(".txt")
                    fileTitle = "Testo ricostruito "+ re.sub(myregex, "\g<1> filtro \g<2>", fileTitle)
                fingerprint = sessionname+"-orig-"
                if fileTitle.startswith(fingerprint):
                    rootelem = origitem
                    myregex = re.escape(fingerprint) + "(.*?)\-(.*?)" + re.escape(".txt")
                    fileTitle = "Corpus originale " + re.sub(myregex, "\g<1> sorgente \g<2>", fileTitle)
                fingerprint = sessionname+"-colonna-"
                if fileTitle.startswith(fingerprint):
                    rootelem = origitem
                    myregex = re.escape(fingerprint) + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Colonna " + re.sub(myregex, "\g<1>", fileTitle)
                fingerprint = sessionname+"-occorrenze-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Occorrenze "+ re.sub(myregex, "\g<1>", fileTitle)
                fingerprint = sessionname+"-occorrenze_filtrate-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)\-" + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Occorrenze "+ re.sub(myregex, "\g<1> filtro \g<2>", fileTitle)
                fingerprint = sessionname+"-coOccorrenze-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)\-" + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Co occorrenze "+ re.sub(myregex, "\g<1> filtro \g<2>", fileTitle)
                fingerprint = sessionname+"-concordanze-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)\-" + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Concordanze "+ re.sub(myregex, "\g<1> filtro \g<2>", fileTitle)
                fingerprint = sessionname+"-contaverbi.tsv"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    fileTitle = "Contaverbi"
                fingerprint = sessionname+"-contapersone-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)\-" + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Contapersone "+ re.sub(myregex, "\g<2> filtro \g<1>", fileTitle)
                fingerprint = sessionname+"-occorrenze_normalizzate-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Occorrenze normalizzate "+ re.sub(myregex, "\g<1>", fileTitle)
                fingerprint = sessionname+"-misure_lessicometriche-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Misure lessicometriche "+ re.sub(myregex, "\g<1>", fileTitle)
                fingerprint = sessionname+"-densitalessicale-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Densità lessicale "+ re.sub(myregex, "\g<1>", fileTitle)
                fingerprint = sessionname+"-gulpease-"
                if fileTitle.startswith(fingerprint):
                    rootelem = resitem
                    myregex = re.escape(fingerprint) + "(.*?)" + re.escape(".tsv")
                    fileTitle = "Gulpease "+ re.sub(myregex, "\g<1>", fileTitle)
                #
            tritem = QTreeWidgetItem(rootelem)
            tritem.setText(0,fileTitle)
            tritem.setText(1,fileName)
            tritem.setExpanded(True)
        resitem.setExpanded(True)
        origitem.setExpanded(True)
        otheritem.setExpanded(True)
        for i in range(self.w.progetto.columnCount()):
            self.w.progetto.resizeColumnToContents(i)

    def showProjectFiles(self):
        if self.w.actionFile_del_progetto.isChecked():
            totSw = self.w.splitter.width()
            self.w.splitter.setSizes([totSw*0.7, totSw*0.3])
            self.w.groupBox_progetto.setVisible(True)
            self.updateProject()
        else:
            self.w.groupBox_progetto.setVisible(False)

    def setcss(self):
        css = ""
        css = css + "QTreeView::branch:has-siblings:!adjoins-item {\n"
        css = css + "border-image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-vline.png) 0;\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:has-siblings:adjoins-item {\n"
        css = css + "border-image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-more.png) 0;\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:!has-children:!has-siblings:adjoins-item {\n"
        css = css + "border-image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-end.png) 0;\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:has-children:!has-siblings:closed,\n"
        css = css + "QTreeView::branch:closed:has-children:has-siblings {\n"
        css = css + "border-image: none;\n"
        css = css + "image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-closed.png);\n"
        css = css + "}\n"
        css = css + "QTreeView::branch:open:has-children:!has-siblings,\n"
        css = css + "QTreeView::branch:open:has-children:has-siblings  {\n"
        css = css + "border-image: none;\n"
        css = css + "image: url("+os.path.abspath(os.path.dirname(sys.argv[0]))+"/icons/stylesheet-branch-open.png);\n"
        css = css + "}"
        self.w.progetto.setStyleSheet(css)

    def apriProgetto(self):
        self.loadSession()
        self.Corpus.txtloadingstopped()

    def chiudiProgetto(self):
        self.Corpus.sessionFile = ""
        self.sessionDir = "."
        self.corpus = []
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.removeRow(0)
            if row<100 or row%100==0:
                QApplication.processEvents()
        self.setWindowTitle("Bran")

    def replaceCorpus(self):
        self.Corpus.replaceCorpus()

    def replaceCells(self):
        self.Corpus.replaceCells()

    def selectVisibleCells(self):
        self.deselectAllCells()
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        totallines = self.w.corpus.rowCount()
        for row in range(self.w.corpus.rowCount()):
            if self.w.actionEsegui_calcoli_solo_su_righe_visibili.isChecked() and self.w.corpus.isRowHidden(row):
                continue
            if row<100 or row%100==0:
                self.Progrdialog.w.testo.setText("Sto selezionando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            thisrow = QTableWidgetSelectionRange(row,0,row,self.w.corpus.columnCount()-1)
            self.w.corpus.setRangeSelected(thisrow, True)
        self.Progrdialog.accept()

    def deselectAllCells(self):
        self.w.corpus.clearSelection()

    def selectFromProjectFiles(self, output = ""):
        self.w.actionFile_del_progetto.setChecked(True)
        self.showProjectFiles()
        self.updateProject()
        return
        #Windows si bloca se provo a selezionare l'elemento
        root = self.w.progetto.invisibleRootItem()
        cCount = root.childCount()
        for i in range(cCount):
            if root.child(i).text(0) == "Risultati di Bran":
                ccCount = root.child(i).childCount()
                for c in range(ccCount):
                    try:
                        item = root.child(i).child(c)
                        if output == item.text(1):
                            print(item.text(1))
                            self.w.progetto.setCurrentItem(root.child(i).child(c))
                    except:
                        pass

    def contaoccorrenze(self):
        self.tableeditor("init")
        #QMessageBox.information(self.w, "Avviso", "Su Windows devi prima di tutto cliccare su Visualizza/File del progetto e provare a aprire una tabella, poi puoi caricare i file con i risultati.")
        output = self.Corpus.contaoccorrenze()
        if self.Corpus.stupidwindows:
            self.selectFromProjectFiles(output)

    def contapersone(self):
        self.tableeditor("init")
        self.Corpus.contapersone()

    def occorrenzenormalizzate(self):
        self.tableeditor("init")
        self.Corpus.occorrenzenormalizzate()

    def contaoccorrenzefiltrate(self):
        self.tableeditor("init")
        self.Corpus.contaoccorrenzefiltrate()

    def contaverbi(self):
        self.tableeditor("init")
        self.Corpus.contaverbi()

    def trovaripetizioni(self):
        self.tableeditor("init")
        self.Corpus.trovaripetizioni()

    def ricostruisciTesto(self):
        self.Corpus.ricostruisciTesto()

    def remUselessSpaces(self, tempstring):
        punt = " (["+re.escape(".,;!?)")+ "])"
        tmpstring = re.sub(punt, "\g<1>", tempstring, flags=re.IGNORECASE)
        punt = "(["+re.escape("'’(")+ "]) "
        tmpstring = re.sub(punt, "\g<1>", tmpstring, flags=re.IGNORECASE|re.DOTALL)
        return tmpstring

    def translatePos(self):
        self.Corpus.translatePos()

    def densitalessico(self):
        self.tableeditor("init")
        self.Corpus.densitalessico()

    def aggiornamenti(self):
        try:
            import dulwich.porcelain as git
        except:
            try:
                from tkinter import messagebox
                thispkg = "la liberia dulwich per Git"
                messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
                pip.main(["install", "dulwich", "--global-option=--pure"])
                import dulwich.porcelain as git
            except:
                try:
                    from pip._internal import main as pipmain
                    from tkinter import messagebox
                    pipmain(["install", "dulwich", "--global-option=--pure"])
                    import dulwich.porcelain as git
                except:
                    return
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        self.Progrdialog.w.testo.setText("Sto cercando gli aggiornamenti")
        self.Progrdialog.w.progressBar.setValue(int((0.1)*100))
        QApplication.processEvents()
        time.sleep(1)
        brandir = os.path.abspath(os.path.dirname(sys.argv[0]))
        gstatus = git.status(repo=brandir, ignored=False)
        print(gstatus)
        doupdate = False
        if len(getattr(gstatus, "unstaged")) >0 or int(len(getattr(gstatus, "staged")["add"])+len(getattr(gstatus, "staged")["delete"])+len(getattr(gstatus, "staged")["modify"]))>0:
            ret = QMessageBox.question(self,'Domanda', "Sembra che tu abbia modificato alcuni file del codice sorgente di Bran, se procedi con l'aggiornamento le tue modifiche verranno perse. Vuoi continuare?", QMessageBox.Yes | QMessageBox.No)
            if ret == QMessageBox.Yes:
                doupdate = True
        else:
            QMessageBox.information(self, "Aggiornamento", "Sto per procedere con l'aggiornamento, potrebbe essere necessario qualche minuto. Per favore, attendi il completamento.")
            doupdate = True
        if doupdate:
            print("Su Windows, se si presenta un errore relativo ai file di lock è necessario instalalre GitBash e dare il comando 'git gc', per attivare il Garbage Collector e ripulire il repository.")
            #https://stackoverflow.com/questions/28720151/git-gc-aggressive-vs-git-repack
            #git.repack(brandir)
            git.pull(brandir, "https://github.com/zorbaproject/Bran.git")
            self.Progrdialog.w.testo.setText("Aggiornamento completo")
            self.Progrdialog.w.progressBar.setValue(int((1)*100))
            QApplication.processEvents()
            #time.sleep(1)
            QMessageBox.information(self, "Aggiornamento", "Aggiornamento completato, adesso è necessario chiudere Bran e avviarlo di nuovo per utilizzare la nuova versione.")
        self.Progrdialog.accept()

    def salvaProgetto(self):
        self.Corpus.salvaProgetto()

    def salvaCSV(self):
        self.Corpus.salvaCSV()

    def connluexport(self):
        self.Corpus.connluexport()

    def esportavistaCSV(self):
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
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
        self.Corpus.CSVsaver(fileName, self.Progrdialog, True, toselect)

    def esportafiltroCSV(self):
        self.Corpus.esportafiltroCSV()

    def esportaCSVperID(self):
        self.Corpus.esportaCSVperID()

    def web2corpus(self):
        w2Cdialog = url2corpus.Form(self)
        w2Cdialog.setmycfgfile(self.Corpus.mycfgfile)
        w2Cdialog.exec()

    def visualizzafrasi(self):
        self.Corpus.visualizzafrasi()
        #alberofrasidialog = alberofrasi.Form(self, self)
        #alberofrasidialog.exec()

    def delselected(self):
        self.Corpus.delselected()

    def enumeratecolumns(self, combo):
        for col in range(self.w.corpus.columnCount()):
            thisname = self.w.corpus.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

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
        totallines = self.Corpus.aToken
        startline = self.Corpus.daToken
        if (totallines-startline) != self.w.corpus.rowCount():
            self.updateCorpus()
        for row in range(startline, totallines):
            fcol = self.w.ccolumn.currentIndex()
            #ctext = self.w.corpus.item(row,col).text()
            ftext = self.w.cfilter.text()
            if self.Corpus.applicaFiltro(row, fcol, ftext): #if bool(re.match(ftext, ctext)):
                self.w.corpus.setRowHidden(row-startline, False)
                tcount = tcount +1
            else:
                self.w.corpus.setRowHidden(row-startline, True)
        self.w.statusbar.showMessage("Risultati totali: " +str(tcount))
        #self.Progrdialog.accept()

    def dofiltra2(self):
        self.Progrdialog = progress.Form()
        self.Progrdialog.show()
        tcount = 0
        totallines = self.w.aToken.value()
        startline = self.w.daToken.value()
        for row in range(startline, totallines):
            if row<100 or row%200==0:
                self.Progrdialog.w.testo.setText("Sto filtrando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            col = self.w.ccolumn.currentIndex()
            #ctext = self.w.corpus.item(row,col).text()
            ftext = self.w.cfilter.text()
            if self.Corpus.applicaFiltro(row, fcol, ftext): #if bool(re.match(ftext, ctext)):
                self.w.corpus.setRowHidden(row-startline, False)
                tcount = tcount +1
            else:
                self.w.corpus.setRowHidden(row-startline, True)
        self.w.statusbar.showMessage("Risultati totali: " +str(tcount))
        self.Progrdialog.accept()

    def findNext(self):
        totallines = self.w.aToken.value()
        startline = self.w.daToken.value()
        irow = 0
        if len(self.w.corpus.selectedItems())>0:
            irow = self.w.corpus.selectedItems()[len(self.w.corpus.selectedItems())-1].row()+1
        if irow < self.w.corpus.rowCount():
            col = self.w.ccolumn.currentIndex()
            for row in range(irow, self.w.corpus.rowCount()):
                if self.w.corpus.isRowHidden(row):
                    continue
                ftext = self.w.cfilter.text()
                if self.Corpus.applicaFiltro(row+startline, col, ftext):
                    self.w.corpus.setCurrentCell(row,0)
                    break

    def filtriMultipli(self):
        self.Corpus.filtriMultipli()
        self.w.ccolumn.setCurrentText(self.filtrimultiplienabled)
        self.w.cfilter.setText(self.Corpus.filter)

    def actionNumero_dipendenze_per_frase(self):
        self.Corpus.actionNumero_dipendenze_per_frase()

    def addTagFromFilter(self):
        self.Corpus.addTagFromFilter()

    def concordanze(self):
        self.Corpus.concordanze()

    def coOccorrenze(self):
        self.Corpus.coOccorrenze()

    def removevisiblerows(self):
        self.Corpus.removevisiblerows()

    def cancelfiltro(self):
        for row in range(self.w.corpus.rowCount()):
            self.w.corpus.setRowHidden(row, False)

    def loadFromTint(self):
        if self.TintAddr=="":
            self.loadTintConfig()
        self.Corpus.loadFromTint(self.TintAddr)

    def loadFromUDpipe(self):
        try:
            if self.Corpus.mycfg["udpipe"] == "":
                self.showbranconfig()
        except:
            self.showbranconfig()
        self.Corpus.loadFromUDpipe()

    def loadTextFromCSV(self):
        self.Corpus.loadTextFromCSV()

    def loadjson(self):
        QMessageBox.information(self, "Attenzione", "Caricare un file JSON non è più supportato.")

    #def opentextfile(self, fileName):
    #    lines = ""
    #    try:
    #        text_file = open(fileName, "r", encoding='utf-8')
    #        lines = text_file.read()
    #        text_file.close()
    #    except:
    #        myencoding = "ISO-8859-15"
    #        #https://pypi.org/project/chardet/
    #        gotEncoding = False
    #        while gotEncoding == False:
    #            try:
    #                myencoding = QInputDialog.getText(self.w, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
    #            except:
    #                print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
    #                myencoding = [input()]
    #            try:
    #                # TODO: prevediamo la codifica "FORCE", che permette di leggere il file come binario ignorando caratteri strani
    #                text_file = open(fileName, "r", encoding=myencoding[0])
    #                lines = text_file.read()
    #                text_file.close()
    #                gotEncoding = True
    #            except:
    #                gotEncoding = False
    #    return lines

    def importfromTreeTagger(self):
        self.Corpus.importfromTreeTagger()

    def loadCSV(self):
        self.Corpus.loadCSV()

    def convertiDaTint(self):
        self.Corpus.convertiDaTint()

    #def corpusCellChanged(self, row, col):
    #    if self.Corpus.ImportingFile:
    #        return
    #    try:
    #        startline = self.w.daToken.value()
    #        self.corpus[row+startline][col] = self.w.corpus.item(row,col).text()
    #    except:
    #        print("Error editing cell")
    #        self.updateCorpus()

    def menualltoken(self):
        self.w.allToken.setChecked(self.w.actionTutti_i_token.isChecked())
        self.updateCorpus()

    def setalltokens(self):
        self.Corpus.setStart(self.w.daToken.value())
        self.Corpus.setEnd(self.w.aToken.value())
        self.Corpus.setAllTokens(self.w.allToken.isChecked())

    def updateCorpus(self):
        self.Corpus.updateCorpus()

    def linescount(self, filename):
        f = open(filename, "r+", encoding='utf-8')
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

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

    def showbranconfig(self):
        self.BranSetdialog = settings.Form(self, self.Corpus)
        self.BranSetdialog.exec()
        if self.BranSetdialog.accepted:
            self.Corpus.mycfg["javapath"] = self.BranSetdialog.w.java.text()
            self.Corpus.mycfg["tintpath"] = self.BranSetdialog.w.tintlib.text()
            self.Corpus.mycfg["tintaddr"] = self.BranSetdialog.w.address.text()
            self.Corpus.mycfg["tintport"] = self.BranSetdialog.w.port.text()
            self.Corpus.mycfg["udpipe"] = self.BranSetdialog.w.udpipe.text()
            self.Corpus.mycfg["rscript"] = self.BranSetdialog.w.rscript.text()
            self.Corpus.mycfg["sessions"] = json.loads(self.BranSetdialog.w.sessions.text())
            self.Corpus.mycfg["udpipemodels"] = json.loads(self.BranSetdialog.w.udpipemodels.text())
            self.Corpus.mycfg["facebook"] = json.loads(self.BranSetdialog.w.facebook.text())
            self.Corpus.mycfg["twitter"] = json.loads(self.BranSetdialog.w.twitter.text())
            self.Corpus.mycfg["tempDir"] = self.BranSetdialog.w.tempDir.text()
            self.Corpus.mycfg["disableProgress"] = self.BranSetdialog.w.disableProgress.isChecked()
            print("Full config:")
            print(self.Corpus.mycfg)
        self.Corpus.savePersonalCFG()

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
        if column == self.corpuscols["pos"][0]:
            try:
                newtext = self.legendaPos[text][0]
                titem.setToolTip(newtext)
            except:
                newtext = text
        self.w.corpus.setItem(row, column, titem)

    def sanitizeTable(self, table):
        for row in range(table.rowCount()):
            for col in range(table.columnCount()):
                if not table.item(row,col):
                    self.setcelltocorpus("", row, col)

    #def sanitizeCorpus(self):
    #    for row in range(len(self.corpus)):
    #        for col in range(len(self.corpuscols)):
    #            try:
    #                self.corpus[row][col] = str(self.corpus[row][col])
    #            except:
    #                self.corpus[row][col] = ""

    def texteditor(self):
        self.Corpus.texteditor()

    def tableeditor(self, runner = ""):
        TBdialog = tableeditor.Form(self.w.corpus, self.Corpus.mycfg)
        TBdialog.sessionDir = self.sessionDir
        TBdialog.w.apricsv.show()
        TBdialog.show()
        if runner == "init":
            TBdialog.hide()

    def confronto(self):
        self.Corpus.confronto()

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
        self.Corpus.misure_lessicometriche()

    def gulpease(self):
        self.Corpus.gulpease()
