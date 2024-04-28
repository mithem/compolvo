import datetime
import enum
import os
from typing import Set, Tuple, Dict

import jwt
import jwt.exceptions
import stripe
from sanic import Sanic, redirect, Request, text, Blueprint, json, HTTPResponse
from sanic.exceptions import BadRequest, NotFound, Unauthorized
from sanic.log import logger
from sanic_openapi import openapi
from tortoise.contrib.sanic import register_tortoise
from tortoise.exceptions import IntegrityError
from tortoise.expressions import Q
from tortoise.functions import Coalesce

from compolvo import cors
from compolvo import options
from compolvo.decorators import patch_endpoint, delete_endpoint, get_endpoint, protected, \
    requires_payment_details, requires_stripe_customer
from compolvo.models import Agent, AgentSoftware, Serializable, PackageManager, \
    PackageManagerAvailableVersion, \
    BillingCycle, BillingCycleType
from compolvo.models import Service, OperatingSystem, Tag, UserRole, User, License, \
    ServiceOffering, ServicePlan
from compolvo.utils import verify_password, hash_password, generate_secret, test_email
from compolvo.websockets import run_websocket_server, run_websocket_handler_queue_worker, \
    queue_websocket_msg

HTTP_HEADER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

app = Sanic("compolvo")

app.config.SERVER_NAME = os.environ["SERVER_NAME"]

app.config.SECRET_KEY = os.environ["COMPOLVO_SECRET_KEY"]
app.config.SESSION_TIMEOUT = 60 * 60

STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
if STRIPE_API_KEY is not None:
    stripe.api_key = STRIPE_API_KEY

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
license = Blueprint("license", url_prefix="/api/license")
operating_system = Blueprint("operating_system", url_prefix="/api/operating-system")
payment_intent = Blueprint("payment_intent", url_prefix="/api/billing/payment/intent")
payment_method = Blueprint("payment_method", url_prefix="/api/billing/payment/method")
billing = Blueprint.group(payment_intent, payment_method)
api = Blueprint.group(user, service_group, tag, payment, agent, agent_software, license,
                      operating_system, billing)

app.blueprint(api)

app.register_middleware(cors.add_cors_headers, "response")


@app.get("/")
async def index(request):
    return redirect("/docs")


@app.post("/api/setup")
@protected({UserRole.Role.ADMIN})
async def db_setup(request, user: User):
    if request.json is not None:
        services = request.json.get("services", False)
        service_offerings = request.json.get("service_offerings", False)
        service_plans = request.json.get("service_plans", False)
        await set_up_demo_db(user, services=services,
                             service_offerings=service_offerings,
                             service_plans=service_plans)
        return text("Created.", status=201)
    return HTTPResponse(status=204)


async def _get_svc_and_tag_from_request(request):
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


async def create_user(email: str, first: str | None, last: str | None, password: str,
                      role: UserRole.Role = None) -> User:
    if not test_email(email):
        raise BadRequest("Invalid email.")
    user = await User.get_or_none(email=email)
    if user is None:
        salt = generate_secret()
        billing_cycle = await BillingCycle.get_or_none(type=BillingCycleType.INDIVIDUAL)
        if billing_cycle is None:
            billing_cycle = await BillingCycle.create(type=BillingCycleType.INDIVIDUAL,
                                                      description="Individual services")
        user = await User.create(
            email=email,
            first_name=first,
            last_name=last,
            password=hash_password(password, salt),
            salt=salt,
            billing_cycle=billing_cycle
        )
    if role is None:
        role = UserRole.Role.USER
    existing_role = await UserRole.get_or_none(user=user, role=role)
    if existing_role is None:
        await UserRole.create(
            user=user,
            role=role
        )
    if STRIPE_API_KEY is not None:
        results = await stripe.Customer.search_async(query=f"email:'{email}'")
        if len(results.data) > 0:
            id = results.data[0].stripe_id
        else:
            customer = await stripe.Customer.create_async(
                email=email,
                name=first + " " + last
            )
            id = customer.id
        user.stripe_id = id
        await user.save()
    app.add_task(set_up_stripe_customer(user))
    return await user.json()


