import asyncio
import datetime
import os
import re

import jwt
import jwt.exceptions
import websockets
from sanic import Sanic, redirect, Request, text, Blueprint, json, HTTPResponse
from sanic.exceptions import BadRequest, NotFound, Unauthorized
from sanic.log import logger
from sanic_openapi import openapi
from tortoise.contrib.sanic import register_tortoise
from tortoise.exceptions import IntegrityError
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from compolvo import cors
from compolvo import options
from compolvo.decorators import patch_endpoint, delete_endpoint, get_endpoint, protected
from compolvo.models import User, Service, ServiceOffering, ServicePlan, Tag, Payment, \
    Agent, AgentSoftware, UserRole, Serializable
from compolvo.utils import hash_password, verify_password, generate_secret

HTTP_HEADER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

app = Sanic("compolvo")

app.config.SERVER_NAME = os.environ["SERVER_NAME"]

app.config.SECRET_KEY = os.environ["COMPOLVO_SECRET_KEY"]
app.config.SESSION_TIMEOUT = 60 * 60

db_hostname = os.environ[
    "DB_HOSTNAME"]  # TODO: Make other parameters configurable via environment variables
db_username = os.environ["DB_USERNAME"]
db_password = os.environ["DB_PASSWORD"]
db_database = os.environ["DB_DATABASE"]
db_port = os.environ["DB_PORT"]
register_tortoise(app,
                  db_url=f'mysql://{db_username}:{db_password}@{db_hostname}:{db_port}/{db_database}',
                  modules={'models': ['compolvo.models']}, generate_schemas=True)

user = Blueprint("user", url_prefix="/api/user")
service = Blueprint("service", url_prefix="/api/service")
service_offering = Blueprint("service_offering", url_prefix="/api/service/offering")
service_plan = Blueprint("service_plan", url_prefix="/api/service/plan")
tag = Blueprint("tag", url_prefix="/api/tag")
service_group = Blueprint.group(service, service_offering, service_plan)
payment = Blueprint("payment", url_prefix="/api/payment")
agent = Blueprint("agent", url_prefix="/api/agent")
agent_software = Blueprint("agent_software", url_prefix="/api/agent/software")
api = Blueprint.group(user, service_group, tag, payment, agent, agent_software)

app.blueprint(api)

app.register_middleware(cors.add_cors_headers, "response")


@app.get("/")
async def index(request):
    return redirect("/docs")


@app.listener("before_server_start")
async def test_user(request):
    async def create_user(email: str, first: str, last: str, password: str,
                          role: UserRole.Role = None):
        user = await User.get_or_none(email=email)
        if user is None:
            salt = generate_secret()
            user = await User.create(
                email=email,
                first_name=first,
                last_name=last,
                password=hash_password(password, salt),
                salt=salt,
            )
        if role is None:
            role = UserRole.Role.USER
        existing_role = await UserRole.get_or_none(user=user, role=role)
        if existing_role is None:
            await UserRole.create(
                user=user,
                role=role
            )

    options.setup_options(app, request)
    await create_user("test@example.com", "Test", "user", "test")
    await create_user("admin@example.com", "Admin", "Istrator", "admin", UserRole.Role.ADMIN)


@app.get("/api/login")
async def login(request: Request):
    email = request.args.get("email", [None])
    password = request.args.get("password", None)
    if email is None or password is None:
        raise BadRequest("Missing email or password.")
    user = await User.get_or_none(email=email)
    if not user:
        raise NotFound("User not found.")
    if not verify_password(password, user.password, user.salt):
        raise Unauthorized()
    expires = datetime.datetime.now() + datetime.timedelta(seconds=app.config.SESSION_TIMEOUT)
    token = jwt.encode({"id": str(user.id), "expires": expires.isoformat()}, app.config.SECRET_KEY,
                       algorithm="HS256")
    headers = {"Set-Cookie": f"token={token}; Expires={expires.strftime(HTTP_HEADER_DATE_FORMAT)}"}
    redirect_url = request.args.get("redirect_url", request.url_for("index"))
    return redirect(redirect_url, headers=headers)


@app.get("/api/logout")
async def logout(request: Request):
    redirect_url = request.args.get("redirect_url", request.url_for("index"))
    return redirect(redirect_url, headers={"Set-Cookie": f"token=deleted"})


@app.get("/admin")
@protected({UserRole.Role.ADMIN})
async def admin(request, user):
    return text("Admin page")

@user.get("/")
@protected()
@get_endpoint(User, {UserRole.Role.ADMIN})
async def get_users(request, users, user):
    pass


