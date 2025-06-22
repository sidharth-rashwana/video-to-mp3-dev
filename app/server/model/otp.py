from pydantic import BaseModel
from fastapi import Body
from typing import Union,Optional,Any
from uuid import uuid1
from pydantic import EmailStr

class otp(BaseModel):
    email : EmailStr