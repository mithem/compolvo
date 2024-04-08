from enum import IntEnum
from typing import List, Type

from sanic import json
from tortoise import run_async
from tortoise.fields import UUIDField, TextField, CharField, IntEnumField, FloatField, IntField, \
    DatetimeField, BooleanField, ForeignKeyField
from tortoise.models import Model


class Serializable:
    fields: List[str]

    def to_dict(self):
        data = {}
        for field in self.fields:
            value = getattr(self, field)
            if field == "id":
                value = str(value)
            data[field] = value
        return data

    def json(self):
        return json(self.to_dict())

    @staticmethod
    def list_json(objects: List["Serializable"]):
        return json(list(map(lambda obj: obj.to_dict(), objects)))

    @staticmethod
    async def all_json(cls: Type[Model]):
        assert Serializable in cls.__mro__, "`cls` must be a subclass of `Serializable`."
        assert Model in cls.__mro__, "`cls` must be a subclass of `Model`."
        return cls.list_json(await cls.all()) # typing: ignore


class User(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField(null=True)
    email = CharField(255, unique=True)
    password = TextField(null=True)

    fields = ["name", "email"]

    @property
    def rolenames(self):
        return ["user"] # TODO: Find a way to actually get user's roles
        return list(map(lambda role: role.role, run_async(UserRole.filter(user=self.id).all())))

    @classmethod
    async def lookup(cls, username=None, email=None):
        if username is not None:
            return await cls.filter(name=username).get_or_none()
        elif email is not None:
            return await cls.filter(email=email).get_or_none()
        else:
            return None

    @classmethod
    async def identify(cls, id):
        return await cls.filter(id=id).get_or_none()

    @property
    def identity(self):
        return self.id



class UserRole(Model, Serializable):
    class Role(IntEnum):
        USER = 1
        ADMIN = 2

    id = UUIDField(pk=True)
    user = ForeignKeyField("models.User", "roles")
    role = IntEnumField(Role)

    fields = ["user", "role"]

class Service(Model, Serializable):
    class RetrievalMethod(IntEnum):
        COMMAND = 1
        APT = 2
        COMPOLVO_PACKAGE = 3

    id = UUIDField(pk=True)
    name = TextField()
    retrieval_method = IntEnumField(RetrievalMethod)
    retrieval_data = TextField()
    latest_version = TextField(null=True)

    fields = ["id", "name", "retrieval_method", "retrieval_data", "latest_version"]

class ServiceOffering(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField()
    service = ForeignKeyField("models.Service", "service_offerings")
    description = TextField(null=True)
    price = FloatField()
    duration_days = IntField()

    fields = ["name", "service", "description", "price", "duration_days"]

class ServicePlan(Model, Serializable):
    id = UUIDField(pk=True)
    service_offering = ForeignKeyField("models.ServiceOffering", "service_plans")
    user = ForeignKeyField("models.User")
    start_date = DatetimeField()
    end_date = DatetimeField(null=True)
    canceled_by_user = BooleanField(default=False)

    fields = ["service_offering", "user", "start_date", "end_date", "canceled_by_user"]

class Payment(Model, Serializable):
    id = UUIDField(pk=True)
    service_plan = ForeignKeyField("models.ServicePlan", "payments")
    amount = FloatField()
    date = DatetimeField()

    fields = ["service_plan", "amount", "date"]

class Agent(Model, Serializable):
    id = UUIDField(pk=True)
    user = ForeignKeyField("models.User", "agents")
    last_connection_start = DatetimeField(null=True)

    fields = ["user", "last_connection_start"]

class AgentSoftware(Model):
    id = UUIDField(pk=True)
    agent = ForeignKeyField("models.Agent", "agent_softwares")
    service_plan = ForeignKeyField("models.ServicePlan", "agent_softwares")
    installed_version = TextField(null=True)
    corrupt = BooleanField(default=False)

    fields = ["agent", "service_plan", "installed_version", "corrupt"]