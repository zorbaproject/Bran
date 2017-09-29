#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import os.path
import sys

localdir = os.path.abspath(os.path.dirname(sys.argv[0]))

oldfile = localdir + "/../vdb1980.txt"
newfile = localdir + "/../vdb2016.txt"

try:
    wordscount = len(sys.argv[1].split(","))
except:
    print("Esempio: python3 diagramma-di-venn.py banana,zappare,abbagliante,computer diagrammavenn.R")
    sys.exit()

try:
    Rfile = sys.argv[2]
except:
    Rfile = "diagrammavenn.R"

wordslist = [[ "", False, False ] for r in range(wordscount)]
for i in range(wordscount):
    wordslist[i][0] = sys.argv[1].split(",")[i]


#leggo i due file dei vocabolari di base
oldvdb = ""
if os.path.isfile(oldfile):
    text_file = open(oldfile, "r")
    oldvdb = text_file.read().split("\n")
    text_file.close()

newvdb = ""
if os.path.isfile(newfile):
    text_file = open(newfile, "r")
    newvdb = text_file.read().split("\n")
    text_file.close()

#controllo se ciascuna delle parole esiste nel vecchio dizionario
#TODO: sarebbe meglio usare le regex per il match
for lemma in oldvdb:
    for i in range(wordscount):
        if wordslist[i][0] == lemma:
             wordslist[i][1] = True

for lemma in newvdb:
    for i in range(wordscount):
        if wordslist[i][0] == lemma:
             wordslist[i][2] = True

# preparo i dati in formato tabulare
set1980 = ""
set2016 = ""
mycsv = "Parola,1980,2016"
for i in range(wordscount):
    mycsv = mycsv + "\n" + wordslist[i][0]
    if wordslist[i][1] == True:
        mycsv = mycsv + ",1"
        set1980 = set1980 + " \"" + wordslist[i][0] + "\"," 
    else:
        mycsv = mycsv + ",0"
    if wordslist[i][2] == True:
        mycsv = mycsv + ",1"
        set2016 = set2016 + " \"" + wordslist[i][0] + "\","
    else:
        mycsv = mycsv + ",0"

print("Ecco la tabella CSV che puoi usare come riepilogo:\n")
print(mycsv)


myRcode = ""
myRcode = myRcode + '#!/usr/bin/Rscript\n'
myRcode = myRcode + 'install.packages("VennDiagram",repos = "https://cran.stat.unipd.it/");\n'
myRcode = myRcode + 'require(VennDiagram);\n'
#myRcode = myRcode + 'X11()\n'
myRcode = myRcode + 'x <- list();\n'
myRcode = myRcode + 'x$VdB1980 <- as.character(c(' + set1980[:-1] + '));\n'
myRcode = myRcode + 'x$VdB2016 <- as.character(c(' + set2016[:-1] + '));\n'
myRcode = myRcode + 'v0 <-venn.diagram(x, lwd = 3, col = c("red", "green"), fill = c("orange", "yellow"), apha = 0.5, filename = NULL, imagetype = "svg");\n'
myRcode = myRcode + 'grid.draw(v0);\n'
myRcode = myRcode + 'overlaps <- calculate.overlap(x);\n'
myRcode = myRcode + 'base <- (length(x)*2);\n'
myRcode = myRcode + 'vl <- 9; #length(v0)\n'
myRcode = myRcode + 'for (i in 1:length(overlaps)){\n'
myRcode = myRcode + 'if (i<base-1) {\n'
myRcode = myRcode + 'v0[[vl-base+i-1]]$label <- paste(setdiff(overlaps[[base-1-i]], overlaps[[base-1]]), collapse = "\\n");\n'
myRcode = myRcode + '} else {\n'
myRcode = myRcode + 'v0[[vl-base+i-1]]$label <- paste(overlaps[[base-1]], collapse = "\\n");\n'
myRcode = myRcode + '}\n'
myRcode = myRcode + '}\n'
#myRcode = myRcode + 'tiff(filename = "diagrammavenn.tiff", compression = "lzw");\n'
myRcode = myRcode + 'svg(filename = "diagrammavenn.svg");\n'
myRcode = myRcode + 'grid.newpage();\n'
myRcode = myRcode + 'grid.draw(v0);\n'

text_file = open(Rfile, "w")
text_file.write(myRcode)
text_file.close()

print("Il codice R con cui realizzare un diagramma di Venn è salvato nel file: " + Rfile)

myRcode = ""
myRcode = myRcode + 'install.packages("RAM")\n'
myRcode = myRcode + 'library(RAM) # https://rdrr.io/cran/RAM/man/group.venn.html\n'
myRcode = myRcode + 'VdB1980 <- as.character(c(' + set1980[:-1] + '))\n'
myRcode = myRcode + 'VdB2016 <- as.character(c(' + set2016[:-1] + '))\n'
myRcode = myRcode + 'group.venn(list(VdB1980=VdB1980, VdB2016=VdB2016), label=TRUE, fill = c("red", "green"), cat.pos = c(330, 30), lab.cex=1.1)\n'

print("\nSi può anche usare questo codice R, meno personalizzabile di quello scritto nel file:\n")
print(myRcode)

#NOTE: Io preferisco avere un file a parte, ma volendo si può integrare R in python e disegnare il grafico all'interno di questo script
#https://rpy2.github.io/doc/latest/html/introduction.html#getting-started
