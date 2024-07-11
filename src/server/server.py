import asyncio
import datetime
import os
import signal
from typing import Set, Tuple, Dict, Iterable, Any, List

import jwt
import jwt.exceptions
import stripe
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sanic import Sanic, redirect, Request, text, Blueprint, json, HTTPResponse
from sanic.handlers import ErrorHandler
from sanic.log import logger
from sanic_openapi import openapi
from tortoise.contrib.sanic import register_tortoise
from tortoise.exceptions import IntegrityError
from tortoise.expressions import F
from tortoise.functions import Coalesce
from tortoise.transactions import in_transaction

import compolvo.email
from compolvo import cors
from compolvo import notify
from compolvo import options
from compolvo.decorators import patch_endpoint, delete_endpoint, get_endpoint, protected, \
    requires_payment_details, requires_stripe_customer, requires_verified_email, \
    bulk_delete_endpoint
from compolvo.models import Agent, AgentSoftware, Serializable, PackageManager, \
    PackageManagerAvailableVersion, \
    BillingCycle, BillingCycleType, ServerStatus, ServiceUserLicenseType, \
    ServiceUserLicenseTypeAttribute, ServiceUserLicenseTypeAttributeType, UserLicense
from compolvo.models import Service, OperatingSystem, Tag, UserRole, User, License, \
    ServiceOffering, ServicePlan, ServiceUserLicenseTypeLevel
from compolvo.notify import Event, Recipient, EventType, SubscriberType, cancel_event
from compolvo.utils import verify_password, check_token, Unauthorized, BadRequest, NotFound, \
    hash_password, generate_secret, test_email, \
    user_has_roles

HTTP_HEADER_DATE_FORMAT = "%a, %d %b %Y %H:%M:%S GMT"

app = Sanic("compolvo")

app.config.SERVER_NAME = os.environ["SERVER_NAME"]
app.config.FALLBACK_ERROR_FORMAT = "text"
app.config.SECRET_KEY = os.environ["COMPOLVO_SECRET_KEY"]
app.config.SESSION_TIMEOUT = 60 * 30

SERVER_ID = os.environ["SERVER_ID"]
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
if STRIPE_API_KEY == "":  # e.g. when docker compose doesn't find the key in the .env file
    STRIPE_API_KEY = None
if STRIPE_API_KEY is not None:
    stripe.api_key = STRIPE_API_KEY

db_hostname = os.environ[
    "DB_HOSTNAME"]
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
available_version = Blueprint("version", url_prefix="/api/service/version")
service_plan = Blueprint("service_plan", url_prefix="/api/service/plan")
tag = Blueprint("tag", url_prefix="/api/tag")
service_group = Blueprint.group(service, service_offering, available_version, service_plan)
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


class CustomErrorHandler(ErrorHandler):
    def default(self, request: Request, exception: Exception) -> HTTPResponse:
        status = getattr(exception, "status", 500)
        if not 400 <= status <= 499:
            logger.exception(exception)
        return text(str(exception), status=status)


app.register_middleware(cors.add_cors_headers, "response")
app.error_handler = CustomErrorHandler()


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


