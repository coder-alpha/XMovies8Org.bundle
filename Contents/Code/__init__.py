######################################################################################
#
#	XMovies8.org
#
######################################################################################

import common
import updater
import re
import urllib2
import json

global_request_timeout = 10

GOOD_RESPONSE_CODES = ['200','206']

TITLE = common.TITLE
PREFIX = common.PREFIX
ART = "art-default.jpg"
ICON = "icon-xmovies8org.png"
ICON_LIST = "icon-list.png"
ICON_COVER = "icon-cover.png"
ICON_SEARCH = "icon-search.png"
ICON_SEARCH_QUE = "icon-search-queue.png"
ICON_NEXT = "icon-next.png"
ICON_MOVIES = "icon-movies.png"
ICON_MOVIES_FILTER = "icon-filter.png"
ICON_MOVIES_GENRE = "icon-genre.png"
ICON_MOVIES_LATEST = "icon-latest.png"
ICON_QUEUE = "icon-bookmark.png"
ICON_UNAV = "MoviePosterUnavailable.jpg"
ICON_PREFS = "icon-prefs.png"
ICON_UPDATE = "icon-update.png"
ICON_UPDATE_NEW = "icon-update-new.png"
BASE_URL = "https://www.xmovies8.org"

######################################################################################
# Set global variables

def Start():

	ObjectContainer.title1 = TITLE
	ObjectContainer.art = R(ART)
	DirectoryObject.thumb = R(ICON_LIST)
	DirectoryObject.art = R(ART)
	VideoClipObject.thumb = R(ICON_MOVIES)
	VideoClipObject.art = R(ART)
	
	HTTP.ClearCache()
	HTTP.Headers['User-Agent'] = "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:48.0) Gecko/20100101 Firefox/48.0"
	HTTP.Headers['Referer'] = BASE_URL
	Log(common.TITLE + ' v.' + common.VERSION)

######################################################################################
# Menu hierarchy

@handler(PREFIX, TITLE, art=ART, thumb=ICON)
def MainMenu():

	oc = ObjectContainer(title2=TITLE)
	oc.add(DirectoryObject(key = Callback(ShowMenu, title = 'Movies'), title = 'Movies', thumb = R(ICON_MOVIES)))
	oc.add(DirectoryObject(key = Callback(Bookmarks, title="Bookmarks"), title = "Bookmarks", thumb = R(ICON_QUEUE)))
	oc.add(DirectoryObject(key = Callback(SearchQueueMenu, title = 'Search Queue'), title = 'Search Queue', summary='Search using saved search terms', thumb = R(ICON_SEARCH_QUE)))
	oc.add(InputDirectoryObject(key = Callback(Search, page_count=1), title='Search', summary='Search Movies', prompt='Search for...', thumb=R(ICON_SEARCH)))
	try:
		if updater.update_available()[0]:
			oc.add(DirectoryObject(key = Callback(updater.menu, title='Update Plugin'), title = 'Update (New Available)', thumb = R(ICON_UPDATE_NEW)))
		else:
			oc.add(DirectoryObject(key = Callback(updater.menu, title='Update Plugin'), title = 'Update (Running Latest)', thumb = R(ICON_UPDATE)))
	except:
		pass
		
	return oc

######################################################################################
@route(PREFIX + "/showMenu")
def ShowMenu(title):

	oc2 = ObjectContainer(title2=title)
	oc2.add(DirectoryObject(key = Callback(SortMenu, title = 'Popular Movies', page_count = 1), title = 'Popular Movies', thumb = R(ICON_MOVIES_FILTER)))
	oc2.add(DirectoryObject(key = Callback(SortMenu, title = 'Latest Movies', page_count = 1), title = 'Latest Movies', thumb = R(ICON_MOVIES_FILTER)))
	oc2.add(DirectoryObject(key = Callback(SortMenu, title = 'Most Watched Movies', page_count = 1), title = 'Most Watched Movies', thumb = R(ICON_MOVIES_FILTER)))
	oc2.add(DirectoryObject(key = Callback(SortMenu, title = 'Filter by Genre', page_count = 1), title = 'Filter by Genre', thumb = R(ICON_MOVIES_GENRE)))
	oc2.add(DirectoryObject(key = Callback(SortMenu, title = 'Filter by Year', page_count = 1), title = 'Filter by Year', thumb = R(ICON_MOVIES_LATEST)))
	oc2.add(DirectoryObject(key = Callback(MainMenu), title = 'Main Menu', thumb = R(ICON)))

	return oc2

