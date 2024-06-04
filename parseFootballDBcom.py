import requests
# import urllib.request
import time
from bs4 import BeautifulSoup, NavigableString
import pandas as pd
import datetime
import socket

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = ''
BETS_SPREADSHEET_ID = ''

HEADERS = {'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148'}

COLUMNNUMBERS = {
    1:"A",
    2:"B",
    3:"C",
    4:"D",
    5:"E",
    6:"F",
    7:"G",
    8:"H",
    9:"I",
    10:"J",
    11:"K",
    12:"L",
    13:"M",
    14:"N",
    15:"O",
    16:"P",
    17:"Q",
    18:"R",
    19:"S",
    20:"T",
    21:"U",
    22:"V",
    23:"W",
    24:"X",
    25:"Y",
    26:"Z",
    27:"AA",
    28:"AB",
    29:"AC",
    30:"AD",
    31:"AE",
    32:"AF",
    33:"AG",
    34:"AH",
    35:"AI",
    36:"AJ",
    37:"AK",
    38:"AL",
    39:"AM",        
    40:"AN"        
}

AwayTeam = ""
HomeTeam = ""



def get_first_available_row(spreadsheet_id, range_name):
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id, range=range_name).execute()

        rows = result.get('values', [])

        firstAvailableRow = 1
        maxGameId = 1

        gameIds = []

        #when the Games tab is blank with just a header row
        if len(rows) > 1:
            for row in rows:
                if row[0] not in gameIds and row[0] != "Game ID":
                    gameIds.append(int(row[0]))
                firstAvailableRow+=1

            maxGameId = max(gameIds) + 1
        else:
            firstAvailableRow = 2

        return str(firstAvailableRow) + "|" + str(maxGameId)
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def get_all_values(spreadsheet_id, range_name, firstColumn, lastColumn):
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)
        request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name+'!'+firstColumn+':'+lastColumn)
        response = request.execute()
        result = response.get('values', [])        
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error



def update_values(spreadsheet_id, range_name, value_input_option,
                  values):
    creds = service_account.Credentials.from_service_account_file(
        'credentials.json', scopes=SCOPES)

    try:
        service = build('sheets', 'v4', credentials=creds)
        body = {
            'values': values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def parseGameData(soup):
    try:
        #get_first_available_row: return str(firstAvailableRow) + "|" + str(maxGameId)
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "Games!A:A")
        gameId = firstAvailableRowTemp.split("|")[1]
        firstAvailableRow = str(firstAvailableRowTemp.split("|")[0])

        leftCol = soup.find('div', {"id":"leftcol"})
        center = leftCol.find('center')
        gameMetadata = center.find("div")

        #<div>September 8, 2022<br/>SoFi Stadium, Inglewood, CA<br/>
        gameDate = str(gameMetadata).split("<br/>")[0].split("<div>")[1]

        update_values(SPREADSHEET_ID,
        "Games!B"+firstAvailableRow, "USER_ENTERED",
            [
                [gameDate]

            ]
        )    

        update_values(SPREADSHEET_ID,
        "Games!A"+firstAvailableRow, "USER_ENTERED",
            [
                [gameId]
            ]
        )    

        scoringSummary = soup.find('table', {'class':'statistics'})

        openHeaderColumn = 3

        #<td>7</td>
        #<td>3</td>
        #<td>7</td>
        #<td>14</td>
        #<td>7</td> (OT)
        #<td><b>31</b></td>

        ignoreFirstRow = True
        quarterCount = 0

        for rows in scoringSummary.find_all('tr'):
            if ignoreFirstRow == False:
                for data in rows.find_all('td'):
                    #team name, away team on top
                    #<td class="left"><a href="/teams/nfl/buffalo-bills/results/2022"><b><span class="hidden-xs">Buffalo Bills</span><span class="visible-xs-inline">Buffalo</span></b></a> (1-0)</td>
                    if len(str(data.contents[0])) > 15:
                        update_values(SPREADSHEET_ID,"Games!"+
                        COLUMNNUMBERS[openHeaderColumn]+firstAvailableRow, "USER_ENTERED",
                            [
                                data.find('span').contents
                            ]
                        )
                        openHeaderColumn+=1
                    #final score is in bold: <b>31</b>, is shown before the home team. Edge case is OT
                    elif '<b>' in str(data.contents[0]):
                        if (quarterCount == 4):
                            openHeaderColumn+=1      
                            update_values(SPREADSHEET_ID,"Games!"+
                            COLUMNNUMBERS[openHeaderColumn]+firstAvailableRow, "USER_ENTERED",
                                [
                                    data.find('b').contents
                                ]
                            )
                            openHeaderColumn+=1      
                            quarterCount = 0
                        else:
                            update_values(SPREADSHEET_ID,"Games!"+
                            COLUMNNUMBERS[openHeaderColumn]+firstAvailableRow, "USER_ENTERED",
                                [
                                    data.find('b').contents
                                ]
                            )
                            openHeaderColumn+=1      
                    #quarter points, with edge case of OT
                    else:          
                        quarterCount+=1
                        update_values(SPREADSHEET_ID,"Games!"+
                        COLUMNNUMBERS[openHeaderColumn]+firstAvailableRow, "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )
                        openHeaderColumn+=1                           
            else:
                ignoreFirstRow = False

        return firstAvailableRowTemp
    except socket.timeout as error:
        print("socket timeout error!")
        return error


def parseBoxScore(soup, gameId):

    try:
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "BoxScores!A:A")
        firstAvailableRow = int(firstAvailableRowTemp.split("|")[0])

        table_div = soup.find('div' , {'id': 'divBox_team' })

        teamStats = table_div.find_all("table", {"class": "statistics"})

        openHeaderColumn = 2
        openSheetRow = 2

        awayTeamRow = firstAvailableRow
        homeTeamRow = firstAvailableRow + 1

        statRow = awayTeamRow

        #[]
        #[<span class="hidden-xs">Jacksonville</span>, <span class="visible-xs-inline">Jax</span>]
        #[<span class="hidden-xs">Washington</span>, <span class="visible-xs-inline">Was</span>]
        #[<b>First downs</b>]
        #['24']
        #['26']
        #['Rushing']
        #['6']
        #['7']


        for statBox in teamStats:

            rows = statBox.find_all('tr')
        
            for row in rows:
                dataPoints = row.find_all('td')
                for data in dataPoints:
                    if data.contents != []:
                        if data.find('span') is not None:
                            #team name
                            #two tables on left and right means only do this twice
                            if openSheetRow <= 3:
                                update_values(SPREADSHEET_ID,"BoxScores!"+
                                "B"+str(firstAvailableRow), "USER_ENTERED",
                                    [
                                        data.find('span').contents
                                    ]
                                )
                                if openSheetRow == 2:
                                    AwayTeam = data.find('span').contents[0]
                                elif openSheetRow == 3:
                                    HomeTeam = data.find('span').contents[0]
                                openSheetRow+=1
                                firstAvailableRow+=1
                        elif (len(str(data.contents[0])) > 6 and "-" not in str(data.contents[0])) or (len(str(data.contents[0])) > 8 and " - " in str(data.contents[0])):
                            #header for a statistic
                            openHeaderColumn+=1     
                            statRow = awayTeamRow                       
                        elif data.find('span') is None:
                            #statistic
                            update_values(SPREADSHEET_ID,"BoxScores!"+
                            COLUMNNUMBERS[openHeaderColumn]+str(statRow), "USER_ENTERED",
                                [
                                    data.contents
                                ]
                            )
                            statRow = homeTeamRow
                    time.sleep(.15)
                time.sleep(1)
            time.sleep(1)
        time.sleep(5)
        # print(tableRows)    

        gameIds = []
        
        for i in range(2):
            gameIds.append([gameId])

        update_values(SPREADSHEET_ID,
        "BoxScores!A"+str(awayTeamRow)+":A"+str((homeTeamRow)), "USER_ENTERED",
                gameIds
        )
        time.sleep(5)
        return HomeTeam + "|" + AwayTeam
    except socket.timeout as error:
        print("socket timeout error!")
        return error


