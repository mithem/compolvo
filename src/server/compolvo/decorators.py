from functools import wraps
from typing import Type, Set

from compolvo.models import Serializable, UserRole, User
from compolvo.utils import check_token, user_has_roles
from sanic import HTTPResponse
from sanic.exceptions import BadRequest, NotFound, Unauthorized


def patch_endpoint(cls: Type[Serializable]):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            try:
                instance = await cls.get_or_none(id=request.args["id"][0])
            except KeyError:
                raise BadRequest(f"Please specify the {cls.__name__}'s id in the query parameters.")
            if instance is None:
                raise NotFound(f"Specified {cls.__name__} not found.")
            for key, value in request.json.items():
                if key not in cls.fields:
                    raise BadRequest(f"Key '{key}' does not exist on {cls.__name__}.")
                setattr(instance, key, value)
            await instance.save()
            return_value = await func(request, instance, *args, **kwargs)
            return return_value if return_value is not None else await instance.json()

        return wrapper

    return decorator


def delete_endpoint(cls: Type[Serializable]):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            instance = await cls.get_or_none(id=request.args["id"][0])
            if instance is None:
                raise NotFound(f"Specified {cls.__name__} not found.")
            await instance.delete()
            return_value = await func(request, instance, *args, **kwargs)
            return return_value if return_value is not None else HTTPResponse(status=204)

        return wrapper

    return decorator


def get_endpoint(cls: Type[Serializable], listing_requires: Set[UserRole.Role] = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            assert isinstance(args[0], User), "Please use the @protected decorator before this one."
            user = args[0]
            instance_id = request.args.get("id", None)
            if instance_id is None:
                if listing_requires is not None and not await user_has_roles(user,
                                                                             listing_requires):
                    raise Unauthorized()
                instances = await cls.all()
                return_value = await func(request, instances, *args, **kwargs)
                if return_value is not None:
                    return return_value
                return await Serializable.list_json(instances)
            instance = await cls.get_or_none(id=instance_id)
            if instance is None:
                raise NotFound(f"Specified {cls.__name__} not found.")
            return_value = await func(request, instance, *args, **kwargs)
            if return_value is not None:
                return return_value
            return await instance.json()

        return wrapper

    return decorator


def protected(requires_roles: Set[UserRole.Role] = None):
    def decorator(func):
        @wraps(func)
        async def decorated_function(request, *args, **kwargs):
            try:
                user = await check_token(request)
                assert user
                if requires_roles is not None:
                    assert await user_has_roles(user, requires_roles)

                response = await func(request, user, *args, **kwargs)
                return response
            except AssertionError:
                raise Unauthorized("Unauthorized.")

        return decorated_function

    return decorator
