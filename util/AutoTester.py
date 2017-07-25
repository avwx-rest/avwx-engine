#!/usr/bin/python3

##--Michael duPont
##--AVWX-Engine : AutoTester.py
##--Constantly test the Metar parser against a list of all possible stations
##--2015-06-19

from avwx import *
import time , csv , smtplib , os , sys , io , requests

timeoutStations = []
notFoundStations = []
parseErrorStations = []
foundMissing = []
knownMissing = []
badInfo = []
colors = ['255,0,0','255,130,0','255,200,0','0,255,0','0,0,255','255,0,200']

#Return True if station hasn't produced a METAR report in the last 2 weeks
def checkPast2Weeks(station):
	try:
		url = 'http://www.aviationweather.gov/metar/data?ids='+station+'&format=raw&date=0&hours=336'
		html = requests.get(url).text
		if html.find('No METAR found for ' + station) != -1: return True
		else: return False
	except:
		return False

def loadStationList(csvFile):
	fin = open(csvFile , 'r')
	#fin = open(csvFile , 'r' , newline='' , encoding='utf-8')
	lines = csv.reader(fin , delimiter=',' , quotechar='|')
	returnList = []
	for line in lines:
		returnList.append(line[0])
	return returnList

def loadMissing(csvFile):
	global knownMissing
	fin = open(csvFile , 'r')
	#fin = open(csvFile , 'r' , newline='' , encoding='utf-8')
	lines = csv.reader(fin , delimiter=',' , quotechar='|')
	for line in lines:
		for station in line:
			knownMissing.append(station)

def runLoopForStation(station):
	print(station)
	currentMETAR = getMETAR(station)
	currentTAF = getTAF(station)
	if type(currentMETAR) == int or type(currentTAF) == int:
		if currentMETAR == 0 or currentTAF == 0:
			global timeoutStations
			timeoutStations.append(timestamp(station))
		elif checkPast2Weeks(station):
			if station not in knownMissing:
				global notFoundStations
				notFoundStations.append(station)
		return
	if station in knownMissing:
		global foundMissing
		foundMissing.append(station)
	try:
		metar = parseMETAR(currentMETAR)
		trans = translateMETAR(metar)
		qa = QATestMETAR(metar)
		if qa: badInfo.append(timestamp(station + '\n\t' + currentMETAR + qa))
		delim = '<br/>&nbsp;&nbsp;'
		taf = parseTAF(currentTAF , delim)
		trans = translateTAF(taf)
		qa = QATestTAF(taf)
		if qa: badInfo.append(timestamp(station + '\n\t' + currentTAF + qa))
		info = getInfoForStation(station)
	except Exception as e:
		global parseErrorStations
		parseErrorStations.append(timestamp(station + '\n\t' + currentTAF + '\n\t' + str(e)))

def QATestMETAR(report):
	ret = ''
	if len(report['Other-List']) > 3: ret += '\n\tQuestionable List: ' + str(report['Other-List'])
	return ret

def QATestTAF(taf):
	ret = ''
	for report in taf['Forecast']:
		if report['Start-Time'] == '' or report['End-Time'] == '': ret += '\n\tTime Code Error: ST = ' + report['Start-Time'] + '  ET = ' + report['End-Time']
		if len(report['Other-List']) > 3: ret += '\n\tQuestionable List: ' + str(report['Other-List'])
		if report['Type'] not in ['BASE','FROM','TEMPO','BECMG','INTER'] and len(report['Type']) > 3 and report['Type'][:4] != 'PROB': ret += '\n\tMissing/Bad Type: ' + report['Type']
	return ret

def outputResults():
	writeString = timestamp("Output for Run\n\n")
	if len(timeoutStations) > 0:
		if len(timeoutStations) > 20000:
			os.popen('blink1-tool --white')
			sys.exit()
		writeString += "We recieved an unknown error for the following " + str(len(timeoutStations)) + " stations:\n"
		for stationOut in timeoutStations: writeString += "\t" + stationOut + "\n"
		writeString += "\n"
	#if len(notFoundStations) > 0:
	#	writeString += "We recieved a 'no station found' for the following " + str(len(notFoundStations)) + " stations:\n"
	#	for stationOut in notFoundStations: writeString += stationOut + ","
	#	writeString += "\n"
	if len(foundMissing) > 0:
		writeString += "We recieved good data for the following " + str(len(foundMissing)) + " formerly missing stations:\n"
		for stationOut in foundMissing: writeString += "\t" + stationOut + "\n"
		writeString += "\n"
	if len(parseErrorStations) > 0:
		writeString += "We recieved a parsing error for the following " + str(len(parseErrorStations)) + " stations:\n"
		for stationOut in parseErrorStations: writeString += "\t" + stationOut + "\n\n"
		writeString += "\n"
	if len(badInfo) > 0:
		writeString += "We recieved bad info for the following " + str(len(badInfo)) + " stations:\n"
		for stationOut in badInfo: writeString += "\t" + stationOut + "\n\n"
		writeString += "\n"
	print(writeString)
	return writeString

def sendEmail(txt):
	TO = 'recv@gmail.com'
	SUBJECT = 'TAF parsing update'
	TEXT = txt
	# Gmail Sign In
	gmail_sender = 'send@gmail.com'
	gmail_passwd = 'application-specific password' #Use two-factor auth
	server = smtplib.SMTP('smtp.gmail.com', 587)
	server.ehlo()
	server.starttls()
	server.login(gmail_sender, gmail_passwd)
	BODY = '\r\n'.join(['To: %s' % TO , 'From: %s' % gmail_sender , 'Subject: %s' % SUBJECT , '' , TEXT])
	try:
		server.sendmail(gmail_sender, [TO], BODY)
		print ('email sent')
	except:
		print ('error sending mail')
	server.quit()

def clearStations():
	global timeoutStations , notFoundStations , parseErrorStations , foundMissing , badInfo
	timeoutStations = []
	notFoundStations = []
	parseErrorStations = []
	foundMissing = []
	badInfo = []

def main():
	i = 0
	emailString = ''
	stationList = loadStationList('stationList.csv')
	loadMissing('badStations.csv')
	while True:
		#Uncomment this line if you have the Blink(1) console library installed
		#os.popen('blink1-tool --rgb=' + colors[i % 6])
		for station in stationList: runLoopForStation(station)
		emailString += outputResults()
		clearStations()
		if i % 3 == 2:
			sendEmail(emailString)
			emailString = ''
		i += 1

if __name__ == '__main__':
	main()
