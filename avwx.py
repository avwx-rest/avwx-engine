##--Michael duPont
##--METAR-RasPi : avwx.py
##--Shared METAR settings and functions
##--2015-05-19

# This file contains a series of functions and variables that are shared with
# mplate and mscreen. This file can also be used in any project that needs a
# means of fetching and/or interpretting METAR and TAF weather data.
#
# While the list of functions is rather large, here are the most useful:
#    getMETAR(station)  Returns METAR report for a given station
#    getTAF(station)   Returns TAF report for a given station
#    parseMETAR(txt)    Returns a key-value dictionary where 'txt' is the report getMETAR returns
#    parseTAF(txt)      Returns a key-value dictionary where 'txt' is the report getTAF returns
#    translateWX(wx)    Translates METAR weather codes into readable strings. +VCTS -> Heavy Vicinity Thunderstorm
#    getFlightRules(vis , splitCloud)
#         Returns int corresponding to flight rules index in flightRules
#         Standard usage states that the current rule is IFR if visibility value is not available
#         vis is string of visibility distance value
#         splitCloud is the ceiling is the format [type,height,modifier]
#         Typical usage:     flightRules[getFlightRules(parsedReport['Visibility'] , getCeiling(parsedReport['Cloud-List']))]
#         Usage with values: flightRules[getFlightRules('8' , ['BKN','014',''])] -> 'MVFR'
#
# Both METAR and TAF reports come in the Standard/International variant and
# the North American variant. parseMETAR and parseTAF automatically figure out
# which parser variant to use, but you're welcome to use the variant functions
# directly if you want. Just know that parsing errors will arise if the
# International parser tries to parse a US report.
#
# Example usage for both METAR and TAF can be found at the bottom of the file.
# You can run this test code by running this file: python mlogic.py

import string , time , sys
if sys.version_info[0] == 2: import urllib2
elif sys.version_info[0] == 3: from urllib.request import urlopen
else: print("Cannot load urllib in avwx.py")
from itertools import permutations

##--Logic Vars
flightRules = ['VFR','MVFR','IFR','LIFR']
cloudList = ['FEW','SCT','BKN','OVC']
charList = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','0','1','2','3','4','5','6','7','8','9']
wxReplacements = {
'RA':'Rain','TS':'Thunderstorm','SH':'Showers','DZ':'Drizzle','VC':'Vicinity','UP':'Unknown Precip',
'SN':'Snow','FZ':'Freezing','SG':'Snow Grains','IC':'Ice Crystals','PL':'Ice Pellets','GR':'Hail','GS':'Small Hail',
'FG':'Fog','BR':'Mist','HZ':'Haze','VA':'Volcanic Ash','DU':'Wide Dust','FU':'Smoke','SA':'Sand','SY':'Spray',
'SQ':'Squall','PO':'Dust Whirls','DS':'Duststorm','SS':'Sandstorm','FC':'Funnel Cloud',
'BL':'Blowing','MI':'Shallow','BC':'Patchy','PR':'Partial','UP':'Unknown'}

metarRMKStarts = [' BLU',' BLU+',' WHT',' GRN',' YLO',' AMB',' RED',' BECMG',' TEMPO',' INTER',' NOSIG',' RMK',' WIND',' QFE',' INFO',' RWY']
tafRMKStarts = ['RMK ','AUTOMATED ','COR ','AMD ','LAST ','FCST ','CANCEL ','CHECK ','WND ','MOD ',' BY']
tafNewLineStarts = [' INTER ' , ' FM' , ' BECMG ' , ' TEMPO ']

##--Station Location Identifiers
RegionsUsingUSParser = ['C', 'K', 'M', 'P', 'T']
RegionsUsingInternationalParser = ['A', 'B', 'D', 'E', 'F', 'G', 'H', 'L', 'M', 'N', 'O', 'R', 'S', 'U', 'V', 'W', 'Y', 'Z']
#The Central American region is split. Therefore we need to use the first two letters
MStationsUsingUSParser = ['MB', 'MD', 'MK', 'MM', 'MT', 'MU', 'MW', 'MY']
MStationsUsingInternationalParser = ['MG', 'MH', 'MN', 'MP', 'MR', 'MS', 'MZ']

#Get METAR report for 'station' from www.aviationweather.gov
#Returns METAR report string
#Else returns error int
#0=Bad connection , 1=Station DNE/Server Error
def getMETAR(station):
	try:
		if sys.version_info[0] == 2:
			response = urllib2.urlopen('http://www.aviationweather.gov/metar/data?ids='+station+'&format=raw&date=0&hours=0')
			html = response.read()
		elif sys.version_info[0] == 3:
			response = urlopen('http://www.aviationweather.gov/metar/data?ids='+station+'&format=raw&date=0&hours=0')
			html = response.read().decode('utf-8')
		if html.find(station+'<') != -1: return 1   #Station does not exist/Database lookup error
		reportStart = html.find('<code>'+station+' ')+6      #Report begins with station iden
		reportEnd = html[reportStart:].find('<')        #Report ends with html bracket
		return html[reportStart:reportStart+reportEnd].replace('\n ','')
	except:
		return 0

