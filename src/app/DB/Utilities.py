from functools import partial
from typing import Optional

import bson
from fastapi import HTTPException

from .DB import get_collection


def or_fail(func):
    try:
        results = func()
    except bson.errors.InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")
    if not results:
        raise HTTPException(status_code=404, detail="Item not found")
    return results


def fail_on_success(func, error_code: int = 422, error_msg="Unprocessable Entity"):
    try:
        results = func()
    except bson.errors.InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")
    if not results:
        return results
    raise HTTPException(status_code=404, detail="Item not found")


def x_or_x(x, x2, collection_name, filter_factory: Optional[dict] = None, update_factory: Optional[dict] = None):
    collection_handle = get_collection(collection_name)
    possible = [filter_factory, update_factory]
    func = partial(collection_handle.__getattribute__(x), *[param for param in possible if param is not None])
    return x2(func)


def x_or_fail(x, collection_name, filter_factory: Optional[dict] = None, update_factory: Optional[dict] = None):
    return x_or_x(x, or_fail, collection_name, filter_factory, update_factory)


def x_or_fail_on_success(x, collection_name, filter_factory: Optional[dict] = None,
                         update_factory: Optional[dict] = None):
    return x_or_x(x, fail_on_success, collection_name, filter_factory, update_factory)


def find_one_or_fail(collection_name, filter_factory: dict):
    return x_or_fail('find_one', collection_name, filter_factory)


def delete_one_or_fail(collection_name, filter_factory: dict):
    return x_or_fail('delete_one', collection_name, filter_factory)


def update_one_or_fail(collection_name, filter_factory: dict,
                       update_factory: dict):
    return x_or_fail('update_one', collection_name, filter_factory, update_factory)


def fail_if_found_one(collection_name, filter_factory: dict):
    """Fails if item is found."""
    return x_or_fail_on_success('find_one', collection_name, filter_factory)
