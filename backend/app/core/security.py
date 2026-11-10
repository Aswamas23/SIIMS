from datetime import datetime, timedelta, timezone
from typing import Optional, Any
import uuid

from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
import base64

from app.core.config import settings


# --- Password hashing (bcrypt, direct — compatible with $2b$ hashes) ---


def hash_password(password: str) -> str:
    """Hash a plain-text password with bcrypt. Returns a $2b$ hash string."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against its bcrypt ($2b$) hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# --- JWT tokens ---

def create_access_token(subject: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token storing sub + exp."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, jti: Optional[str] = None) -> tuple[str, str]:
    """Create a JWT refresh token. Returns (token, jti)."""
    jti = jti or str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "jti": jti,
        "type": "refresh",
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])


# --- Fernet symmetric encryption ---

def _get_fernet() -> Optional[Fernet]:
    """Return a Fernet instance if FERNET_KEY is configured."""
    key = settings.FERNET_KEY
    if not key:
        return None
    # Accept raw 32-byte keys or proper Fernet URL-safe base64 keys
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except Exception:
        # If key is raw bytes, encode to URL-safe base64
        raw = key.encode() if isinstance(key, str) else key
        b64_key = base64.urlsafe_b64encode(raw.ljust(32)[:32])
        return Fernet(b64_key)


def encrypt_value(plain_text: str) -> str:
    """Encrypt a string value using Fernet. Returns base64 ciphertext."""
    fernet = _get_fernet()
    if not fernet:
        return plain_text  # Fallback: no-op if key not configured
    return fernet.encrypt(plain_text.encode()).decode()


def decrypt_value(cipher_text: str) -> str:
    """Decrypt a Fernet-encrypted string."""
    fernet = _get_fernet()
    if not fernet:
        return cipher_text
    try:
        return fernet.decrypt(cipher_text.encode()).decode()
    except Exception:
        return cipher_text  # Return as-is if decryption fails
