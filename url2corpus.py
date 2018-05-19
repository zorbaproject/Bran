#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import re
import html
import sys
import os


useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
thisurl = "http://www.repubblica.it/esteri/2018/05/18/news/aereo_incidente_schianto_cuba_decollo-196760241/?ref=RHPPLF-BH-I0-C8-P7-S1.8-T1"


def find_between(s, first, last ):
    try:
        start = 0
        if first != "":
            start = s.index( first ) + len( first )
        end = len(s)-1
        if last != "":
            end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""

def geturl(thisurl):
    global useragent
    req = urllib.request.Request(
        thisurl, 
        data=None, 
        headers={
            'User-Agent': useragent
        }
    )

    f = urllib.request.urlopen(req)
    thishtml = f.read().decode('utf-8')
    thishtml = html.unescape(thishtml)
    return thishtml


def cleanRepubblica(thishtml):
    start = re.escape('<div class="body-text">')
    end = re.escape('<div id="fb-facepile">')
    
    indexes = [(m.start(0), m.end(0)) for m in re.finditer(start, thishtml)]
    ns = indexes[0][1]
    indexes = [(m.start(0), m.end(0)) for m in re.finditer(end, thishtml)]
    ne = indexes[0][0]
    thishtml = thishtml[ns:ne]
    
    #remove until the first mark, beacause usually the first phrase is useless
    thishtml = re.sub("<strong>.*?<\/strong>.*?[\.]", "", thishtml)
    
    start = re.escape('<div class="snappedPlaceholder"')
    end = re.escape('</div>')
    thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)
    
    start = re.escape('<span class="gs-share-count-text">')
    end = re.escape('</span>')
    thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)
    
    start = re.escape('<blockquote class="twitter-tweet"')
    end = re.escape('</blockquote>')
    thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)
    
    return thishtml

def cleanGeneric(thishtml):
    
    #clean headers 
    thishtml = re.sub("<h[0-9].*?<\/h[0-9]>", "", thishtml, flags=re.DOTALL)
    
    #clean links
    thishtml = re.sub("<a .*?<\/a>", "", thishtml, flags=re.DOTALL)
    
    #clean js and css
    thishtml = re.sub("<script>.*?<\/script>", "", thishtml, flags=re.DOTALL)
    thishtml = re.sub("<style>.*?<\/style>", "", thishtml, flags=re.DOTALL)
    
    #clean all useless symbols
    mysymbols = re.escape('+*#')
    thishtml = re.sub("["+mysymbols+"]", "", thishtml)
    
    #clean all tags (NOTE: DOTALL means that . matches every characters including \n)
    thishtml = re.sub("<.*?>", "", thishtml, flags=re.DOTALL)
    
    #remove all empty lines
    #thishtml = re.sub("^[^a-z]*?$", "EE", thishtml)
    stripped = [line for line in thishtml.split('\n') if line.strip() != '']
    thishtml = "".join(stripped)
    
    #remove double spaces
    while (bool(re.search('\s\s', thishtml))):
        thishtml = re.sub("\s\s", " ", thishtml)
    
    return thishtml

def url2name(thisurl):
    #http://www.repubblica.it/esteri/2018/05/18/news/aereo_incidente_schianto_cuba_decollo-196760241/?ref=RHPPLF-BH-I0-C8-P7-S1.8-T1
    myname = re.sub(re.escape('http://'), "", thisurl)
    myname = re.sub(re.escape('https://'), "", myname)
    myname = re.sub("\?.*$", "", myname)
    myname = re.sub("[\\\/\.]", "-", myname)
    myname = myname + ".txt"
    return myname

def runOnPage(thisurl, output = ""):
    thishtml = geturl(thisurl)
    if 'repubblica.it' in thisurl:
        thishtml = cleanRepubblica(thishtml)
    thishtml = cleanGeneric(thishtml)
    if output == "":
        print(thishtml)
    else:
        fname = output + "/" + url2name(thisurl)
        text_file = open(fname, "w")
        text_file.write(thishtml)
        text_file.close()
    
def runRecursive(thisurl, output = ""):
    #before going on, check if we previously worked on this page
    fname = fname = output + "/" + url2name(thisurl)
    if os.path.isfile(fname) == False:
        runOnPage(thisurl, output)
        #look for every link in the page with the same starting url (up to the first /)
        #before goin on, check if we previously worked on this page


if len(sys.argv)>1:
    thisurl = sys.argv[1]
else:
    print('USAGE: ./url2corpus.py http://www.repubblica.it/esteri/2018/05/18/news/aereo_incidente_schianto_cuba_decollo-196760241/ ./corpus/ -r')
    sys.exit()
output = ""
if len(sys.argv)>2 and os.path.isdir(sys.argv[1]):
    output = sys.argv[1]
if len(sys.argv)<3:
    runOnPage(thisurl, output)
else:
    if sys.argv[3] == "-r" and output != "":
        #here we cycle for all the urls
        print("I'm scanning the URL recursively looking for other pages to download. This is going to be endless (I mean it). When you are tired, just hit Ctrl+C.")
        runRecursive(thisurl, output)
