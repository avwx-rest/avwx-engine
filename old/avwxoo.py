#!/usr/bin/python3

##--Michael duPont
##--AVWX-Engine : avwxoo.py
##--Provides and object-oriented wrapper for the avwx.py function library
##--2015-06-24

import avwx , time

fetchErrors = ['HTTP connection error' , 'Station does not exist/Database lookup error' , "Couldn't find the report in page"]

class Report:
	wxDict = {}        #The data dict which holds the parsed report data
	transDict = {}     #The translation dict which holds the translation strings
	rawReport = ''     #The raw report string
	lastError = ''     #The error string if the previously used function returned False
	lastUpdated = None #The time (secs since epoch) when the report was last updated
	def __init__(self , stationID):
		self.stationID = stationID
	def __str__(self):
		return 'Report object for ' + self.stationID
	def __cmp__(self , other):
		return cmp(self.stationID, other.stationID)
	#Returns the data dictionary
	def getData(self):
		return self.wxDict
	#Returns the translation dictionary
	def getTranslation(self):
		return self.transDict
	#Returns a summary string
	def getSummary(self):
		return None
	#Returns the time (secs since epoch) when the report was last updated
	def getUpdateTime(self):
		return self.lastUpdated
	#Returns the formatted datetime string of when the report was last updated
	def getUpdateTimeString(self):
		if self.lastUpdated: return time.strftime('%Y-%m-%dT%H:%M:%SZ' , time.gmtime(self.lastUpdated))
		return None
	#Returns a dictionary containing basic station information
	def getStationInfo(self):
		try:
			return avwx.getInfoForStation(self.stationID)
		except Exception as e:
			self.lastError = str(e)
			return {}

class METAR(Report):
	def __str__(self):
		return 'METAR object for ' + self.stationID
	#Updates the rawReport string from aviationweather.gov
	#Returns True is successful
	def update(self):
		if not self.stationID:
			self.lastError = 'No station ID found'
			return False
		ret = avwx.getMETAR(self.stationID)
		if type(ret) == int:
			self.lastError = fetchErrors[ret]
			return False
		self.rawReport = ret
		self.lastUpdated = time.time()
		return True
	#Updates the report data
	#Returns True if successful
	def parse(self):
		if not self.rawReport:
			self.lastError = 'No report found'
			return False
		try:
			self.wxDict = avwx.parseMETAR(self.rawReport)
			return True
		except Exception as e:
			self.lastError = str(e)
			return False
	#Updates the translation data
	#Returns True if successful
	def translate(self):
		if not self.wxDict:
			self.lastError = 'No parsed data found'
			return False
		try:
			self.transDict = avwx.translateMETAR(self.wxDict)
			return True
		except Exception as e:
			self.lastError = str(e)
			return False
	def getSummary(self):
		if self.transDict: return avwx.createMETARSummary(self.transDict)
		return None

class TAF(Report):
	delim = '<br/>&nbsp;&nbsp;'
	def __str__(self):
		return 'TAF object for ' + self.stationID
	#Updates the rawReport string from aviationweather.gov
	#Returns True is successful
	def update(self):
		if not self.stationID:
			self.lastError = 'No station ID found'
			return False
		ret = avwx.getTAF(self.stationID)
		if type(ret) == int:
			self.lastError = fetchErrors[ret]
			return False
		self.rawReport = ret
		self.lastUpdated = time.time()
		return True
	#Updates the report data
	#Returns True if successful
	def parse(self):
		if not self.rawReport:
			self.lastError = 'No report found'
			return False
		try:
			self.wxDict = avwx.parseTAF(self.rawReport , self.delim)
			return True
		except Exception as e:
			self.lastError = str(e)
			return False
	#Updates the translation data
	#Returns True if successful
	def translate(self):
		if not self.wxDict:
			self.lastError = 'No parsed data found'
			return False
		try:
			self.transDict = avwx.translateTAF(self.wxDict)
			return True
		except Exception as e:
			self.lastError = str(e)
			return False
	def getForecastSummary(self , index):
		if not self.transDict: return None
		if -1 < index < len(self.transDict['Forecast']): return avwx.createTAFLineSummary(self.transDict['Forecast'][index])
		return None

#Sort by stationID:   stations.sort(key=METAR.attrgetter('stationID')) #This is the default __cmp__
#Sort by update time: stations.sort(key=METAR.attrgetter('lastUpdated'))

#Example Main
if __name__ == '__main__':
	station = 'KMCO'
	
	#Example METAR fetching report from server
	m = METAR(station)
	if m.update() and m.parse() and m.translate():
		print('Summary for {0} ({1}) METAR at {2}\nCurrent Flight Conditions - {3}\n{4}'.format(m.stationID , m.getStationInfo()['City'] , m.getUpdateTimeString() , m.getData()['Flight-Rules'] , m.getSummary()))
	else: print(m.lastError)
	
	print('\n')
	
	#Example TAF using a supplied report and delimeter
	t = TAF(station)
	testReport = 'TAF OPLA 180345Z 1806/1912 33008KT 4000 HZ NSC TX42/1810Z TN29/1900Z <br/>&nbsp;&nbsp;PROB30 <br/>&nbsp;&nbsp;TEMPO 1810/1812 32015G25KT 3000 DRDU FM 181500 TL 190100 25003KT 4000 HZ NSC <br/>&nbsp;&nbsp;TEMPO 1901/1903 30004KT 2500 FU'
	testDelimeter = '<br/>&nbsp;&nbsp;'
	t.rawReport = testReport
	t.delim = testDelimeter
	if t.parse() and t.translate():
		print('Summary for {0} ({1}) TAF'.format(t.stationID , t.getStationInfo()['City']))
		wxData = t.getData()
		for i in range(len(wxData['Forecast'])):
			print('From {0} to {1}: Conditions - {2}, {3}'.format(wxData['Forecast'][i]['Start-Time'] , wxData['Forecast'][i]['End-Time'] , wxData['Forecast'][i]['Flight-Rules'] , t.getForecastSummary(i)))
	else: print(t.lastError)
