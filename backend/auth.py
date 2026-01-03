from fastapi import HTTPException, Depends, Header
from typing import Optional
import jwt
import os
import random
import logging
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

otp_storage = {}

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(email: str, otp: str):
    message = f"""
{'='*60}
🔐 MOCK EMAIL SERVICE - OTP CODE FOR TESTING
{'='*60}
To: {email}
Subject: Your StickerSwap OTP Code
{'='*60}
YOUR OTP CODE: {otp}
{'='*60}
This code expires in 10 minutes.
Use this code to login to StickerSwap.
{'='*60}
"""
    logger.info(message)
    print(message)  # Also print to stdout for visibility

def store_otp(email: str, otp: str):
    otp_storage[email] = {
        'otp': otp,
        'expires_at': datetime.now(timezone.utc) + timedelta(minutes=10)
    }

def verify_otp(email: str, otp: str) -> bool:
    if email not in otp_storage:
        return False
    
    stored = otp_storage[email]
    if datetime.now(timezone.utc) > stored['expires_at']:
        del otp_storage[email]
        return False
    
    if stored['otp'] == otp:
        del otp_storage[email]
        return True
    
    return False

def create_token(user_id: str) -> str:
    payload = {
        'user_id': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token expired')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token')

async def get_current_user(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail='Authorization header missing')
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != 'bearer':
            raise HTTPException(status_code=401, detail='Invalid authentication scheme')
    except ValueError:
        raise HTTPException(status_code=401, detail='Invalid authorization header format')
    
    payload = decode_token(token)
    return payload['user_id']
