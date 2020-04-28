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

try:
    from PySide2.QtWidgets import QApplication
except:
    try:
        thispkg = "le librerie grafiche"
        try:
            from tkinter import messagebox
            messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        except:
            print("Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
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
            print("Errore: Impossibile installare "+thispkg)
            print("Prova ariavviare Bran: se ottieni lo stesso errore, segnalalo.")
            print("If you don't have pip, please run 'python -m ensurepip'")
            print("Then try 'py -m pip install PySide2'")
            sys.exit(1)

#
try:
    import psutil
except:
    try:
        thispkg = "la libreria psutil"
        try:
            from tkinter import messagebox
            messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        except:
            print("Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
        pip.main(["install", "psutil"])
        #pip install --index-url=http://download.qt.io/snapshots/ci/pyside/5.9/latest/ pyside2 --trusted-host download.qt.io
        import psutil
    except:
        try:
            from pip._internal import main as pipmain
            pipmain(["install", "psutil"])
            import psutil
        except:
            print("Errore: Impossibile installare "+thispkg)
            print("Prova ariavviare Bran: se ottieni lo stesso errore, segnalalo.")
            sys.exit(1)


from PySide2.QtCore import QFile
from PySide2.QtCore import QDir
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow
from PySide2.QtCore import QThread


from forms import branwindow
from forms import tint
from forms import BranCorpus
from forms import texteditor
from forms import tableeditor
from forms import confronto

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

def occorrenzeNonBran():
    try:
        separator = sys.argv[4]
    except:
        separator = '\t'
    fileNames = []
    if os.path.isfile(sys.argv[2]):
        fileNames = [sys.argv[2]]
    if os.path.isdir(sys.argv[2]):
        for tfile in os.listdir(sys.argv[2]):
            if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                fileNames.append(os.path.join(sys.argv[2],tfile))
    try:
        col = int(sys.argv[3])
    except:
        col = 0
    for fileName in fileNames:
        table = []
        row = 0
        output = fileName + "-occorrenze-" + str(col) + ".tsv"
        recovery = output + ".tmp"
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery):
                ch = "Y"
                try:
                    if sys.argv[5] == "y" or sys.argv[5] == "Y":
                        ch = "Y"
                except:
                    print("Ho trovato un file di ripristino, lo devo usare? [Y/N]")
                    ch = input()
                if ch == "Y" or ch == "y":
                    with open(recovery, "r", encoding='utf-8') as tempfile:
                       lastline = (list(tempfile)[-1])
                    startatrow = int(lastline)
                    print("Carico la tabella")
                    with open(output, "r", encoding='utf-8') as ins:
                        for line in ins:
                            table.append(line.replace("\n","").replace("\r","").split(separator))
                    print("Comincio dalla riga " + str(startatrow))
                else:
                    table.append([os.path.basename(fileName)+"-"+str(col),"Occorrenze"])
            else:
                table.append([os.path.basename(fileName)+"-"+str(col),"Occorrenze"])
        except:
            startatrow = -1
            table.append([os.path.basename(fileName)+"-"+str(col),"Occorrenze"])
        with open(fileName, "r", encoding='utf-8') as ins:
            for line in ins:
                if row > startatrow:
                    try:
                        thistext = line.replace("\n","").replace("\r","").split(separator)[col]
                    except:
                        thistext = ""
                    tbrow = findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                    if row % 500 == 0:
                        savetable(table, output)
                        with open(recovery, "a", encoding='utf-8') as rowfile:
                            rowfile.write(str(row)+"\n")
                row = row + 1
            savetable(table, output)
            with open(recovery, "a", encoding='utf-8') as rowfile:
                rowfile.write(str(row)+"\n")



if __name__ == "__main__":
    corpuscols = {
                'TAGcorpus': [0, "Tag corpus"],
                'token': [1, "Forma grafica"],
                'lemma': [2, "Lemma"],
                'pos': [3, "Tag PoS"],
                'ner': [4, "Tag NER"],
                'feat': [5, "Morfologia"],
                'IDword': [6, "ID parola"],
                'IDphrase': [7, "ID frase"],
                'dep': [8, "Tag Dep"],
                'head': [9, "Head"]
    }
    ignoretext = "((?<=[^0-9])"+ re.escape(".")+ "|^" + re.escape(".")+ "|(?<= )"+ re.escape("-")+ "|^"+re.escape("-")+ "|"+re.escape(":")+"|(?<=[^0-9])"+re.escape(",")+"|^"+re.escape(",")+"|"+re.escape(";")+"|"+re.escape("?")+"|"+re.escape("!")+"|"+re.escape("«")+"|"+re.escape("»")+"|"+re.escape("\"")+"|"+re.escape("(")+"|"+re.escape(")")+"|^"+re.escape("'")+ "|" + re.escape("[PUNCT]") + "|" + re.escape("[SYMBOL]") + "|" + re.escape("<unknown>") + ")"
    dimList = [100,1000,5000,10000,50000,100000,150000,200000,250000,300000,350000,400000,450000,500000,1000000]
    try:
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/ud.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        legendaPos = json.loads(myjson)
    except:
        legendaPos = {"A":["aggettivo", "aggettivi", "piene"],"AP":["agg. poss", "aggettivi", "piene"],"B":["avverbio", "avverbi", "piene"],"B+PC":["avverbio+pron. clit. ", "avverbi", "piene"],"BN":["avv, negazione", "avverbi", "piene"],"CC":["cong. coord", "congiunzioni", "vuote"],"CS":["cong. sub.", "congiunzioni", "vuote"],"DD":["det. dim.", "aggettivi", "piene"],"DE":["det. esclam.", "aggettivi", "piene"],"DI":["det. indefinito", "aggettivi", "piene"],"DQ":["det. interr.", "aggettivi", "piene"],"DR":["det. Rel", "aggettivi", "piene"],"E":["preposizione", "preposizioni", "vuote"],"E+RD":["prep. art. ", "preposizioni", "vuote"],"FB":["punteggiatura - \"\" () «» - - ", "punteggiatura", "none"],"FC":["punteggiatura - : ;", "punteggiatura", "none"],"FF":["punteggiatura - ,", "punteggiatura", "none"],"FS":["punteggiatura - .?!", "punteggiatura", "none"],"I":["interiezione", "interiezioni", "vuote"],"N":["numero", "altro", "none"],"NO":["numerale", "aggettivi", "piene"],"PC":["pron. Clitico", "pronomi", "vuote"],"PC+PC":["pron. clitico+clitico", "pronomi", "vuote"],"PD":["pron. dimostrativo", "pronomi","vuote"],"PE":["pron. pers. ", "pronomi", "vuote"],"PI":["pron. indef.", "pronomi", "vuote"],"PP":["pron. poss.", "pronomi", "vuote"],"PQ":["pron. interr.", "pronomi", "vuote"],"PR":["pron. rel.", "pronomi", "vuote"],"RD":["art. Det.", "articoli", "vuote"],"RI":["art. ind.", "articoli", "vuote"],"S":["sost.", "sostantivi", "piene"],"SP":["nome proprio", "sostantivi", "piene"],"SW":["forestierismo", "altro", "none"],"T":["det. coll.)", "aggettivi", "piene"],"V":["verbo", "verbi", "piene"],"V+PC":["verbo + pron. clitico", "verbi", "piene"],"V+PC+PC":["verbo + pron. clitico + pron clitico", "verbi", "piene"],"VA":["verbo ausiliare", "verbi", "piene"],"VA+PC":["verbo ausiliare + pron.clitico", "verbi", "piene"],"VM":["verbo mod", "verbi", "piene"],"VM+PC":["verbo mod + pron. clitico", "verbi", "piene"],"X":["altro", "altro", "none"]}
    if len(sys.argv)>1:
        w = "cli"
        app = QApplication(sys.argv)
        Corpus = BranCorpus.BranCorpus(corpuscols, legendaPos, ignoretext, dimList, tablewidget=w)
        Corpus.loadPersonalCFG()
        #print(Corpus.mycfg)
        if sys.argv[1] == "help" or sys.argv[1] == "aiuto":
            print("Le colonne di un corpus sono le seguenti:\n")
            print(Corpus.corpuscols)
            print("\n")
            print("Elenco dei comandi:\n")
            print("python3 main.py tintstart [brancfg]\n")
            print("python3 main.py txt2corpus file.txt|cartella [indirizzoServerTint] [ripristino (y/n)]\n")
            print("python3 main.py splitbigfile file.txt [maxnumberoflines] [.]\n")
            print("python3 main.py samplebigfile file.txt [maxnumberoflines] [.]\n")
            print("python3 main.py occorrenze file.tsv|cartella colonna [ripristino (y/n)]\n")
            print("python3 main.py occorrenzeFiltrate file.tsv|cartella colonna [filtro] [ripristino (y/n)]\n")
            print("python3 main.py occorrenzeNonBran file.tsv|cartella [colonna] [separatore] [ripristino (y/n)]\n")
            print("python3 main.py occorrenzeNormalizzate file.tsv|cartella [colonna] [ripristino (y/n)]\n")
            print("python3 main.py coOccorrenze file.tsv|cartella parola colonna range [ripristino (y/n)]\n")
            print("python3 main.py concordanze file.tsv|cartella parola colonna range [ripristino (y/n)]\n")
            print("python3 main.py estraicolonna file.tsv|cartella colonna\n")
            print("python3 main.py contaverbi file.tsv|cartella [ignora persona (y/n)] [ripristino (y/n)]\n")
            print("python3 main.py misurelessico file.tsv|cartella [colonna] [ripristino (y/n)]\n")
            print("python3 main.py mergetables file1,file2|cartella colonnaChiave [sum|mean|diff,sum|mean|diff] [1] [ripristino (y/n)]\n")
            print("python3 main.py ricostruisci file.tsv|cartella [colonna] [ignorapunteggiatura (y/n)] [filtro] [ripristino (y/n)]\n")
            print("python3 main.py texteditor file.tsv|cartella\n")
            print("python3 main.py confronto file.tsv|cartella\n")
            print("Gli argomenti tra parentesi [] sono facoltativi.")
            print("\nI comandi preceduti da * sono sperimentali o non ancora implementati.")
            sys.exit(0)
        if sys.argv[1] == "txt2corpus":
            fileNames = []
            if os.path.isfile(sys.argv[2]):
                fileNames = [sys.argv[2]]
            if os.path.isdir(sys.argv[2]):
                for tfile in os.listdir(sys.argv[2]):
                    if tfile[-4:] == ".txt":
                        fileNames.append(os.path.join(sys.argv[2],tfile))
            try:
                tmpurl = sys.argv[3]
            except:
                tmpurl = "localhost"
            tinturl = "http://" + tmpurl + ":8012/tint"
            TCThread = tint.TintCorpus(w, fileNames, corpuscols, tinturl)
            TCThread.outputcsv = fileNames[0] + ".tsv"
            try:
                if sys.argv[4] == "y" or sys.argv[4] == "Y":
                    TCThread.alwaysyes = True
            except:
                TCThread.alwaysyes = False
            TCThread.finished.connect(sys.exit)
            TCThread.start()
            while True:
                time.sleep(10)
        if sys.argv[1] == "tintstart":
            TintThread = tint.TintRunner(w)
            try:
                text_file = open(sys.argv[2], "r", encoding='utf-8')
                lines = text_file.read()
                text_file.close()
                mycfg = json.loads(lines.replace("\n", "").replace("\r", ""))
            except:
                mycfg = Corpus.mycfg
            try:
                Java = mycfg["javapath"]
                TintDir = mycfg["tintpath"]
                TintPort = mycfg["tintport"]
            except:
                Java = "/usr/bin/java"
                TintPort = "8012"
                TintDir = os.path.abspath(os.path.dirname(sys.argv[0]))+"/tint/lib"
            TintThread.loadvariables(Java, TintDir, TintPort)
            TintThread.start()
            time.sleep(30)
            print("\nNON CHIUDERE QUESTA FINESTRA:  Tint è eseguito dentro questa finestra. Avvia di nuovo Bran.")
            print("\n\nNON CHIUDERE QUESTA FINESTRA")
        if sys.argv[1] == "texteditor":
            te = texteditor.TextEditor(None, Corpus.mycfg)
            if len(sys.argv)>2:
                fileNames = []
                for i in range(2, len(sys.argv)):
                    if os.path.isfile(sys.argv[i]):
                        fileNames = [sys.argv[i]]
                    if os.path.isdir(sys.argv[i]):
                        for tfile in os.listdir(sys.argv[i]):
                            if tfile[-4:] == ".txt":
                                fileNames.append(os.path.join(sys.argv[i],tfile))
                    te.aprilista(fileNames)
            te.show()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
            sys.exit(app.exec_())
        if sys.argv[1] == "confronto":
            cf = confronto.Confronto(None, Corpus.mycfg, os.path.abspath(os.path.dirname(sys.argv[0])), corpuscols)
            cf.legendaPos = legendaPos
            cf.ignoretext = ignoretext
            cf.dimList = dimList
            if len(sys.argv)>2:
                for i in range(2, len(sys.argv)):
                    if os.path.isfile(sys.argv[i]):
                        cf.w.corpora.addItem(sys.argv[i])
                    if os.path.isdir(sys.argv[i]):
                        for tfile in os.listdir(sys.argv[i]):
                            if tfile[-4:] == ".tsv" or tfile[-4:] == ".csv":
                                cf.w.corpora.addItem(os.path.join(sys.argv[i],tfile))
            cf.show()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
            sys.exit(app.exec_())
        if sys.argv[1] == "occorrenzeNonBran":
            occorrenzeNonBran()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "occorrenze":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                mycol = sys.argv[3]
            except:
                mycol = 0
            try:
                rch = sys.argv[4]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_calcola_occorrenze(mycol, myrecovery)
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "occorrenzeFiltrate":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                mycol = sys.argv[3]
            except:
                mycol = 0
            try:
                myfilter = sys.argv[4]
            except:
                myfilter = ""
            try:
                rch = sys.argv[5]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_occorrenzeFiltrate(mycol, myfilter, myrecovery)
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "coOccorrenze":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                parola = sys.argv[3]
            except:
                sys.exit()
            try:
                mycol = int(sys.argv[4])
            except:
                mycol = 0
            try:
                myrange = int(sys.argv[5])
            except:
                myrange = 0
            try:
                rch = sys.argv[6]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_calcola_coOccorrenze(parola, mycol, myrange, True, myrecovery, "")
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "concordanze":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                parola = sys.argv[3]
            except:
                sys.exit()
            try:
                mycol = int(sys.argv[4])
            except:
                mycol = 0
            try:
                myrange = int(sys.argv[5])
            except:
                myrange = 0
            try:
                rch = sys.argv[6]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_calcola_concordanze(parola, mycol, myrange, True, myrecovery, "")
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "ricostruisci":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                mycol = int(sys.argv[3])
            except:
                mycol = 1
            try:
                if sys.argv[4] == "y" or sys.argv[4] == "Y":
                    myignore = True
                else:
                    myignore = 0/0
            except:
                myignore = False
            try:
                myfilter = sys.argv[5]
            except:
                myfilter = ""
            #try:
            #    rch = sys.argv[6]
            #except:
            #    print("Vuoi usare un file di ripristino? [Y/N]")
            #    rch = input()
            #if rch == "Y" or rch == "y":
            #    myrecovery = True
            #else:
            #    myrecovery = False
            #Corpus.separator = '\t'
            ignpos = []
            if myignore:
                ignpos = Corpus.ignorepos
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_ricostruisci(Corpus.corpus, mycol, ignpos, 0, 0, myfilter)
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "contaverbi":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            ignoreperson = False
            try:
                if sys.argv[3] == "y" or sys.argv[3] == "Y":
                    ignoreperson = True
            except:
                print("Vuoi ignorare persona, numero, genere, e caratteristica clitica dei verbi? [Y/N]")
                ch = input()
                if ch == "Y" or ch == "y":
                    ignoreperson = True
            try:
                if sys.argv[4] == "y" or sys.argv[4] == "Y":
                    contigui = "Y"
            except:
                print("Vuoi che i verbi composti siano contigui? [Y/N]")
                contigui = input()
            try:
                rch = sys.argv[5]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_contaverbi(ignoreperson, contigui, myrecovery)
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "estraicolonna":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                mycol = sys.argv[3]
            except:
                mycol = 0
            try:
                rch = sys.argv[4]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            Corpus.core_estrai_colonna(fileNames, mycol, myrecovery)
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "splitbigfile":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                maxrow = sys.argv[3]
            except:
                maxrow = 0
            try:
                mysplit = sys.argv[4]
            except:
                mysplit = "."
            try:
                rch = sys.argv[5]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            Corpus.core_splitbigfile(myfiles, maxrow, mysplit, myrecovery)
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "samplebigfile":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                maxrow = sys.argv[3]
            except:
                maxrow = 0
            try:
                mysplit = sys.argv[4]
            except:
                mysplit = "."
            try:
                rch = sys.argv[5]
            except:
                #print("Vuoi usare un file di ripristino? [Y/N]")
                #rch = input()
                rch = "N"
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            Corpus.core_samplebigfile(myfiles, maxrow, mysplit, myrecovery)
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "mergetables":
            try:
                if os.path.isdir(sys.argv[2]):
                    mydir = sys.argv[2]
                elif os.path.isfile(sys.argv[2].split(",")[0]):
                    mydir = sys.argv[2].split(",")
                else :
                    mydir = 0/0
            except:
                sys.exit()
            try:
                mycol = sys.argv[3]
            except:
                mycol = 1
            try:
                opstr = str(sys.argv[4])
            except:
                opstr = "sum"
            try:
                headerlines = str(sys.argv[5])
            except:
                headerlines = "1"
            try:
                rch = sys.argv[6]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            Corpus.core_mergetables(mydir, mycol, opstr, headerlines, myrecovery)
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "misurelessico":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                mycol = sys.argv[3]
            except:
                mycol = 1
            try:
                rch = sys.argv[4]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_misure_lessicometriche(mycol, myrecovery)
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "occorrenzeNormalizzate":
            try:
                myfiles = sys.argv[2]
            except:
                sys.exit()
            try:
                mycol = sys.argv[3]
            except:
                mycol = 0
            try:
                rch = sys.argv[4]
            except:
                print("Vuoi usare un file di ripristino? [Y/N]")
                rch = input()
            if rch == "Y" or rch == "y":
                myrecovery = True
            else:
                myrecovery = False
            #Corpus.separator = '\t'
            fileNames = []
            if os.path.isfile(myfiles):
                fileNames = [myfiles]
            if os.path.isdir(myfiles):
                for tfile in os.listdir(myfiles):
                    if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                        fileNames.append(os.path.join(myfiles,tfile))
            for fileName in fileNames:
                Corpus.CSVloader([fileName])
                Corpus.sessionFile = fileName
                Corpus.core_occorrenze_normalizzate(mycol, myrecovery)
                Corpus.chiudiProgetto()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        sys.exit(0)
    else:
        app = QApplication(sys.argv)
        w = branwindow.MainWindow(corpuscols, legendaPos, ignoretext, dimList)
        w.show()
        sys.exit(app.exec_())