@app.post("/api/license/setup")
@protected({UserRole.Role.ADMIN})
async def setup_license(request, user: User):
    licenses = await UserLicense.filter(user=user).all()
    agents = await Agent.filter(user=user).all()
    if await UserLicense.filter().count() == 0:
        license_type = await ServiceUserLicenseType.filter(name="Pro").first()
        licenses = [await UserLicense.create(start_date=datetime.datetime.now(tz=datetime.timezone.utc), license_key="Hello, world!", license_type=license_type, user=user)]
    for license in licenses:
        for agent in agents:
            await send_agent_set_up_license_notification(agent, license)
    return HTTPResponse(status=202)

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
                      role: UserRole.Role = None, skip: bool = False,
                      email_verification: bool = True) -> User:
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
    elif not skip:
        raise IntegrityError("Email already taken.")
    if email_verification:
        if not user.email_verified:
            await compolvo.email.send_user_email_verification_mail(app, user)
    else:
        user.email_verified = True
        await user.save()
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
                name=first or "" + " " + last or ""
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
        os_deb = await OperatingSystem.filter(system_name="debian").first()
        if os_deb is None:
            os_deb = await OperatingSystem.create(
                name="Debian",
                system_name="debian"
            )
        os_win = await OperatingSystem.filter(system_name="windows").first()
        if os_win is None:
            os_win = await OperatingSystem.create(
                name="Windows",
                system_name="windows"
            )
        os_mac = await OperatingSystem.filter(system_name="macOS").first()
        if os_mac is None:
            os_mac = await OperatingSystem.create(
                name="macOS",
                system_name="macOS"
            )
        os_man = await OperatingSystem.filter(system_name="manjaro").first()
        if os_man is None:
            os_man = await OperatingSystem.create(
                name="Manjaro",
                system_name="manjaro"
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
        pm_pacman = await PackageManager.create(
            name="pacman"
        )
        svc_jq = await Service.create(
            system_name="jq",
            name="jq",
            license=lic_mit,
            latest_version="1.7.1",
            hidden=True
        )
        vs_jq = []
        for os, pm in [(os_man, pm_apt), (os_deb, pm_apt), (os_mac, pm_brew), (os_win, pm_choco)]:
            vs_jq.append(await PackageManagerAvailableVersion.create(
                service=svc_jq,
                version="1.7.1",
                latest=True,
                operating_system=os,
                package_manager=pm
            ))
        svc_docker = await Service.create(
            system_name="docker-desktop",
            name="Docker Desktop",
            short_description="Docker Desktop is an integrated development environment (IDE) that allows developers to easily create, manage, and operate Docker containers on both Mac and Windows systems. The application offers a user-friendly interface that facilitates the seamless transition from code to container, incorporating advanced features like container orchestration, network management, and security settings.",
            description="Docker Desktop is a comprehensive, professional development environment designed to simplify developers' work with Docker technology. It provides a robust, user-friendly platform for building, testing, and deploying applications in Docker containers on macOS and Windows operating systems. Docker Desktop enables developers to develop their applications in an isolated environment, ensuring consistency between different development settings and the production environment. The platform supports both Linux and Windows containers and offers flexible tools for network design, volume management, and security. Docker Desktop seamlessly integrates into existing development workflows and offers support for popular IDEs and development tools. It also includes advanced features like an integrated Kubernetes cluster, allowing developers to test their applications in an orchestrated environment. The ability to manage containers directly from the desktop enhances efficiency and enables faster iteration and debugging. Moreover, Docker Desktop provides a secure environment for application development. With built-in security features like automatic updates and easily configurable network settings, Docker Desktop helps developers follow security best practices and minimizes vulnerability to security threats. For businesses seeking an efficient, reliable, and scalable solution for containerizing their applications, Docker Desktop is an excellent choice. It promotes a collaborative development environment and provides developers with the tools needed to effectively develop and manage modern, container-based applications. Docker Desktop thus serves as a bridge between development and production environments, ensuring that applications operate smoothly and without environmental dependencies at every stage of the development cycle.",
            license=lic_mit,
            download_count=100,
            image="",
            latest_version="1.2.5"
        )
        await svc_docker.tags.add(
            tag_developer,
            tag_enthusiast
        )
        l_docker_personal = await ServiceUserLicenseType.create(service=svc_docker, name="Personal",
                                                                level=ServiceUserLicenseTypeLevel.SUBSCRIPTION, setup_script_name="docker-license-setup.sh")
        l_docker_pro = await ServiceUserLicenseType.create(service=svc_docker, name="Pro",
                                                           level=ServiceUserLicenseTypeLevel.SUBSCRIPTION, setup_script_name="docker-license-setup.sh")
        l_docker_team = await ServiceUserLicenseType.create(service=svc_docker, name="Team",
                                                            level=ServiceUserLicenseTypeLevel.PER_USER, setup_script_name="docker-license-setup.sh")
        l_docker_business = await ServiceUserLicenseType.create(service=svc_docker, name="Business",
                                                                level=ServiceUserLicenseTypeLevel.PER_USER, setup_script_name="docker-license-setup.sh")
        l_docker_personal_map = {"commercial_use": False, "image_pulls": "200/6h",
                                 "docker_debug": False, "rbac": False, "sso": False}
        l_docker_pro_map = {"commercial_use": True, "image_pulls": "5000/d", "docker_debug": True,
                            "rbac": False, "sso": False}
        l_docker_team_map = {"commercial_use": True, "image_pulls": "5000/d", "docker_debug": True,
                             "rbac": True, "sso": False}
        l_docker_business_map = {"commercial_use": True, "image_pulls": "5000/d",
                                 "docker_debug": True, "rbac": True, "sso": True}
        for license_type, map in [(l_docker_personal, l_docker_personal_map),
                                  (l_docker_pro, l_docker_pro_map),
                                  (l_docker_team, l_docker_team_map),
                                  (l_docker_business, l_docker_business_map)]:
            for key, value in map.items():
                attr_type = ServiceUserLicenseTypeAttributeType.STRING
                if type(value) == bool:
                    attr_type = ServiceUserLicenseTypeAttributeType.BOOLEAN
                await ServiceUserLicenseTypeAttribute.create(
                    license_type=license_type,
                    attribute_type=attr_type,
                    key=key,
                    value=value,
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
        await v_docker_1.dependencies.add(vs_jq[3])
        await v_docker_2.dependencies.add(vs_jq[1])
        await v_docker_3.dependencies.add(vs_jq[2])
        svc_nginx = await Service.create(
            system_name="nginx",
            name="Nginx",
            short_description="Nginx is a high-performance web server, reverse proxy, and email (IMAP/POP3) proxy, known for its stability, rich feature set, simple configuration, and low resource consumption. Originally designed to solve the C10K problem, it efficiently serves a large number of simultaneous connections.",
            description='Nginx (pronounced "engine-x") is an open-source web server software designed to provide a balance of high performance, scalability, and low resource usage. It serves as a web server, as well as a reverse proxy and an email proxy for IMAP, POP3, and SMTP. Nginx is renowned for its speed and efficiency, particularly in environments where the scalability and performance of web applications are critical. It is commonly used to manage static content, load balancing, and for caching in a distributed environment. The architecture of Nginx is event-driven and asynchronous, which makes it particularly efficient at handling multiple connections simultaneously. This design allows it to scale vertically on modern hardware with minimal resource overhead. Nginx’s performance advantages become especially apparent in serving static content and in handling simultaneous connections by not tying up resources to keep connections open, which in contrast, is a common issue in traditional web servers like Apache. Nginx also functions effectively as a reverse proxy server, providing security, additional layers of functionality, and performance enhancements to an application stack. For instance, Nginx can manage SSL/TLS termination, WebSocket, and HTTP/2 connections, enhancing the capability of the underlying server without additional load. Its configuration system is straightforward, allowing fine-grained control over its operational parameters with minimal configuration overhead. For businesses and developers looking for a reliable and robust server solution, Nginx offers a compelling choice due to its ability to handle high traffic loads and its flexibility in integrating into existing technology stacks. Whether deploying a simple static website or a complex web application requiring robust security and high availability, Nginx provides a performance-optimized solution that has been adopted by some of the largest sites on the Internet, including Netflix, Airbnb, and many others.',
            license=lic_mit,
            download_count=200,
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
        v_nginx_3 = await PackageManagerAvailableVersion.create(
            service=svc_nginx,
            operating_system=os_man,
            package_manager=pm_pacman,
            version="1.25.5",
            latest=True
        )
        await v_nginx_1.dependencies.add(vs_jq[1])  # Add pj as dependency just for demo purposes
        await v_nginx_2.dependencies.add(vs_jq[2])
        await v_nginx_3.dependencies.add(vs_jq[0])
        svc_git = await Service.create(
            system_name="git",
            name="Git",
            short_description="Git is a distributed version control system that enables developers to track and manage changes to code projects efficiently. It facilitates collaborative coding by allowing multiple developers to work on different parts of a project simultaneously without interfering with each other's work. Git is known for its robust branching and merging capabilities, which make it an essential tool for modern software development.",
            description="Git is a powerful, distributed version control system that is pivotal in managing modern software development projects. It allows individual developers and large teams alike to track every single change made to the codebase, ensuring comprehensive version control and historical traceability. By decentralizing the repository management, Git enables team members to work on local copies of the project, which can be synchronized with the main repository as needed. One of Git's hallmark features is its sophisticated branching and merging mechanics. Developers can create branches to experiment with new features or fixes without affecting the main codebase, making it safe to explore innovative solutions. Once the new code is ready and tested, it can be seamlessly merged back into the main branch, maintaining a clean and stable production codebase. Git also excels in performance. Its efficient handling of large repositories and fast operation speeds make it suitable for projects of all sizes, from small startups to large-scale enterprise systems. Additionally, Git's strong support for non-linear development allows for flexible integration of various workflows, such as feature branches, forks, and pull requests, enhancing collaborative efforts and peer review processes. Moreover, Git integrates well with various development tools and platforms, from local IDEs to remote collaboration platforms like GitHub and GitLab. This integration facilitates a smooth workflow for continuous integration (CI) and continuous deployment (CD), crucial for automating the testing and deployment of code changes. For organizations looking to maintain a high standard of code integrity and collaboration, Git offers a reliable, scalable, and efficient solution. It not only helps developers to manage changes effectively but also supports a culture of transparency and collaboration, making it indispensable in the realm of software development. Git's flexibility and power ensure that it remains at the forefront of version control technology, adapting to the evolving needs of developers and projects worldwide.",
            license=lic_mit,
            download_count=300,
            image=""
        )
        v_git_1 = await PackageManagerAvailableVersion.create(
            service=svc_git,
            operating_system=os_win,
            package_manager=pm_choco,
            version="1.2.5",
            latest=True
        )
        await svc_git.tags.add(
            tag_developer
        )
        await svc_git.save()
        svc_nextcloud = await Service.create(
            system_name="nextcloud",
            name="Nextcloud",
            short_description="Nextcloud is an open-source software suite that provides a secure and decentralized platform for file storage, collaboration, and communication. It allows users and organizations to host their own cloud storage service, managing files, contacts, calendars, and more, with full control over their data and privacy.",
            description="Nextcloud is a robust, open-source software solution designed to offer businesses and individuals alike the ability to operate their own private cloud storage and collaboration platform. As a self-hosted system, it empowers users to maintain complete control over their data, ensuring privacy and security in a world where these are increasingly at a premium. Nextcloud facilitates file sharing, calendar and contact management, task scheduling, and real-time document collaboration, all within a user-friendly interface accessible via web or mobile apps. A standout feature of Nextcloud is its extensibility, supported by a vibrant community of developers who contribute to a growing library of apps and plugins. These extensions can transform the core Nextcloud installation into a more customized and versatile tool, integrating features such as mail handling, video conferencing, and office suite tools. This modularity makes it an ideal solution for organizations looking to adapt the platform to their specific operational needs. Nextcloud also excels in providing enterprise-grade security. With features like end-to-end encryption, two-factor authentication, and easy-to-manage user permissions, it gives administrators the tools they need to secure data against unauthorized access. Furthermore, its compliance with major privacy standards, such as GDPR, makes it suitable for organizations needing to adhere to strict data protection regulations. For teams and organizations that prioritize data sovereignty and collaborative flexibility, Nextcloud offers a scalable and reliable platform. It supports a broad range of deployment scenarios, from small teams looking for file sharing solutions to large enterprises needing comprehensive collaboration suites. Nextcloud’s commitment to open-source principles and its proactive approach to security and privacy make it a preferred choice for those seeking an alternative to commercial cloud storage providers.",
            license=lic_mit,
            download_count=400,
            retrieval_method=Service.RetrievalMethod.COMMAND,
            retrieval_data='{"hello": "world"}',
            image=""
        )
        await svc_nextcloud.tags.add(
            tag_enthusiast
        )
        v_nextcloud_1 = await PackageManagerAvailableVersion.create(
            service=svc_nextcloud,
            operating_system=os_deb,
            package_manager=pm_apt,
            version="27.2.5",
            latest=True
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
            off_nginx_month = await ServiceOffering.create(
                service=svc_nginx,
                name="month",
                price=11.99,
                duration_days=30
            )
            off_nginx_2y = await ServiceOffering.create(
                service=svc_nginx,
                name="2-year",
                price=149.99,
                duration_days=360 * 2
            )
            off_nginx_3y = await ServiceOffering.create(
                service=svc_nginx,
                name="3-year",
                price=239.99,
                duration_days=360 * 3
            )
            if service_plans:
                plan_docker = await ServicePlan.create(
                    user=user,
                    service_offering=off_docker_month,
                    start_date=datetime.datetime.now(tz=datetime.timezone.utc)
                )
                plan_git = await ServicePlan.create(
                    user=user,
                    service_offering=off_git_month,
                    start_date=datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
                        days=7)
                )
                plan_nextcloud = await ServicePlan.create(
                    user=user,
                    service_offering=off_nextcloud_year,
                    start_date=datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
                        days=45)
                )
                plan_nginx = await ServicePlan.create(
                    user=user,
                    service_offering=off_nginx_quarter,
                    start_date=datetime.datetime.now(tz=datetime.timezone.utc) - datetime.timedelta(
                        days=45)
                )


@app.listener("before_server_start")
async def test_user(app):
    options.setup_options(app)
    compolvo.email.setup_smtp_server()
    await create_user("test@example.com", "Test", "user", "Test12345!", None, True, False)
    await create_user("admin@example.com", "Admin", "Istrator", "admin", UserRole.Role.ADMIN, True,
                      False)


@app.listener("after_server_start")
async def after_server_start(app):
    await update_server_status(running=True, billing_maintenance=False)


async def get_latest_version(service: Service,
                             os: OperatingSystem) -> PackageManagerAvailableVersion | None:
    return await PackageManagerAvailableVersion.filter(
        service=service,
        latest=True,
        operating_system=os
    ).first()


@app.get("/api/login")
async def login(request: Request):
    email = request.args.get("email", [None])
    password = request.args.get("password", None)
    if email is None or password is None:
        raise BadRequest("Missing email or password.")
    user = await User.get_or_none(email=email)
    if not user or not verify_password(password, user.password, user.salt):
        raise Unauthorized()
    expires = datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(
        seconds=app.config.SESSION_TIMEOUT)
    token = jwt.encode({"id": str(user.id), "expires": expires.strftime("%Y-%m-%dT%H:%M:%SZ")},
                       app.config.SECRET_KEY,
                       algorithm="HS256")
    headers = {"Set-Cookie": f"token={token}; Expires={expires.strftime(HTTP_HEADER_DATE_FORMAT)}"}
    redirect_url = request.args.get("redirect_url", request.url_for("index"))
    user.logged_in = True
    await user.save()
    return redirect(redirect_url, headers=headers)


@app.post("/api/auth")
async def auth(request: Request):
    id = request.json.get("id", None)
    password = request.json.get("password", None)
    if id is None or password is None:
        raise BadRequest("Missing id or password parameters.")
    user = await User.get_or_none(id=id)
    if user is None:
        raise NotFound("User not found.")
    if not user.logged_in or not verify_password(password, user.password, user.salt):
        raise Unauthorized()
    return HTTPResponse(status=204)


@app.get("/api/auth/token")
@protected()
async def get_token(request, user):
    token = request.cookies.get("token", None)
    await check_token(token, app.config.SECRET_KEY)
    decoded = jwt.decode(token, app.config.SECRET_KEY, algorithms=["HS256"])
    return json(decoded)


@app.get("/api/logout")
@protected()
async def logout(request: Request, user: User):
    user.logged_in = False
    await user.save()
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
    if STRIPE_API_KEY is not None and user.stripe_id is not None:
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
            "has_payment_method": has_payment_method,
            "is_admin": await user_has_roles(user, {UserRole.Role.ADMIN})
        }
    )


