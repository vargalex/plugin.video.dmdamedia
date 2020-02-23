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


import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon,urllib,urlparse,base64,time
import urlresolver
from resources.lib.modules import client

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'aHR0cHM6Ly9kbWRhbWVkaWEuaHU='.decode('base64')

class navigator:
    def root(self):
        mainMenu = {'filmek': 'Filmek', '': 'Sorozatok'}
        for menuItem in sorted(mainMenu, reverse=True):
            self.addDirectoryItem(mainMenu[menuItem], 'categories&url=%s' % menuItem, '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self, url):
        url = "" if url == None else url
        self.addDirectoryItem('Keresés', 'search&url=%s&group=mind' % url, '', 'DefaultFolder.png')
        url_content = client.request('%s/%s' % (base_url, url))
        catSearch=client.parseDOM(url_content, 'div', attrs={'class': 'catsearch'})[0].strip()
        rows=client.parseDOM(catSearch, 'button', attrs={'class': 'category'})
        for row in catSearch.splitlines():
            matches = re.search(r'^(.*)data-cat="(.*)">(.*)</button>$', row)
            self.addDirectoryItem(matches.group(3), 'items&url=%s&group=%s' % (url, matches.group(2)), '', 'DefaultFolder.png')
        self.endDirectory()

    def doSearch(self, url, group):
        search_text = self.getSearchText()
        if search_text != '':
            self.getItems("" if url == None else url, group, search_text)

    def getItems(self, url, group, search):
        url = "" if url == None else url
        if search != None:
            search = search.lower()
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
        base = client.parseDOM(url_content, 'div', attrs={'class': 'base'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(base, 'div', attrs={'class': 'sname'})[0]).encode('utf-8').strip()
        panel = client.parseDOM(base, 'div', attrs={'class': 'panel'})[0]
        stand = client.parseDOM(base, 'div', attrs={'class': 'stand'})[0]
        center = client.parseDOM(stand, 'div', attrs={'class': 'center'})[0]
        banner = '%s/%s' % (base_url, client.parseDOM(center, 'img', ret='src')[0])
        desc = client.parseDOM(center, 'div', attrs={'class': 'desc'})[0]
        plot = client.parseDOM(desc, 'div', attrs={'class': 'text'})[0].encode('utf-8').strip().split('<div')[0]
        info = client.parseDOM(stand, 'div', attrs={'class': 'info'})[0]
        time = client.parseDOM(info, 'div', attrs={'class': 'time'})
        duration = int(client.parseDOM(time[0], 'h1')[0].replace(" Perc", "").strip())*60
        seasons = client.parseDOM(panel, 'div')[0].replace('</a>', '</a>\n')
        for season in seasons.splitlines():
            matches = re.search(r'^<a(.*)class="season"(.*)href="(.*)">(.*)</a>$', season.strip())
            if matches:
                self.addDirectoryItem(u'%s. évad' % matches.group(4), 'episodes&url=%s&thumb=%s' % (urllib.quote_plus(matches.group(3)), urllib.quote_plus(thumb)), "%s%s" % (base_url, thumb), 'DefaultMovies.png', meta={'title': title, 'plot': plot, 'duration': duration}, banner=banner)
        self.endDirectory('tvshows')

    def getEpisodes(self, url, thumb):
        url_content = client.request('%s%s' %(base_url, url))
        base = client.parseDOM(url_content, 'div', attrs={'class': 'base'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(base, 'a', attrs={'class': 'sname'})[0]).encode('utf-8').strip()
        panel = client.parseDOM(base, 'div', attrs={'class': 'panel'})[0]
        center = client.parseDOM(base, 'div', attrs={'class': 'center'})[0]
        banner = '%s/%s' % (base_url, client.parseDOM(center, 'img', ret='src')[0])
        desc = client.parseDOM(center, 'div', attrs={'class': 'desc'})[0]
        plot = client.parseDOM(desc, 'div', attrs={'class': 'text'})[0].encode('utf-8').strip().split('<div')[0]
        info = client.parseDOM(base, 'div', attrs={'class': 'info'})[0]
        time = client.parseDOM(info, 'div', attrs={'class': 'time'})
        duration = int(client.parseDOM(time[0], 'h1')[0].replace(" Perc", "").strip())*60
        episodes = client.parseDOM(panel, 'div')[0].replace('</a>', '</a>\n')
        for episode in episodes.splitlines():
            matches = re.search(r'(.*)<a(.*)class="episode([^"]*)"(.*)href="(.*)">(.*)</a>$', episode.strip())
            if matches:
                self.addDirectoryItem(u'%s. rész %s' % (matches.group(6), "| [COLOR limegreen]Feliratos[/COLOR]" if matches.group(3) == "f" else ""), 'episode&url=%s&thumb=%s&banner=%s&plot=%s' % (urllib.quote_plus(matches.group(5)), urllib.quote_plus(thumb), urllib.quote_plus(banner), urllib.quote_plus(plot)), "%s%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': duration}, banner=banner)
        self.endDirectory('episodes')
        
    def getEpisode(self, url, thumb, banner, plot):
        url_content = client.request('%s%s' %(base_url, url))
        base = client.parseDOM(url_content, 'div', attrs={'class': 'base'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(base, 'a', attrs={'class': 'sname'})[0]).encode('utf-8').strip()
        info = client.parseDOM(base, 'div', attrs={'class': 'info'})[0]
        time = client.parseDOM(info, 'div', attrs={'class': 'time'})
        duration = int(client.parseDOM(time[0], 'h1')[0].replace(" Perc", "").strip())*60
        center = client.parseDOM(base, 'div', attrs={'class': 'center'})[0]
        sources = client.parseDOM(center, 'div', attrs={'class': 'video'})[0].encode('utf-8') #.replace('</a>', '</a>\n')
        sources = re.search(r'^(.*)<br>(.*)$', sources, re.MULTILINE).group(1).replace('</a>', '</a>\n')
        if client.parseDOM(info, 'div', attrs={'class': 'textf'}):
            feliratos = "| [COLOR limegreen]Feliratos[/COLOR]"
        else:
            feliratos = ""
        sourceCnt = 0
        for source in sources.splitlines():
            matches = re.search(r'^<a(.*)href="(.*)">(.*)</a>$', source.strip())
            if matches:
                sourceCnt+=1
                self.addDirectoryItem('%s | [B]%s[/B]%s' % (format(sourceCnt, '02'), matches.group(3), feliratos), 'playmovie&url=%s%s' % (url, urllib.quote_plus(matches.group(2))), "%s%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner=banner)
        self.endDirectory('episodes')

    def getMovie(self, url, thumb):
        url_content = client.request('%s%s' %(base_url, url))
        base = client.parseDOM(url_content, 'div', attrs={'class': 'base'})[0]
        title = client.replaceHTMLCodes(client.parseDOM(base, 'div', attrs={'class': 'sname'})[0]).encode('utf-8').strip()
        panel = client.parseDOM(base, 'div', attrs={'class': 'panel'})[0]
        center = client.parseDOM(panel, 'div', attrs={'class': 'center'})[0]
        banner = '%s/%s' % (base_url, client.parseDOM(center, 'img', ret='src')[0])
        desc = client.parseDOM(center, 'div', attrs={'class': 'desc'})[0]
        plot = client.parseDOM(desc, 'div', attrs={'class': 'text'})[0].encode('utf-8').strip().split('<div')[0]
        stand = client.parseDOM(base, 'div', attrs={'class': 'stand'})[0]
        info = client.parseDOM(stand, 'div', attrs={'class': 'info'})[0]
        time = client.parseDOM(info, 'div', attrs={'class': 'time'})
        duration = int(client.parseDOM(time[0], 'h1')[0].replace(" Perc", "").strip())*60
        year = client.parseDOM(time[1], 'h1')[0].strip()
        genre = client.parseDOM(time[2], 'h1')[0].strip()
        filmalt = client.parseDOM(stand, 'div', attrs={'class': 'filmalt'})[0]
        sources = client.parseDOM(filmalt, 'div', attrs={'class': 'video'})[0].replace('</a>', '</a>\n')
        sourceCnt = 0
        for source in sources.splitlines():
            matches = re.search(r'^<a(.*)href="(.*)">(.*)</a>$', source.strip())
            if matches:
                sourceCnt+=1
                self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), matches.group(3)), 'playmovie&url=%s%s' % (url, urllib.quote_plus(matches.group(2))), "%s%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner=banner)
        self.endDirectory('movies')

    def playmovie(self, url):
        url_content = client.request('%s%s' %(base_url, url))
        base = client.parseDOM(url_content, 'div', attrs={'class': 'base'})[0]
        #stand = client.parseDOM(base, 'div', attrs={'class': 'stand'})[0]
        #filmalt = client.parseDOM(stand, 'div', attrs={'class': 'filmalt'})[0]
        video = client.parseDOM(base, 'div', attrs={'class': 'video'})[0]
        source = client.parseDOM(video, 'iframe', ret='src')[0]
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