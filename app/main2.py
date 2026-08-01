
from fastapi import FastAPI,Request,HTTPException
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings

app=FastAPI()

app.add_middleware(SessionMiddleware,secret_key=settings.SECRET_KEY)

oauth=OAuth()
oauth.register(
    name="google",
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

@app.get("/auth/login")
async def login(request: Request):
    redirect_uri = request.url_for("auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)
#first line is the return address to web,second line sends user to google sign page 

@app.get("/auth/google/callback")
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