#Returns the index of the earliest occurence of an item from a list in a string
def findFirstInList(txt,aList):
	startIndex = len(txt)+1
	for item in aList:
		if -1 < txt.find(item) < startIndex: startIndex = txt.find(item)
	if -1 < startIndex < len(txt)+1: return startIndex
	return -1

#Remove remarks and split
#Remarks can include RMK and on, NOSIG and on, and BECMG and on
def __getRemarks(txt):
	txt = txt.replace('?' , '').strip(' ')
	#First look for Altimeter in txt
	altIndex = len(txt)+1
	for item in [' A2',' A3',' Q1',' Q0']:
		index = txt.find(item)
		if -1 < index < len(txt)-6 and txt[index+2:index+6].isdigit(): altIndex = index
	#Then look for earliest remarks 'signifier'
	sigIndex = findFirstInList(txt , metarRMKStarts)
	if sigIndex == -1: sigIndex = len(txt)+1
	if -1 < altIndex < sigIndex: return txt[:altIndex+6].strip().split(' ') , txt[altIndex+7:]
	elif -1 < sigIndex < altIndex: return txt[:sigIndex].strip().split(' ') , txt[sigIndex+1:]
	return txt.strip().split(' ') , ''

#Return True if a space shouldn't exist between two items
#This list grew so large that it had to be moved to its own function for readability
def extraSpaceExists(s1 , s2):
	if s1.isdigit():
		# 10 SM
		if s2 == 'SM' and s1.isdigit(): return True
		# 12 /10
		if len(s2) > 2 and s2[0] == '/' and s1[1:].isdigit(): return True
	if s2.isdigit():
		# OVC 040
		if s1 in cloudList: return True
		# 12/ 10
		if len(s1) > 2 and s1[len(s1)-1] == '/' and s1[:len(s1)-1].isdigit(): return True
	# 36010G20 KT
	if s2 == 'KT' and (s1[:5].isdigit() or (s1[:3] == 'VRB' and s1[3:5].isdigit())): return True
	# 36010K T
	if s2 == 'T' and len(s1) == 6 and (s1[:5].isdigit() or (s1[:3] == 'VRB' and s1[3:5].isdigit())) and s1[5] == 'K': return True
	# FM 122400
	if s1 == 'FM' and (s2.isdigit() or (s2[len(s2)-1] == 'Z' and s2[:len(s2)-1])): return True
	return False

#Sanitize wxData
#We can remove and identify "one-off" elements and fix other issues before parsing a line
#We also return the runway visibility and wind shear since they are very easy to recognize
#and their location in the report is non-standard
visPermutations = [''.join(p) for p in permutations('P6SM')]
def __sanitize(wxData , removeCLRandSKC=True):
	runwayVisibility , shear = '' , ''
	for i in reversed(range(len(wxData))):
		#Remove elements containing only '/'
		if wxData[i].strip('/') == '':
			wxData.pop(i)
		#Identify Runway Visibility
		elif len(wxData[i]) > 4 and wxData[i][0] == 'R' and (wxData[i][3] == '/' or wxData[i][4] == '/') and wxData[i][1:3].isdigit():
			runwayVisibility = wxData.pop(i)
		#Remove RE from wx codes, REVCTS -> VCTS
		elif len(wxData[i]) in [4,6] and wxData[i][:2] == 'RE':
			wxData.pop(i)
		#Fix a slew of easily identifiable conditions where a space does not belong
		elif i != 0 and extraSpaceExists(wxData[i-1] , wxData[i]):
			wxData[i-1] += wxData.pop(i)
		#Remove spurious elements
		elif wxData[i] in ['AUTO' , 'COR' , 'NSC' , 'NCD' , '$' , 'KT' , 'M' , '.']:
			wxData.pop(i)
		#Remove 'Sky Clear' from METAR but not TAF
		elif removeCLRandSKC and wxData[i] in ['CLR' , 'SKC']:
			wxData.pop(i)
		#Remove ammend signifier from start of report ('CCA','CCB',etc)
		elif len(wxData[i]) == 3 and wxData[i][:2] == 'CC' and wxData[i][2].isalpha():
			wxData.pop(i)
		#Identify WInd Shear
		elif len(wxData[i]) > 6 and wxData[i][:2] == 'WS' and wxData[i].find('/') != -1:
			shear = wxData.pop(i)
		#Fix inconsistant 'P6SM' Ex: TP6SM or 6PSM -> P6SM
		elif len(wxData[i]) > 3 and wxData[i][len(wxData[i])-4:] in visPermutations:
			wxData[i] = 'P6SM'
		#Fix joined TX-TN
		elif len(wxData[i]) > 16 and len(wxData[i].split('/')) == 3:
			if wxData[i][:2] == 'TX' and wxData[i].find('TN') != -1:
				wxData.insert(i+1 , wxData[i][:wxData[i].find('TN')])
				wxData[i] = wxData[i][wxData[i].find('TN'):]
			elif wxData[i][:2] == 'TN' and wxData[i].find('TX') != -1:
				wxData.insert(i+1 , wxData[i][:wxData[i].find('TX')])
				wxData[i] = wxData[i][wxData[i].find('TX'):]
	return wxData , runwayVisibility , shear
	
