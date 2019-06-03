# -*- coding: utf-8 -*-

import fiware
import iotTicket
from collector import Collector
import config
import utils

from datetime import datetime
import logging
import logging.handlers
import os, os.path
import errno
from pathlib import Path
import urllib3

log = logging.getLogger()

def main():
    logDir = utils.getAppDir() /'logs'
    mkdir_p( logDir )
    log.setLevel( logging.DEBUG )
    logging.getLogger( urllib3.__name__ ).setLevel( logging.WARNING )
    console = logging.StreamHandler()
    log.addHandler( console )
    formatter = logging.Formatter('%(asctime)s %(levelname)s\n%(message)s')
    fileLog = logging.handlers.RotatingFileHandler( logDir / 'log.txt', encoding = 'utf-8', maxBytes = 2**20, backupCount = 100 )
    fileLog.setLevel( logging.INFO )
    fileLog.setFormatter( formatter )
    log.addHandler( fileLog )
    fileLog = logging.handlers.RotatingFileHandler( logDir / 'log_debug.txt', encoding = 'utf-8', maxBytes = 2**20, backupCount = 10 )
    fileLog.setLevel( logging.DEBUG )
    fileLog.setFormatter( formatter )
    log.addHandler( fileLog )
    
    startDate, endDate = _getStartAndEnd()
    iotTicket.getDataNodes()
    fiware.createEntities()
    if not fiware.sendToQl:
        fiware.addSubscription()

    myCollector = Collector( startDate, endDate )
    try:
        myCollector.startCollecting()
        
    except KeyboardInterrupt:
        log.info( 'Got keyboard interrupt. Collecting stopped.' )
        
    except:
        log.exception( 'Unexpected exception occurred.' )
        exit()
        
    log.info( 'Data collection done.' )
    
def _getStartAndEnd():
    conf = config.loadConfig( 'collector.json' )
    startDate = conf.get( 'startDate', None )
    endDate = conf.get( 'endDate', None )
    try:
        if endDate != None:
            endDate = datetime.fromisoformat( endDate )
            
        if startDate != None:
            startDate = datetime.fromisoformat( startDate )
        
    except ValueError as e:
        log.error( f'Invalid start or end date: {e.args[0]}' )
        exit()
        
    if startDate == None and endDate != None:
        log.error('start date must be given if there is an end date.')
        exit()
        
    if endDate != None:
        if endDate > datetime.now():
            log.error( 'end date cannot be in the future.' )
            exit()
            
        if startDate >= endDate:
            log.error( 'start date cannot be the same or after end date.' )
            exit()
            
    if startDate != None and startDate > datetime.now():
        log.error( 'start date cannot be in the future.' )
        exit()
        
    return startDate, endDate

# Taken from https://stackoverflow.com/a/600612/119527
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
        
if __name__ == '__main__':
    main()
