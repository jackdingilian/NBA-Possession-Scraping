import urllib2
import json
import csv
database = open('possessions.csv', 'w')
players = dict()

def create_player_id_dictionary(season):
    url = "http://stats.nba.com/stats/commonallplayers?LeagueID=00&IsOnlyCurrentSeason=0&Season="+season
    response = None
    while response == None:
        try:
            response = urllib2.urlopen(url)
        except urllib2.URLError, e:
            print e.reason
    data = json.load(response)
    allplayers = data["resultSets"][0]["rowSet"]
    for player in allplayers:
        name = str(player[1]).split(", ")
        if len(name) > 1:
            players[str(player[0])] = name[1] + name[0]
        else:
            players[str(player[0])] = name[0]

#get the game ids for a given date
def get_game_ids(month, day, year):
    if day < 10:
        day = "0" + str(day)
    else:
        day = str(day)
    url = "http://stats.nba.com/stats/scoreboard/?LeagueID=00&gameDate=" + str(month) + "/" + day + "/" + str(year) + "&DayOffset=0"
    print str(month) + "/" + day + "/" + str(year)
    response = None
    while response == None:
        try:
            response = urllib2.urlopen(url)
        except urllib2.URLError, e:
            print e.reason
    data = json.load(response)
    games = data["resultSets"][0]["rowSet"]
    for game in games:
        print game[2]
        get_lineups(game[2])

#get the lineups for each quarter, and overtime if necessary, for a given game
def get_lineups(game_id):
    times = [(10,400), (7210,7500), (14410, 14800), (21610,21900)]
    url ='http://stats.nba.com/stats/boxscore?GameID=' + game_id + '&StartPeriod=0&EndPeriod=10&StartRange=' + str(times[0][0]) + '&EndRange=' + str(times[0][1]) + '&RangeType=2'
    response = None
    while response == None:
        try:
            response = urllib2.urlopen(url)
        except urllib2.URLError, e:
            print e.reason
    data = json.load(response)
    home_team_id = data["resultSets"][0]["rowSet"][0][6]
    away_team_id = data["resultSets"][0]["rowSet"][0][7]
    ot = data["resultSets"][1]["rowSet"][0]
    #game went in 1 OT
    if not ot[11] == 0:
        times.append((28810,29200))
    #game went in 2 OT
    if not ot[12] == 0:
        times.append((31810,32200))
    #game went into 3 OT
    if not ot[13] == 0:
        times.append((34810,35200))
        #game went into 4 OT
    if not ot[14] == 0:
        times.append((37810,38200))
    j = 1 
    lineups = []
    for time in times:
        home = []
        away = []
        url = url ='http://stats.nba.com/stats/boxscore?GameID=' + game_id + '&StartPeriod=0&EndPeriod=10&StartRange=' + str(time[0]) + '&EndRange=' + str(time[1]) + '&RangeType=2'
        response = None

        # I have really bad internet at my house so I use this when it's spotty but be careful
        # because if you're not paying attention this will just loop infinitely if you
        # aren't getting a response.
        while response == None:
            try:
                response = urllib2.urlopen(url)
            except urllib2.URLError, e:
                print e.reason

        data = json.load(response)
        players = data["resultSets"][4]["rowSet"]
        shrink = 50

        # Occasionally there will be an extra player in the given time ranges.  Sometimes there
        # aren't enough or aren't any.  The next two while loops adjust the time ranges to try to
        # find the true lineups.  The api is a little inconsistent so there ar occasionally quarters
        # where you have to stop the script and set the lineups for a quarter manually
        while len(players) > 10:
            # This prints so you can go back and check the data after.  If there are inconsistencies
            # this is where it will be.  
            print len(players)
            print "shrink "  + str(time[0])
            time = (time[0], time[1] - shrink)
            url=  'http://stats.nba.com/stats/boxscore?GameID=' + game_id + '&StartPeriod=0&EndPeriod=10&StartRange=' + str(time[0] ) + '&EndRange=' + str(time[1]) + '&RangeType=2'
            response = None
            while response == None:
                try:
                    response = urllib2.urlopen(url)
                except urllib2.URLError, e:
                    print e.reason
            data = json.load(response)
            players = data["resultSets"][4]["rowSet"]
            shrink = shrink + 50 
            if shrink > 400:
                print "failed 0"
                quit(0)
            for player in players: 
                if player[8] == "0:00":
                    players.remove(player)
        
        while len(players) < 10:
            print len(players)
            print "grow" + str(time[0])
            time = (time[0], time[1] + 20)
            url=  'http://stats.nba.com/stats/boxscore?GameID=' + game_id + '&StartPeriod=0&EndPeriod=10&StartRange=' + str(time[0] ) + '&EndRange=' + str(time[1]) + '&RangeType=2'
            response = None
            while response == None:
                try:
                    response = urllib2.urlopen(url)
                except urllib2.URLError, e:
                    print e.reason
            data = json.load(response)
            players = data["resultSets"][4]["rowSet"]
            if time[1] - time[0] > 1000:
                print "failed 1"
                quit(0)
        j = j + 1

        for i in range (0,5):
            away.append(str(players[i][4]))
        lineups.append(away)
        for i in range (5,10):
            home.append(str(players[i][4]))
        lineups.append(home)
    get_play_by_play(lineups, game_id, home_team_id, away_team_id)


