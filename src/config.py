import json
import utils

def loadConfig( fileName ):
    confFile = utils.getAppDir() / 'conf' / fileName
    with open( confFile, 'r' ) as file:
        return json.load( file )