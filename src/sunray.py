import json
from datetime import datetime as d
from bs4 import BeautifulSoup
import requests
from dateutil import parser
ENDPOINT = 'http://14438.formovietickets.com:2235/T.ASP'

def get_dates():
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
    return dates

def get_daily_html(date):
    params = {'SelectedDate' : date.strftime('%Y%m%d') #add params
                        ,'Page' : 'schedule'
                        ,'WCI' : 'BT'}
    r = requests.get(ENDPOINT,params=params, headers={'Connection':'close'})
    soup = BeautifulSoup(r.text,'html5lib')
    strings = [text for text in soup.stripped_strings]
    return strings

def get_movie_details_from_html(strings):
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
    return strings[movie_start:]

def split_strings_into_movies(strings,date):
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
            for idx2, a2 in enumerate(strings[idx+2:],idx+2):
                if idx2 in movie_starts:
                    break
                else:
                    the_str = strings[idx + 2 + run_time_counter]
                    the_str = the_str.replace('(','').replace(')','').replace('Sold Out','').strip()
                    movie['show_time_{}'.format(run_time_counter)] = the_str#strings[idx + 2 + run_time_counter]
                    run_time_counter += 1
            movie = split_show_times(movie)
            movies += movie
    return movies

def split_show_times(movie):
    temp_movies = []
    for key,value in movie.items():
        temp_movie = {}
        temp_movie['name'] = movie['name']
        temp_movie['run_time'] = movie['run_time']
        temp_movie['date'] = movie['date']
        if 'show_time' in key:
            temp_movie['show_time'] = d.strftime(parser.parse(value),'%H:%M')
            temp_movies.append(temp_movie)
    return temp_movies
    

def get_run_time(str_run_time):
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

def main():
    movies = []
    for date in get_dates():
		strings = get_daily_html(date)
		strings = get_movie_details_from_html(strings)
		daily_movies = split_strings_into_movies(strings,date)            
		movies += daily_movies
    return movies

    
    
if __name__ == '__main__':
    main()
