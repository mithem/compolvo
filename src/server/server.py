import os
import secrets
import string

from sanic import Sanic, redirect, Request, text, Blueprint
from sanic.exceptions import BadRequest, NotFound
from sanic_beskar import Beskar
from sanic_beskar.exceptions import AuthenticationError, TOTPRequired
from tortoise.contrib.sanic import register_tortoise

from compolvo import cors
from compolvo import options
from compolvo.decorators import patch_endpoint, delete_endpoint, get_endpoint
from compolvo.models import User, Service, Serializable, ServiceOffering, ServicePlan

app = Sanic("compolvo")
beskar = Beskar()

app.config.SECRET_KEY = "".join(secrets.choice(string.ascii_letters) for i in range(32))

beskar.init_app(app, User)
db_hostname = os.environ[
    "DB_HOSTNAME"]  # TODO: Make other parameters configurable via environment variables
register_tortoise(app, db_url=f'mysql://root:@{db_hostname}:3306/compolvo',
                  modules={'models': ['compolvo.models']}, generate_schemas=True)

api = Blueprint("api", url_prefix="/api")
user = Blueprint("user", url_prefix="/api/user")
service = Blueprint("service", url_prefix="/api/service")
service_offering = Blueprint("service_offering", url_prefix="/api/service/offering")
service_plan = Blueprint("service_plan", url_prefix="/api/service/plan")

app.blueprint(api)
app.blueprint(user)
app.blueprint(service)
app.blueprint(service_offering)
app.blueprint(service_plan)

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
async def get_services(request):
    return await Serializable.all_json(Service)


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


@api.get("/version")
async def version(request):
    return text("1.0.0a1")


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
async def get_service_offerings(request):
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
        return offering.json()
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


if __name__ == "__main__":
    app.run("0.0.0.0")
