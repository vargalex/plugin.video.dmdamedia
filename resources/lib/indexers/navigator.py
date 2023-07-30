# -*- coding: utf-8 -*-

'''
    dmdamedia Addon
    Copyright (C) 2020

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon, time, locale
import resolveurl as urlresolver
from resources.lib.modules import client, control
from resources.lib.modules.utils import py2_encode, py2_decode

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
else:
    import urlparse
    from urllib import quote_plus

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'https://dmdamedia.hu'

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = control.dataPath
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        self.addDirectoryItem('Mind', 'items&url=%s%s' % (base_url, ''), '', 'DefaultFolder.png')
        self.addDirectoryItem('Filmek', 'items&url=%s%s' % (base_url, '/filmek'), '', 'DefaultFolder.png')
        self.addDirectoryItem('Sorozatok', 'items&url=%s%s' % (base_url, '/sorozatok'), '', 'DefaultFolder.png')
        self.addDirectoryItem('Kategóriák', 'categories', '', 'DefaultFolder.png')
        self.addDirectoryItem('Keresés', 'basesearch', '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self):
        content = client.request(base_url)
        catList = client.parseDOM(content, "div", attrs={'id': 'catlist'})[0]
        categories = re.findall(r'<a href="([^"]+)">([^<]+)</a>', catList)
        for category in categories:
            splittedHref = category[0].split("=")
            self.addDirectoryItem(category[1], 'items&url=%s&category=%s' % (splittedHref[0], splittedHref[1]), '', 'DefaultFolder.png')
        self.endDirectory()

    def getSearches(self):
        self.addDirectoryItem('[COLOR lightgreen]Új keresés[/COLOR]', 'search', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                self.addDirectoryItem(item, 'searchfortext&search=%s' % quote_plus(item), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png') 
        except:
            pass   
        self.endDirectory()

    def deleteSearchHistory(self, url):
        url = "" if url == None else url
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def renderItems(self, url, center, filterparam):
        sorozatok = client.parseDOM(center, "div", attrs={'class': 'sorozatok'})
        for sorozat in sorozatok:
            title = py2_encode(client.parseDOM(sorozat, "h1")[0])
            link = client.parseDOM(sorozat, "a", ret="href")[0]
            link = "/%s" % link if not link.startswith("/") else link
            thumb = client.parseDOM(sorozat, "img", attrs={'class': 'posterload'}, ret="data-src")[0]
            thumb = "/%s" % thumb if not thumb.startswith("/") else thumb
            extraInfo = "" if len(client.parseDOM(sorozat, "div", attrs={'class': 'sorozat'})) == 0 else " [COLOR yellow] - sorozat[/COLOR]"
            matched = True
            if filterparam and filterparam != "mind":
                matched = len(client.parseDOM(sorozat, "div", attrs={'class': filterparam})) > 0
            if matched:
                self.addDirectoryItem("%s%s" % (title, extraInfo if filterparam == "mind" or not filterparam else ""), '%s&url=%s&thumb=%s' % ("series" if extraInfo != "" or "sorozatok" in url else "movie", link, thumb), "%s/%s" % (base_url, thumb), 'DefaultTVShows.png' if extraInfo != "" or "sorozatok" in url else 'DefaultMovies.png')

    def doSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write("%s\n" % search_text)
            file.close()
            self.getSearchedItems(search_text)

    def getSearchedItems(self, search_text):
        content = client.request("%s/%s" % (base_url, "search"), post=("search=%s" % search_text).encode("utf-8"))
        center = client.parseDOM(content, "div", attrs={'class': 'center'})[0]
        self.renderItems(base_url, center, None)
        self.endDirectory()

    def getItems(self, url, category, order, filterparam):
        content = client.request("%s%s%s" % (url, "=%s" % quote_plus(category) if category else "", order or ""))
        if order == None:
            listCont = client.parseDOM(content, "div", attrs={'class': 'list-cont'})
            if len(listCont) > 0:
                hrefs = client.parseDOM(listCont[0], "a")
                for i in range(len(hrefs)):
                    href = client.parseDOM(listCont[0], "a", ret="href")[i]
                    self.addDirectoryItem(hrefs[i], 'items&url=%s&order=%s' % (url, href), '', 'DefaultFolder.png')
                self.endDirectory()
                return
        center = client.parseDOM(content, "div", attrs={'class': 'center'})[0]
        if filterparam == None:
            filterForm = client.parseDOM(center, "form", attrs={'id': 'filterForm'})
            if len(filterForm) > 0:
                buttons = client.parseDOM(filterForm[0], "button", ret="value")
                for button in buttons:
                    name = client.parseDOM(filterForm[0], "button", attrs={'value': button})[0]
                    self.addDirectoryItem(name, 'items&url=%s&category=%s&filterparam=%s' % (url, category, button), '', 'DefaultFolder.png')
                self.endDirectory()
                return
        self.renderItems(url, center, filterparam)
        lapozo = client.parseDOM(center, "div", attrs={'class': 'lapozo'})
        if len(lapozo) > 0:
            hrefs = re.findall(r'<a class="([^"]+)" href="([^"]+)">([^<]+)</a>', lapozo[0])
            if hrefs[-1][0] == "oldal":
                nextPage = re.search(r'.*oldal=([0-9]+).*', hrefs[-1][1])[1]
                allPage = hrefs[-2][2]
                self.addDirectoryItem("[COLOR green]Következő oldal (%s/%s)[/COLOR]" % (nextPage, allPage), 'items&url=%s&order=%s' % (url, hrefs[-1][1]), '', 'DefaultFolder.png')
        self.endDirectory("movies" if "filmek" in url or "film" in filterparam else "tvshows" if "sorozatok" in url or "sorozat" in filterparam else "")

    def getSeries(self, url, thumb):
        url_content = client.request("%s%s" % (base_url, url))
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        plot = py2_encode(client.parseDOM(info, 'p')[0]).strip()
        tab = client.parseDOM(info, 'div', attrs={'class': 'tab'})[0]
        matches = re.search(r'^(.*)<div class="tags">(.*)hossz:</div>(.*)<p>([0-9]*) Perc(.*)$', tab, re.S | re.IGNORECASE)
        if matches:
            duration = int(matches.group(4).strip())*60

        season = client.parseDOM(url_content, 'div', attrs={'class': 'season'})[0]
        seasons = season.replace('</a>', '</a>\n')
        for season in seasons.splitlines():
            matches = re.search(r'^<a(.*)class="evad"(.*)href="(.*)">(.*)</a>$', season.strip())
            if matches:
                self.addDirectoryItem(u'%s. évad' % matches.group(4), 'episodes&url=%s&thumb=%s' % (quote_plus(matches.group(3)), quote_plus(thumb)), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', meta={'title': title, 'plot': plot, 'duration': duration})
        self.endDirectory('tvshows')

    def getEpisodes(self, url, thumb):
        url_content = client.request("%s%s" % (base_url, url))
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        plot = py2_encode(client.parseDOM(info, 'p')[0]).strip()
        tab = client.parseDOM(info, 'div', attrs={'class': 'tab'})[0]
        matches = re.search(r'^(.*)<div class="tags">(.*)hossz:</div>(.*)<p>([0-9]*) Perc(.*)$', tab, re.S | re.IGNORECASE)
        if matches:
            duration = int(matches.group(4).strip())*60

        controls = client.parseDOM(url_content, 'div', attrs={'class': 'controls'})[0]
        episodes = client.parseDOM(controls, 'div', attrs={'class': 'reszek'})[0].replace('</a>', '</a>\n')
        for episode in episodes.splitlines():
            matches = re.search(r'(.*)<a(.*)class="(.*)episode"(.*)href="(.*)">(.*)</a>$', episode.strip())
            if matches:
                self.addDirectoryItem(u'%s. rész %s' % (matches.group(6), "| [COLOR limegreen]Feliratos[/COLOR]" if "sub " in matches.group(3) else ""), 'movie&url=%s&thumb=%s&plot=%s' % (quote_plus(matches.group(5)), quote_plus(thumb), quote_plus(plot)), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': duration})
        self.endDirectory('episodes')

    def getMovie(self, url, thumb):
        url_content = client.request("%s%s" % (base_url, url))
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        plot = py2_encode(client.parseDOM(info, 'p')[0]).strip()
        tab = client.parseDOM(info, 'div', attrs={'class': 'tab'})[0]
        matches = re.search(r'^(.*)<div class="tags">(.*)hossz:</div><p>(.*)<span(.*)>(.*)\(([0-9]*)"(.*)', tab, re.S)
        duration = None
        if matches:
            duration = int(matches.group(6).strip())*60
        else:
            matches = re.search(r'^(.*)<div class="tags">(.*)hossz:</div><p>([0-9]*) Perc(.*)$', tab, re.S)
            if matches:
                duration = int(matches.group(3).strip())*60
        beagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'beagyazas'})[0]
        sources = re.findall(r'<a class="([^"]+)" title="([^"]+)"(.*)href="([^"]+)">([^<]+)</a>', beagyazas)
        sourceCnt = 0
        for source in sources:
            sourceCnt+=1
            self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), source[4]), 'playmovie&url=%s%s' % (url, quote_plus(source[3])), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
        self.endDirectory('movies')

    def playmovie(self, url):
        url_content = client.request("%s%s" % (base_url, url))
        filmbeagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'filmbeagyazas'})
        if len(filmbeagyazas)>0:
            filmbeagyazas = filmbeagyazas[0]
        else:
            filmbeagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'beagyazas'})[0]
        source = client.parseDOM(filmbeagyazas, 'iframe', ret='src')[0]
        xbmc.log('Dmdamedia: resolving url: %s' % source, xbmc.LOGINFO)
        try:
            direct_url = urlresolver.resolve(source)
            if direct_url:
                direct_url = py2_encode(direct_url)
        except Exception as e:
            xbmcgui.Dialog().notification(urlparse.urlparse(url).hostname, str(e))
            return
        if direct_url:
            xbmc.log('Dmdamedia: playing URL: %s' % direct_url, xbmc.LOGINFO)
            play_item = xbmcgui.ListItem(path=direct_url)
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        if thumb == '': thumb = icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append((py2_encode(context[0]), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart == None: Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if isFolder == False: item.setProperty('IsPlayable', 'true')
        if not meta == None: item.setInfo(type='Video', infoLabels = meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('',u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()

        if (keyb.isConfirmed()):
            search_text = keyb.getText()

        return search_text
