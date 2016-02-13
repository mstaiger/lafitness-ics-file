#!/usr/bin/env python

from bs4 import BeautifulSoup
from datetime import timedelta, datetime, date
from time import strftime, strptime
from hashlib import md5
from sys import argv
import urllib2
import re

if len(argv) is 1:
	clubid = '469'
else:
    clubid = argv[1]
url = 'http://lafitness.com/Pages/ClassSchedulePrintVersion.aspx?clubid=' + clubid
response = urllib2.urlopen(url)
html_doc = response.read()

#html_doc = open('lafitness2.html','r').read()
thedate = datetime.strptime(strftime('%Y %m %d'),'%Y %m %d')
today = strftime('%A')
tzinfo = 'America/Chicago'
day = timedelta(days=1)

def dayoffset(today,dayofweek):
	dow = ['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday']
	offset = dow.index(dayofweek) - dow.index(today)
	if dow.index(today) <= dow.index(dayofweek): return offset
	return offset + 7

soup = BeautifulSoup(html_doc, 'html.parser')
[span.extract() for span in soup.find_all('span',attrs={'class':'required'})]
addrblock = soup.find('div',attrs={'style':'font-size: 12px !important; vertical-align: bottom !important;'}).string.strip().splitlines()
tableblock = soup.find('table',attrs={'id':'tblSchedule'})

location = {}

for idx in range(len(addrblock)):
	item = re.sub(r'\t','',addrblock[idx].strip())
	item = re.sub(r',$','',item)
	if idx in [0,1]:
		if idx is 0: location['street'] = item.title()
    	if idx is 1: location['city'] = item.title()
	if idx in [2,3,5]:
		if idx is 2: location['state'] = item
    	if idx is 3: location['zip'] = item
    	if idx is 5: location['phone'] = item


daysofweek = {}
times = {}
schedule = {}
rows = tableblock.find_all('tr')

for rowidx, row in enumerate(rows):
    columns = row.find_all(['th','td'])
    for colidx, column in enumerate(columns):
    	if column.name == 'th':
        	daysofweek[colidx] = column.string.encode('utf-8').strip()
        else:
        	contents = column.find_all(['h5','a'])
        	for i, td in enumerate(contents):
        		if td.string is not None:
					item = td.string.encode('utf-8').strip()

					if colidx == 0:
						times[rowidx] = item
						continue

					if td.get('class') is not None and td['class'][0] == u'TrainerBiosModalBoxActivationTriger':
						classinfo = {'trainer':item}
					else:
						classinfo = {'classname':item}

					classdate = thedate + dayoffset(today,daysofweek[colidx]) * day
					classdate = strptime(classdate.strftime('%Y %m %d ') + times[rowidx],'%Y %m %d %I:%M %p')
					classdatetime = strftime('%Y%m%dT%H%M%S',classdate)

					if schedule.get(classdatetime) is None:
						schedule[classdatetime] = {}

					schedule[classdatetime].update(classinfo)

cal = '''\
BEGIN:VCALENDAR
PRODID:UNofficial.LAFitness.ical.generator
VERSION:2.0
X-WR-CALNAME:{0}, {1} - LA Fitness Class Schedule
X-WR-TIMEZONE:{2}\
'''.format(location['city'],location['state'],tzinfo)

for dt in schedule:
	uid = md5('{0}{1}{2}'.format(dt,schedule[dt]['classname'],schedule[dt]['trainer'])).hexdigest()
	dtend = (datetime.strptime(dt,'%Y%m%dT%H%M%S') + timedelta(hours=1)).strftime('%Y%m%dT%H%M%S')

	event ="""
BEGIN:VEVENT
DTSTART:{3}
DTEND:{4}
SUMMARY:{0} - {1} ({2})
LOCATION:{7}\, {2}\, {8} {9}
DESCRIPTION:Telephone: {6}
URL:{10}
UID:{5}@lafitness.com
END:VEVENT\
"""
	cal += event.format(schedule[dt]['classname'],schedule[dt]['trainer'],location['city'],
		                dt,dtend,uid,location['phone'],
		        		location['street'],location['state'],location['zip'],url)

cal += "\nEND:VCALENDAR"
print cal