@user.get("/email/verify")
async def verify_user_email(request: Request):
    token = request.args.get("verification_token")
    if token is None:
        raise BadRequest("No verification token provided.")
    try:
        decoded = jwt.decode(token, app.config.SECRET_KEY, algorithms=["HS256"])
    except jwt.exceptions.DecodeError:
        raise BadRequest("Bad token provided.")
    user = await User.get_or_none(id=decoded["id"])
    if user is None:
        raise NotFound("User not found.")
    if user.email_verification_token != token:
        raise Unauthorized("Invalid verification token.")
    valid_until_str = decoded.get("valid_until")
    valid_until = datetime.datetime.fromisoformat(valid_until_str)
    if valid_until <= datetime.datetime.now(tz=datetime.timezone.utc):
        return redirect("/error/verification-token-expired")
    user.email_verified = True
    user.email_verification_token = None
    await user.save()
    return redirect("/home")


@user.post("/email/verify")
@protected()
async def send_user_email_verification_email(request, user: User):
    await compolvo.email.send_user_email_verification_mail(app, user)
    return HTTPResponse(status=204)


@user.post("/password/reset")
async def request_password_reset(request: Request):
    email = request.json.get("email")
    if email is None:
        raise BadRequest("Missing email.")
    await compolvo.email.send_user_password_reset_email(app, email)
    return HTTPResponse(status=204)


