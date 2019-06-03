import os.path
from pathlib import Path

def s2mrs( seconds ):
    return round( seconds *1000000 )

def mrs2s( microSeconds ):
    return microSeconds /1000000

def getAppDir():
    return Path( os.path.realpath( __file__ )).parent.parent