######################################################################################
@route(PREFIX + "/sortMenu")
def SortMenu(title, page_count):

	oc = ObjectContainer(title2 = title)
	
	if title == 'Filter by Year':
		page_data = HTML.ElementFromURL(BASE_URL)			
		elem = page_data.xpath(".//li[@class='dropdown'][1]//ul[@class='dropdown-menu multi-column']//li")
		for years in elem:
			key = years.xpath(".//text()")[0]

			oc.add(DirectoryObject(
				key = Callback(ShowCategory, title = title, page_count = page_count, key = key),
				title = key
				)
			)
	elif title == 'Filter by Genre':
		page_data = HTML.ElementFromURL(BASE_URL)			
		elem = page_data.xpath(".//li[@class='dropdown'][2]//ul[@class='dropdown-menu multi-column']//li")
		for genre in elem:
			key = genre.xpath(".//text()")[0]

			oc.add(DirectoryObject(
				key = Callback(ShowCategory, title = title, page_count = page_count, key = key),
				title = key
				)
			)
	else:
		oc = ObjectContainer(title2 = title + ' | Page ' + str(page_count))
		
		if title == 'Popular Movies':
			page_data = HTML.ElementFromURL(BASE_URL + '/popular_movies?page=%s' % page_count)
		elif title == 'Latest Movies':
			page_data = HTML.ElementFromURL(BASE_URL + '/latest_movies?page=%s' % page_count)
		elif title == 'Most Watched Movies':
			page_data = HTML.ElementFromURL(BASE_URL + '/most_watched_movies?page=%s' % page_count)	
		
		elem = page_data.xpath(".//div[@class='video_container b_10']//div[@class='cell_container']")
		
		try:
			last_page_no = page_data.xpath(".//div[@class='clearboth left']//ul//li[last()]//text()")[0]
			if last_page_no == '>>':
				last_page_no = page_count + 1
			else:
				last_page_no = int(last_page_no)
		except:
			pass
			
		for each in elem:
			url = BASE_URL + each.xpath(".//div[@class='thumb']//a//@href")[0]
			#Log("url -------- " + url)
			ttitle = each.xpath(".//div[@class='video_title']//a//text()")[0]
			#Log("ttitle -------- " + ttitle)
			thumb = "http:" + each.xpath(".//div[@class='thumb']//a//@src")[0]
			#Log("thumb -------- " + thumb)

			summary = 'Plot Summary on Movie Page'
			try:
				summary = 'Runtime : '
				summary_elems = each.xpath(".//div[@class='cell']//text()")
				for sume in summary_elems:
					if 'cdata' not in sume.lower() and sume.strip() <> '' and ttitle not in sume:
						summary = summary + sume + ' | '
				summary = (summary + ' Plot Summary on Movie Page').replace('-','').replace('| :', ':').replace(': |',':')
				#Log("summary -------- " + summary)
			except:
				pass

			oc.add(DirectoryObject(
				key = Callback(EpisodeDetail, title = ttitle, url = url, thumb = thumb, summary = summary),
				title = ttitle,
				summary = summary,
				thumb = Resource.ContentsOfURLWithFallback(url = thumb)
				)
			)
		if int(page_count) < last_page_no:
			oc.add(NextPageObject(
				key = Callback(SortMenu, title = title, page_count = int(page_count) + 1),
				title = "Next Page (" + str(int(page_count) + 1) + ") >>",
				thumb = R(ICON_NEXT)
				)
			)
		else:
			oc.add(DirectoryObject(key = Callback(ShowMenu, title = 'Movies'), title = '<< Movies', thumb = R(ICON_MOVIES)))
	
	if len(oc) == 0:
		return ObjectContainer(header=title, message='No More Videos Available')
	return oc
	

