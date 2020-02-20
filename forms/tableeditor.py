#!/usr/bin/env python
# -*- coding: utf-8 -*-


from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QInputDialog
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QPushButton
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QTableWidget
from PySide2.QtWidgets import QTableWidgetItem

import re
import sys
import os
import math
import mmap
import subprocess

from forms import progress
from forms import texteditor


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/tableeditor.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.w.apricsv.clicked.connect(self.apriCSV)
        self.w.salvacsv.clicked.connect(self.salvaCSV)
        self.w.creagrafico.clicked.connect(self.creagrafico)
        self.w.tableWidget.itemSelectionChanged.connect(self.selOps)
        self.w.dofiltra.clicked.connect(self.dofiltra)
        self.w.cancelfiltro.clicked.connect(self.cancelfiltro)
        self.w.filterGroup.clicked.connect(self.filtersh)
        self.w.tableWidget.horizontalHeader().sectionDoubleClicked.connect(self.sortbycolumn)
        self.w.apricsv.hide()
        self.setWindowTitle("Visualizzazione tabella")
        self.sessionDir = "."
        self.separator = "\t"
        self.w.filterWidget.hide()
        self.Rpath = "/usr/bin/Rscript"

    def isaccepted(self):
        self.accept()
    def isrejected(self):
        self.reject()

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
                        for col in onlycols:
                            if col > 0:
                                csv = csv + self.separator
                            try:
                                csv = csv + self.w.tableWidget.item(row,col).text()
                            except:
                                csv = csv + ""
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

    def apriCSV(self):
        fileNames = QFileDialog.getOpenFileNames(self.w.tableWidget, "Apri file CSV", self.sessionDir, "CSV files (*.tsv *.csv)")[0]
        self.Progrdialog = progress.Form(self.w.tableWidget)
        self.Progrdialog.show()
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
                        while len(newtoken) > self.w.tableWidget.columnCount():
                            ci = self.w.tableWidget.columnCount()
                            #self.addcolumn("Colonna"+str(ci), ci)
                            self.addcolumn(newtoken[ci], ci)
                        if firstrow:
                            firstrow = False
                            continue
                        row = self.addlinetotable(newtoken[0],0)
                        for c in range(1,len(newtoken)):
                            self.setcelltotable(newtoken[c],row, c)
        self.Progrdialog.accept()

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
            ctext = self.w.tableWidget.item(row,col).text()
            ftext = self.w.cfilter.text()
            try:
                if self.w.filtronumerico.isChecked():
                    filterit = False
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
                    if filterit:
                        self.w.tableWidget.setRowHidden(row, False)
                        tcount = tcount +1
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
        if self.w.filterWidget.isVisible() == True:
            self.w.filterWidget.hide()
        else:
            self.w.filterWidget.show()

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

        templates = {"Istogramma": scriptdir + "/R/istogramma.R", "Torta": scriptdir + "/R/torta.R"}

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

        values = QInputDialog.getItem(self.w.tableWidget, "Scegli la colonna", "Quale colonna della tabella contiene i valori numerici del grafico?",thisname,current=(len(thisname)-1),editable=False)[0]
        onlycols.append(thisname.index(values))
        customheader.append(re.sub(notallowed, "", values))

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
        plot = plot.replace("BranColonna1", str(customheader[1]))

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


class QTableNumberItem(QTableWidgetItem):
    def __lt__(self, other):
        try:
            myvalue = float(self.text())
            othervalue = float(other.text())
            return myvalue < othervalue
        except:
            return False
