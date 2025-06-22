from pydantic import BaseModel,Field
from typing import Union

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    mobile: Union[str, None] = None

class User(BaseModel):
    user_id: str = Field(..., alias='_id')
    mobile: str
    email: Union[str, None] = None
    role: str
    fullName: Union[str, None] = None
    isVerified: Union[bool, None] = None
    isDeactivated: Union[bool, None] = None
    isDeleted: Union[bool, None] = None
    isSuspended: Union[bool, None] = None

class UserInDB(User):
    hashedPassword: str
