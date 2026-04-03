from passlib.context import CryptContext

# Using bcrypt for password hashing
pwd_context = CryptContext(schemas=["bcrypt"], deprecated="auto")


def hash_password(plain_text_password: str) -> str:
    """Hash a plain text password using bcrypt."""
    return pwd_context.hash(plain_text_password)


def verify_password(plain_text_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_text_password, hashed_password)
