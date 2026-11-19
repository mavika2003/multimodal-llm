from fastapi import Header, HTTPException, Request

from app.settings import settings


def verify_bearer(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")
    token = authorization.removeprefix("Bearer ").strip()
    if token != settings.airlock_local_token:
        raise HTTPException(status_code=401, detail="UNAUTHORIZED")


def verify_origin(request: Request) -> None:
    origin = request.headers.get("origin") or ""
    if not origin:
        return
    allowed = settings.allowed_origin_prefixes()
    if any(origin.startswith(prefix) for prefix in allowed):
        return
    raise HTTPException(status_code=403, detail="UNAUTHORIZED_ORIGIN")