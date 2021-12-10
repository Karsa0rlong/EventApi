from datetime import datetime
from enum import Enum
from typing import List

from bson import ObjectId
from fastapi import APIRouter
from pydantic import BaseModel, Field, validator

from .Constraint import EventColor

router = APIRouter()


class Tag(BaseModel):
    tag: str = Field(..., min_length=1, max_length=64)


class EventTime(BaseModel):
    start_time: datetime
    end_time: datetime
    all_day: bool = False


class Tags(BaseModel):
    tags: List[Tag] = Field(..., max_items=10)  # [set of tags applicable to event]

    @validator('tags')
    def tag_length(cls, v):
        for item in v:
            if len(item.tag) > 64:
                raise ValueError("Only five tags are allowed")
        return v

    @validator('tags')
    def no_duplicates(cls, v):
        tag_set_len = len(set([item.tag for item in v]))
        tag_len = len(v)
        if not tag_len == tag_set_len:
            raise ValueError("Duplicates not allowed")
        return v


class NewEvent(Tags):
    name: str = Field(..., min_length=1, max_length=64)  # "Name of Event"
    description: str = Field(..., max_length=256)  # "A description of the event"
    time_details: EventTime
    presentation: EventColor

    class Config:
        use_enum_values = True


class Stage(str, Enum):
    started = 'started'
    in_progress = 'in_progress'
    complete = 'complete'


class NewEventInDB(NewEvent):
    stage: Stage  # "stage of event"
    owner_id: str  # Who owns the event


class EventResponse(NewEvent):
    id: str = Field(..., alias='_id')

    @validator('id', pre=True, always=True)
    def id_to_string(cls, v: ObjectId):
        return str(v)


class EventInDB(EventResponse):
    stage: Stage  # "stage of event"
    owner_id: str  # Who owns the event


if __name__ == "__main__":
    pass
