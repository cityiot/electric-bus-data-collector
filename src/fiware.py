# -*- coding: utf-8 -*-
'''
Module responsible for operations related to FIWARE such as creating entities and updating them.
'''

import requests
import time
import json
import logging

import dataConverter
import iotTicket
import config
import utils

# logger for module
log = logging.getLogger( __name__ )

#service = 'public_transport'
# location of the file used to keep a record of Orion subscriptions created by this tool
subscriptionsFileName = utils.getAppDir() / 'subscriptions.json'

def addSubscription():
    '''
    Creates a Orion subscription(s) for sending the data to QuantumLeap.
    Actual subscriptions created depends on the configuration.
    '''
    # create or open file for saving the ids of created subscriptions then create the actual subscriptions
    try:
        with open( subscriptionsFileName, 'r+' ) as file:
            _createSubscription( file, json.load( file ) )
            return
            
    except FileNotFoundError:
        pass
    
    with open( subscriptionsFileName, 'w' ) as file:
        _createSubscription( file, {} )
    
def _createSubscription( file, subscriptions ):
    '''
    Internal method used to actually create the subscriptions.
    File is file where subscription ids are saved.
    Subscriptions contains the content of the file as a dictionary or if file was just
    created it is an empty dictionary.
    '''
    # subscriptions created for the current Orion instance used
    mySubscriptions = subscriptions.get( orionUri )
    if mySubscriptions == None:
        # no subscriptions yet for this orion
        mySubscriptions = []
        subscriptions[ orionUri ] = mySubscriptions
        
    # create only if there already is no subscriptions
    if len( mySubscriptions ) == 0:
        # load subscription template 
        subscription = json.load( open( utils.getAppDir() / 'subscription.json', 'r' ) )
        if createAttributeSubscriptions:
            # create separate subscriptions for each attribute
            _sendAttributeSubscriptions( subscription, mySubscriptions )
            
        else:
            # create just one simple subscription for all attributes
            _sendSubscription( subscription, mySubscriptions )
            
        # save ids of created subscriptions to file
        _saveSubscriptions( file, subscriptions )
        # make sure that the subscriptions have been processed before sending any data
        time.sleep( 10.0 )
            
    else:
        log.debug( 'Subscription already created.' )

def _sendSubscription( subscription, mySubscriptions ):
    '''
    Create the given subscription.
    Subscription is the subscription to be created.
    mySubscription is a list where id of the created subscription is added.
    '''
    response = requests.post( orionUri +'subscriptions', json = subscription, headers = subscriptionHeaders )
    if response.status_code == 201:
        log.info( 'subscription created' )
        mySubscriptions.append( response.headers['Location'].split( '/' )[-1])
        
    else:
        log.error( 'Failed to create subscription. Status code ' +str( response.status_code ))
        log.error( response.text() )
        exit()
        
def _sendAttributeSubscriptions( subscription, mySubscriptions ):
    '''
    Creates separate subscriptions for each attribute.
    Subscription is the subscription template.
    mySubscriptions is list for created subscription ids.
    '''
    # list of attributes we will create subscriptions for
    # everything we have conversion info for and location
    attributes = set( [ attr['name'] for attr in dataConverter.attributes.values() ] )
    attributes.add( 'location' )
    for attribute in attributes:
        attrSub = dict( subscription )
        attrSub['subject']['condition']['attrs'] = [ attribute ]
        attrSub['notification']['attrs'] = [ attribute ]
        _sendSubscription( attrSub, mySubscriptions )
        
def _saveSubscriptions( file, subscriptions ):
    '''
    Save subscriptions to file.
    '''
    # clear the file in case there is something there already
    file.truncate( 0 )
    file.seek(0)
    json.dump( subscriptions, file, indent = 4 )
    
