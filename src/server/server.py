import secrets
import string

import sanic_beskar
from sanic import Sanic, redirect, HTTPResponse, Request, text, json
from sanic.errorpages import BadRequest
from sanic_beskar import Beskar
from sanic_beskar.exceptions import AuthenticationError, TOTPRequired
from tortoise.contrib.sanic import register_tortoise
from tortoise.exceptions import IntegrityError

from compolvo.models import User, Service, Serializable

app = Sanic("compolvo")
beskar = Beskar()

#app.config.SECRET_KEY = "".join(secrets.choice(string.ascii_letters) for i in range(32))
app.config.SECRET_KEY = "helloworld"

beskar.init_app(app, User)
register_tortoise(app, db_url='mysql://root:@localhost:3306/compolvo',
                  modules={'models': ['compolvo.models']}, generate_schemas=True)


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
@sanic_beskar.auth_required
async def protected(request):
    return text("You're accessing a protected page!")


@app.get("/api/user")
@sanic_beskar.roles_required(["admin"])
async def get_users(request):
    return await Serializable.all_json(User)


@app.post("/api/user")
async def create_user(request):
    try:
        user = User(
            name=request.json["name"],
            email=request.json["email"],
            password=beskar.hash_password(request.json["password"])
        )
        await user.save()
        return user.json()
    except KeyError:
        raise BadRequest("Missing name, email, or password.")
    except IntegrityError:
        raise BadRequest("User with specified email already exists.")


@app.patch("/api/user")
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


@app.delete("/api/user")
async def delete_user(request):
    try:
        email = request.json["email"]
        user = await User.get(email=email)
        await user.delete()
        return HTTPResponse(status=204)
    except KeyError:
        raise BadRequest("Please specify the new email of the user to delete.")


@app.get("/api/service")
async def get_services(request):
    return await Serializable.all_json(Service)


if __name__ == "__main__":
    app.run()
