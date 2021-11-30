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


class EventStageConstraint(Constraint):
    """A constraint on the stage of an event """
    event_id: str
    constraint_type: ConstraintType = ConstraintType.stage


class EventTimeConstraint(Constraint):
    """A constraint on the stage of an event """
    start_time: datetime
    end_time: datetime
    constraint_type: ConstraintType = ConstraintType.time


class EventColorConstraint(Constraint):
    """A condition that must be fulfilled before"""
    color: Color
    constraint_type: ConstraintType = ConstraintType.color
