#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
import re
from os import listdir
from os.path import isfile, join
import urllib.request
import urllib.parse
import html
import datetime
import json
import subprocess
from socket import timeout
import platform
import time

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtCore import Qt
from PySide2.QtCore import Signal
from PySide2.QtCore import QThread
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QLineEdit
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem #QtGui?

from forms import progress


class TintRunner(QThread):
    dataReceived = Signal(bool)

    def __init__(self, widget,addr = ""):
        QThread.__init__(self)
        self.w = widget
        self.iscli = False
        try:
            if self.w == "cli":
                self.iscli = True
        except:
            self.iscli = False
        self.setTerminationEnabled(True)

    def loadvariables(self, javavar, tintdirvar, tintportvar):
        self.Java = javavar
        self.TintDir = tintdirvar
        self.TintPort = tintportvar

    def __del__(self):
        print("Shutting down thread")

    def run(self):
        self.runServer()
        return

    def runServer(self):
        print("Eseguo il server Tint")
        readystring = "TintServer - Pipeline loaded"  #"[HttpServer] Started"
        CLASSPATH = self.TintDir+"/*"
        args = [self.Java,"-classpath", CLASSPATH, "eu.fbk.dh.tint.runner.TintServer", "-p ",self.TintPort]
        lowram = False
        try:
            import psutil
            mymem = dict(psutil.virtual_memory()._asdict())
            if mymem["total"]/1000000 < 2048:
                lowram = True
        except:
            lowram = True
        if lowram:
            swapinfo = "/etc/dphys-swapfile"
            lines = ""
            if os.path.isfile(swapinfo):
                text_file = open(swapinfo, "r", encoding='utf-8')
                lines = text_file.read()
                text_file.close()
            badswap = True
            for line in lines.split("\n"):
                if "CONF_SWAPSIZE" in line:
                    try:
                        swsize = int(line.split("=")[1])
                    except:
                        swsize = 0
                    if swsize >= 2048:
                        badswap = False
            if badswap:
                msg = "Sembra che tua abbia poca memoria e uno swap piccolo. Per favore, apri il file " + swapinfo + " con privilegi di amministrazione e imposta la riga:\nCONF_SWAPSIZE=2048\nDovrai riavviare il computer perché le modifiche siano effettive."
                if self.iscli:
                    print(msg)
                else:
                    QMessageBox.warning(self.w, "Poca memoria", msg)
            args = [self.Java,"-Xmx1800m", "-classpath", CLASSPATH, "eu.fbk.dh.tint.runner.TintServer", "-p ",self.TintPort]
        print(self.Java)
        try:
            p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            while True:
                lineb = p.stdout.readline()
                line = str(lineb)
                if self.iscli:
                    print("++"+line+"++")
                else:
                    self.w.loglist.addItem(line)
                    self.w.loglist.setCurrentRow(self.w.loglist.count()-1)
                    QApplication.processEvents()
                if readystring in line:
                    break
            self.dataReceived.emit(True)
            self.w.quit.clicked.emit()
        except:
            self.dataReceived.emit(False)



