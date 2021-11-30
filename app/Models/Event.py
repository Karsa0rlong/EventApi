from enum import Enum
from typing import List

from bson import ObjectId
from fastapi import APIRouter
from pydantic import BaseModel, Field, validator
from pydantic.color import Color

from app.Models.Constraint import ConstraintType, Constraint, EventColorConstraint

router = APIRouter()


class BaseEvent(BaseModel):
    name: str  # "Name of Event"
    description: str  # "A description of the event"
    tags: List[str]  # [list of tags applicable to event]
    constraints: List[Constraint]  # [list of Constraints]

    @validator('tags')
    def num_tags_allowed(cls, v):
        if len(v) > 5:
            raise ValueError("Only five tags are allowed")
        return v

    @validator('constraints')
    def num_constraints_allowed(cls, v):
        if len(v) > 5:
            raise ValueError("Only five constraints are allowed")
        return v

    class Config:
        use_enum_values = True
        max_anystr_length = 25


class Stage(str, Enum):
    started = 'started'
    in_progress = 'in_progress'
    complete = 'complete'


class NewEventInDB(BaseEvent):
    stage: Stage  # "stage of event"
    owner_id: str  # Who owns the event


class EventResponse(BaseEvent):
    id: str = Field(..., alias='_id')

    @validator('id', pre=True, always=True)
    def id_to_string(cls, v: ObjectId):
        return str(v)


class EventInDB(EventResponse):
    stage: Stage  # "stage of event"
    owner_id: str  # Who owns the event


if __name__ == "__main__":
    print("test")
    e = BaseEvent(name='Test', description="A test event", tags=["test-tag1", "test-tag2"],
                  constraints=[
                      EventColorConstraint(name='test', constraint_type=ConstraintType.color, color=Color('#d60404'),
                                           _id='1')])
    print(e.dict())
    print("test")
