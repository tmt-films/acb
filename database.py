from datetime import datetime
from config import MONGO_URL
import pymongo
import gridfs
import pytz


class DataBase:
    def __init__(self):
        self.dataset, self.storage, self.database = self.connect()

    def connect(self):
        mongod = pymongo.MongoClient(MONGO_URL)

        database = mongod["TABLE"]

        dataset = database["COLLECTION"]

        storage = gridfs.GridFS(database)

        return dataset, storage, database

    def search(self, user_id=None, allEntry=None):
        if allEntry:
            result = self.dataset.find()
        else:
            result = self.dataset.find_one({"_id": user_id})

        return result

    def insert(self, user_id, name, username):
        # time-stamp
        IST = pytz.timezone('Asia/Kolkata')
        time_stamp = datetime.now(IST).strftime('%Y-%m-%d || %H:%M:%S')

        self.dataset.insert_one({"_id": user_id,
                                 "name": name,
                                 "username": username,
                                 "timestamp": time_stamp})

    def update(self, user_id, new_data):
        self.dataset.update_one({"_id": user_id}, {"$set": new_data})

    def get_all_user_ids(self):
        """
        Retrieves a list of all user IDs from the database.
        """
        # Find all documents, projecting only the _id field for efficiency
        cursor = self.dataset.find({}, {'_id': 1})
        # Extract the _id from each document and return as a list
        return [doc['_id'] for doc in cursor]
