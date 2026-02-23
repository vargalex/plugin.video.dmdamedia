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
import resolveurl
from resources.lib.modules import client, control, cache
from resources.lib.modules.utils import py2_encode, py2_decode

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote_plus
else:
    import urlparse
    from urllib import quote_plus

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = control.setting('dmdamedia_base').strip()
login_url = '%s/login' % base_url
favorites_url = '%s/kedvencek' % base_url

class navigator:
    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(control.dataPath)
        self.searchFileName = os.path.join(self.base_path, "search.history")
        self.username = control.setting('username').strip()
        self.password = control.setting('password').strip()
        self.loginCookie = cache.get(self.getDmdamediaCookie, 24)
        try:
            self.downloadsubtitles = xbmcaddon.Addon().getSettingBool('downloadsubtitles')
        except:
            self.downloadsubtitles = xbmcaddon.Addon().getSetting('downloadsubtitles').lower() == 'true'

    def root(self):
        self.addDirectoryItem('Mind', 'items', '', 'DefaultFolder.png')
        self.addDirectoryItem('Filmek', 'items&url=%s' % '/filmek', '', 'DefaultFolder.png')
        self.addDirectoryItem('Sorozatok', 'items&url=%s' % '/sorozatok', '', 'DefaultFolder.png')
        self.addDirectoryItem('Színészek', 'actors', '', 'DefaultFolder.png')
        self.addDirectoryItem('Kategóriák', 'categories', '', 'DefaultFolder.png')
        if self.loginCookie:
            self.addDirectoryItem('Kedvencek', 'items&url=%s?' % favorites_url, '', 'DefaultFolder.png')
        self.addDirectoryItem('Keresés', 'basesearch', '', 'DefaultFolder.png')
        self.endDirectory()

    def getActors(self):
        content = client.request("%s/%s" % (base_url, "szineszek"), cookie=self.loginCookie)
        cards = client.parseDOM(content, "div", attrs={"class": "actor-card"})
        for card in cards:
            href = client.parseDOM(card, "a", ret="href")[0]
            name = client.parseDOM(card, "h3", attrs={"class": "actor-name"})[0]
            thumb = client.parseDOM(card, "img", attrs={"class": "posterload"}, ret="data-src")[0]
            self.addDirectoryItem(name, 'items&url=%s' % href, "%s%s" % (base_url, thumb), 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self):
        content = client.request(base_url, cookie=self.loginCookie)
        catList = client.parseDOM(content, "div", attrs={'class': 'cat-grid'})[0]
        categories = client.parseDOM(catList, "a")
        links = client.parseDOM(catList, "a", ret="href")
        for category, link in zip(categories, links):
            self.addDirectoryItem(category, 'items&url=%s' % link, '', 'DefaultFolder.png')
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

    def renderItems(self, url, movieGrid, filterparam):
        moviesContent = client.parseDOM(movieGrid, "a")
        moviesHref = client.parseDOM(movieGrid, "a", ret="href")
        for href, content in zip(moviesHref, moviesContent):
            if not href.startswith("/"):
                href = "/%s" % href
            info = client.parseDOM(content, "div", attrs={"class": "card-info"})[0]
            title = client.replaceHTMLCodes(client.parseDOM(info, 'h3', attrs={"class": "card-title"})[0])
            try:
                year = client.parseDOM(info, 'span', attrs={"class": "card-year"})[0]
            except:
                year = None
            poster = client.parseDOM(content, 'div', attrs={"class": "poster-container"})[0]
            thumb = client.parseDOM(poster, "img", attrs={'class': 'posterload'}, ret="data-src")[0]
            cardbadge = client.parseDOM(poster, "div", attrs={'class': 'card-badge.*?'})
            cardbadgeclass = client.parseDOM(poster, "div", attrs={'class': 'card-badge.*?'}, ret="class")
            extraInfo = ""
            for cb,cl in zip(cardbadge, cardbadgeclass):
                classes = cl.split()
                if "badge-imdb" not in classes:
                    extraInfo = "%s - %s" % (extraInfo, cb.strip())
            if extraInfo:
                extraInfo = "[COLOR yellow]%s[/COLOR]" % extraInfo

            #action = "series" if extraInfo != "" or ("sorozatok" in url and not re.match(r".*/[0-9]+\.evad/[0-9]+\.resz", href)) else "movie"
            action = "movie"
            self.addDirectoryItem("%s%s" % (title, extraInfo), '%s&url=%s' % (action, href), "%s/%s" % (base_url, thumb), 'DefaultTVShows.png' if action == "series" else 'DefaultMovies.png', meta={'title': title, 'year': year})

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
        content = client.request("%s/%s" % (base_url, "search"), post=("search=%s" % py2_decode(search_text)), cookie=self.loginCookie)
        center = client.parseDOM(content, "div", attrs={'class': 'center'})[0]
        movieGrid = client.parseDOM(center, "div", attrs={"class": "movie-grid"})[0]
        self.renderItems(base_url, movieGrid, None)
        self.endDirectory()

    def getItems(self, url):
        content = client.request("%s%s" % (base_url, url), cookie=self.loginCookie)
        if "oldal" not in url and "order" not in url:
            subtab = client.parseDOM(content, "div", attrs={'class': 'sub-tab-nav'})
            if len(subtab) > 0:
                hrefs = client.parseDOM(subtab[0], "a", attrs={'class': 'sub-tab-btn.*?'}, ret="href")
                items = client.parseDOM(subtab[0], "a", attrs={'class': 'sub-tab-btn.*?'})
                if len(hrefs) > 0:
                    for link, item in zip(hrefs, items):
                        self.addDirectoryItem(item, 'items&url=%s' % (link), '', 'DefaultFolder.png')
                    self.endDirectory()
                    return
        movieGrid = client.parseDOM(content, "div", attrs={"class": "movie-grid"})[0]
        self.renderItems(url, movieGrid, None)
        lapozo = client.parseDOM(content, "div", attrs={'class': 'lapozo'})
        if len(lapozo) > 0:
            hrefs = client.parseDOM(lapozo[0], "a", attrs={"class": "oldal.*?"}, ret="href")
            try:
                nextPage = re.search(r'.*oldal/([0-9]+)', hrefs[-1]).group(1)
                allPage = re.search(r'.*oldal/([0-9]+)', hrefs[-2]).group(1)
            except:
                nextPage = re.search(r'.*&oldal=([0-9]+)', hrefs[-1]).group(1)
                allPage = re.search(r'.*&oldal=([0-9]+)', hrefs[-2]).group(1)
            self.addDirectoryItem(u'[COLOR lightgreen]K\u00F6vetkez\u0151 oldal (%s/%s)[/COLOR]' % (nextPage, allPage), 'items&url=%s' % quote_plus(hrefs[-1]), '', 'DefaultFolder.png')
        self.endDirectory()

    def getMovie(self, url, evad=None, sorozatKod=None):
        url_content = client.request("%s%s" % (base_url, url), cookie=self.loginCookie)
        container = client.parseDOM(url_content, 'div', attrs={'class': 'hero-container'})[0]
        info = client.parseDOM(container, "div", attrs={"class": "hero-info"})
        try:
            title = client.replaceHTMLCodes(client.parseDOM(info, 'h1', attrs={"class": "hero-title"})[0])
        except:
            title = client.replaceHTMLCodes(client.parseDOM(info, "a", attrs={"class": "hero-title"})[0])
        match = re.search(r"(.*?)<", title)
        if match:
            title = match.group(1)
        title = py2_encode(title).strip()
        thumb = client.parseDOM(container, "div", attrs={"class": "hero-poster-wrapper"})[0]
        thumb = client.parseDOM(thumb, "img", ret="src")[0]
        plot = client.parseDOM(info, "div", attrs={"class": "hero-desc"})[0]
        match = re.search(r"(.*)<br>.*", plot, re.S)
        if match:
            plot = match.group(1)
        meta = client.parseDOM(info, "div", attrs={"class": "hero-meta"})[0]
        spans = client.parseDOM(meta, "span", attrs={"class": "meta-badge"})
        duration = None
        year = None
        for span in spans:
            match = re.fullmatch(r"([0-9]+)ó[ ]*([0-9]+)p", span)
            if match:
                duration = int(match.group(1))*60*60 + int(match.group(2))*60
            match  = re.fullmatch(r"[0-9]{4}", span)
            year = None
            if match:
                year = match.group(0)
        providerList = client.parseDOM(url_content, "div", attrs={"class": "provider-list"})
        if providerList:
            hrefs = client.parseDOM(providerList, "a", attrs={"class": "provider-btn.*?"}, ret="href")
            providers = client.parseDOM(providerList, "a", attrs={"class": "provider-btn.*?"})
            sourceCnt = 0
            for provider, href in zip(providers, hrefs):
                sourceCnt+=1
                if "BEKÜLDÉS" not in provider:
                    self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), provider), 'playmovie&url=%s' % quote_plus("%s%s" % (url, href)), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
        else:
            if not evad:
                seasonsSection = client.parseDOM(url_content, "div", attrs={"class": "seasons-section"})
                if seasonsSection:
                    seasonList = client.parseDOM(seasonsSection[0], "div", attrs={"class": "season-list"})[0]
                    params = client.parseDOM(seasonList, "a", attrs={"class": "season-btn.*?"}, ret="onclick")
                    seasons = client.parseDOM(seasonList, "a", attrs={"class": "season-btn.*?"})
                    for param, season in zip(params, seasons):
                        evadnum = client.parseDOM(season, "span", attrs={"class": "evad-num"})[0]
                        evadtext = client.parseDOM(season, "span", attrs={"class": "evad-text"})[0]
                        match=re.search(r"loadSeason\(([0-9]+), '(.*?)'.*", param)
                        if match:
                            s=match.group(1)
                            code=match.group(2)
                            self.addDirectoryItem('%s %s' % (evadnum, evadtext), 'movie&url=%s&evad=%s&sorozatkod=%s' % (url, s, code), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
            else:
                content = client.request("%s/epizod_betoltes" % base_url, post="evad=%s&sorozatKod=%s" % (evad, sorozatKod))
                hrefs = client.parseDOM(content, "a", attrs={"class": "episode-btn"}, ret="href")
                episodes = client.parseDOM(content, "a", attrs={"class": "episode-btn"})
                for href, episode in zip(hrefs, episodes):
                    episodenum = client.parseDOM(episode, "span", attrs={"class": "ep-num"})[0]
                    episodetext = client.parseDOM(episode, "span", attrs={"class": "ep-text"})[0]
                    self.addDirectoryItem('%s %s' % (episodenum, episodetext), 'movie&url=%s' % href, "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=True, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
        self.endDirectory('movies')

    def playmovie(self, url):
        url_content = client.request("%s%s" % (base_url, url), cookie = self.loginCookie)
        source = client.parseDOM(url_content, 'iframe', ret='src')[0]
        if any(x in source for x in ["streamwish", "filemoon", "embedwish"]):
            source = "%s$$%s" % (source, base_url)
        xbmc.log('Dmdamedia: resolving url %s with ResolveURL' % source, xbmc.LOGINFO)
        direct_url = None
        hmf = resolveurl.HostedMediaFile(source, subs=self.downloadsubtitles)
        subtitles = None
        if hmf:
            try:
                resp = hmf.resolve()
            except resolveurl.resolver.ResolverError as e:
                xbmc.log('Dmdamedia: ResolveURL error: %s' % repr(e), xbmc.LOGINFO)
                xbmcgui.Dialog().notification("URL feloldás hiba", "URL feloldása sikertelen a %s host-on" % urlparse.urlparse(source).hostname)
                return
            if self.downloadsubtitles:
                direct_url = resp.get('url')
            else:
                direct_url = resp
            xbmc.log('Dmdamedia: ResolveURL resolved URL: %s' % direct_url, xbmc.LOGINFO)
            direct_url = py2_encode(direct_url)
            if self.downloadsubtitles:
                subtitles = resp.get('subs')
            play_item = xbmcgui.ListItem(path=direct_url)
            if 'm3u8' in direct_url and control.setting('useisa').lower() == "true":
                from inputstreamhelper import Helper
                is_helper = Helper('hls')
                if is_helper.check_inputstream():
                    if sys.version_info < (3, 0):  # if python version < 3 is safe to assume we are running on Kodi 18
                        play_item.setProperty('inputstreamaddon', 'inputstream.adaptive')   # compatible with Kodi 18 API
                    else:
                        play_item.setProperty('inputstream', 'inputstream.adaptive')  # compatible with recent builds Kodi 19 API
                    try:
                        play_item.setProperty('inputstream.adaptive.stream_headers', direct_url.split("|")[1])
                        play_item.setProperty('inputstream.adaptive.manifest_headers', direct_url.split("|")[1])
                        play_item.setProperty('inputstream.adaptive.license_key', '|%s' % direct_url.split("|")[1])
                    except:
                        pass
                    play_item.setProperty('inputstream.adaptive.manifest_type', 'hls')
            if self.downloadsubtitles:
                if subtitles:
                    errMsg = ""
                    try:
                        if not os.path.exists("%s/subtitles" % self.base_path):
                            errMsg = "Hiba a felirat könyvtár létrehozásakor!"
                            os.mkdir("%s/subtitles" % self.base_path)
                        for f in os.listdir("%s/subtitles" % self.base_path):
                            errMsg = "Hiba a korábbi feliratok törlésekor!"
                            os.remove("%s/subtitles/%s" % (self.base_path, f))
                        finalsubtitles=[]
                        errMsg = "Hiba a sorozat felirat letöltésekor!"
                        for sub in subtitles:
                            subtitle = client.request(subtitles[sub])
                            if len(subtitle) > 0:
                                errMsg = "Hiba a sorozat felirat file kiírásakor!"
                                file = safeopen(os.path.join(self.base_path, "subtitles", "%s.srt" % sub.strip()), "w")
                                file.write(subtitle)
                                file.close()
                                errMsg = "Hiba a sorozat felirat file hozzáadásakor!"
                                finalsubtitles.append(os.path.join(self.base_path, "subtitles", "%s.srt" % sub.strip()))
                            else:
                                xbmc.log("Dmdamedia: Subtitles not found in source", xbmc.LOGINFO)
                        if len(finalsubtitles)>0:
                            errMsg = "Hiba a feliratok beállításakor!"
                            play_item.setSubtitles(finalsubtitles)
                    except:
                        xbmcgui.Dialog().notification("Dmdamedia hiba", errMsg, xbmcgui.NOTIFICATION_ERROR)
                        xbmc.log("Hiba a %s URL-hez tartozó felirat letöltésekor, hiba: %s" % (py2_encode(source), py2_encode(errMsg)), xbmc.LOGERROR)
                else:
                    xbmc.log("Dmdamedia: ResolveURL did not find any subtitles", xbmc.LOGINFO)
            xbmc.log('Dmdamedia: playing URL: %s' % direct_url, xbmc.LOGINFO)
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)
        else:
            xbmc.log('Dmdamedia: ResolveURL could not resolve url: %s' % source, xbmc.LOGINFO)
            xbmcgui.Dialog().notification("URL feloldás hiba", "URL feloldása sikertelen a %s host-on" % urlparse.urlparse(source).hostname)

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

    def getDmdamediaCookie(self):
        if (self.username and self.password) != "":
            loginCookie = client.request(login_url, post='felhasznalonev=%s&jelszo=%s&submit=' % (quote_plus(self.username), quote_plus(self.password)), output="cookie")
            if loginCookie:
                url_content = client.request(favorites_url, cookie=loginCookie)
                if url_content and 'Kijelentkez' in url_content:
                    control.setSetting('loggedin', 'true')
                    return loginCookie
                else:
                    xbmcgui.Dialog().ok("Bejelentkezési hiba!", "Hiba a bejelentkezés során! Hibás felhasználó név, vagy jelszó?")
            else:
                xbmcgui.Dialog().ok("Bejelentkezési hiba!", "Váratlan hiba a bejelentkezés során!")
        else:
            if control.setting('firstopen').lower() == "true":
                xbmcgui.Dialog().ok("Regisztráció", "Figyelem! A [COLOR lightskyblue]%s[/COLOR] oldal bejelentkezés nélkül csak egyetlen forrást tesz elérhetővé, ezért ajánlott a regisztráció és a kiegészítőben a bejelentkezési adatok megadása!" % base_url)
                control.setSetting('firstopen', 'false')
        control.setSetting('loggedin', 'false')
        return

    def logout(self):
        dialog = xbmcgui.Dialog()
        if 1 == dialog.yesno('Dmdamedia kijelentkezés', 'Valóban ki szeretnél jelentkezni?', '', ''):
            control.setSetting('username', '')
            control.setSetting('password', '')
            control.setSetting('loggedin', 'false')
            dialog.ok('Dmdamedia', u'Sikeresen kijelentkeztél.\nAz adataid törlésre kerültek a kiegészítőből.')
