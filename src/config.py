# -*- coding: utf-8 -*-
# Copyright 2019 Tampere University
# This software was developed as a part of the CityIoT project: https://www.cityiot.fi/english
# This source code is licensed under the 3-clause BSD license. See license.txt in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi>
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