def parsePassingStats(soup, gameId, HomeTeam, AwayTeam):

    try:
        print("parsing " + AwayTeam + " @ " + HomeTeam)

        #get_first_available_row: return str(firstAvailableRow) + "|" + str(maxGameId)
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "PassingStats!A:A")
        firstAvailableRow = int(firstAvailableRowTemp.split("|")[0])
        veryFirstAvailableRow = firstAvailableRow

        openHeaderColumn = 4

        playerStats = soup.find('div' , {'id': 'divBox_stats' })

        # print(playerStats)
        #['Josh Allen'], ['31'], ['26'], ['297'], ['9.6'], ['3'], ['2'], ['53t'], ['2'], ['5'], ['112.0'], ['Matthew Stafford'], ['41'], ['29'], ['240'], ['5.9'], ['1'], ['3'], ['28'], ['7'], ['49'], ['63.1'], ['Josh Allen'], ['10'], ['56'], ['5.60'], ['13'], ['1'], ['4'], ['Devin Singletary'], ['8'], ['48'], ['6.00'], ['13'], ['0'], ['2'], ['Zack Moss'], ['6'], ['15'], ['2.50'], ['8'], ['0'], ['1'],

        #first box score is the away team QB
        awayQBStats = playerStats.find_all('div', {'class': 'boxdiv_visitor'})[0]
        statBoxes = awayQBStats.find("table", {"class": "statistics"}).find_all('tr')

        #statBoxes = [<tr class="header right">
        #<th class="left playercell nowrap"><span class="hidden-xs">Buffalo Bills</span><span class="visible-xs-inline">Buffalo</span></th><th>Att</th><th>Cmp</th><th>Yds</th><th>YPA</th><th>TD</th><th>Int</th><th>Lg</th><th>Sack</th><th>Loss</th><th>Rate</th></tr>, <tr class="row0 right">
        #<td class="left"><span class="hidden-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">Josh Allen</a></span><span class="visible-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">J. Allen</a></span></td><td>31</td><td>26</td><td>297</td><td>9.6</td><td>3</td><td>2</td><td>53t</td><td>2</td><td>5</td><td>112.0</td></tr>]

        #length of statBoxes = 2 when 1 QB plays
        #the first <tr> is the header which we ignore, so we make numberOfQBs = -1 therefore the first iteration of the for loop adds 1 to the count, which makes numberOfQBs = 0 when the real QB stat shows.
        #numberOfQBs would then be 1 when the next QB appears in the stats, therefore it goes to the next row as expected
        
        numberOfQBs = -1

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    #<td class="left"><span class="hidden-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">Josh Allen</a></span><span class="visible-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">J. Allen</a></span></td>
                    update_values(SPREADSHEET_ID,"PassingStats!"+
                    "B"+str(firstAvailableRow+numberOfQBs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )           
                    update_values(SPREADSHEET_ID,"PassingStats!"+
                    "C"+str(firstAvailableRow+numberOfQBs), "USER_ENTERED",
                        [
                            [AwayTeam]
                        ]
                    )           
                            
                else:
                    #statistic

                    #longest pass sometimes have a T, assuming it means tied for longest pass
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"PassingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfQBs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"PassingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfQBs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1   
                    time.sleep(.13)
                time.sleep(1.12)
            numberOfQBs += 1
            openHeaderColumn = 4
            time.sleep(3.1)

        time.sleep(10)

        openHeaderColumn = 4
        #subtract the header <tr> in the home team box score
        numberOfQBs -= 1

        #second box score is home team QB
        homeQBStats = playerStats.find_all('div', {'class': 'boxdiv_home'})[0]
        statBoxes = homeQBStats.find("table", {"class": "statistics"}).find_all('tr')

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    update_values(SPREADSHEET_ID,"PassingStats!"+
                    "B"+str(firstAvailableRow+numberOfQBs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )                    
                    update_values(SPREADSHEET_ID,"PassingStats!"+
                    "C"+str(firstAvailableRow+numberOfQBs), "USER_ENTERED",
                        [
                            [HomeTeam]
                        ]
                    )                                    
                else:
                    #statistic
                    #solve t in the longest passing yards
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"PassingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfQBs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"PassingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfQBs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1    
            numberOfQBs+=1
            openHeaderColumn = 4
            time.sleep(3)

        time.sleep(5)
        gameIds = []
        
        for i in range(numberOfQBs):
            gameIds.append([gameId])

        update_values(SPREADSHEET_ID,
        "PassingStats!A"+str(veryFirstAvailableRow)+":A"+str((firstAvailableRow+numberOfQBs-1)), "USER_ENTERED",
                gameIds
        )
        time.sleep(3)
    except socket.timeout as error:
        print("socket timeout error!")
        return error

def parseRushingStats(soup, gameId, HomeTeam, AwayTeam):
    try: 
        #get_first_available_row: return str(firstAvailableRow) + "|" + str(maxGameId)
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "RushingStats!A:A")
        firstAvailableRow = int(firstAvailableRowTemp.split("|")[0])
        veryFirstAvailableRow = firstAvailableRow

        openHeaderColumn = 4

        playerStats = soup.find('div' , {'id': 'divBox_stats' })

        # print(playerStats)
        #['Josh Allen'], ['31'], ['26'], ['297'], ['9.6'], ['3'], ['2'], ['53t'], ['2'], ['5'], ['112.0'], ['Matthew Stafford'], ['41'], ['29'], ['240'], ['5.9'], ['1'], ['3'], ['28'], ['7'], ['49'], ['63.1'], ['Josh Allen'], ['10'], ['56'], ['5.60'], ['13'], ['1'], ['4'], ['Devin Singletary'], ['8'], ['48'], ['6.00'], ['13'], ['0'], ['2'], ['Zack Moss'], ['6'], ['15'], ['2.50'], ['8'], ['0'], ['1'],

        #seond box score is the away team RBs
        awayRBStats = playerStats.find_all('div', {'class': 'boxdiv_visitor'})[1]
        statBoxes = awayRBStats.find("table", {"class": "statistics"}).find_all('tr')

        numberOfRBs = -1

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    #<td class="left"><span class="hidden-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">Josh Allen</a></span><span class="visible-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">J. Allen</a></span></td>
                    update_values(SPREADSHEET_ID,"RushingStats!"+
                    "B"+str(firstAvailableRow+numberOfRBs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )      
                    update_values(SPREADSHEET_ID,"RushingStats!"+
                    "C"+str(firstAvailableRow+numberOfRBs), "USER_ENTERED",
                        [
                            [AwayTeam]
                        ]
                    )                                   
                else:
                    #statistic
                    #longest pass sometimes have a T, assuming it means tied for longest pass
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"RushingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfRBs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"RushingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfRBs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1   
                time.sleep(.25)
            numberOfRBs += 1
            openHeaderColumn = 4
            time.sleep(3.28)

        time.sleep(10)

        openHeaderColumn = 4
        #subtract the header <tr> in the home team box score
        numberOfRBs -= 1

        #second box score is home team QB
        homeRBStats = playerStats.find_all('div', {'class': 'boxdiv_home'})[1]
        statBoxes = homeRBStats.find("table", {"class": "statistics"}).find_all('tr')

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    update_values(SPREADSHEET_ID,"RushingStats!"+
                    "B"+str(firstAvailableRow+numberOfRBs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )      
                    update_values(SPREADSHEET_ID,"RushingStats!"+
                    "C"+str(firstAvailableRow+numberOfRBs), "USER_ENTERED",
                        [
                            [HomeTeam]
                        ]
                    )                                    
                else:
                    #statistic
                    #solve t in the longest passing yards
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"RushingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfRBs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"RushingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfRBs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1   
                time.sleep(.21)
            numberOfRBs+=1
            openHeaderColumn = 4
            time.sleep(2)

        time.sleep(3)

        gameIds = []
        
        for i in range(numberOfRBs):
            gameIds.append([gameId])

        update_values(SPREADSHEET_ID,
        "RushingStats!A"+str(veryFirstAvailableRow)+":A"+str((firstAvailableRow+numberOfRBs-1)), "USER_ENTERED",
                gameIds
        )
    except socket.timeout as error:
        print("socket timeout error!")
        return error


def parseReceivingStats(soup, gameId, HomeTeam, AwayTeam):

    try:
        #get_first_available_row: return str(firstAvailableRow) + "|" + str(maxGameId)
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "ReceivingStats!A:A")
        firstAvailableRow = int(firstAvailableRowTemp.split("|")[0])
        veryFirstAvailableRow = firstAvailableRow

        openHeaderColumn = 4

        playerStats = soup.find('div' , {'id': 'divBox_stats' })

        #third box score is the away team WRs
        awayWRStats = playerStats.find_all('div', {'class': 'boxdiv_visitor'})[2]
        statBoxes = awayWRStats.find("table", {"class": "statistics"}).find_all('tr')

        numberOfWRs = -1

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    #<td class="left"><span class="hidden-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">Josh Allen</a></span><span class="visible-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">J. Allen</a></span></td>
                    update_values(SPREADSHEET_ID,"ReceivingStats!"+
                    "B"+str(firstAvailableRow+numberOfWRs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )     
                    update_values(SPREADSHEET_ID,"ReceivingStats!"+
                    "C"+str(firstAvailableRow+numberOfWRs), "USER_ENTERED",
                        [
                            [AwayTeam]
                        ]
                    )                                    
                else:
                    #statistic
                    #longest pass sometimes have a T, assuming it means tied for longest pass
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"ReceivingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfWRs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"ReceivingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfWRs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1   
                time.sleep(.32)
            numberOfWRs += 1
            openHeaderColumn = 4
            time.sleep(3.3)

        time.sleep(20)

        openHeaderColumn = 4
        numberOfWRs -= 1

        #second box score is home team QB
        homeWRStats = playerStats.find_all('div', {'class': 'boxdiv_home'})[2]
        statBoxes = homeWRStats.find("table", {"class": "statistics"}).find_all('tr')

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    update_values(SPREADSHEET_ID,"ReceivingStats!"+
                    "B"+str(firstAvailableRow+numberOfWRs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )        
                    update_values(SPREADSHEET_ID,"ReceivingStats!"+
                    "C"+str(firstAvailableRow+numberOfWRs), "USER_ENTERED",
                        [
                            [HomeTeam]
                        ]
                    )                              
                else:
                    #statistic
                    #solve t in the longest passing yards
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"ReceivingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfWRs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"ReceivingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfWRs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1   
                time.sleep(.32)
            numberOfWRs+=1
            openHeaderColumn = 4
            time.sleep(3.52)

        time.sleep(5.75)

        gameIds = []
        
        for i in range(numberOfWRs):
            gameIds.append([gameId])

        update_values(SPREADSHEET_ID,
        "ReceivingStats!A"+str(veryFirstAvailableRow)+":A"+str((firstAvailableRow+numberOfWRs-1)), "USER_ENTERED",
                gameIds
        )
    except socket.timeout as error:
        print("socket timeout error!")
        return error


def parseKickingStats(soup, gameId, HomeTeam, AwayTeam):
    
    try: 
        #get_first_available_row: return str(firstAvailableRow) + "|" + str(maxGameId)
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "KickingStats!A:A")
        firstAvailableRow = int(firstAvailableRowTemp.split("|")[0])
        veryFirstAvailableRow = firstAvailableRow

        openHeaderColumn = 4

        awayTeamRow = 2

        playerStats = soup.find('div' , {'id': 'divBox_stats' })

        #seventh box score is the away team kickers
        awayKStats = playerStats.find_all('div', {'class': 'boxdiv_visitor'})[6]
        statBoxes = awayKStats.find("table", {"class": "statistics"}).find_all('tr')

        numberOfKs = -1

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    #<td class="left"><span class="hidden-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">Josh Allen</a></span><span class="visible-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">J. Allen</a></span></td>
                    update_values(SPREADSHEET_ID,"KickingStats!"+
                    "B"+str(firstAvailableRow+numberOfKs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )     
                    update_values(SPREADSHEET_ID,"KickingStats!"+
                    "C"+str(firstAvailableRow+numberOfKs), "USER_ENTERED",
                        [
                            [AwayTeam]
                        ]
                    )                                    
                else:
                    #statistic
                    #longest kick sometimes have a T, assuming it means tied for longest kick
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"KickingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfKs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"KickingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfKs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1   
            numberOfKs += 1
            openHeaderColumn = 4
            time.sleep(3)

        time.sleep(5)

        openHeaderColumn = 4
        numberOfKs -= 1

        #second box score is home team QB
        homeKStats = playerStats.find_all('div', {'class': 'boxdiv_home'})[6]
        statBoxes = homeKStats.find("table", {"class": "statistics"}).find_all('tr')

        for rows in statBoxes:
            for data in rows.find_all('td'):
                if len(str(data.contents[0])) > 7:
                    #player name
                    update_values(SPREADSHEET_ID,"KickingStats!"+
                    "B"+str(firstAvailableRow+numberOfKs), "USER_ENTERED",
                        [
                            data.find('a').contents
                        ]
                    )   
                    update_values(SPREADSHEET_ID,"KickingStats!"+
                    "C"+str(firstAvailableRow+numberOfKs), "USER_ENTERED",
                        [
                            [HomeTeam]
                        ]
                    )                                    
                else:
                    #statistic
                    #solve t in the longest passing yards
                    if 't' in data.contents[0]:
                        update_values(SPREADSHEET_ID,"KickingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfKs)), "USER_ENTERED",
                            [
                                [data.contents[0].split('t')[0]]
                            ]
                        )
                    else:
                        update_values(SPREADSHEET_ID,"KickingStats!"+
                        COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfKs)), "USER_ENTERED",
                            [
                                data.contents
                            ]
                        )          
                    openHeaderColumn+=1    
            numberOfKs+=1
            openHeaderColumn = 4
            time.sleep(3)

        gameIds = []
        
        for i in range(numberOfKs):
            gameIds.append([gameId])

        update_values(SPREADSHEET_ID,
        "KickingStats!A"+str(veryFirstAvailableRow)+":A"+str((firstAvailableRow+numberOfKs-1)), "USER_ENTERED",
                gameIds
        )
    except socket.timeout as error:
        print("socket timeout error!")
        return error

def parseDefenseStats(soup, gameId, HomeTeam, AwayTeam):

    try:
        #get_first_available_row: return str(firstAvailableRow) + "|" + str(maxGameId)
        firstAvailableRowTemp = get_first_available_row(SPREADSHEET_ID, "DefenseStats!A:A")
        firstAvailableRow = int(firstAvailableRowTemp.split("|")[0])
        veryFirstAvailableRow = firstAvailableRow

        openHeaderColumn = 4

        awayTeamRow = 2

        playerStats = soup.find('div' , {'id': 'divBox_stats' })

        #seventh box score is the away team kickers
        awayDStats = playerStats.find_all('div', {'class': 'boxdiv_visitor'})[8]
        statBoxes = awayDStats.find("table", {"class": "statistics"}).find_all('tr')

        numberOfDs = -1 

        for rows in statBoxes:
            # print(rows.find_all('td'))
            if rows.find_all('td') != [] and isinstance(rows.find_all('td')[0].contents[0].contents[0],NavigableString) == False:
                for data in rows.find_all('td'):
                    #edge case of Team in the defense stats for no reason
                    if len(str(data.contents[0])) > 7 and data.find('a') is not None:
                        #player name
                        #<td class="left"><span class="hidden-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">Josh Allen</a></span><span class="visible-xs"><a href="/players/josh-allen-allenjo06" title="Josh Allen Stats">J. Allen</a></span></td>
                        update_values(SPREADSHEET_ID,"DefenseStats!"+
                        "B"+str(firstAvailableRow+numberOfDs), "USER_ENTERED",
                            [
                                data.find('a').contents
                            ]
                        )      
                        update_values(SPREADSHEET_ID,"DefenseStats!"+
                        "C"+str(firstAvailableRow+numberOfDs), "USER_ENTERED",
                            [
                                [AwayTeam]
                            ]
                        )                                    
                    else:
                        #statistic
                        #longest kick sometimes have a T, assuming it means tied for longest kick
                        if 't' in data.contents[0]:
                            update_values(SPREADSHEET_ID,"DefenseStats!"+
                            COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfDs)), "USER_ENTERED",
                                [
                                    [data.contents[0].split('t')[0]]
                                ]
                            )
                        else:
                            update_values(SPREADSHEET_ID,"DefenseStats!"+
                            COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfDs)), "USER_ENTERED",
                                [
                                    data.contents
                                ]
                            )          
                        openHeaderColumn+=1  
                    time.sleep(.29)
            else:
                time.sleep(.1)
                # print("Team defense stat, skipping!") 
            numberOfDs += 1
            openHeaderColumn = 4
            time.sleep(4)
        time.sleep(20)

        homeTeamRow = awayTeamRow + numberOfDs    

        openHeaderColumn = 4
        numberOfDs -= 1

        #second box score is home team QB
        homeDStats = playerStats.find_all('div', {'class': 'boxdiv_home'})[8]
        statBoxes = homeDStats.find("table", {"class": "statistics"}).find_all('tr')

        for rows in statBoxes:
            if rows.find_all('td') != [] and isinstance(rows.find_all('td')[0].contents[0].contents[0],NavigableString) == False:
                for data in rows.find_all('td'):
                    # print(data.contents[0])
                    # if "Team" not in data.contents[0] and '<span' not in data:
                    #     print("REAL ROW")
                    # else:
                    #     print("TEAM ROW")
                    if len(str(data.contents[0])) > 7 and data.find('a') is not None:
                        # real player with a link, not a Team
                        update_values(SPREADSHEET_ID,"DefenseStats!"+
                        "B"+str(firstAvailableRow+numberOfDs), "USER_ENTERED",
                            [
                                data.find('a').contents
                            ]
                        )                    
                        update_values(SPREADSHEET_ID,"DefenseStats!"+
                        "C"+str(firstAvailableRow+numberOfDs), "USER_ENTERED",
                            [
                                [HomeTeam]
                            ]
                        )    
                    elif len(str(data.contents[0])) < 7:
                        #statistic
                        #solve t in the longest passing yards
                        if 't' in data.contents[0]:
                            update_values(SPREADSHEET_ID,"DefenseStats!"+
                            COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfDs)), "USER_ENTERED",
                                [
                                    [data.contents[0].split('t')[0]]
                                ]
                            )
                        else:
                            update_values(SPREADSHEET_ID,"DefenseStats!"+
                            COLUMNNUMBERS[openHeaderColumn]+str((firstAvailableRow+numberOfDs)), "USER_ENTERED",
                                [
                                    data.contents
                                ]
                            )      
                        openHeaderColumn+=1    
                    time.sleep(.32)
            numberOfDs+=1
            openHeaderColumn = 4
            time.sleep(4.07)

        time.sleep(5)

        gameIds = []
        
        for i in range(numberOfDs):
            gameIds.append([gameId])

        update_values(SPREADSHEET_ID,
        "DefenseStats!A"+str(veryFirstAvailableRow)+":A"+str((firstAvailableRow+numberOfDs-1)), "USER_ENTERED",
                gameIds
        )
    except socket.timeout as error:
        print("socket timeout error!")
        return error

