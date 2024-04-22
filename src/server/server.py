import asyncio
import datetime
import os
import queue
import re
from queue import Queue
from typing import Set, Dict

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
    Agent, AgentSoftware, UserRole, Serializable, License, OperatingSystem
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


@app.post("/api/setup")
@protected({UserRole.Role.ADMIN})
async def db_setup(request, user):
    if request.json is not None and request.json.get("services", False):
        tag_developer = await Tag.create(
            label="Developer"
        )
        tag_enthusiast = await Tag.create(
            label="Enthusiast"
        )
        lic_propr = await License.create(
            name="Proprietary"
        )
        lic_mit = await License.create(
            name="MIT"
        )
        os_lin = await OperatingSystem.create(
            name="Linux"
        )
        os_win = await OperatingSystem.create(
            name="Windows"
        )
        os_mac = await OperatingSystem.create(
            name="macOS"
        )
        svc_docker = await Service.create(
            system_name="docker-desktop",
            name="Docker Desktop",
            description="The ultimate Docker experience.",
            license=lic_propr,
            download_count=42069,
            image="",
            latest_version="1.2.5"
        )
        await svc_docker.tags.add(
            tag_developer,
            tag_enthusiast
        )
        await svc_docker.operating_systems.add(
            os_lin,
            os_win,
            os_mac
        )
        await svc_docker.save()
        svc_nginx = await Service.create(
            system_name="nginx",
            name="Nginx",
            description="THE web server",
            license=lic_mit,
            download_count=13098438,
            image="",
            latest_version="1.25.5"
        )
        await svc_nginx.tags.add(
            tag_developer
        )
        await svc_nginx.operating_systems.add(
            os_lin,
            os_mac
        )
        await svc_nginx.save()
        svc_git = await Service.create(
            system_name="git",
            name="Git",
            description="The ultimate version control system.",
            license=lic_mit,
            download_count=42069,
            image=""
        )
        await svc_git.tags.add(
            tag_developer
        )
        await svc_git.operating_systems.add(
            os_lin,
            os_win,
            os_mac
        )
        await svc_git.save()
        svc_nextcloud = await Service.create(
            system_name="nextcloud",
            name="Nextcloud",
            description="The comprehensive cloud - right from your home",
            license=lic_mit,
            download_count=42069,
            retrieval_method=Service.RetrievalMethod.COMMAND,
            retrieval_data='{"hello": "world"}',
            image=""
        )
        await svc_nextcloud.tags.add(
            tag_enthusiast
        )
        await svc_nextcloud.operating_systems.add(
            os_lin,
            os_mac
        )
        await svc_nextcloud.save()
        if request.json is not None and request.json.get("service_offerings", False):
            off_docker_month = await ServiceOffering.create(
                service=svc_docker,
                name="month",
                price=9.99,
                duration_days=30
            )
            off_docker_year = await ServiceOffering.create(
                service=svc_docker,
                name="year",
                price=99.99,
                duration_days=360
            )
            off_git_month = await ServiceOffering.create(
                service=svc_git,
                name="month",
                price=2.99,
                duration_days=30
            )
            off_nextcloud_year = await ServiceOffering.create(
                service=svc_nextcloud,
                name="year",
                price=29.00,
                duration_days=360
            )
            if request.json is not None and request.json.get("service_plans", False):
                plan_docker = await ServicePlan.create(
                    user=user,
                    service_offering=off_docker_month,
                    start_date=datetime.datetime.now()
                )
                plan_git = await ServicePlan.create(
                    user=user,
                    service_offering=off_git_month,
                    start_date=datetime.datetime.now() - datetime.timedelta(days=7)
                )
                plan_nextcloud = await ServicePlan.create(
                    user=user,
                    service_offering=off_nextcloud_year,
                    start_date=datetime.datetime.now() - datetime.timedelta(days=45)
                )
    return HTTPResponse("Created.", status=201)


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
        return {
            **await svc.to_dict(),
            "tags": [await tag.to_dict() for tag in await svc.tags],
            "offerings": [await offering.to_dict() for offering in
                          await ServiceOffering.filter(service=svc).all()],
            "operating_systems": await Serializable.list_dict(await svc.operating_systems)
        }

    if isinstance(services, list):
        return json(
            [await expand(svc) for
             svc in
             services])
    return json(await expand(services))


