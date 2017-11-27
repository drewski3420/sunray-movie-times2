import json
from datetime import datetime as d
from datetime import timedelta
from bs4 import BeautifulSoup
import requests
from dateutil import parser
import icalendar as c
import sunray
import pytz

movies = sunray.main()

cal = c.Calendar()
cal.add('prodid','Drew Product')
cal.add('version','2.0')
cal.add('X-WR-CALNAME','Sun-Ray Cinema' )
uid = 0
for movie in movies:
    show_time_counter = 0
    while True:
        try:
            name = movie['name']
            run_time = parser.parse(movie['run_time']).time()
            show_start_date = parser.parse(movie['date'])
            show_start_time = parser.parse(movie['show_time_{}'.format(show_time_counter)]).time()
            show_start_date_time = d.combine(show_start_date,show_start_time)
            show_end_date_time = show_start_date_time + timedelta(hours=run_time.hour,minutes=run_time.minute)
            show_start_with_tz = show_start_date_time
            show_end_with_tz = show_end_date_time
            event = c.Event()
            event.add('summary',name)
            event.add('dtstart',show_start_with_tz)
            event.add('dtend',show_end_with_tz)
            event.add('dtstamp',d.now())
            event.add('uid',uid)
            cal.add_component(event)
            uid += 1
            show_time_counter += 1
        except ValueError as v:
            break
        except Exception as ex:
            break
with open('test.ics','w+b') as f:
    f.write(cal.to_ical())


        
    