@user.get("/me")
@protected()
async def get_user(request, user):
    return json(
        {**await user.to_dict(), "roles": [await role.to_dict() for role in await user.roles]})

@user.post("/")
async def create_user(request):
    try:
        salt = generate_secret()
        password = hash_password(request.json["password"], salt)
        user = await User.create(
            first_name=request.json.get("first_name"),
            last_name=request.json.get("last_name"),
            email=request.json["email"],
            password=password,
            salt=salt
        )
        await UserRole.create(
            user=user,
            role=UserRole.Role.USER
        )
        return await user.json()
    except KeyError:
        raise BadRequest("Missing name, email, or password.")
    except IntegrityError:
        return HTTPResponse("Email already taken.", 409)


@user.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(User)
async def update_user(request, patched_user, user):
    pass  # TODO: Make, so that authenticated user can update themselves, but not others


@user.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(User)
async def delete_user(request, deleted_user, user):
    pass  # TODO: Make, so that admins can delete anyone, but everyone themselves


@service.get("/")
@protected()
@get_endpoint(Service)
@openapi.summary("Get all services")
@openapi.description(
    "By default, returns a JSON list of all services including tags. If a `id` is specified in the query args, only that specific service will be returned (provided it is found).")
# @openapi.response(200, {"application/json": Union[List[Service], Service]})
async def get_services(request, services, user):
    async def expand(svc: Service) -> dict:
        return {**await svc.to_dict(), "tags": [await tag.to_dict() for tag in await svc.tags],
                "offerings": [await offering.to_dict() for offering in
                              await ServiceOffering.filter(service=svc).all()]}

    if isinstance(services, list):
        return json(
            [await expand(svc) for
             svc in
             services])
    return json(await expand(services))


@service.post("/")
@protected({UserRole.Role.ADMIN})
async def create_service(request, user):
    service = await Service.create(
        name=request.json["name"],
        description=request.json.get("description"),
        license=request.json.get("license"),
        download_count=request.json.get("download_count"),
        retrieval_method=request.json["retrieval_method"],
        retrieval_data=request.json["retrieval_data"],
        image=request.json.get("image")
    )
    return await service.json()


@service.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(Service)
async def update_service(request, svc, user):
    pass


@service.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(Service)
async def delete_service(request, svc, user):
    pass


@service_offering.get("/")
@protected()
@get_endpoint(ServiceOffering)
async def get_service_offerings(request, offerings, user):
    pass


@service_offering.post("/")
@protected({UserRole.Role.ADMIN})
async def create_service_offering(request, user):
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
@protected({UserRole.Role.ADMIN})
@patch_endpoint(ServiceOffering)
async def update_service_offering(request, offering, user):
    pass


@service_offering.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(ServiceOffering)
async def delete_service_offering(request, offering, user):
    pass


@service_plan.get("/")
@protected()
@get_endpoint(ServicePlan, {UserRole.Role.ADMIN})
async def get_service_plans(request, plans, user):
    pass


@service_plan.post("/")
@protected()
async def create_service_plan(request, user):
    try:
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
@protected({UserRole.Role.ADMIN})
@patch_endpoint(ServicePlan)
async def update_service_plan(request, plan, user):
    pass  # TODO: Make so users can cancel their own service plans


@service_plan.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(ServicePlan)
async def delete_service_plan(request, plan, user):
    pass


@tag.get("/")
@protected()
@get_endpoint(Tag)
async def get_tags(request, tags, user):
    pass


@tag.post("/")
@protected({UserRole.Role.ADMIN})
async def create_tag(request, user):
    try:
        label = request.json["label"]
        tag = await Tag.create(label=label)
        return await tag.json()
    except KeyError:
        raise BadRequest("Missing parameters. Requires: label.")


@tag.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(Tag)
async def update_tag(request, tag, user):
    pass


@tag.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(Tag)
async def delete_tag(request, tag, user):
    pass


async def _get_svc_and_tag(request):
    try:
        service = await Service.get_or_none(id=request.json["service"])
        if service is None:
            raise NotFound("Service not found.")
        tag = await Tag.get_or_none(id=request.json["tag"])
        if tag is None:
            raise NotFound("Tag not found.")
        return service, tag
    except KeyError:
        raise BadRequest("Missing paramete)r(s). Required: service, tag (both as ids).")


@service.post("/tag")
@protected({UserRole.Role.ADMIN})
async def associate_tag_with_service(request, user):
    svc, tag = await _get_svc_and_tag(request)
    await svc.tags.add(tag)
    return HTTPResponse(status=204)


