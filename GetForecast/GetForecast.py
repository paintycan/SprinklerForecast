#!/usr/bin/env python3

import xml.etree.ElementTree as etree
import datetime
import time
import os
import math
#import SprinklerOn
import sys
import getopt
import RPi.GPIO as GPIO
import atexit

# GPIO PIN DEFINES
pin_sr_clk =  4 # Shift register clock
pin_sr_noe = 17 # Shift register output enable (low = enable)
pin_sr_dat = 27 # Shift register data
pin_sr_lat = 22 # Shift register latch

# NUMBER OF STATIONS
num_stations = 8

# STATION BITS
values = [0]*num_stations # Create values array

def enableShiftRegisterOutput():
    GPIO.output(pin_sr_noe, False)

def disableShiftRegisterOutput():
    GPIO.output(pin_sr_noe, True)

def setShiftRegister(values):
    GPIO.output(pin_sr_clk, False)
    GPIO.output(pin_sr_lat, False)
    for s in range(0,num_stations):
        GPIO.output(pin_sr_clk, False)
        GPIO.output(pin_sr_dat, values[num_stations-1-s])
        GPIO.output(pin_sr_clk, True)
    GPIO.output(pin_sr_lat, True)

# set values array based on arguments received
def getArgs(stationNum):
    global values
    global num_stations
    for i in range(0,num_stations):
        values[i] = 0
    if int(stationNum) != int(0):
        values[int(stationNum)-1] = 1

def SprinklerOn(stationNum):
    print("Starting Station ", stationNum)
    getArgs(stationNum)
    GPIO.cleanup()
    # setup GPIO pins to interface with shift register
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_sr_clk, GPIO.OUT)
    GPIO.setup(pin_sr_noe, GPIO.OUT)
    disableShiftRegisterOutput()
    GPIO.setup(pin_sr_dat, GPIO.OUT)
    GPIO.setup(pin_sr_lat, GPIO.OUT)

    setShiftRegister(values)
    enableShiftRegisterOutput()

#Get current datetime
now = datetime.datetime.now()
midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

def FetchForecast():
    # Get Wunderground settings from config.xml
    # Open xml file
    treeConfig = etree.parse("config.xml")
    elemRoot = treeConfig.getroot()
    #Get API, state, and zip
    wgrndAPI = elemRoot.find('wunderground/API').text
    wgrndState = elemRoot.find('wunderground/state').text
    wgrndZip = elemRoot.find('wunderground/zip').text

    #wgrndAPI = '4a9d2b5150c1d76c'
    #wgrndState = 'ID'
    #wgrndZip = '83709'

    # Set wunderground urls
    urlForecast = 'http://api.wunderground.com/api/' + wgrndAPI + '/forecast/q/' + wgrndState + '/' + wgrndZip + '.xml'
    urlAstronomy = 'http://api.wunderground.com/api/' + wgrndAPI + '/astronomy/q/' + wgrndState + '/' + wgrndZip + '.xml'

    #set wunderground xml queries
    #urlForecast = 'http://api.wunderground.com/api/4a9d2b5150c1d76c/forecast/q/ID/83709.xml'
    #urlAstronomy = 'http://api.wunderground.com/api/4a9d2b5150c1d76c/astronomy/q/ID/83709.xml'

    #import library to do http requests:
    from urllib.request import urlretrieve

    #Fetch xml files from wunderground
    urlretrieve(urlForecast, 'forecast.xml')
    urlretrieve(urlAstronomy, 'astronomy.xml')

