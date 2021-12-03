from typing import Optional

from bson import ObjectId
from pydantic import BaseModel, Field, validator


class User(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = None


class NewDBUser(User):
    """A user before they are saved in the DB"""
    hashed_password: str


class DBUser(NewDBUser):
    id: str = Field(..., alias='_id')

    @validator('id', pre=True, always=True)
    def id_to_string(cls, v: ObjectId):
        return str(v)
