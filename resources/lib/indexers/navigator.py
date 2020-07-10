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


import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon,urllib,urlparse,base64,time, locale
import urlresolver
from resources.lib.modules import client

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'aHR0cHM6Ly9kbWRhbWVkaWEuaHU='.decode('base64')

class navigator:
    def __init__(self):
        locale.setlocale(locale.LC_ALL, "")
        self.base_path = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile'))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        mainMenu = {'filmek': 'Filmek', '': 'Sorozatok'}
        for menuItem in sorted(mainMenu, reverse=True):
            self.addDirectoryItem(mainMenu[menuItem], 'categories&url=%s' % menuItem, '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self, url):
        url = "" if url == None else url
        self.addDirectoryItem('Keresés', 'basesearch&url=%s&group=mind' % url, '', 'DefaultFolder.png')
        url_content = client.request('%s/%s' % (base_url, url))
        catSearch=client.parseDOM(url_content, 'div', attrs={'class': 'categoryfilter'})[0].strip()
        rows=client.parseDOM(catSearch, 'button', attrs={'class': 'category'})
        for row in catSearch.splitlines():
            matches = re.search(r'^(.*)data-cat="(.*)">(.*)</button>$', row)
            self.addDirectoryItem(matches.group(3), 'items&url=%s&group=%s' % (url, matches.group(2)), '', 'DefaultFolder.png')
        self.endDirectory()

    def getSearches(self, url, group):
        url = "" if url == None else url
        self.addDirectoryItem('Új keresés', 'search&url=%s&group=%s' % (url, group), '', 'DefaultFolder.png')
        try:
            file = open("%s%s" % (self.searchFileName, url), "r")
            items = file.read().splitlines()
            items.sort(cmp=locale.strcoll)
            file.close()
            for item in items:
                self.addDirectoryItem(item, 'items&url=%s&group=%s&search=%s' % (url, group, urllib.quote_plus(item)), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('Keresési előzmények törlése', 'deletesearchhistory&url=%s' % url, '', 'DefaultFolder.png') 
        except:
            pass   
        self.endDirectory()

    def deleteSearchHistory(self, url):
        if os.path.exists("%s%s" % (self.searchFileName, url)):
            os.remove("%s%s" % (self.searchFileName, url))

    def doSearch(self, url, group):
        url = "" if url == None else url
        search_text = self.getSearchText()
        if search_text != '':
            if group == "mind":
                if not os.path.exists(self.base_path):
                    os.mkdir(self.base_path)
                file = open("%s%s" % (self.searchFileName, url), "a")
                file.write("%s\n" % search_text)
                file.close()
            self.getItems(url, group, search_text)

    def getItems(self, url, group, search):
        url = "" if url == None else url
        if search != None:
            search = search.lower()
        else:
            if group == "mind":
                self.addDirectoryItem('Keresés', 'basesearch&url=%s&group=mind' % url, '', 'DefaultFolder.png')
            else:
                self.addDirectoryItem('Keresés', 'search&url=%s&group=%s' % (url, group), '', 'DefaultFolder.png')
        url_content = client.request('%s/%s' % (base_url, url))
        center = client.parseDOM(url_content, 'div', attrs={'class': 'center'})[0].encode('utf-8')
        movies = center.replace('</div>', '</div>\n')
        for line in movies.splitlines():
            matches = re.search(r'^<div class="([^"]*)%s([^"]*)"(.*)data-cim="([^"]*)"(.*)href="([^"]*)"(.*)data-src="([^"]*)(.*)$' % (group if group != "mind" else " "), line.strip())
            if matches:
                isOK = True
                if search != None:
                    lowerLine = line.lower()
                    if search not in lowerLine:
                        isOK = False
                if isOK:        
                    self.addDirectoryItem(matches.group(4), '%s&url=%s&thumb=%s' % ("movie" if url != "" else "series", matches.group(6), urllib.quote_plus(matches.group(8))), "%s%s" % (base_url, matches.group(8)), 'DefaultMovies.png' if url != "" else 'DefaultTVShows.png')
        self.endDirectory('movies' if url != "" else 'tvshows')

    def getSeries(self, url, thumb):
        url_content = client.request('%s%s' %(base_url, url))
        title = client.parseDOM(url_content, 'div', attrs={'class': 'cim'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(title, 'h1')[0]).encode('utf-8').strip()
        panel = client.parseDOM(url_content, 'div', attrs={'class': 'panel'})[0]
        poster = client.parseDOM(panel, 'div', attrs={'class': 'poster'})[0]
        banner = '%s/%s' % (poster, client.parseDOM(panel, 'img', ret='src')[0])
        info = client.parseDOM(panel, 'div', attrs={'class': 'info'})[0]
        plot = client.parseDOM(info, 'div', attrs={'class': 'leiras'})[0].encode('utf-8').strip().split('<div')[0]
        time = client.parseDOM(info, 'div', attrs={'class': 'infotab-time'})[0]
        duration = int(time.replace(" Perc", "").strip())*60
        center = client.parseDOM(url_content, 'div', attrs={'class': 'center'})[0]
        seasons = client.parseDOM(center, 'div', attrs={'class': 'evadok'})[0].replace('</a>', '</a>\n')
        for season in seasons.splitlines():
            matches = re.search(r'^<a(.*)class="linktab"(.*)href="(.*)">(.*)</a>$', season.strip())
            if matches:
                self.addDirectoryItem(u'%s. évad' % matches.group(4), 'episodes&url=%s&thumb=%s' % (urllib.quote_plus(matches.group(3)), urllib.quote_plus(thumb)), "%s%s" % (base_url, thumb), 'DefaultMovies.png', meta={'title': title, 'plot': plot, 'duration': duration}, banner=banner)
        self.endDirectory('tvshows')

    def getEpisodes(self, url, thumb):
        url_content = client.request('%s%s' %(base_url, url))
        title = client.parseDOM(url_content, 'div', attrs={'class': 'cim'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(title, 'h1')[0]).encode('utf-8').strip()
        panel = client.parseDOM(url_content, 'div', attrs={'class': 'panel'})[0]
        poster = client.parseDOM(panel, 'div', attrs={'class': 'poster'})[0]
        banner = '%s/%s' % (poster, client.parseDOM(panel, 'img', ret='src')[0])
        info = client.parseDOM(panel, 'div', attrs={'class': 'info'})[0]
        plot = client.parseDOM(info, 'div', attrs={'class': 'leiras'})[0].encode('utf-8').strip().split('<div')[0]
        time = client.parseDOM(info, 'div', attrs={'class': 'infotab-time'})[0]
        duration = int(time.replace(" Perc", "").strip())*60
        center = client.parseDOM(url_content, 'div', attrs={'class': 'center'})[0]
        episodes = client.parseDOM(center, 'div', attrs={'class': 'reszek'})[0].replace('</a>', '</a>\n')
        for episode in episodes.splitlines():
            matches = re.search(r'(.*)<a(.*)class="linktab([^"]*)"(.*)href="(.*)">(.*)</a>$', episode.strip())
            if matches:
                self.addDirectoryItem(u'%s. rész %s' % (matches.group(6), "| [COLOR limegreen]Feliratos[/COLOR]" if matches.group(3) == "_feliratos" else ""), 'movie&url=%s&thumb=%s&banner=%s&plot=%s' % (urllib.quote_plus(matches.group(5)), urllib.quote_plus(thumb), urllib.quote_plus(banner), urllib.quote_plus(plot)), "%s%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': duration}, banner=banner)
        self.endDirectory('episodes')

    def getMovie(self, url, thumb):
        url_content = client.request('%s%s' %(base_url, url))
        title = client.parseDOM(url_content, 'div', attrs={'class': 'cim'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(title, 'h1')[0]).encode('utf-8').strip()
        plot = client.parseDOM(url_content, 'div', attrs={'class': 'leiras'})[0].encode('utf-8').strip().split('<div')[0]
        time = client.parseDOM(url_content, 'div', attrs={'class': 'infotab-time'})[0]
        duration = int(time.replace(" Perc", "").strip())*60
        year = client.parseDOM(url_content, 'div', attrs={'class': 'infotab-time'})
        if len(year)>1:
            year = year[1]
        else:
            year = ""
        sources = client.parseDOM(url_content, 'div', attrs={'class': 'megosztok'})[0]
        sourceCnt = 0
        for source in sources.splitlines():
            matches = re.search(r'^<a(.*)href="(.*)">(.*)</a>$', source.strip())
            if matches:
                sourceCnt+=1
                self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), matches.group(3)), 'playmovie&url=%s%s' % (url, urllib.quote_plus(matches.group(2))), "%s%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
        self.endDirectory('movies')

    def playmovie(self, url):
        url_content = client.request('%s%s' %(base_url, url))
        filmbeagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'filmbeagyazas'})
        if len(filmbeagyazas)>0:
            filmbeagyazas = filmbeagyazas[0]
        else:
            filmbeagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'beagyazas'})[0]
        source = client.parseDOM(filmbeagyazas, 'iframe', ret='src')[0]
        xbmc.log('Dmdamedia: resolving url: %s' % source, xbmc.LOGNOTICE)
        try:
            direct_url = urlresolver.resolve(source)
            if direct_url:
                direct_url = direct_url.encode('utf-8')
        except Exception as e:
            xbmcgui.Dialog().notification(urlparse.urlparse(url).hostname, e.message)
            return
        if direct_url:
            xbmc.log('Dmdamedia: playing URL: %s' % direct_url, xbmc.LOGNOTICE)
            play_item = xbmcgui.ListItem(path=direct_url)
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        if thumb == '': thumb = icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append((context[0].encode('utf-8'), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
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
