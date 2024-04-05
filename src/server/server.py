from sanic import Sanic, redirect, json
from tortoise.contrib.sanic import register_tortoise
from tortoise.exceptions import IntegrityError

from compolvo.models import Customer

app = Sanic("compolvo")

register_tortoise(app, db_url='mysql://root:@192.168.1.101:3306/compolvo', modules={'models': ['compolvo.models']}, generate_schemas=True)

@app.get("/")
async def index(request):
    return redirect("/api/customer")

@app.get("/api/customer")
async def get_customers(request):
    return json(list(map(lambda c: dict(c), await Customer.all())))


@app.post("/api/customer")
async def create_customer(request):
    try:
        customer = Customer(name=request.json["name"], email=request.json["email"])
        await customer.save()
        return json(dict(customer))
    except IntegrityError as e:
        return json(dict(error=str(e)), status=500)


if __name__ == "__main__":
    app.run()