#get the playbyplay data for a given game given the lineups at the start of each quarter
#lineups are passed as a list of lists where each list represents the home or away lineup
# for each quarter in chronological order: lineups[5] would give you the away lineup to 
# start the 3rd quarter.  if length is > 8 then the game went to overtime
def get_play_by_play(lineups, game_id, home_team_id, away_team_id):
    raw = []
    print game_id
    url = "http://stats.nba.com/stats/playbyplayv2?GameID=" + game_id + "&StartPeriod=0&EndPeriod=10"
    response = None
    while response == None: 
        try:            
            response = urllib2.urlopen(url)
        except urllib2.URLError, e:
            print e.reason
    data = json.load(response)
    plays = data["resultSets"][0]["rowSet"] 
    i = 0
    prev_points = 0
    last_play = None
    prev_away = None
    prev_home = None

    #This just puts each play through a giant if else if to take care of substitutions
    # and record the lineups and result of each possession
    for play in plays:

    # play[2] is the EVENTMSGTYPE location in the json
    # 12 represents the start of a new quarter, so we need to change the lineups
        if play[2] == 12:
            away = lineups[i]
            home = lineups[i + 1]
            i = i + 2

        # 8 corresponds to a substitution.  If the description is in play[7] then
        # it is for the home team, otherwise it's for the away team
        elif play[2] == 8:

            if play[7] == None:
                try:                
                    outplayer = str(play[13])
                    inplayer = str(play[20])
                    away.remove(outplayer)
                    away.append(inplayer)
                except:
                    print play[1]
                    print i 
                    print away
                    print outplayer

            else:
                try:
                    outplayer = str(play[13])
                    inplayer = str(play[20])
                    home.remove(outplayer)
                    home.append(inplayer)
                except:
                    print play[1]
                    print i
                    print home
                    print outplayer
                
        # 1 corresponds to a made field goal.  If it is a 3 pointer then 3PT will be in the 
        # description.
        elif play[2] == 1:
            if play[9] == None:
                if "3PT" in play[7]:
                    raw.append([str(game_id), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]], str(3 + prev_points), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]]])
                    prev_points = 0
                else:
                    raw.append([str(game_id), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]], str(2 + prev_points), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]]])
                    prev_points = 0
            else:
                if "3PT" in play[9]:
                    raw.append([str(game_id), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]], str(3 + prev_points), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]]])
                    prev_points = 0
                else:
                    raw.append([str(game_id), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]], str(2 + prev_points), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]]])
                    prev_points = 0
               
        # 3 corresponds to a free throw.  We want to count free throws made from the same foul as 
        # one possession as well as and one free throws. We also want to store the rosters as of 
        # the first free throw attempt so that the players on the floor when the foul is committed
        # are the ones credited with that possession

        elif play[2] == 3:
            if play[9] == None and not "MISS" in play[7] and ("2 of 2" in play[7] or "3 of 3" in play[7]) :
                raw.append([str(game_id), str(home_team_id), players[prev_home[0]], players[prev_home[1]], players[prev_home[2]], players[prev_home[3]], players[prev_home[4]], str(prev_points + 1), str(away_team_id), players[prev_away[0]], players[prev_away[1]], players[prev_away[2]], players[prev_away[3]], players[prev_away[4]]])
                               
                prev_points = 0
            elif play[7] == None and not "MISS" in play[9] and ("2 of 2" in play[9] or "3 of 3" in play[9]) :
                raw.append([str(game_id), str(away_team_id), players[prev_away[0]], players[prev_away[1]], players[prev_away[2]], players[prev_away[3]], players[prev_away[4]], str(prev_points + 1), str(home_team_id), players[prev_home[0]], players[prev_home[1]], players[prev_home[2]], players[prev_home[3]], players[prev_home[4]]])
                prev_points = 0
                
            elif play[9] == None and not "MISS" in play[7] and ("1 of 2" in play[7] or "1 of 3" in play[7]) :
                prev_points = prev_points + 1
                
                prev_away = []
                prev_away.append(away[0])
                prev_away.append(away[1])
                prev_away.append(away[2])
                prev_away.append(away[3])
                prev_away.append(away[4])
                
                prev_home = []
                prev_home.append(home[0])
                prev_home.append(home[1])
                prev_home.append(home[2])
                prev_home.append(home[3])
                prev_home.append(home[4])
            elif play[7] == None and not "MISS" in play[9] and ("1 of 2" in play[9] or "1 of 3" in play[9]) :
                prev_points = prev_points + 1
                
                prev_away = []
                prev_away.append(away[0])
                prev_away.append(away[1])
                prev_away.append(away[2])
                prev_away.append(away[3])
                prev_away.append(away[4])
                
                prev_home = []
                prev_home.append(home[0])
                prev_home.append(home[1])
                prev_home.append(home[2])
                prev_home.append(home[3])
                prev_home.append(home[4])
            elif play[9] == None and not "MISS" in play[7] and "2 of 3" in play[7]:
                prev_points = prev_points + 1
            elif play[7] == None and not "MISS" in play[9] and "2 of 3" in play[9]:
                prev_points = prev_points + 1
            elif play[9] == None and "MISS" in play[7] and ("1 of 2" in play[7] or "1 of 3" in play[7] or "2 of 3" in play[7]) :
                              
                prev_away = []
                prev_away.append(away[0])
                prev_away.append(away[1])
                prev_away.append(away[2])
                prev_away.append(away[3])
                prev_away.append(away[4])
                
                prev_home = []
                prev_home.append(home[0])
                prev_home.append(home[1])
                prev_home.append(home[2])
                prev_home.append(home[3])
                prev_home.append(home[4])
                
                
            elif play[7] == None and "MISS" in play[9] and ("1 of 2" in play[9] or "1 of 3" in play[9] or "2 of 3" in play[9]) :
                              
                prev_away = []
                prev_away.append(away[0])
                prev_away.append(away[1])
                prev_away.append(away[2])
                prev_away.append(away[3])
                prev_away.append(away[4])
                prev_home = []
                prev_home.append(home[0])
                prev_home.append(home[1])
                prev_home.append(home[2])
                prev_home.append(home[3])
                prev_home.append(home[4])
                
            # This is an and one so we want to add one to the last possession
            elif play[9] == None and not "MISS" in play[7] and "1 of 1" in play[7]  :
                last_play = raw[-1]
                last_play[7] = int(last_play[7]) + 1                
                raw = raw[:-1]
                raw.append(last_play)
            #This is a technical
            elif play[9] == None and not "MISS" in play[7] and "Technical" in play[7]:
                raw.append([str(game_id), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]], str(1), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]]])
            elif play[7] == None and not "MISS" in play[9] and "1 of 1" in play[9]:
                last_play = raw[-1]
                last_play[7] = int(last_play[7]) + 1                
                raw = raw[:-1]
                raw.append(last_play)
            elif play[7] == None and not "MISS" in play[9] and "Technical" in play[9]: 
                raw.append([str(game_id),  str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]], str(1), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]]])

        # Record a zero point possession on turnovers
        elif play[2] == 5:
            if play[9] != None and "Turnover" in play[9]: 
                raw.append([str(game_id), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]], str(0), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]]])
            elif play[7] != None and "Turnover" in play[7]:
                raw.append([str(game_id), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]], str(0), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]]])
                
        # 4 corresponds to a rebound.
        elif play[2] == 4 and last_play != None:
            # last play is a missed field goal by the opposite team (Oreb doesnt end possession)
            if last_play[2] == 2 and last_play[9] != None and "MISS" in last_play[9] and play[7] != None :
                raw.append([str(game_id), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]], str(0), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]]])
            elif last_play[2] == 2 and last_play[7] != None and "MISS" in last_play[7] and play[9] != None:    
                raw.append([str(game_id), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]], str(0), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]]])
            #last play is a missed free throw by the opposite team
            elif last_play[2] == 3 and last_play[9] != None and "MISS" in last_play[9] and play[7] != None :
                raw.append([str(game_id), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]], str(prev_points), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]]])
                prev_points = 0
            elif last_play[2] == 3 and last_play[7] != None and "MISS" in last_play[7] and play[9] != None:    
                raw.append([str(game_id), str(home_team_id), players[home[0]], players[home[1]], players[home[2]], players[home[3]], players[home[4]], str(prev_points), str(away_team_id), players[away[0]], players[away[1]], players[away[2]], players[away[3]], players[away[4]]])
                prev_points = 0
                
        last_play = play
    wr = csv.writer(database, quoting=csv.QUOTE_ALL)
    wr.writerows(raw)

create_player_id_dictionary("2013-14")
# You can use get_game_ids to call get_lineups as well but this loops through every
# game of the season
for i in range(21200001,21201231):
    get_lineups("00"+str(i))

