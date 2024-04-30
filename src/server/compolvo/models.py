import datetime
import enum
from enum import IntEnum
from typing import List, Type, Iterable
from uuid import UUID

import tortoise.queryset
from sanic import json
from tortoise.fields import UUIDField, TextField, CharField, IntEnumField, FloatField, IntField, \
    DatetimeField, BooleanField, ForeignKeyField, ManyToManyField
from tortoise.fields.relational import _NoneAwaitable
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
            elif isinstance(value, Serializable):
                value = await value.to_dict()
            elif isinstance(value, _NoneAwaitable):
                value = None
            data[field] = value
        return data

    async def json(self):
        return json(await self.to_dict())

    @staticmethod
    async def list_json(objects: Iterable["Serializable"]):
        return json(await Serializable.list_dict(objects))

    @staticmethod
    async def list_dict(objects: Iterable["Serializable"]):
        return [await object.to_dict() for object in objects]

    @staticmethod
    async def all_json(cls: Type[Model]):
        assert Serializable in cls.__mro__, "`cls` must be a subclass of `Serializable`."
        assert Model in cls.__mro__, "`cls` must be a subclass of `Model`."
        return await cls.list_json(await cls.all())  # typing: ignore


class BillingCycleType(enum.IntEnum):
    INDIVIDUAL = 0


class BillingCycle(Model, Serializable):
    id = UUIDField(pk=True)
    type = IntEnumField(BillingCycleType, unique=True)
    description = TextField()

    fields = ["id", "type", "description"]


class User(Model, Serializable):
    id = UUIDField(pk=True)
    first_name = TextField(null=True)
    last_name = TextField(null=True)
    email = CharField(255, unique=True)
    password = TextField(null=True)
    salt = TextField(null=True)
    stripe_id = TextField(null=True)
    billing_cycle = ForeignKeyField("models.BillingCycle", "users")

    fields = ["id", "first_name", "last_name", "email", "billing_cycle"]


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
    system_name = TextField()
    short_description = TextField(null=True)
    description = TextField(null=True)
    license = ForeignKeyField("models.License", "services")
    download_count = IntField(null=True)
    tags = ManyToManyField("models.Tag", related_name="services")
    stripe_product_id = TextField(null=True)

    fields = ["id", "system_name", "name", "short_description", "description", "license",
              "download_count",
              "image"]


class OperatingSystem(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField()
    system_name = CharField(255, unique=True)

    fields = ["id", "name", "system_name"]


class PackageManager(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField(null=True)

    fields = ["id", "name"]


class PackageManagerAvailableVersion(Model, Serializable):
    id = UUIDField(pk=True)
    service = ForeignKeyField("models.Service", "available_versions")
    operating_system = ForeignKeyField("models.OperatingSystem", "available_versions")
    package_manager = ForeignKeyField("models.PackageManager", "available_versions")
    version = TextField()
    latest = BooleanField(default=False)

    class Meta:
        unique_together = (("service", "package_manager", "operating_system", "latest"),)


class License(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField()

    fields = ["id", "name"]


class Tag(Model, Serializable):
    id = UUIDField(pk=True)
    label = TextField()

    fields = ["id", "label"]


class ServiceOffering(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField()
    service = ForeignKeyField("models.Service", "service_offerings")
    description = TextField(null=True)
    price = FloatField()
    duration_days = IntField()
    stripe_price_id = TextField(null=True)

    fields = ["id", "name", "service", "description", "price", "duration_days"]


class ServicePlan(Model, Serializable):
    id = UUIDField(pk=True)
    service_offering = ForeignKeyField("models.ServiceOffering", "service_plans")
    user = ForeignKeyField("models.User")
    start_date = DatetimeField()
    end_date = DatetimeField(null=True)
    canceled_by_user = BooleanField(default=False)
    canceled_at = DatetimeField(null=True, default=None)
    stripe_subscription_id = TextField(null=True)

    fields = ["id", "service_offering", "user", "start_date", "end_date", "canceled_by_user",
              "canceled_at"]


class Agent(Model, Serializable):
    id = UUIDField(pk=True)
    name = TextField(null=True)
    user = ForeignKeyField("models.User", "agents")
    connection_from_ip_address = TextField(null=True)
    last_connection_start = DatetimeField(null=True)
    last_connection_end = DatetimeField(null=True)
    connected = BooleanField(default=False)
    connection_interrupted = BooleanField(default=False)
    initialized = BooleanField(default=False)
    operating_system = ForeignKeyField("models.OperatingSystem", "agents", null=True)

    fields = ["id", "name", "user", "connection_from_ip_address", "last_connection_start",
              "last_connection_end", "connected",
              "connection_interrupted", "initialized", "operating_system"]


class AgentSoftware(Model, Serializable):
    id = UUIDField(pk=True)
    agent = ForeignKeyField("models.Agent", "agent_softwares")
    service_plan = ForeignKeyField("models.ServicePlan", "agent_softwares")
    installed_version = TextField(null=True)
    corrupt = BooleanField(default=False)
    installing = BooleanField(default=False)
    uninstalling = BooleanField(default=False)

    fields = ["id", "agent", "service_plan", "installed_version", "corrupt", "installing",
              "uninstalling"]

    class Meta:
        unique_together = (("agent", "service_plan"),)


class ServerStatus(Model, Serializable):
    id = UUIDField(pk=True)
    server_id = CharField(255, unique=True)
    server_running = BooleanField(default=False)
    performing_billing_maintenance = BooleanField(default=False)

    fields = ["id", "server_id", "server_running", "performing_billing_maintenance"]
