from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated
from api.core.auth import create_access_token, verify_password, get_password_hash, Token
from pydantic import BaseModel

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

# Mock DB for demonstration (in production, use SQLAlchemy Session)
fake_users_db = {
    "admin@lawfirm.com": {
        "username": "admin@lawfirm.com",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
    },
    "user@lawfirm.com": {
        "username": "user@lawfirm.com",
        "hashed_password": get_password_hash("user123"),
        "role": "user",
    }
}

class UserResponse(BaseModel):
    username: str
    role: str

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    # In a real app, decode JWT and fetch from DB
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"username": "user@lawfirm.com", "role": "user"}

async def get_current_admin(current_user: Annotated[dict, Depends(get_current_user)]):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return current_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: Annotated[dict, Depends(get_current_user)]):
    return current_user
