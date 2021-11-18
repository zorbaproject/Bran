#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QPushButton
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem
from PySide2.QtSvg import QSvgWidget

import re
import sys
import os
import math
import mmap
import subprocess

from forms import progress
from forms import texteditor


class Form(QMainWindow):
    def __init__(self, parent=None, mycfg=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/tableeditor.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        #layout = QVBoxLayout()
        #layout.addWidget(self.w)
        #self.setLayout(layout)
        self.setCentralWidget(self.w)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.apricsv.clicked.connect(self.apriCSV)
        self.w.salvacsv.clicked.connect(self.salvaCSV)
        self.w.creagrafico.clicked.connect(self.creagrafico)
        self.w.tableWidget.itemSelectionChanged.connect(self.selOps)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.readregexfile.clicked.connect(self.readregexfile)
        self.w.showFilter.clicked.connect(self.filtersh)
        self.w.ribaltatabella.clicked.connect(self.ribaltatabella)
        self.w.changeHeader.clicked.connect(self.changeHeader)
        self.w.addCol.clicked.connect(self.addCol)
        self.w.addRow.clicked.connect(self.addRow)
        self.w.rmCol.clicked.connect(self.rmCol)
        self.w.rmRow.clicked.connect(self.rmRow)
        self.w.tableWidget.horizontalHeader().sectionDoubleClicked.connect(self.sortbycolumn)
        self.w.apricsv.hide()
        self.setWindowTitle("Visualizzazione tabella")
        self.sessionDir = "."
        self.separator = "\t"
        self.mycfg = mycfg
        self.w.filterWidget.hide()
        self.accepted = False
        self.Rpath = self.mycfg["rscript"] #"/usr/bin/Rscript"
        self.regexlist = []
        self.tabella = []

    def isaccepted(self):
        #self.accept()
        self.accepted = True
        self.close()
    def isrejected(self):
        #self.reject()
        self.close()

    def addcolumn(self, text, column):
        cols = self.w.tableWidget.columnCount()
        self.w.tableWidget.setColumnCount(cols+1)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setHorizontalHeaderItem(cols, titem)
        self.enumeratecolumns(self.w.ccolumn)

    def addlinetotable(self, text, column):
        row = self.w.tableWidget.rowCount()
        self.w.tableWidget.insertRow(row)
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setItem(row, column, titem)
        self.w.tableWidget.setCurrentCell(row, column)
        return row

    def setcelltotable(self, text, row, column):
        titem = QTableWidgetItem()
        titem.setText(text)
        self.w.tableWidget.setItem(row, column, titem)

    def addCol(self):
        colheader = QInputDialog.getText(self.w, "Indica l'intestazione", "Scrivi l'intestazione della nuova colonna:", QLineEdit.Normal, "")[0]
        self.addColH(colheader)

    def addColH(self, colheader = ""):
        alreadydone = []
        cols = []
        for i in range(len(self.w.tableWidget.selectedItems())-1,-1,-1):
            col = self.w.tableWidget.selectedItems()[i].column()
            cols.append(col)
        cols.reverse()
        for col in range(len(cols)-1,-1,-1):
            c = cols[col]
            if c in alreadydone:
                continue
            alreadydone.append(c)
            val = colheader
            for r in range(len(self.tabella)):
                tmplist = self.tabella[r][:c+1]
                tmplist.append(val)
                tmplist.extend(self.tabella[r][c+1:])
                self.tabella[r] = tmplist
                val = "" #default
        self.mostraTabella()

    def addRow(self):
        alreadydone = []
        for i in range(len(self.w.tableWidget.selectedItems())-1,-1,-1):
            row = self.w.tableWidget.selectedItems()[i].row()+1
            if row in alreadydone:
                continue
            alreadydone.append(row)
            tmprow = []
            for c in range(self.w.tableWidget.columnCount()):
                tmprow.append("")
            if len(self.tabella)>row+1:
                tmptable = self.tabella[:row+1]
                tmptable.append(tmprow)
                tmptable.extend(self.tabella[row+1:])
                self.tabella = tmptable
            else:
                self.tabella.append(tmprow)
        self.mostraTabella()

    def rmCol(self):
        alreadydone = []
        cols = []
        for i in range(len(self.w.tableWidget.selectedItems())-1,-1,-1):
            col = self.w.tableWidget.selectedItems()[i].column()
            cols.append(col)
        cols.reverse()
        for col in range(len(cols)-1,-1,-1):
            c = cols[col]
            if c in alreadydone:
                continue
            alreadydone.append(c)
            for r in range(len(self.tabella)):
                tmplist = self.tabella[r][:c]
                tmplist.extend(self.tabella[r][c+1:])
                self.tabella[r] = tmplist
        self.mostraTabella()

    def rmRow(self):
        alreadydone = []
        for i in range(len(self.w.tableWidget.selectedItems())-1,-1,-1):
            row = self.w.tableWidget.selectedItems()[i].row()+1
            if row in alreadydone:
                continue
            alreadydone.append(row)
            if len(self.tabella)>row+1:
                tmptable = self.tabella[:row]
                tmptable.extend(self.tabella[row+1:])
                self.tabella = tmptable
            else:
                self.tabella = self.tabella[:row]
        self.mostraTabella()

    def changeHeader(self):
        try:
            col = self.w.tableWidget.selectedItems()[-1].column()
            colheader = self.tabella[0][col]
        except:
            colheader = ""
        colheader = QInputDialog.getText(self.w, "Indica l'intestazione", "Scrivi l'intestazione della colonna selezionata:", QLineEdit.Normal, colheader)[0]
        self.changeHeaderH(colheader)

    def changeHeaderH(self, colheader):
        alreadydone = []
        cols = []
        for i in range(len(self.w.tableWidget.selectedItems())-1,-1,-1):
            col = self.w.tableWidget.selectedItems()[i].column()
            cols.append(col)
        cols.reverse()
        for col in range(len(cols)-1,-1,-1):
            c = cols[col]
            if c in alreadydone:
                continue
            alreadydone.append(c)
            self.tabella[0][c] = colheader
        self.mostraTabella()

    def salvaCSV(self):
        checkfilter = False
        for row in range(self.w.tableWidget.rowCount()):
            if self.w.tableWidget.isRowHidden(row):
                msgBox = QMessageBox(self)
                msgBox.setWindowTitle("Domanda")
                msgBox.setText("Cosa vuoi salvare?")
                msgBox.addButton(QPushButton("Solo le righe filtrate", self.w), QMessageBox.YesRole)
                msgBox.addButton(QPushButton('Salva tutte le righe', self.w), QMessageBox.NoRole)
                msgBox.exec_()
                if msgBox.clickedButton().text() == "Solo le righe filtrate":
                    checkfilter = True
                break
        fileName = QFileDialog.getSaveFileName(self, "Salva file CSV", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.CSVsaver(fileName, checkfilter)

    def CSVsaver(self, fileName, checkfilter = False, customheader = [], onlycols = []):
        if fileName != "":
            if fileName[-4:] != ".csv" and fileName[-4:] != ".tsv":
                fileName = fileName + ".tsv"
            csv = ""
            if len(customheader) > 0:
                for col in range(len(customheader)):
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + customheader[col]
            else:
                for col in range(self.w.tableWidget.columnCount()):
                    if col > 0:
                        csv = csv + self.separator
                    csv = csv + self.w.tableWidget.horizontalHeaderItem(col).text()
            for row in range(self.w.tableWidget.rowCount()):
                if self.w.tableWidget.isRowHidden(row) == False or checkfilter == False:
                    csv = csv + "\n"
                    if len(onlycols) > 0:
                        actCol= 0
                        for col in onlycols:
                            if actCol > 0:
                                csv = csv + self.separator
                            try:
                                csv = csv + self.w.tableWidget.item(row,col).text()
                            except:
                                csv = csv + ""
                            actCol = actCol + 1
                    else:
                        for col in range(self.w.tableWidget.columnCount()):
                            if col > 0:
                                csv = csv + self.separator
                            try:
                                csv = csv + self.w.tableWidget.item(row,col).text()
                            except:
                                csv = csv + ""
            text_file = open(fileName, "w", encoding='utf-8')
            text_file.write(csv)
            text_file.close()

    def readregexfile(self):
        fileNames = QFileDialog.getOpenFileNames(self.w.tableWidget, "Apri lista di regex", self.sessionDir, "Text files (*.tsv *.csv *.txt)")[0]
        self.setregexfile(fileNames)

    def setregexfile(self, fileNames):
        self.regexlist = []
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    linesA = lines.split('\n')
                    for myregex in linesA:
                        if myregex != "":
                            self.regexlist.append(myregex)
        retext = "LIST:"+str(self.regexlist)
        self.w.cfilter.setText(retext)

    def apriCSV(self):
        fileNames = QFileDialog.getOpenFileNames(self.w.tableWidget, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv)")[0]
        self.opentables(fileNames)
        self.mostraTabella()

    def opentables(self, fileNames):
        if len(fileNames) == 0:
            return
        self.Progrdialog = progress.Form(self.w.tableWidget)
        self.Progrdialog.show()
        self.tabella = []
        self.tabella.append([]) #table header
        for fileName in fileNames:
            if not fileName == "":
                if os.path.isfile(fileName):
                    print(fileName)
                    if not os.path.getsize(fileName) > 0:
                        continue
                    try:
                        totallines = self.linescount(fileName)
                    except Exception as ex:
                        print(ex)
                        continue
                    text_file = open(fileName, "r", encoding='utf-8')
                    lines = text_file.read()
                    text_file.close()
                    linesA = lines.split('\n')
                    row = 0
                    firstrow = True
                    for line in linesA:
                        if line == "":
                            continue
                        if row<100 or row%100==0:
                            self.Progrdialog.w.testo.setText("Sto selezionando la riga numero "+str(row))
                            self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                            QApplication.processEvents()
                        if self.Progrdialog.w.annulla.isChecked():
                            return
                        newtoken = line.split(self.separator)
                        while len(newtoken) > len(self.tabella[0]):
                            ci = len(self.tabella[0])
                            #self.addcolumn("Colonna"+str(ci), ci)
                            tmph = self.tabella[0]
                            tmph.append(newtoken[ci])
                            self.tabella[0] = tmph
                        if firstrow:
                            firstrow = False
                            continue
                        #row = self.addlinetotable(newtoken[0],0)
                        newrow = []
                        for c in range(0,len(newtoken)):
                            newrow.append(newtoken[c])
                        self.tabella.append(newrow)
        self.Progrdialog.accept()

    def mostraTabella(self):
        self.Progrdialog = progress.Form(self.w.tableWidget)
        self.Progrdialog.show()
        row = 0
        firstrow = True
        totallines = len(self.tabella)
        self.w.tableWidget.setRowCount(0)
        self.w.tableWidget.setColumnCount(0)
        for line in self.tabella:
            if len(line)==0:
                continue
            if row<100 or row%100==0:
                self.Progrdialog.w.testo.setText("Sto caricando la riga numero "+str(row))
                self.Progrdialog.w.progressBar.setValue(int((row/totallines)*100))
                QApplication.processEvents()
            if self.Progrdialog.w.annulla.isChecked():
                return
            newtoken = line
            while len(newtoken) > self.w.tableWidget.columnCount():
                ci = self.w.tableWidget.columnCount()
                self.addcolumn(newtoken[ci], ci)
            if firstrow:
                firstrow = False
                continue
            row = self.addlinetotable(newtoken[0],0)
            for c in range(1,len(newtoken)):
                self.setcelltotable(newtoken[c],row, c)
        self.Progrdialog.accept()

    def ribaltatabella(self):
        #print(self.tabella)
        r = list(map(list, zip(*self.tabella)))
        self.tabella = r
        #print(self.tabella)
        self.mostraTabella()
        return

    def linescount(self, filename):
        f = open(filename, "r+", encoding='utf-8')
        buf = mmap.mmap(f.fileno(), 0)
        lines = 0
        readline = buf.readline
        while readline():
            lines += 1
        return lines

    def finditemincolumn(self, mytext, col=0, matchexactly = True, escape = True, myflags=0):
        myregex = mytext
        if escape:
            myregex = re.escape(myregex)
        if matchexactly:
            myregex = "^" + myregex + "$"
        for row in range(self.w.tableWidget.rowCount()):
            try:
                if bool(re.match(myregex, self.w.tableWidget.item(row,col).text(), flags=myflags)):
                    return row
            except:
                continue
        return -1


    def selOps(self):
        somma = 0.0
        try:
            for i in range(len(self.w.tableWidget.selectedItems())):
                row = self.w.tableWidget.selectedItems()[i].row()
                col = self.w.tableWidget.selectedItems()[i].column()
                somma = somma + float(self.w.tableWidget.item(row,col).text())
            sommas = f'{somma:.3f}'
            self.w.statusbar.setText("Somma: " +str(sommas))
        except:
            if (self.w.statusbar.text() != ""):
                self.w.statusbar.setText("")


    def enumeratecolumns(self, combo):
        combo.clear()
        for col in range(self.w.tableWidget.columnCount()):
            thisname = self.w.tableWidget.horizontalHeaderItem(col).text()
            combo.addItem(thisname)

    def dofiltra(self):
        tcount = 0
        for row in range(self.w.tableWidget.rowCount()):
            col = self.w.ccolumn.currentIndex()
            try:
                ctext = self.w.tableWidget.item(row,col).text()
            except:
                ctext = ""
            ftext = self.w.cfilter.text()
            try:
                if self.w.filtronumerico.isChecked():
                    filterit = False
                    try:
                        if ctext == "":
                            ctext = "0"
                        if ftext.startswith(">"):
                            filterit = bool(float(ctext) > float(eval(ftext[ftext.find(">")+1:])))
                        elif ftext.startswith("<"):
                            filterit = bool(float(ctext) < float(eval(ftext[ftext.find("<")+1:])))
                        elif ftext.startswith("="):
                            filterit = bool(float(ctext) == float(eval(ftext[ftext.find("=")+1:])))
                        elif ftext.startswith(">="):
                            filterit = bool(float(ctext) >= float(eval(ftext[ftext.find(">=")+2:])))
                        elif ftext.startswith("<="):
                            filterit = bool(float(ctext) <= float(eval(ftext[ftext.find("<=")+2:])))
                        elif ftext.startswith("=="):
                            filterit = bool(float(ctext) == float(eval(ftext[ftext.find("==")+2:])))
                        elif ftext.startswith("!="):
                            filterit = bool(float(ctext) != float(eval(ftext[ftext.find("!=")+2:])))
                        elif ftext.startswith("~"):
                            filterit = math.isclose(float(ctext), float(eval(ftext[ftext.find("~")+1:])), rel_tol=0.1)
                    except:
                        print("Not a Number")
                    if filterit:
                        self.w.tableWidget.setRowHidden(row, False)
                        tcount = tcount +1
                    else:
                        self.w.tableWidget.setRowHidden(row, True)
                else:
                    if ftext.startswith('LIST:[') and len(self.regexlist)>0:
                        for retext in self.regexlist:
                            if bool(re.match("^"+retext+"$", ctext)):
                                self.w.tableWidget.setRowHidden(row, False)
                                tcount = tcount +1
                                break
                            else:
                                self.w.tableWidget.setRowHidden(row, True)
                    else:
                        if bool(re.match(ftext, ctext)):
                            self.w.tableWidget.setRowHidden(row, False)
                            tcount = tcount +1
                        else:
                            self.w.tableWidget.setRowHidden(row, True)
            except:
                print("Error filtering row " + str(row) + " in TableEditor")
                continue
        self.w.statusbar.setText("Risultati totali: " +str(tcount))

    def cancelfiltro(self):
        for row in range(self.w.tableWidget.rowCount()):
            self.w.tableWidget.setRowHidden(row, False)

    def filtersh(self):
        if self.w.showFilter.isChecked():
            self.w.filterWidget.show()
        else:
            self.w.filterWidget.hide()

    def sortbycolumn(self, col):
        self.w.tableWidget.setSortingEnabled(False)
        for row in range(self.w.tableWidget.rowCount()):
            try:
                tbval = float(self.w.tableWidget.item(row,col).text()) #Se la cella contiene testo, questa riga provoca except
                titem = QTableNumberItem()
                titem.setText(self.w.tableWidget.item(row,col).text())
                self.w.tableWidget.setItem(row, col, titem)
            except:
                continue
        self.w.tableWidget.setSortingEnabled(True)
        self.w.tableWidget.sortItems(col)

    def creagrafico(self):
        print("R path: " + self.Rpath)
        scriptdir = os.path.abspath(os.path.dirname(sys.argv[0]))

        templates = {"Istogramma semplice": scriptdir + "/R/istogramma.R", "Istogramma a somma": scriptdir + "/R/istogramma-count.R", "Torta": scriptdir + "/R/torta.R", "Istogrammi a gruppi": scriptdir + "/R/istogramma-gruppi.R"}

        thisname = []
        for key in templates:
            thisname.append(key)
        type = QInputDialog.getItem(self.w.tableWidget, "Scegli il tipo di grafico", "Quale grafico vuoi realizzare?",thisname,current=0,editable=False)[0]

        onlycols = []
        customheader = []

        thisname = []
        for col in range(self.w.tableWidget.columnCount()):
            thisname.append(self.w.tableWidget.horizontalHeaderItem(col).text())
        labels = QInputDialog.getItem(self.w.tableWidget, "Scegli la colonna", "Quale colonna della tabella contiene le etichette (testo) del grafico?",thisname,current=0,editable=False)[0]
        onlycols.append(thisname.index(labels))
        notallowed = "[^0-9a-zA-Z]"
        customheader.append(re.sub(notallowed, "", labels))

        if type != "Istogramma a somma":
            values = QInputDialog.getItem(self.w.tableWidget, "Scegli la colonna", "Quale colonna della tabella contiene i valori numerici del grafico?",thisname,current=(len(thisname)-1),editable=False)[0]
            onlycols.append(thisname.index(values))
            customheader.append(re.sub(notallowed, "", values))
        else:
            values = ""

        if type == "Istogrammi a gruppi":
            groups = QInputDialog.getItem(self.w.tableWidget, "Scegli la colonna", "Quale colonna della tabella contiene i valori per cui raggruppare i dati dei grafici?",thisname,current=0,editable=False)[0]
            onlycols.append(thisname.index(groups))
            customheader.append(re.sub(notallowed, "", groups))

        path = QFileDialog.getExistingDirectory(self, "Seleziona la cartella in cui salvare i file del grafico")
        if path == "" or not os.path.isdir(path):
            return
        path = path.replace("\\", "/")

        text_file = open(templates[type], "r", encoding='utf-8')
        lines = text_file.read()
        text_file.close()

        mybasename = type + "_" + labels + "-"+ values
        mybasename = mybasename.replace(" ", "_")

        print(path + "/" +  mybasename + ".csv")

        self.CSVsaver(path + "/" +  mybasename + ".csv", True, customheader, onlycols)

        plot = lines.replace("fullpath <- \"mytable.csv\";", "fullpath <- \"" + mybasename + ".csv\";")
        plot = plot.replace("BranColonna0", str(customheader[0]))
        if len(customheader)> 1:
            plot = plot.replace("BranColonna1", str(customheader[1]))
        if len(customheader)> 2:
            plot = plot.replace("BranColonna2", str(customheader[2]))

        text_file = open(path + "/" +  mybasename + ".R", "w", encoding='utf-8')
        text_file.write(plot)
        text_file.close()

        #https://docs.python.org/3/library/subprocess.html#using-the-subprocess-module
        ret = QMessageBox.question(self.w.tableWidget,'Domanda', "Vuoi avviare automaticamente R per disegnare il grafico?", QMessageBox.Yes | QMessageBox.No)
        if ret == QMessageBox.Yes:
            process = subprocess.Popen([self.Rpath, mybasename + ".R"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
            outputbyte = process.communicate()[0]
            process.stdin.close()
            stroutput = outputbyte.decode(encoding='utf-8')
            print(stroutput)
            svg = path + "/" +  mybasename + ".svg"
            mydialog = QDialog(self)
            svgwidget = QSvgWidget(mydialog)
            layout = QVBoxLayout()
            layout.addWidget(svgwidget)
            # Set dialog layout
            svgwidget.load(svg)
            mydialog.setLayout(layout)
            mydialog.setWindowTitle("Anteprima del grafico")
            mydialog.show()


class QTableNumberItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            myvalue = float(self.text())
            othervalue = float(other.text())
            return myvalue < othervalue
        except:
            return False
