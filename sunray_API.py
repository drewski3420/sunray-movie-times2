import requests
import json
from datetime import datetime as d, timedelta
from dateutil import parser
import os
import logger as l

logger = l.setup_custom_logger(__name__)

def encode_it(a):
	try:
		return a.encode('utf-8').strip()
	except Exception as e:
		logger.exception('Error in encode_it()',exc_info=True)

def get_omdb_api_key():
	try:
		dir = os.path.dirname(__file__)
		fn = os.path.join(dir, 'configs/omdbapi.json')
		with open(fn) as data_file:
			apikey = json.load(data_file)['apikey']
	except Exception as e:
		logger.exception('Error in getting get_omdb_api_key',exc_info=True)
		apikey = ''
	return apikey
		
def main():
	try:
		omdb_api = get_omdb_api_key()
		dir = os.path.dirname(__file__)
		fn = os.path.join(dir, 'configs/tmsapi.json')
		with open(fn) as data_file:
			APIKEY = json.load(data_file)['apikey']
		ENDPOINT = 'http://data.tmsapi.com/v1.1/movies/showings'
		movies = []
		params = {'api_key' : APIKEY
				,'numDays' : '90'
				,'zip' : '32204'
				,'radius' : '2'
				,'units' : 'km'
				,'imageSize' : 'Sm'
				,'imageText' : 'True'
				,'startDate' : d.now().strftime('%Y-%m-%d')
		}
		logger.info('Getting API Data')
		#with open('static_data.txt','r') as the_file:
		#	r = json.load(the_file)
		r = requests.get(ENDPOINT,params = params)
		logger.info('Got API Data')
		#for result in r:
		for result in r.json():
			logger.info('Looping through results')
			for showtime in result['showtimes']:	
				if showtime['theatre']['id'] == '9777':
					logger.info('Looing through showtimes')
					try:
						movie = {}
						if 'title' in result:
							movie['name'] = encode_it(result['title'])
						else:
							movie['name'] = ''
						if 'runTime' in result:
							run_time_str = result['runTime']
						else:
							run_time_str = 'PT01H00M'
						movie['run_time'] = '{}:{}'.format(run_time_str[2:4],run_time_str[5:7])
						if 'longDescription' in result:
							movie['plot'] = encode_it(result['longDescription'])
						elif 'shortDescription' in result:
							movie['plot'] = encode_it(result['shortDescription'])
						else:
							movie['plot'] = 'Missing Description'
						if 'tmsId' in result:
							movie['id'] = result['tmsId']
						else:
							movie['id'] = 'Missing ID'
						if 'releaseYear' in result:
							movie['year'] = result['releaseYear']
						else:
							movie['year'] = 'Missing Year'
						if 'officialUrl' in result:
							movie['official_url'] = result['officialUrl']
						else:
							movie['official_url'] = 'Missing Official URL'
						imdb_url = get_omdb_movie_details(movie['name'],omdb_api)
						if imdb_url:
							movie['imdb_url'] = imdb_url
						else:
							movie['imdb_url'] = 'Missing IMDB URL'
						show_time = parser.parse(showtime['dateTime'])
						movie['date'] = d.strftime(show_time,'%Y-%m-%d')
						movie['show_time'] = d.strftime(show_time,'%H:%M')
						
						logger.info('Got Movie {} details, appending show time {}'.format(movie['name'],show_time.strftime('%Y-%m-%d %H:%M')))
						movies.append(movie)
						logger.info('Appended movie')
					except Exception as ex:
						logger.exception('Error encountered', exc_info=True)
						logger.exception(json.dumps(result,indent=4))
						pass
	except Exception as e:
		logger.exception('Error in main()',exc_info=True)
	logger.info('Returning movies show times list')
	return movies

def get_omdb_movie_details(movie_name, apikey):
	try:
		URL = 'http://www.omdbapi.com/'
		return_url = ''
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
			return_url = 'https://www.imdb.com/title/{}'.format(target_movie['id'])
			logger.info('Got IMDB ID {}'.format(target_movie['id']))
		else:
			logger.info('Didn''t find OMDB movie for {}'.format(movie_name))			
	except Exception as e:
		logger.exception('Error in get_omdb_movie_details({})'.format(movie_name),exc_info=True)
	return return_url
	
if __name__ == '__main__':
	m = main()
	#for a in m:
	#	print(a)
