import random
import requests
import os
from dotenv import load_dotenv
import json
load_dotenv()

SINCH_URL = os.environ.get('SINCH_URL')
SINCH_TOKEN = os.environ.get('SINCH_TOKEN')
SINCH_SENDER_MOBILE = os.environ.get('SINCH_SENDER_MOBILE')

def generate_otp(length=4):
    """Generate a random OTP of specified length"""
    digits = "0123456789"
    otp = ""
    for i in range(length):
        otp += random.choice(digits)
    return otp

async def send_otp_mobile(otp,to_mobile):
    # Define the headers
    headers = {
        "Authorization": f"Bearer {SINCH_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "from": f"{SINCH_SENDER_MOBILE}",
        "to": [to_mobile],
        "body": f"Your OTP : {otp}",
    }
    payload_json = json.dumps(payload)
    response = requests.post(SINCH_URL, headers=headers, data=payload_json)
    return response.json()