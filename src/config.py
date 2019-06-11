# -*- coding: utf-8 -*-
'''
Helper module for reading configuration files in the JSON format
'''

import json
import utils

def loadConfig( fileName ):
    '''
    Reads the named file from configuration directory and converts it to JSON.
    The conversion result is returned.
    '''
    confFile = utils.getAppDir() / 'conf' / fileName
    with open( confFile, 'r' ) as file:
        return json.load( file )