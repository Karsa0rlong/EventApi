from string import hexdigits
from typing import List

from fastapi import APIRouter, Depends, Path

from ..DB.DB import get_collection
from ..DB.Utilities import find_one_or_fail, delete_one_or_fail, update_one_or_fail
from ..Models.Event import EventResponse, BaseEvent, NewEventInDB, Stage, EventInDB
from ..Models.User import DBUser
from ..dependencies import get_current_active_user, user_and_event_filter

EventRouter = APIRouter(prefix="/events", tags=["events"])


@EventRouter.get("/events/", response_model=List[EventResponse])
async def get_all_events(current_user: DBUser = Depends(get_current_active_user)):
    """Returns list of all events"""
    events_collection = get_collection('events')
    events_cursor = events_collection.find({'owner_id': current_user.id})
    return [event for event in events_cursor]


@EventRouter.post("/events/", response_model=EventResponse)
async def add_event(event_data: BaseEvent, current_user: DBUser = Depends(get_current_active_user)):
    new_event = NewEventInDB(**event_data.dict(), owner_id=current_user.id, stage=Stage.started)
    events_collection = get_collection('events')
    results = events_collection.insert_one(new_event.dict())
    return EventInDB(**new_event.dict(), _id=str(results.inserted_id))


@EventRouter.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: str = Path(..., regex=f'[{hexdigits}]+'),
                    current_user: DBUser = Depends(get_current_active_user)):
    results = find_one_or_fail('events', user_and_event_filter(current_user.id, event_id))
    return results


@EventRouter.delete("/events/{event_id}", response_model=EventResponse)
async def delete_event(event_id: str = Path(..., regex=f'[{hexdigits}]+'),
                       current_user: DBUser = Depends(get_current_active_user)):
    """Deletes an event from storage."""
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    delete_one_or_fail('events', user_and_event_filter(current_user.id, event_id))
    return results


@EventRouter.post("/events/{event_id}/stage", response_model=EventResponse)
async def set_event_stage(event_id: str, stage: Stage, current_user: DBUser = Depends(get_current_active_user)):
    """Marks an event as complete. Does not actually remove from storage."""
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id), {"$set": {"stage": stage}})
    return results