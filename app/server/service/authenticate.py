from typing import Any
from app.server.database.collections import Collections
import app.server.database.core_data as database_query
from app.server.messages import authenticate_msg
from app.server.utils.date_utils import get_current_timestamp,calculate_time_difference_in_minutes
from app.server.utils.email import send_email
from app.server.utils.otp import generate_otp,send_otp_mobile
from app.server.utils import token as token_utils
from app.server.utils.password import get_password_hash
from app.server.logger.custom_logger import logger
from app.server.model.token import Token 
from app.server.utils.token import authenticate_user
from app.server.utils import file_operations
#to find parent 'app' folder Path
from email.mime.text import MIMEText
import os
from fastapi import HTTPException,status
from app.server.utils import networking as networking_util
from jinja2 import Template

SECRET_KEY = os.environ.get('SECRET_KEY', os.getenv("JWT_SECRET_KEY"))
ALGORITHM = os.environ.get('JWT_ALGORITHM', os.getenv("JWT_ALGORITHM"))
RESET_PASSWORD_LINK = os.environ.get('RESET_PASSWORD_LINK', os.getenv("RESET_PASSWORD_LINK"))
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRE_MINUTES', os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES")))
RESET_TOKEN_EXPIRE_MINUTES = int(os.environ.get('JWT_RESET_TOKEN_EXPIRE_MINUTES', os.getenv("JWT_RESET_TOKEN_EXPIRE_MINUTES")))
OTP_VALIDITY_IN_MINUTES = int(os.environ.get('OTP_VALIDITY_IN_MINUTES', os.getenv("OTP_VALIDITY_IN_MINUTES")))
OTP_VALIDITY_IN_MINUTES_SIGNUP = int(os.environ.get('OTP_VALIDITY_IN_MINUTES_SIGNUP', os.getenv("OTP_VALIDITY_IN_MINUTES_SIGNUP")))

async def create_user_account(data,request):
    source_ip = await networking_util.get_source_ip(request)
    route = request.url.path
    if data.role != "USER":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=authenticate_msg.INVALID_REQUEST)
    existing_username = await database_query.read_one(Collections.ACCOUNT, {'mobile':data.mobile,
                                                                            'isVerified':True})
    if existing_username['status'] != status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=authenticate_msg.MOBILE_IN_USE_ALREADY)
    existing_email = await database_query.read_one(Collections.ACCOUNT, {'email':data.email,
                                                                            'isVerified':True})
    if existing_email['status'] != status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=authenticate_msg.USER_ALREADY_HAS_ACCOUNT)
    logger.debug('Generating OTP')
    otp = generate_otp()
    timestamp = get_current_timestamp()
    logger.debug('Generating OTP complete')
    logger.debug('Checking if account already exist with given email')
    email_exist = await database_query.read_one(Collections.ACCOUNT, {'email':data.email})
    mobile_exist = await database_query.read_one(Collections.ACCOUNT, {'mobile':data.mobile})
    logger.debug('Checking if account already exist is complete')
    data = dict(data)
    hashed_password = {'hashedPassword':get_password_hash(otp),
                       'otpTimestamp':timestamp}
    data['isVerified']=False
    logger.debug(email_exist)
    #account is not created before
    logger.debug('Creating a new account')
    if email_exist['status'] == status.HTTP_200_OK and  mobile_exist['status'] != status.HTTP_200_OK: 
        deleted_user = await database_query.delete_one(Collections.ACCOUNT,{'email':data['email']})
        deleted_password = await database_query.delete_one(Collections.PASSWORD,{'userId':email_exist['_id']})
    if  email_exist['status'] != status.HTTP_200_OK and mobile_exist['status'] == status.HTTP_200_OK:
        deleted_user = await database_query.delete_one(Collections.ACCOUNT,{'mobile':data['mobile']})
        deleted_password = await database_query.delete_one(Collections.PASSWORD,{'userId':mobile_exist['_id']})
    if  email_exist['status'] == status.HTTP_200_OK and mobile_exist['status'] == status.HTTP_200_OK:
        deleted_user = await database_query.delete_one(Collections.ACCOUNT,{'mobile':data['mobile']})
        deleted_password = await database_query.delete_one(Collections.PASSWORD,{'userId':mobile_exist['_id']})
    created_account = await database_query.create_one(Collections.ACCOUNT, data)
    hashed_password.update({'userId':created_account['_id']})
    insert_password = await database_query.create_one(Collections.PASSWORD, hashed_password)
    logger.debug('Creating a new account is complete')
    html_file="app/server/templates/account/account_create.html"
    html_content = await file_operations.read_file(html_file)
    template = Template(html_content.decode())
    render_html = template.render(mobile=data['mobile'],otp=otp,validity=OTP_VALIDITY_IN_MINUTES_SIGNUP)
    html_render = MIMEText(render_html, 'html')
    response = send_email(data['email'],html_render,subject=f'''{authenticate_msg.CREATE_ACCOUNT}  
                        {data['mobile']}! Complete Your Account Setup''')
    mobile_delivered = await send_otp_mobile(otp,data['mobile'])
    await database_query.create_one(Collections.NETWORK,{'sourceIP':source_ip , 'route':route, 'userId':created_account['_id']})
    created_account.pop('_id',None)    
    return created_account

