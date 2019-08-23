# -*- coding: utf-8 -*-
# Copyright 2019 Tampere University
# This software was developed as a part of the CityIoT project: https://www.cityiot.fi/english
# This source code is licensed under the 3-clause BSD license. See license.txt in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi>
'''
This module is responsible for fetching measurements from IoT-Ticket.
'''

import time
import json
from datetime import datetime
import dataConverter
import config
import requests
import logging

# logger for the module
log = logging.getLogger( __name__ )

# dictionary for holding datanodes for each site containing bus measurements.
# Key is site id. value is object containing the URL for getting measurements for the datanode  
dataNodes = {}

def getDataNodes():
    '''
    Get the datanodes for all bus sites.
    Has to be called once before getData.
    '''
    # Get ids of all sites that have bus data and get their datanodes
    for siteId in dataConverter.busNames.keys():
        # list for datanodes of the site
        siteNodes = []
        dataNodes[ siteId ] = siteNodes
        # limit 50 is enough here since a bus has at most about 20 datanodes
        response = requests.get( f'{baseUrl}sites/{siteId}/datanodes', auth = auth, params = { 'expand': 'name', 'limit': 50 } )
        if response.status_code != 200:
            log.error( f'Unable to get datanodes for site {siteId} from IoT-Ticket. HTTP status code {response.status_code}')
            log.error( response.text )
            exit()
            
        for node in response.json()['items']:
            # add only those nodes, we have conversion information for, and longitude and latitude which are handled separately from other conversions
            if node['name'] not in list( dataConverter.attributes.keys()) +[ 'Latitude', 'Longitude' ]:
                continue
            
            siteNodes.append( node )
            
def getData( begin, end ):
    """
    Get measurements for all buses' datanodes, we have conversion information, for a given time period.
    Begin and end are the start and end times as unix timestamps as microseconds. They must be integers.
    Difference between begin and end cannot be too long since we get measurements for a datanode with just one 
    request and there is a limit for how many measurements we can get. 2 hours is at least a suitable difference.
    Returns a dictionary with site id as a key. Value is another dictionary with datanode name as the key
    and value list containing value (v) timestamp (ts) dictionaries.
    GetDataNodes has to be called before using this for the first time.
    """
    data = {} # the return value
    # we want to log how long getting data for all datanodes takes so get the current time before we start
    startTime = time.time()
    # we have to make a separate request for each datanode we want measurements for
    # request parameters¨: the begin and end times
    # also use maximum amount for limit i.e. the number of values fetched
    # the real maximum amount of values seen is a lot less about 13000 measurements
    params = {
        'begin': begin,
        'end': end,
        'limit': 100000
    }

    retryTime = 10 # if request fails how long to wait before retrying    
    for siteId, nodes in dataNodes.items():
        siteData = {} # for site's measurements
        data[siteId] = siteData
        for node in nodes:
            # might have to try the request multiple times if we encounter errors
            retrying = False # is this a retry of a previously failed attempt
            while True:
                headers = { 'Accept-Encoding': 'gzip, deflate' }
                # for some reason the above requests default header causes an issue
                # with some requests so if we had an error with this request before lets not use it
                if retrying:
                    headers['Accept-Encoding'] = None
                    
                try:
                    processdata = requests.get( node['href'] +'/processdata', auth = auth, params = params, headers = headers, timeout = 120 )
                    if processdata.status_code == 200:
                        siteData[ node['name'] ] = processdata.json().get('items', [] )
                        break # done got the data
                    
                    log.error( f'Failed to get measurements from IoT-Ticket. HTTP status code: {processdata.status_code}. Retrying after {retryTime} seconds.' )
                    log.error( processdata.text )
                    
                except KeyboardInterrupt:
                    # user wants to stop collecting so make sure this is passed forward
                    raise
                        
                except:
                    log.exception( f'Exception when getting measurements from IoT-Ticket. Retrying after {retryTime} seconds.')
                    
                time.sleep( retryTime )
                retrying = True
            
    log.debug( f'Measurements fetched in {time.time() -startTime:.1f} seconds.' )
    return data
    
def printDataStats( data ):
    '''
    Can be used to print the number of measurements for each data nod after getting the measurements.
    Data is the result from getData.
    Currently not used.
    '''
    for siteName, siteData in data.items():
        log.debug( f'Number of measurements for each datanode of site {siteName}.' )
        for nodeName, processdata in siteData.items():
            log.debug( nodeName +': ' +str( len( processdata )))
     
# read configuration for connecting to IoT-Ticket 
conf = config.loadConfig( 'iot-ticket.json' )
auth = ( conf['username'], conf['password'] )
baseUrl = conf['url']