@user.patch("/password")
async def update_user_password_after_reset(request: Request):
    token = request.json.get("reset_token")
    if token is None:
        raise BadRequest("Missing reset_token.")
    try:
        decoded = jwt.decode(token, app.config.SECRET_KEY, algorithms=["HS256"])
    except jwt.exceptions.DecodeError:
        raise BadRequest("Invalid reset token.")
    user = await User.get_or_none(email=decoded["id"])
    if user is None:
        raise NotFound("User not found.")
    if user.password_reset_token != token:
        raise Unauthorized("Invalid reset token.")
    valid_until_str = decoded.get("valid_until")
    valid_until = datetime.datetime.fromisoformat(valid_until_str)
    if valid_until <= datetime.datetime.now(tz=datetime.timezone.utc):
        return redirect("/error/reset-token-expired")
    password = request.json.get("password")
    if password is None:
        raise BadRequest("Missing password.")
    user.password = hash_password(password, user.salt)
    user.password_reset_token = None
    user.logged_in = False
    await user.save()
    return HTTPResponse(status=204)


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
        user.logged_in = False
    if first_name is not None:
        user.first_name = first_name
    if last_name is not None:
        user.last_name = last_name
    if email is not None:
        user.email = email
        await compolvo.email.send_user_email_verification_mail(app, user)
        await change_user_email_in_stripe(user)
    await user.save()
    return HTTPResponse(status=204)