#Altimeter
def __getAltimeterUS(wxData):
	altimeter = ''
	#Get altimeter
	if wxData and (wxData[len(wxData)-1][0] == 'A' or wxData[len(wxData)-1][0] == 'Q'): altimeter = wxData.pop()
	elif wxData and len(wxData[len(wxData)-1]) == 4 and wxData[len(wxData)-1].isdigit(): altimeter = wxData.pop()
	#Some stations report both, but we only need one
	if wxData and (wxData[len(wxData)-1][0] == 'A' or wxData[len(wxData)-1][0] == 'Q'): wxData.pop()
	return wxData , altimeter

def __getAltimeterInternational(wxData):
	altimeter = ''
	#Get altimeter
	if wxData and (wxData[len(wxData)-1][0] == 'A' or wxData[len(wxData)-1][0] == 'Q'): altimeter = wxData.pop()
	#Some stations report both, but we only need one
	if wxData and (wxData[len(wxData)-1][0] == 'A' or wxData[len(wxData)-1][0] == 'Q'): wxData.pop()
	return wxData , altimeter

def __getTAFAltIceTurb(wxData):
	altimeter = ''
	icing , turbulence = [] , []
	for i in reversed(range(len(wxData))):
		if len(wxData[i]) > 6 and wxData[i][:3] == 'QNH' and wxData[i][3:7].isdigit():
			altimeter = wxData.pop(i)[3:7]
		elif wxData[i].isdigit():
			if wxData[i][0] == '6': icing.append(wxData.pop(i))
			elif wxData[i][0] == '5': turbulence.append(wxData.pop(i))
	return wxData , altimeter , icing , turbulence

#Temp/Dewpoint
def __getTempAndDewpoint(wxData):
	if wxData and (wxData[len(wxData)-1].find('/') != -1):
		TD = wxData.pop().split('/')
		return wxData , TD[0] , TD[1]
	return wxData , '' , ''

#Station and Time
def __getStationAndTime(wxData):
	station = wxData.pop(0)
	if wxData and len(wxData[0]) == 7 and wxData[0][6] == 'Z' and wxData[0][:6].isdigit(): time = wxData.pop(0)
	elif wxData and len(wxData[0]) == 6 and wxData[0].isdigit(): time = wxData.pop(0)
	else: time = ''
	return wxData , station , time

#Surface wind
#Occasionally KT is not included. Check len=5 and is not altimeter. Check len>=8 and contains G (gust)
def __getWindInfo(wxData):
	direction , speed , gust , shear = '' , '' , '' , ''
	variable = []
	if wxData and ((wxData[0][len(wxData[0])-2:] == 'KT') or (wxData[0][len(wxData[0])-3:] == 'KTS') or (len(wxData[0]) == 5 and wxData[0].isdigit()) or (len(wxData[0]) >= 8 and wxData[0].find('G') != -1 and wxData[0].find('/') == -1 and wxData[0].find('MPS') == -1)):
		direction = wxData[0][:3]
		if wxData[0].find('G') != -1:
			gust = wxData[0][wxData[0].find('G')+1:wxData[0].find('KT')]
			speed = wxData[0][3:wxData[0].find('G')]
		else: speed = wxData[0][3:wxData[0].find('KT')]
		wxData.pop(0)
	elif wxData and wxData[0][len(wxData[0])-3:] == 'MPS':
		direction = wxData[0][:3]
		if wxData[0].find('G') != -1:
			gust = wxData[0][wxData[0].find('G')+1:wxData[0].find('MPS')]
			speed = wxData[0][3:wxData[0].find('G')]
		else: speed = wxData[0][3:wxData[0].find('MPS')]
		wxData.pop(0)
	elif wxData and len(wxData[0]) > 5 and wxData[0][3] == '/' and  wxData[0][:3].isdigit() and  wxData[0][3:5].isdigit():
		direction = wxData[0][:3]
		if wxData[0].find('G') != -1:
			gIndex = wxData[0].find('G')
			gust = wxData[0][gIndex+1:gIndex+3]
			speed = wxData[0][4:wxData[0].find('G')]
		else:
			speed = wxData[0][4:]
		wxData.pop(0)
	#Separated Gust
	if wxData and 1 < len(wxData[0]) < 4 and wxData[0][0] == 'G' and wxData[0][1:].isdigit():
		gust = wxData.pop(0)[1:]
	#Variable Wind Direction
	if wxData and len(wxData[0]) == 7 and wxData[0][:3].isdigit() and wxData[0][3] == 'V' and wxData[0][4:].isdigit():
		variable = wxData.pop(0).split('V')
	return wxData , direction , speed , gust , variable

