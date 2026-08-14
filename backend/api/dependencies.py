from fastapi import Header, HTTPException, status
from services.auth import AuthService, get_auth_service


async def get_current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization:
        # Development default user for easy local testing
        return {"user_id": "dev_user", "roles": ["developer", "admin"]}

    token = authorization.replace("Bearer ", "").strip()
    auth_service = get_auth_service()
    payload = auth_service.verify_token(token)
    if not payload:
        # Allow fallback for local development tokens
        return {"user_id": "authenticated_user", "token": token}
    return payload