######################################################################################
# Creates page url from category and creates objects from that page

@route(PREFIX + "/showcategory")
def ShowCategory(title, page_count, key):

	oc = ObjectContainer(title2 = title + ' | ' + key + ' | Page ' + str(page_count))
	if title == 'Filter by Year':
		page_data = HTML.ElementFromURL(BASE_URL + '/' + key + '_movies?page=%s' % page_count)
	elif title == 'Filter by Genre':
		page_data = HTML.ElementFromURL(BASE_URL + '/' + key + '_movies?page=%s' % page_count)
		
	elem = page_data.xpath(".//div[@class='video_container b_10']//div[@class='cell_container']")
	
	try:
		last_page_no = page_data.xpath(".//div[@class='clearboth left']//ul//li[last()]//text()")[0]
		if last_page_no == '>>':
			last_page_no = page_count + 1
		else:
			last_page_no = int(last_page_no)
	except:
		pass
		
	for each in elem:
		url = BASE_URL + each.xpath(".//div[@class='thumb']//a//@href")[0]
		#Log("url -------- " + url)
		ttitle = each.xpath(".//div[@class='video_title']//a//text()")[0]
		#Log("ttitle -------- " + ttitle)
		thumb = "http:" + each.xpath(".//div[@class='thumb']//a//@src")[0]
		#Log("thumb -------- " + thumb)
		
		summary = 'Plot Summary on Movie Page'
		try:
			summary = 'Runtime : '
			summary_elems = each.xpath(".//div[@class='cell']//text()")
			for sume in summary_elems:
				if 'cdata' not in sume.lower() and sume.strip() <> '' and ttitle not in sume:
					summary = summary + sume + ' | '
			summary = (summary + ' Plot Summary on Movie Page').replace('-','').replace('| :', ':').replace(': |',':')
			#Log("summary -------- " + summary)
		except:
			pass

		oc.add(DirectoryObject(
			key = Callback(EpisodeDetail, title = ttitle, url = url, thumb = thumb, summary = summary),
			title = ttitle,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(url = thumb)
			)
		)
	if int(page_count) < last_page_no:
		oc.add(NextPageObject(
			key = Callback(ShowCategory, title = title, page_count = int(page_count) + 1, key = key),
			title = "Next Page (" + str(int(page_count) + 1) + ") >>",
			thumb = R(ICON_NEXT)
			)
		)
	else:
		oc.add(DirectoryObject(key = Callback(ShowMenu, title = 'Movies'), title = '<< Movies', thumb = R(ICON_MOVIES)))

	if len(oc) == 0:
		return ObjectContainer(header=title, message='No More Videos Available')
	return oc

######################################################################################

