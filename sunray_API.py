import requests
import json
from datetime import datetime as d
from dateutil import parser
import os
import logger as l

logger = l.setup_custom_logger(__name__)

def main():
	dir = os.path.dirname(__file__)
	fn = os.path.join(dir, 'configs/tmsapi.json')
	with open(fn) as data_file:
		APIKEY = json.load(data_file)['apikey']
	ENDPOINT = 'http://data.tmsapi.com/v1.1/movies/showings'

	params = {'api_key' : APIKEY
			,'numdays' : '365'
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
		movie = {}
		movie['name'] = result['title']
		run_time_str = result['runTime']
		movie['run_time'] = '{}:{}'.format(run_time_str[2:4],run_time_str[5:7])
		movie['plot'] = result['longDescription']
		movie['id'] = result['tmsId']
		movie['year'] = result['releaseYear']
		for showtime in result['showtimes']:	
			if showtime['theatre']['id'] == '9777':
				show_time = parser.parse(showtime['dateTime'])
				movie['date'] = d.strftime(show_time,'%Y-%m-%d')
				movie['show_time'] = d.strftime(show_time,'%H:%M')
				movies.append(movie)
	return movies


	
if __name__ == '__main__':
	m = main()
