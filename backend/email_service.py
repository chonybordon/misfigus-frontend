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
    from resend import Emails
    RESEND_AVAILABLE = True
    logger.info("Resend package imported successfully")
except ImportError:
    RESEND_AVAILABLE = False
    logger.warning("Resend package not installed. Email will be logged only.")

def check_resend_config():
    """Log Resend configuration status on startup (called from server.py)."""
    api_key = os.environ.get('RESEND_API_KEY', '').strip()
    has_key = bool(api_key)
    logger.info("="*50)
    logger.info("EMAIL SERVICE CONFIGURATION")
    logger.info(f"  RESEND_API_KEY present: {has_key}")
    logger.info(f"  Resend package available: {RESEND_AVAILABLE}")
    if has_key and RESEND_AVAILABLE:
        logger.info("  Status: PRODUCTION MODE - Emails will be sent via Resend")
    else:
        logger.info("  Status: FALLBACK MODE - OTP/codes logged to console only")
    logger.info("="*50)
    return has_key and RESEND_AVAILABLE

def get_resend_configured() -> bool:
    """Check if Resend is properly configured."""
    api_key = os.environ.get('RESEND_API_KEY', '').strip()
    return bool(api_key) and RESEND_AVAILABLE

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
    logger.info(f"[OTP] Attempting to send OTP email to: {email}")
    
    if get_resend_configured():
        logger.info(f"[OTP] Resend configured, attempting to send...")
        try:
            # Set API key
            resend.api_key = os.environ.get('RESEND_API_KEY', '').strip()
            
            # Use Resend's approved test sender for development
            # For production, use a verified domain
            params: resend.Emails.SendParams = {
                "from": "MisFigus <onboarding@resend.dev>",
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
            
            logger.info(f"[OTP] Calling Resend API...")
            emails = Emails()
            response = emails.send(params)
            logger.info(f"[OTP] Resend API response: {response}")
            logger.info(f"[OTP] Email successfully sent to {email}")
            return True
            
        except Exception as e:
            logger.error(f"[OTP] Resend API error: {type(e).__name__}: {e}")
            # Log more details if available
            if hasattr(e, 'message'):
                logger.error(f"[OTP] Error message: {getattr(e, 'message', 'N/A')}")
            if hasattr(e, 'status_code'):
                logger.error(f"[OTP] Status code: {getattr(e, 'status_code', 'N/A')}")
            logger.warning(f"[OTP] Falling back to console logging due to error")
    else:
        logger.info(f"[OTP] Resend not configured (API key missing or package unavailable)")
    
    # Fallback: Log to console only (NEVER return to frontend)
    logger.warning("="*50)
    logger.warning(f"[OTP] EMAIL FALLBACK (Resend not configured or failed)")
    logger.warning(f"[OTP] To: {email}")
    logger.warning(f"[OTP] OTP: {otp}")
    logger.warning("="*50)
    return True

def send_invite_email(email: str, invite_code: str, group_name: str, inviter_name: str) -> bool:
    """
    Send invite code via email using Resend.
    Falls back to console logging if Resend is not configured.
    
    IMPORTANT: Invite code is NEVER returned to the caller or shown in UI.
    """
    logger.info(f"[INVITE] Attempting to send invite email to: {email}")
    
    if get_resend_configured():
        logger.info(f"[INVITE] Resend configured, attempting to send...")
        try:
            # Set API key
            resend.api_key = os.environ.get('RESEND_API_KEY', '').strip()
            
            # Use Resend's approved test sender for development
            params: resend.Emails.SendParams = {
                "from": "MisFigus <onboarding@resend.dev>",
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
            
            logger.info(f"[INVITE] Calling Resend API...")
            emails = Emails()
            response = emails.send(params)
            logger.info(f"[INVITE] Resend API response: {response}")
            logger.info(f"[INVITE] Email successfully sent to {email} for group {group_name}")
            return True
            
        except Exception as e:
            logger.error(f"[INVITE] Resend API error: {type(e).__name__}: {e}")
            if hasattr(e, 'message'):
                logger.error(f"[INVITE] Error message: {getattr(e, 'message', 'N/A')}")
            if hasattr(e, 'status_code'):
                logger.error(f"[INVITE] Status code: {getattr(e, 'status_code', 'N/A')}")
            logger.warning(f"[INVITE] Falling back to console logging due to error")
    else:
        logger.info(f"[INVITE] Resend not configured (API key missing or package unavailable)")
    
    # Fallback: Log to console only (NEVER return to frontend)
    logger.warning("="*50)
    logger.warning(f"[INVITE] EMAIL FALLBACK (Resend not configured or failed)")
    logger.warning(f"[INVITE] To: {email}")
    logger.warning(f"[INVITE] Invite Code: {invite_code}")
    logger.warning(f"[INVITE] Group: {group_name}")
    logger.warning(f"[INVITE] Invited by: {inviter_name}")
    logger.warning("="*50)
    return True
