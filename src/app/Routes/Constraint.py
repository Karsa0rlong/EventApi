from bson import ObjectId
from fastapi import Depends, HTTPException, APIRouter
from pydantic.color import Color

from ..DB.Utilities import find_one_or_fail, update_one_or_fail
from ..Models.Constraint import Constraint, EventStageConstraint, EventColorConstraint, EventTimeConstraint, \
    NewConstraint, EventColor
from ..Models.User import DBUser
from ..dependencies import get_current_active_user, user_and_event_filter

ConstraintRouter = APIRouter(prefix="/events", tags=["constraints"])


@ConstraintRouter.get("/constraint")
async def get_all_constraints():
    pass


def add_constraint_to_event(current_user: DBUser, event_id, new_constraint):
    if not find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)):
        raise HTTPException(status_code=404, detail="Item not found")

    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id),
                       {"$push": {"constraints": new_constraint.dict()}})


@ConstraintRouter.post("/{event_id}/constraint/color", response_model=EventColorConstraint)
async def add_color(event_id, color: Color, current_user: DBUser = Depends(get_current_active_user)):
    valid_color = EventColor(color=color).dict()
    new_constraint = EventColorConstraint(**valid_color, name=color.as_named(fallback=True), _id=str(ObjectId()))
    add_constraint_to_event(current_user=current_user,
                            event_id=event_id,
                            new_constraint=new_constraint)
    return new_constraint


@ConstraintRouter.post("/{event_id}/constraint/date", response_model=EventColorConstraint)
async def add_date(event_id, color: Color, current_user: DBUser = Depends(get_current_active_user)):
    valid_color = EventColor(color=color).dict()
    new_constraint = EventColorConstraint(**valid_color, name=color.as_named(fallback=True), _id=str(ObjectId()))
    add_constraint_to_event(current_user=current_user,
                            event_id=event_id,
                            new_constraint=new_constraint)

    return new_constraint


@ConstraintRouter.post("/{event_id}/constraint", response_model=Constraint)
async def add_event_constraint(event_id, constraint: NewConstraint,
                               current_user: DBUser = Depends(get_current_active_user)):
    """Adds a constraint to the event indicated by the provided event_id"""
    allowed_constraints = {"EventStageConstraint": EventStageConstraint,
                           "EventColorConstraint": EventColorConstraint,
                           "EventTimeConstraint": EventTimeConstraint
                           }
    final_constraint = allowed_constraints[constraint.constraint_type](**constraint.dict(), _id=ObjectId())
    add_constraint_to_event(current_user, event_id, final_constraint)
    return final_constraint


@ConstraintRouter.delete("/{event_id}/constraint/{constraint_id}", response_model=Constraint)
async def delete_event_constraint(event_id: str, constraint_id: str):
    """Deletes a constraint indicated by constaint_id from an event indicated by the provided event_id"""
    print(event_id)  # TODO event_id must match an actual event_id
    return constraint_id
