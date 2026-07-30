from sqlalchemy import select
from app.db import models, schemas
from app.core.authentication import get_password_hash
from sqlalchemy.ext.asyncio import AsyncSession

async def get_user_by_email(db: AsyncSession, email: str):
    
    statement = select(models.User).where(models.User.email == email)
    result = await db.execute(statement)
    return result.scalars().first()

async def create_user(db: AsyncSession, user: schemas.UserCreate):
    hashed_pwd = get_password_hash(user.password)
    
    # Instantiate database model
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_pwd,
        full_name=user.full_name,
    )
    
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user