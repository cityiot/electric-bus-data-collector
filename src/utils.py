# -*- coding: utf-8 -*-
# Copyright 2019 Tampere University
# This software was developed as a part of the CityIoT project: https://www.cityiot.fi/english
# This source code is licensed under the 3-clause BSD license. See license.txt in the repository root directory.
# Author(s): Otto Hylli <otto.hylli@tuni.fi>
'''
Contains some small helper methods.
'''

import os.path
from pathlib import Path

def s2mrs( seconds ):
    '''
    Convert seconds to microseconds.
    Returns rounded result as an integer.
    '''
    return round( seconds *1000000 )

def mrs2s( microSeconds ):
    '''
    Convert microseconds to seconds.
    '''
    return microSeconds /1000000

def getAppDir():
    '''
    Get the absolute path for the tool's root directory i.e. directory containing src, conf etch.
    '''
    # this file's parent dir is src and the root is src's parent
    return Path( os.path.realpath( __file__ )).parent.parent