# -*- coding: utf-8 -*-
# Copyright 2019 Tampere University
# This software was developed as a part of the CityIoT project: https://www.cityiot.fi/english
# This source code is licensed under the 3-clause BSD license. See license.txt in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi>
'''
Contains the Collector class which is responsible for managing the measurement collection process.
It includes getting the measurements from IoT-Ticket for the correct time period, converting them to FIWARE
entities and sending them to FIWARE.
'''

import fiware
import dataConverter
import iotTicket
from utils import s2mrs, mrs2s

import time
import random
from datetime import datetime
import logging

# if collecting historical data how much data to get from IoT-Ticket in one request
# i.e. the length of time between begin and end times given to iotTicket.getData method.  
historyPeriod = 3600 *2
# same as above but for real time collection
rtPeriod = 60
# in real time collection how long to wait to make sure that measurements have arrived to IoT-Ticket before getting them
wait = 30

# convert to microsecons used by IoT-Ticket API
historyPeriod = s2mrs( historyPeriod )
rtPeriod = s2mrs( rtPeriod )
wait = s2mrs( wait )

# get logger for module
log = logging.getLogger( __name__ )

class Collector():        

    def __init__(self, startDate, endDate ):
        '''
        Create collector for given time period.
        If both dates are None, real time collection is started.
        If both dates are not None measurements for the given period is collected.
        If startDate is given but no endDate first collect historical data them when done switch to real time.
        '''
        self.startDate = startDate
        self.endDate = endDate
        # stop is time in microseconds when collecting should stop
        self.stop = None
        if endDate != None:
            self.stop = endDate.timestamp()
            self.stop = s2mrs( round( self.stop ) ) -500001
            
    def startCollecting(self):
        '''
        Begin the defined collecting operation.
        '''
        # self.begin and self.end are used to define the next data collection start and end
        # they are unix timestamps in microseconds
        # self.period determines length of the next measurement collection period
        # if it is the history period it will be the maximum length that can be used
        # if it is the real time period it is the minimum
        if self.startDate != None:
            self.begin = self.startDate.timestamp()
            # we have start date so use history period 
            self.period = historyPeriod
            
        else:
            # no start date so we use real time period
            # start collection from last possible rtPeriod we expect to have measurements for
            # use seconds for now since later code expects it
            self.begin = mrs2s( self._getLastTime() ) -mrs2s( rtPeriod )
            self.period = rtPeriod

        # self.getData tells if we will still get data for next period
        self.getData = True
        # we round timestamps we get from IoT-ticket to nearest seconds so we want to set begin and end so that
        # there will not be duplicate timestamps when we get the next data
        # so we first round begin to seconds then subtract half a second and them convert to microseconds
        # we will then get everything that rounds to begin rounded    
        self.begin = s2mrs( round( self.begin ) ) -s2mrs( 0.5 )
        # set the end to correct value
        self._setEndAndWait()
        while self.getData:
            # log current state including begin and end
            self._printState()
            # get data from IoT-Ticket for current period i.e. between begin and end
            data = iotTicket.getData( self.begin, self.end )
            #self._fakeGetMeasurements()
            
            #iotTicket.printDataStats( data )
            # convert to FIWARE entity updates
            updates = dataConverter.convertToEntityUpdates( data )
            #dataConverter.saveUpdatesToFile( updates )
            #updates = dataConverter.loadUpdates()
            # and send to FIWARE
            fiware.sendData( updates )
            #time.sleep( 20 )
            #fiware.checkUpdates( updates )
            # set begin to end +1 microseconds
            self.begin = self.end +1
            # calcualte appropriate end for next measurements
            self._setEndAndWait()
            
    def _setEndAndWait(self):
        '''
        Calculates the correct end for next measurements.
        It will be based on current begin, period used (real time or history) and current time.
        If required waits (sleeps) so we do not get measurements too early.
        '''
        # first assume we can just get for the full period we are using now
        self.end = self.begin +self.period -1
        
        # if we have stop time check if we are over it i.e. we can stop collecting
        if self.stop != None and self.begin >= self.stop:
            self.getData = False

        # if we have stop time check that our current end is not over it
        elif self.stop != None and self.end > self.stop:
            # almost done collecting just get last measurements before stop
            self.end = self.stop
        
        # rest of checks are relevant only in real time continuous collecting        
        
        # check that current end is not after the time IoT-Ticket does not yet have measurements for us
        # this might be in the future or bit before current moment and we want to make sure that
        # the measurements have arrived before getting them
        # we will either wait for the correct time with current end time or
        # set a new end time and wait or get the measurements right away
        elif self.stop == None and self.end > self._getLastTime():
            # see if we can just set end to the time we expect IoT-Ticket to have measurements for us and get them immediately
            # we can do this if the new measurement period would be longer than our real time collecting period
            # and we are currently using the longer period or if using the shorter period we are behind in collecting
            if (self.period == historyPeriod or rtPeriod <= self.end -self._getLastTime() ) and self._getLastTime() -self.begin > rtPeriod:
                self._setEndToLastTime()
                
            else:
                # we have to wait before getting more measurements
                # if we are using the longer period we have to switch to the shorter and set end using it
                if self.period == historyPeriod:
                    self.period = rtPeriod
                    self.end = self.begin +self.period -1
                    
                # we should wait until the current end is at least wait seconds before current time
                sleepTime = mrs2s(self.end +wait -s2mrs( time.time() )) 
                log.debug( f'{sleepTime:.1f} seconds before getting next measurements.' )
                time.sleep( sleepTime )
        
        # check when using the real time collecting period are we behind the current moment meaning we should catch up
        # by getting measurements for a longer period        
        elif self.period == rtPeriod and self._getLastTime() -self.begin > rtPeriod:
            # check if we are behind less than the longer collecting period
            if self._getLastTime() -self.begin < historyPeriod:
                # set end to the latest moment we expect to get measurements
                self._setEndToLastTime()
                #self.end = self._getLastTime()
                #self.end = mrs2s( self.end )
                #self.end = s2mrs( round( self.end )) +499999
                
            else:
                # we are behind more than the history period so lets switch to use it for now until we catch up
                self.period = historyPeriod
                self.end = self.begin +self.period -1
        
    def _getLastTime(self):
        '''
        Return the current last time we expect IoT-Ticket to have measurements for us.
        This is the current time minus a short wait period to make sure that the measurements have arrived.
        '''
        return s2mrs( time.time()) -wait
    
    def _setEndToLastTime(self):
        '''
        Sets end to last time we expect IoT-Ticket to have measurements.
        '''
        self.end = s2mrs( round( time.time() ) ) -wait +499999
    
    def _printState(self):
        '''
        Logs the current state: begin, end, begin -end, current period and time
        '''
        log.debug( f'Getting next measurements. begin: {datetime.fromtimestamp(mrs2s(self.begin))}, end: {datetime.fromtimestamp(mrs2s(self.end))}, duration: {mrs2s( self.end -self.begin):.1f} now: {datetime.now().time()}, period: {mrs2s(self.period)}' )
        
    def _fakeGetMeasurements(self):
        '''
        Was used in testing.
        '''
        log.debug( f'{mrs2s(self.end -self.begin):.1f} measurement period.' )
        sleepTime = 40 *random.random()
        log.debug( f'{sleepTime:.1f} seconds for operation.' )
        time.sleep( sleepTime )