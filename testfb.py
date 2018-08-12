#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#basic idea is this one: https://blog.michaelyin.info/how-crawl-infinite-scrolling-pages-using-python/ but we need to rewrite it completely to make it work

import urllib.request
import re
import html
import sys
import os
import json
import datetime
from socket import timeout

START_PAGE = "https://it-it.facebook.com/chiesapastafarianaitaliana/" # "https://scrapingclub.com/exercise/list_infinite_scroll/"

TOSELECT_FB = 'pages_reaction_units'

# <div><a ajaxify="/pages_reaction_units/more/?page_id=286796408016028&amp;cursor=%7B%22card_id%22%3A%22videos%22%2C%22has_next_page%22%3Atrue%7D&amp;surface=www_pages_home&amp;unit_count=8&amp;referrer" href="#" rel="ajaxify" class="pam uiBoxLightblue uiMorePagerPrimary" role="button">Altro...<i class="mhs mts arrow img sp_QmW7P-llck- sx_577d40"></i></a><span class="uiMorePagerLoader pam uiBoxLightblue"><span class="img _55ym _55yq _55yo _3-8h" aria-busy="true" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuetext="Caricamento..."></span></span></div>

#UNO
#https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor=%7B%22card_id%22%3A%22videos%22%2C%22has_next_page%22%3Atrue%7D&surface=www_pages_home&unit_count=8&referrer&dpr=1&__user=0&__a=1&__dyn=5V4cjJLyGmaWxd2umeCJDzk68OqfoOm9AKGgS8WGnJLFGA4XwyxuES2N6xvyAubGqKi5azppEHUOqqGxSaUyGxeipi28gyElWAAzppenKtqx2AcUhz998iGtxifGcgLAKibUSbBWAhfypfh4cx25UCiajzaUKegHy4mEepoGmXBy8GumuibBDJ3o9FRxlu7VECqQh1Cqq4Gz-iRAyFK5eviCxyHu4olDhoScz99FXyoyiaCzUqykqqaKHWGVVui4p5UBaBKhWADBCEyS8DpkK25h88EyiibKbF2UxyVriCUKbwFxC4ebybU-QZ4GCXp4dyp8ZdoWbAzAulaayKjyF-i7QF8CqaJ1e4EKdAh99umh4ykiUhDzAUgGUGV8hADAyEOGDmbxTGFUO8ggKii44VFVqKiUyQqV4vzUObz9ohAypd2Xy-m7F8yh2qj-EC&__req=6&__be=-1&__pc=PHASED%3ADEFAULT&__rev=4201145
#https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor={"card_id":"videos","has_next_page":true}&surface=www_pages_home&unit_count=8&referrer&dpr=1&__user=0&__a=1

#DUE
#https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor=%7B%22timeline_cursor%22%3A%22timeline_unit%3A1%3A00000000001531152490%3A04611686018427387904%3A09223372036854775801%3A04611686018427387904%22%2C%22timeline_section_cursor%22%3A%7B%7D%2C%22has_next_page%22%3Atrue%7D&surface=www_pages_home&unit_count=8&dpr=1&__user=0&__a=1&__dyn=5V4cjJLyGmaWxd2umeCJDzk68OqfoOm9AKGgS8WGnJLFGA4XwyxuES2N6xvyAubGqKi5azppEHUOqqGxSaUyGxeipi28gyElWAAzppenKtqx2AcUhz998iGtxifGcgLAKibUSbBWAhfypfh4cx11q9AyAUOKbzAaUx5G3CmaBKVoyaDBDAyVpXgS2qtolnx-q9CJ4gpCCxaE_AJkUGrxjDQFEoGTx65pQmdz8OiquUC8AyFE-6EB6CyHG-GKunAx6hu9iFrAuF9VpG8Jy9Slbwxki2a8AAyXyWgK8oKmQFKbUC2C6ogUK8Lz_jQiGrJAgS9AzQRzEKiehVkEGaVeaDV8viAypFpbgjxabzp4iinBAh8B4K4pUVe4aKaKi4p9V8GcGFRyUtWGucy44bAAzSVFVqKiUyQqV4vzUObz9ohAypd2Xy-m7F8yh2qj-EC&__req=9&__be=-1&__pc=PHASED%3ADEFAULT&__rev=4201145
#https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor={"timeline_cursor":"timeline_unit:1:00000000001531152490:04611686018427387904:09223372036854775801:04611686018427387904","timeline_section_cursor":{},"has_next_page":true}&surface=www_pages_home&unit_count=8&dpr=1&__user=0&__a=1

