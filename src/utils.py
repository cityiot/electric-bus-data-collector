# -*- coding: utf-8 -*-
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