from typing import Any
from fastapi import (
        APIRouter, 
        Body,
        Depends,
        status,
        HTTPException)
from fastapi.responses import JSONResponse
from starlette.requests import Request
from fastapi.security import  OAuth2PasswordRequestForm
from app.server.model.login import SignUpUser, SignUpAdmin,  OTPGenerate
from typing import Annotated
from app.server.service import authenticate
from app.server.model.token import Token 
from app.server.utils.token import get_current_active_user
from app.server.model.token  import User 
from fastapi import Request

router = APIRouter()

######################################### SIGNUP #############################################

@router.post('/create/user/account', summary='To allow user to create a user account')
async def user_sign_up(request: Request,data: SignUpUser=Body(...)) -> dict[str, Any]:
    """signup a user account
    
    Returns:
        dict[str, Any]: response
    """
    created_account = await authenticate.create_user_account(data,request)
    return JSONResponse({'status': status.HTTP_201_CREATED, 'response': created_account})

@router.post('/create/admin/account', summary='To create admin account')
async def admin_sign_up(request: Request,data: SignUpAdmin=Body(...)) -> dict[str, Any]:
    """To create an admin account for the first time from BE , then disable this API
    
    Returns:
        dict[str, Any]: response
    """
    created_account = await authenticate.create_admin_account(request,data)
    return JSONResponse({'status': status.HTTP_201_CREATED, 'response': created_account})


@router.post('/create/admin/invite', summary='To allow admin only to invite an admin')
async def admin_sign_up(request: Request,current_user: Annotated[User, Depends(get_current_active_user)],
                        data: SignUpAdmin=Body(...)) -> dict[str, Any]:
    """signup an admin account while being a admin 

    only admin can create an admin account
    
    Returns:
        dict[str, Any]: response
    """
    if current_user.role not in ['ADMIN']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='You are not authorize to access this API.',
                                    headers={"WWW-Authenticate": "Bearer"})
    created_account = await authenticate.create_admin_account(request,data,current_user)
    return JSONResponse({'status': status.HTTP_201_CREATED, 'response': created_account})

########################################################## REGENERATE OTP ######################################

@router.put('/otp/generate', summary='To allow user to regenerate otp.')
async def generate_otp_login(request: Request,data: OTPGenerate=Body(...)) -> dict[str, Any]:
    """to reset password
    
    Returns:
        dict[str, Any]: response
    """
    generate_otp = await authenticate.generate_otp_login(data,request)
    return JSONResponse({'status': status.HTTP_200_OK, 'response': generate_otp})

########################################################## SIGN-IN ######################################

@router.post('/login', summary='To generate token for login',response_model=Token)
async def token(  request: Request,form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    """Login to Account

    Returns:
        dict[str, Any]: response
    """
    login_data = await authenticate.token(form_data,request)
    return login_data

########################################################## USER DETAILS #################################

@router.get('/user/details', summary='To get already logged in user details')
async def user_details(request: Request,current_user: Annotated[User, Depends(get_current_active_user)]) -> dict[str, Any]:
    """To get user details for population during login
    
    Returns:
        dict[str, Any]: response
    """
    if current_user.role not in ['USER','ADMIN']:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail='You are not authorize to access this API.',
                                    headers={"WWW-Authenticate": "Bearer"})
    data=await authenticate.user_details(current_user,request)
    return JSONResponse({'status': status.HTTP_200_OK, 'response': {'data': data}})