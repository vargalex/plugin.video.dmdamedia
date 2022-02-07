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
from resources.lib.modules import client
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

allCategories = {
    'Akció': ['akcio', 'akció'],
    'Animációs': ['animacio', 'animacios', 'animácios', 'animációs'],
    'Bűnügyi': ['bunugyi'],
    'Csajos': ['csajos'],
    'Családi': ['csalad', 'csaladi', 'családi'],
    'Dráma': ['darma', 'drama', 'dráma'],
    'Dokumentum': ['dokumentum', 'dokumetum'],
    'Életrajzi': ['eletarjzi', 'eletrajzi'],
    'Fantasy': ['fanatasy', 'fantasy', 'fatasy'],
    'Háborús': ['haborus'],
    'Horror': ['horror'],
    'Ismeretterjesztő': ['ismeretterjeszto'],
    'Kaland': ['kaland'],
    'Krimi': ['krimi'],
    'Mese': ['mese'],
    'Minisorozat': ['minisorozat'],
    'Misztikus': ['mis', 'misztiks', 'misztikus'],
    'Musical': ['musical'],
    'Orvosos': ['orvosos'],
    'Politikai': ['politikai'],
    'Romantikus': ['romantikus', 'romatikus'],
    'Sci-fi': ['scifi'],
    'Sport': ['sport'],
    'Thriller': ['thriller'],
    'Történelmi': ['tortenelemi', 'tortenelmi', 'trotenelmi', 'törtenelmi'],
    'Vígjáték': ['vigajtek', 'vigjatek'],
    'Western': ['western'],
    'Zene': ['zene'],
    'Zsaru': ['zsaru']
    }

def getCategoryKeyByValue(val):
    for key, value in allCategories.items():
        if val in value:
            return key
    return val

