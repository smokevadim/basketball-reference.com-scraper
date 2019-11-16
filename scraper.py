'''
basketball-reference.com scraper
author: Vadim Gazizov (smoke.kaliningrad@gmail.com)
'''
import requests
from bs4 import BeautifulSoup
import re
import pandas
from datetime import date
import calendar
from threading import Thread
import os.path

# Constants: start year and end year
startYear = 2001
endYear = 2019
domain = "https://www.basketball-reference.com"
csvFile = "basketball-reference-columns.csv"
abbr_to_num = {name: num for num, name in enumerate(calendar.month_abbr) if num}

limit = 0 # number of entries per month. just for test. after test set to 0


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
        for count, game in enumerate(soup.find(id='schedule').tbody.findAll('td', attrs={'data-stat': 'box_score_text'}), start=1):
            games.append(game.find('a').attrs['href'])

            if limit > 0:
                if count==limit:
                    break
    except:
        pass

    return games

def check_columns():
    columns = [_ for _ in 'Date,Day,Start (time),VisitorTeamName'.split(',')]
    away = []
    home = []
    for i in range(1,19):
        away +=[_ for _ in '\
    ATP{0}Name, ATP{0}MP, ATP{0}FG, ATP{0}FGA, ATP{0}FGPerc, ATP{0}P, ATP{0}PA, ATP{0}PPerc, ATP{0}FT,\
    ATP{0}FTA, ATP{0}FTPerc, ATP{0}ORB, ATP{0}DRB, ATP{0}TRB, ATP{0}AST, ATP{0}STL, ATP{0}BLK, ATP{0}TOV, ATP{0}PF, ATP{0}PTS, ATP{0}PM, \
    ATP{0}TSPerc, ATP{0}eFGPerc, ATP{0}PAr, ATP{0}FTr, ATP{0}ORBPerc, ATP{0}DRBPerc, ATP{0}TRBPerc, ATP{0}ASTPerc, ATP{0}STLPerc, \
    ATP{0}BLKPerc, ATP{0}TOVPerc, ATP{0}USGPerc, ATP{0}ORtg, ATP{0}DRtg'.format(str(i)).replace(' ','').split(',')]

        home += [_ for _ in '\
        HTP{0}Name, HTP{0}MP, HTP{0}FG, HTP{0}FGA, HTP{0}FGPerc, HTP{0}P, HTP{0}PA, HTP{0}PPerc, HTP{0}FT, HTP{0}FTA, HTP{0}FTPerc, \
            HTP{0}ORB, HTP{0}DRB, HTP{0}TRB, HTP{0}AST, HTP{0}STL, HTP{0}BLK, HTP{0}TOV, HTP{0}PF, HTP{0}PTS, HTP{0}PM, HTP{0}TSPerc, HTP{0}eFGPerc, \
            HTP{0}PAr, HTP{0}FTr, HTP{0}ORBPerc, HTP{0}DRBPerc, HTP{0}TRBPerc, HTP{0}ASTPerc, HTP{0}STLPerc, HTP{0}BLKPerc, HTP{0}TOVPerc, \
            HTP{0}USGPerc, HTP{0}ORtg, HTP{0}DRtg'.format(str(i)).replace(' ','').split(',')]
    columns+=away

    columns+= [_ for _ in 'AwayQ1Pts, AwayQ2Pts, AwayQ3Pts, AwayQ4Pts, AwayOT1Pts, AwayOT2Pts, AwayOT3Pts, AwayOT4Pts, AwayOT5Pts, \
    AwayPts, HomeTeamName'.format(str(i)).replace(' ','').split(',')]

    columns+=home

    columns+= [_ for _ in 'HomeQ1Pts, HomeQ2Pts, HomeQ3Pts, HomeQ4Pts, HomeOT1Pts, \
    HomeOT2Pts, HomeOT3Pts, HomeOT4Pts, HomeOT5Pts, HomePts, Official1, Official2, \
    Official3, Attendance'.format(str(i)).replace(' ','').split(',')]
    return columns


