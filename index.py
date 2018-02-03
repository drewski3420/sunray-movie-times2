from __future__ import print_function
import httplib2
import os
import sunray
from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
import json
import datetime
from datetime import timedelta
from bs4 import BeautifulSoup
import requests
from dateutil import parser
import pytz
try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/calendar'
CLIENT_SECRET_FILE = 'configs/client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'

def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir,'.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

def build_event(name,run_time,start_date,end_date,plot,id,year):
    event = {}
    event['start'] = {}
    event['end'] = {}
    event['attachments'] = {}
    event['attendees'] = {}
    start_str = start_date.strftime('%Y-%m-%dT%H:%M:%S')
    end_str = end_date.strftime('%Y-%m-%dT%H:%M:%S')
    event['summary'] = name
    event['location'] = '1028 Park St, Jacksonville, FL 32204'
    description = ''
    if id:
        description += 'http://www.imdb.com/title/{}/'.format(id)
    if year:
        description += '\nYear: {}'.format(year)
    if plot and plot != 'N/A':
		description += '\nPlot: {}'.format(plot)
    if run_time:
		description += '\nRun Time: {}'.format(run_time)
    event['description'] = description
    event['start']['dateTime'] = start_str
    event['start']['timeZone'] = 'America/New_York'
    event['end']['dateTime'] = end_str
    event['end']['timeZone'] = 'America/New_York'
    return event

def get_cal_id(service):
    cals = service.calendarList().list().execute()
    for cal in cals['items']:
        if cal['summary'] == 'Sun-Ray Cinema':
            cal_id = cal['id']
    return cal_id
    
def clear_calendar(cal_id,service):
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time   
    eventsResult = service.events().list(calendarId=cal_id, timeMin=now, singleEvents=True, orderBy='startTime').execute()
    for event in eventsResult['items']:
        service.events().delete(calendarId=cal_id, eventId=event['id']).execute()

def add_event(service, ev, cal_id):
    service.events().insert(calendarId=cal_id, body=ev).execute()
    
def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)
    
    #get calendar ID
    cal_id = get_cal_id(service)

    #first delete all upcoming events
    clear_calendar(cal_id,service)

    #now add new events - first get list of current SunRay showtimes
    movies = sunray.main()
    
    #now loop through and add event
    for movie in movies:
        name = movie['name']
        run_time = parser.parse(movie['run_time']).time()
        show_start_date = parser.parse(movie['date'])
        show_start_time = parser.parse(movie['show_time']).time()
        plot = movie['plot']
        id = movie['id']
        year = movie['year']
        show_start_date_time = datetime.datetime.combine(show_start_date,show_start_time)
        show_end_date_time = show_start_date_time + timedelta(hours=run_time.hour,minutes=run_time.minute)
        show_start_with_tz = show_start_date_time
        show_end_with_tz = show_end_date_time
        #only add if it's after work on a weekday (keeps  calendar cleaner)
        if (show_start_time >= parser.parse('17:00:00').time()) or (show_start_date_time.strftime('%A') in ('Saturday','Sunday')):
            ev = build_event(name,run_time,show_start_with_tz,show_end_with_tz,plot,id,year)
            add_event(service,ev,cal_id)

if __name__ == '__main__':
    main()

def lambda_handler(event, context):
    main()
