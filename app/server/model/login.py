from pydantic import BaseModel,validator,Field,conint
from fastapi import Body
from typing import Union,Optional,Any
from uuid import uuid1
from pydantic import EmailStr
import re

class SignUpUser(BaseModel):
    email : EmailStr
    fullName: str
    mobile : str
    role: str="USER"

class SignUpAdmin(BaseModel):
    email : EmailStr
    fullName: str
    mobile : str
    role: str="ADMIN"

class otp(BaseModel):
    email : EmailStr

class OTPGenerate(BaseModel):
    email : EmailStr