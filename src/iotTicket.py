# -*- coding: utf-8 -*-

import time
import json
from datetime import datetime
import dataConverter
import config
import requests
import logging

log = logging.getLogger( __name__ )

dataNodes = {}

def getDataNodes():
    for siteId in dataConverter.busNames.keys():
        siteNodes = []
        dataNodes[ siteId ] = siteNodes
        response = requests.get( f'{baseUrl}sites/{siteId}/datanodes', auth = auth, params = { 'expand': 'name', 'limit': 50 } )
        if response.status_code != 200:
            log.error( f'Unable to get datanodes for site {siteId} from IoT-Ticket. HTTP status code {response.status_code}')
            log.error( response.text )
            exit()
            
        for node in response.json()['items']:
            if node['name'] not in list( dataConverter.attributes.keys()) +[ 'Latitude', 'Longitude' ]:
                continue
            
            siteNodes.append( node )
            
def getData( begin, end ):
    data = {}
    startTime = time.time()
    params = {
        'begin': begin,
        'end': end
    }

    retryTime = 10    
    for siteId, nodes in dataNodes.items():
        siteData = {}
        data[siteId] = siteData
        for node in nodes:
            while True:
                try:
                    processdata = requests.get( node['href'] +'/processdata', auth = auth, params = params )
                    if processdata.status_code == 200:
                        siteData[ node['name'] ] = processdata.json().get('items', [] )
                        break
                    
                    log.error( f'Failed to get measurements from IoT-Ticket. HTTP status code: {processdata.status_code}. Retrying after {retryTime} seconds.' )
                    log.error( processdata.text )
                    
                except KeyboardInterrupt:
                    raise
                        
                except:
                    log.exception( f'Exception when getting measurements from IoT-Ticket. Retrying after {retryTime} seconds.')
                    
                time.sleep( retryTime )
            
    log.debug( f'Measurements fetched in {time.time() -startTime:.1f} seconds.' )
    return data
    
def printDataStats( data ):
    for siteName, siteData in data.items():
        log.debug( f'Number of measurements for each datanode of site {siteName}.' )
        for nodeName, processdata in siteData.items():
            log.debug( nodeName +': ' +str( len( processdata )))
            
conf = config.loadConfig( 'iot-ticket.json' )
auth = ( conf['username'], conf['password'] )
baseUrl = conf['url']