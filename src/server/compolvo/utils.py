import datetime
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
