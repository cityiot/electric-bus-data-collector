# -*- coding: utf-8 -*-
'''
Separate utility for printing out last measurements for each datanode of each site in IoT-Ticket.
usage: python src/buses.py
'''

import requests
from datetime import datetime

import config

conf = config.loadConfig( 'iot-ticket.json' )

auth = ( conf['username'], conf['password'] )
baseUrl = conf['url']

response = requests.get( baseUrl +'sites/', auth = auth, params = { 'expand': 'name,id' } )

for site in response.json()['items']:
    siteResponse = requests.get( site['href'] +'/datanodes', auth = auth, params = { 'expand': 'name,id,unit,processData', 'limit': 50 } )
    print( site['name'] +' ' +str(site['id'] ))
        
    for node in siteResponse.json()['items']:
        name = node['name']
        id = str( node['id'])
        if 'items' not in node['processData']:
            print( name +' ' +id  )
            continue
            
        processData = node['processData']['items'][0]
        value = str( processData['v'] )
        timestamp = str( datetime.fromtimestamp( processData['ts'] /1000000 ) )
        unit = node.get( 'unit', '' )
        print( '{0} ({4}) {1} {2} {3}'.format( name, value, unit, timestamp, id ))