class TintCorpus(QThread):
    dataReceived = Signal(bool)
    updated = Signal(int)

    def __init__(self, widget, fnames, corpcol, myTintAddr):
        QThread.__init__(self)
        self.corpuswidget = widget
        self.fileNames = fnames
        self.corpuscols = corpcol
        self.Tintaddr = myTintAddr
        self.outputcsv = ""
        self.language = "it-IT"
        self.csvIDcolumn = -1
        self.csvTextcolumn = -1
        self.loadvariables()
        self.setTerminationEnabled(True)
        self.iscli = False
        try:
            if self.corpuswidget == "cli":
                self.iscli = True
        except:
            self.iscli = False
        self.alwaysyes = False
        self.rowfilename = ""

    def loadvariables(self):
        #http://localhost:8012/tint?text=Barack%20Obama%20era%20il%20presidente%20degli%20Stati%20Uniti%20d%27America.
        self.TintTimeout = 60 #300
        self.useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

    def __del__(self):
        print("Shutting down thread")

    def run(self):
        self.loadtxt()
        return

    def loadtxt(self):
        fileID = 0
        self.Progrdialog = progress.Form()
        if not self.iscli:
            self.updated.connect(self.Progrdialog.setValue)
            self.Progrdialog.show()
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
                        while gotEncoding == False:
                            try:
                                self.Progrdialog.hide()
                                myencoding = QInputDialog.getText(self.corpuswidget, "Scegli la codifica", "Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)", QLineEdit.Normal, myencoding)
                                self.Progrdialog.show()
                            except:
                                print("Sembra che questo file non sia codificato in UTF-8. Vuoi provare a specificare una codifica diversa? (Es: cp1252 oppure ISO-8859-15)")
                                myencoding = [input()]
                            try:
                                text_file = open(fileName, "r", encoding=myencoding[0])
                                lines = text_file.read()
                                text_file.close()
                                gotEncoding = True
                            except:
                                gotEncoding = False
                    self.rowfilename = fileName + ".tmp"
                    if self.iscli:
                        self.outputcsv = fileName + ".tsv"
                    print(fileName + " -> " + self.outputcsv)
                    if self.csvIDcolumn <0 or self.csvTextcolumn <0:
                        try:
                            corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:tint"
                            self.Progrdialog.hide()
                            corpusID = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus:", QLineEdit.Normal, corpusID)[0]
                            self.Progrdialog.show()
                        except:
                            corpusID = str(fileID)+"_"+os.path.basename(fileName)+",lang:"+self.language+",tagger:tint"
                        self.text2corpusTINT(lines, corpusID)
                    else:
                        try:
                            sep = QInputDialog.getText(self.corpuswidget, "Scegli il separatore", "Indica il carattere che separa le colonne (\\t è la tabulazione):", QLineEdit.Normal, "\\t")[0]
                            if sep == "\\t":
                                sep = "\t"
                            self.Progrdialog.hide()
                            textID = QInputDialog.getInt(self.corpuswidget, "Scegli il testo", "Indica la colonna della tabella che contiene il testo di questo sottocorpus:")[0]
                            corpusIDtext = QInputDialog.getText(self.corpuswidget, "Scegli il tag", "Indica il tag di questo file nel corpus. Puoi usare [filename] per indicare il nome del file e [numeroColonna] per indicare la colonna da cui estrarre un tag.", QLineEdit.Normal, "[filename], [0]"+",tagger:tint")[0]
                            self.Progrdialog.show()
                            textID = int(textID)
                            for line in lines.split("\n"):
                                corpusID = corpusIDtext.replace("[filename]", os.path.basename(fileName))
                                indexes = [(m.start(0), m.end(0)) for m in re.finditer('\[[0-9]*\]', corpusID)]
                                for n in range(len(indexes)):
                                    start = indexes[n][0]
                                    end = indexes[n][1]
                                    try:
                                        strCol = corpusID[start:end]
                                        intCol = int(corpusID[start+1:end-1])
                                        corpusID = corpusID.replace(strCol, line.split(sep)[intCol])+",lang:"+self.language+",tagger:tint"
                                    except:
                                        print("Impossibile trovare la colonna nel CSV")
                                print(corpusID)
                                self.text2corpusTINT(line.split(sep)[textID], corpusID)
                        except:
                            try:
                                textID = int(self.csvTextcolumn)
                                colID = int(self.csvIDcolumn)
                                if textID != colID:
                                    for line in lines.split("\n"):
                                        corpusID = line.split("\t")[colID]+",lang:"+self.language+",tagger:tint"
                                        self.text2corpusTINT(line.split("\t")[textID], corpusID)
                            except:
                                continue
        if self.fileNames == []:
            testline = "Il gatto è sopra al tetto."
            myres = self.getJson(testline)
            try:
                myarray = json.loads(myres)
                self.dataReceived.emit(True)
            except:
                self.dataReceived.emit(False)
        self.Progrdialog.accept()


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

    def text2corpusTINT(self, text, TAGcorpus):
        #process
        itext = text.replace('.','.\n')
        itext = itext.replace('?','?\n')
        itext = itext.split('\n')
        #itext = re.split('[\n\.\?]', text)
        totallines = len(itext)
        print("Total lines: "+str(totallines))
        self.Progrdialog.setBasetext("Sto lavorando sulla frase numero ")
        self.Progrdialog.setTotal(totallines)
        startatrow = -1
        try:
            if os.path.isfile(self.rowfilename):
                ch = "Y"
                if self.iscli:
                    if self.alwaysyes:
                        ch = "y"
                    else:
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
                with open(self.rowfilename, "r", encoding='utf-8') as ins:
                    for line in ins:
                        if int(line.split("\t")[self.corpuscols["IDphrase"][0]]) > IDphrase:
                            IDphrase = int(line.split("\t")[self.corpuscols["IDphrase"][0]])
        except:
            IDphrase = -1
        row = 0
        for line in itext:
            row = row + 1
            if row > startatrow:
                #self.Progrdialog.w.testo.setText("Sto lavorando sulla frase numero "+str(row))
                #self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                self.updated.emit(row)
                if not self.iscli and row % 20 == 0:
                    QApplication.processEvents()
                if self.Progrdialog.w.annulla.isChecked():
                    return
                myres = ""
                if line != "":
                    myres = self.getJson(line)
                try:
                    myarray = json.loads(myres)
                except:
                    #print("Errore nella lettura:")
                    #print(line)
                    myarray = {'sentences': []}
                oldtokens = ["A", "A", "A"]
                indoltk = 0
                legenda = {'A': ['adj'], 'AP': ['adj'], 'B': ['adv','prep'], 'BN': ['adv'], 'I': ['adv'], 'S': ['n'], 'T': ['pron'], 'RI': ['art'], 'RD': ['art','pron'], 'V': ['v'], 'E': ['prep'], 'VA': ['v'], 'CC': ['conj'], 'PC': ['art','pron'], 'PR': ['conj', 'pron'], 'VM': ['v'], 'CS': ['conj'], 'PE': ['pron'], 'DD': ['adj'], 'DI': ['pron', 'adj'], 'PI': ['pron'], 'SW': ['n']}
                for sentence in myarray["sentences"]:
                    IDphrase = IDphrase +1
                    for token in sentence["tokens"]:
                        morfL = str(token["full_morpho"]).split(' ')
                        posL = str(token["pos"]).split('+')
                        oldtokens[indoltk%3] = posL[0]
                        indoltk = indoltk +1
                        morf = ""
                        try:
                            posN = 0
                            for pos in posL:
                                posML = legenda[pos]
                                ind = 0
                                c = False
                                for morfT in morfL:
                                    #c = False
                                    if ind == 0 and pos=="V" and "VA" in oldtokens:
                                        oldtokens = ["A", "A", "A"]
                                        #se preceduto da ausiliare, è un participio
                                        indo2 = 0
                                        for morfT in morfL:
                                            if "v+part+" in morfT:
                                                ind = indo2
                                                c = True
                                                break
                                            indo2 = indo2 +1
                                    stupidoimperativo = True
                                    for posM in posML:
                                        if bool(re.match('.*?\+'+posM+'([\+/].*?|$)', morfT)):
                                            if "v+imp+pres+" in morfT:
                                                if stupidoimperativo == False:
                                                    if "+2+plur" in morfT or "+2+sing" in morfT:
                                                        if 'I' in oldtokens:
                                                            c = True #il modo imperativo è legittimo solo per seconda persona e solo se c'è una interiezione
                                                            break
                                            else:
                                                c = True
                                                break
                                    if c:
                                        break
                                    ind = ind + 1
                                txt = morfL[ind]
                                if posN > 0:
                                    stind = txt.index('/')+1
                                    stind = txt.index('~',stind)+1
                                    stind = txt.index('+',stind)+1
                                    txt = txt[stind:]
                                else:
                                    stind = txt.index('+')+1
                                    if '/' in txt:
                                        enind = txt.index('/')+1
                                    else:
                                        enind = len(txt)
                                    txt = txt[stind:enind]
                                morf = morf + txt
                                posN = posN +1
                        except:
                            morf = str(token["full_morpho"]) #.split(" ")[0]
                            #print(posL)
                            #print(str(token["full_morpho"]))
                        if self.outputcsv == "":
                            print("You don't have a session. Tint is not going to run.")
                            return
                        else:
                            fullline = str(TAGcorpus) + "\t"
                            fullline = fullline + str(token["originalText"]) + "\t"
                            fullline = fullline + str(token["lemma"]) + "\t"
                            fullline = fullline + str(token["pos"]) + "\t"
                            fullline = fullline + str(token["ner"]) + "\t"
                            fullline = fullline + str(morf) + "\t"
                            fullline = fullline + str(token["index"]) + "\t"
                            fullline = fullline + str(IDphrase)
                            for mydep in sentence["basic-dependencies"]:
                                if mydep["dependent"] == token["index"]:
                                    fullline = fullline + "\t" + str(mydep["dep"]) + "\t"
                                    fullline = fullline + str(mydep["governor"])
                                    break
                            fdatefile = self.outputcsv
                            fullline = self.isdt_to_ud(fullline)
                            with open(fdatefile, "a", encoding='utf-8') as myfile:
                                myfile.write(fullline+"\n")
                if self.iscli:
                    with open(self.rowfilename, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
        if self.iscli:
            print("Done")

    def getJson(self, text):
        #http://localhost:8012/tint?text=Barack%20Obama%20era%20il%20presidente%20degli%20Stati%20Uniti%20d%27America.
        urltext = urllib.parse.quote(text)
        #print(urltext)
        thisurl = self.Tintaddr+"?text=" + urltext
        if thisurl == '':
            return ''
        req = urllib.request.Request(
            thisurl,
            data=None,
            headers={
                'User-Agent': self.useragent
            }
        )

        thishtml = ""
        try:
            f = urllib.request.urlopen(req,timeout=self.TintTimeout)
            ft = f.read() #we should stop if this is taking too long
        except:
            ft = ""
            msg = "ERRORE: Tint non risponde. Prova a chiudere il processo \"java\" e riavviare."
            if self.iscli:
                print(msg)
                sys.exit(1)
            else:
                ret = QMessageBox.question(self.corpuswidget,'Errore', msg + " Vuoi chiudere Bran?", QMessageBox.Yes | QMessageBox.No)
                if ret == QMessageBox.Yes:
                    sys.exit(1)
        try:
            thishtml = ft.decode('utf-8', 'backslashreplace')
        except:
            thishtml = str(ft)
        return thishtml

    #
    def isdt_to_ud(self, fullline):
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/isdt-ud.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        legendaISDTUD = json.loads(myjson)
        thisline = fullline.split("\t")
        Ucolumns = []
        for key in self.corpuscols:
            #TAGcorpus
            if key == "TAGcorpus":
                tags = thisline[self.corpuscols[key][0]]
                if not "lang:" in tags:
                    tags = tags+",lang:"+self.language
                if not "tagger:tint" in tags:
                    tags = tags+",tagger:tint"
                Ucolumns.append(tags)
            if key == "IDword":
                Ucolumns.append(thisline[self.corpuscols['IDword'][0]])
            if key == "IDphrase":
                Ucolumns.append(thisline[self.corpuscols['IDphrase'][0]])
            if key == "token":
                Ucolumns.append(thisline[self.corpuscols['token'][0]])
            if key == "lemma":
                if "[PUNCT]" in thisline[self.corpuscols['lemma'][0]]:
                    Ucolumns.append(thisline[self.corpuscols['token'][0]])
                else:
                    Ucolumns.append(thisline[self.corpuscols['lemma'][0]])
            if key == "pos":
                mypos = thisline[self.corpuscols['pos'][0]]
                myposU = legendaISDTUD["pos"][mypos][0]
                Ucolumns.append(myposU)
            if key == "feat":
                myfeat = thisline[self.corpuscols['feat'][0]]
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
            if key == "head":
                Ucolumns.append(thisline[self.corpuscols['head'][0]])
            if key == "dep":
                Ucolumns.append(thisline[self.corpuscols['dep'][0]])
            if key == "ner":
                Ucolumns.append(thisline[self.corpuscols['ner'][0]])
        #print(Ucolumns)
        csv = ""
        for col in range(len(Ucolumns)):
            if Ucolumns[col] == "":
                Ucolumns[col] = "_"
            if col > 0:
                csv = csv + "\t"
            csv = csv + Ucolumns[col]
        return csv


class Form(QDialog):
    def __init__(self, parent=None, mycfg=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/tint.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        if mycfg == None or mycfg["tintaddr"] == "":
            self.loadsettings()
        else:
            self.w.java.setText(mycfg["javapath"])
            self.w.tintlib.setText(mycfg["tintpath"])
            self.w.address.setText(mycfg["tintaddr"])
            self.w.port.setText(mycfg["tintport"])
        self.w.quit.clicked.connect(self.quitme)
        self.w.loadjava.clicked.connect(self.loadjava)
        self.w.loadtint.clicked.connect(self.loadtint)
        self.w.installJava.clicked.connect(self.installJava)
        self.w.installTint.clicked.connect(self.installTint)
        self.setWindowTitle("Impostazioni di Tint")
        self.notint = False

    def quitme(self):
        self.notint = True
        self.accept()

    def installJava(self):
        url = "https://jdk.java.net/13/"
        QMessageBox.information(self, "Scarica Java", "Se non hai Java puoi scaricarlo da qui per Windows: <a href=\""+url+"\">"+url+"</a>. Devi solo estrarre il file con 7Zip, non servono privilegi di amministrazione. Poi, indica la posizione del file java.exe (di solito nella cartella bin).")

    def installTint(self):
        url = "https://github.com/dhfbk/tint/releases/download/0.2/tint-runner-0.2-bin.tar.gz"
        QMessageBox.information(self, "Scarica Tint", "Se non hai Tint puoi scaricarlo da qui per Windows: <a href=\""+url+"\">"+url+"</a>. Devi solo estrarre il file con 7Zip, non servono privilegi di amministrazione. Poi, indica la posizione della cartella lib.")

    def loadsettings(self):
        if platform.system() == "Windows":
            jdir = "C:/Program Files/Java/"
            try:
                jfiles = os.listdir(jdir)
            except:
                jfiles = []
            jre = ""
            for fil in jfiles:
                if "jre" in fil:
                    jre = fil
            if jre == "":
                self.w.java.setText("")
            else:
                self.w.java.setText(jdir+jre+"/bin/java.exe")
        else:
            self.w.java.setText("/usr/bin/java")
        if platform.system() == "Windows":
            self.w.tintlib.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"\\tint\\lib")
        else:
            self.w.tintlib.setText(os.path.abspath(os.path.dirname(sys.argv[0]))+"/tint/lib")
        self.w.port.setText("8012")
        self.w.address.setText("localhost") #http://localhost:8012/tint

    def loadjava(self):
        QMessageBox.information(self, "Hai già Java?", "Se non hai Java puoi scaricarlo da qui per Windows: <a href=\"https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz\">https://download.java.net/java/GA/jdk10/10.0.1/fb4372174a714e6b8c52526dc134031e/10//openjdk-10.0.1_windows-x64_bin.tar.gz</a>. Devi solo estrarre il file con 7Zip, non servono privilegi di amministrazione. Poi, indica la posizione del file java.exe (di solito nella cartella bin).")
        fileName = QFileDialog.getOpenFileName(self, "Trova Java", ".", "Java (*.exe)")[0]
        if fileName != "":
            self.w.java.setText(fileName)

    def loadtint(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella di Tint")
        if fileName != "":
            self.w.tintlib.setText(fileName)
