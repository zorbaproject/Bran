#!/usr/bin/python3

import sys
import re

print("wiki-pages-extract.py itwiki-20181001-pages-articles.xml wiki-it.txt")


file = open(sys.argv[2],"w")
file.write("")
file.close() 

ispage = False
towrite = False
with open(sys.argv[1], "r") as ins:
    for line in ins:
        if "<page>" in line:
            ispage = True
        if "</page>" in line:
            ispage = False
        if "<text" in line and ispage:
            towrite = True
        if "</text>" in line:
            towrite = False
        if towrite and bool(re.match('^[A-Za-zàèéìòùÈ]', line)):
            line = line.replace("'''", "")
            line = line.replace("''", "")
            line = re.sub("\[\[[^\[\]]*?\|(.*?)\]\]", "\g<1>", line, flags=re.IGNORECASE|re.DOTALL)
            line = line.replace("[[", "")
            line = line.replace("]]", "")
            line = re.sub("\{\{.*?\}\}", "", line, flags=re.IGNORECASE|re.DOTALL)
            line = re.sub("\{\{[^\}]*?$", "", line, flags=re.IGNORECASE|re.DOTALL)
            line = line.replace("&amp;nbsp;", " ")
            line = re.sub("&lt;ref&gt;.*?&lt;/ref&gt;", "", line, flags=re.IGNORECASE|re.DOTALL)
            line = re.sub("&lt;.*?&gt;", "", line, flags=re.IGNORECASE|re.DOTALL)
            line = re.sub("([ \.]).*?://.*? ", "\g<1>", line, flags=re.IGNORECASE|re.DOTALL)
            line = line.replace("&quot;", "\"")
            line = re.sub("\([0-9\.]*?\)", "", line, flags=re.IGNORECASE|re.DOTALL)
            line = re.sub("^.*?\..*?\|", "", line, flags=re.IGNORECASE|re.DOTALL)
            with open(sys.argv[2], "a") as myfile:
                myfile.write(line)
