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

def main():
	try:
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
		r = requests.get(ENDPOINT,params = params)
		logger.info('Got API Data')
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

	
if __name__ == '__main__':
	m = main()
