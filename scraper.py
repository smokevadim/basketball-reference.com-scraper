'''
basketball-reference.com scraper
author: Vadim Gazizov (smoke.kaliningrad@gmail.com)
'''

import requests
from bs4 import BeautifulSoup
import re
import pandas

# Constants: start year and end year
startYear = 2013
endYear = 2013
domain = "https://www.basketball-reference.com"
csvFile = "basketball-reference-columns.csv"
pages = set()


def get_years():
    years = []
    current_year = startYear
    while True:
        years.append(current_year)
        if current_year == endYear:
            return years
        else:
            current_year+=1


def get_months(year):
    months = []
    soup = get_html(domain+'/leagues/NBA_' + str(year) + '_games.html')
    try:
        for month in soup.find(class_='filter').findAll('a'):
            months.append(month.attrs['href'])
    except:
        pass

    return months


def get_games(month):
    games = []
    soup = get_html(domain+month)
    try:
        for iter in soup.find(id='schedule').tbody.findAll('td', attrs={'data-stat': 'box_score_text'}):
            for game in iter.findAll('a'):
                games.append(game.attrs['href'])
    except:
        pass

    return games


def get_data(game, columns):
    data = pandas.DataFrame(columns=columns)
    soup = get_html(domain + game)
    data.loc[0, 'Date'] = soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[1]
    data.loc[0, 'Day'] = soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[1].split(' ')[2]
    data.loc[0, 'Start (time)'] = soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[0]
    data.loc[0, 'VisitorTeamName'] = soup.find('div',class_='scorebox').findAll('div')[1].find('a',attrs = {'itemprop': "name"}).text
    for counter, line in enumerate(soup.findAll('table', class_ = 'sortable stats_table', attrs={'id':re.compile('(box-)*(-game-basic)')})[1].tbody.findAll('tr',attrs={'class':''})):
        if 'Did Not' in line.find('td').text:
            continue
        data.loc[0, 'ATP' + str(counter) + 'MP'] = line.find('td', attrs={'data-stat': "mp"}).text
    print(data)
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    # data[0, 'Date'] = soup.find
    return data


def save_data(data):
    pass


def get_html(url):
    html = requests.get(url, "verify=False").text
    return BeautifulSoup(html, 'html.parser')


if __name__ == '__main__':
    years = get_years()
    results = pandas.read_csv(csvFile)

    for year in years:
        months = get_months(year)
        for count_m, month in enumerate(months):
            games = get_games(month)
            for count_g, game in enumerate(games):
                try:
                    res = get_data(game, results.columns)
                    results.append(res, ignore_index=True, sort=False)
                except Exception:
                    print('Problem in ', game)
                if count_g == 1:
                    break
            if count_m == 1:
                break


    results.to_csv(csvFile)

