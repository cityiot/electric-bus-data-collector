import fiware
import dataConverter
import iotTicket
from utils import s2mrs, mrs2s

import time
import random
from datetime import datetime
import logging

historyPeriod = 3600 *2
rtPeriod = 60
wait = 30

historyPeriod = s2mrs( historyPeriod )
rtPeriod = s2mrs( rtPeriod )
wait = s2mrs( wait )

log = logging.getLogger( __name__ )

class Collector():        

    def __init__(self, startDate, endDate ):
        self.startDate = startDate
        self.endDate = endDate
        self.stop = None
        if endDate != None:
            self.stop = endDate.timestamp()
            self.stop = s2mrs( round( self.stop ) ) -500001
            
    def startCollecting(self):
        if self.startDate != None:
            self.begin = self.startDate.timestamp()
            self.period = historyPeriod
            
        else:
            self.begin = mrs2s( self._getLastTime() ) -mrs2s( rtPeriod )
            self.period = rtPeriod
        
        self.getData = True    
        self.begin = s2mrs( round( self.begin ) ) -s2mrs( 0.5 )
        self._setEndAndWait()
        while self.getData:
            self._printState()
            data = iotTicket.getData( self.begin, self.end )
            #self._fakeGetMeasurements()
            
            #iotTicket.printDataStats( data )
            updates = dataConverter.convertToEntityUpdates( data )
            #dataConverter.saveUpdatesToFile( updates )
            #updates = dataConverter.loadUpdates()
            fiware.sendData( updates )
            #time.sleep( 20 )
            #fiware.checkUpdates( updates )
            self.begin = self.end +1
            self._setEndAndWait()
            
    def _setEndAndWait(self):
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
                # we are behind more than the longer period so lets switch to use it for now until we catch up
                self.period = historyPeriod
                self.end = self.begin +self.period -1
        
    def _getLastTime(self):
        '''
        Return the current last time we expect IoT-Ticket to have measurement for us.
        This is the current time minus a short wait period to make sure that the measurements have arrived.
        '''
        return s2mrs( time.time()) -wait
    
    def _setEndToLastTime(self):
        self.end = s2mrs( round( time.time() ) ) -wait +499999
    
    def _printState(self):
        log.debug( f'Getting next measurements. begin: {datetime.fromtimestamp(mrs2s(self.begin))}, end: {datetime.fromtimestamp(mrs2s(self.end))}, duration: {mrs2s( self.end -self.begin):.1f} now: {datetime.now().time()}, period: {mrs2s(self.period)}' )
        
    def _fakeGetMeasurements(self):
        log.debug( f'{mrs2s(self.end -self.begin):.1f} measurement period.' )
        sleepTime = 40 *random.random()
        log.debug( f'{sleepTime:.1f} seconds for operation.' )
        time.sleep( sleepTime )