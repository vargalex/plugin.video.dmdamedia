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


import urlparse,sys, xbmcgui

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

group = params.get('group')

url = params.get('url')

search = params.get('search')

thumb = params.get('thumb')

banner = params.get('banner')

plot = params.get('plot')

if action == None:
    from resources.lib.indexers import navigator
    navigator.navigator().root()

elif action == 'categories':
    from resources.lib.indexers import navigator
    navigator.navigator().getCategories(url)


elif action == 'items':
    from resources.lib.indexers import navigator
    navigator.navigator().getItems(url, group, search)

elif action == 'movie':
    from resources.lib.indexers import navigator
    navigator.navigator().getMovie(url, thumb)

elif action == 'playmovie':
    from resources.lib.indexers import navigator
    navigator.navigator().playmovie(url)

elif action == 'search':
    from resources.lib.indexers import navigator
    navigator.navigator().doSearch(url, group)

elif action == 'series':
    from resources.lib.indexers import navigator
    navigator.navigator().getSeries(url, thumb)

elif action == 'episodes':
    from resources.lib.indexers import navigator
    navigator.navigator().getEpisodes(url, thumb)

elif action == 'episode':
    from resources.lib.indexers import navigator
    navigator.navigator().getEpisode(url, thumb, banner, plot)