#Visibility
def __getVisibility(wxData):
	visibility = ''
	if wxData and (wxData[0].find('SM') != -1):   #10SM
		if wxData[0] == 'P6SM': visibility = 'P6'
		elif wxData[0].find('/') == -1: visibility = str(int(wxData[0][:wxData[0].find('SM')]))  #str(int()) fixes 01SM
		else: visibility = wxData[0][:wxData[0].find('SM')] #1/2SM
		wxData.pop(0)
	#Vis reported in meters
	elif wxData and len(wxData[0]) == 4 and wxData[0].isdigit(): visibility = wxData.pop(0)
	elif wxData and len(wxData[0]) == 5 and wxData[0][:4].isdigit() and wxData[0][4] == 'M': visibility = wxData.pop(0)[:4]
	elif (len(wxData) > 1) and wxData[1].find('SM') != -1 and wxData[0].isdigit():   #2 1/2SM
		vis1 = wxData.pop(0)  #2
		vis2 = wxData[0][:wxData[0].find('SM')]  #1/2
		wxData.pop(0)
		visibility = str(int(vis1)*int(vis2[2])+int(vis2[0]))+vis2[1:]  #5/2
	return wxData , visibility

def __getTypeAndTimes(wxData):
	reportType , startTime , endTime = 'BASE' , '' , ''
	#TEMPO, BECMG, INTER
	if wxData and wxData[0] in ['TEMPO','BECMG','INTER']: reportType = wxData.pop(0)
	#PROB[30,40]
	elif wxData and len(wxData[0]) == 6 and wxData[0][:4] == 'PROB': reportType = wxData.pop(0)
	#1200/1306
	if wxData and len(wxData[0]) == 9 and wxData[0][4] == '/' and wxData[0][:4].isdigit() and wxData[0][5:].isdigit():
		times = wxData.pop(0).split('/')
		startTime , endTime = times[0] , times[1]
	#FM120000
	elif wxData and len(wxData[0]) == 8 and wxData[0][:2] == 'FM' and wxData[0][2:].isdigit():
		reportType = 'FROM'
		startTime = wxData.pop(0)[2:6]
	#FM120000
	elif wxData and len(wxData[0]) == 9 and wxData[0][:2] == 'FM' and wxData[0][2:6].isdigit() and wxData[0][8] == 'Z':
		reportType = 'FROM'
		startTime = wxData.pop(0)[2:6]
	#FM1200/1306
	elif wxData and len(wxData[0]) == 11 and wxData[0][:2] == 'FM' and wxData[0][2:6].isdigit() and wxData[0][6] == '/' and wxData[0][7:].isdigit():
		reportType = 'FROM'
		startTime = wxData[0][2:6]
		endTime = wxData.pop(0)[7:11]
	return wxData , reportType , startTime , endTime

#Fix rare cloud layer issues
def sanitizeCloud(cloud):
	if len(cloud) < 4: return cloud
	if not cloud[3].isdigit() and cloud[3] != '/':
		if cloud[3] == 'O': cloud[3] == '0'  #Bad "O": FEWO03 -> FEW003
		else:  #Move modifiers to end: BKNC015 -> BKN015C
			cloud = cloud[:3] + cloud[4:] + cloud[3]
	return cloud

#Transforms a cloud string into a list of strings: [Type , Height (, Optional Modifier)]
#Returns cloud string list
def splitCloud(cloud, beginsWithVV):
	splitCloud = []
	cloud = sanitizeCloud(cloud)
	if beginsWithVV:
		splitCloud.append(cloud[:2])
		cloud = cloud[2:]
	while len(cloud) >= 3:
		splitCloud.append(cloud[:3])
		cloud = cloud[3:]
	if cloud: splitCloud.append(cloud)
	return splitCloud

