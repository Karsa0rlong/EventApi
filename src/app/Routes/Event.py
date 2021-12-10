from string import hexdigits
from typing import List

from fastapi import APIRouter, Depends, Path, Body, HTTPException
from pydantic import ValidationError

from ..DB.DB import get_collection
from ..DB.Utilities import find_one_or_fail, delete_one_or_fail, update_one_or_fail
from ..Models.Constraint import EventColor
from ..Models.Event import EventResponse, NewEvent, NewEventInDB, Stage, EventInDB, Tag, Tags
from ..Models.User import DBUser
from ..dependencies import get_current_active_user, user_and_event_filter

EventRouter = APIRouter(prefix="/events", tags=["events"])
eventIDType = Path(..., regex=f'[{hexdigits}]+', max_length=24)


@EventRouter.get("/events/", response_model=List[EventResponse])
async def get_all_events(current_user: DBUser = Depends(get_current_active_user)):
    """Returns list of all events"""
    events_collection = get_collection('events')
    events_cursor = events_collection.find({'owner_id': current_user.id})
    return [event for event in events_cursor]


@EventRouter.post("/events/", response_model=EventResponse)
async def add_event(event_data: NewEvent, current_user: DBUser = Depends(get_current_active_user)):
    new_event = NewEventInDB(**event_data.dict(), owner_id=current_user.id, stage=Stage.started)
    events_collection = get_collection('events')
    results = events_collection.insert_one(new_event.dict())
    return EventInDB(**new_event.dict(), _id=str(results.inserted_id))


@EventRouter.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: str = eventIDType,
                    current_user: DBUser = Depends(get_current_active_user)):
    results = find_one_or_fail('events', user_and_event_filter(current_user.id, event_id))
    return results


@EventRouter.post("/events/{event_id}/set", response_model=EventResponse)
async def set_event_attributes(event_data: NewEvent, event_id: str = eventIDType,
                               current_user: DBUser = Depends(get_current_active_user)):
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id), {"$set": event_data.dict()})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


@EventRouter.post("/events/{event_id}/set/name", response_model=EventResponse, tags=["modify attributes"])
async def set_event_name(event_id: str, name: str = Body(..., min_length=1, max_length=64),
                         current_user: DBUser = Depends(get_current_active_user)):
    """Allows the name of an event to be set."""
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id), {"$set": {"name": name}})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


@EventRouter.post("/events/{event_id}/set/description", response_model=EventResponse, tags=["modify attributes"])
async def set_event_description(event_id: str, description: str = Body(..., max_length=256),
                                current_user: DBUser = Depends(get_current_active_user)):
    """Allows the description of an event to be set."""
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id),
                       {"$set": {"description": description}})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


@EventRouter.post("/events/{event_id}/set/tags", response_model=EventResponse, tags=["modify attributes", "tags"])
async def set_event_tags(event_id: str, tags: List[Tag] = Body(..., max_items=10),
                         current_user: DBUser = Depends(get_current_active_user)):
    """Allows the tags of an event to be set. Overwrites tags not in body of request."""
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id),
                       {"$set": {"tags": [tag.dict() for tag in tags]}})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


def wrap_in_model(model, model_to_wrap):
    try:
        return model(**model_to_wrap.dict(by_alias=True))
    except ValidationError:
        raise HTTPException(status_code=422, detail="Validation Error")


@EventRouter.post("/events/{event_id}/tags", response_model=EventResponse, tags=["modify attributes", "tags"])
async def add_tag_to_event(event_id: str, tag: Tag,
                           current_user: DBUser = Depends(get_current_active_user)):
    """Allows a tag to be added to an event"""
    event = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    event.tags.append(tag)
    results = wrap_in_model(EventInDB, event)
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id),
                       {"$addToSet": {"tags": tag.dict()}})
    return results


@EventRouter.delete("/events/{event_id}/tags", response_model=EventResponse, tags=["modify attributes", "tags"])
async def delete_tag_from_event(event_id: str, tag: Tag,
                                current_user: DBUser = Depends(get_current_active_user)):
    """Allows a tag to be removed to an event"""
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id),
                       {"$pull": {"tags": tag.dict()}})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


@EventRouter.get("/events/{event_id}/tags", response_model=Tags, tags=["modify attributes", "tags"])
async def get_all_tags_from_event(event_id: str,
                                  current_user: DBUser = Depends(get_current_active_user)):
    """Returns all tags belonging to an event"""
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return Tags(tags=results.tags)


@EventRouter.post("/events/{event_id}/set/presentation", response_model=EventResponse, tags=["modify attributes"])
async def set_event_color(event_id: str, presentation: EventColor,
                          current_user: DBUser = Depends(get_current_active_user)):
    """Allows the presentation info of an event to be set."""
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id),
                       {"$set": {"presentation": presentation.dict()}})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


@EventRouter.post("/events/{event_id}/set/stage", response_model=EventResponse)
async def set_event_stage(event_id: str, stage: Stage, current_user: DBUser = Depends(get_current_active_user)):
    """Allows the stage of an event to be set."""
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id), {"$set": {"stage": stage}})
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    return results


@EventRouter.delete("/events/{event_id}", response_model=EventResponse)
async def delete_event(event_id: str = eventIDType,
                       current_user: DBUser = Depends(get_current_active_user)):
    """Deletes an event from storage."""
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    delete_one_or_fail('events', user_and_event_filter(current_user.id, event_id))
    return results
