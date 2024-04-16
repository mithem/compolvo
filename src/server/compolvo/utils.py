import datetime
import hashlib
import secrets
import string
from typing import Optional, Set

import jwt
from compolvo.models import User, UserRole
from jwt.exceptions import InvalidTokenError


async def check_token(request) -> Optional[User]:
    token = request.cookies.get("token")
    if not token:
        return None

    try:
        token = jwt.decode(
            token, request.app.config.SECRET_KEY, algorithms=["HS256"]
        )
        if datetime.datetime.fromisoformat(token["expires"]) <= datetime.datetime.now():
            return None
        return await User.get_or_none(id=token["id"])
    except (InvalidTokenError, KeyError):
        return None


async def user_has_roles(user: User, roles: Set[UserRole.Role]) -> bool:
    existing_role_objs = await UserRole.filter(user=user, role__in=roles)
    existing_roles = map(lambda obj: obj.role, existing_role_objs)
    return set(existing_roles) == roles


def hash_password(password: str, salt: str) -> str:
    return hashlib.sha3_512((password + ":" + salt).encode("utf-8")).hexdigest()


def verify_password(password: str, hash: str, salt: str) -> bool:
    return hash_password(password, salt) == hash


def generate_secret() -> str:
    return "".join(secrets.choice(string.ascii_letters) for _ in range(32))