def GetForecast():
    print('Getting Forecast')
    global now

    FetchForecast()

    #Get high temp and precip from xml
    treeTempSource = etree.parse("forecast.xml")
    rootTempSource = treeTempSource.getroot()
    elemSourceHigh = rootTempSource.find('forecast/simpleforecast/forecastdays/forecastday[1]/high/fahrenheit')
    print ("High: " + elemSourceHigh.text)
    elemSourcePrecip = rootTempSource.find('forecast/simpleforecast/forecastdays/forecastday[1]/qpf_allday/in')
    print ("Precip: " + elemSourcePrecip.text)
 
    #write high temp and precip to config.xml
    treeConfig = etree.parse("config.xml")
    elemRoot = treeConfig.getroot()
    elemHigh = elemRoot.find('weatherInfo/highTemp')
    elemHigh.text = elemSourceHigh.text
    elemPrecip = elemRoot.find('weatherInfo/precip')
    elemPrecip.text = elemSourcePrecip.text
 
    #Get sunrise hour and minute from xml
    treeSunSource = etree.parse("astronomy.xml")
    rootSunSource = treeSunSource.getroot()
    elemHourSource = rootSunSource.find('moon_phase/sunrise/hour')
    #print (elemHourSource.text)
    elemMinSource = rootSunSource.find('moon_phase/sunrise/minute')
    #print (elemMinSource.text)
 
    #Write sunrise time to config.xml
    elemSunHour = elemRoot.find('weatherInfo/sunriseHour')
    elemSunHour.text = elemHourSource.text
    elemSunMinute = elemRoot.find('weatherInfo/sunriseMinute')
    elemSunMinute.text = elemMinSource.text
 
    #Enter process datetime to config.xml
    elemDate = elemRoot.find('date')
    elemDate.text = str(now)
        
    #Write to config.xml
    treeConfig.write('config.xml')

def BackupCrontab():
    #Backup existing crontab
    os.system('crontab -u pi -l > /home/pi/crontab.old.txt')
 
def CreateSchedule():
    #try:
 
    #Open xml file
    treeConfig = etree.parse("config.xml")
    elemRoot = treeConfig.getroot()
    #get sunrise hour and minute
    sunriseHour = elemRoot.find('weatherInfo/sunriseHour').text
    sunriseMinute = elemRoot.find('weatherInfo/sunriseMinute').text
    #get forecast high and rain
    forecastHigh = elemRoot.find('weatherInfo/highTemp').text
    forecastRain = elemRoot.find('weatherInfo/precip').text
    #get other config parameters
    sunriseEnabled = elemRoot.find('starts/sunrise/enabled').text
    sunriseOffset = elemRoot.find('starts/sunrise/hourOffset').text
    timeStartEnabled = elemRoot.find('starts/time/enabled').text
    timeStartHour = elemRoot.find('starts/time/hour').text
    timeStartMinute = elemRoot.find('starts/time/minute').text

    threshRain = elemRoot.find('thresholds/rain').text
    threshCoolHalfTemp = elemRoot.find('thresholds/coolHalfTemp').text
    threshCoolThirdTemp = elemRoot.find('thresholds/coolThirdTemp').text
    threshCoolOffTemp = elemRoot.find('thresholds/coolOffTemp').text
    threshHotEnabled = elemRoot.find('thresholds/hotEnabled').text
    threshHotTemp = elemRoot.find('thresholds/hotTemp').text
    threshHotDuration = elemRoot.find('thresholds/hotExtraDuration').text
    threshHotStartHour = elemRoot.find('thresholds/hotExtraTimeHour').text
    threshHotStartMinute = elemRoot.find('thresholds/hotExtraTimeMinute').text
 
    if timeStartEnabled == str(1):
        startHour = int(timeStartHour)
        startMinute = timeStartMinute
    else:
        startHour = int(sunriseHour) + int(sunriseOffset)
        startMinute = sunriseMinute
 
    #skip watering if rain or too cold
    if (float(forecastRain) < float(threshRain) and int(forecastHigh) > int(threshCoolOffTemp)):
        print('regular program')
        root = etree.Element("root")
        #loop through each station setting in config.xml
        elemStations = elemRoot.find('stations')
        for station in elemStations:
            #get station config numbers
            number = station.find('number')
            duration = station.find('duration').text

            #Set startTime
            startTime = midnight + datetime.timedelta(hours=int(startHour), minutes=int(startMinute))

            #Write to XML
            schedule = etree.SubElement(root, "schedule")
            schedule.set('type', 'regular')
            station = etree.SubElement(schedule, "station")
            station.text = number.text
            rundate = etree.SubElement(schedule, "datetime")
            rundate.text = str(startTime)

            #increment startMinute for next station
            startMinute = int(startMinute) + int(duration)
            #roll over startMinute and startHour when necessary
            if int(startMinute) > int(59):
                startMinute = int(startMinute) - int(60)
                startHour = int(startHour) + int(1)

        #Write stop command to XML
        #Set startTime
        startTime = midnight + datetime.timedelta(hours=int(startHour), minutes=int(startMinute))

        schedule = etree.SubElement(root, "schedule")
        schedule.set('type', 'regular')
        station = etree.SubElement(schedule, "station")
        station.text = '0'
        rundate = etree.SubElement(schedule, "datetime")
        rundate.text = str(startTime)

        tree = etree.ElementTree(root)
        tree.write("schedule.xml")

    #if above hot threshold, add extra entry
    if (int(forecastHigh) >= int(threshHotTemp) and int(threshHotEnabled) == 1):
        print("Hot Program")
        startHour = threshHotStartHour
        startMinute = threshHotStartMinute
 
        treeSched = etree.parse('schedule.xml')
        rootSched = treeSched.getroot()


        #loop through each station setting in config.xml
        elemStations = elemRoot.find('stations')
        for station in elemStations:
            #get configured station numbers
            number = station.find('number')
 
            #Set startTime
            startTime = midnight + datetime.timedelta(hours=int(startHour), minutes=int(startMinute))

            schedule = etree.Element("schedule")
            schedule.set('type', 'hot')
            rootSched.append(schedule)
            elemStation = etree.Element('station')
            elemStation.text = number.text
            schedule.append(elemStation)
            elemDatetime = etree.Element('datetime')
            elemDatetime.text = str(startTime)
            schedule.append(elemDatetime)

            treeSched.write("schedule.xml")

            #increment startMinute for next station
            startMinute = int(startMinute) + int(threshHotDuration)
            #roll over startMinute and startHour when necessary
            if int(startMinute) > int(59):
                startMinute = int(startMinute) - int(60)
                startHour = int(startHour) + int(1)

        #Set startTime
        startTime = midnight + datetime.timedelta(hours=int(startHour), minutes=int(startMinute))
        schedule = etree.Element("schedule")
        schedule.set('type', 'hot')
        rootSched.append(schedule)
        elemStation = etree.Element('station')
        elemStation.text = '0'
        schedule.append(elemStation)
        elemDatetime = etree.Element('datetime')
        elemDatetime.text = str(startTime)
        schedule.append(elemDatetime)

        treeSched.write("schedule.xml")
        
    #except:
       # print("Unexpected error:")

