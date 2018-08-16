#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#basic idea is this one: https://blog.michaelyin.info/how-crawl-infinite-scrolling-pages-using-python/ but we need to rewrite it completely to make it work

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

#START_PAGE = "https://it-it.facebook.com/chiesapastafarianaitaliana/"
#START_PAGE = "https://it-it.facebook.com/salviniofficial/"
START_PAGE = "https://twitter.com/DioSpaghetto"

useragent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'

def geturl(thisurl):
        global useragent
        if thisurl == '':
            return ''
        req = urllib.request.Request(
            thisurl,
            data=None,
            headers={
                'User-Agent': useragent
            }
        )

        thishtml = ""
        if 1==1: #try:
            f = urllib.request.urlopen(req,timeout=300)
            ft = f.read() #we should stop if this is taking too long
        #except:
        #    ft = ""
        try:
            encoding = f.info().get_content_charset() #f.headers.get_content_charset()
            if encoding == None:
                encoding = 'windows-1252'
            thishtml = ft.decode(encoding)
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

def fixunicode(oldstring):
    newstring = oldstring
    orig = []
    repl = []
    indexes = [(m.start(0), m.end(0)) for m in re.finditer(r"\\u....", oldstring)]
    for i in range(len(indexes)):
        start = indexes[i][0]
        end = indexes[i][1]
        tmp = oldstring[start:end]
        if not tmp in orig:
            orig.append(tmp)
            byterepl = b'\u'+tmp[2:].encode('ascii')
            strrepl = byterepl.decode('unicode-escape')
            if "u" in strrepl:
                strrepl = ""
            repl.append(strrepl)
    for i in range(len(orig)):
        newstring = newstring.replace(orig[i], repl[i])
    newstring = re.sub(r'[\uD800-\uDFFF]',"",newstring)
    print(orig)
    print(repl)
    return newstring


def scrapefacebook(mypage):
    TOSELECT_FB = 'pages_reaction_units'
    maxresults = 300
    towait = 10
    lstart = '/pages_reaction_units/more/?page_id='
    lending = '&cursor={"card_id":"videos","has_next_page":true}&surface=www_pages_home&unit_count='+str(maxresults)+'&referrer&dpr=1&__user=0&__a=1'
    allhtml = geturl(mypage)
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
    fname = "fb_" + pagename + ".txt"
    timelineiter = 0
    active = True
    while active:
        link = fbdomain + lstart + pageid + lending
        print(link)
        newhtml = geturl(link)
        try:
            start = newhtml.index("{\"__html\":")
            end = newhtml.index("]]")
            postshtml = newhtml[start:end]
            #eliminazione caratteri unicode surrogati
            postshtml = postshtml.encode("utf-8").decode('unicode-escape')
            postshtml = re.sub(r'[\uD800-\uDFFF]',"",postshtml)
            #dividi per <div e tieni solo quello che sta tra <p> e </p>
            postsarray = re.split('<div', postshtml)
            for i in range(len(postsarray)):
                indexes = [(m.start(0), m.end(0)) for m in re.finditer('<p>(.*?)<\\\\/p>', postsarray[i])]
                thispost = ""
                for n in range(len(indexes)):
                    start = indexes[n][0]
                    end = indexes[n][1]
                    thispost = thispost + postsarray[i][start:end]
                #pulisco i tag non necessari
                postsarray[i] = re.sub(r'<.*?>',"",thispost)
            print(postsarray)
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
        #salvo il risultato in un file: se è il primo ciclo creo il file, altrimenti aggiungo
        if fname != "":
            postsfile = ""
            for i in range(len(postsarray)):
                if postsarray[i] != "":
                    postsfile = postsfile + postsarray[i] + "\n"
            if timelineiter == 0:
                text_file = open(fname, "w", encoding='utf-8')
                text_file.write(postsfile)
                #text_file.write(newhtml)
                text_file.close()
            else:
                with open(fname, "a", encoding='utf-8') as myfile:
                    myfile.write(postsfile)
        timelineiter = timelineiter +1
        time.sleep(towait)


def scrapetwitter(mypage):
    #https://twitter.com/i/profiles/show/DioSpaghetto/timeline/tweets?composed_count=0&include_available_features=1&include_entities=1&include_new_items_bar=true&interval=30000&latent_count=0&min_position=1029148848562872326
    #https://twitter.com/i/profiles/show/DioSpaghetto/timeline/tweets?include_available_features=1&include_entities=1&max_position=1001537618130210816&reset_error_state=false
        
    lstart = '/timeline/tweets?include_available_features=1&include_entities=1&max_position='
    lending = '&reset_error_state=false'
    fname = "tw_salvini.txt"
    twdomain = 'https://twitter.com/i/profiles/show/'
    allhtml = geturl(mypage)
    try:
        start = allhtml.index('max_id=')
        end = allhtml.index('"',start+7)
        max_position = allhtml[start+7:end]
        start = mypage.index("twitter.com/")
        pageid = mypage[start+12:]
    except:
        pageid = ""
        max_position = ""
    link = 'https://twitter.com/i/profiles/show/DioSpaghetto/timeline/tweets' #twdomain + pageid + lstart + max_position + lending
    print(link)
    newhtml = geturl(link)
    #print(newhtml)
    try:
        start = newhtml.index("INIZIOOOOOOO")
        end = newhtml.index("]]")
        postshtml = newhtml[start:end]
        #eliminazione caratteri unicode surrogati
        postshtml = postshtml.encode("utf-8").decode('unicode-escape')
        postshtml = re.sub(r'[\uD800-\uDFFF]',"",postshtml)
        #dividi per <div e tieni solo quello che sta tra <p> e </p>
        postsarray = re.split('<div', postshtml)
        for i in range(len(postsarray)):
            indexes = [(m.start(0), m.end(0)) for m in re.finditer('<p>(.*?)<\\\\/p>', postsarray[i])]
            thispost = ""
            for n in range(len(indexes)):
                start = indexes[n][0]
                end = indexes[n][1]
                thispost = thispost + postsarray[i][start:end]
            #pulisco i tag non necessari
            postsarray[i] = re.sub(r'<.*?>',"",thispost)
        print(postsarray)
    except:
        postsarray = []
    #salvo il risultato in un file
    if fname != "":
        postsfile = ""
        for i in range(len(postsarray)):
            if postsarray[i] != "":
                postsfile = postsfile + postsarray[i] + "\n"
        text_file = open(fname, "w", encoding='utf-8')
        #text_file.write(postsfile)
        text_file.write(newhtml)
        text_file.close()


if __name__ == '__main__':
    if len(sys.argv)>1:
        START_PAGE = sys.argv[1]
    if "facebook.com" in START_PAGE:
        scrapefacebook(START_PAGE)
    if "twitter.com" in START_PAGE:
        scrapetwitter(START_PAGE)
