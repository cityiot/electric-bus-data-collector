# -*- coding: utf-8 -*-
'''
Bus collector main file. Responsible for starting the data collection.
'''

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

# get root logger
log = logging.getLogger()

def main():
    '''
    Function which starts the tool.
    '''
    # setup logging
    setupLogging()
    
    # get start and end dates for collecting if given from config file
    startDate, endDate = _getStartAndEnd()
    # get the list of datanodes we will be collecting measurements from
    iotTicket.getDataNodes()
    # create FIWARE entities to Orion from the buses we collect data from if not already created
    fiware.createEntities()
    if not fiware.sendToQl:
        # we will send measurements to QuantumLeap through Orion subscription(s) so create them if not already created
        fiware.addSubscription()

    # create the collector that takes care of the actual collection process
    myCollector = Collector( startDate, endDate )
    try:
        # and start collecting
        myCollector.startCollecting()
        
    except KeyboardInterrupt:
        log.info( 'Got keyboard interrupt. Collecting stopped.' )
        
    except:
        log.exception( 'Unexpected exception occurred.' )
        exit()
        
    log.info( 'Data collection done.' )

def setupLogging():
    '''
    Configures logging so that everything is logged to the console and log_debug file
    info, warnings and errors are logged to log.txt
    log rotating is used to limit log file sizes and number of backup copies as defined in the logging config file.
    '''
    # get logging configuration from file
    # contains max file size in mb which is converted to bytes
    # contains number of backup log files 
    conf = config.loadConfig( 'logging.json' )
    backups = conf['number_of_backups']
    sizeMb = conf['file_max_size_mb']
    size = round( sizeMb *(2**20) )
    # directory where log files are saved
    logDir = utils.getAppDir() /'logs'
    # create if not exists
    mkdir_p( logDir )
    log.setLevel( logging.DEBUG )
    # because we set root logger log level other modules urllib3 logging is affected and we don't want that
    logging.getLogger( urllib3.__name__ ).setLevel( logging.WARNING )
    console = logging.StreamHandler()
    log.addHandler( console )
    # how log messages are formatted in the files
    formatter = logging.Formatter('%(asctime)s %(levelname)s\n%(message)s')
    fileLog = logging.handlers.RotatingFileHandler( logDir / 'log.txt', encoding = 'utf-8', maxBytes = size, backupCount = backups )
    fileLog.setLevel( logging.INFO )
    fileLog.setFormatter( formatter )
    log.addHandler( fileLog )
    fileLog = logging.handlers.RotatingFileHandler( logDir / 'log_debug.txt', encoding = 'utf-8', maxBytes = size, backupCount = backups )
    fileLog.setLevel( logging.DEBUG )
    fileLog.setFormatter( formatter )
    log.addHandler( fileLog )
        
def _getStartAndEnd():
    '''
    Reads measurement collection start and end dates from config file.
    Checks also that they are ok.
    ''' 
    # read the relevant configuration file
    conf = config.loadConfig( 'collector.json' )
    startDate = conf.get( 'startDate', None )
    endDate = conf.get( 'endDate', None )
    try:
        # if there are dates attempt to create datetime objects from them
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
    '''
    Makes sure that the given directory exists.
    '''
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise
        
if __name__ == '__main__':
    main()
