from typing import Union

from fastapi import Depends, HTTPException

from app.Models.Constraint import Constraint, EventStageConstraint, EventColorConstraint
from app.DB import get_collection
from app.Models.User import DBUser
from app.main import app, get_current_active_user, user_and_event_filter, allowed_constraints


@app.post("/events/{event_id}/constraint", response_model=Constraint)
async def add_event_constraint(event_id, constraint: Union[EventStageConstraint, EventColorConstraint],
                               current_user: DBUser = Depends(get_current_active_user)):
    """Adds a constraint to the event indicated by the provided event_id"""
    print(event_id)  # TODO event_id must match an actual event_id
    if not get_collection('event').find_one(user_and_event_filter(current_user.id, event_id)):
        raise HTTPException(status_code=404, detail="Item not found")
    fake_constraint_id: str = '1'
    final_constraint = allowed_constraints[constraint.constraint_type](**constraint.dict(), _id=fake_constraint_id)
    return final_constraint


@app.delete("/events/{event_id}/constraint/{constraint_id}", response_model=Constraint)
async def delete_event_constraint(event_id: str, constraint_id: str):
    """Deletes a constraint indicated by constaint_id from an event indicated by the provided event_id"""
    print(event_id)  # TODO event_id must match an actual event_id
    return constraint_id