def RunSchedule():
    now = datetime.datetime.now()
    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)

    #strip seconds and microseconds off current time
    stripTimeNow = now.replace(second=0, microsecond=0)
    print(str(now))

    #Get Forecast at 2am
    forecastTime = midnight + datetime.timedelta(hours=2, minutes=0)
    if stripTimeNow == forecastTime:
        GetForecast()
        CreateSchedule()

    #Open xml file
    treeSched = etree.parse("schedule.xml")
    elemRoot = treeSched.getroot()
    
    #loop through each station setting in config.xml
    for elem in elemRoot:
        #get scheduled station numbers
        schedStation = elem.find('station')
        #get scheduled times
        schedDatetime = elem.find('datetime')
        #convert schedule time to datetime
        dtSched = datetime.datetime.strptime(schedDatetime.text, "%Y-%m-%d %H:%M:%S")

        #print(str(stripTimeNow))
        print(str(dtSched))
        # if scheduled time matches now, call SprinklerOn
        if stripTimeNow == dtSched:
            SprinklerOn(schedStation.text)

def main():
    GetForecast()
    CreateSchedule()
    while True:
        try: 
            RunSchedule()
        except:
            pass
        # Adjust to run on the minute
        now = datetime.datetime.now()
        nowSecond = int(now.second)
        if nowSecond != 0:
            time.sleep(60-nowSecond)
        else:
            time.sleep(60)  # check every 60 seconds

if __name__ == "__main__":
  main()