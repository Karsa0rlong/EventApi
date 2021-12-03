from typing import Optional

import bson
from fastapi import HTTPException

from .DB import get_collection


def x_or_fail(x, collection_name, filter_factory: Optional[dict] = None, update_factory: Optional[dict] = None):
    collection_handle = get_collection(collection_name)
    possible = [filter_factory, update_factory]
    try:
        results: dict = collection_handle.__getattribute__(x)(*[param for param in possible if param is not None])
    except bson.errors.InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")
    if not results:
        raise HTTPException(status_code=404, detail="Item not found")
    return results


def find_one_or_fail(collection_name, filter_factory: dict):
    return x_or_fail('find_one', collection_name, filter_factory)


def delete_one_or_fail(collection_name, filter_factory: dict):
    return x_or_fail('delete_one', collection_name, filter_factory)


def update_one_or_fail(collection_name, filter_factory: dict,
                       update_factory: dict):
    return x_or_fail('update_one', collection_name, filter_factory, update_factory)