def createEntities():
    '''
    Creates entities with static attributes to Orion for all bus sites from IoT-Ticket.
    Does nothing if there already is a corresponding entity.
    '''
    # TODO: this is probably not no longer used check and remove if so
    createEntities.entityAlreadyExists = False
    for siteName in dataConverter.busNames.keys():
        entityId = dataConverter.getBusId( siteName )
        # see if there already is an entity with this id
        response = requests.get( orionUri +'entities/' +entityId, headers = headers )
        if response.status_code == 404:
            log.info( f'{entityId} does not exist already' )
            entity = {
                'id': entityId,
                'type': 'Vehicle',
                'source': { 'value': f'{iotTicket.baseUrl}sites/{siteName}' },
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
    '''
    Sends the given entity updates to FIWARE.
    Actual way of sending depends on configuration.
    '''
    # count how many HTTP requests will be done to send the updates
    sendEntities.count = 0
    # Different ways of making the updates an corresponding methods for do in so.
    updateMethods = {
        'small': sendDataSmall,
        'medium': sendDataMedium,
        'simple': sendDataSimple
    }
    # log how long update takes so get start time
    updateStart = time.time()
    updateMethod = updateMethods.get( updateStrategy )
    if updateMethod == None:
        log.error( f'Invalid FIWARE update method {updateStrategy}. Available strategies {", ".join(updateMethods.keys())}.')
        exit()
        
    updateMethod( updates )
    log.debug( 'Sent {0} update requests took {1:.1f} seconds'.format( sendEntities.count, time.time() -updateStart) )
    if sendToQl:
        # if we updated quantumleap directly send newest updates to Orion too
        _updateOrion( updates )
    
def sendDataSmall( updates ):
    '''
    FIWARE update method were one update per entity at most in one request is sent.
    Multiple updates from different entities per request is ok. 
    '''    
    dataLeft = True # do we still have data to send
    # we simply will start from the first update for each entity and go from there
    index = 0
    while dataLeft:
        # entities for this update request
        entities = []
        # lets take one update for each entity if there still is updates for that entity
        for entityUpdates in updates.values():
            if index < len( entityUpdates ):
                entities.append( entityUpdates[ index ] )
                if sendToQl and not qlMultipleNotify:
                    # we are sending to quantumleap but it does not support multiple elements in one request so we have to send just this one
                    sendEntities( [ entityUpdates[ index ] ] )
                
        index += 1
        if len( entities ) == 0:
            # we got no entities so we have sent them all
            dataLeft = False
            
        else:
            # we have some entities so send them
            if not sendToQl or qlMultipleNotify:
                # we are sending to Orion or quantumleap which supports multiple updates per request
                sendEntities( entities )
                
def sendDataSimple( updates ):
    '''
    FIWARE update strategy that sends all updates for an entity in one request.
    '''
    for entities in updates.values():
        sendEntities( entities )
        
def sendDataMedium( updates ):
    '''
    FIWARE update strategy where multiple updates per entity is send in one request
    but there is an upper limit for how many updates there can be in one request.
    '''
    size = 600 # updates per request
    for entities in updates.values():
        for start in range( 0, len( entities ), size ):
            end = start +size
            if end > len( entities ):
                end = len( entities )
                
            sendEntities( entities[start:end] )

def _updateOrion( updates ):
    '''
    Send latest entity updates in updates to Orion.
    Used when everything else is send directly to quantumleap.
    '''
    # we want to sent to Orion the latest update for each attribute so get the attributes
    attrs = dataConverter.getAttributeNames()
    entities = [] # build an update for each entity here
    for entityUpdates in updates.values():
        entity = {} # the entity update
        # attributes we still would like to have updates for
        missingAttrs = set( attrs )
        # start from the end i.e. newest updates
        for i in range( len( entityUpdates ) -1, -1, -1):
            update = entityUpdates[i]
            if len( entity ) == 0:
                # first iteration which tells us that we have at least something so add entity basic info
                entity['id'] = update['id']
                entity['type'] = update['type']
            
            for attr in update:
                if attr in [ 'id', 'type' ]:
                    continue
                
                if attr in missingAttrs:
                    # we do not yet have an update for this
                    entity[ attr ] = update[ attr ]
                    # but no we have
                    missingAttrs.remove( attr )
                    
                if len( missingAttrs ) == 0:
                    # we already have updates for all
                    break
        
        if len( entity ) > 0:
            # we got some updates so we want to send them
            entities.append( entity )    
            
    # send the entities and ensure that they are send to Orion
    sendEntities( entities, False )
                
def sendEntities( entities, useQl = None ):
    '''
    Send the given entity updates to FIWARE.
    Configuration tells if they are send to Orion or Quantumleap.
    Configuration can be overwritten with the useQl parameter value False or True.
    '''
    if len( entities ) == 0:
        log.debug( 'sendEntities got entity list with 0 entities. No need to send it.' )
        return
    
    if useQl == None:
        # if no value use one from configuration
        useQl = sendToQl

    # keep count how many request we are sending        
    sendEntities.count = sendEntities.count +1
    
    # url we are sending the updates assume Orion first
    uri = orionUri +'op/update'
    # request body attribute that has the entities
    entityAttr = 'entities'
    # status code of successfull request
    successStatus = 204
    
    if useQl:
        uri = qlUri +'notify'
        entityAttr = 'data'
        successStatus = 200
        
    payload = {} # request payload
    payload[entityAttr] = entities
    if not useQl:
        # Orion batch update type
        payload['actionType'] = 'append'
    
    #file = open( 'payload' +str(sendEntities.count) +'.json', 'w' )
    #json.dump( payload, file, indent = 4 )
    #file.close()
    retryTime = 10 # in case of failure how long to wait before retrying
    while True:
        try:
            response = requests.post( uri, headers = headers, json = payload, timeout = 120 )
            if response.status_code != successStatus:
                log.error( f'Update failed code: {response.status_code}. Retrying after {retryTime} seconds.' )
                log.error( response.text )
        
            else:
                break # success
                
        except KeyboardInterrupt:
            # user wants to stop so raise
            raise
         
        except:
            log.exception( f'Exception when updating FIWARE. Retrying after {retryTime} seconds.' )
        
        time.sleep( retryTime )
        
def deleteAllSubscriptions():
    '''
    Deletes all subscriptions from Orion. Not just those created by this tool.
    Not used anywhere. Can be used when testing.
    '''
    response = requests.get( orionUri +'subscriptions', headers = subscriptionHeaders )
    for subscription in response.json():
        deleteResp = requests.delete( orionUri +'subscriptions/' +subscription['id'], headers = subscriptionHeaders )
        print( str( deleteResp.status_code ) +' status code when removing subscription ' +str( subscription['id']) )

def deleteAll():
    '''
    Delete everything created by this tool from FIWARE: subscriptions, Orion entities and history data from QuantumLeap.
    Not used anywhere. Can be used for example when testing.
    '''
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
    '''
    Logs info about  if all updates have arrived to QuantumLeap.
    Not currently used. Was used in testing.
    '''
    
    def getTime( item ):
        '''
        Get a timestamp from an entity update.
        '''
        for value in item.values():
            if 'metadata' in value:
                return value['metadata']['timestamp']['value']
            
    for name, values in updates.items():
        entityId = dataConverter.getBusId( name )
        if len( values ) == 0:
            log.info( f'no updates for {entityId}' )
            continue
        
        params = {} # ql api request parameters
        # get data from ql from the time period we have updates for
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
            
        # print len of index i.e. time moments we have measurements for and number of updates
        # they should be the same since there is an update for each timestamp.
        log.debug( f'{entityId} {len( index )} {len( values )}' )

# used to keep count how many requests have been send        
sendEntities.count = 0

# load configuration
conf = config.loadConfig( 'fiware.json' )
orionUri = conf['orion_URL']
qlUri = conf['quantumleap_URL']

headers = conf.get( 'custom_headers', {} )
headers['Fiware-Service'] = conf['service']
headers['Fiware-ServicePath'] = conf['service_path']
# when dealing with subscriptions service path is not required
subscriptionHeaders = dict( headers )
del subscriptionHeaders['Fiware-ServicePath']

sendToQl = conf['send_to_ql']
qlMultipleNotify = conf['ql_multiple_notify']
updateStrategy = conf['update_strategy']
createAttributeSubscriptions = conf['create_attribute_subscriptions']
