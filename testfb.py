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

TOSELECT_FB = '/pages_reaction_units/more/' # 'a[class="page-link next-page"]'

# <div><a ajaxify="/pages_reaction_units/more/?page_id=286796408016028&amp;cursor=%7B%22card_id%22%3A%22videos%22%2C%22has_next_page%22%3Atrue%7D&amp;surface=www_pages_home&amp;unit_count=8&amp;referrer" href="#" rel="ajaxify" class="pam uiBoxLightblue uiMorePagerPrimary" role="button">Altro...<i class="mhs mts arrow img sp_QmW7P-llck- sx_577d40"></i></a><span class="uiMorePagerLoader pam uiBoxLightblue"><span class="img _55ym _55yq _55yo _3-8h" aria-busy="true" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuetext="Caricamento..."></span></span></div>

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


def scrapefacebook(mypage):
    global TOSELECT_FB
    allhtml = geturl(mypage)
    try:
        start = mypage.index("https://")
        end = mypage.index('/',start+9)
        fbdomain = mypage[start:end]
        start = allhtml.index(TOSELECT_FB)
        end = allhtml.index('"',start+1)
        thislink = allhtml[start:end]
    except:
        fbdomain = ""
        thislink = ""
    link = fbdomain + thislink
    print(link)
    newhtml = geturl(link)
    if TOSELECT_FB in newhtml:
        scrapefacebook(link)
    else:
        print("Link terminati")

if __name__ == '__main__':
    if "facebook.com" in START_PAGE:
        scrapefacebook(START_PAGE)