def get_data(game):
    soup = get_html(domain + game)

    data = dict()

    weekday = date(
        int(soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[2].strip()),
        abbr_to_num[soup.find('div', attrs={'class': 'scorebox_meta'}).find('div').text.split(',')[1].split(' ')[1].strip()[:3]],
        int(soup.find('div', attrs={'class': 'scorebox_meta'}).find('div').text.split(',')[1].split(' ')[2].strip())).strftime('%A')
    data['Day'] = weekday

    data['Date'] = soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[1].strip()+','+soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[2].rstrip()
    data['Start (time)'] = soup.find('div', attrs = {'class': 'scorebox_meta'}).find('div').text.split(',')[0]
    data['VisitorTeamName'] = soup.find('div',class_='scorebox').findAll('a',attrs = {'itemprop': "name"})[1].text
    data['HomeTeamName'] = soup.find('div',class_='scorebox').findAll('a',attrs = {'itemprop': "name"})[0].text
    teams = ['A','H']
    for team in teams:
        for counter in range(19):
            try:
                line = soup.findAll('table', class_ = 'sortable stats_table', attrs={'id':re.compile('(box-)*(-game-basic)')})[1 if team == 'A' else 0].tbody.findAll('tr',attrs={'class':''})[counter]
                if 'Did Not' in line.find('td').text:
                    continue
                data[team + 'TP' + str(counter + 1) + 'Name'] = line.find('th', attrs={'data-stat': "player"}).find('a').text
                data[team + 'TP' + str(counter+1) + 'MP'] = line.find('td', attrs={'data-stat': "mp"}).text
                data[team + 'TP' + str(counter+1) + 'FG'] = line.find('td', attrs={'data-stat': "fg"}).text
                data[team + 'TP' + str(counter+1) + 'FGA'] = line.find('td', attrs={'data-stat': "fga"}).text
                data[team + 'TP' + str(counter+1) + 'FGPerc'] = line.find('td', attrs={'data-stat': "fg_pct"}).text
                data[team + 'TP' + str(counter+1) + 'P'] = line.find('td', attrs={'data-stat': "fg3"}).text
                data[team + 'TP' + str(counter+1) + 'PA'] = line.find('td', attrs={'data-stat': "fg3a"}).text
                data[team + 'TP' + str(counter+1) + 'PPerc'] = line.find('td', attrs={'data-stat': "fg3_pct"}).text
                data[team + 'TP' + str(counter+1) + 'FT'] = line.find('td', attrs={'data-stat': "ft"}).text
                data[team + 'TP' + str(counter+1) + 'FTA'] = line.find('td', attrs={'data-stat': "fta"}).text
                data[team + 'TP' + str(counter+1) + 'FTPerc'] = line.find('td', attrs={'data-stat': "ft_pct"}).text
                data[team + 'TP' + str(counter+1) + 'ORB'] = line.find('td', attrs={'data-stat': "orb"}).text
                data[team + 'TP' + str(counter+1) + 'DRB'] = line.find('td', attrs={'data-stat': "drb"}).text
                data[team + 'TP' + str(counter+1) + 'TRB'] = line.find('td', attrs={'data-stat': "trb"}).text
                data[team + 'TP' + str(counter+1) + 'AST'] = line.find('td', attrs={'data-stat': "ast"}).text
                data[team + 'TP' + str(counter+1) + 'STL'] = line.find('td', attrs={'data-stat': "stl"}).text
                data[team + 'TP' + str(counter+1) + 'BLK'] = line.find('td', attrs={'data-stat': "blk"}).text
                data[team + 'TP' + str(counter+1) + 'TOV'] = line.find('td', attrs={'data-stat': "tov"}).text
                data[team + 'TP' + str(counter+1) + 'PF'] = line.find('td', attrs={'data-stat': "pf"}).text
                data[team + 'TP' + str(counter+1) + 'PTS'] = line.find('td', attrs={'data-stat': "pts"}).text
                data[team + 'TP' + str(counter+1) + 'PM'] = line.find('td', attrs={'data-stat': "plus_minus"}).text
    
                adv_line = soup.findAll('table', class_="sortable", id=re.compile('(box-)*(-game-advanced)'))[1 if team == 'A' else 0]
                data[team + 'TP' + str(counter+1) + 'TSPerc'] = adv_line.findAll('td', attrs={'data-stat': "ts_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'eFGPerc'] = adv_line.findAll('td', attrs={'data-stat': "efg_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'PAr'] = adv_line.findAll('td', attrs={'data-stat': "fg3a_per_fga_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'FTr'] = adv_line.findAll('td', attrs={'data-stat': "fta_per_fga_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'ORBPerc'] = adv_line.findAll('td', attrs={'data-stat': "orb_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'DRBPerc'] = adv_line.findAll('td', attrs={'data-stat': "drb_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'TRBPerc'] = adv_line.findAll('td', attrs={'data-stat': "trb_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'ASTPerc'] = adv_line.findAll('td', attrs={'data-stat': "ast_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'STLPerc'] = adv_line.findAll('td', attrs={'data-stat': "stl_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'BLKPerc'] = adv_line.findAll('td', attrs={'data-stat': "blk_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'TOVPerc'] = adv_line.findAll('td', attrs={'data-stat': "tov_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'USGPerc'] = adv_line.findAll('td', attrs={'data-stat': "usg_pct"})[counter].text
                data[team + 'TP' + str(counter+1) + 'ORtg'] = adv_line.findAll('td', attrs={'data-stat': "off_rtg"})[counter].text
                data[team + 'TP' + str(counter+1) + 'DRtg'] = adv_line.findAll('td', attrs={'data-stat': "def_rtg"})[counter].text
            except Exception:
                # need to fill empty data
                continue
    
        line_score = BeautifulSoup(soup.find('div', class_='content_grid').find('div', id='all_line_score').contents[5],'html.parser')
        ot_count= 1;
        for count, away in enumerate(line_score.findAll('tr')[3 if team == 'A' else 2].findAll('td', class_='center'), start=1):
            if count in range(1,5):
                data[('Away' if team == 'A' else 'Home') + 'Q' +str(count)+ 'Pts'] = away.text
            elif line_score.findAll('th')[count+2].text == 'T': #all points
                data[('Away' if team == 'A' else 'Home') + 'Pts'] = away.text
            else: # OverTime
                data[('Away' if team == 'A' else 'Home') + 'OT' + str(ot_count) + 'Pts'] = away.text
                ot_count += 1

    # officials
    officials = soup.find('strong', string=re.compile('Officials:')).find_all_next('a', attrs={'href': re.compile('.*(referees).*')})
    for count, official in enumerate(officials, start=1):
        data['Official'+str(count)] = official.text
        if count == 3:
            break

    # Attendance
    data['Attendance'] = str(soup.find('strong', string=re.compile('Attendance:')).next_sibling.strip(','))

    print(game, ' - OK!')
    return data


def get_html(url):
    html = requests.get(url, "verify=False").text
    return BeautifulSoup(html, 'html.parser')


def run_in_thread(games):
    step = 10
    threads = []
    for i in range(0, len(games), step):
        t = Thread(target=get_data_and_append, args=(games[i:i + step],))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()


def get_data_and_append(games):
    global results
    for game in games:
        try:
            res = get_data(game)
            results = results.append(pandas.DataFrame([res], columns=results.keys()), sort=False)
            results.to_csv(csvFile, mode='a', index=False, header=False if os.path.exists(csvFile) else True)
            results = results[0:0]

        except Exception:
            print('Problem in ', game)

def sort_csv():
    pf = pandas.read_csv(csvFile, low_memory=False, )
    pf['Year'] = ''
    pf['Month'] = ''
    pf['Day_'] = ''
    pf.drop_duplicates(subset=['Date', 'Start (time)', 'VisitorTeamName'], keep='first', inplace=True)
    for row in pf.index:
        pf['Year'][row] = int(pf['Date'][row].split(' ')[2].strip())
        pf['Month'][row] = abbr_to_num[(pf['Date'][row].split(',')[0].split(' ')[0].strip())[:3]]
        pf['Day_'][row] = int(pf['Date'][row].split(',')[0].split(' ')[1].strip())
    pf.sort_values(by=['Year', 'Month', 'Day_'], inplace=True)
    del pf['Year']
    del pf['Month']
    del pf['Day_']
    pf.to_csv(csvFile, mode='w', index=False)

if __name__ == '__main__':
    years = get_years()

    results = pandas.DataFrame(columns=check_columns())

    for year in years:
        months = get_months(year)
        for count_m, month in enumerate(months):
            games = get_games(month)

            run_in_thread(games)

    results = None
    sort_csv()


