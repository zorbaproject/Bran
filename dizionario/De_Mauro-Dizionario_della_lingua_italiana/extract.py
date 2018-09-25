#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re

def codepointtostring(thisword):
    # chr(int('0x0113', 16))
    # &#$0113;
    indexes = [(m.start(0), m.end(0)) for m in re.finditer('&#.*?;', thisword)]
    couples = []
    for n in range(len(indexes)):
        start = indexes[n][0]
        end = indexes[n][1]
        try:
            unicodechar = chr(int('0x'+thisword[start+3:end-1], 16))
            couples.append([thisword[start:end], unicodechar])
        except:
            print(thisword[start:end])
    for n in range(len(couples)):
        thisword = thisword.replace(couples[n][0], couples[n][1])
    return thisword


fileName = "didm0010_le.ddata.txt"
text_file = open(fileName, "r", encoding='utf-8')
lines = text_file.read()
text_file.close()

regex = "<[i]>(.*?)<\/[i]>"
#regex = ".*?href=[\"'](.*?)[\"']"
words = [m.group(1) for m in re.finditer(regex, lines, flags=re.DOTALL)]
cleanlist = [x for x in words if not '<sup>' in x]
#rimuovo i duplicati
sortedlist = list(set(cleanlist))
sortedlist.sort()

fileName = "dizionario-de-mauro.txt"
text_file = open(fileName, "w", encoding='utf-8')
text_file.write("")
text_file.close()

for myword in sortedlist:
    thisword = re.sub(" $", "", myword)
    thisword = re.sub("^ ", "", thisword)
    thisword = codepointtostring(thisword)
    with open(fileName, "a", encoding='utf-8') as myfile:
        myfile.write(thisword+"\n")
    print(thisword)
print(len(sortedlist))


