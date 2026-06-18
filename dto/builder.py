from dto.index import *

def databaseReader():
    import json
    try:
        with open('assets/config/database-config.json', 'r') as f:
            return json.load(f)
    except:
        return {}
