from functools import wraps
from typing import Type, Set

import stripe as stripe_module
from compolvo.models import Serializable, UserRole, User
from compolvo.utils import check_token_for_request, Unauthorized
from compolvo.utils import user_has_roles
from sanic import HTTPResponse, text
from sanic.exceptions import BadRequest, NotFound


def patch_endpoint(cls: Type[Serializable], ignore_unsupported_fields: bool = False):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            id = None
            try:
                id = request.args["id"][0]
                instance = await cls.get_or_none(id=id)
            except KeyError:
                raise BadRequest(f"Please specify the {cls.__name__}'s id in the query parameters.")
            if instance is None:
                raise NotFound(f"Specified {cls.__name__} '{id}' not found.")
            for key, value in request.json.items():
                fields = set(getattr(cls, "patch_fields", cls.fields)) - {"id"}
                if key in fields:
                    setattr(instance, key, value)
                elif not ignore_unsupported_fields:
                    raise BadRequest(f"Key '{key}' does not exist on {cls.__name__}.")
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


def bulk_delete_endpoint(cls: Type[Serializable], requires_roles: Set[UserRole.Role]):
    def decorator(func):
        @wraps(func)
        @protected(requires_roles)
        async def wrapper(request, *args, **kwargs):
            bad_request = BadRequest("Expected JSON body with 'ids' key.")
            if not request.json:
                raise bad_request
            try:
                ids = request.json["ids"]
                await cls.filter(id__in=ids).delete()
                return_value = await func(request, ids, *args, **kwargs)
                return return_value if return_value is not None else HTTPResponse(status=204)
            except KeyError:
                raise bad_request
        return wrapper
    return decorator


def get_endpoint(cls: Type[Serializable], listing_requires: Set[UserRole.Role] = None):
    def decorator(func):
        @wraps(func)
        async def wrapper(request, *args, **kwargs):
            if listing_requires is not None:
                assert isinstance(args[0],
                                  User), "Please use the @protected decorator before this one."
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
            unauthorized = Unauthorized()
            user = await check_token_for_request(request)
            if user is None or not user.logged_in:
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
            if stripe.api_key is None:
                return HTTPResponse("Stripe API key not set, which is required for this endpoint.",
                                    status=500)
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


def requires_verified_email():
    def decorator(func):
        @wraps(func)
        @protected()
        async def decorated_function(request, user: User, *args, **kwargs):
            if not user.email_verified:
                return text("Requires email verification.", status=403)
            return await func(request, *args, **kwargs)

        return decorated_function

    return decorator
