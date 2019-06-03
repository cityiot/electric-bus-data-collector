# -*- coding: utf-8 -*-

import requests
import time
import json
import logging

import dataConverter
import config
import utils

log = logging.getLogger( __name__ )

#service = 'public_transport'
subscriptionsFileName = utils.getAppDir() / 'subscriptions.json'

def addSubscription():
    try:
        with open( subscriptionsFileName, 'r+' ) as file:
            _createSubscription( file, json.load( file ) )
            return
            
    except FileNotFoundError:
        pass
    
    with open( subscriptionsFileName, 'w' ) as file:
        _createSubscription( file, {} )
    
def _createSubscription( file, subscriptions ):
    mySubscriptions = subscriptions.get( orionUri )
    if mySubscriptions == None:
        mySubscriptions = []
        subscriptions[ orionUri ] = mySubscriptions
        
    if len( mySubscriptions ) == 0:
        subscription = json.load( open( utils.getAppDir() / 'subscription.json', 'r' ) )
        if createAttributeSubscriptions:
            _sendAttributeSubscriptions( subscription, mySubscriptions )
            
        else:
            _sendSubscription( subscription, mySubscriptions )
            
        _saveSubscriptions( file, subscriptions )
        time.sleep( 10.0 )
            
    else:
        log.debug( 'Subscription already created.' )

def _sendSubscription( subscription, mySubscriptions ):
    response = requests.post( orionUri +'subscriptions', json = subscription, headers = subscriptionHeaders )
    if response.status_code == 201:
        log.info( 'subscription created' )
        mySubscriptions.append( response.headers['Location'].split( '/' )[-1])
        
    else:
        log.error( 'Failed to create subscription. Status code ' +str( response.status_code ))
        log.error( response.text() )
        exit()
        
def _sendAttributeSubscriptions( subscription, mySubscriptions ):
    attributes = set( [ attr['name'] for attr in dataConverter.attributes.values() ] )
    attributes.add( 'location' )
    for attribute in attributes:
        attrSub = dict( subscription )
        attrSub['subject']['condition']['attrs'] = [ attribute ]
        attrSub['notification']['attrs'] = [ attribute ]
        _sendSubscription( attrSub, mySubscriptions )
        
def _saveSubscriptions( file, subscriptions ):
    file.truncate( 0 )
    file.seek(0)
    json.dump( subscriptions, file, indent = 4 )
    
def createEntities():
    createEntities.entityAlreadyExists = False
    for siteName in dataConverter.busNames.keys():
        entityId = dataConverter.getBusId( siteName )
        response = requests.get( orionUri +'entities/' +entityId, headers = headers )
        if response.status_code == 404:
            log.info( f'{entityId} does not exist already' )
            entity = {
                'id': entityId,
                'type': 'Vehicle',
                'name': { 'value': dataConverter.getBusName( siteName ) },
                'vehicleType': { 'value': 'bus' },
                'category': { 'value': [ 'public', 'tracked' ] },
                'fleetVehicleId': { 'value': dataConverter.getBusName( siteName ) },
                'serviceProvided': { 'value': [ 'urbanTransit' ] }
            }
            
            response = requests.post( orionUri +'entities', json = entity, headers = headers  )
            if response.status_code == 201:
                log.info( 'Entity created' )
            
        elif response.status_code == 200:
            createEntities.entityAlreadyExists = True
            log.info( f'{entityId} already exists' )

def sendData( updates ):
    sendEntities.count = 0
    updateMethods = {
        'small': sendDataSmall,
        'medium': sendDataMedium,
        'simple': sendDataSimple
    }
    updateStart = time.time()
    updateMethod = updateMethods.get( updateStrategy )
    if updateMethod == None:
        log.error( f'Invalid FIWARE update method {updateStrategy}. Available strategies {", ".join(updateMethods.keys())}.')
        exit()
        
    updateMethod( updates )
    log.debug( 'Sent {0} update requests took {1:.1f} seconds'.format( sendEntities.count, time.time() -updateStart) )
    if sendToQl:
        _updateOrion( updates )
    
def sendDataSmall( updates ):    
    dataLeft = True
    index = 0
    while dataLeft:
        entities = []
        for entityUpdates in updates.values():
            if index < len( entityUpdates ):
                entities.append( entityUpdates[ index ] )
                if sendToQl and not qlMultipleNotify:
                    sendEntities( [ entityUpdates[ index ] ] )
                
        index += 1
        if len( entities ) == 0:
            dataLeft = False
            
        else:
            if not sendToQl or qlMultipleNotify:
                sendEntities( entities )
                
def sendDataSimple( updates ):
    for entities in updates.values():
        sendEntities( entities )
        
def sendDataMedium( updates ):
    size = 600
    for entities in updates.values():
        for start in range( 0, len( entities ), size ):
            end = start +size
            if end > len( entities ):
                end = len( entities )
                
            sendEntities( entities[start:end] )

