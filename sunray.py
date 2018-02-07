import logger as l
import json
from datetime import datetime as d
from bs4 import BeautifulSoup
import requests
from dateutil import parser
import os

logger = l.setup_custom_logger(__name__)
ENDPOINT = 'http://14438.formovietickets.com:2235/T.ASP'

def get_dates():
	try:
		dates = []
		params = {'SelectedDate' : d.now().strftime('%Y%m%d')
					,'Page' : 'schedule'
					,'WCI' : 'BT'}
		r = requests.get(ENDPOINT,params=params, headers={'Connection':'close'})
		soup = BeautifulSoup(r.text,'html5lib')
		form = soup.body.table.tbody.tr.form
		for option in form.find_all('option'):
			date = d.strptime(option.text,'%a %b %d, %Y') #get date
			dates.append(date)
		logger.info('Got Dates')
		logger.info('Number of dates found: {}'.format(len(dates)))
	except Exception as e:
		logging.exception('Error in get_dates()',exc_info=True)
	return dates

def get_daily_html(date):
	try:
		params = {'SelectedDate' : date.strftime('%Y%m%d') #add params
							,'Page' : 'schedule'
							,'WCI' : 'BT'}
		r = requests.get(ENDPOINT,params=params, headers={'Connection':'close'})
		soup = BeautifulSoup(r.text,'html5lib')
		strings = [text for text in soup.stripped_strings]
		logger.info('Got Daily Html Strings for date {}'.format(date))
	except Exception as e:
		logging.exception('Error in get_daily_html({})'.format(date),exc_info=True)
	return strings

def get_movie_details_from_html(strings):
	try:
		for idx, string in enumerate(strings): #find the first date, so we can begin parsing in the next block
			try:
				d.strptime(string,'%a %b %d, %Y')
				first_date = idx
				break
			except Exception as ex:
				pass
		for idx, string in enumerate(strings[first_date:],first_date): #starting at the first date above, go until we can't parse anymore. that's where the movies will start
			try:
				d.strptime(string,'%a %b %d, %Y')
			except Exception as ex:
				pass
				movie_start = idx
				break
	except Exception as e:
		logging.exception('Error in get_movie_details_from_html()',exc_info=True)
	return strings[movie_start:]

def get_omdb_movie_details(movie_name):
	try:
		URL = 'http://www.omdbapi.com/'
		details = {'plot' : ''
				   ,'id' : ''
				   ,'year' : ''}
		dir = os.path.dirname(__file__)
		fn = os.path.join(dir, 'configs/omdbapi.json')
		with open(fn) as data_file:
			apikey = json.load(data_file)['apikey']
		
		params = { 'apikey' : apikey
				   ,'plot' : 'full'
				   ,'r' : 'json'
				   ,'type' : 'movie'
				   ,'s' : movie_name
				   ,'page' : 1
				}
		target_movie = {'movie_name' : 'movie'
						,'id' : '0'
						,'year' : '1901'}
		#populate possible movies
		movies = []
		while True:
			r = requests.get(URL, params = params)
			results = r.json()
			if results['Response'] == 'False':
				break     
			for movie in results['Search']:
				movies.append(movie)
			params['page'] += 1
		#first look for match with exact movie title and a poster
		for m in movies:
			if m['Poster'] != 'N/A' and m['Title'].upper() == movie_name.upper() and (int(m['Year']) > int(target_movie['year'])) and (int(m['Year']) <= int(d.now().strftime('%Y'))):
				target_movie['movie_name'] = m['Title']
				target_movie['id'] = m['imdbID']
				target_movie['year'] = m['Year']
		#if nothing found (id still = 0) now look for the most recent matching movie
		if target_movie['id'] == '0':
			for m in movies:
				if (int(m['Year']) > int(target_movie['year'])) and (int(m['Year']) <= int(d.now().strftime('%Y'))):
					target_movie['movie_name'] = m['Title']
					target_movie['id'] = m['imdbID']
					target_movie['year'] = m['Year']
		#now we have (or not) our match and let's continue
		if target_movie['id'] != '0' and target_movie['year'] != '1901':
			params['s'] = ''
			params['i'] = target_movie['id']
			params['y'] = target_movie['year']
			s = requests.get(URL, params = params)
			details['plot'] = s.json()['Plot']
			details['id'] = s.json()['imdbID']
			details['year'] = s.json()['Year']
		if details['id'] == '':
			logger.info('Didn''t find OMDB movie for {}'.format(movie_name))
		else:
			logger.info('Got OMDB movie {}, Year {}, ID {}'.format(movie_name,details['year'], details['id']))
	except Exception as e:
		logging.exception('Error in get_omdb_movie_details({})'.format(movie_name),exc_info=True)
	return details
	
def split_strings_into_movies(strings,date):
	try:
		temp = {}
		for idx, a in enumerate(strings):
			if 'Running Time' in a:
				temp[idx] = 'run_time'
			elif a.upper() == a:
				temp[idx] = 'movie_title'
			else:
				temp[idx] = 'show_time'
		movie_starts = []
		for t,value in temp.items():
			if value == 'movie_title':
				movie_starts.append(t)
		movies = []
		for idx,a in enumerate(strings):
			if idx in movie_starts:
				run_time_counter = 0
				movie = {}
				movie['name'] = strings[idx + 0]
				movie['run_time'] = get_run_time(strings[idx + 1])
				movie['date'] = d.strftime(date,'%Y-%m-%d')
				movie_details = get_omdb_movie_details(movie['name'])
				movie['plot'] = movie_details['plot']
				movie['id'] = movie_details['id']
				movie['year'] = movie_details['year']
				for idx2, a2 in enumerate(strings[idx+2:],idx+2):
					if idx2 in movie_starts:
						break
					else:
						the_str = strings[idx + 2 + run_time_counter]
						the_str = the_str.replace('(','').replace(')','').replace('Sold Out','').strip()
						movie['show_time_{}'.format(run_time_counter)] = the_str
						run_time_counter += 1
				movie = split_show_times(movie)
				movies += movie
	except Exception as e:
		logging.exception('Error in split_strings_into_movies({})'.format(date),exc_info=True)
	return movies

def split_show_times(movie):
	try:
		temp_movies = []
		for key,value in movie.items():
			temp_movie = {}
			temp_movie['name'] = movie['name']
			temp_movie['run_time'] = movie['run_time']
			temp_movie['date'] = movie['date']
			temp_movie['plot'] = movie['plot']
			temp_movie['id'] = movie['id']
			temp_movie['year'] = movie['year']
			if 'show_time' in key:
				temp_movie['show_time'] = d.strftime(parser.parse(value),'%H:%M')
				temp_movies.append(temp_movie)
	except Exception as e:
		logging.exception('Error in split_show_times({})'.format(movie['name']),exc_info=True)
	return temp_movies
	

def get_run_time(str_run_time):
	try:
		split_str = str_run_time.split(' ')
		for index,s in enumerate(split_str):
			try:
				hr = int(s)
				mn = int(split_str[index + 2])
				run_time = '{}:{}'.format(hr,'00{}'.format(mn)[-2:])
				return run_time
				break
			except Exception as ex:
				pass
	except Exception as e:
		logging.exception('Error in get_run_time({})'.format(str_run_time),exc_info=True)
	
def main():
	movies = []
	for date in get_dates():
		strings = get_daily_html(date)
		strings = get_movie_details_from_html(strings)
		daily_movies = split_strings_into_movies(strings,date)            
		movies += daily_movies
	return movies

	
	
if __name__ == '__main__':
	m = main()
	print(json.dumps(m,indent=4))