#Clouds
def __getClouds(wxData):
	clouds = []
	for i in reversed(range(len(wxData))):
		if wxData[i][:3] in cloudList:
			clouds.append(splitCloud(wxData.pop(i) , False))
		elif wxData[i][:2] == 'VV':
			clouds.append(splitCloud(wxData.pop(i) , True))
	clouds.reverse()
	return wxData , clouds

#Returns a dictionary of parsed METAR data
#Keys: Station, Time, Wind-Direction, Wind-Speed, Wind-Gust, Wind-Variable-Dir, Visibility, Runway-Visibility, Altimeter, Temperature, Dewpoint, Cloud-List, Other-List, Remarks, Raw-Report
def parseMETAR(txt):
	if len(txt) < 2: return
	if txt[0] in RegionsUsingUSParser: return parseUSMETAR(txt)
	elif txt[0] in RegionsUsingInternationalParser: return parseInternationalMETAR(txt)
	elif txt[:2] in MStationsUsingUSParser: return parseUSMETAR(txt)
	elif txt[:2] in MStationsUsingInternationalParser: return parseInternationalMETAR(txt)

def parseUSMETAR(txt):
	retWX = {'Raw-Report':txt}
	wxData , retWX['Remarks'] = __getRemarks(txt)
	wxData , retWX['Runway-Visibility'] , notUsed = __sanitize(wxData)
	wxData , retWX['Altimeter'] = __getAltimeterUS(wxData)
	wxData , retWX['Temperature'] , retWX['Dewpoint'] = __getTempAndDewpoint(wxData)
	wxData , retWX['Station'] , retWX['Time'] = __getStationAndTime(wxData)
	wxData , retWX['Wind-Direction'] , retWX['Wind-Speed'] , retWX['Wind-Gust'] , retWX['Wind-Variable-Dir'] = __getWindInfo(wxData)
	wxData , retWX['Visibility'] = __getVisibility(wxData)
	retWX['Other-List'] , retWX['Cloud-List'] = __getClouds(wxData)
	return retWX

def parseInternationalMETAR(txt):
	retWX = {'Raw-Report':txt}
	wxData , retWX['Remarks'] = __getRemarks(txt)
	wxData , retWX['Runway-Visibility'] , notUsed = __sanitize(wxData)
	wxData , retWX['Altimeter'] = __getAltimeterInternational(wxData)
	wxData , retWX['Temperature'] , retWX['Dewpoint'] = __getTempAndDewpoint(wxData)
	wxData , retWX['Station'] , retWX['Time'] = __getStationAndTime(wxData)
	wxData , retWX['Wind-Direction'] , retWX['Wind-Speed'] , retWX['Wind-Gust'] , retWX['Wind-Variable-Dir'] = __getWindInfo(wxData)
	if 'CAVOK' in wxData:
		retWX['Visibility'] = '9999'
		retWX['Cloud-List'] = []
		wxData.pop(wxData.index('CAVOK'))
	else:
		wxData , retWX['Visibility'] = __getVisibility(wxData)
		wxData , retWX['Cloud-List'] = __getClouds(wxData)
	retWX['Other-List'] = wxData #Other weather
	return retWX

#Returns int based on current flight rules from parsed METAR data
#0=VFR , 1=MVFR , 2=IFR , 3=LIFR
#Note: Common practice is to report IFR if visibility unavailable
def getFlightRules(vis , splitCloud):
	#Parse visibility
	if vis == '': return 2
	elif vis == 'P6': vis = 10
	elif vis.find('/') != -1:
		if vis[0] == 'M': vis = 0
		else: vis = int(vis.split('/')[0]) / int(vis.split('/')[1])
	elif len(vis) == 4 and vis.isdigit(): vis = int(vis) * 0.000621371  #Convert meters to miles
	else: vis = int(vis)
	#Parse ceiling
	if splitCloud: cld = int(splitCloud[1])
	else: cld = 99
	#Determine flight rules
	if (vis < 5) or (cld < 30):
		if (vis < 3) or (cld < 10):
			if (vis < 1) or (cld < 5):
				return 3 #LIFR
			return 2 #IFR
		return 1 #MVFR
	return 0 #VFR

#Returns list of ceiling layer from Cloud-List or None if none found
#Only 'Broken', 'Overcast', and 'Vertical Visibility' are considdered ceilings
#Prevents errors due to lack of cloud information (eg. '' or 'FEW///')
def getCeiling(clouds):
	for cloud in clouds:
		if len(cloud) > 1 and cloud[1].isdigit() and cloud[0] in ['OVC','BKN','VV']:
			return cloud
	return None

