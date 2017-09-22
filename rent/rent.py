# coding: UTF8
from urllib2 import urlopen
import requests
from BeautifulSoup import BeautifulSoup
import chardet
import re
import math
import sys
import csv
import codecs
import threading
import time
import logging
import numpy as np
import Queue
#logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()
enc = 'UTF8'
reload(sys)
sys.setdefaultencoding(enc)
user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'
headers = {'User-Agent': user_agent}
session = requests.Session()
session.trust_env = False

# user config
# no boy and seasonal price
len_of_stay = 4.0 + 9.0/30.0
mode = 'season'

def cat(text):
    return '<dt>' + text + '</dt>'

def parse(url, myFile, lock):
    session = requests.Session()
    session.trust_env = False
    req = session.get(url, headers = headers)
    soup = BeautifulSoup(req.content, fromEncoding=enc)

    # find specific room info (roomate's gender, room location, room images)
    detail_right = soup.find('div',{'class':'room_detail_right'})
    if detail_right.find('a',{'class':'btn view viewGray'}) == None:
        detail_left = soup.find('div',{'class':'room_detail_left'})
        roommate = detail_left.find('div',{'class':'greatRoommate'})
        num_girls = len(roommate.findAll('li', {'class':'woman '}))
        num_boys = len(roommate.findAll('li', {'class':'man '}))

        if num_boys == 0:
            num_empty = len(roommate.findAll('li', {'class':'current '}))
            if num_empty == 0:
                num_empty = len(roommate.findAll('li',{'class':'current  last'}))
            room_details = detail_right.find('div', {'class': 'room_name'})
            room_name = room_details.h2.text

            room_location = room_details.find('span', {'class':'ellipsis'}).text
            while room_location.count(' ') > 0:
                room_location = room_location.replace(' ','')

            other_details = detail_right.find('ul', {"class":'detail_room'})
            details = []
            for item in other_details.findAll("li"):
                details.append(item.text)
            details.pop(len(details)-1)
            for element in other_details.findAll('span',{"class":"lineList"}):
                details.append(element.text)
            for element in other_details.findAll('p'):
                details.append(element.text)

            # room images
            images = "<div class=\"lidiv\">"
            imgs = detail_left.find('ul', {'class':"lof-main-wapper"}).findAll('a')
            for img in imgs:
                img = img.get('href')
                imgsrc = '<img src=\"' + img + '\">'
                link = imgsrc.replace('img src', 'a href');
                images = images + link + imgsrc +  '</a>'
            images = images + '</div>'

            # manager/agent of the house/condo
            pr_details = detail_right.find('div',{'class':'r_fixed'})
            pr_tel = pr_details.find('div',{'class':"tel"}).text
            pr_info = pr_details.find('div',{'class':'zoInfo clearfix '})
            pr_name = pr_info.find('p', {'class':'org pr'})
            if pr_name != None:
                pr_name = pr_name.text
            else:
                pr_name = None
            pr_icon = pr_info.find('div',{'class':'img'})

            # price
            price_table = detail_left.find('div', {"class":"payCon"}).table
            all_prices = price_table.findAll('tr')
            way_tag = '' # tag for payment methods - compute total rent price
                         # using this tag
            monthly = []
            season = []
            semi = []
            annual = []

            # getting prices for each payment method
            for way in all_prices:
                way_tag = way.findAll('span')
                if way_tag != None and (way_tag != []):
                    way_tag = way_tag[0].text

                for price in way.findAll('td'):
                    if price.find('span') == None:
                        for s in price:
                            if way_tag == '月付':
                                monthly.append(float(re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", s)[0]))
                            elif way_tag == '季付':
                                season.append(float(re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", s)[0]))
                            elif way_tag == '年付':
                                annual.append(float(re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", s)[0]))
                            elif way_tag == '半年付':
                                semi.append(float(re.findall("[-+]?\d+[\.]?\d*[eE]?[-+]?\d*", s)[0]))

            if mode == 'season': #total rent price for seasonal payment method
                excess = len_of_stay - 4
                # rent + service charge + penalty + excess rent + excess service charge
                total_price = math.floor(len_of_stay) * season[0]          \
                                + season[2]/12.0 * math.floor(len_of_stay) \
                                + season[1]                                \
                                + excess * monthly[0]                      \
                                + excess * monthly[2] / 12.0
            lock.acquire()
            myFile.write('<dl>')
            text = " <a href=\"" + url + "\">" + room_name + "</a>"
            myFile.write(cat(text))
            myFile.write(cat(room_location))
            # write to a html file - number of girls, boys in each room
            text = u'女孩: ' + str(num_girls) + u', 男孩: ' + str(num_boys) + u', 空: ' + str(num_empty)
            myFile.write(cat(text))

            for element in details:
                myFile.write(cat(str(element)))

            text = u'总价(￥): ' + str(total_price)
            myFile.write(cat(text))
            text = pr_name + ': ' + pr_tel
            myFile.write(cat(text))
            myFile.write(cat(str(pr_icon)))
            myFile.write(str(images))
            myFile.write('<p></p>')
            myFile.write('</dl>')
            lock.release()

def open_url(url):
    req = session.get(url, headers = headers)
    soup = BeautifulSoup(req.content, fromEncoding=enc)
    return soup

# get page link on current page (1,2,..., last page)
def get_part_pglist(url):
    soup = open_url(url)
    pages = soup.find('div',{'class':'pages'})
    return pages

# get the following pages after current page (1,2,3,4,5, to last page)
def get_pgurls_from_part_pglist(url, pagelist):
    last = 0
    urls = []
    pages = pagelist
    pages = pages.findAll('a', href=True)
    max_pgnum = 1
    if len(pages) >=2:
        max_pgnum = int(pages[len(pages)-2].text)
    print "     Found", max_pgnum, 'pages'
    print "     Asking the servers for page links..."

    if max_pgnum == 1:
        urls.append(url)

    elif max_pgnum > 1:
        i = 0
        while i < max_pgnum:
            if (i - last) <= 1:
                pg_num = str(i+1)
                link = pagelist(text=pg_num)
                if link != None and link != []:
                    last = i
                    link = "http:" + link[0].parent.get('href')
                    urls.append(link)
            else:
                url = urls[last]
                i = last
                pagelist = get_part_pglist(url)
            i = i + 1
    print "     Succeed: Get links for all pages"
    print ''
    return max_pgnum, urls

def get_pageurls(url):
    partial_pagelist = get_part_pglist(url)
    max_pgnum, pageurls = get_pgurls_from_part_pglist(url, partial_pagelist)
    return max_pgnum, pageurls

def get_attr_urls(attrs, url):
    attr_urls = []
    soup = open_url(url)
    # get each attribute page
    for attr in attrs:
        link = "http:" + soup(text=attr)[0].parent.get('href')
        attr_urls.append(link)
    return attr_urls

def main():
    t1 = time.time()
    lock = threading.Lock()
    ALL = 'all'
    BOOKMARK = 'bookmark'
    ATTRIBUTES = 'location'
    ziroom_homepg = "http://www.ziroom.com/z/nl/z2.html?qwd="
    home_url = ziroom_homepg
    bookmark_loc = "user/bookmark.html"
    max_pgnum = 0
    pageurls = []
    roomurls = []

    mode = raw_input('Enter Mode (all, bookmark, locations; locations by default): ')
    if mode == "" or mode == None:
        mode = ATTRIBUTES #ATTRIBUTES = search residence by location, BOOKMARK
    if mode == ATTRIBUTES:
        attrs_str = raw_input('Enter Location You Want (Press Enter if Deafult):')
        attrs_str = attrs_str.decode('gbk').encode('UTF8')
        replacement = [',' , '，' ,';', '；', '_','——']
        for r in replacement:
            attrs_str = attrs_str.replace(r, ' ')
        attrs = attrs_str.split()
        if attrs_str == "" or attrs_str == None:
            attrs = ['次渠','次渠南','经海路'] # by default

    # Processing bookmarks into urls
    print "Processing Home Pages to Get Each Attribute/Page Content"
    print ""

    if mode != BOOKMARK:
        if mode == ATTRIBUTES:
            attr_urls = get_attr_urls(attrs, home_url)

            # get all pages of attribute pages urls
            for link in attr_urls:
                attr_max_pgnum, attr_pageurls = get_pageurls(link)
                max_pgnum = max_pgnum + attr_max_pgnum
                for element in attr_pageurls:
                    pageurls.append(element)
        # get all pages from current page (all next page and previous page...)
        elif mode == ALL:
            max_pgnum, pageurls = get_pageurls(home_url)

        print "Parse url for Each Room on each Page"
        for url, i in zip(pageurls, range(max_pgnum)):
            rooms = open_url(url).findAll('a',{'class':'t1'})
            for eachroom in rooms:
                link = "http:" + eachroom.get('href')
                if link not in roomurls:
                    roomurls.append(link)
            print "     Processed Page", str(i+1)

        print ''
        print 'Start Processing Each Room. Total:', len(roomurls), 'Rooms...'

    else:
        # parse bookmark
        soup = BeautifulSoup(open(bookmark_loc))
        for link in soup.findAll('dl', id='Rent')[0].findAll('a'):
            roomurls.append(link.get('href'))

    with open('user/result.html', 'w') as myFile:
        # headers
        myFile.write('<html>')
        myFile.write('<head>')
        myFile.write('<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />')
        myFile.write('  <link rel = "stylesheet" type = "text/css" href = "style.css" />')
        myFile.write('</head>')
        myFile.write('<body>')
        #myFile.write('<button type=\"button\" onclick="update()">Update</button>')

        # every url info
        threads = []

        for url in roomurls:
            #parse(url, myFile, lock)
            # every page is a thread, this speeds up the process
            t = threading.Thread(target=parse, args=(url, myFile,lock,))
            threads.append(t)
            t.start()

        for th in threads:
            if th != threading.current_thread():
                th.join()

        myFile.write('</body>')
        myFile.write('</html>')
    print "Finished."
    print "Time: ", time.time() - t1
    wait = raw_input("Press Enter to Exit.")

if __name__ == "__main__":
    main()
    #duration = []
    #for i in range(10):
    #    duration.append(main())
    #avg = np.mean(duration)
    #logger.debug('Time: %f', float(avg))
