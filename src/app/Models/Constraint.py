from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import BaseModel, Field, validator
from pydantic.color import Color


class ConstraintType(str, Enum):
    """Types of constraints that can be used."""
    stage = 'EventStageConstraint'
    color = 'EventColorConstraint'
    time = 'EventTimeConstraint'


class NewConstraint(BaseModel):
    name: str = Field(..., max_length=25)
    constraint_type: ConstraintType


class Constraint(NewConstraint):
    """A condition that must be fulfilled before"""
    id: str = Field(..., alias='_id')

    @validator('id', pre=True, always=True)
    def id_to_string(cls, v: ObjectId):
        return str(v)


class EventStage(BaseModel):
    """A constraint on the stage of an event """
    event_id: str


class EventStageConstraint(EventStage, Constraint):
    constraint_type: ConstraintType = ConstraintType.stage
    pass


class EventTime(BaseModel):
    start_time: datetime
    end_time: datetime
    all_day = bool


class EventTimeConstraint(EventTime, Constraint):
    constraint_type: ConstraintType = ConstraintType.time
    pass


class EventColor(BaseModel):
    color: Color

    @validator('color')
    def color_to_hex_string(cls, v: Color):
        return v.as_hex()


class EventColorConstraint(EventColor, Constraint):
    constraint_type: ConstraintType = ConstraintType.color
    pass


if __name__ == "__main__":
    pass
