# -*- coding: utf-8 -*-
'''
Responsible for converting the IoT-Ticket measurements to FIWARE entity updates.
Contains the conversion information and mapping for IoT-Ticket site ids to bus names.
'''

from datetime import datetime
import json
import logging

# logger for module
log = logging.getLogger( __name__ )

import config

def getBusName( siteName ):
    '''
    Get the name of a bus e.g. TKL14 that corresponds to the given IoT-Ticket site id.
    '''
    return 'TKL' +str( busNames[ siteName ] )
    
def getBusId( siteName ):
    '''
    Get the FIWARE entity id e.g. Vehicle:TKL14 that corresponds to the given IoT-Ticket site id.
    '''
    return 'Vehicle:' +getBusName( siteName )

def getAttributeNames():
    '''
    Get a set containing the names of the dynamic entity attributes bus entities can have i.e. attributes we get measurements for.
    Static attributes such as vehicleType and category are not included.
    '''
    return set( [ attr['name'] for attr in attributes.values() ] +[ 'location' ] )
        
def _roundTimeStamps( data ):
    '''
    Internal method used to round IoT-Ticket measurement time stamps to one second precision.
    Data is the return value of iotTicket.getData.
    '''
    # go through all measurements
    for siteData in data.values():
        for processdata in siteData.values():
            # we don't want duplicate timestamps i.e. measurements from the same datanode that after rounding have the same timestamp
            # we process the times from last to first and drop those that would have the same timestamp
            prevTs = None # timestamp of the previously processed measurement
            for i in range( len(processdata) -1, -1, -1):
                measurement = processdata[i]
                # convert to seconds and round
                measurement['ts'] = round( measurement['ts'] /1000000 )
                if prevTs != None and prevTs == measurement['ts']:
                    del processdata[i +1]
                    
                prevTs = measurement['ts']
                    
def convertToEntityUpdates( data ):
    '''
    Convert data returned by iotTicket.getData to FIWARE entity updates.
    Return value is dictionary with site id as key and value is
    list of entity updates for corresponding bus.
    Each entity update has attribute updates for the same time.
    '''            
    _roundTimeStamps( data )
    # combine latitude and longitude datanode values to location attribute
    for siteData in data.values():
        location = [] # save locations here
        siteData['location'] = location
        
        # lets go through longitude and latitude measurements starting from the first items
        # we will create a location from them if they have the same timestamp
        # if not we will discard the measurement with earlier timestamp and look at the nesxt one
        # get the latitude and longitude measurements and use separate indexes to go through both lists
        lon = { 'items': siteData['Longitude'], 'index': 0 }
        lat = { 'items': siteData['Latitude'], 'index': 0 }
        # delete lat and lon from original data since they are no longer needed
        del siteData['Longitude']
        del siteData['Latitude']
        
        # process until we have reached the end of one of the lists after which we cannot create more locations
        while lat['index'] < len( lat['items'] ) and lon['index'] < len( lon['items'] ):
            if lat['items'][ lat['index'] ]['ts'] == lon['items'][ lon['index'] ]['ts']:
                # same timestamp create location value and move to next in both lists
                location.append( { 'v': [ lon['items'][ lon['index'] ]['v'], lat['items'][ lat['index'] ]['v'] ], 'ts': lat['items'][ lat['index'] ]['ts'] })
                lat['index'] += 1
                lon['index'] += 1

            # discard which ever measurement is earlier
            elif lat['items'][ lat['index'] ]['ts'] < lon['items'][ lon['index'] ]['ts']:
                lat['index'] += 1
                
            else:
                lon['index'] += 1

    # delete all datanodes for which we do not have values
    for siteData in data.values():
        names = set( siteData.keys() )
        for nodeName in names:
            if len( siteData[nodeName] ) == 0:
                del siteData[ nodeName ]
                
    updates = {} # entity updates are saved here        
    for siteName, siteData in data.items():
        siteUpdates = [] # entity updates for a single bus
        updates[ siteName ] = siteUpdates
        # names of datanodes we currently have values which in the beginning is all of them
        # during the process we will remove names of the datanodes whose values we have already processed
        nodeNames = set( siteData.keys() )
        # quantumleap requires that all attributes in a single update have the same timestamp
        # datanodes are updated at different times and frequencies so we have to find the values which have the same timestamp
        # so we will be processing values at different indexes at the value lists starting from the first ones 
        indexes = {} # indexes for each datanode value lists
        for name in nodeNames:
            indexes[name] = 0
        
        # process until we have no values left i.e. we have gone through each datanode's values    
        while len( nodeNames ) > 0:
            entity = {} # entity update goes here
            # collect names of nodes that no longer have values here
            doneNodes = set()
            # find the earliest timestamp we have at least one value for
            ts = min( [ siteData[name][ indexes[name]]['ts'] for name in nodeNames ] )
            # for each datanode values list at the index we are currently at see if
            # the value is from the earliest time stamp
            # if it is create an attribute update from it
            for nodeName in nodeNames:
                processdata = siteData[nodeName]
                index = indexes[ nodeName ]
                data = processdata[ index ]
                if ts == data['ts']:
                    # this value is now processed so for the next round we will check the next value
                    indexes[ nodeName ] = index +1
                    if index == len( processdata ) -1:
                        # all values for the node has been processed so add to doneNodes
                        doneNodes.add( nodeName )
            
                    attribute = {} # new attribute update goes here
                    # get information used to convert the datanode to attribute
                    conversionInfo = attributes[ nodeName ]
                    if nodeName == 'location':
                        # create a geo json item as the location value
                        attribute['type'] = 'geo:json'
                        attribute['value'] = {
                            'type': 'Point',
                            'coordinates': data['v']
                        }
                    
                    else:
                        # other attributes are processed similarly
                        value = data['v']
                        # see if there is a value mapping for this datanode
                        if 'mapping' in conversionInfo:
                            try:
                                # change the value according to the mapping
                                value = conversionInfo[ 'mapping' ][str(value)]
                                
                            except KeyError:
                                log.warning( f'No conversion mapping for {nodeName} value {value} of {siteName} at {datetime.fromtimestamp( data["ts"] )}.' )
                                # discard this value 
                                continue
                                
                        attribute['value'] = value
                        # if type is not in conversion info we assume a number
                        attribute['type'] = conversionInfo.get( 'type', 'Number' )
                        
                    attribute['metadata'] = {
                        'timestamp': {
                            'type': 'DateTime',
                            'value': datetime.utcfromtimestamp( data['ts'] ).isoformat() +'Z'
                        }
                    }

                    # get attribute name from conversion info
                    entity[ conversionInfo['name'] ] = attribute
                    
            # Remove nodes we don't any more have values from the nodes we are processing
            nodeNames.difference_update( doneNodes )
            
            entity['id'] = getBusId( siteName )
            entity['type'] = 'Vehicle'
            siteUpdates.append( entity )
            
    return updates
            
def saveUpdatesToFile( updates ):
    '''
    Method used in testing to save the entity updates to file.
    Not used currently.
    '''
    for siteName, update in updates.items():
        file = open( siteName +'.json', 'w' )
        json.dump( update, file, indent = 4  )
        file.close()
        
def loadUpdates():
    '''
    Testing method used to load updates from files.
    Not currently used.
    '''
    updates = {}
    for name in busNames:
        file = open( f'{name}.json', 'r' )
        updates[ name ] = json.load( file )
        
    return updates

# load conversion information from configuration file
conf = config.loadConfig( 'converter.json' )
attributes = conf['attributes']
busNames = conf['busIDs']