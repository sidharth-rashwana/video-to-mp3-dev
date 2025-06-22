from datetime import datetime, timedelta
from typing import Annotated
from app.server.model.token import TokenData,User,UserInDB
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.server.database.collections import Collections
import app.server.database.core_data as database_query
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Union
import os
from dotenv import load_dotenv
load_dotenv()
# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.environ.get('SECRET_KEY', os.getenv("JWT_SECRET_KEY"))
ALGORITHM = os.environ.get('JWT_ALGORITHM', os.getenv("JWT_ALGORITHM"))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")))
RESET_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_RESET_TOKEN_EXPIRE_MINUTES', os.getenv("JWT_RESET_TOKEN_EXPIRE_MINUTES")))


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

app = FastAPI()

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


async def get_user( mobile: str):
    """
        fake_users_db = {
            "johndoe": {
                "mobile": "johndoe",
                "fullName": "John Doe",
                "email": "johndoe@example.com",
                "hashedPassword": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
            }
        }
    """
    user_data = await database_query.read_one(Collections.ACCOUNT, {'mobile':mobile})
    if user_data.get('status') == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect Credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) 
    password = await database_query.read_one(Collections.PASSWORD, {'userId':user_data['_id']})
    user_data.update({'hashedPassword':password.get('hashedPassword')})
    return UserInDB(**user_data)

async def authenticate_user( mobile: str, password: str):
    user = await get_user( mobile)
    if not verify_password(password, user.hashedPassword):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Incorrect Credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )   
    return user

async def create_login_access_token(user):
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
            data={"sub": user.mobile}, expires_delta=access_token_expires
        )
    return {"access_token": access_token, "token_type": "bearer"}

async def create_password_reset_access_token(user):
    access_token_expires = timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
            data={"sub": user.mobile}, expires_delta=access_token_expires
        )
    return {"access_token": access_token, "token_type": "bearer"}

async def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        mobile: str = payload.get("sub")
        if mobile is None:
            raise credentials_exception
        token_data = TokenData(mobile=mobile)
    except JWTError:
        raise credentials_exception
    user =await get_user(mobile=token_data.mobile)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)]
):
    if current_user.isDeactivated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is deactivated.")
    if not current_user.isVerified:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not verified")
    if current_user.isDeleted :
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail='Your account is already deleted.')
    return current_user

async def decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired")
    except (jwt.DecodeError, jwt.InvalidTokenError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

# async def current_user_details(token: str) -> bool:
#     try:
#         payload = await decode_jwt(token)
#         """
#                     {
#                 "_id": "64e88780604a264263175ac0",
#                 "email": "sidharthrashwana@yahoo.com",
#                 "mobile": "9741502471",
#                 "role": "USER",
#                 "isVerified": true,
#                 "createdAt": 1692960822241,
#                 "isDeactivated": false,
#                 "isDeleted": false,
#                 "isSuspended": false,
#                 "status": 200
#             }
#         """
#         if 'sub' in payload and 'exp' in payload:
#             user_data = await database_query.read_one(Collections.ACCOUNT, {'mobile':payload.get('sub')})
#             data = {'isVerified':user_data['isVerified'],
#                     'mobile':user_data['mobile'],
#                     'email':user_data['email'],
#                     'fullName':user_data['fullName']}
#             return data
#     except HTTPException:
#         return False