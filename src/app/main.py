from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field, EmailStr

from .dependencies import get_current_active_user, SECRET_KEY, ALGORITHM, get_user
from .DB.DB import get_collection
from .Models.User import User, DBUser, NewDBUser
from .Routes import Constraint, Event

# to get a string like this run:
# openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES = 30


class Token(BaseModel):
    """Response model for token endpoint"""
    access_token: str
    token_type: str


password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# other_context = CryptContext(schemes=[])

app = FastAPI()
app.include_router(Constraint.ConstraintRouter)
app.include_router(Event.EventRouter)


def verify_password(plain_password, hashed_password):
    return password_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return password_context.hash(password)


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
