from authlib.integrations.starlette_client import OAuth
from fastapi import HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.db.models import User
from app.core.authentication import create_access_token  # Reuses standard JWT helper

# Initialize Authlib OAuth client
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


async def process_google_oauth_callback(request: Request, db: AsyncSession) -> dict:
    """
    Handles the Google OAuth 2.0 redirect callback.
    Retrieves user profile from Google, creates user if not exists, and returns JWT token.
    """
    try:
        token = await oauth.google.authorize_access_token(request) #sent to google
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth authorization failed: {str(e)}"
        )

    user_info = token.get("userinfo") #extract userifo from google id
    if not user_info or "email" not in user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to retrieve valid profile data from Google"
        )

    email = user_info["email"]
    full_name = user_info.get("name", "")

    # Query DB to check if user already exists
    query = select(User).where(User.email == email)
    result = await db.execute(query)
    user = result.scalars().first()

    # Automatically register new users authenticating via Google
    if not user:
        user = User(
            email=email,
            hashed_password="OAUTH_EXTERNAL_USER",  # Placeholder for OAuth accounts
            full_name=full_name,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # Issue a system JWT access token
    access_token = create_access_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    }