def processURL(url):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print("scraping new game at " + str(current_time))

    response = requests.get(url,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    firstAvailableRowTemp = parseGameData(soup)
    gameId = firstAvailableRowTemp.split("|")[1]

    homeTeamAwayTeam = parseBoxScore(soup,gameId)
    HomeTeam = homeTeamAwayTeam.split("|")[0]
    AwayTeam = homeTeamAwayTeam.split("|")[1]

    parsePassingStats(soup,gameId,HomeTeam,AwayTeam)
    parseRushingStats(soup,gameId,HomeTeam,AwayTeam)
    parseReceivingStats(soup,gameId,HomeTeam,AwayTeam)
    parseKickingStats(soup,gameId,HomeTeam,AwayTeam)
    # parseDefenseStats(soup,gameId,HomeTeam,AwayTeam)

    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print("ending scraping at " + str(current_time))

def updateSchedule(week_number):
    original_schedule = get_all_values(SPREADSHEET_ID, 'Schedule', 'A', 'M')

    update_values(SPREADSHEET_ID, 'PreviousWeek!A1:M33', "USER_ENTERED",
        original_schedule)

    update_values(SPREADSHEET_ID, "Schedule!A2:G33", "USER_ENTERED", [
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
        ["","","","","","",""],
    ])

    next_week = int(week_number)+1

    nextWeek = "https://www.footballdb.com/scores/index.html?lg=NFL&yr=2023&type=reg&wk="+str(next_week)
    response = requests.get(nextWeek,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    schedule = []

    matchups = soup.find_all('div' , {'class': 'lngame' })
    print("finding the times, days and days of week for the next week games....")
    for matchup in matchups:
        # print(matchup)
        awayTeam = str(matchup).split("row-visitor")[1].split('Schedule">')[1].split("</a>")[0]
        homeTeam = str(matchup).split("row-home")[1].split('Schedule">')[1].split("</a>")[0]

        dayOfWeek = str(matchup).split('width:70%;">')[1].split(",")[0]
        # print(dayOfWeek)

        date = str(matchup).split('width:70%;">')[1].split(", ")[1] + "," + str(matchup).split('width:70%;">')[1].split(",")[2].split("</th>")[0]
        # print(date)

        timeOfDay = str(matchup).split('width:30%;">')[1].split("</th>")[0]
        # print(timeOfDay)
        schedule.append([{awayTeam:homeTeam}, date, dayOfWeek, timeOfDay])
    print("done finding the times, days and days of week for the next week games....")
    rowNumberToUpdate = 2

    for game in schedule:
        print("updating schedule... " + str(list(game[0].keys())[0]) + " @ " + str(list(game[0].values())[0]))
        update_values(SPREADSHEET_ID, "Schedule!A"+str(rowNumberToUpdate), "USER_ENTERED", [
                [str(list(game[0].keys())[0]), str(list(game[0].values())[0]), str(next_week), str(list(game[0].values())[0]), str(game[1]), str(game[2]), str(game[3])] 
            ]
        )
        update_values(SPREADSHEET_ID, "Schedule!A"+str(rowNumberToUpdate+1), "USER_ENTERED", [
                [str(list(game[0].values())[0]), str(list(game[0].keys())[0]), str(next_week), str(list(game[0].values())[0]), str(game[1]), str(game[2]), str(game[3])] 
            ]
        )
        rowNumberToUpdate += 2
        time.sleep(0.65)

def updateTemplate_Predictions_Result(week_number):
    try:
        print("copying the predictions to the TEMPLATE_PREDICTIONS_RESULT...")
        #update week predicted, week to find actuals
        update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!C2', "USER_ENTERED",
            [[week_number]])
        time.sleep(0.10)
        update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!D2', "USER_ENTERED",
            [[week_number]])
        time.sleep(0.10)

        #find predictions from TEMPLATE_PREDICTIONS before the template is updated with the next week of predictions
        previous_week_prediction_rushing_yards_matchup = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'P', 'P')
        previous_week_prediction_passing_yards_matchup = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'Q', 'Q')
        previous_week_prediction_rushing_yards_sos = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'V', 'V')
        previous_week_prediction_passing_yards_sos = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'W', 'W')
        previous_week_prediction_sacks_forced_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AA', 'AA')
        previous_week_prediction_rushing_yards_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AE', 'AE')
        previous_week_prediction_passing_yards_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AI', 'AI')
        previous_week_prediction_interceptions_thrown_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AM', 'AM')
        previous_week_prediction_fumbles_lost_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AQ', 'AQ')
        previous_week_prediction_yards_per_play_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AU', 'AU')
        previous_week_prediction_first_downs_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'AY', 'AY')
        previous_week_prediction_third_down_percentage_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'BC', 'BC')
        previous_week_prediction_rushing_tds_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'BG', 'BG')
        previous_week_prediction_passing_tds_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'BK', 'BK')
        previous_week_prediction_rushing_passing_tds_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'BM', 'BM')
        previous_week_prediction_sacks_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'BV', 'BV')
        previous_week_prediction_rushing_yards_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'BX', 'BX')
        previous_week_prediction_passing_yards_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'CD', 'CD')
        previous_week_prediction_interceptions_caught_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'CH', 'CH')
        previous_week_prediction_fumbles_forced_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'CL', 'CL')
        previous_week_prediction_yards_per_play_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'CP', 'CP')
        previous_week_prediction_first_downs_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'CZ', 'CZ')
        previous_week_prediction_third_down_percentage_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'DD', 'DD')
        previous_week_prediction_rushing_tds_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'DH', 'DH')
        previous_week_prediction_passing_tds_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'DL', 'DL')
        previous_week_prediction_rushing_passing_tds_allowed_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'DN', 'DN')
        previous_week_prediction_team_turnover_difference_kpi = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'DS', 'DS')

        #update columns with predictions
        update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!E:E', "USER_ENTERED", previous_week_prediction_rushing_yards_matchup)
        time.sleep(0.15)
        update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!I:I', "USER_ENTERED", previous_week_prediction_passing_yards_matchup)
        time.sleep(0.15)
        update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!M:M', "USER_ENTERED", previous_week_prediction_rushing_yards_sos)
        time.sleep(0.15)
        update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!Q:Q', "USER_ENTERED", previous_week_prediction_passing_yards_sos)
        time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!U:U', "USER_ENTERED", previous_week_prediction_sacks_forced_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!W:W', "USER_ENTERED", previous_week_prediction_rushing_yards_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!Y:Y', "USER_ENTERED", previous_week_prediction_passing_yards_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AA:AA', "USER_ENTERED", previous_week_prediction_interceptions_thrown_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AC:AC', "USER_ENTERED", previous_week_prediction_fumbles_lost_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AE:AE', "USER_ENTERED", previous_week_prediction_yards_per_play_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AG:AG', "USER_ENTERED", previous_week_prediction_first_downs_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AI:AI', "USER_ENTERED", previous_week_prediction_third_down_percentage_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AK:AK', "USER_ENTERED", previous_week_prediction_rushing_tds_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AM:AM', "USER_ENTERED", previous_week_prediction_passing_tds_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AO:AO', "USER_ENTERED", previous_week_prediction_rushing_passing_tds_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AQ:AQ', "USER_ENTERED", previous_week_prediction_sacks_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AS:AS', "USER_ENTERED", previous_week_prediction_rushing_yards_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AU:AU', "USER_ENTERED", previous_week_prediction_passing_yards_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AW:AW', "USER_ENTERED", previous_week_prediction_interceptions_caught_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AY:AY', "USER_ENTERED", previous_week_prediction_fumbles_forced_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AS:AS', "USER_ENTERED", previous_week_prediction_yards_per_play_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AU:AU', "USER_ENTERED", previous_week_prediction_first_downs_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AW:AW', "USER_ENTERED", previous_week_prediction_third_down_percentage_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!AY:AY', "USER_ENTERED", previous_week_prediction_rushing_tds_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!BA:BA', "USER_ENTERED", previous_week_prediction_passing_tds_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!BC:BC', "USER_ENTERED", previous_week_prediction_rushing_passing_tds_allowed_kpi)
        # time.sleep(0.15)
        # update_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT!BE:BE', "USER_ENTERED", previous_week_prediction_team_turnover_difference_kpi)
        # time.sleep(0.15)

        print("successfully values-only pasted the predictions from TEMPLATE_PREDICTIONS to TEMPLATE_PREDICTIONS_RESULT for week " + str(week_number))
    except HttpError as error:
        print("error has occurred: " + error)

