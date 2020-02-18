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
            print("Errore: Impossibile installare "+thispkg)
            print("If you don't have pip, please run 'python -m ensurepip'")
            print("Then try 'py -m pip install PySide2'")
            sys.exit(1)

#
try:
    import psutil
except:
    try:
        from tkinter import messagebox
        thispkg = "la libreria psutil"
        messagebox.showinfo("Installazione, attendi prego", "Sto per installare "+ thispkg +" e ci vorrà del tempo. Premi Ok e vai a prenderti un caffè.")
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
            sys.exit(1)


from PySide2.QtCore import QFile
from PySide2.QtCore import QDir
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QMainWindow
from PySide2.QtCore import QThread


from forms import branwindow



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
                    if sys.argv[4] == "y" or sys.argv[4] == "Y":
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


def contaverbi(corpuscols, legendaPos):
    poscol = corpuscols["pos"][0] #thisname.index(column[0])
    morfcol = corpuscols["feat"][0]
    separator = '\t'
    fileNames = []
    if os.path.isfile(sys.argv[2]):
        fileNames = [sys.argv[2]]
    if os.path.isdir(sys.argv[2]):
        for tfile in os.listdir(sys.argv[2]):
            if tfile[-4:] == ".csv" or tfile[-4:] == ".tsv":
                fileNames.append(os.path.join(sys.argv[2],tfile))
    for fileName in fileNames:
        #totallines = self.w.corpus.rowCount()
        table = []
        output = fileName + "-contaverbi.tsv"
        recovery = output + ".tmp"
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery):
                ch = "Y"
                try:
                    if sys.argv[4] == "y" or sys.argv[4] == "Y":
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
                    table.append(["Modo+Tempo", "Occorrenze", "Percentuali"])
            else:
                table.append(["Modo+Tempo", "Occorrenze", "Percentuali"])
        except:
            startatrow = -1
            table.append(["Modo+Tempo", "Occorrenze", "Percentuali"])
        corpus = []
        with open(fileName, "r", encoding='utf-8') as ins:
            for line in ins:
                corpus.append(line.replace("\n","").replace("\r","").split(separator))
        for row in range(len(corpus)):
            if row > startatrow:
                try:
                    thispos = legendaPos[corpus[row][poscol]][0]
                except:
                    thispos = ""
                thistext = ""
                thistext2 = ""
                if thispos.split(" ")[0] == "verbo":
                    try:
                        thistext = corpus[row][morfcol]
                    except:
                        thistext = ""
                if "ausiliare" in thispos:
                    for ind in range(1,4):
                        try:
                            tmpos = legendaPos[corpus[row+ind][poscol]][0]
                        except:
                            tmpos = ""
                        if "verbo" in tmpos:
                            thistext = ""
                            break
                elif thispos.split(" ")[0] == "verbo":
                    for ind in range(1,4):
                        try:
                            tmpos = legendaPos[corpus[row-ind][poscol]][0]
                        except:
                            tmpos = ""
                        if "ausiliare" in tmpos and "v+part+pass" in thistext:
                            thistext2 = thistext2 + "/" + corpus[row-ind][morfcol]
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
                    tbrow = findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
            if row % 500 == 0 or row == len(corpus)-1:
                savetable(table, output)
                with open(recovery, "a", encoding='utf-8') as rowfile:
                    rowfile.write(str(row)+"\n")
        #calcolo le percentuali
        print("Calcolo le percentuali")
        totallines = len(table)
        verbitotali = 0
        for row in range(len(table)):
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
        savetable(table, output)