@service.post("/")
@protected({UserRole.Role.ADMIN})
async def create_service(request, user):
    lic = request.json.get("license")
    license = await License.get_or_none(id=lic) if lic is not None else None
    service = await Service.create(
        system_name=request.json["system_name"],
        name=request.json["name"],
        description=request.json.get("description"),
        license=license,
        download_count=request.json.get("download_count"),
        retrieval_method=request.json["retrieval_method"],
        retrieval_data=request.json["retrieval_data"],
        image=request.json.get("image")
    )
    oses = request.json.get("operating_systems")
    if oses is not None:
        await service.operating_systems.add(
            *await OperatingSystem.filter(id__in=oses).all()
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


@service_plan.get("/all")
@protected()
@get_endpoint(ServicePlan, {UserRole.Role.ADMIN})
async def get_service_plans(request, plans, user):
    pass


@service_plan.get("/")
@protected()
async def get_own_service_plans(request, user):
    filter_data = {"user": user}
    id = request.args.get("id")
    if id is not None:
        filter_data["id"] = id
    plans = await ServicePlan.filter(**filter_data).all()
    data = []
    for plan in plans:
        offering: ServiceOffering = await plan.service_offering
        service: Service = await offering.service
        offering_dict = {**await offering.to_dict(), "service": await service.to_dict()}
        if plan.canceled_by_user:
            installable = False
        else:
            agent_count = await Agent.filter(user=user).count()
            software_instances_count = await AgentSoftware.filter(service_plan=plan).count()
            installable = software_instances_count < agent_count
        plan_dict = {
            **await plan.to_dict(),
            "service_offering": offering_dict,
            "installable": installable
        }
        data.append(plan_dict)
    return json(data)


@service_plan.post("/")
@protected()
async def create_service_plan(request, user):
    try:
        service_offering_id = request.json["service_offering"]
        offering = await ServiceOffering.get_or_none(id=service_offering_id)
        if offering is None:
            raise NotFound("Specified service offering not found.")
        start_date = request.json.get("start_date")
        start = datetime.date.fromisoformat(
            start_date) if start_date is not None else datetime.datetime.now()
        data = {"user": user, "service_offering": offering, "start_date": start}
        end = request.json.get("end_date")
        if end is not None:
            data["end_date"] = datetime.datetime.fromisoformat(end)
        plan = await ServicePlan.create(**data)
        return await plan.json()
    except (KeyError, AttributeError):
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
    except (KeyError, AttributeError):
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
    plan = request.args.get("installable_for_service_plan")
    if plan is not None:
        plan = await ServicePlan.get_or_none(id=plan)
        if plan is None:
            raise NotFound("Service plan not found.")
        softwares = await AgentSoftware.filter(service_plan=plan).all()
        agents = {await software.agent for software in softwares}
        installable_agents: Set[Serializable] = set(await Agent.filter(user=user).all()) - agents
        return await Serializable.list_json(installable_agents)

    agents = await Agent.filter(user=user).all()
    return await Serializable.list_json(agents)


@agent.get("/name")
async def get_agent_name(request):
    try:
        agent_id = request.args["id"][0]
        agent = await Agent.get_or_none(id=agent_id)
        if agent is None:
            raise NotFound("Agent not found.")
        if not agent.initialized:
            agent.initialized = True
            await agent.save()
        return json({"name": agent.name})
    except KeyError:
        raise BadRequest("Expected `id` query param.")


@agent.patch("/name")
async def update_agent_name(request):
    try:
        id = request.json["id"]
        new_name = request.json["name"]
        agent = await Agent.get_or_none(id=id)
        if agent is None:
            raise NotFound("Agent not found.")
        agent.name = new_name
        await agent.save()
        return json({"name": new_name})
    except (KeyError, AttributeError):
        raise BadRequest("Missing parameter. Expected 'id' and 'name'")


@agent.get("/all")
@protected({UserRole.Role.ADMIN})
@get_endpoint(Agent)
async def get_agents(request, agents, user):
    pass


@agent.post("/")
@protected()
async def create_agent(request, user):
    name = request.json.get("name") if request.json is not None else None
    agent = await Agent.create(
        user=user,
        name=name
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


@agent_software.get("/all")
@protected({UserRole.Role.ADMIN})
@get_endpoint(AgentSoftware)
async def get_agent_software(request, software, user):
    pass


@agent_software.get("/")
@protected()
async def get_own_agent_software(request, user):
    softwares = await AgentSoftware.filter(agent__user=user).all()
    data = []
    for software in softwares:
        offering = await (await software.service_plan).service_offering
        service = await offering.service
        agent = await software.agent
        data.append(
            {
                **await software.to_dict(),
                "latest_version": service.latest_version,
                "offering": await offering.to_dict(),
                "service": await service.to_dict(),
                "agent": await agent.to_dict()
            })
    return json(data)


@agent_software.post("/")
@protected({UserRole.Role.ADMIN})
async def create_agent_software(request, user):
    try:
        agent = await Agent.get_or_none(id=request.json["agent"])
        if agent is None:
            raise NotFound("Agent not found.")
        service_plan = await ServicePlan.get_or_none(id=request.json["service_plan"])
        if service_plan is None:
            raise NotFound("Service plan not found.")
        software = await AgentSoftware.create(
            agent=agent,
            service_plan=service_plan,
        )
        return await software.json()
    except KeyError:
        raise BadRequest("Missing parameters. Required: agent, service_plan")


@agent_software.post("/bulk")
@protected()
async def bulk_create_agent_software(request, user):
    missing_params = BadRequest("Missing parameters. Required: agents, service_plan.")
    agents = []
    if request.json is None:
        raise missing_params
    try:
        plan = await ServicePlan.get_or_none(id=request.json["service_plan"])
        if plan is None:
            raise NotFound("Service plan not found.")
        offering: ServiceOffering = await plan.service_offering
        service: Service = await offering.service
        offerings = await ServiceOffering.filter(service=service).all()
        offering_ids = list(map(lambda offering: offering.id, offerings))
        existing_plans = list(map(lambda plan: plan.id, await ServicePlan.filter(user=user,
                                                                                 service_offering_id__in=offering_ids).all()))
        existing_softwares = await AgentSoftware.filter(
            service_plan_id__in=existing_plans).all().prefetch_related("agent")
        if (await plan.user).id != user.id:
            raise BadRequest(
                "You can't bulk-create agent software for another user's service plan.")
        agent_ids = request.json.get("agents", [])
        for id in agent_ids:
            agent = await Agent.get_or_none(id=id)
            if agent is None:
                raise NotFound(f"Agent {id} not found.")
            if (await agent.user).id != user.id:
                raise BadRequest("You can't bulk-create agent software for other user's agents.")
            for software in existing_softwares:
                potentially_already_installed_agent = await software.agent
                if str(potentially_already_installed_agent.id) == id:
                    raise BadRequest(
                        f"The software you want to install via the service plan is already installed on agent {id} (possibly by another service plan).")
            agents.append(agent)
        softwares = [AgentSoftware(agent=agent, service_plan=plan) for agent in agents]
        await AgentSoftware.bulk_create(softwares)
        for (software, agent) in zip(softwares, agents):
            queue_websocket_msg(str(agent.id),
                                f"install {service.system_name} {software.id} v{service.latest_version}")
        return HTTPResponse(status=201)
    except KeyError:
        raise missing_params
    except IntegrityError:
        raise BadRequest("Service plan is already installed on at least one agent.")


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


@app.post("/api/agent/ws/queue")
@protected({UserRole.Role.ADMIN})
async def send_agent_queue_message(request, user):
    try:
        agent_id = request.json["agent"]
        message = request.json["message"]
        count = request.json.get("count", 1)
        for i in range(count):
            queue_websocket_msg(agent_id, message)
        return text("Accepted.", status=202)
    except KeyError:
        raise BadRequest("Missing parameters. Expected `agent`, `message`")


# Queue for messages pending to be sent to respective agents
websocket_message_queue: Dict[str, Queue[str]] = dict()
# Queue for handling messages sent by agents (as that might require expensive database calls)
# Format: (agent_id: str, message: str)
websocket_handler_queue: Queue[(str, str)] = Queue()


def queue_websocket_msg(agent_id: str, message: str):
    assert type(
        agent_id) == str, "agent id isn't of type str. Don't search further why messages don't get delivered"
    global websocket_message_queue
    queue = websocket_message_queue.get(agent_id)
    if queue is None:
        queue = Queue()
    queue.put(message)
    websocket_message_queue[agent_id] = queue
    logger.debug(f"Queued message for {agent_id}: {message}")


async def handle_websocket_msg(agent_id: str, message: str) -> str | None:
    logger.debug("Handling websocket message for %s: %s", agent_id, message)
    status_pattern = r"(?P<status_key>[\w\d_-]+)=(?P<status_value>[\w\d\    ._-]+)"
    software_status_pattern = r"software status (?P<software_id>[\w\d-]{36}) (?P<status>[\w\d_\.=;-]+)"
    software_status_match = re.match(software_status_pattern, message)
    if software_status_match is not None:
        software_id = software_status_match.group("software_id")
        status = software_status_match.group("status")
        stati = status.split(";")
        print("Stati: " + str(stati))
        status_data = {}
        for status_entry in stati:
            match = re.match(status_pattern, status_entry)
            if match is not None:
                status_data[match.group("status_key")] = match.group("status_value")
        print("Status data: " + str(status_data))
        software = await AgentSoftware.get_or_none(id=software_id)
        if set(status_data.keys()).issubset({"corrupt", "installed_version"}):
            for key, value in status_data.items():
                if value in ["true", "false"]:
                    value = value == "true"
                elif value in ["null", "None"]:
                    value = None
                setattr(software, key, value)
            await software.save()
    return None


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
    logger.debug("Agent logged in successfully: %s", agent_id)

    async def message_emitter(queue: Queue):
        if queue is not None:
            while not queue.empty():
                msg = queue.get()
                await ws.send(msg)

    async def message_consumer():
        try:
            async with asyncio.timeout(1):
                msg = await ws.recv()
                websocket_handler_queue.put((agent_id, msg))
        except TimeoutError:
            pass

    try:
        while True:
            queue = websocket_message_queue.get(agent_id)
            if ws.closed:
                if ws.close_code != 1000:
                    raise ConnectionClosedError(ws.close_rcvd, ws.close_sent)
                raise ConnectionClosedOK(ws.close_rcvd, ws.close_sent)
            await asyncio.gather(message_emitter(queue), message_consumer())
    except ConnectionClosedOK:
        logger.debug("Connection to agent %s closed ok", agent_id)
    except ConnectionClosedError:
        logger.warning("Connection to agent %s closed unexpectedly", agent_id)
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


async def run_websocket_handler_queue_worker():
    logger.info("Running worker handling websocket message queue...")
    while True:
        try:
            agent_id, msg = websocket_handler_queue.get(block=False)
            await handle_websocket_msg(agent_id, msg)
        except queue.Empty:
            await asyncio.sleep(1)



app.add_task(run_websocket_server(app))
app.add_task(run_websocket_handler_queue_worker())

if __name__ == "__main__":
    app.run("0.0.0.0")
