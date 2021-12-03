from bson import ObjectId
from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure
from starlette import status

MONGO_CONTAINER_NAME = 'mongo'


def get_client() -> MongoClient:
    """Creates the db client."""
    client = MongoClient(MONGO_CONTAINER_NAME, 27017)
    try:
        # Test the client is alive.
        client.admin.command('ping')
    except ConnectionFailure:
        # Client is dead cannot service request
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return client


def get_collection(collection_name: str) -> Collection:
    database = get_client().get_database('reminder')
    collection = database.get_collection(collection_name)
    return collection


if __name__ == "__main__":
    database = get_client().get_database('reminder')
    events = get_collection('events')
    users: Collection = get_collection('users')
    events_cursor = events.find({})
    user_cursor = users.find({})
    results = events.delete_one({'_id': ObjectId('61a3f928095f630249f1ee2f')})
    print([event for event in events_cursor])
    print([user for user in user_cursor])
    print(database.list_collection_names())
    # print("test")