def misure_lessicometriche(ignoretext, dimList):
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
        #totallines = self.w.corpus.rowCount()
        table = []
        output = fileName + "-" + str(col)+ "-misure_lessicometriche.tsv"
        recovery = output + ".tmp"
        startatrow = -1
        print(fileName + " -> " + output)
        try:
            if os.path.isfile(recovery):
                ch = "Y"
                try:
                    if sys.argv[4] == "y" or sys.argv[4] == "Y":
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
        except:
            startatrow = -1
        corpus = []
        with open(fileName, "r", encoding='utf-8') as ins:
            for line in ins:
                corpus.append(line.replace("\n","").replace("\r","").split(separator))
        totallines = len(corpus)
        totaltypes = 0
        mytypes = {}
        if startatrow >= (len(corpus)-1):
            continue
        for row in range(len(corpus)):
            if row > startatrow:
                thisposc = "False"
                try:
                    thistext = corpus[row][col]
                    if ignoretext != "":
                        thistext = re.sub(ignoretext, "", thistext)
                except:
                    thistext = ""
                if thistext != "":
                    tbrow = findintable(table, thistext, 0)
                    if tbrow>=0:
                        tbval = int(table[tbrow][1])+1
                        table[tbrow][1] = tbval
                    else:
                        newrow = [thistext, "1"]
                        table.append(newrow)
                        totaltypes = totaltypes + 1
                    if row % 500 == 0:
                        savetable(table, output)
                        with open(recovery, "a", encoding='utf-8') as rowfile:
                            rowfile.write(str(row)+"\n")
        hapax = 0
        classifrequenza = []
        occClassifrequenza = []
        totallines = len(table)
        paroletotali = 0
        for row in range(len(table)):
            if int(table[row][1]) == 1:
                hapax = hapax + 1
            if table[row][1] in classifrequenza:
                ind = classifrequenza.index(table[row][1])
                occClassifrequenza[ind] = occClassifrequenza[ind] + 1
            else:
                classifrequenza.append(table[row][1])
                occClassifrequenza.append(1)
            paroletotali = paroletotali + int(table[row][1])
        dimCorpus = dimList[0]
        for i in range(len(dimList)-1):
            if dimList[i] <= paroletotali and dimList[i+1] >= paroletotali:
                lower = paroletotali - dimList[i]
                upper = dimList[i+1] - paroletotali
                if lower < upper:
                    dimCorpus = dimList[i]
                else:
                    dimCorpus = dimList[i+1]
        for row in range(len(table)):
            thistext = table[row][0]
            ratio = (float(table[row][1])/float(paroletotali)*dimCorpus)
            ratios = f'{ratio:.3f}'
            table[row].append(str(ratios))
            ratio = math.log10(float(table[row][1])/float(paroletotali))
            ratios = f'{ratio:.3f}'
            table[row].append(str(ratios))
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
        table.insert(0,["Token", "Occorrenze", "Frequenza in " + str(dimCorpus) + " parole", "Ordine di grandezza (log10)"])
        savetable(table, output)


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
        output = fileName + "-colonna-" + str(col) + ".tsv"
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
                        thistext = line.replace("\n","").replace("\r","").split(separator)[col]
                    except:
                        thistext = ""
                    with open(output, "a", encoding='utf-8') as outfile:
                        outfile.write(thistext+"\n")
                    with open(recovery, "a", encoding='utf-8') as rowfile:
                        rowfile.write(str(row)+"\n")
                row = row + 1


def mergetables():
    separator = '\t'
    fileNames = []
    if os.path.isdir(sys.argv[2]):
        for tfile in os.listdir(sys.argv[2]):
            if bool(tfile[-4:] == ".tsv" or tfile[-4:] == ".tsv") and tfile[-11:] != "-merged.tsv" and tfile[-11:] != "-merged.csv":
                fileNames.append(os.path.join(sys.argv[2],tfile))
    else:
        return
    dirName = os.path.basename(os.path.dirname(sys.argv[2]))
    try:
        col = int(sys.argv[3])
    except:
        col = 0
    output = os.path.join(sys.argv[2],dirName + "-merged.tsv")
    with open(fileNames[0], "r", encoding='utf-8') as f:
        first_line = f.readline().replace("\n","").replace("\r","")
    try:
        opstr = str(sys.argv[4])
        opers = opstr.split(",")
    except:
        opers = ["sum"]
    try:
        startatrow = int(sys.argv[5])-1
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
        totallines = linescount(fileName)
        ch = "N"
        try:
            if os.path.isfile(recovery):
                try:
                    if sys.argv[6] == "y" or sys.argv[6] == "Y":
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
                    useheader = False
            else:
                if useheader:
                    table.append(first_line.split(separator))
                    useheader = False
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
                    tbrow = findintable(table, thistext, 0)
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
                    if row % 500 == 0:
                        savetable(table, output)
                        with open(recovery, "a", encoding='utf-8') as rowfile:
                            rowfile.write(str(row)+"\n")
                row = row + 1
    if "mean" in opers and firstfile > 0 and row == totallines and startatrow < totallines:
        for mrow in range(len(table)):
            for valind in range(len(opers)):
                if opers[valind] == "mean":
                    try:
                        table[mrow][valind+1] = float(table[mrow][valind+1])/len(fileNames)
                    except:
                        err = True
    savetable(table, output)
    print("Done")
    

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
                with open(output, "a", encoding='utf-8') as outfile:
                    outfile.write(thistext)
            row = row + 1


