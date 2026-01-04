"""Email service using Resend with fallback to console logging."""
import os
import logging
import random
import hashlib
from typing import Optional

logger = logging.getLogger(__name__)

# Try to import resend
try:
    import resend
    RESEND_AVAILABLE = True
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend package not installed. Email will be logged only.")

def get_resend_client():
    """Get Resend client if API key is configured."""
    api_key = os.environ.get('RESEND_API_KEY', '').strip()
    if api_key and RESEND_AVAILABLE:
        resend.api_key = api_key
        return resend
    return None

def generate_otp_code() -> str:
    """Generate a 6-digit OTP code."""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def generate_invite_code() -> str:
    """Generate a 6-digit invite code."""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def hash_otp(otp: str) -> str:
    """Hash OTP for storage (never store plain OTP)."""
    return hashlib.sha256(otp.encode()).hexdigest()

def verify_otp_hash(otp: str, hashed: str) -> bool:
    """Verify OTP against stored hash."""
    return hash_otp(otp) == hashed

def send_otp_email(email: str, otp: str) -> bool:
    """
    Send OTP via email using Resend.
    Falls back to console logging if Resend is not configured.
    
    IMPORTANT: OTP is NEVER returned to the caller or shown in UI.
    """
    client = get_resend_client()
    
    if client:
        try:
            params = {
                "from": "MisFigus <noreply@misfigus.app>",
                "to": [email],
                "subject": "Tu código de verificación - MisFigus",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333;">Código de verificación</h1>
                    <p>Tu código para iniciar sesión en MisFigus es:</p>
                    <div style="background: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 20px 0;">
                        {otp}
                    </div>
                    <p style="color: #666;">Este código expira en 10 minutos.</p>
                    <p style="color: #999; font-size: 12px;">Si no solicitaste este código, puedes ignorar este mensaje.</p>
                </div>
                """
            }
            client.emails.send(params)
            logger.info(f"OTP email sent to {email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}")
            # Fall through to console logging
    
    # Fallback: Log to console only (NEVER return to frontend)
    logger.warning("="*50)
    logger.warning(f"EMAIL FALLBACK (Resend not configured)")
    logger.warning(f"To: {email}")
    logger.warning(f"OTP: {otp}")
    logger.warning("="*50)
    return True

def send_invite_email(email: str, invite_code: str, group_name: str, inviter_name: str) -> bool:
    """
    Send invite code via email using Resend.
    Falls back to console logging if Resend is not configured.
    
    IMPORTANT: Invite code is NEVER returned to the caller or shown in UI.
    """
    client = get_resend_client()
    
    if client:
        try:
            params = {
                "from": "MisFigus <noreply@misfigus.app>",
                "to": [email],
                "subject": f"{inviter_name} te invitó a {group_name} - MisFigus",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h1 style="color: #333;">¡Te invitaron a un grupo!</h1>
                    <p><strong>{inviter_name}</strong> te invitó a unirte al grupo <strong>{group_name}</strong> en MisFigus.</p>
                    <p>Usa este código para unirte:</p>
                    <div style="background: #f5f5f5; padding: 20px; text-align: center; font-size: 32px; font-weight: bold; letter-spacing: 8px; margin: 20px 0;">
                        {invite_code}
                    </div>
                    <p style="color: #666;">Este código expira en 1 hora y solo puede usarse una vez.</p>
                    <p style="color: #999; font-size: 12px;">Si no esperabas esta invitación, puedes ignorar este mensaje.</p>
                </div>
                """
            }
            client.emails.send(params)
            logger.info(f"Invite email sent to {email} for group {group_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to send invite email: {e}")
            # Fall through to console logging
    
    # Fallback: Log to console only (NEVER return to frontend)
    logger.warning("="*50)
    logger.warning(f"EMAIL FALLBACK (Resend not configured)")
    logger.warning(f"To: {email}")
    logger.warning(f"Invite Code: {invite_code}")
    logger.warning(f"Group: {group_name}")
    logger.warning(f"Invited by: {inviter_name}")
    logger.warning("="*50)
    return True
