import requests
import pymongo
from pymongo import MongoClient

class NBAParser:

	def __init__(self):
		self.client = MongoClient()
		self.NBA = self.client.NBA
		self.playByPlay = self.NBA.playByPlay
		self.home = None
		self.away = None
		self.previousPoints = 0 
		self.previousPointsTeam = None
		self.previousAway = None
		self.previousHome = None
		self.possessions = []

	#get the lineups on the floor for a given play in a given game  
	def getLineup(self, gameID, eventID, depth):
		url = "http://stats.nba.com/stats/locations_getmoments/?gameid=%s&eventid=%s" % (str(gameID), str(eventID))
		if depth > 8:
			print "SportsVu API error : Check lineups!!"
			return False, False
		try:
			data = requests.get(url).json()
		except Exception:
			return self.getLineup(gameID, eventID + 1, depth + 1)
		away = []
		home = []
	
		if not data.has_key('moments'):
			return self.getLineup(gameID, eventID + 1, depth + 1)
		if data['moments'] == [] :
			return self.getLineup(gameID, eventID + 1, depth + 1)
		try:
			for i in range(1,6):
				home.append(data['moments'][0][5][i][1])
			for i in range(6,11):
				away.append(data['moments'][0][5][i][1])
			return home, away
		
		except Exception:
			return self.getLineup(gameID, eventID + 1, depth + 1)

	#Previous points is necessary for possesions w offensive rebounds after free throws 
	def getPoints(self, points):
		pointsFinal = points + self.previousPoints
		self.previousPoints = 0
		return pointsFinal

	def doNothing(self, play, lastPlay):
		return None

	def madeFieldGoal(self, play, lastPlay):
		if play[9] == None:
			if "3PT" in play[7]:
				return {'offense': str(self.home), 'defense': str(self.away), 'points': self.getPoints(3), 'team' : 'home', 'eventID' : play[1]}
			else: 
				return {'offense' : str(self.home) , 'defense' : str(self.away), 'points': self.getPoints(2), 'team' : 'home', 'eventID' : play[1]}
		else:
			if "3PT" in play[9]:
				return {'offense': str(self.away), 'defense' :str(self.home), 'points': self.getPoints(3), 'team' : 'away', 'eventID' : play[1]}
			else: 
				return {'offense': str(self.away), 'defense' : str(self.home), 'points': self.getPoints(2), 'team' : 'away', 'eventID' : play[1]}

	
	def freeThrow(self, play, lastPlay):
		if play[9] == None and not "MISS" in play[7] and ("2 of 2" in play[7] or "3 of 3" in play[7]) :
			return {'offense': str(self.previousHome), 'defense' : str(self.previousAway), 'points': self.getPoints(1), 'team' : 'home', 'eventID' : play[1]}
		
		elif play[7] == None and not "MISS" in play[9] and ("2 of 2" in play[9] or "3 of 3" in play[9]) :
			return {'offense': str(self.previousAway), 'defense' : str(self.previousHome), 'points': self.getPoints(1), 'team' : 'away', 'eventID' : play[1]}
		
		#We want the lineups on the floor when the foul was committed to get the points so we save the here
		elif play[9] == None and not "MISS" in play[7] and ("1 of 2" in play[7] or "1 of 3" in play[7]) :
			self.previousPoints = self.previousPoints + 1
			self.previousPointsTeam = "home"
			self.previousAway = self.away
			self.previousHome =self.home

		elif play[7] == None and not "MISS" in play[9] and ("1 of 2" in play[9] or "1 of 3" in play[9]) :
			self.previousPoints = self.previousPoints + 1
			self.previousPointsTeam = "away"
			self.previousAway = self.away
			self.previousHome =self.home

		elif play[9] == None and not "MISS" in play[7] and "2 of 3" in play[7]:
			self.previousPoints = self.previousPoints + 1
			self.previousPointsTeam = "home"

		elif play[7] == None and not "MISS" in play[9] and "2 of 3" in play[9]:
			self.previousPoints = self.previousPoints + 1
			self.previousPointsTeam = "away"

		elif play[9] == None and "MISS" in play[7] and ("1 of 2" in play[7] or "1 of 3" in play[7] or "2 of 3" in play[7]) :
			self.previousAway = self.away
			self.previousHome =self.home

		elif play[7] == None and "MISS" in play[9] and ("1 of 2" in play[9] or "1 of 3" in play[9] or "2 of 3" in play[9]) :
			self.previousAway = self.away
			self.previousHome =self.home

		#And-one
		elif play[9] == None and not "MISS" in play[7] and "1 of 1" in play[7]:
			last_play = self.possessions[-1]
			del self.possessions[-1]
			last_play['points'] = last_play['points'] + 1
			return last_play
        
		elif play[7] == None and not "MISS" in play[9] and "1 of 1" in play[9]:
			last_play = self.possessions[-1]
			del self.possessions[-1]
			last_play['points'] = last_play['points'] + 1
			return last_play
		
        #technical
		elif play[9] == None and not "MISS" in play[7] and "Technical" in play[7]:
			return {'offense' : str(self.home), 'defense' : str(self.away), 'points': self.getPoints(1), 'team' : 'home', 'eventID' : play[1]}
		
		elif play[7] == None and not "MISS" in play[9] and "Technical" in play[9]: 
			return {'offense' : str(self.away), 'defense' : str(self.home), 'points': self.getPoints(1), 'team' : 'away', 'eventID' : play[1]}
		
		return None

	def rebound(self, play, lastPlay):
		#We only care about defensive rebounds, orebs dont change possession
		if lastPlay[9] != None and "MISS" in lastPlay[9] and play[7] != None :
			return {'offense' : str(self.away), 'defense' : str(self.home), 'points': self.getPoints(0), 'team' : 'away', 'eventID' : play[1]}
		elif lastPlay[7] != None and "MISS" in lastPlay[7] and play[9] != None:   
			return {'offense' : str(self.home), 'defense' : str(self.away), 'points': self.getPoints(0), 'team' : 'home', 'eventID' : play[1]}
	
	def turnover(self, play, lastPlay):
		if play[9] != None and "Turnover" in play[9]:
			return {'offense': str(self.away), 'defense' : str(self.home), 'points': self.getPoints(0), 'team' : 'away', 'eventID' : play[1]}
		elif play[7] != None and "Turnover" in play[7]:
			return {'offense': str(self.home), 'defense' : str(self.away), 'points': self.getPoints(0), 'team' : 'home', 'eventID' : play[1]}

	def substitution(self, play, lastPlay):
		if play[7] == None:
			try:
				self.away.append(play[20])
				self.away.remove(play[13])
			except Exception:
				print "Lineup reset! Away, Play # %s" %(play[1])
				self.home, self.away = self.getLineup(play[0], play[1], 0)
		else:
			try:
				self.home.append(play[20])
				self.home.remove(play[13])
			except Exception:
				print "Lineup reset! Home, Play # %s" %(play[1])
				self.home, self.away = self.getLineup(play[0], play[1], 0)
		if self.home == False:
			return False
		return None

	def quarterChange(self, play, lastPlay):
		previousHome = self.home
		previousAway = self.away
		home, away = self.getLineup(play[0], play[1], 0)
		self.home = home
		self.away = away
		# make sure there aren't previous points that havent been recorded
		# ie. team just got an oreb after making 1 FT and missing 2nd
		# but time expires
		if self.previousPoints != 0:
			if self.previousPointsTeam == "home":
				return {'offense' : str(previousHome), 'defense' : str(previousAway), 'points': self.getPoints(0), 'team' : 'home', 'eventID' : play[1]}
			else:
				return {'offense' : str(previousAway), 'defense' : str(previousHome), 'points': self.getPoints(0), 'team' : 'away', 'eventID' : play[1]}
		

		return None

	def getPlayByPlay(self, gameID):
		self.possessions = []
		url = "http://stats.nba.com/stats/playbyplayv2?EndPeriod=10&EndRange=55800&RangeType=2&Season=2014-15&SeasonType=Regular+Season&StartPeriod=1&StartRange=0&GameID=%s" % (str(gameID)) 
		lastPlay = None
		plays = requests.get(url).json()["resultSets"][0]["rowSet"]
		home = plays[1][16]
		away = plays[1][23]
		awayScore = int(plays[-1][10].split(" - ")[0]) 
		homeScore = int(plays[-1][10].split(" - ")[1]) 
		self.away = []
		self.home = []
		cases = {1 : self.madeFieldGoal, 2 : self.doNothing, 3 : self.freeThrow, 4: self.rebound, 5 : self.turnover, 6 : self.doNothing, 7 : self.doNothing, 8 : self.substitution, 9 : self.doNothing, 10 : self.doNothing, 11: self.doNothing, 12 : self.quarterChange, 13 : self.doNothing, 18 : self.doNothing}
		for play in plays:
			possession = cases[play[2]](play, lastPlay)
			if possession != None:
				if possession == False:
					print "%s omitted" % (str(gameID))
					return False
				self.possessions.append(possession)
			lastPlay = play
		return {'gameID' : gameID, 'home': home, 'away': away, 'homeScore' : homeScore, 'awayScore' : awayScore, 'possessions' : self.possessions}

	def getRange(self, startID, endID):
		for i in range(startID, endID):
			game = parse.getPlayByPlay("00" +str(i))
			homeScore = 0
			awayScore = 0
			if game != False:
				possessions = game['possessions']
				for play in possessions:
					if play['team'] == 'home':
						homeScore = homeScore + play['points']
					elif play['team'] == 'away':
						awayScore = awayScore + play['points']
				if homeScore != game['homeScore'] or awayScore != game['awayScore']:
					print "Error in game #%s, real score: %s - %s, recorded score %s - %s" % (game['gameID'], game['homeScore'], game['awayScore'], homeScore, awayScore)
					self.playByPlay.insert(game)
				else:
					print "%s: %s vs %s : %s - %s" % ((game['gameID'], game['home'], game['away'], homeScore, awayScore))
					self.playByPlay.insert(game)

parse = NBAParser()
parse.getRange(21400001,21401231)