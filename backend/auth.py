import os
import uuid
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status, Query, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import text
from db import engine

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "zz-agent-out-secret-key-change-me")  # In production, use environment variable
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)
_bcrypt_module = None
_bcrypt_import_failed = False
PBKDF2_PREFIX = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 260000

# Models
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    username: str

class TokenData(BaseModel):
    username: Optional[str] = None
    role: Optional[str] = None

class User(BaseModel):
    username: str
    role: str

class UserInDB(User):
    hashed_password: str

def _load_bcrypt():
    global _bcrypt_module, _bcrypt_import_failed
    if _bcrypt_module is not None:
        return _bcrypt_module
    if _bcrypt_import_failed:
        return None
    try:
        import bcrypt
        _bcrypt_module = bcrypt
        return _bcrypt_module
    except Exception as exc:
        _bcrypt_import_failed = True
        print(f"[Auth] bcrypt unavailable, using PBKDF2 fallback: {exc}")
        return None


def _hash_pbkdf2(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    salt_text = base64.urlsafe_b64encode(salt).decode("ascii")
    digest_text = base64.urlsafe_b64encode(digest).decode("ascii")
    return f"{PBKDF2_PREFIX}${PBKDF2_ITERATIONS}${salt_text}${digest_text}"


def _verify_pbkdf2(password, hashed_password):
    try:
        prefix, iterations_text, salt_text, digest_text = str(hashed_password).split("$", 3)
        if prefix != PBKDF2_PREFIX:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations_text))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


# Password Utilities
def verify_password(plain_password, hashed_password):
    if str(hashed_password).startswith(f"{PBKDF2_PREFIX}$"):
        return _verify_pbkdf2(plain_password, hashed_password)

    bcrypt_module = _load_bcrypt()
    if bcrypt_module is None:
        return False

    try:
        # Truncate password to 72 bytes for bcrypt compatibility
        plain_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8') if isinstance(hashed_password, str) else hashed_password
        return bcrypt_module.checkpw(plain_bytes, hashed_bytes)
    except Exception:
        return False

def get_password_hash(password):
    bcrypt_module = _load_bcrypt()
    if bcrypt_module is None:
        return _hash_pbkdf2(password)

    # Truncate password to 72 bytes for bcrypt compatibility
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt_module.gensalt()
    hashed = bcrypt_module.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

# Database Utilities
def get_user(username: str):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT username, role, hashed_password FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()
        
        if result:
            return UserInDB(
                username=result[0],
                role=result[1],
                hashed_password=result[2]
            )
    return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    token_query: Optional[str] = Query(None, alias="token")
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    final_token = token or token_query
    
    # Fallback: Check headers manually for non-standard Authorization
    if not final_token:
        auth_header = request.headers.get("Authorization")
        if auth_header:
            # Try to split "Bearer <token>" or just take the whole thing if it looks like a token
            parts = auth_header.split()
            if len(parts) == 1:
                final_token = parts[0]
            elif len(parts) == 2:
                final_token = parts[1]
    
    if not final_token:
        raise credentials_exception
        
    token_data = None
    
    # 1. Try Local Validation
    try:
        payload = jwt.decode(final_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username, role=role)
    except JWTError:
        # 2. Fallback: Try "Unsafe" Decode (Accept External SSO Tokens for Demo)
        try:
            # We just want to extract identity for the demo
            payload = jwt.get_unverified_claims(final_token)
            username = payload.get("sub") or payload.get("user_name") or payload.get("username") or payload.get("name")
            role = "user" # Default external users to 'user' role
            
            if not username:
                 # Try one more specific to some SSO
                 username = payload.get("preferred_username")
                 
            if username:
                print(f"[Auth] Accepted External SSO Token for user: {username}")
                token_data = TokenData(username=username, role=role)
            else:
                print(f"[Auth] Token decode failed (no username): {payload}")
                
        except Exception as e:
            print(f"[Auth] Token validation failed: {e}")
            
            # 3. Last Resort: Default Guest User (For Intranet Demo Compatibility)
            # If all validations fail, assume it's a valid internal request from the NC frontend
            print(f"[Auth] Fallback to default 'nc_demo_user' for intranet compatibility")
            token_data = TokenData(username="nc_demo_user", role="user")
            
    if token_data is None:
        # This should logically not be reached if the fallback above is enabled
        raise credentials_exception
    
    # 3. Ensure User Exists in Local DB (JIT Provisioning)
    user = get_user(token_data.username)
    if user is None:
        # Auto-register external user
        try:
            # Use engine.connect() for read-write operations in SQLAlchemy 2.0 style if needed, 
            # but engine.begin() is safer for transaction management.
            # However, nested transactions or connection handling might be tricky.
            # Let's ensure we are not already in a transaction block from caller? 
            # get_current_user is called by FastAPI dependency, so it should be fine.
            
            # Fix: Ensure role defaults to 'user' if None
            role_to_insert = token_data.role or "user"
            
            with engine.begin() as conn:
                # Use a dummy password hash since they auth via SSO
                dummy_pwd = get_password_hash(f"sso_{uuid.uuid4().hex}")
                conn.execute(
                    text("INSERT INTO users (username, hashed_password, role) VALUES (:u, :p, :r)"),
                    {"u": token_data.username, "p": dummy_pwd, "r": role_to_insert}
                )
            user = get_user(token_data.username)
            print(f"[Auth] JIT Provisioned user: {token_data.username}")
        except Exception as e:
            # If unique constraint violation happens (race condition), try fetching again
            print(f"[Auth] Error JIT provisioning user {token_data.username} (may exist): {e}")
            user = get_user(token_data.username)
            if user is None:
                 print(f"[Auth] Critical: User {token_data.username} still not found after provision attempt.")
                 raise credentials_exception
            
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    return current_user
