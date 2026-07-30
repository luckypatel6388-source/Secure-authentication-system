import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.logger import setup_logging, get_module_logger
from app.database import init_db, close_db
from app.db.session import get_db

from app.db import schemas
from app.db import models
from app.crud import get_user_by_email,create_user
from fastapi.security import OAuth2PasswordRequestForm
from app.core.authentication import verify_password,create_access_token,get_current_user

#from app.redis_client import get_redis_client, check_redis_connection

# Initialize logging configuration before app boot
setup_logging()
logger = get_module_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application startup and shutdown lifecycle events.
    Guarantees clean connection setup and teardown for DB & Redis.
    """
    logger.info(f"Starting {settings.APP_NAME}...")
    
    # 1. Startup: Initialize Database Tables
    try:
        await init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.critical(f"Failed to initialize database: {str(e)}")

    # 2. Startup: Test Redis Connectivity
    """redis_healthy = await check_redis_connection()
    if redis_healthy:
        logger.info("Connected to Redis successfully.")
    else:
        logger.warning("Redis connection check failed on startup.")"""

    yield  # Application running phase

    # 3. Shutdown: Gracefully close connection pools
    logger.info("Shutting down application...")
    await close_db()
    logger.info("Database connection pool closed successfully.")


# Initialize FastAPI Application
app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS Configuration (Allows frontend web apps or cross-origin requests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust allowed domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- SYSTEM ROUTES ---

@app.get("/", tags=["System"])
async def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "status": "online",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["System"])
async def health_check(
    db: AsyncSession = Depends(get_db),
    #redis = Depends(get_redis_client)
):
    """
    Production Health Check Endpoint.
    Tests active connections to both MySQL database and Redis broker.
    """
    db_status = "unhealthy"
    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        logger.error(f"Health check MySQL error: {str(e)}")

    #redis_status = "unhealthy"
    """try:
        await redis.ping()
        redis_status = "healthy"
    except Exception as e:
        logger.error(f"Health check Redis error: {str(e)}")"""

    is_system_healthy = (db_status == "healthy") #and (redis_status == "healthy")
    
    response_payload = {
        "app_name": settings.APP_NAME,
        "status": "ok" if is_system_healthy else "degraded",
        "services": {
            "database_mysql": db_status,
            #"cache_redis": redis_status
        }
    }

    if not is_system_healthy:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=response_payload
        )

    return response_payload

@app.post("/register",response_model=schemas.UserCreate)
async def user_register(user:schemas.UserCreate,db:AsyncSession=Depends(get_db)): #type:ignore
    existing_user= await get_user_by_email(db=db,email=user.email)
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered"
        )
    
    new_user= await create_user(db=db, user=user)
    return new_user

@app.post("/login",tags=["Auth"])
async def user_login(form_data:OAuth2PasswordRequestForm=Depends(),
                     db:AsyncSession=Depends(get_db)):
    user = await get_user_by_email(db=db,email=form_data.username)
    if not user or not verify_password(form_data.password,user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token= create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
    
@app.get("/login/userprofile",response_model=schemas.UserResponse)
async def user_profile(current_user=Depends(get_current_user)):
    
    return current_user