def updateTemplate_Actuals(week_number):
    try:
        print("filling out the Actuals for week " + str(week_number))
        #update actuals with the latest week processed
        update_values(SPREADSHEET_ID, 'TEMPLATE_ACTUALS!A2', "USER_ENTERED", [[str(week_number)]])
        print("Actuals updated with the results of week " + str(week_number))
    except HttpError as error:
        print("error has occurred: " + error)

def transferSheetsToBetsSpreadsheet(week_number):
    try:    
        print("updating `NFL Bets` spreadsheet with the templates...")
        creds = service_account.Credentials.from_service_account_file(
            'credentials.json', scopes=SCOPES)

        service = build('sheets', 'v4', credentials=creds)

        next_week = int(week_number) + 1

        #get values for sheets to transfer
        template_predictions = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS', 'A', 'EC')
        template_bets = get_all_values(SPREADSHEET_ID, 'TEMPLATE_BETS', 'A', 'U')
        template_actuals = get_all_values(SPREADSHEET_ID, 'TEMPLATE_ACTUALS', 'A', 'AG')
        template_predictions_result = get_all_values(SPREADSHEET_ID, 'TEMPLATE_PREDICTIONS_RESULT', 'A', 'BO')
        template_bets_result = get_all_values(SPREADSHEET_ID, 'TEMPLATE_BETS_RESULT', 'A', 'AN')
        template_ranking_mismatches = get_all_values(SPREADSHEET_ID, 'TEMPLATE_RANKING_MISMATCHES', 'A', 'W')

        # Define the names for the new sheets
        new_sheet_names = [
            'Week' + str(week_number) + 'Actuals', 
            'Week' + str(week_number) + 'Predictions_Result', 
            'Week' + str(week_number) + 'Bets_Result', 
            'Week' + str(next_week) + 'Predictions', 
            'Week' + str(next_week) + 'Bets',
            'Week' + str(next_week) + 'RankingMismatches']

        # Create requests to add new sheets
        add_sheet_requests = [{'addSheet': {'properties': {'title': name}}} for name in new_sheet_names]

        # Send the requests to create new sheets
        request = service.spreadsheets().batchUpdate(spreadsheetId=BETS_SPREADSHEET_ID, body={
            'requests': add_sheet_requests
        })
        response = request.execute()

        data_sets = [
            template_actuals,
            template_predictions_result,
            template_bets_result,
            template_predictions,
            template_bets,
            template_ranking_mismatches
        ]

        # Update the new sheets with the different data sets
        for i, name in enumerate(new_sheet_names):
            values = data_sets[i]
            data = [{'range': f'{name}!A1', 'values': values}]
            request = service.spreadsheets().values().batchUpdate(spreadsheetId=BETS_SPREADSHEET_ID, body={'valueInputOption': 'RAW', 'data': data})
            response = request.execute()
        print("finished updating `NFL Bets` with latest actuals, predictions result, bets result, predictions, bets, and ranking mismatches")
        
        #update Weeks tab with the upcoming week number
        request = service.spreadsheets().values().batchUpdate(spreadsheetId=BETS_SPREADSHEET_ID, body={'valueInputOption': 'RAW', 'data': [{'range': 'Weeks!A2', 'values':[[str(next_week)]]}]})
        response = request.execute()
        print("updated `NFL Bets` Weeks tab with the upcoming week number. This is used in the frontend to find the week with bets/predictions.")

    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


