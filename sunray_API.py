import requests
import json
from datetime import datetime as d
from dateutil import parser
import os
import logger as l

logger = l.setup_custom_logger(__name__)

def encode_it(a):
	return a.encode('utf-8').strip()

def main():
	dir = os.path.dirname(__file__)
	fn = os.path.join(dir, 'configs/tmsapi.json')
	with open(fn) as data_file:
		APIKEY = json.load(data_file)['apikey']
	ENDPOINT = 'http://data.tmsapi.com/v1.1/movies/showings'

	params = {'api_key' : APIKEY
			,'numDays' : '90'
			,'zip' : '32204'
			,'radius' : '2'
			,'units' : 'km'
			,'imageSize' : 'Sm'
			,'imageText' : 'True'
			,'startDate' : d.now().strftime('%Y-%m-%d')
	}

	r = requests.get(ENDPOINT,params = params)
	movies = []
	for result in r.json():
			for showtime in result['showtimes']:	
				if showtime['theatre']['id'] == '9777':
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
						movies.append(movie)
					except Exception as ex:
						print(json.dumps(result,indent=4))
						print(ex)
						print('---------------------------------')
						pass
	return movies


	
if __name__ == '__main__':
	m = main()