@user.delete("/admin")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(User)
async def delete_user(request, deleted_user: User, user):
    await stripe.Customer.delete_async(deleted_user.stripe_id)


@user.delete("/")
@protected()
async def delete_own_user(request, user: User):
    if user.stripe_id is not None:
        await stripe.Customer.delete_async(user.stripe_id)
    await user.delete()
    return HTTPResponse(status=204)


@service.get("/")
@get_endpoint(Service)
@openapi.summary("Get all services")
@openapi.description(
    "By default, returns a JSON list of all services including tags. If a `id` is specified in the query args, only that specific service will be returned (provided it is found).")
# @openapi.response(200, {"application/json": Union[List[Service], Service]})
async def get_services(request, services: List[Service] | Service):
    return await fetch_service_data_from_db(services)


async def fetch_service_data_from_db(services: List[Service] | Service, filter_hidden=True):
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
                          await ServiceOffering.filter(service=svc, active=True).order_by(
                              "duration_days").all()],
            "operating_systems": oses,
        }

    if isinstance(services, list):
        return json(
            [await expand(svc) for
             svc in
             services if not filter_hidden or not svc.hidden])
    return json(await expand(services))


@service.get("/admin")
@protected({UserRole.Role.ADMIN})
@get_endpoint(Service)
async def get_services_admin(request, services: List[Service] | Service, user):
    return await fetch_service_data_from_db(services, False)


@service.post("/")
@protected({UserRole.Role.ADMIN})
async def create_service(request, user):
    lic = request.json.get("license")
    license = await License.get_or_none(id=lic) if lic is not None else None
    service = await Service.create(
        system_name=request.json["system_name"],
        name=request.json["name"],
        description=request.json.get("description"),
        short_description=request.json.get("short_description"),
        license=license,
        download_count=request.json.get("download_count")
    )
    oses = request.json.get("operating_systems")
    if oses is not None:
        await service.operating_systems.add(
            *await OperatingSystem.filter(id__in=oses).all()
        )
    return await service.json()


@service.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(Service, True)
async def update_service(request: Request, svc: Service, user):
    # Don't shield against request.json being None as that's already handled by @patch_endpoint
    license = request.json.get("license")
    if license is not None:
        svc.license = await License.get_or_none(id=license)
        await svc.save()
    tags = request.json.get("tags")
    if tags is not None:
        async with in_transaction():
            await svc.tags.clear()
            new_tags = await Tag.filter(id__in=tags).all()
            await svc.tags.add(*new_tags)


@service.patch("/bulk")
@protected({UserRole.Role.ADMIN})
async def bulk_update_services(request: Request, user):
    ids = request.json.get("ids")
    if ids is None:
        raise BadRequest("Missing ids.")
    hidden = request.json.get("hidden")
    if hidden is not None:
        await Service.filter(id__in=ids).update(hidden=hidden)
    return HTTPResponse(status=204)


@service.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(Service)
async def delete_service(request, svc, user):
    pass


@service.delete("/bulk")
@bulk_delete_endpoint(Service, {UserRole.Role.ADMIN})
async def delete_services_bulk(request, service_ids, user):
    pass


async def get_service_offerings_from_request(request: Request,
                                             extra_filters: Dict[str, Any] = None):
    filters = extra_filters if extra_filters is not None else {}
    service = request.args.get("service")
    if service is not None:
        offerings = await ServiceOffering.filter(service__id=service, **filters).all()
    else:
        offerings = await ServiceOffering.filter(**filters).all()
    return await Serializable.list_json(offerings)


@service_offering.get("/")
@protected()
async def get_service_offerings(request: Request, user):
    return await get_service_offerings_from_request(request, {"active": True})


@service_offering.get("/admin")
@protected({UserRole.Role.ADMIN})
async def get_service_offerings_admin(request: Request, user):
    return await get_service_offerings_from_request(request)


@service_offering.patch("/bulk")
@protected({UserRole.Role.ADMIN})
async def bulk_update_service_offerings(request: Request, user):
    ids = request.json.get("ids")
    if ids is None:
        raise BadRequest("Missing ids.")
    active = request.json.get("active")
    if active is not None:
        await ServiceOffering.filter(id__in=ids).update(active=active)
    return HTTPResponse(status=204)


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
@patch_endpoint(ServiceOffering, True)
async def update_service_offering(request: Request, offering: ServiceOffering, user):
    service = request.json.get("service")
    if service is not None:
        offering.service = await Service.get_or_none(id=service)
        await offering.save()


@service_offering.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(ServiceOffering)
async def delete_service_offering(request, offering, user):
    pass


