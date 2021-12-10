from typing import Optional

import bson
from bson import ObjectId
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import BaseModel
from pymongo.collection import Collection
from starlette import status

from .DB.DB import get_client
from .Models.User import DBUser

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> DBUser:
    """Gets user from token passed in JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    # JWT is valid, get user from db by username
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: DBUser = Depends(get_current_user)) -> DBUser:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


def user_and_event_filter(user_id, event_id):
    """Filters: user_id owns event at event_id
        event_id must be a valid ObjectId or 404"""
    try:
        event_id = ObjectId(event_id)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"owner_id": user_id, "_id": ObjectId(event_id)}


SECRET_KEY = "b1fd8ba612900db8ff9f007e94ef8bdb84436d8f14db6274a29e4fb3925e63de"
ALGORITHM = "HS256"


class TokenData(BaseModel):
    username: Optional[str] = None


def get_user(username: str) -> DBUser:
    """Get user from database."""
    client = get_client()
    database = client.get_database('reminder')
    users: Collection = database.get_collection('users')
    user_dict = users.find_one({"username": f"{username}"})
    if user_dict is not None:
        return DBUser(**user_dict)
