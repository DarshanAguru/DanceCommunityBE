from pymongo.server_api import ServerApi
from pymongo.mongo_client import MongoClient

def connectDB():
    try:
        server_api = ServerApi('1')
        client = MongoClient("<Your Mongo  URL>", server_api=server_api)
        db  = client['test']
        return db
    except Exception as e:
        print(e)
        return None