async def set_up_demo_db(user: User, services: bool = False,
                         service_offerings: bool = False, service_plans: bool = False):
    if services:
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
        os_deb = await OperatingSystem.create(
            name="Debian",
            system_name="debian"
        )
        os_win = await OperatingSystem.create(
            name="Windows",
            system_name="windows"
        )
        os_mac = await OperatingSystem.create(
            name="macOS",
            system_name="macOS"
        )
        pm_apt = await PackageManager.create(
            name="apt (debian stable)"
        )
        pm_brew = await PackageManager.create(
            name="brew"
        )
        pm_choco = await PackageManager.create(
            name="choco"
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
        v_docker_1 = await PackageManagerAvailableVersion.create(
            service=svc_docker,
            operating_system=os_win,
            package_manager=pm_choco,
            version="1.2.5",
            latest=True
        )
        v_docker_2 = await PackageManagerAvailableVersion.create(
            service=svc_docker,
            operating_system=os_deb,
            package_manager=pm_apt,
            version="1.2.5",
            latest=True
        )
        v_docker_3 = await PackageManagerAvailableVersion.create(
            service=svc_docker,
            operating_system=os_mac,
            package_manager=pm_brew,
            version="1.2.5",
            latest=True
        )
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
        await svc_nginx.save()
        v_nginx_1 = await PackageManagerAvailableVersion.create(
            service=svc_nginx,
            operating_system=os_deb,
            package_manager=pm_apt,
            version="1.22.1-9",
            latest=True
        )
        v_nginx_2 = await PackageManagerAvailableVersion.create(
            service=svc_nginx,
            operating_system=os_mac,
            package_manager=pm_brew,
            version="1.25.5",
            latest=True
        )
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
        await svc_nextcloud.save()
        if service_offerings:
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
            off_nginx_year = await ServiceOffering.create(
                service=svc_nginx,
                name="year",
                price=89.99,
                duration_days=360
            )
            off_nginx_quarter = await ServiceOffering.create(
                service=svc_nginx,
                name="quarter",
                price=29.99,
                duration_days=90
            )
            if service_plans:
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
                plan_nginx = await ServicePlan.create(
                    user=user,
                    service_offering=off_nginx_quarter,
                    start_date=datetime.datetime.now() - datetime.timedelta(days=45)
                )


@app.listener("before_server_start")
async def test_user(request):
    options.setup_options(app, request)
    await create_user("test@example.com", "Test", "user", "test", None)
    await create_user("admin@example.com", "Admin", "Istrator", "admin", UserRole.Role.ADMIN)


async def get_latest_version(service: Service, os: OperatingSystem) -> str | None:
    query = (
        Service
        .filter(
            id=service.id,
            available_versions__latest=True,
            available_versions__operating_system=os
        )
        .annotate(
            version=Coalesce("available_versions__version")
        )
        .values("version")
    )
    results = await query
    if results:
        return results[0]["version"]
    return None


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


@app.post("/api/auth")
async def auth(request: Request):
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    if email is None or password is None:
        raise BadRequest("Missing email or password parameters.")
    user = await User.get_or_none(email=email)
    if user is None:
        raise NotFound("User not found.")
    if not verify_password(password, user.password, user.salt):
        raise Unauthorized()
    return HTTPResponse(status=204)


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
    if user.stripe_id != None:
        try:
            customer = await stripe.Customer.retrieve_async(user.stripe_id)
            methods = customer.list_payment_methods()
            has_payment_method = len(methods) > 0
        except stripe.InvalidRequestError:  # Customer not found in Stripe
            has_payment_method = False
    else:
        has_payment_method = False
    return json(
        {
            **await user.to_dict(),
            "roles": [await role.to_dict() for role in await user.roles],
            "connected_to_billing_provider": user.stripe_id != None,
            "has_payment_method": has_payment_method
        }
    )


@user.post("/")
async def create_new_user(request):
    try:
        return await create_user(
            request.json["email"],
            request.json.get("first_name"),
            request.json.get("last_name"),
            request.json["password"]
        )
    except KeyError:
        raise BadRequest("Missing name, email, or password.")
    except IntegrityError:
        return HTTPResponse("Email already taken.", 409)


@user.patch("/")
@protected()
async def update_user(request, user: User):
    first_name = request.json.get("first_name", None)
    last_name = request.json.get("last_name", None)
    email = request.json.get("email", None)
    password = request.json.get("password")
    if password is not None:
        user.password = hash_password(password, user.salt)
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        user.email = email
        # TODO: Email verification
    await user.save()
    return HTTPResponse(status=204)


@user.delete("/")
@protected()
@delete_endpoint(User)
async def delete_user(request, deleted_user: User, user):
    await stripe.Customer.delete_async(deleted_user.stripe_id)
    # TODO: Make, so that admins can delete anyone, but everyone themselves


@service.get("/")
@protected()
@get_endpoint(Service)
@openapi.summary("Get all services")
@openapi.description(
    "By default, returns a JSON list of all services including tags. If a `id` is specified in the query args, only that specific service will be returned (provided it is found).")
# @openapi.response(200, {"application/json": Union[List[Service], Service]})
async def get_services(request, services, user):
    async def expand(svc: Service) -> dict:
        query = (
            Service
            .filter(id=svc.id)
            .annotate(
                os_id=Coalesce("available_versions__operating_system__id")
                # just so this field is resolved, as pure strings aren't supported
            )
            .filter(os_id__isnull=False)
            .values("os_id")
        )
        results = await query
        oses = [os.get("os_id") for os in results]

        return {
            **await svc.to_dict(),
            "tags": [await tag.to_dict() for tag in await svc.tags],
            "offerings": [await offering.to_dict() for offering in
                          await ServiceOffering.filter(service=svc).all()],
            "operating_systems": oses,
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
    filter_data = {
        "user": user,
    }
    id = request.args.get("id")
    if id is not None:
        filter_data["id"] = id
    plans = await ServicePlan.filter(Q(canceled_by_user=False) | Q(
        canceled_at__gt=datetime.datetime.now() - datetime.timedelta(days=1.0)),
                                     **filter_data).all()
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
@requires_payment_details(stripe)
async def create_service_plan(request, user, methods):
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
        # don't set up new stripe subscription directly to be compatible with future billing modes
        await app.add_task(evaluate_billing_for_user(user))
        return await plan.json()
    except (KeyError, AttributeError):
        raise BadRequest("Missing parameters. Required: service_offering, and user.")


@service_plan.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(ServicePlan)
async def update_service_plan(request, plan, user):
    pass


@service_plan.delete("/cancel")
@protected()
async def cancel_service_plan(request, user):
    id = request.args.get("id")
    plan = await ServicePlan.get_or_none(id=id)
    if plan is None:
        raise NotFound("Service plan not found.")
    plan_user_id = (await plan.user).id
    if plan_user_id != user.id:
        raise BadRequest("You can only cancel your own service plans.")
    await cancel_service_plan_for_user(plan)
    return await plan.json()


async def cancel_service_plan_for_user(plan: ServicePlan):
    plan.canceled_by_user = True
    if plan.canceled_at is None:
        plan.canceled_at = datetime.datetime.now()
    await plan.save()
    offering: ServiceOffering = await plan.service_offering
    service: Service = await offering.service
    await plan.fetch_related("agent_softwares")
    for software in plan.agent_softwares:
        agent: Agent = await software.agent
        await perform_software_uninstallation(agent, service, software)
    app.add_task(evaluate_billing_for_user(plan.user))


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


@service.post("/tag")
@protected({UserRole.Role.ADMIN})
async def associate_tag_with_service(request, user):
    svc, tag = await _get_svc_and_tag_from_request(request)
    await svc.tags.add(tag)
    return HTTPResponse(status=204)


@service.delete("/tag")
@protected({UserRole.Role.ADMIN})
async def deassociate_tag_with_service(request, user):
    svc, tag = await _get_svc_and_tag_from_request(request)
    await svc.tags.remove(tag)
    return HTTPResponse(status=204)


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
        operating_sys = await agent.operating_system
        os_name = operating_sys.system_name if operating_sys is not None else None
        return json(
            {
                "name": agent.name,
                "operating_system": os_name
            }
        )
    except KeyError:
        raise BadRequest("Expected `id` query param.")


@agent.patch("/init")
async def agent_init(request):
    try:
        id = request.json["id"]
        new_name = request.json.get("name")
        os = request.json.get("operating_system")
        agent = await Agent.get_or_none(id=id)
        if agent is None:
            raise NotFound("Agent not found.")
        operating_system = await OperatingSystem.get_or_none(system_name=os)
        if operating_system is None:
            raise NotFound(f"Operating system '{os}' not found. Please specify valid system_name.")
        if new_name is not None:
            agent.name = new_name
        agent.operating_system = operating_system
        await agent.save()
        return json({"name": new_name or agent.name, "operating_system": os})
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
                "latest_version": await get_latest_version(service, await agent.operating_system),
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
        softwares = [AgentSoftware(agent=agent, service_plan=plan, installing=True) for agent in
                     agents]
        await AgentSoftware.bulk_create(softwares)
        for (software, agent) in zip(softwares, agents):
            await send_agent_software_notification(AgentSoftwareAgentCommand.INSTALL, agent,
                                                   service, software)
        return HTTPResponse(status=201)
    except KeyError:
        raise missing_params
    except IntegrityError:
        raise BadRequest("Service plan is already installed on at least one agent.")


@agent_software.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(AgentSoftware)
async def patch_agent_software(request, software, user):
    pass


@agent_software.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(AgentSoftware)
async def delete_agent_software(request, software, user):
    pass


@agent_software.post("/update")
@protected()
async def update_agent_software(request, user):
    id = request.args.get("id")
    software = await AgentSoftware.get_or_none(id=id)
    if software is None:
        raise NotFound("AgentSoftware not found.")
    agent = await software.agent
    service = await (await (await software.service_plan).service_offering).service
    await send_agent_software_notification(AgentSoftwareAgentCommand.INSTALL, agent, service,
                                           software)
    software.installing = True
    await software.save()
    return HTTPResponse(status=201)


@agent_software.delete("/uninstall")
@protected()
async def uninstall_agent_software(request, user):
    id = request.args.get("id")
    software = await AgentSoftware.get_or_none(id=id)
    if software is None:
        raise NotFound("AgentSoftware not found.")
    agent: Agent = await software.agent
    agent_id = (await agent.user).id
    if str(agent_id) != str(user.id):
        raise BadRequest("You can only uninstall software on your own agents.")
    service: Service = await (await (await software.service_plan).service_offering).service
    await perform_software_uninstallation(agent, service, software)
    return HTTPResponse(status=204)


async def perform_software_uninstallation(agent: Agent, service: Service, software: AgentSoftware):
    await send_agent_software_notification(AgentSoftwareAgentCommand.UNINSTALL, agent, service,
                                           software)
    software.uninstalling = True
    await software.save()


class AgentSoftwareAgentCommand(enum.StrEnum):
    INSTALL = "install"
    UNINSTALL = "uninstall"


async def send_agent_software_notification(command: AgentSoftwareAgentCommand, agent: Agent,
                                           service: Service,
                                           software: AgentSoftware):
    version = await get_latest_version(service, await agent.operating_system)
    match command:
        case AgentSoftwareAgentCommand.INSTALL:
            version_info = f" v{version}"
        case AgentSoftwareAgentCommand.UNINSTALL:
            version_info = ""
        case _:
            raise ValueError("Unexpected AgentSoftwareAgentCommand.")
    message = f"{command.value} {service.system_name} {software.id}{version_info}"
    queue_websocket_msg(str(agent.id), message)


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


@license.get("/")
@protected()
@get_endpoint(License)
async def get_licenses(request, user, licenses):
    pass


@operating_system.get("")
@protected()
@get_endpoint(OperatingSystem)
async def get_operating_systems(request, user, operating_systems):
    pass


@agent.get("/count")
@protected()
async def get_own_agent_count(request, user: User):
    count = await Agent.filter(user=user).count()
    return json({"count": count})


@payment_intent.post("/")
@requires_stripe_customer(stripe)
async def create_payment_intent(request, user, customer):
    intent = await stripe.PaymentIntent.create_async(
        amount=1200,
        currency="eur"
    )
    return json({"client_secret": intent.client_secret})


@payment_method.post("/attach")
@requires_stripe_customer(stripe)
async def attach_payment_method_to_customer(request, user, customer: stripe.Customer):
    try:
        method_id = request.json["method_id"]
        await stripe.PaymentMethod.attach_async(method_id, customer=customer.id)
        await stripe.Customer.modify_async(customer.id,
                                           invoice_settings={"default_payment_method": method_id})
        return HTTPResponse(status=204)
    except (TypeError, KeyError) as e:
        raise BadRequest("Expected method_id for the payment method to attach")


@app.get("/api/billing/cycle")
@protected()
@get_endpoint(BillingCycle)
async def get_billing_cycles(request, user, cycles):
    pass


@app.post("/api/billing/setup")
@protected({UserRole.Role.ADMIN})
async def set_up_billing(request, user):
    app.add_task(set_up_stripe_products())
    return text("Accepted.", status=202)


@app.post("/api/billing/maintenance")
@protected({UserRole.Role.ADMIN})
async def billing_maintenance(request, user):
    app.add_task(perform_billing_maintenance())
    return text("Accepted.", status=202)


async def perform_billing_maintenance():
    logger.info("Performing billing maintenance...")
    await set_up_stripe_products()
    users = await User.all()
    for user in users:
        await evaluate_billing_for_user(user)
    logger.info("Billing maintenance complete")


async def set_up_stripe_products():
    services = await Service.all()
    for service in services:
        product, service = await assert_stripe_product_for_service(service)
        await assert_stripe_prices_for_service(product, service)


async def assert_stripe_product_for_service(service: Service) -> Tuple[stripe.Product, Service]:
    async def create():
        product = await stripe.Product.create_async(
            name=service.name,
            description=service.description,
        )
        service.stripe_product_id = product.id
        await service.save()
        return product, service

    if service.stripe_product_id is not None:
        try:
            product = await stripe.Product.retrieve_async(service.stripe_product_id)
        except stripe.InvalidRequestError as e:
            if "No such product" in str(e):
                return await create()
            raise e
        update_data = {}
        if product.name != service.name:
            update_data["name"] = service.name
        if product.description != service.description:
            update_data["description"] = service.description
        if len(update_data) > 0:
            await stripe.Product.modify_async(product.id, **update_data)
        return product, service
    else:
        return await create()


async def assert_stripe_prices_for_service(product: stripe.Product, service: Service):
    offerings = await ServiceOffering.filter(service=service).all()
    prices = await stripe.Price.search_async(query=f"product:'{product.id}'")
    for offering in offerings:
        potential_prices = list(
            filter(lambda price: str(price.id) == str(offering.stripe_price_id), prices.data))
        prices_length = len(potential_prices)
        if offering.stripe_price_id is not None and prices_length > 0:
            assert prices_length == 1, "Multiple prices associated with the same ServiceOffering."
            price: stripe.Price = potential_prices[0]
            update_data = {}
            target_price = int(offering.price * 100)
            if price.unit_amount != target_price:
                update_data["unit_amount"] = target_price
            if len(update_data) > 0:
                await stripe.Price.modify_async(price.id, **update_data)
        else:
            recurring_data = get_stripe_recurring_object_for_service_offering(offering)
            price = await stripe.Price.create_async(
                product=product.id,
                currency="eur",
                unit_amount=int(offering.price * 100),
                recurring=recurring_data
            )
            offering.stripe_price_id = price.id
            await offering.save()


def get_stripe_recurring_object_for_service_offering(offering: ServiceOffering) -> Dict[
    str, str | int]:
    match offering.name:
        case "month":
            interval = "month"
            interval_count = 1
        case "quarter":
            interval = "month"
            interval_count = 3
        case "year":
            interval = "year"
            interval_count = 1
        case _:
            raise ValueError(
                f"Offering {offering.id} has invalid name for stripe sync: {offering.name}")
    return {"interval": interval,
            "interval_count": interval_count}


async def evaluate_billing_for_user(user: User):
    cycle: BillingCycle = await user.billing_cycle
    match cycle.type:
        case BillingCycleType.INDIVIDUAL:
            await set_up_billing_individual_services_for_user(user)
        case _:
            raise ValueError("Unexpected BillingCycleType")


async def set_up_billing_individual_services_for_user(user: User):
    await set_up_stripe_customer(user)
    service_plans = await ServicePlan.filter(user=user).all()
    for plan in service_plans:
        if plan.stripe_subscription_id is None:
            await create_stripe_subscription_for_plan(user, plan)
        else:
            await handle_stripe_subscription_status(plan)


async def set_up_stripe_customer(user: User) -> User:
    async def create() -> User:
        customer = await stripe.Customer.create_async(
            email=user.email,
            name=user.first_name + " " + user.last_name
        )
        user.stripe_id = customer.id
        await user.save()
        return user

    if user.stripe_id is None:
        return await create()
    try:
        customer = await stripe.Customer.retrieve_async(user.stripe_id)
        return user
    except stripe.InvalidRequestError:
        return await create()


async def handle_stripe_subscription_status(plan: ServicePlan):
    assert plan.stripe_subscription_id is not None
    try:
        subscription = await stripe.Subscription.retrieve_async(plan.stripe_subscription_id)
        if plan.canceled_by_user and subscription.cancel_at is None:
            subscription = await stripe.Subscription.cancel_async(subscription.id)
        if subscription.status in ["canceled", "unpaid", "incomplete_expired"]:
            if not plan.canceled_by_user:
                await cancel_service_plan_for_user(plan)
    except stripe.InvalidRequestError as e:
        if "No such subscription" in str(e):
            return
        raise e


async def get_stripe_price_by_id(product_id: str, price_id: str) -> stripe.Price:
    prices = await stripe.Price.search_async(query=f"product:'{product_id}'")
    potential_prices = list(filter(lambda price: price.id == str(price_id), prices.data))
    assert len(
        potential_prices) == 1, f"Expected exactly one stripe price with id {price_id} for product {product_id}. Got {potential_prices}."
    return potential_prices[0]


async def create_stripe_subscription_for_plan(user: User, service_plan: ServicePlan):
    assert user.stripe_id is not None, f"User {user.id} does not have a stripe ID associated."
    offering: ServiceOffering = await service_plan.service_offering
    service: Service = await offering.service
    if offering.stripe_price_id is None or service.stripe_product_id is None:
        await set_up_stripe_products()
        await offering.refresh_from_db()
        await service.refresh_from_db()
    price = await get_stripe_price_by_id(service.stripe_product_id, offering.stripe_price_id)
    customer = user.stripe_id
    price_id = price.id
    subscription = await stripe.Subscription.create_async(
        customer=customer,
        items=[{"price": price_id}]
    )
    service_plan.stripe_subscription_id = subscription.id
    await service_plan.save()


# TODO: Add endpoints for creating, updating and deleting licenses + OSes
# Queue for messages pending to be sent to respective agents

app.add_task(run_websocket_server(app))
app.add_task(run_websocket_handler_queue_worker())

if __name__ == "__main__":
    app.run("0.0.0.0")