@route(PREFIX + "/episodedetail")
def EpisodeDetail(title, url, thumb, summary):

	summary = re.sub(r'[^0-9a-zA-Z \-/.,\':+&!()]', '?', summary)
	title = title.replace('–',' : ')
	title = unicode(title)
	oc = ObjectContainer(title2 = title)

	page_data = HTML.ElementFromURL(url)
	elem = page_data.xpath(".//div[preceding::div[@class='title clearboth']]//text()")
	summary = elem[0]
	
	#Test
	ref = url.split('#')[0].replace('www.','')
	vID = ref.split('v=')[1]
	#Log("vID: " + vID)
	#Log("Referer: " + ref)
	post_values = {'v': vID}
	h = {'referer': ref}
	data = JSON.ObjectFromURL('https://xmovies8.org/video_info/iframe', values=post_values, headers=h, method='POST')
	#Log(str(data))
	
	try:
		sortable_list = []
		for res, vUrl in data.items():
			vUrl = vUrl.replace('//html5player.org/embed?url=','')
			vUrl = urllib2.unquote(vUrl).decode('utf8') 
			sortable_list.append({'res': int(res),'vUrl':vUrl})
		sortable_list = sorted(sortable_list, reverse=True)
		
		for item in sortable_list:
			res = str(item['res']) + 'p'
			vUrl = str(item['vUrl'])
			
			#Log("vUrl ---------- " + vUrl)
			status = ' - [Offline]'
			if GetHttpStatus(vUrl) in GOOD_RESPONSE_CODES:
				status = ' - [Online]'
			try:
				oc.add(VideoClipObject(
					url = vUrl + '&VidRes=' + res + '&VidRes=' + title + '&VidRes=' + summary + '&VidRes=' + thumb,
					title = title + ' - ' + res + status,
					thumb = thumb,
					art = thumb,
					summary = summary
					)
				)
			except:
				pass
	except:
		pass
		
	if Check(title=title,url=url):
		oc.add(DirectoryObject(
			key = Callback(RemoveBookmark, title = title, url = url),
			title = "Remove Bookmark",
			summary = 'Removes the current movie from the Boomark que',
			thumb = R(ICON_QUEUE)
		)
	)
	else:
		oc.add(DirectoryObject(
			key = Callback(AddBookmark, title = title, url = url, summary=summary, thumb=thumb),
			title = "Bookmark Video",
			summary = 'Adds the current movie to the Boomark que',
			thumb = R(ICON_QUEUE)
		)
	)

	return oc

######################################################################################
# Loads bookmarked shows from Dict.  Titles are used as keys to store the show urls.

@route(PREFIX + "/bookmarks")
def Bookmarks(title):

	oc = ObjectContainer(title1=title)

	for each in Dict:
		longstring = Dict[each]
		
		if 'https:' in longstring and 'Key4Split' in longstring:	
			stitle = longstring.split('Key4Split')[0]
			url = longstring.split('Key4Split')[1]
			summary = longstring.split('Key4Split')[2]
			thumb = longstring.split('Key4Split')[3]

			oc.add(DirectoryObject(
				key=Callback(EpisodeDetail, title=stitle, url=url, thumb=thumb, summary=summary),
				title=stitle,
				thumb=thumb,
				summary=summary
				)
			)
				
	#add a way to clear bookmarks list
	oc.add(DirectoryObject(
		key = Callback(ClearBookmarks),
		title = "Clear Bookmarks",
		thumb = R(ICON_QUEUE),
		summary = "CAUTION! This will clear your entire bookmark list!"
		)
	)

	if len(oc) == 0:
		return ObjectContainer(header=title, message='No Bookmarked Videos Available')
	return oc

######################################################################################
# Checks a show to the bookmarks list using the title as a key for the url
@route(PREFIX + "/checkbookmark")
def Check(title, url):
	longstring = Dict[title]
	#Log("url-----------" + url)
	if longstring != None and (longstring.lower()).find(TITLE.lower()) != -1:
		return True
	return False

######################################################################################
# Adds a movie to the bookmarks list using the title as a key for the url

@route(PREFIX + "/addbookmark")
def AddBookmark(title, url, summary, thumb):
	Dict[title] = title + 'Key4Split' + url +'Key4Split'+ summary + 'Key4Split' + thumb
	Dict.Save()
	return ObjectContainer(header=title, message='This movie has been added to your bookmarks.')

######################################################################################
# Removes a movie to the bookmarks list using the title as a key for the url

@route(PREFIX + "/removebookmark")
def RemoveBookmark(title, url):
	del Dict[title]
	Dict.Save()
	return ObjectContainer(header=title, message='This movie has been removed from your bookmarks.', no_cache=True)

######################################################################################
# Clears the Dict that stores the bookmarks list

