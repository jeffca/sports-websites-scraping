import requests
import time
from bs4 import BeautifulSoup
import datetime

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = ''


HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}

def get_first_available_row(range_name):
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID, range=range_name).execute()

        rows = result.get('values', [])

        firstAvailableRow = 1

        #when the Games tab is blank with just a header row
        if len(rows) > 1:
            for row in rows:
                firstAvailableRow+=1

        else:
            firstAvailableRow = 2

        return str(firstAvailableRow)
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def update_values(range_name, value_input_option,
                  values):
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        # print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def parseTeamPoints(url, firstAvailableRow):
    game_date = url.split("boxscore/")[1].split("/")[0]

    response = requests.get(url,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    box_score_html = soup.find('table', {"class":"basketball"})
    box_score_soup = BeautifulSoup(str(box_score_html).split("<tbody>")[1].split("</tbody>")[0], "html.parser")
    box_score = box_score_soup.find_all("td")

    away_team = ""
    away_team_q1 = 0
    away_team_q2 = 0
    away_team_q3 = 0
    away_team_q4 = 0
    away_team_ot = 0
    away_team_final_score = 0

    home_team = ""
    home_team_q1 = 0
    home_team_q2 = 0
    home_team_q3 = 0
    home_team_q4 = 0
    home_team_ot = 0
    home_team_final_score = 0

    quarter_count = 0

    #<td>NYK (2-4)</td>
    # <td>25</td>
    # <td>21</td>
    # <td>30</td>
    # <td>29</td>
    # <td>105</td>
    # <td>MIL (3-2)</td>
    # <td>21</td>
    # <td>35</td>
    # <td>26</td>
    # <td>28</td>
    # <td>110</td>

    #4 quarter game
    if (len(box_score) == 12):
        for i in box_score:
            td_content = str(i).split("<td>")[1].split("</td>")[0]
            if len(td_content) > 3:
                if away_team == "":
                    away_team = str(i).split("<td>")[1].split(" (")[0]
                else:
                    home_team = str(i).split("<td>")[1].split(" (")[0]
            else:
                if away_team_q1 == 0:
                    away_team_q1 = td_content
                elif away_team_q2 == 0:
                    away_team_q2 = td_content
                elif away_team_q3 == 0:
                    away_team_q3 = td_content
                elif away_team_q4 == 0:
                    away_team_q4 = td_content
                elif away_team_final_score == 0:
                    away_team_final_score = td_content
                elif home_team_q1 == 0:
                    home_team_q1 = td_content
                elif home_team_q2 == 0:
                    home_team_q2 = td_content
                elif home_team_q3 == 0:
                    home_team_q3 = td_content
                elif home_team_q4 == 0:
                    home_team_q4 = td_content
                elif home_team_final_score == 0:
                    home_team_final_score = td_content     
    #OT game
    elif (len(box_score) == 14):
        print("OT Game.....")
        for i in box_score:
            if quarter_count != 4:
                td_content = str(i).split("<td>")[1].split("</td>")[0]
                if len(td_content) > 3:
                    if away_team == "":
                        away_team = str(i).split("<td>")[1].split(" (")[0]
                    else:
                        home_team = str(i).split("<td>")[1].split(" (")[0]
                else:
                    if away_team_q1 == 0:
                        away_team_q1 = td_content
                        quarter_count += 1
                    elif away_team_q2 == 0:
                        away_team_q2 = td_content
                        quarter_count += 1
                    elif away_team_q3 == 0:
                        away_team_q3 = td_content
                        quarter_count += 1
                    elif away_team_q4 == 0:
                        away_team_q4 = td_content
                        quarter_count += 1
                    elif away_team_final_score == 0:
                        away_team_final_score = td_content
                        quarter_count = 0
                    elif home_team_q1 == 0:
                        home_team_q1 = td_content
                        quarter_count += 1
                    elif home_team_q2 == 0:
                        home_team_q2 = td_content
                        quarter_count += 1
                    elif home_team_q3 == 0:
                        home_team_q3 = td_content
                        quarter_count += 1
                    elif home_team_q4 == 0:
                        home_team_q4 = td_content
                        quarter_count += 1
                    elif home_team_final_score == 0:
                        home_team_final_score = td_content   
                        quarter_count = 0
            else:
                quarter_count+=1                                             

    update_values("BoxScores!A"+str(firstAvailableRow)+":N"+str(firstAvailableRow), "USER_ENTERED",
        [
            [
                int(firstAvailableRow)+1,
                game_date,
                away_team,
                home_team,
                away_team_q1,
                away_team_q2,
                away_team_q3,
                away_team_q4,
                away_team_final_score,
                home_team_q1,
                home_team_q2,
                home_team_q3,
                home_team_q4,
                home_team_final_score
            ]
        ]
    )
    time.sleep(0.5)
    print(away_team + " played at " + home_team + " and scored " + str(away_team_final_score) + " while " + home_team + " scored " + str(home_team_final_score))
    return str((int(firstAvailableRow)+1))+"|"+away_team+"|"+home_team

def parsePlayerStats(url, firstAvailableRow, gameId, awayTeam, homeTeam):
    response = requests.get(url,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    html = soup.find_all('table', {"class":"tablesaw"})

    away_team = str(html[0]).split('<tbody>')[1]
    home_team = str(html[1]).split('<tbody>')[1]

    soup = BeautifulSoup(away_team, 'html.parser')
    away_team_stats = soup.find_all('td')

    soup = BeautifulSoup(home_team, "html.parser")
    home_team_stats = soup.find_all('td')

    # <td>30</td> player number
    # <td rel="Randle, Julius"><a href="/player/Julius-Randle/Summary/24301">Julius Randle</a></td>
    # <td>Starter</td>
    # <td>PF</td>
    # <td rel="38.59">38:59</td>
    # <td rel="5.25">5-20</td>
    # <td rel="1.1111111111111">1-9</td>
    # <td rel="5.5555555555556">5-9</td>
    # <td rel="11.6">11.6</td>
    # <td rel="4">4</td>
    # <td rel="8">8</td>
    # <td rel="12">12</td>
    # <td rel="5">5</td>
    # <td rel="4">4</td>
    # <td rel="2">2</td>
    # <td rel="0">0</td>
    # <td rel="1">1</td>
    # <td rel="16">16</td>
    # <td>3</td>
    # <td rel="Hart, Josh"><a href="/player/Josh-Hart/Summary/41440">Josh Hart</a></td>
    current_player = ''
    stat_count = 0
    home_team_player_stats = {}
    away_team_player_stats = {}
    players_processed = 0

    for i in away_team_stats:
        if 'href="/player/' in str(i):
            current_player = str(i).split("</a>")[0].split("/Summary/")[1].split('">')[1]
            stat_count = 0
            players_processed += 1

        #ignore starter/bench stat, and do not go beyond 15 stats for the last player
        if stat_count >= 1 and stat_count <= 16:
            if current_player not in away_team_player_stats:
                # found the current player at this index, initiatilize a new array
                away_team_player_stats[current_player] = []
            else:
                if 'rel="' in str(i):
                    away_team_player_stats[current_player].append(str(i).split('">')[1].split('</td')[0])
                else:
                    #player's position, should be first stat_count
                    away_team_player_stats[current_player].append(str(i).split('<td>')[1].split("</td>")[0])
        stat_count += 1


    for i in home_team_stats:
        if 'href="/player/' in str(i):
            current_player = str(i).split("</a>")[0].split("/Summary/")[1].split('">')[1]
            stat_count = 0
            players_processed += 1

        #ignore starter/bench stat, and do not go beyond 15 stats for the last player
        if stat_count >= 1 and stat_count <= 16:
            if current_player not in home_team_player_stats:
                # found the current player at this index, initiatilize a new array
                home_team_player_stats[current_player] = []
            else:
                if 'rel="' in str(i):
                    home_team_player_stats[current_player].append(str(i).split('">')[1].split('</td')[0])
                else:
                    #player's position, should be first stat_count
                    home_team_player_stats[current_player].append(str(i).split('<td>')[1].split("</td>")[0])
        stat_count += 1

    for player in away_team_player_stats:
        update_values('PlayerStats!A'+firstAvailableRow+":R"+firstAvailableRow,"USER_ENTERED", [
            [gameId,
            player,
            awayTeam,
            away_team_player_stats[player][0],
            away_team_player_stats[player][1],
            away_team_player_stats[player][2],
            away_team_player_stats[player][3],
            away_team_player_stats[player][4],
            away_team_player_stats[player][5],
            away_team_player_stats[player][6],
            away_team_player_stats[player][7],
            away_team_player_stats[player][8],
            away_team_player_stats[player][9],
            away_team_player_stats[player][10],
            away_team_player_stats[player][11],
            away_team_player_stats[player][12],
            away_team_player_stats[player][13],
            away_team_player_stats[player][14],
            ]
        ])
        time.sleep(1.1)
        firstAvailableRow = str(int(firstAvailableRow)+1)
    time.sleep(10)
    for player in home_team_player_stats:
        update_values('PlayerStats!A'+firstAvailableRow+":R"+firstAvailableRow,"USER_ENTERED", [
            [gameId,
            player,
            homeTeam,
            home_team_player_stats[player][0],
            home_team_player_stats[player][1],
            home_team_player_stats[player][2],
            home_team_player_stats[player][3],
            home_team_player_stats[player][4],
            home_team_player_stats[player][5],
            home_team_player_stats[player][6],
            home_team_player_stats[player][7],
            home_team_player_stats[player][8],
            home_team_player_stats[player][9],
            home_team_player_stats[player][10],
            home_team_player_stats[player][11],
            home_team_player_stats[player][12],
            home_team_player_stats[player][13],
            home_team_player_stats[player][14],
            ]
        ])
        time.sleep(1.1)
        firstAvailableRow = str(int(firstAvailableRow)+1)
    time.sleep(10)
    return str(firstAvailableRow)

def processFinishedGames(date_string):
    # day_of_nba_games_url = "https://basketball.realgm.com/nba/scores/2023-10-25"
    nba_games_urls = [
        # "https://basketball.realgm.com/nba/scores/2023-10-24",
        # "https://basketball.realgm.com/nba/scores/2023-10-25",
        # "https://basketball.realgm.com/nba/scores/2023-10-26",
        # "https://basketball.realgm.com/nba/scores/2023-10-27",
        # "https://basketball.realgm.com/nba/scores/2023-10-28",
        # "https://basketball.realgm.com/nba/scores/2023-10-29",
        # "https://basketball.realgm.com/nba/scores/2023-10-30",
        # "https://basketball.realgm.com/nba/scores/2023-10-31",
        # "https://basketball.realgm.com/nba/scores/2023-11-01",
        # "https://basketball.realgm.com/nba/scores/2023-11-02",
        # "https://basketball.realgm.com/nba/scores/2023-11-03",
        # "https://basketball.realgm.com/nba/scores/2023-11-04",
        # "https://basketball.realgm.com/nba/scores/2023-11-05",
        # "https://basketball.realgm.com/nba/scores/2023-11-06"
    ]


    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print("starting data refresh at " + str(current_time))

    processed_games = []

    day_of_nba_games_url = "https://basketball.realgm.com/nba/scores/" + str(date_string)

    # for day_of_nba_games_url in nba_games_urls:
    print("parsing a new day of box scores..." + str(date_string))
    response = requests.get(day_of_nba_games_url,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    box_score_links = soup.find_all("a", text=lambda text: text and "Box Score" in text)

    boxScoresFirstAvailableRow = get_first_available_row('BoxScores!A:A')
    playerStatsFirstAvailableRow = get_first_available_row('PlayerStats!A:A')
    print(box_score_links)
    for box_score_link in box_score_links:
        if '/boxscore/' in str(box_score_link):
            if box_score_link not in processed_games:
                processed_games.append(box_score_link)
                url = "https://basketball.realgm.com"+str(box_score_link).split('href="')[1].split('">')[0]
                
                teamPointsStats = parseTeamPoints(url,boxScoresFirstAvailableRow)
                boxScoresFirstAvailableRow = str(int(boxScoresFirstAvailableRow)+1)
                
                gameId = teamPointsStats.split("|")[0]
                awayTeam = teamPointsStats.split("|")[1]
                homeTeam = teamPointsStats.split("|")[2]
                
                playerStatsFirstAvailableRow = parsePlayerStats(url,playerStatsFirstAvailableRow, gameId, awayTeam, homeTeam)

                time.sleep(1.5)
    time.sleep(2.5)

def updateGoogleSpreadsheet():
    print("updating formulas in Google Sheets...")

    from updateGoogleSheets import updateGoogleSheets
    updateGoogleSheets()

def updateSchedule(date_string):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print("refreshing schedule at " + str(current_time))

    update_values("Schedule!A2:D16", "USER_ENTERED", [
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
        ["","","",""],
    ])


    future_games_url = "https://basketball.realgm.com/nba/scores/" + str(date_string)

    response = requests.get(future_games_url,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    future_games = soup.find_all("table", {"class":"unplayed"})
    
    match_ups = []

    for game in future_games:
        game_soup = BeautifulSoup(str(game), 'html.parser')

        #[<div class="team_name"><h3><a href="/nba/teams/Boston-Celtics/2/Rosters/Current/2024">Boston</a></h3></div>, <div class="team_name"><h3><a href="/nba/teams/Philadelphia-Sixers/22/Rosters/Current/2024">Philadelphia</a></h3></div>]
        team_divs = game_soup.find_all("div", {"class": "team_name"})
        
        #<th colspan="3">7:00 PM ET</th>
        game_time = str(game_soup.find("th", {"colspan": "3"})).split('3">\n')[1].split("</th>")[0]
                
        match_up = [date_string, game_time]
        for team in team_divs:
                t = str(team).split('2024">')[1].split("</a>")[0]
                match_up.append(t)
        match_ups.append(match_up)

    firstAvailableRow = get_first_available_row('Schedule!A:A')

    for match in match_ups:
        update_values("Schedule!A"+str(firstAvailableRow)+":N"+str(firstAvailableRow), "USER_ENTERED",
            [
                match
            ]   
        )
        firstAvailableRow = str(int(firstAvailableRow) + 1)
        time.sleep(1.5)


day_to_process = input("What day of the NBA to process? (YYYY-MM-DD) ")
processFinishedGames(day_to_process)
updateGoogleSpreadsheet()

current_time = datetime.datetime.now().strftime('%H:%M:%S')

print("All done. " + str(current_time))

# future_day_in_schedule = input("What's the next day you want to find the NBA schedule for? (YYYY-MM-DD) ")
# updateSchedule(future_day_in_schedule)