def processWeek(week_number):
    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print("starting data refresh at " + str(current_time))

    weekURL = "https://www.footballdb.com/scores/index.html?lg=NFL&yr=2023&type=reg&wk="+str(week_number)
    response = requests.get(weekURL,headers=HEADERS)
    soup = BeautifulSoup(response.text,'html.parser')

    linksToBoxScores = soup.find_all('div' , {'class': 'sbgmlinx' })


    urls = []

    for link in linksToBoxScores:
        #<div class="sbgmlinx"><a href="/games/boxscore/las-vegas-raiders-vs-los-angeles-rams-2023081906" title="Raiders vs Rams Box Score - August 19, 2023"><b>Raiders vs Rams Box Score</b></a></div>
        href = str(link).split('href="')[1].split('" title="')[0]
        urls.append("https://www.footballdb.com" + href)

    #update the TEMPLATE_PREDICTIONS_RESULT before TEMPLATE_PREDICTIONS is overwritten with the next week of predictions
    updateTemplate_Predictions_Result(week_number)

    for url in urls:
        processURL(url)


    #when the Schedule is updated, TEMPLATE_PREDICTIONS, TEMPLATE_BETS are overwritten
    #when the Schedule is updated, PreviousWeek is overwritten, causing TEMPLATE_ACTUALS to update with the new Next Opponent
    #Note: TEMPLATE_ACTUALS should update on its own. TODO: copy the TEMPLATE_ACTUALS, TEMPLATE_PREDICTIONS_RESULT, TEMPLATE_BETS_RESULT to NFL Bets spreadsheet (separate spreadsheet)
    updateSchedule(week_number)


    #drag formulas down & across newly-created rows across tabs Games, BoxScores, RushingStats, PassingStats, etc.
    from updateGoogleSheets import updateGoogleSheets
    updateGoogleSheets()

    

    #update the Week to Find Actuals in TEMPLATE_ACTUALS so that the formulas utilize the latest scrape using the opponent in the freshly-updated PreviousWeek tab.
    updateTemplate_Actuals(week_number)
    
    #let the TEMPLATE_ACTUALS formulas update now that the Week has updated
    time.sleep(15)
    print("Letting the TEMPLATE_ACTUALS formulas update with the latest week...") 

    #update the NFL Bets spreadsheet with the five templates
    transferSheetsToBetsSpreadsheet(week_number)

    #populate Lines tab with closing lines from the week that just finished, opening lines of next week
    from parseESPNcom import parseESPNcom
    parseESPNcom(week_number)

    current_time = datetime.datetime.now().strftime('%H:%M:%S')
    print("ending data refresh at " + str(current_time))


week_to_process = input("Which week to process? ")
processWeek(week_to_process)

