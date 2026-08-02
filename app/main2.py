
from fastapi import FastAPI,Request,HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from app.logger import setup_logging,get_module_logger
from app.database import init_db,close_db


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


app.add_middleware(SessionMiddleware,secret_key=settings.SECRET_KEY)

oauth=OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


@app.get("/auth/login",tags=["Google authentication"])
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")

    # If deployed on Render (or behind proxy), force HTTPS scheme
    if "onrender.com" in str(request.base_url) or request.headers.get("x-forwarded-proto") == "https":
        redirect_uri = str(redirect_uri).replace("http://", "https://")
        
    return await oauth.google.authorize_redirect(request, redirect_uri)
#first line is the return address to web,second line sends user to google sign page 

@app.get("/auth/google/callback",tags=["Google authentication"])
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(status_code=400, detail="Google authentication failed")
    
    email = user_info["email"]
    name = user_info["name"]
    google_id = user_info["sub"]

    return {"status": "success", "email": email, "name": name, "google_id": google_id}
#oauth.google.authorize_access_token(request) Captures the authorization code returned by Google in the URL query string.
#then sends request to google so that it return acess token and id 
#user_info() Extracts and decodes user details from the ID Token returned by Google.