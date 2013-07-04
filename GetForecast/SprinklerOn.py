#!/usr/bin/env python3

#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#import urlparse
import sys
import os
import datetime
import time
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

def run(stationNum):
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

#run ()

#ip and port of servr
    #by default http server port is 8080
#    server_address = ('', 8080)
#    httpd = HTTPServer(server_address, KodeFunHTTPRequestHandler)
#    print('OpenSprinkler Pi is running...')
#    while True:
#        httpd.handle_request()

def progexit():
    global values
    values = [0]*num_stations
    setShiftRegister(values)

GPIO.cleanup()

if __name__ == '__main__':
#    atexit.register(progexit)
    run()