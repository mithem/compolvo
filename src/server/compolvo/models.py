import datetime
from enum import IntEnum
from typing import List, Type
from uuid import UUID

import tortoise.queryset
from sanic import json
from tortoise import run_async
from tortoise.fields import UUIDField, TextField, CharField, IntEnumField, FloatField, IntField, \
    DatetimeField, BooleanField, ForeignKeyField, ManyToManyField
from tortoise.models import Model


class Serializable:
    fields: List[str]

    async def to_dict(self):
        data = {}
        for field in self.fields:
            value = getattr(self, field)
            if isinstance(value, UUID):
                value = str(value)
            elif isinstance(value, datetime.datetime):
                value = value.isoformat()
            elif isinstance(value, tortoise.queryset.QuerySet):
                value = await value.get_or_none()
                try:
                    value = await value.to_dict()
                    if "id" in value.keys():
                        value = value["id"]
                except AttributeError:
                    value = str(value)
            data[field] = value
        return data

    async def json(self):
        return json(await self.to_dict())

    @staticmethod
    async def list_json(objects: List["Serializable"]):
        return json([await object.to_dict() for object in objects])

    @staticmethod
    async def all_json(cls: Type[Model]):
        assert Serializable in cls.__mro__, "`cls` must be a subclass of `Serializable`."
        assert Model in cls.__mro__, "`cls` must be a subclass of `Model`."
        return await cls.list_json(await cls.all())  # typing: ignore


class User(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField(null=True)
    email = CharField(255, unique=True)
    password = TextField(null=True)

    fields = ["id", "name", "email"]

    @property
    def rolenames(self):
        return ["user"]  # TODO: Find a way to actually get user's roles
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
    description = TextField(null=True)
    license = TextField(null=True)
    download_count = IntField(null=True)
    retrieval_method = IntEnumField(RetrievalMethod)
    retrieval_data = TextField()
    latest_version = TextField(null=True)
    tags = ManyToManyField("models.Tag", related_name="services")

    fields = ["id", "name", "description", "license", "download_count", "retrieval_method",
              "retrieval_data", "latest_version"]


class Tag(Model, Serializable):
    id = UUIDField(pk=True)
    label = TextField()
    # services = ManyToManyField("models.Service", related_name="tags")

    fields = ["id", "label"]

class ServiceOffering(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField()
    service = ForeignKeyField("models.Service", "service_offerings")
    description = TextField(null=True)
    price = FloatField()
    duration_days = IntField()

    fields = ["id", "name", "service", "description", "price", "duration_days"]


class ServicePlan(Model, Serializable):
    id = UUIDField(pk=True)
    service_offering = ForeignKeyField("models.ServiceOffering", "service_plans")
    user = ForeignKeyField("models.User")
    start_date = DatetimeField()
    end_date = DatetimeField(null=True)
    canceled_by_user = BooleanField(default=False)

    fields = ["id", "service_offering", "user", "start_date", "end_date", "canceled_by_user"]


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