def _updateOrion( updates ):
    attrs = dataConverter.getAttributeNames()
    entities = []
    for entityUpdates in updates.values():
        entity = {}
        missingAttrs = set( attrs )
        for i in range( len( entityUpdates ) -1, -1, -1):
            update = entityUpdates[i]
            if len( entity ) == 0:
                entity['id'] = update['id']
                entity['type'] = update['type']
            
            for attr in update:
                if attr in [ 'id', 'type' ]:
                    continue
                
                if attr in missingAttrs:
                    entity[ attr ] = update[ attr ]
                    missingAttrs.remove( attr )
                    
                if len( missingAttrs ) == 0:
                    break
        
        if len( entity ) > 0:
            entities.append( entity )    
            
    sendEntities( entities, False )
                
def sendEntities( entities, useQl = None ):
    if useQl == None:
        useQl = sendToQl
    sendEntities.count = sendEntities.count +1
    
    uri = orionUri +'op/update'
    entityAttr = 'entities'
    successStatus = 204
    
    if useQl:
        uri = qlUri +'notify'
        entityAttr = 'data'
        successStatus = 200
        
    payload = {}
    payload[entityAttr] = entities
    if not useQl:
        payload['actionType'] = 'append'
    
    #file = open( 'payload' +str(sendEntities.count) +'.json', 'w' )
    #json.dump( payload, file, indent = 4 )
    #file.close()
    retryTime = 10
    while True:
        try:
            response = requests.post( uri, headers = headers, json = payload )
            if response.status_code != successStatus:
                log.error( f'Update failed code: {response.status_code}. Retrying after {retryTime} seconds.' )
                log.error( response.text )
        
            else:
                break
                
        except:
            log.exception( f'Exception when updating FIWARE. Retrying after {retryTime} seconds.' )
        
        time.sleep( retryTime )
        
def deleteAllSubscriptions():
    response = requests.get( orionUri +'subscriptions', headers = subscriptionHeaders )
    for subscription in response.json():
        deleteResp = requests.delete( orionUri +'subscriptions/' +subscription['id'], headers = subscriptionHeaders )
        print( str( deleteResp.status_code ) +' status code when removing subscription ' +str( subscription['id']) )

def deleteAll():
    try:
        with open( subscriptionsFileName, 'r+' ) as file:
            subscriptions = json.load( file )
            mySubscriptions = subscriptions.get( orionUri )
            if mySubscriptions != None:
                for subscriptionId in mySubscriptions:
                    deleteResp = requests.delete( orionUri +'subscriptions/' +subscriptionId, headers = subscriptionHeaders )
                    print( str( deleteResp.status_code ) +' status code when removing subscription ' +subscriptionId )
                    
                del subscriptions[orionUri]
                _saveSubscriptions( file, subscriptions )
                
    except FileNotFoundError:
        pass
    
    for entityId in [ dataConverter.getBusId( name ) for name in dataConverter.busNames ]:
        response = requests.delete( orionUri +'entities/' +entityId, headers = headers )
        print( f'{response.status_code} status code when removing {entityId} from orion.' )
        response = requests.delete( qlUri +'entities/' +entityId, headers = headers )
        print( f'{response.status_code} status code when removing {entityId} from Quantumleap.' )        
        
def checkUpdates( updates ):
    def getTime( item ):
        for value in item.values():
            if 'metadata' in value:
                return value['metadata']['timestamp']['value']
            
    for name, values in updates.items():
        entityId = dataConverter.getBusId( name )
        if len( values ) == 0:
            log.info( f'no updates for {entityId}' )
            continue
        
        params = {}
        params['fromDate'] = getTime( values[0] )
        params['toDate'] = getTime( values[-1] )
        
        response = requests.get( f'{qlUri}entities/{entityId}', headers = headers, params = params )
        if response.status_code != 200:
            log.warning( f'{response.status_code} status code when getting measurements from quantumleap for entity {entityId}. ')
            continue
        
        content = response.json()
        index = content['data']['index']
        data = {}
        for attributeData in content['data']['attributes']:
            data[ attributeData['attrName']] = attributeData['values']
            
        log.debug( f'{entityId} {len( index )} {len( values )}' )
        
sendEntities.count = 0

conf = config.loadConfig( 'fiware.json' )
orionUri = conf['orion_URL']
qlUri = conf['quantumleap_URL']

headers = conf.get( 'custom_headers', {} )
headers['Fiware-Service'] = conf['service']
headers['Fiware-ServicePath'] = conf['service_path']
subscriptionHeaders = dict( headers )
del subscriptionHeaders['Fiware-ServicePath']

sendToQl = conf['send_to_ql']
qlMultipleNotify = conf['ql_multiple_notify']
updateStrategy = conf['update_strategy']
createAttributeSubscriptions = conf['create_attribute_subscriptions']