@service_offering.delete("/bulk")
@bulk_delete_endpoint(ServiceOffering, {UserRole.Role.ADMIN})
async def bulk_delete_service_offerings(request, offering_ids, user):
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
    plans = await ServicePlan.filter(canceled_by_user=False, **filter_data).all()
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


@service_plan.get("/count")
@protected()
async def get_service_plan_count(request, user):
    count = await ServicePlan.filter(user=user, canceled_by_user=False).count()
    return json({"count": count})


@service_plan.post("/")
@requires_verified_email()
@requires_payment_details(stripe)
async def create_service_plan(request, user, methods):
    try:
        service_offering_id = request.json["service_offering"]
        offering = await ServiceOffering.get_or_none(id=service_offering_id)
        if offering is None:
            raise NotFound("Specified service offering not found.")
        start_date = request.json.get("start_date")
        start = datetime.date.fromisoformat(
            start_date) if start_date is not None else datetime.datetime.now(
            tz=datetime.timezone.utc)
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
        plan.canceled_at = datetime.datetime.now(tz=datetime.timezone.utc)
    await plan.save()
    offering: ServiceOffering = await plan.service_offering
    service: Service = await offering.service
    await plan.fetch_related("agent_softwares")
    for software in plan.agent_softwares:
        agent: Agent = await software.agent
        await perform_software_uninstallation(agent, service, software)
        event = Event(EventType.AGENT_SOFTWARE_STATUS_UPDATE, Recipient(SubscriberType.SERVER),
                      {"software_id": str(software.id)})
        notify.queue(event)
    if STRIPE_API_KEY is not None:
        app.add_task(evaluate_billing_for_user(await plan.user))


@service_plan.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(ServicePlan)
async def delete_service_plan(request, plan, user):
    pass


@tag.get("/")
@get_endpoint(Tag)
async def get_tags(request, tags):
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


@tag.delete("/bulk")
@bulk_delete_endpoint(Tag, {UserRole.Role.ADMIN})
async def delete_tags_bulk(request, tag_ids, user):
    pass


async def get_os_compatible_agents(agents: Iterable[Agent], oses: Iterable[str]) -> Set[
    Agent]:
    async def agent_is_included(agent: Agent):
        os = await agent.operating_system
        if os is None:
            return False
        return str(os.id) in oses

    return {agent for agent in agents if await agent_is_included(agent)}


@agent.get("/")
@protected()
async def get_own_agents(request, user):
    plan = request.args.get("installable_for_service_plan")
    if plan is not None:
        plan = await ServicePlan.get_or_none(id=plan)
        if plan is None:
            raise NotFound("Service plan not found.")
        service = await (await plan.service_offering).service
        # TODO: Logic to check which agents software can be installed on
        softwares = await AgentSoftware.filter(
            service_plan__service_offering__service=service).all()
        agents_with_service = {await software.agent for software in softwares}
        available_versions = await PackageManagerAvailableVersion.filter(
            service=service).all().prefetch_related("operating_system")
        available_oses = set(
            map(lambda version: str(version.operating_system.id), available_versions))
        agents = await Agent.filter(user=user).all()
        agents_with_compatible_os = await get_os_compatible_agents(agents, available_oses)
        installable_agents: Set[Serializable] = (
                                                        set(agents) - agents_with_service) & agents_with_compatible_os
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
        event = Event(EventType.AGENT_INIT, Recipient(SubscriberType.SERVER),
                      {"agent_id": str(agent.id)})
        notify.queue(event)
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
async def bulk_delete_agents(request, user: User):
    try:
        ids = request.json["ids"]
        if user_has_roles(user, {UserRole.Role.ADMIN}):
            user_filter = {}
        else:
            user_filter = {"user": user}
        await Agent.filter(id__in=ids, **user_filter).all().delete()
        return HTTPResponse(status=204)
    except KeyError:
        raise BadRequest("Missing parameters. Required: ids")


@agent_software.get("/all")
@protected({UserRole.Role.ADMIN})
@get_endpoint(AgentSoftware)
async def get_agent_software(request, software, user):
    pass


@agent_software.get("/count")
@protected()
async def get_agent_software_count(request, user):
    return json({
        "count": await AgentSoftware.filter(agent__user=user).count()
    })


@agent_software.get("/")
@protected()
async def get_own_agent_software(request, user):
    softwares = await AgentSoftware.filter(agent__user=user).all()
    data = []
    for software in softwares:
        offering = await (await software.service_plan).service_offering
        service = await offering.service
        agent = await software.agent
        latest_version = await get_latest_version(service, await agent.operating_system)
        data.append(
            {
                **await software.to_dict(),
                "latest_version": latest_version.version if latest_version is not None else None,
                "offering": await offering.to_dict(),
                "service": await service.to_dict(),
                "agent": await agent.to_dict()
            })
    return json(data)


@agent_software.post("/bulk")
@protected()
async def bulk_create_agent_software(request, user: User):
    missing_params = BadRequest("Missing parameters. Required: agents, service_plan.")
    if request.json is None:
        raise missing_params
    try:
        plan = await ServicePlan.get_or_none(id=request.json["service_plan"])
        await create_agent_softwares_after_safety_checks(request.json["agents"], plan, user)
    except KeyError:
        raise missing_params
    except IntegrityError:
        raise BadRequest("Service plan is already installed on at least one agent.")
    return HTTPResponse(status=201)


