from datetime import datetime, timedelta
from string import hexdigits
from typing import Optional, List

import bson
from bson import ObjectId
from fastapi import Depends, FastAPI, HTTPException, status, Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr
from pymongo.collection import Collection

from DB import get_client, get_collection
from app.Models.Event import BaseEvent, EventInDB, Stage, EventResponse, NewEventInDB
from app.Models.Constraint import EventStageConstraint, EventColorConstraint
from app.Models.User import User, DBUser, NewDBUser

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "b1fd8ba612900db8ff9f007e94ef8bdb84436d8f14db6274a29e4fb3925e63de"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    """Response model for token endpoint"""
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# other_context = CryptContext(schemes=[])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_context.hash(password)


def get_user(username: str) -> DBUser:
    """Get user from database."""
    client = get_client()
    database = client.get_database('reminder')
    users: Collection = database.get_collection('users')
    user_dict = users.find_one({"username": f"{username}"})
    if user_dict is not None:
        return DBUser(**user_dict)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


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


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Token endpoint"""
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=User)
async def read_users_me(current_user: DBUser = Depends(get_current_active_user)):
    return current_user


@app.get("/events/", response_model=List[EventResponse])
async def get_all_events(current_user: DBUser = Depends(get_current_active_user)):
    """Returns list of all events"""
    events_collection = get_collection('events')
    events_cursor = events_collection.find({'owner_id': current_user.id})
    return [event for event in events_cursor]


@app.post("/events/", response_model=EventResponse)
async def add_event(event_data: BaseEvent, current_user: DBUser = Depends(get_current_active_user)):
    new_event = NewEventInDB(**event_data.dict(), owner_id=current_user.id, stage=Stage.started)
    events_collection = get_collection('events')
    results = events_collection.insert_one(new_event.dict())
    return EventInDB(**new_event.dict(), _id=str(results.inserted_id))


def x_or_fail(x, collection_name, filter_factory: Optional[dict] = None, update_factory: Optional[dict] = None):
    collection_handle = get_collection(collection_name)
    possible = [filter_factory, update_factory]
    try:
        results: dict = collection_handle.__getattribute__(x)(*[param for param in possible if param is not None])
    except bson.errors.InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")
    if not results:
        raise HTTPException(status_code=404, detail="Item not found")
    return results


def find_one_or_fail(collection_name, filter_factory: dict):
    return x_or_fail('find_one', collection_name, filter_factory)


def delete_one_or_fail(collection_name, filter_factory: dict):
    return x_or_fail('delete_one', collection_name, filter_factory)


def update_one_or_fail(collection_name, filter_factory: dict,
                       update_factory: dict):
    return x_or_fail('update_one', collection_name, filter_factory, update_factory)


@app.get("/events/{event_id}", response_model=EventResponse)
async def get_event(event_id: str = Path(..., regex=f'[{hexdigits}]+'),
                    current_user: DBUser = Depends(get_current_active_user)):
    results = find_one_or_fail('events', user_and_event_filter(current_user.id, event_id))
    return results


@app.delete("/events/{event_id}", response_model=EventResponse)
async def delete_event(event_id: str = Path(..., regex=f'[{hexdigits}]+'),
                       current_user: DBUser = Depends(get_current_active_user)):
    """Deletes an event from storage."""
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    delete_one_or_fail('events', user_and_event_filter(current_user.id, event_id))
    return results


def user_and_event_filter(user_id, event_id):
    """Filters: user_id owns event at event_id
        event_id must be a valid ObjectId or 404"""
    try:
        event_id = ObjectId(event_id)
    except bson.errors.InvalidId:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"owner_id": user_id, "_id": ObjectId(event_id)}


@app.post("/events/{event_id}/stage", response_model=EventResponse)
async def set_event_stage(event_id: str, stage: Stage, current_user: DBUser = Depends(get_current_active_user)):
    """Marks an event as complete. Does not actually remove from storage."""
    results = EventInDB(**find_one_or_fail('events', user_and_event_filter(current_user.id, event_id)))
    update_one_or_fail('events', user_and_event_filter(current_user.id, event_id), {"$set": {"stage": stage}})
    return results


allowed_constraints = {"EventStageConstraint": EventStageConstraint,
                       "EventColorConstraint": EventColorConstraint}


# TODO event_search, constraint_search, tag_search
# TODO event time frames


# AUTH
class SignUp(BaseModel):
    username: str = Field(..., min_length=1, max_length=64)
    email: EmailStr


class SignUpRequest(SignUp):
    password: str = Field(..., min_length=8, max_length=64)

    def get_hashed_user_credentials(self):
        """Hash the password and return SignUpRequest"""
        credentials = self.dict(exclude={'password'})
        credentials.update({'hashed_password': get_password_hash(self.password)})
        return credentials


@app.post("/auth/signup", response_model=SignUp)
async def sign_up(requested_credentials: SignUpRequest):
    # Todo Verify email active by verification
    new_user = NewDBUser(**requested_credentials.get_hashed_user_credentials())
    users = get_collection("users")
    users.insert_one(new_user.dict())
    return requested_credentials


if __name__ == "__main__":
    print("You must run with a ASGI server!")
