import datetime
import os
import secrets
import string

from sanic import Sanic, redirect, Request, text, Blueprint, json, HTTPResponse
from sanic.exceptions import BadRequest, NotFound
from sanic_beskar import Beskar
from sanic_beskar.exceptions import AuthenticationError, TOTPRequired
from sanic_openapi import openapi
from tortoise.contrib.sanic import register_tortoise

from compolvo import cors
from compolvo import options
from compolvo.decorators import patch_endpoint, delete_endpoint, get_endpoint
from compolvo.models import User, Service, Serializable, ServiceOffering, ServicePlan, Tag

app = Sanic("compolvo")
beskar = Beskar()

app.config.SECRET_KEY = "".join(secrets.choice(string.ascii_letters) for i in range(32))

beskar.init_app(app, User)
db_hostname = os.environ[
    "DB_HOSTNAME"]  # TODO: Make other parameters configurable via environment variables
register_tortoise(app, db_url=f'mysql://root:@{db_hostname}:3306/compolvo',
                  modules={'models': ['compolvo.models']}, generate_schemas=True)

user = Blueprint("user", url_prefix="/api/user")
service = Blueprint("service", url_prefix="/api/service")
service_offering = Blueprint("service_offering", url_prefix="/api/service/offering")
service_plan = Blueprint("service_plan", url_prefix="/api/service/plan")
tag = Blueprint("tag", url_prefix="/api/tag")
service_group = Blueprint.group(service, service_offering, service_plan)
api = Blueprint.group(user, service_group, tag)

app.blueprint(api)

app.register_middleware(cors.add_cors_headers, "response")


@app.get("/")
async def index(request):
    return redirect("/docs")


@app.listener("before_server_start")
async def test_user(request):
    options.setup_options(app, request)
    email = "test@example.com"
    user = await User.get_or_none(email=email)
    if user:
        return text("Already exists.")
    else:
        await User(
            email=email,
            name="Test user",
            password=beskar.hash_password("test")
        ).save()
        return text("Created", status=201)


@app.get("/login")
async def login(request: Request):
    try:
        user = await beskar.authenticate(request.args["email"][0], request.args["password"][0],
                                         lookup="email")
        return redirect(
            request.url_for("index"),
            headers={"Authorization": "Bearer " + await beskar.encode_jwt_token(user)},
        )
    except (KeyError, IndexError):
        raise BadRequest("Expected email as well as password.")
    except (AuthenticationError, TOTPRequired) as e:
        raise BadRequest("Invalid email or password.") from e


@app.get("/protected")
# @sanic_beskar.auth_required
async def protected(request):
    return text("You're accessing a protected page!")


@user.get("/")
# @sanic_beskar.roles_required(["admin"])
async def get_users(request):
    return await Serializable.all_json(User)


@user.post("/")
async def create_user(request):
    try:
        user = await User.create(
            name=request.json["name"],
            email=request.json["email"],
            password=beskar.hash_password(request.json["password"])
        )
        return user.json()
    except KeyError:
        raise BadRequest("Missing name, email, or password.")


@user.patch("/")
@patch_endpoint(User)
async def update_user(request, user):
    pass  # TODO: Authentication: require that user changes itself or has admin/user role


@user.delete("/")
@delete_endpoint(User)
async def delete_user(request, user):
    pass


@service.get("/")
@get_endpoint(Service)
@openapi.summary("Get all services")
@openapi.description(
    "By default, returns a JSON list of all services including tags. If a `id` is specified in the query args, only that specific service will be returned (provided it is found).")
# @openapi.response(200, {"application/json": Union[List[Service], Service]})
async def get_services(request, services):
    async def expand(svc: Service) -> dict:
        return {**await svc.to_dict(), "tags": [await tag.to_dict() for tag in await svc.tags]}

    if isinstance(services, list):
        return json(
            [await expand(svc) for
             svc in
             services])
    return json(await expand(services))


@service.post("/")
async def create_service(request):
    service = await Service.create(
        name=request.json["name"],
        description=request.json.get("description"),
        license=request.json.get("license"),
        download_count=request.json.get("download_count"),
        retrieval_method=request.json["retrieval_method"],
        retrieval_data=request.json["retrieval_data"]
    )
    return await service.json()


@service.patch("/")
@patch_endpoint(Service)
async def update_service(request, svc):
    pass


@service.delete("/")
@delete_endpoint(Service)
async def delete_service(request, svc):
    pass


@service_offering.get("/")
@get_endpoint(ServiceOffering)
async def get_service_offerings(request, offerings):
    pass


@service_offering.post("/")
async def create_service_offering(request):
    try:
        svc = await Service.get_or_none(id=request.json["service"])
        if svc is None:
            raise NotFound("Specified service not found.")
        offering = await ServiceOffering.create(
            name=request.json["name"],
            description=request.json.get("description"),
            price=request.json["price"],
            duration_days=request.json["duration_days"],
            service=svc
        )
        return await offering.json()
    except KeyError:
        raise BadRequest(
            "Missing parameters. Please provide service, name, price, and duration_days.")


@service_offering.patch("/")
@patch_endpoint(ServiceOffering)
async def update_service_offering(request, offering):
    pass


@service_offering.delete("/")
@delete_endpoint(ServiceOffering)
async def delete_service_offering(request, offering):
    pass


@service_plan.get("/")
@get_endpoint(ServicePlan)
async def get_service_plans(request, plans):
    pass


@service_plan.post("/")
async def create_service_plan(request):
    try:
        user_id = request.json["user"]
        user = await User.get(id=user_id)
        service_offering_id = request.json["service_offering"]
        offering = await ServiceOffering.get(id=service_offering_id)
        start_date = request.json.get("start_date")
        start = datetime.date.fromisoformat(
            start_date) if start_date is not None else datetime.datetime.now()
        data = {"user": user, "service_offering": offering, "start_date": start}
        end = request.json.get("end_date")
        if end is not None:
            data = {**data, "end_date": datetime.datetime.fromisoformat(end)}
        plan = await ServicePlan.create(**data)
        return await plan.json()
    except KeyError:
        raise BadRequest("Missing parameters. Required: service_offering, and user.")


@service_plan.patch("/")
@patch_endpoint(ServicePlan)
async def update_service_plan(request, plan):
    pass


@service_plan.delete("/")
@delete_endpoint(ServicePlan)
async def delete_service_plan(request):
    pass


@tag.get("/")
@get_endpoint(Tag)
async def get_tags(request, tags):
    pass


@tag.post("/")
async def create_tag(request):
    try:
        label = request.json["label"]
        tag = await Tag.create(label=label)
        return await tag.json()
    except KeyError:
        raise BadRequest("Missing parameters. Requires: label.")


@tag.patch("/")
@patch_endpoint(Tag)
async def update_tag(request, tag):
    pass


@tag.delete("/")
@delete_endpoint(Tag)
async def delete_tag(request, tag):
    pass


async def _get_svc_and_tag(request):
    try:
        service = await Service.get(id=request.json["service"])
        tag = await Tag.get(id=request.json["tag"])
        return service, tag
    except KeyError:
        raise BadRequest("Missing parameter(s). Required: service, tag (both as ids).")


@service.post("/tag")
async def associate_tag_with_service(request):
    svc, tag = await _get_svc_and_tag(request)
    await svc.tags.add(tag)
    return HTTPResponse(status=204)


@service.delete("/tag")
async def deassociate_tag_with_service(request):
    svc, tag = await _get_svc_and_tag(request)
    await svc.tags.remove(tag)
    return HTTPResponse(status=204)


if __name__ == "__main__":
    app.run("0.0.0.0")