#TRE
#https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor=%7B%22timeline_cursor%22%3A%22timeline_unit%3A1%3A00000000001528624041%3A04611686018427387904%3A09223372036854775793%3A04611686018427387904%22%2C%22timeline_section_cursor%22%3A%7B%7D%2C%22has_next_page%22%3Atrue%7D&surface=www_pages_home&unit_count=8&dpr=1&__user=0&__a=1&__dyn=5V4cjJLyGmaWxd2umeCJDzk68OqfoOm9AKGgS8WGnJLFGA4XwyxuES2N6xvyAubGqKi5azppEHUOqqGxSaUyGxeipi28gyElWAAzppenKtqx2AcUhz998iGtxifGcgLAKibUSbBWAhfypfh4cx11q9AyAUOKbzAaUx5G3CmaBKVoyaDBDAyVpXgS2qtolnx-q9CJ4gpCCxaE_AJkUGrxjDQFEoGTx65pQmdz8OiquUC8AyFE-6EB6CyHG-GKunAx6hu9iFrAuF9VpG8Jy9Slbwxki2a8AAyXyWgK8oKmQFKbUC2C6ogUK8Lz_jQiGrJAgS9AzQRzEKiehVkEGaVeaDV8viAypFpbgjxabzp4iinBAh8B4K4pUVe4aKaKi4p9V8GcGFRyUtWGucy44bAAzSVFVqKiUyQqV4vzUObz9ohAypd2Xy-m7F8yh2qj-EC&__req=c&__be=-1&__pc=PHASED%3ADEFAULT&__rev=4201145
#https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor={"timeline_cursor":"timeline_unit:1:00000000001528624041:04611686018427387904:09223372036854775793:04611686018427387904","timeline_section_cursor":{},"has_next_page":true}&surface=www_pages_home&unit_count=8&dpr=1&__user=0&__a=1

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
        try:
            f = urllib.request.urlopen(req,timeout=300)
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
    global TOSELECT_FB
    maxresults = 100
    lstart = '/pages_reaction_units/more/?page_id='
    lending = '&cursor={"card_id":"videos","has_next_page":true}&surface=www_pages_home&unit_count='+str(maxresults)+'&referrer&dpr=1&__user=0&__a=1'
    allhtml = geturl(mypage)
    try:
        start = mypage.index("https://")
        end = mypage.index('/',start+8)
        fbdomain = mypage[start:end]
        indexes = [(m.start(0), m.end(0)) for m in re.finditer(TOSELECT_FB, allhtml[start+1:])]
        print(indexes)
        start = indexes[0][0]
        end = allhtml.index('"',start+1)
        thislink = allhtml[start:end]
        start = thislink.index("page_id=")
        end = thislink.index('&',start+9)
        pageid = thislink[start+8:end]
    except:
        fbdomain = ""
        pageid = ""
    link = fbdomain + lstart + pageid + lending
    print(link)
    #estrapola page_id
    #https://it-it.facebook.com/pages_reaction_units/more/?page_id=286796408016028&cursor={"card_id":"videos","has_next_page":true}&surface=www_pages_home&unit_count=1000&referrer&dpr=1&__user=0&__a=1
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
            indexes = [(m.start(0), m.end(0)) for m in re.finditer('<p>(.*?)<.*?/p>', postsarray[i])]
            thispost = ""
            for n in range(len(indexes)):
                start = indexes[n][0]
                end = indexes[n][1]
                thispost = thispost + postsarray[i][start:end]
            #pulisco i tag non necessari
            postsarray[i] = re.sub(r'<.*?p>',"",thispost)
        print(postsarray)
    except:
        postsarray = []
    fname = "cpi.txt"
    if fname != "":
        postsfile = ""
        for i in range(len(postsarray)):
            if postsarray[i] != "":
                postsfile = postsfile + postsarray[i] + "\n"
        text_file = open(fname, "w", encoding='utf-8')
        text_file.write(postsfile)
        text_file.close()



if __name__ == '__main__':
    if "facebook.com" in START_PAGE:
        scrapefacebook(START_PAGE)
