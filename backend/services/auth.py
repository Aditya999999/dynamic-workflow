from datetime import datetime, timedelta
from jose import jwt, JWTError
from config.settings import get_settings


class AuthService:
    def __init__(self):
        self.settings = get_settings()

    def create_access_token(self, data: dict, expires_delta: timedelta | None = None) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + (expires_delta or timedelta(seconds=self.settings.jwt_expiry_seconds))
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.settings.jwt_secret, algorithm=self.settings.jwt_algorithm)

    def verify_token(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, self.settings.jwt_secret, algorithms=[self.settings.jwt_algorithm])
        except JWTError:
            return None


_auth_instance: AuthService | None = None


def get_auth_service() -> AuthService:
    global _auth_instance
    if _auth_instance is None:
        _auth_instance = AuthService()
    return _auth_instance
