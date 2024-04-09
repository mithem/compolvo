import os
import secrets
import string

from sanic import Sanic, redirect, HTTPResponse, Request, text, Blueprint
from sanic.exceptions import BadRequest, NotFound
from sanic_beskar import Beskar
from sanic_beskar.exceptions import AuthenticationError, TOTPRequired
from tortoise.contrib.sanic import register_tortoise
from tortoise.exceptions import IntegrityError

from compolvo.models import User, Service, Serializable, ServiceOffering

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

app.blueprint(api)
app.blueprint(user)
app.blueprint(service)
app.blueprint(service_offering)

@app.get("/")
async def index(request):
    return redirect("/docs")


@app.listener("before_server_start")
async def test_user(request):
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
    except IntegrityError:
        raise BadRequest("User with specified email already exists.")


@user.patch("/")
async def update_user(request):
    # TODO: Authentication: require that user changes itself or has admin/user role
    try:
        old_email = request.json["email"]
        new_name = request.json.get("new_name", None)
        new_email = request.json.get("new_email", None)
        new_password = request.json.get("new_password", None)
        user = await User.get(email=old_email)
        if new_name is not None:
            user.name = new_name
        if new_email is not None:
            user.email = new_email
        if new_password is not None:
            user.password = beskar.hash_password(new_password)
        await user.save()
        return user.json()
    except KeyError:
        raise BadRequest("Please specify the old email of the user to change its attributes of.")


@user.delete("/")
async def delete_user(request):
    try:
        email = request.json["email"]
        user = await User.get(email=email)
        await user.delete()
        return HTTPResponse(status=204)
    except KeyError:
        raise BadRequest("Please specify the new email of the user to delete.")


@service.get("/")
async def get_services(request):
    return await Serializable.all_json(Service)


@service.post("/")
async def create_service(request):
    service = await Service.create(
        name=request.json["name"],
        retrieval_method=request.json["retrieval_method"],
        retrieval_data=request.json["retrieval_data"]
    )
    return service.json()


@api.get("/version")
async def version(request):
    return text("1.0.0a1")


@service.patch("/")
async def update_service(request):
    service = await Service.get_or_none(id=request.args["id"][0])
    print("Service: " + str(service))
    if service is None:
        raise NotFound("Service not found.")

    new_name = request.json.get("name", None)
    if new_name is not None:
        service.name = new_name
    new_retrieval_method = request.json.get("retrieval_method")
    if new_retrieval_method is not None:
        service.retrieval_method = new_retrieval_method
    new_retrieval_data = request.json.get("retrieval_data")
    if new_retrieval_data is not None:
        service.retrieval_data = str(new_retrieval_data)
    await service.save()
    return service.json()


@service.delete("/")
async def delete_service(request):
    service = await Service.get_or_none(id=request.args["id"][0])
    if service is None:
        raise NotFound("Service not found.")
    await service.delete()
    return HTTPResponse(status=204)


@service_offering.get("/")
async def get_service_offerings(request):
    service_id = request.args.get("id")
    if service_id is None:
        return await Serializable.all_json(ServiceOffering)
    return await ServiceOffering.filter(service=service_id[0])

if __name__ == "__main__":
    app.run("0.0.0.0")