@service.delete("/tag")
@protected({UserRole.Role.ADMIN})
async def deassociate_tag_with_service(request, user):
    svc, tag = await _get_svc_and_tag(request)
    await svc.tags.remove(tag)
    return HTTPResponse(status=204)


@payment.get("/")
@protected()
@get_endpoint(Payment, {UserRole.Role.ADMIN})
async def get_payments(request, payments, user):
    pass


@payment.post("/")
@protected({UserRole.Role.ADMIN})
async def create_payment(request, user):
    try:
        plan = await ServicePlan.get(id=request.json["service_plan"])
        date_str = request.json.get("date")
        if date_str is not None:
            date = datetime.datetime.fromisoformat(date_str)
        else:
            date = datetime.datetime.now()
        payment = await Payment.create(
            service_plan=plan,
            date=date,
            amount=request.json["amount"]
        )
        return await payment.json()
    except KeyError:
        raise BadRequest("Missing parameters. Required: servcice_plan")


@payment.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(Payment)
async def update_payment(request, payment, user):
    pass


@payment.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(Payment)
async def delete_payment(request, payment, user):
    pass

@agent.get("/")
@protected()
async def get_own_agents(request, user):
    agents = await Agent.filter(user=user).all()
    return await Serializable.list_json(agents)


@agent.get("/all")
@protected({UserRole.Role.ADMIN})
@get_endpoint(Agent)
async def get_agents(request, agents, user):
    pass


@agent.post("/")
@protected()
async def create_agent(request, user):
    agent = await Agent.create(
        user=user
    )
    return await agent.json()

@agent.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(Agent)
async def update_agent(request, agent, user):
    pass


@agent.delete("/")
@protected()
@delete_endpoint(Agent)
async def delete_agent(request, agent, user):
    pass


@agent.delete("/bulk")
@protected()
async def bulk_delete_agents(request, user):
    try:
        ids = request.json["ids"]
        print("Ids: ", ids)
        await Agent.filter(id__in=ids).all().delete()  # TODO: Check RBAC
        return HTTPResponse(status=204)
    except KeyError:
        raise BadRequest("Missing parameters. Required: ids")

@agent_software.get("/")
@protected({UserRole.Role.ADMIN})
@get_endpoint(AgentSoftware)
async def get_agent_software(request, software, user):
    pass


@agent_software.post("/")
@protected({UserRole.Role.ADMIN})
async def create_agent_software(request, user):
    try:
        agent = await Agent.get(id=request.json["agent"])
        service_plan = await ServicePlan.get(id=request.json["service_plan"])
        software = await AgentSoftware.create(
            agent=agent,
            service_plan=service_plan,
        )
        return await software.json()
    except KeyError:
        raise BadRequest("Missing parameters. Required: agent, service_plan")


@agent_software.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(AgentSoftware)
async def update_agent_software(request, software, user):
    pass


@agent_software.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(AgentSoftware)
async def delete_agent_software(request, software, user):
    pass


async def websocket_handler(ws: websockets.WebSocketServerProtocol):
    login_msg = await ws.recv()
    match = re.match(r"^login agent (?P<id>[\w-]{36})$", login_msg)
    if match is None:
        return await ws.close(4000, "Invalid login message.")
    agent_id = match.group("id")
    agent = await Agent.get_or_none(id=agent_id)
    if agent is None:
        return await ws.close(4004, "Agent not found.")
    if agent.connected:
        return await ws.close(4003, "Agent is already connected.")
    agent.last_connection_start = datetime.datetime.now()
    agent.connected = True
    agent.connection_interrupted = False
    await agent.save()
    await ws.send("login successful")
    try:
        while True:
            msg = await ws.recv()
            await ws.send(msg)
    except ConnectionClosedOK:
        pass
    except ConnectionClosedError:
        agent.connection_interrupted = True
    finally:
        agent.last_connection_end = datetime.datetime.now()
        agent.connected = False
        await agent.save()


async def run_websocket_server(app):
    logger.info("Preparing agents' connected attributes...")
    agents = await Agent.filter(connected=True).all()
    for agent in agents:
        agent.connected = False
        await agent.save()
    async with websockets.serve(websocket_handler, "0.0.0.0", 8001):
        logger.info("Started websocket server")
        await asyncio.Future()


app.add_task(run_websocket_server(app))

if __name__ == "__main__":
    app.run("0.0.0.0")