async def create_agent_softwares_after_safety_checks(agent_ids: List[int],
                                                     service_plan: ServicePlan, user: User):
    agents = []
    if service_plan is None:
        raise NotFound("Service plan not found.")
    offering: ServiceOffering = await service_plan.service_offering
    service: Service = await offering.service
    offerings = await ServiceOffering.filter(service=service).all()
    offering_ids = list(map(lambda offering: offering.id, offerings))
    existing_plans = list(map(lambda plan: plan.id, await ServicePlan.filter(user=user,
                                                                             service_offering_id__in=offering_ids).all()))
    existing_softwares = await AgentSoftware.filter(
        service_plan_id__in=existing_plans).all().prefetch_related("agent")
    if (await service_plan.user).id != user.id:
        raise BadRequest(
            "You can't bulk-create agent software for another user's service plan.")
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
    softwares = [AgentSoftware(agent=agent, service_plan=service_plan, installing=True) for agent in
                 agents]
    async with in_transaction():
        await AgentSoftware.bulk_create(softwares)
        for (software, agent) in zip(softwares, agents):
            version = await get_latest_version(service, await agent.operating_system)
            if version is None:
                raise BadRequest("No compatible version found for agent.")
            dependencies = []
            new_deps: List[PackageManagerAvailableVersion] = await version.dependencies.all()
            while len(new_deps) > 0:
                dependencies.extend(new_deps)
                new_deps = [dep for v in new_deps for dep in await v.dependencies.all()]
            for dep in dependencies:
                await send_agent_software_notification(EventType.INSTALL_DEPENDENCY, agent, dep,
                                                       None)
            await send_agent_software_notification(EventType.INSTALL_SOFTWARE, agent,
                                                   version, software)
        await _increase_download_count_for_service(str(service.id), len(agent_ids))


@agent_software.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(AgentSoftware)
async def patch_agent_software(request, software, user):
    pass


@agent_software.delete("/")
@protected()
async def delete_agent_software(request: Request, user: User):
    id = request.args.get("id")
    software: AgentSoftware | None = await AgentSoftware.get_or_none(id=id)
    if software is None:
        raise NotFound(f"AgentSoftware '{id}' not found.")
    if str((await (await software.agent).user).id) != str(user.id):
        raise BadRequest("You can only dismiss software on your own agents.")
    recipient = Recipient(SubscriberType.AGENT, str((await software.agent).id))
    cancel_event(EventType.INSTALL_SOFTWARE, recipient)
    await software.delete()
    return HTTPResponse(status=204)


