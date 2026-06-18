from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
)

fm = FastMail(conf)

async def send_verification_email(email: str, token: str):
    try:
        link = f"{settings.FRONTEND_URL}/verify-email?token={token}"
        msg = MessageSchema(
            subject="Verify your email",
            recipients=[email],
            body=f"""
            <h2>Welcome!</h2>
            <p>Click below to verify. Expires in 24 hours.</p>
            <a href="{link}">Verify Email</a>
            <p>Or copy: {link}</p>
            """,
            subtype=MessageType.html,
        )
        await fm.send_message(msg)
    except Exception as e:
        print(f"[EMAIL ERROR] Could not send to {email}: {e}")
        # Don't raise — let registration succeed even if email fails
        
async def send_password_reset_email(email: str, token: str):
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    msg = MessageSchema(
        subject="Reset your password",
        recipients=[email],
        body=f"""
        <h2>Password Reset</h2>
        <p>This link expires in 1 hour. If you didn't request this, ignore this email.</p>
        <a href="{link}" style="background:#dc2626;color:#fff;padding:12px 24px;
           border-radius:6px;text-decoration:none;">Reset Password</a>
        """,
        subtype=MessageType.html,
    )
    await fm.send_message(msg)