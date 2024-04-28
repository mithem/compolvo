from functools import wraps
from typing import Type, Set

import stripe as stripe_module
from compolvo.models import Serializable, UserRole, User
from compolvo.utils import check_token, user_has_roles
from sanic import HTTPResponse, text
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
                fields = set(getattr(cls, "patch_fields", cls.fields)) - {"id"}
                if key not in fields:
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
            unauthorized = Unauthorized("Unauthorized.")
            user = await check_token(request)
            if user is None:
                raise unauthorized
            if requires_roles is not None:
                if not await user_has_roles(user, requires_roles):
                    raise unauthorized

            return await func(request, user, *args, **kwargs)

        return decorated_function

    return decorator


def requires_stripe_customer(stripe):
    def decorator(func):
        @wraps(func)
        @protected()
        async def decorated_function(request, user: User, *args, **kwargs):
            customer_not_found = text("Stripe customer not found. Try again later.", status=500)
            if user.stripe_id is None:
                return text("Requires stripe synchronization", status=500)
            try:
                customer = await stripe.Customer.retrieve_async(user.stripe_id)
                if getattr(customer, "deleted", False):
                    return customer_not_found
            except stripe.InvalidRequestError:
                return customer_not_found
            return await func(request, user, customer, *args, **kwargs)
        return decorated_function
    return decorator


def requires_payment_details(stripe):
    def decorator(func):
        @wraps(func)
        @requires_stripe_customer(stripe)
        async def decorated_function(request, user: User, customer: stripe_module.Customer, *args,
                                     **kwargs):
            methods = await customer.list_payment_methods_async()
            if len(methods.data) == 0:
                return text("Requires payment details.", status=402)
            return await func(request, user, methods, *args, **kwargs)

        return decorated_function
    return decorator
