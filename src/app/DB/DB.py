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
    pass
    # print("test")