#Translates METAR weather codes into readable strings
#Returns translated string of variable length
def translateWX(wx):
	wxString = ''
	if wx[0] == '+':
		wxString = 'Heavy '
		wx = wx[1:]
	elif wx[0] == '-':
		wxString = 'Light '
		wx = wx[1:]
	if len(wx) not in [2,4,6]: return wx  #Return wx if wx is not a code, ex R03/03002V03
	for i in range(len(wx)//2):
		if wx[:2] in wxReplacements: wxString += wxReplacements[wx[:2]] + ' '
		else: wxString += wx[:2]
		wx = wx[2:]
	return wxString

#Adds timestamp to begining of print statement
#Returns string of time + logString
def timestamp(logString): return time.strftime('%d %H:%M:%S - ') + logString



####################################################################################################################################

def getTAF(station):
	try:
		if sys.version_info[0] == 2:
			response = urllib2.urlopen('http://www.aviationweather.gov/taf/data?ids=' + station + '&format=raw&submit=Get+TAF+data')
			html = response.read()
		elif sys.version_info[0] == 3:
			response = urlopen('http://www.aviationweather.gov/taf/data?ids=' + station + '&format=raw&submit=Get+TAF+data')
			html = response.read().decode('utf-8')
		if html.find(station+'<') != -1: return 1                             #Station does not exist/Database lookup error
		reportStart = html.find('<code>TAF ')+6                               #Standard report begins with 'TAF'
		if reportStart == 5: reportStart = html.find('<code>'+station+' ')+6  #US report begins with station iden
		if reportStart == 5: return 2                                         #Beginning of report is non-standard/skewed
		reportEnd = html[reportStart:].find('</code>')                        #Report ends with html bracket
		return html[reportStart:reportStart+reportEnd].replace('\n ','')
	except:
		return 0

#Returns a dictionary of parsed TAF data
#'delim' is the divider between forecast lines. Ex: aviationweather.gov uses ' <br/>&nbsp;&nbsp;'
#Keys: Station, Time, Forecast, Remarks, Min-Temp, Max-Temp, Raw-Report
#PNG stations also have the following keys: Temp-List, Alt-List
#Forecast is list of report dicts in order of time with the following keys:
#Type , Start-Time, End-Time, Wind-Direction, Wind-Speed, Wind-Gust, Wind-Shear, Visibility, Altimeter, Cloud-List, Icing-List, Turb-List, Other-List, Probability, Raw-Line
#Min/Max-Temp is list: [temp , time]
def parseTAF(txt , delim):
	retWX = {}
	retWX['Raw-Report'] = txt
	while len(txt) > 3 and txt[:4] in ['TAF ' , 'AMD ' , 'COR ']: txt = txt[4:]
	notUsed , retWX['Station'] , retWX['Time'] = __getStationAndTime(txt[:20].split(' '))
	txt = txt.replace(retWX['Station'] , '')
	txt = txt.replace(retWX['Time'] , '')
	retWX['Remarks'] = ''
	parsedLines = []
	prob = ''
	lines = txt.strip(' ').split(delim)
	while len(lines) > 0:
		line = lines[0].strip(' ')
		line = __sanitizeLine(line)
		#Remove Remarks from line
		index = findFirstInList(line , tafRMKStarts)
		if index != -1:
			retWX['Remarks'] = line[index:]
			line = line[:index].strip(' ')
		#Separate new lines fixed by sanitizeLine
		index = findFirstInList(line , tafNewLineStarts)
		if index != -1:
			lines.insert(1 , line[index+1:])
			line = line[:index]
		#Add empty PROB to next line data
		rawLine = line
		if len(line) == 6 and line[:4] == 'PROB':
			prob = line
			line = ''
		if line:
			if retWX['Station'][0] in RegionsUsingUSParser: parsedLine = parseUSTAFLine(line)
			elif retWX['Station'][0] in RegionsUsingInternationalParser: parsedLine = parseInternationalTAFLine(line)
			elif retWX['Station'][:2] in MStationsUsingUSParser: parsedLine = parseUSTAFLine(line)
			elif retWX['Station'][:2] in MStationsUsingInternationalParser: parsedLine = parseInternationalTAFLine(line)
			parsedLine['Probability'] = prob
			parsedLine['Raw-Line'] = rawLine
			prob = ''
			parsedLines.append(parsedLine)
		lines.pop(0)
	#print(parsedLines)
	if parsedLines:
		parsedLines[len(parsedLines)-1]['Other-List'] , retWX['Max-Temp'] , retWX['Min-Temp'] = getTempMinAndMax(parsedLines[len(parsedLines)-1]['Other-List'])
		if not (retWX['Max-Temp'] or retWX['Min-Temp']): parsedLines[0]['Other-List'] , retWX['Max-Temp'] , retWX['Min-Temp'] = getTempMinAndMax(parsedLines[0]['Other-List'])
		parsedLines = findMissingTAFTimes(parsedLines)
		parsedLines = getTAFFlightRules(parsedLines)
	else:
		retWX['Min-Temp'] = ['','']
		retWX['Max-Temp'] = ['','']
	if retWX['Station'][0] == 'A': parsedLines[len(parsedLines)-1]['Other-List'] , retWX['Alt-List'] , retWX['Temp-List'] = getAusTandQ(parsedLines[len(parsedLines)-1]['Other-List'])
	retWX['Forecast'] = parsedLines
	return retWX

def parseUSTAFLine(txt):
	retWX = {}
	wxData = txt.split(' ')
	wxData , notUsed , retWX['Wind-Shear'] = __sanitize(wxData , removeCLRandSKC=False)
	wxData , retWX['Type'] , retWX['Start-Time'] , retWX['End-Time'] = __getTypeAndTimes(wxData)
	wxData , retWX['Wind-Direction'] , retWX['Wind-Speed'] , retWX['Wind-Gust'] , notUsed = __getWindInfo(wxData)
	wxData , retWX['Visibility'] = __getVisibility(wxData)
	wxData , retWX['Cloud-List'] = __getClouds(wxData)
	retWX['Other-List'] , retWX['Altimeter'] , retWX['Icing-List'] , retWX['Turb-List'] = __getTAFAltIceTurb(wxData)
	return retWX
	
def parseInternationalTAFLine(txt):
	retWX = {}
	wxData = txt.split(' ')
	wxData , notUsed , retWX['Wind-Shear'] = __sanitize(wxData , removeCLRandSKC=False)
	wxData , retWX['Type'] , retWX['Start-Time'] , retWX['End-Time'] = __getTypeAndTimes(wxData)
	wxData , retWX['Wind-Direction'] , retWX['Wind-Speed'] , retWX['Wind-Gust'] , notUsed = __getWindInfo(wxData)
	if 'CAVOK' in wxData:
		retWX['Visibility'] = '9999'
		retWX['Cloud-List'] = []
		wxData.pop(wxData.index('CAVOK'))
	else:
		wxData , retWX['Visibility'] = __getVisibility(wxData)
		wxData , retWX['Cloud-List'] = __getClouds(wxData)
	retWX['Other-List'] , retWX['Altimeter'] , retWX['Icing-List'] , retWX['Turb-List'] = __getTAFAltIceTurb(wxData)
	return retWX

#Fixes common mistakes with 'new line' signifiers so that they can be recognized
lineFixes = {'TEMP0':'TEMPO','TEMP O':'TEMPO','TMPO':'TEMPO','TE MPO':'TEMPO','TEMP ':'TEMPO ',' EMPO':' TEMPO','TEMO':'TEMPO','TMPO':'TEMPO','T EMPO':'TEMPO','BECM G':'BECMG','BEMCG':'BECMG','BE CMG':'BECMG','BEMG':'BECMG',' BEC ':' BECMG ','BCEMG':'BECMG'}
def __sanitizeLine(txt):
	for key in lineFixes:
		index = txt.find(key)
		if index > -1: txt = txt[:index] + lineFixes[key] + txt[index+len(key):]
	#Fix when space is missing following new line signifiers
	for item in ['BECMG' , 'TEMPO']:
		if txt.find(item) != -1 and txt.find(item + ' ') == -1:
			insertIndex = txt.find(item)+len(item)
			txt = txt[:insertIndex] + ' ' + txt[insertIndex:]
	return txt

def splitTAFTemp(temp):
	temp = temp.split('/')
	return [temp[0] , temp[1].replace('Z' , '')]

def getTempMinAndMax(otherList):
	tempMax , tempMin  = [] , []
	popList = []
	for i , item in enumerate(otherList):
		if len(item) > 8 and item[0] == 'T' and item.find('/') != -1:
			if item[:2] == 'TX' and (item[2:4].isdigit() or (item[2] == 'M' and item[3:5].isdigit())):
				tempMax = splitTAFTemp(item[2:])
				popList.append(i)
			elif item[:2] == 'TN' and (item[2:4].isdigit() or (item[2] == 'M' and item[3:5].isdigit())):
				tempMin = splitTAFTemp(item[2:])
				popList.append(i)
			elif item[1:3].isdigit() or (item[1] == 'M' and item[2:4].isdigit()):
				if not tempMax: tempMax = splitTAFTemp(item[1:])
				else: tempMin = splitTAFTemp(item[1:])
				popList.append(i)
	for i in reversed(popList): otherList.pop(i)
	if tempMax and tempMin and int(tempMax[0].replace('M' , '-')) < int(tempMin[0].replace('M' , '-')): tempMax , tempMin = tempMin , tempMax
	return otherList , tempMax , tempMin

def getDigitList(aList , fromIndex):
	retList = []
	aList.pop(fromIndex)
	while len(aList) > fromIndex and aList[fromIndex].isdigit(): retList.append(aList.pop(fromIndex))
	return aList , retList

#Get Temp and Alt list for Australian TAFs
def getAusTandQ(otherList):
	tList , qList = [] , []
	if 'T' in otherList: otherList , tList = getDigitList(otherList , otherList.index('T'))
	if 'Q' in otherList: otherList , qList = getDigitList(otherList , otherList.index('Q'))
	return otherList , tList , qList

#Fix any missing time issues (except for error/empty lines)
def findMissingTAFTimes(tafLines):
	lastFMLine = 0
	for i , line in enumerate(tafLines):
		if line['End-Time'] == '' and isNotTempoOrProb(line['Type']):
			lastFMLine = i
			if i < len(tafLines)-1:
				for report in tafLines[i+1:]:
					if isNotTempoOrProb(report['Type']): #Ignore TEMPO and PROB
						line['End-Time'] = report['Start-Time']
						break
	if lastFMLine > 0: tafLines[lastFMLine]['End-Time'] = tafLines[0]['End-Time'] #Special case for final forcast
	return tafLines

#Get flight rules by looking for missing data in prior reports
def getTAFFlightRules(tafLines):
	for i , line in enumerate(tafLines):
		tempVis , tempCloud = line['Visibility'] , line['Cloud-List']
		for report in reversed(tafLines[:i]):
			if isNotTempoOrProb(report['Type']): #Ignore TEMPO and PROB
				if tempVis == '': tempVis = report['Visibility']
				if 'SKC' in report['Other-List'] or 'CLR' in report['Other-List']: tempCloud = 'tempClear'
				elif tempCloud == []: tempCloud = report['Cloud-List']
				if tempVis != '' and tempCloud != []: break
		if tempCloud == 'tempClear': tempCloud = []
		line['Flight-Rules'] = flightRules[getFlightRules(tempVis , getCeiling(tempCloud))]
		#print("Using " + str(tempVis) + ' and ' + str(getCeiling(tempCloud)) + ' gives ' + str(line['Flight-Rules']))
	return tafLines

def isNotTempoOrProb(reportType):
	return reportType != 'TEMPO' and not (len(reportType) == 6 and reportType[:4] == 'PROB')
	


####################################################################################################################################

def metarTest(station):
	ret = timestamp(station + '\n\n')
	txt = getMETAR(station)
	#txt = 'RJOI 032155Z 00000KT 4800 -RA BR SCT005 BKN010 OVC020 17/ 15 A2970 RMK SLP058 P0001 T01720150 60010'
	if type(txt) == int: 
		if txt: ret += 'Station does not exist/Database lookup error'
		else: ret += 'http connection error'
	else:
		data = parseMETAR(txt)
		for key in data: ret += '{0}  --  {1}\n'.format(key , data[key])
		ret += '\nFlight rules for "{0}" and "{1}"  --  "{2}"'.format(data['Visibility'] , getCeiling(data['Cloud-List']) , flightRules[getFlightRules(data['Visibility'] , getCeiling(data['Cloud-List']))])
		if len(data['Other-List']) > 0:
			ret += '\nTranslated WX'
			for wx in data['Other-List']: ret += '  --  ' + translateWX(wx)
	print(ret)

def tafTest(station):
	ret = timestamp(station + '\n\n')
	txt = getTAF(station)
	#txt = 'TAF YWGT 241818Z 2420/2508 VRB05KT 9999 -SHRA FEW015 SCT025 BKN080 <br/>&nbsp;&nbsp;BECMG 2500/2502 24007KT 9999 -SHRA SCT040 <br/>&nbsp;&nbsp;PROB30 INTER 2420/2505 3000 TSRA BKN015 SCT050CB <br/>&nbsp;&nbsp;PROB30 2420/2423 0500 FG'
	delim = '<br/>&nbsp;&nbsp;'
	print(txt+'\n\n')
	taf = parseTAF(txt , delim)
	for line in txt.strip(' ').split(delim):
		print(line)
	print('')
	print(taf['Station'])
	print(taf['Time'])
	print(taf['Remarks'])
	print('')
	for line in taf['Forecast']:
		print(line['Start-Time'])
		print(line['End-Time'])
		print('')
	for line in taf['Forecast']:
		print(line)
		print('')

#This test main provides example usage for all included public functions
if __name__ == '__main__':
	station = 'KJFK'
	metarTest(station)
	print('\n------------------------------------------\n')
	tafTest(station)