def isInCategory(group, classes):
    if group == "mind":
        return True
    else:
        if group in allCategories:
            for value in allCategories[group]:
                if value in classes:
                    return True
        else:
            if group in classes:
                return True
    return False

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")

    def root(self):
        mainMenu = {'film': 'Filmek', '': 'Sorozatok'}
        for menuItem in sorted(mainMenu, reverse=True):
            self.addDirectoryItem(mainMenu[menuItem], 'categories&url=%s' % menuItem, '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self, url):
        url = "" if url == None else url
        self.addDirectoryItem('Keresés', 'basesearch&url=%s&group=mind' % url, '', 'DefaultFolder.png')
        self.addDirectoryItem('Mind', 'items&url=%s&group=mind' % url, '', 'DefaultFolder.png')
        url_content = client.request('%s/%s' % (base_url, url))
        center = client.parseDOM(url_content, 'div', attrs={'class': 'center'})[0]
        wraps = client.parseDOM(center, 'div', attrs={'class': 'wrap'})
        categories = []
        for wrap in wraps:
            topDivClass = client.parseDOM(wrap, 'div', ret='class')[0].replace(',', '')
            for cat in topDivClass.split(' '):
                if cat != 'topseries' and cat != 'vege' and len(cat.replace(' ', ''))>0:
                    if getCategoryKeyByValue(cat) not in categories:
                        categories.append(getCategoryKeyByValue(cat))
        categories.sort(key=locale.strxfrm)
        for cat in categories:
            self.addDirectoryItem(cat, 'items&url=%s&group=%s' % (url, cat), '', 'DefaultFolder.png')
        self.endDirectory()

    def getSearches(self, url, group):
        url = "" if url == None else url
        self.addDirectoryItem('Új keresés', 'search&url=%s&group=%s' % (url, group), '', 'DefaultFolder.png')
        try:
            file = open("%s%s" % (self.searchFileName, url), "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open("%s%s" % (self.searchFileName, url), "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                self.addDirectoryItem(item, 'items&url=%s&group=%s&search=%s' % (url, group, quote_plus(item)), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('Keresési előzmények törlése', 'deletesearchhistory&url=%s' % url, '', 'DefaultFolder.png') 
        except:
            pass   
        self.endDirectory()

    def deleteSearchHistory(self, url):
        url = "" if url == None else url
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
        center = py2_encode(client.parseDOM(url_content, 'div', attrs={'class': 'center'})[0])
        start = time.time()
        wraps = client.parseDOM(center, 'div', attrs={'class': 'wrap'})
        for wrap in wraps:
            topDivClass = client.parseDOM(wrap, 'div', ret='class')[0].replace(',', '')
            if isInCategory(group, topDivClass):
                itemUrl = client.parseDOM(wrap, 'a', ret='href')[0]
                thumb = client.parseDOM(wrap, 'img', ret='data-src')[0]
                title = client.parseDOM(wrap, 'h1')[0]
                data_cim = client.parseDOM(wrap, 'div', ret='data-cim')[0].lower()
                data_cim_en = client.parseDOM(wrap, 'div', ret='data-cim_en')[0].lower()
                isOK = True
                if search != None:
                    lowerTitle = title.lower()
                    if search not in lowerTitle and search not in data_cim and search not in data_cim_en:
                        isOK = False
                if isOK:
                    self.addDirectoryItem(title, '%s&url=%s&thumb=%s' % ("movie" if url != "" else "series", itemUrl, thumb), "%s/%s" % (base_url, thumb), 'DefaultMovies.png' if url != "" else 'DefaultTVShows.png')
        """
        movies = center.replace('</div>', '</div>\n')
        for line in movies.splitlines():
            matches = re.search(r'^<div class="wrap"><div class="([^"]*)%s([^"]*)"(.*)data-cim="([^"]*)"(.*)href="([^"]*)"(.*)data-src="([^"]*)(.*)$' % (group if group != "mind" else " "), line.strip())
            if matches:
                isOK = True
                if search != None:
                    lowerLine = line.lower()
                    if search not in lowerLine:
                        isOK = False
                if isOK:
                    cnt+=1
                    self.addDirectoryItem(matches.group(4), '%s&url=%s&thumb=%s' % ("movie" if url != "" else "series", matches.group(6), quote_plus(matches.group(8))), "%s%s" % (base_url, matches.group(8)), 'DefaultMovies.png' if url != "" else 'DefaultTVShows.png')
        """
        self.endDirectory('movies' if url != "" else 'tvshows')

    def getSeries(self, url, thumb):
        url_content = client.request("%s%s" % (base_url, url))
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        plot = py2_encode(client.parseDOM(info, 'p')[0]).strip()
        tab = client.parseDOM(info, 'div', attrs={'class': 'tab'})[0]
        matches = re.search(r'^(.*)<div class="tags">Epizódhossz:</div><p>([0-9]*) Perc(.*)$', tab, re.S)
        if matches:
            duration = int(matches.group(2).strip())*60

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
        matches = re.search(r'^(.*)<div class="tags">Epizódhossz:</div><p>([0-9]*) Perc(.*)$', tab, re.S)
        if matches:
            duration = int(matches.group(2).strip())*60

        controls = client.parseDOM(url_content, 'div', attrs={'class': 'controls'})[0]
        episodes = client.parseDOM(controls, 'div', attrs={'class': 'reszek'})[0].replace('</a>', '</a>\n')
        for episode in episodes.splitlines():
            matches = re.search(r'(.*)<a(.*)class="(.*)episode"(.*)href="(.*)">(.*)</a>$', episode.strip())
            if matches:
                self.addDirectoryItem(u'%s. rész %s' % (matches.group(6), "| [COLOR limegreen]Feliratos[/COLOR]" if "sub " in matches.group(3) else ""), 'movie&url=%s&thumb=%s&plot=%s' % (quote_plus(matches.group(5)), quote_plus(thumb), quote_plus(plot)), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': duration})
        self.endDirectory('episodes')

    def getMovie(self, url, thumb):
        url_content = client.request(url)
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        plot = py2_encode(client.parseDOM(info, 'p')[0]).strip()
        tab = client.parseDOM(info, 'div', attrs={'class': 'tab'})[0]
        matches = re.search(r'^(.*)<div class="tags">(.*)hossz:</div><p>([0-9]*) Perc(.*)$', tab, re.S)
        if matches:
            duration = int(matches.group(3).strip())*60
        servers = client.parseDOM(url_content, 'div', attrs={'class': 'servers'})[0]
        lista = client.parseDOM(servers, 'div', attrs={'class': 'lista'})[0]
        sources = lista.replace("<a>", "\n<a>").replace("</a>", "</a>\n")
        sourceCnt = 0
        for source in sources.splitlines():
            matches = re.search(r'^<a(.*)href="(.*)">(.*)</a>$', source.strip())
            if matches:
                sourceCnt+=1
                self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), matches.group(3)), 'playmovie&url=%s%s' % (url, quote_plus(matches.group(2))), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
        self.endDirectory('movies')

    def playmovie(self, url):
        url_content = client.request(url)
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
