import datetime
import hashlib
import re
import secrets
import string
from typing import Optional, Set

import compolvo.email
import jwt
import sanic
from compolvo.models import UserRole, User
from jwt.exceptions import InvalidTokenError
from sanic import Request
from sanic.exceptions import SanicException

EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS = 1


async def check_token(token: str, secret_key: str) -> Optional[User]:
    try:
        token = jwt.decode(
            token, secret_key, algorithms=["HS256"]
        )
        if datetime.datetime.fromisoformat(token["expires"]) <= datetime.datetime.now(
                tz=datetime.timezone.utc):
            return None
        return await User.get_or_none(id=token["id"])
    except (InvalidTokenError, KeyError):
        return None


class Unauthorized(SanicException):
    status = 401
    message = "Unauthorized. Please log in."


class BadRequest(SanicException):
    def __init__(self, message: str, status=400):
        self.message = message
        self.status = status


class NotFound(SanicException):
    def __init__(self, message: str, status=404):
        self.message = message
        self.status = status


async def check_token_for_request(request: Request) -> Optional[User]:
    token = request.cookies.get("token")
    if not token:
        return None
    return await check_token(token, request.app.config.SECRET_KEY)


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


def test_email(email: str) -> bool:
    #  https://stackoverflow.com/questions/201323/how-can-i-validate-an-email-address-using-a-regular-expression
    pattern = r"(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9]))\.){3}(?:(2(5[0-5]|[0-4][0-9])|1[0-9][0-9]|[1-9]?[0-9])|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    match = re.match(pattern, email)
    return match is not None


async def send_user_email_verification_mail(app: sanic.Sanic, email: str, user: User):
    valid_until = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        hours=EMAIL_VERIFICATION_TOKEN_LIFETIME_HOURS)
    token = jwt.encode(
        {"id": str(user.id), "valid_until": valid_until.isoformat()},
        app.config.SECRET_KEY,
        algorithm="HS256")
    user.email_verified = False
    user.email_verification_token = token
    await user.save()
    compolvo.email.send_email(email, "Verify your email", "email-verification.jinja",
                              {"token": token})
