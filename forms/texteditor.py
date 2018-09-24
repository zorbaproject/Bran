#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
import sys
import os
import csv
#import re

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QDialog

class TextEditor(QDialog):

    def __init__(self, parent=None):
        super(TextEditor, self).__init__(parent)
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/texteditor.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        #self.w.replace_in_corpus.clicked.connect(self.replaceCorpus)
        self.w.actionConta_occorrenze.triggered.connect(self.contaoccorrenze)
        self.w.actionRimuovi_frasi_ripetute.triggered.connect(self.rm_doublephrases)

    def rm_doublephrases(self):
        #dele phrases repeated: https://pastebin.com/7Krbii0d
        wnumber = 10
        searchthis = " " #this is the separator: if " " you look for words, if "." you look for phrases
        filein = ""
        fileout = ""
        text = ""

        #if len(sys.argv) > 1:
        #    filein = sys.argv[1]
        #if filein == "-h":
        #    print("Usage:\n delete-phrases-repetition.py \"fileinput.txt\" 10 \"fileoutput.txt\" \" \"\n delete-phrases-repetition.py \"fileinput.txt\" 1 \"fileoutput.txt\" \".\"\nNOTE: The number represents occurrences of the separator to get a phrase. If you use \".\" as separator, the number should be 1.")
        #    sys.exit()

        #if len(sys.argv) > 2:
        #   wnumber = int(sys.argv[2])

        #if len(sys.argv) > 3:
        #    fileout = sys.argv[3]

        #if len(sys.argv) > 4:
        #    searchthis = sys.argv[4]

        if filein != "" and os.path.isfile(filein):
            text_file = open(filein , "r")
            #text = text_file.read().replace("\n", "")
            text = text_file.read()
            text_file.close()
        else:
            return

        if wnumber < 0:
            wnumber = 10


        active = 1
        pos = 0
        while active:
            wpos = pos
            npos = pos
            #read a specific number of words
            for i in range(wnumber):
                wpos = text.find(searchthis, npos+1)
                if wpos > 0:
                    npos = wpos
            #check if we reached someway the end of text
            if npos > len(text)-1:
                if pos > len(text)-1:
                    break
                else:
                    npos = len(text)-1
            #read this phrase
            tmpstring = text[pos:npos]
            #replace all occurrences of the phrase, after the first one, with nothing
            if tmpstring != "":
                newtext = nth_replace(text, tmpstring, "", 2, "all right")
                text = newtext
            pos = text.find(searchthis, pos+1)+1 #continue from next word
            if pos <= 0:
                pos = len(text)

        #delete double spaces
        newtext = newtext.replace("  ", " ")

        if fileout:
            text_file = open(fileout, "w")
            text_file.write(newtext)
            text_file.close()
        else:
            self.w.plainTextEdit.document().setPlainText(newtext)

    def findIndexinCol(arr, string, col):
        for i in range(len(arr)):
            if (arr[i][col]) == string:
                return i
        return -1

    def contaoccorrenze(self):
        #conta occorrenze: https://pastebin.com/0tPNVACe
        mycol = 1
        csvfile = ""
        mydelimiter = '\t'
        res = occ_count(csvfile, "", mycol, mydelimiter)

    def occ_count(self, csvfile = "", outputfile = "", mycol = 1, mydelimiter = '\t'):
        mycsv = []
        #mycol = 1
        #csvfile = ""
        #mydelimiter = '\t'
        words = []
        #outputfile = ""

        #if len(sys.argv) < 2:
        #        print("python3 conta-occorrenze.py FILEINPUT FILEOUTPUT COLONNA DELIMITATORE\n ES:\n \"C:\\Programs\\Python 3.6\\Python 3.6 (32-bit).lnk\" \"C:\\conta-occorrenze.py\" \"C:\\ETR Tagged.txt\" \"C:\\occorrenze.csv\" 1 '\\t'")
        #if len(sys.argv) > 1:
        #        csvfile = sys.argv[1]
        #if len(sys.argv) > 2:
        #        outputfile = sys.argv[2]
        #if len(sys.argv) > 3:
        #        mycol = int(sys.argv[3])
        #if len(sys.argv) > 4:
        #        mydelimiter = sys.argv[4]

        if (len(mydelimiter) != 1):
                mydelimiter = '\t'

        if csvfile == "":
                return

        csvfile = os.path.abspath(csvfile)
        origdict = list(csv.reader(open(csvfile), delimiter=mydelimiter)) #this is [row][column]
        for i in range(len(origdict)):
                if (len(origdict[i]) > mycol):
                        mycsv.append(origdict[i][mycol])

        for word in mycsv:
                value_index = findIndexinCol(words,word,0)
                if value_index > -1:
                        thiscount = words[value_index][1]
                        words[value_index][1] = thiscount + 1
                else:
                        value_index = len(words)
                        words.append([word,1])

        csvoutput = ""
        for i in range(len(words)):
                csvoutput += words[i][0] + ";" + str(words[i][1]) + "\n"

        #if (outputfile != ""):
        #        text_file = open(outputfile, "w")
        #        text_file.write(csvoutput)
        #        text_file.close()
        return csvoutput

    def nth_replace(string, old, new, n=1, option='only nth'):
        """
       This function replaces occurrences of string 'old' with string 'new'.
       There are three types of replacement of string 'old':
       1) 'only nth' replaces only nth occurrence (default).
       2) 'all left' replaces nth occurrence and all occurrences to the left.
       3) 'all right' replaces nth occurrence and all occurrences to the right.
       """
        if option == 'only nth':
            left_join = old
            right_join = old
        elif option == 'all left':
            left_join = new
            right_join = old
        elif option == 'all right':
            left_join = old
            right_join = new
        else:
            print("Invalid option. Please choose from: 'only nth' (default), 'all left' or 'all right'")
            return None
        groups = string.split(old)
        nth_split = [left_join.join(groups[:n]), right_join.join(groups[n:])]
        return new.join(nth_split)