if __name__ == "__main__":
    corpuscols = {
                'IDcorpus': [0, "Tag corpus"],
                'Orig': [1, "Forma grafica"],
                'Lemma': [2, "Lemma"],
                'pos': [3, "Tag PoS"],
                'feat': [5, "Morfologia"],
                'ner': [4, "Tag NER"],
                'IDphrase': [7, "ID frase"],
                'IDword': [6, "ID parola"],
                'dep': [8, "Dep"],
                'governor': [9, "Governor"]
    }
    ignoretext = "((?<=[^0-9])"+ re.escape(".")+ "|^" + re.escape(".")+ "|(?<= )"+ re.escape("-")+ "|^"+re.escape("-")+ "|"+re.escape(":")+"|(?<=[^0-9])"+re.escape(",")+"|^"+re.escape(",")+"|"+re.escape(";")+"|"+re.escape("?")+"|"+re.escape("!")+"|"+re.escape("«")+"|"+re.escape("»")+"|"+re.escape("\"")+"|"+re.escape("(")+"|"+re.escape(")")+"|^"+re.escape("'")+ "|" + re.escape("[PUNCT]") + "|" + re.escape("<unknown>") + ")"
    dimList = [100,1000,5000,10000,50000,100000,150000,200000,250000,300000,350000,400000,450000,500000,1000000]
    try:
        filein = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/legenda/isdt.json"
        text_file = open(filein, "r")
        myjson = text_file.read().replace("\n", "").replace("\r", "").split("####")[0]
        text_file.close()
        legendaPos = json.loads(myjson)
    except:
        legendaPos = {"A":["aggettivo", "aggettivi", "piene"],"AP":["agg. poss", "aggettivi", "piene"],"B":["avverbio", "avverbi", "piene"],"B+PC":["avverbio+pron. clit. ", "avverbi", "piene"],"BN":["avv, negazione", "avverbi", "piene"],"CC":["cong. coord", "congiunzioni", "vuote"],"CS":["cong. sub.", "congiunzioni", "vuote"],"DD":["det. dim.", "aggettivi", "piene"],"DE":["det. esclam.", "aggettivi", "piene"],"DI":["det. indefinito", "aggettivi", "piene"],"DQ":["det. interr.", "aggettivi", "piene"],"DR":["det. Rel", "aggettivi", "piene"],"E":["preposizione", "preposizioni", "vuote"],"E+RD":["prep. art. ", "preposizioni", "vuote"],"FB":["punteggiatura - \"\" () «» - - ", "punteggiatura", "none"],"FC":["punteggiatura - : ;", "punteggiatura", "none"],"FF":["punteggiatura - ,", "punteggiatura", "none"],"FS":["punteggiatura - .?!", "punteggiatura", "none"],"I":["interiezione", "interiezioni", "vuote"],"N":["numero", "altro", "none"],"NO":["numerale", "aggettivi", "piene"],"PC":["pron. Clitico", "pronomi", "vuote"],"PC+PC":["pron. clitico+clitico", "pronomi", "vuote"],"PD":["pron. dimostrativo", "pronomi","vuote"],"PE":["pron. pers. ", "pronomi", "vuote"],"PI":["pron. indef.", "pronomi", "vuote"],"PP":["pron. poss.", "pronomi", "vuote"],"PQ":["pron. interr.", "pronomi", "vuote"],"PR":["pron. rel.", "pronomi", "vuote"],"RD":["art. Det.", "articoli", "vuote"],"RI":["art. ind.", "articoli", "vuote"],"S":["sost.", "sostantivi", "piene"],"SP":["nome proprio", "sostantivi", "piene"],"SW":["forestierismo", "altro", "none"],"T":["det. coll.)", "aggettivi", "piene"],"V":["verbo", "verbi", "piene"],"V+PC":["verbo + pron. clitico", "verbi", "piene"],"V+PC+PC":["verbo + pron. clitico + pron clitico", "verbi", "piene"],"VA":["verbo ausiliare", "verbi", "piene"],"VA+PC":["verbo ausiliare + pron.clitico", "verbi", "piene"],"VM":["verbo mod", "verbi", "piene"],"VM+PC":["verbo mod + pron. clitico", "verbi", "piene"],"X":["altro", "altro", "none"]}
    if len(sys.argv)>1:
        w = "cli"
        app = QApplication(sys.argv)
        if sys.argv[1] == "help" or sys.argv[1] == "aiuto":
            print("Le colonne di un corpus sono le seguenti:\n")
            print(corpuscols)
            print("\n")
            print("Elenco dei comandi:\n")
            print("python3 main.py tintstart [brancfg]\n")
            print("python3 main.py txt2corpus file.txt|cartella [indirizzoServerTint] [y]\n")
            print("python3 main.py splitbigfile file.txt [maxnumberoflines] [.]\n")
            print("python3 main.py samplebigfile file.txt [maxnumberoflines] [.]\n")
            print("python3 main.py occorrenze file.tsv|cartella [colonna] [y]\n")
            print("python3 main.py extractcolumn file.tsv|cartella colonna\n")
            print("python3 main.py contaverbi file.tsv|cartella\n")
            print("python3 main.py misurelessico file.tsv|cartella [colonna] [y]\n")
            print("python3 main.py mergetables cartella colonnaChiave [sum|mean|diff,sum|mean|diff] [1] [y]\n")
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
            te = texteditor.TextEditor()
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
            te.exec()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "confronto":
            cf = confronto.Confronto(os.path.abspath(os.path.dirname(sys.argv[0])))
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
            cf.exec()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "occorrenze":
            calcola_occorrenze()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "contaverbi":
            contaverbi(corpuscols, legendaPos)
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "extractcolumn":
            estrai_colonna()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "splitbigfile":
            splitbigfile()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "samplebigfile":
            samplebigfile()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "mergetables":
            mergetables()
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        if sys.argv[1] == "misurelessico":
            misure_lessicometriche(ignoretext, dimList)
            print("ELABORAZIONE TERMINATA: se il prompt rimane in stallo, premi Ctrl+C.")
        sys.exit(0)
    else:
        app = QApplication(sys.argv)
        w = branwindow.MainWindow(corpuscols, legendaPos, ignoretext, dimList)
        w.show()
        sys.exit(app.exec_())