@route(PREFIX + "/clearbookmarks")
def ClearBookmarks():

	remove_list = []
	for each in Dict:
		try:
			url = Dict[each]
			if url.find(TITLE.lower()) != -1 and 'http' in url:
				remove_list.append(each)
		except:
			continue

	for bookmark in remove_list:
		try:
			del Dict[bookmark]
		except Exception as e:
			Log.Error('Error Clearing Bookmarks: %s' %str(e))
			continue

	Dict.Save()
	return ObjectContainer(header="My Bookmarks", message='Your bookmark list will be cleared soon.', no_cache=True)

######################################################################################
# Clears the Dict that stores the search list

@route(PREFIX + "/clearsearches")
def ClearSearches():

	remove_list = []
	for each in Dict:
		try:
			if each.find(TITLE.lower()) != -1 and 'MyCustomSearch' in each:
				remove_list.append(each)
		except:
			continue

	for search_term in remove_list:
		try:
			del Dict[search_term]
		except Exception as e:
			Log.Error('Error Clearing Searches: %s' %str(e))
			continue

	Dict.Save()
	return ObjectContainer(header="Search Queue", message='Your Search Queue list will be cleared soon.', no_cache=True)

####################################################################################################
@route(PREFIX + "/search")
def Search(query, page_count=1):

	Dict[TITLE.lower() +'MyCustomSearch'+query] = query
	Dict.Save()
	oc = ObjectContainer(title2='Search Results')

	page_n = ''
	try:
		furl = BASE_URL
		if page_count > 1:
			furl = BASE_URL + '/results?page=' + str(page_count)

		data = HTTP.Request(furl + '&q=%s' % String.Quote(query, usePlus=True), headers="").content
		page_data = HTML.ElementFromString(data)
		elem = page_data.xpath(".//div[@class='video_container b_10']//div[@class='cell_container']")

		for each in elem:
			url = BASE_URL + each.xpath(".//div[@class='thumb']//a//@href")[0]
			#Log("url -------- " + url)
			ttitle = each.xpath(".//div[@class='video_title']//a//text()")[0]
			#Log("ttitle -------- " + ttitle)
			thumb = "http:" + each.xpath(".//div[@class='thumb']//a//@src")[0]
			#Log("thumb -------- " + thumb)
			summary = each.xpath(".//div[@class='video_quality']//text()")[0]
			#Log("summary -------- " + summary)
			
			oc.add(DirectoryObject(
				key = Callback(EpisodeDetail, title = ttitle, url = url, thumb = thumb, summary = summary),
				title = ttitle,
				summary = summary,
				thumb = Resource.ContentsOfURLWithFallback(url = thumb)
				)
			)
	except:
		pass

	oc.add(NextPageObject(
		key = Callback(SortMenu, title = query, page_count = int(page_count) + 1),
		title = "Next Page (" + str(int(page_count) + 1) + ") >>",
		thumb = R(ICON_NEXT)
		)
	)

	if len(oc) == 1:
		return ObjectContainer(header='Search Results', message='No More Videos Available')
	return oc

####################################################################################################
@route(PREFIX + "/searchQueueMenu")
def SearchQueueMenu(title):
	oc2 = ObjectContainer(title2='Search Using Term')
	#add a way to clear bookmarks list
	oc2.add(DirectoryObject(
		key = Callback(ClearSearches),
		title = "Clear Search Queue",
		thumb = R(ICON_SEARCH),
		summary = "CAUTION! This will clear your entire search queue list!"
		)
	)
	for each in Dict:
		query = Dict[each]
		#Log("each-----------" + each)
		#Log("query-----------" + query)
		try:
			if each.find(TITLE.lower()) != -1 and 'MyCustomSearch' in each and query != 'removed':
				oc2.add(DirectoryObject(key = Callback(Search, query = query, page_count=1), title = query, thumb = R(ICON_SEARCH))
			)
		except:
			pass

	return oc2
	
####################################################################################################
# Get HTTP response code (200 == good)
@route(PREFIX + '/gethttpstatus')
def GetHttpStatus(url):
	try:
		conn = urllib2.urlopen(url, timeout = global_request_timeout)
		resp = str(conn.getcode())
	except StandardError:
		resp = '0'
	#Log(url + " : " + resp)
	return resp