@agent_software.post("/update")
@protected()
async def update_agent_software(request, user):
    id = request.args.get("id")
    software = await AgentSoftware.get_or_none(id=id)
    if software is None:
        raise NotFound("AgentSoftware not found.")
    agent = await software.agent
    service = await (await (await software.service_plan).service_offering).service
    await send_agent_software_notification(EventType.INSTALL_SOFTWARE, agent, service,
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
    version = await get_latest_version(service, await agent.operating_system)
    await send_agent_software_notification(EventType.UNINSTALL_SOFTWARE, agent, version,
                                           software)
    software.uninstalling = True
    await software.save()


async def send_agent_software_notification(command: EventType, agent: Agent,
                                           version: PackageManagerAvailableVersion,
                                           software: AgentSoftware | None):
    assert command in [EventType.INSTALL_SOFTWARE, EventType.UNINSTALL_SOFTWARE,
                       EventType.INSTALL_DEPENDENCY]
    if software is not None:
        software.last_updated = datetime.datetime.now(tz=datetime.timezone.utc)
    service_name = (await version.service).system_name
    msg = {
        "service": service_name
    }
    if command in [EventType.INSTALL_SOFTWARE, EventType.UNINSTALL_SOFTWARE]:
        assert software is not None
        msg["software"] = str(software.id)
    if command in [EventType.INSTALL_SOFTWARE, EventType.INSTALL_DEPENDENCY]:
        msg["version"] = version.version
    recipient = Recipient(SubscriberType.AGENT, str(agent.id))
    event = Event(command, recipient, msg, False)
    notify.queue(event)

async def send_agent_set_up_license_notification(agent: Agent, license: UserLicense):
    recipient = Recipient(SubscriberType.AGENT, str(agent.id))
    license_type: ServiceUserLicenseType = await license.license_type
    service: Service = await license_type.service
    msg = {
        "license": {**await license.to_dict(), "license_key": license.license_key},
        "service": await service.to_dict()
    }
    event = Event(EventType.SET_UP_LICENSE, recipient, msg, False)
    notify.queue(event)

@license.get("/")
@get_endpoint(License)
async def get_licenses(request, licenses):
    pass


@license.post("/")
@protected({UserRole.Role.ADMIN})
async def create_license(request, user):
    try:
        name = request.json["name"]
        license = await License.create(name=name)
        return await license.json()
    except (AttributeError, KeyError):
        raise BadRequest("Expected parameter name.")


@license.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(License)
async def update_license(request, license, user):
    pass


@license.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(License)
async def delete_license(request, license, user):
    pass


@license.delete("/bulk")
@bulk_delete_endpoint(License, {UserRole.Role.ADMIN})
async def delete_licenses_bulk(request, license_ids, user):
    pass


@operating_system.get("/")
@protected()
@get_endpoint(OperatingSystem)
async def get_operating_systems(request, user, operating_systems):
    pass


@operating_system.post("/")
@protected({UserRole.Role.ADMIN})
async def create_operating_system(request, user):
    try:
        name = request.json["name"]
        system_name = request.json["system_name"]
        os = await OperatingSystem.create(name=name, system_name=system_name)
        return os.json()
    except (AttributeError, KeyError):
        raise BadRequest("Expected parameters name and system_name.")


@operating_system.patch("/")
@protected({UserRole.Role.ADMIN})
@patch_endpoint(OperatingSystem)
async def update_operating_system(request, user, operating_system):
    pass


@operating_system.delete("/")
@protected({UserRole.Role.ADMIN})
@delete_endpoint(OperatingSystem)
async def delete_operating_system(request, user, operating_system):
    pass


@agent.get("/count")
@protected()
async def get_own_agent_count(request, user: User):
    count = await Agent.filter(user=user).count()
    return json({"count": count})


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


@payment_method.delete("/all")
@requires_stripe_customer(stripe)
async def remove_all_payment_methods_from_customer(request, user, customer: stripe.Customer):
    methods = await stripe.PaymentMethod.list_async(customer=customer.id)
    for method in methods:
        await stripe.PaymentMethod.detach_async(method.id)
    return HTTPResponse(status=204)


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


@app.get("/api/server/status")
@protected({UserRole.Role.ADMIN})
@get_endpoint(ServerStatus)
async def get_server_stati(request, user, stati):
    pass


@app.post("/api/server/stop")
@protected({UserRole.Role.ADMIN})
async def stop_server(request, user):
    app.stop(False)
    return text("Accepted.", status=202)


async def perform_billing_maintenance():
    if STRIPE_API_KEY is None:
        logger.warning("Skipping billing maintenance as no stripe API key is found.")
        return
    performing_maintenance = await ServerStatus.filter(
        performing_billing_maintenance=True).count() > 0
    if performing_maintenance:
        logger.warning("Already performing billing maintenance, therefore skipping this one.")
        return
    logger.info("Performing billing maintenance...")
    event = Event(EventType.BILLING_MAINTENANCE, Recipient(SubscriberType.USER),
                  {"status": "running"}, True)
    notify.queue(event)
    await update_server_status(billing_maintenance=True)
    try:
        await set_up_stripe_products()
        users = await User.all()
        for user in users:
            await evaluate_billing_for_user(user)
    except Exception as e:
        logger.exception(e)
    await update_server_status(billing_maintenance=False)
    event = Event(EventType.BILLING_MAINTENANCE, Recipient(SubscriberType.USER), {"status": "done"},
                  True)
    notify.queue(event)
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
        case "2-year":
            interval = "year"
            interval_count = 2
        case "3-year":
            interval = "year"
            interval_count = 3
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
            name=(user.first_name or "") + " " + (user.last_name or "")
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


async def change_user_email_in_stripe(user: User):
    if user.stripe_id is not None:
        await stripe.Customer.modify_async(user.stripe_id, email=user.email)
    else:
        await set_up_stripe_customer(user)


async def run_schedules():
    logger.info("Starting schedule runner...")
    scheduler = AsyncIOScheduler()

    billing_maintenance_trigger = CronTrigger(minute="*/1")
    scheduler.add_job(perform_billing_maintenance, billing_maintenance_trigger)

    scheduler.start()


async def update_server_status(running: bool = None, billing_maintenance: bool = None):
    status = await get_server_status()
    if status is None:
        status = await ServerStatus.create(server_id=SERVER_ID, server_running=True)
    if running is not None:
        status.server_running = running
    if billing_maintenance is not None:
        status.performing_billing_maintenance = billing_maintenance
    await status.save()


async def get_server_status() -> ServerStatus | None:
    return await ServerStatus.get_or_none(server_id=SERVER_ID)


async def signal_handler(sig: str):
    logger.info(f"Received {sig}, stopping server...")
    await update_server_status(running=False)
    compolvo.email.quit_smtp_server()
    app.stop()


async def set_up_sigint_handler():
    loop = asyncio.get_event_loop()
    signals = ["SIGINT", "SIGTERM"]
    for sig in signals:
        loop.add_signal_handler(getattr(signal, sig),
                                lambda: asyncio.create_task(signal_handler(sig)))


@available_version.get("/")
@protected({UserRole.Role.ADMIN})
async def get_available_versions(request: Request, user):
    service_id = request.args.get("service_id")
    if service_id is None:
        raise BadRequest("Expected service_id query parameter.")
    service = await Service.get_or_none(id=service_id)
    if service is None:
        raise NotFound(f"Service '{service_id}' not found.")
    versions = await PackageManagerAvailableVersion.filter(service=service).all()
    data = [{
        **await version.to_dict(),
        "operating_system": await (await version.operating_system).to_dict(),
        "package_manager": await (await version.package_manager).to_dict()
    } for version in versions]
    return json(data)


@available_version.delete("/bulk")
@bulk_delete_endpoint(PackageManagerAvailableVersion, {UserRole.Role.ADMIN})
async def delete_available_versions_bulk(request: Request, version_ids, user):
    pass


@app.get("/api/server-status")
@protected({UserRole.Role.ADMIN})
@get_endpoint(ServerStatus)
async def server_status(request, stati, user):
    pass


async def _increase_download_count_for_service(id: str, count: int = None):
    cnt = count if count is not None else 1
    await Service.filter(id=id).update(download_count=F("download_count") + cnt)


app.add_task(run_schedules())
app.add_task(perform_billing_maintenance())
app.add_task(set_up_sigint_handler())
app.add_task(notify.run_websocket_server())
app.add_task(notify.run_queue_worker())
app.add_task(notify.run_event_worker())

if __name__ == "__main__":
    app.run("0.0.0.0")
