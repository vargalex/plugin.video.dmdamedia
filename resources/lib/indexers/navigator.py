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

base_url = 'https://dmda.media'
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
        self.addDirectoryItem('Mind', 'items&url=%s%s' % (base_url, ''), '', 'DefaultFolder.png')
        self.addDirectoryItem('Filmek', 'items&url=%s%s' % (base_url, '/filmek'), '', 'DefaultFolder.png')
        self.addDirectoryItem('Sorozatok', 'items&url=%s%s' % (base_url, '/sorozatok'), '', 'DefaultFolder.png')
        self.addDirectoryItem('Kategóriák', 'categories', '', 'DefaultFolder.png')
        if self.loginCookie:
            self.addDirectoryItem('Kedvencek', 'items&url=%s?' % favorites_url, '', 'DefaultFolder.png')
        self.addDirectoryItem('Keresés', 'basesearch', '', 'DefaultFolder.png')
        self.endDirectory()

    def getCategories(self):
        content = client.request(base_url, cookie=self.loginCookie)
        catList = client.parseDOM(content, "div", attrs={'id': 'catlist'})[0]
        categories = re.findall(r'<a href="([^"]+)">([^<]+)</a>', catList)
        for category in categories:
            splittedHref = category[0].split("=")
            self.addDirectoryItem(category[1], 'items&url=%s' % category[0], '', 'DefaultFolder.png')
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
            title = py2_encode(client.parseDOM(sorozat, "h1")[0]).strip()
            if "<a" in title:
                title = title[:title.find("<a")].strip()
            link = client.parseDOM(sorozat, "a", ret="href")[0]
            link = "/%s" % link if not link.startswith("/") else link
            thumb = client.parseDOM(sorozat, "img", attrs={'class': 'posterload'}, ret="data-src")[0]
            thumb = "/%s" % thumb if not thumb.startswith("/") else thumb
            extraInfo = "" if len(client.parseDOM(sorozat, "div", attrs={'class': 'sorozat'})) == 0 else " [COLOR yellow] - sorozat[/COLOR]"
            matched = True
            if filterparam and filterparam != "mind":
                matched = len(client.parseDOM(sorozat, "div", attrs={'class': filterparam})) > 0
            if matched:
                action = "series" if extraInfo != "" or ("sorozatok" in url and not re.match(r".*/[0-9]+\.evad/[0-9]+\.resz", link)) else "movie"
                self.addDirectoryItem("%s%s" % (title, extraInfo if not filterparam or filterparam == "mind" else ""), '%s&url=%s&thumb=%s' % (action, link, thumb), "%s/%s" % (base_url, thumb), 'DefaultTVShows.png' if action == "series" else 'DefaultMovies.png')

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
        self.renderItems(base_url, center, None)
        self.endDirectory()

    def getItems(self, url, order, filterparam):
        content = client.request("%s" % url, cookie=self.loginCookie)
        if order == None:
            listCont = client.parseDOM(content, "div", attrs={'class': 'list-cont'})
            if len(listCont) > 0:
                hrefs = client.parseDOM(listCont[0], "a")
                for i in range(len(hrefs)):
                    href = client.parseDOM(listCont[0], "a", ret="href")[i]
                    self.addDirectoryItem(hrefs[i], 'items&url=%s&order=%s' % (href, href), '', 'DefaultFolder.png')
                self.endDirectory()
                return
        center = client.parseDOM(content, "div", attrs={'class': 'center'})[0]
        if filterparam == None:
            filterForm = client.parseDOM(center, "form", attrs={'id': 'filterForm'})
            if len(filterForm) > 0:
                buttons = client.parseDOM(filterForm[0], "button", ret="value")
                for button in buttons:
                    name = client.parseDOM(filterForm[0], "button", attrs={'value': button})[0]
                    self.addDirectoryItem(name, 'items&url=%s&filterparam=%s' % (url, button), '', 'DefaultFolder.png')
                self.endDirectory()
                return
        self.renderItems(url, center, filterparam)
        lapozo = client.parseDOM(content, "div", attrs={'class': 'lapozo'})
        if len(lapozo) > 0:
            hrefs = re.findall(r'<a class="([^"]+)" href="([^"]+)">([^<]+)</a>', lapozo[0])
            if hrefs[-1][0] == "oldal":
                nextPage = re.search(r'.*oldal/([0-9]+).*', hrefs[-1][1]).group(1)
                allPage = hrefs[-2][2]
                self.addDirectoryItem(u'[COLOR lightgreen]K\u00F6vetkez\u0151 oldal (%s/%s)[/COLOR]' % (nextPage, allPage), 'items&url=%s&order=%s' % (quote_plus(hrefs[-1][1]), quote_plus(hrefs[-1][1])), '', 'DefaultFolder.png')
        self.endDirectory("movies" if "filmek" in url or (filterparam and "film" in filterparam) else "tvshows" if "sorozatok" in url or (filterparam and "sorozat" in filterparam) else "")

    def getSeries(self, url, thumb):
        url_content = client.request("%s%s" % (base_url, url), cookie=self.loginCookie)
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        if "<a" in title:
            title = title[:title.find("<a")].strip()
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
        url_content = client.request("%s%s" % (base_url, url), cookie=self.loginCookie)
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        if "<a" in title:
            title = title[:title.find("<a")].strip()
        if "</a" in title:
            title = title[:title.find("</a")].strip()
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
        url_content = client.request("%s%s" % (base_url, url), cookie=self.loginCookie)
        info = client.parseDOM(url_content, 'div', attrs={'class': 'info'})[0]
        title = py2_encode(client.replaceHTMLCodes(client.parseDOM(info, 'h1')[0])).strip()
        if "<a" in title:
            title = title[:title.find("<a")].strip()
        if "</a" in title:
            title = title[:title.find("</a")].strip()
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
        sources = re.findall(r'<a class="([^"]+)" title="([^"]+)"(.*?)href="([^"]+)">([^<]+)</a>', beagyazas)
        sourceCnt = 0
        for source in sources:
            sourceCnt+=1
            self.addDirectoryItem('%s | [B]%s[/B]' % (format(sourceCnt, '02'), source[4]), 'playmovie&url=%s' % quote_plus(source[3]), "%s/%s" % (base_url, thumb), 'DefaultMovies.png', isFolder=False, meta={'title': title, 'plot': plot, 'duration': duration}, banner="")
        self.endDirectory('movies')

    def playmovie(self, url):
        url_content = client.request(url, cookie = self.loginCookie)
        filmbeagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'filmbeagyazas'})
        if len(filmbeagyazas)>0:
            filmbeagyazas = filmbeagyazas[0]
        else:
            filmbeagyazas = client.parseDOM(url_content, 'div', attrs={'class': 'beagyazas'})[0]
        source = client.parseDOM(filmbeagyazas, 'iframe', ret='src')[0]
        if any(x in source for x in ["streamwish", "filemoon", "embedwish"]):
            source = "%s$$%s" % (source, base_url)
        xbmc.log('Dmdamedia: resolving url %s with ResolveURL' % source, xbmc.LOGINFO)
        direct_url = None
        hmf = resolveurl.HostedMediaFile(source, subs=self.downloadsubtitles)
        subtitles = None
        if hmf:
            resp = hmf.resolve()
            if self.downloadsubtitles:
                direct_url = resp.get('url')
            else:
                direct_url = resp
            xbmc.log('Dmdamedia: ResolveURL resolved URL: %s' % direct_url, xbmc.LOGINFO)
            direct_url = py2_encode(direct_url)
            if self.downloadsubtitles:
                subtitles = resp.get('subs')
            play_item = xbmcgui.ListItem(path=direct_url)
            if 'm3u8' in direct_url:
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
            xbmc.log('Dmdamedia: ResolveURL could not resolve url: %s' % src, xbmc.LOGINFO)
            xbmcgui.Dialog().notification("URL feloldás hiba", "URL feloldása sikertelen a %s host-on" % urlparse.urlparse(src).hostname)

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
