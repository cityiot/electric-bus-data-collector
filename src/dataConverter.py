# -*- coding: utf-8 -*-

from datetime import datetime
import json
import logging

log = logging.getLogger( __name__ )

import config

def getBusName( siteName ):
    return 'TKL' +str( busNames[ siteName ] )
    
def getBusId( siteName ):
    return 'Vehicle:' +getBusName( siteName )

def getAttributeNames():
    return set( [ attr['name'] for attr in attributes.values() ] +[ 'location' ] )
        
def _roundTimeStamps( data ):
    for siteData in data.values():
        for processdata in siteData.values():
            prevTs = None
            for i in range( len(processdata) -1, -1, -1):
                measurement = processdata[i]
                measurement['ts'] = round( measurement['ts'] /1000000 )
                if prevTs != None and prevTs == measurement['ts']:
                    del processdata[i +1]
                    
                prevTs = measurement['ts']
                    
def convertToEntityUpdates( data ):            
    _roundTimeStamps( data )
    for siteData in data.values():
        location = []
        siteData['location'] = location
        lon = { 'items': siteData['Longitude'], 'index': 0 }
        lat = { 'items': siteData['Latitude'], 'index': 0 }
        del siteData['Longitude']
        del siteData['Latitude']
        while lat['index'] < len( lat['items'] ) and lon['index'] < len( lon['items'] ):
            if lat['items'][ lat['index'] ]['ts'] == lon['items'][ lon['index'] ]['ts']:
                location.append( { 'v': [ lon['items'][ lon['index'] ]['v'], lat['items'][ lat['index'] ]['v'] ], 'ts': lat['items'][ lat['index'] ]['ts'] })
                lat['index'] += 1
                lon['index'] += 1
                
            elif lat['items'][ lat['index'] ]['ts'] < lon['items'][ lon['index'] ]['ts']:
                lat['index'] += 1
                
            else:
                lon['index'] += 1

    for siteData in data.values():
        names = set( siteData.keys() )
        for nodeName in names:
            if len( siteData[nodeName] ) == 0:
                del siteData[ nodeName ]
                
    updates = {}        
    for siteName, siteData in data.items():
        siteUpdates = []
        updates[ siteName ] = siteUpdates
        nodeNames = set( siteData.keys() )
        indexes = {}
        for name in nodeNames:
            indexes[name] = 0
            
        while len( nodeNames ) > 0:
            entity = {}
            doneNodes = set()
            ts = min( [ siteData[name][ indexes[name]]['ts'] for name in nodeNames ] )
            for nodeName in nodeNames:
                processdata = siteData[nodeName]
                index = indexes[ nodeName ]
                data = processdata[ index ]
                if ts == data['ts']:
                    indexes[ nodeName ] = index +1
                    if index == len( processdata ) -1:
                        doneNodes.add( nodeName )
            
                    attribute = {}
                    conversionInfo = attributes[ nodeName ]
                    if nodeName == 'location':
                        attribute['type'] = 'geo:json'
                        attribute['value'] = {
                            'type': 'Point',
                            'coordinates': data['v']
                        }
                    
                    else:
                        value = data['v']
                        if 'mapping' in conversionInfo:
                            try:
                                value = conversionInfo[ 'mapping' ][str(value)]
                                
                            except KeyError:
                                log.warning( f'No conversion mapping for {nodeName} value {value} of {siteName} at {datetime.fromtimestamp( data["ts"] )}.' ) 
                                continue
                                
                        attribute['value'] = value
                        attribute['type'] = conversionInfo.get( 'type', 'Number' )
                        
                    attribute['metadata'] = {
                        'timestamp': {
                            'type': 'DateTime',
                            'value': datetime.utcfromtimestamp( data['ts'] ).isoformat() +'Z'
                        }
                    }
                    
                    entity[ conversionInfo['name'] ] = attribute
                    
            nodeNames.difference_update( doneNodes )
            entity['id'] = getBusId( siteName )
            entity['type'] = 'Vehicle'
            siteUpdates.append( entity )
            
    return updates
            
def saveUpdatesToFile( updates ):
    for siteName, update in updates.items():
        file = open( siteName +'.json', 'w' )
        json.dump( update, file, indent = 4  )
        file.close()
        
def loadUpdates():
    updates = {}
    for name in busNames:
        file = open( f'{name}.json', 'r' )
        updates[ name ] = json.load( file )
        
    return updates

conf = config.loadConfig( 'converter.json' )
attributes = conf['attributes']
busNames = conf['busIDs']