async def create_admin_account(request,data,current_user=None):
    source_ip = await networking_util.get_source_ip(request)
    route = request.url.path
    if data.role != "ADMIN":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail=authenticate_msg.INVALID_REQUEST)
    existing_username = await database_query.read_one(Collections.ACCOUNT, {'mobile':data.mobile,
                                                                            'isVerified':True})
    if existing_username['status'] != status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=authenticate_msg.MOBILE_IN_USE_ALREADY)
    existing_email = await database_query.read_one(Collections.ACCOUNT, {'email':data.email,
                                                                            'isVerified':True})
    if existing_email['status'] != status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail=authenticate_msg.USER_ALREADY_HAS_ACCOUNT)
    logger.debug('Generating OTP')
    otp = generate_otp()
    timestamp = get_current_timestamp()
    logger.debug('Generating OTP complete')
    logger.debug('Checking if account already exist with given email')
    email_exist = await database_query.read_one(Collections.ACCOUNT, {'email':data.email})
    mobile_exist = await database_query.read_one(Collections.ACCOUNT, {'mobile':data.mobile})
    logger.debug('Checking if account already exist is complete')
    data = dict(data)
    hashed_password = {'hashedPassword':get_password_hash(otp),
                       'otpTimestamp':timestamp}
    data['isVerified']=False
    if current_user:
        data['createdBy'] = current_user.user_id
    logger.debug(email_exist)
    #account is not created before
    logger.debug('Creating a new account')
    if email_exist['status'] == status.HTTP_200_OK and  mobile_exist['status'] != status.HTTP_200_OK: 
        deleted_user = await database_query.delete_one(Collections.ACCOUNT,{'email':data['email']})
        deleted_password = await database_query.delete_one(Collections.PASSWORD,{'userId':email_exist['_id']})
    if  email_exist['status'] != status.HTTP_200_OK and mobile_exist['status'] == status.HTTP_200_OK:
        deleted_user = await database_query.delete_one(Collections.ACCOUNT,{'mobile':data['mobile']})
        deleted_password = await database_query.delete_one(Collections.PASSWORD,{'userId':mobile_exist['_id']})
    if  email_exist['status'] == status.HTTP_200_OK and mobile_exist['status'] == status.HTTP_200_OK:
        deleted_user = await database_query.delete_one(Collections.ACCOUNT,{'mobile':data['mobile']})
        deleted_password = await database_query.delete_one(Collections.PASSWORD,{'userId':mobile_exist['_id']})
    created_account = await database_query.create_one(Collections.ACCOUNT, data)
    hashed_password.update({'userId':created_account['_id']})
    insert_password = await database_query.create_one(Collections.PASSWORD, hashed_password)
    logger.debug('Creating a new account is complete')
    html_file="app/server/templates/account/account_create.html"
    html_content = await file_operations.read_file(html_file)
    template = Template(html_content.decode())
    render_html = template.render(mobile=data['mobile'],otp=otp,validity=OTP_VALIDITY_IN_MINUTES_SIGNUP)
    html_render = MIMEText(render_html, 'html')
    response = send_email(data['email'],html_render,subject=f'''{authenticate_msg.CREATE_ACCOUNT}  
                        {data['mobile']}! Complete Your Account Setup''')
    mobile_delivered = await send_otp_mobile(otp,data['mobile'])
    await database_query.create_one(Collections.NETWORK,{'sourceIP':source_ip , 'route':route, 'userId':created_account['_id']})
    created_account.pop('_id',None)    
    return created_account   

