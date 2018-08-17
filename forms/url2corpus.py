#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.request
import urllib.parse
import re
import html
import sys
import os
import json
import datetime
import time
from socket import timeout

from PySide2.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QLabel
from PySide2.QtWidgets import QMessageBox
from PySide2.QtCore import QFile
from PySide2.QtCore import QThread
from PySide2.QtWidgets import QFileDialog
from PySide2.QtWidgets import QMainWindow
from PySide2.QtWidgets import QListWidget

class TXTdownloader(QThread):

    def __init__(self, widget, whattodo):
        QThread.__init__(self)
        self.w = widget
        self.whattodo = whattodo
        self.loadvariables()
        self.setTerminationEnabled(True)
        self.stopme = False

    def loadvariables(self):
        #there are a few urls we should ignore
        self.ignore = ['quotidiano.repubblica.it', 'rep.repubblica.it', 'trovacinema.repubblica.it', 'miojob.repubblica.it', 'racconta.repubblica.it', 'video.repubblica.it', 'www.repubblica.it/economia/miojob/', 'facebook.com', 'google.com', 'yahoo.com', 'twitter.com', 'ansa.it/games/', 'ansa.it/meteo/', 'ansa.it/nuova_europa/', 'corporate.ansa.it', 'filmalcinema.shtml', 'trovacinema', 'splash.repubblica.it', 'd.repubblica.it/ricerca', 'video.d.repubblica.it', 'finanza.repubblica.it', '/static/servizi/']

        self.useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

        self.thisurl = ""
        self.visited = []
        self.visitedfile = ""
        self.firstrun = True
        self.vdb = []
        self.vdbfile = os.path.abspath(os.path.dirname(sys.argv[0]))+"/dizionario/vdb2016.txt"
        if os.path.isfile(self.vdbfile):
            self.vdb = [line.rstrip('\n') for line in open(self.vdbfile, encoding='utf-8')]
        else:
            QMessageBox.warning(self.w, "Errore", "Non ho trovato il VdB 2016 in "+self.vdbfile)
        self.todate = datetime.datetime.now().strftime('%Y-%m-%d')

    def __del__(self):
        print("Shutting down thread")

    def stop():
        self.stopme = True

    def run(self):
        if self.whattodo == "generica":
            self.downloadtxt()
        if self.whattodo == "searchrep":
            self.searchrep()
        if self.whattodo == "dotwitter":
            self.dotwitter()
        if self.whattodo == "dofb":
            self.dofb()
        return

    def find_between(self, s, first, last ):
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

    def geturl(self, thisurl):
        #global useragent
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
            f = urllib.request.urlopen(req,timeout=self.w.timeout.value())
            ft = f.read() #we should stop if this is taking too long
        except:
            ft = ""
        try:
            encoding = f.info().get_content_charset() #f.headers.get_content_charset()
            if encoding == None:
                encoding = 'windows-1252'
            thishtml = ft.decode(encoding)
            #print(encoding)
        except:
            try:
               thishtml = ft.decode('utf-8', 'backslashreplace')
            except:
               thishtml = str(ft)
        try:
            thishtml = html.unescape(thishtml)
        except:
            thishtml = ""
        return thishtml


    def cleanRepubblica(self, thishtml):
        #look for known article delimiters
        start = ['<div class="body-text".*?>', '<div class="entrytext".*?>', '<div class="post-entry".*?>', '<div class="entry-content".*?>', '<div class="article-maincolblog".*?>', '<div class="detail-articles".*?>', '<div class="entry".*?>']
        end = ['<div id="fb-facepile">','<p class="dettagliotag">', '<footer', '<p class="postmetadata">', '<!-- fine TESTO -->', '<div class=\'sociable\'>']
        cs = 0
        ce = 0
        for i in range(len(start)):
            if (bool(re.search(start[i], thishtml))):
                cs = i
        for i in range(len(end)):
            if (bool(re.search(end[i], thishtml))):
                ce = i
        #if we didn't find delimitier, this is an unknown article type so we stop here
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(start[cs], thishtml)]
        if len(indexes)<1:
            return ""
        ns = indexes[0][1]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(end[ce], thishtml)]
        if len(indexes)<1:
            return ""
        ne = indexes[0][0]
        #get only the article
        if ns < 0 or ne < 0:
            return ""
        thishtml = thishtml[ns:ne]

        #remove photogalleries
        start = re.escape('<div class="snappedPlaceholder"')
        end = re.escape('</div>')
        thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)

        #remove share buttons
        start = re.escape('<span class="gs-share-count-text">')
        end = re.escape('</span>')
        thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)

        #remove twitter feed
        start = re.escape('<blockquote class="twitter-tweet"')
        end = re.escape('</blockquote>')
        thishtml = re.sub(start+".*?"+end, "", thishtml, flags=re.DOTALL)

        return thishtml

    def cleanRepubblicaSearch(self, thishtml):
        #look for known article delimiters
        start = ['<section id="lista-risultati">']
        end = ['<!-- /risultati -->']
        cs = 0
        ce = 0
        for i in range(len(start)):
            if (bool(re.search(start[i], thishtml))):
                cs = i
        for i in range(len(end)):
            if (bool(re.search(end[i], thishtml))):
                ce = i
        #if we didn't find delimitier, this is an unknown article type so we stop here
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(start[cs], thishtml)]
        if len(indexes)<1:
            return ""
        ns = indexes[0][1]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(end[ce], thishtml)]
        if len(indexes)<1:
            return ""
        ne = indexes[0][0]
        #get only the search results
        if ns < 0 or ne < 0:
            return ""
        thishtml = thishtml[ns:ne]

        return thishtml

    def cleanAnsa(self, thishtml):
        #look for known article delimiters
        start = ['<div itemprop="articleBody".*?>']
        end = ['<div id="relatedMobile"']
        cs = 0
        ce = 0
        for i in range(len(start)):
            if (bool(re.search(start[i], thishtml))):
                cs = i
        for i in range(len(end)):
            if (bool(re.search(end[i], thishtml))):
                ce = i
        #if we didn't find delimitier, this is an unknown article type so we stop here
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(start[cs], thishtml)]
        if len(indexes)<1:
            return ""
        ns = indexes[0][1]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(end[ce], thishtml)]
        if len(indexes)<1:
            return ""
        ne = indexes[0][0]
        #get only the article
        if ns < 0 or ne < 0:
            return ""
        thishtml = thishtml[ns:ne]

        return thishtml

    def cleanGeneric(self, thishtml):

        #clean headers
        thishtml = re.sub("<h[0-9].*?<\/h[0-9]>", "", thishtml, flags=re.DOTALL)

        #clean links
        repl = ""
        if self.w.keeplinkscontent.isChecked():
            repl = "\g<1>"#NOTE \g<\> is equal to \1, meaning group 1, but it's less ambiguous
        thishtml = re.sub("<[aA]\s.*?>(.*?)<\/[aA]>", repl, thishtml, flags=re.DOTALL)

        #clean js and css
        thishtml = re.sub("<script.*?<\/script>", "", thishtml, flags=re.IGNORECASE|re.DOTALL)
        thishtml = re.sub("<style.*?<\/style>", "", thishtml, flags=re.IGNORECASE|re.DOTALL)

        #remove strong tag if in caps lock
        thishtml = re.sub("<strong>[^a-z]+?<\/strong>", "", thishtml)

        #clean all useless symbols
        mysymbols = re.escape('+*#')
        thishtml = re.sub("["+mysymbols+"]", "", thishtml)

        #clean all tags (NOTE: DOTALL means that . matches every characters including \n)
        thishtml = re.sub("<.*?>", "", thishtml, flags=re.DOTALL)

        #remove all empty lines
        #stripped = [line for line in thishtml.split('\n') if line.strip() != '']
        #thishtml = "".join(stripped)
        nl = '\n' #switch to ' ' if you don't want paragraph separation
        stripped = ""
        for line in thishtml.split('\n'):
            if line.strip() != '':
                for word in line.split():
                    #it's a good idea to check if at least a few words in every lines belong to the vdb
                    if word in self.vdb or self.w.usevdb.isChecked(): #len(vdb)<1:
                        stripped = stripped + line + nl
                        break
        thishtml = stripped

        #remove double spaces
        while (bool(re.search('\s\s', thishtml))):
            thishtml = re.sub("\s\s", " ", thishtml)

        #remove initial spaces
        thishtml = re.sub("^\s", "", thishtml)
        thishtml = re.sub("^\s*?-", "", thishtml)
        thishtml = re.sub("^(di)\s", "", thishtml)

        #delete spaces at the end of the lines, then delete line if it does not end with a dot
        stripped = ""
        for line in thishtml.split('\n'):
            line = re.sub("\s*?$", "", line)
            if len(line)<200 and bool(re.match('.*?[\.,;\?!]$.*?', line))==False:
                line = ''
            stripped = stripped + line + nl
        thishtml = stripped

        return thishtml

    def getLinks(self, thishtml):
        #regex = "<[aA] .*?href=\"(http.*?|\/.*?)\".*?<\/[aA]>"
        regex = ".*?href=[\"'](.*?)[\"']"
        links = [m.group(1) for m in re.finditer(regex, thishtml, flags=re.DOTALL)]
        return links

    def getSearchLinks(self, thishtml):
        links = [m.group(1) for m in re.finditer("<a .*?href=\"(http.*?|\/.*?)\".*?title=.*?<\/a>", thishtml, flags=re.DOTALL)]
        return links

    def getRSSLinks(self, thishtml):
        links = [m.group(1) for m in re.finditer("<link>.*?(http.*?)(\]\]>)*?<\/link>", thishtml, flags=re.DOTALL)]
        return links

    def url2name(self, thisurl):
        myname = re.sub(re.escape('http://'), "", thisurl)
        myname = re.sub(re.escape('https://'), "", myname)
        #myname = re.sub("\?.*$", "", myname)
        myname = re.sub("[\\\/\.\?&]", "-", myname)
        if len(myname)>200:
            myname = myname[0:200]
        myname = myname + ".txt"
        return myname

    def runOnPage(self, thisurl, output = ""):
        self.firstrun = False
        if bool(re.match(self.w.ignoreext.text(), thisurl))==True or self.w.stopall.isChecked():
            return []
        thishtml = self.geturl(thisurl)
        links = self.getLinks(thishtml)
        m = re.match(r"(http.*?\..*?)(\/|$)", thisurl)
        baseurl = m.group(1)
        for i in range(len(links)):
            if len(links[i]) < 6:
                links[i] = ""
            elif links[i][0] == '/':
                links[i] = baseurl + links[i]
            elif links[i][:5] != 'http:' and links[i][:6] != 'https:':
                links[i] = baseurl + "/" + links[i]
            #print(links[i])
            if links[i] == thisurl:
                links[i] = ''
            else:
                for ii in range(len(self.ignore)):
                    if self.ignore[ii] in links[i]:
                        links[i] = ''
        for ii in range(len(self.ignore)):
            if self.ignore[ii] in thisurl:
                return []
        #cleaning for Repubblica.it
        if 'repubblica.it' in thisurl:
            if 'rss2.0.xml' in thisurl:
                links = self.getRSSLinks(thishtml)
                return links
            thishtml = self.cleanRepubblica(thishtml)
        #cleaning for ANSA.it
        if 'ansa.it' in thisurl:
            if 'rss.xml' in thisurl:
                links = self.getRSSLinks(thishtml)
                return links
            thishtml = self.cleanAnsa(thishtml)
        thishtml = self.cleanGeneric(thishtml)
        if output == "":
            print(thishtml)
        else:
            fname = output + "/" + self.url2name(thisurl)
            if thishtml != "":
                text_file = open(fname, "w", encoding='utf-8')
                text_file.write(thishtml)
                text_file.close()
                self.w.results.addItem(thisurl)
                self.w.results.setCurrentRow(self.w.results.count()-1)
                QApplication.processEvents()
        return links

    def runRecursive(self, thisurl, output = ""):
        #global visited
        if self.w.stopall.isChecked():
            self.quit()
            return
        #before going on, check if we previously worked on this page
        m = re.match(r"http.*?\.(.*?)(\/|$)", thisurl)
        baseurl = m.group(1)
        fname = output + "/" + self.url2name(thisurl)
        if os.path.isfile(fname) == False or self.firstrun:
            #if re.sub("\?.*$", "", thisurl) not in visited:
            if thisurl not in self.visited: #and bool(re.match(self.w.ignoreext.text(), thisurl))==False:
                links = self.runOnPage(thisurl, output)
                self.visited.append(thisurl)
            else:
                links = []
            #look for every link in the page with the same starting url (up to the first /)
            for i in range(len(links)):
                m = re.match(r"http.*?:\/\/(.*?)(\/|$)", links[i])
                lbaseurl = ''
                if m:
                    lbaseurl = m.group(1)
                if re.sub("\?.*$", "", links[i]) not in self.visited and baseurl in lbaseurl:
                    #print(links[i])
                    with open(self.visitedfile, "a", encoding='utf-8') as myfile:
                        myfile.write(links[i]+"\n")
                    self.runRecursive(links[i],output)

    def runSearchRepubblica(self, thisquery, output, fromdate, todate):
        query = thisquery.replace('RICERCAREPUBBLICA:','')
        if query == '':
            query = '+'
        query = query.replace(' ','+')
        #we are not allowed to get more than 250 pages
        for npage in range(250):
            #http://ricerca.repubblica.it/ricerca/repubblica-it?author=&sortby=adate&query=+&fromdate=2000-10-01&todate=2018-05-22&mode=all&page=1
            thisurl = 'http://ricerca.repubblica.it/ricerca/repubblica-it?author=&sortby=adate&query=' +query +'&fromdate='+fromdate+'&todate='+todate+'&mode=all&page='+str(npage)
            thishtml = self.geturl(thisurl)
            thishtml = self.cleanRepubblicaSearch(thishtml)
            links = self.getSearchLinks(thishtml)
            #m = re.match(r"(http.*?\..*?)(\/|$)", 'http://www.repubblica.it')
            baseurl = 'http://www.repubblica.it' #m.group(1)
            alllinks = []
            articlesfile = output + "/articles.tmp"
            if os.path.isfile(articlesfile):
                alllinks = [line.rstrip('\n') for line in open(articlesfile, encoding='utf-8')]
            for i in range(len(links)):
                if self.w.stopall.isChecked():
                    self.quit()
                    return
                if links[i][0] == '/':
                    links[i] = baseurl+ links[i]
                if links[i] not in alllinks and 'www.repubblica.it/?ref=search' not in links[i] and 'ricerca.repubblica.it' not in links[i]:
                    fname = output + "/" + self.url2name(links[i])
                    if os.path.isfile(fname) == False:
                        pagehtml = self.geturl(links[i])
                        pagehtml = self.cleanGeneric(pagehtml)
                        if pagehtml != "":
                            text_file = open(fname, "w", encoding='utf-8')
                            text_file.write(pagehtml)
                            text_file.close()
                            alllinks.append(links[i])
                            self.w.results.addItem(links[i])
                            self.w.results.setCurrentRow(self.w.results.count()-1)
                            with open(articlesfile, "a", encoding='utf-8') as myfile:
                                myfile.write(links[i]+"\n")

    def downloadtxt(self):
        thisurl = self.w.url.text()
        output = ""
        if os.path.isdir(self.w.folder.text()):
            output = self.w.folder.text()
        else:
            return
        self.w.results.clear()
        self.w.resultsgrp.setTitle("STO LAVORANDO:")
        if self.w.recursive.isChecked():
            self.visitedfile = output + "/visited.tmp"
            if os.path.isfile(self.visitedfile):
                self.visited = [line.rstrip('\n') for line in open(self.visitedfile, encoding='utf-8')]
            self.runRecursive(thisurl, output)
        else:
            self.runOnPage(thisurl, output)
        self.w.resultsgrp.setTitle("In attesa")

    def searchrep(self):
        thisurl = self.w.repquery.text()
        self.w.results.clear()
        todate = str(self.w.aanno.value()) + "-" + str(self.w.amese.value()) + "-" + str(self.w.agiorno.value())
        fromdate = str(self.w.daanno.value()) + "-" + str(self.w.damese.value()) + "-" + str(self.w.dagiorno.value())
        if os.path.isdir(self.w.folder.text()):
            output = self.w.folder.text()
            fromyear = int(fromdate.split('-')[0])
            frommonth = int(fromdate.split('-')[1])
            toyear = int(todate.split('-')[0])
            for iy in range(1+toyear-fromyear):
                for im in range(13-frommonth):
                    nfromdate = str(fromyear+iy)+'-'+str(frommonth+im).zfill(2) +'-01'
                    self.w.results.addItem(nfromdate)
                    self.w.results.setCurrentRow(self.w.results.count()-1)
                    if self.w.stopall.isChecked():
                        self.quit()
                        return
                    fdatefile = output + "/fromdate.tmp"
                    with open(fdatefile, "a", encoding='utf-8') as myfile:
                        myfile.write(str(nfromdate)+"\n")
                    self.runSearchRepubblica(thisurl, output, nfromdate, todate)
                frommonth = 1
            return
        else:
            return

    def dotwitter(self):
        #self.get_all_tweets(self.w.twittername.text()) #nome senza la @
        print("Not implemented")

    def scrapefacebook(self, mypage):
        TOSELECT_FB = 'pages_reaction_units'
        maxresults = 300
        towait = 10
        lstart = '/pages_reaction_units/more/?page_id='
        lending = '&cursor={"card_id":"videos","has_next_page":true}&surface=www_pages_home&unit_count='+str(maxresults)+'&referrer&dpr=1&__user=0&__a=1'
        output = ""
        if os.path.isdir(self.w.folder.text()):
            output = self.w.folder.text() + "/"
        self.w.results.addItem(mypage)
        self.w.results.setCurrentRow(self.w.results.count()-1)
        allhtml = self.geturl(mypage)
        try:
            start = mypage.index("https://")
            end = mypage.index('/',start+8)
            fbdomain = mypage[start:end]
            indexes = [(m.start(0), m.end(0)) for m in re.finditer(TOSELECT_FB, allhtml[start+1:])]
            start = indexes[0][0]
            end = allhtml.index('"',start+1)
            thislink = allhtml[start:end]
            #estrapola page_id
            #https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor={"card_id":"videos","has_next_page":true}&surface=www_pages_home&unit_count=300&referrer&dpr=1&__user=0&__a=1
            start = thislink.index("page_id=")
            end = thislink.index('&',start+9)
            pageid = thislink[start+8:end]
            start = mypage.index("facebook.com")
            pagename = mypage[start+12:]
            pagename = re.sub(r'[^A-Za-z0-9]',"",pagename)
        except:
            fbdomain = ""
            pageid = ""
        fname = output + "fb_" + pagename + ".txt"
        if self.w.fbcsv.isChecked():
            fname = output + "fb_" + pagename + ".csv"
        alllinks = []
        linksfile = output + "fb_" + pagename + ".tmp"
        if os.path.isfile(linksfile):
            alllinks = [line.rstrip('\n') for line in open(linksfile, encoding='utf-8')]
        timelineiter = 0
        ripristino = False
        active = True
        while active:
            link = fbdomain + lstart + pageid + lending
            if timelineiter == 0 and len(alllinks)>0:
                link = alllinks[len(alllinks)-1]
                ripristino = True
            with open(linksfile, "a", encoding='utf-8') as lfile:
                lfile.write(link+'\n')
            #print(link)
            self.w.results.addItem(link)
            self.w.results.setCurrentRow(self.w.results.count()-1)
            if self.w.stopall.isChecked():
                active = False
                self.quit()
                return
            newhtml = self.geturl(link)
            try:
                start = newhtml.index("{\"__html\":")
                end = newhtml.index("]]")
                postshtml = newhtml[start:end]
                #eliminazione caratteri unicode surrogati
                postshtml = postshtml.encode("utf-8").decode('unicode-escape')
                postshtml = re.sub(r'[\uD800-\uDFFF]',"",postshtml)
                #dividi per <div e tieni solo quello che sta tra <p> e </p>
                #data-utime, print(datetime.utcfromtimestamp(int(utime)).strftime('%Y-%m-%d %H:%M:%S'))
                postsarray = re.split('<div', postshtml)
                timearray = []
                for i in range(len(postsarray)):
                    indexes = [(m.start(0), m.end(0)) for m in re.finditer('<p>(.*?)<\\\\/p>', postsarray[i])]
                    thispost = ""
                    for n in range(len(indexes)):
                        start = indexes[n][0]
                        end = indexes[n][1]
                        thispost = thispost + postsarray[i][start:end]
                    #pulisco i tag non necessari
                    postsarray[i] = re.sub(r'<.*?>',"",thispost)
                #print(postsarray)
                try:
                    maxresults = 8
                    start = newhtml.index('&cursor=')
                    end = newhtml.index("&unit_count=", start+1)
                    lending = newhtml[start:end]
                    #eliminazione caratteri unicode surrogati
                    lending = lending.encode("utf-8").decode('unicode-escape')
                    lending = re.sub(r'[\uD800-\uDFFF]',"",lending)
                    lending = urllib.parse.unquote(lending)
                    lending = lending + '&unit_count='+str(maxresults)+'&dpr=1&__user=0&__a=1'
                    #https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor={"timeline_cursor":"timeline_unit:1:00000000001528624041:04611686018427387904:09223372036854775793:04611686018427387904","timeline_section_cursor":{},"has_next_page":true}&surface=www_pages_home&unit_count=8&dpr=1&__user=0&__a=1
                except:
                    active = False
            except:
                postsarray = []
                timearray = []
            #salvo il risultato in un file: se è il primo ciclo creo il file, altrimenti aggiungo
            if fname != "":
                postsfile = ""
                for i in range(len(postsarray)):
                    if postsarray[i] != "":
                        if self.w.fbcsv.isChecked():
                            postsfile = postsfile + timearray[i] + "\t"
                        postsfile = postsfile + postsarray[i] + "\n"
                if timelineiter == 0 and ripristino==False:
                    text_file = open(fname, "w", encoding='utf-8')
                    text_file.write(postsfile)
                    text_file.close()
                else:
                    with open(fname, "a", encoding='utf-8') as myfile:
                        myfile.write(postsfile)
            timelineiter = timelineiter +1
            time.sleep(towait)

    def dofb(self):
        self.w.results.clear()
        self.w.resultsgrp.setTitle("STO LAVORANDO:")
        fbname = self.w.fbname.text()
        self.scrapefacebook(fbname)
        self.w.resultsgrp.setTitle("In attesa")


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        #QMessageBox.warning(self, self.tr("My Application"), self.tr("The document has been modified.\nDo you want to save your changes?"))
        file = QFile(os.path.abspath(os.path.dirname(sys.argv[0]))+"/forms/url2corpus.ui")
        file.open(QFile.ReadOnly)
        loader = QUiLoader()
        self.w = loader.load(file)
        layout = QVBoxLayout()
        layout.addWidget(self.w)
        self.setLayout(layout)
        self.w.accepted.connect(self.isaccepted)
        self.w.rejected.connect(self.isrejected)
        self.setWindowTitle("Estrai corpus da sito web")
        self.w.resultsgrp.setTitle("In attesa")
        self.w.download.clicked.connect(self.downloadtxt)
        self.w.searchrep.clicked.connect(self.searchrep)
        self.w.dotwitter.clicked.connect(self.dotwitter)
        self.w.dofb.clicked.connect(self.dofb)
        #self.w.stopall.clicked.connect(self.stopall)
        self.w.choosefolder.clicked.connect(self.choosefolder)
        self.w.ignoreext.setText(".*(\.zip|\.xml|\.pdf|\.avi|\.gif|\.jpeg|\.jpg|\.ico|\.png|\.wav|\.mp3|\.mp4|\.mpg|\.mpeg|\.tif|\.tiff|\.css|\.json|\.rar)$")
        todate = datetime.datetime.now().strftime('%Y-%m-%d')
        self.w.aanno.setValue(int(todate.split('-')[0]))
        self.w.amese.setValue(int(todate.split('-')[1]))
        self.w.agiorno.setValue(int(todate.split('-')[2]))
        self.mycfgfile = ""
        self.mycfg = json.loads('{"javapath": "", "tintpath": "", "tintaddr": "", "tintport": "", "sessions" : []}')

    def loadPersonalCFG(self):
        try:
            text_file = open(self.mycfgfile, "r", encoding='utf-8')
            lines = text_file.read()
            text_file.close()
            self.mycfg = json.loads(lines)
        except:
            print("Creo il file di configurazione")

    def savePersonalCFG(self):
        try:
            cfgtxt = json.dumps(self.mycfg)
            text_file = open(self.mycfgfile, "w", encoding='utf-8')
            text_file.write(cfgtxt)
            text_file.close()
        except:
            print("Non posso salvare la configurazione")


    def downloadtxt(self):
        self.myThread = TXTdownloader(self.w, "generica")
        self.myThread.finished.connect(self.threadstopped)
        self.myThread.start()

    def searchrep(self):
        self.myThread = TXTdownloader(self.w, "searchrep")
        self.myThread.finished.connect(self.threadstopped)
        self.myThread.start()

    def dotwitter(self):
        consumer_key = self.w.consumer_key.text()
        consumer_secret = self.w.consumer_secret.text()
        access_key = self.w.access_key.text()
        access_secret = self.w.access_secret.text()
        tmptw = [consumer_key, consumer_secret, access_key, access_secret]
        self.mycfg["twitter"] = tmptw
        self.savePersonalCFG()
        self.myThread = TXTdownloader(self.w, "dotwitter")
        self.myThread.finished.connect(self.threadstopped)
        self.myThread.start()

    def dofb(self):
        #fbappid = self.w.fbappid.text()
        #fbappsecret = self.w.fbappsecret.text()
        #tmpfb = [fbappid, fbappsecret]
        #self.mycfg["facebook"] = tmpfb
        self.savePersonalCFG()
        self.myThread = TXTdownloader(self.w, "dofb")
        self.myThread.finished.connect(self.threadstopped)
        self.myThread.start()

    def threadstopped(self):
        self.w.stopall.setChecked(False)

    def setmycfgfile(self, mfile):
        self.mycfgfile = mfile
        self.mycfg = json.loads('{"javapath": "", "tintpath": "", "tintaddr": "", "tintport": "", "sessions" : []}')
        self.loadPersonalCFG()
        try:
            self.w.consumer_key.setText(self.mycfg["twitter"][0])
            self.w.consumer_secret.setText(self.mycfg["twitter"][1])
            self.w.access_key.setText(self.mycfg["twitter"][2])
            self.w.access_secret.setText(self.mycfg["twitter"][3])
            #self.w.fbappid.setText(self.mycfg["facebook"][0])
            #self.w.fbappsecret.setText(self.mycfg["facebook"][1])
        except:
            return

    def choosefolder(self):
        fileName = QFileDialog.getExistingDirectory(self, "Seleziona la cartella in cui salvare il corpus")
        if not fileName == "":
            if os.path.isdir(fileName):
                self.w.folder.setText(fileName)

    def isaccepted(self):
            self.accept()
    def isrejected(self):
            self.reject()
