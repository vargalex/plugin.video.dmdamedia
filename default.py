# -*- coding: utf-8 -*-

'''
    dmdamedia Add-on
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


import sys, xbmcgui
from resources.lib.indexers import navigator

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl


params = dict(parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

group = params.get('group')

url = params.get('url') or ""

search = params.get('search')

thumb = params.get('thumb')

banner = params.get('banner')

plot = params.get('plot')

evad = params.get('evad')

sorozatkod = params.get('sorozatkod')

if action == None:
    navigator.navigator().root()

elif action == 'categories':
    navigator.navigator().getCategories()

elif action == 'actors':
    navigator.navigator().getActors()

elif action == 'items':
    navigator.navigator().getItems(url)

elif action == 'movie':
    navigator.navigator().getMovie(url, evad, sorozatkod)

elif action == 'playmovie':
    navigator.navigator().playmovie(url)

elif action == 'search':
    navigator.navigator().doSearch()

elif action == 'deletesearchhistory':
    navigator.navigator().deleteSearchHistory(url)

elif action == 'basesearch':
    navigator.navigator().getSearches()

elif action == 'searchfortext':
    navigator.navigator().getSearchedItems(search)

elif action == 'logout':
    navigator.navigator().logout()

elif action == 'inputStreamSettings':
    import xbmcaddon
    xbmcaddon.Addon(id='inputstream.adaptive').openSettings()