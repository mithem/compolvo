from functools import wraps
from typing import Type

from compolvo.models import Serializable
from sanic import HTTPResponse
from sanic.exceptions import BadRequest, NotFound


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
        async def wrapper(request, *args, **kwargs):
            instance = await cls.get_or_none(id=request.args["id"][0])
            if instance is None:
                raise NotFound(f"Specified {cls.__name__} not found.")
            await instance.delete()
            return_value = await func(request, instance, *args, **kwargs)
            return return_value if return_value is not None else HTTPResponse(status=204)

        return wrapper

    return decorator
