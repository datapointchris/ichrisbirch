"""Starts the database for the very first time"""
import os

import dotenv
import pymongo

import mongomanager

dotenv.load_dotenv()


CLIENT = pymongo.MongoClient(os.environ.get('MONGODB_LOCAL'))
DATABASE = os.environ.get('DATABASE')
COLLECTION = os.environ.get('COLLECTION')
db = mongomanager.DBManager(client=CLIENT, database=DATABASE, collection=COLLECTION)

if __name__ == '__main__':
    db.reset_db()
    print('Successfully reset the databse!')