async def token(form_data,request)->Token:
    source_ip = await networking_util.get_source_ip(request)
    route = request.url.path
    logger.debug('Getting details about entered email.')
    user=await authenticate_user(form_data.username, form_data.password)
    existing_account = await database_query.read_one(Collections.ACCOUNT, {'mobile':user.mobile,
                                                                                'role':user.role
                                                                                })
    account_status = await database_query.read_one(Collections.PASSWORD, {'userId':existing_account['_id']
                                                                            })
    logger.debug('Checking if account is verified')
    if not user.isVerified :
        timestamp = get_current_timestamp()
        time_difference = calculate_time_difference_in_minutes(account_status['otpTimestamp'],timestamp)
        if time_difference > OTP_VALIDITY_IN_MINUTES_SIGNUP:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=authenticate_msg.OTP_EXPIRED)                
        update_account = await database_query.update_one(Collections.ACCOUNT,{'email':user.email},{"$set":
                                                    {'isVerified':True,
                                                    'createdAt':get_current_timestamp(),
                                                    'isDeactivated':False,
                                                    'isDeleted':False,
                                                    'isSuspended':False
                                                    }})
        updated_password = await database_query.update_one(Collections.PASSWORD, 
                                                    filter_by={'userId':existing_account['_id']},
                                                    update_by={"$set":{'otpTimestamp':timestamp}})
        logger.debug('Verification of the account is complete')
        html_file="app/server/templates/account/account_verified.html"
        html_content = await file_operations.read_file(html_file)
        template = Template(html_content.decode())
        render_html = template.render(mobile=user.mobile)
        html_render = MIMEText(render_html, 'html')
        response = send_email(user.email,html_render,subject=f"{authenticate_msg.VERIFY_ACCOUNT} {user.mobile}!")
        logger.debug('Verification of the account is complete')
    else:
            """
            normal login after creation , account should be verified
        """
            if not user.isVerified :
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN , detail=authenticate_msg.USER_ACCOUNT_NOT_VERIFIED)
            if user.isDeactivated :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail=authenticate_msg.USER_NOT_FOUND)
            if user.isDeleted :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail=authenticate_msg.USER_NOT_FOUND)
            timestamp = get_current_timestamp()
            if 'otpTimestamp' not in account_status:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail='OTP is not generated')
            time_difference = calculate_time_difference_in_minutes(account_status['otpTimestamp'],timestamp)
            if time_difference > OTP_VALIDITY_IN_MINUTES:
                logger.debug('generating new otp')
                otp_resend = await generate_otp_login({'email':user.email},request)
                logger.debug(otp_resend)
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=authenticate_msg.OTP_EXPIRED)
    await database_query.create_one(Collections.NETWORK,{'sourceIP':source_ip , 'route':route, 'userId':existing_account['_id']})    
    jwt_access_token = await token_utils.create_login_access_token(user)
    return jwt_access_token

async def generate_otp_login(data,request):
    source_ip = await networking_util.get_source_ip(request)
    route = request.url.path
    data=dict(data)
    existing_user = await database_query.read_one(Collections.ACCOUNT, {'email':data['email']})
    if existing_user['status'] == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail='User not found')
    otp = generate_otp()
    timestamp = get_current_timestamp()
    hashed_password  = get_password_hash(otp)
    logger.debug('Sending OTP onto email')
    html_file="app/server/templates/otp/otp_send.html"
    html_content = await file_operations.read_file(html_file)
    template = Template(html_content.decode())
    render_html = template.render(mobile=existing_user['mobile'],otp=otp,validity=OTP_VALIDITY_IN_MINUTES)
    html_render = MIMEText(render_html, 'html')
    response = send_email(existing_user['email'],html_render,subject=f"{authenticate_msg.OTP_SENT}")
    mobile_delivered = await send_otp_mobile(otp,existing_user['mobile'])
    logger.debug('Sending OTP onto email is complete')
    inserted_document = await database_query.update_one(Collections.PASSWORD, 
                                                       filter_by={'userId':existing_user['_id']},
                                                       update_by={"$set":{'hashedPassword':hashed_password,'otpTimestamp':timestamp}})
    await database_query.create_one(Collections.NETWORK,{'sourceIP':source_ip,'route':route,'userId':existing_user['_id']})
    return 'OTP is successfully sent on registered email and mobile.'

async def verify_account_otp(data):
    data = data if isinstance(data, dict) else data.dict()
    existing_user = await database_query.read_one(Collections.ACCOUNT, {'email':data['email']})
    if existing_user['status'] == status.HTTP_404_NOT_FOUND:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND , detail=authenticate_msg.USER_NOT_FOUND)
    otp = generate_otp()
    hashed_password  = get_password_hash(otp)
    logger.debug('Sending OTP onto email')
    html_file="app/server/templates/otp/otp_send.html"
    html_content = await file_operations.read_file(html_file)
    template = Template(html_content.decode())
    render_html = template.render(email=existing_user['mobile'],otp=otp,validity=OTP_VALIDITY_IN_MINUTES_SIGNUP)
    html_render = MIMEText(render_html, 'html')
    response = send_email(existing_user['email'],html_render,subject=f"{authenticate_msg.OTP_SENT}")
    mobile_delivered = await send_otp_mobile(otp,data['mobile'])
    logger.debug('Sending OTP onto email is complete')
    timestamp = get_current_timestamp()
    updated_password = await database_query.update_one(Collections.PASSWORD, 
                                                       filter_by={'userId':existing_user['_id']},
                                                       update_by={"$set":{'hashedPassword':hashed_password,
                                                                          'otpTimestamp':timestamp}})
    return authenticate_msg.OTP_SENT


async def user_details(current_user,request):
    source_ip = await networking_util.get_source_ip(request)
    route = request.url.path
    await database_query.create_one(Collections.NETWORK,{'sourceIP':source_ip,'route':route,'userId':current_user.user_id})
    data = {'fullName':current_user.fullName,'mobile':current_user.mobile,'role':current_user.role,'email':current_user.email}
    return data